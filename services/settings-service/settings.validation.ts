import {
  ACCRUAL_FREQUENCIES,
  CreateAttendanceRuleInput,
  CreateLeavePolicyInput,
  LEAVE_DEDUCTION_MODES,
  LEAVE_POLICY_TYPES,
  PAY_SCHEDULES,
  SETTINGS_STATUSES,
  SettingsStatus,
  UpdateAttendanceRuleInput,
  UpdateLeavePolicyInput,
  UpsertPayrollSettingsInput,
  WEEK_DAYS,
} from './settings.model';
import { ValidationError } from '../employee-service/employee.validation';

function requireString(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (typeof value !== 'string' || value.trim() === '') {
    details.push({ field, reason: 'must be a non-empty string' });
  }
}

function validateNonNegativeNumber(
  details: Array<{ field: string; reason: string }>,
  field: string,
  value: unknown,
): void {
  if (typeof value !== 'number' || Number.isNaN(value) || value < 0) {
    details.push({ field, reason: 'must be a non-negative number' });
  }
}

function validateWeekDays(details: Array<{ field: string; reason: string }>, workdays: unknown): void {
  if (!Array.isArray(workdays) || workdays.length === 0) {
    details.push({ field: 'workdays', reason: 'must include at least one workday' });
    return;
  }

  const invalid = workdays.some((workday) => !WEEK_DAYS.includes(workday));
  if (invalid) {
    details.push({ field: 'workdays', reason: `must contain only: ${WEEK_DAYS.join(', ')}` });
  }
}

function validateStatus(details: Array<{ field: string; reason: string }>, status: unknown): void {
  if (status !== undefined && !SETTINGS_STATUSES.includes(status as SettingsStatus)) {
    details.push({ field: 'status', reason: `must be one of: ${SETTINGS_STATUSES.join(', ')}` });
  }
}

function validatePayrollPayDay(details: Array<{ field: string; reason: string }>, paySchedule: unknown, payDay: unknown): void {
  if (typeof payDay !== 'number' || !Number.isInteger(payDay)) {
    details.push({ field: 'pay_day', reason: 'must be an integer' });
    return;
  }

  if (paySchedule === 'Weekly' || paySchedule === 'BiWeekly') {
    if (payDay < 1 || payDay > 7) {
      details.push({ field: 'pay_day', reason: 'must be between 1 and 7 for Weekly or BiWeekly schedules' });
    }
    return;
  }

  if (paySchedule === 'SemiMonthly' || paySchedule === 'Monthly') {
    if (payDay < 1 || payDay > 31) {
      details.push({ field: 'pay_day', reason: 'must be between 1 and 31 for SemiMonthly or Monthly schedules' });
    }
  }
}

function validateOptionalAttendanceRuleFields(
  details: Array<{ field: string; reason: string }>,
  input: UpdateAttendanceRuleInput,
): void {
  if (input.name !== undefined && (typeof input.name !== 'string' || input.name.trim() === '')) {
    details.push({ field: 'name', reason: 'must be a non-empty string' });
  }

  if (input.timezone !== undefined && (typeof input.timezone !== 'string' || input.timezone.trim() === '')) {
    details.push({ field: 'timezone', reason: 'must be a non-empty string' });
  }

  if (input.workdays !== undefined) {
    validateWeekDays(details, input.workdays);
  }

  if (input.standard_work_hours !== undefined) {
    validateNonNegativeNumber(details, 'standard_work_hours', input.standard_work_hours);
    if (typeof input.standard_work_hours === 'number' && input.standard_work_hours > 24) {
      details.push({ field: 'standard_work_hours', reason: 'must be 24 or fewer hours' });
    }
  }

  if (input.grace_period_minutes !== undefined) {
    validateNonNegativeNumber(details, 'grace_period_minutes', input.grace_period_minutes);
  }

  if (input.late_after_minutes !== undefined) {
    validateNonNegativeNumber(details, 'late_after_minutes', input.late_after_minutes);
  }

  if (input.auto_clock_out_hours !== undefined) {
    validateNonNegativeNumber(details, 'auto_clock_out_hours', input.auto_clock_out_hours);
    if (typeof input.auto_clock_out_hours === 'number' && input.auto_clock_out_hours > 24) {
      details.push({ field: 'auto_clock_out_hours', reason: 'must be 24 or fewer hours' });
    }
  }

  if (input.require_geo_fencing !== undefined && typeof input.require_geo_fencing !== 'boolean') {
    details.push({ field: 'require_geo_fencing', reason: 'must be a boolean when provided' });
  }

  validateStatus(details, input.status);
}

