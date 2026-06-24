from __future__ import annotations

from typing import Any

from country.base.banking_interface import BankingInterface
from integrations.pakistan.raast_payment import build_raast_payment_export as _raast_export
from integrations.pakistan.bank_salary import (
    generate_salary_bank_csv as _csv,
    generate_salary_bank_excel_rows as _excel,
)
from integrations.pakistan.payment_reconciliation import reconcile_payroll_payments as _reconcile


class PakistanBankingAdapter(BankingInterface):
    """
    Pakistan-specific banking operations.
    Wraps existing integrations.pakistan.* functions behind the BankingInterface.
    """

    def build_raast_payment_export(self, payload: dict[str, Any]) -> dict[str, Any]:
        return _raast_export(payload)

    def generate_salary_bank_csv(self, payload: dict[str, Any]) -> str:
        return _csv(payload)

    def generate_salary_bank_excel_rows(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        return _excel(payload)

    def reconcile_payroll_payments(self, data: dict[str, Any]) -> dict[str, Any]:
        return _reconcile(data)
