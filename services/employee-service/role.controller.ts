import { Request, Response } from 'express';
import { EMPLOYMENT_CATEGORIES, ROLE_STATUSES } from './role.model';
import { RoleService } from './role.service';
import { ConflictError, NotFoundError } from './service.errors';
import { ValidationError } from './employee.validation';
import { AuthContext } from './rbac.middleware';
import { ApiError, sendApiError } from '../../middleware/error-handler';
import { logAuditMutation } from '../../middleware/audit';
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

export class RoleController {
  private readonly logger = getStructuredLogger('employee-service');

  constructor(private readonly roleService: RoleService) {}

  createRole = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const role = this.roleService.createRole(req.body);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: role.tenant_id,
        action: 'role_created',
        entity: 'Role',
        entityId: role.role_id,
        before: {},
        after: role,
      });
      res.status(201).json({ data: role });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getRole = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      res.status(200).json({ data: this.roleService.getRoleIntegrity(req.params.roleId) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listRoles = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const status = typeof req.query.status === 'string' ? req.query.status : undefined;
      const employmentCategory = typeof req.query.employment_category === 'string' ? req.query.employment_category : undefined;

      if (status && !ROLE_STATUSES.includes(status as never)) {
        sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
          { field: 'status', reason: `must be one of: ${ROLE_STATUSES.join(', ')}` },
        ]);
        return;
      }

      if (employmentCategory && !EMPLOYMENT_CATEGORIES.includes(employmentCategory as never)) {
        sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
          { field: 'employment_category', reason: `must be one of: ${EMPLOYMENT_CATEGORIES.join(', ')}` },
        ]);
        return;
      }

      res.status(200).json({
        data: this.roleService.listRoles({
          status: status as never,
          employment_category: employmentCategory as never,
        }),
      });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateRole = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const before = this.roleService.getRoleById(req.params.roleId);
      const role = this.roleService.updateRole(req.params.roleId, req.body);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: role.tenant_id,
        action: 'role_updated',
        entity: 'Role',
        entityId: role.role_id,
        before,
        after: role,
      });
      res.status(200).json({ data: role });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  deleteRole = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const before = this.roleService.getRoleById(req.params.roleId);
      this.roleService.deleteRole(req.params.roleId);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: before.tenant_id,
        action: 'role_deleted',
        entity: 'Role',
        entityId: req.params.roleId,
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
