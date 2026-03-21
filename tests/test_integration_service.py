from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

from integration_api import delete_webhook, get_delivery_attempts, get_webhooks, patch_webhook, post_delivery_replay, post_webhook
from integration_service import IntegrationService


def test_signed_delivery_filters_events_and_preserves_tenant_scope(tmp_path: Path) -> None:
    requests: list[dict] = []

    def http_client(request: dict) -> dict:
        requests.append(request)
        return {'status_code': 202, 'body': '{"ok":true}'}

    service = IntegrationService(db_path=str(tmp_path / 'integration.sqlite3'), http_client=http_client, master_key='m' * 32)
    webhook = service.create_webhook(
        {
            'tenant_id': 'tenant-acme',
            'target_url': 'https://hooks.example.com/hrms',
            'subscribed_events': ['LeaveRequestApproved'],
            'secret': 'super-secret',
            'description': 'Payroll export',
            'max_attempts': 3,
        },
        actor={'id': 'admin-1', 'type': 'user'},
        trace_id='trace-create',
    )
    service.create_webhook(
        {
            'tenant_id': 'tenant-acme',
            'target_url': 'https://hooks.example.com/other',
            'subscribed_events': ['PayrollProcessed'],
            'secret': 'different-secret',
        },
        actor={'id': 'admin-1', 'type': 'user'},
        trace_id='trace-create-2',
    )

    result = service.consume_event(
        {
            'event_name': 'LeaveRequestApproved',
            'tenant_id': 'tenant-acme',
            'source': 'leave-service',
            'data': {
                'leave_request_id': 'leave-1',
                'employee_id': 'emp-1',
                'approver_employee_id': 'mgr-1',
                'total_days': 2.0,
                'leave_type': 'Annual',
                'status': 'Approved',
                'decision_at': '2026-03-21T00:00:00+00:00',
            },
            'metadata': {'version': 'v1', 'correlation_id': 'corr-1', 'idempotency_key': 'leave-1'},
        },
        trace_id='trace-event',
    )
    assert result['matched_webhooks'] == 1

    jobs = service.run_delivery_jobs(tenant_id='tenant-acme')
    assert len(jobs) == 1
    assert len(requests) == 1
    request = requests[0]
    assert request['url'] == 'https://hooks.example.com/hrms'
    body = request['body']
    timestamp = request['headers']['X-HRMS-Timestamp']
    expected = 'sha256=' + hmac.new('super-secret'.encode('utf-8'), f'{timestamp}.{body}'.encode('utf-8'), hashlib.sha256).hexdigest()
    assert request['headers']['X-HRMS-Signature-256'] == expected
    assert request['headers']['X-HRMS-Tenant-Id'] == 'tenant-acme'

    deliveries, _ = service.list_delivery_attempts(tenant_id='tenant-acme')
    assert len(deliveries) == 1
    assert deliveries[0]['delivery']['status'] == 'Succeeded'
    assert deliveries[0]['webhook_id'] == webhook.webhook_id

    duplicate = service.consume_event(
        {
            'event_id': json.loads(body)['event_id'],
            'event_type': 'leave.request.approved',
            'tenant_id': 'tenant-acme',
            'source': 'leave-service',
            'timestamp': json.loads(body)['timestamp'],
            'data': json.loads(body)['data'],
            'metadata': json.loads(body)['metadata'],
        },
        trace_id='trace-dup',
    )
    assert duplicate['duplicate'] is True


def test_retry_and_dead_letter_tracking_support_replay(tmp_path: Path) -> None:
    attempts = {'count': 0}

    def flaky_http_client(_: dict) -> dict:
        attempts['count'] += 1
        if attempts['count'] <= 3:
            return {'status_code': 500, 'body': '{"error":"down"}'}
        return {'status_code': 200, 'body': '{"ok":true}'}

    service = IntegrationService(db_path=str(tmp_path / 'integration.sqlite3'), http_client=flaky_http_client, master_key='m' * 32)
    webhook = service.create_webhook(
        {
            'tenant_id': 'tenant-acme',
            'target_url': 'https://hooks.example.com/retry',
            'subscribed_events': ['PayrollProcessed'],
            'secret': 'retry-secret',
            'max_attempts': 3,
        },
        trace_id='trace-create',
    )
    scheduled = service.consume_event(
        {
            'event_name': 'PayrollProcessed',
            'tenant_id': 'tenant-acme',
            'source': 'payroll-service',
            'data': {
                'payroll_record_id': 'pay-1',
                'employee_id': 'emp-1',
                'pay_period_start': '2026-03-01',
                'pay_period_end': '2026-03-31',
                'gross_pay': '1000.00',
                'net_pay': '900.00',
                'currency': 'USD',
                'status': 'Processed',
            },
            'metadata': {'version': 'v1', 'correlation_id': 'corr-2', 'idempotency_key': 'pay-1'},
        },
        trace_id='trace-payroll',
    )
    delivery_id = scheduled['scheduled_deliveries'][0]['delivery_id']

    service.run_delivery_jobs(tenant_id='tenant-acme')

    delivery = service.deliveries[delivery_id]
    assert delivery.status == 'DeadLettered'
    assert delivery.attempt_count == 3
    assert service.dead_letters.entries
    listed, _ = service.list_delivery_attempts(tenant_id='tenant-acme', webhook_id=webhook.webhook_id)
    assert len(listed) == 3
    assert all(item['status'] == 'Failed' for item in listed)

    replay = service.replay_failed_delivery(delivery_id, tenant_id='tenant-acme', trace_id='trace-replay')
    service.run_delivery_jobs(tenant_id='tenant-acme')
    replayed = service.deliveries[replay.delivery_id]
    assert replayed.status == 'Succeeded'
    assert replayed.replay_of_delivery_id == delivery_id


