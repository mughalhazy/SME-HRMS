from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any



def _is_valid_mobile(value: str) -> bool:
    normalized = value.replace("+", "").replace("-", "").strip()
    return normalized.isdigit() and len(normalized) in {11, 12}


def _validate_payment(item: dict[str, Any], idx: int) -> list[str]:
    errors: list[str] = []
    if not str(item.get("transaction_id", "")).strip():
        errors.append(f"payments[{idx}].transaction_id is required")
    if not str(item.get("debtor_iban", "")).startswith("PK"):
        errors.append(f"payments[{idx}].debtor_iban must be PK IBAN")

    creditor_iban = str(item.get("creditor_iban", "")).strip()
    creditor_mobile = str(item.get("creditor_mobile", "")).strip()
    if not creditor_iban.startswith("PK") and not _is_valid_mobile(creditor_mobile):
        errors.append(f"payments[{idx}] must include creditor_iban (PK...) or valid creditor_mobile")

    try:
        amount = Decimal(str(item.get("amount", "0")))
        if amount <= 0:
            errors.append(f"payments[{idx}].amount must be > 0")
    except Exception:
        errors.append(f"payments[{idx}].amount must be numeric")
    return errors


def _validate_batch_total(payload: dict[str, Any], transactions: list[dict[str, str]]) -> None:
    payroll_total = payload.get("payroll_total")
    if payroll_total is None:
        return
    txn_total = sum(Decimal(item["amount"]) for item in transactions)
    expected = Decimal(str(payroll_total))
    if txn_total.quantize(Decimal("0.01")) != expected.quantize(Decimal("0.01")):
        raise ValueError(f"raast transaction total {txn_total:.2f} must match payroll_total {expected:.2f}")


def build_raast_payment_export(payload: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    batch_id = str(payload.get("batch_id", f"raast-{int(datetime.now(timezone.utc).timestamp())}"))
    currency = str(payload.get("currency", "PKR"))

    transactions: list[dict[str, str]] = []
    errors: list[str] = []
    payments = list(payload.get("payments", []))
    if not payments:
        errors.append("payments must be a non-empty array")
    for idx, item in enumerate(payments):
        errors.extend(_validate_payment(item, idx))
        transactions.append(
            {
                "transaction_id": str(item.get("transaction_id", "")),
                "amount": f"{Decimal(str(item.get('amount', '0'))):.2f}",
                "currency": str(item.get("currency", currency)),
                "debtor_iban": str(item.get("debtor_iban", "")),
                "creditor_iban": str(item.get("creditor_iban", "")),
                "creditor_mobile": str(item.get("creditor_mobile", "")),
                "narration": str(item.get("narration", "Salary Disbursement")),
                "employee_id": str(item.get("employee_id", "")),
            }
        )

    if errors:
        raise ValueError("; ".join(errors))

    _validate_batch_total(payload, transactions)

    return {
        "payment_network": "RAAST",
        "exported_at": now,
        "batch": {
            "batch_id": batch_id,
            "company": str(payload.get("company", "")),
            "currency": currency,
            "transaction_count": len(transactions),
        },
        "transactions": transactions,
    }
