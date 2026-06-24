"""
S7-G02 — Architecture proof: second country adapter works without service changes.

Tests:
1. Resolver returns Pakistan adapter for Pakistan org.
2. Resolver returns Dummy adapter for dummy org.
3. Both adapters satisfy the same interfaces — no service code changes needed.
"""
import pytest

from core.country_resolver import CountryResolver, seed_dev_defaults
from country.base.banking_interface import BankingInterface
from country.base.tax_engine import TaxEngineInterface
from country.base.compliance_engine import ComplianceEngineInterface
from country.base.payroll_rules import PayrollRulesInterface


@pytest.fixture()
def resolver():
    r = CountryResolver()
    seed_dev_defaults(r)
    return r


def test_resolver_returns_pakistan_adapter(resolver):
    adapter = resolver.resolve("ORG_DEFAULT")
    from country.pakistan import PakistanAdapter
    assert isinstance(adapter, PakistanAdapter)


def test_resolver_returns_dummy_adapter(resolver):
    adapter = resolver.resolve("ORG_DUMMY")
    from country.dummy import DummyAdapter
    assert isinstance(adapter, DummyAdapter)


def test_both_adapters_satisfy_interfaces(resolver):
    """No service change is needed — both adapters expose the same interface attributes."""
    for org_id in ("ORG_DEFAULT", "ORG_DUMMY"):
        adapter = resolver.resolve(org_id)
        assert isinstance(adapter.tax_engine, TaxEngineInterface), f"{org_id} tax_engine interface"
        assert isinstance(adapter.compliance_engine, ComplianceEngineInterface), f"{org_id} compliance_engine interface"
        assert isinstance(adapter.payroll_rules_engine, PayrollRulesInterface), f"{org_id} payroll_rules_engine interface"
        assert isinstance(adapter.banking, BankingInterface), f"{org_id} banking interface"


def test_dummy_tax_engine_returns_zero_tax(resolver):
    adapter = resolver.resolve("ORG_DUMMY")
    result = adapter.tax_engine.calculate_tax({"gross_salary": 100000})
    assert result["tax_amount"] == 0.0


def test_dummy_banking_returns_balanced_reconciliation(resolver):
    adapter = resolver.resolve("ORG_DUMMY")
    result = adapter.banking.reconcile_payroll_payments({"payroll": [], "payments": []})
    assert result["summary"]["is_balanced"] is True


def test_pakistan_banking_adapter_present(resolver):
    adapter = resolver.resolve("ORG_DEFAULT")
    assert isinstance(adapter.banking, BankingInterface)
