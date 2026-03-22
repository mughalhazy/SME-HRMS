import { Request, Response } from 'express';
import { logAuditMutation } from '../../middleware/audit';
import { ApiError, sendApiError } from '../../middleware/error-handler';
import { getStructuredLogger } from '../../middleware/logger';
import { AuthContext } from './rbac.middleware';
import { ValidationError } from './employee.validation';
import { ConflictError, NotFoundError } from './service.errors';
import { AssetManagementService } from './asset-management.service';
import { EmployeeService } from './employee.service';

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

export class AssetManagementController {
  private readonly logger = getStructuredLogger('employee-service');

  constructor(
    private readonly assetService: AssetManagementService,
    private readonly employeeService: EmployeeService,
  ) {}

  private canAccessEmployee(auth: AuthContext, employeeId: string | undefined): boolean {
    if (!employeeId) {
      return auth.role === 'Admin' || auth.role === 'Service' || auth.role === 'Manager';
    }
    if (auth.role === 'Admin' || auth.role === 'Service') {
      return true;
    }
    if (auth.role === 'Employee' || auth.role === 'PayrollAdmin') {
      return auth.employee_id === employeeId;
    }
    if (auth.role === 'Manager') {
      return this.employeeService.canManagerAccessEmployee(auth.employee_id, auth.department_id, employeeId);
    }
    return false;
  }

  private ensureEmployeeScope(req: Request, res: Response, auth: AuthContext, employeeId: string | undefined): boolean {
    if (this.canAccessEmployee(auth, employeeId)) {
      return true;
    }
    sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
    return false;
  }

  createAsset = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const linkedEmployeeId = typeof req.body.assigned_employee_id === 'string' ? req.body.assigned_employee_id : undefined;
      if (!this.ensureEmployeeScope(req, res, auth, linkedEmployeeId)) {
        return;
      }
      const result = this.assetService.createAsset({ ...req.body, tenant_id: req.tenantId });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: result.asset.tenant_id,
        action: 'asset_created',
        entity: 'Asset',
        entityId: result.asset.asset_id,
        before: {},
        after: result,
      });
      res.status(201).json({ data: result.asset, lifecycle: result.lifecycle });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getAsset = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const asset = this.assetService.getAssetById(req.params.assetId);
      if (!this.ensureEmployeeScope(req, res, auth, asset.assigned_employee_id)) {
        return;
      }
      res.status(200).json({ data: asset, lifecycle: this.assetService.listAssetLifecycle(asset.asset_id) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listAssets = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      let employeeId = typeof req.query.employee_id === 'string' ? req.query.employee_id : undefined;
      if (auth.role === 'Employee' || auth.role === 'PayrollAdmin') {
        employeeId = auth.employee_id;
      }
      if (employeeId && !this.ensureEmployeeScope(req, res, auth, employeeId)) {
        return;
      }
      const assets = this.assetService.listAssets({
        tenant_id: req.tenantId,
        employee_id: employeeId,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
        asset_type: typeof req.query.asset_type === 'string' ? req.query.asset_type : undefined,
        category: typeof req.query.category === 'string' ? req.query.category : undefined,
      });
      res.status(200).json({ data: assets });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  allocateAsset = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureEmployeeScope(req, res, auth, req.body.employee_id)) {
        return;
      }
      const before = this.assetService.getAssetById(req.params.assetId);
      const result = this.assetService.allocateAsset(req.params.assetId, { ...req.body, tenant_id: req.tenantId });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: result.asset.tenant_id,
        action: 'asset_allocated',
        entity: 'Asset',
        entityId: result.asset.asset_id,
        before,
        after: result,
      });
      res.status(200).json({ data: result.asset, lifecycle: result.lifecycle });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  returnAsset = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const before = this.assetService.getAssetById(req.params.assetId);
      if (!this.ensureEmployeeScope(req, res, auth, before.assigned_employee_id)) {
        return;
      }
      const result = this.assetService.returnAsset(req.params.assetId, { ...req.body, tenant_id: req.tenantId });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: result.asset.tenant_id,
        action: 'asset_returned',
        entity: 'Asset',
        entityId: result.asset.asset_id,
        before,
        after: result,
      });
      res.status(200).json({ data: result.asset, lifecycle: result.lifecycle });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateAssetStatus = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const before = this.assetService.getAssetById(req.params.assetId);
      if (!this.ensureEmployeeScope(req, res, auth, before.assigned_employee_id)) {
        return;
      }
      const result = this.assetService.updateAssetStatus(req.params.assetId, {
        ...req.body,
        tenant_id: req.tenantId,
        actor_id: req.body?.actor_id ?? auth.employee_id ?? auth.role,
      });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: result.asset.tenant_id,
        action: 'asset_status_updated',
        entity: 'Asset',
        entityId: result.asset.asset_id,
        before,
        after: result,
      });
      res.status(200).json({ data: result.asset, lifecycle: result.lifecycle });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listAssetLifecycle = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const asset = this.assetService.getAssetById(req.params.assetId);
      if (!this.ensureEmployeeScope(req, res, auth, asset.assigned_employee_id)) {
        return;
      }
      res.status(200).json({ data: this.assetService.listAssetLifecycle(req.params.assetId) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  private handleError(req: Request, res: Response, error: unknown): void {
    if (error instanceof ValidationError) {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', error.details);
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
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      sendError(req, res, 401, 'TOKEN_INVALID', 'Missing or invalid bearer token');
      return;
    }
    sendError(req, res, 500, 'INTERNAL_ERROR', 'Unexpected error');
  }
}
