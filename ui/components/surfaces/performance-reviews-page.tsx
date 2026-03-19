import Link from 'next/link'
import {
  ArrowRight,
  ChartColumnIncreasing,
  CheckCheck,
  ChevronRight,
  Clock3,
  LoaderCircle,
  Sparkles,
  Star,
  TrendingDown,
  TrendingUp,
  UsersRound,
} from 'lucide-react'

import { EmptyState, Skeleton } from '@/components/ui/feedback'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PageGrid, PageHero, PageStack } from '@/components/ui/page'

const metrics = [
  {
    label: 'Reviews pending',
    value: '32',
    note: '8 due this week',
    icon: Clock3,
  },
  {
    label: 'Completed reviews',
    value: '84',
    note: '72% of cycle closed',
    icon: CheckCheck,
  },
  {
    label: 'Avg rating',
    value: '4.2',
    note: 'Across submitted reviews',
    icon: ChartColumnIncreasing,
  },
  {
    label: 'Top performers',
    value: '11',
    note: 'Rated 4.7 and above',
    icon: Star,
  },
]

const reviewQueue = [
  {
    id: 'prf-4401',
    employee: 'Noah Bennett',
    role: 'Senior Product Engineer',
    department: 'Engineering',
    status: 'Pending',
    rating: null,
    dueDate: 'Mar 24',
    dueContext: 'Manager review due in 5 days',
  },
  {
    id: 'prf-4402',
    employee: 'Amina Yusuf',
    role: 'Finance Manager',
    department: 'Finance',
    status: 'In progress',
    rating: '4.4',
    dueDate: 'Mar 22',
    dueContext: 'Calibration notes waiting',
  },
  {
    id: 'prf-4403',
    employee: 'Jordan Kim',
    role: 'Operations Lead',
    department: 'Operations',
    status: 'Completed',
    rating: '4.8',
    dueDate: 'Mar 18',
    dueContext: 'Closed 1 day early',
  },
  {
    id: 'prf-4404',
    employee: 'Priya Shah',
    role: 'HR Business Partner',
    department: 'People',
    status: 'Pending',
    rating: null,
    dueDate: 'Mar 27',
    dueContext: 'Self review still missing',
  },
  {
    id: 'prf-4405',
    employee: 'Liam Carter',
    role: 'Customer Success Manager',
    department: 'Customer Success',
    status: 'In progress',
    rating: '3.8',
    dueDate: 'Mar 21',
    dueContext: 'Peer feedback 2/3 complete',
  },
]

const topPerformers = [
  { name: 'Jordan Kim', team: 'Operations', rating: '4.8', note: 'Strong cross-functional execution' },
  { name: 'Maya Patel', team: 'Design', rating: '4.7', note: 'Highest collaboration score' },
  { name: 'Ethan Cole', team: 'Sales', rating: '4.7', note: 'Exceeded quota and mentoring goals' },
]

const needsAttention = [
  { name: 'Liam Carter', team: 'Customer Success', gap: 'Delivery consistency trending down' },
  { name: 'Olivia Chen', team: 'Marketing', gap: 'Review overdue with no manager draft' },
]

const comparisonStats = [
  { label: 'Highest team avg', value: 'Engineering · 4.5' },
  { label: 'Most pending', value: 'Operations · 9 reviews' },
  { label: 'Fastest completion', value: 'People · 6.1 days' },
]

const pastReviews = [
  {
    period: 'Q4 2025',
    completion: '91%',
    summary: 'Completion improved after review deadlines were staggered by department.',
    trend: 'Completion rate +9%',
  },
  {
    period: 'Q3 2025',
    completion: '82%',
    summary: 'Ratings clustered tightly, suggesting stronger calibration but less differentiation.',
    trend: 'Avg rating variance -0.3',
  },
  {
    period: 'Mid-year 2025',
    completion: '88%',
    summary: 'Top performer concentration shifted from Sales to Engineering and Operations.',
    trend: 'Top performers +4 employees',
  },
]

