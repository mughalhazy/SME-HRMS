import { ApiError, apiRequest } from '@/lib/api/client'

import type {
  CreateEmployeeInput,
  Employee,
  EmployeeFilters,
  EmployeeListResponse,
  EmployeeResponse,
  UpdateEmployeeInput,
} from './types'

const DEMO_EMPLOYEES: Employee[] = [
  {
    employee_id: 'emp_demo_001',
    employee_number: 'E-001',
    first_name: 'Amina',
    last_name: 'Yusuf',
    email: 'amina.yusuf@example.com',
    phone: '+1 555-0101',
    hire_date: '2023-02-14',
    employment_type: 'FullTime',
    status: 'Active',
    department_id: 'dep-fin',
    role_id: 'role-finance-manager',
    manager_employee_id: 'emp_demo_004',
    created_at: '2023-02-14T09:00:00.000Z',
    updated_at: '2026-03-18T08:00:00.000Z',
  },
  {
    employee_id: 'emp_demo_002',
    employee_number: 'E-002',
    first_name: 'Jordan',
    last_name: 'Kim',
    email: 'jordan.kim@example.com',
    phone: '+1 555-0102',
    hire_date: '2024-06-10',
    employment_type: 'FullTime',
    status: 'OnLeave',
    department_id: 'dep-ops',
    role_id: 'role-ops-lead',
    manager_employee_id: 'emp_demo_005',
    created_at: '2024-06-10T09:00:00.000Z',
    updated_at: '2026-03-17T15:12:00.000Z',
  },
  {
    employee_id: 'emp_demo_003',
    employee_number: 'E-003',
    first_name: 'Noah',
    last_name: 'Bennett',
    email: 'noah.bennett@example.com',
    phone: '+1 555-0103',
    hire_date: '2022-09-01',
    employment_type: 'Contract',
    status: 'Active',
    department_id: 'dep-eng',
    role_id: 'role-frontend-engineer',
    manager_employee_id: 'emp_demo_006',
    created_at: '2022-09-01T09:00:00.000Z',
    updated_at: '2026-03-16T11:40:00.000Z',
  },
]

function toQueryString(filters: EmployeeFilters = {}): string {
  const params = new URLSearchParams()

  if (filters.status && filters.status !== 'all') {
    params.set('status', filters.status)
  }

  if (filters.departmentId) {
    params.set('department_id', filters.departmentId)
  }

  if (filters.limit) {
    params.set('limit', String(filters.limit))
  }

  if (filters.cursor) {
    params.set('cursor', filters.cursor)
  }

  const query = params.toString()
  return query ? `?${query}` : ''
}

function filterDemoEmployees(filters: EmployeeFilters = {}) {
  return DEMO_EMPLOYEES.filter((employee) => {
    if (filters.status && filters.status !== 'all' && employee.status !== filters.status) {
      return false
    }

    if (filters.departmentId && employee.department_id !== filters.departmentId) {
      return false
    }

    return true
  })
}

function demoListResponse(filters: EmployeeFilters = {}): EmployeeListResponse {
  const rows = filterDemoEmployees(filters)
  const limited = rows.slice(0, filters.limit ?? 25)

  return {
    data: limited,
    page: {
      nextCursor: null,
      hasNext: false,
      limit: filters.limit ?? 25,
    },
  }
}

export async function listEmployees(filters: EmployeeFilters = {}) {
  try {
    return await apiRequest<EmployeeListResponse>(`/api/v1/employees${toQueryString(filters)}`)
  } catch (error) {
    if (error instanceof ApiError || error instanceof TypeError) {
      return demoListResponse(filters)
    }

    throw error
  }
}

export async function getEmployee(employeeId: string) {
  try {
    return await apiRequest<EmployeeResponse>(`/api/v1/employees/${employeeId}`)
  } catch (error) {
    if (error instanceof ApiError || error instanceof TypeError) {
      const fallback = DEMO_EMPLOYEES.find((employee) => employee.employee_id === employeeId) ?? DEMO_EMPLOYEES[0]
      return { data: fallback }
    }

    throw error
  }
}

export function createEmployee(payload: CreateEmployeeInput) {
  return apiRequest<EmployeeResponse>('/api/v1/employees', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateEmployee(employeeId: string, payload: UpdateEmployeeInput) {
  return apiRequest<EmployeeResponse>(`/api/v1/employees/${employeeId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function getEmployeeFullName(employee: Pick<Employee, 'first_name' | 'last_name'>): string {
  return `${employee.first_name} ${employee.last_name}`.trim()
}
