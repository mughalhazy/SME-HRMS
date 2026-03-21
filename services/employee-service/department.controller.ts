import { Request, Response } from 'express';
import { ApiError, sendApiError } from '../../middleware/error-handler';
import { logAuditMutation } from '../../middleware/audit';
import { getStructuredLogger } from '../../middleware/logger';
import { DEPARTMENT_STATUSES } from './department.model';
import { DepartmentService } from './department.service';
import { ConflictError, NotFoundError } from './service.errors';
import { ValidationError } from './employee.validation';
import { AuthContext } from './rbac.middleware';

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

export class DepartmentController {
  private readonly logger = getStructuredLogger('employee-service');

  constructor(private readonly departmentService: DepartmentService) {}

  private ensureManagerScope(req: Request, res: Response, auth: AuthContext, departmentId: string): boolean {
    if (auth.role !== 'Manager' || !auth.department_id) {
      return true;
    }

    if (departmentId !== auth.department_id) {
      sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
      return false;
    }

    return true;
  }

  createDepartment = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const department = this.departmentService.createDepartment(req.body);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: department.tenant_id,
        action: 'department_created',
        entity: 'Department',
        entityId: department.department_id,
        before: {},
        after: department,
      });
      res.status(201).json({ data: department });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getDepartment = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.departmentId)) {
        return;
      }
      const department = this.departmentService.getDepartmentById(req.params.departmentId);
      res.status(200).json({ data: department });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listDepartments = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const status = req.query.status;

      if (status && typeof status === 'string' && !DEPARTMENT_STATUSES.includes(status as never)) {
        sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
          { field: 'status', reason: `must be one of: ${DEPARTMENT_STATUSES.join(', ')}` },
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
      if (auth.role === 'Manager' && auth.department_id) {
        departmentFilter = auth.department_id;
      }

      const page = this.departmentService.listDepartments({
        department_id: departmentFilter,
        status: typeof status === 'string' ? (status as never) : undefined,
        parent_department_id: typeof req.query.parent_department_id === 'string' ? req.query.parent_department_id : undefined,
        head_employee_id: typeof req.query.head_employee_id === 'string' ? req.query.head_employee_id : undefined,
        limit: rawLimit,
        cursor,
      });

      res.status(200).json({
        data: page.data,
        page: {
          nextCursor: page.page.nextCursor,
          hasNext: page.page.hasNext,
          limit: page.page.limit,
        },
      });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateDepartment = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.departmentId)) {
        return;
      }
      const before = this.departmentService.getDepartmentById(req.params.departmentId);
      const department = this.departmentService.updateDepartment(req.params.departmentId, req.body);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: department.tenant_id,
        action: 'department_updated',
        entity: 'Department',
        entityId: department.department_id,
        before,
        after: department,
      });
      res.status(200).json({ data: department });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  deleteDepartment = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.departmentId)) {
        return;
      }
      const before = this.departmentService.getDepartmentById(req.params.departmentId);
      this.departmentService.deleteDepartment(req.params.departmentId);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: before.tenant_id,
        action: 'department_deleted',
        entity: 'Department',
        entityId: req.params.departmentId,
        before,
        after: {},
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

    sendError(req, res, 500, 'INTERNAL_SERVER_ERROR', 'An unexpected error occurred');
  }
}
