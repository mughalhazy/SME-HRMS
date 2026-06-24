from __future__ import annotations

import base64
import gzip
import json

from mobile.app import MobileAppService
from services.mobile_gateway import MobileGatewayService


def _decode_wire(response: dict) -> dict:
    wire = response['wire']
    body = gzip.decompress(base64.b64decode(wire['body'].encode('ascii')))
    return json.loads(body.decode('utf-8'))


def _aggregate() -> dict:
    return {
        'payroll': [
            {'id': 'p-1', 'period': '2026-03', 'net_pay': '125000.00', 'currency': 'PKR'},
            {'id': 'p-2', 'period': '2026-02', 'net_pay': '123000.00', 'currency': 'PKR'},
        ],
        'attendance': [
            {'id': 'l-1', 'leave_type': 'annual', 'balance_days': 10},
            {'id': 'l-2', 'leave_type': 'sick', 'balance_days': 3},
        ],
        'decisions': [
            {
                'id': 'd-1',
                'type': 'approval',
                'severity': 'critical',
                'title': 'Approve payroll exception',
                'why': 'Overtime threshold breached by 30%.',
                'primary_action': 'approve_exception',
                'due_at': '2026-04-01T08:00:00Z',
                'heavy_blob': 'x' * 5000,
            },
            {
                'id': 'd-2',
                'type': 'attendance',
                'severity': 'high',
                'title': 'Resolve missing check-in',
                'why': 'Attendance record is incomplete for shift handoff.',
                'primary_action': 'request_correction',
                'due_at': '2026-04-01T09:00:00Z',
            },
        ],
        'notifications': [
            {'id': 'n-1', 'severity': 'high', 'title': 'Leave request needs response', 'action': 'open_leave_request'},
        ],
    }


def test_mobile_endpoints_functional_and_decision_first() -> None:
    service = MobileGatewayService()
    aggregate = _aggregate()

    dashboard_status, dashboard = service.dashboard(aggregate, page=1, page_size=1, request_id='trace-dashboard')
    payslip_status, payslip = service.payslip_view(aggregate, request_id='trace-payslip')
    leave_status, leave = service.leave_apply(aggregate, request_id='trace-leave')
    alerts_status, alerts = service.alerts(aggregate, request_id='trace-alerts')

    assert dashboard_status == 200
    assert payslip_status == 200
    assert leave_status == 200
    assert alerts_status == 200

    assert dashboard['data']['decision_first'] is True
    assert dashboard['data']['decision_cards_only'] is True
    assert dashboard['data']['minimal_payload'] is True
    assert dashboard['data']['endpoint'] == '/api/mobile/dashboard'
    assert dashboard['data']['source'] == ['decisions']
    assert dashboard['meta']['pagination']['count'] == 1

    assert payslip['data']['endpoint'] == '/api/mobile/payslip'
    assert payslip['data']['items'][0]['type'] == 'decision'
    assert leave['data']['endpoint'] == '/api/mobile/leave/apply'
    assert leave['data']['items'][0]['type'] == 'decision'
    assert alerts['data']['endpoint'] == '/api/mobile/alerts'
    assert alerts['data']['items'][0]['type'] == 'decision'


def test_payloads_minimized_and_compressed() -> None:
    service = MobileGatewayService()
    aggregate = _aggregate()

    _, dashboard = service.dashboard(aggregate, request_id='trace-min')
    decoded = _decode_wire(dashboard)

    assert 'heavy_blob' not in str(decoded)
    assert dashboard['wire']['compressed_size_bytes'] < dashboard['wire']['raw_size_bytes']
    assert dashboard['wire']['raw_size_bytes'] < 5000


def test_fallback_and_cache_behavior() -> None:
    service = MobileGatewayService()
    empty = {'payroll': [], 'attendance': [], 'decisions': [], 'notifications': []}

    _, first = service.dashboard(empty, request_id='first-request')
    _, second = service.dashboard(empty, request_id='second-request')

    assert first['data']['fallback_used'] is True
    assert len(first['data']['items']) == 1
    assert first['meta']['request_id'] == 'first-request'
    # Cached response is reused for identical cache key.
    assert second['meta']['request_id'] == 'first-request'


def test_mobile_session_token_auth_and_validation() -> None:
    app = MobileAppService(session_secret='mobile-test-secret-123456')
    token = app.sessions.issue_token(user_id='manager-1', role='Manager')
    auth = f'Bearer {token}'

    status, payload = app.get_dashboard(_aggregate(), authorization=auth, trace_id='mobile-auth-pass')
    assert status == 200
    assert payload['data']['decision_first'] is True

    fail_status, fail_payload = app.get_dashboard(_aggregate(), authorization='Bearer invalid.token', trace_id='mobile-auth-fail')
    assert fail_status == 401
    assert fail_payload['error']['code'] == 'TOKEN_INVALID'
