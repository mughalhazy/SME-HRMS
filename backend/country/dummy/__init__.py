from .banking import DummyBankingAdapter
from .compliance_engine import DummyComplianceEngine
from .payroll_rules import DummyPayrollRulesEngine
from .statutory_validator import DummyStatutoryValidator
from .tax_engine import DummyTaxEngine


class DummyAdapter:
    """
    Minimal country adapter for architecture proof.
    Proves that a second country can be added as adapter-only with zero service changes.
    """

    def __init__(self) -> None:
        self.tax_engine = DummyTaxEngine()
        self.compliance_engine = DummyComplianceEngine()
        self.payroll_rules_engine = DummyPayrollRulesEngine()
        self.statutory_validator = DummyStatutoryValidator()
        self.banking = DummyBankingAdapter()


__all__ = [
    "DummyAdapter",
    "DummyTaxEngine",
    "DummyComplianceEngine",
    "DummyPayrollRulesEngine",
    "DummyStatutoryValidator",
    "DummyBankingAdapter",
]
