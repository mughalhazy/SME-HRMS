import base64
import json

from payroll_service import PayrollService


def _token(role: str) -> str:
    return "Bearer " + base64.urlsafe_b64encode(json.dumps({"role": role}).encode()).decode().rstrip("=")


class _StubRules:
    called = False

    def apply_rules(self, input):
        self.called = True
        return {
            "adjusted_gross_salary": float(input["gross_salary"]),
            "rule_adjustments": [],
            "final_deductions": {"total": float(input.get("deductions", 0))},
            "extra_earnings": 0.0,
            "extra_deductions": 0.0,
        }


class _StubTax:
    called = False

    def calculate_tax(self, input):
        self.called = True
        return {"tax_amount": 10.0}


class _StubCompliance:
    called_validate = False
    called_reports = False

    def validate_payroll(self, input):
        self.called_validate = True
        return {"is_valid": True, "violations": []}

    def generate_reports(self, input):
        self.called_reports = True
        return {"reports": [], "metadata": {}}


class _StubAdapter:
    def __init__(self):
        self.tax_engine = _StubTax()
        self.payroll_rules_engine = _StubRules()
        self.compliance_engine = _StubCompliance()


class _StubResolver:
    def __init__(self):
        self.adapter = _StubAdapter()

    def resolve(self, organization_id: str):
        return self.adapter


def test_payroll_routes_through_country_adapter() -> None:
    service = PayrollService()
    service.country_resolver = _StubResolver()
    admin = _token("Admin")

    service.upsert_payroll_tax_profile(
        {
            "employee_id": "emp-country-1",
            "jurisdiction": "PK",
            "tax_code": "PK-WHT",
            "metadata": {"rate": "5.00"},
        },
        admin,
    )

    _, record = service.create_payroll_record(
        {
            "employee_id": "emp-country-1",
            "pay_period_start": "2026-01-01",
            "pay_period_end": "2026-01-31",
            "base_salary": "1000.00",
            "currency": "USD",
        },
        admin,
    )
    assert record["deductions"] == "10.00"

    service.run_payroll("2026-01-01", "2026-01-31", admin)
    assert service.country_resolver.adapter.payroll_rules_engine.called is True
    assert service.country_resolver.adapter.tax_engine.called is True
    assert service.country_resolver.adapter.compliance_engine.called_validate is True
    assert service.country_resolver.adapter.compliance_engine.called_reports is True
