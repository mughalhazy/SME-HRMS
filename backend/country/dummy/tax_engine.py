from __future__ import annotations

from typing import Any

from country.base.tax_engine import TaxEngineInterface


class DummyTaxEngine(TaxEngineInterface):
    """Minimal tax engine for architecture proof tests. Returns zero tax."""

    def calculate_tax(self, input: dict[str, Any]) -> dict[str, float]:
        return {"tax_amount": 0.0, "effective_rate": 0.0}
