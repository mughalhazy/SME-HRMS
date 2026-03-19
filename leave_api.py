from __future__ import annotations

from datetime import date
from time import perf_counter
from typing import Any, Callable, Dict

from leave_service import LeaveService, LeaveServiceError
from resilience import new_trace_id


def _parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


def error_envelope(trace_id: str, exc: LeaveServiceError) -> dict:
    return exc.payload


def with_error_handling(handler: Callable[..., Dict[str, Any]]) -> Callable[..., tuple[int, dict]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict]:
        trace_id = kwargs.pop("trace_id", None) or new_trace_id()
        service = args[0]
        operation = getattr(handler, "__name__", "leave.operation")
        started = perf_counter()
        try:
            status, payload = handler(*args, **kwargs)
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={"status": status})
            return status, payload
        except LeaveServiceError as exc:
            service.observability.logger.error(
                "leave.error",
                trace_id=trace_id,
                message=operation,
                context={"code": exc.payload["error"]["code"], "details": exc.payload["error"]["details"]},
            )
            service.observability.track(
                operation,
                trace_id=trace_id,
                started_at=started,
                success=False,
                context={"status": exc.status_code, "code": exc.payload["error"]["code"]},
            )
            return exc.status_code, error_envelope(trace_id, exc)
        except (KeyError, TypeError, ValueError):
            service.observability.logger.error(
                "leave.validation_error",
                trace_id=trace_id,
                message=operation,
                context={},
            )
            service.observability.track(
                operation,
                trace_id=trace_id,
                started_at=started,
                success=False,
                context={"status": 422, "code": "VALIDATION_ERROR"},
            )
            return (
                422,
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid request payload.",
                        "details": [],
                        "traceId": trace_id,
                    }
                },
            )

    return wrapped


@with_error_handling
def post_leave_requests(service: LeaveService, actor_role: str, actor_employee_id: str, payload: dict) -> tuple[int, dict]:
    return service.create_request(
        actor_role=actor_role,
        actor_employee_id=actor_employee_id,
        employee_id=payload["employee_id"],
        leave_type=payload["leave_type"],
        start_date=_parse_date(payload["start_date"]),
        end_date=_parse_date(payload["end_date"]),
        reason=payload.get("reason"),
        approver_employee_id=payload.get("approver_employee_id"),
    )


@with_error_handling
def post_leave_decision(service: LeaveService, action: str, actor_role: str, actor_employee_id: str, leave_request_id: str, payload: dict | None = None) -> tuple[int, dict]:
    body = payload or {}
    return service.decide_request(
        action=action,
        actor_role=actor_role,
        actor_employee_id=actor_employee_id,
        leave_request_id=leave_request_id,
        reason=body.get("reason"),
    )


@with_error_handling
def get_leave_requests(service: LeaveService, actor_role: str, actor_employee_id: str, query: dict | None = None) -> tuple[int, dict]:
    params = query or {}
    return service.list_requests(
        actor_role=actor_role,
        actor_employee_id=actor_employee_id,
        employee_id=params.get("employee_id"),
        approver_employee_id=params.get("approver_employee_id"),
        status=params.get("status"),
    )
