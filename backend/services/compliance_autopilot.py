from __future__ import annotations

from typing import Any


class ComplianceAutopilot:
    """Precheck orchestrator for payroll compliance validation and report generation."""

    def __init__(self, compliance_service: Any) -> None:
        self.compliance_service = compliance_service

    def run_precheck(self, payroll_batch: dict[str, Any]) -> dict[str, Any]:
        validation = self.compliance_service.validate_payroll(payroll_batch)
        if not validation.get("is_valid", False):
            return {
                "ok": False,
                "stop_payroll": True,
                "error": {
                    "code": "COMPLIANCE_VALIDATION_FAILED",
                    "message": "Payroll compliance validation failed",
                    "details": list(validation.get("violations", [])),
                },
                "validation": validation,
            }

        reports = self.compliance_service.generate_reports(payroll_batch)
        generated_reports = reports.get("reports", {}) if isinstance(reports, dict) else {}
        if not isinstance(generated_reports, dict):
            generated_reports = {}
        return {
            "ok": True,
            "stop_payroll": False,
            "validation": validation,
            "reports": reports,
            "outputs": {
                "fbr_json": generated_reports.get("fbr_annexure_c", {}),
                "eobi_json": generated_reports.get("eobi_pr_01", {}),
                "pessi_json": generated_reports.get("pessi", {}),
            },
        }
