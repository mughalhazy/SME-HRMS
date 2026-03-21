import { PaginatedResult } from '../../db/optimization';
import { DepartmentRepository } from './department.repository';
import { EmployeeRepository } from './employee.repository';
import { ValidationError } from './employee.validation';
import { RoleRepository } from './role.repository';
import { ConflictError, NotFoundError } from './service.errors';
import {
  BusinessUnit,
  CostCenter,
  CreateBusinessUnitInput,
  CreateCostCenterInput,
  CreateGradeBandInput,
  CreateJobPositionInput,
  CreateLegalEntityInput,
  CreateLocationInput,
  GradeBand,
  JobPosition,
  LegalEntity,
  Location,
  OrgEntityFilters,
  OrgEntityKind,
  UpdateBusinessUnitInput,
  UpdateCostCenterInput,
  UpdateGradeBandInput,
  UpdateJobPositionInput,
  UpdateLegalEntityInput,
  UpdateLocationInput,
} from './org.model';
import { OrgStructureRepository } from './org.repository';
import {
  validateCreateBusinessUnit,
  validateCreateCostCenter,
  validateCreateGradeBand,
  validateCreateJobPosition,
  validateCreateLegalEntity,
  validateCreateLocation,
  validateUpdateBusinessUnit,
  validateUpdateCostCenter,
  validateUpdateGradeBand,
  validateUpdateJobPosition,
  validateUpdateLegalEntity,
  validateUpdateLocation,
} from './org.validation';

type OrgRecord = BusinessUnit | LegalEntity | Location | CostCenter | GradeBand | JobPosition;

export class OrgStructureService {
  constructor(
    private readonly repository: OrgStructureRepository,
    private readonly employeeRepository: EmployeeRepository,
    private readonly departmentRepository: DepartmentRepository,
    private readonly roleRepository: RoleRepository,
  ) {}

  createBusinessUnit(input: CreateBusinessUnitInput): BusinessUnit {
    validateCreateBusinessUnit(input);
    this.ensureUnique('business_unit', input.name, input.code);
    this.assertBusinessUnitReferences(undefined, input.parent_business_unit_id, input.leader_employee_id);
    return this.repository.create('business_unit', input) as BusinessUnit;
  }

  createLegalEntity(input: CreateLegalEntityInput): LegalEntity {
    validateCreateLegalEntity(input);
    this.ensureUnique('legal_entity', input.name, input.code);
    if (input.business_unit_id) {
      this.requireActiveBusinessUnit(input.business_unit_id, 'business_unit_id');
    }
    return this.repository.create('legal_entity', input) as LegalEntity;
  }

  createLocation(input: CreateLocationInput): Location {
    validateCreateLocation(input);
    this.ensureUnique('location', input.name, input.code);
    if (input.legal_entity_id) {
      this.requireActiveLegalEntity(input.legal_entity_id, 'legal_entity_id');
    }
    return this.repository.create('location', input) as Location;
  }

  createCostCenter(input: CreateCostCenterInput): CostCenter {
    validateCreateCostCenter(input);
    this.ensureUnique('cost_center', input.name, input.code);
    this.assertCostCenterReferences(input.business_unit_id, input.department_id, input.legal_entity_id, input.manager_employee_id);
    return this.repository.create('cost_center', input) as CostCenter;
  }

  createGradeBand(input: CreateGradeBandInput): GradeBand {
    validateCreateGradeBand(input);
    this.ensureUnique('grade_band', input.name, input.code);
    return this.repository.create('grade_band', input) as GradeBand;
  }

  createJobPosition(input: CreateJobPositionInput): JobPosition {
    validateCreateJobPosition(input);
    this.ensureUnique('job_position', input.title, input.code);
    this.assertJobPositionReferences(undefined, input);
    return this.repository.create('job_position', input) as JobPosition;
  }

  getBusinessUnitById(entityId: string): BusinessUnit {
    return this.getById('business_unit', entityId) as BusinessUnit;
  }

