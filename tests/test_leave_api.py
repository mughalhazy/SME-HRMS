from __future__ import annotations

import unittest
from datetime import date

from leave_api import get_leave_requests, post_leave_decision, post_leave_requests
from leave_service import LeaveService


class LeaveApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = LeaveService()

    def test_post_leave_requests_returns_created_payload(self) -> None:
        status, payload = post_leave_requests(
            self.service,
            "Employee",
            "emp-001",
            {
                "employee_id": "emp-001",
                "leave_type": "Annual",
                "start_date": date(2026, 10, 1).isoformat(),
                "end_date": date(2026, 10, 2).isoformat(),
                "reason": "Family travel",
            },
            trace_id="trace-leave-create",
        )

        self.assertEqual(status, 201)
        self.assertEqual(payload["employee_id"], "emp-001")
        self.assertEqual(payload["leave_balance"]["remaining_days"], 18.0)

    def test_post_leave_decision_rejects_and_returns_balance_state(self) -> None:
        _, created = self.service.create_request(
            "Employee",
            "emp-001",
            "emp-001",
            "Casual",
            date(2026, 10, 5),
            date(2026, 10, 5),
        )
        self.service.submit_request("Employee", "emp-001", created["leave_request_id"])

        status, payload = post_leave_decision(
            self.service,
            "reject",
            "Manager",
            "emp-manager",
            created["leave_request_id"],
            {"reason": "Quarter close freeze"},
            trace_id="trace-leave-reject",
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "Rejected")
        self.assertEqual(payload["leave_balance"]["reserved_days"], 0.0)

    def test_get_leave_requests_returns_validation_error_for_invalid_payload(self) -> None:
        status, payload = post_leave_requests(
            self.service,
            "Employee",
            "emp-001",
            {
                "employee_id": "emp-001",
                "leave_type": "Annual",
                "start_date": "invalid",
                "end_date": date(2026, 11, 2).isoformat(),
            },
            trace_id="trace-leave-invalid",
        )

        self.assertEqual(status, 422)
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(payload["error"]["traceId"], "trace-leave-invalid")

    def test_get_leave_requests_lists_filtered_requests(self) -> None:
        _, created = self.service.create_request(
            "Employee",
            "emp-001",
            "emp-001",
            "Sick",
            date(2026, 11, 10),
            date(2026, 11, 10),
        )
        self.service.submit_request("Employee", "emp-001", created["leave_request_id"])

        status, payload = get_leave_requests(
            self.service,
            "Employee",
            "emp-001",
            {"employee_id": "emp-001", "status": "Submitted"},
            trace_id="trace-leave-list",
        )

        self.assertEqual(status, 200)
        self.assertEqual(len(payload["data"]), 1)
        self.assertEqual(payload["data"][0]["status"], "Submitted")
        self.assertTrue(payload["leave_balances"])


if __name__ == "__main__":
    unittest.main()
