from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class PayrollPolicyEngine:
    """Applies payroll policy math (non-tax, non-compliance)."""

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        return Decimal(str(value or "0"))

    @classmethod
    def money(cls, value: Any) -> Decimal:
        return cls._decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_overtime_pay(self, *, overtime_hours: Any, overtime_rate: Any, overtime_tiers: list[dict[str, Any]] | None = None) -> Decimal:
        hours = self.money(overtime_hours)
        if not overtime_tiers:
            return (hours * self.money(overtime_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        remaining = hours
        total = Decimal("0.00")
        previous_threshold = Decimal("0.00")

        normalized_tiers = sorted((overtime_tiers or []), key=lambda tier: self._decimal(tier.get("up_to_hours", "0")))
        for tier in normalized_tiers:
            threshold = self._decimal(tier.get("up_to_hours", "0"))
            tier_rate = self.money(tier.get("rate", overtime_rate))
            tier_cap = max(Decimal("0.00"), threshold - previous_threshold)
            tier_hours = min(max(Decimal("0.00"), remaining), tier_cap)
            total += tier_hours * tier_rate
            remaining -= tier_hours
            previous_threshold = threshold
            if remaining <= Decimal("0.00"):
                break

        if remaining > Decimal("0.00"):
            last_rate = self.money((normalized_tiers[-1] if normalized_tiers else {}).get("rate", overtime_rate))
            total += remaining * last_rate

        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_penalties(self, *, basic: Any, penalties: list[dict[str, Any]] | None = None) -> Decimal:
        if not penalties:
            return Decimal("0.00")

        basic_amount = self.money(basic)
        total = Decimal("0.00")
        for penalty in penalties:
            mode = str(penalty.get("mode", "flat"))
            value = self._decimal(penalty.get("value", "0"))
            if mode == "percent_of_basic":
                total += basic_amount * value / Decimal("100")
            else:
                total += value
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_shift_pay(self, *, basic: Any, shift_rules: list[dict[str, Any]] | None = None, shift_key: str | None = None) -> Decimal:
        if not shift_rules or not shift_key:
            return Decimal("0.00")

        basic_amount = self.money(basic)
        total = Decimal("0.00")
        for rule in shift_rules:
            if str(rule.get("shift")) != shift_key:
                continue
            mode = str(rule.get("mode", "flat"))
            value = self._decimal(rule.get("value", "0"))
            if mode == "percent_of_basic":
                total += basic_amount * value / Decimal("100")
            else:
                total += value

        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def build_period_totals(
        self,
        *,
        basic: Any,
        allowances: Any,
        deductions: Any,
        overtime_hours: Any = 0,
        overtime_rate: Any = 0,
        overtime_tiers: list[dict[str, Any]] | None = None,
        penalties: list[dict[str, Any]] | None = None,
        shift_rules: list[dict[str, Any]] | None = None,
        shift_key: str | None = None,
    ) -> dict[str, Decimal]:
        basic_amount = self.money(basic)
        allowance_amount = self.money(allowances)
        deduction_amount = self.money(deductions)

        overtime_pay = self.calculate_overtime_pay(
            overtime_hours=overtime_hours,
            overtime_rate=overtime_rate,
            overtime_tiers=overtime_tiers,
        )
        shift_pay = self.calculate_shift_pay(
            basic=basic_amount,
            shift_rules=shift_rules,
            shift_key=shift_key,
        )
        penalties_total = self.calculate_penalties(
            basic=basic_amount,
            penalties=penalties,
        )

        gross = (basic_amount + allowance_amount + overtime_pay + shift_pay).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        taxable = (gross - deduction_amount - penalties_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "basic": basic_amount,
            "allowances": allowance_amount,
            "deductions": deduction_amount,
            "overtime_pay": overtime_pay,
            "shift_pay": shift_pay,
            "penalties": penalties_total,
            "gross": gross,
            "taxable": taxable,
        }

    def calculate_net(self, *, taxable: Any, tax: Any) -> Decimal:
        return (self.money(taxable) - self.money(tax)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
