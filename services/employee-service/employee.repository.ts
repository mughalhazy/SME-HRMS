import { randomUUID } from 'node:crypto';
import { CacheService } from '../../cache/cache.service';
import { ConnectionPool, PaginatedResult, QueryOptimizer, applyCursorPagination } from '../../db/optimization';
import { PersistentMap } from '../../db/persistent-map';
import {
  CreateEmployeeInput,
  Department,
  Employee,
  EmployeeDirectoryReadModel,
  EmployeeFilters,
  EmployeeListReadModelBundle,
  EmployeeReadModelBundle,
  EmployeeReportingReadModel,
  EmployeeStatus,
  OrganizationStructureReadModel,
  Role,
  UpdateEmployeeInput,
} from './employee.model';
import {
  BusinessUnit,
  CostCenter,
  EmployeeCostAllocation,
  GradeBand,
  JobPosition,
  LegalEntity,
  Location,
  ReportingLine,
} from './org.model';
import {
  DEFAULT_TENANT_ID,
  seedBusinessUnits,
  seedCostCenters,
  seedDepartments,
  seedGradeBands,
  seedJobPositions,
  seedLegalEntities,
  seedLocations,
  seedRoles,
} from './domain-seed';

const EMPLOYEE_CACHE_PREFIX = 'employees';

export interface EmployeeReferenceRepository {
  findDepartmentById(departmentId: string): Department | null;
  findRoleById(roleId: string): Role | null;
  findBusinessUnitById?(businessUnitId: string): BusinessUnit | null;
  findLegalEntityById?(legalEntityId: string): LegalEntity | null;
  findLocationById?(locationId: string): Location | null;
  findCostCenterById?(costCenterId: string): CostCenter | null;
  findGradeBandById?(gradeBandId: string): GradeBand | null;
  findJobPositionById?(jobPositionId: string): JobPosition | null;
}

export interface EmployeeRepositoryOptions {
  tenantId?: string;
  referenceRepository?: EmployeeReferenceRepository;
}

export class EmployeeRepository {
  private readonly employees: PersistentMap<Employee>;
  private readonly employeeNumberIndex = new Map<string, string>();
  private readonly emailIndex = new Map<string, string>();
  private readonly departmentIndex = new Map<string, Set<string>>();
  private readonly roleIndex = new Map<string, Set<string>>();
  private readonly statusIndex = new Map<EmployeeStatus, Set<string>>();
  private readonly managerIndex = new Map<string, Set<string>>();
  private readonly matrixManagerIndex = new Map<string, Set<string>>();
  private readonly businessUnitIndex = new Map<string, Set<string>>();
  private readonly legalEntityIndex = new Map<string, Set<string>>();
  private readonly locationIndex = new Map<string, Set<string>>();
  private readonly costCenterIndex = new Map<string, Set<string>>();
  private readonly jobPositionIndex = new Map<string, Set<string>>();
  private readonly gradeBandIndex = new Map<string, Set<string>>();
  private readonly cache = new CacheService({ ttlMs: 15_000, maxEntries: 1_000 });
  private readonly pool = new ConnectionPool(16);
  private readonly optimizer = new QueryOptimizer(10);
  private readonly referenceRepository: EmployeeReferenceRepository;
  private readonly tenantId: string;

