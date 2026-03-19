import {
  CreateDepartmentInput,
  DEPARTMENT_STATUSES,
  DepartmentStatus,
  UpdateDepartmentInput,
} from './department.model';
import { ValidationError } from './employee.validation';

function requireString(
  details: Array<{ field: string; reason: string }>,
  field: string,
  value: unknown,
): void {
  if (typeof value !== 'string' || value.trim() === '') {
    details.push({ field, reason: 'must be a non-empty string' });
  }
}

export function validateCreateDepartment(input: CreateDepartmentInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  requireString(details, 'name', input.name);
  requireString(details, 'code', input.code);

  if (input.description !== undefined && typeof input.description !== 'string') {
    details.push({ field: 'description', reason: 'must be a string when provided' });
  }

  if (input.parent_department_id !== undefined && typeof input.parent_department_id !== 'string') {
    details.push({ field: 'parent_department_id', reason: 'must be a string when provided' });
  }

  if (input.head_employee_id !== undefined && typeof input.head_employee_id !== 'string') {
    details.push({ field: 'head_employee_id', reason: 'must be a string when provided' });
  }

  if (input.status !== undefined && !DEPARTMENT_STATUSES.includes(input.status)) {
    details.push({
      field: 'status',
      reason: `must be one of: ${DEPARTMENT_STATUSES.join(', ')}`,
    });
  }

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdateDepartment(input: UpdateDepartmentInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }

  if (input.name !== undefined && (typeof input.name !== 'string' || input.name.trim() === '')) {
    details.push({ field: 'name', reason: 'must be a non-empty string' });
  }

  if (input.code !== undefined && (typeof input.code !== 'string' || input.code.trim() === '')) {
    details.push({ field: 'code', reason: 'must be a non-empty string' });
  }

  if (input.description !== undefined && typeof input.description !== 'string') {
    details.push({ field: 'description', reason: 'must be a string when provided' });
  }

  if (input.parent_department_id !== undefined && typeof input.parent_department_id !== 'string') {
    details.push({ field: 'parent_department_id', reason: 'must be a string when provided' });
  }

  if (input.head_employee_id !== undefined && typeof input.head_employee_id !== 'string') {
    details.push({ field: 'head_employee_id', reason: 'must be a string when provided' });
  }

  if (input.status !== undefined && !DEPARTMENT_STATUSES.includes(input.status)) {
    details.push({
      field: 'status',
      reason: `must be one of: ${DEPARTMENT_STATUSES.join(', ')}`,
    });
  }

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateDepartmentStatus(status: DepartmentStatus): void {
  if (!DEPARTMENT_STATUSES.includes(status)) {
    throw new ValidationError([
      {
        field: 'status',
        reason: `must be one of: ${DEPARTMENT_STATUSES.join(', ')}`,
      },
    ]);
  }
}
