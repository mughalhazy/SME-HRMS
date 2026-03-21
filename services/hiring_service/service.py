from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from threading import RLock
from time import perf_counter
from typing import Any
from uuid import uuid4

from audit_service import emit_audit_record
from event_contract import EventRegistry
from notification_service import NotificationService, NotificationServiceError
from outbox_system import OutboxManager
from persistent_store import PersistentKVStore
from resilience import CentralErrorLogger, CircuitBreaker, CircuitBreakerOpenError, DeadLetterQueue, Observability, run_with_retry
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id
from workflow_service import WorkflowService, WorkflowServiceError


class HiringValidationError(ValueError):
    """Raised for domain validation errors."""


@dataclass(slots=True)
class JobRequisition:
    requisition_id: str
    tenant_id: str
    title: str
    department_id: str
    role_id: str | None
    employment_type: str
    justification: str
    openings_count: int
    requested_by: str
    hiring_manager_id: str | None
    recruiter_ids: list[str] = field(default_factory=list)
    hiring_plan: dict[str, Any] = field(default_factory=dict)
    status: str = "Draft"
    approval_workflow_id: str | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    job_posting_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class JobPosting:
    job_posting_id: str
    tenant_id: str
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
    requisition_id: str | None = None
    hiring_manager_id: str | None = None
    recruiter_ids: list[str] = field(default_factory=list)
    hiring_plan: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class PipelineTemplate:
    pipeline_template_id: str
    tenant_id: str
    name: str
    stages: list[dict[str, Any]]
    is_default: bool
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class Candidate:
    candidate_id: str
    tenant_id: str
    job_posting_id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    resume_url: str | None
    source: str | None
    application_date: date
    status: str
    pipeline_template_id: str | None
    current_offer_id: str | None = None
    hire_workflow_id: str | None = None
    source_candidate_id: str | None = None
    source_profile_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class CandidateStageTransition:
    candidate_stage_transition_id: str
    tenant_id: str
    candidate_id: str
    from_status: str | None
    to_status: str
    changed_at: datetime
    changed_by: str | None = None
    reason: str | None = None
    notes: str | None = None


@dataclass(slots=True)
class EvaluationForm:
    evaluation_form_id: str
    tenant_id: str
    name: str
    stage: str
    sections: list[dict[str, Any]]
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class Interview:
    interview_id: str
    tenant_id: str
    candidate_id: str
    interview_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    location_or_link: str | None
    google_calendar_event_id: str | None = None
    google_calendar_event_link: str | None = None
    interviewer_employee_ids: list[str] = field(default_factory=list)
    evaluation_form_id: str | None = None
    feedback_summary: str | None = None
    recommendation: str | None = None
    status: str = "Scheduled"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class InterviewScorecard:
    scorecard_id: str
    tenant_id: str
    interview_id: str
    candidate_id: str
    evaluation_form_id: str | None
    overall_rating: float
    recommendation: str
    competencies: list[dict[str, Any]]
    structured_feedback: dict[str, Any]
    submitted_by: str
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class Offer:
    offer_id: str
    tenant_id: str
    candidate_id: str
    job_posting_id: str
    title: str
    salary_amount: float
    currency: str
    start_date: date
    status: str
    compensation_summary: dict[str, Any]
    created_by: str
    approval_workflow_id: str | None = None
    approved_at: datetime | None = None
    sent_at: datetime | None = None
    accepted_at: datetime | None = None
    declined_at: datetime | None = None
    status_reason: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class EmployeeProfile:
    employee_id: str
    tenant_id: str
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
    employee_service_payload: dict[str, Any] = field(default_factory=dict)
    onboarding_status: str = "Pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EmployeeServiceHandoffAdapter:
    """Compatibility-safe handoff adapter for employee-service owned onboarding records."""

    def __init__(self) -> None:
        self.records: dict[tuple[str, str], dict[str, Any]] = {}

    def create_employee_record(self, payload: dict[str, Any]) -> dict[str, Any]:
        tenant_id = normalize_tenant_id(payload.get("tenant_id"))
        employee_id = str(payload.get("employee_id") or uuid4())
        employee_number = str(payload.get("employee_number") or f"EMP-{employee_id[:8].upper()}")
        record = {
            "employee_id": employee_id,
            "tenant_id": tenant_id,
            "employee_number": employee_number,
            "first_name": payload["first_name"],
            "last_name": payload["last_name"],
            "email": payload["email"],
            "phone": payload.get("phone"),
            "hire_date": payload["hire_date"],
            "employment_type": payload["employment_type"],
            "status": payload.get("status", "Draft"),
            "department_id": payload["department_id"],
            "role_id": payload["role_id"],
            "source": "hiring-service",
            "created_at": payload.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "updated_at": payload.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        }
        self.records[(tenant_id, employee_id)] = record
        return dict(record)

    def get_employee_record(self, *, tenant_id: str, employee_id: str) -> dict[str, Any]:
        record = self.records.get((normalize_tenant_id(tenant_id), employee_id))
        if record is None:
            raise HiringValidationError("employee does not exist")
        return dict(record)


