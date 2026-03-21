import {
  CreateEmployeeInput,
  Employee,
  EmployeeFilters,
  EmployeeReadModelBundle,
  EmployeeStatus,
  UpdateEmployeeInput,
} from './employee.model';
import { DepartmentRepository } from './department.repository';
import { EmployeeRepository } from './employee.repository';
import { EmployeeEventOutbox } from './event-outbox';
import { validateCreateEmployee, validateStatus, validateUpdateEmployee, ValidationError } from './employee.validation';
import { RoleService } from './role.service';
import { ConflictError, NotFoundError } from './service.errors';

const STATUS_TRANSITIONS: Record<EmployeeStatus, EmployeeStatus[]> = {
  Draft: ['Active', 'Terminated'],
  Active: ['OnLeave', 'Suspended', 'Terminated'],
  OnLeave: ['Active', 'Suspended', 'Terminated'],
  Suspended: ['Active', 'Terminated'],
  Terminated: [],
};

interface EmployeePerformanceReviewReferenceRepository {
  hasEmployeeReference(employeeId: string): boolean;
}

export class EmployeeService {
  readonly eventOutbox = new EmployeeEventOutbox();

  constructor(
    private readonly repository: EmployeeRepository,
    private readonly roleService?: RoleService,
    private readonly departmentRepository?: DepartmentRepository,
    private readonly performanceReviewRepository?: EmployeePerformanceReviewReferenceRepository,
    private readonly tenantId: string = 'tenant-default',
  ) {}

  createEmployee(input: CreateEmployeeInput): Employee {
    validateCreateEmployee(input);
    this.assertActorTenant(input.tenant_id);
    this.ensureUniqueEmployee(input.employee_number, input.email);
    this.ensureDepartmentAndRoleAreAssignable(input.department_id, input.role_id);
    this.ensureOrgAssignments({
      department_id: input.department_id,
      role_id: input.role_id,
      manager_employee_id: input.manager_employee_id,
      business_unit_id: input.business_unit_id,
      legal_entity_id: input.legal_entity_id,
      location_id: input.location_id,
      cost_center_id: input.cost_center_id,
      job_position_id: input.job_position_id,
      grade_band_id: input.grade_band_id,
      matrix_manager_employee_ids: input.matrix_manager_employee_ids,
      cost_allocations: input.cost_allocations,
    });
    this.ensureManagerRelationship(input.manager_employee_id);
    this.ensureMatrixManagers(input.matrix_manager_employee_ids, input.manager_employee_id);

    if (input.status === 'Active') {
      this.ensureActivationRequirements(input.department_id, input.role_id, input.job_position_id, input.cost_center_id);
    }

    this.ensureRoleAssignmentLink(input.role_id);

    const employee = this.repository.create({ ...input, tenant_id: this.tenantId });
    this.roleService?.linkEmployee(employee.role_id, employee.employee_id);
    this.eventOutbox.enqueue('EmployeeCreated', this.tenantId, {
      employee_id: employee.employee_id,
      employee_number: employee.employee_number,
      department_id: employee.department_id,
      role_id: employee.role_id,
      business_unit_id: employee.business_unit_id,
      legal_entity_id: employee.legal_entity_id,
      location_id: employee.location_id,
      cost_center_id: employee.cost_center_id,
      job_position_id: employee.job_position_id,
      grade_band_id: employee.grade_band_id,
      matrix_manager_employee_ids: employee.matrix_manager_employee_ids,
      cost_allocations: employee.cost_allocations,
      status: employee.status,
      created_at: employee.created_at,
    }, employee.employee_id);
    this.eventOutbox.dispatchPending();
    return employee;
  }

  getEmployeeById(employeeId: string): Employee {
    const employee = this.repository.findById(employeeId);
    if (!employee) {
      throw new NotFoundError('employee not found');
    }
    return employee;
  }

  getEmployeeReadModels(employeeId: string): EmployeeReadModelBundle {
    return this.repository.toReadModelBundle(this.getEmployeeById(employeeId));
  }

  listEmployees(filters: EmployeeFilters) {
    this.assertActorTenant(filters.tenant_id);
    return this.repository.list({ ...filters, tenant_id: this.tenantId });
  }

  listEmployeeReadModels(filters: EmployeeFilters) {
    this.assertActorTenant(filters.tenant_id);
    const page = this.repository.list({ ...filters, tenant_id: this.tenantId });
    return this.repository.toReadModelListBundle(page.data);
  }

