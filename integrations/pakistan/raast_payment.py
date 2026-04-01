from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_raast_payment_export(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a Raast-compatible payment export structure."""

    now = datetime.now(timezone.utc).isoformat()
    batch_id = str(payload.get("batch_id", f"raast-{int(datetime.now(timezone.utc).timestamp())}"))
    currency = str(payload.get("currency", "PKR"))

    transactions = []
    for item in list(payload.get("payments", [])):
        transactions.append(
            {
                "transaction_id": str(item.get("transaction_id", "")),
                "amount": str(item.get("amount", "0")),
                "currency": str(item.get("currency", currency)),
                "debtor_iban": str(item.get("debtor_iban", "")),
                "creditor_iban": str(item.get("creditor_iban", "")),
                "creditor_mobile": str(item.get("creditor_mobile", "")),
                "narration": str(item.get("narration", "Salary Disbursement")),
                "employee_id": str(item.get("employee_id", "")),
            }
        )

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
