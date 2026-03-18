'use client'

import type { ReactNode } from 'react'
import Link from 'next/link'
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Mail, Phone, UserRoundSearch } from 'lucide-react'

import { Button } from '@/components/ui/button'
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
    return <div className="rounded-3xl border border-slate-200 bg-white p-10 text-sm text-slate-500">Loading employee profiles…</div>
  }

  if (query.isError) {
    return <div className="rounded-3xl border border-slate-200 bg-white p-10 text-sm text-rose-600">{query.error.message}</div>
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
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

        <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
          Select employee
          <select
            className="h-11 rounded-xl border border-slate-200 bg-white px-3 text-sm"
            value={selectedEmployee?.employee_id ?? ''}
            onChange={(event) => setSelectedEmployeeId(event.target.value)}
          >
            {employees.map((employee) => (
              <option key={employee.employee_id} value={employee.employee_id}>
                {getEmployeeFullName(employee)} · {employee.employee_number}
              </option>
            ))}
          </select>
        </label>

        <div className="mt-5 space-y-3">
          {employees.map((employee) => {
            const active = employee.employee_id === selectedEmployee?.employee_id
            return (
              <button
                key={employee.employee_id}
                type="button"
                onClick={() => setSelectedEmployeeId(employee.employee_id)}
                className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                  active ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <p className="font-semibold">{getEmployeeFullName(employee)}</p>
                <p className={`text-sm ${active ? 'text-slate-200' : 'text-slate-500'}`}>{employee.department_id} · {employee.role_id}</p>
              </button>
            )
          })}
        </div>
      </section>

      {selectedEmployee ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
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

          <div className="mt-6 rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
            This surface keeps profile discovery lightweight while the full employee route remains the source of truth for edit and deep-detail workflows.
          </div>
        </section>
      ) : (
        <div className="rounded-3xl border border-slate-200 bg-white p-10 text-sm text-slate-500">No employee records available yet.</div>
      )}
    </div>
  )
}

function ProfileCard({ label, value, icon }: { label: string; value: string; icon?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-3 inline-flex items-center gap-2 text-base font-semibold text-slate-950">
        {icon}
        {value}
      </p>
    </div>
  )
}
