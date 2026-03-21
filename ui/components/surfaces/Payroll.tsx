'use client'

import { useMemo, useState } from 'react'
import { BadgeDollarSign, CalendarRange, Filter, RefreshCw, Wallet } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/feedback'
import { Select } from '@/components/ui/input'
import {
  KpiGrid,
  PageSection,
  PageSectionHeader,
  PageStack,
  StatCard,
  pageIconChipClassName,
  pageSurfaceClassName,
} from '@/components/ui/page'
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

const tableHeadClassName = 'h-11 px-6 text-xs font-semibold uppercase tracking-[0.16em] text-[var(--muted-foreground)]'
const numericHeadClassName = `${tableHeadClassName} text-right`
const employeeCellClassName = 'w-[28%] px-6 py-4 align-top'
const numericCellClassName = 'w-[14%] px-6 py-4 text-right align-top tabular-nums'
const statusCellClassName = 'w-[16%] px-6 py-4 align-top'
const filterFieldClassName = 'space-y-2'
const metricClassName = `${pageSurfaceClassName} p-4`

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

function NumericCell({ value, detail, emphasized = false }: { value: string; detail: string; emphasized?: boolean }) {
  return (
    <div className="space-y-2">
      <p className={cn('text-sm font-semibold text-slate-900', emphasized && 'text-base text-slate-950')}>{value}</p>
      <p className="text-xs text-slate-500">{detail}</p>
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
    <PageStack className="text-slate-900">
      <PageSection>
        <PageSectionHeader
          eyebrow="Payroll workspace"
          title="Payroll register control"
          description="Review each payroll line with financial clarity, confirm settlement readiness, and keep the active cycle controlled from one register."
          badge={
            <Badge variant="outline" className="w-fit border-[var(--border)] bg-[var(--surface-subtle)] text-[var(--muted-foreground)]">
              Payroll control
            </Badge>
          }
          actions={
            <div className="grid w-full gap-4 xl:w-[320px]">
              <div className={filterFieldClassName}>
                <label className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--muted-foreground)]" htmlFor="payroll-cycle-selector">
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

              <Button className="w-full xl:justify-center" type="button">
                <BadgeDollarSign className="h-4 w-4" />
                Run payroll
              </Button>
            </div>
          }
        />
      </PageSection>

      <KpiGrid className="xl:grid-cols-3">
        <StatCard title="Total payroll" value={formatCurrency(summary.totalPayroll)} hint={`${filteredEntries.length} employees in current register.`} icon={Wallet} />
        <StatCard title="Processed" value={String(summary.processed).padStart(2, '0')} hint="Registers ready for settlement release." icon={BadgeDollarSign} />
        <StatCard title="Pending" value={String(summary.pending + summary.flagged).padStart(2, '0')} hint="Processing or review items still open in this cycle." icon={RefreshCw} />
      </KpiGrid>

      <section className="space-y-4">
        <PageSection className="p-4">
          <div className="grid gap-4 xl:grid-cols-12 xl:items-end">
            <div className={cn(filterFieldClassName, 'xl:col-span-4')}>
              <label className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--muted-foreground)]" htmlFor="control-cycle-filter">
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

            <div className={cn(filterFieldClassName, 'xl:col-span-3')}>
              <label className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--muted-foreground)]" htmlFor="department-filter">
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

            <div className={cn(filterFieldClassName, 'xl:col-span-3')}>
              <label className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--muted-foreground)]" htmlFor="status-filter">
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

            <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)] xl:col-span-2 xl:justify-end xl:self-end">
              <Filter className="h-4 w-4" />
              <span>{filteredEntries.length} rows</span>
            </div>
          </div>
        </PageSection>

        <div className="overflow-hidden rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-surface)]">
          <div className="flex flex-col gap-3 border-b border-[var(--border)] bg-[var(--surface-subtle)] px-6 py-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-[var(--foreground)]">Payroll register</h3>
              <p className="text-sm text-slate-600">Primary payroll workspace for salary review, deduction control, and net pay confirmation.</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
              <CalendarRange className="h-4 w-4" />
              <span>{selectedCycle}</span>
            </div>
          </div>

          {filteredEntries.length ? (
            <Table className="table-fixed">
              <TableHeader>
                <TableRow className="border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface)] hover:shadow-none">
                  <TableHead className={cn(tableHeadClassName, 'w-[28%] px-6')}>Employee</TableHead>
                  <TableHead className={cn(numericHeadClassName, 'w-[14%] px-6')}>Base salary</TableHead>
                  <TableHead className={cn(numericHeadClassName, 'w-[14%] px-6')}>Allowances</TableHead>
                  <TableHead className={cn(numericHeadClassName, 'w-[14%] px-6')}>Deductions</TableHead>
                  <TableHead className={cn(numericHeadClassName, 'w-[14%] px-6')}>Net pay</TableHead>
                  <TableHead className={cn(tableHeadClassName, 'w-[16%] px-6 text-left')}>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="[&_tr:nth-child(even)]:bg-transparent">
                {filteredEntries.map((entry) => {
                  const grossPay = entry.baseSalary + entry.allowances

                  return (
                    <TableRow key={entry.id} className="h-auto border-[var(--border)] hover:bg-[var(--surface-subtle)]/70 hover:shadow-none">
                      <TableCell className={employeeCellClassName}>
                        <div className="space-y-2">
                          <div className="space-y-1">
                            <p className="text-sm font-semibold text-slate-950">{entry.employee}</p>
                            <p className="text-xs text-slate-500">
                              {entry.employeeNumber} · {entry.department}
                            </p>
                          </div>
                          <p className="text-xs leading-5 text-slate-500">{entry.note}</p>
                        </div>
                      </TableCell>

                      <TableCell className={numericCellClassName}>
                        <NumericCell value={formatCurrency(entry.baseSalary)} detail={`Cycle ${entry.cycle}`} />
                      </TableCell>

                      <TableCell className={numericCellClassName}>
                        <NumericCell value={formatCurrency(entry.allowances)} detail={`Gross ${formatCurrency(grossPay)}`} />
                      </TableCell>

                      <TableCell className={numericCellClassName}>
                        <NumericCell value={formatCurrency(entry.deductions)} detail="Standard deductions" />
                      </TableCell>

                      <TableCell className={numericCellClassName}>
                        <NumericCell value={formatCurrency(entry.netPay)} detail="Settlement amount" emphasized />
                      </TableCell>

                      <TableCell className={statusCellClassName}>
                        <div className="space-y-2">
                          <Badge
                            variant="outline"
                            className={cn(
                              'inline-flex min-w-24 justify-center rounded-full px-3 py-1 text-xs font-semibold',
                              statusClassName(entry.status),
                            )}
                          >
                            {entry.status}
                          </Badge>
                          <p className="text-xs text-slate-500">{entry.id}</p>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="px-6 py-6">
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
          <div className={metricClassName}>
            <div className="flex items-start gap-3">
              <div className={pageIconChipClassName}>
                <Wallet className="h-4 w-4" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-900">Settlement readiness</p>
                <p className="text-sm text-slate-600">Processed entries are aligned for release once final reconciliation is complete.</p>
              </div>
            </div>
          </div>

          <div className={metricClassName}>
            <div className="flex items-start gap-3">
              <div className={pageIconChipClassName}>
                <BadgeDollarSign className="h-4 w-4" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-900">Financial control</p>
                <p className="text-sm text-slate-600">Base salary, allowances, deductions, and net pay remain aligned for rapid review.</p>
              </div>
            </div>
          </div>

          <div className={metricClassName}>
            <div className="flex items-start gap-3">
              <div className={pageIconChipClassName}>
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
    </PageStack>
  )
}
