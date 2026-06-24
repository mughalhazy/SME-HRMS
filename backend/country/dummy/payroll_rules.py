from __future__ import annotations

from typing import Any

from country.base.payroll_rules import PayrollRulesInterface


class DummyPayrollRulesEngine(PayrollRulesInterface):
    """Minimal payroll rules engine for architecture proof tests. Passes through unchanged."""

    def apply_rules(self, input: dict[str, Any]) -> dict[str, Any]:
        return {**input, "rules_applied": [], "country": "dummy"}
