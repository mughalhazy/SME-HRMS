from __future__ import annotations

import base64
import json

import pytest

from payroll_service import PayrollService, ServiceError
from services.compliance_service import PakistanComplianceService
from services.compliance_autopilot import ComplianceAutopilot


def _token(role: str) -> str:
    return "Bearer " + base64.urlsafe_b64encode(json.dumps({"role": role}).encode()).decode().rstrip("=")


def test_tax_slabs_formula_2026() -> None:
    service = PakistanComplianceService()
    zero_tax = service.calculate_tax("50000", tax_year="2026")
    assert zero_tax["tax_slab_code"] == "S1"
    assert zero_tax["annual_tax"] == 0.0
    assert zero_tax["monthly_tax"] == 0.0

    slab_s4 = service.calculate_tax("200000", tax_year="2026")
    assert slab_s4["tax_slab_code"] == "S4"
    assert slab_s4["annual_tax"] == 230000.0
    assert slab_s4["monthly_tax"] == 19166.67


def test_report_schema_contains_required_payloads() -> None:
    service = PakistanComplianceService()
    output = service.generate_reports(
        {
            "period": "2026-01",
            "organization_data": {"ntn": "NTN-1", "name": "Demo Org", "address": "LHR", "withholding_agent_cnic_ntn": "123"},
            "employee_records": [
                {
                    "employee_id": "E-1",
                    "cnic": "1234567890123",
                    "full_name": "Ali",
                    "annual_taxable_income": "1200000",
                    "annual_tax": "30000",
                    "monthly_tax_deducted": "2500",
                    "tax_slab_code": "S2",
                }
            ],
        }
    )
    reports = output["reports"]
    assert "fbr_annexure_c" in reports
    assert "eobi_pr_01" in reports
    assert "pessi" in reports
    assert reports["fbr_annexure_c"]["totals"]["total_employees"] == 1


def test_invalid_payroll_is_blocked_for_missing_cnic() -> None:
    payroll = PayrollService()
    admin = _token("Admin")
    payroll.upsert_payroll_tax_profile(
        {
            "employee_id": "emp-invalid-cnic",
            "jurisdiction": "DEFAULT",
            "tax_code": "WHT",
            "metadata": {"rate": "5.00", "cnic": "abc"},
        },
        admin,
    )
    payroll.create_payroll_record(
        {
            "employee_id": "emp-invalid-cnic",
            "pay_period_start": "2026-02-01",
            "pay_period_end": "2026-02-28",
            "base_salary": "100000.00",
            "currency": "USD",
        },
        admin,
    )
    with pytest.raises(ServiceError) as exc:
        payroll.run_payroll("2026-02-01", "2026-02-28", admin)
    assert exc.value.code == "COMPLIANCE_VALIDATION_FAILED"


def test_compliance_autopilot_blocks_invalid_payroll() -> None:
    service = PakistanComplianceService()
    autopilot = ComplianceAutopilot(service)
    result = autopilot.run_precheck(
        {
            "period": "2026-01",
            "employee_records": [
                {
                    "employee_id": "E-1",
                    "full_name": "Ali",
                    "cnic": "bad",
                    "annual_taxable_income": "1000",
                }
            ],
            "organization_data": {"name": "Demo Org"},
        }
    )
    assert result["ok"] is False
    assert result["stop_payroll"] is True
    assert result["error"]["code"] == "COMPLIANCE_VALIDATION_FAILED"


def test_compliance_autopilot_generates_required_json_outputs() -> None:
    service = PakistanComplianceService()
    autopilot = ComplianceAutopilot(service)
    result = autopilot.run_precheck(
        {
            "period": "2026-01",
            "organization_data": {"ntn": "NTN-1", "name": "Demo Org", "address": "LHR", "withholding_agent_cnic_ntn": "123"},
            "employee_records": [
                {
                    "employee_id": "E-1",
                    "cnic": "1234567890123",
                    "full_name": "Ali",
                    "annual_taxable_income": "1200000",
                    "annual_tax": "30000",
                    "monthly_tax_deducted": "2500",
                    "tax_slab_code": "S2",
                }
            ],
        }
    )
    assert result["ok"] is True
    outputs = result["outputs"]
    assert "fbr_json" in outputs
    assert "eobi_json" in outputs
    assert "pessi_json" in outputs
    assert outputs["fbr_json"]["totals"]["total_employees"] == 1
