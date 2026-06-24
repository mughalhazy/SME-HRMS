from __future__ import annotations

from typing import Any

from country.base.statutory_validator import StatutoryValidatorInterface


class DummyStatutoryValidator(StatutoryValidatorInterface):
    """Minimal statutory validator for architecture proof tests. Always valid."""

    def validate_employee(self, employee_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "employee_id": employee_data.get("employee_id", "unknown"),
            "is_valid": True,
            "violations": [],
        }

    def validate_payroll_readiness(self, payroll_input: dict[str, Any]) -> dict[str, Any]:
        return {"is_valid": True, "blocking_count": 0, "violations": []}

    def get_validation_rules(self) -> list[dict[str, Any]]:
        return []
