from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AccountingAdapter(ABC):
    @abstractmethod
    def export_payroll_journal(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class QuickBooksAdapter(AccountingAdapter):
    def export_payroll_journal(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": "QuickBooks",
            "status": "stubbed",
            "journal_entries": list(payload.get("journal_entries", [])),
            "message": "QuickBooks connector is a stub and does not call external APIs.",
        }


class SAPAdapter(AccountingAdapter):
    def export_payroll_journal(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": "SAP",
            "status": "stubbed",
            "journal_entries": list(payload.get("journal_entries", [])),
            "message": "SAP connector is a stub and does not call external APIs.",
        }
