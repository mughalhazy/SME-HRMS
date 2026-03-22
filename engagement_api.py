from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from api_contract import error_payload, success_response
from engagement_service import EngagementService, EngagementServiceError
from resilience import new_trace_id

SERVICE_NAME = 'engagement-service'


def _actor_meta(actor_role: str | None, actor_employee_id: str | None) -> dict[str, str] | None:
    if not actor_employee_id:
        return None
    return {'id': actor_employee_id, 'type': 'user', 'role': actor_role or 'Employee'}


def error_envelope(trace_id: str, exc: EngagementServiceError, *, tenant_id: str | None = None, actor: dict[str, str] | None = None) -> dict[str, Any]:
    error = exc.payload['error']
    return error_payload(error['code'], error['message'], trace_id, error.get('details'), tenant_id=tenant_id, actor=actor, service=SERVICE_NAME)


def with_error_handling(handler: Callable[..., tuple[int, dict[str, Any]]]) -> Callable[..., tuple[int, dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service: EngagementService = args[0]
        operation = getattr(handler, '__name__', 'engagement.operation')
        started = perf_counter()
        actor_role = args[1] if len(args) > 1 and isinstance(args[1], str) else None
        actor_employee_id = args[2] if len(args) > 2 and isinstance(args[2], str) else None
        actor = _actor_meta(actor_role, actor_employee_id)
        try:
            status, payload = handler(*args, trace_id=trace_id, **kwargs)
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={'status': status})
            tenant_id = payload.get('tenant_id') if isinstance(payload, dict) else None
            return success_response(status, payload, request_id=trace_id, tenant_id=tenant_id, actor=actor, service=SERVICE_NAME)
        except EngagementServiceError as exc:
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': exc.status_code, 'code': exc.payload['error']['code']})
            return exc.status_code, error_envelope(trace_id, exc, tenant_id=getattr(service, 'tenant_id', None), actor=actor)
        except (KeyError, TypeError, ValueError) as exc:
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': 422, 'code': 'VALIDATION_ERROR'})
            return 422, error_payload('VALIDATION_ERROR', str(exc) or 'Invalid request payload.', trace_id, tenant_id=getattr(service, 'tenant_id', None), actor=actor, service=SERVICE_NAME)

    return wrapped


@with_error_handling
def post_surveys(service: EngagementService, actor_role: str, actor_employee_id: str, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return service.create_survey(payload, actor_id=actor_employee_id, actor_type='user', trace_id=trace_id)


@with_error_handling
def post_survey_publish(service: EngagementService, actor_role: str, actor_employee_id: str, survey_id: str, payload: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = payload or {}
    return service.publish_survey(survey_id, tenant_id=params.get('tenant_id'), actor_id=actor_employee_id, actor_type='user', trace_id=trace_id)


@with_error_handling
def post_survey_close(service: EngagementService, actor_role: str, actor_employee_id: str, survey_id: str, payload: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = payload or {}
    return service.close_survey(survey_id, tenant_id=params.get('tenant_id'), actor_id=actor_employee_id, actor_type='user', trace_id=trace_id)


@with_error_handling
def post_responses(service: EngagementService, actor_role: str, actor_employee_id: str, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return service.submit_response(payload, actor_id=actor_employee_id, actor_type='user', trace_id=trace_id)


@with_error_handling
def get_surveys(service: EngagementService, actor_role: str, actor_employee_id: str, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    return service.list_surveys(tenant_id=params.get('tenant_id'), status=params.get('status'))


@with_error_handling
def get_survey(service: EngagementService, actor_role: str, actor_employee_id: str, survey_id: str, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    return service.get_survey(survey_id, tenant_id=params.get('tenant_id'))


@with_error_handling
def get_responses(service: EngagementService, actor_role: str, actor_employee_id: str, survey_id: str, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    return service.list_responses(survey_id, tenant_id=params.get('tenant_id'))


@with_error_handling
def get_aggregated_results(service: EngagementService, actor_role: str, actor_employee_id: str, survey_id: str, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    return service.get_aggregated_results(survey_id, tenant_id=params.get('tenant_id'))
