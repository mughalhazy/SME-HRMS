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
        return event

    def dispatch_pending(
        self,
        publisher: Callable[[dict[str, Any]], None],
        *,
        attempts: int = 3,
        retryable: Callable[[Exception], bool] | None = None,
    ) -> list[dict[str, Any]]:
        dispatched: list[dict[str, Any]] = []
        for outbox_id in sorted(self.records.keys()):
            record = self.records.get(outbox_id)
            if record is None or record.status == 'dispatched':
                continue

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
                self.observability.logger.error(
                    'outbox.dispatch_failed',
                    message=record.event_type,
                    context={'event_id': record.event_id, 'tenant_id': record.tenant_id, 'error': str(exc)},
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
        result = handler(event)
        outcome = {'consumer': consumer_name, 'event_id': event_id, 'processed_at': _utc_now().isoformat(), 'result': result}
        self.consumers[dedupe_key] = outcome
        self.consumer_dedupe.record(dedupe_key, fingerprint, 200, outcome)
        return result, False
