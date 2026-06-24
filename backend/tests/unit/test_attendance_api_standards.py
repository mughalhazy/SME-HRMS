from __future__ import annotations

import unittest
from datetime import date
from uuid import uuid4

from attendance_service import Actor, AttendanceService, AttendanceServiceError, EmployeeSnapshot, InMemoryEmployeeDirectory
from attendance_service.api import error_envelope, get_attendance_records, post_attendance_log, post_attendance_records


class AttendanceApiStandardsUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.department_id = uuid4()
        self.employee_id = uuid4()
        self.directory = InMemoryEmployeeDirectory(
            [EmployeeSnapshot(employee_id=self.employee_id, status='Active', department_id=self.department_id)]
        )
        self.service = AttendanceService(self.directory)

    def test_error_envelope_contains_scs_fields(self) -> None:
        exc = AttendanceServiceError(
            code='VALIDATION_ERROR',
            message='One or more fields are invalid.',
            details=[{'field': 'attendance_date', 'reason': 'must be an ISO date'}],
        )
        payload = error_envelope('trace-unit-1', exc)

        self.assertEqual(payload['status'], 'error')
        self.assertEqual(payload['data'], {})
        self.assertTrue({'request_id', 'timestamp', 'pagination'}.issubset(payload['meta'].keys()))
        self.assertEqual(payload['meta']['service'], 'attendance-service')
        self.assertEqual(payload['meta']['request_id'], 'trace-unit-1')
        self.assertEqual(payload['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(payload['error']['details'][0]['field'], 'attendance_date')

    def test_bad_request_payload_returns_422_with_request_id(self) -> None:
        actor = Actor(employee_id=self.employee_id, role='Employee')
        status, payload = post_attendance_records(
            self.service,
            actor,
            {
                'employee_id': str(self.employee_id),
                'attendance_date': date(2026, 1, 1).isoformat(),
                'attendance_status': 'INVALID_STATUS',
            },
            trace_id='trace-unit-422',
        )

        self.assertEqual(status, 422)
        self.assertEqual(payload['status'], 'error')
        self.assertEqual(payload['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(payload['meta']['request_id'], 'trace-unit-422')

    def test_log_endpoint_uses_domain_validation_error_shape(self) -> None:
        actor = Actor(employee_id=self.employee_id, role='Employee')
        status, payload = post_attendance_log(
            self.service,
            actor,
            {
                'employee_id': str(self.employee_id),
                'event_type': 'CheckOut',
                'occurred_at': 'invalid-datetime',
            },
            trace_id='trace-unit-log',
        )
        self.assertEqual(status, 422)
        self.assertEqual(payload['status'], 'error')
        self.assertEqual(payload['meta']['request_id'], 'trace-unit-log')

    def test_fetch_endpoint_returns_records_and_aggregation_in_success_envelope(self) -> None:
        actor = Actor(employee_id=self.employee_id, role='Employee')
        post_attendance_log(
            self.service,
            actor,
            {
                'employee_id': str(self.employee_id),
                'event_type': 'CheckIn',
                'occurred_at': '2026-01-02T09:00:00',
            },
            trace_id='trace-unit-log-ok',
        )
        status, payload = get_attendance_records(
            self.service,
            actor,
            {
                'employee_id': str(self.employee_id),
                'from_date': '2026-01-01',
                'to_date': '2026-01-31',
            },
            trace_id='trace-unit-fetch',
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload['status'], 'success')
        self.assertEqual(set(payload.keys()), {'status', 'data', 'meta', 'error'})
        self.assertTrue({'records', 'aggregation'}.issubset(payload['data'].keys()))
        self.assertEqual(payload['data']['filters']['attendance_date_from'], '2026-01-01')
        self.assertEqual(payload['data']['aggregation']['records'], 1)
        self.assertEqual(payload['meta']['pagination']['count'], 1)
        self.assertIsNone(payload['error'])


if __name__ == '__main__':
    unittest.main()
