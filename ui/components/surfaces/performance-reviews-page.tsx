import Link from 'next/link'
import {
  ArrowRight,
  CalendarClock,
  CheckCheck,
  ChevronRight,
  Clock3,
  Download,
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
import { PageStack } from '@/components/ui/page'

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
    note: 'Stable from last cycle',
    icon: TrendingUp,
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
    department: 'Engineering',
    role: 'Senior Product Engineer',
    note: 'Peer feedback below team median',
    status: 'Pending',
    rating: '—',
    dueDate: 'Mar 24',
  },
  {
    id: 'prf-4402',
    employee: 'Amina Yusuf',
    department: 'Finance',
    role: 'Finance Manager',
    note: 'Calibration notes waiting',
    status: 'In progress',
    rating: '4.4',
    dueDate: 'Mar 22',
  },
  {
    id: 'prf-4403',
    employee: 'Jordan Kim',
    department: 'Operations',
    role: 'Operations Lead',
    note: 'Highest delivery score in team',
    status: 'Completed',
    rating: '4.8',
    dueDate: 'Mar 18',
  },
  {
    id: 'prf-4404',
    employee: 'Priya Shah',
    department: 'People',
    role: 'HR Business Partner',
    note: 'Self review still missing',
    status: 'Pending',
    rating: '—',
    dueDate: 'Mar 27',
  },
  {
    id: 'prf-4405',
    employee: 'Liam Carter',
    department: 'Customer Success',
    role: 'Customer Success Manager',
    note: 'Lowest momentum among open reviews',
    status: 'In progress',
    rating: '3.8',
    dueDate: 'Mar 21',
  },
]

const topPerformers = [
  { name: 'Jordan Kim', meta: 'Operations · 4.8', note: 'Strong execution across cross-functional work.' },
  { name: 'Maya Patel', meta: 'Design · 4.7', note: 'Highest collaboration signal in current cycle.' },
  { name: 'Ethan Cole', meta: 'Sales · 4.7', note: 'Exceeded quota and mentoring goals.' },
]

const needsAttention = [
  { name: 'Liam Carter', meta: 'Customer Success · 3.8', note: 'Delivery consistency trending below team baseline.' },
  { name: 'Olivia Chen', meta: 'Marketing · Pending', note: 'Review overdue with no manager draft started.' },
  { name: 'Priya Shah', meta: 'People · Pending', note: 'Missing self review is slowing completion.' },
]

const quickInsights = [
  { label: 'Most pending', value: 'Operations', note: '9 reviews are still open this cycle.' },
  { label: 'Fastest completion', value: 'People', note: '6.1 days from kickoff to close.' },
  { label: 'Rating variance', value: '1.1 pts', note: 'Wider spread than last cycle for stronger differentiation.' },
]

const historyCards = [
  {
    title: 'Past cycles',
    value: 'Q4 2025',
    note: '91% completion after staggered department deadlines.',
  },
  {
    title: 'Completion trend',
    value: '+9%',
    note: 'Cycle close rate improved compared with Q3 2025.',
  },
  {
    title: 'Rating variance',
    value: '-0.3',
    note: 'Last cycle ratings clustered tighter during calibration.',
  },
]

