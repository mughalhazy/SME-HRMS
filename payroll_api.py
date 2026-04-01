from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from api_contract import error_response, pagination_payload, success_response
from payroll_service import PayrollService, ServiceError
from resilience import new_trace_id
from services.payroll.paas import PayrollManagedService


SERVICE_NAME = 'payroll-service'


_ERROR_STATUS_BY_CODE = {
    'VALIDATION_ERROR': 422,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'CONFLICT': 409,
}


def _decode_actor(service: PayrollService, authorization: str | None) -> dict[str, str | None] | None:
    if not authorization:
        return None
    try:
        ctx = service.decode_bearer_token(authorization)
    except Exception:
        return None
    return {
        'id': ctx.employee_id,
        'type': 'user',
        'role': ctx.role.value,
        'department_id': ctx.department_id,
    }


def _error_response(code: str, message: str, *, trace_id: str, details: list[dict[str, Any]] | None = None, actor: dict[str, Any] | None = None, tenant_id: str | None = None) -> tuple[int, dict[str, Any]]:
    return error_response(
        _ERROR_STATUS_BY_CODE.get(code, 400),
        code,
        message,
        request_id=trace_id,
        details=details,
        tenant_id=tenant_id,
        actor=actor,
        service=SERVICE_NAME,
    )


def with_error_handling(handler: Callable[..., tuple[int, dict[str, Any]]]) -> Callable[..., tuple[int, dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service = args[0]
        operation = getattr(handler, '__name__', 'payroll.operation')
        started = perf_counter()
        authorization = kwargs.get('authorization')
        if authorization is None and len(args) > 2 and isinstance(args[2], (str, type(None))):
            authorization = args[2]
        actor = _decode_actor(service, authorization)
        try:
            status, payload = handler(*args, trace_id=trace_id, **kwargs)
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={'status': status})
            pagination = payload.pop('_pagination', None) if isinstance(payload, dict) else None
            return success_response(
                status,
                payload,
                request_id=trace_id,
                pagination=pagination,
                tenant_id=service.tenant_id,
                actor=actor,
                service=SERVICE_NAME,
            )
        except ServiceError as exc:
            service.error_logger.log(operation, exc, trace_id=trace_id)
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': exc.status, 'code': exc.code})
            return _error_response(exc.code, exc.message, trace_id=trace_id, details=exc.details, actor=actor, tenant_id=service.tenant_id)
        except (TypeError, ValueError) as exc:
            service.error_logger.log(operation, exc, trace_id=trace_id)
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': 422, 'code': 'VALIDATION_ERROR'})
            return _error_response('VALIDATION_ERROR', 'Invalid request payload.', trace_id=trace_id, actor=actor, tenant_id=service.tenant_id)

    return wrapped


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if set(payload.keys()) == {'data'}:
        return payload['data']
    return payload


@with_error_handling
def post_payroll_records(service: PayrollService, payload: dict[str, Any], authorization: str | None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    status, result = service.create_payroll_record(payload, authorization, trace_id=trace_id)
    return status, _normalize_payload(result)


@with_error_handling
def get_payroll_record(service: PayrollService, payroll_record_id: str, authorization: str | None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    status, result = service.get_payroll_record(payroll_record_id, authorization)
    return status, _normalize_payload(result)


@with_error_handling
def get_payroll_records(service: PayrollService, authorization: str | None, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    limit = int(params.get('limit', 25))
    status, result = service.list_payroll_records(
        authorization,
        employee_id=params.get('employee_id'),
        period_start=params.get('period_start') or params.get('pay_period_start'),
        period_end=params.get('period_end') or params.get('pay_period_end'),
        status=params.get('status'),
        limit=limit,
        cursor=params.get('cursor'),
    )
    items = result['data']
    page = result.get('page', {})
    return status, {
        'items': items,
        'data': items,
        'filters': {
            key: params[key]
            for key in ('employee_id', 'period_start', 'period_end', 'pay_period_start', 'pay_period_end', 'status')
            if params.get(key) is not None
        },
        '_pagination': pagination_payload(
            limit=page.get('limit', limit),
            cursor=params.get('cursor'),
            next_cursor=page.get('nextCursor'),
            count=len(items),
            extra={'has_next': page.get('hasNext', False)},
        ),
    }


@with_error_handling
def post_payroll_run(service: PayrollService, payload: dict[str, Any], authorization: str | None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    status, result = service.run_payroll(
        payload['period_start'],
        payload['period_end'],
        authorization,
        records=payload.get('records'),
        idempotency_key=payload.get('idempotency_key'),
        trace_id=trace_id,
    )
    return status, _normalize_payload(result)


@with_error_handling
def post_payroll_mark_paid(service: PayrollService, payroll_record_id: str, payload: dict[str, Any] | None, authorization: str | None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    body = payload or {}
    status, result = service.mark_paid(
        payroll_record_id,
        authorization,
        payment_date=body.get('payment_date'),
        idempotency_key=body.get('idempotency_key'),
        trace_id=trace_id,
    )
    return status, _normalize_payload(result)


@with_error_handling
def post_paas_run_payroll(service: PayrollService, payload: dict[str, Any], authorization: str | None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    managed = PayrollManagedService(service)
    data = managed.run_payroll(
        tier=str(payload["tier"]),
        actor_id=str(payload.get("actor_id", "external-operator")),
        actor_mode=str(payload.get("actor_mode", "external_operator")),
        period_start=str(payload["period_start"]),
        period_end=str(payload["period_end"]),
        authorization=authorization,
        trace_id=trace_id,
    )
    return 200, data


@with_error_handling
def post_paas_override(service: PayrollService, payload: dict[str, Any], authorization: str | None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    managed = PayrollManagedService(service)
    data = managed.admin_override(
        tier=str(payload["tier"]),
        actor_id=str(payload.get("actor_id", "admin")),
        payroll_record_id=str(payload["payroll_record_id"]),
        payment_date=payload.get("payment_date"),
        reason=payload.get("reason"),
        authorization=authorization,
        trace_id=trace_id,
    )
    return 200, data
