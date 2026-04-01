from __future__ import annotations

from integrations.accounting.base import QuickBooksAdapter, SAPAdapter
from integrations.biometric.device_adapter import ingest_device_logs
from integrations.pakistan.bank_salary import generate_salary_bank_csv, generate_salary_bank_excel_rows
from integrations.pakistan.eobi_adapter import submit_pr01
from integrations.pakistan.fbr_adapter import submit_annexure_c
from integrations.pakistan.pessi_adapter import submit_contribution_return
from integrations.pakistan.raast_payment import build_raast_payment_export
from services.compliance_service import PakistanComplianceService


def _compliance_reports() -> dict[str, object]:
    service = PakistanComplianceService()
    generated = service.generate_reports(
        {
            "period": "2026-01",
            "organization_data": {
                "ntn": "NTN-123",
                "name": "SME Demo",
                "address": "Lahore",
                "withholding_agent_cnic_ntn": "3520212345678",
                "eobi_registration": "EOBI-22",
                "pessi_registration": "PESSI-44",
            },
            "employee_records": [
                {
                    "employee_id": "E-1",
                    "cnic": "3520212345678",
                    "full_name": "Ali Khan",
                    "tax_status": "filer",
                    "annual_gross_income": "1200000",
                    "annual_taxable_income": "1200000",
                    "tax_slab_code": "S2",
                    "annual_tax": "30000",
                    "monthly_tax_deducted": "2500",
                    "exemptions": [],
                }
            ],
        }
    )
    return generated["reports"]


def test_submission_adapters_accept_compliance_payloads() -> None:
    reports = _compliance_reports()

    fbr = submit_annexure_c(reports["fbr_annexure_c"])
    assert fbr["submitted"] is True

    eobi = submit_pr01(reports["eobi_pr_01"])
    assert eobi["submitted"] is True

    pessi = submit_contribution_return(reports["pessi"])
    assert pessi["submitted"] is True


def test_bank_salary_and_raast_exports_are_callable() -> None:
    employees = [
        {
            "employee_id": "E-1",
            "full_name": "Ali Khan",
            "bank_account": "0123456789",
            "iban": "PK36SCBL0000001123456702",
            "net_salary": "97500.50",
        }
    ]

    csv_payload = generate_salary_bank_csv({"employees": employees, "currency": "PKR"})
    assert "employee_id,employee_name,bank_account,iban,net_salary,currency,payment_reference" in csv_payload
    assert "E-1,Ali Khan" in csv_payload

    excel_payload = generate_salary_bank_excel_rows({"employees": employees})
    assert excel_payload["sheet_name"] == "SalaryDisbursement"
    assert len(excel_payload["rows"]) == 2

    raast = build_raast_payment_export(
        {
            "company": "SME Demo",
            "payments": [
                {
                    "transaction_id": "TX-1",
                    "amount": "97500.50",
                    "debtor_iban": "PK36SCBL0000001123456702",
                    "creditor_iban": "PK12HABB0000001010101010",
                    "employee_id": "E-1",
                }
            ],
        }
    )
    assert raast["payment_network"] == "RAAST"
    assert raast["batch"]["transaction_count"] == 1


def test_accounting_and_biometric_adapters_are_callable() -> None:
    qb = QuickBooksAdapter().export_payroll_journal({"journal_entries": [{"account": "Salaries", "amount": "100"}]})
    sap = SAPAdapter().export_payroll_journal({"journal_entries": [{"account": "Salaries", "amount": "100"}]})

    assert qb["status"] == "stubbed"
    assert sap["status"] == "stubbed"

    biometric = ingest_device_logs(
        {
            "logs": [
                {"employee_id": "E-1", "event_type": "check_in", "timestamp": "2026-01-01T09:00:00Z", "device_id": "BIO-1"},
                {"employee_id": "", "event_type": "check_out", "timestamp": "not-a-date", "device_id": "BIO-1"},
            ]
        }
    )
    assert biometric["accepted_logs"] == 1
    assert biometric["rejected_logs"] == 1
