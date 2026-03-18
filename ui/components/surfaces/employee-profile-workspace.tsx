'use client'

import type { ReactNode } from 'react'
import Link from 'next/link'
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Mail, Phone, UserRoundSearch } from 'lucide-react'

import { Button, buttonVariants } from '@/components/ui/button'
import { Select } from '@/components/ui/input'
import { EmptyState, ErrorState, SurfaceSkeleton } from '@/components/ui/feedback'
import { PageGrid } from '@/components/ui/page'
import { getEmployeeFullName, listEmployees } from '@/lib/employees/api'

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' }).format(new Date(value))
}

export function EmployeeProfileWorkspace() {
  const query = useQuery({
    queryKey: ['employee-profile-workspace'],
    queryFn: () => listEmployees({ limit: 8 }),
  })
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string>('')

  const employees = query.data?.data ?? []
  const selectedEmployee = useMemo(() => {
    const fallbackId = selectedEmployeeId || employees[0]?.employee_id
    return employees.find((employee) => employee.employee_id === fallbackId) ?? employees[0]
  }, [employees, selectedEmployeeId])

  if (query.isLoading) {
    return <SurfaceSkeleton lines={7} />
  }

  if (query.isError) {
    return <ErrorState title="Unable to load employee profiles" message={query.error.message} onRetry={() => query.refetch()} />
  }

  return (
    <PageGrid className="xl:grid-cols-[360px_minmax(0,1fr)]">
      <section className="rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-surface)]">
        <div className="mb-4 flex items-start gap-3">
          <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
            <UserRoundSearch className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">Profile launcher</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Canonical employee profile coverage with quick handoff into the full dynamic profile route.
            </p>
          </div>
        </div>

        {employees.length === 0 ? (
          <EmptyState
            icon={UserRoundSearch}
            title="No employees available"
            message="Add your first employee to start using the profile workspace and detail screens."
            action={
              <Button asChild>
                <Link href="/employees/new">Add employee</Link>
              </Button>
            }
          />
        ) : (
          <>
            <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
              Select employee
              <Select
                value={selectedEmployee?.employee_id ?? ''}
                onChange={(event) => setSelectedEmployeeId(event.target.value)}
              >
                {employees.map((employee) => (
                  <option key={employee.employee_id} value={employee.employee_id}>
                    {getEmployeeFullName(employee)} · {employee.employee_number}
                  </option>
                ))}
              </Select>
            </label>

            <div className="mt-5 space-y-3">
              {employees.map((employee) => {
                const active = employee.employee_id === selectedEmployee?.employee_id
                return (
                  <button
                    key={employee.employee_id}
                    type="button"
                    onClick={() => setSelectedEmployeeId(employee.employee_id)}
                    className={buttonVariants({
                      variant: active ? 'default' : 'outline',
                      size: 'lg',
                      className: 'h-auto w-full flex-col items-start rounded-[var(--radius-surface)] px-4 py-3 text-left whitespace-normal',
                    })}
                  >
                    <p className="font-semibold">{getEmployeeFullName(employee)}</p>
                    <p className={`text-sm ${active ? 'text-slate-200' : 'text-slate-500'}`}>{employee.department_id} · {employee.role_id}</p>
                  </button>
                )
              })}
            </div>
          </>
        )}
      </section>

      {selectedEmployee ? (
        <section className="rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-surface)]">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Employee profile</p>
              <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{getEmployeeFullName(selectedEmployee)}</h2>
              <p className="mt-2 text-sm text-slate-600">
                {selectedEmployee.employee_number} · {selectedEmployee.department_id} · {selectedEmployee.role_id}
              </p>
            </div>
            <Button asChild>
              <Link href={`/employees/${selectedEmployee.employee_id}`}>
                Open full profile
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <ProfileCard label="Email" value={selectedEmployee.email} icon={<Mail className="h-4 w-4" />} />
            <ProfileCard label="Phone" value={selectedEmployee.phone || 'Not provided'} icon={<Phone className="h-4 w-4" />} />
            <ProfileCard label="Hire date" value={formatDate(selectedEmployee.hire_date)} />
            <ProfileCard label="Employment type" value={selectedEmployee.employment_type} />
            <ProfileCard label="Status" value={selectedEmployee.status} />
            <ProfileCard label="Manager employee ID" value={selectedEmployee.manager_employee_id || 'Unassigned'} />
          </div>

          <div className="mt-6 rounded-[var(--radius-surface)] bg-[var(--surface-subtle)] p-4 text-sm text-slate-600">
            This surface keeps profile discovery lightweight while the full employee route remains the source of truth for edit and deep-detail workflows.
          </div>
        </section>
      ) : (
        <EmptyState
          icon={UserRoundSearch}
          title="No employee selected"
          message="Choose an employee from the launcher to preview profile details here."
        />
      )}
    </PageGrid>
  )
}

function ProfileCard({ label, value, icon }: { label: string; value: string; icon?: ReactNode }) {
  return (
    <div className="rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface-subtle)] p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-3 inline-flex items-center gap-2 text-base font-semibold text-slate-950">
        {icon}
        {value}
      </p>
    </div>
  )
}
