import { Request, Response } from 'express';
import { EMPLOYEE_STATUSES } from './employee.model';
import { EmployeeService } from './employee.service';
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

export class ContractorController {
  private readonly logger = getStructuredLogger('employee-service');

  constructor(private readonly employeeService: EmployeeService) {}

  private ensureManagerScope(req: Request, res: Response, auth: AuthContext, employeeId: string): boolean {
    if (auth.role !== 'Manager') {
      return true;
    }

    if (this.employeeService.canManagerAccessEmployee(auth.employee_id, auth.department_id, employeeId)) {
      return true;
    }

    sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
    return false;
  }

  createContractor = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (auth.role === 'Manager' && auth.department_id && req.body.department_id !== auth.department_id) {
        sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
        return;
      }

      const contractor = this.employeeService.createContractor({ ...req.body, tenant_id: req.tenantId, employment_type: 'Contract' });
      const readModels = this.employeeService.getContractorReadModels(contractor.employee_id);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: contractor.tenant_id,
        action: 'contractor_created',
        entity: 'ContractorProfile',
        entityId: contractor.employee_id,
        before: {},
        after: contractor,
      });
      res.status(201).json({ data: contractor, read_models: readModels });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getContractor = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.employeeId)) {
        return;
      }

      const contractor = this.employeeService.getContractorById(req.params.employeeId);
      const readModels = this.employeeService.getContractorReadModels(contractor.employee_id);
      res.status(200).json({ data: contractor, read_models: readModels });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listContractors = (req: Request, res: Response): void => {
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
      let managerFilter = typeof req.query.manager_employee_id === 'string' ? req.query.manager_employee_id : undefined;
      let employeeFilter: string | undefined;
      const roleFilter = typeof req.query.role_id === 'string' ? req.query.role_id : undefined;
      const businessUnitFilter = typeof req.query.business_unit_id === 'string' ? req.query.business_unit_id : undefined;
      const legalEntityFilter = typeof req.query.legal_entity_id === 'string' ? req.query.legal_entity_id : undefined;
      const locationFilter = typeof req.query.location_id === 'string' ? req.query.location_id : undefined;
      const costCenterFilter = typeof req.query.cost_center_id === 'string' ? req.query.cost_center_id : undefined;
      const jobPositionFilter = typeof req.query.job_position_id === 'string' ? req.query.job_position_id : undefined;
      const gradeBandFilter = typeof req.query.grade_band_id === 'string' ? req.query.grade_band_id : undefined;

      if (auth.role === 'Employee') {
        departmentFilter = undefined;
        managerFilter = undefined;
        employeeFilter = auth.employee_id;
      }
      if (auth.role === 'Manager') {
        if (managerFilter && auth.employee_id && managerFilter !== auth.employee_id) {
          sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
          return;
        }
        managerFilter = auth.employee_id ?? managerFilter;
        departmentFilter = auth.department_id ?? departmentFilter;
      }

      const filters = {
        tenant_id: req.tenantId,
        employee_id: employeeFilter,
        department_id: departmentFilter,
        role_id: roleFilter,
        manager_employee_id: managerFilter,
        business_unit_id: businessUnitFilter,
        legal_entity_id: legalEntityFilter,
        location_id: locationFilter,
        cost_center_id: costCenterFilter,
        job_position_id: jobPositionFilter,
        grade_band_id: gradeBandFilter,
        status: typeof status === 'string' ? (status as never) : undefined,
        limit: rawLimit,
        cursor,
      };

      const page = this.employeeService.listContractors(filters);
      const readModels = this.employeeService.listContractorReadModels(filters);
      res.status(200).json({
        data: page.data,
        page: {
          nextCursor: page.page.nextCursor,
          hasNext: page.page.hasNext,
          limit: page.page.limit,
        },
        read_models: readModels,
      });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateContractor = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.employeeId)) {
        return;
      }
      if (req.body?.department_id !== undefined) {
        sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
          { field: 'department_id', reason: 'use the department assignment endpoint for department changes' },
        ]);
        return;
      }

      const before = this.employeeService.getContractorById(req.params.employeeId);
      const contractor = this.employeeService.updateContractor(req.params.employeeId, req.body);
      const readModels = this.employeeService.getContractorReadModels(contractor.employee_id);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: contractor.tenant_id,
        action: 'contractor_updated',
        entity: 'ContractorProfile',
        entityId: contractor.employee_id,
        before,
        after: contractor,
      });
      res.status(200).json({ data: contractor, read_models: readModels });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateContractorStatus = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureManagerScope(req, res, auth, req.params.employeeId)) {
        return;
      }

      const before = this.employeeService.getContractorById(req.params.employeeId);
      const contractor = this.employeeService.updateStatus(req.params.employeeId, req.body.status);
      const readModels = this.employeeService.getContractorReadModels(contractor.employee_id);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: contractor.tenant_id,
        action: 'contractor_status_updated',
        entity: 'ContractorProfile',
        entityId: contractor.employee_id,
        before,
        after: contractor,
      });
      res.status(200).json({ data: contractor, read_models: readModels });
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
