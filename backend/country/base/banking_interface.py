from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BankingInterface(ABC):
    """
    Country-specific banking operations interface.

    All bank-format generation, payment export, and reconciliation logic
    lives in country adapters that implement this interface.
    Services must never import country-specific banking modules directly.
    """

    @abstractmethod
    def build_raast_payment_export(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build a Raast instant payment batch export payload."""

    @abstractmethod
    def generate_salary_bank_csv(self, payload: dict[str, Any]) -> str:
        """Generate a bank-format salary disbursement CSV string."""

    @abstractmethod
    def generate_salary_bank_excel_rows(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate salary disbursement rows for Excel/spreadsheet export."""

    @abstractmethod
    def reconcile_payroll_payments(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Match payment confirmations against payroll records.
        Returns: summary, mismatches, missing_payments, failures, unmatched_payments.
        """
