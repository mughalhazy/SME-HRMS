'use client'

import {
  AlertTriangle,
  BadgeDollarSign,
  Building2,
  CheckCircle2,
  Clock3,
  CreditCard,
  Eye,
  MoreHorizontal,
  RefreshCw,
  ShieldAlert,
  Wallet,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'

type PayrollRunStatus = 'Processed' | 'Pending' | 'Failed'

type PayrollRun = {
  runId: string
  cycle: string
  employees: number
  totalAmount: string
  status: PayrollRunStatus
  date: string
}

const kpiCards = [
  { label: 'Current Cycle', value: 'March 2026', description: 'Primary payroll window', icon: Clock3, iconClassName: 'bg-sky-50 text-sky-700' },
  { label: 'Employees Paid', value: '1180', description: 'Successfully queued and settled', icon: CheckCircle2, iconClassName: 'bg-emerald-50 text-emerald-700' },
  { label: 'Pending Payments', value: '68', description: 'Awaiting bank confirmation', icon: AlertTriangle, iconClassName: 'bg-amber-50 text-amber-700' },
  { label: 'Total Payroll', value: '$1,240,000', description: 'Gross amount for this cycle', icon: Wallet, iconClassName: 'bg-violet-50 text-violet-700' },
] as const

const payrollRuns: PayrollRun[] = [
  { runId: 'PR-2026-03-05', cycle: 'Mar 01–05, 2026', employees: 260, totalAmount: '$278,000', status: 'Processed', date: 'Mar 05, 2026' },
  { runId: 'PR-2026-03-12', cycle: 'Mar 06–12, 2026', employees: 288, totalAmount: '$304,500', status: 'Processed', date: 'Mar 12, 2026' },
  { runId: 'PR-2026-03-19', cycle: 'Mar 13–19, 2026', employees: 304, totalAmount: '$319,800', status: 'Pending', date: 'Mar 19, 2026' },
  { runId: 'PR-2026-03-20A', cycle: 'Off-cycle Bonus', employees: 46, totalAmount: '$82,400', status: 'Failed', date: 'Mar 20, 2026' },
  { runId: 'PR-2026-03-26', cycle: 'Mar 20–26, 2026', employees: 282, totalAmount: '$255,300', status: 'Pending', date: 'Mar 26, 2026' },
]

const exceptions = [
  { title: 'Failed transactions', value: '12', detail: 'Needs payment gateway review', icon: CreditCard, accent: 'text-rose-700', surface: 'bg-rose-50' },
  { title: 'Missing bank details', value: '23', detail: 'Employees cannot be disbursed', icon: Building2, accent: 'text-amber-700', surface: 'bg-amber-50' },
  { title: 'Flagged employees', value: '7', detail: 'Manual verification required', icon: ShieldAlert, accent: 'text-violet-700', surface: 'bg-violet-50' },
] as const

const recentActivity = [
  { title: 'Payroll run PR-2026-03-19 submitted for settlement', time: 'Today • 09:42 AM', tone: 'bg-emerald-500' },
  { title: '12 failed bonus transfers escalated to finance operations', time: 'Today • 08:15 AM', tone: 'bg-rose-500' },
  { title: '23 employees flagged for missing bank details', time: 'Mar 18, 2026 • 05:24 PM', tone: 'bg-amber-500' },
  { title: 'March cycle reconciliation exported by Payroll Admin', time: 'Mar 18, 2026 • 02:10 PM', tone: 'bg-sky-500' },
  { title: 'Payroll run PR-2026-03-12 marked as processed', time: 'Mar 12, 2026 • 06:34 PM', tone: 'bg-slate-500' },
]

function getStatusStyles(status: PayrollRunStatus) {
  switch (status) {
    case 'Processed':
      return { badgeVariant: 'success' as const, badgeClassName: 'border-transparent bg-emerald-100 text-emerald-800', dotClassName: 'bg-emerald-500' }
    case 'Pending':
      return { badgeVariant: 'outline' as const, badgeClassName: 'border-amber-200 bg-amber-50 text-amber-800', dotClassName: 'bg-amber-500' }
    case 'Failed':
      return { badgeVariant: 'outline' as const, badgeClassName: 'border-rose-200 bg-rose-50 text-rose-800', dotClassName: 'bg-rose-500' }
  }
}

export function Payroll() {
  return (
    <div className="space-y-6 text-slate-900">
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-4 p-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <Badge variant="outline" className="w-fit border-slate-200 bg-slate-50 text-slate-600">Payroll operations</Badge>
            <div>
              <h2 className="text-3xl font-semibold tracking-tight text-slate-950">Payroll</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">Monitor cycles, track exceptions, and manage disbursement runs in one clean workspace.</p>
            </div>
          </div>
          <Button className="h-10 px-4 shadow-sm" type="button">
            <BadgeDollarSign className="h-4 w-4" />
            Run Payroll
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpiCards.map((item) => {
          const Icon = item.icon
          return (
            <Card key={item.label} className="border-slate-200 bg-white shadow-sm">
              <CardContent className="flex items-start justify-between p-5">
                <div className="space-y-1">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{item.label}</p>
                  <p className="text-2xl font-semibold tracking-tight text-slate-950">{item.value}</p>
                  <p className="text-sm text-slate-500">{item.description}</p>
                </div>
                <div className={cn('flex h-10 w-10 items-center justify-center rounded-xl border border-white/80', item.iconClassName)}>
                  <Icon className="h-4.5 w-4.5" />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader className="gap-2 border-b border-slate-100 pb-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="text-base text-slate-950">Payroll Runs</CardTitle>
                <CardDescription className="text-sm text-slate-500">Structured register of processed, pending, and failed payroll batches.</CardDescription>
              </div>
              <Badge className="border-slate-200 bg-slate-50 text-slate-600" variant="outline">{payrollRuns.length} runs</Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-100 bg-slate-50/70 hover:bg-slate-50/70">
                    <TableHead className="h-11 px-5 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Run ID</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cycle</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Employees</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Total Amount</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Status</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Date</TableHead>
                    <TableHead className="pr-5 text-right text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payrollRuns.map((run) => {
                    const status = getStatusStyles(run.status)
                    return (
                      <TableRow key={run.runId} className="border-slate-100 hover:bg-slate-50/80">
                        <TableCell className="px-5 py-3.5"><div className="font-semibold text-slate-800">{run.runId}</div></TableCell>
                        <TableCell className="py-3.5 text-sm text-slate-600">{run.cycle}</TableCell>
                        <TableCell className="py-3.5 text-sm font-medium text-slate-700">{run.employees}</TableCell>
                        <TableCell className="py-3.5 text-sm font-semibold text-slate-900">{run.totalAmount}</TableCell>
                        <TableCell className="py-3.5">
                          <Badge className={cn('gap-2 font-semibold', status.badgeClassName)} variant={status.badgeVariant}>
                            <span className={cn('h-2 w-2 rounded-full', status.dotClassName)} />
                            {run.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="py-3.5 text-sm text-slate-600">{run.date}</TableCell>
                        <TableCell className="py-3.5 pr-5 text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button className="h-8 w-8 rounded-lg" size="icon" type="button" variant="ghost"><MoreHorizontal className="h-4 w-4" /></Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="border-slate-200 bg-white">
                              <DropdownMenuItem><Eye className="h-4 w-4 text-slate-500" />View</DropdownMenuItem>
                              <DropdownMenuItem className={cn(run.status !== 'Failed' && 'text-slate-400')} disabled={run.status !== 'Failed'}><RefreshCw className="h-4 w-4" />Retry</DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-base text-slate-950">Exceptions Panel</CardTitle>
              <CardDescription className="text-sm text-slate-500">High-priority issues requiring payroll operations follow-up.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {exceptions.map((item, index) => {
                const Icon = item.icon
                return (
                  <div key={item.title}>
                    <div className="flex items-start gap-3">
                      <div className={cn('flex h-10 w-10 shrink-0 items-center justify-center rounded-xl', item.surface)}>
                        <Icon className={cn('h-4.5 w-4.5', item.accent)} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-slate-800">{item.title}</p>
                            <p className="mt-1 text-sm text-slate-500">{item.detail}</p>
                          </div>
                          <span className={cn('text-lg font-semibold', item.accent)}>{item.value}</span>
                        </div>
                      </div>
                    </div>
                    {index < exceptions.length - 1 ? <Separator className="mt-4" /> : null}
                  </div>
                )
              })}
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-base text-slate-950">Recent Activity</CardTitle>
              <CardDescription className="text-sm text-slate-500">Operational events from the current cycle.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentActivity.map((item, index) => (
                <div key={item.title} className="space-y-4">
                  <div className="flex items-start gap-3">
                    <span className={cn('mt-1.5 h-2.5 w-2.5 rounded-full', item.tone)} />
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-slate-900">{item.title}</p>
                      <p className="text-sm text-slate-500">{item.time}</p>
                    </div>
                  </div>
                  {index < recentActivity.length - 1 ? <Separator /> : null}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  )
}
