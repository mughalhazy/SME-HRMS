import { randomUUID } from 'node:crypto';
import { CacheService } from '../../cache/cache.service';
import { ConnectionPool, PaginatedResult, QueryOptimizer, applyCursorPagination } from '../../db/optimization';
import { CreateEmployeeInput, Employee, EmployeeFilters, EmployeeStatus, UpdateEmployeeInput } from './employee.model';

const EMPLOYEE_CACHE_PREFIX = 'employees';

export class EmployeeRepository {
  private readonly employees = new Map<string, Employee>();
  private readonly employeeNumberIndex = new Map<string, string>();
  private readonly emailIndex = new Map<string, string>();
  private readonly departmentIndex = new Map<string, Set<string>>();
  private readonly statusIndex = new Map<EmployeeStatus, Set<string>>();
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
      this.addToIndex(this.statusIndex, record.status, record.employee_id);
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

          if (filters.status && employee.status !== filters.status) {
            return false;
          }

          return true;
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
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'employees.updateDepartment', expectedIndex: 'pk_employees' }, () => {
      const employee = this.employees.get(employeeId);

      if (!employee) {
        return null;
      }

      const updated: Employee = {
        ...employee,
        department_id: departmentId,
        updated_at: new Date().toISOString(),
      };

      this.reindexEmployee(employee, updated);
      this.employees.set(employeeId, updated);
      this.invalidateEmployeeCache(employeeId);
      return updated;
    }));
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

  countByDepartmentId(departmentId: string): number {
    return (this.departmentIndex.get(departmentId)?.size ?? 0);
  }

  hasDirectReports(managerEmployeeId: string): boolean {
    return [...this.employees.values()].some((employee) => employee.manager_employee_id === managerEmployeeId);
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
      this.removeFromIndex(this.statusIndex, existing.status, employeeId);
      this.invalidateEmployeeCache(employeeId);
      return true;
    }));
  }

  private collectCandidateIds(filters: EmployeeFilters): string[] {
    if (filters.employee_id) {
      return this.employees.has(filters.employee_id) ? [filters.employee_id] : [];
    }

    if (filters.department_id && filters.status) {
      const departmentIds = this.departmentIndex.get(filters.department_id) ?? new Set<string>();
      const statusIds = this.statusIndex.get(filters.status) ?? new Set<string>();
      return [...departmentIds].filter((employeeId) => statusIds.has(employeeId));
    }

    if (filters.department_id) {
      return [...(this.departmentIndex.get(filters.department_id) ?? new Set<string>())];
    }

    if (filters.status) {
      return [...(this.statusIndex.get(filters.status) ?? new Set<string>())];
    }

    return [...this.employees.keys()];
  }

  private resolveExpectedIndex(filters: EmployeeFilters): string {
    if (filters.employee_id) {
      return 'pk_employees';
    }
    if (filters.department_id && filters.status) {
      return 'idx_employees_department_id + idx_employees_status';
    }
    if (filters.department_id) {
      return 'idx_employees_department_id';
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

    if (previous.status !== next.status) {
      this.removeFromIndex(this.statusIndex, previous.status, previous.employee_id);
      this.addToIndex(this.statusIndex, next.status, next.employee_id);
    }
  }

  private invalidateEmployeeCache(employeeId: string): void {
    this.cache.invalidate(`${EMPLOYEE_CACHE_PREFIX}:by-id:${employeeId}`);
    this.cache.invalidateByPrefix(`${EMPLOYEE_CACHE_PREFIX}:list:`);
  }
}
