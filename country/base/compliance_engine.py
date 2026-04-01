from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ComplianceEngine(ABC):
    @abstractmethod
    def validate_payroll(self, input: dict[str, Any]) -> dict[str, Any]:
        """Validate payroll compliance prior to report generation."""

    @abstractmethod
    def generate_reports(self, input: dict[str, Any]) -> dict[str, Any]:
        """Generate country compliance reports for finalized payroll results."""
