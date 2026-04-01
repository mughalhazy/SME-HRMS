from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / 'api' / 'manager_dashboard.py'
SPEC = importlib.util.spec_from_file_location('manager_dashboard_api', MODULE_PATH)
manager_dashboard_api = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(manager_dashboard_api)

ENDPOINTS = manager_dashboard_api.ENDPOINTS
get_alerts = manager_dashboard_api.get_alerts
get_overtime = manager_dashboard_api.get_overtime
get_approvals = manager_dashboard_api.get_approvals
get_burnout = manager_dashboard_api.get_burnout
get_performance = manager_dashboard_api.get_performance


class ManagerDashboardApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.aggregate = {
            'attendance': {
                'records': [
                    {
                        'employee_id': 'E-100',
                        'employee_name': 'Ava',
                        'late_minutes': 60,
                        'unplanned_absence': False,
                        'missing_check_in': False,
                        'missing_check_out': False,
                        'due_at': '2026-04-01T08:30:00Z',
                    },
                    {
                        'employee_id': 'E-101',
                        'employee_name': 'Nora',
                        'late_minutes': 0,
                        'unplanned_absence': True,
                        'missing_check_in': False,
                        'missing_check_out': False,
                        'due_at': '2026-04-01T09:00:00Z',
                    },
                ],
                'approvals': [
                    {
                        'id': 'A-1',
                        'status': 'pending',
                        'type': 'leave',
                        'employee_id': 'E-100',
                        'employee_name': 'Ava',
                        'age_hours': 27,
                        'due_at': '2026-04-01T10:00:00Z',
                    }
                ],
            },
            'payroll': {
                'policy': {'overtime_threshold_hours': 12},
                'entries': [
                    {
                        'employee_id': 'E-102',
                        'employee_name': 'Ben',
                        'department': 'Ops',
                        'overtime_hours': 22,
                        'approved': False,
                        'due_at': '2026-04-01T11:00:00Z',
                    }
                ],
                'approvals': [
                    {
                        'id': 'A-2',
                        'status': 'pending',
                        'type': 'timesheet',
                        'employee_id': 'E-102',
                        'employee_name': 'Ben',
                        'age_hours': 10,
                        'due_at': '2026-04-01T12:00:00Z',
                    }
                ],
            },
            'analytics': {
                'approvals': [
                    {
                        'id': 'A-3',
                        'status': 'pending',
                        'type': 'expense',
                        'employee_id': 'E-103',
                        'employee_name': 'Kai',
                        'age_hours': 4,
                        'due_at': '2026-04-01T13:00:00Z',
                    }
                ],
                'workload_signals': [
                    {
                        'employee_id': 'E-104',
                        'employee_name': 'Lia',
                        'high_load_days': 11,
                        'overtime_hours': 21,
                        'leave_days_used': 0,
                        'after_hours_sessions': 9,
                        'due_at': '2026-04-01T14:00:00Z',
                    }
                ],
                'performance_signals': [
                    {
                        'employee_id': 'E-105',
                        'employee_name': 'Moe',
                        'current_score': 58,
                        'baseline_score': 92,
                        'target_score': 90,
                        'due_at': '2026-04-01T15:00:00Z',
                    }
                ],
            },
        }

    def test_endpoints_are_exposed(self) -> None:
        self.assertEqual(ENDPOINTS, ('/alerts', '/overtime', '/approvals', '/burnout', '/performance'))

    def test_alerts_endpoint_returns_decision_first_issues(self) -> None:
        status, payload = get_alerts(self.aggregate, trace_id='trace-alerts')

        self.assertEqual(status, 200)
        self.assertEqual(payload['data']['endpoint'], '/alerts')
        self.assertEqual(payload['data']['source'], ['attendance'])
        self.assertEqual(payload['meta']['request_id'], 'trace-alerts')
        self.assertEqual(payload['data']['items'][0]['severity'], 'critical')
        self.assertNotIn('chart', str(payload).lower())

    def test_overtime_endpoint_uses_payroll_aggregate(self) -> None:
        status, payload = get_overtime(self.aggregate, trace_id='trace-overtime')

        self.assertEqual(status, 200)
        self.assertEqual(payload['data']['endpoint'], '/overtime')
        self.assertEqual(payload['data']['items'][0]['policy_threshold_hours'], 12)
        self.assertEqual(payload['data']['items'][0]['overtime_hours'], 22)

    def test_approvals_endpoint_aggregates_attendance_payroll_analytics(self) -> None:
        status, payload = get_approvals(self.aggregate, trace_id='trace-approvals')

        self.assertEqual(status, 200)
        self.assertEqual(payload['data']['endpoint'], '/approvals')
        self.assertEqual(payload['data']['source'], ['attendance', 'payroll', 'analytics'])
        self.assertEqual(len(payload['data']['items']), 3)
        self.assertEqual(payload['data']['items'][0]['approval_id'], 'A-1')

    def test_burnout_and_performance_endpoints_return_actionable_items(self) -> None:
        burnout_status, burnout_payload = get_burnout(self.aggregate, trace_id='trace-burnout')
        performance_status, performance_payload = get_performance(self.aggregate, trace_id='trace-performance')

        self.assertEqual(burnout_status, 200)
        self.assertEqual(performance_status, 200)
        self.assertEqual(burnout_payload['data']['endpoint'], '/burnout')
        self.assertEqual(performance_payload['data']['endpoint'], '/performance')
        self.assertEqual(burnout_payload['data']['items'][0]['severity'], 'critical')
        self.assertEqual(performance_payload['data']['items'][0]['severity'], 'critical')
        self.assertNotIn('chart', str(burnout_payload).lower())
        self.assertNotIn('chart', str(performance_payload).lower())


if __name__ == '__main__':
    unittest.main()
