from __future__ import annotations


def loan_request(*, employee_id: str, amount: float, currency: str = "PKR") -> dict[str, object]:
    """Placeholder loan-request API contract for financial wellness integrations."""
    return {
        "type": "loan_request",
        "status": "accepted_placeholder",
        "employee_id": employee_id,
        "amount": float(amount),
        "currency": currency,
    }


def salary_advance(*, employee_id: str, amount: float, currency: str = "PKR") -> dict[str, object]:
    """Placeholder EWA/salary-advance API contract for downstream provider routing."""
    return {
        "type": "salary_advance",
        "status": "accepted_placeholder",
        "employee_id": employee_id,
        "amount": float(amount),
        "currency": currency,
    }
