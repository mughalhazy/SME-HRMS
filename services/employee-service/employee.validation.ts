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

function requireString(
  details: Array<{ field: string; reason: string }>,
  field: string,
  value: unknown,
): void {
  if (typeof value !== 'string' || value.trim() === '') {
    details.push({ field, reason: 'must be a non-empty string' });
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

  if (input.phone !== undefined && (typeof input.phone !== 'string' || input.phone.trim() === '')) {
    details.push({ field: 'phone', reason: 'must be a non-empty string when provided' });
  }

  if (input.email && !EMAIL_REGEX.test(input.email)) {
    details.push({ field: 'email', reason: 'must be a valid email address' });
  }

  if (input.hire_date && !isIsoDate(input.hire_date)) {
    details.push({ field: 'hire_date', reason: 'must be an ISO date (YYYY-MM-DD)' });
  }

  if (!EMPLOYMENT_TYPES.includes(input.employment_type)) {
    details.push({
      field: 'employment_type',
      reason: `must be one of: ${EMPLOYMENT_TYPES.join(', ')}`,
    });
  }

  if (input.status && !EMPLOYEE_STATUSES.includes(input.status)) {
    details.push({
      field: 'status',
      reason: `must be one of: ${EMPLOYEE_STATUSES.join(', ')}`,
    });
  }

  if (input.manager_employee_id !== undefined && (typeof input.manager_employee_id !== 'string' || input.manager_employee_id.trim() === '')) {
    details.push({ field: 'manager_employee_id', reason: 'must be a non-empty string when provided' });
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

  if (input.first_name !== undefined && (typeof input.first_name !== 'string' || input.first_name.trim() === '')) {
    details.push({ field: 'first_name', reason: 'must be a non-empty string' });
  }

  if (input.last_name !== undefined && (typeof input.last_name !== 'string' || input.last_name.trim() === '')) {
    details.push({ field: 'last_name', reason: 'must be a non-empty string' });
  }

  if (input.email !== undefined && (!EMAIL_REGEX.test(input.email) || input.email.trim() === '')) {
    details.push({ field: 'email', reason: 'must be a valid email address' });
  }

  if (input.phone !== undefined && (typeof input.phone !== 'string' || input.phone.trim() === '')) {
    details.push({ field: 'phone', reason: 'must be a non-empty string when provided' });
  }

  if (input.hire_date !== undefined && !isIsoDate(input.hire_date)) {
    details.push({ field: 'hire_date', reason: 'must be an ISO date (YYYY-MM-DD)' });
  }

  if (input.department_id !== undefined && (typeof input.department_id !== 'string' || input.department_id.trim() === '')) {
    details.push({ field: 'department_id', reason: 'must be a non-empty string' });
  }

  if (input.role_id !== undefined && (typeof input.role_id !== 'string' || input.role_id.trim() === '')) {
    details.push({ field: 'role_id', reason: 'must be a non-empty string' });
  }

  if (input.manager_employee_id !== undefined && (typeof input.manager_employee_id !== 'string' || input.manager_employee_id.trim() === '')) {
    details.push({ field: 'manager_employee_id', reason: 'must be a non-empty string when provided' });
  }

  if (input.employment_type !== undefined && !EMPLOYMENT_TYPES.includes(input.employment_type)) {
    details.push({
      field: 'employment_type',
      reason: `must be one of: ${EMPLOYMENT_TYPES.join(', ')}`,
    });
  }

  if (input.role_id !== undefined && (typeof input.role_id !== 'string' || input.role_id.trim() === '')) {
    details.push({ field: 'role_id', reason: 'must be a non-empty string when provided' });
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