  getLegalEntityById(entityId: string): LegalEntity {
    return this.getById('legal_entity', entityId) as LegalEntity;
  }

  getLocationById(entityId: string): Location {
    return this.getById('location', entityId) as Location;
  }

  getCostCenterById(entityId: string): CostCenter {
    return this.getById('cost_center', entityId) as CostCenter;
  }

  getGradeBandById(entityId: string): GradeBand {
    return this.getById('grade_band', entityId) as GradeBand;
  }

  getJobPositionById(entityId: string): JobPosition {
    return this.getById('job_position', entityId) as JobPosition;
  }

  list(kind: OrgEntityKind, filters: OrgEntityFilters): PaginatedResult<OrgRecord> {
    return this.repository.list(kind, filters);
  }

  updateBusinessUnit(entityId: string, input: UpdateBusinessUnitInput): BusinessUnit {
    validateUpdateBusinessUnit(input);
    const existing = this.getBusinessUnitById(entityId);
    this.ensureUnique('business_unit', input.name, input.code, entityId);
    this.assertBusinessUnitReferences(entityId, input.parent_business_unit_id ?? existing.parent_business_unit_id, input.leader_employee_id ?? existing.leader_employee_id);
    return this.requireUpdated('business_unit', entityId, input) as BusinessUnit;
  }

  updateLegalEntity(entityId: string, input: UpdateLegalEntityInput): LegalEntity {
    validateUpdateLegalEntity(input);
    const existing = this.getLegalEntityById(entityId);
    this.ensureUnique('legal_entity', input.name, input.code, entityId);
    if ((input.business_unit_id ?? existing.business_unit_id) !== undefined) {
      this.requireActiveBusinessUnit(input.business_unit_id ?? existing.business_unit_id, 'business_unit_id');
    }
    return this.requireUpdated('legal_entity', entityId, input) as LegalEntity;
  }

  updateLocation(entityId: string, input: UpdateLocationInput): Location {
    validateUpdateLocation(input);
    const existing = this.getLocationById(entityId);
    this.ensureUnique('location', input.name, input.code, entityId);
    if ((input.legal_entity_id ?? existing.legal_entity_id) !== undefined) {
      this.requireActiveLegalEntity(input.legal_entity_id ?? existing.legal_entity_id, 'legal_entity_id');
    }
    return this.requireUpdated('location', entityId, input) as Location;
  }

  updateCostCenter(entityId: string, input: UpdateCostCenterInput): CostCenter {
    validateUpdateCostCenter(input);
    const existing = this.getCostCenterById(entityId);
    this.ensureUnique('cost_center', input.name, input.code, entityId);
    this.assertCostCenterReferences(
      input.business_unit_id ?? existing.business_unit_id,
      input.department_id ?? existing.department_id,
      input.legal_entity_id ?? existing.legal_entity_id,
      input.manager_employee_id ?? existing.manager_employee_id,
    );
    return this.requireUpdated('cost_center', entityId, input) as CostCenter;
  }

  updateGradeBand(entityId: string, input: UpdateGradeBandInput): GradeBand {
    validateUpdateGradeBand(input);
    this.getGradeBandById(entityId);
    this.ensureUnique('grade_band', input.name, input.code, entityId);
    return this.requireUpdated('grade_band', entityId, input) as GradeBand;
  }

  updateJobPosition(entityId: string, input: UpdateJobPositionInput): JobPosition {
    validateUpdateJobPosition(input);
    const existing = this.getJobPositionById(entityId);
    this.ensureUnique('job_position', input.title, input.code, entityId);
    this.assertJobPositionReferences(entityId, { ...existing, ...input });
    return this.requireUpdated('job_position', entityId, input) as JobPosition;
  }

  private ensureUnique(kind: OrgEntityKind, name?: string, code?: string, entityId?: string): void {
    if (name) {
      const sameName = this.repository.findByName(kind, name);
      if (sameName && this.getEntityId(kind, sameName) !== entityId) {
        throw new ConflictError(`${kind} name already exists`);
      }
    }
    if (code) {
      const sameCode = this.repository.findByCode(kind, code);
      if (sameCode && this.getEntityId(kind, sameCode) !== entityId) {
        throw new ConflictError(`${kind} code already exists`);
      }
    }
  }

