# Hiring Service

Canonical implementation notes for `hiring-service`, aligned to the domain, workflow, API, security, and data architecture anchors.

## Scope
- Owns `JobPosting`, `Candidate`, and `Interview` lifecycle.
- Supports candidate progression: `Applied -> Screening -> Interviewing -> Offered -> Hired`.
- Emits cross-service events, including `CandidateHired` for employee onboarding.

## HTTP surface (`/api/v1`)
- `POST /api/v1/hiring/job-postings`
- `PATCH /api/v1/hiring/job-postings/{job_posting_id}`
- `GET /api/v1/hiring/job-postings/{job_posting_id}`
- `GET /api/v1/hiring/job-postings?status=&department_id=&limit=&cursor=`
- `POST /api/v1/hiring/candidates`
- `POST /api/v1/hiring/candidates/import/linkedin` — import candidates into a posting from LinkedIn payloads.
- `PATCH /api/v1/hiring/candidates/{candidate_id}`
- `GET /api/v1/hiring/candidates/{candidate_id}`
- `GET /api/v1/hiring/candidates?job_posting_id=&status=&limit=&cursor=`
- `GET /api/v1/hiring/candidate-pipeline?pipeline_stage=&department_id=&job_posting_id=`
- `POST /api/v1/hiring/interviews`
- `POST /api/v1/hiring/interviews/google-calendar` — schedule interview + sync to Google Calendar.
- `PATCH /api/v1/hiring/interviews/{interview_id}`
- `GET /api/v1/hiring/interviews/{interview_id}`
- `GET /api/v1/hiring/interviews?candidate_id=&status=&limit=&cursor=`
- `POST /api/v1/hiring/candidates/{candidate_id}/mark-hired`

## Authorization capabilities
- `CAP-HIR-001`: manage job postings.
- `CAP-HIR-002`: manage candidate pipeline + interviews.

## Domain rules implemented in code
- Job postings validate `employment_type`, date boundaries, openings count, and status.
- Candidates enforce existing job posting linkage, unique `(job_posting_id, email)`, initial `Applied` stage, stage transition history, and query support by posting/stage.
- Interviews enforce candidate linkage, schedule boundaries, enum integrity, and query support by candidate, with optional Google Calendar sync metadata (`google_calendar_event_id`, `google_calendar_event_link`).
- Candidate detail payloads hydrate linked job posting, stage history, and interviews.
- Interview detail payloads hydrate linked candidate summary.
- LinkedIn import maps source identifiers/profile URLs and records provider-specific import events.
- Candidate hire finalization allowed only from `Offered` stage.

## Events
- `JobPostingOpened`
- `JobPostingClosed`
- `CandidateApplied`
- `CandidateStageChanged`
- `CandidateStageTransitionRecorded`
- `InterviewScheduled`
- `InterviewCompleted`
- `InterviewCalendarSynced`
- `CandidateImported`
- `LinkedInCandidatesImported`
- `CandidateHired`

## Notes
The current implementation is an in-memory domain service (`services/hiring_service/service.py`) intended as a deterministic reference implementation and can be wrapped by any web transport layer.
