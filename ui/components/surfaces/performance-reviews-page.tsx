import Link from 'next/link'
import {
  ArrowRight,
  CalendarClock,
  ChartColumnIncreasing,
  CheckCheck,
  ChevronRight,
  Clock3,
  Filter,
  LoaderCircle,
  Sparkles,
  Star,
  TrendingDown,
  TrendingUp,
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
    accent: 'bg-amber-50 text-amber-700',
  },
  {
    label: 'Completed reviews',
    value: '84',
    note: '72% of current cycle closed',
    icon: CheckCheck,
    accent: 'bg-emerald-50 text-emerald-700',
  },
  {
    label: 'Avg rating',
    value: '4.2',
    note: 'Steady from last cycle',
    icon: ChartColumnIncreasing,
    accent: 'bg-sky-50 text-sky-700',
  },
  {
    label: 'Top performers',
    value: '11',
    note: 'Rated 4.7 and above',
    icon: Star,
    accent: 'bg-violet-50 text-violet-700',
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
    priority: 'Overdue inputs',
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
    priority: 'Needs alignment',
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
    priority: 'Ready to calibrate',
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
    priority: 'Waiting on employee',
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
    priority: 'Needs attention',
  },
]

const topPerformers = [
  { name: 'Jordan Kim', meta: 'Operations · 4.8', note: 'Strong cross-functional execution' },
  { name: 'Maya Patel', meta: 'Design · 4.7', note: 'Highest collaboration score' },
  { name: 'Ethan Cole', meta: 'Sales · 4.7', note: 'Exceeded quota and mentoring goals' },
]

const needsAttention = [
  { name: 'Liam Carter', meta: 'Customer Success · 3.8', note: 'Delivery consistency trending down' },
  { name: 'Olivia Chen', meta: 'Marketing · pending', note: 'Review overdue with no manager draft' },
]

const comparisonStats = [
  { label: 'Highest team avg', value: 'Engineering · 4.5', context: '+0.3 above company avg' },
  { label: 'Most pending', value: 'Operations · 9 reviews', context: 'Largest review backlog this week' },
  { label: 'Fastest completion', value: 'People · 6.1 days', context: 'Best turnaround from kickoff to close' },
]

