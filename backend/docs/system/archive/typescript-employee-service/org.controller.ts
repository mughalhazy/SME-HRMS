import { Request, Response } from 'express';
import { ApiError, sendApiError } from '../../middleware/error-handler';
import { logAuditMutation } from '../../middleware/audit';
import { getStructuredLogger } from '../../middleware/logger';
import { ValidationError } from './employee.validation';
import { ORG_ENTITY_STATUSES, OrgEntityKind } from './org.model';
import { OrgStructureService } from './org.service';
import { AuthContext } from './rbac.middleware';
import { ConflictError, NotFoundError } from './service.errors';
import { EmployeeEventOutbox } from './event-outbox';

const KIND_BY_ROUTE: Record<string, OrgEntityKind> = {
  'business-units': 'business_unit',
  'legal-entities': 'legal_entity',
  locations: 'location',
  'cost-centers': 'cost_center',
  'grade-bands': 'grade_band',
  'job-positions': 'job_position',
};

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

export class OrgStructureController {
  private readonly logger = getStructuredLogger('employee-service');
  private readonly eventOutbox = new EmployeeEventOutbox();

  constructor(private readonly orgStructureService: OrgStructureService) {}

  createEntity = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const kind = this.parseKind(req.params.kind);
      if (!this.ensureManagerWriteScope(req, res, auth, kind, req.body)) {
        return;
      }
      const entity = this.create(kind, req.body);
      this.eventOutbox.enqueue(this.toLegacyEventName(kind, 'Created'), entity.tenant_id, entity, this.getEntityId(kind, entity));
      this.eventOutbox.dispatchPending();
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: entity.tenant_id,
        action: `${kind}_created`,
        entity: kind,
        entityId: this.getEntityId(kind, entity),
        before: {},
        after: entity,
      });
      res.status(201).json({ data: entity });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getEntity = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const kind = this.parseKind(req.params.kind);
      const entity = this.get(kind, req.params.entityId);
      if (!this.ensureManagerReadScope(req, res, auth, entity)) {
        return;
      }
      res.status(200).json({ data: entity });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listEntities = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const kind = this.parseKind(req.params.kind);
      const status = req.query.status;
      if (status && typeof status === 'string' && !ORG_ENTITY_STATUSES.includes(status as never)) {
        sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
          { field: 'status', reason: `must be one of: ${ORG_ENTITY_STATUSES.join(', ')}` },
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
      const filters = {
        tenant_id: req.tenantId,
        entity_id: typeof req.query.entity_id === 'string' ? req.query.entity_id : undefined,
        status: typeof status === 'string' ? (status as never) : undefined,
        business_unit_id: typeof req.query.business_unit_id === 'string' ? req.query.business_unit_id : undefined,
        department_id: typeof req.query.department_id === 'string' ? req.query.department_id : undefined,
        legal_entity_id: typeof req.query.legal_entity_id === 'string' ? req.query.legal_entity_id : undefined,
        manager_employee_id: typeof req.query.manager_employee_id === 'string' ? req.query.manager_employee_id : undefined,
        parent_entity_id: typeof req.query.parent_entity_id === 'string' ? req.query.parent_entity_id : undefined,
        limit: rawLimit,
        cursor: typeof req.query.cursor === 'string' ? req.query.cursor : undefined,
      };
      if (auth.role === 'Manager' && auth.department_id && !filters.department_id && (kind === 'cost_center' || kind === 'job_position')) {
        filters.department_id = auth.department_id;
      }
      const page = this.orgStructureService.list(kind, filters);
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

  updateEntity = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const kind = this.parseKind(req.params.kind);
      const before = this.get(kind, req.params.entityId);
      if (!this.ensureManagerWriteScope(req, res, auth, kind, { ...before, ...req.body })) {
        return;
      }
      const entity = this.update(kind, req.params.entityId, req.body);
      this.eventOutbox.enqueue(this.toLegacyEventName(kind, 'Updated'), entity.tenant_id, entity, this.getEntityId(kind, entity));
      this.eventOutbox.dispatchPending();
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: entity.tenant_id,
        action: `${kind}_updated`,
        entity: kind,
        entityId: this.getEntityId(kind, entity),
        before,
        after: entity,
      });
      res.status(200).json({ data: entity });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  private parseKind(kindSegment: string): OrgEntityKind {
    const kind = KIND_BY_ROUTE[kindSegment];
    if (!kind) {
      throw new ValidationError([{ field: 'kind', reason: 'unsupported org entity kind' }]);
    }
    return kind;
  }

  private get(kind: OrgEntityKind, entityId: string): any {
    switch (kind) {
      case 'business_unit':
        return this.orgStructureService.getBusinessUnitById(entityId);
      case 'legal_entity':
        return this.orgStructureService.getLegalEntityById(entityId);
      case 'location':
        return this.orgStructureService.getLocationById(entityId);
      case 'cost_center':
        return this.orgStructureService.getCostCenterById(entityId);
      case 'grade_band':
        return this.orgStructureService.getGradeBandById(entityId);
      case 'job_position':
        return this.orgStructureService.getJobPositionById(entityId);
    }
  }

  private create(kind: OrgEntityKind, body: any): any {
    switch (kind) {
      case 'business_unit':
        return this.orgStructureService.createBusinessUnit(body);
      case 'legal_entity':
        return this.orgStructureService.createLegalEntity(body);
      case 'location':
        return this.orgStructureService.createLocation(body);
      case 'cost_center':
        return this.orgStructureService.createCostCenter(body);
      case 'grade_band':
        return this.orgStructureService.createGradeBand(body);
      case 'job_position':
        return this.orgStructureService.createJobPosition(body);
    }
  }

  private update(kind: OrgEntityKind, entityId: string, body: any): any {
    switch (kind) {
      case 'business_unit':
        return this.orgStructureService.updateBusinessUnit(entityId, body);
      case 'legal_entity':
        return this.orgStructureService.updateLegalEntity(entityId, body);
      case 'location':
        return this.orgStructureService.updateLocation(entityId, body);
      case 'cost_center':
        return this.orgStructureService.updateCostCenter(entityId, body);
      case 'grade_band':
        return this.orgStructureService.updateGradeBand(entityId, body);
      case 'job_position':
        return this.orgStructureService.updateJobPosition(entityId, body);
    }
  }

  private ensureManagerReadScope(req: Request, res: Response, auth: AuthContext, entity: any): boolean {
    if (auth.role !== 'Manager' || !auth.department_id) {
      return true;
    }
    if (entity.department_id && entity.department_id !== auth.department_id) {
      sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
      return false;
    }
    return true;
  }

  private ensureManagerWriteScope(req: Request, res: Response, auth: AuthContext, kind: OrgEntityKind, entity: any): boolean {
    if (auth.role !== 'Manager' || !auth.department_id) {
      return true;
    }
    if ((kind === 'cost_center' || kind === 'job_position') && entity.department_id && entity.department_id !== auth.department_id) {
      sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
      return false;
    }
    return true;
  }

  private toLegacyEventName(kind: OrgEntityKind, action: 'Created' | 'Updated'): any {
    const base = {
      business_unit: 'BusinessUnit',
      legal_entity: 'LegalEntity',
      location: 'Location',
      cost_center: 'CostCenter',
      grade_band: 'GradeBand',
      job_position: 'JobPosition',
    }[kind];
    return `${base}${action}`;
  }

  private getEntityId(kind: OrgEntityKind, entity: any): string {
    switch (kind) {
      case 'business_unit':
        return entity.business_unit_id;
      case 'legal_entity':
        return entity.legal_entity_id;
      case 'location':
        return entity.location_id;
      case 'cost_center':
        return entity.cost_center_id;
      case 'grade_band':
        return entity.grade_band_id;
      case 'job_position':
        return entity.job_position_id;
    }
  }

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
