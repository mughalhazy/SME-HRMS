'use client'

import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  CircleDotDashed,
  GripVertical,
  LoaderCircle,
  MoveRight,
  Sparkles,
  Users,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input, Select } from '@/components/ui/input'
import { EmptyState, ErrorState, SurfaceSkeleton } from '@/components/ui/feedback'
import { PageStack } from '@/components/ui/page'
import { apiRequest } from '@/lib/api/client'
import { cn } from '@/lib/utils'

type CandidateStatus = 'Applied' | 'Screening' | 'Interviewing' | 'Offered' | 'Hired'
type BoardStage = 'Applied' | 'Interview' | 'Offer' | 'Hired'
type InterviewType = 'PhoneScreen' | 'Technical' | 'Behavioral' | 'Panel' | 'Final'

type CandidateRecord = {
  id: string
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
  location: string
}

type DraftInterview = {
  interviewType: InterviewType
  scheduledAt: string
  location: string
}

type CandidateApiRow = {
  candidate_id: string
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
  location: string
}

type StageDefinition = {
  id: BoardStage
  title: string
  description: string
  panelClassName: string
  badgeClassName: string
}

const STAGES: StageDefinition[] = [
  {
    id: 'Applied',
    title: 'Applied',
    description: 'New applicants and recruiter screening stay here before interviews.',
    panelClassName: 'border-sky-200 bg-sky-50',
    badgeClassName: 'bg-sky-100 text-sky-700 border-sky-200',
  },
  {
    id: 'Interview',
    title: 'Interview',
    description: 'Active interview loop with scheduling, panels, and next-step coordination.',
    panelClassName: 'border-violet-200 bg-violet-50',
    badgeClassName: 'bg-violet-100 text-violet-700 border-violet-200',
  },
  {
    id: 'Offer',
    title: 'Offer',
    description: 'Finalists with extended offers awaiting closeout and acceptance.',
    panelClassName: 'border-amber-200 bg-amber-50',
    badgeClassName: 'bg-amber-100 text-amber-700 border-amber-200',
  },
  {
    id: 'Hired',
    title: 'Hired',
    description: 'Accepted candidates ready for employee onboarding handoff.',
    panelClassName: 'border-emerald-200 bg-emerald-50',
    badgeClassName: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  },
]

const EMPTY_INTERVIEW_DRAFT: DraftInterview = {
  interviewType: 'Technical',
  scheduledAt: '',
  location: '',
}

function mapCandidate(row: CandidateApiRow): CandidateRecord {
  return {
    id: row.candidate_id,
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
    location: row.location,
  }
}

function statusToStage(status: CandidateStatus): BoardStage {
  if (status === 'Interviewing') return 'Interview'
  if (status === 'Offered') return 'Offer'
  if (status === 'Hired') return 'Hired'
  return 'Applied'
}

function canMoveStage(from: BoardStage, to: BoardStage) {
  const stageOrder: BoardStage[] = ['Applied', 'Interview', 'Offer', 'Hired']
  const delta = stageOrder.indexOf(to) - stageOrder.indexOf(from)
  return Math.abs(delta) === 1
}

function nextStatusForDrop(currentStatus: CandidateStatus, targetStage: BoardStage): CandidateStatus {
  if (targetStage === 'Interview') return 'Interviewing'
  if (targetStage === 'Offer') return 'Offered'
  if (targetStage === 'Hired') return 'Hired'
  return currentStatus === 'Applied' ? 'Applied' : 'Screening'
}