export function PerformanceReviewsPage() {
  return (
    <PageStack className="gap-6">
      <PageHero
        eyebrow="Performance"
        title="Performance"
        description={
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
            <p>32 reviews pending across the current cycle.</p>
            <span className="hidden text-slate-300 sm:inline">•</span>
            <p className="text-slate-500">Prioritize overdue managers, compare ratings, and move quickly into review detail.</p>
          </div>
        }
        actions={
          <>
            <Button asChild>
              <Link href="/performance/new">
                Start review
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/performance?filter=pending">Pending first</Link>
            </Button>
          </>
        }
      />

      <PageGrid className="gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon

          return (
            <Card key={metric.label} className="border-slate-200 bg-white shadow-sm">
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-slate-500">{metric.label}</p>
                    <p className="text-3xl font-semibold tracking-tight text-slate-950">{metric.value}</p>
                    <p className="text-sm text-slate-600">{metric.note}</p>
                  </div>
                  <div className="rounded-2xl bg-slate-100 p-2.5 text-slate-700">
                    <Icon className="h-4 w-4" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </PageGrid>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(320px,1fr)]">
        <section className="overflow-hidden rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-surface)]">
          <div className="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-950">Review queue</p>
              <p className="text-sm text-slate-600">The active review workspace surfaces due dates, progress, and rating context without turning into a heavy table.</p>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              <UsersRound className="h-3.5 w-3.5" />
              5 priority reviews
            </div>
          </div>

          <div className="divide-y divide-slate-200">
            {reviewQueue.map((review) => (
              <Link
                key={review.id}
                href={`/performance/${review.id}`}
                className="grid gap-4 px-5 py-4 transition-colors hover:bg-slate-50 xl:grid-cols-[minmax(0,1.4fr)_140px_120px_140px_24px] xl:items-center"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-slate-950">{review.employee}</p>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      {review.department}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{review.role}</p>
                  <p className="mt-2 text-xs font-medium text-slate-500">{review.dueContext}</p>
                </div>

                <div className="space-y-1">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Status</p>
                  <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusClassName(review.status)}`}>
                    {review.status}
                  </span>
                </div>

                <div className="space-y-1">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Rating</p>
                  <p className="text-sm font-semibold text-slate-950">{review.rating ?? '—'}</p>
                </div>

                <div className="space-y-1">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Due date</p>
                  <p className="text-sm font-semibold text-slate-950">{review.dueDate}</p>
                </div>

                <div className="hidden justify-self-end text-slate-400 xl:block">
                  <ChevronRight className="h-4 w-4" />
                </div>
              </Link>
            ))}
          </div>
        </section>

        <aside className="space-y-4">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2 text-emerald-600">
                <TrendingUp className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-[0.18em]">Top performers</span>
              </div>
              <CardTitle className="text-base">Standout employees this cycle</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {topPerformers.map((employee) => (
                <div key={employee.name} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium text-slate-950">{employee.name}</p>
                      <p className="text-sm text-slate-500">{employee.team}</p>
                    </div>
                    <p className="text-sm font-semibold text-slate-950">{employee.rating}</p>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{employee.note}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2 text-amber-600">
                <TrendingDown className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-[0.18em]">Needs attention</span>
              </div>
              <CardTitle className="text-base">Where follow-up should start</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {needsAttention.map((employee) => (
                <div key={employee.name} className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                  <p className="font-medium text-slate-950">{employee.name}</p>
                  <p className="text-sm text-slate-500">{employee.team}</p>
                  <p className="mt-2 text-sm text-slate-600">{employee.gap}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2 text-slate-300">
                <Sparkles className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-[0.18em]">Quick comparisons</span>
              </div>
              <CardTitle className="text-base text-white">Compare team performance at a glance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {comparisonStats.map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{stat.label}</p>
                  <p className="mt-2 text-sm font-semibold text-white">{stat.value}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </aside>
      </div>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.65fr)]">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader className="border-b border-slate-200 pb-4">
            <CardTitle className="text-base">Past reviews and cycle trends</CardTitle>
            <p className="text-sm text-slate-600">Historical summaries keep recent context visible for calibration and decision making.</p>
          </CardHeader>
          <CardContent className="space-y-4 pt-5">
            {pastReviews.map((review) => (
              <div key={review.period} className="grid gap-4 rounded-2xl border border-slate-200 p-4 md:grid-cols-[160px_minmax(0,1fr)_150px] md:items-center">
                <div>
                  <p className="text-sm font-semibold text-slate-950">{review.period}</p>
                  <p className="mt-1 text-sm text-slate-500">Completion {review.completion}</p>
                </div>
                <p className="text-sm leading-6 text-slate-600">{review.summary}</p>
                <p className="text-sm font-semibold text-slate-950 md:text-right">{review.trend}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">No reviews state</CardTitle>
            </CardHeader>
            <CardContent>
              <EmptyState
                icon={CheckCheck}
                title="No active reviews"
                message="When a new cycle begins, pending reviews will appear here with status, due date, and comparison context."
                action={
                  <Button asChild>
                    <Link href="/performance/new">Create review</Link>
                  </Button>
                }
              />
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">No insights state</CardTitle>
            </CardHeader>
            <CardContent>
              <EmptyState
                icon={ChartColumnIncreasing}
                title="No insights yet"
                message="Insights will unlock after enough reviews are submitted to compare teams, ratings, and completion patterns."
              />
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Loading placeholders</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-[minmax(0,1fr)_110px_90px] gap-3 rounded-2xl border border-slate-200 p-4">
                <div className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3.5 w-48" />
                </div>
                <Skeleton className="h-7 w-20 rounded-full" />
                <Skeleton className="h-7 w-16" />
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <LoaderCircle className="h-4 w-4 animate-spin" />
                Loading review insights
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </PageStack>
  )
}

function statusClassName(status: string) {
  switch (status) {
    case 'Completed':
      return 'bg-emerald-100 text-emerald-700'
    case 'In progress':
      return 'bg-sky-100 text-sky-700'
    default:
      return 'bg-amber-100 text-amber-700'
  }
}
