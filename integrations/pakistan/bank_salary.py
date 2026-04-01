from __future__ import annotations

import csv
import io
from decimal import Decimal
from typing import Any


_HEADERS = ["employee_id", "employee_name", "bank_account", "iban", "net_salary", "currency", "payment_reference"]


def _validate_employee(employee: dict[str, Any], idx: int) -> list[str]:
    errors: list[str] = []
    if not str(employee.get("employee_id", "")).strip():
        errors.append(f"employees[{idx}].employee_id is required")
    if not str(employee.get("full_name", "")).strip():
        errors.append(f"employees[{idx}].full_name is required")
    if not str(employee.get("iban", "")).strip().startswith("PK"):
        errors.append(f"employees[{idx}].iban must be a PK IBAN")
    try:
        amount = Decimal(str(employee.get("net_salary", "0")))
        if amount <= 0:
            errors.append(f"employees[{idx}].net_salary must be > 0")
    except Exception:
        errors.append(f"employees[{idx}].net_salary must be numeric")
    return errors


def _row_from_employee(employee: dict[str, Any], currency: str) -> dict[str, str]:
    return {
        "employee_id": str(employee.get("employee_id", "")),
        "employee_name": str(employee.get("full_name", "")),
        "bank_account": str(employee.get("bank_account", "")),
        "iban": str(employee.get("iban", "")),
        "net_salary": f"{Decimal(str(employee.get('net_salary', '0'))):.2f}",
        "currency": str(employee.get("currency", currency)),
        "payment_reference": str(employee.get("payment_reference", "SALARY")),
    }


def generate_salary_bank_csv(payload: dict[str, Any]) -> str:
    employees = list(payload.get("employees", []))
    currency = str(payload.get("currency", "PKR"))
    errors: list[str] = []
    for idx, employee in enumerate(employees):
        errors.extend(_validate_employee(employee, idx))
    if errors:
        raise ValueError("; ".join(errors))

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_HEADERS)
    writer.writeheader()
    for employee in employees:
        writer.writerow(_row_from_employee(employee, currency))
    return buffer.getvalue()


def generate_salary_bank_excel_rows(payload: dict[str, Any]) -> dict[str, Any]:
    employees = list(payload.get("employees", []))
    currency = str(payload.get("currency", "PKR"))
    rows = [_HEADERS]
    for idx, employee in enumerate(employees):
        validation = _validate_employee(employee, idx)
        if validation:
            raise ValueError("; ".join(validation))
        row_map = _row_from_employee(employee, currency)
        rows.append([row_map[h] for h in _HEADERS])

    return {"sheet_name": "SalaryDisbursement", "rows": rows, "currency": currency}
