import { randomUUID } from 'node:crypto';
import { CacheService } from '../../cache/cache.service';
import { PersistentMap } from '../../db/persistent-map';
import { ConnectionPool, QueryOptimizer } from '../../db/optimization';
import {
  AttendanceRule,
  AttendanceRuleFilters,
  AttendanceRuleReadModel,
  CreateAttendanceRuleInput,
  CreateLeavePolicyInput,
  LeavePolicy,
  LeavePolicyFilters,
  LeavePolicyReadModel,
  PayrollSettings,
  PayrollSettingsReadModel,
  SettingsReadModelBundle,
  SettingsStatus,
  TenantConfig,
  UpdateAttendanceRuleInput,
  UpdateLeavePolicyInput,
  UpsertPayrollSettingsInput,
  UpsertTenantConfigInput,
} from './settings.model';

const SETTINGS_CACHE_PREFIX = 'settings';
const DEFAULT_TENANT_ID = 'tenant-default';

export class SettingsRepository {
  private readonly tenantId: string;
  private readonly attendanceRules: PersistentMap<AttendanceRule>;
  private readonly leavePolicies: PersistentMap<LeavePolicy>;
  private readonly tenantConfigs: PersistentMap<TenantConfig>;
  private payrollSettings: PayrollSettings | null = null;

  private readonly attendanceRuleCodeIndex = new Map<string, string>();
  private readonly attendanceRuleStatusIndex = new Map<SettingsStatus, Set<string>>();
  private readonly leavePolicyCodeIndex = new Map<string, string>();
  private readonly leavePolicyTypeIndex = new Map<string, Set<string>>();
  private readonly leavePolicyStatusIndex = new Map<SettingsStatus, Set<string>>();
  private readonly cache = new CacheService({ ttlMs: 15_000, maxEntries: 1_000 });
  private readonly pool = new ConnectionPool(8);
  private readonly optimizer = new QueryOptimizer(10);

  constructor(tenantId: string = DEFAULT_TENANT_ID) {
    this.tenantId = tenantId;
    this.attendanceRules = new PersistentMap<AttendanceRule>(`settings-service:${tenantId}:attendance_rules`);
    this.leavePolicies = new PersistentMap<LeavePolicy>(`settings-service:${tenantId}:leave_policies`);
    this.tenantConfigs = new PersistentMap<TenantConfig>(`settings-service:${tenantId}:tenant_configs`);
    this.rebuildIndexes();
  }

