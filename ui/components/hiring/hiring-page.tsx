'use client'

import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BriefcaseBusiness, ChevronRight, Users } from 'lucide-react'

import { HiringPipelineBoard } from '@/components/hiring/hiring-pipeline-board'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { EmptyState, ErrorState } from '@/components/ui/feedback'
import { Select } from '@/components/ui/input'
import { PageSection, PageSectionHeader, PageStack, pageSurfaceClassName } from '@/components/ui/page'
import { apiRequest } from '@/lib/api/client'
import { cn } from '@/lib/utils'

const EMPTY_COUNTS = {
  activeCandidates: 0,
  openRoles: 0,
}

type CandidateRow = {
  candidate_id: string
  job_posting_id: string
}

type JobRow = {
  job_posting_id: string
  title: string
  department_name?: string
  status: string
  openings_count: number
}

export function HiringPage() {
  const [selectedJobId, setSelectedJobId] = useState<string>('all')

  const candidatesQuery = useQuery({
    queryKey: ['hiring-candidates'],
    queryFn: () => apiRequest<{ data: CandidateRow[] }>('/api/v1/hiring/candidates'),
  })
  const jobsQuery = useQuery({
    queryKey: ['job-postings'],
    queryFn: () => apiRequest<{ data: JobRow[] }>('/api/v1/hiring/job-postings?limit=20'),
  })

  const counts = useMemo(() => {
    const candidates = candidatesQuery.data?.data ?? []
    const jobs = jobsQuery.data?.data ?? []
    const openJobs = jobs.filter((job) => job.status === 'Open')

    return {
      activeCandidates: candidates.length,
      openRoles: openJobs.length,
    }
  }, [candidatesQuery.data, jobsQuery.data])

  const openJobs = useMemo(() => (jobsQuery.data?.data ?? []).filter((job) => job.status === 'Open'), [jobsQuery.data])

  useEffect(() => {
    if (openJobs.length === 0) return

    if (selectedJobId !== 'all' && openJobs.some((job) => job.job_posting_id === selectedJobId)) {
      return
    }

    setSelectedJobId(openJobs[0]?.job_posting_id ?? 'all')
  }, [openJobs, selectedJobId])

  const filteredCandidates = useMemo(() => {
    const candidates = candidatesQuery.data?.data ?? []
    if (selectedJobId === 'all') return candidates
    return candidates.filter((candidate) => candidate.job_posting_id === selectedJobId)
  }, [candidatesQuery.data, selectedJobId])

  const selectedJob = openJobs.find((job) => job.job_posting_id === selectedJobId) ?? null
  const context = candidatesQuery.isLoading || jobsQuery.isLoading ? EMPTY_COUNTS : counts

  return (
    <PageStack>
      <PageSection>
        <PageSectionHeader
          eyebrow="Hiring workspace"
          title="Hiring"
          description="Run hiring as a left-to-right pipeline so candidate movement, stage pressure, and active requisitions stay in one scan path."
          actions={
            <Button type="button">
              <BriefcaseBusiness className="h-4 w-4" />
              Create Job
            </Button>
          }
          badge={
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
              <Badge variant="outline" className="gap-2 px-3 py-2 text-sm">
                <BriefcaseBusiness className="h-4 w-4 text-slate-500" />
                {context.openRoles} open roles
              </Badge>
              <Badge variant="outline" className="gap-2 px-3 py-2 text-sm">
                <Users className="h-4 w-4 text-slate-500" />
                {context.activeCandidates} active candidates
              </Badge>
            </div>
          }
        />

        <div className="space-y-6 px-4 py-4 sm:px-5 sm:py-5">
          {jobsQuery.isError ? (
            <ErrorState title="Unable to load active jobs" message={jobsQuery.error.message} onRetry={() => jobsQuery.refetch()} />
          ) : openJobs.length === 0 && !jobsQuery.isLoading ? (
            <EmptyState
              icon={BriefcaseBusiness}
              title="No active jobs available"
              message="Open requisitions will appear here so the hiring board can stay focused on one live pipeline at a time."
            />
          ) : (
            <section className={cn(pageSurfaceClassName, 'space-y-4 p-4')}>
              <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div className="space-y-1">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Active job</p>
                  <h2 className="text-sm font-semibold text-slate-950">Choose a requisition to focus the pipeline</h2>
                </div>
                <div className="flex w-full flex-col gap-3 xl:w-auto xl:min-w-[320px]">
                  <Select value={selectedJobId} onChange={(event) => setSelectedJobId(event.target.value)} disabled={jobsQuery.isLoading}>
                    {openJobs.map((job) => (
                      <option key={job.job_posting_id} value={job.job_posting_id}>
                        {job.title}
                      </option>
                    ))}
                  </Select>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
                <Badge variant="outline" className="px-3 py-2 text-sm">
                  {selectedJob?.department_name ?? 'Active requisition'}
                </Badge>
                <Badge variant="outline" className="gap-2 px-3 py-2 text-sm">
                  <Users className="h-4 w-4 text-slate-500" />
                  {filteredCandidates.length} candidates in flow
                </Badge>
                <Badge variant="outline" className="gap-2 px-3 py-2 text-sm">
                  <ChevronRight className="h-4 w-4 text-slate-500" />
                  Applied → Hired
                </Badge>
              </div>
            </section>
          )}

          {openJobs.length > 0 || jobsQuery.isLoading ? (
            <HiringPipelineBoard selectedJobId={selectedJobId} selectedJobTitle={selectedJob?.title ?? null} />
          ) : null}
        </div>
      </PageSection>
    </PageStack>
  )
}