  constructor(options: EmployeeReferenceRepository | EmployeeRepositoryOptions = {}) {
    const hasRepo = typeof (options as EmployeeReferenceRepository).findDepartmentById === 'function';
    this.tenantId = hasRepo ? DEFAULT_TENANT_ID : ((options as EmployeeRepositoryOptions).tenantId ?? DEFAULT_TENANT_ID);
    const referenceRepository = hasRepo ? (options as EmployeeReferenceRepository) : (options as EmployeeRepositoryOptions).referenceRepository;
    this.employees = new PersistentMap<Employee>(`employee-service:employees:${this.tenantId}`);

    if (referenceRepository) {
      this.referenceRepository = referenceRepository;
      this.rebuildIndexes();
      return;
    }

    const departmentMap = new Map<string, Department>(seedDepartments(this.tenantId).map((department) => [department.department_id, department]));
    const roleMap = new Map<string, Role>(seedRoles(this.tenantId).map((role) => [role.role_id, role]));
    const businessUnitMap = new Map<string, BusinessUnit>(seedBusinessUnits(this.tenantId).map((businessUnit) => [businessUnit.business_unit_id, businessUnit]));
    const legalEntityMap = new Map<string, LegalEntity>(seedLegalEntities(this.tenantId).map((legalEntity) => [legalEntity.legal_entity_id, legalEntity]));
    const locationMap = new Map<string, Location>(seedLocations(this.tenantId).map((location) => [location.location_id, location]));
    const costCenterMap = new Map<string, CostCenter>(seedCostCenters(this.tenantId).map((costCenter) => [costCenter.cost_center_id, costCenter]));
    const gradeBandMap = new Map<string, GradeBand>(seedGradeBands(this.tenantId).map((gradeBand) => [gradeBand.grade_band_id, gradeBand]));
    const jobPositionMap = new Map<string, JobPosition>(seedJobPositions(this.tenantId).map((jobPosition) => [jobPosition.job_position_id, jobPosition]));
    this.referenceRepository = {
      findDepartmentById: (departmentId: string) => this.matchTenant(departmentMap.get(departmentId) ?? null),
      findRoleById: (roleId: string) => this.matchTenant(roleMap.get(roleId) ?? null),
      findBusinessUnitById: (businessUnitId: string) => this.matchTenant(businessUnitMap.get(businessUnitId) ?? null),
      findLegalEntityById: (legalEntityId: string) => this.matchTenant(legalEntityMap.get(legalEntityId) ?? null),
      findLocationById: (locationId: string) => this.matchTenant(locationMap.get(locationId) ?? null),
      findCostCenterById: (costCenterId: string) => this.matchTenant(costCenterMap.get(costCenterId) ?? null),
      findGradeBandById: (gradeBandId: string) => this.matchTenant(gradeBandMap.get(gradeBandId) ?? null),
      findJobPositionById: (jobPositionId: string) => this.matchTenant(jobPositionMap.get(jobPositionId) ?? null),
    };
    this.rebuildIndexes();
  }

