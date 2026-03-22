from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

CANONICAL_EVENT_TYPES: dict[str, str] = {
    "EmployeeCreated": "employee.created",
    "EmployeeUpdated": "employee.updated",
    "EmployeeStatusChanged": "employee.status.changed",
    "PerformanceReviewCycleCreated": "performance.review_cycle.created",
    "PerformanceReviewCycleOpened": "performance.review_cycle.opened",
    "PerformanceReviewCycleClosed": "performance.review_cycle.closed",
    "PerformanceGoalCreated": "performance.goal.created",
    "PerformanceGoalSubmitted": "performance.goal.submitted",
    "PerformanceGoalApproved": "performance.goal.approved",
    "PerformanceGoalRejected": "performance.goal.rejected",
    "PerformanceFeedbackRecorded": "performance.feedback.recorded",
    "PerformanceCalibrationCreated": "performance.calibration.created",
    "PerformanceCalibrationSubmitted": "performance.calibration.submitted",
    "PerformanceCalibrationFinalized": "performance.calibration.finalized",
    "PerformanceCalibrationRejected": "performance.calibration.rejected",
    "PerformancePipCreated": "performance.pip.created",
    "PerformancePipSubmitted": "performance.pip.submitted",
    "PerformancePipActive": "performance.pip.active",
    "PerformancePipRejected": "performance.pip.rejected",
    "PerformancePipProgressUpdated": "performance.pip.progress_updated",
    "LeaveRequestSubmitted": "leave.request.submitted",
    "LeaveRequestApproved": "leave.request.approved",
    "LeaveRequestRejected": "leave.request.rejected",
    "LeaveRequestCancelled": "leave.request.cancelled",
    "AttendanceCaptured": "attendance.record.captured",
    "AttendanceLogged": "attendance.record.logged",
    "AttendanceCorrected": "attendance.record.corrected",
    "AttendanceApproved": "attendance.record.approved",
    "AttendanceLocked": "attendance.period.locked",
    "AttendancePeriodClosed": "attendance.period.closed",
    "AttendanceSyncedFromLeave": "attendance.leave.synced",
    "AttendanceAbsenceAlertsGenerated": "attendance.absence_alert.generated",
    "AttendanceValidated": "attendance.record.validated",
    "PayrollDrafted": "payroll.record.drafted",
    "PayrollProcessed": "payroll.record.processed",
    "PayrollPaid": "payroll.record.paid",
    "PayrollCancelled": "payroll.record.cancelled",
    "PayrollMonthlyTriggerExecuted": "payroll.run.monthly_trigger_executed",
    "PayrollRecordRejected": "payroll.record.rejected",
    "PayrollRecordFailed": "payroll.record.failed",
    "JobPostingOpened": "hiring.job_posting.opened",
    "JobPostingOnHold": "hiring.job_posting.on_hold",
    "RequisitionCreated": "hiring.requisition.created",
    "RequisitionSubmitted": "hiring.requisition.submitted",
    "RequisitionApproved": "hiring.requisition.approved",
    "JobPostingClosed": "hiring.job_posting.closed",
    "CandidateApplied": "hiring.candidate.applied",
    "CandidateStageChanged": "hiring.candidate.stage.changed",
    "CandidateStageTransitionRecorded": "hiring.candidate.stage_transition.recorded",
    "InterviewScheduled": "hiring.interview.scheduled",
    "InterviewCalendarSynced": "hiring.interview.calendar_synced",
    "InterviewCompleted": "hiring.interview.completed",
    "CandidateHired": "hiring.candidate.hired",
    "CandidateImported": "hiring.candidate.imported",
    "LinkedInCandidatesImported": "hiring.linkedin_candidates.imported",
    "OfferCreated": "hiring.offer.created",
    "OfferApprovalRequested": "hiring.offer.approval_requested",
    "OfferApproved": "hiring.offer.approved",
    "OfferSent": "hiring.offer.sent",
    "OfferAccepted": "hiring.offer.accepted",
    "OfferDeclined": "hiring.offer.declined",
    "OnboardingHandoffReady": "hiring.onboarding.handoff_ready",
    "NotificationQueued": "notification.message.queued",
    "NotificationSent": "notification.message.sent",
    "NotificationFailed": "notification.message.failed",
    "NotificationSuppressed": "notification.message.suppressed",
    "DocumentStored": "employee.document.stored",
    "DocumentUpdated": "employee.document.updated",
    "DocumentExpiryTracked": "employee.document.expiry.tracked",
    "PolicyAcknowledged": "employee.policy.acknowledged",
    "ComplianceTaskCreated": "employee.compliance.task.created",
    "ComplianceTaskAssigned": "employee.compliance.task.assigned",
    "ComplianceTaskCompleted": "employee.compliance.task.completed",
    "ContractActivated": "employee.contract.activated",
    "UserProvisioned": "auth.user.provisioned",
    "UserAuthenticated": "auth.user.authenticated",
    "SessionRevoked": "auth.session.revoked",
    "RefreshTokenRotated": "auth.refresh_token.rotated",
    "RoleBindingChanged": "auth.role_binding.changed",
    "AuthorizationPolicyUpdated": "auth.authorization.policy.updated",
    "TravelRequestCreated": "travel.request.created",
    "TravelRequestSubmitted": "travel.request.submitted",
    "TravelRequestApproved": "travel.request.approved",
    "TravelRequestRejected": "travel.request.rejected",
    "TravelItineraryUpdated": "travel.itinerary.updated",
    "TravelRequestCancelled": "travel.request.cancelled",
    "TravelRequestCompleted": "travel.request.completed",
}

