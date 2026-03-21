from __future__ import annotations

import base64
import json

from payroll_api import get_payroll_record, get_payroll_records, post_payroll_mark_paid, post_payroll_records, post_payroll_run
from payroll_service import PayrollService


def token(role: str, employee_id: str | None = None) -> str:
    payload = {'role': role}
    if employee_id:
        payload['employee_id'] = employee_id
    return 'Bearer ' + base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')


def test_payroll_api_create_list_run_and_mark_paid_follow_d1_contract():
    service = PayrollService()
    admin = token('Admin')

    create_status, created = post_payroll_records(
        service,
        {
            'employee_id': 'emp-201',
            'pay_period_start': '2026-01-01',
            'pay_period_end': '2026-01-31',
            'base_salary': '1000.00',
            'allowances': '100.00',
            'deductions': '50.00',
            'overtime_pay': '20.00',
            'currency': 'USD',
        },
        admin,
        trace_id='trace-payroll-api-create',
    )
    assert create_status == 201
    assert created['status'] == 'success'
    assert created['meta']['request_id'] == 'trace-payroll-api-create'
    assert created['meta']['service'] == 'payroll-service'
    assert created['meta']['tenant_id'] == 'tenant-default'
    assert created['meta']['actor']['role'] == 'Admin'

    list_status, listed = get_payroll_records(
        service,
        admin,
        {'employee_id': 'emp-201', 'limit': '10', 'status': 'Draft'},
        trace_id='trace-payroll-api-list',
    )
    assert list_status == 200
    assert listed['status'] == 'success'
    assert listed['data']['items'][0]['payroll_record_id'] == created['data']['payroll_record_id']
    assert listed['data']['data'][0]['employee_id'] == 'emp-201'
    assert listed['meta']['pagination']['count'] == 1
    assert listed['meta']['pagination']['limit'] == 10
    assert listed['meta']['pagination']['has_next'] is False

    get_status, fetched = get_payroll_record(
        service,
        created['data']['payroll_record_id'],
        admin,
        trace_id='trace-payroll-api-get',
    )
    assert get_status == 200
    assert fetched['data']['payroll_record_id'] == created['data']['payroll_record_id']

    run_status, run_payload = post_payroll_run(
        service,
        {'period_start': '2026-01-01', 'period_end': '2026-01-31'},
        admin,
        trace_id='trace-payroll-api-run',
    )
    assert run_status == 200
    assert run_payload['data']['processed_count'] >= 1

    mark_paid_status, paid = post_payroll_mark_paid(
        service,
        created['data']['payroll_record_id'],
        {'payment_date': '2026-02-01'},
        admin,
        trace_id='trace-payroll-api-paid',
    )
    assert mark_paid_status == 200
    assert paid['data']['status'] == 'Paid'


def test_payroll_api_errors_follow_d1_contract():
    service = PayrollService()
    admin = token('Admin')

    status, payload = get_payroll_records(
        service,
        admin,
        {'limit': 'not-a-number'},
        trace_id='trace-payroll-api-invalid',
    )
    assert status == 422
    assert payload['status'] == 'error'
    assert payload['data'] == {}
    assert payload['error']['code'] == 'VALIDATION_ERROR'
    assert payload['meta']['request_id'] == 'trace-payroll-api-invalid'
    assert payload['meta']['service'] == 'payroll-service'
