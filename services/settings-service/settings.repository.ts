import { randomUUID } from 'node:crypto';
import { CacheService } from '../../cache/cache.service';
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
  UpdateAttendanceRuleInput,
  UpdateLeavePolicyInput,
  UpsertPayrollSettingsInput,
} from './settings.model';

const SETTINGS_CACHE_PREFIX = 'settings';

export class SettingsRepository {
  private readonly attendanceRules = new Map<string, AttendanceRule>();
  private readonly leavePolicies = new Map<string, LeavePolicy>();
  private payrollSettings: PayrollSettings | null = null;

  private readonly attendanceRuleCodeIndex = new Map<string, string>();
  private readonly attendanceRuleStatusIndex = new Map<SettingsStatus, Set<string>>();
  private readonly leavePolicyCodeIndex = new Map<string, string>();
  private readonly leavePolicyTypeIndex = new Map<string, Set<string>>();
  private readonly leavePolicyStatusIndex = new Map<SettingsStatus, Set<string>>();
  private readonly cache = new CacheService({ ttlMs: 15_000, maxEntries: 1_000 });
  private readonly pool = new ConnectionPool(8);
  private readonly optimizer = new QueryOptimizer(10);

  createAttendanceRule(input: CreateAttendanceRuleInput): AttendanceRule {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.attendanceRules.create', expectedIndex: 'uq_attendance_rules_code' }, () => {
      const timestamp = new Date().toISOString();
      const record: AttendanceRule = {
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
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.attendanceRules.update', expectedIndex: 'pk_attendance_rules' }, () => {
      const current = this.attendanceRules.get(attendanceRuleId);
      if (!current) {
        return null;
      }

      const updated: AttendanceRule = {
        ...current,
        ...input,
        workdays: input.workdays ? [...input.workdays] : current.workdays,
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
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.attendanceRules.findById', expectedIndex: 'pk_attendance_rules' }, () => {
      return this.attendanceRules.get(attendanceRuleId) ?? null;
    }));
  }

  findAttendanceRuleByCode(code: string): AttendanceRule | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.attendanceRules.findByCode', expectedIndex: 'uq_attendance_rules_code' }, () => {
      const attendanceRuleId = this.attendanceRuleCodeIndex.get(code);
      return attendanceRuleId ? (this.attendanceRules.get(attendanceRuleId) ?? null) : null;
    }));
  }

  listAttendanceRules(filters: AttendanceRuleFilters = {}): AttendanceRule[] {
    const cacheKey = `${SETTINGS_CACHE_PREFIX}:attendanceRules:${JSON.stringify(filters)}`;
    const cached = this.cache.get<AttendanceRule[]>(cacheKey);
    if (cached) {
      return cached;
    }

    const result = this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.attendanceRules.list', expectedIndex: 'idx_attendance_rules_status' }, () => {
      const candidateIds = filters.status
        ? [...(this.attendanceRuleStatusIndex.get(filters.status) ?? new Set<string>())]
        : [...this.attendanceRules.keys()];

      return candidateIds
        .map((attendanceRuleId) => this.attendanceRules.get(attendanceRuleId))
        .filter((rule): rule is AttendanceRule => Boolean(rule))
        .sort((left, right) => right.updated_at.localeCompare(left.updated_at));
    }));

    this.cache.set(cacheKey, result, { ttlMs: 10_000 });
    return result;
  }

  createLeavePolicy(input: CreateLeavePolicyInput): LeavePolicy {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.leavePolicies.create', expectedIndex: 'uq_leave_policies_code' }, () => {
      const timestamp = new Date().toISOString();
      const record: LeavePolicy = {
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
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.leavePolicies.update', expectedIndex: 'pk_leave_policies' }, () => {
      const current = this.leavePolicies.get(leavePolicyId);
      if (!current) {
        return null;
      }

      const updated: LeavePolicy = {
        ...current,
        ...input,
        updated_at: new Date().toISOString(),
      };

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
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.leavePolicies.findById', expectedIndex: 'pk_leave_policies' }, () => {
      return this.leavePolicies.get(leavePolicyId) ?? null;
    }));
  }

  findLeavePolicyByCode(code: string): LeavePolicy | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.leavePolicies.findByCode', expectedIndex: 'uq_leave_policies_code' }, () => {
      const leavePolicyId = this.leavePolicyCodeIndex.get(code);
      return leavePolicyId ? (this.leavePolicies.get(leavePolicyId) ?? null) : null;
    }));
  }

  listLeavePolicies(filters: LeavePolicyFilters = {}): LeavePolicy[] {
    const cacheKey = `${SETTINGS_CACHE_PREFIX}:leavePolicies:${JSON.stringify(filters)}`;
    const cached = this.cache.get<LeavePolicy[]>(cacheKey);
    if (cached) {
      return cached;
    }

    const result = this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.leavePolicies.list', expectedIndex: this.resolveLeavePolicyIndex(filters) }, () => {
      const candidateIds = filters.leave_type
        ? [...(this.leavePolicyTypeIndex.get(filters.leave_type) ?? new Set<string>())]
        : filters.status
          ? [...(this.leavePolicyStatusIndex.get(filters.status) ?? new Set<string>())]
          : [...this.leavePolicies.keys()];

      return candidateIds
        .map((leavePolicyId) => this.leavePolicies.get(leavePolicyId))
        .filter((policy): policy is LeavePolicy => Boolean(policy))
        .filter((policy) => !filters.status || policy.status === filters.status)
        .sort((left, right) => right.updated_at.localeCompare(left.updated_at));
    }));

    this.cache.set(cacheKey, result, { ttlMs: 10_000 });
    return result;
  }

  upsertPayrollSettings(input: UpsertPayrollSettingsInput): PayrollSettings {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.payroll.upsert', expectedIndex: 'idx_payroll_settings_status' }, () => {
      const timestamp = new Date().toISOString();
      const nextRecord: PayrollSettings = {
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
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'settings.payroll.get', expectedIndex: 'idx_payroll_settings_status' }, () => {
      return this.payrollSettings ? { ...this.payrollSettings, approval_chain: [...this.payrollSettings.approval_chain] } : null;
    }));
  }

  toReadModelBundle(): SettingsReadModelBundle {
    const attendanceRules = this.listAttendanceRules().map((rule) => this.toAttendanceRuleReadModel(rule));
    const leavePolicies = this.listLeavePolicies().map((policy) => this.toLeavePolicyReadModel(policy));
    const payrollSettings = this.payrollSettings ? this.toPayrollSettingsReadModel(this.payrollSettings) : null;
    const updatedAtCandidates = [
      ...attendanceRules.map((rule) => rule.updated_at),
      ...leavePolicies.map((policy) => policy.updated_at),
      payrollSettings?.updated_at,
    ].filter((value): value is string => Boolean(value));

    return {
      settings_configuration_view: {
        attendance_rules: attendanceRules,
        leave_policies: leavePolicies,
        payroll_settings: payrollSettings,
        updated_at: updatedAtCandidates.length > 0 ? updatedAtCandidates.sort().at(-1) ?? null : null,
      },
    };
  }

  private toAttendanceRuleReadModel(rule: AttendanceRule): AttendanceRuleReadModel {
    return {
      attendance_rule_id: rule.attendance_rule_id,
      code: rule.code,
      name: rule.name,
      schedule_summary: `${rule.workdays.join(', ')} · ${rule.standard_work_hours}h/day`,
      compliance_summary: `${rule.grace_period_minutes}m grace · late after ${rule.late_after_minutes}m${rule.require_geo_fencing ? ' · geo-fencing on' : ''}`,
      status: rule.status,
      updated_at: rule.updated_at,
    };
  }

  private toLeavePolicyReadModel(policy: LeavePolicy): LeavePolicyReadModel {
    return {
      leave_policy_id: policy.leave_policy_id,
      code: policy.code,
      name: policy.name,
      leave_type: policy.leave_type,
      entitlement_summary: `${policy.annual_entitlement_days} days/year · carry forward ${policy.carry_forward_limit_days} days`,
      approval_summary: `${policy.requires_approval ? 'Manager approval required' : 'No approval required'} · ${policy.allow_negative_balance ? 'negative balance allowed' : 'negative balance blocked'}`,
      status: policy.status,
      updated_at: policy.updated_at,
    };
  }

  private toPayrollSettingsReadModel(settings: PayrollSettings): PayrollSettingsReadModel {
    return {
      payroll_setting_id: settings.payroll_setting_id,
      pay_schedule: settings.pay_schedule,
      pay_day: settings.pay_day,
      currency: settings.currency,
      payroll_summary: `${settings.pay_schedule} payroll · pay day ${settings.pay_day} · ${settings.currency}`,
      controls_summary: `${settings.attendance_cutoff_days} day attendance cutoff · leave mode ${settings.leave_deduction_mode} · ${settings.approval_chain.join(' → ')}`,
      status: settings.status,
      updated_at: settings.updated_at,
    };
  }

  private resolveLeavePolicyIndex(filters: LeavePolicyFilters): string {
    if (filters.leave_type) {
      return 'idx_leave_policies_type_status';
    }
    if (filters.status) {
      return 'idx_leave_policies_status';
    }
    return 'idx_leave_policies_status';
  }

  private addToIndex(index: Map<string, Set<string>>, key: string, id: string): void {
    const existing = index.get(key) ?? new Set<string>();
    existing.add(id);
    index.set(key, existing);
  }

  private removeFromIndex(index: Map<string, Set<string>>, key: string, id: string): void {
    const existing = index.get(key);
    if (!existing) {
      return;
    }

    existing.delete(id);
    if (existing.size === 0) {
      index.delete(key);
      return;
    }

    index.set(key, existing);
  }

  private invalidateCache(): void {
    this.cache.invalidateByPrefix(`${SETTINGS_CACHE_PREFIX}:`);
  }
}
