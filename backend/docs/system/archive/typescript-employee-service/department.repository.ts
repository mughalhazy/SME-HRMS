import { randomUUID } from 'node:crypto';
import { CacheService } from '../../cache/cache.service';
import { ConnectionPool, PaginatedResult, QueryOptimizer, applyCursorPagination } from '../../db/optimization';
import { PersistentMap } from '../../db/persistent-map';
import { CreateDepartmentInput, Department, DepartmentFilters, DepartmentStatus, UpdateDepartmentInput } from './department.model';
import { DEFAULT_TENANT_ID, seedDepartments } from './domain-seed';

const DEPARTMENT_CACHE_PREFIX = 'departments';

export class DepartmentRepository {
  private readonly departments: PersistentMap<Department>;
  private readonly nameIndex = new Map<string, string>();
  private readonly codeIndex = new Map<string, string>();
  private readonly statusIndex = new Map<DepartmentStatus, Set<string>>();
  private readonly parentDepartmentIndex = new Map<string, Set<string>>();
  private readonly headEmployeeIndex = new Map<string, string>();
  private readonly cache = new CacheService({ ttlMs: 15_000, maxEntries: 1_000 });
  private readonly pool = new ConnectionPool(16);
  private readonly optimizer = new QueryOptimizer(10);

  constructor(
    private readonly tenantId: string = DEFAULT_TENANT_ID,
    seedData: Department[] = seedDepartments(tenantId),
  ) {
    this.departments = new PersistentMap<Department>(`employee-service:departments:${this.tenantId}`);
    if (this.departments.keys().length > 0) {
      this.rebuildIndexes();
      return;
    }
    for (const department of seedData) {
      if (department.tenant_id !== this.tenantId) {
        continue;
      }
      this.departments.set(department.department_id, { ...department });
      this.nameIndex.set(department.name, department.department_id);
      this.codeIndex.set(department.code, department.department_id);
      this.addToIndex(this.statusIndex, department.status, department.department_id);
      if (department.parent_department_id) {
        this.addToIndex(this.parentDepartmentIndex, department.parent_department_id, department.department_id);
      }
      if (department.head_employee_id) {
        this.headEmployeeIndex.set(department.head_employee_id, department.department_id);
      }
    }
    this.rebuildIndexes();
  }

