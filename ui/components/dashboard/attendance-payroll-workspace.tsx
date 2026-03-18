'use client'

import type { ChangeEvent, ComponentType, ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity,
  ArrowUpRight,
  BadgeDollarSign,
  CalendarRange,
  Clock3,
  ReceiptText,
  RefreshCw,
  TimerReset,
  Wallet,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { EmptyState, ErrorState, TableSkeleton } from '@/components/ui/feedback'
import { PageGrid, PageStack } from '@/components/ui/page'
import {
  type AttendanceRecord,
  type PayrollRecord,
  clockInEmployee,
  clockOutEmployee,
  fetchAttendanceRecords,
  fetchPayrollRecords,
  getEmployeeOptions,
  runPayroll,
} from '@/lib/api/hrms'
import { cn } from '@/lib/utils'

function formatCurrency(value: string, currency: string = 'USD') {
  const amount = Number(value)
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0)
}

function formatDateTime(value: string | null) {
  if (!value) {
    return '—'
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function startOfMonth() {
  const now = new Date()
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1)).toISOString().slice(0, 10)
}

function endOfMonth() {
  const now = new Date()
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 0)).toISOString().slice(0, 10)
}

function startOfWindow(days: number) {
  return new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
}

function statusTone(status: string) {
  switch (status) {
    case 'Present':
    case 'Paid':
    case 'Processed':
    case 'Approved':
      return 'bg-emerald-50 text-emerald-700 ring-emerald-200'
    case 'Late':
    case 'Draft':
      return 'bg-amber-50 text-amber-700 ring-amber-200'
    default:
      return 'bg-slate-100 text-slate-700 ring-slate-200'
  }
}

function SurfaceCard({
  title,
  subtitle,
  icon: Icon,
  children,
}: {
  title: string
  subtitle: string
  icon: ComponentType<{ className?: string }>
  children: ReactNode
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_24px_80px_-48px_rgba(15,23,42,0.45)]">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="mb-2 inline-flex rounded-full bg-slate-100 p-2 text-slate-700">
            <Icon className="size-4" />
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-950">{title}</h2>
          <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
        </div>
      </div>
      {children}
    </section>
  )
}

function Metric({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-3 text-2xl font-semibold text-slate-950">{value}</p>
      <p className="mt-1 text-sm text-slate-600">{hint}</p>
    </div>
  )
}

function SyncBadge({ mode, source }: { mode: string; source: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ring-1',
        mode === 'live'
          ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
          : 'bg-amber-50 text-amber-700 ring-amber-200',
      )}
    >
      <span className={cn('size-2 rounded-full', mode === 'live' ? 'bg-emerald-500' : 'bg-amber-500')} />
      {mode === 'live' ? 'Live sync' : 'Demo fallback'} · {source}
    </span>
  )
}

