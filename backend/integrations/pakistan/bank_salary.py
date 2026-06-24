from __future__ import annotations

import csv
import io
from decimal import Decimal
from typing import Any


_BANK_HEADERS: dict[str, list[str]] = {
    "standard": ["employee_id", "employee_name", "bank_account", "iban", "net_salary", "currency", "payment_reference"],
    "hbl_bulk": ["employee_id", "employee_name", "iban", "amount", "currency", "narration", "payment_reference"],
    "meezan_bulk": ["employee_id", "employee_name", "account_or_iban", "amount", "currency", "payment_reference"],
}


def _validate_employee(employee: dict[str, Any], idx: int) -> list[str]:
    errors: list[str] = []
    if not str(employee.get("employee_id", "")).strip():
        errors.append(f"employees[{idx}].employee_id is required")
    if not str(employee.get("full_name", "")).strip():
        errors.append(f"employees[{idx}].full_name is required")
    iban = str(employee.get("iban", "")).strip()
    bank_account = str(employee.get("bank_account", "")).strip()
    if not iban.startswith("PK") and not bank_account:
        errors.append(f"employees[{idx}] requires iban (PK...) or bank_account")
    try:
        amount = Decimal(str(employee.get("net_salary", "0")))
        if amount <= 0:
            errors.append(f"employees[{idx}].net_salary must be > 0")
    except Exception:
        errors.append(f"employees[{idx}].net_salary must be numeric")
    return errors


def _base_row(employee: dict[str, Any], currency: str) -> dict[str, str]:
    return {
        "employee_id": str(employee.get("employee_id", "")),
        "employee_name": str(employee.get("full_name", "")),
        "bank_account": str(employee.get("bank_account", "")),
        "iban": str(employee.get("iban", "")),
        "net_salary": f"{Decimal(str(employee.get('net_salary', '0'))):.2f}",
        "currency": str(employee.get("currency", currency)),
        "payment_reference": str(employee.get("payment_reference", "SALARY")),
        "amount": f"{Decimal(str(employee.get('net_salary', '0'))):.2f}",
        "narration": str(employee.get("narration", "Salary Disbursement")),
        "account_or_iban": str(employee.get("iban", employee.get("bank_account", ""))),
    }


def _resolve_headers(bank_format: str) -> list[str]:
    if bank_format not in _BANK_HEADERS:
        supported = ", ".join(sorted(_BANK_HEADERS))
        raise ValueError(f"bank_format must be one of: {supported}")
    return _BANK_HEADERS[bank_format]


def _validate_totals_match_payroll(payload: dict[str, Any], employees: list[dict[str, Any]]) -> None:
    payroll_total = payload.get("payroll_total")
    if payroll_total is None:
        return
    export_total = sum(Decimal(str(emp.get("net_salary", "0"))) for emp in employees)
    expected = Decimal(str(payroll_total))
    if export_total.quantize(Decimal("0.01")) != expected.quantize(Decimal("0.01")):
        raise ValueError(f"payment export total {export_total:.2f} must match payroll_total {expected:.2f}")


def generate_salary_bank_csv(payload: dict[str, Any]) -> str:
    employees = list(payload.get("employees", []))
    currency = str(payload.get("currency", "PKR"))
    bank_format = str(payload.get("bank_format", "standard"))
    headers = _resolve_headers(bank_format)
    errors: list[str] = []
    if not employees:
        errors.append("employees must be a non-empty array")
    for idx, employee in enumerate(employees):
        errors.extend(_validate_employee(employee, idx))
    if errors:
        raise ValueError("; ".join(errors))

    _validate_totals_match_payroll(payload, employees)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    for employee in employees:
        writer.writerow({k: v for k, v in _base_row(employee, currency).items() if k in headers})
    return buffer.getvalue()


def generate_salary_bank_excel_rows(payload: dict[str, Any]) -> dict[str, Any]:
    employees = list(payload.get("employees", []))
    currency = str(payload.get("currency", "PKR"))
    bank_format = str(payload.get("bank_format", "standard"))
    headers = _resolve_headers(bank_format)
    if not employees:
        raise ValueError("employees must be a non-empty array")
    _validate_totals_match_payroll(payload, employees)
    rows = [headers]
    for idx, employee in enumerate(employees):
        validation = _validate_employee(employee, idx)
        if validation:
            raise ValueError("; ".join(validation))
        row_map = _base_row(employee, currency)
        rows.append([row_map[h] for h in headers])

    return {"sheet_name": "SalaryDisbursement", "rows": rows, "currency": currency, "bank_format": bank_format}
