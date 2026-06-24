from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from api_contract import error_response, success_response
from automation_service import AutomationService, AutomationServiceError
from resilience import new_trace_id

_ERROR_STATUS_BY_CODE = {
    'VALIDATION_ERROR': 422,
    'RULE_NOT_FOUND': 404,
    'TENANT_SCOPE_VIOLATION': 403,
}


def _error_response(code: str, message: str, *, details: list[dict[str, Any]] | None = None, trace_id: str) -> tuple[int, dict[str, Any]]:
    return error_response(_ERROR_STATUS_BY_CODE.get(code, 400), code, message, request_id=trace_id, details=details)


def with_error_handling(handler: Callable[..., tuple[int, dict[str, Any]]]) -> Callable[..., tuple[int, dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service: AutomationService = args[0]
        operation = getattr(handler, '__name__', 'automation.operation')
        started = perf_counter()
        try:
            status, payload = handler(*args, trace_id=trace_id, **kwargs)
            pagination = payload.pop('_pagination', None) if isinstance(payload, dict) else None
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={'status': status})
            return success_response(status, payload, request_id=trace_id, pagination=pagination)
        except AutomationServiceError as exc:
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': _ERROR_STATUS_BY_CODE.get(exc.code, 400), 'code': exc.code})
            return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)
        except PermissionError:
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': 403, 'code': 'TENANT_SCOPE_VIOLATION'})
            return _error_response('TENANT_SCOPE_VIOLATION', 'Tenant scope does not permit this operation', trace_id=trace_id)

    return wrapped


@with_error_handling
def post_rule(service: AutomationService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    rule = service.create_rule(payload, actor=payload.get('actor') if isinstance(payload.get('actor'), dict) else None, trace_id=trace_id)
    return 201, rule.to_dict()


@with_error_handling
def get_rules(service: AutomationService, query: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    rows = service.list_rules(tenant_id=str(query['tenant_id']), status=str(query['status']) if query.get('status') else None)
    return 200, {'items': [row.to_dict() for row in rows], '_pagination': {'count': len(rows), 'limit': len(rows), 'cursor': None, 'next_cursor': None}}


@with_error_handling
def post_event(service: AutomationService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return 202, service.consume_event(payload, trace_id=trace_id)


@with_error_handling
def get_executions(service: AutomationService, query: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    rows = service.list_executions(tenant_id=str(query['tenant_id']), rule_id=str(query['rule_id']) if query.get('rule_id') else None)
    return 200, {'items': [row.to_dict() for row in rows], '_pagination': {'count': len(rows), 'limit': len(rows), 'cursor': None, 'next_cursor': None}}
