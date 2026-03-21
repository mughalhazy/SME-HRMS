from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable
from uuid import uuid4

from persistent_store import PersistentKVStore
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id


@dataclass
class OutboxEvent:
    event_id: str
    tenant_id: str
    aggregate_type: str
    aggregate_id: str
    event_name: str
    payload: dict[str, Any]
    trace_id: str
    occurred_at: str
    published_at: str | None
    failed_attempts: int
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventOutbox:
    def __init__(self, *, db_path: str | None = None):
        self.events = PersistentKVStore[str, OutboxEvent](service='background-jobs', namespace='event_outbox', db_path=db_path)
        self._lock = RLock()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def stage_event(
        self,
        *,
        tenant_id: str,
        aggregate_type: str,
        aggregate_id: str,
        event_name: str,
        payload: dict[str, Any],
        trace_id: str,
        event_id: str | None = None,
        occurred_at: str | None = None,
    ) -> OutboxEvent:
        tenant = normalize_tenant_id(tenant_id)
        with self._lock:
            outbox_event = OutboxEvent(
                event_id=event_id or str(uuid4()),
                tenant_id=tenant,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_name=event_name,
                payload=dict(payload),
                trace_id=trace_id,
                occurred_at=occurred_at or self._now(),
                published_at=None,
                failed_attempts=0,
                created_at=self._now(),
            )
            self.events[outbox_event.event_id] = outbox_event
            return outbox_event

    def stage_canonical_event(self, event: dict[str, Any], *, aggregate_type: str, aggregate_id: str) -> OutboxEvent:
        event_name = str(event.get('legacy_event_name') or event.get('event_name') or event.get('type') or event.get('event_type') or 'UnknownEvent')
        return self.stage_event(
            tenant_id=str(event.get('tenant_id') or DEFAULT_TENANT_ID),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_name=event_name,
            payload=event,
            trace_id=str(event.get('metadata', {}).get('correlation_id') or event.get('trace_id') or uuid4().hex),
            event_id=str(event.get('event_id') or uuid4()),
            occurred_at=str(event.get('timestamp') or self._now()),
        )

    def pending_events(self, *, tenant_id: str | None = None) -> list[OutboxEvent]:
        tenant = normalize_tenant_id(tenant_id) if tenant_id is not None else None
        rows = [row for row in self.events.values() if row.published_at is None]
        if tenant is not None:
            rows = [row for row in rows if row.tenant_id == tenant]
        rows.sort(key=lambda row: (row.occurred_at, row.created_at, row.event_id))
        return rows

    def list_events(self, *, tenant_id: str | None = None) -> list[OutboxEvent]:
        rows = list(self.events.values())
        if tenant_id is not None:
            tenant = normalize_tenant_id(tenant_id)
            rows = [row for row in rows if row.tenant_id == tenant]
        rows.sort(key=lambda row: (row.created_at, row.event_id))
        return rows

    def mark_published(self, event_id: str) -> OutboxEvent:
        with self._lock:
            event = self.events[event_id]
            event.published_at = self._now()
            self.events[event_id] = event
            return event

    def mark_failed(self, event_id: str) -> OutboxEvent:
        with self._lock:
            event = self.events[event_id]
            event.failed_attempts += 1
            self.events[event_id] = event
            return event

    def get_event(self, event_id: str, *, tenant_id: str | None = None) -> OutboxEvent:
        event = self.events[event_id]
        if tenant_id is not None:
            assert_tenant_access(event.tenant_id, tenant_id)
        return event

    def dispatch_pending(
        self,
        dispatcher: Callable[[OutboxEvent], Any],
        *,
        tenant_id: str | None = None,
        max_events: int | None = None,
    ) -> dict[str, Any]:
        dispatched: list[str] = []
        failed: list[dict[str, Any]] = []
        rows = self.pending_events(tenant_id=tenant_id)
        if max_events is not None:
            rows = rows[:max_events]
        for row in rows:
            try:
                dispatcher(row)
                self.mark_published(row.event_id)
                dispatched.append(row.event_id)
            except Exception as exc:  # noqa: BLE001
                self.mark_failed(row.event_id)
                failed.append({'event_id': row.event_id, 'reason': str(exc), 'event_name': row.event_name})
        return {
            'dispatched_count': len(dispatched),
            'failed_count': len(failed),
            'dispatched_event_ids': dispatched,
            'failures': failed,
        }
