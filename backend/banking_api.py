from __future__ import annotations

import uuid
from typing import Any

from api_contract import error_payload, success_payload
from bank_service import BankService

SERVICE_NAME = "bank-service"

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
# POST /api/v1/banking/disbursements
# ---------------------------------------------------------------------------

def post_disbursement(
    service: BankService,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Initiate salary disbursement batch for a pay period."""
    required = ("organization_id", "period", "method", "employees")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        return _err("VALIDATION_ERROR", f"Missing required fields: {', '.join(missing)}")
    try:
        batch = service.create_disbursement(
            organization_id=payload["organization_id"],
            period=payload["period"],
            method=payload["method"],
            employees=payload["employees"],
            bank_format=payload.get("bank_format"),
            actor=payload.get("actor", "api"),
        )
    except (ValueError, KeyError) as exc:
        return _err("VALIDATION_ERROR", str(exc))
    return _ok(_serialize_batch(batch), status=201)


# ---------------------------------------------------------------------------
# GET /api/v1/banking/disbursements/{disbursement_id}
# ---------------------------------------------------------------------------

def get_disbursement(
    service: BankService,
    disbursement_id: str,
    authorization: str | None = None,
) -> tuple[int, dict]:
    batch = service.get_disbursement(disbursement_id)
    if batch is None:
        return _err("NOT_FOUND", f"Disbursement {disbursement_id} not found")
    return _ok(_serialize_batch(batch))


# ---------------------------------------------------------------------------
# GET /api/v1/banking/disbursements?period=&status=&limit=&cursor=
# ---------------------------------------------------------------------------

def list_disbursements(
    service: BankService,
    authorization: str | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, dict]:
    params = query or {}
    results = service.list_disbursements(
        period=params.get("period"),
        status=params.get("status"),
        limit=int(params.get("limit", 50)),
        cursor=params.get("cursor"),
    )
    return _ok({"items": [_serialize_batch(b) for b in results], "count": len(results)})


# ---------------------------------------------------------------------------
# POST /api/v1/banking/disbursements/{disbursement_id}/execute
# ---------------------------------------------------------------------------

def execute_disbursement(
    service: BankService,
    disbursement_id: str,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Trigger bank/Raast export generation and mark as SUBMITTED."""
    try:
        result = service.execute_disbursement(
            disbursement_id=disbursement_id,
            payroll_data=payload.get("payroll_data", {}),
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        msg = str(exc)
        code = "NOT_FOUND" if "not found" in msg else "PRECONDITION_FAILED"
        return _err(code, msg)
    return _ok(result)


# ---------------------------------------------------------------------------
# GET /api/v1/banking/payments?disbursement_id=&employee_id=&status=
# ---------------------------------------------------------------------------

def list_payments(
    service: BankService,
    authorization: str | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, dict]:
    params = query or {}
    results = service.list_payments(
        disbursement_id=params.get("disbursement_id"),
        employee_id=params.get("employee_id"),
        status=params.get("status"),
        limit=int(params.get("limit", 100)),
        cursor=params.get("cursor"),
    )
    return _ok({
        "items": [_serialize_payment(p) for p in results],
        "count": len(results),
    })


# ---------------------------------------------------------------------------
# POST /api/v1/banking/reconcile
# ---------------------------------------------------------------------------

def post_reconciliation(
    service: BankService,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Run reconciliation for a disbursement batch."""
    disbursement_id = payload.get("disbursement_id")
    if not disbursement_id:
        return _err("VALIDATION_ERROR", "disbursement_id is required")
    try:
        report = service.run_reconciliation(
            disbursement_id=disbursement_id,
            payroll_rows=payload.get("payroll", []),
            payment_rows=payload.get("payments", []),
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        return _err("VALIDATION_ERROR", str(exc))
    return _ok(_serialize_reconciliation(report), status=201)


# ---------------------------------------------------------------------------
# GET /api/v1/banking/reconciliation/{reconciliation_id}
# ---------------------------------------------------------------------------

def get_reconciliation(
    service: BankService,
    reconciliation_id: str,
    authorization: str | None = None,
) -> tuple[int, dict]:
    report = service.get_reconciliation(reconciliation_id)
    if report is None:
        return _err("NOT_FOUND", f"Reconciliation {reconciliation_id} not found")
    return _ok(_serialize_reconciliation(report))


# ---------------------------------------------------------------------------
# POST /api/v1/banking/raast/payout
# ---------------------------------------------------------------------------

def post_raast_payout(
    service: BankService,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    """Single Raast payout for EWA or salary advance."""
    required = ("batch_id", "company", "payments")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        return _err("VALIDATION_ERROR", f"Missing required fields: {', '.join(missing)}")
    try:
        result = service.raast_payout(
            batch_id=payload["batch_id"],
            company=payload["company"],
            payments=payload["payments"],
            payroll_total=payload.get("payroll_total"),
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        return _err("VALIDATION_ERROR", str(exc))
    return _ok(result, status=201)


# ---------------------------------------------------------------------------
# GET /api/v1/banking/accounts?employee_id=
# ---------------------------------------------------------------------------

def get_bank_accounts(
    service: BankService,
    authorization: str | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, dict]:
    employee_id = (query or {}).get("employee_id")
    if not employee_id:
        return _err("VALIDATION_ERROR", "employee_id is required")
    accounts = service.get_bank_accounts(employee_id)
    return _ok({
        "items": [_serialize_account(a) for a in accounts],
        "count": len(accounts),
    })


# ---------------------------------------------------------------------------
# POST /api/v1/banking/accounts
# ---------------------------------------------------------------------------

def post_bank_account(
    service: BankService,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    required = ("employee_id", "organization_id", "iban", "bank_code", "account_holder")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        return _err("VALIDATION_ERROR", f"Missing required fields: {', '.join(missing)}")
    try:
        acct = service.register_bank_account(
            employee_id=payload["employee_id"],
            organization_id=payload["organization_id"],
            iban=payload["iban"],
            bank_code=payload["bank_code"],
            account_holder=payload["account_holder"],
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        return _err("VALIDATION_ERROR", str(exc))
    return _ok(_serialize_account(acct), status=201)


# ---------------------------------------------------------------------------
# PATCH /api/v1/banking/accounts/{account_id}
# ---------------------------------------------------------------------------

def patch_bank_account(
    service: BankService,
    account_id: str,
    payload: dict[str, Any],
    authorization: str | None = None,
) -> tuple[int, dict]:
    try:
        acct = service.update_bank_account(
            account_id=account_id,
            updates=payload,
            actor=payload.get("actor", "api"),
        )
    except ValueError as exc:
        msg = str(exc)
        return _err("NOT_FOUND" if "not found" in msg else "VALIDATION_ERROR", msg)
    return _ok(_serialize_account(acct))


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

def _serialize_batch(b) -> dict:
    return {
        "disbursement_id": b.disbursement_id,
        "organization_id": b.organization_id,
        "period": b.period,
        "method": b.method,
        "state": b.state,
        "employee_count": b.employee_count,
        "total_amount": b.total_amount,
        "bank_format": b.bank_format,
        "submitted_at": b.submitted_at,
        "confirmed_at": b.confirmed_at,
        "created_at": b.created_at,
        "updated_at": b.updated_at,
    }


def _serialize_payment(p) -> dict:
    return {
        "payment_id": p.payment_id,
        "disbursement_id": p.disbursement_id,
        "employee_id": p.employee_id,
        "expected_amount": p.expected_amount,
        "paid_amount": p.paid_amount,
        "status": p.status,
        "failure_reason": p.failure_reason,
        "confirmed_at": p.confirmed_at,
        "created_at": p.created_at,
    }


def _serialize_reconciliation(r) -> dict:
    return {
        "reconciliation_id": r.reconciliation_id,
        "disbursement_id": r.disbursement_id,
        "period": r.period,
        "summary": r.summary,
        "mismatches": r.mismatches,
        "missing_payments": r.missing_payments,
        "failures": r.failures,
        "unmatched_payments": r.unmatched_payments,
        "created_at": r.created_at,
    }


def _serialize_account(a) -> dict:
    return {
        "account_id": a.account_id,
        "employee_id": a.employee_id,
        "organization_id": a.organization_id,
        "iban": a.iban,
        "bank_code": a.bank_code,
        "account_holder": a.account_holder,
        "is_primary": a.is_primary,
        "is_verified": a.is_verified,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
    }
