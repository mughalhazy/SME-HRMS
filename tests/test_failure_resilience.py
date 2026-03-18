from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest
from datetime import date

from leave_service import LeaveService
from payroll_service import PayrollService
from resilience import CircuitBreaker, CircuitBreakerOpenError, IdempotencyStore, run_with_retry
from services.hiring_service import HiringService


GATEWAY_PATH = pathlib.Path(__file__).resolve().parents[1] / 'docker' / 'api_gateway_service.py'
SPEC = importlib.util.spec_from_file_location('api_gateway_service_runtime', GATEWAY_PATH)
api_gateway_service = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = api_gateway_service
SPEC.loader.exec_module(api_gateway_service)


def token(role: str, employee_id: str | None = None) -> str:
    import base64
    import json

    payload = {'role': role}
    if employee_id:
        payload['employee_id'] = employee_id
    return 'Bearer ' + base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')


class FailureResilienceTests(unittest.TestCase):
    def test_retry_uses_exponential_backoff_and_recovers(self) -> None:
        attempts: list[int] = []

        def flaky() -> str:
            attempts.append(len(attempts) + 1)
            if len(attempts) < 3:
                raise TimeoutError('temporary timeout')
            return 'ok'

        result = run_with_retry(
            flaky,
            attempts=3,
            base_delay=0.001,
            timeout_seconds=0.05,
            retryable=lambda exc: isinstance(exc, TimeoutError),
        )

        self.assertEqual(result, 'ok')
        self.assertEqual(attempts, [1, 2, 3])

    def test_circuit_breaker_opens_after_threshold(self) -> None:
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

        with self.assertRaises(RuntimeError):
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError('boom-1')))
        with self.assertRaises(RuntimeError):
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError('boom-2')))
        with self.assertRaises(CircuitBreakerOpenError):
            breaker.call(lambda: 'never')

    def test_gateway_ready_check_degrades_without_raising(self) -> None:
        result = api_gateway_service._check_service_health('employee-service', 'http://127.0.0.1:1', 'trace-ready')
        self.assertEqual(result['status'], 'degraded')
        self.assertIn('reason', result)

    def test_leave_approval_is_idempotent_and_dead_letters_are_recoverable(self) -> None:
        service = LeaveService()
        _, created = service.create_request(
            'Employee',
            'emp-001',
            'emp-001',
            'Annual',
            date(2026, 7, 1),
            date(2026, 7, 3),
        )
        service.submit_request('Employee', 'emp-001', created['leave_request_id'], idempotency_key='leave-submit-1')
        first_code, first_payload = service.decide_request(
            'approve',
            'Manager',
            'emp-manager',
            created['leave_request_id'],
            idempotency_key='leave-approve-1',
            simulate_event_failure=True,
        )
        second_code, second_payload = service.decide_request(
            'approve',
            'Manager',
            'emp-manager',
            created['leave_request_id'],
            idempotency_key='leave-approve-1',
        )

        self.assertEqual(first_code, 200)
        self.assertEqual(second_code, 200)
        self.assertEqual(first_payload['leave_request_id'], second_payload['leave_request_id'])
        self.assertEqual(len(service.dead_letters.entries), 1)

        recovered = service.replay_dead_letters()
        self.assertEqual(len(recovered), 1)
        self.assertTrue(service.dead_letters.entries[0].recovered_at)

    def test_payroll_run_is_idempotent_and_isolates_failed_records(self) -> None:
        service = PayrollService()
        admin = token('Admin')
        code, payload = service.run_payroll(
            '2026-08-01',
            '2026-08-31',
            admin,
            records=[
                {
                    'employee_id': 'emp-1',
                    'pay_period_start': '2026-08-01',
                    'pay_period_end': '2026-08-31',
                    'base_salary': '1000.00',
                    'currency': 'USD',
                },
                {
                    'employee_id': 'emp-bad',
                    'pay_period_start': '2026-01-01',
                    'pay_period_end': '2026-01-31',
                    'base_salary': '1000.00',
                    'currency': 'USD',
                },
            ],
            idempotency_key='payroll-run-aug',
        )
        code2, payload2 = service.run_payroll(
            '2026-08-01',
            '2026-08-31',
            admin,
            records=[
                {
                    'employee_id': 'emp-1',
                    'pay_period_start': '2026-08-01',
                    'pay_period_end': '2026-08-31',
                    'base_salary': '1000.00',
                    'currency': 'USD',
                },
                {
                    'employee_id': 'emp-bad',
                    'pay_period_start': '2026-01-01',
                    'pay_period_end': '2026-01-31',
                    'base_salary': '1000.00',
                    'currency': 'USD',
                },
            ],
            idempotency_key='payroll-run-aug',
        )

        self.assertEqual(code, 200)
        self.assertEqual(code2, 200)
        self.assertEqual(payload, payload2)
        self.assertEqual(payload['data']['processed_count'], 1)
        self.assertEqual(payload['data']['failed_count'], 1)
        self.assertEqual(len(service.dead_letters.entries), 1)

    def test_hiring_calendar_sync_falls_back_to_manual_scheduling(self) -> None:
        service = HiringService()
        posting = service.create_job_posting(
            {
                'title': 'SRE',
                'department_id': 'dep-ops',
                'role_id': 'role-sre',
                'employment_type': 'FullTime',
                'description': 'Own reliability',
                'openings_count': 1,
                'posting_date': '2026-01-01',
                'status': 'Open',
            }
        )
        candidate = service.create_candidate(
            {
                'job_posting_id': posting['job_posting_id'],
                'first_name': 'Nina',
                'last_name': 'Shaw',
                'email': 'nina@example.com',
                'application_date': '2026-01-03',
            }
        )
        service.update_candidate(candidate['candidate_id'], {'status': 'Screening'})
        service.update_candidate(candidate['candidate_id'], {'status': 'Interviewing'})

        interview = service.schedule_interview_with_google_calendar(
            {
                'candidate_id': candidate['candidate_id'],
                'interview_type': 'Technical',
                'scheduled_start': '2026-01-09T10:00:00Z',
                'scheduled_end': '2026-01-09T11:00:00Z',
                'simulate_google_failure': True,
            }
        )

        self.assertIsNone(interview['google_calendar_event_id'])
        self.assertEqual(interview['location_or_link'], 'manual-scheduling-required')
        self.assertEqual(len(service.dead_letters.entries), 1)

    def test_idempotency_store_replays_same_request(self) -> None:
        store = IdempotencyStore()
        store.record('key-1', 'fingerprint-a', 200, {'ok': True})
        replay = store.replay_or_conflict('key-1', 'fingerprint-a')
        self.assertIsNotNone(replay)
        assert replay is not None
        self.assertEqual(replay.payload['ok'], True)


if __name__ == '__main__':
    unittest.main()
