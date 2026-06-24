from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StatutoryValidatorInterface(ABC):
    """Base interface for country-specific statutory validation — SPEC §08 L3.

    All country adapters that enforce statutory data requirements must implement
    this interface. The payroll service calls validate_payroll_readiness() during
    the pre-payroll gate to block finalization when statutory data is incomplete.

    AC6: "Invalid statutory data blocks payroll" — enforced via this interface.
    """

    @abstractmethod
    def validate_employee(self, employee_data: dict[str, Any]) -> dict[str, Any]:
        """Validate a single employee's statutory data completeness.

        Args:
            employee_data: Employee record dict with at minimum:
                employee_id, statutory identifiers, bank details, province/location.

        Returns:
            {
                "employee_id": str,
                "is_valid": bool,
                "violations": [{"rule_id": str, "message": str, "field": str}]
            }
        """

    @abstractmethod
    def validate_payroll_readiness(self, payroll_input: dict[str, Any]) -> dict[str, Any]:
        """Validate statutory readiness for a full payroll run.

        Checks all employees in the payroll batch against country statutory
        requirements before payroll finalization is permitted.

        Args:
            payroll_input: {
                "period": str,          # "YYYY-MM"
                "legal_entity_id": str,
                "employees": list[dict] # list of employee_data dicts
            }

        Returns:
            {
                "is_valid": bool,
                "blocking_count": int,
                "violations": [{"employee_id": str, "rule_id": str, "message": str}]
            }
        """

    @abstractmethod
    def get_validation_rules(self) -> list[dict[str, Any]]:
        """Return the full set of statutory validation rules for this country.

        Used by the compliance service to display human-readable rule descriptions
        and generate validation reports.

        Returns:
            [{"rule_id": str, "description": str, "severity": str, "field": str}]
        """


StatutoryValidator = StatutoryValidatorInterface
