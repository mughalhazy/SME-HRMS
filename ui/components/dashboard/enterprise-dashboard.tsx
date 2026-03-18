'use client'

import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  Clock3,
  CreditCard,
  LoaderCircle,
  Plus,
  RefreshCcw,
  Users,
} from 'lucide-react'

import { Button, buttonVariants } from '@/components/ui/button'
import { Input, Select, Textarea } from '@/components/ui/input'
import { PageGrid, PageStack } from '@/components/ui/page'
import { apiRequest, buildApiUrl, buildHeaders } from '@/lib/api/client'

type EmployeeRow = {
  employee_id: string
  employee_number?: string
  first_name?: string
  last_name?: string
  full_name?: string
  department_name?: string
  department_id?: string
  status?: string
  employee_status?: string
  employment_type?: string
  hire_date?: string
  role_id?: string
  email?: string
}

type AttendanceRow = {
  employee_id?: string
  employee_name?: string
  attendance_date?: string
  attendance_status?: string
  check_in_time?: string | null
  check_out_time?: string | null
  total_hours?: string
  updated_at?: string
}

type LeaveRow = {
  leave_request_id: string
  employee_name?: string
  leave_type?: string
  start_date?: string
  end_date?: string
  status?: string
  updated_at?: string
}

type PayrollRow = {
  payroll_record_id: string
  employee_name?: string
  employee_id?: string
  pay_period_start?: string
  pay_period_end?: string
  net_pay?: string
  gross_pay?: string
  status?: string
  currency?: string
  payment_date?: string | null
  updated_at?: string
}

type JobPostingRow = {
  job_posting_id: string
  title?: string
  status?: string
  openings_count?: number
  posting_date?: string
  department_id?: string
}

type DashboardDataset = {
  employees: EmployeeRow[]
  attendance: AttendanceRow[]
  leave: LeaveRow[]
  payroll: PayrollRow[]
  jobs: JobPostingRow[]
  fetchedAt: string
}

type WidgetState = 'live' | 'empty' | 'error'

type ActionKey = 'add-employee' | 'run-payroll' | 'approve-leave' | 'post-job'

type ActionConfig = {
  key: ActionKey
  title: string
  description: string
  path: string
  method: 'POST'
  submitLabel: string
  buildPath?: (form: Record<string, string>) => string
  buildBody: (form: Record<string, string>) => Record<string, unknown>
}

type QueryEnvelope<T> = {
  data?: T[]
  page?: {
    nextCursor?: string | null
    hasNext?: boolean
    limit?: number
  }
} & Record<string, unknown>

const dashboardQueryKey = ['enterprise-dashboard'] as const

const quickActions: ActionConfig[] = [
  {
    key: 'add-employee',
    title: 'Add employee',
    description: 'Create a new employee record in the employee-service flow.',
    path: '/api/v1/employees',
    method: 'POST',
    submitLabel: 'Create employee',
    buildBody: (form) => ({
      employee_number: form.employee_number,
      first_name: form.first_name,
      last_name: form.last_name,
      email: form.email,
      phone: form.phone,
      hire_date: form.hire_date,
      employment_type: form.employment_type,
      status: form.status,
      department_id: form.department_id,
      role_id: form.role_id,
      manager_employee_id: form.manager_employee_id || undefined,
    }),
  },
  {
    key: 'run-payroll',
    title: 'Run payroll',
    description: 'Trigger the canonical payroll run for the selected pay period.',
    path: '/api/v1/payroll/run',
    method: 'POST',
    submitLabel: 'Run payroll',
    buildPath: (form) =>
      `/api/v1/payroll/run?period_start=${encodeURIComponent(form.period_start)}&period_end=${encodeURIComponent(form.period_end)}`,
    buildBody: () => ({}),
  },
  {
    key: 'approve-leave',
    title: 'Approve leave',
    description: 'Send the selected request through the canonical approval flow.',
    path: '/api/v1/leave/requests',
    method: 'POST',
    submitLabel: 'Approve request',
    buildPath: (form) => `/api/v1/leave/requests/${encodeURIComponent(form.leave_request_id)}/approve`,
    buildBody: () => ({}),
  },
  {
    key: 'post-job',
    title: 'Post job',
    description: 'Open a new job posting in the hiring-service flow.',
    path: '/api/v1/hiring/job-postings',
    method: 'POST',
    submitLabel: 'Create posting',
    buildBody: (form) => ({
      title: form.title,
      department_id: form.department_id,
      role_id: form.role_id || undefined,
      employment_type: form.employment_type,
      description: form.description,
      openings_count: Number(form.openings_count),
      posting_date: form.posting_date,
      closing_date: form.closing_date || undefined,
      status: form.status,
      location: form.location || undefined,
    }),
  },
]