export function PerformanceReviewsPage() {
  return (
    <PageStack className="gap-6">
      <section className="grid grid-cols-12 gap-6 border-b border-slate-200 pb-6">
        <div className="col-span-12 flex flex-col gap-4 xl:col-span-8">
          <div className="flex flex-col gap-4">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Performance</p>
            <div className="flex flex-col gap-4">
              <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Performance</h1>
              <p className="text-sm leading-6 text-slate-600">32 reviews pending this cycle with clear comparison signals for prioritization, calibration, and decision support.</p>
            </div>
          </div>
        </div>

        <div className="col-span-12 flex flex-wrap items-start justify-start gap-4 xl:col-span-4 xl:justify-end">
          <Button asChild>
            <Link href="/performance/new">
              Start review
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/performance?filter=open">
              <Filter className="h-4 w-4" />
              Filter
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/performance/export">
              <Download className="h-4 w-4" />
              Export
            </Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon

          return (
            <Card key={metric.label} className="h-full">
              <CardContent className="flex h-full items-start justify-between gap-4 p-6">
                <div className="flex min-h-24 flex-col gap-4">
                  <p className="text-sm font-medium text-slate-500">{metric.label}</p>
                  <p className="text-3xl font-semibold tracking-tight text-slate-950">{metric.value}</p>
                  <p className="text-sm text-slate-600">{metric.note}</p>
                </div>
                <div className="rounded-[var(--radius-surface)] bg-slate-100 p-6 text-slate-700">
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </section>

      <section className="grid grid-cols-12 gap-6">
        <div className="col-span-12 xl:col-span-8">
          <Card>
            <CardHeader className="gap-4 border-b border-slate-200 p-6">
              <div className="flex items-center gap-4 text-slate-500">
                <Clock3 className="h-4 w-4" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">Review queue</span>
              </div>
              <div className="grid grid-cols-12 gap-4 text-sm text-slate-500">
                <div className="col-span-5">Employee</div>
                <div className="col-span-2">Status</div>
                <div className="col-span-2">Rating</div>
                <div className="col-span-2">Due date</div>
                <div className="col-span-1 text-right">Open</div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-200">
                {reviewQueue.map((review) => (
                  <Link
                    key={review.id}
                    href={`/performance/${review.id}`}
                    className="block transition-colors hover:bg-slate-50"
                  >
                    <div className="grid min-h-24 grid-cols-12 items-center gap-4 p-6">
                      <div className="col-span-5 flex min-w-0 flex-col gap-4">
                        <div className="flex flex-wrap items-center gap-4">
                          <p className="text-base font-semibold text-slate-950">{review.employee}</p>
                          <span className="rounded-full bg-slate-100 px-4 py-1 text-xs font-semibold text-slate-600">
                            {review.department}
                          </span>
                        </div>
                        <div className="flex min-w-0 flex-col gap-4 text-sm text-slate-600">
                          <p>{review.role}</p>
                          <p className="truncate">{review.note}</p>
                        </div>
                      </div>

                      <div className="col-span-2">
                        <div className="inline-flex rounded-full bg-slate-50 px-4 py-2 text-sm font-semibold">
                          <span className={statusClassName(review.status)}>{review.status}</span>
                        </div>
                      </div>

                      <div className="col-span-2">
                        <GhostCell value={review.rating} label={review.id.toUpperCase()} />
                      </div>

                      <div className="col-span-2">
                        <GhostCell value={review.dueDate} label="Due" />
                      </div>

                      <div className="col-span-1 flex justify-end text-slate-400">
                        <ChevronRight className="h-4 w-4" />
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <aside className="col-span-12 flex flex-col gap-6 xl:col-span-4">
          <Card>
            <CardHeader className="gap-4 border-b border-slate-200 p-6">
              <div className="flex items-center gap-4 text-slate-500">
                <TrendingUp className="h-4 w-4" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">Top performers</span>
              </div>
              <CardTitle className="text-base">Highest-rated employees this cycle</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 p-6">
              {topPerformers.map((item) => (
                <InsightItem key={item.name} name={item.name} meta={item.meta} note={item.note} />
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="gap-4 border-b border-slate-200 p-6">
              <div className="flex items-center gap-4 text-slate-500">
                <TrendingDown className="h-4 w-4" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">Needs attention</span>
              </div>
              <CardTitle className="text-base">Reviews requiring follow-up</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 p-6">
              {needsAttention.map((item) => (
                <InsightItem key={item.name} name={item.name} meta={item.meta} note={item.note} />
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="gap-4 border-b border-slate-200 p-6">
              <div className="flex items-center gap-4 text-slate-500">
                <Sparkles className="h-4 w-4" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">Quick insights</span>
              </div>
              <CardTitle className="text-base">Comparison signals for prioritization</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 p-6">
              {quickInsights.map((item) => (
                <div key={item.label} className="flex flex-col gap-4 rounded-[var(--radius-surface)] bg-slate-50 p-6">
                  <p className="text-sm font-medium text-slate-500">{item.label}</p>
                  <p className="text-base font-semibold text-slate-950">{item.value}</p>
                  <p className="text-sm text-slate-600">{item.note}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </aside>
      </section>

      <section className="grid grid-cols-12 gap-6">
        <div className="col-span-12 xl:col-span-8">
          <Card>
            <CardHeader className="gap-4 border-b border-slate-200 p-6">
              <div className="flex items-center gap-4 text-slate-500">
                <CalendarClock className="h-4 w-4" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">History and trends</span>
              </div>
              <CardTitle className="text-base">Past cycles and completion movement</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-6 p-6">
              <div className="grid gap-4 md:grid-cols-3">
                {historyCards.map((item) => (
                  <div key={item.title} className="flex h-full flex-col gap-4 rounded-[var(--radius-surface)] bg-slate-50 p-6">
                    <p className="text-sm font-medium text-slate-500">{item.title}</p>
                    <p className="text-2xl font-semibold tracking-tight text-slate-950">{item.value}</p>
                    <p className="text-sm text-slate-600">{item.note}</p>
                  </div>
                ))}
              </div>

              <div className="grid gap-4">
                <div className="grid grid-cols-12 gap-4 rounded-[var(--radius-surface)] bg-slate-50 p-6 text-sm text-slate-500">
                  <div className="col-span-3">Cycle</div>
                  <div className="col-span-3">Completion</div>
                  <div className="col-span-6">Summary</div>
                </div>
                <div className="grid grid-cols-12 gap-4 rounded-[var(--radius-surface)] p-6">
                  <div className="col-span-3 text-sm font-semibold text-slate-950">Q4 2025</div>
                  <div className="col-span-3 text-sm text-slate-600">91%</div>
                  <div className="col-span-6 text-sm text-slate-600">Completion improved after deadlines were staggered by department.</div>
                </div>
                <div className="grid grid-cols-12 gap-4 rounded-[var(--radius-surface)] p-6">
                  <div className="col-span-3 text-sm font-semibold text-slate-950">Q3 2025</div>
                  <div className="col-span-3 text-sm text-slate-600">82%</div>
                  <div className="col-span-6 text-sm text-slate-600">Ratings clustered tightly, suggesting stronger calibration with less differentiation.</div>
                </div>
                <div className="grid grid-cols-12 gap-4 rounded-[var(--radius-surface)] p-6">
                  <div className="col-span-3 text-sm font-semibold text-slate-950">Mid-year 2025</div>
                  <div className="col-span-3 text-sm text-slate-600">88%</div>
                  <div className="col-span-6 text-sm text-slate-600">Top performer concentration shifted from Sales toward Engineering and Operations.</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="col-span-12 flex flex-col gap-6 xl:col-span-4">
          <Card>
            <CardHeader className="gap-4 border-b border-slate-200 p-6">
              <div className="flex items-center gap-4 text-slate-500">
                <LoaderCircle className="h-4 w-4" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">Loading skeletons</span>
              </div>
              <CardTitle className="text-base">Workspace loading states</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 p-6">
              {[0, 1, 2].map((item) => (
                <div key={item} className="grid grid-cols-12 gap-4 rounded-[var(--radius-surface)] bg-slate-50 p-6">
                  <div className="col-span-5 flex flex-col gap-4">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-4 w-full" />
                  </div>
                  <div className="col-span-2 flex items-center">
                    <Skeleton className="h-8 w-20 rounded-full" />
                  </div>
                  <div className="col-span-2 flex items-center">
                    <Skeleton className="h-10 w-full rounded-[var(--radius-surface)]" />
                  </div>
                  <div className="col-span-2 flex items-center">
                    <Skeleton className="h-10 w-full rounded-[var(--radius-surface)]" />
                  </div>
                  <div className="col-span-1 flex items-center justify-end">
                    <Skeleton className="h-4 w-4" />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="gap-4 border-b border-slate-200 p-6">
              <CardTitle className="text-base">Empty states</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-6 p-6">
              <EmptyState
                icon={CheckCheck}
                title="No reviews in queue"
                message="When a cycle opens, pending reviews will appear here for comparison and prioritization."
                action={
                  <Button asChild>
                    <Link href="/performance/new">Create review</Link>
                  </Button>
                }
              />
              <EmptyState
                icon={Sparkles}
                title="No insights yet"
                message="Insights will populate after enough reviews are in progress or completed to compare patterns."
              />
            </CardContent>
          </Card>
        </div>
      </section>
    </PageStack>
  )
}

function InsightItem({
  name,
  meta,
  note,
}: {
  name: string
  meta: string
  note: string
}) {
  return (
    <div className="flex flex-col gap-4 rounded-[var(--radius-surface)] bg-slate-50 p-6">
      <div className="flex flex-col gap-4">
        <p className="text-base font-semibold text-slate-950">{name}</p>
        <p className="text-sm text-slate-500">{meta}</p>
      </div>
      <p className="text-sm text-slate-600">{note}</p>
    </div>
  )
}

function GhostCell({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex min-h-14 flex-col justify-center gap-4 rounded-[var(--radius-surface)] bg-slate-50 p-6">
      <p className="text-sm font-semibold text-slate-950">{value}</p>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</p>
    </div>
  )
}

function statusClassName(status: string) {
  switch (status) {
    case 'Completed':
      return 'text-emerald-700'
    case 'In progress':
      return 'text-sky-700'
    default:
      return 'text-amber-700'
  }
}
