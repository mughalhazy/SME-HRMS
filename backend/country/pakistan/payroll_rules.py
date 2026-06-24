from __future__ import annotations

from decimal import Decimal
from typing import Any

from country.base import PayrollRulesEngine


# G40: Pakistan-specific statutory constants.
# Factories Act 1934: overtime at 2x basic rate.
# Standing Orders Ordinance: Eid bonus = 1 month basic salary per Eid.
# National minimum wage (update via MINIMUM_WAGE when government revises).
MINIMUM_WAGE = Decimal("32000")       # PKR/month — national minimum wage 2024
OVERTIME_RATE_MULTIPLIER = Decimal("2")   # Factories Act 1934
EID_HOLIDAYS = 2                          # Eid-ul-Fitr + Eid-ul-Adha per year


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
        violations: list[dict[str, Any]] = []

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
            rule_adjustments.append({
                "rule_id": str(rule.get("code", "UNKNOWN")),
                "description": str(rule.get("name", "country_rule_adjustment")),
                "amount_delta": float(amount if category == "earning" else -amount),
            })

        adjusted_gross_salary = (gross_salary + extra_earnings).quantize(Decimal("0.01"))
        final_deductions = (deductions + extra_deductions).quantize(Decimal("0.01"))

        # G40: Pakistan statutory validations.

        # Minimum wage enforcement (national minimum wage PKR 32,000/month).
        basic_salary = Decimal(str(context.get("basic_salary", gross_salary)))
        if basic_salary < MINIMUM_WAGE:
            violations.append({
                "rule_id": "PK_MIN_WAGE",
                "severity": "error",
                "message": f"Basic salary PKR {float(basic_salary):,.2f} is below national minimum wage PKR {float(MINIMUM_WAGE):,.2f}",
            })

        # Overtime rate enforcement — Factories Act 1934: overtime must be paid at 2x basic rate.
        overtime_hours = Decimal(str(context.get("overtime_hours", "0")))
        overtime_paid = Decimal(str(context.get("overtime_paid", "0")))
        if overtime_hours > Decimal("0"):
            hourly_basic = (basic_salary / Decimal("26") / Decimal("8")).quantize(Decimal("0.01"))
            required_overtime = (overtime_hours * hourly_basic * OVERTIME_RATE_MULTIPLIER).quantize(Decimal("0.01"))
            if overtime_paid < required_overtime:
                violations.append({
                    "rule_id": "PK_OVERTIME_RATE",
                    "severity": "error",
                    "message": (
                        f"Overtime paid PKR {float(overtime_paid):,.2f} is below required 2x rate "
                        f"PKR {float(required_overtime):,.2f} for {float(overtime_hours)} hours"
                    ),
                })

        # Eid bonus enforcement — Standing Orders Ordinance 1968.
        # Employees are entitled to one month basic salary per Eid holiday (2 per year).
        # Flag if eid_bonus_due is set in context but eid_bonus_paid is absent or insufficient.
        eid_bonus_due = Decimal(str(context.get("eid_bonus_due", "0")))
        eid_bonus_paid = Decimal(str(context.get("eid_bonus_paid", "0")))
        if eid_bonus_due > Decimal("0") and eid_bonus_paid < eid_bonus_due:
            violations.append({
                "rule_id": "PK_EID_BONUS",
                "severity": "warning",
                "message": (
                    f"Eid bonus due PKR {float(eid_bonus_due):,.2f} but only "
                    f"PKR {float(eid_bonus_paid):,.2f} recorded"
                ),
            })

        return {
            "adjusted_gross_salary": float(adjusted_gross_salary),
            "rule_adjustments": rule_adjustments,
            "final_deductions": {"total": float(final_deductions)},
            "extra_earnings": float(extra_earnings.quantize(Decimal("0.01"))),
            "extra_deductions": float(extra_deductions.quantize(Decimal("0.01"))),
            "statutory_violations": violations,
        }
