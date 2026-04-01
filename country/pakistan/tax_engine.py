from __future__ import annotations

from decimal import Decimal
from typing import Any

from country.base import TaxEngine
from country.pakistan.statutory import PakistanStatutoryService


class PakistanTaxEngine(TaxEngine):
    def __init__(self) -> None:
        self.service = PakistanStatutoryService()

    def calculate_tax(self, input: dict[str, Any]) -> dict[str, float]:
        employee_data = input.get("employee_data") or {}
        metadata = employee_data.get("metadata") or {}
        if "rate" in metadata:
            gross_salary = Decimal(str(input.get("gross_salary", "0")))
            rate = Decimal(str(metadata.get("rate", "0")))
            monthly_tax = (gross_salary * rate / Decimal("100")).quantize(Decimal("0.01"))
            return {"tax_amount": float(monthly_tax)}

        tax_year = str(input.get("tax_year", "2026"))
        tax_result = self.service.calculate_tax(input.get("gross_salary", "0"), tax_year=tax_year)
        return {"tax_amount": float(tax_result["monthly_tax"])}
