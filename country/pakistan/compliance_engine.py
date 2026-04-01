from __future__ import annotations

from typing import Any

from country.base import ComplianceEngine
from services.compliance_service import PakistanComplianceService


class PakistanComplianceEngine(ComplianceEngine):
    def __init__(self) -> None:
        self.service = PakistanComplianceService()

    def validate_payroll(self, input: dict[str, Any]) -> dict[str, Any]:
        return self.service.validate_payroll(input)

    def generate_reports(self, input: dict[str, Any]) -> dict[str, Any]:
        return self.service.generate_reports(input)
