from datetime import date, datetime

from services.attendance_service import AttendanceService


def test_face_recognition_matches_employee_and_records_attendance_for_payroll_sync() -> None:
    service = AttendanceService()
    service.ingest_face_encodings(
        employee_database={
            "emp-1": [0.10, 0.20, 0.30],
            "emp-2": [0.90, 0.80, 0.70],
        }
    )

    match = service.record_face_attendance(
        frame=[0.11, 0.19, 0.29],
        attendance_date=date(2026, 3, 4),
        shift_hours="8",
        check_in=datetime(2026, 3, 4, 9, 0),
        check_out=datetime(2026, 3, 4, 18, 0),
    )

    assert match.employee_id == "emp-1"
    assert str(match.confidence).startswith("0.")

    payroll_inputs = service.sync_attendance_to_payroll_inputs(
        employee_id="emp-1",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 31),
    )

    assert payroll_inputs["records"] == "1"
    assert payroll_inputs["overtime_hours"] == "1.00"
    assert payroll_inputs["total_hours"] == "9.00"


def test_face_recognition_simulates_multiple_matching_scenarios() -> None:
    service = AttendanceService()
    service.ingest_face_encodings(
        employee_database={
            "emp-1": [0.10, 0.20, 0.30],
            "emp-2": [0.90, 0.80, 0.70],
        }
    )

    first = service.record_face_attendance(
        frame=[0.88, 0.79, 0.68],
        attendance_date=date(2026, 3, 5),
        shift_hours="8",
        worked_hours="8.00",
    )
    second = service.record_face_attendance(
        frame=[0.09, 0.22, 0.28],
        attendance_date=date(2026, 3, 6),
        shift_hours="8",
        worked_hours="7.50",
    )

    assert first.employee_id == "emp-2"
    assert second.employee_id == "emp-1"
    assert first.confidence > 0
    assert second.confidence > 0
