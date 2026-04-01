from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


def _validate_payment(item: dict[str, Any], idx: int) -> list[str]:
    errors: list[str] = []
    if not str(item.get("transaction_id", "")).strip():
        errors.append(f"payments[{idx}].transaction_id is required")
    if not str(item.get("debtor_iban", "")).startswith("PK"):
        errors.append(f"payments[{idx}].debtor_iban must be PK IBAN")
    if not (str(item.get("creditor_iban", "")).startswith("PK") or str(item.get("creditor_mobile", "")).strip()):
        errors.append(f"payments[{idx}] must include creditor_iban or creditor_mobile")
    try:
        amount = Decimal(str(item.get("amount", "0")))
        if amount <= 0:
            errors.append(f"payments[{idx}].amount must be > 0")
    except Exception:
        errors.append(f"payments[{idx}].amount must be numeric")
    return errors


def build_raast_payment_export(payload: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    batch_id = str(payload.get("batch_id", f"raast-{int(datetime.now(timezone.utc).timestamp())}"))
    currency = str(payload.get("currency", "PKR"))

    transactions: list[dict[str, str]] = []
    errors: list[str] = []
    for idx, item in enumerate(list(payload.get("payments", []))):
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
