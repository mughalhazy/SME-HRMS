import {
  CreateEmployeeInput,
  EMPLOYEE_STATUSES,
  EMPLOYMENT_TYPES,
  EmployeeStatus,
  UpdateEmployeeInput,
} from './employee.model';

export class ValidationError extends Error {
  constructor(public readonly details: Array<{ field: string; reason: string }>) {
    super('One or more fields are invalid.');
    this.name = 'ValidationError';
  }
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function isIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));
}

function requireString(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (typeof value !== 'string' || value.trim() === '') {
    details.push({ field, reason: 'must be a non-empty string' });
  }
}

function validateOptionalString(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (value !== undefined && (typeof value !== 'string' || value.trim() === '')) {
    details.push({ field, reason: 'must be a non-empty string when provided' });
  }
}

function validateOptionalStringArray(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (value === undefined) {
    return;
  }
  if (!Array.isArray(value) || value.some((item) => typeof item !== 'string' || item.trim() === '')) {
    details.push({ field, reason: 'must be an array of non-empty strings when provided' });
  }
}

function validateCostAllocations(details: Array<{ field: string; reason: string }>, costAllocations: unknown): void {
  if (costAllocations === undefined) {
    return;
  }
  if (!Array.isArray(costAllocations) || costAllocations.length === 0) {
    details.push({ field: 'cost_allocations', reason: 'must be a non-empty array when provided' });
    return;
  }

  let total = 0;
  for (const [index, item] of costAllocations.entries()) {
    if (!item || typeof item !== 'object') {
      details.push({ field: `cost_allocations[${index}]`, reason: 'must be an object' });
      continue;
    }
    const allocation = item as Record<string, unknown>;
    if (typeof allocation.cost_center_id !== 'string' || allocation.cost_center_id.trim() === '') {
      details.push({ field: `cost_allocations[${index}].cost_center_id`, reason: 'must be a non-empty string' });
    }
    if (typeof allocation.allocation_percentage !== 'number' || allocation.allocation_percentage <= 0 || allocation.allocation_percentage > 100) {
      details.push({ field: `cost_allocations[${index}].allocation_percentage`, reason: 'must be a number between 0 and 100' });
    } else {
      total += allocation.allocation_percentage;
    }
    if (allocation.is_primary !== undefined && typeof allocation.is_primary !== 'boolean') {
      details.push({ field: `cost_allocations[${index}].is_primary`, reason: 'must be a boolean when provided' });
    }
  }

  if (Math.round(total * 100) / 100 !== 100) {
    details.push({ field: 'cost_allocations', reason: 'allocation percentages must total 100' });
  }
}

export function validateCreateEmployee(input: CreateEmployeeInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  requireString(details, 'employee_number', input.employee_number);
  requireString(details, 'first_name', input.first_name);
  requireString(details, 'last_name', input.last_name);
  requireString(details, 'email', input.email);
  requireString(details, 'hire_date', input.hire_date);
  requireString(details, 'department_id', input.department_id);
  requireString(details, 'role_id', input.role_id);

  validateOptionalString(details, 'phone', input.phone);
  validateOptionalString(details, 'manager_employee_id', input.manager_employee_id);
  validateOptionalString(details, 'business_unit_id', input.business_unit_id);
  validateOptionalString(details, 'legal_entity_id', input.legal_entity_id);
  validateOptionalString(details, 'location_id', input.location_id);
  validateOptionalString(details, 'cost_center_id', input.cost_center_id);
  validateOptionalString(details, 'job_position_id', input.job_position_id);
  validateOptionalString(details, 'grade_band_id', input.grade_band_id);
  validateOptionalStringArray(details, 'matrix_manager_employee_ids', input.matrix_manager_employee_ids);
  validateCostAllocations(details, input.cost_allocations);

  if (input.email && !EMAIL_REGEX.test(input.email)) {
    details.push({ field: 'email', reason: 'must be a valid email address' });
  }

  if (input.hire_date && !isIsoDate(input.hire_date)) {
    details.push({ field: 'hire_date', reason: 'must be an ISO date (YYYY-MM-DD)' });
  }

  if (!EMPLOYMENT_TYPES.includes(input.employment_type)) {
    details.push({ field: 'employment_type', reason: `must be one of: ${EMPLOYMENT_TYPES.join(', ')}` });
  }

  if (input.status && !EMPLOYEE_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${EMPLOYEE_STATUSES.join(', ')}` });
  }

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdateEmployee(input: UpdateEmployeeInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }

  validateOptionalString(details, 'first_name', input.first_name);
  validateOptionalString(details, 'last_name', input.last_name);
  validateOptionalString(details, 'phone', input.phone);
  validateOptionalString(details, 'department_id', input.department_id);
  validateOptionalString(details, 'role_id', input.role_id);
  validateOptionalString(details, 'manager_employee_id', input.manager_employee_id);
  validateOptionalString(details, 'business_unit_id', input.business_unit_id);
  validateOptionalString(details, 'legal_entity_id', input.legal_entity_id);
  validateOptionalString(details, 'location_id', input.location_id);
  validateOptionalString(details, 'cost_center_id', input.cost_center_id);
  validateOptionalString(details, 'job_position_id', input.job_position_id);
  validateOptionalString(details, 'grade_band_id', input.grade_band_id);
  validateOptionalStringArray(details, 'matrix_manager_employee_ids', input.matrix_manager_employee_ids);
  validateCostAllocations(details, input.cost_allocations);

  if (input.email !== undefined && (!EMAIL_REGEX.test(input.email) || input.email.trim() === '')) {
    details.push({ field: 'email', reason: 'must be a valid email address' });
  }

  if (input.hire_date !== undefined && !isIsoDate(input.hire_date)) {
    details.push({ field: 'hire_date', reason: 'must be an ISO date (YYYY-MM-DD)' });
  }

  if (input.employment_type !== undefined && !EMPLOYMENT_TYPES.includes(input.employment_type)) {
    details.push({ field: 'employment_type', reason: `must be one of: ${EMPLOYMENT_TYPES.join(', ')}` });
  }

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateStatus(status: EmployeeStatus): void {
  if (!EMPLOYEE_STATUSES.includes(status)) {
    throw new ValidationError([
      {
        field: 'status',
        reason: `must be one of: ${EMPLOYEE_STATUSES.join(', ')}`,
      },
    ]);
  }
}
