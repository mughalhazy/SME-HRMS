import {
  ALLOWANCE_STATUSES,
  AllowanceFilters,
  BENEFITS_ENROLLMENT_STATUSES,
  BENEFITS_PLAN_STATUSES,
  BENEFITS_PLAN_TYPES,
  BenefitsEnrollmentFilters,
  BenefitsPlanFilters,
  COMPENSATION_BAND_STATUSES,
  CompensationBandFilters,
  CreateAllowanceInput,
  CreateBenefitsEnrollmentInput,
  CreateBenefitsPlanInput,
  CreateCompensationBandInput,
  CreateSalaryRevisionInput,
  SALARY_REVISION_STATUSES,
  SalaryRevisionFilters,
  UpdateAllowanceInput,
  UpdateBenefitsEnrollmentInput,
  UpdateBenefitsPlanInput,
  UpdateCompensationBandInput,
  UpdateSalaryRevisionInput,
} from './compensation.model';
import { ValidationError } from './employee.validation';

function isIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));
}

function requireString(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (typeof value !== 'string' || value.trim() === '') {
    details.push({ field, reason: 'must be a non-empty string' });
  }
}

function optionalString(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (value !== undefined && (typeof value !== 'string' || value.trim() === '')) {
    details.push({ field, reason: 'must be a non-empty string when provided' });
  }
}

function optionalBoolean(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (value !== undefined && typeof value !== 'boolean') {
    details.push({ field, reason: 'must be a boolean when provided' });
  }
}

function optionalPagination(details: Array<{ field: string; reason: string }>, limit: unknown, cursor: unknown): void {
  if (limit !== undefined && (!Number.isInteger(limit) || Number(limit) < 1 || Number(limit) > 100)) {
    details.push({ field: 'limit', reason: 'must be an integer between 1 and 100' });
  }
  if (cursor !== undefined && (typeof cursor !== 'string' || cursor.trim() === '')) {
    details.push({ field: 'cursor', reason: 'must be a non-empty string when provided' });
  }
}

function validateMoney(details: Array<{ field: string; reason: string }>, field: string, value: unknown, opts: { allowZero?: boolean } = {}): void {
  if (typeof value !== 'string' || value.trim() === '') {
    details.push({ field, reason: 'must be a monetary string' });
    return;
  }
  if (!/^-?\d+(\.\d{1,2})?$/.test(value.trim())) {
    details.push({ field, reason: 'must be a decimal with up to 2 fractional digits' });
    return;
  }
  const numeric = Number(value);
  const minimum = opts.allowZero === false ? Number.MIN_VALUE : 0;
  if (Number.isNaN(numeric) || numeric < minimum) {
    details.push({ field, reason: 'must be greater than or equal to 0.00' });
  }
}

function validateOptionalMoney(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (value !== undefined) {
    validateMoney(details, field, value);
  }
}

function validateDateRange(details: Array<{ field: string; reason: string }>, fromField: string, fromValue: unknown, toField: string, toValue: unknown): void {
  if (typeof fromValue === 'string' && !isIsoDate(fromValue)) {
    details.push({ field: fromField, reason: 'must be an ISO date (YYYY-MM-DD)' });
  }
  if (typeof toValue === 'string' && !isIsoDate(toValue)) {
    details.push({ field: toField, reason: 'must be an ISO date (YYYY-MM-DD)' });
  }
  if (typeof fromValue === 'string' && typeof toValue === 'string' && isIsoDate(fromValue) && isIsoDate(toValue) && toValue < fromValue) {
    details.push({ field: toField, reason: `must be on or after ${fromField}` });
  }
}

function validateCurrency(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (value !== undefined && (typeof value !== 'string' || !/^[A-Z]{3}$/.test(value))) {
    details.push({ field, reason: 'must be a 3-letter ISO currency code' });
  }
}