  createAttendanceRule(input: CreateAttendanceRuleInput): AttendanceRule {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.attendanceRules.create', expectedIndex: 'uq_attendance_rules_tenant_code' }, () => {
      const timestamp = new Date().toISOString();
      const record: AttendanceRule = {
        tenant_id: this.tenantId,
        attendance_rule_id: randomUUID(),
        code: input.code,
        name: input.name,
        timezone: input.timezone,
        workdays: [...input.workdays],
        standard_work_hours: input.standard_work_hours,
        grace_period_minutes: input.grace_period_minutes,
        late_after_minutes: input.late_after_minutes,
        auto_clock_out_hours: input.auto_clock_out_hours,
        require_geo_fencing: input.require_geo_fencing ?? false,
        status: input.status ?? 'Draft',
        created_at: timestamp,
        updated_at: timestamp,
      };
      this.attendanceRules.set(record.attendance_rule_id, record);
      this.attendanceRuleCodeIndex.set(record.code, record.attendance_rule_id);
      this.addToIndex(this.attendanceRuleStatusIndex, record.status, record.attendance_rule_id);
      this.invalidateCache();
      return record;
    }));
  }

  updateAttendanceRule(attendanceRuleId: string, input: UpdateAttendanceRuleInput): AttendanceRule | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.attendanceRules.update', expectedIndex: 'pk_attendance_rules + tenant_id' }, () => {
      const current = this.attendanceRules.get(attendanceRuleId);
      if (!current || current.tenant_id !== this.tenantId) {
        return null;
      }
      const updated: AttendanceRule = {
        ...current,
        ...input,
        workdays: input.workdays ? [...input.workdays] : current.workdays,
        tenant_id: this.tenantId,
        updated_at: new Date().toISOString(),
      };
      if (current.status !== updated.status) {
        this.removeFromIndex(this.attendanceRuleStatusIndex, current.status, attendanceRuleId);
        this.addToIndex(this.attendanceRuleStatusIndex, updated.status, attendanceRuleId);
      }
      this.attendanceRules.set(attendanceRuleId, updated);
      this.invalidateCache();
      return updated;
    }));
  }

  findAttendanceRuleById(attendanceRuleId: string): AttendanceRule | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.attendanceRules.findById', expectedIndex: 'pk_attendance_rules + tenant_id' }, () => {
      const rule = this.attendanceRules.get(attendanceRuleId) ?? null;
      return rule?.tenant_id === this.tenantId ? rule : null;
    }));
  }

  findAttendanceRuleByCode(code: string): AttendanceRule | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.attendanceRules.findByCode', expectedIndex: 'uq_attendance_rules_tenant_code' }, () => {
      const attendanceRuleId = this.attendanceRuleCodeIndex.get(code);
      return attendanceRuleId ? this.findAttendanceRuleById(attendanceRuleId) : null;
    }));
  }

  listAttendanceRules(filters: AttendanceRuleFilters = {}): AttendanceRule[] {
    const cacheKey = `${SETTINGS_CACHE_PREFIX}:${this.tenantId}:attendanceRules:${JSON.stringify(filters)}`;
    const cached = this.cache.get<AttendanceRule[]>(cacheKey);
    if (cached) {
      return cached;
    }
    const result = this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.attendanceRules.list', expectedIndex: 'idx_attendance_rules_tenant_status' }, () => {
      const candidateIds = filters.status
        ? [...(this.attendanceRuleStatusIndex.get(filters.status) ?? new Set<string>())]
        : [...this.attendanceRules.keys()];
      return candidateIds
        .map((attendanceRuleId) => this.attendanceRules.get(attendanceRuleId))
        .filter((rule): rule is AttendanceRule => Boolean(rule) && rule.tenant_id === this.tenantId)
        .sort((left, right) => right.updated_at.localeCompare(left.updated_at));
    }));
    this.cache.set(cacheKey, result, { ttlMs: 10_000 });
    return result;
  }

  createLeavePolicy(input: CreateLeavePolicyInput): LeavePolicy {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.leavePolicies.create', expectedIndex: 'uq_leave_policies_tenant_code' }, () => {
      const timestamp = new Date().toISOString();
      const record: LeavePolicy = {
        tenant_id: this.tenantId,
        leave_policy_id: randomUUID(),
        code: input.code,
        name: input.name,
        leave_type: input.leave_type,
        accrual_frequency: input.accrual_frequency,
        accrual_rate_days: input.accrual_rate_days,
        annual_entitlement_days: input.annual_entitlement_days,
        carry_forward_limit_days: input.carry_forward_limit_days,
        requires_approval: input.requires_approval ?? true,
        allow_negative_balance: input.allow_negative_balance ?? false,
        status: input.status ?? 'Draft',
        created_at: timestamp,
        updated_at: timestamp,
      };
      this.leavePolicies.set(record.leave_policy_id, record);
      this.leavePolicyCodeIndex.set(record.code, record.leave_policy_id);
      this.addToIndex(this.leavePolicyTypeIndex, record.leave_type, record.leave_policy_id);
      this.addToIndex(this.leavePolicyStatusIndex, record.status, record.leave_policy_id);
      this.invalidateCache();
      return record;
    }));
  }

  updateLeavePolicy(leavePolicyId: string, input: UpdateLeavePolicyInput): LeavePolicy | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.leavePolicies.update', expectedIndex: 'pk_leave_policies + tenant_id' }, () => {
      const current = this.leavePolicies.get(leavePolicyId);
      if (!current || current.tenant_id !== this.tenantId) {
        return null;
      }
      const updated: LeavePolicy = { ...current, ...input, tenant_id: this.tenantId, updated_at: new Date().toISOString() };
      if (current.status !== updated.status) {
        this.removeFromIndex(this.leavePolicyStatusIndex, current.status, leavePolicyId);
        this.addToIndex(this.leavePolicyStatusIndex, updated.status, leavePolicyId);
      }
      this.leavePolicies.set(leavePolicyId, updated);
      this.invalidateCache();
      return updated;
    }));
  }

  findLeavePolicyById(leavePolicyId: string): LeavePolicy | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.leavePolicies.findById', expectedIndex: 'pk_leave_policies + tenant_id' }, () => {
      const policy = this.leavePolicies.get(leavePolicyId) ?? null;
      return policy?.tenant_id === this.tenantId ? policy : null;
    }));
  }

  findLeavePolicyByCode(code: string): LeavePolicy | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.leavePolicies.findByCode', expectedIndex: 'uq_leave_policies_tenant_code' }, () => {
      const leavePolicyId = this.leavePolicyCodeIndex.get(code);
      return leavePolicyId ? this.findLeavePolicyById(leavePolicyId) : null;
    }));
  }

  listLeavePolicies(filters: LeavePolicyFilters = {}): LeavePolicy[] {
    const cacheKey = `${SETTINGS_CACHE_PREFIX}:${this.tenantId}:leavePolicies:${JSON.stringify(filters)}`;
    const cached = this.cache.get<LeavePolicy[]>(cacheKey);
    if (cached) {
      return cached;
    }
    const result = this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.leavePolicies.list', expectedIndex: 'idx_leave_policies_tenant_type_status' }, () => {
      const candidateIds = filters.leave_type
        ? [...(this.leavePolicyTypeIndex.get(filters.leave_type) ?? new Set<string>())]
        : filters.status
          ? [...(this.leavePolicyStatusIndex.get(filters.status) ?? new Set<string>())]
          : [...this.leavePolicies.keys()];
      return candidateIds
        .map((leavePolicyId) => this.leavePolicies.get(leavePolicyId))
        .filter((policy): policy is LeavePolicy => Boolean(policy) && policy.tenant_id === this.tenantId)
        .filter((policy) => !filters.status || policy.status === filters.status)
        .sort((left, right) => right.updated_at.localeCompare(left.updated_at));
    }));
    this.cache.set(cacheKey, result, { ttlMs: 10_000 });
    return result;
  }

  upsertPayrollSettings(input: UpsertPayrollSettingsInput): PayrollSettings {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.payroll.upsert', expectedIndex: 'idx_payroll_settings_tenant_status' }, () => {
      const timestamp = new Date().toISOString();
      const nextRecord: PayrollSettings = {
        tenant_id: this.tenantId,
        payroll_setting_id: this.payrollSettings?.payroll_setting_id ?? randomUUID(),
        pay_schedule: input.pay_schedule,
        pay_day: input.pay_day,
        currency: input.currency,
        overtime_multiplier: input.overtime_multiplier,
        attendance_cutoff_days: input.attendance_cutoff_days,
        leave_deduction_mode: input.leave_deduction_mode,
        approval_chain: [...input.approval_chain],
        status: input.status ?? 'Active',
        created_at: this.payrollSettings?.created_at ?? timestamp,
        updated_at: timestamp,
      };
      this.payrollSettings = nextRecord;
      this.invalidateCache();
      return nextRecord;
    }));
  }

  getPayrollSettings(): PayrollSettings | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.payroll.get', expectedIndex: 'idx_payroll_settings_tenant_status' }, () => {
      return this.payrollSettings && this.payrollSettings.tenant_id === this.tenantId
        ? { ...this.payrollSettings, approval_chain: [...this.payrollSettings.approval_chain] }
        : null;
    }));
  }

  upsertTenantConfig(input: UpsertTenantConfigInput): TenantConfig {
    const current = this.getTenantConfig();
    const record: TenantConfig = {
      tenant_id: this.tenantId,
      feature_flags: { ...(current?.feature_flags ?? {}), ...(input.feature_flags ?? {}) },
      leave_policy_refs: input.leave_policy_refs ? [...input.leave_policy_refs] : [...(current?.leave_policy_refs ?? [])],
      payroll_rule_refs: input.payroll_rule_refs ? [...input.payroll_rule_refs] : [...(current?.payroll_rule_refs ?? [])],
      locale: input.locale ?? current?.locale ?? 'en-US',
      legal_entity: input.legal_entity ?? current?.legal_entity ?? 'SME HRMS',
      enabled_locations: input.enabled_locations ? [...input.enabled_locations] : [...(current?.enabled_locations ?? [])],
      updated_at: new Date().toISOString(),
    };
    this.tenantConfigs.set(this.tenantId, record);
    this.invalidateCache();
    return record;
  }

  getTenantConfig(): TenantConfig {
    return this.tenantConfigs.get(this.tenantId) ?? {
      tenant_id: this.tenantId,
      feature_flags: {},
      leave_policy_refs: [],
      payroll_rule_refs: [],
      locale: 'en-US',
      legal_entity: 'SME HRMS',
      enabled_locations: [],
      updated_at: new Date(0).toISOString(),
    };
  }

  toReadModelBundle(): SettingsReadModelBundle {
    const attendanceRules = this.listAttendanceRules().map((rule) => this.toAttendanceRuleReadModel(rule));
    const leavePolicies = this.listLeavePolicies().map((policy) => this.toLeavePolicyReadModel(policy));
    const payrollSettings = this.payrollSettings ? this.toPayrollSettingsReadModel(this.payrollSettings) : null;
    const tenantConfiguration = this.getTenantConfig();
    const updatedAtCandidates = [
      ...attendanceRules.map((rule) => rule.updated_at),
      ...leavePolicies.map((policy) => policy.updated_at),
      payrollSettings?.updated_at,
      tenantConfiguration.updated_at,
    ].filter((value): value is string => Boolean(value));
    return {
      settings_configuration_view: {
        tenant_id: this.tenantId,
        attendance_rules: attendanceRules,
        leave_policies: leavePolicies,
        payroll_settings: payrollSettings,
        tenant_configuration: tenantConfiguration,
        updated_at: updatedAtCandidates.sort().at(-1) ?? null,
      },
    };
  }

  toAttendanceRuleReadModel(rule: AttendanceRule): AttendanceRuleReadModel {
    return {
      tenant_id: rule.tenant_id,
      attendance_rule_id: rule.attendance_rule_id,
      code: rule.code,
      name: rule.name,
      schedule_summary: `${rule.workdays.join(', ')} · ${rule.standard_work_hours}h/day · ${rule.timezone}`,
      compliance_summary: `Grace ${rule.grace_period_minutes}m · Late after ${rule.late_after_minutes}m · Geo fencing ${rule.require_geo_fencing ? 'required' : 'optional'}`,
      status: rule.status,
      updated_at: rule.updated_at,
    };
  }

  toLeavePolicyReadModel(policy: LeavePolicy): LeavePolicyReadModel {
    return {
      tenant_id: policy.tenant_id,
      leave_policy_id: policy.leave_policy_id,
      code: policy.code,
      name: policy.name,
      leave_type: policy.leave_type,
      entitlement_summary: `${policy.annual_entitlement_days} days/year · carry forward ${policy.carry_forward_limit_days} days`,
      approval_summary: `${policy.requires_approval ? 'Approval required' : 'Approval optional'} · negative balance ${policy.allow_negative_balance ? 'allowed' : 'blocked'}`,
      status: policy.status,
      updated_at: policy.updated_at,
    };
  }

  toPayrollSettingsReadModel(settings: PayrollSettings): PayrollSettingsReadModel {
    return {
      tenant_id: settings.tenant_id,
      payroll_setting_id: settings.payroll_setting_id,
      pay_schedule: settings.pay_schedule,
      pay_day: settings.pay_day,
      currency: settings.currency,
      payroll_summary: `${settings.pay_schedule} payroll on day ${settings.pay_day} (${settings.currency})`,
      controls_summary: `Overtime x${settings.overtime_multiplier} · cutoff ${settings.attendance_cutoff_days} days · ${settings.leave_deduction_mode}`,
      status: settings.status,
      updated_at: settings.updated_at,
    };
  }

  private rebuildIndexes(): void {
    this.attendanceRuleCodeIndex.clear();
    this.attendanceRuleStatusIndex.clear();
    for (const rule of this.attendanceRules.values()) {
      if (rule.tenant_id !== this.tenantId) continue;
      this.attendanceRuleCodeIndex.set(rule.code, rule.attendance_rule_id);
      this.addToIndex(this.attendanceRuleStatusIndex, rule.status, rule.attendance_rule_id);
    }
    this.leavePolicyCodeIndex.clear();
    this.leavePolicyTypeIndex.clear();
    this.leavePolicyStatusIndex.clear();
    for (const policy of this.leavePolicies.values()) {
      if (policy.tenant_id !== this.tenantId) continue;
      this.leavePolicyCodeIndex.set(policy.code, policy.leave_policy_id);
      this.addToIndex(this.leavePolicyTypeIndex, policy.leave_type, policy.leave_policy_id);
      this.addToIndex(this.leavePolicyStatusIndex, policy.status, policy.leave_policy_id);
    }
  }

  private addToIndex(index: Map<string, Set<string>>, key: string, id: string): void {
    const bucket = index.get(key) ?? new Set<string>();
    bucket.add(id);
    index.set(key, bucket);
  }

  private removeFromIndex(index: Map<string, Set<string>>, key: string, id: string): void {
    const bucket = index.get(key);
    if (!bucket) return;
    bucket.delete(id);
    if (bucket.size === 0) index.delete(key);
  }

  private invalidateCache(): void {
    this.cache.invalidateByPrefix(`${SETTINGS_CACHE_PREFIX}:${this.tenantId}:`);
  }
}
