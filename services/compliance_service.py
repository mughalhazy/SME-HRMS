from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class PakistanComplianceService:
    TAX_SLABS: dict[str, list[dict[str, Any]]] = {
        "2024": [
            {"code": "S1", "min_income": 0, "max_income": 600000, "base_tax": 0, "rate": "0.00", "threshold": None},
            {"code": "S2", "min_income": 600001, "max_income": 1200000, "base_tax": 0, "rate": "0.05", "threshold": 600000},
            {"code": "S3", "min_income": 1200001, "max_income": 2200000, "base_tax": 30000, "rate": "0.15", "threshold": 1200000},
            {"code": "S4", "min_income": 2200001, "max_income": 3200000, "base_tax": 180000, "rate": "0.25", "threshold": 2200000},
            {"code": "S5", "min_income": 3200001, "max_income": 4100000, "base_tax": 430000, "rate": "0.30", "threshold": 3200000},
            {"code": "S6", "min_income": 4100001, "max_income": None, "base_tax": 700000, "rate": "0.35", "threshold": 4100000},
        ],
        "2025": [
            {"code": "S1", "min_income": 0, "max_income": 600000, "base_tax": 0, "rate": "0.00", "threshold": None},
            {"code": "S2", "min_income": 600001, "max_income": 1200000, "base_tax": 0, "rate": "0.05", "threshold": 600000},
            {"code": "S3", "min_income": 1200001, "max_income": 2200000, "base_tax": 30000, "rate": "0.15", "threshold": 1200000},
            {"code": "S4", "min_income": 2200001, "max_income": 3200000, "base_tax": 180000, "rate": "0.25", "threshold": 2200000},
            {"code": "S5", "min_income": 3200001, "max_income": 4100000, "base_tax": 430000, "rate": "0.30", "threshold": 3200000},
            {"code": "S6", "min_income": 4100001, "max_income": None, "base_tax": 700000, "rate": "0.35", "threshold": 4100000},
        ],
        "2026": [
            {"code": "S1", "min_income": 0, "max_income": 600000, "base_tax": 0, "rate": "0.00", "threshold": None},
            {"code": "S2", "min_income": 600001, "max_income": 1200000, "base_tax": 0, "rate": "0.05", "threshold": 600000},
            {"code": "S3", "min_income": 1200001, "max_income": 2200000, "base_tax": 30000, "rate": "0.15", "threshold": 1200000},
            {"code": "S4", "min_income": 2200001, "max_income": 3200000, "base_tax": 180000, "rate": "0.25", "threshold": 2200000},
            {"code": "S5", "min_income": 3200001, "max_income": 4100000, "base_tax": 430000, "rate": "0.30", "threshold": 3200000},
            {"code": "S6", "min_income": 4100001, "max_income": None, "base_tax": 700000, "rate": "0.35", "threshold": 4100000},
        ],
    }

    def _money(self, value: Any) -> Decimal:
        return Decimal(str(value or "0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _slab_for_income(self, annual_taxable_income: Decimal, tax_year: str) -> dict[str, Any]:
        slabs = self.TAX_SLABS.get(str(tax_year), self.TAX_SLABS["2026"])
        for slab in slabs:
            min_income = Decimal(str(slab["min_income"]))
            max_income = slab["max_income"]
            max_decimal = Decimal(str(max_income)) if max_income is not None else None
            if annual_taxable_income >= min_income and (max_decimal is None or annual_taxable_income <= max_decimal):
                return slab
        return slabs[-1]

    def calculate_tax(self, monthly_taxable_income: Any, tax_year: str = "2026") -> dict[str, Any]:
        monthly_income = self._money(monthly_taxable_income)
        annual_income = (monthly_income * Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        slab = self._slab_for_income(annual_income, tax_year)
        threshold = slab.get("threshold")
        if threshold is None:
            annual_tax = Decimal("0.00")
        else:
            annual_tax = (
                Decimal(str(slab["base_tax"]))
                + (annual_income - Decimal(str(threshold))) * Decimal(str(slab["rate"]))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        monthly_tax = (annual_tax / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "tax_slab_code": slab["code"],
            "annual_taxable_income": float(annual_income),
            "annual_tax": float(annual_tax),
            "monthly_tax": float(monthly_tax),
        }

    def validate_payroll(self, payload: dict[str, Any]) -> dict[str, Any]:
        errors: list[dict[str, Any]] = []
        for employee in list(payload.get("employee_records", [])):
            employee_id = str(employee.get("employee_id", ""))
            monthly_salary = employee.get("monthly_gross_salary", employee.get("gross_pay", "0"))
            annual_tax = employee.get("annual_tax")
            taxable_income = employee.get("annual_taxable_income")
            monthly_tax_deducted = employee.get("monthly_tax_deducted")
            cnic = str(employee.get("cnic", "")).strip()

            try:
                salary_amount = Decimal(str(monthly_salary))
                if salary_amount < 0:
                    raise ValueError("negative")
            except Exception:
                errors.append({"employee_id": employee_id, "rule_id": "INVALID_SALARY", "severity": "error", "message": "Invalid salary"})

            taxable_amount = Decimal(str(taxable_income or "0"))
            if taxable_amount > 0 and annual_tax is None:
                errors.append({"employee_id": employee_id, "rule_id": "MISSING_TAX", "severity": "error", "message": "Missing annual tax"})
            if taxable_amount > 0 and monthly_tax_deducted is None:
                errors.append({"employee_id": employee_id, "rule_id": "MISSING_TAX", "severity": "error", "message": "Missing monthly tax deducted"})

            if len(cnic) != 13 or not cnic.isdigit():
                errors.append({"employee_id": employee_id, "rule_id": "MISSING_CNIC", "severity": "error", "message": "Missing or invalid CNIC"})

        return {"is_valid": len(errors) == 0, "violations": errors}

    def generate_reports(self, payload: dict[str, Any]) -> dict[str, Any]:
        period = str(payload.get("period", "2026-01"))
        year = int(period.split("-")[0])
        month = int(period.split("-")[1]) if "-" in period else 1
        org = dict(payload.get("organization_data", {}))
        employees = []
        for employee in list(payload.get("employee_records", [])):
            employees.append(
                {
                    "employee_id": str(employee.get("employee_id", "")),
                    "cnic": str(employee.get("cnic", "")),
                    "full_name": str(employee.get("full_name", "")),
                    "tax_status": str(employee.get("tax_status", "filer")),
                    "annual_gross_income": float(self._money(employee.get("annual_gross_income", employee.get("annual_taxable_income", 0)))),
                    "annual_taxable_income": float(self._money(employee.get("annual_taxable_income", 0))),
                    "tax_slab_code": str(employee.get("tax_slab_code", "")),
                    "annual_tax": float(self._money(employee.get("annual_tax", 0))),
                    "monthly_tax_deducted": float(self._money(employee.get("monthly_tax_deducted", 0))),
                    "exemptions": list(employee.get("exemptions", [])),
                }
            )

        total_taxable_income = sum((Decimal(str(item["annual_taxable_income"])) for item in employees), Decimal("0"))
        total_tax_deducted = sum((Decimal(str(item["monthly_tax_deducted"])) for item in employees), Decimal("0"))

        annexure_c = {
            "tax_year": str(year),
            "period": {"month": month, "year": year},
            "employer": {
                "ntn": str(org.get("ntn", "")),
                "name": str(org.get("name", "")),
                "address": str(org.get("address", "")),
                "withholding_agent_cnic_ntn": str(org.get("withholding_agent_cnic_ntn", "")),
            },
            "totals": {
                "total_employees": len(employees),
                "total_taxable_income": float(total_taxable_income.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "total_tax_deducted": float(total_tax_deducted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            },
            "employees": employees,
        }

        eobi_pr_01 = {
            "submission_format": "PR-01",
            "period": {"month": month, "year": year},
            "employer": {"name": str(org.get("name", "")), "registration_number": str(org.get("eobi_registration", ""))},
            "employees": [{"employee_id": item["employee_id"], "cnic": item["cnic"]} for item in employees],
        }
        pessi = {
            "period": {"month": month, "year": year},
            "establishment": {"name": str(org.get("name", "")), "registration_number": str(org.get("pessi_registration", ""))},
            "employees": [{"employee_id": item["employee_id"], "cnic": item["cnic"]} for item in employees],
        }
        return {
            "reports": {
                "fbr_annexure_c": annexure_c,
                "eobi_pr_01": eobi_pr_01,
                "pessi": pessi,
            },
            "metadata": {"country_code": str(payload.get("country_code", "PK")).upper(), "period": period},
        }
