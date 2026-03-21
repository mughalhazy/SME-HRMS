import base64
import json

from payroll_service import PayrollService


def test_payroll_service_syncs_compensation_context_without_recalculating_payroll() -> None:
    service = PayrollService()

    result = service.sync_compensation_context({
        'employee_id': 'emp-comp-001',
        'department_id': 'dep-eng',
        'role_id': 'role-frontend-engineer',
        'employee_status': 'Active',
        'effective_from': '2026-01-01',
        'base_salary': '7000.00',
        'allowances': '300.00',
        'deductions': '125.00',
        'currency': 'USD',
        'overtime_rate': '45.00',
    })

    assert result['source'] == 'employee-service.compensation'
    assert result['salary_structure']['base_salary'] == '7000.00'
    assert result['salary_structure']['allowances'] == '300.00'
    assert result['salary_structure']['deductions'] == '125.00'

    admin = 'Bearer ' + base64.urlsafe_b64encode(json.dumps({'role': 'Admin', 'employee_id': 'pay-admin'}).encode()).decode().rstrip('=')

    status, payroll = service.create_payroll_record({
        'employee_id': 'emp-comp-001',
        'pay_period_start': '2026-01-01',
        'pay_period_end': '2026-01-31',
        'currency': 'USD',
    }, admin)

    assert status == 201
    assert payroll['base_salary'] == '7000.00'
    assert payroll['allowances'] == '300.00'
    assert payroll['deductions'] == '125.00'
    assert payroll['gross_pay'] == '7300.00'
    assert payroll['net_pay'] == '7175.00'
