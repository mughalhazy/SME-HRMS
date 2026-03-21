import { randomUUID } from 'node:crypto';
import { CacheService } from '../../cache/cache.service';
import { ConnectionPool, PaginatedResult, QueryOptimizer, applyCursorPagination } from '../../db/optimization';
import { PersistentMap } from '../../db/persistent-map';
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
  OrgEntityStatus,
  UpdateBusinessUnitInput,
  UpdateCostCenterInput,
  UpdateGradeBandInput,
  UpdateJobPositionInput,
  UpdateLegalEntityInput,
  UpdateLocationInput,
} from './org.model';
import {
  seedBusinessUnits,
  seedCostCenters,
  seedGradeBands,
  seedJobPositions,
  seedLegalEntities,
  seedLocations,
  DEFAULT_TENANT_ID,
} from './domain-seed';

type OrgRecord = BusinessUnit | LegalEntity | Location | CostCenter | GradeBand | JobPosition;
type CreateInput = CreateBusinessUnitInput | CreateLegalEntityInput | CreateLocationInput | CreateCostCenterInput | CreateGradeBandInput | CreateJobPositionInput;
type UpdateInput = UpdateBusinessUnitInput | UpdateLegalEntityInput | UpdateLocationInput | UpdateCostCenterInput | UpdateGradeBandInput | UpdateJobPositionInput;

const ORG_CACHE_PREFIX = 'employee-service:org';

export class OrgStructureRepository {
  private readonly cache = new CacheService({ ttlMs: 15_000, maxEntries: 2_000 });
  private readonly pool = new ConnectionPool(16);
  private readonly optimizer = new QueryOptimizer(10);

  private readonly businessUnits: PersistentMap<BusinessUnit>;
  private readonly legalEntities: PersistentMap<LegalEntity>;
  private readonly locations: PersistentMap<Location>;
  private readonly costCenters: PersistentMap<CostCenter>;
  private readonly gradeBands: PersistentMap<GradeBand>;
  private readonly jobPositions: PersistentMap<JobPosition>;

  private readonly indexes = {
    business_unit: this.createIndexSet(),
    legal_entity: this.createIndexSet(),
    location: this.createIndexSet(),
    cost_center: this.createIndexSet(),
    grade_band: this.createIndexSet(),
    job_position: this.createIndexSet(),
  };

  constructor(private readonly tenantId: string = DEFAULT_TENANT_ID) {
    this.businessUnits = new PersistentMap<BusinessUnit>(`${ORG_CACHE_PREFIX}:business_units:${tenantId}`);
    this.legalEntities = new PersistentMap<LegalEntity>(`${ORG_CACHE_PREFIX}:legal_entities:${tenantId}`);
    this.locations = new PersistentMap<Location>(`${ORG_CACHE_PREFIX}:locations:${tenantId}`);
    this.costCenters = new PersistentMap<CostCenter>(`${ORG_CACHE_PREFIX}:cost_centers:${tenantId}`);
    this.gradeBands = new PersistentMap<GradeBand>(`${ORG_CACHE_PREFIX}:grade_bands:${tenantId}`);
    this.jobPositions = new PersistentMap<JobPosition>(`${ORG_CACHE_PREFIX}:job_positions:${tenantId}`);

    this.ensureSeeded('business_unit');
    this.ensureSeeded('legal_entity');
    this.ensureSeeded('location');
    this.ensureSeeded('cost_center');
    this.ensureSeeded('grade_band');
    this.ensureSeeded('job_position');
    this.rebuildAllIndexes();
  }

