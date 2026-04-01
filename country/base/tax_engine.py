from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TaxEngineInterface(ABC):
    @abstractmethod
    def calculate_tax(self, input: dict[str, Any]) -> dict[str, float]:
        """Calculate payroll tax for a payroll period context."""


TaxEngine = TaxEngineInterface
