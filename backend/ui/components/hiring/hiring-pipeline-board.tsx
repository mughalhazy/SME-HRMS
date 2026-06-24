'use client'

import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  CircleDotDashed,
  GripVertical,
  LoaderCircle,
  RefreshCcw,
  Users,
} from 'lucide-react'

import { Badge } from '@/components/base/badge'
import { Button } from '@/components/base/button'
import { EmptyState, ErrorState, SurfaceSkeleton } from '@/components/base/feedback'
import { Input, Select } from '@/components/base/input'
import { PageStack, pageIconChipClassName, pageSurfaceClassName } from '@/components/base/page'
import { apiRequest } from '@/lib/api/client'
import { cn } from '@/lib/utils'

type CandidateStatus = 'Applied' | 'Screening' | 'Interviewing' | 'Offered' | 'Hired'
type BoardStage = 'Applied' | 'Screening' | 'Interview' | 'Offer' | 'Hired'
type InterviewType = 'PhoneScreen' | 'Technical' | 'Behavioral' | 'Panel' | 'Final'
type InterviewStatus = 'Scheduled' | 'Completed' | 'Cancelled' | 'NoShow'

type CandidateRecord = {
  id: string
  jobPostingId: string
  name: string
  email: string
  role: string
  source: string
  status: CandidateStatus
  score: number
  appliedDate: string
  updatedAt: string
  summary: string
}

type InterviewRecord = {
  id: string
  candidateId: string
  interviewType: InterviewType
  scheduledAt: string
  scheduledEndAt: string
  location: string
  status: InterviewStatus
  updatedAt: string
}

type DraftInterview = {
  interviewType: InterviewType
  scheduledAt: string
  scheduledEndAt: string
  location: string
}

type CandidateApiRow = {
  candidate_id: string
  job_posting_id: string
  candidate_name: string
  candidate_email: string
  job_title: string
  source: string
  pipeline_stage: CandidateStatus
  score: number
  application_date: string
  updated_at: string
  summary: string
}

type InterviewApiRow = {
  interview_id: string
  candidate_id: string
  interview_type: InterviewType
  scheduled_at: string
  scheduled_end_at: string
  location: string
  status: InterviewStatus
  updated_at: string
}

type StageDefinition = {
  id: BoardStage
  title: string
  description: string
}

const STAGES: StageDefinition[] = [
  {
    id: 'Applied',
    title: 'Applied',
    description: 'New candidates ready for first review.',
  },
  {
    id: 'Screening',
    title: 'Screening',
    description: 'Initial recruiter review and qualification.',
  },
  {
    id: 'Interview',
    title: 'Interview',
    description: 'Active interview planning and feedback.',
  },
  {
    id: 'Offer',
    title: 'Offer',
    description: 'Final terms and closeout coordination.',
  },
  {
    id: 'Hired',
    title: 'Hired',
    description: 'Accepted candidates ready for handoff.',
  },
]

const EMPTY_INTERVIEW_DRAFT: DraftInterview = {
  interviewType: 'Technical',
  scheduledAt: '',
  scheduledEndAt: '',
  location: '',
}

function mapCandidate(row: CandidateApiRow): CandidateRecord {
  return {
    id: row.candidate_id,
    jobPostingId: row.job_posting_id,
    name: row.candidate_name,
    email: row.candidate_email,
    role: row.job_title,
    source: row.source,
    status: row.pipeline_stage,
    score: row.score,
    appliedDate: row.application_date,
    updatedAt: row.updated_at,
    summary: row.summary,
  }
}

function mapInterview(row: InterviewApiRow): InterviewRecord {
  return {
    id: row.interview_id,
    candidateId: row.candidate_id,
    interviewType: row.interview_type,
    scheduledAt: row.scheduled_at,
    scheduledEndAt: row.scheduled_end_at,
    location: row.location,
    status: row.status,
    updatedAt: row.updated_at,
  }
}

