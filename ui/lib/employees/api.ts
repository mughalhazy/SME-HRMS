import { apiRequest } from '@/lib/api/client'

import type {
  CreateEmployeeInput,
  Employee,
  EmployeeFilters,
  EmployeeListResponse,
  EmployeeResponse,
  UpdateEmployeeInput,
} from './types'

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

export function listEmployees(filters: EmployeeFilters = {}) {
  return apiRequest<EmployeeListResponse>(`/api/v1/employees${toQueryString(filters)}`)
}

export function getEmployee(employeeId: string) {
  return apiRequest<EmployeeResponse>(`/api/v1/employees/${employeeId}`)
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
