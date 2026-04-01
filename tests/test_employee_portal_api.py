from __future__ import annotations

import importlib.util
import pathlib
import sys

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / 'api' / 'employee_portal.py'
SPEC = importlib.util.spec_from_file_location('employee_portal_api', MODULE_PATH)
employee_portal = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = employee_portal
SPEC.loader.exec_module(employee_portal)


def test_endpoints_declared() -> None:
    assert employee_portal.ENDPOINTS == ('/payslip', '/leave/apply', '/attendance', '/profile')


def test_payslip_retrieval_is_functional_and_compact() -> None:
    status, payload = employee_portal.get_payslip({'payroll_record_id': 'pay-1', 'period': '2026-03', 'net_pay': '145000.00'})

    assert status == 200
    assert payload['data']['endpoint'] == '/payslip'
    assert payload['data']['payslip']['payroll_record_id'] == 'pay-1'
    assert payload['data']['decision']['next_action'] == 'acknowledge_payslip'
    assert 'check_in' not in payload['data']['payslip']


def test_leave_request_submission_is_functional() -> None:
    status, payload = employee_portal.post_leave_apply(
        {
            'employee_id': 'emp-1',
            'leave_type': 'annual',
            'start_date': '2026-04-10',
            'end_date': '2026-04-12',
        }
    )

    assert status == 201
    assert payload['data']['endpoint'] == '/leave/apply'
    assert payload['data']['leave_request']['status'] == 'submitted'
    assert payload['data']['decision']['next_action'] == 'track_approval_status'


def test_attendance_and_profile_are_mobile_optimized() -> None:
    attendance_status, attendance_payload = employee_portal.get_attendance({'status': 'present', 'worked_hours': '08:15'})
    profile_status, profile_payload = employee_portal.get_profile({'employee_id': 'emp-1', 'name': 'Ayesha', 'department': 'People Ops'})

    assert attendance_status == 200
    assert profile_status == 200

    attendance_data = attendance_payload['data']['attendance']
    profile_data = profile_payload['data']['profile']

    assert 'check_in' not in attendance_data
    assert 'check_out' not in attendance_data
    assert 'email' not in profile_data
    assert profile_payload['data']['decision']['confidence'] >= 90
