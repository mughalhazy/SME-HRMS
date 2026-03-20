'use client'

import { useMemo, useState } from 'react'
import { BadgeDollarSign, CalendarRange, Filter, RefreshCw, Wallet } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/feedback'
import { Select } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'

type PayrollStatus = 'Pending' | 'Processed' | 'Flagged'

type PayrollEntry = {
  id: string
  employee: string
  employeeNumber: string
  department: string
  cycle: string
  baseSalary: number
  allowances: number
  deductions: number
  netPay: number
  status: PayrollStatus
  note: string
}

const payrollCycles = ['March 2026', 'February 2026', 'January 2026'] as const
const departments = ['All departments', 'Operations', 'Finance', 'Engineering', 'People'] as const
const statusFilters = ['All statuses', 'Pending', 'Processed', 'Flagged'] as const

const payrollEntries: PayrollEntry[] = [
  {
    id: 'PR-24001',
    employee: 'Ava Johnson',
    employeeNumber: 'EMP-1042',
    department: 'Operations',
    cycle: 'March 2026',
    baseSalary: 6200,
    allowances: 480,
    deductions: 840,
    netPay: 5840,
    status: 'Processed',
    note: 'Released to settlement on Mar 19',
  },
  {
    id: 'PR-24002',
    employee: 'Noah Kim',
    employeeNumber: 'EMP-1178',
    department: 'Finance',
    cycle: 'March 2026',
    baseSalary: 7100,
    allowances: 560,
    deductions: 910,
    netPay: 6750,
    status: 'Processed',
    note: 'Bank confirmation complete',
  },
  {
    id: 'PR-24003',
    employee: 'Mia Patel',
    employeeNumber: 'EMP-1266',
    department: 'Engineering',
    cycle: 'March 2026',
    baseSalary: 8350,
    allowances: 650,
    deductions: 1240,
    netPay: 7760,
    status: 'Pending',
    note: 'Awaiting final approvals',
  },
  {
    id: 'PR-24004',
    employee: 'Liam Brooks',
    employeeNumber: 'EMP-1321',
    department: 'People',
    cycle: 'March 2026',
    baseSalary: 5800,
    allowances: 420,
    deductions: 760,
    netPay: 5460,
    status: 'Pending',
    note: 'Queued for processing batch B',
  },
  {
    id: 'PR-24005',
    employee: 'Sophia Chen',
    employeeNumber: 'EMP-1384',
    department: 'Operations',
    cycle: 'March 2026',
    baseSalary: 6640,
    allowances: 510,
    deductions: 980,
    netPay: 6170,
    status: 'Flagged',
    note: 'Allowance variance requires review',
  },
  {
    id: 'PR-24006',
    employee: 'Ethan Rivera',
    employeeNumber: 'EMP-1415',
    department: 'Engineering',
    cycle: 'February 2026',
    baseSalary: 7920,
    allowances: 640,
    deductions: 1180,
    netPay: 7380,
    status: 'Processed',
    note: 'Closed in prior payroll cycle',
  },
]

function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function statusClassName(status: PayrollStatus) {
  switch (status) {
    case 'Processed':
      return 'border-transparent bg-emerald-50 text-emerald-700'
    case 'Pending':
      return 'border-slate-200 bg-slate-50 text-slate-700'
    case 'Flagged':
      return 'border-transparent bg-amber-50 text-amber-700'
  }
}

function SummaryMetric({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="space-y-2 border-l border-slate-200 pl-4 first:border-l-0 first:pl-0">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="text-2xl font-semibold tracking-tight text-slate-950">{value}</p>
      <p className="text-sm text-slate-600">{hint}</p>
    </div>
  )
}

