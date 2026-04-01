from __future__ import annotations

import csv
import io
from typing import Any


_HEADERS = [
    "employee_id",
    "employee_name",
    "bank_account",
    "iban",
    "net_salary",
    "currency",
    "payment_reference",
]


def _row_from_employee(employee: dict[str, Any], currency: str) -> dict[str, str]:
    return {
        "employee_id": str(employee.get("employee_id", "")),
        "employee_name": str(employee.get("full_name", "")),
        "bank_account": str(employee.get("bank_account", "")),
        "iban": str(employee.get("iban", "")),
        "net_salary": str(employee.get("net_salary", "0")),
        "currency": str(employee.get("currency", currency)),
        "payment_reference": str(employee.get("payment_reference", "SALARY")),
    }


def generate_salary_bank_csv(payload: dict[str, Any]) -> str:
    employees = list(payload.get("employees", []))
    currency = str(payload.get("currency", "PKR"))

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_HEADERS)
    writer.writeheader()
    for employee in employees:
        writer.writerow(_row_from_employee(employee, currency))

    return buffer.getvalue()


def generate_salary_bank_excel_rows(payload: dict[str, Any]) -> dict[str, Any]:
    """Excel-friendly structure. Caller can serialize using openpyxl/pandas if available."""

    employees = list(payload.get("employees", []))
    currency = str(payload.get("currency", "PKR"))
    rows = [_HEADERS]
    for employee in employees:
        row_map = _row_from_employee(employee, currency)
        rows.append([row_map[h] for h in _HEADERS])

    return {"sheet_name": "SalaryDisbursement", "rows": rows}
