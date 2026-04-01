from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4


@dataclass(slots=True)
class SalaryAdvanceRequest:
    request_id: str
    employee_id: str
    amount: Decimal
    currency: str
    status: str
    requested_at: datetime
    approved_at: datetime | None = None
    approved_by: str | None = None
    remaining_balance: Decimal = Decimal("0.00")

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "employee_id": self.employee_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "status": self.status,
            "requested_at": self.requested_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "remaining_balance": str(self.remaining_balance),
        }


class FinancialWellnessService:
    """Financial wellness workflows with payroll deduction integration."""

    def __init__(self) -> None:
        self._requests: dict[str, SalaryAdvanceRequest] = {}

    def request_salary_advance(self, *, employee_id: str, amount: float, currency: str = "PKR") -> dict[str, object]:
        request = SalaryAdvanceRequest(
            request_id=str(uuid4()),
            employee_id=employee_id,
            amount=Decimal(str(amount)).quantize(Decimal("0.01")),
            currency=currency,
            status="PendingApproval",
            requested_at=datetime.now(timezone.utc),
            remaining_balance=Decimal(str(amount)).quantize(Decimal("0.01")),
        )
        self._requests[request.request_id] = request
        return request.to_dict()

    def approve_salary_advance(self, *, request_id: str, approver_id: str) -> dict[str, object]:
        request = self._requests[request_id]
        request.status = "Approved"
        request.approved_by = approver_id
        request.approved_at = datetime.now(timezone.utc)
        return request.to_dict()

    def payroll_deduction_for_employee(self, *, employee_id: str, max_deduction: Decimal | int | float | str) -> Decimal:
        pending = [
            req
            for req in self._requests.values()
            if req.employee_id == employee_id and req.status == "Approved" and req.remaining_balance > Decimal("0.00")
        ]
        total = sum((req.remaining_balance for req in pending), Decimal("0.00"))
        cap = Decimal(str(max_deduction)).quantize(Decimal("0.01"))
        deduction = min(total, cap).quantize(Decimal("0.01"))
        remaining = deduction
        for req in pending:
            if remaining <= Decimal("0.00"):
                break
            step = min(req.remaining_balance, remaining)
            req.remaining_balance = (req.remaining_balance - step).quantize(Decimal("0.01"))
            remaining = (remaining - step).quantize(Decimal("0.01"))
            if req.remaining_balance == Decimal("0.00"):
                req.status = "Deducted"
        return deduction


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
