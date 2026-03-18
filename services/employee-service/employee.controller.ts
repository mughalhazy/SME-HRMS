import { Request, Response } from 'express';
import { EMPLOYEE_STATUSES } from './employee.model';
import { ConflictError, EmployeeService, NotFoundError } from './employee.service';
import { ValidationError } from './employee.validation';
import { AuthContext } from './rbac.middleware';
import { ApiError, sendApiError } from '../../middleware/error-handler';

function sendError(
  req: Request,
  res: Response,
  status: number,
  code: string,
  message: string,
  details?: Array<{ field: string; reason: string }>,
): void {
  sendApiError(req, res, new ApiError(status, code, message, details ?? []));
}

function getAuth(req: Request): AuthContext {
  if (!req.auth) {
    throw new Error('UNAUTHORIZED');
  }
  return req.auth;
}

export class EmployeeController {
  constructor(private readonly employeeService: EmployeeService) {}

  private ensureManagerScope(req: Request, res: Response, auth: AuthContext, employeeId: string): boolean {
    if (auth.role !== 'Manager' || !auth.department_id) {
      return true;
    }

    const target = this.employeeService.getEmployeeById(employeeId);
    if (target.department_id !== auth.department_id) {
      sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
      return false;
    }

    return true;
  }

  createEmployee = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (auth.role === 'Manager' && auth.department_id && req.body.department_id !== auth.department_id) {
        sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
        return;
      }

      const employee = this.employeeService.createEmployee(req.body);
      res.status(201).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getEmployee = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.employeeId)) {
        return;
      }
      const employee = this.employeeService.getEmployeeById(req.params.employeeId);
      res.status(200).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listEmployees = (req: Request, res: Response): void => {
    const auth = getAuth(req);
    const status = req.query.status;

    if (status && typeof status === 'string' && !EMPLOYEE_STATUSES.includes(status as never)) {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
        { field: 'status', reason: `must be one of: ${EMPLOYEE_STATUSES.join(', ')}` },
      ]);
      return;
    }

    const rawLimit = typeof req.query.limit === 'string' ? Number(req.query.limit) : 25;
    if (!Number.isInteger(rawLimit) || rawLimit < 1 || rawLimit > 100) {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
        { field: 'limit', reason: 'must be an integer between 1 and 100' },
      ]);
      return;
    }

    let departmentFilter = typeof req.query.department_id === 'string' ? req.query.department_id : undefined;
    if (auth.role === 'Employee') {
      departmentFilter = undefined;
    }
    if (auth.role === 'Manager' && auth.department_id) {
      departmentFilter = auth.department_id;
    }

    const employees = this.employeeService
      .listEmployees({
        department_id: departmentFilter,
        status: typeof status === 'string' ? (status as never) : undefined,
      })
      .filter((employee) => auth.role !== 'Employee' || auth.employee_id === employee.employee_id)
      .slice(0, rawLimit);

    res.status(200).json({
      data: employees,
      page: {
        nextCursor: null,
        hasNext: false,
        limit: rawLimit,
      },
    });
  };

  updateEmployee = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.employeeId)) {
        return;
      }
      const employee = this.employeeService.updateEmployee(req.params.employeeId, req.body);
      res.status(200).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  assignDepartment = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.employeeId)) {
        return;
      }
      if (auth.role === 'Manager' && auth.department_id && req.body.department_id !== auth.department_id) {
        sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
        return;
      }
      const employee = this.employeeService.assignDepartment(req.params.employeeId, req.body.department_id);
      res.status(200).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateStatus = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.employeeId)) {
        return;
      }
      const employee = this.employeeService.updateStatus(req.params.employeeId, req.body.status);
      res.status(200).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  deleteEmployee = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.employeeId)) {
        return;
      }
      this.employeeService.deleteEmployee(req.params.employeeId);
      res.status(204).send();
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  private handleError(req: Request, res: Response, error: unknown): void {
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      sendError(req, res, 401, 'TOKEN_INVALID', 'Missing or invalid bearer token');
      return;
    }

    if (error instanceof ValidationError) {
      sendError(req, res, 422, 'VALIDATION_ERROR', error.message, error.details);
      return;
    }

    if (error instanceof NotFoundError) {
      sendError(req, res, 404, 'NOT_FOUND', error.message);
      return;
    }

    if (error instanceof ConflictError) {
      sendError(req, res, 409, 'CONFLICT', error.message);
      return;
    }

    sendError(req, res, 500, 'INTERNAL_SERVER_ERROR', 'Unexpected server failure.');
  }
}