  updateEmployee(employeeId: string, input: UpdateEmployeeInput): Employee {
    validateUpdateEmployee(input);

    const existing = this.repository.findById(employeeId);
    if (!existing) {
      throw new NotFoundError('employee not found');
    }

    if (input.email && input.email !== existing.email) {
      const sameEmail = this.repository.findByEmail(input.email);
      if (sameEmail && sameEmail.employee_id !== employeeId) {
        throw new ConflictError('email already exists');
      }
    }

    const nextDepartmentId = input.department_id ?? existing.department_id;
    const nextRoleId = input.role_id ?? existing.role_id;
    const nextManagerEmployeeId = input.manager_employee_id ?? existing.manager_employee_id;
    const nextMatrixManagers = input.matrix_manager_employee_ids ?? existing.matrix_manager_employee_ids;
    const nextJobPositionId = input.job_position_id ?? existing.job_position_id;
    const nextCostCenterId = input.cost_center_id ?? existing.cost_center_id;
    this.ensureDepartmentAndRoleAreAssignable(nextDepartmentId, nextRoleId);
    this.ensureOrgAssignments({
      department_id: nextDepartmentId,
      role_id: nextRoleId,
      manager_employee_id: nextManagerEmployeeId,
      business_unit_id: input.business_unit_id ?? existing.business_unit_id,
      legal_entity_id: input.legal_entity_id ?? existing.legal_entity_id,
      location_id: input.location_id ?? existing.location_id,
      cost_center_id: nextCostCenterId,
      job_position_id: nextJobPositionId,
      grade_band_id: input.grade_band_id ?? existing.grade_band_id,
      matrix_manager_employee_ids: nextMatrixManagers,
      cost_allocations: input.cost_allocations ?? existing.cost_allocations,
    }, employeeId);
    this.ensureManagerRelationship(nextManagerEmployeeId, employeeId);
    this.ensureMatrixManagers(nextMatrixManagers, nextManagerEmployeeId, employeeId);

    if (input.role_id && input.role_id !== existing.role_id) {
      this.ensureRoleAssignmentLink(input.role_id);
    }

    const updated = this.repository.update(employeeId, input);

    if (updated && input.role_id && input.role_id !== existing.role_id) {
      this.roleService?.relinkEmployee(existing.role_id, updated.role_id, employeeId);
    }

    if (!updated) {
      throw new NotFoundError('employee not found');
    }

    if (updated.status === 'Active') {
      this.ensureActivationRequirements(updated.department_id, updated.role_id, updated.job_position_id, updated.cost_center_id);
    }

    this.eventOutbox.enqueue('EmployeeUpdated', this.tenantId, {
      employee_id: updated.employee_id,
      department_id: updated.department_id,
      role_id: updated.role_id,
      business_unit_id: updated.business_unit_id,
      legal_entity_id: updated.legal_entity_id,
      location_id: updated.location_id,
      cost_center_id: updated.cost_center_id,
      job_position_id: updated.job_position_id,
      grade_band_id: updated.grade_band_id,
      matrix_manager_employee_ids: updated.matrix_manager_employee_ids,
      cost_allocations: updated.cost_allocations,
      status: updated.status,
      updated_at: updated.updated_at,
    }, updated.employee_id);
    this.eventOutbox.dispatchPending();

    return updated;
  }

  assignDepartment(employeeId: string, departmentId: string): Employee {
    if (!departmentId || departmentId.trim() === '') {
      throw new ValidationError([{ field: 'department_id', reason: 'must be a non-empty string' }]);
    }

    const employee = this.getEmployeeById(employeeId);
    const department = this.repository.findDepartmentById(departmentId);
    if (!department) {
      throw new ValidationError([{ field: 'department_id', reason: 'department was not found' }]);
    }
    if (department.status !== 'Active') {
      throw new ValidationError([{ field: 'department_id', reason: `department must be Active, got ${department.status}` }]);
    }

    if (employee.job_position_id) {
      const jobPosition = this.repository.findJobPositionById(employee.job_position_id);
      if (jobPosition && jobPosition.department_id !== departmentId) {
        throw new ConflictError('cannot move employee to a different department while retaining a job position in another department');
      }
    }

    const updated = this.repository.updateDepartment(employeeId, departmentId);
    if (!updated) {
      throw new NotFoundError('employee not found');
    }

    return updated;
  }