function statusToStage(status: CandidateStatus): BoardStage {
  if (status === 'Interviewing') return 'Interview'
  if (status === 'Offered') return 'Offer'
  return status
}

function stageToStatus(stage: BoardStage): CandidateStatus {
  if (stage === 'Interview') return 'Interviewing'
  if (stage === 'Offer') return 'Offered'
  return stage
}

function canMoveStage(from: BoardStage, to: BoardStage) {
  const stageOrder: BoardStage[] = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired']
  const delta = stageOrder.indexOf(to) - stageOrder.indexOf(from)
  return Math.abs(delta) === 1
}

function getPreviousStage(stage: BoardStage) {
  const stageOrder: BoardStage[] = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired']
  const index = stageOrder.indexOf(stage)
  return index > 0 ? stageOrder[index - 1] : null
}

function getNextStage(stage: BoardStage) {
  const stageOrder: BoardStage[] = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired']
  const index = stageOrder.indexOf(stage)
  return index < stageOrder.length - 1 ? stageOrder[index + 1] : null
}

function formatDateLabel(value: string) {
  return new Intl.DateTimeFormat('en', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatShortDateLabel(value: string) {
  return new Intl.DateTimeFormat('en', {
    month: 'short',
    day: 'numeric',
  }).format(new Date(value))
}

function defaultInterviewEnd(startAt: string) {
  if (!startAt) return ''
  return new Date(new Date(startAt).getTime() + 1000 * 60 * 60).toISOString().slice(0, 16)
}

function getDropHint(fromStage: BoardStage | null, toStage: BoardStage) {
  if (!fromStage) return 'Drop candidate here'
  if (fromStage === toStage) return 'Already in this stage'
  return canMoveStage(fromStage, toStage) ? `Move ${fromStage} → ${toStage}` : 'Only adjacent stage moves are allowed'
}

function getStatusBadgeClassName(status: CandidateStatus | InterviewStatus) {
  if (status === 'Hired' || status === 'Completed') return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  if (status === 'Offered' || status === 'Scheduled') return 'border-blue-200 bg-blue-50 text-blue-700'
  if (status === 'Cancelled' || status === 'NoShow') return 'border-rose-200 bg-rose-50 text-rose-700'
  return 'border-slate-200 bg-slate-50 text-slate-700'
}

type HiringPipelineBoardProps = {
  selectedJobId: string
  selectedJobTitle: string | null
}

export function HiringPipelineBoard({ selectedJobId, selectedJobTitle }: HiringPipelineBoardProps) {
  const queryClient = useQueryClient()
  const candidatesQuery = useQuery({
    queryKey: ['hiring-candidates'],
    queryFn: () => apiRequest<{ data: CandidateApiRow[] }>('/api/v1/hiring/candidates'),
  })
  const interviewsQuery = useQuery({
    queryKey: ['hiring-interviews'],
    queryFn: () => apiRequest<{ data: InterviewApiRow[] }>('/api/v1/hiring/interviews'),
  })

  const [candidates, setCandidates] = useState<CandidateRecord[]>([])
  const [interviews, setInterviews] = useState<InterviewRecord[]>([])
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null)
  const [draggedCandidateId, setDraggedCandidateId] = useState<string | null>(null)
  const [hoverStage, setHoverStage] = useState<BoardStage | null>(null)
  const [message, setMessage] = useState('Drag candidates forward one stage at a time or review details from the side panel.')
  const [drafts, setDrafts] = useState<Record<string, DraftInterview>>({})

  useEffect(() => {
    if (candidatesQuery.data?.data) {
      setCandidates(candidatesQuery.data.data.map(mapCandidate))
    }
  }, [candidatesQuery.data])

  useEffect(() => {
    if (interviewsQuery.data?.data) {
      setInterviews(interviewsQuery.data.data.map(mapInterview))
    }
  }, [interviewsQuery.data])

  const visibleCandidates = useMemo(() => {
    if (selectedJobId === 'all') return candidates
    return candidates.filter((candidate) => candidate.jobPostingId === selectedJobId)
  }, [candidates, selectedJobId])

  useEffect(() => {
    if (visibleCandidates.length === 0) {
      setSelectedCandidateId(null)
      return
    }

    if (!selectedCandidateId || !visibleCandidates.some((candidate) => candidate.id === selectedCandidateId)) {
      setSelectedCandidateId(visibleCandidates[0]?.id ?? null)
    }
  }, [visibleCandidates, selectedCandidateId])

  const stageMutation = useMutation({
    mutationFn: ({ candidateId, pipelineStage }: { candidateId: string; pipelineStage: CandidateStatus }) =>
      apiRequest(`/api/v1/hiring/candidates/${candidateId}/stage`, {
        method: 'PATCH',
        body: JSON.stringify({ pipeline_stage: pipelineStage }),
      }),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['hiring-candidates'] })
    },
  })

  const interviewMutation = useMutation({
    mutationFn: ({ candidateId, draft }: { candidateId: string; draft: DraftInterview }) =>
      apiRequest(`/api/v1/hiring/candidates/${candidateId}/interviews`, {
        method: 'POST',
        body: JSON.stringify({
          interview_type: draft.interviewType,
          scheduled_at: draft.scheduledAt,
          scheduled_end_at: draft.scheduledEndAt,
          location: draft.location,
        }),
      }),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['hiring-candidates'] })
      void queryClient.invalidateQueries({ queryKey: ['hiring-interviews'] })
    },
  })

  const interviewStatusMutation = useMutation({
    mutationFn: ({ interviewId, status }: { interviewId: string; status: InterviewStatus }) =>
      apiRequest(`/api/v1/hiring/interviews/${interviewId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ['hiring-candidates'] })
      void queryClient.invalidateQueries({ queryKey: ['hiring-interviews'] })
    },
  })

  const interviewsByCandidate = useMemo(() => {
    return interviews.reduce<Record<string, InterviewRecord[]>>((accumulator, interview) => {
      const list = accumulator[interview.candidateId] ?? []
      list.push(interview)
      accumulator[interview.candidateId] = list.sort(
        (left, right) => new Date(left.scheduledAt).getTime() - new Date(right.scheduledAt).getTime(),
      )
      return accumulator
    }, {})
  }, [interviews])

  const candidatesByStage = useMemo(() => {
    return STAGES.reduce<Record<BoardStage, CandidateRecord[]>>(
      (accumulator, stage) => {
        const rows = visibleCandidates
          .filter((candidate) => statusToStage(candidate.status) === stage.id)
          .sort((left, right) => new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime())

        accumulator[stage.id] = rows
        return accumulator
      },
      { Applied: [], Screening: [], Interview: [], Offer: [], Hired: [] },
    )
  }, [visibleCandidates])

  const selectedCandidate = selectedCandidateId ? visibleCandidates.find((candidate) => candidate.id === selectedCandidateId) ?? null : null
  const selectedStage = selectedCandidate ? statusToStage(selectedCandidate.status) : null
  const selectedCandidateInterviews = selectedCandidate ? interviewsByCandidate[selectedCandidate.id] ?? [] : []
  const selectedDraft = selectedCandidate ? drafts[selectedCandidate.id] ?? EMPTY_INTERVIEW_DRAFT : EMPTY_INTERVIEW_DRAFT
  const upcomingInterview = selectedCandidateInterviews.find((entry) => entry.status === 'Scheduled') ?? selectedCandidateInterviews[0] ?? null
  const previousStage = selectedStage ? getPreviousStage(selectedStage) : null
  const nextStage = selectedStage ? getNextStage(selectedStage) : null

  function moveCandidate(candidateId: string, targetStage: BoardStage) {
    const candidate = visibleCandidates.find((entry) => entry.id === candidateId) ?? candidates.find((entry) => entry.id === candidateId)
    if (!candidate) return

    const currentStage = statusToStage(candidate.status)
    if (!canMoveStage(currentStage, targetStage)) {
      setMessage(`Workflow alignment check: ${candidate.name} can only move one stage at a time.`)
      return
    }

    const updatedStatus = stageToStatus(targetStage)

    setCandidates((current) =>
      current.map((entry) =>
        entry.id === candidateId
          ? {
              ...entry,
              status: updatedStatus,
              updatedAt: new Date().toISOString(),
            }
          : entry,
      ),
    )

    if (targetStage === 'Interview' && (drafts[candidateId]?.scheduledAt?.length ?? 0) === 0) {
      const scheduledAt = new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString().slice(0, 16)
      setDrafts((current) => ({
        ...current,
        [candidateId]: {
          ...EMPTY_INTERVIEW_DRAFT,
          scheduledAt,
          scheduledEndAt: defaultInterviewEnd(scheduledAt),
          location: 'Google Meet',
        },
      }))
    }

    setMessage(`${candidate.name} moved to ${targetStage}.`)

    void stageMutation.mutateAsync({ candidateId, pipelineStage: updatedStatus }).catch((error) => {
      setMessage(error instanceof Error ? error.message : `Unable to move ${candidate.name}.`)
      void queryClient.invalidateQueries({ queryKey: ['hiring-candidates'] })
    })
  }

  function handleScheduleInterview(candidateId: string) {
    const candidate = visibleCandidates.find((entry) => entry.id === candidateId) ?? candidates.find((entry) => entry.id === candidateId)
    const draft = drafts[candidateId] ?? EMPTY_INTERVIEW_DRAFT

    if (!candidate) return

    if (statusToStage(candidate.status) !== 'Interview') {
      setMessage(`Schedule interviews from the Interview stage only for ${candidate.name}.`)
      return
    }

    if (!draft.scheduledAt || !draft.location.trim()) {
      setMessage(`Interview scheduling needs both a date/time and a location for ${candidate.name}.`)
      return
    }

    if (!draft.scheduledEndAt) {
      setMessage(`Add an interview end time for ${candidate.name} before scheduling.`)
      return
    }

    if (new Date(draft.scheduledEndAt).getTime() <= new Date(draft.scheduledAt).getTime()) {
      setMessage(`Interview end time must be after the start time for ${candidate.name}.`)
      return
    }

    const interview: InterviewRecord = {
      id: `local-${candidateId}`,
      candidateId,
      interviewType: draft.interviewType,
      scheduledAt: new Date(draft.scheduledAt).toISOString(),
      scheduledEndAt: new Date(draft.scheduledEndAt).toISOString(),
      location: draft.location.trim(),
      status: 'Scheduled',
      updatedAt: new Date().toISOString(),
    }

    setInterviews((current) => [...current, interview])
    setCandidates((current) =>
      current.map((entry) =>
        entry.id === candidateId
          ? {
              ...entry,
              updatedAt: new Date().toISOString(),
            }
          : entry,
      ),
    )
    setDrafts((current) => ({ ...current, [candidateId]: EMPTY_INTERVIEW_DRAFT }))
    setMessage(`${draft.interviewType} interview scheduled for ${candidate.name} on ${formatDateLabel(interview.scheduledAt)}.`)

    void interviewMutation.mutateAsync({ candidateId, draft }).catch((error) => {
      setMessage(error instanceof Error ? error.message : `Unable to schedule an interview for ${candidate.name}.`)
      void queryClient.invalidateQueries({ queryKey: ['hiring-candidates'] })
      void queryClient.invalidateQueries({ queryKey: ['hiring-interviews'] })
    })
  }

  function handleInterviewStatusUpdate(interviewId: string, status: InterviewStatus) {
    const interview = interviews.find((entry) => entry.id === interviewId)
    if (!interview) return

    const candidate = visibleCandidates.find((entry) => entry.id === interview.candidateId) ?? candidates.find((entry) => entry.id === interview.candidateId)

    setInterviews((current) =>
      current.map((entry) =>
        entry.id === interviewId
          ? {
              ...entry,
              status,
              updatedAt: new Date().toISOString(),
            }
          : entry,
      ),
    )

    if (candidate) {
      setCandidates((current) =>
        current.map((entry) =>
          entry.id === candidate.id
            ? {
                ...entry,
                updatedAt: new Date().toISOString(),
              }
            : entry,
        ),
      )
      setMessage(`Interview status updated to ${status} for ${candidate.name}.`)
    }

    void interviewStatusMutation.mutateAsync({ interviewId, status }).catch((error) => {
      setMessage(error instanceof Error ? error.message : 'Unable to update interview status.')
      void queryClient.invalidateQueries({ queryKey: ['hiring-candidates'] })
      void queryClient.invalidateQueries({ queryKey: ['hiring-interviews'] })
    })
  }

  const isLoading = candidatesQuery.isLoading || interviewsQuery.isLoading
  const isError = candidatesQuery.isError || interviewsQuery.isError
  const errorMessage = candidatesQuery.error?.message ?? interviewsQuery.error?.message
  const totalVisibleCandidates = visibleCandidates.length

  return (
    <PageStack className="gap-6">
      <section className={cn(pageSurfaceClassName, 'space-y-4 p-4')}>
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Pipeline flow</p>
            <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              {STAGES.map((stage, index) => (
                <div key={stage.id} className="flex items-center gap-2">
                  <span>{stage.title}</span>
                  {index < STAGES.length - 1 ? <ChevronRight className="h-4 w-4 text-slate-300" /> : null}
                </div>
              ))}
            </div>
            <h2 className="text-lg font-semibold text-slate-950">{selectedJobTitle ? `${selectedJobTitle} pipeline` : 'Candidate pipeline'}</h2>
            <p className="text-sm leading-6 text-slate-600">{isLoading ? 'Loading pipeline…' : isError ? errorMessage : message}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2">{totalVisibleCandidates} candidates</span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2">Drag left or right</span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2">Stage-by-stage movement</span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                void candidatesQuery.refetch()
                void interviewsQuery.refetch()
              }}
              disabled={candidatesQuery.isFetching || interviewsQuery.isFetching}
            >
              <RefreshCcw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>
      </section>

      {isLoading ? (
        <SurfaceSkeleton lines={6} />
      ) : isError ? (
        <ErrorState
          title="Unable to load candidate pipeline"
          message={errorMessage ?? 'Unknown error'}
          onRetry={() => {
            void candidatesQuery.refetch()
            void interviewsQuery.refetch()
          }}
        />
      ) : visibleCandidates.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No candidates in pipeline"
          message={selectedJobTitle ? `No candidates are attached to ${selectedJobTitle} yet. Refresh the board to sync the latest hiring data.` : 'Candidate cards will appear here once applications are created. Refresh the board to sync the latest hiring data.'}
          action={
            <Button
              variant="outline"
              onClick={() => {
                void candidatesQuery.refetch()
                void interviewsQuery.refetch()
              }}
              disabled={candidatesQuery.isFetching || interviewsQuery.isFetching}
            >
              Refresh board
            </Button>
          }
        />
      ) : (
        <div className="grid gap-6 xl:grid-cols-12">
          <section className={cn(pageSurfaceClassName, 'min-w-0 overflow-x-auto p-4 xl:col-span-9')}>
            <div className="grid min-w-[1200px] grid-cols-5 gap-4">
              {STAGES.map((stage) => {
                const draggedCandidate = candidates.find((candidate) => candidate.id === draggedCandidateId)
                const draggedStage = draggedCandidate ? statusToStage(draggedCandidate.status) : null
                const canDrop = draggedStage ? canMoveStage(draggedStage, stage.id) : false
                const isHovered = hoverStage === stage.id

                return (
                  <section
                    key={stage.id}
                    className={cn(
                      'flex min-h-[680px] min-w-0 flex-col rounded-[var(--radius-surface)] border border-slate-200 bg-slate-50 p-4 transition-colors',
                      isHovered && canDrop && 'border-slate-300 bg-slate-100',
                      isHovered && !canDrop && draggedStage && 'border-rose-200 bg-rose-50',
                    )}
                    onDragOver={(event) => {
                      event.preventDefault()
                      setHoverStage(stage.id)
                    }}
                    onDragLeave={() => setHoverStage((current) => (current === stage.id ? null : current))}
                    onDrop={(event) => {
                      event.preventDefault()
                      const candidateId = event.dataTransfer.getData('text/plain')
                      setHoverStage(null)
                      setDraggedCandidateId(null)
                      if (candidateId) {
                        moveCandidate(candidateId, stage.id)
                      }
                    }}
                  >
                    <header className="flex min-h-[112px] flex-col justify-between gap-3 border-b border-slate-200 pb-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 space-y-1">
                          <h2 className="text-sm font-semibold text-slate-950">{stage.title}</h2>
                          <p className="text-xs leading-5 text-slate-600">{stage.description}</p>
                        </div>
                        <Badge variant="outline" className="min-w-10 justify-center border-slate-200 bg-white px-3 py-1 text-slate-700">
                          {candidatesByStage[stage.id].length}
                        </Badge>
                      </div>
                      <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">{getDropHint(draggedStage, stage.id)}</p>
                    </header>

                    <div className="flex flex-1 flex-col gap-3 pt-4">
                      {candidatesByStage[stage.id].map((candidate) => {
                        const candidateInterviews = interviewsByCandidate[candidate.id] ?? []
                        const nextInterview = candidateInterviews.find((entry) => entry.status === 'Scheduled') ?? candidateInterviews[0] ?? null
                        const isSelected = selectedCandidateId === candidate.id
                        const isDragging = draggedCandidateId === candidate.id

                        return (
                          <article
                            key={candidate.id}
                            draggable
                            onClick={() => setSelectedCandidateId(candidate.id)}
                            onDragStart={(event) => {
                              event.dataTransfer.setData('text/plain', candidate.id)
                              event.dataTransfer.effectAllowed = 'move'
                              setDraggedCandidateId(candidate.id)
                            }}
                            onDragEnd={() => {
                              setDraggedCandidateId(null)
                              setHoverStage(null)
                            }}
                            className={cn(
                              'flex flex-col gap-3 rounded-[var(--radius-control)] border border-slate-200 bg-white p-3 transition-colors duration-150 hover:border-slate-300',
                              isSelected && 'border-slate-300 bg-slate-50',
                              isDragging && 'border-slate-300 opacity-70',
                            )}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0 space-y-3">
                                <div className="flex items-center gap-2 text-slate-400">
                                  <GripVertical className="h-4 w-4" />
                                  <Badge className={cn('rounded-full px-3 py-1', getStatusBadgeClassName(candidate.status))}>{candidate.status}</Badge>
                                </div>
                                <div className="space-y-1">
                                  <h3 className="truncate text-sm font-semibold text-slate-950">{candidate.name}</h3>
                                  <p className="truncate text-sm text-slate-700">{candidate.role}</p>
                                  <p className="truncate text-xs text-slate-500">{candidate.email}</p>
                                </div>
                              </div>
                              <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700">
                                {candidate.score}%
                              </div>
                            </div>

                            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600">
                              <span className="rounded-md bg-slate-50 px-2 py-1 text-slate-500">Applied {formatShortDateLabel(candidate.appliedDate)}</span>
                              <span className="rounded-md bg-slate-50 px-2 py-1 text-slate-500">{candidate.source}</span>
                              <span className="rounded-md bg-slate-50 px-2 py-1 text-slate-500">{nextInterview ? formatShortDateLabel(nextInterview.scheduledAt) : 'No interview'}</span>
                            </div>

                            <div className="flex items-center justify-between gap-3 border-t border-slate-200 pt-3 text-xs text-slate-500">
                              <span className="truncate">Updated {formatShortDateLabel(candidate.updatedAt)}</span>
                              <Button type="button" size="sm" variant="ghost" className="h-auto px-3 py-1 text-xs text-slate-600" onClick={() => setSelectedCandidateId(candidate.id)}>
                                Review
                              </Button>
                            </div>
                          </article>
                        )
                      })}

                      {candidatesByStage[stage.id].length === 0 ? (
                        <div className="flex min-h-[160px] flex-1 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white px-4 py-6 text-center text-sm text-slate-500">
                          No candidates in {stage.title}.
                        </div>
                      ) : null}
                    </div>
                  </section>
                )
              })}
            </div>
          </section>

          <aside className={cn(pageSurfaceClassName, 'space-y-4 p-4 xl:col-span-3')}>
            {selectedCandidate ? (
              <>
                <div className="space-y-3 border-b border-slate-200 pb-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Candidate details</p>
                      <h2 className="text-lg font-semibold text-slate-950">{selectedCandidate.name}</h2>
                      <p className="text-sm text-slate-700">{selectedCandidate.role}</p>
                    </div>
                    <Badge className={cn('rounded-full px-3 py-1', getStatusBadgeClassName(selectedCandidate.status))}>{selectedCandidate.status}</Badge>
                  </div>
                  <p className="text-sm leading-6 text-slate-600">{selectedCandidate.summary}</p>
                </div>

                <div className="space-y-3 border-b border-slate-200 pb-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-sm font-semibold text-slate-950">Progression</h3>
                    <span className="text-xs text-slate-500">Updated {formatDateLabel(selectedCandidate.updatedAt)}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                    {STAGES.map((stage, index) => (
                      <div key={stage.id} className="flex items-center gap-2">
                        <span className={cn(statusToStage(selectedCandidate.status) === stage.id && 'text-slate-900')}>{stage.title}</span>
                        {index < STAGES.length - 1 ? <ChevronRight className="h-4 w-4 text-slate-300" /> : null}
                      </div>
                    ))}
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Email</p>
                      <p className="mt-2 text-sm text-slate-700">{selectedCandidate.email}</p>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Source</p>
                      <p className="mt-2 text-sm text-slate-700">{selectedCandidate.source}</p>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Applied</p>
                      <p className="mt-2 text-sm text-slate-700">{formatShortDateLabel(selectedCandidate.appliedDate)}</p>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Score</p>
                      <p className="mt-2 text-sm text-slate-700">{selectedCandidate.score}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => previousStage && moveCandidate(selectedCandidate.id, previousStage)}
                      disabled={!previousStage || stageMutation.isPending}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Move back
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => nextStage && moveCandidate(selectedCandidate.id, nextStage)}
                      disabled={!nextStage || stageMutation.isPending}
                    >
                      Move next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="space-y-3 border-b border-slate-200 pb-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-sm font-semibold text-slate-950">Activity</h3>
                    <Badge variant="outline" className="border-slate-200 bg-slate-50 px-3 py-1 text-slate-700">
                      {selectedCandidateInterviews.length} items
                    </Badge>
                  </div>
                  {upcomingInterview ? (
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="space-y-1">
                          <p className="text-sm font-semibold text-slate-950">Next interview</p>
                          <p className="text-sm text-slate-600">{formatDateLabel(upcomingInterview.scheduledAt)} · {upcomingInterview.location}</p>
                        </div>
                        <Badge className={cn('rounded-full px-3 py-1', getStatusBadgeClassName(upcomingInterview.status))}>{upcomingInterview.status}</Badge>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">
                      No interview activity recorded yet.
                    </div>
                  )}

                  <div className="space-y-2">
                    {selectedCandidateInterviews.map((interview) => (
                      <div key={interview.id} className="space-y-3 rounded-lg border border-slate-200 bg-white p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <p className="text-sm font-semibold text-slate-950">{interview.interviewType}</p>
                            <p className="text-xs text-slate-600">{formatDateLabel(interview.scheduledAt)}</p>
                          </div>
                          <Badge className={cn('rounded-full px-3 py-1', getStatusBadgeClassName(interview.status))}>{interview.status}</Badge>
                        </div>
                        <div className="grid gap-2">
                          <p className="text-xs text-slate-600">{interview.location}</p>
                          <Select
                            value={interview.status}
                            onChange={(event) => handleInterviewStatusUpdate(interview.id, event.target.value as InterviewStatus)}
                            disabled={interviewStatusMutation.isPending}
                            className="border-slate-200"
                          >
                            <option value="Scheduled">Scheduled</option>
                            <option value="Completed">Completed</option>
                            <option value="Cancelled">Cancelled</option>
                            <option value="NoShow">No show</option>
                          </Select>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="space-y-1">
                      <h3 className="text-sm font-semibold text-slate-950">Notes and scheduling</h3>
                      <p className="text-xs text-slate-600">Keep secondary actions here so the board stays focused on progression.</p>
                    </div>
                    <div className={pageIconChipClassName}>
                      <CircleDotDashed className="h-4 w-4" />
                    </div>
                  </div>

                  {selectedStage === 'Interview' ? (
                    <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
                      <label className="grid gap-1 text-xs font-medium text-slate-700">
                        Interview type
                        <Select
                          value={selectedDraft.interviewType}
                          onChange={(event) =>
                            setDrafts((current) => ({
                              ...current,
                              [selectedCandidate.id]: {
                                ...selectedDraft,
                                interviewType: event.target.value as InterviewType,
                              },
                            }))
                          }
                          className="border-slate-200 bg-white"
                        >
                          <option value="PhoneScreen">Phone screen</option>
                          <option value="Technical">Technical</option>
                          <option value="Behavioral">Behavioral</option>
                          <option value="Panel">Panel</option>
                          <option value="Final">Final</option>
                        </Select>
                      </label>
                      <label className="grid gap-1 text-xs font-medium text-slate-700">
                        Date and time
                        <Input
                          type="datetime-local"
                          value={selectedDraft.scheduledAt}
                          onChange={(event) =>
                            setDrafts((current) => ({
                              ...current,
                              [selectedCandidate.id]: {
                                ...selectedDraft,
                                scheduledAt: event.target.value,
                                scheduledEndAt:
                                  selectedDraft.scheduledEndAt.length > 0
                                    ? selectedDraft.scheduledEndAt
                                    : defaultInterviewEnd(event.target.value),
                              },
                            }))
                          }
                          className="border-slate-200 bg-white"
                        />
                      </label>
                      <label className="grid gap-1 text-xs font-medium text-slate-700">
                        End time
                        <Input
                          type="datetime-local"
                          value={selectedDraft.scheduledEndAt}
                          onChange={(event) =>
                            setDrafts((current) => ({
                              ...current,
                              [selectedCandidate.id]: {
                                ...selectedDraft,
                                scheduledEndAt: event.target.value,
                              },
                            }))
                          }
                          className="border-slate-200 bg-white"
                        />
                      </label>
                      <label className="grid gap-1 text-xs font-medium text-slate-700">
                        Location or meeting link
                        <Input
                          type="text"
                          placeholder="Google Meet / Zoom / HQ Room 4"
                          value={selectedDraft.location}
                          onChange={(event) =>
                            setDrafts((current) => ({
                              ...current,
                              [selectedCandidate.id]: {
                                ...selectedDraft,
                                location: event.target.value,
                              },
                            }))
                          }
                          className="border-slate-200 bg-white"
                        />
                      </label>
                      <Button type="button" onClick={() => handleScheduleInterview(selectedCandidate.id)} disabled={interviewMutation.isPending}>
                        {interviewMutation.isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <CalendarDays className="h-4 w-4" />}
                        Schedule interview
                      </Button>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">
                      Move this candidate into Interview to schedule a session, or keep reviewing progress from the board.
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500">
                Select a candidate card to review details, activity, and next actions.
              </div>
            )}
          </aside>
        </div>
      )}
    </PageStack>
  )
}
