from datetime import date, datetime

from services.attendance_service import AttendanceService


def test_attendance_inputs_shift_hours_overtime_and_sync_to_payroll() -> None:
    service = AttendanceService()

    service.record_attendance(
        employee_id="emp-1",
        attendance_date=date(2026, 3, 1),
        source="biometric",
        shift_hours="8",
        check_in=datetime(2026, 3, 1, 9, 0),
        check_out=datetime(2026, 3, 1, 18, 0),
    )
    service.record_attendance(
        employee_id="emp-1",
        attendance_date=date(2026, 3, 2),
        source="gps",
        shift_hours="8",
        worked_hours="7.50",
    )
    manual = service.record_attendance(
        employee_id="emp-1",
        attendance_date=date(2026, 3, 3),
        source="manual",
        shift_hours="8",
        worked_hours="10.00",
    )

    assert str(manual.overtime_hours) == "2.00"

    payroll_inputs = service.sync_attendance_to_payroll_inputs(
        employee_id="emp-1",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )
    assert payroll_inputs == {
        "employee_id": "emp-1",
        "period_start": "2026-03-01",
        "period_end": "2026-03-31",
        "records": "3",
        "total_hours": "26.50",
        "overtime_hours": "3.00",
        "late_penalties": "0.00",
        "unresolved_missing_punches": "0",
    }


def test_attendance_hardening_grace_ladder_missing_punch_and_multi_shift() -> None:
    service = AttendanceService()
    service.register_shift_template(
        template_name="day",
        shift_hours="8",
        scheduled_start_hour=9,
        scheduled_end_hour=17,
        grace_period_minutes=10,
    )
    service.register_shift_template(
        template_name="night",
        shift_hours="10",
        scheduled_start_hour=20,
        scheduled_end_hour=6,
        grace_period_minutes=5,
    )

    first = service.record_attendance(
        employee_id="emp-2",
        attendance_date=date(2026, 3, 1),
        source="biometric",
        shift_hours="8",
        shift_template="day",
        check_in=datetime(2026, 3, 1, 9, 12),
        check_out=datetime(2026, 3, 1, 18, 0),
        late_penalty_ladder=[
            {"up_to_minutes": 5, "penalty": "2.00"},
            {"up_to_minutes": 20, "penalty": "5.00"},
            {"up_to_minutes": 999, "penalty": "10.00"},
        ],
    )
    second = service.record_attendance(
        employee_id="emp-2",
        attendance_date=date(2026, 3, 2),
        source="manual",
        shift_hours="8",
        shift_template="day",
        check_in=datetime(2026, 3, 2, 9, 0),
        missing_punch_resolution="assume_shift_window",
    )
    third = service.record_attendance(
        employee_id="emp-2",
        attendance_date=date(2026, 3, 3),
        source="gps",
        shift_hours="8",
        shift_template="night",
        worked_hours="12.00",
    )

    assert first.late_minutes == 2
    assert str(first.late_penalty) == "2.00"
    assert second.missing_punch_resolved is True
    assert second.check_out is not None
    assert third.shift_template == "night"
    assert str(third.overtime_hours) == "2.00"

    payroll_inputs = service.sync_attendance_to_payroll_inputs(
        employee_id="emp-2",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )
    assert payroll_inputs["late_penalties"] == "2.00"
    assert payroll_inputs["unresolved_missing_punches"] == "0"
    assert payroll_inputs["overtime_hours"] == "2.80"
