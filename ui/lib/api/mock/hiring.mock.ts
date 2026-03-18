import { clone, getMockDb, nowIso, randomId, simulateLatency } from './shared'

export async function listJobPostingsMock(params: { status?: string; limit?: number } = {}) {
  await simulateLatency()

  const rows = getMockDb().jobs
    .filter((job) => (!params.status || job.status === params.status))
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))

  return { data: clone(rows.slice(0, params.limit ?? rows.length)) }
}

export async function createJobPostingMock(payload: {
  title: string
  department_id: string
  role_id?: string
  employment_type: string
  description: string
  openings_count: number
  posting_date: string
  closing_date?: string
  status: string
  location?: string
}, options?: { failRate?: number }) {
  await simulateLatency({ failRate: options?.failRate ?? 0.08 })

  const job = {
    job_posting_id: randomId('job'),
    title: payload.title,
    department_id: payload.department_id,
    department_name: payload.department_id,
    role_id: payload.role_id,
    role_title: payload.role_id,
    employment_type: payload.employment_type as 'FullTime' | 'PartTime' | 'Contract' | 'Intern',
    description: payload.description,
    openings_count: payload.openings_count,
    posting_date: payload.posting_date,
    closing_date: payload.closing_date ?? null,
    status: payload.status as 'Draft' | 'Open' | 'OnHold' | 'Closed' | 'Filled',
    location: payload.location,
    updated_at: nowIso(),
  }

  getMockDb().jobs.unshift(job)
  return { data: clone(job) }
}

export async function listCandidatesMock() {
  await simulateLatency()

  const db = getMockDb()
  const interviewsByCandidate = db.interviews.reduce<Record<string, number>>((accumulator, interview) => {
    accumulator[interview.candidate_id] = (accumulator[interview.candidate_id] ?? 0) + 1
    return accumulator
  }, {})

  const rows = db.candidates
    .map((candidate) => ({
      ...candidate,
      interview_count: interviewsByCandidate[candidate.candidate_id] ?? candidate.interview_count,
    }))
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))

  return { data: clone(rows) }
}

export async function listInterviewsMock() {
  await simulateLatency()
  return { data: clone(getMockDb().interviews.sort((left, right) => left.scheduled_at.localeCompare(right.scheduled_at))) }
}

export async function updateCandidateStageMock(candidateId: string, pipelineStage: 'Applied' | 'Screening' | 'Interviewing' | 'Offered' | 'Hired', options?: { failRate?: number }) {
  await simulateLatency({ failRate: options?.failRate ?? 0.05 })

  const candidate = getMockDb().candidates.find((entry) => entry.candidate_id === candidateId)
  if (!candidate) {
    throw new Error('Candidate not found')
  }

  candidate.pipeline_stage = pipelineStage
  candidate.stage_updated_at = nowIso()
  candidate.updated_at = candidate.stage_updated_at

  return { data: clone(candidate) }
}

export async function scheduleInterviewMock(candidateId: string, payload: { interviewType: 'PhoneScreen' | 'Technical' | 'Behavioral' | 'Panel' | 'Final'; scheduledAt: string; location: string }, options?: { failRate?: number }) {
  await simulateLatency({ failRate: options?.failRate ?? 0.06 })

  const db = getMockDb()
  const candidate = db.candidates.find((entry) => entry.candidate_id === candidateId)
  if (!candidate) {
    throw new Error('Candidate not found')
  }

  const interview = {
    interview_id: randomId('int'),
    candidate_id: candidateId,
    interview_type: payload.interviewType,
    scheduled_at: new Date(payload.scheduledAt).toISOString(),
    location: payload.location.trim(),
  }

  db.interviews.push(interview)
  candidate.next_interview_at = interview.scheduled_at
  candidate.interview_count += 1
  candidate.stage_updated_at = nowIso()
  candidate.updated_at = candidate.stage_updated_at

  return { data: clone(interview) }
}
