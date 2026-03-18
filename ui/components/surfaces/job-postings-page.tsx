'use client'

import Link from 'next/link'
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, BriefcaseBusiness, CircleGauge, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { EmptyState, ErrorState, StatSkeletonGrid, SurfaceSkeleton } from '@/components/ui/feedback'
import { PageHero, PageStack, StatCard } from '@/components/ui/page'
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
    <PageStack>
      <PageHero
        eyebrow="Job postings"
        title="Open requisitions without recruiter clutter"
        description="Job posting health is separated from the candidate board so teams can review requisition demand, opening count, and readiness before entering the pipeline workflow."
        actions={
          <Button asChild>
            <Link href="/candidate-pipeline">
              Open candidate pipeline
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        }
      />

      {query.isLoading ? (
        <>
          <StatSkeletonGrid count={3} />
          <SurfaceSkeleton lines={3} />
        </>
      ) : query.isError ? (
        <ErrorState
          title="Unable to load job postings"
          message={query.error.message}
          onRetry={() => query.refetch()}
        />
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <StatCard title="Open postings" value={String(metrics.openPostings)} hint="Ready for sourcing" icon={BriefcaseBusiness} />
            <StatCard title="Total openings" value={String(metrics.totalOpenings)} hint="Across all active requisitions" icon={Users} />
            <StatCard title="On-hold roles" value={String(metrics.onHold)} hint="Requires staffing decision" icon={CircleGauge} />
          </section>

          <section className="grid gap-4 xl:grid-cols-3">
            {jobs.length === 0 ? (
              <div className="xl:col-span-3">
                <EmptyState
                  icon={BriefcaseBusiness}
                  title="No job postings yet"
                  message="There are no active requisitions yet. Create a posting from the dashboard to start sourcing candidates."
                  action={
                    <Button asChild>
                      <Link href="/candidate-pipeline">
                        Review pipeline
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    </Button>
                  }
                />
              </div>
            ) : (
              jobs.map((job) => (
                <article
                  key={job.job_posting_id}
                  className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition-transform duration-150 hover:-translate-y-0.5"
                >
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
        </>
      )}
    </PageStack>
  )
}
