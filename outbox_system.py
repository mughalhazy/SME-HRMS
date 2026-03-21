from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from event_contract import EventRegistry, ensure_event_contract
from persistent_store import PersistentKVStore
from resilience import DeadLetterQueue, IdempotencyStore, Observability, run_with_retry


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class OutboxRecord:
    outbox_id: str
    event_id: str
    event_type: str
    tenant_id: str
    status: str
    source: str
    payload: dict[str, Any]
    created_at: str
    updated_at: str
    dispatched_at: str | None = None
    attempt_count: int = 0
    last_error: str | None = None
    last_error_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OutboxManager:
    def __init__(
        self,
        *,
        service_name: str,
        tenant_id: str,
        db_path: str | None,
        observability: Observability | None = None,
        dead_letters: DeadLetterQueue | None = None,
        event_registry: EventRegistry | None = None,
    ) -> None:
        self.service_name = service_name
        self.tenant_id = tenant_id
        self.records = PersistentKVStore[str, OutboxRecord](service=service_name, namespace='outbox_records', db_path=db_path)
        self.consumers = PersistentKVStore[str, dict[str, Any]](service=service_name, namespace='processed_events', db_path=db_path)
        self.dispatch_log = PersistentKVStore[str, dict[str, Any]](service=service_name, namespace='dispatch_log', db_path=db_path)
        self.observability = observability or Observability(service_name)
        self.dead_letters = dead_letters or DeadLetterQueue()
        self.registry = event_registry or EventRegistry()
        self.consumer_dedupe = IdempotencyStore()

    def transaction(self, *stores: PersistentKVStore[Any, Any]):
        return PersistentKVStore.transaction(*stores, self.records, self.consumers, self.dispatch_log)

    def enqueue(
        self,
        *,
        legacy_event_name: str,
        data: dict[str, Any],
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event, _ = ensure_event_contract(
            {'event_name': legacy_event_name, 'tenant_id': self.tenant_id, 'data': data, 'metadata': metadata or {}},
            source=self.service_name,
            tenant_id=self.tenant_id,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            registry=self.registry,
        )
        now = _utc_now().isoformat()
        event['legacy_event_name'] = legacy_event_name
        event['type'] = legacy_event_name
        record = OutboxRecord(
            outbox_id=str(event['event_id']),
            event_id=str(event['event_id']),
            event_type=str(event['event_type']),
            tenant_id=self.tenant_id,
            status='pending',
            source=self.service_name,
            payload=event,
            created_at=now,
            updated_at=now,
            metadata={'legacy_event_name': legacy_event_name, **(metadata or {})},
        )
        self.records[record.outbox_id] = record
        correlation = str(event.get('metadata', {}).get('correlation_id') or correlation_id or event.get('event_id'))
        self.observability.logger.info(
            'outbox.enqueued',
            trace_id=correlation,
            message=legacy_event_name,
            action='outbox.enqueue',
            status='pending',
            tenant_id=self.tenant_id,
            correlation_id=correlation,
            context={'event_id': record.event_id, 'event_name': legacy_event_name, 'event_type': record.event_type, 'tenant_id': self.tenant_id, 'trace_stage': 'event'},
        )
        self.observability.record_trace('outbox.enqueue', request_id=correlation, status='pending', stage='event', context={'tenant_id': self.tenant_id, 'event_id': record.event_id, 'event_name': legacy_event_name, 'event_type': record.event_type, 'correlation_id': correlation})
        return event

    def dispatch_pending(
        self,
        publisher: Callable[[dict[str, Any]], None],
        *,
        attempts: int = 3,
        retryable: Callable[[Exception], bool] | None = None,
    ) -> list[dict[str, Any]]:
        dispatched: list[dict[str, Any]] = []
        pending_records = [
            record
            for record in self.records.values()
            if record is not None and record.status != 'dispatched'
        ]
        pending_records.sort(key=lambda record: (record.created_at, record.outbox_id))
        for record in pending_records:
            outbox_id = record.outbox_id

            def _publish() -> None:
                publisher(record.payload)

            try:
                run_with_retry(
                    _publish,
                    attempts=attempts,
                    base_delay=0.01,
                    timeout_seconds=0.5,
                    retryable=retryable or (lambda exc: True),
                )
                now = _utc_now().isoformat()
                record.status = 'dispatched'
                record.dispatched_at = now
                record.updated_at = now
                record.attempt_count += 1
                record.last_error = None
                record.last_error_at = None
                self.records[outbox_id] = record
                self.dispatch_log[outbox_id] = {
                    'event_id': record.event_id,
                    'event_type': record.event_type,
                    'tenant_id': record.tenant_id,
                    'status': 'dispatched',
                    'dispatched_at': now,
                    'attempt_count': record.attempt_count,
                }
                trace_id = str(record.payload.get('metadata', {}).get('correlation_id') or record.event_id)
                self.observability.metrics.record_request('outbox.dispatch_pending', trace_id=trace_id, latency_ms=0.0, success=True, context={'tenant_id': record.tenant_id, 'event_name': record.event_type, 'event_id': record.event_id, 'status': 'dispatched', 'trace_stage': 'event', 'correlation_id': trace_id})
                self.observability.record_trace('outbox.dispatch_pending', request_id=trace_id, status='dispatched', stage='event', context={'tenant_id': record.tenant_id, 'event_name': record.event_type, 'event_id': record.event_id, 'correlation_id': trace_id})
                dispatched.append(record.payload)
            except Exception as exc:  # noqa: BLE001
                now = _utc_now().isoformat()
                record.status = 'failed'
                record.updated_at = now
                record.attempt_count += attempts
                record.last_error = str(exc)
                record.last_error_at = now
                self.records[outbox_id] = record
                self.dispatch_log[outbox_id] = {
                    'event_id': record.event_id,
                    'event_type': record.event_type,
                    'tenant_id': record.tenant_id,
                    'status': 'failed',
                    'updated_at': now,
                    'attempt_count': record.attempt_count,
                    'last_error': str(exc),
                }
                self.dead_letters.push('outbox_dispatch', record.event_type, record.payload, str(exc), retryable=True)
                trace_id = str(record.payload.get('metadata', {}).get('correlation_id') or record.event_id)
                self.observability.metrics.record_request('outbox.dispatch_pending', trace_id=trace_id, latency_ms=0.0, success=False, context={'tenant_id': record.tenant_id, 'event_name': record.event_type, 'event_id': record.event_id, 'status': 'failed', 'trace_stage': 'event', 'error_category': 'dependency', 'correlation_id': trace_id})
                self.observability.record_trace('outbox.dispatch_pending', request_id=trace_id, status='failed', stage='event', context={'tenant_id': record.tenant_id, 'event_name': record.event_type, 'event_id': record.event_id, 'error': str(exc), 'correlation_id': trace_id})
                self.observability.logger.error(
                    'outbox.dispatch_failed',
                    trace_id=trace_id,
                    message=record.event_type,
                    action='outbox.dispatch_pending',
                    status='failed',
                    tenant_id=record.tenant_id,
                    correlation_id=trace_id,
                    context={'event_id': record.event_id, 'tenant_id': record.tenant_id, 'error': str(exc), 'event_name': record.event_type, 'trace_stage': 'event'},
                )
        return dispatched

    def consume_once(
        self,
        *,
        consumer_name: str,
        event: dict[str, Any],
        handler: Callable[[dict[str, Any]], Any],
    ) -> tuple[Any, bool]:
        event_id = str(event['event_id'])
        dedupe_key = f'{consumer_name}:{event_id}'
        fingerprint = f"{event['event_type']}::{event.get('tenant_id')}::{event_id}"
        replay = self.consumer_dedupe.replay_or_conflict(dedupe_key, fingerprint)
        if replay is not None:
            return replay.payload['result'], True
        trace_id = str(event.get('metadata', {}).get('correlation_id') or event.get('trace_id') or event_id)
        self.observability.record_trace('outbox.consume_once', request_id=trace_id, status='processing', stage='event', context={'tenant_id': str(event.get('tenant_id') or self.tenant_id), 'event_id': event_id, 'event_name': str(event.get('event_type') or event.get('event_name') or ''), 'consumer_name': consumer_name, 'correlation_id': trace_id})
        result = handler(event)
        outcome = {'consumer': consumer_name, 'event_id': event_id, 'processed_at': _utc_now().isoformat(), 'result': result}
        self.consumers[dedupe_key] = outcome
        self.observability.metrics.record_request('outbox.consume_once', trace_id=trace_id, latency_ms=0.0, success=True, context={'tenant_id': str(event.get('tenant_id') or self.tenant_id), 'event_name': str(event.get('event_type') or event.get('event_name') or ''), 'event_id': event_id, 'consumer_name': consumer_name, 'status': 'processed', 'trace_stage': 'event', 'correlation_id': trace_id})
        self.observability.record_trace('outbox.consume_once', request_id=trace_id, status='processed', stage='event', context={'tenant_id': str(event.get('tenant_id') or self.tenant_id), 'event_id': event_id, 'event_name': str(event.get('event_type') or event.get('event_name') or ''), 'consumer_name': consumer_name, 'correlation_id': trace_id})
        self.consumer_dedupe.record(dedupe_key, fingerprint, 200, outcome)
        return result, False
