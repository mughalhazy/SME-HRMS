import { randomUUID } from 'node:crypto';
import { CacheService } from '../../cache/cache.service';
import { ConnectionPool, QueryOptimizer } from '../../db/optimization';
import { CreateRoleInput, EmploymentCategory, Role, RoleFilters, RoleStatus, UpdateRoleInput, resolveRolePermissions } from './role.model';

const ROLE_CACHE_PREFIX = 'roles';

export class RoleRepository {
  private readonly roles = new Map<string, Role>();
  private readonly titleIndex = new Map<string, string>();
  private readonly statusIndex = new Map<RoleStatus, Set<string>>();
  private readonly categoryIndex = new Map<EmploymentCategory, Set<string>>();
  private readonly employeeRoleIndex = new Map<string, Set<string>>();
  private readonly cache = new CacheService({ ttlMs: 15_000, maxEntries: 1_000 });
  private readonly pool = new ConnectionPool(16);
  private readonly optimizer = new QueryOptimizer(10);

  create(input: CreateRoleInput): Role {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'roles.create' }, () => {
      const timestamp = new Date().toISOString();
      const record: Role = {
        role_id: randomUUID(),
        title: input.title,
        level: input.level,
        description: input.description,
        employment_category: input.employment_category,
        status: input.status ?? 'Draft',
        permissions: resolveRolePermissions(input),
        created_at: timestamp,
        updated_at: timestamp,
      };

      this.roles.set(record.role_id, record);
      this.titleIndex.set(this.normalizeTitle(record.title), record.role_id);
      this.addToIndex(this.statusIndex, record.status, record.role_id);
      this.addToIndex(this.categoryIndex, record.employment_category, record.role_id);
      this.invalidateRoleCache(record.role_id);
      return record;
    }));
  }

  findById(roleId: string): Role | null {
    const cacheKey = `${ROLE_CACHE_PREFIX}:by-id:${roleId}`;
    const cached = this.cache.get<Role>(cacheKey);
    if (cached) {
      return cached;
    }

    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'roles.findById', expectedIndex: 'pk_roles' }, () => {
      const role = this.roles.get(roleId) ?? null;
      if (role) {
        this.cache.set(cacheKey, role);
      }
      return role;
    }));
  }

  findByTitle(title: string): Role | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'roles.findByTitle', expectedIndex: 'uq_roles_title' }, () => {
      const roleId = this.titleIndex.get(this.normalizeTitle(title));
      return roleId ? (this.roles.get(roleId) ?? null) : null;
    }));
  }

  list(filters: RoleFilters = {}): Role[] {
    const cacheKey = `${ROLE_CACHE_PREFIX}:list:${JSON.stringify(filters)}`;
    const cached = this.cache.get<Role[]>(cacheKey);
    if (cached) {
      return cached;
    }

    const result = this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'roles.list', expectedIndex: this.resolveExpectedIndex(filters) }, () => {
      const candidateIds = this.collectCandidateIds(filters);
      return candidateIds
        .map((roleId) => this.roles.get(roleId))
        .filter((role): role is Role => Boolean(role))
        .filter((role) => {
          if (filters.status && role.status !== filters.status) {
            return false;
          }

          if (filters.employment_category && role.employment_category !== filters.employment_category) {
            return false;
          }

          return true;
        })
        .sort((left, right) => left.title.localeCompare(right.title));
    }));

    this.cache.set(cacheKey, result, { ttlMs: 10_000 });
    return result;
  }

  update(roleId: string, input: UpdateRoleInput): Role | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'roles.update', expectedIndex: 'pk_roles' }, () => {
      const existing = this.roles.get(roleId);
      if (!existing) {
        return null;
      }

      const updated: Role = {
        ...existing,
        ...input,
        permissions: resolveRolePermissions({
          employment_category: input.employment_category ?? existing.employment_category,
          permissions: input.permissions ?? existing.permissions,
        }),
        updated_at: new Date().toISOString(),
      };

      this.reindexRole(existing, updated);
      this.roles.set(roleId, updated);
      this.invalidateRoleCache(roleId);
      return updated;
    }));
  }

  delete(roleId: string): boolean {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'roles.delete', expectedIndex: 'pk_roles' }, () => {
      const existing = this.roles.get(roleId);
      if (!existing) {
        return false;
      }

      this.roles.delete(roleId);
      this.titleIndex.delete(this.normalizeTitle(existing.title));
      this.removeFromIndex(this.statusIndex, existing.status, roleId);
      this.removeFromIndex(this.categoryIndex, existing.employment_category, roleId);
      this.employeeRoleIndex.delete(roleId);
      this.invalidateRoleCache(roleId);
      return true;
    }));
  }

  assignEmployee(roleId: string, employeeId: string): void {
    this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'roles.assignEmployee', expectedIndex: 'idx_employees_role_id' }, () => {
      const set = this.employeeRoleIndex.get(roleId) ?? new Set<string>();
      set.add(employeeId);
      this.employeeRoleIndex.set(roleId, set);
      this.invalidateRoleCache(roleId);
    }));
  }

  unassignEmployee(roleId: string, employeeId: string): void {
    this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'roles.unassignEmployee', expectedIndex: 'idx_employees_role_id' }, () => {
      const set = this.employeeRoleIndex.get(roleId);
      if (!set) {
        return;
      }
      set.delete(employeeId);
      if (set.size === 0) {
        this.employeeRoleIndex.delete(roleId);
      }
      this.invalidateRoleCache(roleId);
    }));
  }

  countEmployees(roleId: string): number {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'roles.countEmployees', expectedIndex: 'idx_employees_role_id' }, () => {
      return this.employeeRoleIndex.get(roleId)?.size ?? 0;
    }));
  }

  listEmployeeIds(roleId: string): string[] {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'roles.listEmployeeIds', expectedIndex: 'idx_employees_role_id' }, () => {
      return [...(this.employeeRoleIndex.get(roleId) ?? new Set<string>())].sort();
    }));
  }

  private collectCandidateIds(filters: RoleFilters): string[] {
    if (filters.status && filters.employment_category) {
      const statuses = this.statusIndex.get(filters.status) ?? new Set<string>();
      const categories = this.categoryIndex.get(filters.employment_category) ?? new Set<string>();
      return [...statuses].filter((roleId) => categories.has(roleId));
    }

    if (filters.status) {
      return [...(this.statusIndex.get(filters.status) ?? new Set<string>())];
    }

    if (filters.employment_category) {
      return [...(this.categoryIndex.get(filters.employment_category) ?? new Set<string>())];
    }

    return [...this.roles.keys()];
  }

  private resolveExpectedIndex(filters: RoleFilters): string {
    if (filters.status && filters.employment_category) {
      return 'idx_roles_status + idx_roles_employment_category';
    }
    if (filters.status) {
      return 'idx_roles_status';
    }
    if (filters.employment_category) {
      return 'idx_roles_employment_category';
    }
    return 'pk_roles';
  }

  private normalizeTitle(title: string): string {
    return title.trim().toLowerCase();
  }

  private addToIndex<K>(index: Map<K, Set<string>>, key: K, roleId: string): void {
    const set = index.get(key) ?? new Set<string>();
    set.add(roleId);
    index.set(key, set);
  }

  private removeFromIndex<K>(index: Map<K, Set<string>>, key: K, roleId: string): void {
    const set = index.get(key);
    if (!set) {
      return;
    }
    set.delete(roleId);
    if (set.size === 0) {
      index.delete(key);
    }
  }

  private reindexRole(previous: Role, next: Role): void {
    if (this.normalizeTitle(previous.title) !== this.normalizeTitle(next.title)) {
      this.titleIndex.delete(this.normalizeTitle(previous.title));
      this.titleIndex.set(this.normalizeTitle(next.title), next.role_id);
    }

    if (previous.status !== next.status) {
      this.removeFromIndex(this.statusIndex, previous.status, previous.role_id);
      this.addToIndex(this.statusIndex, next.status, next.role_id);
    }

    if (previous.employment_category !== next.employment_category) {
      this.removeFromIndex(this.categoryIndex, previous.employment_category, previous.role_id);
      this.addToIndex(this.categoryIndex, next.employment_category, next.role_id);
    }
  }

  private invalidateRoleCache(roleId: string): void {
    this.cache.invalidate(`${ROLE_CACHE_PREFIX}:by-id:${roleId}`);
    this.cache.invalidateByPrefix(`${ROLE_CACHE_PREFIX}:list:`);
  }
}
