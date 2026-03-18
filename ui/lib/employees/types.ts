export const EMPLOYMENT_TYPES = ['FullTime', 'PartTime', 'Contract', 'Intern'] as const
export const EMPLOYEE_STATUSES = ['Draft', 'Active', 'OnLeave', 'Suspended', 'Terminated'] as const

export type EmploymentType = (typeof EMPLOYMENT_TYPES)[number]
export type EmployeeStatus = (typeof EMPLOYEE_STATUSES)[number]

export interface Employee {
  employee_id: string
  employee_number: string
  first_name: string
  last_name: string
  email: string
  phone?: string
  hire_date: string
  employment_type: EmploymentType
  status: EmployeeStatus
  department_id: string
  role_id: string
  manager_employee_id?: string
  created_at: string
  updated_at: string
}

export interface EmployeeListResponse {
  data: Employee[]
  page: {
    nextCursor: string | null
    hasNext: boolean
    limit: number
  }
}

export interface EmployeeResponse {
  data: Employee
}

export interface CreateEmployeeInput {
  employee_number: string
  first_name: string
  last_name: string
  email: string
  phone?: string
  hire_date: string
  employment_type: EmploymentType
  status?: EmployeeStatus
  department_id: string
  role_id: string
  manager_employee_id?: string
}

export interface UpdateEmployeeInput {
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
  hire_date?: string
  employment_type?: EmploymentType
  role_id?: string
  manager_employee_id?: string
}

export interface EmployeeFilters {
  status?: EmployeeStatus | 'all'
  departmentId?: string
  limit?: number
  cursor?: string | null
}

export interface EmployeeFormValues {
  employee_number: string
  first_name: string
  last_name: string
  email: string
  phone: string
  hire_date: string
  employment_type: EmploymentType
  status: EmployeeStatus
  department_id: string
  role_id: string
  manager_employee_id: string
}
