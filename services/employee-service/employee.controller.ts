import { randomUUID } from 'node:crypto';
import { Request, Response } from 'express';
import { EMPLOYEE_STATUSES } from './employee.model';
import { ConflictError, EmployeeService, NotFoundError } from './employee.service';
import { ValidationError } from './employee.validation';

function getTraceId(req: Request): string {
  const incomingTraceId = req.headers['x-trace-id'];

  if (typeof incomingTraceId === 'string' && incomingTraceId.length > 0) {
    return incomingTraceId;
  }

  return randomUUID().replace(/-/g, '').slice(0, 16);
}

function sendError(
  req: Request,
  res: Response,
  status: number,
  code: string,
  message: string,
  details?: Array<{ field: string; reason: string }>,
): void {
  res.status(status).json({
    error: {
      code,
      message,
      details,
      traceId: getTraceId(req),
    },
  });
}

export class EmployeeController {
  constructor(private readonly employeeService: EmployeeService) {}

  createEmployee = (req: Request, res: Response): void => {
    try {
      const employee = this.employeeService.createEmployee(req.body);
      res.status(201).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getEmployee = (req: Request, res: Response): void => {
    try {
      const employee = this.employeeService.getEmployeeById(req.params.employeeId);
      res.status(200).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listEmployees = (req: Request, res: Response): void => {
    const status = req.query.status;
    if (status && typeof status === 'string' && !EMPLOYEE_STATUSES.includes(status as never)) {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
        { field: 'status', reason: `must be one of: ${EMPLOYEE_STATUSES.join(', ')}` },
      ]);
      return;
    }

    const employees = this.employeeService.listEmployees({
      department_id: typeof req.query.department_id === 'string' ? req.query.department_id : undefined,
      status: typeof status === 'string' ? (status as never) : undefined,
    });

    res.status(200).json({
      data: employees,
      page: {
        nextCursor: null,
        hasNext: false,
        limit: Number(req.query.limit) || 25,
      },
    });
  };

  updateEmployee = (req: Request, res: Response): void => {
    try {
      const employee = this.employeeService.updateEmployee(req.params.employeeId, req.body);
      res.status(200).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  assignDepartment = (req: Request, res: Response): void => {
    try {
      const employee = this.employeeService.assignDepartment(req.params.employeeId, req.body.department_id);
      res.status(200).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateStatus = (req: Request, res: Response): void => {
    try {
      const employee = this.employeeService.updateStatus(req.params.employeeId, req.body.status);
      res.status(200).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  deleteEmployee = (req: Request, res: Response): void => {
    try {
      this.employeeService.deleteEmployee(req.params.employeeId);
      res.status(204).send();
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  private handleError(req: Request, res: Response, error: unknown): void {
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
