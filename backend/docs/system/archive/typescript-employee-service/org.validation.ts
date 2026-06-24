import {
  CreateBusinessUnitInput,
  CreateCostCenterInput,
  CreateGradeBandInput,
  CreateJobPositionInput,
  CreateLegalEntityInput,
  CreateLocationInput,
  ORG_ENTITY_STATUSES,
  OrgEntityStatus,
  UpdateBusinessUnitInput,
  UpdateCostCenterInput,
  UpdateGradeBandInput,
  UpdateJobPositionInput,
  UpdateLegalEntityInput,
  UpdateLocationInput,
} from './org.model';
import { ValidationError } from './employee.validation';

function requireString(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (typeof value !== 'string' || value.trim() === '') {
    details.push({ field, reason: 'must be a non-empty string' });
  }
}

function validateStatus(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (value !== undefined && !ORG_ENTITY_STATUSES.includes(value as OrgEntityStatus)) {
    details.push({ field, reason: `must be one of: ${ORG_ENTITY_STATUSES.join(', ')}` });
  }
}

function validateOptionalString(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (value !== undefined && (typeof value !== 'string' || value.trim() === '')) {
    details.push({ field, reason: 'must be a non-empty string when provided' });
  }
}

function validatePositiveInteger(details: Array<{ field: string; reason: string }>, field: string, value: unknown): void {
  if (value !== undefined && (!Number.isInteger(value) || Number(value) < 1)) {
    details.push({ field, reason: 'must be a positive integer' });
  }
}

function throwIfDetails(details: Array<{ field: string; reason: string }>): void {
  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateCreateBusinessUnit(input: CreateBusinessUnitInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'name', input.name);
  requireString(details, 'code', input.code);
  validateOptionalString(details, 'description', input.description);
  validateOptionalString(details, 'parent_business_unit_id', input.parent_business_unit_id);
  validateOptionalString(details, 'leader_employee_id', input.leader_employee_id);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateUpdateBusinessUnit(input: UpdateBusinessUnitInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  validateOptionalString(details, 'name', input.name);
  validateOptionalString(details, 'code', input.code);
  validateOptionalString(details, 'description', input.description);
  validateOptionalString(details, 'parent_business_unit_id', input.parent_business_unit_id);
  validateOptionalString(details, 'leader_employee_id', input.leader_employee_id);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateCreateLegalEntity(input: CreateLegalEntityInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'name', input.name);
  requireString(details, 'code', input.code);
  validateOptionalString(details, 'registration_number', input.registration_number);
  validateOptionalString(details, 'tax_identifier', input.tax_identifier);
  validateOptionalString(details, 'business_unit_id', input.business_unit_id);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateUpdateLegalEntity(input: UpdateLegalEntityInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  validateOptionalString(details, 'name', input.name);
  validateOptionalString(details, 'code', input.code);
  validateOptionalString(details, 'registration_number', input.registration_number);
  validateOptionalString(details, 'tax_identifier', input.tax_identifier);
  validateOptionalString(details, 'business_unit_id', input.business_unit_id);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateCreateLocation(input: CreateLocationInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'name', input.name);
  requireString(details, 'code', input.code);
  requireString(details, 'country_code', input.country_code);
  requireString(details, 'timezone', input.timezone);
  validateOptionalString(details, 'address_line_1', input.address_line_1);
  validateOptionalString(details, 'address_line_2', input.address_line_2);
  validateOptionalString(details, 'city', input.city);
  validateOptionalString(details, 'state_or_region', input.state_or_region);
  validateOptionalString(details, 'postal_code', input.postal_code);
  validateOptionalString(details, 'legal_entity_id', input.legal_entity_id);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateUpdateLocation(input: UpdateLocationInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  validateOptionalString(details, 'name', input.name);
  validateOptionalString(details, 'code', input.code);
  validateOptionalString(details, 'country_code', input.country_code);
  validateOptionalString(details, 'timezone', input.timezone);
  validateOptionalString(details, 'address_line_1', input.address_line_1);
  validateOptionalString(details, 'address_line_2', input.address_line_2);
  validateOptionalString(details, 'city', input.city);
  validateOptionalString(details, 'state_or_region', input.state_or_region);
  validateOptionalString(details, 'postal_code', input.postal_code);
  validateOptionalString(details, 'legal_entity_id', input.legal_entity_id);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateCreateCostCenter(input: CreateCostCenterInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'name', input.name);
  requireString(details, 'code', input.code);
  validateOptionalString(details, 'business_unit_id', input.business_unit_id);
  validateOptionalString(details, 'department_id', input.department_id);
  validateOptionalString(details, 'legal_entity_id', input.legal_entity_id);
  validateOptionalString(details, 'manager_employee_id', input.manager_employee_id);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateUpdateCostCenter(input: UpdateCostCenterInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  validateOptionalString(details, 'name', input.name);
  validateOptionalString(details, 'code', input.code);
  validateOptionalString(details, 'business_unit_id', input.business_unit_id);
  validateOptionalString(details, 'department_id', input.department_id);
  validateOptionalString(details, 'legal_entity_id', input.legal_entity_id);
  validateOptionalString(details, 'manager_employee_id', input.manager_employee_id);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateCreateGradeBand(input: CreateGradeBandInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'name', input.name);
  requireString(details, 'code', input.code);
  validateOptionalString(details, 'family', input.family);
  validatePositiveInteger(details, 'level_order', input.level_order);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateUpdateGradeBand(input: UpdateGradeBandInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  validateOptionalString(details, 'name', input.name);
  validateOptionalString(details, 'code', input.code);
  validateOptionalString(details, 'family', input.family);
  validatePositiveInteger(details, 'level_order', input.level_order);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateCreateJobPosition(input: CreateJobPositionInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  requireString(details, 'title', input.title);
  requireString(details, 'code', input.code);
  requireString(details, 'department_id', input.department_id);
  validateOptionalString(details, 'business_unit_id', input.business_unit_id);
  validateOptionalString(details, 'legal_entity_id', input.legal_entity_id);
  validateOptionalString(details, 'location_id', input.location_id);
  validateOptionalString(details, 'grade_band_id', input.grade_band_id);
  validateOptionalString(details, 'role_id', input.role_id);
  validateOptionalString(details, 'reports_to_position_id', input.reports_to_position_id);
  validateOptionalString(details, 'default_cost_center_id', input.default_cost_center_id);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}

export function validateUpdateJobPosition(input: UpdateJobPositionInput): void {
  const details: Array<{ field: string; reason: string }> = [];
  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }
  validateOptionalString(details, 'title', input.title);
  validateOptionalString(details, 'code', input.code);
  validateOptionalString(details, 'department_id', input.department_id);
  validateOptionalString(details, 'business_unit_id', input.business_unit_id);
  validateOptionalString(details, 'legal_entity_id', input.legal_entity_id);
  validateOptionalString(details, 'location_id', input.location_id);
  validateOptionalString(details, 'grade_band_id', input.grade_band_id);
  validateOptionalString(details, 'role_id', input.role_id);
  validateOptionalString(details, 'reports_to_position_id', input.reports_to_position_id);
  validateOptionalString(details, 'default_cost_center_id', input.default_cost_center_id);
  validateStatus(details, 'status', input.status);
  throwIfDetails(details);
}
