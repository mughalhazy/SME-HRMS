from __future__ import annotations

from typing import Any, Callable

from api_contract import error_payload, pagination_payload, success_response
from helpdesk_service import HelpdeskService, HelpdeskServiceError
from resilience import new_trace_id


SERVICE_NAME = 'helpdesk-service'


def _actor_meta(actor_role: str | None, actor_id: str | None) -> dict[str, str] | None:
    if isinstance(actor_role, str) and isinstance(actor_id, str):
        return {'id': actor_id, 'type': 'user', 'role': actor_role}
    return None


def with_error_handling(handler: Callable[..., tuple[int, dict[str, Any]]]) -> Callable[..., tuple[int, dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service = args[0]
        actor_role = args[1] if len(args) > 1 else None
        actor_id = args[2] if len(args) > 2 else None
        actor = _actor_meta(actor_role, actor_id)
        try:
            status, payload = handler(*args, **kwargs)
            pagination = payload.pop('_pagination', None) if isinstance(payload, dict) else None
            tenant_id = payload.get('tenant_id') if isinstance(payload, dict) else getattr(service, 'tenant_id', None)
            return success_response(status, payload, request_id=trace_id, pagination=pagination, tenant_id=tenant_id, actor=actor, service=SERVICE_NAME)
        except HelpdeskServiceError as exc:
            error = exc.payload['error']
            return exc.status_code, error_payload(error['code'], error['message'], trace_id, error['details'], tenant_id=getattr(service, 'tenant_id', None), actor=actor, service=SERVICE_NAME)
        except (KeyError, TypeError, ValueError):
            return 422, error_payload('VALIDATION_ERROR', 'Invalid request payload.', trace_id, tenant_id=getattr(service, 'tenant_id', None), actor=actor, service=SERVICE_NAME)

    return wrapped


@with_error_handling
def post_helpdesk_tickets(service: HelpdeskService, actor_role: str, actor_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return service.create_ticket(payload, actor_id=actor_id, actor_role=actor_role, actor_type='user')


@with_error_handling
def post_helpdesk_ticket_attachment(service: HelpdeskService, actor_role: str, actor_id: str, ticket_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return service.add_attachment(ticket_id, payload, actor_id=actor_id, actor_role=actor_role, actor_type='user', tenant_id=payload.get('tenant_id'))


@with_error_handling
def post_helpdesk_ticket_comment(service: HelpdeskService, actor_role: str, actor_id: str, ticket_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return service.add_comment(ticket_id, payload, actor_id=actor_id, actor_role=actor_role, actor_type='user', tenant_id=payload.get('tenant_id'))


@with_error_handling
def post_helpdesk_ticket_submit(service: HelpdeskService, actor_role: str, actor_id: str, ticket_id: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = payload or {}
    return service.submit_ticket(ticket_id, actor_id=actor_id, actor_role=actor_role, actor_type='user', tenant_id=body.get('tenant_id'))


@with_error_handling
def post_helpdesk_ticket_decision(service: HelpdeskService, action: str, actor_role: str, actor_id: str, ticket_id: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = payload or {}
    return service.decide_ticket(ticket_id, action=action, actor_id=actor_id, actor_role=actor_role, actor_type='user', tenant_id=body.get('tenant_id'), comment=body.get('comment'), resolution_summary=body.get('resolution_summary'))


@with_error_handling
def post_helpdesk_ticket_close(service: HelpdeskService, actor_role: str, actor_id: str, ticket_id: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = payload or {}
    return service.close_ticket(ticket_id, body, actor_id=actor_id, actor_role=actor_role, actor_type='user', tenant_id=body.get('tenant_id'))


@with_error_handling
def post_helpdesk_ticket_reopen(service: HelpdeskService, actor_role: str, actor_id: str, ticket_id: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = payload or {}
    return service.reopen_ticket(ticket_id, body, actor_id=actor_id, actor_role=actor_role, actor_type='user', tenant_id=body.get('tenant_id'))


@with_error_handling
def post_helpdesk_sla_monitor(service: HelpdeskService, actor_role: str, actor_id: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = payload or {}
    return service.run_sla_monitor(tenant_id=body.get('tenant_id'))


@with_error_handling
def get_helpdesk_ticket(service: HelpdeskService, actor_role: str, actor_id: str, ticket_id: str, query: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    params = query or {}
    return service.get_ticket(ticket_id, tenant_id=params.get('tenant_id'), actor_id=actor_id, actor_role=actor_role)


@with_error_handling
def get_helpdesk_tickets(service: HelpdeskService, actor_role: str, actor_id: str, query: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    params = query or {}
    status, payload = service.list_tickets(
        tenant_id=params.get('tenant_id'),
        requester_employee_id=params.get('requester_employee_id'),
        assigned_employee_id=params.get('assigned_employee_id'),
        status=params.get('status'),
        actor_id=actor_id,
        actor_role=actor_role,
    )
    payload['_pagination'] = pagination_payload(count=len(payload['items']))
    return status, payload


@with_error_handling
def get_helpdesk_analytics(service: HelpdeskService, actor_role: str, actor_id: str, query: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    params = query or {}
    return service.get_analytics(tenant_id=params.get('tenant_id'))


@with_error_handling
def post_helpdesk_automation_hook(service: HelpdeskService, actor_role: str, actor_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return service.register_automation_hook(payload, actor_id=actor_id, tenant_id=payload.get('tenant_id'))


@with_error_handling
def get_helpdesk_automation_hooks(service: HelpdeskService, actor_role: str, actor_id: str, query: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    params = query or {}
    return service.list_automation_hooks(tenant_id=params.get('tenant_id'), event_name=params.get('event_name'))


@with_error_handling
def get_helpdesk_automation_runs(service: HelpdeskService, actor_role: str, actor_id: str, query: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    params = query or {}
    return service.list_automation_runs(tenant_id=params.get('tenant_id'), ticket_id=params.get('ticket_id'))