function formatDateLabel(value: string) {
  return new Intl.DateTimeFormat('en', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function getDropHint(fromStage: BoardStage | null, toStage: BoardStage) {
  if (!fromStage) return 'Drop candidate here'
  if (fromStage === toStage) return 'Already in this column'
  return canMoveStage(fromStage, toStage) ? `Move ${fromStage} → ${toStage}` : 'Workflow blocks this move'
}

export function HiringPipelineBoard() {
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
  const [draggedCandidateId, setDraggedCandidateId] = useState<string | null>(null)
  const [hoverStage, setHoverStage] = useState<BoardStage | null>(null)
  const [message, setMessage] = useState('Drag a candidate card to the next workflow column to keep the pipeline in sync.')
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
          location: draft.location,
        }),
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
        const rows = candidates
          .filter((candidate) => statusToStage(candidate.status) === stage.id)
          .sort((left, right) => new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime())

        accumulator[stage.id] = rows
        return accumulator
      },
      { Applied: [], Interview: [], Offer: [], Hired: [] },
    )
  }, [candidates])

  const metrics = useMemo(() => {
    const total = candidates.length
    const scheduledCount = interviews.length
    const hiredCount = candidatesByStage.Hired.length
    const activeOffers = candidatesByStage.Offer.length

    return {
      total,
      scheduledCount,
      hiredCount,
      activeOffers,
      conversion: total === 0 ? 0 : Math.round((hiredCount / total) * 100),
    }
  }, [candidates.length, candidatesByStage.Hired.length, candidatesByStage.Offer.length, interviews.length])

  function moveCandidate(candidateId: string, targetStage: BoardStage) {
    const candidate = candidates.find((entry) => entry.id === candidateId)
    if (!candidate) return

    const currentStage = statusToStage(candidate.status)
    if (!canMoveStage(currentStage, targetStage)) {
      setMessage(`Workflow alignment check: ${candidate.name} can only move one stage at a time.`)
      return
    }

    const updatedStatus = nextStatusForDrop(candidate.status, targetStage)

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

    void stageMutation.mutateAsync({ candidateId, pipelineStage: updatedStatus }).catch((error) => {
      setMessage(error instanceof Error ? error.message : `Unable to move ${candidate.name}.`)
      void queryClient.invalidateQueries({ queryKey: ['hiring-candidates'] })
    })

    if (targetStage === 'Interview' && (drafts[candidateId]?.scheduledAt?.length ?? 0) === 0) {
      setDrafts((current) => ({
        ...current,
        [candidateId]: {
          ...EMPTY_INTERVIEW_DRAFT,
          scheduledAt: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString().slice(0, 16),
          location: 'Google Meet',
        },
      }))
    }

    setMessage(`${candidate.name} moved to ${targetStage}. Underlying state is now ${updatedStatus}.`)
  }

  function handleScheduleInterview(candidateId: string) {
    const candidate = candidates.find((entry) => entry.id === candidateId)
    const draft = drafts[candidateId] ?? EMPTY_INTERVIEW_DRAFT

    if (!candidate) return

    if (statusToStage(candidate.status) !== 'Interview') {
      setMessage(`Schedule interviews from the Interview column only for ${candidate.name}.`)
      return
    }

    if (!draft.scheduledAt || !draft.location.trim()) {
      setMessage(`Interview scheduling needs both a date/time and a location for ${candidate.name}.`)
      return
    }

    const interview: InterviewRecord = {
      id: `local-${candidateId}`,
      candidateId,
      interviewType: draft.interviewType,
      scheduledAt: new Date(draft.scheduledAt).toISOString(),
      location: draft.location.trim(),
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

  const isLoading = candidatesQuery.isLoading || interviewsQuery.isLoading
  const isError = candidatesQuery.isError || interviewsQuery.isError
  const errorMessage = candidatesQuery.error?.message ?? interviewsQuery.error?.message

  return (
    <PageStack className="rounded-lg border border-slate-200 bg-white p-6 text-slate-950">
        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <div className="grid gap-6 px-6 py-6 lg:grid-cols-[1.7fr_1fr] lg:px-8">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 rounded-md border border-violet-200 bg-violet-50 px-3 py-1 text-sm font-medium text-violet-700">
                <Sparkles className="h-4 w-4" />
                CAP-HIR-002 · Candidate pipeline and interviews
              </div>
              <div className="space-y-3">
                <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-500">Hiring pipeline</p>
                <h1 className="max-w-3xl text-3xl font-semibold tracking-tight text-slate-950 md:text-5xl">
                  Kanban hiring board with workflow-safe drag and drop.
                </h1>
                <p className="max-w-3xl text-base leading-7 text-slate-600 md:text-lg">
                  The board follows the canonical candidate hiring workflow: Applied and Screening feed Interview,
                  Interview feeds Offer, and Offer hands off cleanly into Hired for onboarding.
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              <MetricCard icon={Users} label="Active candidates" value={metrics.total} detail="All cards stay derived from candidate state." />
              <MetricCard icon={CalendarDays} label="Scheduled interviews" value={metrics.scheduledCount} detail="Interview scheduling updates candidate freshness instantly." />
              <MetricCard icon={BriefcaseBusiness} label="Offers in flight" value={metrics.activeOffers} detail="Offer stage stays separate from interview activity." />
              <MetricCard icon={CheckCircle2} label="Hired conversion" value={`${metrics.conversion}%`} detail={`${metrics.hiredCount} candidates are ready for onboarding handoff.`} />
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-4 md:p-5">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 rounded-md bg-slate-900 p-2 text-white">
                <CircleDotDashed className="h-4 w-4" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-slate-900 md:text-base">State sync + workflow validation</h2>
                <p className="text-sm text-slate-600">
                  {isLoading ? 'Loading mock pipeline data…' : isError ? errorMessage : message}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-slate-500">
              <span className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5">Only adjacent stage moves are allowed</span>
              <span className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5">Interview scheduling is available inside Interview</span>
              <span className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5">UI columns are derived from canonical candidate status</span>
            </div>
          </div>
        </section>

        {isLoading ? (
          <SurfaceSkeleton lines={6} />
        ) : isError ? (
          <ErrorState title="Unable to load candidate pipeline" message={errorMessage ?? 'Unknown error'} onRetry={() => { void candidatesQuery.refetch(); void interviewsQuery.refetch() }} />
        ) : candidates.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No candidates in pipeline"
            message="Candidate cards will appear here once new applications are created. Refresh the board or create a new candidate from the hiring workflow."
            action={<Button variant="outline" onClick={() => { void candidatesQuery.refetch(); void interviewsQuery.refetch() }} disabled={candidatesQuery.isFetching || interviewsQuery.isFetching}>Refresh board</Button>}
          />
        ) : (
          <section className="grid gap-4 xl:grid-cols-4">
            {STAGES.map((stage) => {
              const draggedCandidate = candidates.find((candidate) => candidate.id === draggedCandidateId)
              const draggedStage = draggedCandidate ? statusToStage(draggedCandidate.status) : null
              const canDrop = draggedStage ? canMoveStage(draggedStage, stage.id) : false
              const isHovered = hoverStage === stage.id

              return (
                <div
                  key={stage.id}
                  className={cn(
                    'min-h-[540px] rounded-lg border bg-white p-4 transition-colors',
                    isHovered && canDrop && 'border-slate-950 bg-slate-50',
                    isHovered && !canDrop && draggedStage && 'border-rose-300 bg-rose-50',
                    !isHovered && 'border-slate-200',
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
                  <div className={cn('mb-4 rounded-lg border p-4', stage.panelClassName)}>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-950">{stage.title}</h3>
                        <p className="mt-1 text-sm leading-6 text-slate-600">{stage.description}</p>
                      </div>
                      <span className={cn('inline-flex min-w-11 items-center justify-center rounded-md border px-3 py-1 text-sm font-semibold', stage.badgeClassName)}>
                        {candidatesByStage[stage.id].length}
                      </span>
                    </div>
                    <p className="mt-3 text-xs font-medium uppercase tracking-[0.22em] text-slate-500">
                      {getDropHint(draggedStage, stage.id)}
                    </p>
                  </div>

                  <div className="space-y-3">
                    {candidatesByStage[stage.id].map((candidate) => {
                      const candidateStage = statusToStage(candidate.status)
                      const nextInterview = interviewsByCandidate[candidate.id]?.[0]
                      const interviewCount = interviewsByCandidate[candidate.id]?.length ?? 0
                      const draft = drafts[candidate.id] ?? EMPTY_INTERVIEW_DRAFT
                      const isDragging = draggedCandidateId === candidate.id

                      return (
                        <article
                          key={candidate.id}
                          draggable
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
                            'rounded-lg border border-slate-200 bg-white p-4 transition duration-200',
                            isDragging && 'rotate-[1deg] scale-[0.99] border-slate-900 opacity-70',
                          )}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="space-y-2">
                              <div className="flex items-center gap-2 text-slate-400">
                                <GripVertical className="h-4 w-4" />
                                <span className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                                  {candidate.status}
                                </span>
                              </div>
                              <div>
                                <h4 className="text-base font-semibold text-slate-950">{candidate.name}</h4>
                                <p className="text-sm text-slate-600">{candidate.role}</p>
                              </div>
                            </div>
                            <div className="rounded-md bg-slate-950 px-2.5 py-1 text-xs font-semibold text-white">
                              {candidate.score}
                            </div>
                          </div>

                          <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
                            <span className="rounded-md bg-slate-100 px-2.5 py-1">{candidate.source}</span>
                            <span className="rounded-md bg-slate-100 px-2.5 py-1">Applied {candidate.appliedDate}</span>
                            <span className="rounded-md bg-slate-100 px-2.5 py-1">{candidate.email}</span>
                          </div>

                          <p className="mt-3 text-sm leading-6 text-slate-600">{candidate.summary}</p>

                          <div className="mt-4 rounded-2xl bg-slate-50 p-3 text-sm text-slate-700">
                            <div className="flex items-center justify-between gap-3">
                              <span className="font-medium text-slate-900">Pipeline state</span>
                              <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                                Updated {formatDateLabel(candidate.updatedAt)}
                              </span>
                            </div>
                            <div className="mt-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                              <span>{candidateStage}</span>
                              {candidateStage !== 'Hired' && <MoveRight className="h-3.5 w-3.5" />}
                              <span>{candidate.status}</span>
                            </div>
                            <div className="mt-3 grid gap-2 text-xs text-slate-600">
                              <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2">
                                <span>Interview count</span>
                                <span className="font-semibold text-slate-900">{interviewCount}</span>
                              </div>
                              <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2">
                                <span>Next interview</span>
                                <span className="font-semibold text-slate-900">{nextInterview ? formatDateLabel(nextInterview.scheduledAt) : 'Not scheduled'}</span>
                              </div>
                            </div>
                          </div>

                          {candidateStage === 'Interview' ? (
                            <div className="mt-4 rounded-lg border border-violet-200 bg-violet-50 p-3">
                              <div className="mb-3">
                                <h5 className="text-sm font-semibold text-violet-950">Schedule interview</h5>
                                <p className="text-xs text-violet-800">Keep the interview plan on the card so the board and schedule stay synchronized.</p>
                              </div>
                              <div className="grid gap-2">
                                <label className="grid gap-1 text-xs font-medium text-slate-700">
                                  Interview type
                                  <Select
                                    value={draft.interviewType}
                                    onChange={(event) =>
                                      setDrafts((current) => ({
                                        ...current,
                                        [candidate.id]: {
                                          ...draft,
                                          interviewType: event.target.value as InterviewType,
                                        },
                                      }))
                                    }
                                    className="border-violet-200"
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
                                    value={draft.scheduledAt}
                                    onChange={(event) =>
                                      setDrafts((current) => ({
                                        ...current,
                                        [candidate.id]: {
                                          ...draft,
                                          scheduledAt: event.target.value,
                                        },
                                      }))
                                    }
                                    className="border-violet-200"
                                  />
                                </label>
                                <label className="grid gap-1 text-xs font-medium text-slate-700">
                                  Location or meeting link
                                  <Input
                                    type="text"
                                    placeholder="Google Meet / Zoom / HQ Room 4"
                                    value={draft.location}
                                    onChange={(event) =>
                                      setDrafts((current) => ({
                                        ...current,
                                        [candidate.id]: {
                                          ...draft,
                                          location: event.target.value,
                                        },
                                      }))
                                    }
                                    className="border-violet-200"
                                  />
                                </label>
                                <Button className="mt-1 w-full" onClick={() => handleScheduleInterview(candidate.id)} disabled={interviewMutation.isPending}>
                                  {interviewMutation.isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
                                  Schedule interview
                                </Button>
                              </div>
                            </div>
                          ) : null}
                        </article>
                      )
                    })}

                    {candidatesByStage[stage.id].length === 0 ? (
                      <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
                        No candidates in {stage.title}. Drop a card here to progress the workflow.
                      </div>
                    ) : null}
                  </div>
                </div>
              )
            })}
          </section>
        )}
    </PageStack>
  )
}

type MetricCardProps = {
  icon: typeof Users
  label: string
  value: number | string
  detail: string
}

function MetricCard({ icon: Icon, label, value, detail }: MetricCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">{label}</p>
          <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">{value}</p>
        </div>
        <div className="rounded-2xl bg-white p-3 text-slate-900 shadow-sm">
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{detail}</p>
    </div>
  )
}
