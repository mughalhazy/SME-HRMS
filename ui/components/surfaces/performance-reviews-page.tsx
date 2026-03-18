import { CheckCheck, MessageSquareText, Target, TrendingUp } from 'lucide-react'

import { PageGrid, PageHero, PageStack, SectionHeading, StatCard } from '@/components/ui/page'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

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
    <PageStack>
      <PageHero
        eyebrow="Performance reviews"
        title="Review-cycle status with clear completion signals"
        description="The page keeps the review state visible first so HR can quickly see which reviews are drafted, submitted, or acknowledged without digging into noisy detail views."
      />

      <PageGrid className="md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Submitted" value="12" hint="Ready for acknowledgment" icon={CheckCheck} />
        <StatCard title="Drafts" value="3" hint="Manager follow-up needed" icon={MessageSquareText} />
        <StatCard title="High ratings" value="5" hint="Talent retention watchlist" icon={TrendingUp} />
        <StatCard title="Goal alignment" value="94%" hint="Cycle tracking on course" icon={Target} />
      </PageGrid>

      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <SectionHeading title="Review queue" description="One row per review with reviewer, department, period, and rating context." />
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Employee</TableHead>
              <TableHead>Reviewer</TableHead>
              <TableHead>Period</TableHead>
              <TableHead>Rating</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {reviewRows.map((row) => (
              <TableRow key={row.performanceReviewId}>
                <TableCell>
                  <p className="font-medium text-slate-950">{row.employeeName}</p>
                  <p className="text-slate-500">{row.departmentName}</p>
                </TableCell>
                <TableCell className="text-slate-600">{row.reviewerName}</TableCell>
                <TableCell className="text-slate-600">{row.reviewPeriod}</TableCell>
                <TableCell className="text-slate-600">{row.overallRating}</TableCell>
                <TableCell>
                  <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusClassName(row.status)}`}>
                    {row.status}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </section>
    </PageStack>
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
