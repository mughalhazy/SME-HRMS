import {
  CONTRACT_TYPES,
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

function validateOptionalDate(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (value !== undefined && (typeof value !== 'string' || !isIsoDate(value))) {
    details.push({ field, reason: 'must be an ISO date (YYYY-MM-DD) when provided' });
  }
}

function validateContractMetadata(
  details: Array<{ field: string; reason: string }>,
  employmentType: CreateEmployeeInput['employment_type'] | UpdateEmployeeInput['employment_type'] | undefined,
  contractMetadata: unknown,
): void {
  if (contractMetadata === undefined) {
    if (employmentType === 'Contract') {
      details.push({ field: 'contract_metadata', reason: 'is required when employment_type is Contract' });
    }
    return;
  }

  if (employmentType !== undefined && employmentType !== 'Contract') {
    details.push({ field: 'contract_metadata', reason: 'is only allowed when employment_type is Contract' });
    return;
  }

  if (!contractMetadata || typeof contractMetadata !== 'object' || Array.isArray(contractMetadata)) {
    details.push({ field: 'contract_metadata', reason: 'must be an object when provided' });
    return;
  }

  const metadata = contractMetadata as Record<string, unknown>;
  requireString(details, 'contract_metadata.contract_type', metadata.contract_type);
  requireString(details, 'contract_metadata.contract_start_date', metadata.contract_start_date);
  requireString(details, 'contract_metadata.access_expires_at', metadata.access_expires_at);
  validateOptionalDate(details, 'contract_metadata.contract_end_date', metadata.contract_end_date);
  validateOptionalString(details, 'contract_metadata.vendor_name', metadata.vendor_name);
  validateOptionalString(details, 'contract_metadata.vendor_contact_email', metadata.vendor_contact_email);
  validateOptionalString(details, 'contract_metadata.purchase_order_number', metadata.purchase_order_number);
  validateOptionalString(details, 'contract_metadata.billing_currency', metadata.billing_currency);
  validateOptionalString(details, 'contract_metadata.sponsor_employee_id', metadata.sponsor_employee_id);
  validateOptionalString(details, 'contract_metadata.external_worker_id', metadata.external_worker_id);

  if (typeof metadata.contract_start_date === 'string' && !isIsoDate(metadata.contract_start_date)) {
    details.push({ field: 'contract_metadata.contract_start_date', reason: 'must be an ISO date (YYYY-MM-DD)' });
  }

  if (typeof metadata.access_expires_at === 'string' && !isIsoDate(metadata.access_expires_at)) {
    details.push({ field: 'contract_metadata.access_expires_at', reason: 'must be an ISO date (YYYY-MM-DD)' });
  }

  if (typeof metadata.contract_type === 'string' && !CONTRACT_TYPES.includes(metadata.contract_type as never)) {
    details.push({ field: 'contract_metadata.contract_type', reason: `must be one of: ${CONTRACT_TYPES.join(', ')}` });
  }

  if (metadata.vendor_contact_email !== undefined && (typeof metadata.vendor_contact_email !== 'string' || !EMAIL_REGEX.test(metadata.vendor_contact_email))) {
    details.push({ field: 'contract_metadata.vendor_contact_email', reason: 'must be a valid email address when provided' });
  }

  if (metadata.billing_rate !== undefined && (typeof metadata.billing_rate !== 'number' || metadata.billing_rate <= 0)) {
    details.push({ field: 'contract_metadata.billing_rate', reason: 'must be a positive number when provided' });
  }

  if (
    typeof metadata.contract_start_date === 'string'
    && typeof metadata.contract_end_date === 'string'
    && isIsoDate(metadata.contract_start_date)
    && isIsoDate(metadata.contract_end_date)
    && metadata.contract_end_date < metadata.contract_start_date
  ) {
    details.push({ field: 'contract_metadata.contract_end_date', reason: 'must be on or after contract_start_date' });
  }

  if (
    typeof metadata.contract_start_date === 'string'
    && typeof metadata.access_expires_at === 'string'
    && isIsoDate(metadata.contract_start_date)
    && isIsoDate(metadata.access_expires_at)
    && metadata.access_expires_at < metadata.contract_start_date
  ) {
    details.push({ field: 'contract_metadata.access_expires_at', reason: 'must be on or after contract_start_date' });
  }

  if (
    typeof metadata.contract_end_date === 'string'
    && typeof metadata.access_expires_at === 'string'
    && isIsoDate(metadata.contract_end_date)
    && isIsoDate(metadata.access_expires_at)
    && metadata.access_expires_at > metadata.contract_end_date
  ) {
    details.push({ field: 'contract_metadata.access_expires_at', reason: 'must be on or before contract_end_date when provided' });
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
  validateContractMetadata(details, input.employment_type, input.contract_metadata);
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
  validateContractMetadata(details, input.employment_type, input.contract_metadata);
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
