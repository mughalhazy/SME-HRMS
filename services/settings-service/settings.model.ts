export const SETTINGS_STATUSES = ['Draft', 'Active', 'Archived'] as const;
export type SettingsStatus = (typeof SETTINGS_STATUSES)[number];

export const PAY_SCHEDULES = ['Weekly', 'BiWeekly', 'SemiMonthly', 'Monthly'] as const;
export type PaySchedule = (typeof PAY_SCHEDULES)[number];

export const LEAVE_POLICY_TYPES = ['Annual', 'Sick', 'Casual', 'Unpaid', 'Parental', 'Other'] as const;
export type LeavePolicyType = (typeof LEAVE_POLICY_TYPES)[number];

export const ACCRUAL_FREQUENCIES = ['None', 'Monthly', 'Quarterly', 'Yearly'] as const;
export type AccrualFrequency = (typeof ACCRUAL_FREQUENCIES)[number];

export const LEAVE_DEDUCTION_MODES = ['None', 'Prorated', 'FullDay'] as const;
export type LeaveDeductionMode = (typeof LEAVE_DEDUCTION_MODES)[number];

export const WEEK_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] as const;
export type WeekDay = (typeof WEEK_DAYS)[number];

export interface AttendanceRule {
  tenant_id: string;
  attendance_rule_id: string;
  code: string;
  name: string;
  timezone: string;
  workdays: WeekDay[];
  standard_work_hours: number;
  grace_period_minutes: number;
  late_after_minutes: number;
  auto_clock_out_hours?: number;
  require_geo_fencing: boolean;
  status: SettingsStatus;
  created_at: string;
  updated_at: string;
}

export interface LeavePolicy {
  tenant_id: string;
  leave_policy_id: string;
  code: string;
  name: string;
  leave_type: LeavePolicyType;
  accrual_frequency: AccrualFrequency;
  accrual_rate_days: number;
  annual_entitlement_days: number;
  carry_forward_limit_days: number;
  requires_approval: boolean;
  allow_negative_balance: boolean;
  status: SettingsStatus;
  created_at: string;
  updated_at: string;
}

export interface PayrollSettings {
  tenant_id: string;
  payroll_setting_id: string;
  pay_schedule: PaySchedule;
  pay_day: number;
  currency: string;
  overtime_multiplier: number;
  attendance_cutoff_days: number;
  leave_deduction_mode: LeaveDeductionMode;
  approval_chain: string[];
  status: SettingsStatus;
  created_at: string;
  updated_at: string;
}

export interface TenantConfig {
  tenant_id: string;
  feature_flags: Record<string, boolean>;
  leave_policy_refs: string[];
  payroll_rule_refs: string[];
  locale: string;
  legal_entity: string;
  enabled_locations: string[];
  updated_at: string;
}

export interface AttendanceRuleReadModel {
  tenant_id: string;
  attendance_rule_id: string;
  code: string;
  name: string;
  schedule_summary: string;
  compliance_summary: string;
  status: SettingsStatus;
  updated_at: string;
}

export interface LeavePolicyReadModel {
  tenant_id: string;
  leave_policy_id: string;
  code: string;
  name: string;
  leave_type: LeavePolicyType;
  entitlement_summary: string;
  approval_summary: string;
  status: SettingsStatus;
  updated_at: string;
}

export interface PayrollSettingsReadModel {
  tenant_id: string;
  payroll_setting_id: string;
  pay_schedule: PaySchedule;
  pay_day: number;
  currency: string;
  payroll_summary: string;
  controls_summary: string;
  status: SettingsStatus;
  updated_at: string;
}

export interface SettingsConfigurationView {
  tenant_id: string;
  attendance_rules: AttendanceRuleReadModel[];
  leave_policies: LeavePolicyReadModel[];
  payroll_settings: PayrollSettingsReadModel | null;
  tenant_configuration: TenantConfig;
  updated_at: string | null;
}

export interface SettingsReadModelBundle {
  settings_configuration_view: SettingsConfigurationView;
}

export interface CreateAttendanceRuleInput {
  tenant_id?: string;
  code: string;
  name: string;
  timezone: string;
  workdays: WeekDay[];
  standard_work_hours: number;
  grace_period_minutes: number;
  late_after_minutes: number;
  auto_clock_out_hours?: number;
  require_geo_fencing?: boolean;
  status?: SettingsStatus;
}

export interface UpdateAttendanceRuleInput {
  name?: string;
  timezone?: string;
  workdays?: WeekDay[];
  standard_work_hours?: number;
  grace_period_minutes?: number;
  late_after_minutes?: number;
  auto_clock_out_hours?: number;
  require_geo_fencing?: boolean;
  status?: SettingsStatus;
}

export interface AttendanceRuleFilters {
  tenant_id?: string;
  status?: SettingsStatus;
}

export interface CreateLeavePolicyInput {
  tenant_id?: string;
  code: string;
  name: string;
  leave_type: LeavePolicyType;
  accrual_frequency: AccrualFrequency;
  accrual_rate_days: number;
  annual_entitlement_days: number;
  carry_forward_limit_days: number;
  requires_approval?: boolean;
  allow_negative_balance?: boolean;
  status?: SettingsStatus;
}

export interface UpdateLeavePolicyInput {
  name?: string;
  accrual_frequency?: AccrualFrequency;
  accrual_rate_days?: number;
  annual_entitlement_days?: number;
  carry_forward_limit_days?: number;
  requires_approval?: boolean;
  allow_negative_balance?: boolean;
  status?: SettingsStatus;
}

export interface LeavePolicyFilters {
  tenant_id?: string;
  leave_type?: LeavePolicyType;
  status?: SettingsStatus;
}

export interface UpsertPayrollSettingsInput {
  tenant_id?: string;
  pay_schedule: PaySchedule;
  pay_day: number;
  currency: string;
  overtime_multiplier: number;
  attendance_cutoff_days: number;
  leave_deduction_mode: LeaveDeductionMode;
  approval_chain: string[];
  status?: SettingsStatus;
}

export interface UpsertTenantConfigInput {
  tenant_id?: string;
  feature_flags?: Record<string, boolean>;
  leave_policy_refs?: string[];
  payroll_rule_refs?: string[];
  locale?: string;
  legal_entity?: string;
  enabled_locations?: string[];
}
