from __future__ import annotations

from typing import Any
from uuid import uuid4

from config.integrations import load_integrations_config
from integrations.http_client import IntegrationHTTPError, JsonHTTPClient, RetryPolicy
from integrations.pakistan.submission_tracking import DEFAULT_SUBMISSION_TRACKER, SubmissionTracker


_REQUIRED_KEYS = {"period", "establishment", "employees"}


def submit_contribution_return(
    payload: dict[str, Any],
    *,
    http_client: JsonHTTPClient | None = None,
    config: dict[str, Any] | None = None,
    tracker: SubmissionTracker | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    missing = _REQUIRED_KEYS.difference(payload.keys())
    if missing:
        errors.append(f"Missing top-level keys: {sorted(missing)}")

    establishment = payload.get("establishment")
    if not isinstance(establishment, dict) or "registration_number" not in establishment:
        errors.append("Missing establishment registration_number.")
    if not isinstance(payload.get("employees"), list):
        errors.append("employees must be an array.")

    submission_id = f"pessi_{uuid4().hex[:12]}"
    track = tracker or DEFAULT_SUBMISSION_TRACKER
    track.create_pending(submission_id, "PESSI_SESSI", "contribution_return", payload)

    if errors:
        result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "PESSI_SESSI", "format": "contribution_return", "errors": errors, "response_payload": {"errors": errors}}
        track.mark_failed(submission_id, result["response_payload"])
        return result

    cfg = config or {}
    shared = load_integrations_config().pessi
    base_url = str(cfg.get("base_url") or shared.endpoint).rstrip("/")
    token = str(cfg.get("auth_token") or shared.auth_token)
    timeout = float(cfg.get("timeout_seconds") or shared.timeout_seconds)
    attempts = int(cfg.get("retry_attempts") or shared.retry_attempts)
    if not base_url or not token:
        errors = ["Missing PESSI integration configuration (base_url/auth_token)."]
        result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "PESSI_SESSI", "format": "contribution_return", "errors": errors, "response_payload": {"errors": errors}}
        track.mark_failed(submission_id, result["response_payload"])
        return result

    client = http_client or JsonHTTPClient(timeout_seconds=timeout, retry_policy=RetryPolicy(attempts=attempts))
    try:
        response = client.post_json(
            f"{base_url}/contribution-returns",
            payload,
            headers={"Authorization": f"Bearer {token}", "X-Submission-Id": submission_id},
        )
        body = response.get("body", {})
        if not body.get("ack_id"):
            errors = ["PESSI response missing ack_id."]
            result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "PESSI_SESSI", "format": "contribution_return", "errors": errors, "response_payload": body}
            track.mark_failed(submission_id, body)
            return result

        result = {"status": "submitted", "submitted": True, "submission_status": "submitted", "submission_id": submission_id, "provider": "PESSI_SESSI", "format": "contribution_return", "errors": [], "ack_id": str(body["ack_id"]), "response_payload": body}
        track.mark_submitted(submission_id, body)
        return result
    except IntegrationHTTPError as exc:
        response_payload = {"code": exc.code, "message": exc.message, "status_code": exc.status_code}
        result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "PESSI_SESSI", "format": "contribution_return", "errors": [f"{exc.code}: {exc.message}"], "http_status": exc.status_code, "response_payload": response_payload}
        track.mark_failed(submission_id, response_payload)
        return result
