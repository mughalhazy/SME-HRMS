from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PayrollRulesInterface(ABC):
    @abstractmethod
    def apply_rules(self, input: dict[str, Any]) -> dict[str, Any]:
        """Apply country payroll rules and return adjusted values + trace."""


PayrollRulesEngine = PayrollRulesInterface