  updateStatus(employeeId: string, status: EmployeeStatus): Employee {
    validateStatus(status);

    const employee = this.repository.findById(employeeId);
    if (!employee) {
      throw new NotFoundError('employee not found');
    }

    if (employee.status === status) {
      return employee;
    }

    if (!STATUS_TRANSITIONS[employee.status].includes(status)) {
      throw new ConflictError(`cannot transition status from ${employee.status} to ${status}`);
    }

    if (status === 'Active') {
      this.ensureActivationRequirements(employee.department_id, employee.role_id, employee.job_position_id, employee.cost_center_id);
    }

    const updated = this.repository.updateStatus(employeeId, status);
    if (!updated) {
      throw new NotFoundError('employee not found');
    }

    this.eventOutbox.enqueue('EmployeeStatusChanged', this.tenantId, {
      employee_id: updated.employee_id,
      status: updated.status,
      manager_employee_id: updated.manager_employee_id,
      matrix_manager_employee_ids: updated.matrix_manager_employee_ids,
      updated_at: updated.updated_at,
    }, `${updated.employee_id}:${updated.status}`);
    this.eventOutbox.dispatchPending();

    return updated;
  }

  deleteEmployee(employeeId: string): void {
    const existing = this.repository.findById(employeeId);
    if (!existing) {
      throw new NotFoundError('employee not found');
    }

    if (this.repository.hasDirectReports(employeeId)) {
      throw new ConflictError('cannot delete employee with direct or matrix reports');
    }

    const headedDepartment = this.departmentRepository?.findByHeadEmployeeId(employeeId);
    if (headedDepartment) {
      throw new ConflictError('cannot delete employee assigned as department head');
    }

    if (this.performanceReviewRepository?.hasEmployeeReference(employeeId)) {
      throw new ConflictError('cannot delete employee referenced by performance reviews');
    }

    if (!this.repository.delete(employeeId)) {
      throw new NotFoundError('employee not found');
    }

    this.roleService?.unlinkEmployee(existing.role_id, employeeId);
  }

  canManagerAccessEmployee(managerEmployeeId: string | undefined, managerDepartmentId: string | undefined, targetEmployeeId: string): boolean {
    if (!managerEmployeeId && !managerDepartmentId) {
      return false;
    }
    const target = this.getEmployeeById(targetEmployeeId);
    if (managerDepartmentId && target.department_id === managerDepartmentId) {
      return true;
    }
    if (managerEmployeeId && (target.manager_employee_id === managerEmployeeId || target.matrix_manager_employee_ids.includes(managerEmployeeId))) {
      return true;
    }
    if (managerEmployeeId && this.repository.getIndirectReportIds(managerEmployeeId).has(targetEmployeeId)) {
      return true;
    }
    return false;
  }

  private ensureUniqueEmployee(employeeNumber: string, email: string): void {
    if (this.repository.findByEmployeeNumber(employeeNumber)) {
      throw new ConflictError('employee_number already exists');
    }

    if (this.repository.findByEmail(email)) {
      throw new ConflictError('email already exists');
    }
  }

  private ensureDepartmentAndRoleAreAssignable(departmentId: string, roleId: string): void {
    const department = this.repository.findDepartmentById(departmentId);
    if (!department) {
      throw new ValidationError([{ field: 'department_id', reason: 'department was not found' }]);
    }
    if (department.status !== 'Active') {
      throw new ValidationError([{ field: 'department_id', reason: `department must be Active, got ${department.status}` }]);
    }

    const role = this.repository.findRoleById(roleId);
    if (!role) {
      throw new ValidationError([{ field: 'role_id', reason: 'role was not found' }]);
    }
    if (role.status !== 'Active') {
      throw new ValidationError([{ field: 'role_id', reason: `role must be Active, got ${role.status}` }]);
    }
  }

  private ensureRoleAssignmentLink(roleId: string): void {
    if (this.roleService) {
      this.roleService.getActiveRoleById(roleId);
      return;
    }

    const role = this.repository.findRoleById(roleId);
    if (!role) {
      throw new ValidationError([{ field: 'role_id', reason: 'role was not found' }]);
    }
    if (role.status !== 'Active') {
      throw new ValidationError([{ field: 'role_id', reason: 'role must be active for employee assignment' }]);
    }
  }

