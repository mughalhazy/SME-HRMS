from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def pagination_payload(*, limit: int | None = None, cursor: str | None = None, next_cursor: str | None = None, count: int | None = None, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        'limit': limit,
        'cursor': cursor,
        'next_cursor': next_cursor,
        'count': count,
    }
    if extra:
        payload.update(dict(extra))
    return payload


def meta_payload(request_id: str, pagination: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        'request_id': request_id,
        'timestamp': _timestamp(),
        'pagination': dict(pagination or {}),
    }


def success_payload(data: Any, request_id: str, *, pagination: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        'status': 'success',
        'data': data,
        'meta': meta_payload(request_id, pagination),
        'error': None,
    }


def success_response(status: int, data: Any, *, request_id: str, pagination: Mapping[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    return status, success_payload(data, request_id, pagination=pagination)


def error_payload(code: str, message: str, request_id: str, details: dict[str, Any] | list[dict[str, Any]] | None = None, *, pagination: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        'status': 'error',
        'data': {},
        'meta': meta_payload(request_id, pagination),
        'error': {
            'code': code,
            'message': message,
            'details': details or {},
        },
    }


def error_response(status: int, code: str, message: str, *, request_id: str, details: dict[str, Any] | list[dict[str, Any]] | None = None, pagination: Mapping[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    return status, error_payload(code, message, request_id, details, pagination=pagination)
