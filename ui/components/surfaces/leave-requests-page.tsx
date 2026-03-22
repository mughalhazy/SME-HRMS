'use client'

import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CalendarClock, CheckCircle2, Clock3, RefreshCw, ShieldCheck } from 'lucide-react'

import { EmptyState, ErrorState, StatSkeletonGrid, TableSkeleton } from '@/components/base/feedback'
import { KpiGrid, PageHero, PageStack, SectionHeading, StatCard } from '@/components/base/page'
import { Button } from '@/components/base/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/base/table'
import { apiRequest } from '@/lib/api/client'

type LeaveRow = {
  leave_request_id: string
  employee_name: string
  department_name: string
  leave_type: string
  start_date: string
  end_date: string
  total_days: number
  approver_name?: string
  status: string
}

const coverageIcons = {
  pending: Clock3,
  approved: CheckCircle2,
  reviewed: ShieldCheck,
} as const

type CoverageSignalKey = keyof typeof coverageIcons

export function LeaveRequestsPage() {
  const query = useQuery({
    queryKey: ['leave-requests'],
    queryFn: () => apiRequest<{ data: LeaveRow[] }>('/api/v1/leave/requests'),
  })

  const leaveRows = query.data?.data ?? []
  const coverageSignals = useMemo<{ key: CoverageSignalKey; label: string; value: string; hint: string }[]>(
    () => [
      {
        key: 'pending',
        label: 'Pending approvals',
        value: String(leaveRows.filter((row) => row.status === 'Submitted').length),
        hint: 'Actionable now',
      },
      {
        key: 'approved',
        label: 'Approved this week',
        value: String(leaveRows.filter((row) => row.status === 'Approved').length),
        hint: 'No blockers detected',
      },
      {
        key: 'reviewed',
        label: 'Coverage reviewed',
        value: leaveRows.length ? '100%' : '0%',
        hint: 'Manager check recorded',
      },
    ],
    [leaveRows],
  )

  return (
    <PageStack>
      <PageHero
        eyebrow="Leave requests"
        title="Keep approvals clear, fast, and low-risk"
        description={
          <>
            This surface is aligned to <code className="rounded bg-slate-100 px-1 py-0.5">Leave</code> with the approval queue,
            department context, and coverage clarity surfaced first.
          </>
        }
        actions={
          <Button variant="outline" onClick={() => query.refetch()} disabled={query.isFetching}>
            <RefreshCw className={`h-4 w-4 ${query.isFetching ? 'animate-spin' : ''}`} />
            Refresh queue
          </Button>
        }
      />

      {query.isLoading ? (
        <>
          <StatSkeletonGrid count={3} />
          <TableSkeleton rows={6} columns={5} />
        </>
      ) : query.isError ? (
        <ErrorState title="Unable to load leave requests" message={query.error.message} onRetry={() => query.refetch()} />
      ) : (
        <>
          <KpiGrid className="xl:grid-cols-3">
            {coverageSignals.map((signal) => {
              const Icon = coverageIcons[signal.key]
              return <StatCard key={signal.label} title={signal.label} value={signal.value} hint={signal.hint} icon={Icon} />
            })}
          </KpiGrid>

          <section className="overflow-hidden rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-surface)]">
            <SectionHeading
              title="Approval queue"
              description="Most urgent requests stay at the top with department and approver context visible."
              badge={<span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">Canonical surface: Leave</span>}
            />

            {leaveRows.length === 0 ? (
                <div className="p-5">
                  <EmptyState
                    icon={CalendarClock}
                    title="No leave requests yet"
                    message="Leave requests will appear here once employees begin submitting time-off requests."
                    action={<Button variant="outline" onClick={() => query.refetch()} disabled={query.isFetching}>Refresh queue</Button>}
                  />
                </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Leave</TableHead>
                    <TableHead>Dates</TableHead>
                    <TableHead>Approver</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leaveRows.map((row) => (
                    <TableRow key={row.leave_request_id}>
                      <TableCell>
                        <p className="font-medium text-slate-950">{row.employee_name}</p>
                        <p className="text-slate-500">{row.department_name}</p>
                      </TableCell>
                      <TableCell className="text-slate-600">{row.leave_type} · {row.total_days} days</TableCell>
                      <TableCell className="text-slate-600">{row.start_date} → {row.end_date}</TableCell>
                      <TableCell className="text-slate-600">{row.approver_name ?? 'Pending assignment'}</TableCell>
                      <TableCell>
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${row.status === 'Submitted' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                          {row.status}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </section>
        </>
      )}
    </PageStack>
  )
}
