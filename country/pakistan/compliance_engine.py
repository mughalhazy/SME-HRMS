from __future__ import annotations

from typing import Any

from country.base import ComplianceEngine


class PakistanComplianceEngine(ComplianceEngine):
    def validate_payroll(self, input: dict[str, Any]) -> dict[str, Any]:
        violations: list[dict[str, str]] = []
        if str(input.get("country_code", "")).upper() != "PK":
            violations.append(
                {
                    "code": "COUNTRY_MISMATCH",
                    "message": "Pakistan adapter requires country_code PK",
                    "severity": "error",
                }
            )
        if not list(input.get("employee_records", [])):
            violations.append(
                {
                    "code": "EMPTY_PAYROLL",
                    "message": "Employee records are required for compliance validation",
                    "severity": "warning",
                }
            )
        return {"is_valid": not any(v["severity"] == "error" for v in violations), "violations": violations}

    def generate_reports(self, input: dict[str, Any]) -> dict[str, Any]:
        period = str(input.get("period", "unknown"))
        country_code = str(input.get("country_code", "PK")).upper()
        return {
            "reports": [
                {
                    "report_type": "annexure_c",
                    "file_name": f"annexure_c_{period}_{country_code}.json",
                    "content_ref": f"reports/{country_code.lower()}/{period}/annexure_c.json",
                }
            ],
            "metadata": {"country_code": country_code, "period": period},
        }
