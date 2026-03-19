import { Department } from './department.model';
import { DEFAULT_ROLE_PERMISSIONS, Role } from './role.model';

export function timestampSeed(): string {
  return '2026-01-01T00:00:00.000Z';
}

export function seedDepartments(): Department[] {
  const createdAt = timestampSeed();
  return [
    {
      department_id: 'dep-hr',
      name: 'People Operations',
      code: 'HR',
      description: 'People operations, talent, and compliance.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      department_id: 'dep-eng',
      name: 'Engineering',
      code: 'ENG',
      description: 'Product engineering and platform delivery.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      department_id: 'dep-fin',
      name: 'Finance',
      code: 'FIN',
      description: 'Financial planning, accounting, and reporting.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
      department_id: 'dep-ops',
      name: 'Operations',
      code: 'OPS',
      description: 'Operational readiness and shared services.',
      status: 'Active',
      created_at: createdAt,
      updated_at: createdAt,
    },
    {
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

export function seedRoles(): Role[] {
  const createdAt = timestampSeed();
  return [
    {
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
