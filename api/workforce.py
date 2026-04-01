from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from api_contract import error_response, success_response
from resilience import new_trace_id
from services.analytics.workforce import WorkforceAnalyticsError, WorkforceAnalyticsService


_ERROR_CODES = {
    'must be': (422, 'VALIDATION_ERROR'),
    'at least one value': (422, 'VALIDATION_ERROR'),
}


def _error_for(exc: WorkforceAnalyticsError) -> tuple[int, str, str]:
    message = str(exc)
    for fragment, payload in _ERROR_CODES.items():
        if fragment in message:
            status, code = payload
            return status, code, message
    return 422, 'VALIDATION_ERROR', message


def with_error_handling(handler: Callable[..., tuple[int, dict[str, Any]]]) -> Callable[..., tuple[int, dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service: WorkforceAnalyticsService = args[0]
        started = perf_counter()
        try:
            status, payload = handler(*args, trace_id=trace_id, **kwargs)
            return success_response(status, payload, request_id=trace_id, tenant_id=service.tenant_id, service='workforce-analytics')
        except WorkforceAnalyticsError as exc:
            status, code, message = _error_for(exc)
            return error_response(status, code, message, request_id=trace_id, tenant_id=service.tenant_id, service='workforce-analytics')
        finally:
            _ = perf_counter() - started

    return wrapped


@with_error_handling
def post_absenteeism_metric(service: WorkforceAnalyticsService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return 200, service.calculate_absenteeism(
        absent_days=payload.get('absent_days'),
        working_days=payload.get('working_days'),
        expected_absence_rate=payload.get('expected_absence_rate', 3.0),
    )


@with_error_handling
def post_overtime_pattern_metric(service: WorkforceAnalyticsService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return 200, service.calculate_overtime_pattern(
        overtime_hours=payload.get('overtime_hours') or [],
        expected_hours=payload.get('expected_hours', 8.0),
    )


@with_error_handling
def post_attrition_risk_metric(service: WorkforceAnalyticsService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return 200, service.calculate_attrition_risk(
        engagement_score=payload.get('engagement_score'),
        tenure_months=payload.get('tenure_months'),
        absenteeism_rate=payload.get('absenteeism_rate'),
        overtime_ratio=payload.get('overtime_ratio'),
    )


@with_error_handling
def post_burnout_index_metric(service: WorkforceAnalyticsService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    return 200, service.calculate_burnout_index(
        engagement_score=payload.get('engagement_score'),
        overtime_hours=payload.get('overtime_hours'),
        absent_days=payload.get('absent_days'),
        working_days=payload.get('working_days'),
    )
