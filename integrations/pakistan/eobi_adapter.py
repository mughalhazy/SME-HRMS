from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from integrations.http_client import IntegrationHTTPError, JsonHTTPClient, RetryPolicy


_REQUIRED_KEYS = {"period", "employer", "employees"}


def submit_pr01(payload: dict[str, Any], *, http_client: JsonHTTPClient | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    missing = _REQUIRED_KEYS.difference(payload.keys())
    if missing:
        errors.append(f"Missing top-level keys: {sorted(missing)}")

    period = payload.get("period")
    if not isinstance(period, dict) or "month" not in period or "year" not in period:
        errors.append("Invalid period shape; expected month/year.")

    employer = payload.get("employer")
    if not isinstance(employer, dict) or "registration_number" not in employer:
        errors.append("Missing employer registration_number.")

    if not isinstance(payload.get("employees"), list):
        errors.append("employees must be an array.")

    submission_id = f"eobi_{uuid4().hex[:12]}"
    if errors:
        return {"status": "failure", "submitted": False, "submission_id": submission_id, "provider": "EOBI", "format": "pr_01", "errors": errors}

    cfg = config or {}
    base_url = str(cfg.get("base_url") or os.getenv("PAKISTAN_EOBI_BASE_URL", "")).rstrip("/")
    token = str(cfg.get("auth_token") or os.getenv("PAKISTAN_EOBI_AUTH_TOKEN", ""))
    timeout = float(cfg.get("timeout_seconds") or os.getenv("PAKISTAN_EOBI_TIMEOUT_SECONDS", "10"))
    attempts = int(cfg.get("retry_attempts") or os.getenv("PAKISTAN_EOBI_RETRY_ATTEMPTS", "3"))
    if not base_url or not token:
        return {"status": "failure", "submitted": False, "submission_id": submission_id, "provider": "EOBI", "format": "pr_01", "errors": ["Missing EOBI integration configuration (base_url/auth_token)."]}

    client = http_client or JsonHTTPClient(timeout_seconds=timeout, retry_policy=RetryPolicy(attempts=attempts))
    try:
        response = client.post_json(
            f"{base_url}/pr-01/submissions",
            payload,
            headers={"Authorization": f"Bearer {token}", "X-Submission-Id": submission_id},
        )
        body = response.get("body", {})
        if not body.get("ack_id"):
            return {"status": "failure", "submitted": False, "submission_id": submission_id, "provider": "EOBI", "format": "pr_01", "errors": ["EOBI response missing ack_id."]}
        return {"status": "success", "submitted": True, "submission_id": submission_id, "provider": "EOBI", "format": "pr_01", "errors": [], "ack_id": str(body["ack_id"])}
    except IntegrationHTTPError as exc:
        return {"status": "failure", "submitted": False, "submission_id": submission_id, "provider": "EOBI", "format": "pr_01", "errors": [f"{exc.code}: {exc.message}"], "http_status": exc.status_code}
