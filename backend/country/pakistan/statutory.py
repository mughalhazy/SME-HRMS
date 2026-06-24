from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


# G36: EOBI contribution defaults (configurable per employer via calculate_eobi args).
# Employer: 5% of insurable wage. Employee: 1% of insurable wage.
_EOBI_DEFAULTS: dict[str, Any] = {
    "min_wage": Decimal("8000"),   # EOBI insurable wage floor
    "max_wage": Decimal("32000"),  # EOBI insurable wage ceiling (national minimum wage)
    "employee_rate": Decimal("0.01"),
    "employer_rate": Decimal("0.05"),
}

# G37: Provincial social security defaults (PESSI/SESSI/KP).
# Wage cap per PESSI/SESSI Acts. Rates: employer 6%, employee 1%.
_SOCIAL_SECURITY_DEFAULTS: dict[str, dict[str, Any]] = {
    "punjab": {"regime": "PESSI", "wage_cap": Decimal("18000"), "employer_rate": Decimal("0.06"), "employee_rate": Decimal("0.01")},
    "sindh": {"regime": "SESSI", "wage_cap": Decimal("18000"), "employer_rate": Decimal("0.06"), "employee_rate": Decimal("0.01")},
    "khyber pakhtunkhwa": {"regime": "KP", "wage_cap": Decimal("18000"), "employer_rate": Decimal("0.05"), "employee_rate": Decimal("0.01")},
    "kp": {"regime": "KP", "wage_cap": Decimal("18000"), "employer_rate": Decimal("0.05"), "employee_rate": Decimal("0.01")},
    "kpk": {"regime": "KP", "wage_cap": Decimal("18000"), "employer_rate": Decimal("0.05"), "employee_rate": Decimal("0.01")},
}

# MN-G01: Provident Fund defaults — Employees Provident Funds Act 1952.
# Minimum employer contribution is 2% under the Act; 10% is the common market rate.
# Both rates are configurable per employer via update_provident_fund_rates().
_PF_DEFAULTS: dict[str, Any] = {
    "employer_rate": Decimal("0.10"),
    "employee_rate": Decimal("0.10"),
    "min_employer_rate": Decimal("0.02"),  # statutory minimum
}

# G38: WPPF — Workers Profit Participation Fund (5% of net profits).
# Companies Profits (Workers Participation) Act 1968.
_WPPF_RATE = Decimal("0.05")

# G39: WWF — Workers Welfare Fund (2% of income above PKR 500,000/year).
_WWF_RATE = Decimal("0.02")
_WWF_THRESHOLD = Decimal("500000")