const defaultForms: Record<ActionKey, Record<string, string>> = {
  'add-employee': {
    employee_number: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    hire_date: todayIso(),
    employment_type: 'FullTime',
    status: 'Active',
    department_id: '',
    role_id: '',
    manager_employee_id: '',
  },
  'run-payroll': {
    period_start: monthStartIso(),
    period_end: todayIso(),
  },
  'approve-leave': {
    leave_request_id: '',
  },
  'post-job': {
    title: '',
    department_id: '',
    role_id: '',
    employment_type: 'FullTime',
    description: '',
    openings_count: '1',
    posting_date: todayIso(),
    closing_date: '',
    status: 'Open',
    location: '',
  },
}

export function EnterpriseDashboard() {
  const queryClient = useQueryClient()
  const [token, setToken] = useState('')
  const [activeAction, setActiveAction] = useState<ActionKey | null>(null)
  const [forms, setForms] = useState(defaultForms)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const dashboardQuery = useQuery({
    queryKey: [...dashboardQueryKey, token],
    queryFn: () => fetchDashboardData(token),
  })

  const actionMutation = useMutation({
    mutationFn: async (actionKey: ActionKey) => {
      const config = quickActions.find((action) => action.key === actionKey)
      if (!config) {
        throw new Error('Unknown action')
      }

      const form = forms[actionKey]
      const path = config.buildPath ? config.buildPath(form) : config.path
      return apiRequest(path, {
        method: config.method,
        headers: buildHeaders({ token }),
        body: JSON.stringify(config.buildBody(form)),
      })
    },
    onSuccess: (_payload, actionKey) => {
      setActionMessage(`${labelForAction(actionKey)} flow triggered successfully.`)
      setForms((current) => ({ ...current, [actionKey]: { ...defaultForms[actionKey] } }))
      setActiveAction(null)
      void queryClient.invalidateQueries({ queryKey: [...dashboardQueryKey] })
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : 'Action failed'
      setActionMessage(message)
    },
  })

  const data = dashboardQuery.data

  const employeesSummary = useMemo(() => {
    const rows = data?.employees ?? []
    return {
      total: rows.length,
      active: rows.filter((row) => statusForEmployee(row) === 'Active').length,
      newHires: rows.filter((row) => isInCurrentMonth(row.hire_date)).length,
      recent: rows.slice(0, 4),
      state: toWidgetState(rows.length, dashboardQuery.isError),
    }
  }, [data?.employees, dashboardQuery.isError])

  const attendanceSummary = useMemo(() => {
    const rows = (data?.attendance ?? []).filter((row) => row.attendance_date === todayIso())
    return {
      total: rows.length,
      present: rows.filter((row) => row.attendance_status === 'Present').length,
      late: rows.filter((row) => row.attendance_status === 'Late').length,
      absent: rows.filter((row) => row.attendance_status === 'Absent').length,
      recent: rows.slice(0, 4),
      state: toWidgetState(rows.length, dashboardQuery.isError),
    }
  }, [data?.attendance, dashboardQuery.isError])

  const leaveSummary = useMemo(() => {
    const rows = data?.leave ?? []
    return {
      total: rows.length,
      pending: rows.filter((row) => row.status === 'Submitted').length,
      approved: rows.filter((row) => row.status === 'Approved').length,
      recent: rows.slice(0, 4),
      state: toWidgetState(rows.length, dashboardQuery.isError),
      pendingRows: rows.filter((row) => row.status === 'Submitted').slice(0, 12),
    }
  }, [data?.leave, dashboardQuery.isError])

  const payrollSummary = useMemo(() => {
    const rows = data?.payroll ?? []
    return {
      total: rows.length,
      processed: rows.filter((row) => row.status === 'Processed').length,
      paid: rows.filter((row) => row.status === 'Paid').length,
      draft: rows.filter((row) => row.status === 'Draft').length,
      netPay: currencyFormat(rows.reduce((sum, row) => sum + numberFromValue(row.net_pay), 0)),
      recent: rows.slice(0, 4),
      state: toWidgetState(rows.length, dashboardQuery.isError),
    }
  }, [data?.payroll, dashboardQuery.isError])

  const jobsSummary = useMemo(() => {
    const rows = data?.jobs ?? []
    return {
      total: rows.length,
      open: rows.filter((row) => row.status === 'Open').length,
      recent: rows.slice(0, 4),
    }
  }, [data?.jobs])

  const cards = [
    {
      key: 'employees',
      title: 'Employee count',
      value: formatCompact(employeesSummary.total),
      subtitle: `${employeesSummary.active} active • ${employeesSummary.newHires} joined this month`,
      tone: 'slate',
      icon: Users,
      state: employeesSummary.state,
      items: employeesSummary.recent.map((row) => ({
        primary: employeeName(row),
        secondary: row.department_name ?? 'Department pending',
        meta: statusForEmployee(row) ?? 'Unknown',
      })),
    },
    {
      key: 'attendance',
      title: 'Attendance summary',
      value: formatCompact(attendanceSummary.total),
      subtitle: `${attendanceSummary.present} present • ${attendanceSummary.late} late • ${attendanceSummary.absent} absent`,
      tone: 'emerald',
      icon: Clock3,
      state: attendanceSummary.state,
      items: attendanceSummary.recent.map((row) => ({
        primary: row.employee_name ?? 'Unknown employee',
        secondary: row.check_in_time ? `Checked in ${formatTime(row.check_in_time)}` : 'No check-in recorded',
        meta: row.attendance_status ?? 'Unknown',
      })),
    },
    {
      key: 'leave',
      title: 'Leave requests',
      value: formatCompact(leaveSummary.pending),
      subtitle: `${leaveSummary.approved} approved • ${leaveSummary.total} tracked`,
      tone: 'amber',
      icon: CheckCircle2,
      state: leaveSummary.state,
      items: leaveSummary.recent.map((row) => ({
        primary: row.employee_name ?? 'Unknown employee',
        secondary: `${row.leave_type ?? 'Leave'} • ${formatDateRange(row.start_date, row.end_date)}`,
        meta: row.status ?? 'Unknown',
      })),
    },
    {
      key: 'payroll',
      title: 'Payroll status',
      value: payrollSummary.netPay,
      subtitle: `${payrollSummary.processed} processed • ${payrollSummary.paid} paid • ${payrollSummary.draft} draft`,
      tone: 'violet',
      icon: CreditCard,
      state: payrollSummary.state,
      items: payrollSummary.recent.map((row) => ({
        primary: row.employee_name ?? row.employee_id ?? 'Unknown employee',
        secondary: formatDateRange(row.pay_period_start, row.pay_period_end),
        meta: row.status ?? 'Unknown',
      })),
    },
  ] as const

  return (
    <PageStack className="text-slate-950">
        <section className="rounded-lg border border-slate-200 bg-white px-5 py-5 shadow-sm sm:px-7 sm:py-6">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500">
                <span className="font-medium text-slate-700">Dashboard</span>
                <span>Enterprise view</span>
                {data?.fetchedAt ? <span>Updated {formatDateTime(data.fetchedAt)}</span> : null}
              </div>
              <div className="space-y-2">
                <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">Clean signal across people, time, leave, and payroll.</h1>
                <p className="max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
                  Built against the canonical dashboard read-model surfaces, with compact summaries and quick actions mapped to the underlying service flows.
                </p>
              </div>
            </div>

            <div className="grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:min-w-[320px]">
              <label className="space-y-2 text-sm font-medium text-slate-700">
                <span>Bearer token</span>
                <Input
                  value={token}
                  onChange={(event) => setToken(event.target.value)}
                  placeholder="Optional for authenticated reads/actions"
                 
                />
              </label>
              <div className="flex flex-wrap items-center gap-3">
                <Button onClick={() => void dashboardQuery.refetch()} disabled={dashboardQuery.isFetching}>
                  {dashboardQuery.isFetching ? <LoaderCircle className="size-4 animate-spin" /> : <RefreshCcw className="size-4" />}
                  Refresh data
                </Button>
                <a
                  href={buildApiUrl('/api/v1/employees')}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-slate-950"
                >
                  Open API <ArrowRight className="size-4" />
                </a>
              </div>
            </div>
          </div>
        </section>

        {actionMessage ? (
          <section className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            {actionMessage}
          </section>
        ) : null}

        <PageGrid className="xl:grid-cols-[minmax(0,1fr)_320px]">
          <PageGrid className="md:grid-cols-2">
            {cards.map((card) => (
              <article key={card.key} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-slate-500">{card.title}</p>
                    <div className="space-y-1">
                      <h2 className="text-3xl font-semibold tracking-tight">{card.value}</h2>
                      <p className="text-sm text-slate-600">{card.subtitle}</p>
                    </div>
                  </div>
                  <div className={iconToneClass(card.tone)}>
                    <card.icon className="size-5" />
                  </div>
                </div>

                <div className="mt-4 border-t border-slate-200 pt-4">
                  {card.state === 'error' ? (
                    <EmptyState message="Unable to load this widget from the API." />
                  ) : card.items.length === 0 ? (
                    <EmptyState message="No records returned for this widget yet." />
                  ) : (
                    <ul className="space-y-3">
                      {card.items.map((item, index) => (
                        <li key={`${card.key}-${index}`} className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-slate-900">{item.primary}</p>
                            <p className="truncate text-sm text-slate-500">{item.secondary}</p>
                          </div>
                          <span className="whitespace-nowrap rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                            {item.meta}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </article>
            ))}
          </PageGrid>

          <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="space-y-1">
              <p className="text-sm font-medium text-slate-500">Quick actions</p>
              <h2 className="text-2xl font-semibold tracking-tight">Move work forward fast.</h2>
              <p className="text-sm leading-6 text-slate-600">Each action targets the canonical API flow for the owning service, without leaving the dashboard.</p>
            </div>

            <div className="mt-5 space-y-3">
              {quickActions.map((action) => (
                <button
                  key={action.key}
                  type="button"
                  onClick={() => {
                    setActionMessage(null)
                    setActiveAction(action.key)
                    if (action.key === 'approve-leave' && !forms['approve-leave'].leave_request_id) {
                      const firstPending = leaveSummary.pendingRows[0]?.leave_request_id ?? ''
                      if (firstPending) {
                        setForms((current) => ({
                          ...current,
                          'approve-leave': { leave_request_id: firstPending },
                        }))
                      }
                    }
                  }}
                  className={buttonVariants({
                    variant: 'outline',
                    size: 'lg',
                    className: 'h-auto w-full justify-between rounded-[var(--radius-surface)] px-4 py-3 text-left whitespace-normal',
                  })}
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{action.title}</p>
                    <p className="mt-1 text-sm font-normal text-slate-500">{action.description}</p>
                  </div>
                  <ChevronRight className="size-4 text-slate-400" />
                </button>
              ))}
            </div>

            <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-medium text-slate-500">Read model coverage</p>
              <div className="mt-3 grid gap-3 text-sm text-slate-600">
                <div className="flex items-center justify-between"><span>Employees</span><span>{employeesSummary.total}</span></div>
                <div className="flex items-center justify-between"><span>Attendance today</span><span>{attendanceSummary.total}</span></div>
                <div className="flex items-center justify-between"><span>Pending leave</span><span>{leaveSummary.pending}</span></div>
                <div className="flex items-center justify-between"><span>Payroll records</span><span>{payrollSummary.total}</span></div>
                <div className="flex items-center justify-between"><span>Open jobs</span><span>{jobsSummary.open}</span></div>
              </div>
            </div>
          </aside>
        </PageGrid>

      {activeAction ? (
        <ActionDialog
          action={quickActions.find((item) => item.key === activeAction)!}
          form={forms[activeAction]}
          pendingLeaveRows={leaveSummary.pendingRows}
          isPending={actionMutation.isPending}
          onClose={() => setActiveAction(null)}
          onChange={(field, value) =>
            setForms((current) => ({
              ...current,
              [activeAction]: {
                ...current[activeAction],
                [field]: value,
              },
            }))
          }
          onSubmit={() => actionMutation.mutate(activeAction)}
        />
      ) : null}
    </PageStack>
  )
}

function ActionDialog({
  action,
  form,
  pendingLeaveRows,
  isPending,
  onClose,
  onChange,
  onSubmit,
}: {
  action: ActionConfig
  form: Record<string, string>
  pendingLeaveRows: LeaveRow[]
  isPending: boolean
  onClose: () => void
  onChange: (field: string, value: string) => void
  onSubmit: () => void
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/35 p-4 sm:items-center">
      <div className="w-full max-w-xl rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-surface)]">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-500">Quick action</p>
            <h3 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">{action.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{action.description}</p>
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>

        <div className="mt-6 space-y-4">{renderFields(action.key, form, pendingLeaveRows, onChange)}</div>

        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <Button variant="outline" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={isPending || hasMissingRequiredFields(action.key, form)}>
            {isPending ? <LoaderCircle className="size-4 animate-spin" /> : <Plus className="size-4" />}
            {action.submitLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}

function renderFields(
  actionKey: ActionKey,
  form: Record<string, string>,
  pendingLeaveRows: LeaveRow[],
  onChange: (field: string, value: string) => void,
) {
  if (actionKey === 'add-employee') {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        <InputField label="Employee #" value={form.employee_number} onChange={(value) => onChange('employee_number', value)} />
        <InputField label="Hire date" type="date" value={form.hire_date} onChange={(value) => onChange('hire_date', value)} />
        <InputField label="First name" value={form.first_name} onChange={(value) => onChange('first_name', value)} />
        <InputField label="Last name" value={form.last_name} onChange={(value) => onChange('last_name', value)} />
        <InputField label="Email" type="email" value={form.email} onChange={(value) => onChange('email', value)} />
        <InputField label="Phone" value={form.phone} onChange={(value) => onChange('phone', value)} />
        <InputField label="Department ID" value={form.department_id} onChange={(value) => onChange('department_id', value)} />
        <InputField label="Role ID" value={form.role_id} onChange={(value) => onChange('role_id', value)} />
        <SelectField label="Employment type" value={form.employment_type} options={['FullTime', 'PartTime', 'Contract', 'Intern']} onChange={(value) => onChange('employment_type', value)} />
        <SelectField label="Status" value={form.status} options={['Active', 'Draft', 'OnLeave', 'Suspended', 'Terminated']} onChange={(value) => onChange('status', value)} />
        <div className="sm:col-span-2">
          <InputField label="Manager employee ID" value={form.manager_employee_id} onChange={(value) => onChange('manager_employee_id', value)} />
        </div>
      </div>
    )
  }

  if (actionKey === 'run-payroll') {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        <InputField label="Period start" type="date" value={form.period_start} onChange={(value) => onChange('period_start', value)} />
        <InputField label="Period end" type="date" value={form.period_end} onChange={(value) => onChange('period_end', value)} />
      </div>
    )
  }

  if (actionKey === 'approve-leave') {
    return (
      <div className="space-y-4">
        <SelectField
          label="Pending request"
          value={form.leave_request_id}
          options={pendingLeaveRows.map((row) => ({
            label: `${row.employee_name ?? 'Unknown'} · ${row.leave_request_id}`,
            value: row.leave_request_id,
          }))}
          placeholder="Select a submitted leave request"
          onChange={(value) => onChange('leave_request_id', value)}
        />
        <InputField label="Leave request ID" value={form.leave_request_id} onChange={(value) => onChange('leave_request_id', value)} />
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="sm:col-span-2">
        <InputField label="Title" value={form.title} onChange={(value) => onChange('title', value)} />
      </div>
      <InputField label="Department ID" value={form.department_id} onChange={(value) => onChange('department_id', value)} />
      <InputField label="Role ID" value={form.role_id} onChange={(value) => onChange('role_id', value)} />
      <SelectField label="Employment type" value={form.employment_type} options={['FullTime', 'PartTime', 'Contract', 'Intern']} onChange={(value) => onChange('employment_type', value)} />
      <InputField label="Openings" type="number" value={form.openings_count} onChange={(value) => onChange('openings_count', value)} />
      <InputField label="Posting date" type="date" value={form.posting_date} onChange={(value) => onChange('posting_date', value)} />
      <InputField label="Closing date" type="date" value={form.closing_date} onChange={(value) => onChange('closing_date', value)} />
      <SelectField label="Status" value={form.status} options={['Open', 'Draft', 'OnHold']} onChange={(value) => onChange('status', value)} />
      <div className="sm:col-span-2">
        <InputField label="Location" value={form.location} onChange={(value) => onChange('location', value)} />
      </div>
      <div className="sm:col-span-2">
        <TextAreaField label="Description" value={form.description} onChange={(value) => onChange('description', value)} />
      </div>
    </div>
  )
}

function InputField({
  label,
  value,
  onChange,
  type = 'text',
}: {
  label: string
  value: string
  onChange: (value: string) => void
  type?: string
}) {
  return (
    <label className="space-y-2 text-sm font-medium text-slate-700">
      <span>{label}</span>
      <Input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
       
      />
    </label>
  )
}

function TextAreaField({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <label className="space-y-2 text-sm font-medium text-slate-700">
      <span>{label}</span>
      <Textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
       
      />
    </label>
  )
}

function SelectField({
  label,
  value,
  options,
  placeholder,
  onChange,
}: {
  label: string
  value: string
  options: Array<string | { label: string; value: string }>
  placeholder?: string
  onChange: (value: string) => void
}) {
  return (
    <label className="space-y-2 text-sm font-medium text-slate-700">
      <span>{label}</span>
      <Select
        value={value}
        onChange={(event) => onChange(event.target.value)}
       
      >
        {placeholder ? <option value="">{placeholder}</option> : null}
        {options.map((option) => {
          const normalized = typeof option === 'string' ? { label: option, value: option } : option
          return (
            <option key={normalized.value} value={normalized.value}>
              {normalized.label}
            </option>
          )
        })}
      </Select>
    </label>
  )
}

function EmptyState({ message }: { message: string }) {
  return <p className="text-sm leading-6 text-slate-500">{message}</p>
}

async function fetchDashboardData(token: string): Promise<DashboardDataset> {
  const today = todayIso()
  const monthStart = monthStartIso()
  const headers = buildHeaders({ token })

  const [employees, attendance, leave, payroll, jobs] = await Promise.all([
    fetchArray<EmployeeRow>('/api/v1/employees?limit=200', headers),
    fetchArray<AttendanceRow>(`/api/v1/attendance/records?from=${today}&to=${today}`, headers),
    fetchArray<LeaveRow>(`/api/v1/leave/requests?status=Submitted&from=${monthStart}&to=${today}`, headers),
    fetchArray<PayrollRow>(`/api/v1/payroll/records?period_start=${monthStart}&period_end=${today}`, headers),
    fetchArray<JobPostingRow>('/api/v1/hiring/job-postings?status=Open&limit=20', headers),
  ])

  return {
    employees,
    attendance,
    leave,
    payroll,
    jobs,
    fetchedAt: new Date().toISOString(),
  }
}

async function fetchArray<T>(path: string, headers: HeadersInit): Promise<T[]> {
  try {
    const payload = await apiRequest<QueryEnvelope<T>>(path, { headers })
    return extractRows<T>(payload)
  } catch {
    return []
  }
}

function extractRows<T>(payload: QueryEnvelope<T>): T[] {
  if (Array.isArray(payload.data)) {
    return payload.data
  }

  const arrayValue = Object.values(payload).find((value) => Array.isArray(value))
  return Array.isArray(arrayValue) ? (arrayValue as T[]) : []
}

function iconToneClass(tone: 'slate' | 'emerald' | 'amber' | 'violet') {
  const tones = {
    slate: 'inline-flex size-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700',
    emerald: 'inline-flex size-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700',
    amber: 'inline-flex size-11 items-center justify-center rounded-2xl bg-amber-50 text-amber-700',
    violet: 'inline-flex size-11 items-center justify-center rounded-2xl bg-violet-50 text-violet-700',
  }

  return tones[tone]
}

function formatCompact(value: number) {
  return new Intl.NumberFormat('en-US', { notation: value > 999 ? 'compact' : 'standard', maximumFractionDigits: 1 }).format(value)
}

function currencyFormat(value: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatDateRange(start?: string, end?: string) {
  if (!start && !end) {
    return 'Date pending'
  }

  const formatter = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' })
  const startLabel = start ? formatter.format(new Date(start)) : 'Start TBD'
  const endLabel = end ? formatter.format(new Date(end)) : 'End TBD'
  return `${startLabel} - ${endLabel}`
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' }).format(new Date(value))
}

function employeeName(row: EmployeeRow) {
  if (row.full_name) {
    return row.full_name
  }
  return [row.first_name, row.last_name].filter(Boolean).join(' ') || row.employee_id
}

function statusForEmployee(row: EmployeeRow) {
  return row.employee_status ?? row.status ?? 'Unknown'
}

function numberFromValue(value?: string) {
  const parsed = Number(value ?? '0')
  return Number.isFinite(parsed) ? parsed : 0
}

function toWidgetState(rowCount: number, hasQueryError: boolean): WidgetState {
  if (rowCount > 0) {
    return 'live'
  }
  return hasQueryError ? 'error' : 'empty'
}

function hasMissingRequiredFields(actionKey: ActionKey, form: Record<string, string>) {
  const requirements: Record<ActionKey, string[]> = {
    'add-employee': ['employee_number', 'first_name', 'last_name', 'email', 'hire_date', 'employment_type', 'status', 'department_id', 'role_id'],
    'run-payroll': ['period_start', 'period_end'],
    'approve-leave': ['leave_request_id'],
    'post-job': ['title', 'department_id', 'employment_type', 'description', 'openings_count', 'posting_date', 'status'],
  }

  return requirements[actionKey].some((field) => !form[field])
}

function labelForAction(actionKey: ActionKey) {
  return quickActions.find((action) => action.key === actionKey)?.title ?? 'Action'
}

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

function monthStartIso() {
  const now = new Date()
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1)).toISOString().slice(0, 10)
}

function isInCurrentMonth(value?: string) {
  if (!value) {
    return false
  }

  const date = new Date(value)
  const now = new Date()
  return date.getUTCFullYear() === now.getUTCFullYear() && date.getUTCMonth() === now.getUTCMonth()
}
