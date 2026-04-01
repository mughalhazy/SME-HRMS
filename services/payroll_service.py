from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Literal

from country.pakistan.compliance_engine import PakistanComplianceEngine
from country.pakistan.tax_engine import PakistanTaxEngine

PayrollFrequency = Literal["monthly", "weekly", "daily"]

_PERIOD_DIVISOR: dict[PayrollFrequency, Decimal] = {
    "monthly": Decimal("1"),
    "weekly": Decimal("4"),
    "daily": Decimal("30"),
}


@dataclass(slots=True)
class PayrollComputation:
    frequency: PayrollFrequency
    basic: Decimal
    allowances: Decimal
    deductions: Decimal
    overtime_pay: Decimal
    tax: Decimal
    gross: Decimal
    taxable: Decimal
    net: Decimal
    payout: Decimal
    carry_forward: Decimal


class PayrollService:
    """Pakistan payroll calculation flow aligned to docs/specs/country/pakistan/payroll.md."""

    def __init__(self, tax_engine: PakistanTaxEngine | None = None, compliance_engine: PakistanComplianceEngine | None = None) -> None:
        self.tax_engine = tax_engine or PakistanTaxEngine()
        self.compliance_engine = compliance_engine or PakistanComplianceEngine()

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        return Decimal(str(value or "0"))

    @classmethod
    def _money(cls, value: Any) -> Decimal:
        return cls._decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_gross(self, basic: Any, allowances: Any, overtime_pay: Any = 0) -> Decimal:
        return (self._money(basic) + self._money(allowances) + self._money(overtime_pay)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_overtime_pay(self, overtime_hours: Any, overtime_rate: Any) -> Decimal:
        return (self._money(overtime_hours) * self._money(overtime_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_taxable(self, gross: Any, deductions: Any) -> Decimal:
        return (self._money(gross) - self._money(deductions)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_net(self, taxable: Any, tax: Any) -> Decimal:
        return (self._money(taxable) - self._money(tax)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def gratuity(self, basic: Any, rate: Any) -> Decimal:
        return (self._money(basic) * self._decimal(rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def provident_fund(self, basic: Any, rate: Any) -> Decimal:
        return (self._money(basic) * self._decimal(rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def loan_deduction(self, installment: Any) -> Decimal:
        return self._money(installment)

    def final_settlement(self, leave_encashment: Any, pending_deductions: Any) -> dict[str, str]:
        leave_amount = self._money(leave_encashment)
        pending_amount = self._money(pending_deductions)
        net_amount = (leave_amount - pending_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "leave_encashment": str(leave_amount),
            "pending_deductions": str(pending_amount),
            "net_settlement": str(net_amount),
        }

    def calculate_payroll(
        self,
        *,
        basic: Any,
        allowances: Any,
        deductions: Any,
        overtime_hours: Any = 0,
        overtime_rate: Any = 0,
        frequency: PayrollFrequency = "monthly",
        tax_year: str = "2026",
        compliance_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if frequency not in _PERIOD_DIVISOR:
            raise ValueError("frequency must be monthly, weekly, or daily")

        divisor = _PERIOD_DIVISOR[frequency]
        period_basic = (self._money(basic) / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        period_allowances = (self._money(allowances) / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        period_deductions = (self._money(deductions) / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        period_overtime_hours = (self._money(overtime_hours) / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        overtime_pay = self.calculate_overtime_pay(period_overtime_hours, overtime_rate)

        gross = self.calculate_gross(period_basic, period_allowances, overtime_pay)
        taxable = self.calculate_taxable(gross, period_deductions)

        tax_base = taxable if taxable > Decimal("0") else Decimal("0.00")
        tax_result = self.tax_engine.calculate_tax({"gross_salary": str(tax_base), "tax_year": tax_year})
        tax = self._money(tax_result.get("tax_amount", "0"))
        net = self.calculate_net(taxable, tax)

        payout = net if net >= Decimal("0") else Decimal("0.00")
        carry_forward = Decimal("0.00") if net >= Decimal("0") else abs(net)

        computation = PayrollComputation(
            frequency=frequency,
            basic=period_basic,
            allowances=period_allowances,
            deductions=period_deductions,
            overtime_pay=overtime_pay,
            tax=tax,
            gross=gross,
            taxable=taxable,
            net=net,
            payout=payout,
            carry_forward=carry_forward,
        )

        validation = self.compliance_engine.validate_payroll(compliance_payload or {"employee_records": []})

        return {
            "frequency": computation.frequency,
            "basic": str(computation.basic),
            "allowances": str(computation.allowances),
            "deductions": str(computation.deductions),
            "overtime_pay": str(computation.overtime_pay),
            "gross": str(computation.gross),
            "taxable": str(computation.taxable),
            "tax": str(computation.tax),
            "net": str(computation.net),
            "payout": str(computation.payout),
            "carry_forward": str(computation.carry_forward),
            "compliance": validation,
        }
