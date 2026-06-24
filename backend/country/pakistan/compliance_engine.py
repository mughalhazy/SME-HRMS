from __future__ import annotations

from typing import Any

from country.base import ComplianceEngine
from country.pakistan.statutory import PakistanStatutoryService


class PakistanComplianceEngine(ComplianceEngine):
    def __init__(self) -> None:
        self.service = PakistanStatutoryService()

    def validate_payroll(self, input: dict[str, Any]) -> dict[str, Any]:
        return self.service.validate_payroll(input)

    def generate_reports(self, input: dict[str, Any]) -> dict[str, Any]:
        return self.service.generate_reports(input)
