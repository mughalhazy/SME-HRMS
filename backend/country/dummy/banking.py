from __future__ import annotations

from typing import Any

from country.base.banking_interface import BankingInterface


class DummyBankingAdapter(BankingInterface):
    """Minimal banking adapter for architecture proof tests."""

    def build_raast_payment_export(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"format": "dummy_raast", "payload": payload}

    def generate_salary_bank_csv(self, payload: dict[str, Any]) -> str:
        return "employee_id,amount\n"

    def generate_salary_bank_excel_rows(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        return []

    def reconcile_payroll_payments(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "summary": {"is_balanced": True, "total": 0},
            "mismatches": [],
            "missing_payments": [],
            "failures": [],
            "unmatched_payments": [],
        }
