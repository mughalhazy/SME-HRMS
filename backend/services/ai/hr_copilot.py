from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessContext:
    actor_role: str


class HRCopilot:
    """Explainable HR Q&A helper backed by payroll and compliance data."""

    _ALLOWED_ROLES = {"Admin", "HR", "Payroll", "Manager"}
    _SUPPORTED_QUERIES = {"salary breakdown", "leave balance", "tax explanation"}

    def __init__(self, *, payroll_data: dict[str, dict[str, float]], compliance_data: dict[str, dict[str, float | str]]) -> None:
        self.payroll_data = payroll_data
        self.compliance_data = compliance_data

    def answer_query(self, *, query: str, employee_id: str, context: AccessContext) -> dict[str, str]:
        normalized_query = query.strip().lower()
        self._require_supported_query(normalized_query)
        self._require_access(context)

        if normalized_query == "salary breakdown":
            return self._salary_breakdown(employee_id)
        if normalized_query == "leave balance":
            return self._leave_balance(employee_id)
        return self._tax_explanation(employee_id)

    def _require_supported_query(self, query: str) -> None:
        if query not in self._SUPPORTED_QUERIES:
            supported = ", ".join(sorted(self._SUPPORTED_QUERIES))
            raise ValueError(f"Unsupported HR query '{query}'. Supported: {supported}.")

    def _require_access(self, context: AccessContext) -> None:
        if context.actor_role not in self._ALLOWED_ROLES:
            raise PermissionError("Access denied: role is not authorized for HR Copilot queries.")

    def _salary_breakdown(self, employee_id: str) -> dict[str, str]:
        payroll = self._get_payroll(employee_id)
        gross = payroll["base_salary"] + payroll["allowances"] + payroll["bonus"]
        deductions = payroll["tax_deduction"] + payroll["benefit_deduction"]
        net = gross - deductions

        answer = (
            f"Gross pay is {gross:.2f}; deductions are {deductions:.2f}; net pay is {net:.2f}."
        )
        explanation = (
            "Computed from payroll components: base_salary + allowances + bonus, "
            "then minus tax_deduction and benefit_deduction."
        )
        return {"answer": answer, "explanation": explanation}

    def _leave_balance(self, employee_id: str) -> dict[str, str]:
        payroll = self._get_payroll(employee_id)
        compliance = self._get_compliance(employee_id)

        accrued = payroll["leave_accrued_days"]
        used = payroll["leave_used_days"]
        carryover = float(compliance.get("leave_carryover_days", 0.0))
        balance = accrued + carryover - used

        answer = f"Leave balance is {balance:.1f} days."
        explanation = (
            "Calculated using payroll leave ledger (accrued - used) and compliance carryover policy."
        )
        return {"answer": answer, "explanation": explanation}

    def _tax_explanation(self, employee_id: str) -> dict[str, str]:
        payroll = self._get_payroll(employee_id)
        compliance = self._get_compliance(employee_id)

        taxable_income = payroll["base_salary"] + payroll["allowances"] + payroll["bonus"]
        tax_rate = float(compliance.get("tax_rate", 0.0))
        withheld = payroll["tax_deduction"]
        expected = taxable_income * tax_rate

        answer = (
            f"Tax withheld is {withheld:.2f} on taxable income {taxable_income:.2f} "
            f"at policy tax rate {tax_rate:.2%}."
        )
        explanation = (
            "Compliance tax_rate was applied to payroll taxable income to derive expected withholding "
            f"({expected:.2f}); payroll records currently withhold {withheld:.2f}."
        )
        return {"answer": answer, "explanation": explanation}

    def _get_payroll(self, employee_id: str) -> dict[str, float]:
        if employee_id not in self.payroll_data:
            raise ValueError(f"Payroll data not found for employee '{employee_id}'.")
        return self.payroll_data[employee_id]

    def _get_compliance(self, employee_id: str) -> dict[str, float | str]:
        if employee_id not in self.compliance_data:
            raise ValueError(f"Compliance data not found for employee '{employee_id}'.")
        return self.compliance_data[employee_id]