  create(kind: OrgEntityKind, input: CreateInput): OrgRecord {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: `org.${kind}.create` }, () => {
      const config = this.getConfig(kind);
      const timestamp = new Date().toISOString();
      const record = this.buildRecord(kind, input, timestamp);
      config.map.set(String(record[config.idField]), record as never);
      this.rebuildIndexes(kind);
      this.invalidateCache(kind, String(record[config.idField]));
      return record;
    }));
  }

  findById(kind: OrgEntityKind, entityId: string): OrgRecord | null {
    const config = this.getConfig(kind);
    const cacheKey = `${ORG_CACHE_PREFIX}:${kind}:by-id:${this.tenantId}:${entityId}`;
    const cached = this.cache.get<OrgRecord>(cacheKey);
    if (cached) {
      return cached;
    }

    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: `org.${kind}.findById` }, () => {
      const record = (config.map.get(entityId as never) ?? null) as OrgRecord | null;
      if (record && record.tenant_id === this.tenantId) {
        this.cache.set(cacheKey, record);
        return record;
      }
      return null;
    }));
  }

  findByName(kind: OrgEntityKind, name: string): OrgRecord | null {
    const entityId = this.indexes[kind].name.get(name);
    return entityId ? this.findById(kind, entityId) : null;
  }

  findByCode(kind: OrgEntityKind, code: string): OrgRecord | null {
    const entityId = this.indexes[kind].code.get(code);
    return entityId ? this.findById(kind, entityId) : null;
  }

  list(kind: OrgEntityKind, filters: OrgEntityFilters): PaginatedResult<OrgRecord> {
    this.assertTenantFilter(filters.tenant_id);
    const cacheKey = `${ORG_CACHE_PREFIX}:${kind}:list:${this.tenantId}:${JSON.stringify(filters)}`;
    const cached = this.cache.get<PaginatedResult<OrgRecord>>(cacheKey);
    if (cached) {
      return cached;
    }

    const config = this.getConfig(kind);
    const result = this.pool.runWithConnection(() => this.optimizer.execute({ operation: `org.${kind}.list` }, () => {
      const rows = this.collectCandidateIds(kind, filters)
        .map((entityId) => (config.map.get(entityId as never) ?? null) as OrgRecord | null)
        .filter((record): record is OrgRecord => Boolean(record) && record.tenant_id === this.tenantId)
        .filter((record) => this.matchesFilters(kind, record, filters))
        .sort((left, right) => {
          if (left.updated_at === right.updated_at) {
            return String(left[config.idField]).localeCompare(String(right[config.idField]));
          }
          return right.updated_at.localeCompare(left.updated_at);
        });
      return applyCursorPagination(rows.map((row) => ({ ...row, employee_id: String(row[config.idField]), created_at: row.created_at })), { limit: filters.limit, cursor: filters.cursor });
    })) as unknown as PaginatedResult<OrgRecord>;

    this.cache.set(cacheKey, result, { ttlMs: 10_000 });
    return result;
  }

  update(kind: OrgEntityKind, entityId: string, input: UpdateInput): OrgRecord | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: `org.${kind}.update` }, () => {
      const config = this.getConfig(kind);
      const current = this.findById(kind, entityId);
      if (!current) {
        return null;
      }
      const updated: OrgRecord = {
        ...current,
        ...input,
        tenant_id: this.tenantId,
        updated_at: new Date().toISOString(),
      };
      config.map.set(entityId as never, updated as never);
      this.rebuildIndexes(kind);
      this.invalidateCache(kind, entityId);
      return updated;
    }));
  }

  delete(kind: OrgEntityKind, entityId: string): boolean {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: `org.${kind}.delete` }, () => {
      const config = this.getConfig(kind);
      const current = this.findById(kind, entityId);
      if (!current) {
        return false;
      }
      config.map.delete(entityId as never);
      this.rebuildIndexes(kind);
      this.invalidateCache(kind, entityId);
      return true;
    }));
  }

  private ensureSeeded(kind: OrgEntityKind): void {
    const config = this.getConfig(kind);
    if (config.map.keys().length > 0) {
      return;
    }
    for (const record of config.seed(this.tenantId)) {
      config.map.set(String(record[config.idField]), record as never);
    }
  }

  private buildRecord(kind: OrgEntityKind, input: CreateInput, timestamp: string): OrgRecord {
    const tenant_id = this.tenantId;
    if (kind === 'job_position') {
      const position = input as CreateJobPositionInput;
      return {
        tenant_id,
        job_position_id: randomUUID(),
        title: position.title,
        code: position.code,
        department_id: position.department_id,
        business_unit_id: position.business_unit_id,
        legal_entity_id: position.legal_entity_id,
        location_id: position.location_id,
        grade_band_id: position.grade_band_id,
        role_id: position.role_id,
        reports_to_position_id: position.reports_to_position_id,
        default_cost_center_id: position.default_cost_center_id,
        status: position.status ?? 'Draft',
        created_at: timestamp,
        updated_at: timestamp,
      } satisfies JobPosition;
    }

    const named = input as Exclude<CreateInput, CreateJobPositionInput>;
    switch (kind) {
      case 'business_unit':
        return {
          tenant_id,
          business_unit_id: randomUUID(),
          name: named.name,
          code: named.code,
          description: (named as CreateBusinessUnitInput).description,
          parent_business_unit_id: (named as CreateBusinessUnitInput).parent_business_unit_id,
          leader_employee_id: (named as CreateBusinessUnitInput).leader_employee_id,
          status: (named as CreateBusinessUnitInput).status ?? 'Draft',
          created_at: timestamp,
          updated_at: timestamp,
        } satisfies BusinessUnit;
      case 'legal_entity':
        return {
          tenant_id,
          legal_entity_id: randomUUID(),
          name: named.name,
          code: named.code,
          registration_number: (named as CreateLegalEntityInput).registration_number,
          tax_identifier: (named as CreateLegalEntityInput).tax_identifier,
          business_unit_id: (named as CreateLegalEntityInput).business_unit_id,
          status: (named as CreateLegalEntityInput).status ?? 'Draft',
          created_at: timestamp,
          updated_at: timestamp,
        } satisfies LegalEntity;
      case 'location':
        return {
          tenant_id,
          location_id: randomUUID(),
          name: named.name,
          code: named.code,
          address_line_1: (named as CreateLocationInput).address_line_1,
          address_line_2: (named as CreateLocationInput).address_line_2,
          city: (named as CreateLocationInput).city,
          state_or_region: (named as CreateLocationInput).state_or_region,
          postal_code: (named as CreateLocationInput).postal_code,
          country_code: (named as CreateLocationInput).country_code,
          timezone: (named as CreateLocationInput).timezone,
          legal_entity_id: (named as CreateLocationInput).legal_entity_id,
          status: (named as CreateLocationInput).status ?? 'Draft',
          created_at: timestamp,
          updated_at: timestamp,
        } satisfies Location;
      case 'cost_center':
        return {
          tenant_id,
          cost_center_id: randomUUID(),
          name: named.name,
          code: named.code,
          business_unit_id: (named as CreateCostCenterInput).business_unit_id,
          department_id: (named as CreateCostCenterInput).department_id,
          legal_entity_id: (named as CreateCostCenterInput).legal_entity_id,
          manager_employee_id: (named as CreateCostCenterInput).manager_employee_id,
          status: (named as CreateCostCenterInput).status ?? 'Draft',
          created_at: timestamp,
          updated_at: timestamp,
        } satisfies CostCenter;
      case 'grade_band':
        return {
          tenant_id,
          grade_band_id: randomUUID(),
          name: named.name,
          code: named.code,
          family: (named as CreateGradeBandInput).family,
          level_order: (named as CreateGradeBandInput).level_order,
          status: (named as CreateGradeBandInput).status ?? 'Draft',
          created_at: timestamp,
          updated_at: timestamp,
        } satisfies GradeBand;
    }
    throw new Error('unsupported org entity kind');
  }

  private getConfig(kind: OrgEntityKind): any {
    switch (kind) {
      case 'business_unit':
        return { map: this.businessUnits, idField: 'business_unit_id', nameField: 'name', codeField: 'code', managerField: 'leader_employee_id', parentField: 'parent_business_unit_id', seed: seedBusinessUnits };
      case 'legal_entity':
        return { map: this.legalEntities, idField: 'legal_entity_id', nameField: 'name', codeField: 'code', businessUnitField: 'business_unit_id', seed: seedLegalEntities };
      case 'location':
        return { map: this.locations, idField: 'location_id', nameField: 'name', codeField: 'code', legalEntityField: 'legal_entity_id', seed: seedLocations };
      case 'cost_center':
        return { map: this.costCenters, idField: 'cost_center_id', nameField: 'name', codeField: 'code', businessUnitField: 'business_unit_id', departmentField: 'department_id', legalEntityField: 'legal_entity_id', managerField: 'manager_employee_id', seed: seedCostCenters };
      case 'grade_band':
        return { map: this.gradeBands, idField: 'grade_band_id', nameField: 'name', codeField: 'code', seed: seedGradeBands };
      case 'job_position':
        return { map: this.jobPositions, idField: 'job_position_id', nameField: 'title', codeField: 'code', businessUnitField: 'business_unit_id', departmentField: 'department_id', legalEntityField: 'legal_entity_id', parentField: 'reports_to_position_id', seed: seedJobPositions };
    }
  }

  private rebuildAllIndexes(): void {
    this.rebuildIndexes('business_unit');
    this.rebuildIndexes('legal_entity');
    this.rebuildIndexes('location');
    this.rebuildIndexes('cost_center');
    this.rebuildIndexes('grade_band');
    this.rebuildIndexes('job_position');
  }

  private rebuildIndexes(kind: OrgEntityKind): void {
    const config = this.getConfig(kind);
    const index = this.indexes[kind];
    index.name.clear();
    index.code.clear();
    index.status.clear();
    index.businessUnit.clear();
    index.department.clear();
    index.legalEntity.clear();
    index.manager.clear();
    index.parent.clear();

    for (const record of config.map.values() as OrgRecord[]) {
      const entityId = String((record as any)[config.idField]);
      index.name.set(String((record as any)[config.nameField]), entityId);
      index.code.set(String((record as any)[config.codeField]), entityId);
      this.addToIndex(index.status, String(record.status), entityId);
      if (config.businessUnitField && (record as any)[config.businessUnitField]) {
        this.addToIndex(index.businessUnit, String((record as any)[config.businessUnitField]), entityId);
      }
      if (config.departmentField && (record as any)[config.departmentField]) {
        this.addToIndex(index.department, String((record as any)[config.departmentField]), entityId);
      }
      if (config.legalEntityField && (record as any)[config.legalEntityField]) {
        this.addToIndex(index.legalEntity, String((record as any)[config.legalEntityField]), entityId);
      }
      if (config.managerField && (record as any)[config.managerField]) {
        this.addToIndex(index.manager, String((record as any)[config.managerField]), entityId);
      }
      if (config.parentField && (record as any)[config.parentField]) {
        this.addToIndex(index.parent, String((record as any)[config.parentField]), entityId);
      }
    }
  }

  private collectCandidateIds(kind: OrgEntityKind, filters: OrgEntityFilters): string[] {
    const config = this.getConfig(kind);
    const index = this.indexes[kind];
    if (filters.entity_id) {
      return config.map.has(filters.entity_id as never) ? [filters.entity_id] : [];
    }
    if (filters.parent_entity_id) {
      return [...(index.parent.get(filters.parent_entity_id) ?? new Set<string>())];
    }
    if (filters.department_id) {
      return [...(index.department.get(filters.department_id) ?? new Set<string>())];
    }
    if (filters.business_unit_id) {
      return [...(index.businessUnit.get(filters.business_unit_id) ?? new Set<string>())];
    }
    if (filters.legal_entity_id) {
      return [...(index.legalEntity.get(filters.legal_entity_id) ?? new Set<string>())];
    }
    if (filters.manager_employee_id) {
      return [...(index.manager.get(filters.manager_employee_id) ?? new Set<string>())];
    }
    if (filters.status) {
      return [...(index.status.get(filters.status) ?? new Set<string>())];
    }
    return [...config.map.keys()];
  }

  private matchesFilters(kind: OrgEntityKind, record: OrgRecord, filters: OrgEntityFilters): boolean {
    const config = this.getConfig(kind);
    if (filters.status && record.status !== filters.status) {
      return false;
    }
    if (filters.business_unit_id && config.businessUnitField && (record as any)[config.businessUnitField] !== filters.business_unit_id) {
      return false;
    }
    if (filters.department_id && config.departmentField && (record as any)[config.departmentField] !== filters.department_id) {
      return false;
    }
    if (filters.legal_entity_id && config.legalEntityField && (record as any)[config.legalEntityField] !== filters.legal_entity_id) {
      return false;
    }
    if (filters.manager_employee_id && config.managerField && (record as any)[config.managerField] !== filters.manager_employee_id) {
      return false;
    }
    if (filters.parent_entity_id && config.parentField && (record as any)[config.parentField] !== filters.parent_entity_id) {
      return false;
    }
    return true;
  }

  private invalidateCache(kind: OrgEntityKind, entityId: string): void {
    this.cache.invalidate(`${ORG_CACHE_PREFIX}:${kind}:by-id:${this.tenantId}:${entityId}`);
    this.cache.invalidateByPrefix(`${ORG_CACHE_PREFIX}:${kind}:list:${this.tenantId}:`);
  }

  private createIndexSet() {
    return {
      name: new Map<string, string>(),
      code: new Map<string, string>(),
      status: new Map<OrgEntityStatus, Set<string>>(),
      businessUnit: new Map<string, Set<string>>(),
      department: new Map<string, Set<string>>(),
      legalEntity: new Map<string, Set<string>>(),
      manager: new Map<string, Set<string>>(),
      parent: new Map<string, Set<string>>(),
    };
  }

  private addToIndex(index: Map<string, Set<string>>, key: string, value: string): void {
    const current = index.get(key) ?? new Set<string>();
    current.add(value);
    index.set(key, current);
  }

  private assertTenantFilter(actorTenantId?: string): void {
    if (actorTenantId && actorTenantId !== this.tenantId) {
      throw new Error('TENANT_SCOPE_VIOLATION');
    }
  }
}
