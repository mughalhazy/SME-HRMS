from datetime import date

import unittest

from attendance_service import build_attendance_ui


class AttendanceUiBuilderTests(unittest.TestCase):
    def test_build_attendance_ui_aggregates_summary_and_normalizes_records(self) -> None:
        payload = build_attendance_ui(
            [
                {
                    "employee_id": "emp-1",
                    "employee_number": "E-001",
                    "employee_name": "Jane Doe",
                    "department_id": "dep-1",
                    "department_name": "Engineering",
                    "attendance_date": date(2026, 4, 1),
                    "attendance_status": "Present",
                    "check_in_time": "2026-04-01T09:00:00",
                    "check_out_time": "2026-04-01T17:00:00",
                    "total_hours": "8.00",
                    "source": "Manual",
                    "record_state": "Approved",
                    "updated_at": "2026-04-01T17:10:00",
                },
                {
                    "employee_id": "emp-2",
                    "employee_number": "E-002",
                    "employee_name": "John Smith",
                    "department_id": "dep-1",
                    "department_name": "Engineering",
                    "attendance_date": "2026-04-02",
                    "attendance_status": "Late",
                    "check_in_time": "2026-04-02T09:30:00",
                    "check_out_time": "2026-04-02T18:00:00",
                    "total_hours": "8.50",
                    "source": "Biometric",
                    "record_state": "Validated",
                    "updated_at": "2026-04-02T18:10:00",
                },
            ]
        )

        self.assertEqual(payload["surface"], "attendance_dashboard")
        self.assertEqual(payload["summary"]["totalRecords"], 2)
        self.assertEqual(payload["summary"]["uniqueEmployees"], 2)
        self.assertEqual(payload["summary"]["dateRange"]["from"], "2026-04-01")
        self.assertEqual(payload["summary"]["dateRange"]["to"], "2026-04-02")
        self.assertEqual(payload["summary"]["statusBreakdown"]["Present"], 1)
        self.assertEqual(payload["summary"]["statusBreakdown"]["Late"], 1)
        self.assertEqual(payload["summary"]["averageHours"], "8.25")
        self.assertEqual(payload["records"][0]["attendanceDate"], "2026-04-02")

    def test_build_attendance_ui_validates_read_model_fields(self) -> None:
        with self.assertRaises(ValueError):
            build_attendance_ui([{"employee_id": "emp-1"}])

    def test_build_attendance_ui_handles_empty_rows(self) -> None:
        payload = build_attendance_ui([])
        self.assertEqual(payload["summary"]["totalRecords"], 0)
        self.assertEqual(payload["records"], [])


if __name__ == "__main__":
    unittest.main()
