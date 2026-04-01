from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import uuid4


_REQUIRED_TOP_LEVEL_KEYS = {"tax_year", "period", "employer", "totals", "employees"}
_REQUIRED_PERIOD_KEYS = {"month", "year"}
_REQUIRED_EMPLOYER_KEYS = {"ntn", "name", "address", "withholding_agent_cnic_ntn"}
_REQUIRED_TOTAL_KEYS = {"total_employees", "total_taxable_income", "total_tax_deducted"}
_REQUIRED_EMPLOYEE_KEYS = {
    "employee_id",
    "cnic",
    "full_name",
    "tax_status",
    "annual_gross_income",
    "annual_taxable_income",
    "tax_slab_code",
    "annual_tax",
    "monthly_tax_deducted",
    "exemptions",
}


def _is_non_negative_number(value: Any) -> bool:
    try:
        return Decimal(str(value)) >= 0
    except Exception:
        return False


def _validate_annexure_c_payload(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []

    missing = _REQUIRED_TOP_LEVEL_KEYS.difference(payload.keys())
    if missing:
        errors.append(f"Missing top-level keys: {sorted(missing)}")
        return False, errors

    period = payload.get("period")
    employer = payload.get("employer")
    totals = payload.get("totals")
    employees = payload.get("employees")

    if not isinstance(period, dict) or _REQUIRED_PERIOD_KEYS.difference(period.keys()):
        errors.append("Invalid period shape; expected month and year.")

    if not isinstance(employer, dict) or _REQUIRED_EMPLOYER_KEYS.difference(employer.keys()):
        errors.append("Invalid employer shape; required FBR employer metadata is missing.")

    if not isinstance(totals, dict) or _REQUIRED_TOTAL_KEYS.difference(totals.keys()):
        errors.append("Invalid totals shape for Annexure-C.")

    if not isinstance(employees, list):
        errors.append("employees must be an array.")
        employees = []

    for idx, employee in enumerate(employees):
        if not isinstance(employee, dict):
            errors.append(f"employees[{idx}] must be an object.")
            continue

        missing_employee = _REQUIRED_EMPLOYEE_KEYS.difference(employee.keys())
        if missing_employee:
            errors.append(f"employees[{idx}] missing keys: {sorted(missing_employee)}")

        cnic = str(employee.get("cnic", "")).strip()
        if len(cnic) != 13 or not cnic.isdigit():
            errors.append(f"employees[{idx}] invalid CNIC.")

        for field in (
            "annual_gross_income",
            "annual_taxable_income",
            "annual_tax",
            "monthly_tax_deducted",
        ):
            if not _is_non_negative_number(employee.get(field, 0)):
                errors.append(f"employees[{idx}] {field} must be numeric and >= 0.")

    if isinstance(totals, dict):
        expected_count = len(employees)
        if totals.get("total_employees") != expected_count:
            errors.append("totals.total_employees does not match employees count.")

        sum_monthly = sum(Decimal(str(e.get("monthly_tax_deducted", 0))) for e in employees if isinstance(e, dict))
        if Decimal(str(totals.get("total_tax_deducted", 0))).quantize(Decimal("0.01")) != sum_monthly.quantize(Decimal("0.01")):
            errors.append("totals.total_tax_deducted does not match employee monthly tax sum.")

    return len(errors) == 0, errors


def submit_annexure_c(payload: dict[str, Any]) -> dict[str, Any]:
    """Submit Annexure-C payload to FBR.

    This adapter simulates submission in environments where the FBR API is unavailable.
    """

    is_valid, errors = _validate_annexure_c_payload(payload)
    submission_id = f"fbr_{uuid4().hex[:12]}"

    if not is_valid:
        return {
            "status": "failure",
            "submitted": False,
            "submission_id": submission_id,
            "provider": "FBR",
            "format": "annexure_c",
            "errors": errors,
            "mode": "simulated",
        }

    return {
        "status": "success",
        "submitted": True,
        "submission_id": submission_id,
        "provider": "FBR",
        "format": "annexure_c",
        "errors": [],
        "mode": "simulated",
    }
