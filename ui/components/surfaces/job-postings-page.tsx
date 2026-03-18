import type { ComponentType } from 'react'
import Link from 'next/link'
import { ArrowRight, BriefcaseBusiness, CircleGauge, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'

const jobs = [
  {
    jobPostingId: 'job-204',
    title: 'Frontend Engineer',
    departmentId: 'dep-eng',
    employmentType: 'FullTime',
    status: 'Open',
    openings: 2,
    postingDate: '2026-03-12',
  },
  {
    jobPostingId: 'job-205',
    title: 'People Operations Manager',
    departmentId: 'dep-hr',
    employmentType: 'FullTime',
    status: 'Open',
    openings: 1,
    postingDate: '2026-03-14',
  },
  {
    jobPostingId: 'job-198',
    title: 'Payroll Analyst',
    departmentId: 'dep-fin',
    employmentType: 'Contract',
    status: 'OnHold',
    openings: 1,
    postingDate: '2026-03-01',
  },
]

export function JobPostingsPage() {
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
        <SignalCard title="Open postings" value="2" hint="Ready for sourcing" icon={BriefcaseBusiness} />
        <SignalCard title="Total openings" value="4" hint="Across all active requisitions" icon={Users} />
        <SignalCard title="On-hold roles" value="1" hint="Requires staffing decision" icon={CircleGauge} />
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        {jobs.map((job) => (
          <article key={job.jobPostingId} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${job.status === 'Open' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                {job.status}
              </span>
              <span className="text-xs font-medium text-slate-500">{job.jobPostingId}</span>
            </div>
            <h3 className="mt-4 text-xl font-semibold tracking-tight text-slate-950">{job.title}</h3>
            <dl className="mt-4 grid gap-3 text-sm text-slate-600">
              <div className="flex items-center justify-between gap-4"><dt>Department</dt><dd>{job.departmentId}</dd></div>
              <div className="flex items-center justify-between gap-4"><dt>Employment type</dt><dd>{job.employmentType}</dd></div>
              <div className="flex items-center justify-between gap-4"><dt>Openings</dt><dd>{job.openings}</dd></div>
              <div className="flex items-center justify-between gap-4"><dt>Posting date</dt><dd>{job.postingDate}</dd></div>
            </dl>
          </article>
        ))}
      </section>
    </div>
  )
}

function SignalCard({ title, value, hint, icon: Icon }: { title: string; value: string; hint: string; icon: ComponentType<{ className?: string }> }) {
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
