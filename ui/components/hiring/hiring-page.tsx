'use client'

import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BriefcaseBusiness, Plus, Users } from 'lucide-react'

import { HiringPipelineBoard } from '@/components/hiring/hiring-pipeline-board'
import { JobPostingsPage } from '@/components/surfaces/job-postings-page'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PageSection, PageSectionHeader, PageStack } from '@/components/ui/page'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
    <PageStack>
      <PageSection>
        <PageSectionHeader
          eyebrow="Hiring workspace"
          title="Pipeline and requisition control"
          description="Move candidates through a single hiring flow with clear stage progression and supporting context kept beside the main pipeline."
          actions={
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
          <Tabs key={tab} defaultValue={tab} className="space-y-6">
            <TabsList className="max-w-md">
              <TabsTrigger value="pipeline" onClick={() => setTab('pipeline')}>
                <Users className="h-4 w-4" />
                Candidate pipeline
              </TabsTrigger>
              <TabsTrigger value="postings" onClick={() => setTab('postings')}>
                <BriefcaseBusiness className="h-4 w-4" />
                Job postings
              </TabsTrigger>
            </TabsList>
          </Tabs>

          {tab === 'pipeline' ? <HiringPipelineBoard /> : <JobPostingsPage />}
        </div>
      </PageSection>
    </PageStack>
  )
}
