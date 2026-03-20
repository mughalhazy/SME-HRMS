'use client'

import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BriefcaseBusiness, Plus, Users } from 'lucide-react'

import { HiringPipelineBoard } from '@/components/hiring/hiring-pipeline-board'
import { JobPostingsPage } from '@/components/surfaces/job-postings-page'
import { Button } from '@/components/ui/button'
import { apiRequest } from '@/lib/api/client'

const EMPTY_COUNTS = {
  activeCandidates: 0,
  openRoles: 0,
}

type CandidateRow = {
  candidate_id: string
}

type JobRow = {
  job_posting_id: string
  status: string
}

export function HiringPage() {
  const [tab, setTab] = useState<'pipeline' | 'postings'>('pipeline')

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

    return {
      activeCandidates: candidates.length,
      openRoles: jobs.filter((job) => job.status === 'Open').length,
    }
  }, [candidatesQuery.data, jobsQuery.data])

  const context = candidatesQuery.isLoading || jobsQuery.isLoading ? EMPTY_COUNTS : counts

  return (
    <div className="space-y-6">
      <section className="space-y-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Pipeline</p>
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Hiring</h1>
              <p className="max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
                Move candidates through a single hiring flow with clear stage progression, lightweight review,
                and supporting details kept alongside the pipeline.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
              <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5">
                <BriefcaseBusiness className="h-4 w-4 text-slate-500" />
                <span>{context.openRoles} open roles</span>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5">
                <Users className="h-4 w-4 text-slate-500" />
                <span>{context.activeCandidates} active candidates</span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button type="button" onClick={() => setTab('pipeline')}>
              <Plus className="h-4 w-4" />
              Add candidate
            </Button>
            <Button type="button" variant="outline" onClick={() => setTab('postings')}>
              <BriefcaseBusiness className="h-4 w-4" />
              Create job
            </Button>
          </div>
        </div>

        <div className="space-y-6">
          <div className="grid h-auto w-full max-w-md grid-cols-2 gap-2 rounded-lg border border-slate-200 bg-slate-50 p-1">
            <button
              type="button"
              onClick={() => setTab('pipeline')}
              className={`inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition ${
                tab === 'pipeline' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:bg-white hover:text-slate-900'
              }`}
            >
              <Users className="h-4 w-4" />
              Candidate pipeline
            </button>
            <button
              type="button"
              onClick={() => setTab('postings')}
              className={`inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition ${
                tab === 'postings' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:bg-white hover:text-slate-900'
              }`}
            >
              <BriefcaseBusiness className="h-4 w-4" />
              Job postings
            </button>
          </div>

          {tab === 'pipeline' ? <HiringPipelineBoard /> : <JobPostingsPage />}
        </div>
      </section>
    </div>
  )
}
