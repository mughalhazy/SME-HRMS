import Link from 'next/link'
import {
  ArrowRight,
  CheckCheck,
  Clock3,
  Sparkles,
  Star,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { PageStack } from '@/components/ui/page'

const metrics = [
  {
    label: 'Reviews pending',
    value: '32',
    note: '8 due this week',
    icon: Clock3,
  },
  {
    label: 'Completed',
    value: '84',
    note: '72% of cycle closed',
    icon: CheckCheck,
  },
  {
    label: 'Average score',
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
    stage: 'Manager review',
    score: '—',
    dueDate: 'Mar 24',
  },
  {
    id: 'prf-4402',
    employee: 'Amina Yusuf',
    department: 'Finance',
    role: 'Finance Manager',
    note: 'Calibration notes waiting',
    status: 'In progress',
    stage: 'Calibration',
    score: '4.4',
    dueDate: 'Mar 22',
  },
  {
    id: 'prf-4403',
    employee: 'Jordan Kim',
    department: 'Operations',
    role: 'Operations Lead',
    note: 'Highest delivery score in team',
    status: 'Completed',
    stage: 'Closed',
    score: '4.8',
    dueDate: 'Mar 18',
  },
  {
    id: 'prf-4404',
    employee: 'Priya Shah',
    department: 'People',
    role: 'HR Business Partner',
    note: 'Self review still missing',
    status: 'Pending',
    stage: 'Self review',
    score: '—',
    dueDate: 'Mar 27',
  },
  {
    id: 'prf-4405',
    employee: 'Liam Carter',
    department: 'Customer Success',
    role: 'Customer Success Manager',
    note: 'Lowest momentum among open reviews',
    status: 'In progress',
    stage: 'Manager review',
    score: '3.8',
    dueDate: 'Mar 21',
  },
]

const topPerformers = [
  { name: 'Jordan Kim', meta: 'Operations · 4.8', note: 'Strong execution across cross-functional work.' },
  { name: 'Maya Patel', meta: 'Design · 4.7', note: 'Highest collaboration signal in current cycle.' },
  { name: 'Ethan Cole', meta: 'Sales · 4.7', note: 'Exceeded quota and mentoring goals.' },
]

const lowPerformers = [
  { name: 'Liam Carter', meta: 'Customer Success · 3.8', note: 'Delivery consistency trending below team baseline.' },
  { name: 'Olivia Chen', meta: 'Marketing · Pending', note: 'Review overdue with no manager draft started.' },
  { name: 'Priya Shah', meta: 'People · Pending', note: 'Missing self review is slowing completion.' },
]

const quickInsights = [
  { label: 'Trend', value: 'Completion pace is up 9%', note: 'More reviews are closing before calibration starts.' },
  { label: 'Concentration', value: 'Operations has the heaviest queue', note: '9 open reviews are still waiting for manager action.' },
  { label: 'Spread', value: 'Rating variance is 1.1 pts', note: 'Differentiation is wider than last cycle and needs calibration focus.' },
]

export function PerformanceReviewsPage() {
  return (
    <PageStack className="gap-6">
      <section className="grid grid-cols-12 gap-6 border-b border-slate-200 pb-6">
        <div className="col-span-12 flex flex-col gap-4 xl:col-span-9">
          <div className="flex flex-col gap-3">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Performance</p>
            <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
              <div className="flex flex-col gap-3">
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Performance reviews</h1>
                <p className="max-w-3xl text-sm leading-6 text-slate-600">
                  Spring 2026 cycle with active calibration in progress and pending reviews prioritized for manager follow-up.
                </p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
            <span className="rounded-full bg-slate-100 px-3 py-1.5 font-medium text-slate-700">Cycle: Spring 2026</span>
            <span className="rounded-full bg-amber-50 px-3 py-1.5 font-medium text-amber-700">Status: In progress</span>
            <span className="rounded-full bg-slate-100 px-3 py-1.5 font-medium text-slate-700">Period: Mar 1 — Apr 15</span>
          </div>
        </div>

        <div className="col-span-12 flex items-start justify-start xl:col-span-3 xl:justify-end">
          <Button asChild>
            <Link href="/performance/new">
              Start review
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon

          return (
            <Card key={metric.label} className="h-full border-slate-200 shadow-none">
              <CardContent className="flex h-full items-start justify-between gap-4 p-4">
                <div className="flex min-h-24 flex-col justify-between gap-2">
                  <p className="text-sm font-medium text-slate-500">{metric.label}</p>
                  <p className="text-3xl font-semibold tracking-tight text-slate-950">{metric.value}</p>
                  <p className="text-sm text-slate-600">{metric.note}</p>
                </div>
                <div className="rounded-[var(--radius-surface)] bg-slate-100 p-3 text-slate-600">
                  <Icon className="h-4 w-4" />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </section>

      <section className="grid grid-cols-12 gap-6">
        <div className="col-span-12 xl:col-span-8">
          <div className="rounded-[var(--radius-surface)] border border-slate-200 bg-white">
            <div className="flex flex-col gap-4 border-b border-slate-200 p-6">
              <div className="flex items-center gap-2 text-slate-500">
                <Clock3 className="h-4 w-4" />
                <span className="text-sm font-semibold uppercase tracking-[0.18em]">Review queue</span>
              </div>
              <div className="flex flex-col gap-2">
                <h2 className="text-lg font-semibold text-slate-950">Prioritized reviews for action</h2>
                <p className="text-sm text-slate-600">
                  Structured around current status, stage, and due date so managers can move the cycle forward without table-heavy scanning.
                </p>
              </div>
            </div>

            <div className="hidden border-b border-slate-200 px-6 py-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 md:grid md:grid-cols-[minmax(0,2.6fr)_minmax(0,1.2fr)_minmax(0,1.2fr)_auto] md:gap-4">
              <span>Employee</span>
              <span>Status</span>
              <span>Score / stage</span>
              <span className="text-right">Action</span>
            </div>

            <div className="divide-y divide-slate-200">
              {reviewQueue.map((review) => (
                <div
                  key={review.id}
                  className="grid gap-4 px-6 py-4 md:grid-cols-[minmax(0,2.6fr)_minmax(0,1.2fr)_minmax(0,1.2fr)_auto] md:items-center"
                >
                  <div className="flex min-w-0 flex-col gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-semibold text-slate-950">{review.employee}</p>
                      <span className="text-xs font-medium text-slate-500">{review.department}</span>
                    </div>
                    <div className="flex flex-col gap-1 text-sm text-slate-600">
                      <p>{review.role}</p>
                      <p className="truncate">{review.note}</p>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <span className={badgeClassName(review.status)}>{review.status}</span>
                    <p className="text-sm text-slate-500">Due {review.dueDate}</p>
                  </div>

                  <div className="flex flex-col gap-2 text-sm">
                    <p className="font-semibold text-slate-950">{review.score}</p>
                    <p className="text-slate-500">{review.stage}</p>
                  </div>

                  <div className="flex justify-start md:justify-end">
                    <Button variant="ghost" asChild className="h-9 px-3 text-slate-700">
                      <Link href={`/performance/${review.id}`}>Open review</Link>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <aside className="col-span-12 flex flex-col gap-6 xl:col-span-4">
          <div className="flex flex-col gap-4 rounded-[var(--radius-surface)] border border-slate-200 bg-slate-50/60 p-4">
            <div className="flex items-center gap-2 text-slate-500">
              <TrendingUp className="h-4 w-4" />
              <span className="text-sm font-semibold uppercase tracking-[0.18em]">Top performers</span>
            </div>
            <div className="flex flex-col gap-3">
              {topPerformers.map((item) => (
                <InsightItem key={item.name} name={item.name} meta={item.meta} note={item.note} />
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-4 rounded-[var(--radius-surface)] border border-slate-200 bg-slate-50/60 p-4">
            <div className="flex items-center gap-2 text-slate-500">
              <TrendingDown className="h-4 w-4" />
              <span className="text-sm font-semibold uppercase tracking-[0.18em]">Low performers</span>
            </div>
            <div className="flex flex-col gap-3">
              {lowPerformers.map((item) => (
                <InsightItem key={item.name} name={item.name} meta={item.meta} note={item.note} />
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-4 rounded-[var(--radius-surface)] border border-slate-200 bg-slate-50/60 p-4">
            <div className="flex items-center gap-2 text-slate-500">
              <Sparkles className="h-4 w-4" />
              <span className="text-sm font-semibold uppercase tracking-[0.18em]">Quick insights</span>
            </div>
            <div className="flex flex-col gap-3">
              {quickInsights.map((item) => (
                <div key={item.label} className="flex flex-col gap-2 border-b border-slate-200 pb-3 last:border-b-0 last:pb-0">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{item.label}</p>
                  <p className="text-sm font-semibold text-slate-950">{item.value}</p>
                  <p className="text-sm text-slate-600">{item.note}</p>
                </div>
              ))}
            </div>
          </div>
        </aside>
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
    <div className="flex flex-col gap-2 border-b border-slate-200 pb-3 last:border-b-0 last:pb-0">
      <p className="text-sm font-semibold text-slate-950">{name}</p>
      <p className="text-sm text-slate-500">{meta}</p>
      <p className="text-sm text-slate-600">{note}</p>
    </div>
  )
}

function badgeClassName(status: string) {
  switch (status) {
    case 'Completed':
      return 'inline-flex w-fit rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700'
    case 'In progress':
      return 'inline-flex w-fit rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700'
    default:
      return 'inline-flex w-fit rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700'
  }
}
