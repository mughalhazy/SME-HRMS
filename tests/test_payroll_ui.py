from payroll_ui import PAYROLL_SUMMARY_FIELDS, build_payroll_ui


def test_build_payroll_ui_for_authorized_user():
    rows = [
        {
            "payroll_record_id": "pr-1",
            "employee_id": "emp-1",
            "employee_number": "E001",
            "employee_name": "Alice",
            "department_id": "dep-1",
            "department_name": "Finance",
            "pay_period_start": "2026-01-01",
            "pay_period_end": "2026-01-31",
            "base_salary": "1000.00",
            "allowances": "100.00",
            "deductions": "50.00",
            "overtime_pay": "20.00",
            "gross_pay": "1120.00",
            "net_pay": "1070.00",
            "currency": "USD",
            "payment_date": None,
            "status": "Processed",
            "updated_at": "2026-02-01T00:00:00Z",
            "ignored_field": "should-not-leak",
        }
    ]

    ui = build_payroll_ui(rows, ["CAP-PAY-001", "CAP-PAY-002"])

    assert ui["surface"] == "payroll_dashboard"
    assert ui["readModel"] == "payroll_summary_view"
    assert ui["summary"]["records"] == 1
    assert ui["summary"]["totalGrossPay"] == "1120.00"
    assert ui["summary"]["totalNetPay"] == "1070.00"
    assert ui["actions"]["runPayroll"] is True
    assert ui["actions"]["markPaid"] is True
    assert list(ui["table"]["rows"][0].keys()) == list(PAYROLL_SUMMARY_FIELDS)
    assert "ignored_field" not in ui["table"]["rows"][0]


def test_build_payroll_ui_for_unauthorized_user():
    ui = build_payroll_ui([], [])

    assert ui["permissions"]["can_read"] is False
    assert ui["table"]["rows"] == []
    assert ui["summary"]["records"] == 0
    assert ui["actions"]["runPayroll"] is False
    assert ui["actions"]["markPaid"] is False
