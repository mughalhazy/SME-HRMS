from datetime import date, datetime
from uuid import uuid4

import unittest

from attendance_service import (
    Actor,
    AttendanceService,
    AttendanceServiceError,
    AttendanceStatus,
    EmployeeSnapshot,
    InMemoryEmployeeDirectory,
    RecordState,
)
from attendance_service.api import post_attendance_records


class AttendanceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dep_a = uuid4()
        self.dep_b = uuid4()
        self.emp_1 = uuid4()
        self.emp_2 = uuid4()
        self.directory = InMemoryEmployeeDirectory(
            [
                EmployeeSnapshot(employee_id=self.emp_1, status="Active", department_id=self.dep_a),
                EmployeeSnapshot(employee_id=self.emp_2, status="Active", department_id=self.dep_b),
            ]
        )
        self.service = AttendanceService(self.directory)

    def test_employee_can_create_own_record(self) -> None:
        actor = Actor(employee_id=self.emp_1, role="Employee")
        record = self.service.create_record(
            actor,
            employee_id=self.emp_1,
            attendance_date=date(2026, 1, 2),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 1, 2, 9, 0),
            check_out_time=datetime(2026, 1, 2, 18, 0),
        )
        self.assertEqual(record.total_hours, 9)
        self.assertEqual(record.lifecycle_state, RecordState.VALIDATED)

    def test_employee_cannot_create_other_employee_record(self) -> None:
        actor = Actor(employee_id=self.emp_1, role="Employee")
        with self.assertRaises(AttendanceServiceError):
            self.service.create_record(
                actor,
                employee_id=self.emp_2,
                attendance_date=date(2026, 1, 2),
                attendance_status=AttendanceStatus.PRESENT,
            )

    def test_manager_can_approve_same_department(self) -> None:
        manager = Actor(employee_id=uuid4(), role="Manager", department_id=self.dep_a)
        record = self.service.create_record(
            manager,
            employee_id=self.emp_1,
            attendance_date=date(2026, 2, 10),
            attendance_status=AttendanceStatus.ABSENT,
        )
        updated = self.service.approve_record(manager, record.attendance_id)
        self.assertEqual(updated.lifecycle_state, RecordState.APPROVED)

    def test_period_lock_requires_approval(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 2, 10),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 2, 10, 10, 0),
            check_out_time=datetime(2026, 2, 10, 14, 0),
        )
        with self.assertRaises(AttendanceServiceError):
            self.service.lock_period(admin, period_id="2026-02", from_date=date(2026, 2, 1), to_date=date(2026, 2, 28))

    def test_summary_aggregates_hours_and_status(self) -> None:
        admin = Actor(employee_id=uuid4(), role="Admin")
        r1 = self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 3, 1),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 3, 1, 9, 0),
            check_out_time=datetime(2026, 3, 1, 17, 0),
        )
        r2 = self.service.create_record(
            admin,
            employee_id=self.emp_1,
            attendance_date=date(2026, 3, 2),
            attendance_status=AttendanceStatus.ABSENT,
        )
        self.service.approve_record(admin, r1.attendance_id)
        self.service.approve_record(admin, r2.attendance_id)

        summary = self.service.get_summary(
            admin, employee_id=self.emp_1, period_start=date(2026, 3, 1), period_end=date(2026, 3, 31)
        )
        self.assertEqual(summary["totalHours"], "8.00")
        self.assertEqual(summary["statusBreakdown"]["Present"], 1)
        self.assertEqual(summary["statusBreakdown"]["Absent"], 1)

    def test_api_uses_error_envelope(self) -> None:
        actor = Actor(employee_id=self.emp_1, role="Employee")
        status, payload = post_attendance_records(
            self.service,
            actor,
            {
                "employee_id": str(self.emp_2),
                "attendance_date": "2026-01-01",
                "attendance_status": "Present",
            },
            trace_id="trace-1",
        )
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"]["traceId"], "trace-1")


if __name__ == "__main__":
    unittest.main()
