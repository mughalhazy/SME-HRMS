from __future__ import annotations

from decimal import Decimal
from typing import Any

from country.base import PayrollRulesEngine


class PakistanPayrollRulesEngine(PayrollRulesEngine):
    def apply_rules(self, input: dict[str, Any]) -> dict[str, Any]:
        gross_salary = Decimal(str(input.get("gross_salary", "0")))
        allowances = Decimal(str(input.get("allowances", "0")))
        deductions = Decimal(str(input.get("deductions", "0")))
        context = dict(input.get("context", {}))
        rules = list(input.get("rules", []))

        rule_adjustments: list[dict[str, Any]] = []
        extra_earnings = Decimal("0.00")
        extra_deductions = Decimal("0.00")

        for rule in rules:
            if not bool(rule.get("active", False)):
                continue
            category = str(rule.get("category"))
            calc_mode = str(rule.get("calculation_mode"))
            value = Decimal(str(rule.get("value", "0")))
            if calc_mode == "flat":
                amount = value
            else:
                base_amount = Decimal(str(context.get(rule.get("input_key") or "taxable_earnings", "0")))
                amount = (base_amount * value / Decimal("100")).quantize(Decimal("0.01"))
            if category == "earning":
                extra_earnings += amount
            elif category == "deduction":
                extra_deductions += amount
            rule_adjustments.append(
                {
                    "rule_id": str(rule.get("code", "UNKNOWN")),
                    "description": str(rule.get("name", "country_rule_adjustment")),
                    "amount_delta": float(amount if category == "earning" else -amount),
                }
            )

        adjusted_gross_salary = (gross_salary + extra_earnings).quantize(Decimal("0.01"))
        final_deductions = (deductions + extra_deductions).quantize(Decimal("0.01"))

        return {
            "adjusted_gross_salary": float(adjusted_gross_salary),
            "rule_adjustments": rule_adjustments,
            "final_deductions": {"total": float(final_deductions)},
            "extra_earnings": float(extra_earnings.quantize(Decimal("0.01"))),
            "extra_deductions": float(extra_deductions.quantize(Decimal("0.01"))),
        }
