from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from threading import RLock
from time import perf_counter
from typing import Any
from uuid import uuid4

from event_contract import EventRegistry, emit_canonical_event

from resilience import CentralErrorLogger, CircuitBreaker, CircuitBreakerOpenError, DeadLetterQueue, Observability, run_with_retry


class HiringValidationError(ValueError):
    """Raised for domain validation errors."""


@dataclass(slots=True)
class JobPosting:
    job_posting_id: str
    title: str
    department_id: str
    role_id: str | None
    employment_type: str
    location: str | None
    description: str
    openings_count: int
    posting_date: date
    closing_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class Candidate:
    candidate_id: str
    job_posting_id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    resume_url: str | None
    source: str | None
    application_date: date
    status: str
    created_at: datetime
    updated_at: datetime
    source_candidate_id: str | None = None
    source_profile_url: str | None = None


@dataclass(slots=True)
class CandidateStageTransition:
    candidate_stage_transition_id: str
    candidate_id: str
    from_status: str | None
    to_status: str
    changed_at: datetime
    changed_by: str | None = None
    reason: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class Interview:
    interview_id: str
    candidate_id: str
    interview_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    location_or_link: str | None
    google_calendar_event_id: str | None = None
    google_calendar_event_link: str | None = None
    interviewer_employee_ids: list[str] = field(default_factory=list)
    feedback_summary: str | None = None
    recommendation: str | None = None
    status: str = "Scheduled"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class EmployeeProfile:
    employee_id: str
    candidate_id: str
    job_posting_id: str
    department_id: str
    role_id: str | None
    first_name: str
    last_name: str
    email: str
    phone: str | None
    employment_type: str
    hire_date: date
    status: str
    created_at: datetime
    updated_at: datetime


