from __future__ import annotations

from typing import Any, Callable

from api_contract import error_payload, pagination_payload, success_response
from expense_service import ExpenseService, ExpenseServiceError
from resilience import new_trace_id


SERVICE_NAME = 'expense-service'


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
        except ExpenseServiceError as exc:
            error = exc.payload['error']
            return exc.status_code, error_payload(error['code'], error['message'], trace_id, error['details'], tenant_id=getattr(service, 'tenant_id', None), actor=actor, service=SERVICE_NAME)
        except (KeyError, TypeError, ValueError):
            return 422, error_payload('VALIDATION_ERROR', 'Invalid request payload.', trace_id, tenant_id=getattr(service, 'tenant_id', None), actor=actor, service=SERVICE_NAME)

    return wrapped


@with_error_handling
def post_expense_categories(service: ExpenseService, actor_role: str, actor_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return service.create_category(payload, actor_id=actor_id, actor_type='user')


@with_error_handling
def post_expense_claims(service: ExpenseService, actor_role: str, actor_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return service.create_claim(payload, actor_id=actor_id, actor_type='user')


@with_error_handling
def post_expense_attachment(service: ExpenseService, actor_role: str, actor_id: str, expense_claim_id: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return service.add_attachment(expense_claim_id, payload, actor_id=actor_id, actor_type='user', tenant_id=payload.get('tenant_id'))


@with_error_handling
def post_expense_submit(service: ExpenseService, actor_role: str, actor_id: str, expense_claim_id: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = payload or {}
    return service.submit_claim(expense_claim_id, actor_id=actor_id, actor_type='user', tenant_id=body.get('tenant_id'))


@with_error_handling
def post_expense_decision(service: ExpenseService, action: str, actor_role: str, actor_id: str, expense_claim_id: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = payload or {}
    return service.decide_claim(expense_claim_id, action=action, actor_id=actor_id, actor_role=actor_role, actor_type='user', tenant_id=body.get('tenant_id'), comment=body.get('comment'))


@with_error_handling
def post_expense_reimburse(service: ExpenseService, actor_role: str, actor_id: str, expense_claim_id: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = payload or {}
    return service.reimburse_claim(expense_claim_id, body, actor_id=actor_id, actor_role=actor_role, actor_type='user', tenant_id=body.get('tenant_id'))


@with_error_handling
def get_expense_claim(service: ExpenseService, actor_role: str, actor_id: str, expense_claim_id: str, query: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    params = query or {}
    return service.get_claim(expense_claim_id, tenant_id=params.get('tenant_id'), actor_id=actor_id)


@with_error_handling
def get_expense_claims(service: ExpenseService, actor_role: str, actor_id: str, query: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    params = query or {}
    status, payload = service.list_claims(
        tenant_id=params.get('tenant_id'),
        employee_id=params.get('employee_id'),
        approver_employee_id=params.get('approver_employee_id'),
        status=params.get('status'),
        category_code=params.get('category_code'),
    )
    payload['_pagination'] = pagination_payload(count=len(payload['items']))
    return status, payload