class PakistanStatutoryService:
    # G34/G41: Versioned slabs. 2025/2026 mirror 2024 as safe default.
    # Update via update_tax_slabs() when FBR publishes Finance Act changes each July —
    # no code deployment needed.
    TAX_SLABS: dict[str, list[dict[str, Any]]] = {
        "2024": [
            {"code": "S1", "min_income": 0, "max_income": 600000, "base_tax": 0, "rate": "0.00", "threshold": None},
            {"code": "S2", "min_income": 600001, "max_income": 1200000, "base_tax": 0, "rate": "0.05", "threshold": 600000},
            {"code": "S3", "min_income": 1200001, "max_income": 2200000, "base_tax": 30000, "rate": "0.15", "threshold": 1200000},
            {"code": "S4", "min_income": 2200001, "max_income": 3200000, "base_tax": 180000, "rate": "0.25", "threshold": 2200000},
            {"code": "S5", "min_income": 3200001, "max_income": 4100000, "base_tax": 430000, "rate": "0.30", "threshold": 3200000},
            {"code": "S6", "min_income": 4100001, "max_income": None, "base_tax": 700000, "rate": "0.35", "threshold": 4100000},
        ],
        # NOTE: 2025 and 2026 values pending FBR Finance Act confirmation each July.
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

    # G34/G41: Runtime slab update — override without code deployment.
    # Call at startup from config file or env-injected JSON after each Finance Act (July).
    def update_tax_slabs(self, year: str, slabs: list[dict[str, Any]]) -> None:
        self.TAX_SLABS[str(year)] = slabs

    # MR-G01: Runtime update path for EOBI rates — parallel to update_tax_slabs().
    # EOBI insurable wage floor/ceiling and contribution rates change via gazette notifications.
    # Call this at startup from config/env without requiring a code deployment.
    def update_eobi_rates(
        self,
        min_wage: Any | None = None,
        max_wage: Any | None = None,
        employee_rate: Any | None = None,
        employer_rate: Any | None = None,
    ) -> None:
        if min_wage is not None:
            _EOBI_DEFAULTS["min_wage"] = self._money(min_wage)
        if max_wage is not None:
            _EOBI_DEFAULTS["max_wage"] = self._money(max_wage)
        if employee_rate is not None:
            _EOBI_DEFAULTS["employee_rate"] = Decimal(str(employee_rate))
        if employer_rate is not None:
            _EOBI_DEFAULTS["employer_rate"] = Decimal(str(employer_rate))

    # MR-G01: Runtime update path for PESSI/SESSI/KP social security rates.
    # Province wage caps and contribution rates change via provincial gazette notifications.
    # Call this at startup from config/env without requiring a code deployment.
    def update_social_security_rates(
        self,
        province: str,
        wage_cap: Any | None = None,
        employer_rate: Any | None = None,
        employee_rate: Any | None = None,
    ) -> None:
        key = province.lower().strip()
        if key not in _SOCIAL_SECURITY_DEFAULTS:
            _SOCIAL_SECURITY_DEFAULTS[key] = {
                "regime": province.upper(),
                "wage_cap": Decimal("18000"),
                "employer_rate": Decimal("0.06"),
                "employee_rate": Decimal("0.01"),
            }
        if wage_cap is not None:
            _SOCIAL_SECURITY_DEFAULTS[key]["wage_cap"] = self._money(wage_cap)
        if employer_rate is not None:
            _SOCIAL_SECURITY_DEFAULTS[key]["employer_rate"] = Decimal(str(employer_rate))
        if employee_rate is not None:
            _SOCIAL_SECURITY_DEFAULTS[key]["employee_rate"] = Decimal(str(employee_rate))

    # MN-G01: Runtime update for PF rates — parallel to update_eobi_rates().
    def update_provident_fund_rates(
        self,
        employer_rate: Any | None = None,
        employee_rate: Any | None = None,
    ) -> None:
        if employer_rate is not None:
            rate = Decimal(str(employer_rate))
            if rate < _PF_DEFAULTS["min_employer_rate"]:
                raise ValueError(
                    f"Employer PF rate {rate} is below statutory minimum "
                    f"{_PF_DEFAULTS['min_employer_rate']} under the Employees Provident Funds Act 1952."
                )
            _PF_DEFAULTS["employer_rate"] = rate
        if employee_rate is not None:
            _PF_DEFAULTS["employee_rate"] = Decimal(str(employee_rate))

    # MN-G01: Gratuity — Industrial and Commercial Employment (Standing Orders) Ordinance 1968.
    # Eligibility: minimum `qualifying_years` (default 5) of continuous service.
    # Amount: 1 month basic salary per completed year of service.
    def calculate_gratuity(
        self,
        monthly_basic_salary: Any,
        years_of_service: Any,
        qualifying_years: int = 5,
    ) -> dict[str, Any]:
        basic = self._money(monthly_basic_salary)
        years = Decimal(str(years_of_service))
        completed_years = int(years)
        annual_basic = (basic * Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        eligible = completed_years >= qualifying_years
        if not eligible:
            return {
                "monthly_basic_salary": float(basic),
                "annual_basic_salary": float(annual_basic),
                "years_of_service": float(years),
                "completed_years": completed_years,
                "qualifying_years": qualifying_years,
                "eligible": False,
                "gratuity_amount": 0.0,
            }
        gratuity = (basic * Decimal(str(completed_years))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "monthly_basic_salary": float(basic),
            "annual_basic_salary": float(annual_basic),
            "years_of_service": float(years),
            "completed_years": completed_years,
            "qualifying_years": qualifying_years,
            "eligible": True,
            "gratuity_amount": float(gratuity),
        }

    # MN-G01: Provident Fund — Employees Provident Funds Act 1952.
    # Configurable employer/employee rates; defaults from _PF_DEFAULTS.
    def calculate_provident_fund(
        self,
        monthly_basic_salary: Any,
        employer_rate: Any = None,
        employee_rate: Any = None,
    ) -> dict[str, Any]:
        basic = self._money(monthly_basic_salary)
        er_rate = Decimal(str(employer_rate)) if employer_rate is not None else _PF_DEFAULTS["employer_rate"]
        emp_rate = Decimal(str(employee_rate)) if employee_rate is not None else _PF_DEFAULTS["employee_rate"]
        employer_pf = (basic * er_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        employee_pf = (basic * emp_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "monthly_basic_salary": float(basic),
            "employer_rate": float(er_rate),
            "employee_rate": float(emp_rate),
            "employer_pf": float(employer_pf),
            "employee_pf": float(employee_pf),
            "total_pf": float(
                (employer_pf + employee_pf).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ),
        }

    # G33/G35: tax_status and exemptions parameters added.
    # MN-G02: bonus_income parameter added — bonus is taxable income under FBR rules.
    def calculate_tax(
        self,
        monthly_taxable_income: Any,
        tax_year: str = "2026",
        tax_status: str = "filer",
        exemptions: list[dict[str, Any]] | None = None,
        bonus_income: Any | None = None,
    ) -> dict[str, Any]:
        monthly_income = self._money(monthly_taxable_income)
        annual_income = (monthly_income * Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # MN-G02: Add bonus income to annual taxable base before slab lookup.
        bonus = self._money(bonus_income) if bonus_income is not None else Decimal("0.00")
        annual_income = (annual_income + bonus).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # G35: Subtract statutory exempt allowances before slab lookup.
        # Exemptions: [{code, description, amount}] — medical, conveyance, HRA within limits.
        total_exemptions = Decimal("0.00")
        if exemptions:
            for ex in exemptions:
                total_exemptions += self._money(ex.get("amount", 0))
        annual_taxable = (annual_income - total_exemptions).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if annual_taxable < Decimal("0"):
            annual_taxable = Decimal("0.00")

        slab = self._slab_for_income(annual_taxable, tax_year)
        threshold = slab.get("threshold")
        if threshold is None:
            annual_tax = Decimal("0.00")
        else:
            annual_tax = (
                Decimal(str(slab["base_tax"]))
                + (annual_taxable - Decimal(str(threshold))) * Decimal(str(slab["rate"]))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # G33: Non-filer surcharge — Finance Act 2023/2024.
        # Non-filers pay 100% additional tax on salary income (effective rate doubles).
        non_filer_surcharge = Decimal("0.00")
        if str(tax_status).lower() == "non_filer":
            non_filer_surcharge = annual_tax
            annual_tax = (annual_tax * Decimal("2")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        monthly_tax = (annual_tax / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "tax_slab_code": slab["code"],
            "annual_taxable_income": float(annual_taxable),
            "total_exemptions": float(total_exemptions),
            "bonus_income": float(bonus),
            "annual_tax": float(annual_tax),
            "non_filer_surcharge": float(non_filer_surcharge),
            "monthly_tax": float(monthly_tax),
            "tax_status": tax_status,
        }

    # MN-G03: Arrears taxation — FBR requirement.
    # Arrears (backdated salary revisions) must be taxed in the period they relate to.
    # Taxing arrears entirely in the payment month inflates that month's income and
    # may incorrectly push the employee into a higher slab.
    def calculate_arrears_tax(
        self,
        arrears_amount: Any,
        period_months: int,
        monthly_salary_at_time: Any,
        tax_year: str = "2026",
        tax_status: str = "filer",
        exemptions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        arrears = self._money(arrears_amount)
        months = max(1, int(period_months))
        monthly_arrears = (arrears / Decimal(str(months))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        base = self.calculate_tax(monthly_salary_at_time, tax_year, tax_status, exemptions)
        base_monthly_tax = Decimal(str(base["monthly_tax"]))

        enhanced_monthly = self._money(monthly_salary_at_time) + monthly_arrears
        enhanced = self.calculate_tax(enhanced_monthly, tax_year, tax_status, exemptions)
        enhanced_monthly_tax = Decimal(str(enhanced["monthly_tax"]))

        incremental = max(Decimal("0.00"), enhanced_monthly_tax - base_monthly_tax)
        total_arrears_tax = (incremental * Decimal(str(months))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "arrears_amount": float(arrears),
            "period_months": months,
            "monthly_arrears": float(monthly_arrears),
            "base_monthly_salary": float(self._money(monthly_salary_at_time)),
            "base_monthly_tax": float(base_monthly_tax),
            "enhanced_monthly_tax": float(enhanced_monthly_tax),
            "incremental_monthly_tax": float(incremental),
            "total_arrears_tax": float(total_arrears_tax),
            "tax_year": tax_year,
            "tax_status": tax_status,
        }

    # G36: EOBI contribution calculation per employee.
    # insurable_wage = min(max(basic, eobi_min_wage), eobi_max_wage)
    def calculate_eobi(
        self,
        monthly_basic_salary: Any,
        eobi_min_wage: Any = None,
        eobi_max_wage: Any = None,
        employee_rate: Any = None,
        employer_rate: Any = None,
    ) -> dict[str, Any]:
        basic = self._money(monthly_basic_salary)
        min_wage = self._money(eobi_min_wage) if eobi_min_wage is not None else _EOBI_DEFAULTS["min_wage"]
        max_wage = self._money(eobi_max_wage) if eobi_max_wage is not None else _EOBI_DEFAULTS["max_wage"]
        emp_rate = Decimal(str(employee_rate)) if employee_rate is not None else _EOBI_DEFAULTS["employee_rate"]
        er_rate = Decimal(str(employer_rate)) if employer_rate is not None else _EOBI_DEFAULTS["employer_rate"]

        insurable_wage = min(max(basic, min_wage), max_wage).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        employee_eobi = (insurable_wage * emp_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        employer_eobi = (insurable_wage * er_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "insurable_wage": float(insurable_wage),
            "employee_eobi": float(employee_eobi),
            "employer_eobi": float(employer_eobi),
            "total_eobi": float((employee_eobi + employer_eobi).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        }

    # G37: Provincial social security contribution per employee.
    # Returns None if province has no registered regime.
    def calculate_social_security(
        self,
        province: str,
        monthly_gross_salary: Any,
        wage_cap: Any = None,
        employer_rate: Any = None,
        employee_rate: Any = None,
    ) -> dict[str, Any] | None:
        province_key = str(province).strip().lower()
        config = _SOCIAL_SECURITY_DEFAULTS.get(province_key)
        if config is None:
            return None

        gross = self._money(monthly_gross_salary)
        cap = self._money(wage_cap) if wage_cap is not None else config["wage_cap"]
        er_rate = Decimal(str(employer_rate)) if employer_rate is not None else config["employer_rate"]
        emp_rate = Decimal(str(employee_rate)) if employee_rate is not None else config["employee_rate"]

        social_security_wage = min(gross, cap).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        employer_contribution = (social_security_wage * er_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        employee_contribution = (social_security_wage * emp_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "regime": config["regime"],
            "social_security_wage": float(social_security_wage),
            "employer_contribution": float(employer_contribution),
            "employee_contribution": float(employee_contribution),
            "total_contribution": float(
                (employer_contribution + employee_contribution).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ),
        }

    # G38: Workers Profit Participation Fund — 5% of net profits.
    # Required under Companies Profits (Workers Participation) Act 1968.
    def calculate_wppf(self, net_profit: Any) -> dict[str, Any]:
        profit = self._money(net_profit)
        if profit <= Decimal("0"):
            return {"net_profit": float(profit), "wppf_amount": 0.0, "applicable": False}
        wppf = (profit * _WPPF_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {"net_profit": float(profit), "wppf_amount": float(wppf), "applicable": True}

    # G39: Workers Welfare Fund — 2% of income for employers with income > PKR 500,000/year.
    def calculate_wwf(self, annual_income: Any) -> dict[str, Any]:
        income = self._money(annual_income)
        if income <= _WWF_THRESHOLD:
            return {"annual_income": float(income), "wwf_amount": 0.0, "applicable": False, "threshold": float(_WWF_THRESHOLD)}
        wwf = (income * _WWF_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {"annual_income": float(income), "wwf_amount": float(wwf), "applicable": True, "threshold": float(_WWF_THRESHOLD)}

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
            province = str(employee.get("province", "")).strip()

            # G36: Calculate EOBI per employee
            eobi = self.calculate_eobi(
                monthly_basic_salary=employee.get("monthly_basic_salary", employee.get("monthly_gross_salary", 0)),
            )

            # G37: Calculate social security per employee
            ss = self.calculate_social_security(
                province=province,
                monthly_gross_salary=employee.get("monthly_gross_salary", 0),
            )

            employees.append({
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
                "province": province,
                "eobi": eobi,
                "social_security": ss,
            })

        total_taxable_income = sum((Decimal(str(item["annual_taxable_income"])) for item in employees), Decimal("0"))
        total_tax_deducted = sum((Decimal(str(item["monthly_tax_deducted"])) for item in employees), Decimal("0"))
        total_employer_eobi = sum(e.get("eobi", {}).get("employer_eobi", 0.0) for e in employees)
        total_employee_eobi = sum(e.get("eobi", {}).get("employee_eobi", 0.0) for e in employees)

        province_social_reports: dict[str, dict[str, Any]] = {}
        for item in employees:
            province_key = str(item.get("province", "")).strip().lower()
            if province_key == "punjab":
                key, regime = "pessi", "PESSI"
            elif province_key == "sindh":
                key, regime = "sessi", "SESSI"
            elif province_key in {"khyber pakhtunkhwa", "kp", "kpk"}:
                key, regime = "kp", "KP"
            else:
                continue
            if key not in province_social_reports:
                province_social_reports[key] = {
                    "period": {"month": month, "year": year},
                    "establishment": {
                        "name": str(org.get("name", "")),
                        "registration_number": str(org.get(f"{key}_registration", org.get("pessi_registration", ""))),
                        "social_security_regime": regime,
                    },
                    "employees": [],
                    "totals": {"employer_contribution": 0.0, "employee_contribution": 0.0},
                }
            ss = item.get("social_security") or {}
            province_social_reports[key]["employees"].append({
                "employee_id": item["employee_id"],
                "cnic": item["cnic"],
                "province": item.get("province", ""),
                "social_security_wage": ss.get("social_security_wage", 0.0),
                "employer_contribution": ss.get("employer_contribution", 0.0),
                "employee_contribution": ss.get("employee_contribution", 0.0),
            })
            province_social_reports[key]["totals"]["employer_contribution"] = round(
                province_social_reports[key]["totals"]["employer_contribution"] + ss.get("employer_contribution", 0.0), 2
            )
            province_social_reports[key]["totals"]["employee_contribution"] = round(
                province_social_reports[key]["totals"]["employee_contribution"] + ss.get("employee_contribution", 0.0), 2
            )

        _empty_ss = lambda regime, reg_key: {
            "period": {"month": month, "year": year},
            "establishment": {
                "name": str(org.get("name", "")),
                "registration_number": str(org.get(reg_key, "")),
                "social_security_regime": regime,
            },
            "employees": [],
            "totals": {"employer_contribution": 0.0, "employee_contribution": 0.0},
        }

        return {
            "reports": {
                "fbr_annexure_c": {
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
                },
                "eobi_pr_01": {
                    "submission_format": "PR-01",
                    "period": {"month": month, "year": year},
                    "employer": {
                        "name": str(org.get("name", "")),
                        "registration_number": str(org.get("eobi_registration", "")),
                    },
                    "employees": [
                        {
                            "employee_id": item["employee_id"],
                            "cnic": item["cnic"],
                            "insurable_wage": item.get("eobi", {}).get("insurable_wage", 0.0),
                            "employee_eobi": item.get("eobi", {}).get("employee_eobi", 0.0),
                            "employer_eobi": item.get("eobi", {}).get("employer_eobi", 0.0),
                        }
                        for item in employees
                    ],
                    "totals": {
                        "total_employer_eobi": round(total_employer_eobi, 2),
                        "total_employee_eobi": round(total_employee_eobi, 2),
                        "total_eobi": round(total_employer_eobi + total_employee_eobi, 2),
                    },
                },
                "pessi": province_social_reports.get("pessi", _empty_ss("PESSI", "pessi_registration")),
                "sessi": province_social_reports.get("sessi", _empty_ss("SESSI", "sessi_registration")),
                "kp": province_social_reports.get("kp", _empty_ss("KP", "kp_registration")),
            },
            "metadata": {
                "country_code": str(payload.get("country_code") or payload.get("jurisdiction") or "").upper(),
                "period": period,
            },
        }


PakistanComplianceService = PakistanStatutoryService
