from __future__ import annotations

import uuid
from typing import Any

from api_contract import error_payload, success_payload
from services.compliance_service import ComplianceService

SERVICE_NAME = "compliance-service"

_ERROR_STATUS = {
    "NOT_FOUND": 404,
    "VALIDATION_ERROR": 422,
    "CONFLICT": 409,
    "FORBIDDEN": 403,
    "PRECONDITION_FAILED": 412,
}


def _ok(data: Any, status: int = 200) -> tuple[int, dict]:
    return status, success_payload(data, str(uuid.uuid4()), service=SERVICE_NAME)


def _err(code: str, message: str) -> tuple[int, dict]:
    return _ERROR_STATUS.get(code, 400), error_payload(code, message, str(uuid.uuid4()), service=SERVICE_NAME)


# ---------------------------------------------------------------------------
# POST /api/v1/compliance/submissions
# ---------------------------------------------------------------------------

def post_compliance_submission(
    service: ComplianceService,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Initiate a compliance submission for a pay period."""
    required = ("organization_id", "legal_entity_id", "period", "submission_type")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        return _err("VALIDATION_ERROR", f"Missing required fields: {', '.join(missing)}")
    try:
        sub = service.create_submission(
            organization_id=payload["organization_id"],
            legal_entity_id=payload["legal_entity_id"],
            period=payload["period"],
            submission_type=payload["submission_type"],
            actor=payload.get("actor", "api"),
        )
    except (ValueError, KeyError) as exc:
        return _err("VALIDATION_ERROR", str(exc))
    return _ok(_serialize_submission(sub), status=201)


# ---------------------------------------------------------------------------
# GET /api/v1/compliance/submissions/{submission_id}
# ---------------------------------------------------------------------------

def get_compliance_submission(
    service: ComplianceService,
    submission_id: str,
    authorization: str | None = None,
) -> tuple[int, dict]:
    sub = service.get_submission(submission_id)
    if sub is None:
        return _err("NOT_FOUND", f"Submission {submission_id} not found")
    return _ok(_serialize_submission(sub))


# ---------------------------------------------------------------------------
# GET /api/v1/compliance/submissions?period=&type=&status=&limit=&cursor=
# ---------------------------------------------------------------------------

def list_compliance_submissions(
    service: ComplianceService,
    authorization: str | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, dict]:
    params = query or {}
    results = service.list_submissions(
        period=params.get("period"),
        submission_type=params.get("type"),
        status=params.get("status"),
        limit=int(params.get("limit", 50)),
        cursor=params.get("cursor"),
    )
    return _ok({"items": [_serialize_submission(s) for s in results], "count": len(results)})


# ---------------------------------------------------------------------------
# POST /api/v1/compliance/submissions/{submission_id}/validate
# ---------------------------------------------------------------------------

def validate_compliance_submission(
    service: ComplianceService,
    submission_id: str,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Run pre-payroll validation gate. Blocks payroll finalization if violations found."""
    try:
        result = service.validate_submission(
            submission_id=submission_id,
            payroll_input=payload.get("payroll_input", {}),
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        msg = str(exc)
        code = "NOT_FOUND" if "not found" in msg else "PRECONDITION_FAILED"
        return _err(code, msg)
    return _ok(result)


# ---------------------------------------------------------------------------
# POST /api/v1/compliance/submissions/{submission_id}/generate
# ---------------------------------------------------------------------------

def generate_compliance_report(
    service: ComplianceService,
    submission_id: str,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Generate statutory report artifacts after validation passes."""
    try:
        artifact = service.generate_report(
            submission_id=submission_id,
            payroll_results=payload.get("payroll_results", {}),
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        msg = str(exc)
        code = "NOT_FOUND" if "not found" in msg else "PRECONDITION_FAILED"
        return _err(code, msg)
    return _ok({"submission_id": submission_id, "artifact": artifact})


# ---------------------------------------------------------------------------
# POST /api/v1/compliance/submissions/{submission_id}/submit
# ---------------------------------------------------------------------------

def submit_compliance(
    service: ComplianceService,
    submission_id: str,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Dispatch validated report to government authority (FBR/EOBI/PESSI)."""
    try:
        result = service.submit(
            submission_id=submission_id,
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        msg = str(exc)
        code = "NOT_FOUND" if "not found" in msg else "PRECONDITION_FAILED"
        return _err(code, msg)
    return _ok(result)


# ---------------------------------------------------------------------------
# POST /api/v1/compliance/submissions/{submission_id}/retry
# ---------------------------------------------------------------------------

def retry_compliance_submission(
    service: ComplianceService,
    submission_id: str,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Retry a failed submission."""
    try:
        result = service.retry(
            submission_id=submission_id,
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        msg = str(exc)
        code = "NOT_FOUND" if "not found" in msg else "PRECONDITION_FAILED"
        return _err(code, msg)
    return _ok(result)


# ---------------------------------------------------------------------------
# GET /api/v1/compliance/submissions/{submission_id}/report
# ---------------------------------------------------------------------------

def get_compliance_report(
    service: ComplianceService,
    submission_id: str,
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Retrieve generated report artifact for a submission."""
    sub = service.get_submission(submission_id)
    if sub is None:
        return _err("NOT_FOUND", f"Submission {submission_id} not found")
    if sub.report_artifact is None:
        return _err("NOT_FOUND", f"No report artifact for submission {submission_id}. Call /generate first.")
    return _ok({"submission_id": submission_id, "report": sub.report_artifact, "state": sub.state})


# ---------------------------------------------------------------------------
# GET /api/v1/compliance/audit?submission_id=&period=&limit=&cursor=
# ---------------------------------------------------------------------------

def get_compliance_audit(
    service: ComplianceService,
    authorization: str | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, dict]:
    """Return immutable compliance audit trail."""
    params = query or {}
    records = service.get_audit_trail(
        submission_id=params.get("submission_id"),
        period=params.get("period"),
        limit=int(params.get("limit", 100)),
        cursor=params.get("cursor"),
    )
    return _ok({
        "items": [
            {
                "audit_id": r.audit_id,
                "submission_id": r.submission_id,
                "from_state": r.from_state,
                "to_state": r.to_state,
                "actor": r.actor,
                "detail": r.detail,
                "recorded_at": r.recorded_at,
            }
            for r in records
        ],
        "count": len(records),
    })


# ---------------------------------------------------------------------------
# Serializer
# ---------------------------------------------------------------------------

def _serialize_submission(sub) -> dict:
    return {
        "submission_id": sub.submission_id,
        "organization_id": sub.organization_id,
        "legal_entity_id": sub.legal_entity_id,
        "period": sub.period,
        "submission_type": sub.submission_type,
        "state": sub.state,
        "is_valid": sub.is_valid,
        "violations": sub.violations,
        "report_artifact": sub.report_artifact,
        "created_at": sub.created_at,
        "updated_at": sub.updated_at,
    }
