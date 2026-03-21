from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol
from uuid import uuid4

from api_contract import pagination_payload
from event_contract import (
    EventContractError,
    EventRegistry,
    emit_canonical_event,
    ensure_event_contract,
    legacy_event_name_for,
)
from resilience import DeadLetterQueue, Observability
from tenant_support import assert_tenant_access, normalize_tenant_id


class NotificationServiceError(Exception):
    def __init__(self, code: str, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


class NotificationChannel(str, Enum):
    EMAIL = "Email"
    SMS = "SMS"
    PUSH = "Push"
    IN_APP = "InApp"


class NotificationStatus(str, Enum):
    QUEUED = "Queued"
    SENT = "Sent"
    FAILED = "Failed"
    SUPPRESSED = "Suppressed"


class DeliveryOutcome(str, Enum):
    SENT = "Sent"
    FAILED = "Failed"
    DEFERRED = "Deferred"
    SUPPRESSED = "Suppressed"


@dataclass
class TenantNotificationConfig:
    tenant_id: str
    feature_flags: dict[str, bool] = field(default_factory=dict)
    leave_policy_refs: list[str] = field(default_factory=list)
    payroll_rule_refs: list[str] = field(default_factory=list)
    locale: str = "en-US"
    legal_entity: str = "SME HRMS"
    enabled_locations: list[str] = field(default_factory=list)
    notification_defaults: dict[str, dict[str, Any]] = field(default_factory=dict)
    template_overrides: dict[str, dict[str, str | None]] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NotificationTemplate:
    template_id: str
    tenant_id: str
    code: str
    channel: NotificationChannel
    subject_template: str | None
    body_template: str
    topic_code: str
    locale: str = "en-US"
    status: str = "Active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NotificationPreference:
    preference_id: str
    tenant_id: str
    subject_type: str
    subject_id: str
    topic_code: str
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    in_app_enabled: bool = True
    quiet_hours: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DeliveryAttempt:
    delivery_attempt_id: str
    tenant_id: str
    message_id: str
    provider_name: str
    attempt_number: int
    attempted_at: datetime
    outcome: DeliveryOutcome
    response_code: str | None = None
    response_message: str | None = None
    provider_message_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NotificationMessage:
    message_id: str
    tenant_id: str
    template_id: str | None
    template_code: str | None
    event_name: str | None
    event_type: str | None
    recipient: str
    subject_type: str
    subject_id: str
    topic_code: str
    channel: NotificationChannel
    destination: str
    payload: dict[str, Any]
    subject_text: str | None
    body_text: str
    status: NotificationStatus
    queued_at: datetime
    sent_at: datetime | None
    delivered_at: datetime | None
    failed_at: datetime | None
    failure_reason: str | None
    read_at: datetime | None
    retry_count: int
    last_attempt_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class EventNotificationPlan:
    template_code: str
    subject_type: str
    subject_id_field: str
    topic_code: str
    channels: tuple[NotificationChannel, ...]
    destination_field: str | None = None


@dataclass
class DeliveryResult:
    outcome: DeliveryOutcome
    response_code: str
    response_message: str
    provider_message_id: str | None = None
    retryable: bool = False


class DeliveryProvider(Protocol):
    provider_name: str
    channel: NotificationChannel

    def deliver(self, message: NotificationMessage, attempt_number: int) -> DeliveryResult:
        ...


class InAppDeliveryProvider:
    provider_name = "inbox"
    channel = NotificationChannel.IN_APP

    def deliver(self, message: NotificationMessage, attempt_number: int) -> DeliveryResult:
        return DeliveryResult(
            outcome=DeliveryOutcome.SENT,
            response_code="202",
            response_message="in-app notification persisted",
            provider_message_id=f"inapp-{message.message_id}",
        )


class EmailDeliveryProvider:
    provider_name = "mock-email-pipeline"
    channel = NotificationChannel.EMAIL

    def deliver(self, message: NotificationMessage, attempt_number: int) -> DeliveryResult:
        transient_failures = int(message.payload.get("simulate_email_failures", 0) or 0)
        permanent_failure = bool(message.payload.get("force_email_failure")) or str(message.destination).startswith("fail:")

        if permanent_failure:
            return DeliveryResult(
                outcome=DeliveryOutcome.FAILED,
                response_code="550",
                response_message="email delivery rejected by provider",
                retryable=False,
            )

        if transient_failures >= attempt_number:
            return DeliveryResult(
                outcome=DeliveryOutcome.DEFERRED,
                response_code="429",
                response_message="email provider rate limited request",
                retryable=True,
            )

        return DeliveryResult(
            outcome=DeliveryOutcome.SENT,
            response_code="202",
            response_message="email accepted for delivery",
            provider_message_id=f"email-{message.message_id}-{attempt_number}",
        )


EVENT_NOTIFICATION_PLANS: dict[str, tuple[EventNotificationPlan, ...]] = {
    "LeaveRequestSubmitted": (
        EventNotificationPlan(
            template_code="leave.submitted.approver",
            subject_type="Employee",
            subject_id_field="approver_employee_id",
            destination_field="approver_email",
            topic_code="leave.submission",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "LeaveRequestApproved": (
        EventNotificationPlan(
            template_code="leave.approved.employee",
            subject_type="Employee",
            subject_id_field="employee_id",
            destination_field="employee_email",
            topic_code="leave.approval",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "LeaveRequestRejected": (
        EventNotificationPlan(
            template_code="leave.rejected.employee",
            subject_type="Employee",
            subject_id_field="employee_id",
            destination_field="employee_email",
            topic_code="leave.rejection",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "LeaveRequestCancelled": (
        EventNotificationPlan(
            template_code="leave.cancelled.employee",
            subject_type="Employee",
            subject_id_field="employee_id",
            destination_field="employee_email",
            topic_code="leave.cancellation",
            channels=(NotificationChannel.IN_APP,),
        ),
    ),
    "AttendanceCaptured": (
        EventNotificationPlan(
            template_code="attendance.captured.employee",
            subject_type="Employee",
            subject_id_field="employee_id",
            destination_field="employee_email",
            topic_code="attendance.capture",
            channels=(NotificationChannel.IN_APP,),
        ),
    ),
    "PerformanceReviewSubmitted": (
        EventNotificationPlan(
            template_code="performance.review.submitted.employee",
            subject_type="Employee",
            subject_id_field="employee_id",
            destination_field="employee_email",
            topic_code="performance.review_submission",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "PerformanceReviewFinalized": (
        EventNotificationPlan(
            template_code="performance.review.finalized.employee",
            subject_type="Employee",
            subject_id_field="employee_id",
            destination_field="employee_email",
            topic_code="performance.review_finalized",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "PayrollProcessed": (
        EventNotificationPlan(
            template_code="payroll.processed.employee",
            subject_type="Employee",
            subject_id_field="employee_id",
            destination_field="employee_email",
            topic_code="payroll.processed",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "PayrollPaid": (
        EventNotificationPlan(
            template_code="payroll.paid.employee",
            subject_type="Employee",
            subject_id_field="employee_id",
            destination_field="employee_email",
            topic_code="payroll.paid",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "CandidateStageChanged": (
        EventNotificationPlan(
            template_code="hiring.candidate.stage_changed",
            subject_type="Candidate",
            subject_id_field="candidate_id",
            destination_field="candidate_email",
            topic_code="hiring.candidate_stage",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "InterviewScheduled": (
        EventNotificationPlan(
            template_code="interview.scheduled.candidate",
            subject_type="Candidate",
            subject_id_field="candidate_id",
            destination_field="candidate_email",
            topic_code="hiring.interview_scheduled",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "InterviewCalendarSynced": (
        EventNotificationPlan(
            template_code="interview.calendar_synced.candidate",
            subject_type="Candidate",
            subject_id_field="candidate_id",
            destination_field="candidate_email",
            topic_code="hiring.interview_calendar",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "UserProvisioned": (
        EventNotificationPlan(
            template_code="auth.user_provisioned",
            subject_type="UserAccount",
            subject_id_field="user_id",
            destination_field="email",
            topic_code="auth.user_provisioned",
            channels=(NotificationChannel.IN_APP, NotificationChannel.EMAIL),
        ),
    ),
    "SessionRevoked": (
        EventNotificationPlan(
            template_code="auth.session_revoked",
            subject_type="UserAccount",
            subject_id_field="user_id",
            topic_code="auth.session_revoked",
            channels=(NotificationChannel.IN_APP,),
        ),
    ),
}


DEFAULT_TEMPLATE_SEED = (
    ("leave.submitted.approver", NotificationChannel.IN_APP, "Leave request awaiting approval", "{employee_name} submitted {leave_type} leave for {start_date} to {end_date}."),
    ("leave.submitted.approver", NotificationChannel.EMAIL, "Leave request awaiting approval", "Approve {employee_name}'s {leave_type} leave request for {start_date} to {end_date}."),
    ("leave.approved.employee", NotificationChannel.IN_APP, "Leave request approved", "Your leave request for {start_date} to {end_date} was approved by {approver_name}."),
    ("leave.approved.employee", NotificationChannel.EMAIL, "Leave approved", "Your {leave_type} leave request for {start_date} to {end_date} has been approved."),
    ("leave.rejected.employee", NotificationChannel.IN_APP, "Leave request rejected", "Your leave request for {start_date} to {end_date} was rejected."),
    ("leave.rejected.employee", NotificationChannel.EMAIL, "Leave rejected", "Your {leave_type} leave request for {start_date} to {end_date} was rejected."),
    ("leave.cancelled.employee", NotificationChannel.IN_APP, "Leave request cancelled", "Your leave request for {start_date} to {end_date} was cancelled."),
    ("attendance.captured.employee", NotificationChannel.IN_APP, "Attendance captured", "Attendance for {attendance_date} was recorded with status {attendance_status}."),
    ("performance.review.submitted.employee", NotificationChannel.IN_APP, "Performance review submitted", "Your review for {review_period_start} to {review_period_end} was submitted by {reviewer_name}."),
    ("performance.review.submitted.employee", NotificationChannel.EMAIL, "Performance review submitted", "Your performance review for {review_period_start} to {review_period_end} is ready."),
    ("performance.review.finalized.employee", NotificationChannel.IN_APP, "Performance review finalized", "Your performance review was finalized with status {status}."),
    ("performance.review.finalized.employee", NotificationChannel.EMAIL, "Performance review finalized", "Your performance review has been finalized."),
    ("payroll.processed.employee", NotificationChannel.IN_APP, "Payroll ready for review", "Payroll for {pay_period_start} to {pay_period_end} was processed. Net pay: {net_pay} {currency}."),
    ("payroll.processed.employee", NotificationChannel.EMAIL, "Payroll processed", "Your payroll for {pay_period_start} to {pay_period_end} is ready. Net pay: {net_pay} {currency}."),
    ("payroll.paid.employee", NotificationChannel.IN_APP, "Payroll paid", "Payroll payment of {net_pay} {currency} was sent on {payment_date}."),
    ("payroll.paid.employee", NotificationChannel.EMAIL, "Payroll paid", "Payment of {net_pay} {currency} was completed on {payment_date}."),
    ("hiring.candidate.stage_changed", NotificationChannel.IN_APP, "Candidate update", "Your application moved to {pipeline_stage}."),
    ("hiring.candidate.stage_changed", NotificationChannel.EMAIL, "Application update", "Your application for {job_title} moved to {pipeline_stage}."),
    ("interview.scheduled.candidate", NotificationChannel.IN_APP, "Interview scheduled", "Your interview is scheduled for {scheduled_start}."),
    ("interview.scheduled.candidate", NotificationChannel.EMAIL, "Interview scheduled", "Your interview is booked for {scheduled_start}. Join via {location}."),
    ("interview.calendar_synced.candidate", NotificationChannel.IN_APP, "Calendar invite available", "Your interview invite is now synced to calendar."),
    ("interview.calendar_synced.candidate", NotificationChannel.EMAIL, "Calendar invite synced", "A calendar invite was synced for your interview."),
    ("auth.user_provisioned", NotificationChannel.IN_APP, "Account provisioned", "Your {legal_entity} account is ready to use."),
    ("auth.user_provisioned", NotificationChannel.EMAIL, "Welcome to SME HRMS", "Your account is provisioned and ready."),
    ("auth.session_revoked", NotificationChannel.IN_APP, "Session revoked", "A session was revoked. Please sign in again if needed."),
)


class NotificationService:
    def __init__(self, *, max_delivery_attempts: int = 3) -> None:
        self.max_delivery_attempts = max_delivery_attempts
        self.templates: dict[tuple[str, str, NotificationChannel], NotificationTemplate] = {}
        self.preferences: dict[tuple[str, str, str, str], NotificationPreference] = {}
        self.messages: dict[str, NotificationMessage] = {}
        self.delivery_attempts: list[DeliveryAttempt] = []
        self.events: list[dict[str, Any]] = []
        self.event_registry = EventRegistry()
        self.dead_letters = DeadLetterQueue()
        self.observability = Observability("notification-service")
        self.tenant_configs: dict[str, TenantNotificationConfig] = {}
        self.subject_tenants: dict[tuple[str, str], str] = {}
        self.delivery_providers: dict[NotificationChannel, DeliveryProvider] = {
            NotificationChannel.IN_APP: InAppDeliveryProvider(),
            NotificationChannel.EMAIL: EmailDeliveryProvider(),
        }
        self._seed_templates()

    def _seed_templates(self) -> None:
        for code, channel, subject_template, body_template in DEFAULT_TEMPLATE_SEED:
            self.register_template(
                tenant_id="*",
                code=code,
                channel=channel,
                topic_code=code.rsplit(".", 1)[0] if "." in code else code,
                subject_template=subject_template,
                body_template=body_template,
            )

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _tenant_config(self, tenant_id: str) -> TenantNotificationConfig:
        tenant_id = normalize_tenant_id(tenant_id)
        if tenant_id not in self.tenant_configs:
            self.tenant_configs[tenant_id] = TenantNotificationConfig(tenant_id=tenant_id)
        return self.tenant_configs[tenant_id]

    def upsert_tenant_config(self, tenant_id: str, config: dict[str, Any]) -> TenantNotificationConfig:
        normalized_tenant = normalize_tenant_id(tenant_id)
        current = self._tenant_config(normalized_tenant)
        record = TenantNotificationConfig(
            tenant_id=normalized_tenant,
            feature_flags={**current.feature_flags, **dict(config.get("feature_flags") or {})},
            leave_policy_refs=list(config.get("leave_policy_refs") or current.leave_policy_refs),
            payroll_rule_refs=list(config.get("payroll_rule_refs") or current.payroll_rule_refs),
            locale=str(config.get("locale") or current.locale or "en-US"),
            legal_entity=str(config.get("legal_entity") or current.legal_entity or "SME HRMS"),
            enabled_locations=list(config.get("enabled_locations") or current.enabled_locations),
            notification_defaults={**current.notification_defaults, **dict(config.get("notification_defaults") or {})},
            template_overrides={**current.template_overrides, **dict(config.get("template_overrides") or {})},
            updated_at=self._now(),
        )
        self.tenant_configs[normalized_tenant] = record
        return record

    def register_template(
        self,
        *,
        tenant_id: str,
        code: str,
        channel: NotificationChannel,
        topic_code: str,
        body_template: str,
        subject_template: str | None = None,
        status: str = "Active",
        locale: str | None = None,
    ) -> NotificationTemplate:
        now = self._now()
        normalized_tenant = normalize_tenant_id(tenant_id)
        template = NotificationTemplate(
            template_id=str(uuid4()),
            tenant_id=normalized_tenant,
            code=code,
            channel=channel,
            subject_template=subject_template,
            body_template=body_template,
            topic_code=topic_code,
            locale=locale or self._tenant_config(normalized_tenant if normalized_tenant != "*" else "tenant-default").locale,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self.templates[(normalized_tenant, code, channel)] = template
        return template

    def _resolve_template(self, tenant_id: str, code: str, channel: NotificationChannel) -> NotificationTemplate:
        overrides = self._tenant_config(tenant_id).template_overrides.get(code) or {}
        template = self.templates.get((tenant_id, code, channel)) or self.templates.get(("*", code, channel))
        if template is None or template.status != "Active":
            raise NotificationServiceError(
                "TEMPLATE_NOT_FOUND",
                f"Template {code} for {channel.value} is not configured",
            )
        if not overrides:
            return template
        return NotificationTemplate(
            template_id=template.template_id,
            tenant_id=tenant_id,
            code=template.code,
            channel=template.channel,
            subject_template=overrides.get("subject_template", template.subject_template),
            body_template=overrides.get("body_template", template.body_template) or template.body_template,
            topic_code=template.topic_code,
            locale=self._tenant_config(tenant_id).locale,
            status=template.status,
            created_at=template.created_at,
            updated_at=self._now(),
        )

    def _validate_subject_reference(self, *, tenant_id: str, subject_type: str, subject_id: str) -> None:
        allowed_subject_types = {"Employee", "Candidate", "UserAccount", "Service"}
        if subject_type not in allowed_subject_types:
            raise NotificationServiceError(
                "VALIDATION_ERROR",
                "subject_type is invalid",
                details=[{"field": "subject_type", "reason": "must be one of: " + ", ".join(sorted(allowed_subject_types))}],
            )
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise NotificationServiceError(
                "VALIDATION_ERROR",
                "subject_id is required",
                details=[{"field": "subject_id", "reason": "must be a non-empty string"}],
            )
        scoped_key = (subject_type, subject_id)
        existing_tenant = self.subject_tenants.get(scoped_key)
        if existing_tenant is not None:
            try:
                assert_tenant_access(existing_tenant, tenant_id)
            except PermissionError as exc:
                raise NotificationServiceError("FORBIDDEN", "Cross-tenant recipient access is not allowed") from exc
        else:
            self.subject_tenants[scoped_key] = tenant_id

    def _assert_subject_tenant_access(self, *, tenant_id: str, subject_id: str) -> None:
        matches = [stored_tenant for (stored_type, stored_subject_id), stored_tenant in self.subject_tenants.items() if stored_subject_id == subject_id]
        if not matches:
            return
        for stored_tenant in matches:
            try:
                assert_tenant_access(stored_tenant, tenant_id)
            except PermissionError as exc:
                raise NotificationServiceError("FORBIDDEN", "Cross-tenant recipient access is not allowed") from exc

    def get_or_create_preference(self, *, tenant_id: str, subject_type: str, subject_id: str, topic_code: str) -> NotificationPreference:
        self._validate_subject_reference(tenant_id=tenant_id, subject_type=subject_type, subject_id=subject_id)
        if not topic_code:
            raise NotificationServiceError(
                "VALIDATION_ERROR",
                "topic_code is required",
                details=[{"field": "topic_code", "reason": "must be a non-empty string"}],
            )
        key = (tenant_id, subject_type, subject_id, topic_code)
        preference = self.preferences.get(key)
        if preference:
            return preference

        defaults = dict(self._tenant_config(tenant_id).notification_defaults.get(topic_code) or {})
        preference = NotificationPreference(
            preference_id=str(uuid4()),
            tenant_id=tenant_id,
            subject_type=subject_type,
            subject_id=subject_id,
            topic_code=topic_code,
            email_enabled=bool(defaults.get("email_enabled", True)),
            sms_enabled=bool(defaults.get("sms_enabled", False)),
            push_enabled=bool(defaults.get("push_enabled", True)),
            in_app_enabled=bool(defaults.get("in_app_enabled", True)),
            quiet_hours=defaults.get("quiet_hours"),
        )
        self.preferences[key] = preference
        return preference

    def update_preferences(
        self,
        *,
        tenant_id: str,
        subject_type: str,
        subject_id: str,
        topic_code: str,
        patch: dict[str, Any],
        actor: dict[str, str] | None = None,
        trace_id: str | None = None,
    ) -> NotificationPreference:
        if not isinstance(patch, dict):
            raise NotificationServiceError("VALIDATION_ERROR", "Preference patch must be an object")
        preference = self.get_or_create_preference(tenant_id=tenant_id, subject_type=subject_type, subject_id=subject_id, topic_code=topic_code)
        allowed = {"email_enabled", "sms_enabled", "push_enabled", "in_app_enabled", "quiet_hours"}
        unknown = sorted(set(patch).difference(allowed))
        if unknown:
            raise NotificationServiceError(
                "VALIDATION_ERROR",
                "Unknown preference fields",
                details=[{"field": field, "reason": "is not supported"} for field in unknown],
            )
        details: list[dict[str, Any]] = []
        before = serialize_preference(preference)
        for field_name in {"email_enabled", "sms_enabled", "push_enabled", "in_app_enabled"}:
            if field_name in patch and not isinstance(patch[field_name], bool):
                details.append({"field": field_name, "reason": "must be a boolean"})
        if "quiet_hours" in patch and patch["quiet_hours"] is not None and not isinstance(patch["quiet_hours"], dict):
            details.append({"field": "quiet_hours", "reason": "must be an object when provided"})
        if details:
            raise NotificationServiceError("VALIDATION_ERROR", "Preference patch is invalid", details=details)
        for field_name, value in patch.items():
            setattr(preference, field_name, value)
        preference.updated_at = self._now()
        self.observability.logger.audit(
            "notification_preference_updated",
            trace_id=trace_id,
            actor=(actor or {}).get("id", "system"),
            entity="NotificationPreference",
            entity_id=preference.preference_id,
            context={
                "tenant_id": tenant_id,
                "subject_type": subject_type,
                "subject_id": subject_id,
                "topic_code": topic_code,
                "before": before,
                "after": serialize_preference(preference),
            },
        )
        return preference

    def get_preferences(
        self,
        *,
        tenant_id: str,
        subject_type: str,
        subject_id: str,
        topic_code: str | None = None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> tuple[list[NotificationPreference], dict[str, Any]]:
        self._validate_subject_reference(tenant_id=tenant_id, subject_type=subject_type, subject_id=subject_id)
        rows = [
            pref
            for pref in self.preferences.values()
            if pref.tenant_id == tenant_id and pref.subject_type == subject_type and pref.subject_id == subject_id
        ]
        if topic_code is not None:
            rows = [pref for pref in rows if pref.topic_code == topic_code]
        rows.sort(key=lambda row: row.topic_code)
        return self._paginate(rows, limit=limit, cursor=cursor)

    def ingest_event(self, event: dict[str, Any], *, trace_id: str | None = None) -> list[NotificationMessage]:
        try:
            canonical_event, _ = ensure_event_contract(event, source="notification-api", registry=self.event_registry)
        except EventContractError as exc:
            if str(exc) == "missing_tenant_context":
                raise NotificationServiceError("VALIDATION_ERROR", "tenant_id is required") from exc
            raise NotificationServiceError("VALIDATION_ERROR", f"Invalid event payload: {exc}") from exc

        tenant_id = normalize_tenant_id(str(canonical_event["tenant_id"]))
        self._assert_event_payload_is_tenant_safe(tenant_id=tenant_id, event=canonical_event)
        event_type = canonical_event["event_type"]
        event_name = str(canonical_event["metadata"].get("legacy_event_name") or legacy_event_name_for(event_type))

        plans = EVENT_NOTIFICATION_PLANS.get(event_name)
        if not plans:
            raise NotificationServiceError("UNSUPPORTED_EVENT", f"No notification mapping registered for {event_name}")

        created: list[NotificationMessage] = []
        for plan in plans:
            subject_id = canonical_event["data"].get(plan.subject_id_field)
            if not subject_id:
                raise NotificationServiceError(
                    "VALIDATION_ERROR",
                    f"{plan.subject_id_field} is required for {event_name}",
                    details=[{"field": plan.subject_id_field, "reason": "must be provided by upstream event"}],
                )
            for channel in plan.channels:
                created.append(
                    self._queue_notification(
                        tenant_id=tenant_id,
                        template_code=plan.template_code,
                        subject_type=plan.subject_type,
                        subject_id=str(subject_id),
                        topic_code=plan.topic_code,
                        channel=channel,
                        destination=self._resolve_destination(
                            channel=channel,
                            subject_id=str(subject_id),
                            event=canonical_event["data"],
                            destination_field=plan.destination_field,
                        ),
                        payload=self._enrich_payload(
                            tenant_id=tenant_id,
                            event_name=event_name,
                            event_type=event_type,
                            payload=canonical_event["data"],
                            metadata=canonical_event["metadata"],
                        ),
                        event_name=event_name,
                        event_type=event_type,
                        trace_id=trace_id,
                    )
                )
        return created

    def _assert_event_payload_is_tenant_safe(self, *, tenant_id: str, event: dict[str, Any]) -> None:
        mismatched = [
            key for key, value in dict(event.get("data") or {}).items()
            if key.endswith("_tenant_id") and value and normalize_tenant_id(str(value)) != tenant_id
        ]
        if mismatched:
            raise NotificationServiceError(
                "FORBIDDEN",
                "Event payload contains a cross-tenant recipient reference",
                details=[{"field": key, "reason": "must match event tenant_id"} for key in mismatched],
            )

    def _enrich_payload(
        self,
        *,
        tenant_id: str,
        event_name: str,
        event_type: str,
        payload: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        tenant_config = self._tenant_config(tenant_id)
        return {
            **payload,
            "event_name": event_name,
            "event_type": event_type,
            "tenant_id": tenant_id,
            "locale": tenant_config.locale,
            "legal_entity": tenant_config.legal_entity,
            "metadata": metadata,
        }

    def _resolve_destination(self, *, channel: NotificationChannel, subject_id: str, event: dict[str, Any], destination_field: str | None) -> str:
        if channel == NotificationChannel.IN_APP:
            return f"inbox:{subject_id}"
        if destination_field and event.get(destination_field):
            return str(event[destination_field])
        if event.get("destination"):
            return str(event["destination"])
        return f"unresolved:{subject_id}"

    def _queue_notification(
        self,
        *,
        tenant_id: str,
        template_code: str,
        subject_type: str,
        subject_id: str,
        topic_code: str,
        channel: NotificationChannel,
        destination: str,
        payload: dict[str, Any],
        event_name: str,
        event_type: str,
        trace_id: str | None = None,
    ) -> NotificationMessage:
        self._validate_subject_reference(tenant_id=tenant_id, subject_type=subject_type, subject_id=subject_id)
        template = self._resolve_template(tenant_id, template_code, channel)
        preference = self.get_or_create_preference(tenant_id=tenant_id, subject_type=subject_type, subject_id=subject_id, topic_code=topic_code)
        now = self._now()
        subject_text, body_text = self._render_template(template, payload)
        message = NotificationMessage(
            message_id=str(uuid4()),
            tenant_id=tenant_id,
            template_id=template.template_id,
            template_code=template.code,
            event_name=event_name,
            event_type=event_type,
            recipient=subject_id,
            subject_type=subject_type,
            subject_id=subject_id,
            topic_code=topic_code,
            channel=channel,
            destination=destination,
            payload=payload,
            subject_text=subject_text,
            body_text=body_text,
            status=NotificationStatus.QUEUED,
            queued_at=now,
            sent_at=None,
            delivered_at=None,
            failed_at=None,
            failure_reason=None,
            read_at=None,
            retry_count=0,
            last_attempt_at=None,
            created_at=now,
            updated_at=now,
        )
        self.messages[message.message_id] = message
        self._publish_message_event(
            legacy_event_name="NotificationQueued",
            message=message,
            status=message.status.value,
            trace_id=trace_id,
        )

        if not self._channel_enabled(preference, channel) or self._quiet_hours_active(preference, now=now):
            message.status = NotificationStatus.SUPPRESSED
            message.failure_reason = "Suppressed by notification preferences"
            message.updated_at = now
            self._publish_message_event(
                legacy_event_name="NotificationSuppressed",
                message=message,
                status=message.status.value,
                trace_id=trace_id,
            )
            return message

        self._attempt_delivery(message.message_id, trace_id=trace_id)
        return self.messages[message.message_id]

    def _quiet_hours_active(self, preference: NotificationPreference, *, now: datetime) -> bool:
        quiet_hours = preference.quiet_hours or {}
        start = quiet_hours.get("start")
        end = quiet_hours.get("end")
        if not start or not end:
            return False
        try:
            start_hour = int(str(start).split(":", 1)[0])
            end_hour = int(str(end).split(":", 1)[0])
        except ValueError:
            return False
        current_hour = now.hour
        if start_hour <= end_hour:
            return start_hour <= current_hour < end_hour
        return current_hour >= start_hour or current_hour < end_hour

    def _channel_enabled(self, preference: NotificationPreference, channel: NotificationChannel) -> bool:
        return {
            NotificationChannel.EMAIL: preference.email_enabled,
            NotificationChannel.SMS: preference.sms_enabled,
            NotificationChannel.PUSH: preference.push_enabled,
            NotificationChannel.IN_APP: preference.in_app_enabled,
        }[channel]

    def _render_template(self, template: NotificationTemplate, payload: dict[str, Any]) -> tuple[str | None, str]:
        subject = template.subject_template.format_map(_SafePayload(payload)) if template.subject_template else None
        body = template.body_template.format_map(_SafePayload(payload))
        return subject, body

    def _provider_for(self, channel: NotificationChannel) -> DeliveryProvider:
        provider = self.delivery_providers.get(channel)
        if provider is None:
            raise NotificationServiceError("VALIDATION_ERROR", f"No delivery provider configured for {channel.value}")
        return provider

    def _attempt_delivery(self, message_id: str, *, trace_id: str | None = None) -> NotificationMessage:
        message = self.get_message(message_id=message_id)
        if message.status in {NotificationStatus.SENT, NotificationStatus.SUPPRESSED}:
            return message

        provider = self._provider_for(message.channel)
        now = self._now()
        attempt_number = len([row for row in self.delivery_attempts if row.message_id == message.message_id]) + 1
        result = provider.deliver(message, attempt_number)
        attempt = DeliveryAttempt(
            delivery_attempt_id=str(uuid4()),
            tenant_id=message.tenant_id,
            message_id=message.message_id,
            provider_name=provider.provider_name,
            attempt_number=attempt_number,
            attempted_at=now,
            outcome=result.outcome,
            response_code=result.response_code,
            response_message=result.response_message,
            provider_message_id=result.provider_message_id,
            created_at=now,
        )
        self.delivery_attempts.append(attempt)
        message.last_attempt_at = now
        message.retry_count = max(0, attempt_number - 1)
        message.updated_at = now

        if result.outcome == DeliveryOutcome.SENT:
            message.status = NotificationStatus.SENT
            message.sent_at = now
            message.delivered_at = now
            message.failure_reason = None
            self._publish_message_event("NotificationSent", message=message, status=message.status.value, trace_id=trace_id)
            return message

        if result.retryable and attempt_number < self.max_delivery_attempts:
            message.status = NotificationStatus.QUEUED
            message.failure_reason = result.response_message
            return message

        message.status = NotificationStatus.FAILED
        message.failed_at = now
        message.failure_reason = result.response_message
        self.dead_letters.push(
            workflow="notification_dispatch",
            operation="delivery_attempt",
            payload={"message_id": message.message_id, "tenant_id": message.tenant_id, "channel": message.channel.value},
            reason=result.response_message,
            trace_id=trace_id,
            retryable=result.retryable and attempt_number >= self.max_delivery_attempts,
        )
        self._publish_message_event("NotificationFailed", message=message, status=message.status.value, trace_id=trace_id)
        return message

    def process_pending_deliveries(self, *, tenant_id: str | None = None, limit: int | None = None, trace_id: str | None = None) -> list[NotificationMessage]:
        rows = [
            message for message in self.messages.values()
            if message.status == NotificationStatus.QUEUED and message.channel != NotificationChannel.IN_APP
        ]
        if tenant_id is not None:
            normalized_tenant = normalize_tenant_id(tenant_id)
            rows = [message for message in rows if message.tenant_id == normalized_tenant]
        rows.sort(key=lambda row: row.queued_at)
        processed: list[NotificationMessage] = []
        for message in rows[:limit]:
            processed.append(self._attempt_delivery(message.message_id, trace_id=trace_id))
        return processed

    def retry_failed_deliveries(self, *, tenant_id: str | None = None, trace_id: str | None = None) -> list[NotificationMessage]:
        rows = [
            message for message in self.messages.values()
            if message.status == NotificationStatus.FAILED and message.channel != NotificationChannel.IN_APP
        ]
        if tenant_id is not None:
            normalized_tenant = normalize_tenant_id(tenant_id)
            rows = [message for message in rows if message.tenant_id == normalized_tenant]
        rows.sort(key=lambda row: row.updated_at)
        retried: list[NotificationMessage] = []
        for message in rows:
            if len([attempt for attempt in self.delivery_attempts if attempt.message_id == message.message_id]) >= self.max_delivery_attempts:
                continue
            message.status = NotificationStatus.QUEUED
            retried.append(self._attempt_delivery(message.message_id, trace_id=trace_id))
        return retried

    def _publish_message_event(self, legacy_event_name: str, *, message: NotificationMessage, status: str, trace_id: str | None = None) -> None:
        emit_canonical_event(
            self.events,
            legacy_event_name=legacy_event_name,
            data={
                "message_id": message.message_id,
                "template_id": message.template_id,
                "template_code": message.template_code,
                "subject_type": message.subject_type,
                "subject_id": message.subject_id,
                "channel": message.channel.value,
                "destination": message.destination,
                "status": status,
                "queued_at": message.queued_at.isoformat(),
                "sent_at": message.sent_at.isoformat() if message.sent_at else None,
                "failed_at": message.failed_at.isoformat() if message.failed_at else None,
                "failure_reason": message.failure_reason,
            },
            source="notification-service",
            tenant_id=message.tenant_id,
            registry=self.event_registry,
            correlation_id=trace_id,
            idempotency_key=f"{legacy_event_name}:{message.message_id}:{status}",
        )

    def get_message(self, *, message_id: str, tenant_id: str | None = None) -> NotificationMessage:
        try:
            message = self.messages[message_id]
        except KeyError as exc:
            raise NotificationServiceError("MESSAGE_NOT_FOUND", "Notification message not found") from exc
        if tenant_id is not None:
            try:
                assert_tenant_access(message.tenant_id, tenant_id)
            except PermissionError as exc:
                raise NotificationServiceError("FORBIDDEN", "Notification message does not belong to the tenant") from exc
        return message

    def list_delivery(
        self,
        *,
        tenant_id: str,
        subject_id: str | None = None,
        status: str | None = None,
        channel: str | None = None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        rows = [row for row in self.messages.values() if row.tenant_id == tenant_id]
        if subject_id is not None and (not isinstance(subject_id, str) or not subject_id.strip()):
            raise NotificationServiceError("VALIDATION_ERROR", "subject_id filter is invalid", details=[{"field": "subject_id", "reason": "must be a non-empty string"}])
        if subject_id is not None:
            rows = [row for row in rows if row.subject_id == subject_id]
        if status is not None:
            rows = [row for row in rows if row.status.value == status]
        if channel is not None:
            rows = [row for row in rows if row.channel.value == channel]
        rows.sort(key=lambda row: row.queued_at, reverse=True)
        page, pagination = self._paginate(rows, limit=limit, cursor=cursor)
        return [self._delivery_view(row) for row in page], pagination

    def get_inbox(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        unread_only: bool = False,
        limit: int = 25,
        cursor: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise NotificationServiceError("VALIDATION_ERROR", "subject_id is required", details=[{"field": "subject_id", "reason": "must be a non-empty string"}])
        self._assert_subject_tenant_access(tenant_id=tenant_id, subject_id=subject_id)
        rows = [
            row for row in self.messages.values()
            if row.tenant_id == tenant_id and row.subject_id == subject_id and row.channel == NotificationChannel.IN_APP
        ]
        if unread_only:
            rows = [row for row in rows if row.read_at is None]
        rows.sort(key=lambda row: row.queued_at, reverse=True)
        page_rows, pagination = self._paginate(rows, limit=limit, cursor=cursor)
        items = [self._inbox_view(row) for row in page_rows]
        unread_count = sum(1 for row in rows if row.read_at is None)
        return {
            "tenant_id": tenant_id,
            "subject_id": subject_id,
            "items": items,
            "summary": {
                "total": len(rows),
                "unread": unread_count,
                "sent": sum(1 for row in rows if row.status == NotificationStatus.SENT),
                "suppressed": sum(1 for row in rows if row.status == NotificationStatus.SUPPRESSED),
                "failed": sum(1 for row in rows if row.status == NotificationStatus.FAILED),
            },
        }, pagination

    def mark_inbox_item_read(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        message_id: str,
        actor: dict[str, str] | None = None,
        trace_id: str | None = None,
    ) -> NotificationMessage:
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise NotificationServiceError("VALIDATION_ERROR", "subject_id is required", details=[{"field": "subject_id", "reason": "must be a non-empty string"}])
        message = self.get_message(message_id=message_id, tenant_id=tenant_id)
        if message.subject_id != subject_id or message.channel != NotificationChannel.IN_APP:
            raise NotificationServiceError("FORBIDDEN", "Inbox item does not belong to subject")
        if message.read_at is None:
            message.read_at = self._now()
            message.updated_at = message.read_at
            self.observability.logger.audit(
                "notification_read",
                trace_id=trace_id,
                actor=(actor or {}).get("id", subject_id),
                entity="NotificationMessage",
                entity_id=message.message_id,
                context={"tenant_id": tenant_id, "subject_id": subject_id, "status": message.status.value},
            )
        return message

    def _delivery_view(self, message: NotificationMessage) -> dict[str, Any]:
        attempts = [attempt for attempt in self.delivery_attempts if attempt.message_id == message.message_id]
        last_attempt = attempts[-1] if attempts else None
        dead_letter = next((entry for entry in reversed(self.dead_letters.entries) if entry.payload.get("message_id") == message.message_id), None)
        return {
            "message_id": message.message_id,
            "tenant_id": message.tenant_id,
            "template_id": message.template_id,
            "template_code": message.template_code,
            "subject_type": message.subject_type,
            "subject_id": message.subject_id,
            "recipient": message.recipient,
            "channel": message.channel.value,
            "destination": message.destination,
            "status": message.status.value,
            "queued_at": message.queued_at.isoformat(),
            "sent_at": message.sent_at.isoformat() if message.sent_at else None,
            "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
            "failed_at": message.failed_at.isoformat() if message.failed_at else None,
            "failure_reason": message.failure_reason,
            "last_provider_name": last_attempt.provider_name if last_attempt else None,
            "last_attempt_outcome": last_attempt.outcome.value if last_attempt else None,
            "attempt_count": len(attempts),
            "dead_letter_id": dead_letter.dead_letter_id if dead_letter else None,
            "updated_at": message.updated_at.isoformat(),
        }

    def _inbox_view(self, message: NotificationMessage) -> dict[str, Any]:
        return {
            "message_id": message.message_id,
            "tenant_id": message.tenant_id,
            "event_name": message.event_name,
            "topic_code": message.topic_code,
            "status": message.status.value,
            "title": message.subject_text or "Notification",
            "body": message.body_text,
            "queued_at": message.queued_at.isoformat(),
            "read_at": message.read_at.isoformat() if message.read_at else None,
            "unread": message.read_at is None,
        }

    def _paginate(self, rows: list[Any], *, limit: int = 25, cursor: str | None = None) -> tuple[list[Any], dict[str, Any]]:
        normalized_limit = max(1, min(int(limit or 25), 100))
        offset = int(cursor or 0)
        page = rows[offset:offset + normalized_limit]
        next_cursor = str(offset + normalized_limit) if offset + normalized_limit < len(rows) else None
        return page, pagination_payload(limit=normalized_limit, cursor=str(offset) if cursor is not None else None, next_cursor=next_cursor, count=len(page))


class _SafePayload(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


_DATETIME_FIELDS = {
    "queued_at",
    "sent_at",
    "delivered_at",
    "failed_at",
    "read_at",
    "last_attempt_at",
    "created_at",
    "updated_at",
}


def serialize_message(message: NotificationMessage) -> dict[str, Any]:
    payload = asdict(message)
    payload["channel"] = message.channel.value
    payload["status"] = message.status.value
    for field_name in _DATETIME_FIELDS:
        value = payload.get(field_name)
        payload[field_name] = value.isoformat() if value else None
    return payload


def serialize_preference(preference: NotificationPreference) -> dict[str, Any]:
    payload = asdict(preference)
    for field_name in ["created_at", "updated_at"]:
        payload[field_name] = payload[field_name].isoformat()
    return payload
