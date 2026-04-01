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
    }
