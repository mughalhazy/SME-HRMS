import { randomUUID } from 'node:crypto';
import { Request, Response } from 'express';
import { EMPLOYEE_STATUSES } from './employee.model';
import { ConflictError, EmployeeService, NotFoundError } from './employee.service';
import { ValidationError } from './employee.validation';

type AuthRole = 'Admin' | 'Manager' | 'Employee';

type AuthContext = {
  role: AuthRole;
  employee_id?: string;
  department_id?: string;
};

function parseAuth(req: Request): AuthContext {
  const authorization = req.headers.authorization;
  if (!authorization || !authorization.startsWith('Bearer ')) {
    throw new Error('UNAUTHORIZED');
  }

  try {
    const payload = JSON.parse(Buffer.from(authorization.slice(7), 'base64url').toString('utf8'));
    return {
      role: payload.role,
      employee_id: payload.employee_id,
      department_id: payload.department_id,
    } as AuthContext;
  } catch {
    throw new Error('UNAUTHORIZED');
  }
}

function canRead(ctx: AuthContext, targetEmployeeId?: string): boolean {
  if (ctx.role === 'Admin') {
    return true;
  }

  if (ctx.role === 'Manager') {
    return true;
  }

  if (ctx.role === 'Employee') {
    return !targetEmployeeId || ctx.employee_id === targetEmployeeId;
  }

  return false;
}

function canWrite(ctx: AuthContext, targetEmployeeId?: string): boolean {
  if (ctx.role === 'Admin' || ctx.role === 'Manager') {
    return true;
  }

  if (ctx.role === 'Employee') {
    return targetEmployeeId !== undefined && ctx.employee_id === targetEmployeeId;
  }

  return false;
}


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
      const auth = parseAuth(req);
      if (!canWrite(auth)) {
        sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
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
      const auth = parseAuth(req);
      if (!canRead(auth, req.params.employeeId)) {
        sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
        return;
      }
      const employee = this.employeeService.getEmployeeById(req.params.employeeId);
      res.status(200).json({ data: employee });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listEmployees = (req: Request, res: Response): void => {
    let auth: AuthContext;
    try {
      auth = parseAuth(req);
    } catch {
      sendError(req, res, 401, 'UNAUTHORIZED', 'Missing or invalid bearer token');
      return;
    }
    const status = req.query.status;
    if (status && typeof status === 'string' && !EMPLOYEE_STATUSES.includes(status as never)) {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
        { field: 'status', reason: `must be one of: ${EMPLOYEE_STATUSES.join(', ')}` },
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

    const employees = this.employeeService.listEmployees({
      department_id: departmentFilter,
      status: typeof status === 'string' ? (status as never) : undefined,
    }).filter((employee) => canRead(auth, employee.employee_id));

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
      const auth = parseAuth(req);
      if (!canWrite(auth, req.params.employeeId)) {
        sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
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
      const auth = parseAuth(req);
      if (!canWrite(auth, req.params.employeeId)) {
        sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
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
      const auth = parseAuth(req);
      if (!canWrite(auth, req.params.employeeId)) {
        sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
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
      const auth = parseAuth(req);
      if (!canWrite(auth, req.params.employeeId)) {
        sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
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
      sendError(req, res, 401, 'UNAUTHORIZED', 'Missing or invalid bearer token');
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
