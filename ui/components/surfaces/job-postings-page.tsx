'use client'

import type { ComponentType } from 'react'
import Link from 'next/link'
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, BriefcaseBusiness, CircleGauge, LoaderCircle, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { apiRequest } from '@/lib/api/client'

type JobRow = {
  job_posting_id: string
  title: string
  department_id: string
  employment_type: string
  status: string
  openings_count: number
  posting_date: string
}

export function JobPostingsPage() {
  const query = useQuery({
    queryKey: ['job-postings'],
    queryFn: () => apiRequest<{ data: JobRow[] }>('/api/v1/hiring/job-postings?limit=20'),
  })

  const jobs = query.data?.data ?? []
  const metrics = useMemo(
    () => ({
      openPostings: jobs.filter((job) => job.status === 'Open').length,
      totalOpenings: jobs.reduce((sum, job) => sum + job.openings_count, 0),
      onHold: jobs.filter((job) => job.status === 'OnHold').length,
    }),
    [jobs],
  )

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Job postings</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Open requisitions without recruiter clutter.</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Job posting health is separated from the candidate board so teams can review requisition demand, opening count, and readiness before entering the pipeline workflow.
            </p>
          </div>
          <Button asChild>
            <Link href="/candidate-pipeline">
              Open candidate pipeline
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <SignalCard title="Open postings" value={String(metrics.openPostings)} hint="Ready for sourcing" icon={BriefcaseBusiness} />
        <SignalCard title="Total openings" value={String(metrics.totalOpenings)} hint="Across all active requisitions" icon={Users} />
        <SignalCard title="On-hold roles" value={String(metrics.onHold)} hint="Requires staffing decision" icon={CircleGauge} />
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        {query.isLoading ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-5 text-sm text-slate-500 shadow-sm inline-flex items-center gap-2">
            <LoaderCircle className="h-4 w-4 animate-spin" /> Loading job postings…
          </div>
        ) : query.isError ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-5 text-sm text-rose-600 shadow-sm">{query.error.message}</div>
        ) : (
          jobs.map((job) => (
            <article key={job.job_posting_id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${job.status === 'Open' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                  {job.status}
                </span>
                <span className="text-xs font-medium text-slate-500">{job.job_posting_id}</span>
              </div>
              <h3 className="mt-4 text-xl font-semibold tracking-tight text-slate-950">{job.title}</h3>
              <dl className="mt-4 grid gap-3 text-sm text-slate-600">
                <div className="flex items-center justify-between gap-4"><dt>Department</dt><dd>{job.department_id}</dd></div>
                <div className="flex items-center justify-between gap-4"><dt>Employment type</dt><dd>{job.employment_type}</dd></div>
                <div className="flex items-center justify-between gap-4"><dt>Openings</dt><dd>{job.openings_count}</dd></div>
                <div className="flex items-center justify-between gap-4"><dt>Posting date</dt><dd>{job.posting_date}</dd></div>
              </dl>
            </article>
          ))
        )}
      </section>
    </div>
  )
}

function SignalCard({ title, value, hint, icon: Icon }: { title: string; value: string; hint: string; icon: ComponentType<{ className?: string }> }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="w-fit rounded-2xl bg-slate-100 p-2 text-slate-700">
        <Icon className="h-4 w-4" />
      </div>
      <p className="mt-4 text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-950">{value}</p>
      <p className="mt-1 text-sm text-slate-600">{hint}</p>
    </div>
  )
}
