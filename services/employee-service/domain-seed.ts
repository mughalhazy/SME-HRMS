import { Department } from './department.model';
import { BusinessUnit, CostCenter, GradeBand, JobPosition, LegalEntity, Location } from './org.model';
import { DEFAULT_ROLE_PERMISSIONS, Role } from './role.model';

export const DEFAULT_TENANT_ID = 'tenant-default';

export function timestampSeed(): string {
  return '2026-01-01T00:00:00.000Z';
}

export function seedDepartments(tenantId: string = DEFAULT_TENANT_ID): Department[] {
  const createdAt = timestampSeed();
  return [
    {
      tenant_id: tenantId,
      department_id: 'dep-hr',
      name: 'People Operations',
      code: 'HR',
      description: 'People operations, talent, and compliance.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      department_id: 'dep-eng',
      name: 'Engineering',
      code: 'ENG',
      description: 'Product engineering and platform delivery.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      department_id: 'dep-fin',
      name: 'Finance',
      code: 'FIN',
      description: 'Financial planning, accounting, and reporting.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      department_id: 'dep-ops',
      name: 'Operations',
      code: 'OPS',
      description: 'Operational readiness and shared services.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      department_id: 'dep-archive',
      name: 'Legacy Programs',
      code: 'LEG',
      description: 'Archived organizational area retained for history.',
      status: 'Archived',
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

export function seedRoles(tenantId: string = DEFAULT_TENANT_ID): Role[] {
  const createdAt = timestampSeed();
  return [
    {
      tenant_id: tenantId,
      role_id: 'role-hr-director',
      title: 'HR Director',
      level: 'Director',
      description: 'Owns people strategy and HR operations.',
      employment_category: 'Executive',
      permissions: DEFAULT_ROLE_PERMISSIONS.Executive,
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      role_id: 'role-frontend-engineer',
      title: 'Frontend Engineer',
      level: 'IC3',
      description: 'Builds and maintains UI applications.',
      employment_category: 'Staff',
      permissions: DEFAULT_ROLE_PERMISSIONS.Staff,
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      role_id: 'role-finance-manager',
      title: 'Finance Manager',
      level: 'M2',
      description: 'Leads the finance operating cadence.',
      employment_category: 'Manager',
      permissions: DEFAULT_ROLE_PERMISSIONS.Manager,
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      role_id: 'role-ops-lead',
      title: 'Operations Lead',
      level: 'M1',
      description: 'Coordinates operations execution.',
      employment_category: 'Manager',
      permissions: DEFAULT_ROLE_PERMISSIONS.Manager,
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      role_id: 'role-contractor-consultant',
      title: 'Contractor Consultant',
      level: 'Contract',
      description: 'Active contractor role for external workforce assignments.',
      employment_category: 'Contractor',
      permissions: DEFAULT_ROLE_PERMISSIONS.Contractor,
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      role_id: 'role-legacy-contractor',
      title: 'Legacy Contractor',
      level: 'Contract',
      description: 'Retired contract role retained for compatibility.',
      employment_category: 'Contractor',
      permissions: DEFAULT_ROLE_PERMISSIONS.Contractor,
      status: 'Inactive',
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

export function seedBusinessUnits(tenantId: string = DEFAULT_TENANT_ID): BusinessUnit[] {
  const createdAt = timestampSeed();
  return [
    {
      tenant_id: tenantId,
      business_unit_id: 'bu-corp',
      name: 'Corporate Services',
      code: 'CORP',
      description: 'Shared services spanning HR, finance, and operations.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      business_unit_id: 'bu-product',
      name: 'Product & Engineering',
      code: 'PROD',
      description: 'Product delivery, engineering, and platform operations.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

export function seedLegalEntities(tenantId: string = DEFAULT_TENANT_ID): LegalEntity[] {
  const createdAt = timestampSeed();
  return [
    {
      tenant_id: tenantId,
      legal_entity_id: 'le-us-main',
      name: 'SME HRMS USA Inc.',
      code: 'USMAIN',
      registration_number: 'US-2026-001',
      tax_identifier: '99-0000001',
      business_unit_id: 'bu-corp',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      legal_entity_id: 'le-product-labs',
      name: 'SME Product Labs LLC',
      code: 'PRODLABS',
      registration_number: 'US-2026-002',
      tax_identifier: '99-0000002',
      business_unit_id: 'bu-product',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

export function seedLocations(tenantId: string = DEFAULT_TENANT_ID): Location[] {
  const createdAt = timestampSeed();
  return [
    {
      tenant_id: tenantId,
      location_id: 'loc-nyc',
      name: 'New York HQ',
      code: 'NYC-HQ',
      city: 'New York',
      state_or_region: 'NY',
      country_code: 'US',
      timezone: 'America/New_York',
      legal_entity_id: 'le-us-main',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      location_id: 'loc-sfo',
      name: 'San Francisco Hub',
      code: 'SFO-HUB',
      city: 'San Francisco',
      state_or_region: 'CA',
      country_code: 'US',
      timezone: 'America/Los_Angeles',
      legal_entity_id: 'le-product-labs',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

export function seedCostCenters(tenantId: string = DEFAULT_TENANT_ID): CostCenter[] {
  const createdAt = timestampSeed();
  return [
    {
      tenant_id: tenantId,
      cost_center_id: 'cc-hr-001',
      name: 'People Operations Core',
      code: 'HR-001',
      business_unit_id: 'bu-corp',
      department_id: 'dep-hr',
      legal_entity_id: 'le-us-main',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      cost_center_id: 'cc-eng-001',
      name: 'Engineering Product Delivery',
      code: 'ENG-001',
      business_unit_id: 'bu-product',
      department_id: 'dep-eng',
      legal_entity_id: 'le-product-labs',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

export function seedGradeBands(tenantId: string = DEFAULT_TENANT_ID): GradeBand[] {
  const createdAt = timestampSeed();
  return [
    {
      tenant_id: tenantId,
      grade_band_id: 'gb-ic3',
      name: 'IC3',
      code: 'IC3',
      family: 'Individual Contributor',
      level_order: 3,
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      grade_band_id: 'gb-m2',
      name: 'M2',
      code: 'M2',
      family: 'Management',
      level_order: 6,
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}

export function seedJobPositions(tenantId: string = DEFAULT_TENANT_ID): JobPosition[] {
  const createdAt = timestampSeed();
  return [
    {
      tenant_id: tenantId,
      job_position_id: 'pos-hr-director',
      title: 'HR Director',
      code: 'POS-HR-DIR',
      department_id: 'dep-hr',
      business_unit_id: 'bu-corp',
      legal_entity_id: 'le-us-main',
      location_id: 'loc-nyc',
      grade_band_id: 'gb-m2',
      role_id: 'role-hr-director',
      default_cost_center_id: 'cc-hr-001',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      tenant_id: tenantId,
      job_position_id: 'pos-frontend-engineer',
      title: 'Frontend Engineer',
      code: 'POS-FE-ENG',
      department_id: 'dep-eng',
      business_unit_id: 'bu-product',
      legal_entity_id: 'le-product-labs',
      location_id: 'loc-sfo',
      grade_band_id: 'gb-ic3',
      role_id: 'role-frontend-engineer',
      default_cost_center_id: 'cc-eng-001',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
  ];
}
