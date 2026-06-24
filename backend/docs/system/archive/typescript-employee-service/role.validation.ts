import {
  CreateRoleInput,
  EMPLOYMENT_CATEGORIES,
  ROLE_PERMISSION_CODES,
  ROLE_STATUSES,
  UpdateRoleInput,
} from './role.model';
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

function validatePermissions(
  details: Array<{ field: string; reason: string }>,
  permissions: unknown,
  field = 'permissions',
): void {
  if (!Array.isArray(permissions)) {
    details.push({ field, reason: 'must be an array of permission codes' });
    return;
  }

  for (const permission of permissions) {
    if (!ROLE_PERMISSION_CODES.includes(permission)) {
      details.push({
        field,
        reason: `contains unsupported permission code: ${String(permission)}`,
      });
    }
  }
}

export function validateCreateRole(input: CreateRoleInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  requireString(details, 'title', input.title);

  if (input.level !== undefined && (typeof input.level !== 'string' || input.level.trim() === '')) {
    details.push({ field: 'level', reason: 'must be a non-empty string when provided' });
  }

  if (input.description !== undefined && typeof input.description !== 'string') {
    details.push({ field: 'description', reason: 'must be a string when provided' });
  }

  if (!EMPLOYMENT_CATEGORIES.includes(input.employment_category)) {
    details.push({
      field: 'employment_category',
      reason: `must be one of: ${EMPLOYMENT_CATEGORIES.join(', ')}`,
    });
  }

  if (input.status !== undefined && !ROLE_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${ROLE_STATUSES.join(', ')}` });
  }

  if (input.permissions !== undefined) {
    validatePermissions(details, input.permissions);
  }

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdateRole(input: UpdateRoleInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }

  if (input.title !== undefined && (typeof input.title !== 'string' || input.title.trim() === '')) {
    details.push({ field: 'title', reason: 'must be a non-empty string' });
  }

  if (input.level !== undefined && (typeof input.level !== 'string' || input.level.trim() === '')) {
    details.push({ field: 'level', reason: 'must be a non-empty string when provided' });
  }

  if (input.description !== undefined && typeof input.description !== 'string') {
    details.push({ field: 'description', reason: 'must be a string when provided' });
  }

  if (input.employment_category !== undefined && !EMPLOYMENT_CATEGORIES.includes(input.employment_category)) {
    details.push({
      field: 'employment_category',
      reason: `must be one of: ${EMPLOYMENT_CATEGORIES.join(', ')}`,
    });
  }

  if (input.status !== undefined && !ROLE_STATUSES.includes(input.status)) {
    details.push({ field: 'status', reason: `must be one of: ${ROLE_STATUSES.join(', ')}` });
  }

  if (input.permissions !== undefined) {
    validatePermissions(details, input.permissions);
  }

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}
