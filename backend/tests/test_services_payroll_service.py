from services.payroll_service import PayrollService
from services.attendance_service import AttendanceService
from datetime import date, datetime


def test_calculation_flow_matches_spec() -> None:
    service = PayrollService()
    gross = service.calculate_gross("1000", "250")
    taxable = service.calculate_taxable(gross, "100")
    net = service.calculate_net(taxable, "50")

    assert str(gross) == "1250.00"
    assert str(taxable) == "1150.00"
    assert str(net) == "1100.00"


def test_component_helpers_and_final_settlement() -> None:
    service = PayrollService()

    assert str(service.gratuity("1000", "0.0833")) == "83.30"
    assert str(service.provident_fund("1000", "0.10")) == "100.00"
    assert str(service.loan_deduction("75")) == "75.00"

    settlement = service.final_settlement("1200", "300")
    assert settlement == {
        "leave_encashment": "1200.00",
        "pending_deductions": "300.00",
        "net_settlement": "900.00",
    }


def test_frequency_support_and_engine_integration() -> None:
    service = PayrollService()

    monthly = service.calculate_payroll(
        basic="120000",
        allowances="30000",
        deductions="10000",
        frequency="monthly",
        compliance_payload={"employee_records": []},
    )
    weekly = service.calculate_payroll(
        basic="120000",
        allowances="30000",
        deductions="10000",
        frequency="weekly",
        compliance_payload={"employee_records": []},
    )
    daily = service.calculate_payroll(
        basic="120000",
        allowances="30000",
        deductions="10000",
        frequency="daily",
        compliance_payload={"employee_records": []},
    )

    assert monthly["frequency"] == "monthly"
    assert weekly["frequency"] == "weekly"
    assert daily["frequency"] == "daily"

    assert monthly["compliance"]["is_valid"] is True
    assert weekly["compliance"]["is_valid"] is True
    assert daily["compliance"]["is_valid"] is True


def test_negative_net_is_blocked_for_payout_and_carried_forward() -> None:
    service = PayrollService()
    result = service.calculate_payroll(
        basic="1000",
        allowances="0",
        deductions="5000",
        frequency="monthly",
        compliance_payload={"employee_records": []},
    )

    assert result["net"] == "-4000.00"
    assert result["payout"] == "0.00"
    assert result["carry_forward"] == "4000.00"


def test_overtime_is_included_as_payroll_input() -> None:
    service = PayrollService()
    result = service.calculate_payroll(
        basic="1000",
        allowances="100",
        deductions="50",
        overtime_hours="5",
        overtime_rate="20",
        frequency="monthly",
        compliance_payload={"employee_records": []},
    )

    assert result["overtime_pay"] == "100.00"
    assert result["gross"] == "1200.00"
    assert result["taxable"] == "1150.00"


def test_policy_engine_supports_overtime_tiers_penalties_and_shift_rules() -> None:
    service = PayrollService()
    result = service.calculate_payroll(
        basic="1000",
        allowances="100",
        deductions="50",
        overtime_hours="5",
        overtime_rate="20",
        overtime_tiers=[
            {"up_to_hours": "2", "rate": "20"},
            {"up_to_hours": "4", "rate": "30"},
        ],
        penalties=[{"mode": "flat", "value": "10"}, {"mode": "percent_of_basic", "value": "1"}],
        shift_rules=[{"shift": "night", "mode": "flat", "value": "25"}],
        shift_key="night",
        frequency="monthly",
        compliance_payload={"employee_records": []},
    )

    assert result["overtime_pay"] == "130.00"
    assert result["shift_pay"] == "25.00"
    assert result["penalties"] == "20.00"
    assert result["gross"] == "1255.00"
    assert result["taxable"] == "1185.00"


def test_attendance_sync_penalties_and_overtime_feed_payroll_correctly() -> None:
    attendance = AttendanceService()
    payroll = PayrollService()

    attendance.record_attendance(
        employee_id="emp-3",
        attendance_date=date(2026, 3, 1),
        source="biometric",
        shift_hours="8",
        check_in=datetime(2026, 3, 1, 9, 30),
        check_out=datetime(2026, 3, 1, 19, 30),
        scheduled_start_hour=9,
        grace_period_minutes=10,
        late_penalty_ladder=[
            {"up_to_minutes": 5, "penalty": "2"},
            {"up_to_minutes": 30, "penalty": "10"},
        ],
    )

    payroll_inputs = attendance.sync_attendance_to_payroll_inputs(
        employee_id="emp-3",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )
    result = payroll.calculate_payroll(
        basic="1000",
        allowances="100",
        deductions="50",
        overtime_hours=payroll_inputs["overtime_hours"],
        overtime_rate="20",
        penalties=[{"mode": "flat", "value": payroll_inputs["late_penalties"]}],
        frequency="monthly",
        compliance_payload={"employee_records": []},
    )

    assert payroll_inputs["overtime_hours"] == "2.00"
    assert payroll_inputs["late_penalties"] == "10.00"
    assert result["overtime_pay"] == "40.00"
    assert result["penalties"] == "10.00"
    assert result["taxable"] == "1080.00"
