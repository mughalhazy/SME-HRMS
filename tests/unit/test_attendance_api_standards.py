from __future__ import annotations

import unittest
from datetime import date
from uuid import uuid4

from attendance_service import Actor, AttendanceService, AttendanceServiceError, AttendanceStatus, EmployeeSnapshot, InMemoryEmployeeDirectory
from attendance_service.api import error_envelope, post_attendance_records


class AttendanceApiStandardsUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.department_id = uuid4()
        self.employee_id = uuid4()
        self.directory = InMemoryEmployeeDirectory(
            [EmployeeSnapshot(employee_id=self.employee_id, status="Active", department_id=self.department_id)]
        )
        self.service = AttendanceService(self.directory)

    def test_error_envelope_contains_canonical_fields(self) -> None:
        exc = AttendanceServiceError(
            code="VALIDATION_ERROR",
            message="One or more fields are invalid.",
            details=[{"field": "attendance_date", "reason": "must be an ISO date"}],
        )
        payload = error_envelope("trace-unit-1", exc)

        self.assertEqual(set(payload.keys()), {"error"})
        self.assertEqual(
            set(payload["error"].keys()),
            {"code", "message", "details", "traceId"},
        )
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(payload["error"]["traceId"], "trace-unit-1")

    def test_bad_request_payload_returns_422_with_trace_id(self) -> None:
        actor = Actor(employee_id=self.employee_id, role="Employee")
        status, payload = post_attendance_records(
            self.service,
            actor,
            {
                "employee_id": str(self.employee_id),
                "attendance_date": date(2026, 1, 1).isoformat(),
                "attendance_status": "INVALID_STATUS",
            },
            trace_id="trace-unit-422",
        )

        self.assertEqual(status, 422)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(payload["error"]["traceId"], "trace-unit-422")


if __name__ == "__main__":
    unittest.main()