const trendCards = [
  {
    label: 'Ratings spread',
    value: '1.1 pts',
    context: 'Wider than last cycle, giving managers clearer differentiation.',
  },
  {
    label: 'Cycle velocity',
    value: '6.4 days',
    context: 'Average time from draft start to completion across open reviews.',
  },
  {
    label: 'Calibration risk',
    value: '4 teams',
    context: 'Departments with elevated pending volume and low completion momentum.',
  },
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
            <p>32 reviews pending.</p>
            <span className="hidden text-slate-300 sm:inline">•</span>
            <p className="text-slate-500">Analytical review workspace for comparison, prioritization, and decision making across the cycle.</p>
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
              <Link href="/performance?filter=pending">
                <Filter className="h-4 w-4" />
                Pending first
              </Link>
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
                  <div className={`rounded-2xl p-2.5 ${metric.accent}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </PageGrid>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,1fr)]">
        <div className="overflow-hidden rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-surface)]">
          <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                <Clock3 className="h-3.5 w-3.5" />
                Review queue
              </div>
              <div>
                <p className="text-lg font-semibold text-slate-950">Priority reviews in motion</p>
                <p className="text-sm text-slate-600">A list-first queue that keeps employee context, status, rating, and due date visible without dropping into a dense table.</p>
              </div>
            </div>

            <div className="grid gap-3 sm:w-[240px]">
              <div className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">This week</p>
                <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">5</p>
                <p className="mt-1 text-sm text-slate-600">Priority reviews need action this week.</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-3xl border border-slate-200 bg-white px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Pending</p>
                  <p className="mt-2 text-lg font-semibold text-slate-950">2</p>
                </div>
                <div className="rounded-3xl border border-slate-200 bg-white px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">In progress</p>
                  <p className="mt-2 text-lg font-semibold text-slate-950">2</p>
                </div>
              </div>
            </div>
          </div>

          <div className="divide-y divide-slate-200">
            {reviewQueue.map((review) => (
              <Link
                key={review.id}
                href={`/performance/${review.id}`}
                className="group block px-5 py-4 transition-colors hover:bg-slate-50"
              >
                <div className="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(260px,1fr)_24px] xl:items-center">
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-slate-950">{review.employee}</p>
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                        {review.department}
                      </span>
                      <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-500 ring-1 ring-slate-200">
                        {review.priority}
                      </span>
                    </div>
                    <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_180px] sm:items-end">
                      <div>
                        <p className="text-sm text-slate-600">{review.role}</p>
                        <p className="mt-1 text-sm text-slate-500">{review.dueContext}</p>
                      </div>
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 sm:justify-self-start xl:justify-self-end">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Status</p>
                        <span className={`mt-2 inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusClassName(review.status)}`}>
                          {review.status}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 xl:gap-2">
                    <QueueStat label="Rating" value={review.rating ?? '—'} />
                    <QueueStat label="Due date" value={review.dueDate} />
                    <QueueStat label="Review ID" value={review.id.toUpperCase()} />
                  </div>

                  <div className="hidden justify-self-end text-slate-400 transition-transform group-hover:translate-x-0.5 xl:block">
                    <ChevronRight className="h-4 w-4" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <aside className="space-y-4">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2 text-slate-500">
                <Sparkles className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-[0.18em]">Performance insights</span>
              </div>
              <CardTitle className="text-base">Signals to support calibration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <InsightGroup
                title="Top performers"
                icon={TrendingUp}
                tone="text-emerald-600"
                items={topPerformers}
              />

              <InsightGroup
                title="Needs attention"
                icon={TrendingDown}
                tone="text-amber-600"
                items={needsAttention}
              />
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-white shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2 text-slate-300">
                <ChartColumnIncreasing className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-[0.18em]">Quick comparisons</span>
              </div>
              <CardTitle className="text-base text-white">Compare where attention should go next</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {comparisonStats.map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{stat.label}</p>
                  <p className="mt-2 text-sm font-semibold text-white">{stat.value}</p>
                  <p className="mt-1 text-sm text-slate-300">{stat.context}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </aside>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(300px,0.95fr)]">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader className="border-b border-slate-200 pb-4">
            <div className="flex items-center gap-2 text-slate-500">
              <CalendarClock className="h-4 w-4" />
              <span className="text-xs font-semibold uppercase tracking-[0.18em]">History and trends</span>
            </div>
            <CardTitle className="text-base">Past reviews and cycle movement</CardTitle>
            <p className="text-sm text-slate-600">Recent summaries and trend snapshots keep prior cycles close to the active queue.</p>
          </CardHeader>
          <CardContent className="space-y-5 pt-5">
            <div className="grid gap-3 md:grid-cols-3">
              {trendCards.map((card) => (
                <div key={card.label} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{card.label}</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{card.value}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{card.context}</p>
                </div>
              ))}
            </div>

            <div className="space-y-4">
              {pastReviews.map((review) => (
                <div key={review.period} className="grid gap-4 rounded-3xl border border-slate-200 p-4 md:grid-cols-[160px_minmax(0,1fr)_160px] md:items-center">
                  <div>
                    <p className="text-sm font-semibold text-slate-950">{review.period}</p>
                    <p className="mt-1 text-sm text-slate-500">Completion {review.completion}</p>
                  </div>
                  <p className="text-sm leading-6 text-slate-600">{review.summary}</p>
                  <p className="text-sm font-semibold text-slate-950 md:text-right">{review.trend}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Fallback states</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-3xl border border-dashed border-slate-200 p-2">
                <EmptyState
                  icon={CheckCheck}
                  title="No active reviews"
                  message="When a new cycle begins, pending reviews appear here with status, due date, and rating context."
                  action={
                    <Button asChild>
                      <Link href="/performance/new">Create review</Link>
                    </Button>
                  }
                />
              </div>
              <div className="rounded-3xl border border-dashed border-slate-200 p-2">
                <EmptyState
                  icon={ChartColumnIncreasing}
                  title="No insights yet"
                  message="Insights unlock after enough reviews are submitted to compare teams, ratings, and completion patterns."
                />
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Loading placeholders</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[0, 1].map((item) => (
                <div key={item} className="grid gap-3 rounded-3xl border border-slate-200 p-4 sm:grid-cols-[minmax(0,1fr)_110px_90px] sm:items-center">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-36" />
                    <Skeleton className="h-3.5 w-full max-w-[220px]" />
                  </div>
                  <Skeleton className="h-7 w-20 rounded-full" />
                  <Skeleton className="h-7 w-16" />
                </div>
              ))}
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

function InsightGroup({
  title,
  icon: Icon,
  tone,
  items,
}: {
  title: string
  icon: typeof TrendingUp
  tone: string
  items: Array<{ name: string; meta: string; note: string }>
}) {
  return (
    <div className="space-y-3 rounded-3xl border border-slate-200 bg-slate-50 p-4">
      <div className={`flex items-center gap-2 ${tone}`}>
        <Icon className="h-4 w-4" />
        <p className="text-xs font-semibold uppercase tracking-[0.18em]">{title}</p>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.name} className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium text-slate-950">{item.name}</p>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{item.meta}</p>
            </div>
            <p className="mt-2 text-sm text-slate-600">{item.note}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function QueueStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-950">{value}</p>
    </div>
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
