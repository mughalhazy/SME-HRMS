import type { CreateEmployeeInput, Employee, EmployeeFilters, EmployeeListResponse, EmployeeResponse, UpdateEmployeeInput } from '@/lib/employees/types'

import { clone, getMockDb, nowIso, randomId, simulateLatency, toTitleName } from './shared'

function matchesFilters(employee: Employee, filters: EmployeeFilters = {}) {
  if (filters.status && filters.status !== 'all' && employee.status !== filters.status) {
    return false
  }

  if (filters.departmentId && employee.department_id !== filters.departmentId) {
    return false
  }

  return true
}

export async function listEmployeesMock(filters: EmployeeFilters = {}): Promise<EmployeeListResponse> {
  await simulateLatency()

  const rows = getMockDb().employees
    .filter((employee) => matchesFilters(employee, filters))
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))

  const offset = filters.cursor ? Number(filters.cursor) : 0
  const limit = filters.limit ?? 25
  const pageRows = rows.slice(offset, offset + limit).map((row) => clone<Employee>(row))
  const nextOffset = offset + limit

  return {
    data: pageRows,
    page: {
      nextCursor: nextOffset < rows.length ? String(nextOffset) : null,
      hasNext: nextOffset < rows.length,
      limit,
    },
  }
}

export async function getEmployeeMock(employeeId: string): Promise<EmployeeResponse> {
  await simulateLatency()

  const row = getMockDb().employees.find((employee) => employee.employee_id === employeeId)
  return {
    data: clone<Employee>(row ?? getMockDb().employees[0]),
  }
}

export async function createEmployeeMock(payload: CreateEmployeeInput, options?: { failRate?: number }): Promise<EmployeeResponse> {
  await simulateLatency({ failRate: options?.failRate ?? 0.08 })

  const db = getMockDb()
  const timestamp = nowIso()
  const employee: Employee = {
    employee_id: randomId('emp'),
    employee_number: payload.employee_number,
    first_name: payload.first_name,
    last_name: payload.last_name,
    email: payload.email,
    phone: payload.phone,
    hire_date: payload.hire_date,
    employment_type: payload.employment_type,
    status: payload.status ?? 'Active',
    department_id: payload.department_id,
    role_id: payload.role_id,
    manager_employee_id: payload.manager_employee_id,
    created_at: timestamp,
    updated_at: timestamp,
  }

  const manager = db.employees.find((entry) => entry.employee_id === payload.manager_employee_id)
  db.employees.unshift({
    ...employee,
    full_name: toTitleName(employee.first_name, employee.last_name),
    department_name: payload.department_id,
    role_title: payload.role_id,
    manager_name: manager?.full_name,
  })

  return { data: clone(employee) }
}

export async function updateEmployeeMock(employeeId: string, payload: UpdateEmployeeInput, options?: { failRate?: number }): Promise<EmployeeResponse> {
  await simulateLatency({ failRate: options?.failRate ?? 0.08 })

  const db = getMockDb()
  const employee = db.employees.find((entry) => entry.employee_id === employeeId)

  if (!employee) {
    throw new Error('Employee not found')
  }

  Object.assign(employee, payload)
  employee.full_name = toTitleName(employee.first_name, employee.last_name)
  employee.updated_at = nowIso()
  employee.role_title = employee.role_id
  employee.manager_name = db.employees.find((entry) => entry.employee_id === employee.manager_employee_id)?.full_name

  return {
    data: clone<Employee>(employee),
  }
}
