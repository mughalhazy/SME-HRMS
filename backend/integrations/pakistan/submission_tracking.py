from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from audit_service.service import emit_audit_record


LIFECYCLE_STATES = ("DRAFT", "VALIDATED", "SUBMITTED", "ACKNOWLEDGED", "FAILED", "RETRY")
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"VALIDATED", "FAILED"},
    "VALIDATED": {"SUBMITTED", "FAILED"},
    "SUBMITTED": {"ACKNOWLEDGED", "FAILED"},
    "FAILED": {"RETRY"},
    "RETRY": {"SUBMITTED", "FAILED"},
    "ACKNOWLEDGED": set(),
}


@dataclass
class SubmissionRecord:
    submission_id: str
    provider: str
    submission_format: str
    status: str
    request_payload: dict[str, Any]
    response_payload: dict[str, Any]
    attempt_count: int = 0
    history: list[dict[str, Any]] | None = None


class SubmissionTracker:
    def __init__(self, *, persistence_path: str | None = None) -> None:
        self._records: dict[str, SubmissionRecord] = {}
        self._persistence_path = Path(persistence_path) if persistence_path else Path(tempfile.gettempdir()) / "sme-hrms" / "pakistan-submissions.json"
        self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _load(self) -> None:
        if not self._persistence_path.exists():
            return
        raw = json.loads(self._persistence_path.read_text(encoding="utf-8"))
        for item in raw.get("records", []):
            self._records[item["submission_id"]] = SubmissionRecord(**item)

    def _persist(self) -> None:
        payload = {
            "records": [
                {
                    "submission_id": record.submission_id,
                    "provider": record.provider,
                    "submission_format": record.submission_format,
                    "status": record.status,
                    "request_payload": record.request_payload,
                    "response_payload": record.response_payload,
                    "attempt_count": record.attempt_count,
                    "history": list(record.history or []),
                }
                for record in self._records.values()
            ]
        }
        self._persistence_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    def _audit(self, submission_id: str, before: str, after: str, metadata: dict[str, Any] | None = None) -> None:
        emit_audit_record(
            service_name="pakistan_submission_tracker",
            tenant_id="default",
            actor={"id": "system", "type": "system"},
            action="SUBMISSION_STATUS_CHANGED",
            entity="compliance_submission",
            entity_id=submission_id,
            before={"status": before},
            after={"status": after, **(metadata or {})},
            trace_id=submission_id,
            source={"provider": self._records.get(submission_id).provider if self._records.get(submission_id) else None},
        )

    def _transition(self, submission_id: str, to_state: str, *, response_payload: dict[str, Any] | None = None, details: dict[str, Any] | None = None) -> None:
        record = self._records.get(submission_id)
        if not record:
            return
        if to_state not in LIFECYCLE_STATES:
            return
        allowed = _ALLOWED_TRANSITIONS.get(record.status, set())
        if to_state not in allowed:
            return
        before = record.status
        record.status = to_state
        if response_payload is not None:
            record.response_payload = response_payload
        record.history = list(record.history or [])
        record.history.append({"from": before, "to": to_state, "at": self._now(), "details": details or {}})
        if to_state == "SUBMITTED":
            record.attempt_count += 1
        self._persist()
        self._audit(submission_id, before, to_state, {"attempt_count": record.attempt_count, **(details or {})})

    def create_pending(self, submission_id: str, provider: str, submission_format: str, payload: dict[str, Any]) -> None:
        self._records[submission_id] = SubmissionRecord(
            submission_id=submission_id,
            provider=provider,
            submission_format=submission_format,
            status="DRAFT",
            request_payload=payload,
            response_payload={},
            history=[],
        )
        self._persist()
        self._audit(submission_id, "NONE", "DRAFT")

    def mark_validated(self, submission_id: str) -> None:
        self._transition(submission_id, "VALIDATED")

    def mark_submitted(self, submission_id: str, response_payload: dict[str, Any]) -> None:
        self._transition(submission_id, "SUBMITTED", response_payload=response_payload)

    def mark_acknowledged(self, submission_id: str, response_payload: dict[str, Any]) -> None:
        self._transition(submission_id, "ACKNOWLEDGED", response_payload=response_payload)

    def mark_failed(self, submission_id: str, response_payload: dict[str, Any]) -> None:
        self._transition(submission_id, "FAILED", response_payload=response_payload)

    def mark_retry(self, submission_id: str, reason: str) -> None:
        self._transition(submission_id, "RETRY", details={"reason": reason})

    def export_for_manual_fallback(self) -> list[dict[str, Any]]:
        return [
            {
                "submission_id": record.submission_id,
                "provider": record.provider,
                "format": record.submission_format,
                "status": record.status,
                "attempt_count": record.attempt_count,
                "request_payload": record.request_payload,
            }
            for record in self._records.values()
            if record.status in {"FAILED", "RETRY"}
        ]

    def reconcile_manual_ack(self, submission_id: str, ack_payload: dict[str, Any]) -> bool:
        record = self._records.get(submission_id)
        if not record:
            return False
        if record.status not in {"FAILED", "RETRY", "SUBMITTED"}:
            return False
        if record.status in {"FAILED", "RETRY"}:
            # Recover to a submitted state before provider acknowledgement.
            if record.status == "FAILED":
                self.mark_retry(submission_id, "manual-reconcile")
            self.mark_submitted(submission_id, ack_payload)
        self.mark_acknowledged(submission_id, ack_payload)
        return True

    def get(self, submission_id: str) -> SubmissionRecord | None:
        return self._records.get(submission_id)


DEFAULT_SUBMISSION_TRACKER = SubmissionTracker()