export function Payroll() {
  const [selectedCycle, setSelectedCycle] = useState<(typeof payrollCycles)[number]>('March 2026')
  const [selectedDepartment, setSelectedDepartment] = useState<(typeof departments)[number]>('All departments')
  const [selectedStatus, setSelectedStatus] = useState<(typeof statusFilters)[number]>('All statuses')

  const filteredEntries = useMemo(() => {
    return payrollEntries.filter((entry) => {
      const matchesCycle = entry.cycle === selectedCycle
      const matchesDepartment = selectedDepartment === 'All departments' || entry.department === selectedDepartment
      const matchesStatus = selectedStatus === 'All statuses' || entry.status === selectedStatus

      return matchesCycle && matchesDepartment && matchesStatus
    })
  }, [selectedCycle, selectedDepartment, selectedStatus])

  const summary = useMemo(() => {
    return filteredEntries.reduce(
      (result, entry) => {
        result.totalPayroll += entry.netPay
        if (entry.status === 'Processed') {
          result.processed += 1
        }
        if (entry.status === 'Pending') {
          result.pending += 1
        }
        if (entry.status === 'Flagged') {
          result.flagged += 1
        }
        return result
      },
      { totalPayroll: 0, processed: 0, pending: 0, flagged: 0 },
    )
  }, [filteredEntries])

  return (
    <div className="space-y-6 text-slate-900">
      <section className="space-y-6 border-b border-slate-200 pb-6">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-3xl space-y-3">
            <Badge variant="outline" className="w-fit border-slate-200 bg-slate-50 text-slate-600">
              Payroll control
            </Badge>
            <div className="space-y-2">
              <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Payroll</h2>
              <p className="text-sm leading-6 text-slate-600">
                Review each payroll line with financial clarity, confirm settlement readiness, and process the active pay cycle from a controlled register.
              </p>
            </div>
          </div>
          <div className="flex w-full flex-col gap-4 xl:max-w-sm xl:items-end">
            <div className="grid gap-3 sm:grid-cols-3 xl:w-full">
              <div className="space-y-2 sm:col-span-1 xl:col-span-3">
                <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="payroll-cycle-selector">
                  Payroll cycle
                </label>
                <Select id="payroll-cycle-selector" value={selectedCycle} onChange={(event) => setSelectedCycle(event.target.value as (typeof payrollCycles)[number])}>
                  {payrollCycles.map((cycle) => (
                    <option key={cycle} value={cycle}>
                      {cycle}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
            <Button className="w-full xl:w-auto" type="button">
              <BadgeDollarSign className="h-4 w-4" />
              Run payroll
            </Button>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <SummaryMetric label="Total payroll" value={formatCurrency(summary.totalPayroll)} hint={`${filteredEntries.length} employees in current register`} />
          <SummaryMetric label="Processed" value={String(summary.processed).padStart(2, '0')} hint="Ready for settlement release" />
          <SummaryMetric label="Pending" value={String(summary.pending + summary.flagged).padStart(2, '0')} hint="Requires processing or review" />
        </div>
      </section>

      <section className="space-y-4">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)]">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="control-cycle-filter">
              Payroll cycle
            </label>
            <Select id="control-cycle-filter" value={selectedCycle} onChange={(event) => setSelectedCycle(event.target.value as (typeof payrollCycles)[number])}>
              {payrollCycles.map((cycle) => (
                <option key={cycle} value={cycle}>
                  {cycle}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="department-filter">
              Department
            </label>
            <Select
              id="department-filter"
              value={selectedDepartment}
              onChange={(event) => setSelectedDepartment(event.target.value as (typeof departments)[number])}
            >
              {departments.map((department) => (
                <option key={department} value={department}>
                  {department}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="status-filter">
              Status
            </label>
            <Select id="status-filter" value={selectedStatus} onChange={(event) => setSelectedStatus(event.target.value as (typeof statusFilters)[number])}>
              {statusFilters.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </Select>
          </div>
        </div>

        <div className="overflow-hidden rounded-[var(--radius-surface)] border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-col gap-3 border-b border-slate-200 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-slate-950">Payroll register</h3>
              <p className="text-sm text-slate-600">Primary payroll workspace for salary review, deduction control, and net pay confirmation.</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <Filter className="h-4 w-4" />
              <span>{filteredEntries.length} rows</span>
            </div>
          </div>

          {filteredEntries.length ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-100 bg-slate-50/70 hover:bg-slate-50/70">
                    <TableHead className="h-11 px-6 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Employee</TableHead>
                    <TableHead className="text-right text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Base salary</TableHead>
                    <TableHead className="text-right text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Allowances</TableHead>
                    <TableHead className="text-right text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Deductions</TableHead>
                    <TableHead className="text-right text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Net pay</TableHead>
                    <TableHead className="px-6 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEntries.map((entry) => {
                    const grossPay = entry.baseSalary + entry.allowances

                    return (
                      <TableRow key={entry.id} className="border-slate-100 hover:bg-slate-50/60">
                        <TableCell className="px-6 py-4 align-top">
                          <div className="space-y-2">
                            <div>
                              <p className="font-semibold text-slate-900">{entry.employee}</p>
                              <p className="text-sm text-slate-500">
                                {entry.employeeNumber} • {entry.department}
                              </p>
                            </div>
                            <p className="text-sm text-slate-500">{entry.note}</p>
                          </div>
                        </TableCell>
                        <TableCell className="py-4 text-right align-top">
                          <div className="space-y-2">
                            <p className="font-medium tabular-nums text-slate-900">{formatCurrency(entry.baseSalary)}</p>
                            <p className="text-sm tabular-nums text-slate-500">Cycle: {entry.cycle}</p>
                          </div>
                        </TableCell>
                        <TableCell className="py-4 text-right align-top">
                          <div className="space-y-2">
                            <p className="font-medium tabular-nums text-slate-900">{formatCurrency(entry.allowances)}</p>
                            <p className="text-sm tabular-nums text-slate-500">Earnings: {formatCurrency(grossPay)}</p>
                          </div>
                        </TableCell>
                        <TableCell className="py-4 text-right align-top">
                          <div className="space-y-2">
                            <p className="font-medium tabular-nums text-slate-900">{formatCurrency(entry.deductions)}</p>
                            <p className="text-sm text-slate-500">Standard payroll deductions</p>
                          </div>
                        </TableCell>
                        <TableCell className="py-4 text-right align-top">
                          <div className="space-y-2">
                            <p className="font-semibold tabular-nums text-slate-950">{formatCurrency(entry.netPay)}</p>
                            <p className="text-sm text-slate-500">Settlement amount</p>
                          </div>
                        </TableCell>
                        <TableCell className="px-6 py-4 align-top">
                          <div className="space-y-2">
                            <Badge variant="outline" className={cn('w-fit', statusClassName(entry.status))}>
                              {entry.status}
                            </Badge>
                            <p className="text-sm text-slate-500">{entry.id}</p>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="px-4 py-6 sm:px-6">
              <EmptyState
                action={
                  <Button type="button">
                    <RefreshCw className="h-4 w-4" />
                    Run payroll
                  </Button>
                }
                className="border-none bg-transparent p-0 text-left shadow-none"
                icon={CalendarRange}
                message="No payroll records match the selected controls. Adjust the filters or run payroll for the selected cycle to populate the register."
                title="No payroll data for this view"
              />
            </div>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-[var(--radius-surface)] border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-slate-100 p-2 text-slate-700">
                <Wallet className="h-4 w-4" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-900">Settlement readiness</p>
                <p className="text-sm text-slate-600">Processed entries are aligned for release once final reconciliation is complete.</p>
              </div>
            </div>
          </div>
          <div className="rounded-[var(--radius-surface)] border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-slate-100 p-2 text-slate-700">
                <BadgeDollarSign className="h-4 w-4" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-900">Financial control</p>
                <p className="text-sm text-slate-600">Base salary, allowances, deductions, and net pay remain aligned for rapid review.</p>
              </div>
            </div>
          </div>
          <div className="rounded-[var(--radius-surface)] border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-slate-100 p-2 text-slate-700">
                <RefreshCw className="h-4 w-4" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-900">Processing focus</p>
                <p className="text-sm text-slate-600">Pending and flagged lines stay visible without adding visual noise to the main table.</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
