from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from api_contract import error_response, pagination_payload, success_response
from reporting_analytics import ReportingAnalyticsError, ReportingAnalyticsService
from resilience import new_trace_id


_ERROR_CODES = {
    'report was not found': (404, 'REPORT_NOT_FOUND'),
    'aggregate_type is not supported': (422, 'UNSUPPORTED_AGGREGATE'),
    'report_type is not supported': (422, 'UNSUPPORTED_REPORT_TYPE'),
    'name is required': (422, 'VALIDATION_ERROR'),
    'cadence must be daily, weekly, or monthly': (422, 'VALIDATION_ERROR'),
    'export_format must be csv or json': (422, 'VALIDATION_ERROR'),
}


def _error_for(exc: ReportingAnalyticsError) -> tuple[int, str, str]:
    message = str(exc)
    status, code = _ERROR_CODES.get(message, (422, 'VALIDATION_ERROR'))
    return status, code, message


def with_error_handling(handler: Callable[..., tuple[int, dict[str, Any]]]) -> Callable[..., tuple[int, dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service = args[0]
        started = perf_counter()
        operation = getattr(handler, '__name__', 'reporting.operation')
        try:
            status, payload = handler(*args, trace_id=trace_id, **kwargs)
            pagination = payload.pop('_pagination', None) if isinstance(payload, dict) else None
            return success_response(status, payload, request_id=trace_id, pagination=pagination, tenant_id=service.tenant_id, service='reporting-analytics')
        except ReportingAnalyticsError as exc:
            service.projection_state['last_api_error'] = {'operation': operation, 'message': str(exc), 'trace_id': trace_id, 'captured_at': service._now()}
            status, code, message = _error_for(exc)
            return error_response(status, code, message, request_id=trace_id, tenant_id=service.tenant_id, service='reporting-analytics')
        finally:
            service.projection_state['last_api_call'] = {'operation': operation, 'trace_id': trace_id, 'captured_at': service._now(), 'duration_ms': round((perf_counter() - started) * 1000, 2)}

    return wrapped


@with_error_handling
def get_reporting_aggregates(service: ReportingAnalyticsService, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    rows = service.list_aggregates(
        aggregate_type=params.get('aggregate_type'),
        dimension_key=params.get('dimension_key'),
        dimension_value=params.get('dimension_value'),
    )
    return 200, {
        'items': rows,
        '_pagination': pagination_payload(count=len(rows), limit=len(rows), cursor=None, next_cursor=None),
    }


@with_error_handling
def post_reporting_report(service: ReportingAnalyticsService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return 201, service.create_report_definition(payload)


@with_error_handling
def get_reporting_reports(service: ReportingAnalyticsService, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    rows = service.list_report_definitions()
    return 200, {
        'items': rows,
        '_pagination': pagination_payload(count=len(rows), limit=len(rows), cursor=None, next_cursor=None),
    }


@with_error_handling
def post_reporting_run(service: ReportingAnalyticsService, report_id: str, payload: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    run = service.run_report(report_id, trace_id=trace_id, filters_override=dict((payload or {}).get('filters') or {}))
    return 202, run


@with_error_handling
def post_reporting_export(service: ReportingAnalyticsService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    export = service.export_report(
        report_id=str(payload['report_id']),
        report_run_id=payload.get('report_run_id'),
        export_format=str(payload.get('export_format') or 'json'),
        trace_id=trace_id,
        schedule_id=payload.get('schedule_id'),
    )
    return 202, export


@with_error_handling
def get_reporting_exports(service: ReportingAnalyticsService, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    rows = service.list_exports(report_id=params.get('report_id'))
    return 200, {
        'items': rows,
        '_pagination': pagination_payload(count=len(rows), limit=len(rows), cursor=None, next_cursor=None),
    }


@with_error_handling
def post_reporting_schedule(service: ReportingAnalyticsService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return 201, service.create_schedule(payload)


@with_error_handling
def get_reporting_schedules(service: ReportingAnalyticsService, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    rows = service.list_schedules(active_only=bool(params.get('active_only', False)))
    return 200, {
        'items': rows,
        '_pagination': pagination_payload(count=len(rows), limit=len(rows), cursor=None, next_cursor=None),
    }


@with_error_handling
def get_workforce_attrition_metrics(service: ReportingAnalyticsService, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    items = service.list_aggregates(aggregate_type='workforce.attrition.summary', dimension_key=params.get('dimension_key'), dimension_value=params.get('dimension_value'))
    return 200, {'items': items, '_pagination': pagination_payload(count=len(items), limit=len(items), cursor=None, next_cursor=None)}


@with_error_handling
def get_workforce_hiring_funnel(service: ReportingAnalyticsService, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    items = service.list_aggregates(aggregate_type='hiring.funnel.summary', dimension_key=params.get('dimension_key'), dimension_value=params.get('dimension_value'))
    return 200, {'items': items, '_pagination': pagination_payload(count=len(items), limit=len(items), cursor=None, next_cursor=None)}


@with_error_handling
def get_workforce_attendance_trends(service: ReportingAnalyticsService, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    items = service.list_aggregates(aggregate_type='workforce.attendance.trend', dimension_key=params.get('dimension_key'), dimension_value=params.get('dimension_value'))
    return 200, {'items': items, '_pagination': pagination_payload(count=len(items), limit=len(items), cursor=None, next_cursor=None)}


@with_error_handling
def get_workforce_dashboard(service: ReportingAnalyticsService, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    items = service.list_aggregates(aggregate_type='workforce.dashboard.summary', dimension_key=params.get('dimension_key') or 'tenant', dimension_value=params.get('dimension_value') or service.tenant_id)
    return 200, {'items': items, '_pagination': pagination_payload(count=len(items), limit=len(items), cursor=None, next_cursor=None)}
