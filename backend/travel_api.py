from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from api_contract import error_payload, pagination_payload, success_response
from resilience import new_trace_id
from travel_service import TravelService, TravelServiceError

SERVICE_NAME = 'travel-service'


def _actor_meta(actor_role: str | None, actor_employee_id: str | None) -> dict[str, str] | None:
    if not actor_employee_id:
        return None
    return {'id': actor_employee_id, 'type': 'user', 'role': actor_role or 'Employee'}


def error_envelope(trace_id: str, exc: TravelServiceError, *, tenant_id: str | None = None, actor: dict[str, str] | None = None) -> dict[str, Any]:
    error = exc.payload['error']
    return error_payload(error['code'], error['message'], trace_id, error.get('details'), tenant_id=tenant_id, actor=actor, service=SERVICE_NAME)


def with_error_handling(handler: Callable[..., tuple[int, dict[str, Any]]]) -> Callable[..., tuple[int, dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service: TravelService = args[0]
        operation = getattr(handler, '__name__', 'travel.operation')
        started = perf_counter()
        actor_role = args[1] if len(args) > 1 and isinstance(args[1], str) else None
        actor_employee_id = args[2] if len(args) > 2 and isinstance(args[2], str) else None
        actor = _actor_meta(actor_role, actor_employee_id)
        try:
            status, payload = handler(*args, trace_id=trace_id, **kwargs)
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={'status': status})
            pagination = payload.pop('_pagination', None) if isinstance(payload, dict) else None
            tenant_id = payload.get('tenant_id') if isinstance(payload, dict) else None
            return success_response(status, payload, request_id=trace_id, pagination=pagination, tenant_id=tenant_id, actor=actor, service=SERVICE_NAME)
        except TravelServiceError as exc:
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': exc.status_code, 'code': exc.payload['error']['code']})
            return exc.status_code, error_envelope(trace_id, exc, tenant_id=getattr(service, 'tenant_id', None), actor=actor)
        except (KeyError, TypeError, ValueError) as exc:
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': 422, 'code': 'VALIDATION_ERROR'})
            return 422, error_payload('VALIDATION_ERROR', str(exc) or 'Invalid request payload.', trace_id, tenant_id=getattr(service, 'tenant_id', None), actor=actor, service=SERVICE_NAME)

    return wrapped


@with_error_handling
def post_travel_requests(service: TravelService, actor_role: str, actor_employee_id: str, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return service.create_request(payload, actor_id=actor_employee_id, actor_type='user', trace_id=trace_id)


@with_error_handling
def post_travel_request_submit(service: TravelService, actor_role: str, actor_employee_id: str, travel_request_id: str, payload: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return service.submit_request(travel_request_id, actor_id=actor_employee_id, actor_type='user', trace_id=trace_id)


@with_error_handling
def post_travel_request_decision(service: TravelService, action: str, actor_role: str, actor_employee_id: str, travel_request_id: str, payload: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    body = payload or {}
    return service.decide_request(travel_request_id, action=action, actor_id=actor_employee_id, actor_type='user', actor_role=actor_role, comment=body.get('comment'), trace_id=trace_id)


@with_error_handling
def put_travel_itinerary(service: TravelService, actor_role: str, actor_employee_id: str, travel_request_id: str, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return service.update_itinerary(travel_request_id, payload, actor_id=actor_employee_id, actor_type='user', trace_id=trace_id)


@with_error_handling
def post_travel_request_cancel(service: TravelService, actor_role: str, actor_employee_id: str, travel_request_id: str, payload: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return service.cancel_request(travel_request_id, actor_id=actor_employee_id, actor_type='user', trace_id=trace_id)


@with_error_handling
def post_travel_request_complete(service: TravelService, actor_role: str, actor_employee_id: str, travel_request_id: str, payload: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return service.complete_request(travel_request_id, actor_id=actor_employee_id, actor_type='user', trace_id=trace_id)


@with_error_handling
def get_travel_request(service: TravelService, actor_role: str, actor_employee_id: str, travel_request_id: str, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    return service.get_request(travel_request_id, tenant_id=params.get('tenant_id'))


@with_error_handling
def get_travel_requests(service: TravelService, actor_role: str, actor_employee_id: str, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    limit = int(params.get('limit', 25))
    status, payload = service.list_requests(tenant_id=params.get('tenant_id'), employee_id=params.get('employee_id'), status=params.get('status'), limit=limit, cursor=params.get('cursor'))
    payload['_pagination'] = payload.get('_pagination') or pagination_payload(limit=limit, cursor=params.get('cursor'), next_cursor=None, count=len(payload.get('items', [])))
    return status, payload