LEGACY_EVENT_NAMES = {value: key for key, value in CANONICAL_EVENT_TYPES.items()}
_RESERVED_KEYS = {
    "event_id",
    "event_type",
    "event_name",
    "type",
    "tenant_id",
    "timestamp",
    "occurred_at",
    "source",
    "producer_service",
    "trace_id",
    "data",
    "metadata",
}


class EventContractError(ValueError):
    """Raised when an event cannot satisfy the canonical event contract."""


@dataclass
class EventRegistry:
    events_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    events_by_idempotency_key: dict[str, dict[str, Any]] = field(default_factory=dict)

    def register(self, event: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        event_id = str(event["event_id"])
        metadata = event.get("metadata", {})
        idempotency_key = metadata.get("idempotency_key")
        fingerprint = _event_fingerprint(event)

        if event_id in self.events_by_id:
            existing = self.events_by_id[event_id]
            existing_fingerprint = _event_fingerprint(existing)
            if idempotency_key and existing_fingerprint == fingerprint:
                return existing, True
            raise EventContractError("non_idempotent_events")

        if idempotency_key:
            compound_key = f"{event['tenant_id']}::{event['event_type']}::{idempotency_key}"
            existing = self.events_by_idempotency_key.get(compound_key)
            if existing is not None:
                if _event_fingerprint(existing) != fingerprint:
                    raise EventContractError("non_idempotent_events")
                return existing, True

        self.events_by_id[event_id] = event
        if idempotency_key:
            self.events_by_idempotency_key[f"{event['tenant_id']}::{event['event_type']}::{idempotency_key}"] = event
        return event, False


def normalize_event_type(raw: str) -> str:
    candidate = str(raw or "").strip()
    if not candidate:
        raise EventContractError("invalid_event_structure")
    if candidate in CANONICAL_EVENT_TYPES:
        return CANONICAL_EVENT_TYPES[candidate]
    if "." in candidate:
        parts = [segment for segment in candidate.split(".") if segment]
        return ".".join(_normalize_segment(part) for part in parts)
    normalized = candidate.replace("-", ".").replace("_", ".")
    if "." in normalized:
        parts = [segment for segment in normalized.split(".") if segment]
        return ".".join(_normalize_segment(part) for part in parts)
    pieces = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z]|$)", candidate)
    if not pieces:
        return candidate.lower()
    return ".".join(piece.lower() for piece in pieces)


