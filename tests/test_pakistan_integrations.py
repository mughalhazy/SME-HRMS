from __future__ import annotations

from integrations.accounting.base import QuickBooksAdapter, SAPAdapter, SAPConnectorConfig
from integrations.biometric.device_adapter import ingest_device_logs
from integrations.http_client import IntegrationHTTPError
from integrations.pakistan.bank_salary import generate_salary_bank_csv, generate_salary_bank_excel_rows
from integrations.pakistan.eobi_adapter import submit_pr01
from integrations.pakistan.fbr_adapter import submit_annexure_c
from integrations.pakistan.pessi_adapter import submit_contribution_return
from integrations.pakistan.raast_payment import build_raast_payment_export
from integrations.pakistan.submission_tracking import SubmissionTracker
from services.compliance_service import PakistanComplianceService


class FakeHttpClient:
    def __init__(self, response: dict[str, object] | None = None, error: Exception | None = None) -> None:
        self.response = response or {"status_code": 200, "body": {"ack_id": "ACK-1", "status": "accepted"}}
        self.error = error
        self.calls: list[dict[str, object]] = []

    def post_json(self, url: str, payload: dict[str, object], headers: dict[str, str] | None = None) -> dict[str, object]:
        self.calls.append({"url": url, "payload": payload, "headers": headers or {}})
        if self.error:
            raise self.error
        return self.response


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


def test_submission_adapters_make_http_calls_with_compliance_payloads() -> None:
    reports = _compliance_reports()
    tracker = SubmissionTracker()

    fbr_client = FakeHttpClient(response={"status_code": 200, "body": {"ack_id": "FBR-ACK"}})
    fbr = submit_annexure_c(
        reports["fbr_annexure_c"],
        http_client=fbr_client,
        tracker=tracker,
        config={"base_url": "https://fbr.example", "auth_token": "token", "signing_secret": "secret", "timeout_seconds": 5, "retry_attempts": 4},
    )
    assert fbr["submitted"] is True
    assert fbr["submission_status"] == "submitted"
    assert len(fbr_client.calls) == 1

    eobi_client = FakeHttpClient(response={"status_code": 200, "body": {"ack_id": "EOBI-ACK"}})
    eobi = submit_pr01(
        reports["eobi_pr_01"],
        http_client=eobi_client,
        tracker=tracker,
        config={"base_url": "https://eobi.example", "auth_token": "token", "timeout_seconds": 9, "retry_attempts": 2},
    )
    assert eobi["submitted"] is True
    assert eobi["submission_status"] == "submitted"

    pessi_client = FakeHttpClient(response={"status_code": 200, "body": {"ack_id": "PESSI-ACK"}})
    pessi = submit_contribution_return(
        reports["pessi"],
        http_client=pessi_client,
        tracker=tracker,
        config={"base_url": "https://pessi.example", "auth_token": "token", "timeout_seconds": 7, "retry_attempts": 3},
    )
    assert pessi["submitted"] is True
    assert pessi["submission_status"] == "submitted"

    stored = tracker.get(eobi["submission_id"])
    assert stored is not None
    assert stored.status == "ACKNOWLEDGED"
    assert stored.response_payload["ack_id"] == "EOBI-ACK"
    assert stored.attempt_count == 1


def test_submission_adapters_map_http_errors() -> None:
    reports = _compliance_reports()
    tracker = SubmissionTracker()
    err = IntegrationHTTPError(status_code=503, code="UNAVAILABLE", message="Service unavailable")
    result = submit_annexure_c(
        reports["fbr_annexure_c"],
        http_client=FakeHttpClient(error=err),
        tracker=tracker,
        config={"base_url": "https://fbr.example", "auth_token": "token"},
    )
    assert result["submitted"] is False
    assert result["submission_status"] == "failed"
    assert result["http_status"] == 503
    stored = tracker.get(result["submission_id"])
    assert stored is not None
    assert stored.status == "FAILED"


