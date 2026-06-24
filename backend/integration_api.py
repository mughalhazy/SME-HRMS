from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from api_contract import error_response, success_response
from integration_service import IntegrationService, IntegrationServiceError
from resilience import new_trace_id

_ERROR_STATUS_BY_CODE = {
    'VALIDATION_ERROR': 422,
    'WEBHOOK_NOT_FOUND': 404,
    'DELIVERY_NOT_FOUND': 404,
    'INVALID_DELIVERY_STATE': 409,
    'TENANT_SCOPE_VIOLATION': 403,
    'SECRET_INTEGRITY_ERROR': 500,
}


def _error_response(code: str, message: str, *, details: list[dict[str, Any]] | None = None, trace_id: str) -> tuple[int, dict[str, Any]]:
    return error_response(_ERROR_STATUS_BY_CODE.get(code, 400), code, message, request_id=trace_id, details=details)


def with_error_handling(handler: Callable[..., tuple[int, dict[str, Any]]]) -> Callable[..., tuple[int, dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service: IntegrationService = args[0]
        operation = getattr(handler, '__name__', 'integration.operation')
        started = perf_counter()
        try:
            status, payload = handler(*args, trace_id=trace_id, **kwargs)
            pagination = payload.pop('_pagination', None) if isinstance(payload, dict) else None
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={'status': status})
            return success_response(status, payload, request_id=trace_id, pagination=pagination)
        except IntegrationServiceError as exc:
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': _ERROR_STATUS_BY_CODE.get(exc.code, 400), 'code': exc.code})
            return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)
        except PermissionError:
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': 403, 'code': 'TENANT_SCOPE_VIOLATION'})
            return _error_response('TENANT_SCOPE_VIOLATION', 'Tenant scope does not permit this operation', trace_id=trace_id)

    return wrapped


@with_error_handling
def post_webhook(service: IntegrationService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    webhook = service.create_webhook(payload, actor=payload.get('actor') if isinstance(payload.get('actor'), dict) else None, trace_id=trace_id)
    return 201, service._serialize_webhook(webhook)


@with_error_handling
def patch_webhook(service: IntegrationService, webhook_id: str, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    webhook = service.update_webhook(webhook_id, payload, actor=payload.get('actor') if isinstance(payload.get('actor'), dict) else None, trace_id=trace_id)
    return 200, service._serialize_webhook(webhook)


@with_error_handling
def delete_webhook(service: IntegrationService, webhook_id: str, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    webhook = service.delete_webhook(webhook_id, tenant_id=str(payload['tenant_id']), actor=payload.get('actor') if isinstance(payload.get('actor'), dict) else None, trace_id=trace_id)
    return 200, service._serialize_webhook(webhook)


@with_error_handling
def get_webhooks(service: IntegrationService, query: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    limit = int(query.get('limit', 25) or 25)
    rows, pagination = service.list_webhooks(tenant_id=str(query['tenant_id']), status=query.get('status'), limit=limit, cursor=query.get('cursor'))
    return 200, {'items': [service._serialize_webhook(row) for row in rows], '_pagination': pagination}


@with_error_handling
def get_delivery_attempts(service: IntegrationService, query: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    limit = int(query.get('limit', 25) or 25)
    rows, pagination = service.list_delivery_attempts(
        tenant_id=str(query['tenant_id']),
        webhook_id=str(query['webhook_id']) if query.get('webhook_id') else None,
        delivery_status=str(query['delivery_status']) if query.get('delivery_status') else None,
        event_type=str(query['event_type']) if query.get('event_type') else None,
        limit=limit,
        cursor=query.get('cursor'),
    )
    return 200, {'items': rows, '_pagination': pagination}


@with_error_handling
def post_delivery_replay(service: IntegrationService, delivery_id: str, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    replay = service.replay_failed_delivery(
        delivery_id,
        tenant_id=str(payload['tenant_id']),
        actor=payload.get('actor') if isinstance(payload.get('actor'), dict) else None,
        trace_id=trace_id,
    )
    return 202, replay.to_dict()