export function validateCreateAttendanceRule(input: CreateAttendanceRuleInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  requireString(details, 'code', input.code);
  requireString(details, 'name', input.name);
  requireString(details, 'timezone', input.timezone);
  validateWeekDays(details, input.workdays);
  validateOptionalAttendanceRuleFields(details, input);

  if (input.late_after_minutes < input.grace_period_minutes) {
    details.push({ field: 'late_after_minutes', reason: 'must be greater than or equal to grace_period_minutes' });
  }

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdateAttendanceRule(input: UpdateAttendanceRuleInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }

  validateOptionalAttendanceRuleFields(details, input);

  if (
    input.late_after_minutes !== undefined
    && input.grace_period_minutes !== undefined
    && input.late_after_minutes < input.grace_period_minutes
  ) {
    details.push({ field: 'late_after_minutes', reason: 'must be greater than or equal to grace_period_minutes' });
  }

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

function validateLeavePolicyCore(
  details: Array<{ field: string; reason: string }>,
  input: {
    name?: string;
    code?: string;
    leave_type?: unknown;
    accrual_frequency?: unknown;
    accrual_rate_days?: unknown;
    annual_entitlement_days?: unknown;
    carry_forward_limit_days?: unknown;
    requires_approval?: unknown;
    allow_negative_balance?: unknown;
    status?: unknown;
  },
  requireIdentity: boolean,
): void {
  if (requireIdentity) {
    requireString(details, 'code', input.code);
    requireString(details, 'name', input.name);
  }

  if (input.name !== undefined && (typeof input.name !== 'string' || input.name.trim() === '')) {
    details.push({ field: 'name', reason: 'must be a non-empty string' });
  }

  if (input.leave_type !== undefined && !LEAVE_POLICY_TYPES.includes(input.leave_type as never)) {
    details.push({ field: 'leave_type', reason: `must be one of: ${LEAVE_POLICY_TYPES.join(', ')}` });
  }

  if (input.accrual_frequency !== undefined && !ACCRUAL_FREQUENCIES.includes(input.accrual_frequency as never)) {
    details.push({ field: 'accrual_frequency', reason: `must be one of: ${ACCRUAL_FREQUENCIES.join(', ')}` });
  }

  if (input.accrual_rate_days !== undefined) {
    validateNonNegativeNumber(details, 'accrual_rate_days', input.accrual_rate_days);
  }

  if (input.annual_entitlement_days !== undefined) {
    validateNonNegativeNumber(details, 'annual_entitlement_days', input.annual_entitlement_days);
  }

  if (input.carry_forward_limit_days !== undefined) {
    validateNonNegativeNumber(details, 'carry_forward_limit_days', input.carry_forward_limit_days);
  }

  if (input.requires_approval !== undefined && typeof input.requires_approval !== 'boolean') {
    details.push({ field: 'requires_approval', reason: 'must be a boolean when provided' });
  }

  if (input.allow_negative_balance !== undefined && typeof input.allow_negative_balance !== 'boolean') {
    details.push({ field: 'allow_negative_balance', reason: 'must be a boolean when provided' });
  }

  if (
    typeof input.annual_entitlement_days === 'number'
    && typeof input.carry_forward_limit_days === 'number'
    && input.carry_forward_limit_days > input.annual_entitlement_days
  ) {
    details.push({ field: 'carry_forward_limit_days', reason: 'must not exceed annual_entitlement_days' });
  }

  if (input.leave_type === 'Unpaid' && typeof input.annual_entitlement_days === 'number' && input.annual_entitlement_days !== 0) {
    details.push({ field: 'annual_entitlement_days', reason: 'must be 0 for Unpaid leave policies' });
  }

  if (input.accrual_frequency === 'None' && typeof input.accrual_rate_days === 'number' && input.accrual_rate_days !== 0) {
    details.push({ field: 'accrual_rate_days', reason: 'must be 0 when accrual_frequency is None' });
  }

  validateStatus(details, input.status);
}

export function validateCreateLeavePolicy(input: CreateLeavePolicyInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  validateLeavePolicyCore(details, input, true);

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdateLeavePolicy(input: UpdateLeavePolicyInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }

  validateLeavePolicyCore(details, input, false);

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpsertPayrollSettings(input: UpsertPayrollSettingsInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  if (!PAY_SCHEDULES.includes(input.pay_schedule)) {
    details.push({ field: 'pay_schedule', reason: `must be one of: ${PAY_SCHEDULES.join(', ')}` });
  }

  validatePayrollPayDay(details, input.pay_schedule, input.pay_day);
  requireString(details, 'currency', input.currency);

  if (input.currency && !/^[A-Z]{3}$/.test(input.currency)) {
    details.push({ field: 'currency', reason: 'must be a 3-letter uppercase ISO currency code' });
  }

  if (typeof input.overtime_multiplier !== 'number' || Number.isNaN(input.overtime_multiplier) || input.overtime_multiplier < 1) {
    details.push({ field: 'overtime_multiplier', reason: 'must be a number greater than or equal to 1' });
  }

  if (!Number.isInteger(input.attendance_cutoff_days) || input.attendance_cutoff_days < 0 || input.attendance_cutoff_days > 31) {
    details.push({ field: 'attendance_cutoff_days', reason: 'must be an integer between 0 and 31' });
  }

  if (!LEAVE_DEDUCTION_MODES.includes(input.leave_deduction_mode)) {
    details.push({ field: 'leave_deduction_mode', reason: `must be one of: ${LEAVE_DEDUCTION_MODES.join(', ')}` });
  }

  if (!Array.isArray(input.approval_chain) || input.approval_chain.length === 0 || input.approval_chain.some((entry) => typeof entry !== 'string' || entry.trim() === '')) {
    details.push({ field: 'approval_chain', reason: 'must be a non-empty list of approval stages' });
  }

  validateStatus(details, input.status);

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}
