import { Request, Response } from 'express';
import { EMPLOYEE_STATUSES } from './employee.model';
import { ConflictError, EmployeeService, NotFoundError } from './employee.service';
import { ValidationError } from './employee.validation';
import { AuthContext } from './rbac.middleware';
import { ApiError, sendApiError } from '../../middleware/error-handler';
import { getStructuredLogger } from '../../middleware/logger';

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
  private readonly logger = getStructuredLogger('employee-service');

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
      this.logger.audit('employee_created', req.traceId ?? 'missing-trace-id', {
        actor: auth.employee_id ?? auth.role,
        employee_id: employee.employee_id,
        department_id: employee.department_id,
      });
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
    try {
      const auth = getAuth(req);
      const status = req.query.status;

      if (status && typeof status === 'string' && !EMPLOYEE_STATUSES.includes(status as never)) {
        sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
          { field: 'status', reason: `must be one of: ${EMPLOYEE_STATUSES.join(', ')}` },
        ]);
        return;
      }

      const rawLimit = typeof req.query.limit === 'string' ? Number(req.query.limit) : undefined;
      if (rawLimit !== undefined && (!Number.isInteger(rawLimit) || rawLimit < 1 || rawLimit > 100)) {
        sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
          { field: 'limit', reason: 'must be an integer between 1 and 100' },
        ]);
        return;
      }

      const cursor = typeof req.query.cursor === 'string' ? req.query.cursor : undefined;
      let departmentFilter = typeof req.query.department_id === 'string' ? req.query.department_id : undefined;
      let employeeFilter: string | undefined;
      if (auth.role === 'Employee') {
        departmentFilter = undefined;
        employeeFilter = auth.employee_id;
      }
      if (auth.role === 'Manager' && auth.department_id) {
        departmentFilter = auth.department_id;
      }

      const page = this.employeeService.listEmployees({
        employee_id: employeeFilter,
        department_id: departmentFilter,
        status: typeof status === 'string' ? (status as never) : undefined,
        limit: rawLimit,
        cursor,
      });

      const employees = page.data;
      const hasNext = page.page.hasNext;
      const nextCursor = page.page.nextCursor;

      res.status(200).json({
        data: employees,
        page: {
          nextCursor,
          hasNext,
          limit: page.page.limit,
        },
      });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateEmployee = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.employeeId)) {
        return;
      }
      const employee = this.employeeService.updateEmployee(req.params.employeeId, req.body);
      this.logger.audit('employee_updated', req.traceId ?? 'missing-trace-id', {
        actor: auth.employee_id ?? auth.role,
        employee_id: employee.employee_id,
        fields: Object.keys(req.body ?? {}).sort(),
      });
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
      this.logger.audit('employee_department_assigned', req.traceId ?? 'missing-trace-id', {
        actor: auth.employee_id ?? auth.role,
        employee_id: employee.employee_id,
        department_id: employee.department_id,
      });
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
      this.logger.audit('employee_status_updated', req.traceId ?? 'missing-trace-id', {
        actor: auth.employee_id ?? auth.role,
        employee_id: employee.employee_id,
        status: employee.status,
      });
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
      this.logger.audit('employee_deleted', req.traceId ?? 'missing-trace-id', {
        actor: auth.employee_id ?? auth.role,
        employee_id: req.params.employeeId,
      });
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

    if (error instanceof Error && error.message === 'INVALID_CURSOR') {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
        { field: 'cursor', reason: 'must be a valid opaque cursor' },
      ]);
      return;
    }

    if (error instanceof Error && error.message === 'INVALID_PAGINATION_LIMIT') {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
        { field: 'limit', reason: 'must be an integer between 1 and 100' },
      ]);
      return;
    }

    if (error instanceof Error && error.message === 'DB_CONNECTION_POOL_EXHAUSTED') {
      sendError(req, res, 503, 'SERVICE_UNAVAILABLE', 'Temporary database overload. Please retry later.');
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
