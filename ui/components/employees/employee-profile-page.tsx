'use client'

import type { ReactNode } from 'react'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Mail, Phone, ShieldCheck, UserRound } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { ErrorState, SurfaceSkeleton } from '@/components/ui/feedback'
import { PageStack } from '@/components/ui/page'
import { getEmployee, getEmployeeFullName } from '@/lib/employees/api'

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' }).format(new Date(value))
}

function DetailCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
      <div className="mt-4 grid gap-4 text-sm text-slate-600">{children}</div>
    </section>
  )
}

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="grid gap-1 border-b border-slate-100 pb-3 last:border-b-0 last:pb-0 md:grid-cols-[180px,1fr] md:gap-4">
      <span className="font-medium text-slate-500">{label}</span>
      <span className="text-slate-900">{value}</span>
    </div>
  )
}

export function EmployeeProfilePage({ employeeId }: { employeeId: string }) {
  const query = useQuery({
    queryKey: ['employee', employeeId],
    queryFn: () => getEmployee(employeeId),
  })

  if (query.isLoading) {
    return <SurfaceSkeleton lines={7} />
  }

  if (query.isError) {
    return <ErrorState title="Unable to load employee profile" message={query.error.message} onRetry={() => query.refetch()} />
  }

  if (!query.data) {
    return null
  }

  const employee = query.data.data

  return (
    <PageStack>
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <Link href="/employees" className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900">
              <ArrowLeft className="h-4 w-4" />
              Back to employee list
            </Link>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Employee profile</p>
              <h1 className="text-3xl font-semibold tracking-tight text-slate-950">{getEmployeeFullName(employee)}</h1>
              <p className="mt-2 text-sm text-slate-600">
                {employee.employee_number} · {employee.department_id} · {employee.role_id}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button asChild variant="outline">
              <Link href={`mailto:${employee.email}`}>
                <Mail className="h-4 w-4" />
                Email
              </Link>
            </Button>
            <Button asChild>
              <Link href={`/employees/${employee.employee_id}/edit`}>Edit profile</Link>
            </Button>
          </div>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.4fr,1fr]">
        <DetailCard title="Identity and employment details">
          <DetailRow label="Email" value={employee.email} />
          <DetailRow label="Phone" value={employee.phone || 'Not provided'} />
          <DetailRow label="Hire date" value={formatDate(employee.hire_date)} />
          <DetailRow label="Employment type" value={employee.employment_type} />
          <DetailRow label="Status" value={employee.status} />
          <DetailRow label="Department ID" value={employee.department_id} />
          <DetailRow label="Role ID" value={employee.role_id} />
          <DetailRow label="Manager employee ID" value={employee.manager_employee_id || 'Unassigned'} />
        </DetailCard>

        <div className="grid gap-6">
          <DetailCard title="Contact quick actions">
            <DetailRow
              label="Primary contact"
              value={
                <span className="inline-flex items-center gap-2">
                  <Mail className="h-4 w-4 text-slate-400" />
                  {employee.email}
                </span>
              }
            />
            <DetailRow
              label="Phone"
              value={
                <span className="inline-flex items-center gap-2">
                  <Phone className="h-4 w-4 text-slate-400" />
                  {employee.phone || 'Not provided'}
                </span>
              }
            />
          </DetailCard>

          <DetailCard title="Audit and lifecycle">
            <DetailRow
              label="Created"
              value={<span className="inline-flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-slate-400" />{formatDate(employee.created_at)}</span>}
            />
            <DetailRow label="Last updated" value={formatDate(employee.updated_at)} />
            <DetailRow label="Canonical surface" value="employee_profile" />
            <DetailRow label="Primary owner" value="employee-service" />
            <DetailRow label="Workspace status" value={<span className="inline-flex items-center gap-2"><UserRound className="h-4 w-4 text-slate-400" />Ready for edits</span>} />
          </DetailCard>
        </div>
      </div>
    </PageStack>
  )
}