def test_submission_lifecycle_retry_and_manual_reconcile_flow() -> None:
    reports = _compliance_reports()
    tracker = SubmissionTracker()
    err = IntegrationHTTPError(status_code=503, code="UNAVAILABLE", message="Service unavailable")
    result = submit_annexure_c(
        reports["fbr_annexure_c"],
        http_client=FakeHttpClient(error=err),
        tracker=tracker,
        config={"base_url": "https://fbr.example", "auth_token": "token", "retry_attempts": 2},
    )
    assert result["submitted"] is False
    stored = tracker.get(result["submission_id"])
    assert stored is not None
    assert stored.status == "FAILED"
    assert any(h["to"] == "RETRY" for h in (stored.history or []))
    exports = tracker.export_for_manual_fallback()
    assert any(row["submission_id"] == result["submission_id"] for row in exports)

    reconciled = tracker.reconcile_manual_ack(result["submission_id"], {"ack_id": "MANUAL-ACK"})
    assert reconciled is True
    assert tracker.get(result["submission_id"]).status == "ACKNOWLEDGED"


def test_bank_salary_and_raast_exports_validate_and_build() -> None:
    employees = [{"employee_id": "E-1", "full_name": "Ali Khan", "bank_account": "0123456789", "iban": "PK36SCBL0000001123456702", "net_salary": "97500.50"}]

    csv_payload = generate_salary_bank_csv({"employees": employees, "currency": "PKR"})
    assert "employee_id,employee_name,bank_account,iban,net_salary,currency,payment_reference" in csv_payload
    assert "97500.50" in csv_payload

    excel_payload = generate_salary_bank_excel_rows({"employees": employees})
    assert excel_payload["sheet_name"] == "SalaryDisbursement"
    assert len(excel_payload["rows"]) == 2

    raast = build_raast_payment_export(
        {
            "company": "SME Demo",
            "payments": [{"transaction_id": "TX-1", "amount": "97500.50", "debtor_iban": "PK36SCBL0000001123456702", "creditor_iban": "PK12HABB0000001010101010", "employee_id": "E-1"}],
        }
    )
    assert raast["payment_network"] == "RAAST"
    assert raast["batch"]["transaction_count"] == 1


def test_accounting_and_biometric_adapters() -> None:
    qb_client = FakeHttpClient(response={"status_code": 200, "body": {"JournalEntry": {"Id": "1", "SyncToken": "0"}}})
    qb = QuickBooksAdapter(
        config={"base_url": "https://quickbooks.example", "realm_id": "123", "access_token": "token", "retry_attempts": 5, "timeout_seconds": 8},
        http_client=qb_client,
    ).export_payroll_journal({"journal_entries": [{"account": "Salaries", "amount": "100"}]})
    assert qb["status"] == "success"

    sap_client = FakeHttpClient(response={"status_code": 200, "body": {"document_id": "DOC-1"}})
    sap = SAPAdapter(
        SAPConnectorConfig(base_url="https://sap.example", company_code="1000", auth_token="token", timeout_seconds=5, retry_attempts=4),
        http_client=sap_client,
    ).export_payroll_journal({"journal_entries": [{"gl": "5000", "amount": "100"}], "posting_date": "2026-01-31"})
    assert sap["status"] == "success"

    biometric = ingest_device_logs(
        {
            "logs": [
                {"emp_code": "E-1", "event_code": "IN", "event_time": "2026-01-01T09:00:00Z", "terminal_id": "BIO-1"},
                {"employee": {"code": "E-2"}, "event": {"id": "1", "ts": "2026-01-01T17:00:00Z"}, "device": {"serial": "BIO-2"}},
                {"employee_id": "", "event_type": "check_out", "timestamp": "not-a-date", "device_id": "BIO-1"},
            ]
        }
    )
    assert biometric["accepted_logs"] == 2
    assert biometric["rejected_logs"] == 1
