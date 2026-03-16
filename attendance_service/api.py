from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from typing import Any, Callable, Dict
from uuid import UUID

from attendance_service.models import AttendanceSource, AttendanceStatus
from attendance_service.service import Actor, AttendanceService, AttendanceServiceError


def _parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


def _parse_datetime(raw: str | None) -> datetime | None:
    return datetime.fromisoformat(raw) if raw else None


def error_envelope(trace_id: str, exc: AttendanceServiceError) -> dict:
    return {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "traceId": trace_id,
        }
    }


def with_error_handling(handler: Callable[..., Dict[str, Any]]) -> Callable[..., tuple[int, dict]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict]:
        trace_id = kwargs.pop("trace_id", "generated-trace-id")
        try:
            return handler(*args, **kwargs)
        except AttendanceServiceError as exc:
            status = 403 if exc.code == "FORBIDDEN" else 422
            return status, error_envelope(trace_id, exc)

    return wrapped


@with_error_handling
def post_attendance_records(service: AttendanceService, actor: Actor, payload: dict) -> tuple[int, dict]:
    record = service.create_record(
        actor,
        employee_id=UUID(payload["employee_id"]),
        attendance_date=_parse_date(payload["attendance_date"]),
        attendance_status=AttendanceStatus(payload["attendance_status"]),
        source=AttendanceSource(payload["source"]) if payload.get("source") else None,
        check_in_time=_parse_datetime(payload.get("check_in_time")),
        check_out_time=_parse_datetime(payload.get("check_out_time")),
    )
    return 201, _record_to_response(record)


@with_error_handling
def patch_attendance_record(service: AttendanceService, actor: Actor, attendance_id: str, payload: dict) -> tuple[int, dict]:
    record = service.update_record(
        actor,
        UUID(attendance_id),
        attendance_status=AttendanceStatus(payload["attendance_status"]) if payload.get("attendance_status") else None,
        check_in_time=_parse_datetime(payload.get("check_in_time")),
        check_out_time=_parse_datetime(payload.get("check_out_time")),
    )
    return 200, _record_to_response(record)


def _record_to_response(record: Any) -> dict:
    data = asdict(record)
    for key in ["attendance_id", "employee_id"]:
        data[key] = str(data[key])
    for key in ["attendance_date", "check_in_time", "check_out_time", "created_at", "updated_at"]:
        if data.get(key):
            data[key] = data[key].isoformat()
    for key in ["attendance_status", "source", "lifecycle_state"]:
        if data.get(key):
            data[key] = data[key].value
    if data.get("total_hours") is not None:
        data["total_hours"] = str(data["total_hours"])
    return data