  private ensureManagerRelationship(managerEmployeeId?: string, employeeId?: string): void {
    if (managerEmployeeId === undefined) {
      return;
    }

    if (managerEmployeeId === '') {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'must be omitted or a non-empty string' }]);
    }

    if (employeeId && managerEmployeeId === employeeId) {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'employee cannot manage themselves' }]);
    }

    const manager = this.repository.findById(managerEmployeeId);
    if (!manager) {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'manager employee was not found' }]);
    }
    if (manager.status === 'Terminated') {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'manager employee cannot be Terminated' }]);
    }

    if (employeeId && this.repository.getIndirectReportIds(employeeId).has(managerEmployeeId)) {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'reporting hierarchy cannot contain cycles' }]);
    }
  }

  private ensureMatrixManagers(matrixManagerEmployeeIds?: string[], managerEmployeeId?: string, employeeId?: string): void {
    if (!matrixManagerEmployeeIds) {
      return;
    }

    const seen = new Set<string>();
    for (const matrixManagerEmployeeId of matrixManagerEmployeeIds) {
      if (seen.has(matrixManagerEmployeeId)) {
        throw new ValidationError([{ field: 'matrix_manager_employee_ids', reason: 'matrix managers must be unique' }]);
      }
      seen.add(matrixManagerEmployeeId);

      if (employeeId && matrixManagerEmployeeId === employeeId) {
        throw new ValidationError([{ field: 'matrix_manager_employee_ids', reason: 'employee cannot matrix-manage themselves' }]);
      }
      if (managerEmployeeId && matrixManagerEmployeeId === managerEmployeeId) {
        throw new ValidationError([{ field: 'matrix_manager_employee_ids', reason: 'matrix managers cannot duplicate the primary manager' }]);
      }
      const manager = this.repository.findById(matrixManagerEmployeeId);
      if (!manager) {
        throw new ValidationError([{ field: 'matrix_manager_employee_ids', reason: 'matrix manager employee was not found' }]);
      }
      if (manager.status === 'Terminated') {
        throw new ValidationError([{ field: 'matrix_manager_employee_ids', reason: 'matrix manager employee cannot be Terminated' }]);
      }
    }
  }

  private ensureOrgAssignments(
    input: Pick<
      CreateEmployeeInput,
      | 'department_id'
      | 'role_id'
      | 'manager_employee_id'
      | 'business_unit_id'
      | 'legal_entity_id'
      | 'location_id'
      | 'cost_center_id'
      | 'job_position_id'
      | 'grade_band_id'
      | 'matrix_manager_employee_ids'
      | 'cost_allocations'
    >,
    employeeId?: string,
  ): void {
    if (input.business_unit_id) {
      const businessUnit = this.repository.findBusinessUnitById(input.business_unit_id);
      if (!businessUnit) {
        throw new ValidationError([{ field: 'business_unit_id', reason: 'business unit was not found' }]);
      }
      if (businessUnit.status !== 'Active') {
        throw new ValidationError([{ field: 'business_unit_id', reason: 'business unit must be Active' }]);
      }
    }

    if (input.legal_entity_id) {
      const legalEntity = this.repository.findLegalEntityById(input.legal_entity_id);
      if (!legalEntity) {
        throw new ValidationError([{ field: 'legal_entity_id', reason: 'legal entity was not found' }]);
      }
      if (legalEntity.status !== 'Active') {
        throw new ValidationError([{ field: 'legal_entity_id', reason: 'legal entity must be Active' }]);
      }
      if (input.business_unit_id && legalEntity.business_unit_id && legalEntity.business_unit_id !== input.business_unit_id) {
        throw new ValidationError([{ field: 'legal_entity_id', reason: 'legal entity must belong to the selected business unit' }]);
      }
    }

    if (input.location_id) {
      const location = this.repository.findLocationById(input.location_id);
      if (!location) {
        throw new ValidationError([{ field: 'location_id', reason: 'location was not found' }]);
      }
      if (location.status !== 'Active') {
        throw new ValidationError([{ field: 'location_id', reason: 'location must be Active' }]);
      }
      if (input.legal_entity_id && location.legal_entity_id && location.legal_entity_id !== input.legal_entity_id) {
        throw new ValidationError([{ field: 'location_id', reason: 'location must belong to the selected legal entity' }]);
      }
    }

    if (input.cost_center_id) {
      const costCenter = this.repository.findCostCenterById(input.cost_center_id);
      if (!costCenter) {
        throw new ValidationError([{ field: 'cost_center_id', reason: 'cost center was not found' }]);
      }
      if (costCenter.status !== 'Active') {
        throw new ValidationError([{ field: 'cost_center_id', reason: 'cost center must be Active' }]);
      }
      if (costCenter.department_id && costCenter.department_id !== input.department_id) {
        throw new ValidationError([{ field: 'cost_center_id', reason: 'cost center must belong to the selected department' }]);
      }
      if (input.legal_entity_id && costCenter.legal_entity_id && costCenter.legal_entity_id !== input.legal_entity_id) {
        throw new ValidationError([{ field: 'cost_center_id', reason: 'cost center must belong to the selected legal entity' }]);
      }
      if (input.business_unit_id && costCenter.business_unit_id && costCenter.business_unit_id !== input.business_unit_id) {
        throw new ValidationError([{ field: 'cost_center_id', reason: 'cost center must belong to the selected business unit' }]);
      }
    }

    if (input.grade_band_id) {
      const gradeBand = this.repository.findGradeBandById(input.grade_band_id);
      if (!gradeBand) {
        throw new ValidationError([{ field: 'grade_band_id', reason: 'grade band was not found' }]);
      }
      if (gradeBand.status !== 'Active') {
        throw new ValidationError([{ field: 'grade_band_id', reason: 'grade band must be Active' }]);
      }
    }

    if (input.job_position_id) {
      const jobPosition = this.repository.findJobPositionById(input.job_position_id);
      if (!jobPosition) {
        throw new ValidationError([{ field: 'job_position_id', reason: 'job position was not found' }]);
      }
      if (jobPosition.status !== 'Active') {
        throw new ValidationError([{ field: 'job_position_id', reason: 'job position must be Active' }]);
      }
      if (jobPosition.department_id !== input.department_id) {
        throw new ValidationError([{ field: 'job_position_id', reason: 'job position must belong to the selected department' }]);
      }
      if (jobPosition.role_id && jobPosition.role_id !== input.role_id) {
        throw new ValidationError([{ field: 'job_position_id', reason: 'job position must align to the selected role' }]);
      }
      if (input.business_unit_id && jobPosition.business_unit_id && jobPosition.business_unit_id !== input.business_unit_id) {
        throw new ValidationError([{ field: 'job_position_id', reason: 'job position must belong to the selected business unit' }]);
      }
      if (input.legal_entity_id && jobPosition.legal_entity_id && jobPosition.legal_entity_id !== input.legal_entity_id) {
        throw new ValidationError([{ field: 'job_position_id', reason: 'job position must belong to the selected legal entity' }]);
      }
      if (input.location_id && jobPosition.location_id && jobPosition.location_id !== input.location_id) {
        throw new ValidationError([{ field: 'job_position_id', reason: 'job position must belong to the selected location' }]);
      }
      if (input.grade_band_id && jobPosition.grade_band_id && jobPosition.grade_band_id !== input.grade_band_id) {
        throw new ValidationError([{ field: 'job_position_id', reason: 'job position must align to the selected grade band' }]);
      }
      if (input.cost_center_id && jobPosition.default_cost_center_id && jobPosition.default_cost_center_id !== input.cost_center_id) {
        throw new ValidationError([{ field: 'job_position_id', reason: 'job position default cost center must align to the selected cost center' }]);
      }
    }

    if (input.cost_allocations && input.cost_allocations.length > 0) {
      const primaryAllocations = input.cost_allocations.filter((allocation) => allocation.is_primary);
      if (primaryAllocations.length > 1) {
        throw new ValidationError([{ field: 'cost_allocations', reason: 'only one cost allocation can be primary' }]);
      }
      for (const allocation of input.cost_allocations) {
        const costCenter = this.repository.findCostCenterById(allocation.cost_center_id);
        if (!costCenter) {
          throw new ValidationError([{ field: 'cost_allocations', reason: `cost center ${allocation.cost_center_id} was not found` }]);
        }
        if (costCenter.status !== 'Active') {
          throw new ValidationError([{ field: 'cost_allocations', reason: `cost center ${allocation.cost_center_id} must be Active` }]);
        }
      }
    }

    if (input.manager_employee_id) {
      this.ensureManagerRelationship(input.manager_employee_id, employeeId);
    }
    if (input.matrix_manager_employee_ids) {
      this.ensureMatrixManagers(input.matrix_manager_employee_ids, input.manager_employee_id, employeeId);
    }
  }

  private ensureActivationRequirements(departmentId: string, roleId: string, jobPositionId?: string, costCenterId?: string): void {
    this.ensureDepartmentAndRoleAreAssignable(departmentId, roleId);
    if (jobPositionId) {
      const jobPosition = this.repository.findJobPositionById(jobPositionId);
      if (!jobPosition || jobPosition.status !== 'Active') {
        throw new ValidationError([{ field: 'job_position_id', reason: 'job position must be Active for employee activation' }]);
      }
    }
    if (costCenterId) {
      const costCenter = this.repository.findCostCenterById(costCenterId);
      if (!costCenter || costCenter.status !== 'Active') {
        throw new ValidationError([{ field: 'cost_center_id', reason: 'cost center must be Active for employee activation' }]);
      }
    }
  }

  private assertActorTenant(actorTenantId?: string): void {
    if (actorTenantId && actorTenantId !== this.tenantId) {
      throw new ValidationError([{ field: 'tenant_id', reason: 'actor tenant does not match requested tenant scope' }]);
    }
  }
}
