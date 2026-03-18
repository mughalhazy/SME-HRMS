import type { ComponentType } from 'react'
import { CheckCheck, MessageSquareText, Target, TrendingUp } from 'lucide-react'

const reviewRows = [
  {
    performanceReviewId: 'prf-4401',
    employeeName: 'Noah Bennett',
    reviewerName: 'Helen Brooks',
    departmentName: 'Engineering',
    reviewPeriod: '2026-01-01 → 2026-03-31',
    overallRating: 'Exceeds Expectations',
    status: 'Submitted',
  },
  {
    performanceReviewId: 'prf-4402',
    employeeName: 'Amina Yusuf',
    reviewerName: 'Marco Diaz',
    departmentName: 'Finance',
    reviewPeriod: '2026-01-01 → 2026-03-31',
    overallRating: 'Meets Expectations',
    status: 'Acknowledged',
  },
  {
    performanceReviewId: 'prf-4403',
    employeeName: 'Jordan Kim',
    reviewerName: 'Sara Wong',
    departmentName: 'Operations',
    reviewPeriod: '2026-01-01 → 2026-03-31',
    overallRating: 'In Progress',
    status: 'Draft',
  },
]

export function PerformanceReviewsPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Performance reviews</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Review-cycle status with clear completion signals.</h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          The page keeps the review state visible first so HR can quickly see which reviews are drafted, submitted, or acknowledged without digging into noisy detail views.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <ReviewSignal title="Submitted" value="12" hint="Ready for acknowledgment" icon={CheckCheck} />
        <ReviewSignal title="Drafts" value="3" hint="Manager follow-up needed" icon={MessageSquareText} />
        <ReviewSignal title="High ratings" value="5" hint="Talent retention watchlist" icon={TrendingUp} />
        <ReviewSignal title="Goal alignment" value="94%" hint="Cycle tracking on course" icon={Target} />
      </section>

      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-4">
          <h3 className="font-semibold text-slate-950">Review queue</h3>
          <p className="text-sm text-slate-600">One row per review with reviewer, department, period, and rating context.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-6 py-3 font-medium">Employee</th>
                <th className="px-6 py-3 font-medium">Reviewer</th>
                <th className="px-6 py-3 font-medium">Period</th>
                <th className="px-6 py-3 font-medium">Rating</th>
                <th className="px-6 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {reviewRows.map((row) => (
                <tr key={row.performanceReviewId} className="hover:bg-slate-50">
                  <td className="px-6 py-4">
                    <p className="font-medium text-slate-950">{row.employeeName}</p>
                    <p className="text-slate-500">{row.departmentName}</p>
                  </td>
                  <td className="px-6 py-4 text-slate-600">{row.reviewerName}</td>
                  <td className="px-6 py-4 text-slate-600">{row.reviewPeriod}</td>
                  <td className="px-6 py-4 text-slate-600">{row.overallRating}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusClassName(row.status)}`}>
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

function ReviewSignal({ title, value, hint, icon: Icon }: { title: string; value: string; hint: string; icon: ComponentType<{ className?: string }> }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="rounded-2xl bg-slate-100 p-2 text-slate-700 w-fit">
        <Icon className="h-4 w-4" />
      </div>
      <p className="mt-4 text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-950">{value}</p>
      <p className="mt-1 text-sm text-slate-600">{hint}</p>
    </div>
  )
}

function statusClassName(status: string) {
  switch (status) {
    case 'Submitted':
      return 'bg-sky-100 text-sky-700'
    case 'Acknowledged':
      return 'bg-emerald-100 text-emerald-700'
    default:
      return 'bg-amber-100 text-amber-700'
  }
}
