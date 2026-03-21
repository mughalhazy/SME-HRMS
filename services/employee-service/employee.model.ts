export const EMPLOYMENT_TYPES = ['FullTime', 'PartTime', 'Contract', 'Intern'] as const;
export type EmploymentType = (typeof EMPLOYMENT_TYPES)[number];

export const EMPLOYEE_STATUSES = ['Draft', 'Active', 'OnLeave', 'Suspended', 'Terminated'] as const;
export type EmployeeStatus = (typeof EMPLOYEE_STATUSES)[number];

export const DEPARTMENT_STATUSES = ['Proposed', 'Active', 'Inactive', 'Archived'] as const;
export type DepartmentStatus = (typeof DEPARTMENT_STATUSES)[number];

export const ROLE_EMPLOYMENT_CATEGORIES = ['Staff', 'Manager', 'Executive', 'Contractor'] as const;
export type RoleEmploymentCategory = (typeof ROLE_EMPLOYMENT_CATEGORIES)[number];

export const ROLE_STATUSES = ['Draft', 'Active', 'Inactive', 'Archived'] as const;
export type RoleStatus = (typeof ROLE_STATUSES)[number];

export interface Department {
  tenant_id: string;
  department_id: string;
  name: string;
  code: string;
  description?: string;
  head_employee_id?: string;
  status: DepartmentStatus;
  created_at: string;
  updated_at: string;
}

export interface Role {
  tenant_id: string;
  role_id: string;
  title: string;
  level?: string;
  description?: string;
  employment_category: RoleEmploymentCategory;
  status: RoleStatus;
  created_at: string;
  updated_at: string;
}

export interface Employee {
  tenant_id: string;
  employee_id: string;
  employee_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  hire_date: string;
  employment_type: EmploymentType;
  status: EmployeeStatus;
  department_id: string;
  role_id: string;
  manager_employee_id?: string;
  created_at: string;
  updated_at: string;
}

export interface EmployeeDirectoryReadModel {
  tenant_id: string;
  employee_id: string;
  employee_number: string;
  full_name: string;
  email: string;
  phone?: string;
  hire_date: string;
  employment_type: EmploymentType;
  employee_status: EmployeeStatus;
  department_id: string;
  department_name: string;
  role_id: string;
  role_title: string;
  manager_employee_id?: string;
  manager_name?: string;
  updated_at: string;
}

export interface OrganizationStructureReadModel {
  tenant_id: string;
  department_id: string;
  department_name: string;
  department_code: string;
  department_status: DepartmentStatus;
  head_employee_id?: string;
  head_employee_name?: string;
  employee_id: string;
  employee_name: string;
  employee_status: EmployeeStatus;
  manager_employee_id?: string;
  manager_name?: string;
  role_id: string;
  role_title: string;
  updated_at: string;
}

export interface EmployeeReadModelBundle {
  employee_directory_view: EmployeeDirectoryReadModel;
  organization_structure_view: OrganizationStructureReadModel;
}

export interface EmployeeListReadModelBundle {
  employee_directory_view: EmployeeDirectoryReadModel[];
  organization_structure_view: OrganizationStructureReadModel[];
}

export interface CreateEmployeeInput {
  tenant_id?: string;
  employee_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  hire_date: string;
  employment_type: EmploymentType;
  status?: EmployeeStatus;
  department_id: string;
  role_id: string;
  manager_employee_id?: string;
}

export interface UpdateEmployeeInput {
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  hire_date?: string;
  employment_type?: EmploymentType;
  department_id?: string;
  role_id?: string;
  manager_employee_id?: string;
}

export interface EmployeeFilters {
  tenant_id?: string;
  employee_id?: string;
  department_id?: string;
  role_id?: string;
  status?: EmployeeStatus;
  limit?: number;
  cursor?: string;
}