def legacy_event_name_for(event_type: str) -> str:
    normalized = normalize_event_type(event_type)
    return LEGACY_EVENT_NAMES.get(normalized, normalized)


def ensure_event_contract(
    payload: dict[str, Any],
    *,
    source: str,
    tenant_id: str | None = None,
    correlation_id: str | None = None,
    idempotency_key: str | None = None,
    registry: EventRegistry | None = None,
) -> tuple[dict[str, Any], bool]:
    raw = deepcopy(payload)
    event, auto_fixed = _normalize_structure(
        raw,
        source=source,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
    )
    qc_results = _qc_checks(event)
    if not all(item["passed"] for item in qc_results):
        failure = next(item["name"] for item in qc_results if not item["passed"])
        if failure == "tenant_id_present":
            raise EventContractError("missing_tenant_context")
        raise EventContractError("invalid_event_structure")

    duplicate = False
    if registry is not None:
        event, duplicate = registry.register(event)

    re_qc = _re_qc_checks(event, duplicate=duplicate)
    if not all(item["passed"] for item in re_qc):
        failure = next(item["name"] for item in re_qc if not item["passed"])
        if failure == "duplicate_event_handling":
            raise EventContractError("non_idempotent_events")
        raise EventContractError("invalid_event_structure")

    event["metadata"]["qc"] = {
        "checks": qc_results,
        "auto_fixed": auto_fixed,
        "rechecked": re_qc,
        "duplicate": duplicate,
    }
    return event, duplicate


def emit_canonical_event(
    store: list[dict[str, Any]],
    *,
    legacy_event_name: str,
    data: dict[str, Any],
    source: str,
    tenant_id: str,
    registry: EventRegistry,
    correlation_id: str | None = None,
    idempotency_key: str | None = None,
    aliases: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event, duplicate = ensure_event_contract(
        {"event_name": legacy_event_name, "data": data, "tenant_id": tenant_id},
        source=source,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        registry=registry,
    )
    enriched = {
        **event,
        "legacy_event_name": legacy_event_name,
        "type": legacy_event_name,
    }
    if aliases:
        enriched.update(aliases)
    if not duplicate:
        store.append(enriched)
    return enriched


def _normalize_structure(
    raw: dict[str, Any],
    *,
    source: str,
    tenant_id: str | None,
    correlation_id: str | None,
    idempotency_key: str | None,
) -> tuple[dict[str, Any], list[str]]:
    auto_fixed: list[str] = []
    metadata = dict(raw.get("metadata") or {})
    payload_source = str(raw.get("source") or raw.get("producer_service") or source)
    raw_event_type = raw.get("event_type") or raw.get("event_name") or raw.get("type")
    if raw_event_type is None:
        raise EventContractError("invalid_event_structure")
    normalized_event_type = normalize_event_type(str(raw_event_type))
    if raw_event_type != normalized_event_type:
        auto_fixed.append("normalize_event_names")

    if "data" in raw and isinstance(raw.get("data"), dict):
        data = dict(raw["data"])
    else:
        data = {key: value for key, value in raw.items() if key not in _RESERVED_KEYS}
        auto_fixed.append("wrap_payload_in_standard_schema")

    if not raw.get("event_id"):
        auto_fixed.append("generate_event_ids")

    if "version" not in metadata or "correlation_id" not in metadata:
        auto_fixed.append("inject_missing_metadata")

    resolved_tenant_id = raw.get("tenant_id") or tenant_id
    if data.get("tenant_id") and resolved_tenant_id and str(data.get("tenant_id")) != str(resolved_tenant_id):
        raise EventContractError("invalid_event_structure")
    if resolved_tenant_id is not None and "tenant_id" not in data:
        data["tenant_id"] = resolved_tenant_id
        auto_fixed.append("propagate_tenant_context")

    if raw.get("event_name") or raw.get("type"):
        metadata.setdefault("legacy_event_name", str(raw.get("event_name") or raw.get("type")))
    metadata.setdefault("version", "v1")
    metadata.setdefault("correlation_id", correlation_id or str(uuid4()))
    if idempotency_key is not None:
        metadata.setdefault("idempotency_key", str(idempotency_key))
    metadata.setdefault("trace_id", metadata.get("correlation_id"))

    normalized_timestamp = _normalize_timestamp(raw.get("timestamp") or raw.get("occurred_at") or metadata.get("occurred_at"))
    metadata.setdefault("occurred_at", normalized_timestamp)
    metadata.setdefault("producer_service", payload_source)

    legacy_name = str(metadata.get("legacy_event_name") or legacy_event_name_for(normalized_event_type))
    event = {
        "event_id": str(raw.get("event_id") or uuid4()),
        "event_type": normalized_event_type,
        "event_name": legacy_name,
        "tenant_id": resolved_tenant_id,
        "timestamp": normalized_timestamp,
        "occurred_at": normalized_timestamp,
        "source": payload_source,
        "producer_service": payload_source,
        "trace_id": str(metadata["correlation_id"]),
        "data": data,
        "metadata": metadata,
    }
    return event, auto_fixed


def _normalize_timestamp(raw: Any) -> str:
    if raw is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(raw, datetime):
        value = raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(raw)


def _normalize_segment(segment: str) -> str:
    if re.fullmatch(r"[a-z0-9_]+", segment):
        return segment
    pieces = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z]|$)", segment)
    if not pieces:
        return segment.lower()
    return "_".join(piece.lower() for piece in pieces)


