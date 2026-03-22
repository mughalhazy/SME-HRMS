'use client'

import type { FormEvent, ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { AlertTriangle, LoaderCircle } from 'lucide-react'

import { Button } from '@/components/base/button'
import { Input, Select, inputClassName } from '@/components/base/input'
import { ApiError } from '@/lib/api/client'
import {
  EMPLOYEE_STATUSES,
  EMPLOYMENT_TYPES,
  type CreateEmployeeInput,
  type Employee,
  type EmployeeFormValues,
  type UpdateEmployeeInput,
} from '@/lib/employees/types'
import { validateEmployeeForm, type EmployeeFormErrors } from '@/lib/employees/validation'

function normalizeValues(values: EmployeeFormValues): EmployeeFormValues {
  return {
    ...values,
    employee_number: values.employee_number.trim(),
    first_name: values.first_name.trim(),
    last_name: values.last_name.trim(),
    email: values.email.trim(),
    phone: values.phone.trim(),
    hire_date: values.hire_date.trim(),
    department_id: values.department_id.trim(),
    role_id: values.role_id.trim(),
    manager_employee_id: values.manager_employee_id.trim(),
  }
}

function toApiPayload(values: EmployeeFormValues, mode: 'create'): CreateEmployeeInput
function toApiPayload(values: EmployeeFormValues, mode: 'edit'): UpdateEmployeeInput
function toApiPayload(values: EmployeeFormValues, mode: 'create' | 'edit'): CreateEmployeeInput | UpdateEmployeeInput {
  const normalized = normalizeValues(values)

  if (mode === 'create') {
    return {
      employee_number: normalized.employee_number,
      first_name: normalized.first_name,
      last_name: normalized.last_name,
      email: normalized.email,
      phone: normalized.phone || undefined,
      hire_date: normalized.hire_date,
      employment_type: normalized.employment_type,
      status: normalized.status,
      department_id: normalized.department_id,
      role_id: normalized.role_id,
      manager_employee_id: normalized.manager_employee_id || undefined,
    }
  }

  return {
    first_name: normalized.first_name,
    last_name: normalized.last_name,
    email: normalized.email,
    phone: normalized.phone || undefined,
    hire_date: normalized.hire_date,
    employment_type: normalized.employment_type,
    role_id: normalized.role_id,
    manager_employee_id: normalized.manager_employee_id || undefined,
  }
}

function getApiFieldErrors(error: unknown): EmployeeFormErrors {
  if (!(error instanceof ApiError)) {
    return {}
  }

  return error.details.reduce<EmployeeFormErrors>((accumulator, detail) => {
    if (detail.field && !(detail.field in accumulator)) {
      const key = detail.field as keyof EmployeeFormValues
      accumulator[key] = detail.reason ?? error.message
    }
    return accumulator
  }, {})
}

function Field({
  label,
  htmlFor,
  error,
  hint,
  children,
}: {
  label: string
  htmlFor: string
  error?: string
  hint?: string
  children: ReactNode
}) {
  return (
    <label htmlFor={htmlFor} className="flex flex-col gap-2 text-sm font-medium text-slate-700">
      <span>{label}</span>
      {children}
      {error ? <span className="text-xs font-medium text-rose-600">{error}</span> : hint ? <span className="text-xs text-slate-500">{hint}</span> : null}
    </label>
  )
}

export function EmployeeForm({
  mode,
  initialValues,
  employee,
  onSubmit,
  onCancel,
}: {
  mode: 'create' | 'edit'
  initialValues: EmployeeFormValues
  employee?: Employee
  onSubmit: (values: EmployeeFormValues) => Promise<void>
  onCancel?: () => void
}) {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState<EmployeeFormErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const heading = useMemo(
    () => (mode === 'create' ? 'Create employee record' : `Edit ${employee?.first_name ?? 'employee'} profile`),
    [employee?.first_name, mode],
  )

  const handleChange = <K extends keyof EmployeeFormValues>(field: K, value: EmployeeFormValues[K]) => {
    setValues((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const nextErrors = validateEmployeeForm(values, mode)
    setErrors(nextErrors)
    setSubmitError(null)

    if (Object.keys(nextErrors).length > 0) {
      return
    }

    try {
      setIsSubmitting(true)
      await onSubmit(values)
    } catch (error) {
      const apiFieldErrors = getApiFieldErrors(error)
      if (Object.keys(apiFieldErrors).length > 0) {
        setErrors((current) => ({ ...current, ...apiFieldErrors }))
      }
      setSubmitError(error instanceof Error ? error.message : 'Unable to save employee.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-surface)]">
      <div className="mb-5 flex flex-col gap-2">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Employee create / edit</p>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">{heading}</h1>
        <p className="max-w-2xl text-sm leading-6 text-slate-600">
          Capture canonical employee fields with inline validation, clear submit feedback, and API-aligned payloads.
        </p>
      </div>

      {submitError ? (
        <div className="mb-6 flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            <p className="font-medium text-rose-900">Unable to save employee</p>
            <p>{submitError}</p>
          </div>
        </div>
      ) : null}

      <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit} noValidate aria-busy={isSubmitting}>
        {isSubmitting ? (
          <div className="md:col-span-2 inline-flex items-center gap-2 rounded-[var(--radius-control)] border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm font-medium text-slate-600 animate-[surface-enter_180ms_ease-out]">
            <LoaderCircle className="h-4 w-4 animate-spin" />
            Saving changes…
          </div>
        ) : null}

        <fieldset className="contents" disabled={isSubmitting}>
        <Field label="Employee number" htmlFor="employee_number" error={errors.employee_number} hint={mode === 'edit' ? 'Employee number cannot be changed after creation.' : 'Use the canonical employee identifier.'}>
          <Input
            id="employee_number"
            className={inputClassName}
            value={values.employee_number}
            onChange={(event) => handleChange('employee_number', event.target.value)}
            disabled={mode === 'edit'}
            aria-invalid={Boolean(errors.employee_number)}
          />
        </Field>

        <Field label="Email" htmlFor="email" error={errors.email}>
          <Input
            id="email"
            className={inputClassName}
            type="email"
            value={values.email}
            onChange={(event) => handleChange('email', event.target.value)}
            aria-invalid={Boolean(errors.email)}
          />
        </Field>

        <Field label="First name" htmlFor="first_name" error={errors.first_name}>
          <Input
            id="first_name"
            className={inputClassName}
            value={values.first_name}
            onChange={(event) => handleChange('first_name', event.target.value)}
            aria-invalid={Boolean(errors.first_name)}
          />
        </Field>

        <Field label="Last name" htmlFor="last_name" error={errors.last_name}>
          <Input
            id="last_name"
            className={inputClassName}
            value={values.last_name}
            onChange={(event) => handleChange('last_name', event.target.value)}
            aria-invalid={Boolean(errors.last_name)}
          />
        </Field>

        <Field label="Phone" htmlFor="phone" error={errors.phone} hint="Optional, but recommended for operational contact.">
          <Input
            id="phone"
            className={inputClassName}
            value={values.phone}
            onChange={(event) => handleChange('phone', event.target.value)}
            aria-invalid={Boolean(errors.phone)}
          />
        </Field>

        <Field label="Hire date" htmlFor="hire_date" error={errors.hire_date}>
          <Input
            id="hire_date"
            className={inputClassName}
            type="date"
            value={values.hire_date}
            onChange={(event) => handleChange('hire_date', event.target.value)}
            aria-invalid={Boolean(errors.hire_date)}
          />
        </Field>

        <Field label="Employment type" htmlFor="employment_type" error={errors.employment_type}>
          <Select
            id="employment_type"
            className={inputClassName}
            value={values.employment_type}
            onChange={(event) => handleChange('employment_type', event.target.value as EmployeeFormValues['employment_type'])}
            aria-invalid={Boolean(errors.employment_type)}
          >
            {EMPLOYMENT_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Status" htmlFor="status" error={errors.status} hint={mode === 'edit' ? 'Status is controlled by lifecycle workflows on the detail view.' : undefined}>
          <Select
            id="status"
            className={inputClassName}
            value={values.status}
            onChange={(event) => handleChange('status', event.target.value as EmployeeFormValues['status'])}
            aria-invalid={Boolean(errors.status)}
            disabled={mode === 'edit'}
          >
            {EMPLOYEE_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Department ID" htmlFor="department_id" error={errors.department_id}>
          <Input
            id="department_id"
            className={inputClassName}
            value={values.department_id}
            onChange={(event) => handleChange('department_id', event.target.value)}
            aria-invalid={Boolean(errors.department_id)}
          />
        </Field>

        <Field label="Role ID" htmlFor="role_id" error={errors.role_id}>
          <Input
            id="role_id"
            className={inputClassName}
            value={values.role_id}
            onChange={(event) => handleChange('role_id', event.target.value)}
            aria-invalid={Boolean(errors.role_id)}
          />
        </Field>

        <Field label="Manager employee ID" htmlFor="manager_employee_id" error={errors.manager_employee_id} hint="Leave blank if no manager is assigned yet.">
          <Input
            id="manager_employee_id"
            className={inputClassName}
            value={values.manager_employee_id}
            onChange={(event) => handleChange('manager_employee_id', event.target.value)}
            aria-invalid={Boolean(errors.manager_employee_id)}
          />
        </Field>

        <div className="mt-2 flex items-end justify-end gap-3 border-t border-slate-200 pt-4 md:col-span-2">
          {onCancel ? (
            <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
              Cancel
            </Button>
          ) : null}
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
            {isSubmitting ? 'Saving…' : mode === 'create' ? 'Create employee' : 'Save changes'}
          </Button>
        </div>
        </fieldset>
      </form>
    </section>
  )
}

export function getDefaultEmployeeFormValues(employee?: Employee): EmployeeFormValues {
  return {
    employee_number: employee?.employee_number ?? '',
    first_name: employee?.first_name ?? '',
    last_name: employee?.last_name ?? '',
    email: employee?.email ?? '',
    phone: employee?.phone ?? '',
    hire_date: employee?.hire_date ?? '',
    employment_type: employee?.employment_type ?? 'FullTime',
    status: employee?.status ?? 'Draft',
    department_id: employee?.department_id ?? '',
    role_id: employee?.role_id ?? '',
    manager_employee_id: employee?.manager_employee_id ?? '',
  }
}

export { toApiPayload }
