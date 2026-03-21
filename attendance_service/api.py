from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from time import perf_counter
from typing import Any, Callable, Dict
from uuid import UUID

from attendance_service.models import AttendanceLogEvent, AttendanceSource, AttendanceStatus
from attendance_service.service import Actor, AttendanceService, AttendanceServiceError
from api_contract import error_payload, pagination_payload, success_response
from resilience import new_trace_id


SERVICE_NAME = 'attendance-service'


def _parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


def _parse_datetime(raw: str | None) -> datetime | None:
    return datetime.fromisoformat(raw) if raw else None


def _actor_meta(actor: Actor) -> dict[str, str | None]:
    return {
        'id': str(actor.employee_id),
        'type': 'user',
        'role': actor.role,
        'department_id': str(actor.department_id) if actor.department_id else None,
    }


def error_envelope(trace_id: str, exc: AttendanceServiceError, *, actor: Actor | None = None) -> dict:
    return error_payload(exc.code, exc.message, trace_id, exc.details, actor=_actor_meta(actor) if actor else None, service=SERVICE_NAME)


def with_error_handling(handler: Callable[..., Dict[str, Any]]) -> Callable[..., tuple[int, dict]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service = args[0]
        actor = args[1] if len(args) > 1 and isinstance(args[1], Actor) else None
        operation = getattr(handler, '__name__', 'attendance.operation')
        started = perf_counter()
        try:
            status, payload = handler(*args, **kwargs)
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={'status': status})
            pagination = payload.pop('_pagination', None) if isinstance(payload, dict) else None
            return success_response(status, payload, request_id=trace_id, pagination=pagination, actor=_actor_meta(actor) if actor else None, service=SERVICE_NAME)
        except AttendanceServiceError as exc:
            status_map = {
                'FORBIDDEN': 403,
                'EMPLOYEE_NOT_FOUND': 404,
                'ATTENDANCE_NOT_FOUND': 404,
                'ATTENDANCE_DUPLICATE': 409,
                'ATTENDANCE_LOCKED': 409,
                'LOCK_REQUIRES_APPROVAL': 409,
                'APPROVAL_REQUIRES_VALIDATED': 409,
                'TIME_LOGIC_INVALID': 422,
                'DATE_RANGE_INVALID': 422,
            }
            status = status_map.get(exc.code, 422)
            service.observability.logger.error(
                'attendance.error',
                trace_id=trace_id,
                message=operation,
                context={'code': exc.code, 'details': exc.details},
            )
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': status, 'code': exc.code})
            return status, error_envelope(trace_id, exc, actor=actor)
        except ValueError:
            service.observability.logger.error(
                'attendance.validation_error',
                trace_id=trace_id,
                message=operation,
                context={},
            )
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': 422, 'code': 'VALIDATION_ERROR'})
            return 422, error_payload('VALIDATION_ERROR', 'Invalid request payload.', trace_id, actor=_actor_meta(actor) if actor else None, service=SERVICE_NAME)

    return wrapped


@with_error_handling
def post_attendance_records(service: AttendanceService, actor: Actor, payload: dict) -> tuple[int, dict]:
    record = service.create_record(
        actor,
        employee_id=UUID(payload['employee_id']),
        attendance_date=_parse_date(payload['attendance_date']),
        attendance_status=AttendanceStatus(payload['attendance_status']),
        source=AttendanceSource(payload['source']) if payload.get('source') else None,
        check_in_time=_parse_datetime(payload.get('check_in_time')),
        check_out_time=_parse_datetime(payload.get('check_out_time')),
        correction_note=payload.get('correction_note'),
    )
    return 201, _record_to_response(record)


@with_error_handling
def post_attendance_log(service: AttendanceService, actor: Actor, payload: dict) -> tuple[int, dict]:
    record = service.log_attendance(
        actor,
        employee_id=UUID(payload['employee_id']),
        event_type=AttendanceLogEvent(payload['event_type']),
        occurred_at=_parse_datetime(payload['occurred_at']),
        source=AttendanceSource(payload['source']) if payload.get('source') else None,
    )
    return 200, _record_to_response(record)


@with_error_handling
def get_attendance_records(service: AttendanceService, actor: Actor, query: dict) -> tuple[int, dict]:
    employee_id = UUID(query['employee_id'])
    from_date = _parse_date(query['from_date'])
    to_date = _parse_date(query['to_date'])
    records = service.list_records(actor, employee_id=employee_id, from_date=from_date, to_date=to_date)
    aggregation = service.aggregate_period(actor, employee_id=employee_id, from_date=from_date, to_date=to_date)
    return 200, {
        'records': [_record_to_response(record) for record in records],
        'aggregation': aggregation,
        'filters': {
            'employee_id': str(employee_id),
            'attendance_date_from': from_date.isoformat(),
            'attendance_date_to': to_date.isoformat(),
        },
        '_pagination': pagination_payload(count=len(records), limit=len(records), cursor=None, next_cursor=None),
    }


@with_error_handling
def get_attendance_record(service: AttendanceService, actor: Actor, attendance_id: str) -> tuple[int, dict]:
    record = service.get_record(actor, UUID(attendance_id))
    return 200, _record_to_response(record)


@with_error_handling
def patch_attendance_record(service: AttendanceService, actor: Actor, attendance_id: str, payload: dict) -> tuple[int, dict]:
    record = service.update_record(
        actor,
        UUID(attendance_id),
        attendance_status=AttendanceStatus(payload['attendance_status']) if payload.get('attendance_status') else None,
        check_in_time=_parse_datetime(payload.get('check_in_time')),
        check_out_time=_parse_datetime(payload.get('check_out_time')),
        correction_note=payload.get('correction_note'),
    )
    return 200, _record_to_response(record)


@with_error_handling
def post_attendance_approval(service: AttendanceService, actor: Actor, attendance_id: str) -> tuple[int, dict]:
    record = service.approve_record(actor, UUID(attendance_id))
    return 200, _record_to_response(record)


@with_error_handling
def post_attendance_period_lock(service: AttendanceService, actor: Actor, payload: dict) -> tuple[int, dict]:
    result = service.lock_period(
        actor,
        period_id=payload['period_id'],
        from_date=_parse_date(payload['from_date']),
        to_date=_parse_date(payload['to_date']),
    )
    return 200, result


@with_error_handling
def get_attendance_summary(service: AttendanceService, actor: Actor, query: dict) -> tuple[int, dict]:
    result = service.get_summary(
        actor,
        employee_id=UUID(query['employee_id']),
        period_start=_parse_date(query['period_start']),
        period_end=_parse_date(query['period_end']),
    )
    return 200, result


@with_error_handling
def get_attendance_absence_alerts(service: AttendanceService, actor: Actor, query: dict) -> tuple[int, dict]:
    result = service.attendance_absence_alerts(actor, attendance_date=_parse_date(query['attendance_date']))
    return 200, result


def _record_to_response(record: Any) -> dict:
    data = asdict(record)
    for key in ['attendance_id', 'employee_id']:
        data[key] = str(data[key])
    for key in ['attendance_date', 'check_in_time', 'check_out_time', 'created_at', 'updated_at']:
        if data.get(key):
            data[key] = data[key].isoformat()
    for key in ['attendance_status', 'source', 'lifecycle_state']:
        if data.get(key):
            data[key] = data[key].value
    if data.get('anomalies'):
        data['anomalies'] = [anomaly.value for anomaly in data['anomalies']]
    if data.get('total_hours') is not None:
        data['total_hours'] = str(data['total_hours'])
    return data
