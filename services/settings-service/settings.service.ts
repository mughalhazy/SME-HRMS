import { ConflictError, NotFoundError } from '../employee-service/service.errors';
import {
  AttendanceRule,
  AttendanceRuleFilters,
  CreateAttendanceRuleInput,
  CreateLeavePolicyInput,
  LeavePolicy,
  LeavePolicyFilters,
  PayrollSettings,
  SettingsReadModelBundle,
  UpdateAttendanceRuleInput,
  UpdateLeavePolicyInput,
  UpsertPayrollSettingsInput,
} from './settings.model';
import { SettingsRepository } from './settings.repository';
import {
  validateCreateAttendanceRule,
  validateCreateLeavePolicy,
  validateUpdateAttendanceRule,
  validateUpdateLeavePolicy,
  validateUpsertPayrollSettings,
} from './settings.validation';
import { ValidationError } from '../employee-service/employee.validation';

export class SettingsService {
  constructor(private readonly repository: SettingsRepository) {}

  createAttendanceRule(input: CreateAttendanceRuleInput): AttendanceRule {
    validateCreateAttendanceRule(input);

    if (this.repository.findAttendanceRuleByCode(input.code)) {
      throw new ConflictError('attendance rule code already exists');
    }

    return this.repository.createAttendanceRule(input);
  }

  updateAttendanceRule(attendanceRuleId: string, input: UpdateAttendanceRuleInput): AttendanceRule {
    validateUpdateAttendanceRule(input);

    const current = this.getAttendanceRuleById(attendanceRuleId);
    const nextGracePeriod = input.grace_period_minutes ?? current.grace_period_minutes;
    const nextLateAfterMinutes = input.late_after_minutes ?? current.late_after_minutes;

    if (nextLateAfterMinutes < nextGracePeriod) {
      throw new ValidationError([{ field: 'late_after_minutes', reason: 'must be greater than or equal to grace_period_minutes' }]);
    }

    const updated = this.repository.updateAttendanceRule(attendanceRuleId, input);
    if (!updated) {
      throw new NotFoundError('attendance rule not found');
    }
    return updated;
  }

  getAttendanceRuleById(attendanceRuleId: string): AttendanceRule {
    const rule = this.repository.findAttendanceRuleById(attendanceRuleId);
    if (!rule) {
      throw new NotFoundError('attendance rule not found');
    }
    return rule;
  }

  listAttendanceRules(filters: AttendanceRuleFilters = {}): AttendanceRule[] {
    return this.repository.listAttendanceRules(filters);
  }

  createLeavePolicy(input: CreateLeavePolicyInput): LeavePolicy {
    validateCreateLeavePolicy(input);

    if (this.repository.findLeavePolicyByCode(input.code)) {
      throw new ConflictError('leave policy code already exists');
    }

    const activePolicyForType = this.repository.listLeavePolicies({ leave_type: input.leave_type, status: 'Active' });
    if ((input.status ?? 'Draft') === 'Active' && activePolicyForType.length > 0) {
      throw new ConflictError('an Active leave policy already exists for this leave_type');
    }

    return this.repository.createLeavePolicy(input);
  }

  updateLeavePolicy(leavePolicyId: string, input: UpdateLeavePolicyInput): LeavePolicy {
    validateUpdateLeavePolicy(input);

    const current = this.getLeavePolicyById(leavePolicyId);
    const nextLeaveType = current.leave_type;
    const nextStatus = input.status ?? current.status;
    const nextAccrualFrequency = input.accrual_frequency ?? current.accrual_frequency;
    const nextAccrualRateDays = input.accrual_rate_days ?? current.accrual_rate_days;
    const nextAnnualEntitlementDays = input.annual_entitlement_days ?? current.annual_entitlement_days;
    const nextCarryForwardLimitDays = input.carry_forward_limit_days ?? current.carry_forward_limit_days;

    if (nextCarryForwardLimitDays > nextAnnualEntitlementDays) {
      throw new ValidationError([{ field: 'carry_forward_limit_days', reason: 'must not exceed annual_entitlement_days' }]);
    }

    if (nextLeaveType === 'Unpaid' && nextAnnualEntitlementDays !== 0) {
      throw new ValidationError([{ field: 'annual_entitlement_days', reason: 'must be 0 for Unpaid leave policies' }]);
    }

    if (nextAccrualFrequency === 'None' && nextAccrualRateDays !== 0) {
      throw new ValidationError([{ field: 'accrual_rate_days', reason: 'must be 0 when accrual_frequency is None' }]);
    }

    if (nextStatus === 'Active') {
      const activePolicyForType = this.repository.listLeavePolicies({ leave_type: nextLeaveType, status: 'Active' })
        .find((policy) => policy.leave_policy_id !== leavePolicyId);
      if (activePolicyForType) {
        throw new ConflictError('an Active leave policy already exists for this leave_type');
      }
    }

    const updated = this.repository.updateLeavePolicy(leavePolicyId, input);
    if (!updated) {
      throw new NotFoundError('leave policy not found');
    }
    return updated;
  }

  getLeavePolicyById(leavePolicyId: string): LeavePolicy {
    const policy = this.repository.findLeavePolicyById(leavePolicyId);
    if (!policy) {
      throw new NotFoundError('leave policy not found');
    }
    return policy;
  }

  listLeavePolicies(filters: LeavePolicyFilters = {}): LeavePolicy[] {
    return this.repository.listLeavePolicies(filters);
  }

  upsertPayrollSettings(input: UpsertPayrollSettingsInput): PayrollSettings {
    validateUpsertPayrollSettings(input);

    const current = this.repository.getPayrollSettings();
    if (current?.status === 'Active' && (input.status ?? 'Active') === 'Draft') {
      throw new ConflictError('cannot replace Active payroll settings with Draft status');
    }

    return this.repository.upsertPayrollSettings(input);
  }

  getPayrollSettings(): PayrollSettings {
    const settings = this.repository.getPayrollSettings();
    if (!settings) {
      throw new NotFoundError('payroll settings not found');
    }
    return settings;
  }

  getSettingsReadModels(): SettingsReadModelBundle {
    return this.repository.toReadModelBundle();
  }
}