  private getById(kind: OrgEntityKind, entityId: string): OrgRecord {
    const record = this.repository.findById(kind, entityId);
    if (!record) {
      throw new NotFoundError(`${kind} not found`);
    }
    return record;
  }

  private requireUpdated(kind: OrgEntityKind, entityId: string, input: object): OrgRecord {
    const updated = this.repository.update(kind, entityId, input as never);
    if (!updated) {
      throw new NotFoundError(`${kind} not found`);
    }
    return updated;
  }

  private assertBusinessUnitReferences(entityId: string | undefined, parentBusinessUnitId?: string, leaderEmployeeId?: string): void {
    if (parentBusinessUnitId) {
      if (entityId && parentBusinessUnitId === entityId) {
        throw new ValidationError([{ field: 'parent_business_unit_id', reason: 'business unit cannot be its own parent' }]);
      }
      const parent = this.repository.findById('business_unit', parentBusinessUnitId) as BusinessUnit | null;
      if (!parent) {
        throw new ValidationError([{ field: 'parent_business_unit_id', reason: 'parent business unit was not found' }]);
      }
      if (parent.status !== 'Active' && parent.status !== 'Draft') {
        throw new ValidationError([{ field: 'parent_business_unit_id', reason: 'parent business unit must be Draft or Active' }]);
      }
      let cursor: BusinessUnit | null = parent;
      while (cursor?.parent_business_unit_id) {
        if (cursor.parent_business_unit_id === entityId) {
          throw new ValidationError([{ field: 'parent_business_unit_id', reason: 'business unit hierarchy cannot contain cycles' }]);
        }
        cursor = this.repository.findById('business_unit', cursor.parent_business_unit_id) as BusinessUnit | null;
      }
    }

    if (leaderEmployeeId) {
      const leader = this.employeeRepository.findById(leaderEmployeeId);
      if (!leader) {
        throw new ValidationError([{ field: 'leader_employee_id', reason: 'leader employee was not found' }]);
      }
      if (leader.status === 'Terminated') {
        throw new ValidationError([{ field: 'leader_employee_id', reason: 'leader employee cannot be Terminated' }]);
      }
    }
  }

  private assertCostCenterReferences(businessUnitId?: string, departmentId?: string, legalEntityId?: string, managerEmployeeId?: string): void {
    if (businessUnitId) {
      this.requireActiveBusinessUnit(businessUnitId, 'business_unit_id');
    }
    if (departmentId) {
      const department = this.departmentRepository.findById(departmentId);
      if (!department) {
        throw new ValidationError([{ field: 'department_id', reason: 'department was not found' }]);
      }
      if (department.status !== 'Active') {
        throw new ValidationError([{ field: 'department_id', reason: 'department must be Active' }]);
      }
    }
    if (legalEntityId) {
      this.requireActiveLegalEntity(legalEntityId, 'legal_entity_id');
    }
    if (managerEmployeeId) {
      const manager = this.employeeRepository.findById(managerEmployeeId);
      if (!manager) {
        throw new ValidationError([{ field: 'manager_employee_id', reason: 'manager employee was not found' }]);
      }
      if (manager.status === 'Terminated') {
        throw new ValidationError([{ field: 'manager_employee_id', reason: 'manager employee cannot be Terminated' }]);
      }
    }
  }

