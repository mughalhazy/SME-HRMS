export const EMPLOYMENT_TYPES = ['FullTime', 'PartTime', 'Contract', 'Intern'] as const;
export type EmploymentType = (typeof EMPLOYMENT_TYPES)[number];

export const EMPLOYEE_STATUSES = ['Draft', 'Active', 'OnLeave', 'Suspended', 'Terminated'] as const;
export type EmployeeStatus = (typeof EMPLOYEE_STATUSES)[number];

export interface Employee {
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

export interface CreateEmployeeInput {
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
  employee_id?: string;
  department_id?: string;
  status?: EmployeeStatus;
  limit?: number;
  cursor?: string;
}