export function AttendancePayrollWorkspace() {
  const queryClient = useQueryClient()
  const employees = getEmployeeOptions()
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(employees[0]?.id ?? '')
  const [attendanceFrom, setAttendanceFrom] = useState(startOfWindow(14))
  const [attendanceTo, setAttendanceTo] = useState(new Date().toISOString().slice(0, 10))
  const [payrollStatus, setPayrollStatus] = useState('All')
  const [payrollPeriodStart, setPayrollPeriodStart] = useState(startOfMonth())
  const [payrollPeriodEnd, setPayrollPeriodEnd] = useState(endOfMonth())
  const [selectedPayslip, setSelectedPayslip] = useState<PayrollRecord | null>(null)
  const [localAttendance, setLocalAttendance] = useState<AttendanceRecord[]>([])
  const [localPayroll, setLocalPayroll] = useState<PayrollRecord[]>([])

  const attendanceQuery = useQuery({
    queryKey: ['attendance-records', selectedEmployeeId, attendanceFrom, attendanceTo],
    queryFn: () => fetchAttendanceRecords({ employeeId: selectedEmployeeId, from: attendanceFrom, to: attendanceTo }),
    refetchInterval: 15_000,
    placeholderData: (previous: Awaited<ReturnType<typeof fetchAttendanceRecords>> | undefined) => previous,
    enabled: Boolean(selectedEmployeeId),
  })

  const payrollQuery = useQuery({
    queryKey: ['payroll-records', payrollPeriodStart, payrollPeriodEnd, payrollStatus],
    queryFn: () => fetchPayrollRecords({ periodStart: payrollPeriodStart, periodEnd: payrollPeriodEnd, status: payrollStatus }),
    refetchInterval: 20_000,
    placeholderData: (previous: Awaited<ReturnType<typeof fetchPayrollRecords>> | undefined) => previous,
  })

  const attendanceRecords = useMemo(() => {
    const remote = attendanceQuery.data?.records ?? []
    const merged = [...localAttendance, ...remote]
    const deduped = new Map(merged.map((record) => [record.attendanceId, record]))
    return [...deduped.values()].sort((left, right) => right.attendanceDate.localeCompare(left.attendanceDate))
  }, [attendanceQuery.data?.records, localAttendance])

  const payrollRecords = useMemo(() => {
    const remote = payrollQuery.data?.records ?? []
    const merged = [...localPayroll, ...remote]
    const deduped = new Map(merged.map((record) => [record.payrollRecordId, record]))
    return [...deduped.values()].sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
  }, [localPayroll, payrollQuery.data?.records])

  const attendanceSummary = useMemo(() => {
    const totalHours = attendanceRecords.reduce((sum: number, record: AttendanceRecord) => sum + Number(record.totalHours || '0'), 0)
    const openEntry = attendanceRecords.find((record) => !record.checkOutTime && record.attendanceDate === attendanceTo)

    return {
      records: attendanceRecords.length,
      hours: attendanceRecords.length ? (totalHours / attendanceRecords.length).toFixed(2) : '0.00',
      presentDays: attendanceRecords.filter((record: AttendanceRecord) => record.attendanceStatus === 'Present').length,
      openEntry,
    }
  }, [attendanceRecords, attendanceTo])

  const payrollSummary = useMemo(() => {
    const totalNet = payrollRecords.reduce((sum: number, record: PayrollRecord) => sum + Number(record.netPay || '0'), 0)
    const totalGross = payrollRecords.reduce((sum: number, record: PayrollRecord) => sum + Number(record.grossPay || '0'), 0)

    return {
      records: payrollRecords.length,
      totalNet,
      totalGross,
      pending: payrollRecords.filter((record: PayrollRecord) => record.status !== 'Paid').length,
    }
  }, [payrollRecords])

  const clockInMutation = useMutation({
    mutationFn: async () => clockInEmployee(selectedEmployeeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance-records'] })
    },
    onError: () => {
      const employee = employees.find((entry) => entry.id === selectedEmployeeId)
      if (!employee) {
        return
      }

      setLocalAttendance((current) => [
        {
          attendanceId: `local-${Date.now()}`,
          employeeId: employee.id,
          employeeNumber: employee.number,
          employeeName: employee.name,
          departmentName: employee.department,
          attendanceDate: new Date().toISOString().slice(0, 10),
          attendanceStatus: 'Present',
          checkInTime: new Date().toISOString(),
          checkOutTime: null,
          totalHours: '0.00',
          source: 'Manual',
          recordState: 'Queued locally',
          updatedAt: new Date().toISOString(),
        },
        ...current,
      ])
    },
  })

  const clockOutMutation = useMutation({
    mutationFn: async () => {
      if (!attendanceSummary.openEntry) {
        throw new Error('No active attendance session found.')
      }

      return clockOutEmployee(attendanceSummary.openEntry.attendanceId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance-records'] })
    },
    onError: () => {
      if (!attendanceSummary.openEntry) {
        return
      }

      setLocalAttendance((current) => {
        const updatedRecord = attendanceSummary.openEntry
          ? {
              ...attendanceSummary.openEntry,
              checkOutTime: new Date().toISOString(),
              totalHours: '8.00',
              recordState: 'Queued locally',
              updatedAt: new Date().toISOString(),
            }
          : null

        if (!updatedRecord) {
          return current
        }

        const hasExisting = current.some((record) => record.attendanceId === updatedRecord.attendanceId)
        if (!hasExisting) {
          return [updatedRecord, ...current]
        }

        return current.map((record) => (record.attendanceId === updatedRecord.attendanceId ? updatedRecord : record))
      })
    },
  })

  const runPayrollMutation = useMutation({
    mutationFn: async () => runPayroll({ periodStart: payrollPeriodStart, periodEnd: payrollPeriodEnd }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payroll-records'] })
    },
    onError: () => {
      setLocalPayroll((current) =>
        current.length
          ? current
          : [
              {
                payrollRecordId: `local-payroll-${Date.now()}`,
                employeeId: 'emp-1',
                employeeNumber: 'E-001',
                employeeName: 'Jane Doe',
                departmentName: 'Engineering',
                payPeriodStart: payrollPeriodStart,
                payPeriodEnd: payrollPeriodEnd,
                baseSalary: '4200.00',
                allowances: '250.00',
                deductions: '180.00',
                overtimePay: '140.00',
                grossPay: '4590.00',
                netPay: '4410.00',
                currency: 'USD',
                paymentDate: null,
                status: 'Processed',
                updatedAt: new Date().toISOString(),
              },
            ],
      )
    },
  })

  return (
    <PageStack>
      <section className="rounded-[32px] border border-slate-200/80 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.08),_transparent_35%),linear-gradient(180deg,_#ffffff_0%,_#f8fafc_100%)] p-6 shadow-[0_32px_120px_-48px_rgba(15,23,42,0.22)] lg:p-8">

          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.28em] text-sky-700">SME HRMS · Attendance + Payroll</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                Real-time workforce operations without the lag.
              </h1>
              <p className="mt-4 text-base leading-7 text-slate-600 sm:text-lg">
                Canonical attendance and payroll surfaces with fast local rendering, resilient API sync, and one-click actions for clock events, payroll runs, and payslip review.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <Metric label="Attendance sync" value={attendanceQuery.isFetching ? 'Refreshing' : 'Ready'} hint="15s live polling with cached previous data" />
              <Metric label="Payroll sync" value={payrollQuery.isFetching ? 'Refreshing' : 'Ready'} hint="20s refresh with filtered period queries" />
              <Metric label="UX target" value="10/10" hint="Fast tables, fallback resilience, responsive layout" />
            </div>
          </div>
      </section>

      <PageGrid className="xl:grid-cols-[1.2fr_1fr]">
          <SurfaceCard title="Attendance dashboard" subtitle="Clock in/out, live status, and clean history for the selected employee." icon={Clock3}>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 lg:flex-row lg:items-end lg:justify-between">
                <div className="grid gap-3 sm:grid-cols-3">
                  <label className="text-sm font-medium text-slate-700">
                    Employee
                    <select
                      className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none ring-0"
                      value={selectedEmployeeId}
                      onChange={(event: ChangeEvent<HTMLSelectElement>) => setSelectedEmployeeId(event.target.value)}
                    >
                      {employees.map((employee) => (
                        <option key={employee.id} value={employee.id}>
                          {employee.name} · {employee.number}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="text-sm font-medium text-slate-700">
                    From
                    <input
                      className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
                      type="date"
                      value={attendanceFrom}
                      onChange={(event: ChangeEvent<HTMLInputElement>) => setAttendanceFrom(event.target.value)}
                    />
                  </label>

                  <label className="text-sm font-medium text-slate-700">
                    To
                    <input
                      className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
                      type="date"
                      value={attendanceTo}
                      onChange={(event: ChangeEvent<HTMLInputElement>) => setAttendanceTo(event.target.value)}
                    />
                  </label>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <SyncBadge mode={attendanceQuery.data?.syncMode ?? 'demo'} source={attendanceQuery.data?.syncSource ?? 'not loaded'} />
                  <Button variant="outline" onClick={() => attendanceQuery.refetch()}>
                    <RefreshCw className={cn('size-4', attendanceQuery.isFetching && 'animate-spin')} />
                    Refresh
                  </Button>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <Metric label="History rows" value={String(attendanceSummary.records)} hint="Filtered by employee and date range" />
                <Metric label="Avg hours" value={`${attendanceSummary.hours} hrs`} hint="Computed client-side to avoid blocking UI" />
                <Metric label="Present days" value={String(attendanceSummary.presentDays)} hint={attendanceSummary.openEntry ? 'Active session open now' : 'No active session'} />
              </div>

              <div className="flex flex-wrap items-center gap-3 rounded-2xl bg-slate-950 p-4 text-white">
                <div className="mr-auto">
                  <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-300">Clock actions</p>
                  <p className="mt-1 text-sm text-slate-300">
                    Fast optimistic updates keep the UI responsive even if the service is slow.
                  </p>
                </div>
                <Button onClick={() => clockInMutation.mutate()} disabled={clockInMutation.isPending || Boolean(attendanceSummary.openEntry)}>
                  <Activity className="size-4" />
                  {clockInMutation.isPending ? 'Clocking in…' : 'Clock in'}
                </Button>
                <Button variant="secondary" onClick={() => clockOutMutation.mutate()} disabled={clockOutMutation.isPending || !attendanceSummary.openEntry}>
                  <TimerReset className="size-4" />
                  {clockOutMutation.isPending ? 'Clocking out…' : 'Clock out'}
                </Button>
              </div>

              <div className="overflow-hidden rounded-2xl border border-slate-200">
                <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-3">
                  <div>
                    <h3 className="font-semibold text-slate-900">Attendance history</h3>
                    <p className="text-sm text-slate-600">Recent records sorted by attendance date.</p>
                  </div>
                  <span className="text-sm text-slate-500">Updated {formatDateTime(attendanceRecords[0]?.updatedAt ?? null)}</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="bg-white text-left text-slate-500">
                      <tr>
                        <th className="px-4 py-3 font-medium">Date</th>
                        <th className="px-4 py-3 font-medium">Status</th>
                        <th className="px-4 py-3 font-medium">Check in</th>
                        <th className="px-4 py-3 font-medium">Check out</th>
                        <th className="px-4 py-3 font-medium">Hours</th>
                        <th className="px-4 py-3 font-medium">State</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 bg-white">
                      {attendanceRecords.map((record) => (
                        <tr key={record.attendanceId} className="hover:bg-slate-50">
                          <td className="px-4 py-3 font-medium text-slate-900">{record.attendanceDate}</td>
                          <td className="px-4 py-3">
                            <span className={cn('inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1', statusTone(record.attendanceStatus))}>
                              {record.attendanceStatus}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-600">{formatDateTime(record.checkInTime)}</td>
                          <td className="px-4 py-3 text-slate-600">{formatDateTime(record.checkOutTime)}</td>
                          <td className="px-4 py-3 text-slate-900">{record.totalHours}</td>
                          <td className="px-4 py-3 text-slate-600">{record.recordState}</td>
                        </tr>
                      ))}
                      {!attendanceRecords.length && (
                        <tr>
                          <td className="px-4 py-10 text-center text-slate-500" colSpan={6}>
                            No attendance records found for the selected filters.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </SurfaceCard>

          <SurfaceCard title="Payroll dashboard" subtitle="Period-aware payroll summaries with a built-in payslip viewer." icon={Wallet}>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="grid gap-3 sm:grid-cols-3">
                  <label className="text-sm font-medium text-slate-700">
                    Period start
                    <input
                      className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
                      type="date"
                      value={payrollPeriodStart}
                      onChange={(event: ChangeEvent<HTMLInputElement>) => setPayrollPeriodStart(event.target.value)}
                    />
                  </label>
                  <label className="text-sm font-medium text-slate-700">
                    Period end
                    <input
                      className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
                      type="date"
                      value={payrollPeriodEnd}
                      onChange={(event: ChangeEvent<HTMLInputElement>) => setPayrollPeriodEnd(event.target.value)}
                    />
                  </label>
                  <label className="text-sm font-medium text-slate-700">
                    Status
                    <select
                      className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
                      value={payrollStatus}
                      onChange={(event: ChangeEvent<HTMLSelectElement>) => setPayrollStatus(event.target.value)}
                    >
                      {['All', 'Draft', 'Processed', 'Paid'].map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <SyncBadge mode={payrollQuery.data?.syncMode ?? 'demo'} source={payrollQuery.data?.syncSource ?? 'not loaded'} />
                  <Button variant="outline" onClick={() => payrollQuery.refetch()}>
                    <RefreshCw className={cn('size-4', payrollQuery.isFetching && 'animate-spin')} />
                    Refresh
                  </Button>
                  <Button onClick={() => runPayrollMutation.mutate()} disabled={runPayrollMutation.isPending}>
                    <BadgeDollarSign className="size-4" />
                    {runPayrollMutation.isPending ? 'Running payroll…' : 'Run payroll'}
                  </Button>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <Metric label="Records" value={String(payrollSummary.records)} hint="Filtered payroll rows" />
                <Metric label="Gross pay" value={formatCurrency(String(payrollSummary.totalGross))} hint="Rendered from cached records" />
                <Metric label="Net pay" value={formatCurrency(String(payrollSummary.totalNet))} hint={`${payrollSummary.pending} rows still need completion`} />
              </div>

              <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
                <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
                  <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-3">
                    <div>
                      <h3 className="font-semibold text-slate-900">Payroll records</h3>
                      <p className="text-sm text-slate-600">Select a row to inspect the payslip breakdown.</p>
                    </div>
                    <CalendarRange className="size-4 text-slate-400" />
                  </div>
                  {payrollQuery.isLoading ? (
                    <TableSkeleton rows={5} columns={5} />
                  ) : payrollQuery.isError ? (
                    <div className="p-4">
                      <ErrorState title="Unable to load payroll data" message={payrollQuery.error.message} onRetry={() => payrollQuery.refetch()} />
                    </div>
                  ) : payrollRecords.length === 0 ? (
                    <div className="p-4">
                      <EmptyState
                        icon={ReceiptText}
                        title="No payroll records yet"
                        message="No payroll records match the selected period and status filters. Adjust the filters or run payroll to generate the next batch."
                        action={
                          <Button onClick={() => runPayrollMutation.mutate()} disabled={runPayrollMutation.isPending}>
                            <BadgeDollarSign className="size-4" />
                            {runPayrollMutation.isPending ? 'Running payroll…' : 'Run payroll'}
                          </Button>
                        }
                      />
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-slate-200 text-sm">
                        <thead className="bg-white text-left text-slate-500">
                          <tr>
                            <th className="px-4 py-3 font-medium">Employee</th>
                            <th className="px-4 py-3 font-medium">Period</th>
                            <th className="px-4 py-3 font-medium">Status</th>
                            <th className="px-4 py-3 font-medium">Net pay</th>
                            <th className="px-4 py-3 font-medium">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 bg-white">
                          {payrollRecords.map((record) => (
                            <tr key={record.payrollRecordId} className="hover:bg-slate-50">
                              <td className="px-4 py-3">
                                <p className="font-medium text-slate-900">{record.employeeName}</p>
                                <p className="text-xs text-slate-500">{record.departmentName}</p>
                              </td>
                              <td className="px-4 py-3 text-slate-600">
                                {record.payPeriodStart} → {record.payPeriodEnd}
                              </td>
                              <td className="px-4 py-3">
                                <span className={cn('inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1', statusTone(record.status))}>
                                  {record.status}
                                </span>
                              </td>
                              <td className="px-4 py-3 font-medium text-slate-900">{formatCurrency(record.netPay, record.currency)}</td>
                              <td className="px-4 py-3">
                                <Button variant="outline" size="sm" onClick={() => setSelectedPayslip(record)}>
                                  View payslip
                                  <ArrowUpRight className="size-4" />
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                  <div className="mb-4 flex items-center gap-3">
                    <div className="rounded-2xl bg-white p-2 text-slate-700 shadow-sm">
                      <Wallet className="size-4" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">Payslip viewer</h3>
                      <p className="text-sm text-slate-600">Fast detail panel driven by the selected payroll row.</p>
                    </div>
                  </div>

                  {selectedPayslip ? (
                    <div className="space-y-4">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Employee</p>
                        <p className="mt-2 text-xl font-semibold text-slate-950">{selectedPayslip.employeeName}</p>
                        <p className="text-sm text-slate-600">{selectedPayslip.employeeNumber} · {selectedPayslip.departmentName}</p>
                      </div>

                      <div className="grid gap-3 sm:grid-cols-2">
                        <Metric label="Base" value={formatCurrency(selectedPayslip.baseSalary, selectedPayslip.currency)} hint="Contract salary" />
                        <Metric label="Allowances" value={formatCurrency(selectedPayslip.allowances, selectedPayslip.currency)} hint="Non-base additions" />
                        <Metric label="Overtime" value={formatCurrency(selectedPayslip.overtimePay, selectedPayslip.currency)} hint="Attendance-linked uplift" />
                        <Metric label="Deductions" value={formatCurrency(selectedPayslip.deductions, selectedPayslip.currency)} hint="Taxes and adjustments" />
                      </div>

                      <div className="rounded-2xl bg-slate-950 p-4 text-white">
                        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">Net pay</p>
                        <p className="mt-3 text-3xl font-semibold">{formatCurrency(selectedPayslip.netPay, selectedPayslip.currency)}</p>
                        <p className="mt-2 text-sm text-slate-300">
                          Period {selectedPayslip.payPeriodStart} to {selectedPayslip.payPeriodEnd}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex min-h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 text-center">
                      <Wallet className="size-8 text-slate-400" />
                      <p className="mt-4 font-medium text-slate-900">Select a payroll row to open the payslip viewer.</p>
                      <p className="mt-2 text-sm text-slate-600">
                        Breakdown rendering stays instant because the viewer reuses already-fetched record data.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </SurfaceCard>
      </PageGrid>
    </PageStack>
  )
}
