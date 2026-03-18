'use client'

import Link from 'next/link'
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, BriefcaseBusiness, CircleGauge, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { EmptyState, ErrorState, StatSkeletonGrid, SurfaceSkeleton } from '@/components/ui/feedback'
import { PageGrid, PageHero, PageStack, SectionHeading, StatCard } from '@/components/ui/page'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
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
          <PageGrid className="md:grid-cols-3">
            <StatCard title="Open postings" value={String(metrics.openPostings)} hint="Ready for sourcing" icon={BriefcaseBusiness} />
            <StatCard title="Total openings" value={String(metrics.totalOpenings)} hint="Across all active requisitions" icon={Users} />
            <StatCard title="On-hold roles" value={String(metrics.onHold)} hint="Requires staffing decision" icon={CircleGauge} />
          </PageGrid>

          <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <SectionHeading
              title="Open requisitions"
              description="Requisition status, department context, and opening volume stay in a single scan path."
            />
            {jobs.length === 0 ? (
              <div className="p-5">
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
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Employment</TableHead>
                    <TableHead>Openings</TableHead>
                    <TableHead>Posting date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.job_posting_id}>
                      <TableCell>
                        <div className="font-medium text-slate-950">{job.title}</div>
                        <div className="text-sm text-slate-500">{job.job_posting_id}</div>
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${job.status === 'Open' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'}`}>
                          {job.status}
                        </span>
                      </TableCell>
                      <TableCell className="text-slate-600">{job.department_id}</TableCell>
                      <TableCell className="text-slate-600">{job.employment_type}</TableCell>
                      <TableCell className="text-slate-600">{job.openings_count}</TableCell>
                      <TableCell className="text-slate-600">{job.posting_date}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </section>
        </>
      )}
    </PageStack>
  )
}
