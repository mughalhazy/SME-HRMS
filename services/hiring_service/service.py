from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4


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


@dataclass(slots=True)
class Interview:
    interview_id: str
    candidate_id: str
    interview_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    location_or_link: str | None
    interviewer_employee_ids: list[str] = field(default_factory=list)
    feedback_summary: str | None = None
    recommendation: str | None = None
    status: str = "Scheduled"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


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
    CANDIDATE_SOURCES = {"Referral", "JobBoard", "CareerSite", "Agency", "Other"}
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
        self.interviews: dict[str, Interview] = {}
        self.events: list[dict[str, Any]] = []

    def create_job_posting(self, payload: dict[str, Any]) -> dict[str, Any]:
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

    def list_job_postings(self, *, status: str | None = None, department_id: str | None = None) -> list[dict[str, Any]]:
        if status is not None:
            self._validate_value(status, self.JOB_POSTING_STATUSES, "status")
        rows: list[JobPosting] = list(self.job_postings.values())
        if status:
            rows = [r for r in rows if r.status == status]
        if department_id:
            rows = [r for r in rows if r.department_id == department_id]
        rows.sort(key=lambda r: (r.posting_date, r.job_posting_id), reverse=True)
        return [self._serialize(x) for x in rows]

    def create_candidate(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require(payload, ["job_posting_id", "first_name", "last_name", "email", "application_date"])
        posting = self._require_job_posting(payload["job_posting_id"])
        if posting.status not in {"Open", "OnHold"}:
            raise HiringValidationError("candidates can only be created for Open/OnHold job postings")

        source = payload.get("source")
        if source is not None:
            self._validate_value(source, self.CANDIDATE_SOURCES, "source")

        # unique (job_posting_id, email)
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
            application_date=self._coerce_date(payload["application_date"], "application_date"),
            status=payload.get("status", "Applied"),
            created_at=self._now(),
            updated_at=self._now(),
        )
        self._validate_value(candidate.status, self.CANDIDATE_STATUSES, "status")
        self.candidates[candidate.candidate_id] = candidate
        self._emit("CandidateApplied", {"candidate_id": candidate.candidate_id, "job_posting_id": candidate.job_posting_id})
        return self._serialize(candidate)

    def update_candidate(self, candidate_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id)
        previous_status = candidate.status

        for key in ["first_name", "last_name", "email", "phone", "resume_url", "source"]:
            if key in patch:
                if key == "source" and patch[key] is not None:
                    self._validate_value(patch[key], self.CANDIDATE_SOURCES, "source")
                setattr(candidate, key, patch[key])

        if "application_date" in patch:
            candidate.application_date = self._coerce_date(patch["application_date"], "application_date")

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
            self._emit(
                "CandidateStageChanged",
                {
                    "candidate_id": candidate.candidate_id,
                    "from_status": previous_status,
                    "to_status": candidate.status,
                },
            )

        return self._serialize(candidate)

    def get_candidate(self, candidate_id: str) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id)
        payload = self._serialize(candidate)
        payload["interviews"] = [
            self._serialize(x)
            for x in sorted(
                (i for i in self.interviews.values() if i.candidate_id == candidate_id),
                key=lambda row: (row.scheduled_start, row.interview_id),
            )
        ]
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
        return self._serialize(interview)

    def update_interview(self, interview_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        interview = self._require_interview(interview_id)
        previous_status = interview.status

        if "interview_type" in patch:
            self._validate_value(patch["interview_type"], self.INTERVIEW_TYPES, "interview_type")
            interview.interview_type = patch["interview_type"]

        for key in ["location_or_link", "feedback_summary", "interviewer_employee_ids"]:
            if key in patch:
                value = patch[key]
                if key == "interviewer_employee_ids":
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

        return self._serialize(interview)

    def mark_candidate_hired(self, candidate_id: str) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id)
        if candidate.status != "Offered":
            raise HiringValidationError("candidate can only be hired from Offered status")
        candidate.status = "Hired"
        candidate.updated_at = self._now()

        self._emit("CandidateStageChanged", {"candidate_id": candidate_id, "from_status": "Offered", "to_status": "Hired"})
        self._emit("CandidateHired", {"candidate_id": candidate_id, "job_posting_id": candidate.job_posting_id})
        return self._serialize(candidate)

    def list_candidate_pipeline_view(
        self,
        *,
        pipeline_stage: str | None = None,
        department_id: str | None = None,
        job_posting_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if pipeline_stage is not None:
            self._validate_value(pipeline_stage, self.CANDIDATE_STATUSES, "pipeline_stage")

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
                "next_interview_at": next_interview.isoformat() if next_interview else None,
                "interview_count": len(interviews),
                "hiring_owner_employee_id": None,
                "hiring_owner_name": None,
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

    def _serialize(self, instance: Any) -> dict[str, Any]:
        payload = asdict(instance)
        for key, value in list(payload.items()):
            if isinstance(value, (datetime, date)):
                payload[key] = value.isoformat()
        return payload

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append(
            {
                "event_type": event_type,
                "payload": payload,
                "occurred_at": self._now().isoformat(),
            }
        )

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
