from __future__ import annotations

from datetime import date
from time import perf_counter
from typing import Any, Callable, Dict

from api_contract import error_payload, pagination_payload, success_response
from leave_service import LeaveService, LeaveServiceError
from resilience import new_trace_id


SERVICE_NAME = 'leave-service'


def _parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


def _actor_meta(actor_role: str, actor_employee_id: str) -> dict[str, str]:
    return {'id': actor_employee_id, 'type': 'user', 'role': actor_role}


def error_envelope(trace_id: str, exc: LeaveServiceError, *, tenant_id: str | None = None, actor: dict[str, str] | None = None) -> dict:
    error = exc.payload['error']
    return error_payload(error['code'], error['message'], trace_id, error.get('details'), tenant_id=tenant_id, actor=actor, service=SERVICE_NAME)


def with_error_handling(handler: Callable[..., Dict[str, Any]]) -> Callable[..., tuple[int, dict]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service = args[0]
        operation = getattr(handler, '__name__', 'leave.operation')
        started = perf_counter()
        actor_role = args[1] if len(args) > 1 else None
        actor_employee_id = args[2] if len(args) > 2 else None
        actor = _actor_meta(actor_role, actor_employee_id) if isinstance(actor_role, str) and isinstance(actor_employee_id, str) else None
        try:
            status, payload = handler(*args, **kwargs)
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={'status': status})
            pagination = payload.pop('_pagination', None) if isinstance(payload, dict) else None
            tenant_id = payload.get('tenant_id') if isinstance(payload, dict) else None
            return success_response(
                status,
                payload,
                request_id=trace_id,
                pagination=pagination,
                tenant_id=tenant_id,
                actor=actor,
                service=SERVICE_NAME,
            )
        except LeaveServiceError as exc:
            service.observability.logger.error(
                'leave.error',
                trace_id=trace_id,
                message=operation,
                context={'code': exc.payload['error']['code'], 'details': exc.payload['error']['details']},
            )
            service.observability.track(
                operation,
                trace_id=trace_id,
                started_at=started,
                success=False,
                context={'status': exc.status_code, 'code': exc.payload['error']['code']},
            )
            return exc.status_code, error_envelope(trace_id, exc, tenant_id=getattr(service, 'tenant_id', None), actor=actor)
        except (KeyError, TypeError, ValueError):
            service.observability.logger.error(
                'leave.validation_error',
                trace_id=trace_id,
                message=operation,
                context={},
            )
            service.observability.track(
                operation,
                trace_id=trace_id,
                started_at=started,
                success=False,
                context={'status': 422, 'code': 'VALIDATION_ERROR'},
            )
            return (
                422,
                error_payload('VALIDATION_ERROR', 'Invalid request payload.', trace_id, tenant_id=getattr(service, 'tenant_id', None), actor=actor, service=SERVICE_NAME),
            )

    return wrapped


@with_error_handling
def post_leave_requests(service: LeaveService, actor_role: str, actor_employee_id: str, payload: dict) -> tuple[int, dict]:
    return service.create_request(
        actor_role=actor_role,
        actor_employee_id=actor_employee_id,
        employee_id=payload['employee_id'],
        leave_type=payload['leave_type'],
        start_date=_parse_date(payload['start_date']),
        end_date=_parse_date(payload['end_date']),
        reason=payload.get('reason'),
        approver_employee_id=payload.get('approver_employee_id'),
        tenant_id=payload.get('tenant_id'),
    )


@with_error_handling
def post_leave_submit(service: LeaveService, actor_role: str, actor_employee_id: str, leave_request_id: str, payload: dict | None = None) -> tuple[int, dict]:
    body = payload or {}
    return service.submit_request(
        actor_role=actor_role,
        actor_employee_id=actor_employee_id,
        leave_request_id=leave_request_id,
        idempotency_key=body.get('idempotency_key'),
        tenant_id=body.get('tenant_id'),
    )


@with_error_handling
def post_leave_decision(service: LeaveService, action: str, actor_role: str, actor_employee_id: str, leave_request_id: str, payload: dict | None = None) -> tuple[int, dict]:
    body = payload or {}
    return service.decide_request(
        action=action,
        actor_role=actor_role,
        actor_employee_id=actor_employee_id,
        leave_request_id=leave_request_id,
        reason=body.get('reason'),
        idempotency_key=body.get('idempotency_key'),
        tenant_id=body.get('tenant_id'),
    )


@with_error_handling
def get_leave_request(service: LeaveService, actor_role: str, actor_employee_id: str, leave_request_id: str, query: dict | None = None) -> tuple[int, dict]:
    params = query or {}
    return service.get_request(
        actor_role=actor_role,
        actor_employee_id=actor_employee_id,
        leave_request_id=leave_request_id,
        tenant_id=params.get('tenant_id'),
    )


@with_error_handling
def patch_leave_request(service: LeaveService, actor_role: str, actor_employee_id: str, leave_request_id: str, payload: dict) -> tuple[int, dict]:
    return service.patch_request(
        actor_role=actor_role,
        actor_employee_id=actor_employee_id,
        leave_request_id=leave_request_id,
        patch=payload,
        tenant_id=payload.get('tenant_id'),
    )


@with_error_handling
def get_leave_requests(service: LeaveService, actor_role: str, actor_employee_id: str, query: dict | None = None) -> tuple[int, dict]:
    params = query or {}
    status, payload = service.list_requests(
        actor_role=actor_role,
        actor_employee_id=actor_employee_id,
        employee_id=params.get('employee_id'),
        approver_employee_id=params.get('approver_employee_id'),
        status=params.get('status'),
        tenant_id=params.get('tenant_id'),
    )
    items = payload['data']
    normalized = {
        'items': items,
        'data': items,
        'leave_balances': payload.get('leave_balances', []),
        '_pagination': pagination_payload(
            limit=None,
            cursor=None,
            next_cursor=None,
            count=len(items),
        ),
    }
    if params:
        normalized['filters'] = {
            key: params[key]
            for key in ('employee_id', 'approver_employee_id', 'status')
            if params.get(key) is not None
        }
    return status, normalized