def _event_fingerprint(event: dict[str, Any]) -> str:
    return json.dumps(
        {
            "event_type": event["event_type"],
            "tenant_id": event["tenant_id"],
            "source": event["source"],
            "data": event["data"],
        },
        sort_keys=True,
        default=str,
    )


def _qc_checks(event: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"name": "event_naming_valid", "passed": _is_event_name_valid(event.get("event_type"))},
        {"name": "schema_compliant", "passed": _is_schema_compliant(event)},
        {"name": "tenant_id_present", "passed": bool(event.get("tenant_id"))},
        {"name": "tenant_id_propagated_to_payload", "passed": event.get("data", {}).get("tenant_id") == event.get("tenant_id")},
        {"name": "correlation_id_present", "passed": bool(event.get("metadata", {}).get("correlation_id"))},
        {"name": "event_id_unique", "passed": bool(event.get("event_id"))},
    ]


def _re_qc_checks(event: dict[str, Any], *, duplicate: bool) -> list[dict[str, Any]]:
    return [
        {"name": "duplicate_event_handling", "passed": (not duplicate) or bool(event.get("metadata", {}).get("idempotency_key"))},
        {"name": "schema_validation", "passed": _is_schema_compliant(event)},
    ]


def _is_event_name_valid(event_type: Any) -> bool:
    if not isinstance(event_type, str):
        return False
    parts = event_type.split(".")
    return len(parts) >= 2 and all(bool(re.fullmatch(r"[a-z][a-z0-9_]*", part)) for part in parts)


def _is_schema_compliant(event: dict[str, Any]) -> bool:
    try:
        datetime.fromisoformat(str(event["timestamp"]).replace("Z", "+00:00"))
    except Exception:
        return False
    metadata = event.get("metadata")
    return (
        isinstance(event.get("event_id"), str)
        and isinstance(event.get("event_type"), str)
        and isinstance(event.get("event_name"), str)
        and isinstance(event.get("trace_id"), str)
        and isinstance(event.get("source"), str)
        and isinstance(event.get("data"), dict)
        and isinstance(metadata, dict)
        and isinstance(metadata.get("version"), str)
        and isinstance(metadata.get("correlation_id"), str)
    )