class HiringService:
    """Enterprise ATS implementation extending the existing hiring-service domain."""

    JOB_POSTING_STATUSES = {"Draft", "Open", "OnHold", "Closed", "Filled"}
    REQUISITION_STATUSES = {"Draft", "PendingApproval", "Approved", "Rejected", "Open", "Closed", "Cancelled"}
    CANDIDATE_STATUSES = {"Applied", "Screening", "Interviewing", "Offered", "Hired", "Rejected", "Withdrawn"}
    CANONICAL_PIPELINE_STAGES = ("Applied", "Screening", "Interview", "Offer", "Hired", "Rejected")
    CANDIDATE_STATUS_ALIASES = {
        "Applied": "Applied",
        "Screening": "Screening",
        "Interview": "Interviewing",
        "Interviewing": "Interviewing",
        "Offer": "Offered",
        "Offered": "Offered",
        "Hired": "Hired",
        "Rejected": "Rejected",
        "Withdrawn": "Withdrawn",
    }
    STATUS_TO_CANONICAL_STAGE = {
        "Applied": "Applied",
        "Screening": "Screening",
        "Interviewing": "Interview",
        "Offered": "Offer",
        "Hired": "Hired",
        "Rejected": "Rejected",
        "Withdrawn": "Rejected",
    }
    INTERVIEW_STATUSES = {"Scheduled", "Completed", "Cancelled", "NoShow"}
    EMPLOYMENT_TYPES = {"FullTime", "PartTime", "Contract", "Intern"}
    CANDIDATE_SOURCES = {"Referral", "JobBoard", "CareerSite", "Agency", "LinkedIn", "Other"}
    INTERVIEW_TYPES = {"PhoneScreen", "Technical", "Behavioral", "Panel", "Final"}
    RECOMMENDATIONS = {"StrongHire", "Hire", "NoHire", "Undecided"}
    OFFER_STATUSES = {"Draft", "PendingApproval", "Approved", "Sent", "Accepted", "Declined", "Cancelled"}
    ROLE_CAPABILITIES = {
        "Admin": {"*"},
        "Service": {"*"},
        "Recruiter": {"requisition.manage", "job_posting.manage", "candidate.manage", "interview.manage", "offer.manage"},
        "Manager": {"requisition.manage", "requisition.approve", "job_posting.manage", "candidate.manage", "interview.manage", "offer.approve", "hire.approve"},
        "HiringManager": {"requisition.manage", "requisition.approve", "job_posting.manage", "candidate.manage", "interview.manage", "offer.approve", "hire.approve"},
    }
    CANDIDATE_STATUS_FLOW = {
        "Applied": {"Screening", "Rejected", "Withdrawn"},
        "Screening": {"Interviewing", "Rejected", "Withdrawn"},
        "Interviewing": {"Offered", "Rejected", "Withdrawn"},
        "Offered": {"Hired", "Rejected", "Withdrawn"},
        "Hired": set(),
        "Rejected": set(),
        "Withdrawn": set(),
    }

    def __init__(
        self,
        db_path: str | None = None,
        *,
        workflow_service: WorkflowService | None = None,
        notification_service: NotificationService | None = None,
        employee_service: EmployeeServiceHandoffAdapter | None = None,
        tenant_id: str = DEFAULT_TENANT_ID,
    ) -> None:
        self.job_postings = PersistentKVStore[str, JobPosting](service="hiring-service", namespace="job_postings", db_path=db_path)
        shared_db_path = self.job_postings.db_path
        self.requisitions = PersistentKVStore[str, JobRequisition](service="hiring-service", namespace="requisitions", db_path=shared_db_path)
        self.pipeline_templates = PersistentKVStore[str, PipelineTemplate](service="hiring-service", namespace="pipeline_templates", db_path=shared_db_path)
        self.candidates = PersistentKVStore[str, Candidate](service="hiring-service", namespace="candidates", db_path=shared_db_path)
        self.candidate_stage_transitions = PersistentKVStore[str, CandidateStageTransition](service="hiring-service", namespace="candidate_stage_transitions", db_path=shared_db_path)
        self.evaluation_forms = PersistentKVStore[str, EvaluationForm](service="hiring-service", namespace="evaluation_forms", db_path=shared_db_path)
        self.interviews = PersistentKVStore[str, Interview](service="hiring-service", namespace="interviews", db_path=shared_db_path)
        self.scorecards = PersistentKVStore[str, InterviewScorecard](service="hiring-service", namespace="scorecards", db_path=shared_db_path)
        self.offers = PersistentKVStore[str, Offer](service="hiring-service", namespace="offers", db_path=shared_db_path)
        self.employee_profiles = PersistentKVStore[str, EmployeeProfile](service="hiring-service", namespace="employee_handoffs", db_path=shared_db_path)
        self.hired_candidate_index = PersistentKVStore[str, str](service="hiring-service", namespace="hired_candidate_index", db_path=shared_db_path)
        self.events: list[dict[str, Any]] = []
        self.tenant_id = normalize_tenant_id(tenant_id)
        self.event_registry = EventRegistry()
        self.notification_service = notification_service or NotificationService()
        self.workflow_service = workflow_service or WorkflowService(notification_service=self.notification_service)
        self.employee_service = employee_service or EmployeeServiceHandoffAdapter()
        self.error_logger = CentralErrorLogger("hiring-service")
        self.dead_letters = DeadLetterQueue()
        self.observability = Observability("hiring-service")
        self.outbox = OutboxManager(
            service_name="hiring-service",
            tenant_id=self.tenant_id,
            db_path=shared_db_path,
            observability=self.observability,
            dead_letters=self.dead_letters,
            event_registry=self.event_registry,
        )
        self.integration_breakers = {
            "google-calendar": CircuitBreaker(failure_threshold=2, recovery_timeout=1.0),
            "linkedin": CircuitBreaker(failure_threshold=2, recovery_timeout=1.0),
        }
        self._lock = RLock()
        self._ensure_default_pipeline_template(self.tenant_id)
        self._register_workflows()

    def _register_workflows(self) -> None:
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code="candidate_hiring_approval",
            source_service="hiring-service",
            subject_type="Candidate",
            description="Centralized candidate hiring approval workflow.",
            steps=[
                {
                    "name": "hire-approval",
                    "type": "approval",
                    "assignee_template": "{approver_assignee}",
                    "sla": "PT48H",
                    "escalation_assignee_template": "{escalation_assignee}",
                }
            ],
        )
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code="job_requisition_approval",
            source_service="hiring-service",
            subject_type="JobRequisition",
            description="Job requisition approval workflow.",
            steps=[
                {
                    "name": "requisition-approval",
                    "type": "approval",
                    "assignee_template": "{approver_assignee}",
                    "sla": "PT72H",
                    "escalation_assignee_template": "{escalation_assignee}",
                }
            ],
        )
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code="offer_approval",
            source_service="hiring-service",
            subject_type="Offer",
            description="Offer approval workflow.",
            steps=[
                {
                    "name": "offer-approval",
                    "type": "approval",
                    "assignee_template": "{approver_assignee}",
                    "sla": "PT48H",
                    "escalation_assignee_template": "{escalation_assignee}",
                }
            ],
        )

    # ---------------------------------------------------------------------
    # Requisition management
    # ---------------------------------------------------------------------
    def create_requisition(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require(payload, ["title", "department_id", "employment_type", "justification", "openings_count", "requested_by"])
        self._validate_value(payload["employment_type"], self.EMPLOYMENT_TYPES, "employment_type")
        if int(payload["openings_count"]) < 1:
            raise HiringValidationError("openings_count must be >= 1")
        tenant_id = self._resolve_tenant_id(payload)
        self._authorize(payload, "requisition.manage", department_id=payload.get("department_id"), tenant_id=tenant_id)

        requisition = JobRequisition(
            requisition_id=self._new_id(),
            tenant_id=tenant_id,
            title=payload["title"],
            department_id=payload["department_id"],
            role_id=payload.get("role_id"),
            employment_type=payload["employment_type"],
            justification=payload["justification"],
            openings_count=int(payload["openings_count"]),
            requested_by=str(payload["requested_by"]),
            hiring_manager_id=payload.get("hiring_manager_id"),
            recruiter_ids=list(payload.get("recruiter_ids", [])),
            hiring_plan=self._normalize_hiring_plan(payload.get("hiring_plan")),
            status=payload.get("status", "Draft"),
        )
        self._validate_value(requisition.status, self.REQUISITION_STATUSES, "status")
        self.requisitions[requisition.requisition_id] = requisition
        response = self.get_requisition(requisition.requisition_id, tenant_id=tenant_id)
        self._audit_hiring_mutation("requisition_created", "JobRequisition", requisition.requisition_id, {}, response, payload=payload)
        self._emit("RequisitionCreated", {
            "tenant_id": tenant_id,
            "requisition_id": requisition.requisition_id,
            "department_id": requisition.department_id,
            "requested_by": requisition.requested_by,
        })
        return response

    def get_requisition(self, requisition_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        requisition = self._require_requisition(requisition_id, tenant_id=tenant_id)
        payload = self._serialize(requisition)
        payload["candidate_count"] = sum(1 for candidate in self.candidates.values() if candidate.tenant_id == requisition.tenant_id and candidate.job_posting_id == requisition.job_posting_id)
        return payload

    def list_requisitions(self, *, tenant_id: str | None = None, status: str | None = None, department_id: str | None = None) -> list[dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id or self.tenant_id)
        if status is not None:
            self._validate_value(status, self.REQUISITION_STATUSES, "status")
        rows = [row for row in self.requisitions.values() if row.tenant_id == tenant]
        if status:
            rows = [row for row in rows if row.status == status]
        if department_id:
            rows = [row for row in rows if row.department_id == department_id]
        rows.sort(key=lambda row: (row.updated_at, row.requisition_id), reverse=True)
        return [self.get_requisition(row.requisition_id, tenant_id=tenant) for row in rows]

    def submit_requisition_for_approval(self, requisition_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        patch = payload or {}
        requisition = self._require_requisition(requisition_id, tenant_id=patch.get("tenant_id"))
        self._authorize(patch, "requisition.manage", department_id=requisition.department_id, tenant_id=requisition.tenant_id)
        before = self.get_requisition(requisition_id, tenant_id=requisition.tenant_id)
        approver_assignee = self._approval_assignee(patch, default_role="Manager")
        if not requisition.approval_workflow_id:
            workflow = self.workflow_service.start_workflow(
                tenant_id=requisition.tenant_id,
                definition_code="job_requisition_approval",
                source_service="hiring-service",
                subject_type="JobRequisition",
                subject_id=requisition.requisition_id,
                actor_id=str(patch.get("changed_by") or requisition.requested_by),
                actor_type="user",
                context={"approver_assignee": approver_assignee, "escalation_assignee": "role:Admin"},
            )
            requisition.approval_workflow_id = workflow["workflow_id"]
        requisition.status = "PendingApproval"
        requisition.updated_at = self._now()
        response = self.get_requisition(requisition_id, tenant_id=requisition.tenant_id)
        self._audit_hiring_mutation("requisition_submitted", "JobRequisition", requisition_id, before, response, payload=patch)
        self._emit("RequisitionSubmitted", {
            "tenant_id": requisition.tenant_id,
            "requisition_id": requisition.requisition_id,
            "department_id": requisition.department_id,
            "workflow_id": requisition.approval_workflow_id,
        })
        return response

    def approve_requisition(self, requisition_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        patch = payload or {}
        requisition = self._require_requisition(requisition_id, tenant_id=patch.get("tenant_id"))
        self._authorize(patch, "requisition.approve", department_id=requisition.department_id, tenant_id=requisition.tenant_id)
        before = self.get_requisition(requisition_id, tenant_id=requisition.tenant_id)
        if not requisition.approval_workflow_id:
            self.submit_requisition_for_approval(requisition_id, patch)
        workflow = self._approve_workflow(
            requisition.approval_workflow_id,
            tenant_id=requisition.tenant_id,
            payload=patch,
            comment="Requisition approved",
        )
        if workflow.get("metadata", {}).get("terminal_result") != "approved":
            raise HiringValidationError("requisition approval workflow did not complete")
        requisition.status = "Approved"
        requisition.approved_at = self._now()
        requisition.updated_at = self._now()
        if patch.get("create_job_posting", True) and not requisition.job_posting_id:
            posting = self.create_job_posting(
                {
                    "tenant_id": requisition.tenant_id,
                    "title": requisition.title,
                    "department_id": requisition.department_id,
                    "role_id": requisition.role_id,
                    "employment_type": requisition.employment_type,
                    "description": patch.get("description") or requisition.justification,
                    "openings_count": requisition.openings_count,
                    "posting_date": patch.get("posting_date") or self._now().date().isoformat(),
                    "status": patch.get("posting_status", "Open"),
                    "requisition_id": requisition.requisition_id,
                    "hiring_manager_id": requisition.hiring_manager_id,
                    "recruiter_ids": requisition.recruiter_ids,
                    "hiring_plan": requisition.hiring_plan,
                    "changed_by": patch.get("changed_by"),
                    "actor_role": patch.get("actor_role"),
                }
            )
            requisition.job_posting_id = posting["job_posting_id"]
            requisition.status = "Open"
        response = self.get_requisition(requisition_id, tenant_id=requisition.tenant_id)
        self._audit_hiring_mutation("requisition_approved", "JobRequisition", requisition_id, before, response, payload=patch)
        self._emit("RequisitionApproved", {
            "tenant_id": requisition.tenant_id,
            "requisition_id": requisition.requisition_id,
            "job_posting_id": requisition.job_posting_id,
        })
        return response

    # ---------------------------------------------------------------------
    # Job postings
    # ---------------------------------------------------------------------
    def create_job_posting(self, payload: dict[str, Any]) -> dict[str, Any]:
        started = perf_counter()
        with self._lock:
            self._require(payload, ["title", "department_id", "employment_type", "description", "openings_count", "posting_date"])
            self._validate_value(payload["employment_type"], self.EMPLOYMENT_TYPES, "employment_type")
            if int(payload["openings_count"]) < 1:
                raise HiringValidationError("openings_count must be >= 1")
            tenant_id = self._resolve_tenant_id(payload)
            self._authorize(payload, "job_posting.manage", department_id=payload.get("department_id"), tenant_id=tenant_id)

            posting_date = self._coerce_date(payload["posting_date"], "posting_date")
            closing_date = self._coerce_optional_date(payload.get("closing_date"), "closing_date")
            if closing_date and closing_date < posting_date:
                raise HiringValidationError("closing_date must be on or after posting_date")

            status = payload.get("status", "Draft")
            self._validate_value(status, self.JOB_POSTING_STATUSES, "status")
            requisition_id = payload.get("requisition_id")
            if requisition_id:
                requisition = self._require_requisition(requisition_id, tenant_id=tenant_id)
                if requisition.status not in {"Approved", "Open"}:
                    raise HiringValidationError("requisition must be approved before opening a posting")

            job_posting = JobPosting(
                job_posting_id=self._new_id(),
                tenant_id=tenant_id,
                title=payload["title"],
                department_id=payload["department_id"],
                role_id=payload.get("role_id"),
                employment_type=payload["employment_type"],
                location=payload.get("location"),
                description=payload["description"],
                openings_count=int(payload["openings_count"]),
                posting_date=posting_date,
                closing_date=closing_date,
                status=status,
                requisition_id=requisition_id,
                hiring_manager_id=payload.get("hiring_manager_id"),
                recruiter_ids=list(payload.get("recruiter_ids", [])),
                hiring_plan=self._normalize_hiring_plan(payload.get("hiring_plan")),
            )
            self.job_postings[job_posting.job_posting_id] = job_posting
            if requisition_id:
                requisition = self._require_requisition(requisition_id, tenant_id=tenant_id)
                requisition.job_posting_id = job_posting.job_posting_id
                requisition.status = "Open" if status == "Open" else requisition.status
                requisition.updated_at = self._now()
            if status == "Open":
                self._emit("JobPostingOpened", {"tenant_id": tenant_id, "job_posting_id": job_posting.job_posting_id})
        response = self.get_job_posting(job_posting.job_posting_id, tenant_id=tenant_id)
        self._audit_hiring_mutation("job_posting_created", "JobPosting", job_posting.job_posting_id, {}, response, payload=payload)
        self.observability.track("create_job_posting", trace_id=self.observability.trace_id(), started_at=started, success=True, context={"status": 201, "job_posting_id": job_posting.job_posting_id})
        return response

    def update_job_posting(self, job_posting_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        posting = self._require_job_posting(job_posting_id, tenant_id=patch.get("tenant_id"))
        self._authorize(patch, "job_posting.manage", department_id=posting.department_id, tenant_id=posting.tenant_id)
        before = self.get_job_posting(job_posting_id, tenant_id=posting.tenant_id)
        previous_status = posting.status

        for key in ["title", "department_id", "role_id", "location", "description", "hiring_manager_id"]:
            if key in patch:
                setattr(posting, key, patch[key])

        if "employment_type" in patch:
            self._validate_value(patch["employment_type"], self.EMPLOYMENT_TYPES, "employment_type")
            posting.employment_type = patch["employment_type"]
        if "openings_count" in patch:
            if int(patch["openings_count"]) < 1:
                raise HiringValidationError("openings_count must be >= 1")
            posting.openings_count = int(patch["openings_count"])
        if "recruiter_ids" in patch:
            posting.recruiter_ids = list(patch.get("recruiter_ids") or [])
        if "hiring_plan" in patch:
            posting.hiring_plan = self._normalize_hiring_plan(patch.get("hiring_plan"))

        posting_date = posting.posting_date
        if "posting_date" in patch:
            posting_date = self._coerce_date(patch["posting_date"], "posting_date")
            posting.posting_date = posting_date
        if "closing_date" in patch:
            posting.closing_date = self._coerce_optional_date(patch.get("closing_date"), "closing_date")
        if posting.closing_date and posting.closing_date < posting_date:
            raise HiringValidationError("closing_date must be on or after posting_date")
        if "status" in patch:
            self._validate_value(patch["status"], self.JOB_POSTING_STATUSES, "status")
            posting.status = patch["status"]
        posting.updated_at = self._now()

        if previous_status != posting.status:
            if posting.status == "Open":
                self._emit("JobPostingOpened", {"tenant_id": posting.tenant_id, "job_posting_id": posting.job_posting_id})
            elif posting.status == "OnHold":
                self._emit("JobPostingOnHold", {"tenant_id": posting.tenant_id, "job_posting_id": posting.job_posting_id})
            elif posting.status in {"Closed", "Filled"}:
                self._emit("JobPostingClosed", {"tenant_id": posting.tenant_id, "job_posting_id": posting.job_posting_id, "status": posting.status})
        response = self.get_job_posting(posting.job_posting_id, tenant_id=posting.tenant_id)
        self._audit_hiring_mutation("job_posting_updated", "JobPosting", posting.job_posting_id, before, response, payload=patch)
        return response

    def get_job_posting(self, job_posting_id: str, tenant_id: str | None = None) -> dict[str, Any]:
        posting = self._require_job_posting(job_posting_id, tenant_id=tenant_id)
        payload = self._serialize(posting)
        payload["candidate_count"] = self._candidate_count(job_posting_id, tenant_id=posting.tenant_id)
        payload["requisition"] = self.get_requisition(posting.requisition_id, tenant_id=posting.tenant_id) if posting.requisition_id else None
        return payload

    def list_job_postings(
        self,
        *,
        status: str | None = None,
        department_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if status is not None:
            self._validate_value(status, self.JOB_POSTING_STATUSES, "status")
        if limit is not None and limit < 1:
            raise HiringValidationError("limit must be >= 1")
        tenant = normalize_tenant_id(tenant_id or self.tenant_id)
        rows = [r for r in self.job_postings.values() if r.tenant_id == tenant]
        if status:
            rows = [r for r in rows if r.status == status]
        if department_id:
            rows = [r for r in rows if r.department_id == department_id]
        rows.sort(key=lambda r: (r.posting_date, r.updated_at, r.job_posting_id), reverse=True)
        if cursor is not None:
            cursor_index = next((index for index, row in enumerate(rows) if row.job_posting_id == cursor), None)
            if cursor_index is None:
                raise HiringValidationError("cursor does not exist")
            rows = rows[cursor_index + 1:]
        if limit is not None:
            rows = rows[:limit]
        return [self.get_job_posting(row.job_posting_id, tenant_id=tenant) for row in rows]

    def delete_job_posting(self, job_posting_id: str, *, tenant_id: str | None = None, actor_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = actor_payload or {}
        posting = self._require_job_posting(job_posting_id, tenant_id=tenant_id or payload.get("tenant_id"))
        self._authorize(payload, "job_posting.manage", department_id=posting.department_id, tenant_id=posting.tenant_id)
        if any(candidate.job_posting_id == job_posting_id and candidate.tenant_id == posting.tenant_id for candidate in self.candidates.values()):
            raise HiringValidationError("job posting cannot be deleted while candidates exist")
        before = self.get_job_posting(job_posting_id, tenant_id=posting.tenant_id)
        del self.job_postings[job_posting_id]
        self._audit_hiring_mutation("job_posting_deleted", "JobPosting", job_posting_id, before, {}, payload=payload)
        return before

    # ---------------------------------------------------------------------
    # Tenant-specific pipeline templates
    # ---------------------------------------------------------------------
    def configure_pipeline_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        tenant_id = self._resolve_tenant_id(payload)
        stages = payload.get("stages")
        if not isinstance(stages, list) or not stages:
            raise HiringValidationError("stages must be a non-empty list")
        normalized_stages = [self._normalize_pipeline_stage_definition(stage) for stage in stages]
        template = PipelineTemplate(
            pipeline_template_id=self._new_id(),
            tenant_id=tenant_id,
            name=str(payload.get("name") or "Default ATS Pipeline"),
            stages=normalized_stages,
            is_default=bool(payload.get("is_default", True)),
        )
        if template.is_default:
            for existing in self.pipeline_templates.values():
                if existing.tenant_id == tenant_id and existing.is_default:
                    existing.is_default = False
                    existing.updated_at = self._now()
        self.pipeline_templates[template.pipeline_template_id] = template
        return self._serialize(template)

    def get_default_pipeline_template(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        tenant = normalize_tenant_id(tenant_id or self.tenant_id)
        self._ensure_default_pipeline_template(tenant)
        template = next(row for row in self.pipeline_templates.values() if row.tenant_id == tenant and row.is_default)
        return self._serialize(template)

    def _ensure_default_pipeline_template(self, tenant_id: str) -> None:
        if any(row.tenant_id == tenant_id and row.is_default for row in self.pipeline_templates.values()):
            return
        default_stages = [
            {"code": "Applied", "label": "Applied", "sequence": 1, "aliases": ["Applied"], "terminal": False},
            {"code": "Screening", "label": "Screening", "sequence": 2, "aliases": ["Screening"], "terminal": False},
            {"code": "Interview", "label": "Interview", "sequence": 3, "aliases": ["Interview", "Interviewing"], "terminal": False},
            {"code": "Offer", "label": "Offer", "sequence": 4, "aliases": ["Offer", "Offered"], "terminal": False},
            {"code": "Hired", "label": "Hired", "sequence": 5, "aliases": ["Hired"], "terminal": True},
            {"code": "Rejected", "label": "Rejected", "sequence": 6, "aliases": ["Rejected", "Withdrawn"], "terminal": True},
        ]
        template = PipelineTemplate(
            pipeline_template_id=self._new_id(),
            tenant_id=tenant_id,
            name="Default ATS Pipeline",
            stages=default_stages,
            is_default=True,
        )
        self.pipeline_templates[template.pipeline_template_id] = template

    # ---------------------------------------------------------------------
    # Candidate management / pipeline
    # ---------------------------------------------------------------------
    def create_candidate(self, payload: dict[str, Any]) -> dict[str, Any]:
        started = perf_counter()
        with self._lock:
            self._require(payload, ["job_posting_id", "first_name", "last_name", "email", "application_date"])
            posting = self._require_job_posting(payload["job_posting_id"], tenant_id=payload.get("tenant_id"))
            self._authorize(payload, "candidate.manage", department_id=posting.department_id, tenant_id=posting.tenant_id, posting=posting)
            if posting.status not in {"Open", "OnHold"}:
                raise HiringValidationError("candidates can only be created for Open/OnHold job postings")
            source = payload.get("source")
            if source is not None:
                self._validate_value(source, self.CANDIDATE_SOURCES, "source")
            initial_status = self._normalize_candidate_status(payload.get("status", "Applied"))
            if initial_status != "Applied":
                raise HiringValidationError("candidate status must start as Applied")
            for existing in self.candidates.values():
                if existing.tenant_id == posting.tenant_id and existing.job_posting_id == payload["job_posting_id"] and existing.email.lower() == payload["email"].lower():
                    raise HiringValidationError("candidate email must be unique within the job posting")
            pipeline_template = self.get_default_pipeline_template(tenant_id=posting.tenant_id)
            candidate = Candidate(
                candidate_id=self._new_id(),
                tenant_id=posting.tenant_id,
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
                pipeline_template_id=pipeline_template["pipeline_template_id"],
            )
            self.candidates[candidate.candidate_id] = candidate
            self._record_candidate_stage_transition(
                candidate_id=candidate.candidate_id,
                tenant_id=candidate.tenant_id,
                from_status=None,
                to_status=candidate.status,
                changed_by=payload.get("changed_by"),
                reason=payload.get("stage_reason"),
                notes=payload.get("stage_notes"),
            )
            self._emit("CandidateApplied", {
                "tenant_id": candidate.tenant_id,
                "candidate_id": candidate.candidate_id,
                "job_posting_id": candidate.job_posting_id,
                "candidate_email": candidate.email,
            })
        self.observability.track("create_candidate", trace_id=self.observability.trace_id(), started_at=started, success=True, context={"status": 201, "candidate_id": candidate.candidate_id})
        response = self.get_candidate(candidate.candidate_id, tenant_id=candidate.tenant_id)
        self._audit_hiring_mutation("candidate_created", "Candidate", candidate.candidate_id, {}, response, payload=payload)
        return response

    def list_candidates(
        self,
        *,
        job_posting_id: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id or self.tenant_id)
        if job_posting_id is not None:
            self._require_job_posting(job_posting_id, tenant_id=tenant)
        if status is not None:
            status = self._normalize_candidate_status(status)
        if limit is not None and limit < 1:
            raise HiringValidationError("limit must be >= 1")
        rows = [row for row in self.candidates.values() if row.tenant_id == tenant]
        if job_posting_id:
            rows = [row for row in rows if row.job_posting_id == job_posting_id]
        if status:
            rows = [row for row in rows if row.status == status]
        rows.sort(key=lambda row: (row.application_date, row.updated_at, row.candidate_id), reverse=True)
        if cursor is not None:
            cursor_index = next((index for index, row in enumerate(rows) if row.candidate_id == cursor), None)
            if cursor_index is None:
                raise HiringValidationError("cursor does not exist")
            rows = rows[cursor_index + 1:]
        if limit is not None:
            rows = rows[:limit]
        return [self.get_candidate(row.candidate_id, tenant_id=tenant) for row in rows]

    def health_snapshot(self) -> dict[str, Any]:
        return self.observability.health_status(
            checks={
                "requisitions": len(self.requisitions),
                "job_postings": len(self.job_postings),
                "pipeline_templates": len(self.pipeline_templates),
                "candidates": len(self.candidates),
                "candidate_stage_transitions": len(self.candidate_stage_transitions),
                "interviews": len(self.interviews),
                "offers": len(self.offers),
                "scorecards": len(self.scorecards),
            }
        )

    def update_candidate(self, candidate_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id, tenant_id=patch.get("tenant_id"))
        posting = self._require_job_posting(candidate.job_posting_id, tenant_id=candidate.tenant_id)
        self._authorize(patch, "candidate.manage", department_id=posting.department_id, tenant_id=candidate.tenant_id, posting=posting)
        before = self.get_candidate(candidate_id, tenant_id=candidate.tenant_id)
        previous_status = candidate.status

        for key in ["first_name", "last_name", "email", "phone", "resume_url", "source", "source_candidate_id", "source_profile_url"]:
            if key in patch:
                if key == "source" and patch[key] is not None:
                    self._validate_value(patch[key], self.CANDIDATE_SOURCES, "source")
                if key == "email":
                    for existing in self.candidates.values():
                        if existing.tenant_id == candidate.tenant_id and existing.candidate_id != candidate_id and existing.job_posting_id == candidate.job_posting_id and existing.email.lower() == patch[key].lower():
                            raise HiringValidationError("candidate email must be unique within the job posting")
                setattr(candidate, key, patch[key])
        if "application_date" in patch:
            candidate.application_date = self._coerce_date(patch["application_date"], "application_date")
        if "job_posting_id" in patch and patch["job_posting_id"] != candidate.job_posting_id:
            new_job_posting = self._require_job_posting(patch["job_posting_id"], tenant_id=candidate.tenant_id)
            if new_job_posting.status not in {"Open", "OnHold"}:
                raise HiringValidationError("candidates can only be assigned to Open/OnHold job postings")
            for existing in self.candidates.values():
                if existing.tenant_id == candidate.tenant_id and existing.candidate_id != candidate_id and existing.job_posting_id == patch["job_posting_id"] and existing.email.lower() == candidate.email.lower():
                    raise HiringValidationError("candidate email must be unique within the job posting")
            candidate.job_posting_id = patch["job_posting_id"]
        if "status" in patch:
            next_status = self._normalize_candidate_status(patch["status"])
            if next_status != candidate.status and next_status not in self.CANDIDATE_STATUS_FLOW[candidate.status]:
                raise HiringValidationError(f"invalid candidate status transition: {candidate.status} -> {next_status}")
            candidate.status = next_status
        candidate.updated_at = self._now()
        if previous_status != candidate.status:
            self._record_candidate_stage_transition(
                candidate_id=candidate.candidate_id,
                tenant_id=candidate.tenant_id,
                from_status=previous_status,
                to_status=candidate.status,
                changed_by=patch.get("changed_by"),
                reason=patch.get("stage_reason"),
                notes=patch.get("stage_notes"),
            )
            self._emit("CandidateStageChanged", {
                "tenant_id": candidate.tenant_id,
                "candidate_id": candidate.candidate_id,
                "candidate_email": candidate.email,
                "job_title": posting.title,
                "pipeline_stage": self.STATUS_TO_CANONICAL_STAGE[candidate.status],
                "from_status": previous_status,
                "to_status": candidate.status,
            })
        response = self.get_candidate(candidate.candidate_id, tenant_id=candidate.tenant_id)
        self._audit_hiring_mutation("candidate_updated", "Candidate", candidate.candidate_id, before, response, payload=patch)
        return response

    def get_candidate(self, candidate_id: str, tenant_id: str | None = None) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id, tenant_id=tenant_id)
        payload = self._serialize(candidate)
        payload["job_posting"] = self.get_job_posting(candidate.job_posting_id, tenant_id=candidate.tenant_id)
        payload["stage_history"] = self.list_candidate_stage_history(candidate_id, tenant_id=candidate.tenant_id)
        payload["interviews"] = self.list_interviews(candidate_id=candidate_id, tenant_id=candidate.tenant_id)
        payload["offers"] = self.list_offers(candidate_id=candidate_id, tenant_id=candidate.tenant_id)
        payload["pipeline_stage"] = self.STATUS_TO_CANONICAL_STAGE[candidate.status]
        payload["pipeline_template"] = self.get_default_pipeline_template(tenant_id=candidate.tenant_id)
        employee_id = self.hired_candidate_index.get(candidate_id)
        payload["employee_profile"] = self.get_employee_profile(employee_id, tenant_id=candidate.tenant_id) if employee_id else None
        return payload

    def get_candidate_summary(self, candidate_id: str, tenant_id: str | None = None) -> dict[str, Any]:
        candidate = self._require_candidate(candidate_id, tenant_id=tenant_id)
        job_posting = self._require_job_posting(candidate.job_posting_id, tenant_id=candidate.tenant_id)
        return {
            "candidate_id": candidate.candidate_id,
            "tenant_id": candidate.tenant_id,
            "job_posting_id": candidate.job_posting_id,
            "job_posting_title": job_posting.title,
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "email": candidate.email,
            "status": candidate.status,
            "pipeline_stage": self.STATUS_TO_CANONICAL_STAGE[candidate.status],
        }

    def list_candidate_stage_history(self, candidate_id: str, tenant_id: str | None = None) -> list[dict[str, Any]]:
        candidate = self._require_candidate(candidate_id, tenant_id=tenant_id)
        rows = [transition for transition in self.candidate_stage_transitions.values() if transition.tenant_id == candidate.tenant_id and transition.candidate_id == candidate_id]
        rows.sort(key=lambda row: (row.changed_at, row.candidate_stage_transition_id))
        return [self._serialize(row) for row in rows]

    def list_candidate_pipeline_view(
        self,
        *,
        pipeline_stage: str | None = None,
        department_id: str | None = None,
        job_posting_id: str | None = None,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id or self.tenant_id)
        normalized_stage = None
        if pipeline_stage is not None:
            normalized_stage = self.STATUS_TO_CANONICAL_STAGE[self._normalize_candidate_status(pipeline_stage)]
        if job_posting_id is not None:
            self._require_job_posting(job_posting_id, tenant_id=tenant)
        rows: list[dict[str, Any]] = []
        for candidate in self.candidates.values():
            if candidate.tenant_id != tenant:
                continue
            posting = self._require_job_posting(candidate.job_posting_id, tenant_id=tenant)
            interviews = [x for x in self.interviews.values() if x.tenant_id == tenant and x.candidate_id == candidate.candidate_id]
            offers = [x for x in self.offers.values() if x.tenant_id == tenant and x.candidate_id == candidate.candidate_id]
            next_interview = None
            scheduled = sorted((x.scheduled_start for x in interviews if x.status == "Scheduled"), reverse=False)
            if scheduled:
                next_interview = scheduled[0]
            active_offer = sorted(offers, key=lambda row: (row.updated_at, row.offer_id), reverse=True)
            active_offer = active_offer[0] if active_offer else None
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
                "pipeline_stage_normalized": self.STATUS_TO_CANONICAL_STAGE[candidate.status],
                "stage_updated_at": candidate.updated_at.isoformat(),
                "source": candidate.source,
                "source_candidate_id": candidate.source_candidate_id,
                "next_interview_at": next_interview.isoformat() if next_interview else None,
                "interview_count": len(interviews),
                "scorecard_count": len([score for score in self.scorecards.values() if score.tenant_id == tenant and score.candidate_id == candidate.candidate_id]),
                "last_interview_recommendation": self._latest_interview_recommendation(interviews),
                "offer_id": active_offer.offer_id if active_offer else None,
                "offer_status": active_offer.status if active_offer else None,
                "hiring_owner_employee_id": posting.hiring_manager_id,
                "hiring_owner_name": None,
                "hired_employee_id": self.hired_candidate_index.get(candidate.candidate_id),
                "updated_at": candidate.updated_at.isoformat(),
            }
            rows.append(row)
        if normalized_stage:
            rows = [row for row in rows if row["pipeline_stage_normalized"] == normalized_stage]
        if department_id:
            rows = [row for row in rows if row["department_id"] == department_id]
        if job_posting_id:
            rows = [row for row in rows if row["job_posting_id"] == job_posting_id]
        rows.sort(key=lambda row: (row["stage_updated_at"], row["candidate_id"]), reverse=True)
        return rows

    def build_hiring_ui(self, *, pipeline_stage: str | None = None, department_id: str | None = None, job_posting_id: str | None = None) -> dict[str, list[dict[str, Any]]]:
        return {
            "job_postings": self.list_job_postings(department_id=department_id, tenant_id=self.tenant_id),
            "candidate_pipeline": self.list_candidate_pipeline_view(pipeline_stage=pipeline_stage, department_id=department_id, job_posting_id=job_posting_id, tenant_id=self.tenant_id),
        }

    # ---------------------------------------------------------------------
    # Evaluation system + interviews
    # ---------------------------------------------------------------------
    def create_evaluation_form(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require(payload, ["name", "stage", "sections"])
        tenant_id = self._resolve_tenant_id(payload)
        form = EvaluationForm(
            evaluation_form_id=self._new_id(),
            tenant_id=tenant_id,
            name=str(payload["name"]),
            stage=self.STATUS_TO_CANONICAL_STAGE[self._normalize_candidate_status(payload["stage"])],
            sections=list(payload["sections"]),
            is_active=bool(payload.get("is_active", True)),
        )
        self.evaluation_forms[form.evaluation_form_id] = form
        response = self._serialize(form)
        self._audit_hiring_mutation("evaluation_form_created", "EvaluationForm", form.evaluation_form_id, {}, response, payload=payload)
        return response

    def create_interview(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require(payload, ["candidate_id", "interview_type", "scheduled_start", "scheduled_end"])
        candidate = self._require_candidate(payload["candidate_id"], tenant_id=payload.get("tenant_id"))
        posting = self._require_job_posting(candidate.job_posting_id, tenant_id=candidate.tenant_id)
        self._authorize(payload, "interview.manage", department_id=posting.department_id, tenant_id=candidate.tenant_id, posting=posting)
        if candidate.status not in {"Interviewing", "Offered"}:
            raise HiringValidationError("interviews can only be scheduled for Interviewing/Offered candidates")
        self._validate_value(payload["interview_type"], self.INTERVIEW_TYPES, "interview_type")
        scheduled_start = self._coerce_datetime(payload["scheduled_start"], "scheduled_start")
        scheduled_end = self._coerce_datetime(payload["scheduled_end"], "scheduled_end")
        if scheduled_end <= scheduled_start:
            raise HiringValidationError("scheduled_end must be after scheduled_start")
        evaluation_form_id = payload.get("evaluation_form_id")
        if evaluation_form_id:
            self._require_evaluation_form(evaluation_form_id, tenant_id=candidate.tenant_id)
        interview = Interview(
            interview_id=self._new_id(),
            tenant_id=candidate.tenant_id,
            candidate_id=payload["candidate_id"],
            interview_type=payload["interview_type"],
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            location_or_link=payload.get("location_or_link"),
            interviewer_employee_ids=list(payload.get("interviewer_employee_ids", [])),
            evaluation_form_id=evaluation_form_id,
            feedback_summary=payload.get("feedback_summary"),
            recommendation=payload.get("recommendation"),
            status=payload.get("status", "Scheduled"),
        )
        self._validate_value(interview.status, self.INTERVIEW_STATUSES, "status")
        if interview.recommendation is not None:
            self._validate_value(interview.recommendation, self.RECOMMENDATIONS, "recommendation")
        self.interviews[interview.interview_id] = interview
        self._emit("InterviewScheduled", {
            "tenant_id": interview.tenant_id,
            "interview_id": interview.interview_id,
            "candidate_id": interview.candidate_id,
            "candidate_email": candidate.email,
            "scheduled_start": interview.scheduled_start.isoformat(),
            "location": interview.location_or_link,
        })
        response = self.get_interview(interview.interview_id, tenant_id=interview.tenant_id)
        self._audit_hiring_mutation("interview_created", "Interview", interview.interview_id, {}, response, payload=payload)
        return response

    def schedule_interview_with_google_calendar(self, payload: dict[str, Any]) -> dict[str, Any]:
        interview = self.create_interview(payload)
        interview_model = self._require_interview(interview["interview_id"], tenant_id=payload.get("tenant_id"))
        candidate = self._require_candidate(interview_model.candidate_id, tenant_id=interview_model.tenant_id)

        def sync_calendar() -> str:
            if payload.get("simulate_google_failure"):
                raise TimeoutError("google calendar sync timed out")
            return self._new_id()

        try:
            calendar_event_id = self.integration_breakers["google-calendar"].call(
                lambda: run_with_retry(sync_calendar, attempts=3, base_delay=0.05, timeout_seconds=0.2, retryable=lambda exc: isinstance(exc, TimeoutError))
            )
            interview_model.google_calendar_event_id = calendar_event_id
            interview_model.google_calendar_event_link = f"https://calendar.google.com/calendar/event?eid={calendar_event_id}"
            if not interview_model.location_or_link:
                interview_model.location_or_link = f"https://meet.google.com/{calendar_event_id[:3]}-{calendar_event_id[3:6]}-{calendar_event_id[6:9]}"
            interview_model.updated_at = self._now()
            self._emit("InterviewCalendarSynced", {
                "tenant_id": interview_model.tenant_id,
                "interview_id": interview_model.interview_id,
                "candidate_id": interview_model.candidate_id,
                "candidate_email": candidate.email,
                "provider": "GoogleCalendar",
                "external_event_id": calendar_event_id,
            })
        except CircuitBreakerOpenError as exc:
            self.error_logger.log("schedule_interview_with_google_calendar", exc, details={"candidate_id": interview_model.candidate_id})
            self.dead_letters.push("candidate_hiring", "InterviewCalendarSyncDeferred", {"interview_id": interview_model.interview_id, "candidate_id": interview_model.candidate_id}, str(exc))
            interview_model.location_or_link = interview_model.location_or_link or "manual-scheduling-required"
        except Exception as exc:  # noqa: BLE001
            self.error_logger.log("schedule_interview_with_google_calendar", exc, details={"candidate_id": interview_model.candidate_id})
            self.dead_letters.push("candidate_hiring", "InterviewCalendarSyncDeferred", {"interview_id": interview_model.interview_id, "candidate_id": interview_model.candidate_id}, str(exc))
            interview_model.location_or_link = interview_model.location_or_link or "manual-scheduling-required"
        return self.get_interview(interview_model.interview_id, tenant_id=interview_model.tenant_id)

    def update_interview(self, interview_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        interview = self._require_interview(interview_id, tenant_id=patch.get("tenant_id"))
        candidate = self._require_candidate(interview.candidate_id, tenant_id=interview.tenant_id)
        posting = self._require_job_posting(candidate.job_posting_id, tenant_id=interview.tenant_id)
        self._authorize(patch, "interview.manage", department_id=posting.department_id, tenant_id=interview.tenant_id, posting=posting)
        before = self.get_interview(interview_id, tenant_id=interview.tenant_id)
        previous_status = interview.status
        if "candidate_id" in patch and patch["candidate_id"] != interview.candidate_id:
            candidate = self._require_candidate(patch["candidate_id"], tenant_id=interview.tenant_id)
            if candidate.status not in {"Interviewing", "Offered"}:
                raise HiringValidationError("interviews can only be assigned to Interviewing/Offered candidates")
            interview.candidate_id = patch["candidate_id"]
        if "interview_type" in patch:
            self._validate_value(patch["interview_type"], self.INTERVIEW_TYPES, "interview_type")
            interview.interview_type = patch["interview_type"]
        if "evaluation_form_id" in patch:
            evaluation_form_id = patch.get("evaluation_form_id")
            if evaluation_form_id is not None:
                self._require_evaluation_form(evaluation_form_id, tenant_id=interview.tenant_id)
            interview.evaluation_form_id = evaluation_form_id
        for key in ["location_or_link", "feedback_summary", "interviewer_employee_ids"]:
            if key in patch:
                value = patch[key]
                if key == "interviewer_employee_ids":
                    value = list(value or [])
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
        if previous_status != interview.status:
            if interview.status == "Completed":
                self._emit("InterviewCompleted", {"tenant_id": interview.tenant_id, "interview_id": interview.interview_id, "candidate_id": interview.candidate_id})
            elif interview.status == "Cancelled":
                self._emit("InterviewCancelled", {"tenant_id": interview.tenant_id, "interview_id": interview.interview_id, "candidate_id": interview.candidate_id})
            elif interview.status == "NoShow":
                self._emit("InterviewNoShow", {"tenant_id": interview.tenant_id, "interview_id": interview.interview_id, "candidate_id": interview.candidate_id})
        response = self.get_interview(interview.interview_id, tenant_id=interview.tenant_id)
        self._audit_hiring_mutation("interview_updated", "Interview", interview.interview_id, before, response, payload=patch)
        return response

    def create_scorecard(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require(payload, ["interview_id", "overall_rating", "recommendation", "submitted_by"])
        interview = self._require_interview(payload["interview_id"], tenant_id=payload.get("tenant_id"))
        candidate = self._require_candidate(interview.candidate_id, tenant_id=interview.tenant_id)
        self._validate_value(payload["recommendation"], self.RECOMMENDATIONS, "recommendation")
        scorecard = InterviewScorecard(
            scorecard_id=self._new_id(),
            tenant_id=interview.tenant_id,
            interview_id=interview.interview_id,
            candidate_id=candidate.candidate_id,
            evaluation_form_id=payload.get("evaluation_form_id") or interview.evaluation_form_id,
            overall_rating=float(payload["overall_rating"]),
            recommendation=payload["recommendation"],
            competencies=list(payload.get("competencies", [])),
            structured_feedback=dict(payload.get("structured_feedback") or {}),
            submitted_by=str(payload["submitted_by"]),
        )
        self.scorecards[scorecard.scorecard_id] = scorecard
        interview.feedback_summary = scorecard.structured_feedback.get("summary") or interview.feedback_summary
        interview.recommendation = scorecard.recommendation
        interview.updated_at = self._now()
        response = self.get_scorecard(scorecard.scorecard_id, tenant_id=scorecard.tenant_id)
        self._audit_hiring_mutation("scorecard_created", "InterviewScorecard", scorecard.scorecard_id, {}, response, payload=payload)
        return response

    def get_scorecard(self, scorecard_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        scorecard = self._require_scorecard(scorecard_id, tenant_id=tenant_id)
        payload = self._serialize(scorecard)
        payload["candidate"] = self.get_candidate_summary(scorecard.candidate_id, tenant_id=scorecard.tenant_id)
        interview = self._require_interview(scorecard.interview_id, tenant_id=scorecard.tenant_id)
        payload["interview"] = {
            "interview_id": interview.interview_id,
            "candidate_id": interview.candidate_id,
            "interview_type": interview.interview_type,
            "status": interview.status,
            "scheduled_start": interview.scheduled_start.isoformat(),
            "scheduled_end": interview.scheduled_end.isoformat(),
        }
        return payload

    def get_interview(self, interview_id: str, tenant_id: str | None = None) -> dict[str, Any]:
        interview = self._require_interview(interview_id, tenant_id=tenant_id)
        payload = self._serialize(interview)
        payload["candidate"] = self.get_candidate_summary(interview.candidate_id, tenant_id=interview.tenant_id)
        payload["scorecards"] = [
            {
                "scorecard_id": score.scorecard_id,
                "overall_rating": score.overall_rating,
                "recommendation": score.recommendation,
                "submitted_by": score.submitted_by,
                "submitted_at": score.submitted_at.isoformat(),
            }
            for score in self.scorecards.values()
            if score.tenant_id == interview.tenant_id and score.interview_id == interview.interview_id
        ]
        return payload

    def list_interviews(self, *, candidate_id: str | None = None, status: str | None = None, limit: int | None = None, cursor: str | None = None, tenant_id: str | None = None) -> list[dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id or self.tenant_id)
        if candidate_id is not None:
            self._require_candidate(candidate_id, tenant_id=tenant)
        if status is not None:
            self._validate_value(status, self.INTERVIEW_STATUSES, "status")
        if limit is not None and limit < 1:
            raise HiringValidationError("limit must be >= 1")
        rows = [row for row in self.interviews.values() if row.tenant_id == tenant]
        if candidate_id:
            rows = [row for row in rows if row.candidate_id == candidate_id]
        if status:
            rows = [row for row in rows if row.status == status]
        rows.sort(key=lambda row: (row.scheduled_start, row.updated_at, row.interview_id), reverse=False)
        if cursor is not None:
            cursor_index = next((index for index, row in enumerate(rows) if row.interview_id == cursor), None)
            if cursor_index is None:
                raise HiringValidationError("cursor does not exist")
            rows = rows[cursor_index + 1:]
        if limit is not None:
            rows = rows[:limit]
        return [self.get_interview(row.interview_id, tenant_id=tenant) for row in rows]

    # ---------------------------------------------------------------------
    # Offer management and onboarding handoff
    # ---------------------------------------------------------------------
    def create_offer(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require(payload, ["candidate_id", "salary_amount", "currency", "start_date", "created_by"])
        candidate = self._require_candidate(payload["candidate_id"], tenant_id=payload.get("tenant_id"))
        posting = self._require_job_posting(candidate.job_posting_id, tenant_id=candidate.tenant_id)
        self._authorize(payload, "offer.manage", department_id=posting.department_id, tenant_id=candidate.tenant_id, posting=posting)
        if candidate.status not in {"Interviewing", "Offered"}:
            raise HiringValidationError("offers can only be created for Interviewing/Offered candidates")
        offer = Offer(
            offer_id=self._new_id(),
            tenant_id=candidate.tenant_id,
            candidate_id=candidate.candidate_id,
            job_posting_id=candidate.job_posting_id,
            title=payload.get("title") or posting.title,
            salary_amount=float(payload["salary_amount"]),
            currency=str(payload["currency"]),
            start_date=self._coerce_date(payload["start_date"], "start_date"),
            status=payload.get("status", "Draft"),
            compensation_summary=dict(payload.get("compensation_summary") or {}),
            created_by=str(payload["created_by"]),
            status_reason=payload.get("status_reason"),
        )
        self._validate_value(offer.status, self.OFFER_STATUSES, "status")
        self.offers[offer.offer_id] = offer
        candidate.current_offer_id = offer.offer_id
        if candidate.status == "Interviewing":
            self.update_candidate(candidate.candidate_id, {"tenant_id": candidate.tenant_id, "status": "Offered", "changed_by": payload.get("changed_by") or payload.get("created_by"), "stage_reason": "offer drafted"})
        response = self.get_offer(offer.offer_id, tenant_id=offer.tenant_id)
        self._audit_hiring_mutation("offer_created", "Offer", offer.offer_id, {}, response, payload=payload)
        self._emit("OfferCreated", {"tenant_id": offer.tenant_id, "offer_id": offer.offer_id, "candidate_id": candidate.candidate_id, "candidate_email": candidate.email})
        return response

    def submit_offer_for_approval(self, offer_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        patch = payload or {}
        offer = self._require_offer(offer_id, tenant_id=patch.get("tenant_id"))
        candidate = self._require_candidate(offer.candidate_id, tenant_id=offer.tenant_id)
        posting = self._require_job_posting(candidate.job_posting_id, tenant_id=offer.tenant_id)
        self._authorize(patch, "offer.manage", department_id=posting.department_id, tenant_id=offer.tenant_id, posting=posting)
        before = self.get_offer(offer_id, tenant_id=offer.tenant_id)
        if not offer.approval_workflow_id:
            workflow = self.workflow_service.start_workflow(
                tenant_id=offer.tenant_id,
                definition_code="offer_approval",
                source_service="hiring-service",
                subject_type="Offer",
                subject_id=offer.offer_id,
                actor_id=str(patch.get("changed_by") or offer.created_by),
                actor_type="user",
                context={"approver_assignee": self._approval_assignee(patch, default_role="Manager"), "escalation_assignee": "role:Admin"},
            )
            offer.approval_workflow_id = workflow["workflow_id"]
        offer.status = "PendingApproval"
        offer.updated_at = self._now()
        response = self.get_offer(offer.offer_id, tenant_id=offer.tenant_id)
        self._audit_hiring_mutation("offer_submitted", "Offer", offer_id, before, response, payload=patch)
        self._emit("OfferApprovalRequested", {"tenant_id": offer.tenant_id, "offer_id": offer.offer_id, "candidate_id": offer.candidate_id, "candidate_email": candidate.email})
        return response

    def approve_offer(self, offer_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        patch = payload or {}
        offer = self._require_offer(offer_id, tenant_id=patch.get("tenant_id"))
        candidate = self._require_candidate(offer.candidate_id, tenant_id=offer.tenant_id)
        posting = self._require_job_posting(candidate.job_posting_id, tenant_id=offer.tenant_id)
        self._authorize(patch, "offer.approve", department_id=posting.department_id, tenant_id=offer.tenant_id, posting=posting)
        before = self.get_offer(offer_id, tenant_id=offer.tenant_id)
        if not offer.approval_workflow_id:
            self.submit_offer_for_approval(offer_id, patch)
        workflow = self._approve_workflow(offer.approval_workflow_id, tenant_id=offer.tenant_id, payload=patch, comment="Offer approved")
        if workflow.get("metadata", {}).get("terminal_result") != "approved":
            raise HiringValidationError("offer approval workflow did not complete")
        offer.status = "Approved"
        offer.approved_at = self._now()
        offer.updated_at = self._now()
        response = self.get_offer(offer.offer_id, tenant_id=offer.tenant_id)
        self._audit_hiring_mutation("offer_approved", "Offer", offer_id, before, response, payload=patch)
        self._emit("OfferApproved", {"tenant_id": offer.tenant_id, "offer_id": offer.offer_id, "candidate_id": offer.candidate_id, "candidate_email": candidate.email})
        return response

    def send_offer(self, offer_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        patch = payload or {}
        offer = self._require_offer(offer_id, tenant_id=patch.get("tenant_id"))
        candidate = self._require_candidate(offer.candidate_id, tenant_id=offer.tenant_id)
        if offer.status not in {"Approved", "Sent"}:
            raise HiringValidationError("offer must be approved before sending")
        before = self.get_offer(offer_id, tenant_id=offer.tenant_id)
        offer.status = "Sent"
        offer.sent_at = self._now()
        offer.updated_at = self._now()
        response = self.get_offer(offer.offer_id, tenant_id=offer.tenant_id)
        self._audit_hiring_mutation("offer_sent", "Offer", offer_id, before, response, payload=patch)
        self._emit("OfferSent", {"tenant_id": offer.tenant_id, "offer_id": offer.offer_id, "candidate_id": offer.candidate_id, "candidate_email": candidate.email})
        return response

    def accept_offer(self, offer_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        patch = payload or {}
        offer = self._require_offer(offer_id, tenant_id=patch.get("tenant_id"))
        candidate = self._require_candidate(offer.candidate_id, tenant_id=offer.tenant_id)
        if offer.status not in {"Approved", "Sent"}:
            raise HiringValidationError("offer must be approved or sent before acceptance")
        before = self.get_offer(offer_id, tenant_id=offer.tenant_id)
        offer.status = "Accepted"
        offer.accepted_at = self._now()
        offer.updated_at = self._now()
        response = self.get_offer(offer.offer_id, tenant_id=offer.tenant_id)
        self._audit_hiring_mutation("offer_accepted", "Offer", offer_id, before, response, payload=patch)
        self._emit("OfferAccepted", {"tenant_id": offer.tenant_id, "offer_id": offer.offer_id, "candidate_id": offer.candidate_id, "candidate_email": candidate.email})
        return response

    def decline_offer(self, offer_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        patch = payload or {}
        offer = self._require_offer(offer_id, tenant_id=patch.get("tenant_id"))
        candidate = self._require_candidate(offer.candidate_id, tenant_id=offer.tenant_id)
        before = self.get_offer(offer_id, tenant_id=offer.tenant_id)
        offer.status = "Declined"
        offer.declined_at = self._now()
        offer.status_reason = patch.get("reason")
        offer.updated_at = self._now()
        response = self.get_offer(offer.offer_id, tenant_id=offer.tenant_id)
        self._audit_hiring_mutation("offer_declined", "Offer", offer_id, before, response, payload=patch)
        self._emit("OfferDeclined", {"tenant_id": offer.tenant_id, "offer_id": offer.offer_id, "candidate_id": offer.candidate_id, "candidate_email": candidate.email})
        return response

    def get_offer(self, offer_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        offer = self._require_offer(offer_id, tenant_id=tenant_id)
        payload = self._serialize(offer)
        payload["candidate"] = self.get_candidate_summary(offer.candidate_id, tenant_id=offer.tenant_id)
        payload["workflow"] = self.workflow_service.get_instance(offer.approval_workflow_id, tenant_id=offer.tenant_id) if offer.approval_workflow_id else None
        return payload

    def list_offers(self, *, candidate_id: str | None = None, tenant_id: str | None = None) -> list[dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id or self.tenant_id)
        rows = [row for row in self.offers.values() if row.tenant_id == tenant]
        if candidate_id is not None:
            rows = [row for row in rows if row.candidate_id == candidate_id]
        rows.sort(key=lambda row: (row.updated_at, row.offer_id), reverse=True)
        return [self.get_offer(row.offer_id, tenant_id=tenant) for row in rows]

    def mark_candidate_hired(self, candidate_id: str, employee_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = employee_payload or {}
        candidate = self._require_candidate(candidate_id, tenant_id=payload.get("tenant_id"))
        posting = self._require_job_posting(candidate.job_posting_id, tenant_id=candidate.tenant_id)
        self._authorize(payload, "hire.approve", department_id=posting.department_id, tenant_id=candidate.tenant_id, posting=posting)
        if candidate.status != "Offered":
            raise HiringValidationError("candidate can only be hired from Offered status")
        active_offer = self._current_offer_for_candidate(candidate.candidate_id, tenant_id=candidate.tenant_id)
        if active_offer and active_offer.status not in {"Accepted", "Approved", "Sent"}:
            raise HiringValidationError("candidate offer must be approved or accepted before hire")
        approver_id = str(payload.get("changed_by") or "role:Admin")
        approver_role = str(payload.get("approver_role") or payload.get("actor_role") or "Admin")
        if not candidate.hire_workflow_id:
            workflow = self.workflow_service.start_workflow(
                tenant_id=candidate.tenant_id,
                definition_code="candidate_hiring_approval",
                source_service="hiring-service",
                subject_type="Candidate",
                subject_id=candidate_id,
                actor_id=approver_id,
                actor_type="user",
                context={"approver_assignee": self._approval_assignee(payload, default_role=approver_role), "escalation_assignee": "role:Admin"},
            )
            candidate.hire_workflow_id = workflow["workflow_id"]
        workflow = self._approve_workflow(candidate.hire_workflow_id, tenant_id=candidate.tenant_id, payload=payload, comment="Candidate hire approved")
        if workflow.get("metadata", {}).get("terminal_result") != "approved":
            raise HiringValidationError("candidate hiring workflow did not complete")
        before = self.get_candidate(candidate_id, tenant_id=candidate.tenant_id)
        employee_profile = self._upsert_employee_profile_for_candidate(candidate, payload)
        candidate.status = "Hired"
        candidate.updated_at = self._now()
        self._record_candidate_stage_transition(candidate_id=candidate_id, tenant_id=candidate.tenant_id, from_status="Offered", to_status="Hired", changed_by=payload.get("changed_by"), reason="candidate accepted offer", notes=None)
        self._emit("CandidateStageChanged", {"tenant_id": candidate.tenant_id, "candidate_id": candidate_id, "candidate_email": candidate.email, "job_title": posting.title, "pipeline_stage": "Hired", "from_status": "Offered", "to_status": "Hired"})
        self._emit("CandidateHired", {"tenant_id": candidate.tenant_id, "candidate_id": candidate_id, "job_posting_id": candidate.job_posting_id, "employee_id": employee_profile.employee_id, "candidate_email": candidate.email})
        self._emit("OnboardingHandoffReady", {"tenant_id": candidate.tenant_id, "candidate_id": candidate_id, "employee_id": employee_profile.employee_id, "onboarding_status": employee_profile.onboarding_status})
        response = self.get_candidate(candidate_id, tenant_id=candidate.tenant_id)
        self._audit_hiring_mutation("candidate_hired", "Candidate", candidate_id, before, response, payload=payload)
        return response

    def _upsert_employee_profile_for_candidate(self, candidate: Candidate, payload: dict[str, Any]) -> EmployeeProfile:
        posting = self._require_job_posting(candidate.job_posting_id, tenant_id=candidate.tenant_id)
        existing_employee_id = self.hired_candidate_index.get(candidate.candidate_id)
        now = self._now()
        hire_date = self._coerce_date(payload.get("hire_date", now.date().isoformat()), "hire_date")
        employee_id = str(payload.get("employee_id") or existing_employee_id or self._new_id())
        for employee in self.employee_profiles.values():
            if employee.tenant_id == candidate.tenant_id and employee.employee_id != employee_id and employee.email.lower() == candidate.email.lower():
                raise HiringValidationError("employee email must be unique")
        employee_payload = {
            "tenant_id": candidate.tenant_id,
            "employee_id": employee_id,
            "employee_number": payload.get("employee_number"),
            "first_name": payload.get("first_name", candidate.first_name),
            "last_name": payload.get("last_name", candidate.last_name),
            "email": payload.get("email", candidate.email),
            "phone": payload.get("phone", candidate.phone),
            "hire_date": hire_date.isoformat(),
            "employment_type": payload.get("employment_type", posting.employment_type),
            "status": payload.get("status", "Draft"),
            "department_id": payload.get("department_id", posting.department_id),
            "role_id": payload.get("role_id", posting.role_id),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        employee_record = self.employee_service.create_employee_record(employee_payload)
        if existing_employee_id and existing_employee_id in self.employee_profiles:
            employee = self.employee_profiles[existing_employee_id]
            employee.department_id = employee_record["department_id"]
            employee.role_id = employee_record["role_id"]
            employee.first_name = employee_record["first_name"]
            employee.last_name = employee_record["last_name"]
            employee.email = employee_record["email"]
            employee.phone = employee_record["phone"]
            employee.employment_type = employee_record["employment_type"]
            employee.hire_date = hire_date
            employee.status = employee_record["status"]
            employee.employee_service_payload = employee_record
            employee.onboarding_status = "HandoffCompleted"
            employee.updated_at = now
            return employee
        employee = EmployeeProfile(
            employee_id=employee_record["employee_id"],
            tenant_id=candidate.tenant_id,
            candidate_id=candidate.candidate_id,
            job_posting_id=posting.job_posting_id,
            department_id=employee_record["department_id"],
            role_id=employee_record["role_id"],
            first_name=employee_record["first_name"],
            last_name=employee_record["last_name"],
            email=employee_record["email"],
            phone=employee_record["phone"],
            employment_type=employee_record["employment_type"],
            hire_date=hire_date,
            status=employee_record["status"],
            employee_service_payload=employee_record,
            onboarding_status="HandoffCompleted",
            created_at=now,
            updated_at=now,
        )
        self.employee_profiles[employee.employee_id] = employee
        self.hired_candidate_index[candidate.candidate_id] = employee.employee_id
        return employee

    def get_employee_profile(self, employee_id: str, tenant_id: str | None = None) -> dict[str, Any]:
        employee = self.employee_profiles.get(employee_id)
        if employee is None:
            raise HiringValidationError("employee does not exist")
        assert_tenant_access(employee.tenant_id, normalize_tenant_id(tenant_id or self.tenant_id))
        payload = self._serialize(employee)
        payload["candidate"] = self.get_candidate_summary(employee.candidate_id, tenant_id=employee.tenant_id)
        payload["job_posting"] = self.get_job_posting(employee.job_posting_id, tenant_id=employee.tenant_id)
        payload["employee_service_record"] = self.employee_service.get_employee_record(tenant_id=employee.tenant_id, employee_id=employee.employee_id)
        return payload

    def list_employee_profiles(self, *, candidate_id: str | None = None, tenant_id: str | None = None) -> list[dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id or self.tenant_id)
        rows = [row for row in self.employee_profiles.values() if row.tenant_id == tenant]
        if candidate_id is not None:
            rows = [row for row in rows if row.candidate_id == candidate_id]
        rows.sort(key=lambda row: (row.hire_date, row.updated_at, row.employee_id), reverse=True)
        return [self.get_employee_profile(row.employee_id, tenant_id=tenant) for row in rows]

    # ---------------------------------------------------------------------
    # External imports
    # ---------------------------------------------------------------------
    def import_candidates_from_linkedin(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._require(payload, ["job_posting_id", "candidates"])
        posting = self._require_job_posting(payload["job_posting_id"], tenant_id=payload.get("tenant_id"))
        self._authorize(payload, "candidate.manage", department_id=posting.department_id, tenant_id=posting.tenant_id, posting=posting)
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
            duplicate = any(c.tenant_id == posting.tenant_id and c.job_posting_id == posting.job_posting_id and c.email.lower() == email.lower() for c in self.candidates.values())
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
                "tenant_id": posting.tenant_id,
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
            self._emit("CandidateImported", {"tenant_id": posting.tenant_id, "candidate_id": imported_candidate["candidate_id"], "job_posting_id": payload["job_posting_id"], "provider": "LinkedIn", "source_candidate_id": source_candidate_id})
        self._emit("LinkedInCandidatesImported", {"tenant_id": posting.tenant_id, "job_posting_id": payload["job_posting_id"], "imported_count": len(imported), "skipped_count": len(skipped)})
        return {"job_posting_id": payload["job_posting_id"], "provider": "LinkedIn", "imported": imported, "skipped": skipped}

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    def _audit_hiring_mutation(self, action: str, entity: str, entity_id: str, before: dict[str, Any], after: dict[str, Any], *, payload: dict[str, Any] | None = None) -> None:
        patch = payload or {}
        trace_id = self.observability.trace_id()
        tenant_id = normalize_tenant_id(after.get("tenant_id") if isinstance(after, dict) and after.get("tenant_id") else before.get("tenant_id") if isinstance(before, dict) and before.get("tenant_id") else patch.get("tenant_id") or self.tenant_id)
        actor = self._actor_context(patch)
        self.observability.logger.audit(action, trace_id=trace_id, actor=actor, entity=entity, entity_id=entity_id, context={"tenant_id": tenant_id, "before": before, "after": after})
        emit_audit_record(service_name="hiring-service", tenant_id=tenant_id, actor=actor, action=action, entity=entity, entity_id=entity_id, before=before, after=after, trace_id=trace_id, source={"capability": self._capability_for_action(action)})

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        event_payload = dict(payload)
        tenant_id = normalize_tenant_id(event_payload.get("tenant_id") or self.tenant_id)
        event_payload.setdefault("tenant_id", tenant_id)
        if event_payload.get("candidate_stage_transition_id"):
            idempotency_key = str(event_payload["candidate_stage_transition_id"])
        elif event_payload.get("offer_id"):
            idempotency_key = str(event_payload["offer_id"])
        elif event_payload.get("requisition_id"):
            idempotency_key = str(event_payload["requisition_id"])
        elif event_payload.get("interview_id"):
            idempotency_key = str(event_payload["interview_id"])
        elif event_payload.get("employee_profile_id"):
            idempotency_key = str(event_payload["employee_profile_id"])
        elif event_payload.get("candidate_id") and event_payload.get("from_status") and event_payload.get("to_status"):
            idempotency_key = f"{event_payload['candidate_id']}:{event_payload['from_status']}:{event_payload['to_status']}"
        elif event_payload.get("candidate_id"):
            idempotency_key = str(event_payload["candidate_id"])
        elif event_payload.get("job_posting_id"):
            idempotency_key = str(event_payload["job_posting_id"])
        else:
            idempotency_key = self._new_id()
        self.outbox.tenant_id = tenant_id
        event = self.outbox.enqueue(legacy_event_name=event_type, data=event_payload, idempotency_key=idempotency_key, metadata={"occurred_at": self._now().isoformat()})
        self.outbox.dispatch_pending(self.events.append)
        event["payload"] = event_payload
        event["occurred_at"] = self._now().isoformat()
        event["legacy_event_type"] = event_type
        try:
            self.notification_service.ingest_event({"event_name": event_type, "tenant_id": tenant_id, "data": event_payload})
        except NotificationServiceError:
            pass

    def _approval_assignee(self, payload: dict[str, Any], *, default_role: str) -> str:
        approver_assignee = payload.get("approver_assignee")
        if approver_assignee:
            return str(approver_assignee)
        if payload.get("approver_id"):
            return str(payload["approver_id"])
        role = str(payload.get("approver_role") or default_role)
        return f"role:{role}"

    def _approve_workflow(self, workflow_id: str | None, *, tenant_id: str, payload: dict[str, Any], comment: str) -> dict[str, Any]:
        if workflow_id is None:
            raise HiringValidationError("approval workflow is required")
        try:
            actor_role = payload.get("actor_role") or payload.get("approver_role") or "Admin"
            actor_id = str(payload.get("changed_by") or payload.get("actor_id") or payload.get("approver_assignee") or f"role:{actor_role}")
            return self.workflow_service.approve_step(workflow_id, tenant_id=tenant_id, actor_id=actor_id, actor_type=str(payload.get("actor_type") or "user"), actor_role=actor_role, comment=comment)
        except WorkflowServiceError as exc:
            raise HiringValidationError(exc.message) from exc

    def _normalize_hiring_plan(self, value: Any) -> dict[str, Any]:
        plan = dict(value or {})
        if "headcount" not in plan:
            plan["headcount"] = 1
        if "must_have_skills" in plan and not isinstance(plan["must_have_skills"], list):
            raise HiringValidationError("hiring_plan.must_have_skills must be a list")
        return plan

    def _normalize_pipeline_stage_definition(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise HiringValidationError("each pipeline stage must be an object")
        code = self.STATUS_TO_CANONICAL_STAGE[self._normalize_candidate_status(value.get("code") or value.get("label"))]
        aliases = [str(alias) for alias in value.get("aliases") or [code]]
        return {
            "code": code,
            "label": str(value.get("label") or code),
            "sequence": int(value.get("sequence") or 0),
            "aliases": aliases,
            "terminal": bool(value.get("terminal", code in {"Hired", "Rejected"})),
        }

    def _normalize_candidate_status(self, value: str) -> str:
        status = self.CANDIDATE_STATUS_ALIASES.get(str(value), str(value))
        self._validate_value(status, self.CANDIDATE_STATUSES, "status")
        return status

    def _serialize(self, instance: Any) -> dict[str, Any]:
        payload = asdict(instance)
        for key, value in list(payload.items()):
            if isinstance(value, (datetime, date)):
                payload[key] = value.isoformat()
        return payload

    def _resolve_tenant_id(self, payload: dict[str, Any] | None) -> str:
        return normalize_tenant_id((payload or {}).get("tenant_id") or self.tenant_id)

    def _actor_context(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        patch = payload or {}
        return {
            "id": str(patch.get("changed_by") or patch.get("actor_id") or "system"),
            "type": str(patch.get("actor_type") or ("user" if patch.get("changed_by") or patch.get("actor_id") else "system")),
            "role": patch.get("actor_role") or patch.get("approver_role"),
            "department_id": patch.get("department_id"),
        }

    def _authorize(self, payload: dict[str, Any] | None, action: str, *, department_id: str | None, tenant_id: str, posting: JobPosting | None = None) -> None:
        actor = self._actor_context(payload)
        actor_tenant = normalize_tenant_id((payload or {}).get("tenant_id") or tenant_id)
        assert_tenant_access(tenant_id, actor_tenant)
        role = str(actor.get("role") or "Admin")
        capabilities = self.ROLE_CAPABILITIES.get(role, set())
        if "*" in capabilities or action in capabilities:
            if role in {"Manager", "HiringManager"}:
                actor_department = (payload or {}).get("department_id")
                if actor_department and department_id and actor_department != department_id:
                    raise PermissionError("TENANT_SCOPE_VIOLATION")
            if role == "Recruiter" and action in {"requisition.approve", "offer.approve", "hire.approve"}:
                raise PermissionError("TENANT_SCOPE_VIOLATION")
            if role == "Recruiter" and posting is not None and posting.recruiter_ids:
                actor_id = actor.get("id")
                if actor_id and actor_id != "system" and actor_id not in posting.recruiter_ids:
                    raise PermissionError("TENANT_SCOPE_VIOLATION")
            return
        raise PermissionError("TENANT_SCOPE_VIOLATION")

    def _capability_for_action(self, action: str) -> str:
        if action.startswith("requisition") or action.startswith("job_posting"):
            return "CAP-HIR-001"
        return "CAP-HIR-002"

    def _candidate_count(self, job_posting_id: str, *, tenant_id: str) -> int:
        return sum(1 for candidate in self.candidates.values() if candidate.tenant_id == tenant_id and candidate.job_posting_id == job_posting_id)

    def _current_offer_for_candidate(self, candidate_id: str, *, tenant_id: str) -> Offer | None:
        offers = [offer for offer in self.offers.values() if offer.tenant_id == tenant_id and offer.candidate_id == candidate_id]
        if not offers:
            return None
        offers.sort(key=lambda row: (row.updated_at, row.offer_id), reverse=True)
        return offers[0]

    def _latest_interview_recommendation(self, interviews: list[Interview]) -> str | None:
        recommended = [row for row in interviews if row.recommendation]
        if not recommended:
            return None
        recommended.sort(key=lambda row: (row.updated_at, row.interview_id), reverse=True)
        return recommended[0].recommendation

    def _record_candidate_stage_transition(self, *, candidate_id: str, tenant_id: str, from_status: str | None, to_status: str, changed_by: str | None, reason: str | None, notes: str | None) -> CandidateStageTransition:
        transition = CandidateStageTransition(candidate_stage_transition_id=self._new_id(), tenant_id=tenant_id, candidate_id=candidate_id, from_status=from_status, to_status=to_status, changed_at=self._now(), changed_by=changed_by, reason=reason, notes=notes)
        self.candidate_stage_transitions[transition.candidate_stage_transition_id] = transition
        after = self._serialize(transition)
        self._audit_hiring_mutation("candidate_stage_transition_recorded", "CandidateStageTransition", transition.candidate_stage_transition_id, {}, after, payload={"tenant_id": tenant_id, "changed_by": changed_by})
        self._emit("CandidateStageTransitionRecorded", {"tenant_id": tenant_id, "candidate_stage_transition_id": transition.candidate_stage_transition_id, "candidate_id": candidate_id, "from_status": from_status, "to_status": to_status})
        return transition

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

    def _require_requisition(self, requisition_id: str, *, tenant_id: str | None = None) -> JobRequisition:
        requisition = self.requisitions.get(requisition_id)
        if not requisition:
            raise HiringValidationError("requisition_id does not exist")
        assert_tenant_access(requisition.tenant_id, normalize_tenant_id(tenant_id or requisition.tenant_id))
        return requisition

    def _require_job_posting(self, job_posting_id: str, *, tenant_id: str | None = None) -> JobPosting:
        posting = self.job_postings.get(job_posting_id)
        if not posting:
            raise HiringValidationError("job_posting_id does not exist")
        assert_tenant_access(posting.tenant_id, normalize_tenant_id(tenant_id or posting.tenant_id))
        return posting

    def _require_candidate(self, candidate_id: str, *, tenant_id: str | None = None) -> Candidate:
        candidate = self.candidates.get(candidate_id)
        if not candidate:
            raise HiringValidationError("candidate_id does not exist")
        assert_tenant_access(candidate.tenant_id, normalize_tenant_id(tenant_id or candidate.tenant_id))
        return candidate

    def _require_evaluation_form(self, evaluation_form_id: str, *, tenant_id: str | None = None) -> EvaluationForm:
        form = self.evaluation_forms.get(evaluation_form_id)
        if not form:
            raise HiringValidationError("evaluation_form_id does not exist")
        assert_tenant_access(form.tenant_id, normalize_tenant_id(tenant_id or form.tenant_id))
        return form

    def _require_interview(self, interview_id: str, *, tenant_id: str | None = None) -> Interview:
        interview = self.interviews.get(interview_id)
        if not interview:
            raise HiringValidationError("interview_id does not exist")
        assert_tenant_access(interview.tenant_id, normalize_tenant_id(tenant_id or interview.tenant_id))
        return interview

    def _require_scorecard(self, scorecard_id: str, *, tenant_id: str | None = None) -> InterviewScorecard:
        scorecard = self.scorecards.get(scorecard_id)
        if not scorecard:
            raise HiringValidationError("scorecard_id does not exist")
        assert_tenant_access(scorecard.tenant_id, normalize_tenant_id(tenant_id or scorecard.tenant_id))
        return scorecard

    def _require_offer(self, offer_id: str, *, tenant_id: str | None = None) -> Offer:
        offer = self.offers.get(offer_id)
        if not offer:
            raise HiringValidationError("offer_id does not exist")
        assert_tenant_access(offer.tenant_id, normalize_tenant_id(tenant_id or offer.tenant_id))
        return offer