def test_management_apis_are_d1_compliant_and_tenant_safe(tmp_path: Path) -> None:
    service = IntegrationService(db_path=str(tmp_path / 'integration.sqlite3'), master_key='m' * 32)

    status, created = post_webhook(
        service,
        {
            'tenant_id': 'tenant-acme',
            'target_url': 'https://hooks.example.com/manage',
            'subscribed_events': ['AttendanceCaptured'],
            'secret': 'manage-secret',
            'actor': {'id': 'admin-1', 'type': 'user'},
        },
        trace_id='trace-api-create',
    )
    assert status == 201
    assert created['status'] == 'success'
    webhook_id = created['data']['webhook_id']
    assert created['data']['secret']['configured'] is True
    assert 'secret_ciphertext' not in created['data']

    patch_status, patched = patch_webhook(
        service,
        webhook_id,
        {
            'tenant_id': 'tenant-acme',
            'status': 'Disabled',
            'subscribed_events': ['AttendanceApproved'],
            'actor': {'id': 'admin-1', 'type': 'user'},
        },
        trace_id='trace-api-patch',
    )
    assert patch_status == 200
    assert patched['data']['status'] == 'Disabled'
    assert patched['data']['subscribed_events'] == ['attendance.record.approved']

    list_status, listed = get_webhooks(service, {'tenant_id': 'tenant-acme'}, trace_id='trace-api-list')
    assert list_status == 200
    assert listed['meta']['pagination']['count'] == 1

    forbidden_status, forbidden = delete_webhook(
        service,
        webhook_id,
        {'tenant_id': 'tenant-other', 'actor': {'id': 'admin-2', 'type': 'user'}},
        trace_id='trace-api-delete-forbidden',
    )
    assert forbidden_status == 403
    assert forbidden['error']['code'] == 'TENANT_SCOPE_VIOLATION'

    delete_status, deleted = delete_webhook(
        service,
        webhook_id,
        {'tenant_id': 'tenant-acme', 'actor': {'id': 'admin-1', 'type': 'user'}},
        trace_id='trace-api-delete',
    )
    assert delete_status == 200
    assert deleted['data']['status'] == 'Deleted'


def test_delivery_api_lists_attempts_and_replays_failed_deliveries(tmp_path: Path) -> None:
    responses = iter([
        {'status_code': 500, 'body': '{"error":"nope"}'},
        {'status_code': 200, 'body': '{"ok":true}'},
    ])

    def client(_: dict) -> dict:
        return next(responses)

    service = IntegrationService(db_path=str(tmp_path / 'integration.sqlite3'), http_client=client, master_key='m' * 32)
    service.create_webhook(
        {
            'tenant_id': 'tenant-acme',
            'target_url': 'https://hooks.example.com/replay-api',
            'subscribed_events': ['AttendanceCaptured'],
            'secret': 'secret-value',
            'max_attempts': 1,
        },
        trace_id='trace-create',
    )
    scheduled = service.consume_event(
        {
            'event_name': 'AttendanceCaptured',
            'tenant_id': 'tenant-acme',
            'source': 'attendance-service',
            'data': {
                'employee_id': 'emp-77',
                'employee_number': 'E-77',
                'department_id': 'dep-eng',
                'role_id': 'role-eng',
                'status': 'Draft',
                'hire_date': '2026-03-21',
            },
            'metadata': {'version': 'v1', 'correlation_id': 'corr-3', 'idempotency_key': 'att-77'},
        },
        trace_id='trace-employee',
    )
    delivery_id = scheduled['scheduled_deliveries'][0]['delivery_id']
    service.run_delivery_jobs(tenant_id='tenant-acme')

    list_status, attempts_payload = get_delivery_attempts(
        service,
        {'tenant_id': 'tenant-acme', 'delivery_status': 'DeadLettered'},
        trace_id='trace-attempts',
    )
    assert list_status == 200
    assert attempts_payload['data']['items'][0]['delivery']['delivery_id'] == delivery_id

    replay_status, replay_payload = post_delivery_replay(
        service,
        delivery_id,
        {'tenant_id': 'tenant-acme', 'actor': {'id': 'admin-1', 'type': 'user'}},
        trace_id='trace-replay-api',
    )
    assert replay_status == 202
    service.run_delivery_jobs(tenant_id='tenant-acme')
    assert service.deliveries[replay_payload['data']['delivery_id']].status == 'Succeeded'