class HiringService:
    """In-memory domain service implementing the canonical hiring workflow."""

    JOB_POSTING_STATUSES = {"Draft", "Open", "OnHold", "Closed", "Filled"}
    CANDIDATE_STATUSES = {
        "Applied",
        "Screening",
        "Interviewing",
        "Offered",
        "Hired",
        "Rejected",
        "Withdrawn",
    }
    INTERVIEW_STATUSES = {"Scheduled", "Completed", "Cancelled", "NoShow"}
    EMPLOYMENT_TYPES = {"FullTime", "PartTime", "Contract", "Intern"}
    CANDIDATE_SOURCES = {"Referral", "JobBoard", "CareerSite", "Agency", "LinkedIn", "Other"}
    INTERVIEW_TYPES = {"PhoneScreen", "Technical", "Behavioral", "Panel", "Final"}
    RECOMMENDATIONS = {"StrongHire", "Hire", "NoHire", "Undecided"}

    CANDIDATE_STATUS_FLOW = {
        "Applied": {"Screening", "Rejected", "Withdrawn"},
        "Screening": {"Interviewing", "Rejected", "Withdrawn"},
        "Interviewing": {"Offered", "Rejected", "Withdrawn"},
        "Offered": {"Hired", "Rejected", "Withdrawn"},
        "Hired": set(),
        "Rejected": set(),
        "Withdrawn": set(),
    }

    def __init__(self) -> None:
        self.job_postings: dict[str, JobPosting] = {}
        self.candidates: dict[str, Candidate] = {}
        self.candidate_stage_transitions: dict[str, CandidateStageTransition] = {}
        self.interviews: dict[str, Interview] = {}
        self.employee_profiles: dict[str, EmployeeProfile] = {}
        self.hired_candidate_index: dict[str, str] = {}
        self.events: list[dict[str, Any]] = []
        self.tenant_id = "tenant-default"
        self.event_registry = EventRegistry()
        self.error_logger = CentralErrorLogger("hiring-service")
        self.dead_letters = DeadLetterQueue()
        self.observability = Observability("hiring-service")
        self.integration_breakers = {
            "google-calendar": CircuitBreaker(failure_threshold=2, recovery_timeout=1.0),
            "linkedin": CircuitBreaker(failure_threshold=2, recovery_timeout=1.0),
        }
        self._lock = RLock()

    def create_job_posting(self, payload: dict[str, Any]) -> dict[str, Any]:
        started = perf_counter()
        with self._lock:
            self._require(payload, ["title", "department_id", "employment_type", "description", "openings_count", "posting_date"])
            self._validate_value(payload["employment_type"], self.EMPLOYMENT_TYPES, "employment_type")
            if payload["openings_count"] < 1:
                raise HiringValidationError("openings_count must be >= 1")

            posting_date = self._coerce_date(payload["posting_date"], "posting_date")
            closing_date = self._coerce_optional_date(payload.get("closing_date"), "closing_date")
            if closing_date and closing_date < posting_date:
                raise HiringValidationError("closing_date must be on or after posting_date")

            status = payload.get("status", "Draft")
            self._validate_value(status, self.JOB_POSTING_STATUSES, "status")

            job_posting = JobPosting(
                job_posting_id=self._new_id(),
                title=payload["title"],
                department_id=payload["department_id"],
                role_id=payload.get("role_id"),
                employment_type=payload["employment_type"],
                location=payload.get("location"),
                description=payload["description"],
                openings_count=payload["openings_count"],
                posting_date=posting_date,
                closing_date=closing_date,
                status=status,
                created_at=self._now(),
                updated_at=self._now(),
            )
            self.job_postings[job_posting.job_posting_id] = job_posting
            if status == "Open":
                self._emit("JobPostingOpened", {"job_posting_id": job_posting.job_posting_id})
        self.observability.track("create_job_posting", trace_id=self.observability.trace_id(), started_at=started, success=True, context={"status": 201, "job_posting_id": job_posting.job_posting_id})
        return self._serialize(job_posting)

    def update_job_posting(self, job_posting_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        posting = self._require_job_posting(job_posting_id)
        previous_status = posting.status

        for key in ["title", "department_id", "role_id", "location", "description"]:
            if key in patch:
                setattr(posting, key, patch[key])

        if "employment_type" in patch:
            self._validate_value(patch["employment_type"], self.EMPLOYMENT_TYPES, "employment_type")
            posting.employment_type = patch["employment_type"]

        if "openings_count" in patch:
            if patch["openings_count"] < 1:
                raise HiringValidationError("openings_count must be >= 1")
            posting.openings_count = patch["openings_count"]

        posting_date = posting.posting_date
        if "posting_date" in patch:
            posting_date = self._coerce_date(patch["posting_date"], "posting_date")
            posting.posting_date = posting_date

        if "closing_date" in patch:
            posting.closing_date = self._coerce_optional_date(patch["closing_date"], "closing_date")

        if posting.closing_date and posting.closing_date < posting_date:
            raise HiringValidationError("closing_date must be on or after posting_date")

        if "status" in patch:
            self._validate_value(patch["status"], self.JOB_POSTING_STATUSES, "status")
            posting.status = patch["status"]

        posting.updated_at = self._now()

        if previous_status != posting.status:
            if posting.status == "Open":
                self._emit("JobPostingOpened", {"job_posting_id": posting.job_posting_id})
            if posting.status in {"Closed", "Filled"}:
                self._emit("JobPostingClosed", {"job_posting_id": posting.job_posting_id, "status": posting.status})

        return self._serialize(posting)

    def get_job_posting(self, job_posting_id: str) -> dict[str, Any]:
        posting = self._require_job_posting(job_posting_id)
        payload = self._serialize(posting)
        payload["candidate_count"] = self._candidate_count(job_posting_id)
        return payload

    def list_job_postings(
        self,
        *,
        status: str | None = None,
        department_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        if status is not None:
            self._validate_value(status, self.JOB_POSTING_STATUSES, "status")
        if limit is not None and limit < 1:
            raise HiringValidationError("limit must be >= 1")

        rows: list[JobPosting] = list(self.job_postings.values())
        if status:
            rows = [r for r in rows if r.status == status]
        if department_id:
            rows = [r for r in rows if r.department_id == department_id]
        rows.sort(key=lambda r: (r.posting_date, r.updated_at, r.job_posting_id), reverse=True)

        if cursor is not None:
            cursor_index = next((index for index, row in enumerate(rows) if row.job_posting_id == cursor), None)
            if cursor_index is None:
                raise HiringValidationError("cursor does not exist")
            rows = rows[cursor_index + 1 :]

        if limit is not None:
            rows = rows[:limit]

        return [self.get_job_posting(x.job_posting_id) for x in rows]

    def delete_job_posting(self, job_posting_id: str) -> dict[str, Any]:
        with self._lock:
            posting = self._require_job_posting(job_posting_id)
            if any(candidate.job_posting_id == job_posting_id for candidate in self.candidates.values()):
                raise HiringValidationError("job posting cannot be deleted while candidates exist")

            payload = self._serialize(posting)
            payload["candidate_count"] = 0
            del self.job_postings[job_posting_id]
            return payload

    def create_candidate(self, payload: dict[str, Any]) -> dict[str, Any]:
        started = perf_counter()
        with self._lock:
            self._require(payload, ["job_posting_id", "first_name", "last_name", "email", "application_date"])
            posting = self._require_job_posting(payload["job_posting_id"])
            if posting.status not in {"Open", "OnHold"}:
                raise HiringValidationError("candidates can only be created for Open/OnHold job postings")

            source = payload.get("source")
            if source is not None:
                self._validate_value(source, self.CANDIDATE_SOURCES, "source")

            initial_status = payload.get("status", "Applied")
            self._validate_value(initial_status, self.CANDIDATE_STATUSES, "status")
            if initial_status != "Applied":
                raise HiringValidationError("candidate status must start as Applied")

            for existing in self.candidates.values():
                if existing.job_posting_id == payload["job_posting_id"] and existing.email.lower() == payload["email"].lower():
                    raise HiringValidationError("candidate email must be unique within the job posting")

            candidate = Candidate(
                candidate_id=self._new_id(),
                job_posting_id=payload["job_posting_id"],
                first_name=payload["first_name"],
                last_name=payload["last_name"],
                email=payload["email"],
                phone=payload.get("phone"),
                resume_url=payload.get("resume_url"),
                source=source,
                source_candidate_id=payload.get("source_candidate_id"),
                source_profile_url=payload.get("source_profile_url"),
                application_date=self._coerce_date(payload["application_date"], "application_date"),
                status=initial_status,
                created_at=self._now(),
                updated_at=self._now(),
            )
            self.candidates[candidate.candidate_id] = candidate
            self._record_candidate_stage_transition(
                candidate_id=candidate.candidate_id,
                from_status=None,
                to_status=candidate.status,
                changed_by=payload.get("changed_by"),
                reason=payload.get("stage_reason"),
                notes=payload.get("stage_notes"),
            )
            self._emit("CandidateApplied", {"candidate_id": candidate.candidate_id, "job_posting_id": candidate.job_posting_id})
        self.observability.track("create_candidate", trace_id=self.observability.trace_id(), started_at=started, success=True, context={"status": 201, "candidate_id": candidate.candidate_id})
        return self.get_candidate(candidate.candidate_id)

    def list_candidates(
        self,
        *,
        job_posting_id: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        if job_posting_id is not None:
            self._require_job_posting(job_posting_id)
        if status is not None:
            self._validate_value(status, self.CANDIDATE_STATUSES, "status")
        if limit is not None and limit < 1:
            raise HiringValidationError("limit must be >= 1")

        rows = list(self.candidates.values())
        if job_posting_id:
            rows = [row for row in rows if row.job_posting_id == job_posting_id]
        if status:
            rows = [row for row in rows if row.status == status]
        rows.sort(key=lambda row: (row.application_date, row.updated_at, row.candidate_id), reverse=True)

        if cursor is not None:
            cursor_index = next((index for index, row in enumerate(rows) if row.candidate_id == cursor), None)
            if cursor_index is None:
                raise HiringValidationError("cursor does not exist")
            rows = rows[cursor_index + 1 :]

        if limit is not None:
            rows = rows[:limit]

        return [self.get_candidate(row.candidate_id) for row in rows]

    def health_snapshot(self) -> dict[str, Any]:
        return self.observability.health_status(
            checks={
                "job_postings": len(self.job_postings),
                "candidates": len(self.candidates),
                "candidate_stage_transitions": len(self.candidate_stage_transitions),
                "interviews": len(self.interviews),
            }
        )

    def update_candidate(self, candidate_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id)
        previous_status = candidate.status

        for key in [
            "first_name",
            "last_name",
            "email",
            "phone",
            "resume_url",
            "source",
            "source_candidate_id",
            "source_profile_url",
        ]:
            if key in patch:
                if key == "source" and patch[key] is not None:
                    self._validate_value(patch[key], self.CANDIDATE_SOURCES, "source")
                if key == "email":
                    for existing in self.candidates.values():
                        if existing.candidate_id != candidate_id and existing.job_posting_id == candidate.job_posting_id and existing.email.lower() == patch[key].lower():
                            raise HiringValidationError("candidate email must be unique within the job posting")
                setattr(candidate, key, patch[key])

        if "application_date" in patch:
            candidate.application_date = self._coerce_date(patch["application_date"], "application_date")

        if "job_posting_id" in patch and patch["job_posting_id"] != candidate.job_posting_id:
            new_job_posting = self._require_job_posting(patch["job_posting_id"])
            if new_job_posting.status not in {"Open", "OnHold"}:
                raise HiringValidationError("candidates can only be assigned to Open/OnHold job postings")
            for existing in self.candidates.values():
                if existing.candidate_id != candidate_id and existing.job_posting_id == patch["job_posting_id"] and existing.email.lower() == candidate.email.lower():
                    raise HiringValidationError("candidate email must be unique within the job posting")
            candidate.job_posting_id = patch["job_posting_id"]

        if "status" in patch:
            next_status = patch["status"]
            self._validate_value(next_status, self.CANDIDATE_STATUSES, "status")
            if next_status != candidate.status and next_status not in self.CANDIDATE_STATUS_FLOW[candidate.status]:
                raise HiringValidationError(
                    f"invalid candidate status transition: {candidate.status} -> {next_status}"
                )
            candidate.status = next_status

        candidate.updated_at = self._now()

        if previous_status != candidate.status:
            self._record_candidate_stage_transition(
                candidate_id=candidate.candidate_id,
                from_status=previous_status,
                to_status=candidate.status,
                changed_by=patch.get("changed_by"),
                reason=patch.get("stage_reason"),
                notes=patch.get("stage_notes"),
            )
            self._emit(
                "CandidateStageChanged",
                {
                    "candidate_id": candidate.candidate_id,
                    "from_status": previous_status,
                    "to_status": candidate.status,
                },
            )

        return self.get_candidate(candidate.candidate_id)

    def get_candidate(self, candidate_id: str) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id)
        payload = self._serialize(candidate)
        payload["job_posting"] = self.get_job_posting(candidate.job_posting_id)
        payload["stage_history"] = self.list_candidate_stage_history(candidate_id)
        payload["interviews"] = self.list_interviews(candidate_id=candidate_id)
        employee_id = self.hired_candidate_index.get(candidate_id)
        payload["employee_profile"] = self.get_employee_profile(employee_id) if employee_id else None
        return payload

    def create_interview(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require(payload, ["candidate_id", "interview_type", "scheduled_start", "scheduled_end"])
        candidate = self._require_candidate(payload["candidate_id"])
        if candidate.status not in {"Interviewing", "Offered"}:
            raise HiringValidationError("interviews can only be scheduled for Interviewing/Offered candidates")

        self._validate_value(payload["interview_type"], self.INTERVIEW_TYPES, "interview_type")
        scheduled_start = self._coerce_datetime(payload["scheduled_start"], "scheduled_start")
        scheduled_end = self._coerce_datetime(payload["scheduled_end"], "scheduled_end")
        if scheduled_end <= scheduled_start:
            raise HiringValidationError("scheduled_end must be after scheduled_start")

        interview = Interview(
            interview_id=self._new_id(),
            candidate_id=payload["candidate_id"],
            interview_type=payload["interview_type"],
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            location_or_link=payload.get("location_or_link"),
            interviewer_employee_ids=list(payload.get("interviewer_employee_ids", [])),
            feedback_summary=payload.get("feedback_summary"),
            recommendation=payload.get("recommendation"),
            status=payload.get("status", "Scheduled"),
            created_at=self._now(),
            updated_at=self._now(),
        )
        self._validate_value(interview.status, self.INTERVIEW_STATUSES, "status")
        if interview.recommendation is not None:
            self._validate_value(interview.recommendation, self.RECOMMENDATIONS, "recommendation")

        self.interviews[interview.interview_id] = interview
        self._emit("InterviewScheduled", {"interview_id": interview.interview_id, "candidate_id": interview.candidate_id})
        return self.get_interview(interview.interview_id)

    def get_interview(self, interview_id: str) -> dict[str, Any]:
        interview = self._require_interview(interview_id)
        payload = self._serialize(interview)
        payload["candidate"] = self.get_candidate_summary(interview.candidate_id)
        return payload

    def list_interviews(
        self,
        *,
        candidate_id: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        if candidate_id is not None:
            self._require_candidate(candidate_id)
        if status is not None:
            self._validate_value(status, self.INTERVIEW_STATUSES, "status")
        if limit is not None and limit < 1:
            raise HiringValidationError("limit must be >= 1")

        rows = list(self.interviews.values())
        if candidate_id:
            rows = [row for row in rows if row.candidate_id == candidate_id]
        if status:
            rows = [row for row in rows if row.status == status]
        rows.sort(key=lambda row: (row.scheduled_start, row.updated_at, row.interview_id), reverse=False)

        if cursor is not None:
            cursor_index = next((index for index, row in enumerate(rows) if row.interview_id == cursor), None)
            if cursor_index is None:
                raise HiringValidationError("cursor does not exist")
            rows = rows[cursor_index + 1 :]

        if limit is not None:
            rows = rows[:limit]

        return [self.get_interview(row.interview_id) for row in rows]

    def schedule_interview_with_google_calendar(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Schedule interview and simulate synchronization to Google Calendar."""
        interview = self.create_interview(payload)
        interview_model = self._require_interview(interview["interview_id"])

        def sync_calendar() -> str:
            if payload.get("simulate_google_failure"):
                raise TimeoutError("google calendar sync timed out")
            return self._new_id()

        try:
            calendar_event_id = self.integration_breakers["google-calendar"].call(
                lambda: run_with_retry(
                    sync_calendar,
                    attempts=3,
                    base_delay=0.05,
                    timeout_seconds=0.2,
                    retryable=lambda exc: isinstance(exc, TimeoutError),
                )
            )
            interview_model.google_calendar_event_id = calendar_event_id
            interview_model.google_calendar_event_link = f"https://calendar.google.com/calendar/event?eid={calendar_event_id}"
            if not interview_model.location_or_link:
                interview_model.location_or_link = f"https://meet.google.com/{calendar_event_id[:3]}-{calendar_event_id[3:6]}-{calendar_event_id[6:9]}"
            interview_model.updated_at = self._now()

            self._emit(
                "InterviewCalendarSynced",
                {
                    "interview_id": interview_model.interview_id,
                    "candidate_id": interview_model.candidate_id,
                    "provider": "GoogleCalendar",
                    "external_event_id": calendar_event_id,
                },
            )
        except CircuitBreakerOpenError as exc:
            self.error_logger.log("schedule_interview_with_google_calendar", exc, details={"candidate_id": interview_model.candidate_id})
            self.dead_letters.push("candidate_hiring", "InterviewCalendarSyncDeferred", {"interview_id": interview_model.interview_id, "candidate_id": interview_model.candidate_id}, str(exc))
            interview_model.location_or_link = interview_model.location_or_link or "manual-scheduling-required"
        except Exception as exc:  # noqa: BLE001
            self.error_logger.log("schedule_interview_with_google_calendar", exc, details={"candidate_id": interview_model.candidate_id})
            self.dead_letters.push("candidate_hiring", "InterviewCalendarSyncDeferred", {"interview_id": interview_model.interview_id, "candidate_id": interview_model.candidate_id}, str(exc))
            interview_model.location_or_link = interview_model.location_or_link or "manual-scheduling-required"
        return self.get_interview(interview_model.interview_id)

    def import_candidates_from_linkedin(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Import candidates from LinkedIn payloads for a target job posting."""
        self._require(payload, ["job_posting_id", "candidates"])
        self._require_job_posting(payload["job_posting_id"])
        rows = payload["candidates"]
        if not isinstance(rows, list) or not rows:
            raise HiringValidationError("candidates must be a non-empty list")

        imported: list[dict[str, Any]] = []
        skipped: list[dict[str, str]] = []
        for row in rows:
            source_candidate_id = row.get("source_candidate_id") or row.get("linkedin_member_id") or "unknown"
            email = row.get("email")
            if not email:
                skipped.append({"source_candidate_id": source_candidate_id, "reason": "email is required"})
                continue

            duplicate = any(
                c.job_posting_id == payload["job_posting_id"] and c.email.lower() == email.lower()
                for c in self.candidates.values()
            )
            if duplicate:
                skipped.append({"source_candidate_id": source_candidate_id, "reason": "duplicate email for job posting"})
                continue

            full_name = (row.get("full_name") or "").strip()
            first_name = row.get("first_name")
            last_name = row.get("last_name")
            if not first_name and full_name:
                name_parts = full_name.split(maxsplit=1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""

            candidate_payload = {
                "job_posting_id": payload["job_posting_id"],
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": row.get("phone"),
                "resume_url": row.get("resume_url"),
                "source": "LinkedIn",
                "source_candidate_id": source_candidate_id,
                "source_profile_url": row.get("source_profile_url") or row.get("linkedin_profile_url"),
                "application_date": row.get("application_date", self._now().date().isoformat()),
            }
            imported_candidate = self.create_candidate(candidate_payload)
            imported.append(imported_candidate)
            self._emit(
                "CandidateImported",
                {
                    "candidate_id": imported_candidate["candidate_id"],
                    "job_posting_id": payload["job_posting_id"],
                    "provider": "LinkedIn",
                    "source_candidate_id": source_candidate_id,
                },
            )

        self._emit(
            "LinkedInCandidatesImported",
            {
                "job_posting_id": payload["job_posting_id"],
                "imported_count": len(imported),
                "skipped_count": len(skipped),
            },
        )
        return {
            "job_posting_id": payload["job_posting_id"],
            "provider": "LinkedIn",
            "imported": imported,
            "skipped": skipped,
        }

    def update_interview(self, interview_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        interview = self._require_interview(interview_id)
        previous_status = interview.status

        if "candidate_id" in patch and patch["candidate_id"] != interview.candidate_id:
            candidate = self._require_candidate(patch["candidate_id"])
            if candidate.status not in {"Interviewing", "Offered"}:
                raise HiringValidationError("interviews can only be assigned to Interviewing/Offered candidates")
            interview.candidate_id = patch["candidate_id"]

        if "interview_type" in patch:
            self._validate_value(patch["interview_type"], self.INTERVIEW_TYPES, "interview_type")
            interview.interview_type = patch["interview_type"]

        for key in ["location_or_link", "feedback_summary", "interviewer_employee_ids"]:
            if key in patch:
                value = patch[key]
                if key == "interviewer_employee_ids":
                    if value is None:
                        value = []
                    else:
                        value = list(value)
                setattr(interview, key, value)

        if "scheduled_start" in patch:
            interview.scheduled_start = self._coerce_datetime(patch["scheduled_start"], "scheduled_start")
        if "scheduled_end" in patch:
            interview.scheduled_end = self._coerce_datetime(patch["scheduled_end"], "scheduled_end")
        if interview.scheduled_end <= interview.scheduled_start:
            raise HiringValidationError("scheduled_end must be after scheduled_start")

        if "recommendation" in patch:
            recommendation = patch["recommendation"]
            if recommendation is not None:
                self._validate_value(recommendation, self.RECOMMENDATIONS, "recommendation")
            interview.recommendation = recommendation

        if "status" in patch:
            self._validate_value(patch["status"], self.INTERVIEW_STATUSES, "status")
            interview.status = patch["status"]

        interview.updated_at = self._now()

        if previous_status != interview.status and interview.status == "Completed":
            self._emit("InterviewCompleted", {"interview_id": interview.interview_id, "candidate_id": interview.candidate_id})

        return self.get_interview(interview.interview_id)

    def mark_candidate_hired(self, candidate_id: str, employee_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id)
        if candidate.status != "Offered":
            raise HiringValidationError("candidate can only be hired from Offered status")

        employee_profile = self._upsert_employee_profile_for_candidate(candidate, employee_payload or {})
        candidate.status = "Hired"
        candidate.updated_at = self._now()

        self._record_candidate_stage_transition(
            candidate_id=candidate_id,
            from_status="Offered",
            to_status="Hired",
            changed_by=(employee_payload or {}).get("changed_by"),
            reason="candidate accepted offer",
            notes=None,
        )
        self._emit("CandidateStageChanged", {"candidate_id": candidate_id, "from_status": "Offered", "to_status": "Hired"})
        self._emit(
            "CandidateHired",
            {
                "candidate_id": candidate_id,
                "job_posting_id": candidate.job_posting_id,
                "employee_id": employee_profile.employee_id,
            },
        )
        self._emit(
            "EmployeeCreatedFromCandidate",
            {
                "candidate_id": candidate_id,
                "employee_id": employee_profile.employee_id,
                "department_id": employee_profile.department_id,
                "role_id": employee_profile.role_id,
            },
        )
        return self.get_candidate(candidate_id)

    def get_employee_profile(self, employee_id: str) -> dict[str, Any]:
        employee = self.employee_profiles.get(employee_id)
        if employee is None:
            raise HiringValidationError("employee does not exist")
        payload = self._serialize(employee)
        payload["candidate"] = self.get_candidate_summary(employee.candidate_id)
        payload["job_posting"] = self.get_job_posting(employee.job_posting_id)
        return payload

    def list_employee_profiles(self, *, candidate_id: str | None = None) -> list[dict[str, Any]]:
        rows = list(self.employee_profiles.values())
        if candidate_id is not None:
            rows = [row for row in rows if row.candidate_id == candidate_id]
        rows.sort(key=lambda row: (row.hire_date, row.updated_at, row.employee_id), reverse=True)
        return [self.get_employee_profile(row.employee_id) for row in rows]

    def _upsert_employee_profile_for_candidate(self, candidate: Candidate, payload: dict[str, Any]) -> EmployeeProfile:
        posting = self._require_job_posting(candidate.job_posting_id)
        existing_employee_id = self.hired_candidate_index.get(candidate.candidate_id)
        now = self._now()
        hire_date = self._coerce_date(payload.get("hire_date", now.date().isoformat()), "hire_date")
        employee_id = payload.get("employee_id") or existing_employee_id or self._new_id()
        for employee in self.employee_profiles.values():
            if employee.employee_id != employee_id and employee.email.lower() == candidate.email.lower():
                raise HiringValidationError("employee email must be unique")

        if existing_employee_id and existing_employee_id in self.employee_profiles:
            employee = self.employee_profiles[existing_employee_id]
            employee.department_id = payload.get("department_id", posting.department_id)
            employee.role_id = payload.get("role_id", posting.role_id)
            employee.first_name = payload.get("first_name", candidate.first_name)
            employee.last_name = payload.get("last_name", candidate.last_name)
            employee.email = payload.get("email", candidate.email)
            employee.phone = payload.get("phone", candidate.phone)
            employee.employment_type = payload.get("employment_type", posting.employment_type)
            employee.hire_date = hire_date
            employee.status = payload.get("status", "Active")
            employee.updated_at = now
            return employee

        employee = EmployeeProfile(
            employee_id=employee_id,
            candidate_id=candidate.candidate_id,
            job_posting_id=posting.job_posting_id,
            department_id=payload.get("department_id", posting.department_id),
            role_id=payload.get("role_id", posting.role_id),
            first_name=payload.get("first_name", candidate.first_name),
            last_name=payload.get("last_name", candidate.last_name),
            email=payload.get("email", candidate.email),
            phone=payload.get("phone", candidate.phone),
            employment_type=payload.get("employment_type", posting.employment_type),
            hire_date=hire_date,
            status=payload.get("status", "Active"),
            created_at=now,
            updated_at=now,
        )
        self.employee_profiles[employee.employee_id] = employee
        self.hired_candidate_index[candidate.candidate_id] = employee.employee_id
        return employee

    def list_candidate_stage_history(self, candidate_id: str) -> list[dict[str, Any]]:
        self._require_candidate(candidate_id)
        rows = [
            transition
            for transition in self.candidate_stage_transitions.values()
            if transition.candidate_id == candidate_id
        ]
        rows.sort(key=lambda row: (row.changed_at, row.candidate_stage_transition_id))
        return [self._serialize(row) for row in rows]

    def list_candidate_pipeline_view(
        self,
        *,
        pipeline_stage: str | None = None,
        department_id: str | None = None,
        job_posting_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if pipeline_stage is not None:
            self._validate_value(pipeline_stage, self.CANDIDATE_STATUSES, "pipeline_stage")
        if job_posting_id is not None:
            self._require_job_posting(job_posting_id)

        rows: list[dict[str, Any]] = []
        for candidate in self.candidates.values():
            posting = self._require_job_posting(candidate.job_posting_id)
            interviews = [x for x in self.interviews.values() if x.candidate_id == candidate.candidate_id]

            next_interview = None
            scheduled = sorted((x.scheduled_start for x in interviews if x.status == "Scheduled"), reverse=False)
            if scheduled:
                next_interview = scheduled[0]

            row = {
                "candidate_id": candidate.candidate_id,
                "candidate_name": f"{candidate.first_name} {candidate.last_name}".strip(),
                "candidate_email": candidate.email,
                "job_posting_id": posting.job_posting_id,
                "job_title": posting.title,
                "department_id": posting.department_id,
                "department_name": None,
                "role_id": posting.role_id,
                "role_title": None,
                "application_date": candidate.application_date.isoformat(),
                "pipeline_stage": candidate.status,
                "stage_updated_at": candidate.updated_at.isoformat(),
                "source": candidate.source,
                "source_candidate_id": candidate.source_candidate_id,
                "next_interview_at": next_interview.isoformat() if next_interview else None,
                "interview_count": len(interviews),
                "last_interview_recommendation": self._latest_interview_recommendation(interviews),
                "hiring_owner_employee_id": None,
                "hiring_owner_name": None,
                "hired_employee_id": self.hired_candidate_index.get(candidate.candidate_id),
                "updated_at": candidate.updated_at.isoformat(),
            }
            rows.append(row)

        if pipeline_stage:
            rows = [row for row in rows if row["pipeline_stage"] == pipeline_stage]
        if department_id:
            rows = [row for row in rows if row["department_id"] == department_id]
        if job_posting_id:
            rows = [row for row in rows if row["job_posting_id"] == job_posting_id]

        rows.sort(key=lambda row: (row["stage_updated_at"], row["candidate_id"]), reverse=True)
        return rows

    def build_hiring_ui(
        self,
        *,
        pipeline_stage: str | None = None,
        department_id: str | None = None,
        job_posting_id: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Build UI-friendly surfaces for hiring pages from canonical read-model fields."""
        return {
            "job_postings": self.list_job_postings(department_id=department_id),
            "candidate_pipeline": self.list_candidate_pipeline_view(
                pipeline_stage=pipeline_stage,
                department_id=department_id,
                job_posting_id=job_posting_id,
            ),
        }

    def get_candidate_summary(self, candidate_id: str) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id)
        job_posting = self._require_job_posting(candidate.job_posting_id)
        return {
            "candidate_id": candidate.candidate_id,
            "job_posting_id": candidate.job_posting_id,
            "job_posting_title": job_posting.title,
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "email": candidate.email,
            "status": candidate.status,
        }

    def _candidate_count(self, job_posting_id: str) -> int:
        return sum(1 for candidate in self.candidates.values() if candidate.job_posting_id == job_posting_id)

    def _serialize(self, instance: Any) -> dict[str, Any]:
        payload = asdict(instance)
        for key, value in list(payload.items()):
            if isinstance(value, (datetime, date)):
                payload[key] = value.isoformat()
        return payload

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if payload.get("candidate_stage_transition_id"):
            idempotency_key = str(payload["candidate_stage_transition_id"])
        elif payload.get("interview_id"):
            idempotency_key = str(payload["interview_id"])
        elif payload.get("employee_profile_id"):
            idempotency_key = str(payload["employee_profile_id"])
        elif payload.get("candidate_id") and payload.get("from_status") and payload.get("to_status"):
            idempotency_key = f"{payload['candidate_id']}:{payload['from_status']}:{payload['to_status']}"
        elif payload.get("candidate_id"):
            idempotency_key = str(payload["candidate_id"])
        elif payload.get("job_posting_id"):
            idempotency_key = str(payload["job_posting_id"])
        else:
            idempotency_key = self._new_id()

        event = emit_canonical_event(
            self.events,
            legacy_event_name=event_type,
            data=payload,
            source="hiring-service",
            tenant_id=self.tenant_id,
            registry=self.event_registry,
            idempotency_key=idempotency_key,
            aliases={"payload": payload, "occurred_at": self._now().isoformat()},
        )
        event["legacy_event_type"] = event_type

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _new_id(self) -> str:
        return str(uuid4())

    def _require(self, payload: dict[str, Any], fields: list[str]) -> None:
        for field_name in fields:
            if field_name not in payload or payload[field_name] in (None, ""):
                raise HiringValidationError(f"{field_name} is required")

    def _validate_value(self, value: str, allowed: set[str], field_name: str) -> None:
        if value not in allowed:
            allowed_values = ", ".join(sorted(allowed))
            raise HiringValidationError(f"{field_name} must be one of: {allowed_values}")

    def _coerce_date(self, value: Any, field_name: str) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise HiringValidationError(f"{field_name} must be a valid ISO date") from exc
        raise HiringValidationError(f"{field_name} must be a date or ISO date string")

    def _coerce_optional_date(self, value: Any, field_name: str) -> date | None:
        if value is None:
            return None
        return self._coerce_date(value, field_name)

    def _coerce_datetime(self, value: Any, field_name: str) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            source = value.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(source)
            except ValueError as exc:
                raise HiringValidationError(f"{field_name} must be a valid ISO datetime") from exc
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        raise HiringValidationError(f"{field_name} must be a datetime or ISO datetime string")

    def _require_job_posting(self, job_posting_id: str) -> JobPosting:
        posting = self.job_postings.get(job_posting_id)
        if not posting:
            raise HiringValidationError("job_posting_id does not exist")
        return posting

    def _require_candidate(self, candidate_id: str) -> Candidate:
        candidate = self.candidates.get(candidate_id)
        if not candidate:
            raise HiringValidationError("candidate_id does not exist")
        return candidate

    def _require_interview(self, interview_id: str) -> Interview:
        interview = self.interviews.get(interview_id)
        if not interview:
            raise HiringValidationError("interview_id does not exist")
        return interview

    def _record_candidate_stage_transition(
        self,
        *,
        candidate_id: str,
        from_status: str | None,
        to_status: str,
        changed_by: str | None,
        reason: str | None,
        notes: str | None,
    ) -> CandidateStageTransition:
        transition = CandidateStageTransition(
            candidate_stage_transition_id=self._new_id(),
            candidate_id=candidate_id,
            from_status=from_status,
            to_status=to_status,
            changed_at=self._now(),
            changed_by=changed_by,
            reason=reason,
            notes=notes,
        )
        self.candidate_stage_transitions[transition.candidate_stage_transition_id] = transition
        self._emit(
            "CandidateStageTransitionRecorded",
            {
                "candidate_stage_transition_id": transition.candidate_stage_transition_id,
                "candidate_id": candidate_id,
                "from_status": from_status,
                "to_status": to_status,
            },
        )
        return transition

    def _latest_interview_recommendation(self, interviews: list[Interview]) -> str | None:
        recommended = [row for row in interviews if row.recommendation]
        if not recommended:
            return None
        recommended.sort(key=lambda row: (row.updated_at, row.interview_id), reverse=True)
        return recommended[0].recommendation
