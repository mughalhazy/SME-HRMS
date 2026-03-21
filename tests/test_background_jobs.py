from __future__ import annotations

import base64
import json
from datetime import date, datetime, timedelta, timezone

import pytest

from background_jobs import BackgroundJobService, JobStatus
from background_jobs_api import (
    get_background_job,
    get_background_jobs,
    post_background_job,
    post_background_job_cancel,
    post_background_job_retry,
)
from leave_service import LeaveService
from notification_service import NotificationService
from payroll_service import PayrollService


def _bearer(role: str, employee_id: str | None = None) -> str:
    payload = {'role': role}
    if employee_id is not None:
        payload['employee_id'] = employee_id
    return 'Bearer ' + base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')


def test_payroll_run_job_wraps_payroll_service_and_stages_outbox_events() -> None:
    payroll = PayrollService()
    notification = NotificationService()
    jobs = BackgroundJobService(payroll_service=payroll, notification_service=notification)
    payroll.register_employee_profile('emp-1', department_id='dep-fin')

    job = jobs.enqueue_job(
        tenant_id='tenant-default',
        job_type='payroll.run',
        payload={
            'period_start': '2026-03-01',
            'period_end': '2026-03-31',
            'authorization': _bearer('Admin'),
            'records': [
                {
                    'employee_id': 'emp-1',
                    'pay_period_start': '2026-03-01',
                    'pay_period_end': '2026-03-31',
                    'base_salary': '1000.00',
                    'currency': 'USD',
                }
            ],
        },
        idempotency_key='payroll-run-march-2026',
    )

    completed = jobs.execute_job(job.job_id, tenant_id='tenant-default')

    assert completed.status == JobStatus.SUCCEEDED
    assert completed.last_result is not None
    assert completed.last_result['response']['data']['processed_count'] == 1
    assert any(event.event_name == 'PayrollProcessed' for event in jobs.outbox.list_events(tenant_id='tenant-default'))
    assert len(payroll.batches) == 1


def test_jobs_retry_then_dead_letter_when_handler_keeps_failing() -> None:
    jobs = BackgroundJobService()
    attempts: list[int] = []

    def failing_handler(context):
        attempts.append(len(attempts) + 1)
        raise RuntimeError('transient boom')

    jobs.register_handler('test.fail', failing_handler, max_attempts=2)
    job = jobs.enqueue_job(tenant_id='tenant-default', job_type='test.fail', payload={'value': 1})

    terminal = jobs.execute_job(job.job_id, tenant_id='tenant-default')

    assert terminal.status == JobStatus.DEAD_LETTERED
    assert terminal.attempts == 2
    assert len(attempts) == 2
    assert len(jobs.dead_letters.entries) == 1
    assert len(jobs.job_failures) == 1


def test_job_enqueue_is_idempotent_for_same_payload() -> None:
    jobs = BackgroundJobService()
    jobs.register_handler('test.noop', lambda context: {'ok': True}, max_attempts=1)

    first = jobs.enqueue_job(
        tenant_id='tenant-default',
        job_type='test.noop',
        payload={'hello': 'world'},
        idempotency_key='same-job',
    )
    second = jobs.enqueue_job(
        tenant_id='tenant-default',
        job_type='test.noop',
        payload={'hello': 'world'},
        idempotency_key='same-job',
    )

    assert first.job_id == second.job_id
    completed = jobs.execute_job(first.job_id, tenant_id='tenant-default')
    replayed = jobs.execute_job(first.job_id, tenant_id='tenant-default')
    assert completed.status == JobStatus.SUCCEEDED
    assert replayed.status == JobStatus.SUCCEEDED


def test_scheduled_jobs_only_run_when_due() -> None:
    jobs = BackgroundJobService()
    jobs.register_handler('test.marker', lambda context: {'marker': context.job.payload['marker']}, max_attempts=1)
    now = datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc)
    due = jobs.enqueue_job(
        tenant_id='tenant-default',
        job_type='test.marker',
        payload={'marker': 'due'},
        scheduled_at=now.isoformat(),
    )
    future = jobs.enqueue_job(
        tenant_id='tenant-default',
        job_type='test.marker',
        payload={'marker': 'future'},
        scheduled_at=(now + timedelta(hours=1)).isoformat(),
    )

    executed = jobs.run_due_jobs(now=now.isoformat())

    assert [job.job_id for job in executed] == [due.job_id]
    assert jobs.get_job(due.job_id, tenant_id='tenant-default').status == JobStatus.SUCCEEDED
    assert jobs.get_job(future.job_id, tenant_id='tenant-default').status == JobStatus.SCHEDULED


def test_leave_recompute_job_preserves_tenant_scope() -> None:
    leave = LeaveService()
    jobs = BackgroundJobService(leave_service=leave)
    _, created = leave.create_request(
        'Employee',
        'emp-001',
        'emp-001',
        'Annual',
        date(2026, 4, 10),
        date(2026, 4, 12),
        tenant_id='tenant-default',
    )
    leave.submit_request('Employee', 'emp-001', created['leave_request_id'], tenant_id='tenant-default')

    job = jobs.enqueue_job(
        tenant_id='tenant-default',
        job_type='leave.balance.recompute',
        payload={'employee_id': 'emp-001'},
    )
    completed = jobs.execute_job(job.job_id, tenant_id='tenant-default')

    assert completed.status == JobStatus.SUCCEEDED
    with pytest.raises(Exception):
        jobs.get_job(job.job_id, tenant_id='tenant-other')


