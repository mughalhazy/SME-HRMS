from .compliance_engine import PakistanComplianceEngine
from .payroll_rules import PakistanPayrollRulesEngine
from .tax_engine import PakistanTaxEngine


class PakistanAdapter:
    def __init__(self) -> None:
        self.tax_engine = PakistanTaxEngine()
        self.compliance_engine = PakistanComplianceEngine()
        self.payroll_rules_engine = PakistanPayrollRulesEngine()


__all__ = ["PakistanAdapter", "PakistanTaxEngine", "PakistanComplianceEngine", "PakistanPayrollRulesEngine"]
