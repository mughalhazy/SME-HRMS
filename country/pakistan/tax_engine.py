from __future__ import annotations

from typing import Any

from country.base import TaxEngine
from services.compliance_service import PakistanComplianceService


class PakistanTaxEngine(TaxEngine):
    def __init__(self) -> None:
        self.service = PakistanComplianceService()

    def calculate_tax(self, input: dict[str, Any]) -> dict[str, float]:
        tax_year = str(input.get("tax_year", "2026"))
        tax_result = self.service.calculate_tax(input.get("gross_salary", "0"), tax_year=tax_year)
        return {"tax_amount": float(tax_result["monthly_tax"])}
