from __future__ import annotations

import hashlib
import hmac
from decimal import Decimal
from typing import Any
from uuid import uuid4

from config.integrations import load_integrations_config
from integrations.http_client import IntegrationHTTPError, JsonHTTPClient, RetryPolicy
from integrations.pakistan.submission_tracking import DEFAULT_SUBMISSION_TRACKER, SubmissionTracker


_REQUIRED_TOP_LEVEL_KEYS = {"tax_year", "period", "employer", "totals", "employees"}
_REQUIRED_PERIOD_KEYS = {"month", "year"}
_REQUIRED_EMPLOYER_KEYS = {"ntn", "name", "address", "withholding_agent_cnic_ntn"}
_REQUIRED_TOTAL_KEYS = {"total_employees", "total_taxable_income", "total_tax_deducted"}
_REQUIRED_EMPLOYEE_KEYS = {
    "employee_id",
    "cnic",
    "full_name",
    "tax_status",
    "annual_gross_income",
    "annual_taxable_income",
    "tax_slab_code",
    "annual_tax",
    "monthly_tax_deducted",
    "exemptions",
}


def _is_non_negative_number(value: Any) -> bool:
    try:
        return Decimal(str(value)) >= 0
    except Exception:
        return False


def _validate_annexure_c_payload(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    missing = _REQUIRED_TOP_LEVEL_KEYS.difference(payload.keys())
    if missing:
        errors.append(f"Missing top-level keys: {sorted(missing)}")
        return False, errors

    period = payload.get("period")
    employer = payload.get("employer")
    totals = payload.get("totals")
    employees = payload.get("employees")

    if not isinstance(period, dict) or _REQUIRED_PERIOD_KEYS.difference(period.keys()):
        errors.append("Invalid period shape; expected month and year.")

    if not isinstance(employer, dict) or _REQUIRED_EMPLOYER_KEYS.difference(employer.keys()):
        errors.append("Invalid employer shape; required FBR employer metadata is missing.")

    if not isinstance(totals, dict) or _REQUIRED_TOTAL_KEYS.difference(totals.keys()):
        errors.append("Invalid totals shape for Annexure-C.")

    if not isinstance(employees, list):
        errors.append("employees must be an array.")
        employees = []

    for idx, employee in enumerate(employees):
        if not isinstance(employee, dict):
            errors.append(f"employees[{idx}] must be an object.")
            continue

        missing_employee = _REQUIRED_EMPLOYEE_KEYS.difference(employee.keys())
        if missing_employee:
            errors.append(f"employees[{idx}] missing keys: {sorted(missing_employee)}")

        cnic = str(employee.get("cnic", "")).strip()
        if len(cnic) != 13 or not cnic.isdigit():
            errors.append(f"employees[{idx}] invalid CNIC.")

        for field in ("annual_gross_income", "annual_taxable_income", "annual_tax", "monthly_tax_deducted"):
            if not _is_non_negative_number(employee.get(field, 0)):
                errors.append(f"employees[{idx}] {field} must be numeric and >= 0.")

    if isinstance(totals, dict):
        if totals.get("total_employees") != len(employees):
            errors.append("totals.total_employees does not match employees count.")
        sum_monthly = sum(Decimal(str(e.get("monthly_tax_deducted", 0))) for e in employees if isinstance(e, dict))
        if Decimal(str(totals.get("total_tax_deducted", 0))).quantize(Decimal("0.01")) != sum_monthly.quantize(Decimal("0.01")):
            errors.append("totals.total_tax_deducted does not match employee monthly tax sum.")

    return len(errors) == 0, errors


def _signature(secret: str, submission_id: str, ntn: str) -> str:
    to_sign = f"{submission_id}:{ntn}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), to_sign, hashlib.sha256).hexdigest()


def submit_annexure_c(
    payload: dict[str, Any],
    *,
    http_client: JsonHTTPClient | None = None,
    config: dict[str, Any] | None = None,
    tracker: SubmissionTracker | None = None,
) -> dict[str, Any]:
    is_valid, errors = _validate_annexure_c_payload(payload)
    submission_id = f"fbr_{uuid4().hex[:12]}"
    track = tracker or DEFAULT_SUBMISSION_TRACKER
    track.create_pending(submission_id, "FBR", "annexure_c", payload)
    if not is_valid:
        result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "FBR", "format": "annexure_c", "errors": errors, "response_payload": {"errors": errors}}
        track.mark_failed(submission_id, result["response_payload"])
        return result

    cfg = config or {}
    shared = load_integrations_config().fbr
    base_url = str(cfg.get("base_url") or shared.endpoint).rstrip("/")
    token = str(cfg.get("auth_token") or shared.auth_token)
    signing_secret = str(cfg.get("signing_secret") or "")
    timeout = float(cfg.get("timeout_seconds") or shared.timeout_seconds)
    attempts = int(cfg.get("retry_attempts") or shared.retry_attempts)

    if not base_url or not token:
        errors = ["Missing FBR integration configuration (base_url/auth_token)."]
        result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "FBR", "format": "annexure_c", "errors": errors, "response_payload": {"errors": errors}}
        track.mark_failed(submission_id, result["response_payload"])
        return result

    client = http_client or JsonHTTPClient(timeout_seconds=timeout, retry_policy=RetryPolicy(attempts=attempts))
    endpoint = f"{base_url}/annexure-c/submissions"
    headers = {"Authorization": f"Bearer {token}", "X-Submission-Id": submission_id}
    if signing_secret:
        headers["X-Signature"] = _signature(signing_secret, submission_id, str(payload.get("employer", {}).get("ntn", "")))

    try:
        response = client.post_json(endpoint, payload, headers=headers)
        body = response.get("body", {})
        ack_id = body.get("ack_id")
        if not ack_id:
            result = {"status": "failed", "submitted": False, "submission_status": "failed", "submission_id": submission_id, "provider": "FBR", "format": "annexure_c", "errors": ["FBR response missing ack_id."], "response_payload": body}
            track.mark_failed(submission_id, body)
            return result
        result = {
            "status": "submitted",
            "submitted": True,
            "submission_status": "submitted",
            "submission_id": submission_id,
            "provider": "FBR",
            "format": "annexure_c",
            "errors": [],
            "ack_id": str(ack_id),
            "provider_status": str(body.get("status", "accepted")),
            "response_payload": body,
        }
        track.mark_submitted(submission_id, body)
        return result
    except IntegrationHTTPError as exc:
        response_payload = {"code": exc.code, "message": exc.message, "status_code": exc.status_code}
        result = {
            "status": "failed",
            "submitted": False,
            "submission_status": "failed",
            "submission_id": submission_id,
            "provider": "FBR",
            "format": "annexure_c",
            "errors": [f"{exc.code}: {exc.message}"],
            "http_status": exc.status_code,
            "response_payload": response_payload,
        }
        track.mark_failed(submission_id, response_payload)
        return result
