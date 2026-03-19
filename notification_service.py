from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from resilience import Observability


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
class NotificationTemplate:
    template_id: str
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
    message_id: str
    provider_name: str
    attempt_number: int
    attempted_at: datetime
    outcome: DeliveryOutcome
    response_code: str | None = None
    response_message: str | None = None
    provider_message_id: str | None = None


@dataclass
class NotificationMessage:
    message_id: str
    template_id: str | None
    template_code: str | None
    event_name: str | None
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
    failure_reason: str | None
    read_at: datetime | None
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
    ("attendance.captured.employee", NotificationChannel.IN_APP, "Attendance captured", "Attendance for {attendance_date} was recorded with status {attendance_status}."),
    ("payroll.processed.employee", NotificationChannel.IN_APP, "Payroll ready for review", "Payroll for {pay_period_start} to {pay_period_end} was processed. Net pay: {net_pay} {currency}."),
    ("payroll.processed.employee", NotificationChannel.EMAIL, "Payroll processed", "Your payroll for {pay_period_start} to {pay_period_end} is ready. Net pay: {net_pay} {currency}."),
    ("payroll.paid.employee", NotificationChannel.IN_APP, "Payroll paid", "Payroll payment of {net_pay} {currency} was sent on {payment_date}."),
    ("payroll.paid.employee", NotificationChannel.EMAIL, "Payroll paid", "Payment of {net_pay} {currency} was completed on {payment_date}."),
    ("interview.scheduled.candidate", NotificationChannel.IN_APP, "Interview scheduled", "Your interview is scheduled for {scheduled_start}."),
    ("interview.scheduled.candidate", NotificationChannel.EMAIL, "Interview scheduled", "Your interview is booked for {scheduled_start}. Join via {location}."),
    ("interview.calendar_synced.candidate", NotificationChannel.IN_APP, "Calendar invite available", "Your interview invite is now synced to calendar."),
    ("interview.calendar_synced.candidate", NotificationChannel.EMAIL, "Calendar invite synced", "A calendar invite was synced for your interview."),
    ("auth.user_provisioned", NotificationChannel.IN_APP, "Account provisioned", "Your SME HRMS account is ready to use."),
    ("auth.user_provisioned", NotificationChannel.EMAIL, "Welcome to SME HRMS", "Your account is provisioned and ready."),
    ("auth.session_revoked", NotificationChannel.IN_APP, "Session revoked", "A session was revoked. Please sign in again if needed."),
)


