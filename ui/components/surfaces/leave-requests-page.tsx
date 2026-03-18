'use client'

import { CalendarClock, CheckCircle2, Clock3, ShieldCheck } from 'lucide-react'

const leaveRows = [
  {
    leaveRequestId: 'lev-1024',
    employeeName: 'Jordan Kim',
    departmentName: 'Operations',
    leaveType: 'Annual Leave',
    startDate: '2026-03-22',
    endDate: '2026-03-25',
    totalDays: 4,
    approverName: 'Sara Wong',
    status: 'Submitted',
  },
  {
    leaveRequestId: 'lev-1023',
    employeeName: 'Amina Yusuf',
    departmentName: 'Finance',
    leaveType: 'Sick Leave',
    startDate: '2026-03-18',
    endDate: '2026-03-19',
    totalDays: 2,
    approverName: 'Marco Diaz',
    status: 'Approved',
  },
  {
    leaveRequestId: 'lev-1022',
    employeeName: 'Helen Brooks',
    departmentName: 'Engineering',
    leaveType: 'Parental Leave',
    startDate: '2026-04-01',
    endDate: '2026-05-12',
    totalDays: 30,
    approverName: 'People Ops Council',
    status: 'Submitted',
  },
]

const coverageSignals = [
  { label: 'Pending approvals', value: '2', hint: 'Actionable now', icon: Clock3 },
  { label: 'Approved this week', value: '7', hint: 'No blockers detected', icon: CheckCircle2 },
  { label: 'Coverage reviewed', value: '100%', hint: 'Manager check recorded', icon: ShieldCheck },
]

export function LeaveRequestsPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Leave requests</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Keep approvals clear, fast, and low-risk.</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              This surface is aligned to <code className="rounded bg-slate-100 px-1 py-0.5">leave_requests_view</code> with the approval queue, department context, and coverage clarity surfaced first.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-4 py-2 text-sm font-medium text-amber-700">
            <CalendarClock className="h-4 w-4" />
            Approval-first layout
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {coverageSignals.map((signal) => (
          <div key={signal.label} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="rounded-2xl bg-slate-100 p-2 text-slate-700 w-fit">
              <signal.icon className="h-4 w-4" />
            </div>
            <p className="mt-4 text-sm font-medium text-slate-500">{signal.label}</p>
            <p className="mt-2 text-3xl font-semibold text-slate-950">{signal.value}</p>
            <p className="mt-1 text-sm text-slate-600">{signal.hint}</p>
          </div>
        ))}
      </section>

      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-2 border-b border-slate-200 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="font-semibold text-slate-950">Approval queue</h3>
            <p className="text-sm text-slate-600">Most urgent requests stay at the top with department and approver context visible.</p>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">Canonical surface: leave_requests</span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-3 font-medium">Employee</th>
                <th className="px-6 py-3 font-medium">Leave</th>
                <th className="px-6 py-3 font-medium">Dates</th>
                <th className="px-6 py-3 font-medium">Approver</th>
                <th className="px-6 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {leaveRows.map((row) => (
                <tr key={row.leaveRequestId} className="hover:bg-slate-50">
                  <td className="px-6 py-4">
                    <p className="font-medium text-slate-950">{row.employeeName}</p>
                    <p className="text-slate-500">{row.departmentName}</p>
                  </td>
                  <td className="px-6 py-4 text-slate-600">{row.leaveType} · {row.totalDays} days</td>
                  <td className="px-6 py-4 text-slate-600">{row.startDate} → {row.endDate}</td>
                  <td className="px-6 py-4 text-slate-600">{row.approverName}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${row.status === 'Submitted' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
