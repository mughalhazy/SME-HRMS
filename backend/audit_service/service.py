from __future__ import annotations

import base64
import copy
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import Any, Iterable
from uuid import uuid4

from tenant_support import DEFAULT_TENANT_ID, normalize_tenant_id


def default_audit_log_path() -> Path:
    return Path(os.getenv('HRMS_AUDIT_LOG_PATH') or (Path(tempfile.gettempdir()) / 'sme-hrms' / 'audit-records.jsonl'))


@dataclass(frozen=True)
class AuditActor:
    id: str
    type: str
    role: str | None = None
    department_id: str | None = None


@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    tenant_id: str
    actor: dict[str, Any]
    action: str
    entity: str
    entity_id: str
    before: dict[str, Any]
    after: dict[str, Any]
    timestamp: str
    trace_id: str
    source: dict[str, Any]


class AuditQueryError(ValueError):
    pass


class AuditService:
    def __init__(self, log_path: str | os.PathLike[str] | None = None):
        self.log_path = Path(log_path) if log_path else default_audit_log_path()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def append_record(
        self,
        *,
        tenant_id: str,
        actor: dict[str, Any],
        action: str,
        entity: str,
        entity_id: str,
        before: Any,
        after: Any,
        trace_id: str,
        source: dict[str, Any] | None = None,
        audit_id: str | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        record = AuditRecord(
            audit_id=audit_id or str(uuid4()),
            tenant_id=normalize_tenant_id(tenant_id),
            actor=self._normalize_actor(actor),
            action=action,
            entity=entity,
            entity_id=str(entity_id),
            before=self._normalize_mapping(before),
            after=self._normalize_mapping(after),
            timestamp=timestamp or datetime.utcnow().isoformat() + 'Z',
            trace_id=trace_id,
            source=self._normalize_mapping(source or {}),
        )
        payload = json.dumps(asdict(record), sort_keys=True)
        with self._lock:
            with self.log_path.open('a', encoding='utf-8') as handle:
                handle.write(payload)
                handle.write('\n')
        return asdict(record)

    def list_records(
        self,
        *,
        tenant_id: str,
        actor_id: str | None = None,
        actor_type: str | None = None,
        entity: str | None = None,
        entity_id: str | None = None,
        action: str | None = None,
        timestamp_from: str | None = None,
        timestamp_to: str | None = None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        if not tenant:
            raise AuditQueryError('tenant_id is required')
        if limit < 1 or limit > 100:
            raise AuditQueryError('limit must be between 1 and 100')

        rows = [
            row for row in self._read_records()
            if row['tenant_id'] == tenant
            and (actor_id is None or row.get('actor', {}).get('id') == actor_id)
            and (actor_type is None or row.get('actor', {}).get('type') == actor_type)
            and (entity is None or row['entity'] == entity)
            and (entity_id is None or row['entity_id'] == str(entity_id))
            and (action is None or row['action'] == action)
            and (timestamp_from is None or row['timestamp'] >= timestamp_from)
            and (timestamp_to is None or row['timestamp'] <= timestamp_to)
        ]
        rows.sort(key=lambda row: (row['timestamp'], row['audit_id']), reverse=True)

        offset = self._decode_cursor(cursor)
        page = rows[offset: offset + limit]
        next_cursor = self._encode_cursor(offset + limit) if offset + limit < len(rows) else None
        pagination = {
            'limit': limit,
            'cursor': cursor,
            'next_cursor': next_cursor,
            'count': len(page),
            'total_count': len(rows),
        }
        return page, pagination

    def _read_records(self) -> Iterable[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        with self._lock:
            with self.log_path.open('r', encoding='utf-8') as handle:
                return [json.loads(line) for line in handle if line.strip()]

    @staticmethod
    def _encode_cursor(offset: int) -> str:
        return base64.urlsafe_b64encode(str(offset).encode('utf-8')).decode('utf-8').rstrip('=')

    @staticmethod
    def _decode_cursor(cursor: str | None) -> int:
        if not cursor:
            return 0
        padded = cursor + '=' * (-len(cursor) % 4)
        try:
            value = base64.urlsafe_b64decode(padded.encode('utf-8')).decode('utf-8')
            offset = int(value)
        except Exception as exc:  # pragma: no cover - defensive guard
            raise AuditQueryError('cursor is invalid') from exc
        if offset < 0:
            raise AuditQueryError('cursor is invalid')
        return offset

    @staticmethod
    def _normalize_actor(actor: dict[str, Any] | AuditActor | str | None) -> dict[str, Any]:
        if isinstance(actor, str):
            payload = {'id': actor, 'type': 'system'}
        elif isinstance(actor, AuditActor):
            payload = asdict(actor)
        elif isinstance(actor, dict):
            payload = dict(actor)
        else:
            payload = {'id': 'system', 'type': 'system'}

        payload['id'] = str(payload.get('id') or 'system')
        payload['type'] = str(payload.get('type') or 'system')
        if payload.get('role') is not None:
            payload['role'] = str(payload['role'])
        if payload.get('department_id') is not None:
            payload['department_id'] = str(payload['department_id'])
        return payload

    @classmethod
    def _normalize_mapping(cls, value: Any) -> dict[str, Any]:
        normalized = cls._serialize_value(value)
        return normalized if isinstance(normalized, dict) else {'value': normalized}

    @classmethod
    def _serialize_value(cls, value: Any) -> Any:
        if value is None:
            return {}
        if is_dataclass(value):
            return cls._serialize_value(asdict(value))
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {str(key): cls._serialize_value(val) for key, val in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [cls._serialize_value(item) for item in value]
        if hasattr(value, 'to_dict') and callable(value.to_dict):
            return cls._serialize_value(value.to_dict())
        if hasattr(value, '__dict__') and not isinstance(value, (str, bytes, int, float, bool)):
            return cls._serialize_value(copy.deepcopy(vars(value)))
        return value


_AUDIT_SERVICE: AuditService | None = None


def get_audit_service(log_path: str | os.PathLike[str] | None = None) -> AuditService:
    global _AUDIT_SERVICE
    resolved = Path(log_path) if log_path else default_audit_log_path()
    if _AUDIT_SERVICE is None or _AUDIT_SERVICE.log_path != resolved:
        _AUDIT_SERVICE = AuditService(resolved)
    return _AUDIT_SERVICE



def emit_audit_record(
    *,
    service_name: str,
    tenant_id: str,
    actor: dict[str, Any] | AuditActor | str | None,
    action: str,
    entity: str,
    entity_id: str,
    before: Any,
    after: Any,
    trace_id: str,
    source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_payload = {'service': service_name, **(source or {})}
    return get_audit_service().append_record(
        tenant_id=tenant_id,
        actor=AuditService._normalize_actor(actor),
        action=action,
        entity=entity,
        entity_id=entity_id,
        before=before,
        after=after,
        trace_id=trace_id,
        source=source_payload,
    )
