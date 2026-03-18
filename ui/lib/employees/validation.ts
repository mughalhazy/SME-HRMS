import { EMPLOYEE_STATUSES, EMPLOYMENT_TYPES, type EmployeeFormValues } from './types'

export type EmployeeFormErrors = Partial<Record<keyof EmployeeFormValues, string>>

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const isoDateRegex = /^\d{4}-\d{2}-\d{2}$/

function isIsoDate(value: string): boolean {
  return isoDateRegex.test(value) && !Number.isNaN(Date.parse(value))
}

export function validateEmployeeForm(values: EmployeeFormValues, mode: 'create' | 'edit'): EmployeeFormErrors {
  const errors: EmployeeFormErrors = {}

  if (mode === 'create' && values.employee_number.trim() === '') {
    errors.employee_number = 'Employee number is required.'
  }

  if (values.first_name.trim() === '') {
    errors.first_name = 'First name is required.'
  }

  if (values.last_name.trim() === '') {
    errors.last_name = 'Last name is required.'
  }

  if (values.email.trim() === '') {
    errors.email = 'Email is required.'
  } else if (!emailRegex.test(values.email)) {
    errors.email = 'Enter a valid email address.'
  }

  if (values.phone.trim() !== '' && values.phone.trim().length < 7) {
    errors.phone = 'Phone number looks too short.'
  }

  if (values.hire_date.trim() === '') {
    errors.hire_date = 'Hire date is required.'
  } else if (!isIsoDate(values.hire_date)) {
    errors.hire_date = 'Use YYYY-MM-DD for the hire date.'
  }

  if (!EMPLOYMENT_TYPES.includes(values.employment_type)) {
    errors.employment_type = 'Choose a valid employment type.'
  }

  if (!EMPLOYEE_STATUSES.includes(values.status)) {
    errors.status = 'Choose a valid employee status.'
  }

  if (values.department_id.trim() === '') {
    errors.department_id = 'Department is required.'
  }

  if (values.role_id.trim() === '') {
    errors.role_id = 'Role is required.'
  }

  if (values.manager_employee_id.trim() !== '' && values.manager_employee_id.trim() === values.employee_number.trim()) {
    errors.manager_employee_id = 'Manager cannot match the employee number.'
  }

  return errors
}
