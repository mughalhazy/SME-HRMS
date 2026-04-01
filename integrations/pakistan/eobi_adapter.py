from __future__ import annotations

from typing import Any
from uuid import uuid4

from config.integrations import load_integrations_config
from integrations.http_client import IntegrationHTTPError, JsonHTTPClient, RetryPolicy
from integrations.pakistan.submission_tracking import DEFAULT_SUBMISSION_TRACKER, SubmissionTracker


_REQUIRED_KEYS = {"submission_format", "period", "employer", "employees"}


def _validate_pr01_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = _REQUIRED_KEYS.difference(payload.keys())
    if missing:
        errors.append(f"Missing top-level keys: {sorted(missing)}")

    if str(payload.get("submission_format", "")).strip().upper() != "PR-01":
        errors.append("submission_format must be PR-01")

    period = payload.get("period")
    if not isinstance(period, dict) or "month" not in period or "year" not in period:
        errors.append("Invalid period shape; expected month/year.")

    employer = payload.get("employer")
    if not isinstance(employer, dict) or not str(employer.get("registration_number", "")).strip():
        errors.append("Missing employer registration_number.")

    employees = payload.get("employees")
    if not isinstance(employees, list) or len(employees) == 0:
        errors.append("employees must be a non-empty array.")

    return errors


def submit_pr01(
    payload: dict[str, Any],
    *,
    http_client: JsonHTTPClient | None = None,
    config: dict[str, Any] | None = None,
    tracker: SubmissionTracker | None = None,
) -> dict[str, Any]:
    submission_id = f"eobi_{uuid4().hex[:12]}"
    track = tracker or DEFAULT_SUBMISSION_TRACKER
    track.create_pending(submission_id, "EOBI", "pr_01", payload)

    errors = _validate_pr01_payload(payload)
    if errors:
        result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "EOBI", "format": "pr_01", "errors": errors, "response_payload": {"errors": errors}}
        track.mark_failed(submission_id, result["response_payload"])
        return result

    cfg = config or {}
    shared = load_integrations_config().eobi
    base_url = str(cfg.get("base_url") or shared.endpoint).rstrip("/")
    token = str(cfg.get("auth_token") or shared.auth_token)
    timeout = float(cfg.get("timeout_seconds") or shared.timeout_seconds)
    attempts = int(cfg.get("retry_attempts") or shared.retry_attempts)
    if not base_url or not token:
        errors = ["Missing EOBI integration configuration (base_url/auth_token)."]
        result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "EOBI", "format": "pr_01", "errors": errors, "response_payload": {"errors": errors}}
        track.mark_failed(submission_id, result["response_payload"])
        return result

    client = http_client or JsonHTTPClient(timeout_seconds=timeout, retry_policy=RetryPolicy(attempts=attempts))
    try:
        response = client.post_json(
            f"{base_url}/pr-01/submissions",
            payload,
            headers={"Authorization": f"Bearer {token}", "X-Submission-Id": submission_id},
        )
        body = response.get("body", {})
        if not body.get("ack_id"):
            errors = ["EOBI response missing ack_id."]
            result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "EOBI", "format": "pr_01", "errors": errors, "response_payload": body}
            track.mark_failed(submission_id, body)
            return result
        result = {"status": "submitted", "submitted": True, "submission_status": "submitted", "submission_id": submission_id, "provider": "EOBI", "format": "pr_01", "errors": [], "ack_id": str(body["ack_id"]), "response_payload": body}
        track.mark_submitted(submission_id, body)
        return result
    except IntegrationHTTPError as exc:
        response_payload = {"code": exc.code, "message": exc.message, "status_code": exc.status_code}
        result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "EOBI", "format": "pr_01", "errors": [f"{exc.code}: {exc.message}"], "http_status": exc.status_code, "response_payload": response_payload}
        track.mark_failed(submission_id, response_payload)
        return result
