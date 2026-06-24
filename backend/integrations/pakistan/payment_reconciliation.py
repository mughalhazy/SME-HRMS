from __future__ import annotations

from decimal import Decimal
from typing import Any


FAILURE_STATES = {"failed", "reversed", "rejected", "timeout"}
SUCCESS_STATES = {"success", "posted", "paid", "settled"}


def _money(value: Any) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def reconcile_payroll_payments(payload: dict[str, Any]) -> dict[str, Any]:
    payroll_rows = list(payload.get("payroll", []))
    payment_rows = list(payload.get("payments", []))

    payroll_by_employee = {str(row.get("employee_id", "")): _money(row.get("payout", row.get("net_salary", "0"))) for row in payroll_rows}
    payments_by_employee = {str(row.get("employee_id", "")): row for row in payment_rows}

    matched = 0
    mismatches: list[dict[str, Any]] = []
    missing_payments: list[str] = []
    failures: list[dict[str, Any]] = []

    for employee_id, expected in payroll_by_employee.items():
        payment = payments_by_employee.get(employee_id)
        if payment is None:
            missing_payments.append(employee_id)
            continue

        paid_amount = _money(payment.get("amount", payment.get("paid_amount", "0")))
        status = str(payment.get("status", "success")).strip().lower()

        if status in FAILURE_STATES:
            failures.append(
                {
                    "employee_id": employee_id,
                    "status": status,
                    "expected": f"{expected:.2f}",
                    "paid": f"{paid_amount:.2f}",
                    "reason": str(payment.get("failure_reason", "payment_failed")),
                    "next_action": "retry_payment",
                }
            )
            continue

        if status not in SUCCESS_STATES:
            failures.append(
                {
                    "employee_id": employee_id,
                    "status": status or "unknown",
                    "expected": f"{expected:.2f}",
                    "paid": f"{paid_amount:.2f}",
                    "reason": "unrecognized_payment_status",
                    "next_action": "manual_review",
                }
            )
            continue

        if expected != paid_amount:
            mismatches.append(
                {
                    "employee_id": employee_id,
                    "expected": f"{expected:.2f}",
                    "paid": f"{paid_amount:.2f}",
                    "delta": f"{(expected - paid_amount):.2f}",
                    "next_action": "adjustment_required",
                }
            )
        else:
            matched += 1

    unmatched_payments = [
        str(row.get("employee_id", ""))
        for row in payment_rows
        if str(row.get("employee_id", "")) not in payroll_by_employee
    ]

    return {
        "summary": {
            "payroll_count": len(payroll_rows),
            "payment_count": len(payment_rows),
            "matched_count": matched,
            "mismatch_count": len(mismatches),
            "missing_count": len(missing_payments),
            "failure_count": len(failures),
            "unmatched_payment_count": len(unmatched_payments),
            "is_balanced": not (mismatches or missing_payments or failures),
        },
        "mismatches": mismatches,
        "missing_payments": missing_payments,
        "failures": failures,
        "unmatched_payments": unmatched_payments,
    }