class NotificationService:
    def __init__(self) -> None:
        self.templates: dict[tuple[str, NotificationChannel], NotificationTemplate] = {}
        self.preferences: dict[tuple[str, str, str], NotificationPreference] = {}
        self.messages: dict[str, NotificationMessage] = {}
        self.delivery_attempts: list[DeliveryAttempt] = []
        self.events: list[dict[str, Any]] = []
        self.observability = Observability("notification-service")
        self._seed_templates()

    def _seed_templates(self) -> None:
        for code, channel, subject_template, body_template in DEFAULT_TEMPLATE_SEED:
            self.register_template(
                code=code,
                channel=channel,
                topic_code=code.rsplit(".", 1)[0] if "." in code else code,
                subject_template=subject_template,
                body_template=body_template,
            )

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def register_template(
        self,
        *,
        code: str,
        channel: NotificationChannel,
        topic_code: str,
        body_template: str,
        subject_template: str | None = None,
    ) -> NotificationTemplate:
        now = self._now()
        template = NotificationTemplate(
            template_id=str(uuid4()),
            code=code,
            channel=channel,
            subject_template=subject_template,
            body_template=body_template,
            topic_code=topic_code,
            created_at=now,
            updated_at=now,
        )
        self.templates[(code, channel)] = template
        return template

    def get_or_create_preference(self, *, subject_type: str, subject_id: str, topic_code: str) -> NotificationPreference:
        self._validate_subject_reference(subject_type=subject_type, subject_id=subject_id)
        if not topic_code:
            raise NotificationServiceError('VALIDATION_ERROR', 'topic_code is required', details=[{'field': 'topic_code', 'reason': 'must be a non-empty string'}])
        key = (subject_type, subject_id, topic_code)
        preference = self.preferences.get(key)
        if preference:
            return preference
        preference = NotificationPreference(
            preference_id=str(uuid4()),
            subject_type=subject_type,
            subject_id=subject_id,
            topic_code=topic_code,
        )
        self.preferences[key] = preference
        return preference

    def update_preferences(self, *, subject_type: str, subject_id: str, topic_code: str, patch: dict[str, Any]) -> NotificationPreference:
        if not isinstance(patch, dict):
            raise NotificationServiceError('VALIDATION_ERROR', 'Preference patch must be an object')
        preference = self.get_or_create_preference(subject_type=subject_type, subject_id=subject_id, topic_code=topic_code)
        allowed = {"email_enabled", "sms_enabled", "push_enabled", "in_app_enabled", "quiet_hours"}
        unknown = sorted(set(patch).difference(allowed))
        if unknown:
            raise NotificationServiceError("VALIDATION_ERROR", "Unknown preference fields", details=[{"field": field, "reason": "is not supported"} for field in unknown])
        details: list[dict[str, Any]] = []
        for field_name in {'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled'}:
            if field_name in patch and not isinstance(patch[field_name], bool):
                details.append({'field': field_name, 'reason': 'must be a boolean'})
        if 'quiet_hours' in patch and patch['quiet_hours'] is not None and not isinstance(patch['quiet_hours'], dict):
            details.append({'field': 'quiet_hours', 'reason': 'must be an object when provided'})
        if details:
            raise NotificationServiceError('VALIDATION_ERROR', 'Preference patch is invalid', details=details)
        for field_name, value in patch.items():
            setattr(preference, field_name, value)
        preference.updated_at = self._now()
        return preference

    def get_preferences(self, *, subject_type: str, subject_id: str, topic_code: str | None = None) -> list[NotificationPreference]:
        self._validate_subject_reference(subject_type=subject_type, subject_id=subject_id)
        rows = [pref for pref in self.preferences.values() if pref.subject_type == subject_type and pref.subject_id == subject_id]
        if topic_code is not None:
            rows = [pref for pref in rows if pref.topic_code == topic_code]
        return sorted(rows, key=lambda row: row.topic_code)

    def _validate_subject_reference(self, *, subject_type: str, subject_id: str) -> None:
        allowed_subject_types = {'Employee', 'Candidate', 'UserAccount', 'Service'}
        if subject_type not in allowed_subject_types:
            raise NotificationServiceError('VALIDATION_ERROR', 'subject_type is invalid', details=[{'field': 'subject_type', 'reason': 'must be one of: ' + ', '.join(sorted(allowed_subject_types))}])
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise NotificationServiceError('VALIDATION_ERROR', 'subject_id is required', details=[{'field': 'subject_id', 'reason': 'must be a non-empty string'}])

    def ingest_event(self, event: dict[str, Any]) -> list[NotificationMessage]:
        event_name = str(event.get("event_name") or event.get("type") or "")
        if not event_name:
            raise NotificationServiceError("VALIDATION_ERROR", "event_name is required")

        plans = EVENT_NOTIFICATION_PLANS.get(event_name)
        if not plans:
            raise NotificationServiceError("UNSUPPORTED_EVENT", f"No notification mapping registered for {event_name}")

        created: list[NotificationMessage] = []
        for plan in plans:
            subject_id = event.get(plan.subject_id_field)
            if not subject_id:
                raise NotificationServiceError(
                    "VALIDATION_ERROR",
                    f"{plan.subject_id_field} is required for {event_name}",
                    details=[{"field": plan.subject_id_field, "reason": "must be provided by upstream event"}],
                )
            for channel in plan.channels:
                created.append(
                    self._queue_notification(
                        template_code=plan.template_code,
                        subject_type=plan.subject_type,
                        subject_id=str(subject_id),
                        topic_code=plan.topic_code,
                        channel=channel,
                        destination=self._resolve_destination(channel=channel, subject_id=str(subject_id), event=event, destination_field=plan.destination_field),
                        payload={**event, "event_name": event_name},
                        event_name=event_name,
                    )
                )
        return created

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
        template_code: str,
        subject_type: str,
        subject_id: str,
        topic_code: str,
        channel: NotificationChannel,
        destination: str,
        payload: dict[str, Any],
        event_name: str,
    ) -> NotificationMessage:
        template = self.templates.get((template_code, channel))
        if template is None:
            raise NotificationServiceError(
                "TEMPLATE_NOT_FOUND",
                f"Template {template_code} for {channel.value} is not configured",
            )

        preference = self.get_or_create_preference(subject_type=subject_type, subject_id=subject_id, topic_code=topic_code)
        if not self._channel_enabled(preference, channel):
            return self._record_message(
                template=template,
                event_name=event_name,
                subject_type=subject_type,
                subject_id=subject_id,
                topic_code=topic_code,
                channel=channel,
                destination=destination,
                payload=payload,
                status=NotificationStatus.SUPPRESSED,
                failure_reason="Suppressed by subject preferences",
                sent=False,
            )

        return self._record_message(
            template=template,
            event_name=event_name,
            subject_type=subject_type,
            subject_id=subject_id,
            topic_code=topic_code,
            channel=channel,
            destination=destination,
            payload=payload,
            status=NotificationStatus.SENT,
            failure_reason=None,
            sent=True,
        )

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

    def _record_message(
        self,
        *,
        template: NotificationTemplate,
        event_name: str,
        subject_type: str,
        subject_id: str,
        topic_code: str,
        channel: NotificationChannel,
        destination: str,
        payload: dict[str, Any],
        status: NotificationStatus,
        failure_reason: str | None,
        sent: bool,
    ) -> NotificationMessage:
        now = self._now()
        subject_text, body_text = self._render_template(template, payload)
        message = NotificationMessage(
            message_id=str(uuid4()),
            template_id=template.template_id,
            template_code=template.code,
            event_name=event_name,
            subject_type=subject_type,
            subject_id=subject_id,
            topic_code=topic_code,
            channel=channel,
            destination=destination,
            payload=payload,
            subject_text=subject_text,
            body_text=body_text,
            status=status,
            queued_at=now,
            sent_at=now if sent else None,
            failure_reason=failure_reason,
            read_at=None,
            created_at=now,
            updated_at=now,
        )
        self.messages[message.message_id] = message
        self.events.append({"event_name": "NotificationQueued", "message_id": message.message_id, "status": message.status.value})
        outcome = DeliveryOutcome.SUPPRESSED if status == NotificationStatus.SUPPRESSED else DeliveryOutcome.SENT
        self.delivery_attempts.append(
            DeliveryAttempt(
                delivery_attempt_id=str(uuid4()),
                message_id=message.message_id,
                provider_name="inbox" if channel == NotificationChannel.IN_APP else "mock-provider",
                attempt_number=1,
                attempted_at=now,
                outcome=outcome,
                response_code="202" if sent else "PREFERENCE_BLOCK",
                response_message="delivered" if sent else failure_reason,
                provider_message_id=str(uuid4()) if sent else None,
            )
        )
        self.events.append({
            "event_name": "NotificationSent" if sent else "NotificationSuppressed",
            "message_id": message.message_id,
            "status": message.status.value,
        })
        return message

    def get_message(self, message_id: str) -> NotificationMessage:
        try:
            return self.messages[message_id]
        except KeyError as exc:
            raise NotificationServiceError("MESSAGE_NOT_FOUND", "Notification message not found") from exc

    def list_delivery(
        self,
        *,
        subject_id: str | None = None,
        status: str | None = None,
        channel: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = list(self.messages.values())
        if subject_id is not None and (not isinstance(subject_id, str) or not subject_id.strip()):
            raise NotificationServiceError('VALIDATION_ERROR', 'subject_id filter is invalid', details=[{'field': 'subject_id', 'reason': 'must be a non-empty string'}])
        if subject_id is not None:
            rows = [row for row in rows if row.subject_id == subject_id]
        if status is not None:
            rows = [row for row in rows if row.status.value == status]
        if channel is not None:
            rows = [row for row in rows if row.channel.value == channel]
        rows.sort(key=lambda row: row.queued_at, reverse=True)
        return [self._delivery_view(row) for row in rows]

    def get_inbox(self, *, subject_id: str, unread_only: bool = False) -> dict[str, Any]:
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise NotificationServiceError('VALIDATION_ERROR', 'subject_id is required', details=[{'field': 'subject_id', 'reason': 'must be a non-empty string'}])
        rows = [
            row for row in self.messages.values()
            if row.subject_id == subject_id and row.channel == NotificationChannel.IN_APP
        ]
        if unread_only:
            rows = [row for row in rows if row.read_at is None]
        rows.sort(key=lambda row: row.queued_at, reverse=True)
        items = [self._inbox_view(row) for row in rows]
        unread_count = sum(1 for row in rows if row.read_at is None)
        return {
            "subject_id": subject_id,
            "items": items,
            "summary": {
                "total": len(items),
                "unread": unread_count,
                "sent": sum(1 for row in rows if row.status == NotificationStatus.SENT),
                "suppressed": sum(1 for row in rows if row.status == NotificationStatus.SUPPRESSED),
            },
        }

    def mark_inbox_item_read(self, *, subject_id: str, message_id: str) -> NotificationMessage:
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise NotificationServiceError('VALIDATION_ERROR', 'subject_id is required', details=[{'field': 'subject_id', 'reason': 'must be a non-empty string'}])
        message = self.get_message(message_id)
        if message.subject_id != subject_id or message.channel != NotificationChannel.IN_APP:
            raise NotificationServiceError("FORBIDDEN", "Inbox item does not belong to subject")
        if message.read_at is None:
            message.read_at = self._now()
            message.updated_at = message.read_at
        return message

    def _delivery_view(self, message: NotificationMessage) -> dict[str, Any]:
        attempts = [attempt for attempt in self.delivery_attempts if attempt.message_id == message.message_id]
        last_attempt = attempts[-1] if attempts else None
        return {
            "message_id": message.message_id,
            "template_id": message.template_id,
            "template_code": message.template_code,
            "subject_type": message.subject_type,
            "subject_id": message.subject_id,
            "channel": message.channel.value,
            "destination": message.destination,
            "status": message.status.value,
            "queued_at": message.queued_at.isoformat(),
            "sent_at": message.sent_at.isoformat() if message.sent_at else None,
            "failure_reason": message.failure_reason,
            "last_provider_name": last_attempt.provider_name if last_attempt else None,
            "last_attempt_outcome": last_attempt.outcome.value if last_attempt else None,
            "attempt_count": len(attempts),
            "updated_at": message.updated_at.isoformat(),
        }

    def _inbox_view(self, message: NotificationMessage) -> dict[str, Any]:
        return {
            "message_id": message.message_id,
            "event_name": message.event_name,
            "topic_code": message.topic_code,
            "status": message.status.value,
            "title": message.subject_text or "Notification",
            "body": message.body_text,
            "queued_at": message.queued_at.isoformat(),
            "read_at": message.read_at.isoformat() if message.read_at else None,
            "unread": message.read_at is None,
        }


class _SafePayload(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


def serialize_message(message: NotificationMessage) -> dict[str, Any]:
    payload = asdict(message)
    payload["channel"] = message.channel.value
    payload["status"] = message.status.value
    for field_name in ["queued_at", "sent_at", "read_at", "created_at", "updated_at"]:
        value = payload.get(field_name)
        payload[field_name] = value.isoformat() if value else None
    return payload


def serialize_preference(preference: NotificationPreference) -> dict[str, Any]:
    payload = asdict(preference)
    for field_name in ["created_at", "updated_at"]:
        payload[field_name] = payload[field_name].isoformat()
    return payload
