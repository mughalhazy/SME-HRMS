from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SubmissionRecord:
    submission_id: str
    provider: str
    submission_format: str
    status: str  # pending | submitted | failed
    request_payload: dict[str, Any]
    response_payload: dict[str, Any]


class SubmissionTracker:
    def __init__(self) -> None:
        self._records: dict[str, SubmissionRecord] = {}

    def create_pending(self, submission_id: str, provider: str, submission_format: str, payload: dict[str, Any]) -> None:
        self._records[submission_id] = SubmissionRecord(
            submission_id=submission_id,
            provider=provider,
            submission_format=submission_format,
            status="pending",
            request_payload=payload,
            response_payload={},
        )

    def mark_submitted(self, submission_id: str, response_payload: dict[str, Any]) -> None:
        record = self._records.get(submission_id)
        if not record:
            return
        record.status = "submitted"
        record.response_payload = response_payload

    def mark_failed(self, submission_id: str, response_payload: dict[str, Any]) -> None:
        record = self._records.get(submission_id)
        if not record:
            return
        record.status = "failed"
        record.response_payload = response_payload

    def get(self, submission_id: str) -> SubmissionRecord | None:
        return self._records.get(submission_id)


DEFAULT_SUBMISSION_TRACKER = SubmissionTracker()