  create(input: CreateDepartmentInput): Department {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'departments.create' }, () => {
      const timestamp = new Date().toISOString();
      const record: Department = {
        tenant_id: this.tenantId,
        department_id: randomUUID(),
        name: input.name,
        code: input.code,
        description: input.description,
        parent_department_id: input.parent_department_id,
        head_employee_id: input.head_employee_id,
        status: input.status ?? 'Proposed',
        created_at: timestamp,
        updated_at: timestamp,
      };

      this.departments.set(record.department_id, record);
      this.nameIndex.set(record.name, record.department_id);
      this.codeIndex.set(record.code, record.department_id);
      this.addToIndex(this.statusIndex, record.status, record.department_id);
      if (record.parent_department_id) {
        this.addToIndex(this.parentDepartmentIndex, record.parent_department_id, record.department_id);
      }
      if (record.head_employee_id) {
        this.headEmployeeIndex.set(record.head_employee_id, record.department_id);
      }
      this.invalidateDepartmentCache(record.department_id);
      return record;
    }));
  }

  findById(departmentId: string): Department | null {
    const cacheKey = `${DEPARTMENT_CACHE_PREFIX}:by-id:${this.tenantId}:${departmentId}`;
    const cached = this.cache.get<Department>(cacheKey);
    if (cached) {
      return cached;
    }

    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'departments.findById', expectedIndex: 'idx_departments_tenant_id + pk_departments' }, () => {
      const department = this.departments.get(departmentId) ?? null;
      if (department && department.tenant_id === this.tenantId) {
        this.cache.set(cacheKey, department);
        return department;
      }
      return null;
    }));
  }

  findByName(name: string): Department | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'departments.findByName', expectedIndex: 'uq_departments_tenant_name' }, () => {
      const departmentId = this.nameIndex.get(name);
      return departmentId ? this.findById(departmentId) : null;
    }));
  }

  findByCode(code: string): Department | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'departments.findByCode', expectedIndex: 'uq_departments_tenant_code' }, () => {
      const departmentId = this.codeIndex.get(code);
      return departmentId ? this.findById(departmentId) : null;
    }));
  }

  findByHeadEmployeeId(employeeId: string): Department | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'departments.findByHeadEmployeeId', expectedIndex: 'idx_departments_tenant_head_employee_id' }, () => {
      const departmentId = this.headEmployeeIndex.get(employeeId);
      return departmentId ? this.findById(departmentId) : null;
    }));
  }

  list(filters: DepartmentFilters): PaginatedResult<Department> {
    this.assertTenantFilter(filters.tenant_id);
    const cacheKey = `${DEPARTMENT_CACHE_PREFIX}:list:${this.tenantId}:${JSON.stringify(filters)}`;
    const cached = this.cache.get<PaginatedResult<Department>>(cacheKey);
    if (cached) {
      return cached;
    }

    const result = this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'departments.list', expectedIndex: this.resolveExpectedIndex(filters) }, () => {
      const candidateIds = this.collectCandidateIds(filters);
      const rows = candidateIds
        .map((departmentId) => this.departments.get(departmentId))
        .filter((department): department is Department => Boolean(department) && department.tenant_id === this.tenantId)
        .filter((department) => {
          if (filters.status && department.status !== filters.status) {
            return false;
          }

          if (filters.parent_department_id && department.parent_department_id !== filters.parent_department_id) {
            return false;
          }

          if (filters.head_employee_id && department.head_employee_id !== filters.head_employee_id) {
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

  update(departmentId: string, input: UpdateDepartmentInput): Department | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'departments.update', expectedIndex: 'idx_departments_tenant_id + pk_departments' }, () => {
      const department = this.findById(departmentId);
      if (!department) {
        return null;
      }

      const updated: Department = {
        ...department,
        ...input,
        tenant_id: this.tenantId,
        updated_at: new Date().toISOString(),
      };

      this.reindexDepartment(department, updated);
      this.departments.set(departmentId, updated);
      this.invalidateDepartmentCache(departmentId);
      return updated;
    }));
  }

  delete(departmentId: string): boolean {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'departments.delete', expectedIndex: 'idx_departments_tenant_id + pk_departments' }, () => {
      const existing = this.findById(departmentId);
      if (!existing) {
        return false;
      }

      this.departments.delete(departmentId);
      this.nameIndex.delete(existing.name);
      this.codeIndex.delete(existing.code);
      this.removeFromIndex(this.statusIndex, existing.status, departmentId);
      if (existing.parent_department_id) {
        this.removeFromIndex(this.parentDepartmentIndex, existing.parent_department_id, departmentId);
      }
      if (existing.head_employee_id) {
        this.headEmployeeIndex.delete(existing.head_employee_id);
      }
      this.invalidateDepartmentCache(departmentId);
      return true;
    }));
  }

  hasChildren(departmentId: string): boolean {
    return (this.parentDepartmentIndex.get(departmentId)?.size ?? 0) > 0;
  }


  private rebuildIndexes(): void {
    this.nameIndex.clear();
    this.codeIndex.clear();
    this.statusIndex.clear();
    this.parentDepartmentIndex.clear();
    this.headEmployeeIndex.clear();
    for (const department of this.departments.values()) {
      this.nameIndex.set(department.name, department.department_id);
      this.codeIndex.set(department.code, department.department_id);
      this.addToIndex(this.statusIndex, department.status, department.department_id);
      if (department.parent_department_id) {
        this.addToIndex(this.parentDepartmentIndex, department.parent_department_id, department.department_id);
      }
      if (department.head_employee_id) {
        this.headEmployeeIndex.set(department.head_employee_id, department.department_id);
      }
    }
  }

  private collectCandidateIds(filters: DepartmentFilters): string[] {
    if (filters.department_id) {
      return this.departments.has(filters.department_id) ? [filters.department_id] : [];
    }

    if (filters.head_employee_id) {
      const departmentId = this.headEmployeeIndex.get(filters.head_employee_id);
      return departmentId ? [departmentId] : [];
    }

    if (filters.parent_department_id && filters.status) {
      const parentIds = this.parentDepartmentIndex.get(filters.parent_department_id) ?? new Set<string>();
      const statusIds = this.statusIndex.get(filters.status) ?? new Set<string>();
      return [...parentIds].filter((departmentId) => statusIds.has(departmentId));
    }

    if (filters.parent_department_id) {
      return [...(this.parentDepartmentIndex.get(filters.parent_department_id) ?? new Set<string>())];
    }

    if (filters.status) {
      return [...(this.statusIndex.get(filters.status) ?? new Set<string>())];
    }

    return [...this.departments.keys()];
  }

  private resolveExpectedIndex(filters: DepartmentFilters): string {
    if (filters.department_id) {
      return 'idx_departments_tenant_id + pk_departments';
    }
    if (filters.head_employee_id) {
      return 'idx_departments_tenant_head_employee_id';
    }
    if (filters.parent_department_id && filters.status) {
      return 'idx_departments_tenant_parent_department_id + idx_departments_tenant_status';
    }
    if (filters.parent_department_id) {
      return 'idx_departments_tenant_parent_department_id';
    }
    if (filters.status) {
      return 'idx_departments_tenant_status';
    }
    return 'idx_departments_tenant_id';
  }

  private assertTenantFilter(tenantId?: string): void {
    if (tenantId && tenantId !== this.tenantId) {
      throw new Error('cross_tenant_filter_blocked');
    }
    this.rebuildIndexes();
  }

  private addToIndex<K>(index: Map<K, Set<string>>, key: K, departmentId: string): void {
    const set = index.get(key) ?? new Set<string>();
    set.add(departmentId);
    index.set(key, set);
  }

  private removeFromIndex<K>(index: Map<K, Set<string>>, key: K, departmentId: string): void {
    const set = index.get(key);
    if (!set) {
      return;
    }
    set.delete(departmentId);
    if (set.size === 0) {
      index.delete(key);
    }
    this.rebuildIndexes();
  }

  private reindexDepartment(previous: Department, next: Department): void {
    if (previous.name !== next.name) {
      this.nameIndex.delete(previous.name);
      this.nameIndex.set(next.name, next.department_id);
    }

    if (previous.code !== next.code) {
      this.codeIndex.delete(previous.code);
      this.codeIndex.set(next.code, next.department_id);
    }

    if (previous.status !== next.status) {
      this.removeFromIndex(this.statusIndex, previous.status, previous.department_id);
      this.addToIndex(this.statusIndex, next.status, next.department_id);
    }

    if (previous.parent_department_id !== next.parent_department_id) {
      if (previous.parent_department_id) {
        this.removeFromIndex(this.parentDepartmentIndex, previous.parent_department_id, previous.department_id);
      }
      if (next.parent_department_id) {
        this.addToIndex(this.parentDepartmentIndex, next.parent_department_id, next.department_id);
      }
    }

    if (previous.head_employee_id !== next.head_employee_id) {
      if (previous.head_employee_id) {
        this.headEmployeeIndex.delete(previous.head_employee_id);
      }
      if (next.head_employee_id) {
        this.headEmployeeIndex.set(next.head_employee_id, next.department_id);
      }
    }
    this.rebuildIndexes();
  }

  private invalidateDepartmentCache(departmentId: string): void {
    this.cache.invalidate(`${DEPARTMENT_CACHE_PREFIX}:by-id:${this.tenantId}:${departmentId}`);
    this.cache.invalidateByPrefix(`${DEPARTMENT_CACHE_PREFIX}:list:${this.tenantId}:`);
  }
}
