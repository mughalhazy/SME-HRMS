from __future__ import annotations

import inspect

from core.country_resolver import CountryResolver
from country.base import ComplianceEngineInterface, PayrollRulesInterface, TaxEngineInterface
from country.pakistan.payroll_rules import PakistanPayrollRulesEngine
from country.pakistan.tax_engine import PakistanTaxEngine
from services.ai.anomaly_engine import AnomalyEngine
from services.compliance_autopilot import ComplianceAutopilot


def test_country_abstraction_resolves_adapter_with_interface_contracts_only() -> None:
    resolver = CountryResolver()
    adapter = resolver.resolve("ORG_DEFAULT")

    assert isinstance(adapter.tax_engine, TaxEngineInterface)
    assert isinstance(adapter.compliance_engine, ComplianceEngineInterface)
    assert isinstance(adapter.payroll_rules_engine, PayrollRulesInterface)


class _LifecycleSpyCompliance:
    def __init__(self, *, is_valid: bool) -> None:
        self.is_valid = is_valid
        self.calls: list[str] = []

    def validate_payroll(self, _payload):
        self.calls.append("validate")
        return {"is_valid": self.is_valid, "violations": [] if self.is_valid else [{"rule_id": "X"}]}

    def generate_reports(self, _payload):
        self.calls.append("reports")
        return {"reports": {"fbr_annexure_c": {}, "eobi_pr_01": {}, "pessi": {}}, "metadata": {}}


def test_compliance_lifecycle_validates_before_reports_and_blocks_invalid() -> None:
    valid_spy = _LifecycleSpyCompliance(is_valid=True)
    valid_result = ComplianceAutopilot(valid_spy).run_precheck({"employee_records": []})

    assert valid_spy.calls == ["validate", "reports"]
    assert valid_result["ok"] is True
    assert valid_result["stop_payroll"] is False

    invalid_spy = _LifecycleSpyCompliance(is_valid=False)
    invalid_result = ComplianceAutopilot(invalid_spy).run_precheck({"employee_records": []})

    assert invalid_spy.calls == ["validate"]
    assert invalid_result["ok"] is False
    assert invalid_result["stop_payroll"] is True


def test_payroll_correctness_uses_country_adapters_for_rules_and_tax() -> None:
    rules = PakistanPayrollRulesEngine()
    tax = PakistanTaxEngine()

    rule_result = rules.apply_rules(
        {
            "gross_salary": "100000",
            "allowances": "5000",
            "deductions": "1000",
            "context": {"taxable_earnings": "100000"},
            "rules": [
                {"active": True, "category": "earning", "calculation_mode": "flat", "value": "2000", "code": "BONUS", "name": "Bonus"},
                {
                    "active": True,
                    "category": "deduction",
                    "calculation_mode": "percent",
                    "value": "1.5",
                    "input_key": "taxable_earnings",
                    "code": "LEVY",
                    "name": "Levy",
                },
            ],
        }
    )

    assert rule_result["adjusted_gross_salary"] == 102000.0
    assert rule_result["final_deductions"]["total"] == 2500.0

    slab_tax = tax.calculate_tax({"gross_salary": "200000", "tax_year": "2026", "employee_data": {}})
    assert slab_tax["tax_amount"] == 19166.67

    override_tax = tax.calculate_tax({"gross_salary": "100000", "employee_data": {"metadata": {"rate": "5"}}})
    assert override_tax["tax_amount"] == 5000.0


def test_anomaly_detection_thresholds_and_explanations_are_consistent() -> None:
    engine = AnomalyEngine()

    low = engine.detect_overtime_anomaly(current_overtime_hours=10, historical_average_overtime_hours=10)
    high = engine.detect_overtime_anomaly(current_overtime_hours=50, historical_average_overtime_hours=10)
    promo = engine.detect_salary_spike(current_salary=130000, historical_average_salary=100000, promotion_event=True)
    no_promo = engine.detect_salary_spike(current_salary=130000, historical_average_salary=100000, promotion_event=False)

    assert low["risk_score"] < high["risk_score"]
    assert engine.threshold_level(low["risk_score"]) in {"low", "medium"}
    assert engine.threshold_level(high["risk_score"]) == "high"
    assert promo["risk_score"] < no_promo["risk_score"]
    assert "WHY_FLAGGED:" in high["explanation"]


def test_core_payroll_service_has_no_country_specific_branching() -> None:
    source = inspect.getsource(__import__("payroll_service"))

    assert "if country" not in source.lower()
    assert "pakistan" not in source.lower()
    assert "country_resolver" in source
