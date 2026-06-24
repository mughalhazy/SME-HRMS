from __future__ import annotations

from time import perf_counter
from typing import Any, Callable, Dict

from api_contract import error_payload, success_response
from employee_service import EmployeeService, EmployeeServiceError
from resilience import new_trace_id


SERVICE_NAME = 'employee-service'


def _error_envelope(trace_id: str, exc: EmployeeServiceError, *, tenant_id: str | None = None) -> dict:
    error = exc.payload['error']
    return error_payload(error['code'], error['message'], trace_id, error.get('details'), tenant_id=tenant_id, service=SERVICE_NAME)


def with_error_handling(handler: Callable[..., Dict[str, Any]]) -> Callable[..., tuple[int, dict]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service = args[0]
        operation = getattr(handler, '__name__', 'employee.operation')
        started = perf_counter()
        try:
            status, payload = handler(*args, **kwargs)
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={'status': status})
            pagination = payload.pop('_pagination', None) if isinstance(payload, dict) else None
            tenant_id = payload.get('tenant_id') if isinstance(payload, dict) else None
            return success_response(status, payload, request_id=trace_id, pagination=pagination, tenant_id=tenant_id, service=SERVICE_NAME)
        except EmployeeServiceError as exc:
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': exc.status_code})
            return exc.status_code, _error_envelope(trace_id, exc, tenant_id=getattr(service, 'tenant_id', None))
        except (KeyError, TypeError, ValueError):
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': 422})
            return 422, error_payload('VALIDATION_ERROR', 'Invalid request payload.', trace_id, tenant_id=getattr(service, 'tenant_id', None), service=SERVICE_NAME)
    return wrapped


# ---------------------------------------------------------------------------
# Department handlers
# ---------------------------------------------------------------------------

@with_error_handling
def post_departments(service: EmployeeService, payload: dict) -> tuple[int, dict]:
    return service.create_department(payload)


@with_error_handling
def get_departments(service: EmployeeService, query: dict) -> tuple[int, dict]:
    return service.list_departments(tenant_id=query.get('tenant_id'), status=query.get('status'))


@with_error_handling
def get_department(service: EmployeeService, department_id: str) -> tuple[int, dict]:
    return service.get_department(department_id)


@with_error_handling
def patch_department(service: EmployeeService, department_id: str, payload: dict) -> tuple[int, dict]:
    return service.update_department(department_id, payload)


# ---------------------------------------------------------------------------
# Role handlers
# ---------------------------------------------------------------------------

@with_error_handling
def post_roles(service: EmployeeService, payload: dict) -> tuple[int, dict]:
    return service.create_role(payload)


@with_error_handling
def get_roles(service: EmployeeService, query: dict) -> tuple[int, dict]:
    return service.list_roles(tenant_id=query.get('tenant_id'), status=query.get('status'))


@with_error_handling
def get_role(service: EmployeeService, role_id: str) -> tuple[int, dict]:
    return service.get_role(role_id)


@with_error_handling
def patch_role(service: EmployeeService, role_id: str, payload: dict) -> tuple[int, dict]:
    return service.update_role(role_id, payload)


# ---------------------------------------------------------------------------
# Employee handlers
# ---------------------------------------------------------------------------

@with_error_handling
def post_employees(service: EmployeeService, payload: dict) -> tuple[int, dict]:
    return service.create_employee(payload)


@with_error_handling
def get_employees(service: EmployeeService, query: dict) -> tuple[int, dict]:
    return service.list_employees(
        tenant_id=query.get('tenant_id'),
        department_id=query.get('department_id'),
        status=query.get('status'),
    )


@with_error_handling
def get_employee(service: EmployeeService, employee_id: str) -> tuple[int, dict]:
    return service.get_employee(employee_id)


@with_error_handling
def patch_employee(service: EmployeeService, employee_id: str, payload: dict) -> tuple[int, dict]:
    return service.update_employee(employee_id, payload)


@with_error_handling
def post_employee_terminate(service: EmployeeService, employee_id: str, payload: dict) -> tuple[int, dict]:
    return service.terminate_employee(employee_id, payload)


@with_error_handling
def post_employee_transfer(service: EmployeeService, employee_id: str, payload: dict) -> tuple[int, dict]:
    return service.transfer_employee(employee_id, payload)