  private assertJobPositionReferences(entityId: string | undefined, input: Partial<JobPosition>): void {
    const department = this.departmentRepository.findById(input.department_id ?? '');
    if (!department) {
      throw new ValidationError([{ field: 'department_id', reason: 'department was not found' }]);
    }
    if (department.status !== 'Active') {
      throw new ValidationError([{ field: 'department_id', reason: 'department must be Active' }]);
    }

    if (input.business_unit_id) {
      this.requireActiveBusinessUnit(input.business_unit_id, 'business_unit_id');
    }
    if (input.legal_entity_id) {
      this.requireActiveLegalEntity(input.legal_entity_id, 'legal_entity_id');
    }
    if (input.location_id) {
      const location = this.repository.findById('location', input.location_id) as Location | null;
      if (!location) {
        throw new ValidationError([{ field: 'location_id', reason: 'location was not found' }]);
      }
      if (location.status !== 'Active') {
        throw new ValidationError([{ field: 'location_id', reason: 'location must be Active' }]);
      }
    }
    if (input.grade_band_id) {
      const gradeBand = this.repository.findById('grade_band', input.grade_band_id) as GradeBand | null;
      if (!gradeBand) {
        throw new ValidationError([{ field: 'grade_band_id', reason: 'grade band was not found' }]);
      }
      if (gradeBand.status !== 'Active') {
        throw new ValidationError([{ field: 'grade_band_id', reason: 'grade band must be Active' }]);
      }
    }
    if (input.role_id) {
      const role = this.roleRepository.findById(input.role_id);
      if (!role) {
        throw new ValidationError([{ field: 'role_id', reason: 'role was not found' }]);
      }
      if (role.status !== 'Active') {
        throw new ValidationError([{ field: 'role_id', reason: 'role must be Active' }]);
      }
    }
    if (input.default_cost_center_id) {
      const costCenter = this.repository.findById('cost_center', input.default_cost_center_id) as CostCenter | null;
      if (!costCenter) {
        throw new ValidationError([{ field: 'default_cost_center_id', reason: 'default cost center was not found' }]);
      }
      if (costCenter.status !== 'Active') {
        throw new ValidationError([{ field: 'default_cost_center_id', reason: 'default cost center must be Active' }]);
      }
    }
    if (input.reports_to_position_id) {
      if (entityId && input.reports_to_position_id === entityId) {
        throw new ValidationError([{ field: 'reports_to_position_id', reason: 'job position cannot report to itself' }]);
      }
      let cursor = this.repository.findById('job_position', input.reports_to_position_id) as JobPosition | null;
      if (!cursor) {
        throw new ValidationError([{ field: 'reports_to_position_id', reason: 'reports-to position was not found' }]);
      }
      while (cursor?.reports_to_position_id) {
        if (cursor.reports_to_position_id === entityId) {
          throw new ValidationError([{ field: 'reports_to_position_id', reason: 'job position hierarchy cannot contain cycles' }]);
        }
        cursor = this.repository.findById('job_position', cursor.reports_to_position_id) as JobPosition | null;
      }
    }
  }

  private requireActiveBusinessUnit(businessUnitId: string, field: string): void {
    const businessUnit = this.repository.findById('business_unit', businessUnitId) as BusinessUnit | null;
    if (!businessUnit) {
      throw new ValidationError([{ field, reason: 'business unit was not found' }]);
    }
    if (businessUnit.status !== 'Active') {
      throw new ValidationError([{ field, reason: 'business unit must be Active' }]);
    }
  }

  private requireActiveLegalEntity(legalEntityId: string, field: string): void {
    const legalEntity = this.repository.findById('legal_entity', legalEntityId) as LegalEntity | null;
    if (!legalEntity) {
      throw new ValidationError([{ field, reason: 'legal entity was not found' }]);
    }
    if (legalEntity.status !== 'Active') {
      throw new ValidationError([{ field, reason: 'legal entity must be Active' }]);
    }
  }

  private getEntityId(kind: OrgEntityKind, record: OrgRecord): string {
    switch (kind) {
      case 'business_unit':
        return (record as BusinessUnit).business_unit_id;
      case 'legal_entity':
        return (record as LegalEntity).legal_entity_id;
      case 'location':
        return (record as Location).location_id;
      case 'cost_center':
        return (record as CostCenter).cost_center_id;
      case 'grade_band':
        return (record as GradeBand).grade_band_id;
      case 'job_position':
        return (record as JobPosition).job_position_id;
    }
  }
}