def test_outbox_dispatch_job_marks_notification_events_published() -> None:
    notification = NotificationService()
    jobs = BackgroundJobService(notification_service=notification)
    jobs.outbox.stage_event(
        tenant_id='tenant-default',
        aggregate_type='LeaveRequest',
        aggregate_id='lr-1',
        event_name='LeaveRequestApproved',
        payload={
            'event_name': 'LeaveRequestApproved',
            'tenant_id': 'tenant-default',
            'employee_id': 'emp-001',
            'employee_email': 'amina.yusuf@example.com',
            'approver_name': 'Helen Brooks',
            'leave_type': 'Annual',
            'start_date': '2026-03-21',
            'end_date': '2026-03-22',
        },
        trace_id='trace-outbox-1',
    )
    job = jobs.enqueue_job(tenant_id='tenant-default', job_type='outbox.dispatch', payload={'max_events': 10})

    completed = jobs.execute_job(job.job_id, tenant_id='tenant-default')

    assert completed.status == JobStatus.SUCCEEDED
    assert completed.last_result['dispatched_count'] == 1
    pending = jobs.outbox.pending_events(tenant_id='tenant-default')
    assert pending == []
    inbox, _ = notification.get_inbox(tenant_id='tenant-default', subject_id='emp-001')
    assert inbox['summary']['total'] >= 1


def test_workflow_escalation_job_stages_escalation_event() -> None:
    jobs = BackgroundJobService()
    job = jobs.enqueue_job(
        tenant_id='tenant-default',
        job_type='workflow.escalation',
        payload={
            'now': '2026-03-21T13:00:00+00:00',
            'workflow': {
                'workflow_id': '5d892b38-2381-4f17-84eb-4d17f5b4d444',
                'created_at': '2026-03-21T10:00:00+00:00',
                'steps': [
                    {
                        'step_id': '0eae0fe5-5f05-4b87-8fa5-28b78a6ce129',
                        'type': 'approval',
                        'assignee': 'hr-ops',
                        'status': 'pending',
                        'sla': 'PT1H',
                    }
                ],
                'status': 'pending',
            },
        },
    )

    completed = jobs.execute_job(job.job_id, tenant_id='tenant-default')

    assert completed.status == JobStatus.SUCCEEDED
    assert completed.last_result['escalation_count'] == 1
    assert any(event.event_name == 'WorkflowEscalationReady' for event in jobs.outbox.list_events(tenant_id='tenant-default'))


def test_background_job_api_returns_d1_envelopes_for_status_and_admin_controls() -> None:
    jobs = BackgroundJobService()
    jobs.register_handler('test.noop', lambda context: {'ok': True}, max_attempts=1)

    status, created = post_background_job(
        jobs,
        {
            'request_id': 'req-1',
            'tenant_id': 'tenant-default',
            'actor': {'id': 'svc-1', 'type': 'service'},
            'job_type': 'test.noop',
            'payload': {'hello': 'world'},
            'idempotency_key': 'job-api-noop',
        },
    )
    assert status == 202
    assert created['status'] == 'success'
    job_id = created['data']['job_id']

    jobs.execute_job(job_id, tenant_id='tenant-default')

    get_status, fetched = get_background_job(jobs, job_id, {'tenant_id': 'tenant-default', 'actor_role': 'Admin'})
    assert get_status == 200
    assert fetched['status'] == 'success'
    assert fetched['data']['status'] == 'Succeeded'
    assert fetched['meta']['pagination'] == {}

    list_status, listed = get_background_jobs(jobs, {'tenant_id': 'tenant-default', 'actor_role': 'Admin'})
    assert list_status == 200
    assert listed['status'] == 'success'
    assert listed['meta']['pagination']['count'] == 1

    queued = jobs.enqueue_job(tenant_id='tenant-default', job_type='test.noop', payload={'hello': 'cancel-me'})
    cancel_status, cancelled = post_background_job_cancel(jobs, queued.job_id, {'tenant_id': 'tenant-default', 'actor_role': 'Admin'})
    assert cancel_status == 200
    assert cancelled['data']['status'] == 'Cancelled'

    failing_jobs = BackgroundJobService()
    failing_jobs.register_handler('test.fail', lambda context: (_ for _ in ()).throw(RuntimeError('boom')), max_attempts=1)
    failed_job = failing_jobs.enqueue_job(tenant_id='tenant-default', job_type='test.fail', payload={})
    failing_jobs.execute_job(failed_job.job_id, tenant_id='tenant-default')
    retry_status, retried = post_background_job_retry(
        failing_jobs,
        failed_job.job_id,
        {'tenant_id': 'tenant-default', 'actor_role': 'Admin'},
    )
    assert retry_status == 202
    assert retried['data']['status'] == 'Scheduled'
