export const ORG_ENTITY_STATUSES = ['Draft', 'Active', 'Inactive', 'Archived'] as const;
export type OrgEntityStatus = (typeof ORG_ENTITY_STATUSES)[number];

export const REPORTING_RELATIONSHIP_TYPES = ['Primary', 'Matrix'] as const;
export type ReportingRelationshipType = (typeof REPORTING_RELATIONSHIP_TYPES)[number];

export type OrgEntityKind =
  | 'business_unit'
  | 'legal_entity'
  | 'location'
  | 'cost_center'
  | 'grade_band'
  | 'job_position';

export interface BusinessUnit {
  tenant_id: string;
  business_unit_id: string;
  name: string;
  code: string;
  description?: string;
  parent_business_unit_id?: string;
  leader_employee_id?: string;
  status: OrgEntityStatus;
  created_at: string;
  updated_at: string;
}

export interface LegalEntity {
  tenant_id: string;
  legal_entity_id: string;
  name: string;
  code: string;
  registration_number?: string;
  tax_identifier?: string;
  business_unit_id?: string;
  status: OrgEntityStatus;
  created_at: string;
  updated_at: string;
}

export interface Location {
  tenant_id: string;
  location_id: string;
  name: string;
  code: string;
  address_line_1?: string;
  address_line_2?: string;
  city?: string;
  state_or_region?: string;
  postal_code?: string;
  country_code: string;
  timezone: string;
  legal_entity_id?: string;
  status: OrgEntityStatus;
  created_at: string;
  updated_at: string;
}

export interface CostCenter {
  tenant_id: string;
  cost_center_id: string;
  name: string;
  code: string;
  business_unit_id?: string;
  department_id?: string;
  legal_entity_id?: string;
  manager_employee_id?: string;
  status: OrgEntityStatus;
  created_at: string;
  updated_at: string;
}

export interface GradeBand {
  tenant_id: string;
  grade_band_id: string;
  name: string;
  code: string;
  family?: string;
  level_order: number;
  status: OrgEntityStatus;
  created_at: string;
  updated_at: string;
}

export interface JobPosition {
  tenant_id: string;
  job_position_id: string;
  title: string;
  code: string;
  department_id: string;
  business_unit_id?: string;
  legal_entity_id?: string;
  location_id?: string;
  grade_band_id?: string;
  role_id?: string;
  reports_to_position_id?: string;
  default_cost_center_id?: string;
  status: OrgEntityStatus;
  created_at: string;
  updated_at: string;
}

export interface ReportingLine {
  reporting_line_id: string;
  tenant_id: string;
  employee_id: string;
  manager_employee_id: string;
  relationship_type: ReportingRelationshipType;
  purpose?: string;
  created_at: string;
  updated_at: string;
}

export interface EmployeeCostAllocation {
  cost_center_id: string;
  allocation_percentage: number;
  is_primary?: boolean;
}

export interface OrgEntityFilters {
  tenant_id?: string;
  entity_id?: string;
  status?: OrgEntityStatus;
  business_unit_id?: string;
  department_id?: string;
  legal_entity_id?: string;
  manager_employee_id?: string;
  parent_entity_id?: string;
  limit?: number;
  cursor?: string;
}

export type CreateBusinessUnitInput = Pick<BusinessUnit, 'name' | 'code'> & Partial<Pick<BusinessUnit, 'description' | 'parent_business_unit_id' | 'leader_employee_id' | 'status'>> & { tenant_id?: string };
export type UpdateBusinessUnitInput = Partial<Pick<BusinessUnit, 'name' | 'code' | 'description' | 'parent_business_unit_id' | 'leader_employee_id' | 'status'>>;

export type CreateLegalEntityInput = Pick<LegalEntity, 'name' | 'code'> & Partial<Pick<LegalEntity, 'registration_number' | 'tax_identifier' | 'business_unit_id' | 'status'>> & { tenant_id?: string };
export type UpdateLegalEntityInput = Partial<Pick<LegalEntity, 'name' | 'code' | 'registration_number' | 'tax_identifier' | 'business_unit_id' | 'status'>>;

export type CreateLocationInput = Pick<Location, 'name' | 'code' | 'country_code' | 'timezone'> & Partial<Pick<Location, 'address_line_1' | 'address_line_2' | 'city' | 'state_or_region' | 'postal_code' | 'legal_entity_id' | 'status'>> & { tenant_id?: string };
export type UpdateLocationInput = Partial<Pick<Location, 'name' | 'code' | 'country_code' | 'timezone' | 'address_line_1' | 'address_line_2' | 'city' | 'state_or_region' | 'postal_code' | 'legal_entity_id' | 'status'>>;

export type CreateCostCenterInput = Pick<CostCenter, 'name' | 'code'> & Partial<Pick<CostCenter, 'business_unit_id' | 'department_id' | 'legal_entity_id' | 'manager_employee_id' | 'status'>> & { tenant_id?: string };
export type UpdateCostCenterInput = Partial<Pick<CostCenter, 'name' | 'code' | 'business_unit_id' | 'department_id' | 'legal_entity_id' | 'manager_employee_id' | 'status'>>;

export type CreateGradeBandInput = Pick<GradeBand, 'name' | 'code' | 'level_order'> & Partial<Pick<GradeBand, 'family' | 'status'>> & { tenant_id?: string };
export type UpdateGradeBandInput = Partial<Pick<GradeBand, 'name' | 'code' | 'level_order' | 'family' | 'status'>>;

export type CreateJobPositionInput = Pick<JobPosition, 'title' | 'code' | 'department_id'> & Partial<Pick<JobPosition, 'business_unit_id' | 'legal_entity_id' | 'location_id' | 'grade_band_id' | 'role_id' | 'reports_to_position_id' | 'default_cost_center_id' | 'status'>> & { tenant_id?: string };
export type UpdateJobPositionInput = Partial<Pick<JobPosition, 'title' | 'code' | 'department_id' | 'business_unit_id' | 'legal_entity_id' | 'location_id' | 'grade_band_id' | 'role_id' | 'reports_to_position_id' | 'default_cost_center_id' | 'status'>>;