  create(input: CreateEmployeeInput): Employee {
    this.assertTenantFilter(input.tenant_id);
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.create' }, () => {
      const timestamp = new Date().toISOString();
      const normalizedAllocations = this.normalizeCostAllocations(input.cost_allocations, input.cost_center_id);
      const record: Employee = {
        tenant_id: this.tenantId,
        employee_id: randomUUID(),
        employee_number: input.employee_number,
        first_name: input.first_name,
        last_name: input.last_name,
        email: input.email,
        phone: input.phone,
        hire_date: input.hire_date,
        employment_type: input.employment_type,
        status: input.status ?? 'Draft',
        department_id: input.department_id,
        role_id: input.role_id,
        manager_employee_id: input.manager_employee_id,
        business_unit_id: input.business_unit_id,
        legal_entity_id: input.legal_entity_id,
        location_id: input.location_id,
        cost_center_id: input.cost_center_id,
        job_position_id: input.job_position_id,
        grade_band_id: input.grade_band_id,
        matrix_manager_employee_ids: [...(input.matrix_manager_employee_ids ?? [])],
        cost_allocations: normalizedAllocations,
        created_at: timestamp,
        updated_at: timestamp,
      };

      this.employees.set(record.employee_id, record);
      this.reindexEmployee(null, record);
      this.invalidateEmployeeCache(record.employee_id);
      return record;
    }));
  }

  findById(employeeId: string): Employee | null {
    const cacheKey = `${EMPLOYEE_CACHE_PREFIX}:by-id:${this.tenantId}:${employeeId}`;
    const cached = this.cache.get<Employee>(cacheKey);
    if (cached) {
      return cached;
    }

    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.findById', expectedIndex: 'idx_employees_tenant_id + pk_employees' }, () => {
      const employee = this.employees.get(employeeId) ?? null;
      if (employee && employee.tenant_id === this.tenantId) {
        this.cache.set(cacheKey, employee);
        return employee;
      }
      return null;
    }));
  }

  findByEmployeeNumber(employeeNumber: string): Employee | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.findByEmployeeNumber', expectedIndex: 'uq_employees_tenant_employee_number' }, () => {
      const employeeId = this.employeeNumberIndex.get(employeeNumber);
      return employeeId ? this.findById(employeeId) : null;
    }));
  }

  findByEmail(email: string): Employee | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.findByEmail', expectedIndex: 'uq_employees_tenant_email' }, () => {
      const employeeId = this.emailIndex.get(email);
      return employeeId ? this.findById(employeeId) : null;
    }));
  }

  findDepartmentById(departmentId: string): Department | null {
    return this.referenceRepository.findDepartmentById(departmentId);
  }

  findRoleById(roleId: string): Role | null {
    return this.referenceRepository.findRoleById(roleId);
  }

  findBusinessUnitById(businessUnitId: string): BusinessUnit | null {
    return this.referenceRepository.findBusinessUnitById?.(businessUnitId) ?? null;
  }

  findLegalEntityById(legalEntityId: string): LegalEntity | null {
    return this.referenceRepository.findLegalEntityById?.(legalEntityId) ?? null;
  }

  findLocationById(locationId: string): Location | null {
    return this.referenceRepository.findLocationById?.(locationId) ?? null;
  }

  findCostCenterById(costCenterId: string): CostCenter | null {
    return this.referenceRepository.findCostCenterById?.(costCenterId) ?? null;
  }

  findGradeBandById(gradeBandId: string): GradeBand | null {
    return this.referenceRepository.findGradeBandById?.(gradeBandId) ?? null;
  }

  findJobPositionById(jobPositionId: string): JobPosition | null {
    return this.referenceRepository.findJobPositionById?.(jobPositionId) ?? null;
  }

  list(filters: EmployeeFilters): PaginatedResult<Employee> {
    this.assertTenantFilter(filters.tenant_id);
    const cacheKey = `${EMPLOYEE_CACHE_PREFIX}:list:${this.tenantId}:${JSON.stringify(filters)}`;
    const cached = this.cache.get<PaginatedResult<Employee>>(cacheKey);
    if (cached) {
      return cached;
    }

    const result = this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.list', expectedIndex: this.resolveExpectedIndex(filters) }, () => {
      const candidateIds = this.collectCandidateIds(filters);
      const rows = candidateIds
        .map((employeeId) => this.employees.get(employeeId))
        .filter((employee): employee is Employee => Boolean(employee) && employee.tenant_id === this.tenantId)
        .filter((employee) => {
          if (filters.department_id && employee.department_id !== filters.department_id) {
            return false;
          }
          if (filters.role_id && employee.role_id !== filters.role_id) {
            return false;
          }
          if (filters.manager_employee_id && employee.manager_employee_id !== filters.manager_employee_id && !employee.matrix_manager_employee_ids.includes(filters.manager_employee_id)) {
            return false;
          }
          if (filters.business_unit_id && employee.business_unit_id !== filters.business_unit_id) {
            return false;
          }
          if (filters.legal_entity_id && employee.legal_entity_id !== filters.legal_entity_id) {
            return false;
          }
          if (filters.location_id && employee.location_id !== filters.location_id) {
            return false;
          }
          if (filters.cost_center_id && employee.cost_center_id !== filters.cost_center_id) {
            return false;
          }
          if (filters.job_position_id && employee.job_position_id !== filters.job_position_id) {
            return false;
          }
          if (filters.grade_band_id && employee.grade_band_id !== filters.grade_band_id) {
            return false;
          }
          if (filters.status && employee.status !== filters.status) {
            return false;
          }
          return true;
        })
        .sort((left, right) => {
          if (left.updated_at === right.updated_at) {
            return left.employee_id.localeCompare(right.employee_id);
          }
          return right.updated_at.localeCompare(left.updated_at);
        });

      return applyCursorPagination(rows, {
        limit: filters.limit,
        cursor: filters.cursor,
      });
    }));

    this.cache.set(cacheKey, result, { ttlMs: 10_000 });
    return result;
  }

  update(employeeId: string, input: UpdateEmployeeInput): Employee | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.update', expectedIndex: 'idx_employees_tenant_id + pk_employees' }, () => {
      const employee = this.findById(employeeId);
      if (!employee) {
        return null;
      }
      const updated: Employee = {
        ...employee,
        ...input,
        tenant_id: this.tenantId,
        matrix_manager_employee_ids: input.matrix_manager_employee_ids ? [...input.matrix_manager_employee_ids] : employee.matrix_manager_employee_ids,
        cost_allocations: input.cost_allocations !== undefined
          ? this.normalizeCostAllocations(input.cost_allocations, input.cost_center_id ?? employee.cost_center_id)
          : this.normalizeCostAllocations(employee.cost_allocations, input.cost_center_id ?? employee.cost_center_id),
        updated_at: new Date().toISOString(),
      };

      this.reindexEmployee(employee, updated);
      this.employees.set(employeeId, updated);
      this.invalidateEmployeeCache(employeeId);
      return updated;
    }));
  }

  updateDepartment(employeeId: string, departmentId: string): Employee | null {
    return this.update(employeeId, { department_id: departmentId });
  }

  updateStatus(employeeId: string, status: EmployeeStatus): Employee | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.updateStatus', expectedIndex: 'idx_employees_tenant_id + pk_employees' }, () => {
      const employee = this.findById(employeeId);
      if (!employee) {
        return null;
      }
      const updated: Employee = {
        ...employee,
        status,
        updated_at: new Date().toISOString(),
      };
      this.reindexEmployee(employee, updated);
      this.employees.set(employeeId, updated);
      this.invalidateEmployeeCache(employeeId);
      return updated;
    }));
  }

  countByDepartmentId(departmentId: string): number {
    return this.departmentIndex.get(departmentId)?.size ?? 0;
  }

  hasDirectReports(employeeId: string): boolean {
    return (this.managerIndex.get(employeeId)?.size ?? 0) > 0 || (this.matrixManagerIndex.get(employeeId)?.size ?? 0) > 0;
  }

  listDirectAndMatrixReports(employeeId: string): Employee[] {
    const ids = new Set<string>([
      ...(this.managerIndex.get(employeeId) ?? new Set<string>()),
      ...(this.matrixManagerIndex.get(employeeId) ?? new Set<string>()),
    ]);
    return [...ids]
      .map((id) => this.findById(id))
      .filter((employee): employee is Employee => Boolean(employee));
  }

  getIndirectReportIds(managerEmployeeId: string): Set<string> {
    const seen = new Set<string>();
    const queue = [...(this.managerIndex.get(managerEmployeeId) ?? new Set<string>())];
    while (queue.length > 0) {
      const employeeId = queue.shift();
      if (!employeeId || seen.has(employeeId)) {
        continue;
      }
      seen.add(employeeId);
      for (const reportId of this.managerIndex.get(employeeId) ?? []) {
        if (!seen.has(reportId)) {
          queue.push(reportId);
        }
      }
    }
    return seen;
  }

  delete(employeeId: string): boolean {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.delete', expectedIndex: 'idx_employees_tenant_id + pk_employees' }, () => {
      const existing = this.findById(employeeId);
      if (!existing) {
        return false;
      }
      this.employees.delete(employeeId);
      this.reindexEmployee(existing, null);
      this.invalidateEmployeeCache(employeeId);
      return true;
    }));
  }

  toReadModelBundle(employee: Employee): EmployeeReadModelBundle {
    return {
      employee_directory_view: this.toDirectoryReadModel(employee),
      organization_structure_view: this.toOrganizationReadModel(employee),
      employee_reporting_view: this.toReportingReadModel(employee),
    };
  }

  toReadModelListBundle(employees: Employee[]): EmployeeListReadModelBundle {
    return {
      employee_directory_view: employees.map((employee) => this.toDirectoryReadModel(employee)),
      organization_structure_view: employees.map((employee) => this.toOrganizationReadModel(employee)),
      employee_reporting_view: employees.map((employee) => this.toReportingReadModel(employee)),
    };
  }

  private toDirectoryReadModel(employee: Employee): EmployeeDirectoryReadModel {
    const department = this.findDepartmentById(employee.department_id);
    const role = this.findRoleById(employee.role_id);
    const manager = employee.manager_employee_id ? this.findById(employee.manager_employee_id) : null;
    const businessUnit = employee.business_unit_id ? this.findBusinessUnitById(employee.business_unit_id) : null;
    const legalEntity = employee.legal_entity_id ? this.findLegalEntityById(employee.legal_entity_id) : null;
    const location = employee.location_id ? this.findLocationById(employee.location_id) : null;
    const costCenter = employee.cost_center_id ? this.findCostCenterById(employee.cost_center_id) : null;
    const jobPosition = employee.job_position_id ? this.findJobPositionById(employee.job_position_id) : null;
    const gradeBand = employee.grade_band_id ? this.findGradeBandById(employee.grade_band_id) : null;
    const matrixManagers = employee.matrix_manager_employee_ids
      .map((managerEmployeeId) => this.findById(managerEmployeeId))
      .filter((row): row is Employee => Boolean(row));

    return {
      tenant_id: employee.tenant_id,
      employee_id: employee.employee_id,
      employee_number: employee.employee_number,
      full_name: `${employee.first_name} ${employee.last_name}`.trim(),
      email: employee.email,
      phone: employee.phone,
      hire_date: employee.hire_date,
      employment_type: employee.employment_type,
      employee_status: employee.status,
      department_id: employee.department_id,
      department_name: department?.name ?? 'Unknown Department',
      role_id: employee.role_id,
      role_title: role?.title ?? 'Unknown Role',
      manager_employee_id: employee.manager_employee_id,
      manager_name: manager ? `${manager.first_name} ${manager.last_name}`.trim() : undefined,
      business_unit_id: employee.business_unit_id,
      business_unit_name: businessUnit?.name,
      legal_entity_id: employee.legal_entity_id,
      legal_entity_name: legalEntity?.name,
      location_id: employee.location_id,
      location_name: location?.name,
      cost_center_id: employee.cost_center_id,
      cost_center_name: costCenter?.name,
      job_position_id: employee.job_position_id,
      job_position_title: jobPosition?.title,
      grade_band_id: employee.grade_band_id,
      grade_band_name: gradeBand?.name,
      matrix_manager_employee_ids: [...employee.matrix_manager_employee_ids],
      matrix_manager_names: matrixManagers.map((row) => `${row.first_name} ${row.last_name}`.trim()),
      cost_allocations: employee.cost_allocations.map((allocation) => ({ ...allocation })),
      updated_at: employee.updated_at,
    };
  }

  private toOrganizationReadModel(employee: Employee): OrganizationStructureReadModel {
    const department = this.findDepartmentById(employee.department_id);
    const role = this.findRoleById(employee.role_id);
    const manager = employee.manager_employee_id ? this.findById(employee.manager_employee_id) : null;
    const head = department?.head_employee_id ? this.findById(department.head_employee_id) : null;
    const businessUnit = employee.business_unit_id ? this.findBusinessUnitById(employee.business_unit_id) : null;
    const legalEntity = employee.legal_entity_id ? this.findLegalEntityById(employee.legal_entity_id) : null;
    const location = employee.location_id ? this.findLocationById(employee.location_id) : null;
    const costCenter = employee.cost_center_id ? this.findCostCenterById(employee.cost_center_id) : null;
    const jobPosition = employee.job_position_id ? this.findJobPositionById(employee.job_position_id) : null;
    const gradeBand = employee.grade_band_id ? this.findGradeBandById(employee.grade_band_id) : null;
    const matrixManagerNames = employee.matrix_manager_employee_ids
      .map((managerEmployeeId) => this.findById(managerEmployeeId))
      .filter((row): row is Employee => Boolean(row))
      .map((row) => `${row.first_name} ${row.last_name}`.trim());

    return {
      tenant_id: employee.tenant_id,
      department_id: employee.department_id,
      department_name: department?.name ?? 'Unknown Department',
      department_code: department?.code ?? 'UNKNOWN',
      department_status: department?.status ?? 'Archived',
      head_employee_id: department?.head_employee_id,
      head_employee_name: head ? `${head.first_name} ${head.last_name}`.trim() : undefined,
      employee_id: employee.employee_id,
      employee_name: `${employee.first_name} ${employee.last_name}`.trim(),
      employee_status: employee.status,
      manager_employee_id: employee.manager_employee_id,
      manager_name: manager ? `${manager.first_name} ${manager.last_name}`.trim() : undefined,
      role_id: employee.role_id,
      role_title: role?.title ?? 'Unknown Role',
      business_unit_id: employee.business_unit_id,
      business_unit_name: businessUnit?.name,
      legal_entity_id: employee.legal_entity_id,
      legal_entity_name: legalEntity?.name,
      location_id: employee.location_id,
      location_name: location?.name,
      cost_center_id: employee.cost_center_id,
      cost_center_name: costCenter?.name,
      job_position_id: employee.job_position_id,
      job_position_title: jobPosition?.title,
      grade_band_id: employee.grade_band_id,
      grade_band_name: gradeBand?.name,
      matrix_manager_names: matrixManagerNames,
      updated_at: employee.updated_at,
    };
  }

  private toReportingReadModel(employee: Employee): EmployeeReportingReadModel {
    const primaryManager = employee.manager_employee_id ? this.findById(employee.manager_employee_id) : null;
    const reportingLines: ReportingLine[] = [];
    if (employee.manager_employee_id) {
      reportingLines.push({
        reporting_line_id: `${employee.employee_id}:primary:${employee.manager_employee_id}`,
        tenant_id: employee.tenant_id,
        employee_id: employee.employee_id,
        manager_employee_id: employee.manager_employee_id,
        relationship_type: 'Primary',
        created_at: employee.created_at,
        updated_at: employee.updated_at,
      });
    }
    for (const matrixManagerEmployeeId of employee.matrix_manager_employee_ids) {
      reportingLines.push({
        reporting_line_id: `${employee.employee_id}:matrix:${matrixManagerEmployeeId}`,
        tenant_id: employee.tenant_id,
        employee_id: employee.employee_id,
        manager_employee_id: matrixManagerEmployeeId,
        relationship_type: 'Matrix',
        created_at: employee.created_at,
        updated_at: employee.updated_at,
      });
    }

    return {
      tenant_id: employee.tenant_id,
      employee_id: employee.employee_id,
      primary_manager_employee_id: employee.manager_employee_id,
      primary_manager_name: primaryManager ? `${primaryManager.first_name} ${primaryManager.last_name}`.trim() : undefined,
      matrix_managers: employee.matrix_manager_employee_ids.map((managerEmployeeId) => {
        const manager = this.findById(managerEmployeeId);
        return {
          employee_id: managerEmployeeId,
          manager_name: manager ? `${manager.first_name} ${manager.last_name}`.trim() : undefined,
        };
      }),
      reporting_lines: reportingLines,
      updated_at: employee.updated_at,
    };
  }

  private rebuildIndexes(): void {
    this.employeeNumberIndex.clear();
    this.emailIndex.clear();
    this.departmentIndex.clear();
    this.roleIndex.clear();
    this.statusIndex.clear();
    this.managerIndex.clear();
    this.matrixManagerIndex.clear();
    this.businessUnitIndex.clear();
    this.legalEntityIndex.clear();
    this.locationIndex.clear();
    this.costCenterIndex.clear();
    this.jobPositionIndex.clear();
    this.gradeBandIndex.clear();

    for (const employee of this.employees.values()) {
      this.reindexEmployee(null, employee);
    }
  }

  private reindexEmployee(previous: Employee | null, next: Employee | null): void {
    if (previous) {
      this.employeeNumberIndex.delete(previous.employee_number);
      this.emailIndex.delete(previous.email);
      this.removeFromIndex(this.departmentIndex, previous.department_id, previous.employee_id);
      this.removeFromIndex(this.roleIndex, previous.role_id, previous.employee_id);
      this.removeFromIndex(this.statusIndex, previous.status, previous.employee_id);
      if (previous.manager_employee_id) {
        this.removeFromIndex(this.managerIndex, previous.manager_employee_id, previous.employee_id);
      }
      for (const managerEmployeeId of previous.matrix_manager_employee_ids) {
        this.removeFromIndex(this.matrixManagerIndex, managerEmployeeId, previous.employee_id);
      }
      this.removeOptionalIndex(this.businessUnitIndex, previous.business_unit_id, previous.employee_id);
      this.removeOptionalIndex(this.legalEntityIndex, previous.legal_entity_id, previous.employee_id);
      this.removeOptionalIndex(this.locationIndex, previous.location_id, previous.employee_id);
      this.removeOptionalIndex(this.costCenterIndex, previous.cost_center_id, previous.employee_id);
      this.removeOptionalIndex(this.jobPositionIndex, previous.job_position_id, previous.employee_id);
      this.removeOptionalIndex(this.gradeBandIndex, previous.grade_band_id, previous.employee_id);
    }

    if (next) {
      this.employeeNumberIndex.set(next.employee_number, next.employee_id);
      this.emailIndex.set(next.email, next.employee_id);
      this.addToIndex(this.departmentIndex, next.department_id, next.employee_id);
      this.addToIndex(this.roleIndex, next.role_id, next.employee_id);
      this.addToIndex(this.statusIndex, next.status, next.employee_id);
      if (next.manager_employee_id) {
        this.addToIndex(this.managerIndex, next.manager_employee_id, next.employee_id);
      }
      for (const managerEmployeeId of next.matrix_manager_employee_ids) {
        this.addToIndex(this.matrixManagerIndex, managerEmployeeId, next.employee_id);
      }
      this.addOptionalIndex(this.businessUnitIndex, next.business_unit_id, next.employee_id);
      this.addOptionalIndex(this.legalEntityIndex, next.legal_entity_id, next.employee_id);
      this.addOptionalIndex(this.locationIndex, next.location_id, next.employee_id);
      this.addOptionalIndex(this.costCenterIndex, next.cost_center_id, next.employee_id);
      this.addOptionalIndex(this.jobPositionIndex, next.job_position_id, next.employee_id);
      this.addOptionalIndex(this.gradeBandIndex, next.grade_band_id, next.employee_id);
    }
  }

  private collectCandidateIds(filters: EmployeeFilters): string[] {
    if (filters.employee_id) {
      return this.employees.has(filters.employee_id) ? [filters.employee_id] : [];
    }
    if (filters.manager_employee_id) {
      return [...new Set<string>([
        ...(this.managerIndex.get(filters.manager_employee_id) ?? new Set<string>()),
        ...(this.matrixManagerIndex.get(filters.manager_employee_id) ?? new Set<string>()),
      ])];
    }
    if (filters.department_id) {
      return [...(this.departmentIndex.get(filters.department_id) ?? new Set<string>())];
    }
    if (filters.role_id) {
      return [...(this.roleIndex.get(filters.role_id) ?? new Set<string>())];
    }
    if (filters.business_unit_id) {
      return [...(this.businessUnitIndex.get(filters.business_unit_id) ?? new Set<string>())];
    }
    if (filters.legal_entity_id) {
      return [...(this.legalEntityIndex.get(filters.legal_entity_id) ?? new Set<string>())];
    }
    if (filters.location_id) {
      return [...(this.locationIndex.get(filters.location_id) ?? new Set<string>())];
    }
    if (filters.cost_center_id) {
      return [...(this.costCenterIndex.get(filters.cost_center_id) ?? new Set<string>())];
    }
    if (filters.job_position_id) {
      return [...(this.jobPositionIndex.get(filters.job_position_id) ?? new Set<string>())];
    }
    if (filters.grade_band_id) {
      return [...(this.gradeBandIndex.get(filters.grade_band_id) ?? new Set<string>())];
    }
    if (filters.status) {
      return [...(this.statusIndex.get(filters.status) ?? new Set<string>())];
    }
    return [...this.employees.keys()];
  }

  private resolveExpectedIndex(filters: EmployeeFilters): string {
    if (filters.employee_id) {
      return 'idx_employees_tenant_id + pk_employees';
    }
    if (filters.manager_employee_id) {
      return 'idx_employees_manager_employee_id';
    }
    if (filters.department_id) {
      return 'idx_employees_department_id';
    }
    if (filters.role_id) {
      return 'idx_employees_role_id';
    }
    if (filters.status) {
      return 'idx_employees_status';
    }
    return 'idx_employees_tenant_id';
  }

  private invalidateEmployeeCache(employeeId: string): void {
    this.cache.invalidate(`${EMPLOYEE_CACHE_PREFIX}:by-id:${this.tenantId}:${employeeId}`);
    this.cache.invalidateByPrefix(`${EMPLOYEE_CACHE_PREFIX}:list:${this.tenantId}:`);
  }

  private addToIndex(index: Map<string, Set<string>>, key: string, value: string): void {
    const current = index.get(key) ?? new Set<string>();
    current.add(value);
    index.set(key, current);
  }

  private removeFromIndex(index: Map<string, Set<string>>, key: string, value: string): void {
    const current = index.get(key);
    if (!current) {
      return;
    }
    current.delete(value);
    if (current.size === 0) {
      index.delete(key);
      return;
    }
    index.set(key, current);
  }

  private addOptionalIndex(index: Map<string, Set<string>>, key: string | undefined, value: string): void {
    if (key) {
      this.addToIndex(index, key, value);
    }
  }

  private removeOptionalIndex(index: Map<string, Set<string>>, key: string | undefined, value: string): void {
    if (key) {
      this.removeFromIndex(index, key, value);
    }
  }

  private normalizeCostAllocations(costAllocations: EmployeeCostAllocation[] | undefined, costCenterId: string | undefined): EmployeeCostAllocation[] {
    if (costAllocations && costAllocations.length > 0) {
      return costAllocations.map((allocation, index) => ({
        cost_center_id: allocation.cost_center_id,
        allocation_percentage: allocation.allocation_percentage,
        is_primary: allocation.is_primary ?? (index === 0),
      }));
    }
    if (costCenterId) {
      return [{ cost_center_id: costCenterId, allocation_percentage: 100, is_primary: true }];
    }
    return [];
  }

  private assertTenantFilter(actorTenantId?: string): void {
    if (actorTenantId && actorTenantId !== this.tenantId) {
      throw new Error('TENANT_SCOPE_VIOLATION');
    }
  }

  private matchTenant<T extends { tenant_id: string }>(record: T | null): T | null {
    return record?.tenant_id === this.tenantId ? record : null;
  }
}
