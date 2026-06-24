from __future__ import annotations

from typing import Any

from country.base.compliance_engine import ComplianceEngineInterface


class DummyComplianceEngine(ComplianceEngineInterface):
    """Minimal compliance engine for architecture proof tests. Returns no violations."""

    def validate_payroll(self, input: dict[str, Any]) -> dict[str, Any]:
        return {"valid": True, "violations": [], "country": "dummy"}

    def generate_reports(self, input: dict[str, Any]) -> dict[str, Any]:
        return {"reports": [], "country": "dummy"}
