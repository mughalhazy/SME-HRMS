from __future__ import annotations

from decimal import Decimal
from typing import Any

from country.base import TaxEngine


class PakistanTaxEngine(TaxEngine):
    def calculate_tax(self, input: dict[str, Any]) -> dict[str, float]:
        gross_salary = Decimal(str(input.get("gross_salary", "0")))
        employee_data = dict(input.get("employee_data", {}))
        metadata = dict(employee_data.get("metadata", {}))
        withholding_rate = Decimal(str(metadata.get("rate", "0")))
        tax_amount = (gross_salary * withholding_rate / Decimal("100")).quantize(Decimal("0.01"))
        return {"tax_amount": float(tax_amount)}
