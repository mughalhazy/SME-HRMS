import { randomUUID } from 'node:crypto';
import { CacheService } from '../../cache/cache.service';
import { ConnectionPool, PaginatedResult, QueryOptimizer, applyCursorPagination } from '../../db/optimization';
import {
  CreateEmployeeInput,
  Department,
  Employee,
  EmployeeDirectoryReadModel,
  EmployeeFilters,
  EmployeeListReadModelBundle,
  EmployeeReadModelBundle,
  EmployeeStatus,
  OrganizationStructureReadModel,
  Role,
  UpdateEmployeeInput,
} from './employee.model';

const EMPLOYEE_CACHE_PREFIX = 'employees';

function timestampSeed(): string {
  return '2026-01-01T00:00:00.000Z';
}

function seedDepartments(): Department[] {
  const createdAt = timestampSeed();
  return [
    {
      department_id: 'dep-hr',
      name: 'People Operations',
      code: 'HR',
      description: 'People operations, talent, and compliance.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      department_id: 'dep-eng',
      name: 'Engineering',
      code: 'ENG',
      description: 'Product engineering and platform delivery.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      department_id: 'dep-fin',
      name: 'Finance',
      code: 'FIN',
      description: 'Financial planning, accounting, and reporting.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      department_id: 'dep-ops',
      name: 'Operations',
      code: 'OPS',
      description: 'Operational readiness and shared services.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      department_id: 'dep-archive',
      name: 'Legacy Programs',
      code: 'LEG',
      description: 'Archived organizational area retained for history.',
      status: 'Archived',
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

function seedRoles(): Role[] {
  const createdAt = timestampSeed();
  return [
    {
      role_id: 'role-hr-director',
      title: 'HR Director',
      level: 'Director',
      description: 'Owns people strategy and HR operations.',
      employment_category: 'Executive',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      role_id: 'role-frontend-engineer',
      title: 'Frontend Engineer',
      level: 'IC3',
      description: 'Builds and maintains UI applications.',
      employment_category: 'Staff',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      role_id: 'role-finance-manager',
      title: 'Finance Manager',
      level: 'M2',
      description: 'Leads the finance operating cadence.',
      employment_category: 'Manager',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      role_id: 'role-ops-lead',
      title: 'Operations Lead',
      level: 'M1',
      description: 'Coordinates operations execution.',
      employment_category: 'Manager',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      role_id: 'role-legacy-contractor',
      title: 'Legacy Contractor',
      level: 'Contract',
      description: 'Retired contract role retained for compatibility.',
      employment_category: 'Contractor',
      status: 'Inactive',
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

export class EmployeeRepository {
  private readonly employees = new Map<string, Employee>();
  private readonly employeeNumberIndex = new Map<string, string>();
  private readonly emailIndex = new Map<string, string>();
  private readonly departmentIndex = new Map<string, Set<string>>();
  private readonly roleIndex = new Map<string, Set<string>>();
  private readonly statusIndex = new Map<EmployeeStatus, Set<string>>();
  private readonly managerIndex = new Map<string, Set<string>>();
  private readonly departments = new Map<string, Department>(seedDepartments().map((department) => [department.department_id, department]));
  private readonly roles = new Map<string, Role>(seedRoles().map((role) => [role.role_id, role]));
  private readonly cache = new CacheService({ ttlMs: 15_000, maxEntries: 1_000 });
  private readonly pool = new ConnectionPool(16);
  private readonly optimizer = new QueryOptimizer(10);

  create(input: CreateEmployeeInput): Employee {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.create' }, () => {
      const timestamp = new Date().toISOString();
      const record: Employee = {
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
        created_at: timestamp,
        updated_at: timestamp,
      };

      this.employees.set(record.employee_id, record);
      this.employeeNumberIndex.set(record.employee_number, record.employee_id);
      this.emailIndex.set(record.email, record.employee_id);
      this.addToIndex(this.departmentIndex, record.department_id, record.employee_id);
      this.addToIndex(this.roleIndex, record.role_id, record.employee_id);
      this.addToIndex(this.statusIndex, record.status, record.employee_id);
      if (record.manager_employee_id) {
        this.addToIndex(this.managerIndex, record.manager_employee_id, record.employee_id);
      }
      this.invalidateEmployeeCache(record.employee_id);
      return record;
    }));
  }

  findById(employeeId: string): Employee | null {
    const cacheKey = `${EMPLOYEE_CACHE_PREFIX}:by-id:${employeeId}`;
    const cached = this.cache.get<Employee>(cacheKey);
    if (cached) {
      return cached;
    }

    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.findById', expectedIndex: 'pk_employees' }, () => {
      const employee = this.employees.get(employeeId) ?? null;
      if (employee) {
        this.cache.set(cacheKey, employee);
      }
      return employee;
    }));
  }

  findByEmployeeNumber(employeeNumber: string): Employee | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.findByEmployeeNumber', expectedIndex: 'uq_employees_employee_number' }, () => {
      const employeeId = this.employeeNumberIndex.get(employeeNumber);
      return employeeId ? (this.employees.get(employeeId) ?? null) : null;
    }));
  }

  findByEmail(email: string): Employee | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.findByEmail', expectedIndex: 'uq_employees_email' }, () => {
      const employeeId = this.emailIndex.get(email);
      return employeeId ? (this.employees.get(employeeId) ?? null) : null;
    }));
  }

  findDepartmentById(departmentId: string): Department | null {
    return this.departments.get(departmentId) ?? null;
  }

  findRoleById(roleId: string): Role | null {
    return this.roles.get(roleId) ?? null;
  }

  list(filters: EmployeeFilters): PaginatedResult<Employee> {
    const cacheKey = `${EMPLOYEE_CACHE_PREFIX}:list:${JSON.stringify(filters)}`;
    const cached = this.cache.get<PaginatedResult<Employee>>(cacheKey);
    if (cached) {
      return cached;
    }

    const result = this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.list', expectedIndex: this.resolveExpectedIndex(filters) }, () => {
      const candidateIds = this.collectCandidateIds(filters);
      const rows = candidateIds
        .map((employeeId) => this.employees.get(employeeId))
        .filter((employee): employee is Employee => Boolean(employee))
        .filter((employee) => {
          if (filters.department_id && employee.department_id !== filters.department_id) {
            return false;
          }

          if (filters.role_id && employee.role_id !== filters.role_id) {
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
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.update', expectedIndex: 'pk_employees' }, () => {
      const employee = this.employees.get(employeeId);

      if (!employee) {
        return null;
      }

      const updated: Employee = {
        ...employee,
        ...input,
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
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.updateStatus', expectedIndex: 'pk_employees' }, () => {
      const employee = this.employees.get(employeeId);

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

  delete(employeeId: string): boolean {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.delete', expectedIndex: 'pk_employees' }, () => {
      const existing = this.employees.get(employeeId);
      if (!existing) {
        return false;
      }

      this.employees.delete(employeeId);
      this.employeeNumberIndex.delete(existing.employee_number);
      this.emailIndex.delete(existing.email);
      this.removeFromIndex(this.departmentIndex, existing.department_id, employeeId);
      this.removeFromIndex(this.roleIndex, existing.role_id, employeeId);
      this.removeFromIndex(this.statusIndex, existing.status, employeeId);
      if (existing.manager_employee_id) {
        this.removeFromIndex(this.managerIndex, existing.manager_employee_id, employeeId);
      }
      this.invalidateEmployeeCache(employeeId);
      return true;
    }));
  }

  hasDirectReports(employeeId: string): boolean {
    return (this.managerIndex.get(employeeId)?.size ?? 0) > 0;
  }

  toReadModelBundle(employee: Employee): EmployeeReadModelBundle {
    return {
      employee_directory_view: this.toEmployeeDirectoryReadModel(employee),
      organization_structure_view: this.toOrganizationStructureReadModel(employee),
    };
  }

  toReadModelListBundle(employees: Employee[]): EmployeeListReadModelBundle {
    return {
      employee_directory_view: employees.map((employee) => this.toEmployeeDirectoryReadModel(employee)),
      organization_structure_view: employees.map((employee) => this.toOrganizationStructureReadModel(employee)),
    };
  }

  private toEmployeeDirectoryReadModel(employee: Employee): EmployeeDirectoryReadModel {
    const department = this.departments.get(employee.department_id);
    const role = this.roles.get(employee.role_id);
    const manager = employee.manager_employee_id ? this.employees.get(employee.manager_employee_id) : undefined;

    return {
      employee_id: employee.employee_id,
      employee_number: employee.employee_number,
      full_name: this.toFullName(employee.first_name, employee.last_name),
      email: employee.email,
      phone: employee.phone,
      hire_date: employee.hire_date,
      employment_type: employee.employment_type,
      employee_status: employee.status,
      department_id: employee.department_id,
      department_name: department?.name ?? employee.department_id,
      role_id: employee.role_id,
      role_title: role?.title ?? employee.role_id,
      manager_employee_id: employee.manager_employee_id,
      manager_name: manager ? this.toFullName(manager.first_name, manager.last_name) : undefined,
      updated_at: employee.updated_at,
    };
  }

  private toOrganizationStructureReadModel(employee: Employee): OrganizationStructureReadModel {
    const department = this.departments.get(employee.department_id);
    const role = this.roles.get(employee.role_id);
    const manager = employee.manager_employee_id ? this.employees.get(employee.manager_employee_id) : undefined;
    const head = department?.head_employee_id ? this.employees.get(department.head_employee_id) : undefined;

    return {
      department_id: employee.department_id,
      department_name: department?.name ?? employee.department_id,
      department_code: department?.code ?? employee.department_id,
      department_status: department?.status ?? 'Archived',
      head_employee_id: department?.head_employee_id,
      head_employee_name: head ? this.toFullName(head.first_name, head.last_name) : undefined,
      employee_id: employee.employee_id,
      employee_name: this.toFullName(employee.first_name, employee.last_name),
      employee_status: employee.status,
      manager_employee_id: employee.manager_employee_id,
      manager_name: manager ? this.toFullName(manager.first_name, manager.last_name) : undefined,
      role_id: employee.role_id,
      role_title: role?.title ?? employee.role_id,
      updated_at: employee.updated_at,
    };
  }

  private collectCandidateIds(filters: EmployeeFilters): string[] {
    if (filters.employee_id) {
      return this.employees.has(filters.employee_id) ? [filters.employee_id] : [];
    }

    const candidateSets: Set<string>[] = [];

    if (filters.department_id) {
      candidateSets.push(this.departmentIndex.get(filters.department_id) ?? new Set<string>());
    }

    if (filters.role_id) {
      candidateSets.push(this.roleIndex.get(filters.role_id) ?? new Set<string>());
    }

    if (filters.status) {
      candidateSets.push(this.statusIndex.get(filters.status) ?? new Set<string>());
    }

    if (candidateSets.length === 0) {
      return [...this.employees.keys()];
    }

    return [...candidateSets.slice(1).reduce((intersection, current) => {
      return new Set([...intersection].filter((employeeId) => current.has(employeeId)));
    }, candidateSets[0])];
  }

  private resolveExpectedIndex(filters: EmployeeFilters): string {
    if (filters.employee_id) {
      return 'pk_employees';
    }
    if (filters.department_id && filters.role_id && filters.status) {
      return 'idx_employees_department_id + idx_employees_role_id + idx_employees_status';
    }
    if (filters.department_id && filters.role_id) {
      return 'idx_employees_department_id + idx_employees_role_id';
    }
    if (filters.department_id && filters.status) {
      return 'idx_employees_department_id + idx_employees_status';
    }
    if (filters.role_id && filters.status) {
      return 'idx_employees_role_id + idx_employees_status';
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
    return 'pk_employees';
  }

  private addToIndex<K>(index: Map<K, Set<string>>, key: K, employeeId: string): void {
    const set = index.get(key) ?? new Set<string>();
    set.add(employeeId);
    index.set(key, set);
  }

  private removeFromIndex<K>(index: Map<K, Set<string>>, key: K, employeeId: string): void {
    const set = index.get(key);
    if (!set) {
      return;
    }
    set.delete(employeeId);
    if (set.size === 0) {
      index.delete(key);
    }
  }

  private reindexEmployee(previous: Employee, next: Employee): void {
    if (previous.employee_number !== next.employee_number) {
      this.employeeNumberIndex.delete(previous.employee_number);
      this.employeeNumberIndex.set(next.employee_number, next.employee_id);
    }

    if (previous.email !== next.email) {
      this.emailIndex.delete(previous.email);
      this.emailIndex.set(next.email, next.employee_id);
    }

    if (previous.department_id !== next.department_id) {
      this.removeFromIndex(this.departmentIndex, previous.department_id, previous.employee_id);
      this.addToIndex(this.departmentIndex, next.department_id, next.employee_id);
    }

    if (previous.role_id !== next.role_id) {
      this.removeFromIndex(this.roleIndex, previous.role_id, previous.employee_id);
      this.addToIndex(this.roleIndex, next.role_id, next.employee_id);
    }

    if (previous.status !== next.status) {
      this.removeFromIndex(this.statusIndex, previous.status, previous.employee_id);
      this.addToIndex(this.statusIndex, next.status, next.employee_id);
    }

    if (previous.manager_employee_id !== next.manager_employee_id) {
      if (previous.manager_employee_id) {
        this.removeFromIndex(this.managerIndex, previous.manager_employee_id, previous.employee_id);
      }
      if (next.manager_employee_id) {
        this.addToIndex(this.managerIndex, next.manager_employee_id, next.employee_id);
      }
    }
  }

  private invalidateEmployeeCache(employeeId: string): void {
    this.cache.invalidate(`${EMPLOYEE_CACHE_PREFIX}:by-id:${employeeId}`);
    this.cache.invalidateByPrefix(`${EMPLOYEE_CACHE_PREFIX}:list:`);
  }

  private toFullName(firstName: string, lastName: string): string {
    return `${firstName} ${lastName}`.trim();
  }
}