export function validateCreateCompensationBand(input: CreateCompensationBandInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'grade_band_id', input.grade_band_id);
  requireString(details, 'name', input.name);
  requireString(details, 'code', input.code);
  validateCurrency(details, 'currency', input.currency ?? 'USD');
  validateMoney(details, 'min_salary', input.min_salary);
  validateMoney(details, 'max_salary', input.max_salary);
  validateOptionalMoney(details, 'target_salary', input.target_salary);
  if (typeof input.min_salary === 'string' && typeof input.max_salary === 'string' && Number(input.max_salary) < Number(input.min_salary)) {
    details.push({ field: 'max_salary', reason: 'must be greater than or equal to min_salary' });
  }
  if (input.target_salary !== undefined) {
    const target = Number(input.target_salary);
    if (!Number.isNaN(target) && (target < Number(input.min_salary) || target > Number(input.max_salary))) {
      details.push({ field: 'target_salary', reason: 'must be within the min_salary and max_salary range' });
    }
  }
  if (input.status && !COMPENSATION_BAND_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${COMPENSATION_BAND_STATUSES.join(', ')}` });
  }
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdateCompensationBand(input: UpdateCompensationBandInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  optionalString(details, 'grade_band_id', input.grade_band_id);
  optionalString(details, 'name', input.name);
  optionalString(details, 'code', input.code);
  validateCurrency(details, 'currency', input.currency);
  validateOptionalMoney(details, 'min_salary', input.min_salary);
  validateOptionalMoney(details, 'max_salary', input.max_salary);
  validateOptionalMoney(details, 'target_salary', input.target_salary);
  if (input.status && !COMPENSATION_BAND_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${COMPENSATION_BAND_STATUSES.join(', ')}` });
  }
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateCompensationBandFilters(filters: CompensationBandFilters): void {
  const details: Array<{ field: string; reason: string }> = [];
  optionalString(details, 'grade_band_id', filters.grade_band_id);
  if (filters.status && !COMPENSATION_BAND_STATUSES.includes(filters.status)) {
    details.push({ field: 'status', reason: `must be one of: ${COMPENSATION_BAND_STATUSES.join(', ')}` });
  }
  optionalPagination(details, filters.limit, filters.cursor);
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateCreateSalaryRevision(input: CreateSalaryRevisionInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'employee_id', input.employee_id);
  requireString(details, 'effective_from', input.effective_from);
  validateDateRange(details, 'effective_from', input.effective_from, 'effective_to', input.effective_to);
  validateMoney(details, 'base_salary', input.base_salary);
  validateCurrency(details, 'currency', input.currency ?? 'USD');
  optionalString(details, 'reason', input.reason);
  optionalString(details, 'compensation_band_id', input.compensation_band_id);
  if (input.status && !SALARY_REVISION_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${SALARY_REVISION_STATUSES.join(', ')}` });
  }
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdateSalaryRevision(input: UpdateSalaryRevisionInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  optionalString(details, 'compensation_band_id', input.compensation_band_id);
  if (input.effective_from !== undefined && (typeof input.effective_from !== 'string' || input.effective_from.trim() === '')) {
    details.push({ field: 'effective_from', reason: 'must be a non-empty string when provided' });
  }
  validateDateRange(details, 'effective_from', input.effective_from, 'effective_to', input.effective_to);
  validateOptionalMoney(details, 'base_salary', input.base_salary);
  validateCurrency(details, 'currency', input.currency);
  optionalString(details, 'reason', input.reason);
  if (input.status && !SALARY_REVISION_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${SALARY_REVISION_STATUSES.join(', ')}` });
  }
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateSalaryRevisionFilters(filters: SalaryRevisionFilters): void {
  const details: Array<{ field: string; reason: string }> = [];
  optionalString(details, 'employee_id', filters.employee_id);
  optionalString(details, 'compensation_band_id', filters.compensation_band_id);
  if (filters.status && !SALARY_REVISION_STATUSES.includes(filters.status)) {
    details.push({ field: 'status', reason: `must be one of: ${SALARY_REVISION_STATUSES.join(', ')}` });
  }
  optionalPagination(details, filters.limit, filters.cursor);
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateCreateBenefitsPlan(input: CreateBenefitsPlanInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'name', input.name);
  requireString(details, 'code', input.code);
  if (!BENEFITS_PLAN_TYPES.includes(input.plan_type)) {
    details.push({ field: 'plan_type', reason: `must be one of: ${BENEFITS_PLAN_TYPES.join(', ')}` });
  }
  optionalString(details, 'provider', input.provider);
  validateCurrency(details, 'currency', input.currency ?? 'USD');
  validateMoney(details, 'employee_contribution_default', input.employee_contribution_default ?? '0.00');
  validateMoney(details, 'employer_contribution_default', input.employer_contribution_default ?? '0.00');
  optionalString(details, 'payroll_deduction_code', input.payroll_deduction_code);
  if (input.status && !BENEFITS_PLAN_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${BENEFITS_PLAN_STATUSES.join(', ')}` });
  }
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdateBenefitsPlan(input: UpdateBenefitsPlanInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  optionalString(details, 'name', input.name);
  optionalString(details, 'code', input.code);
  if (input.plan_type !== undefined && !BENEFITS_PLAN_TYPES.includes(input.plan_type)) {
    details.push({ field: 'plan_type', reason: `must be one of: ${BENEFITS_PLAN_TYPES.join(', ')}` });
  }
  optionalString(details, 'provider', input.provider);
  validateCurrency(details, 'currency', input.currency);
  validateOptionalMoney(details, 'employee_contribution_default', input.employee_contribution_default);
  validateOptionalMoney(details, 'employer_contribution_default', input.employer_contribution_default);
  optionalString(details, 'payroll_deduction_code', input.payroll_deduction_code);
  if (input.status && !BENEFITS_PLAN_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${BENEFITS_PLAN_STATUSES.join(', ')}` });
  }
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateBenefitsPlanFilters(filters: BenefitsPlanFilters): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (filters.plan_type && !BENEFITS_PLAN_TYPES.includes(filters.plan_type)) {
    details.push({ field: 'plan_type', reason: `must be one of: ${BENEFITS_PLAN_TYPES.join(', ')}` });
  }
  if (filters.status && !BENEFITS_PLAN_STATUSES.includes(filters.status)) {
    details.push({ field: 'status', reason: `must be one of: ${BENEFITS_PLAN_STATUSES.join(', ')}` });
  }
  optionalPagination(details, filters.limit, filters.cursor);
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateCreateBenefitsEnrollment(input: CreateBenefitsEnrollmentInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'employee_id', input.employee_id);
  requireString(details, 'benefits_plan_id', input.benefits_plan_id);
  requireString(details, 'effective_from', input.effective_from);
  validateDateRange(details, 'effective_from', input.effective_from, 'effective_to', input.effective_to);
  optionalString(details, 'coverage_level', input.coverage_level);
  validateOptionalMoney(details, 'employee_contribution', input.employee_contribution);
  validateOptionalMoney(details, 'employer_contribution', input.employer_contribution);
  if (input.status && !BENEFITS_ENROLLMENT_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${BENEFITS_ENROLLMENT_STATUSES.join(', ')}` });
  }
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdateBenefitsEnrollment(input: UpdateBenefitsEnrollmentInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  validateDateRange(details, 'effective_from', input.effective_from, 'effective_to', input.effective_to);
  optionalString(details, 'coverage_level', input.coverage_level);
  validateOptionalMoney(details, 'employee_contribution', input.employee_contribution);
  validateOptionalMoney(details, 'employer_contribution', input.employer_contribution);
  if (input.status && !BENEFITS_ENROLLMENT_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${BENEFITS_ENROLLMENT_STATUSES.join(', ')}` });
  }
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateBenefitsEnrollmentFilters(filters: BenefitsEnrollmentFilters): void {
  const details: Array<{ field: string; reason: string }> = [];
  optionalString(details, 'employee_id', filters.employee_id);
  optionalString(details, 'benefits_plan_id', filters.benefits_plan_id);
  if (filters.status && !BENEFITS_ENROLLMENT_STATUSES.includes(filters.status)) {
    details.push({ field: 'status', reason: `must be one of: ${BENEFITS_ENROLLMENT_STATUSES.join(', ')}` });
  }
  optionalPagination(details, filters.limit, filters.cursor);
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateCreateAllowance(input: CreateAllowanceInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'employee_id', input.employee_id);
  requireString(details, 'name', input.name);
  requireString(details, 'code', input.code);
  requireString(details, 'effective_from', input.effective_from);
  validateDateRange(details, 'effective_from', input.effective_from, 'effective_to', input.effective_to);
  validateCurrency(details, 'currency', input.currency ?? 'USD');
  validateMoney(details, 'amount', input.amount);
  optionalBoolean(details, 'taxable', input.taxable);
  optionalBoolean(details, 'recurring', input.recurring);
  if (input.status && !ALLOWANCE_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${ALLOWANCE_STATUSES.join(', ')}` });
  }
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdateAllowance(input: UpdateAllowanceInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  optionalString(details, 'name', input.name);
  optionalString(details, 'code', input.code);
  validateCurrency(details, 'currency', input.currency);
  validateOptionalMoney(details, 'amount', input.amount);
  optionalBoolean(details, 'taxable', input.taxable);
  optionalBoolean(details, 'recurring', input.recurring);
  validateDateRange(details, 'effective_from', input.effective_from, 'effective_to', input.effective_to);
  if (input.status && !ALLOWANCE_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${ALLOWANCE_STATUSES.join(', ')}` });
  }
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateAllowanceFilters(filters: AllowanceFilters): void {
  const details: Array<{ field: string; reason: string }> = [];
  optionalString(details, 'employee_id', filters.employee_id);
  if (filters.status && !ALLOWANCE_STATUSES.includes(filters.status)) {
    details.push({ field: 'status', reason: `must be one of: ${ALLOWANCE_STATUSES.join(', ')}` });
  }
  optionalPagination(details, filters.limit, filters.cursor);
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}
