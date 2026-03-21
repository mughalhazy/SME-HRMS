from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    tenant_id: str | None = None
    actor: Mapping[str, Any] | None = None
    service: str | None = None


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def request_context(
    request_id: str,
    *,
    tenant_id: str | None = None,
    actor: Mapping[str, Any] | None = None,
    service: str | None = None,
) -> RequestContext:
    return RequestContext(
        request_id=request_id,
        tenant_id=tenant_id,
        actor=dict(actor) if actor else None,
        service=service,
    )


def pagination_payload(
    *,
    limit: int | None = None,
    cursor: str | None = None,
    next_cursor: str | None = None,
    count: int | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        'limit': limit,
        'cursor': cursor,
        'next_cursor': next_cursor,
        'count': count,
    }
    if extra:
        payload.update(dict(extra))
    return payload


def list_payload(
    items: list[Any],
    *,
    extra: Mapping[str, Any] | None = None,
    legacy_key: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {'items': items}
    if legacy_key:
        payload[legacy_key] = items
    if extra:
        payload.update(dict(extra))
    return payload


def _coerce_context(
    request_id: str | RequestContext,
    *,
    tenant_id: str | None = None,
    actor: Mapping[str, Any] | None = None,
    service: str | None = None,
) -> RequestContext:
    if isinstance(request_id, RequestContext):
        return request_id
    return request_context(request_id, tenant_id=tenant_id, actor=actor, service=service)


def meta_payload(
    request_id: str | RequestContext,
    pagination: Mapping[str, Any] | None = None,
    *,
    tenant_id: str | None = None,
    actor: Mapping[str, Any] | None = None,
    service: str | None = None,
) -> dict[str, Any]:
    context = _coerce_context(request_id, tenant_id=tenant_id, actor=actor, service=service)
    meta: dict[str, Any] = {
        'request_id': context.request_id,
        'timestamp': _timestamp(),
        'pagination': dict(pagination or {}),
    }
    if context.tenant_id is not None:
        meta['tenant_id'] = context.tenant_id
    if context.actor is not None:
        meta['actor'] = dict(context.actor)
    if context.service is not None:
        meta['service'] = context.service
    return meta


def success_payload(
    data: Any,
    request_id: str | RequestContext,
    *,
    pagination: Mapping[str, Any] | None = None,
    tenant_id: str | None = None,
    actor: Mapping[str, Any] | None = None,
    service: str | None = None,
) -> dict[str, Any]:
    context = _coerce_context(request_id, tenant_id=tenant_id, actor=actor, service=service)
    return {
        'status': 'success',
        'data': data,
        'meta': meta_payload(context, pagination),
        'error': None,
    }


def success_response(
    status: int,
    data: Any,
    *,
    request_id: str | RequestContext,
    pagination: Mapping[str, Any] | None = None,
    tenant_id: str | None = None,
    actor: Mapping[str, Any] | None = None,
    service: str | None = None,
) -> tuple[int, dict[str, Any]]:
    return status, success_payload(
        data,
        request_id,
        pagination=pagination,
        tenant_id=tenant_id,
        actor=actor,
        service=service,
    )


def error_payload(
    code: str,
    message: str,
    request_id: str | RequestContext,
    details: dict[str, Any] | list[dict[str, Any]] | None = None,
    *,
    pagination: Mapping[str, Any] | None = None,
    tenant_id: str | None = None,
    actor: Mapping[str, Any] | None = None,
    service: str | None = None,
) -> dict[str, Any]:
    context = _coerce_context(request_id, tenant_id=tenant_id, actor=actor, service=service)
    return {
        'status': 'error',
        'data': {},
        'meta': meta_payload(context, pagination),
        'error': {
            'code': code,
            'message': message,
            'details': details or {},
        },
    }


def error_response(
    status: int,
    code: str,
    message: str,
    *,
    request_id: str | RequestContext,
    details: dict[str, Any] | list[dict[str, Any]] | None = None,
    pagination: Mapping[str, Any] | None = None,
    tenant_id: str | None = None,
    actor: Mapping[str, Any] | None = None,
    service: str | None = None,
) -> tuple[int, dict[str, Any]]:
    return status, error_payload(
        code,
        message,
        request_id,
        details,
        pagination=pagination,
        tenant_id=tenant_id,
        actor=actor,
        service=service,
    )
