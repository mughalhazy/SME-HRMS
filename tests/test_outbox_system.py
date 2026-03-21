from __future__ import annotations

from pathlib import Path

from outbox_system import OutboxManager


def test_outbox_dispatch_retries_and_tracks_failure(tmp_path: Path) -> None:
    manager = OutboxManager(
        service_name='attendance-service',
        tenant_id='tenant-default',
        db_path=str(tmp_path / 'outbox.sqlite3'),
    )
    manager.enqueue(
        legacy_event_name='AttendanceCaptured',
        data={
            'attendance_id': '11111111-1111-1111-1111-111111111111',
            'employee_id': '22222222-2222-2222-2222-222222222222',
            'attendance_date': '2026-03-21',
            'attendance_status': 'Present',
            'record_state': 'Captured',
        },
        idempotency_key='11111111-1111-1111-1111-111111111111',
    )

    attempts = {'count': 0}

    def flaky_publisher(_: dict) -> None:
        attempts['count'] += 1
        raise RuntimeError('broker unavailable')

    dispatched = manager.dispatch_pending(flaky_publisher, attempts=2)
    assert dispatched == []
    record = next(iter(manager.records.values()))
    assert record.status == 'failed'
    assert record.attempt_count == 2
    assert record.last_error == 'broker unavailable'
    assert attempts['count'] == 2
    assert manager.dead_letters.entries


def test_outbox_consumer_is_replay_safe(tmp_path: Path) -> None:
    manager = OutboxManager(
        service_name='leave-service',
        tenant_id='tenant-default',
        db_path=str(tmp_path / 'consumer.sqlite3'),
    )
    event = manager.enqueue(
        legacy_event_name='LeaveRequestApproved',
        data={
            'leave_request_id': 'leave-1',
            'employee_id': 'emp-1',
            'approver_employee_id': 'mgr-1',
            'total_days': 2.0,
            'leave_type': 'Annual',
            'status': 'Approved',
            'decision_at': '2026-03-21T00:00:00+00:00',
        },
        idempotency_key='leave-1',
    )

    invocations = {'count': 0}

    def handler(payload: dict) -> dict:
        invocations['count'] += 1
        return {'event_type': payload['event_type']}

    first, duplicate_first = manager.consume_once(consumer_name='notification-service', event=event, handler=handler)
    second, duplicate_second = manager.consume_once(consumer_name='notification-service', event=event, handler=handler)

    assert duplicate_first is False
    assert duplicate_second is True
    assert first == second
    assert invocations['count'] == 1
