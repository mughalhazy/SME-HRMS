from __future__ import annotations

import pytest

from services.ai.hr_copilot import AccessContext, HRCopilot


@pytest.fixture
def copilot() -> HRCopilot:
    return HRCopilot(
        payroll_data={
            "emp-101": {
                "base_salary": 5000.0,
                "allowances": 1000.0,
                "bonus": 500.0,
                "tax_deduction": 650.0,
                "benefit_deduction": 350.0,
                "leave_accrued_days": 20.0,
                "leave_used_days": 8.0,
            }
        },
        compliance_data={
            "emp-101": {
                "tax_rate": 0.10,
                "leave_carryover_days": 2.0,
            }
        },
    )


def test_salary_breakdown_returns_answer_and_explanation(copilot: HRCopilot) -> None:
    response = copilot.answer_query(
        query="salary breakdown",
        employee_id="emp-101",
        context=AccessContext(actor_role="HR"),
    )

    assert response["answer"] == "Gross pay is 6500.00; deductions are 1000.00; net pay is 5500.00."
    assert "Computed from payroll components" in response["explanation"]


def test_leave_balance_returns_answer_and_explanation(copilot: HRCopilot) -> None:
    response = copilot.answer_query(
        query="leave balance",
        employee_id="emp-101",
        context=AccessContext(actor_role="Manager"),
    )

    assert response["answer"] == "Leave balance is 14.0 days."
    assert "compliance carryover policy" in response["explanation"]


def test_tax_explanation_uses_payroll_and_compliance_data(copilot: HRCopilot) -> None:
    response = copilot.answer_query(
        query="tax explanation",
        employee_id="emp-101",
        context=AccessContext(actor_role="Payroll"),
    )

    assert "Tax withheld is 650.00" in response["answer"]
    assert "policy tax rate 10.00%" in response["answer"]
    assert "expected withholding (650.00)" in response["explanation"]


def test_unauthorized_role_is_denied(copilot: HRCopilot) -> None:
    with pytest.raises(PermissionError, match="Access denied"):
        copilot.answer_query(
            query="salary breakdown",
            employee_id="emp-101",
            context=AccessContext(actor_role="Employee"),
        )


def test_unsupported_query_is_rejected(copilot: HRCopilot) -> None:
    with pytest.raises(ValueError, match="Unsupported HR query"):
        copilot.answer_query(
            query="salary history",
            employee_id="emp-101",
            context=AccessContext(actor_role="HR"),
        )
