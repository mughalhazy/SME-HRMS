export const ROLE_STATUSES = ['Draft', 'Active', 'Inactive', 'Archived'] as const;
export const EMPLOYMENT_CATEGORIES = ['Staff', 'Manager', 'Executive', 'Contractor'] as const;
export const ROLE_PERMISSION_CODES = [
  'CAP-EMP-001',
  'CAP-EMP-002',
  'CAP-ATT-001',
  'CAP-ATT-002',
  'CAP-LEV-001',
  'CAP-LEV-002',
  'CAP-PAY-001',
  'CAP-PAY-002',
  'CAP-HIR-001',
  'CAP-HIR-002',
  'CAP-PRF-001',
] as const;

export type RoleStatus = (typeof ROLE_STATUSES)[number];
export type EmploymentCategory = (typeof EMPLOYMENT_CATEGORIES)[number];
export type RolePermissionCode = (typeof ROLE_PERMISSION_CODES)[number];

export interface RolePermissionMapping {
  role_template: EmploymentCategory;
  permissions: RolePermissionCode[];
}

export interface Role {
  tenant_id: string;
  role_id: string;
  title: string;
  level?: string;
  description?: string;
  employment_category: EmploymentCategory;
  status: RoleStatus;
  permissions: RolePermissionCode[];
  created_at: string;
  updated_at: string;
}

export interface CreateRoleInput {
  tenant_id?: string;
  title: string;
  level?: string;
  description?: string;
  employment_category: EmploymentCategory;
  status?: RoleStatus;
  permissions?: RolePermissionCode[];
}

export interface UpdateRoleInput {
  title?: string;
  level?: string;
  description?: string;
  employment_category?: EmploymentCategory;
  status?: RoleStatus;
  permissions?: RolePermissionCode[];
}

export interface RoleFilters {
  tenant_id?: string;
  status?: RoleStatus;
  employment_category?: EmploymentCategory;
}

export const DEFAULT_ROLE_PERMISSIONS: Record<EmploymentCategory, RolePermissionCode[]> = {
  Staff: ['CAP-EMP-001', 'CAP-ATT-001', 'CAP-LEV-001', 'CAP-PRF-001'],
  Manager: ['CAP-EMP-001', 'CAP-EMP-002', 'CAP-ATT-001', 'CAP-ATT-002', 'CAP-LEV-001', 'CAP-LEV-002', 'CAP-HIR-001', 'CAP-HIR-002', 'CAP-PRF-001'],
  Executive: ['CAP-EMP-001', 'CAP-EMP-002', 'CAP-ATT-001', 'CAP-ATT-002', 'CAP-LEV-001', 'CAP-LEV-002', 'CAP-PAY-001', 'CAP-HIR-001', 'CAP-HIR-002', 'CAP-PRF-001'],
  Contractor: ['CAP-EMP-001', 'CAP-ATT-001', 'CAP-LEV-001'],
};

export function resolveRolePermissions(input: {
  employment_category: EmploymentCategory;
  permissions?: RolePermissionCode[];
}): RolePermissionCode[] {
  const permissions = input.permissions ?? DEFAULT_ROLE_PERMISSIONS[input.employment_category];
  return [...new Set(permissions)].sort();
}
