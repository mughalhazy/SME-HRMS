export const DEPARTMENT_STATUSES = ['Proposed', 'Active', 'Inactive', 'Archived'] as const;
export type DepartmentStatus = (typeof DEPARTMENT_STATUSES)[number];

export interface Department {
  department_id: string;
  name: string;
  code: string;
  description?: string;
  parent_department_id?: string;
  head_employee_id?: string;
  status: DepartmentStatus;
  created_at: string;
  updated_at: string;
}

export interface CreateDepartmentInput {
  name: string;
  code: string;
  description?: string;
  parent_department_id?: string;
  head_employee_id?: string;
  status?: DepartmentStatus;
}

export interface UpdateDepartmentInput {
  name?: string;
  code?: string;
  description?: string;
  parent_department_id?: string;
  head_employee_id?: string;
  status?: DepartmentStatus;
}

export interface DepartmentFilters {
  department_id?: string;
  status?: DepartmentStatus;
  parent_department_id?: string;
  head_employee_id?: string;
  limit?: number;
  cursor?: string;
}
