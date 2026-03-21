from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from api_contract import error_response, pagination_payload, success_response
from background_jobs import BackgroundJobError, BackgroundJobService
from resilience import new_trace_id


_ERROR_STATUS_BY_CODE = {
    'JOB_NOT_FOUND': 404,
    'UNKNOWN_JOB_TYPE': 422,
    'FORBIDDEN': 403,
    'INVALID_JOB_STATE': 409,
    'TENANT_SCOPE_VIOLATION': 403,
    'QUEUE_OVERFLOW': 429,
}


def _error_response(code: str, message: str, *, details: list[dict[str, Any]] | None = None, trace_id: str) -> tuple[int, dict[str, Any]]:
    return error_response(_ERROR_STATUS_BY_CODE.get(code, 400), code, message, request_id=trace_id, details=details)


def with_error_handling(handler: Callable[..., tuple[int, dict[str, Any]]]) -> Callable[..., tuple[int, dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        trace_id = kwargs.pop('trace_id', None) or new_trace_id()
        service = args[0]
        operation = getattr(handler, '__name__', 'background_jobs.operation')
        started = perf_counter()
        try:
            status, payload = handler(*args, trace_id=trace_id, **kwargs)
            pagination = payload.pop('_pagination', None) if isinstance(payload, dict) else None
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={'status': status})
            return success_response(status, payload, request_id=trace_id, pagination=pagination)
        except BackgroundJobError as exc:
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': exc.status_code, 'code': exc.code})
            return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)

    return wrapped


@with_error_handling
def post_background_job(service: BackgroundJobService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    job = service.enqueue_job(
        tenant_id=str(payload['tenant_id']),
        job_type=str(payload['job_type']),
        payload=dict(payload.get('payload') or {}),
        scheduled_at=payload.get('scheduled_at'),
        actor_id=payload.get('actor', {}).get('id') if isinstance(payload.get('actor'), dict) else None,
        actor_type=payload.get('actor', {}).get('type', 'service') if isinstance(payload.get('actor'), dict) else 'service',
        trace_id=trace_id,
        correlation_id=payload.get('request_id') or trace_id,
        idempotency_key=payload.get('idempotency_key'),
    )
    return 202, job.to_dict()


@with_error_handling
def get_background_job(service: BackgroundJobService, job_id: str, query: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    job = service.get_job(job_id, tenant_id=str(query['tenant_id']), actor_role=str(query.get('actor_role') or 'Admin'))
    return 200, job.to_dict()


@with_error_handling
def get_background_jobs(service: BackgroundJobService, query: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    rows = service.list_jobs(tenant_id=str(query['tenant_id']), actor_role=str(query.get('actor_role') or 'Admin'), status=query.get('status'))
    return 200, {
        'data': [row.to_dict() for row in rows],
        '_pagination': pagination_payload(count=len(rows), limit=len(rows), cursor=None, next_cursor=None),
    }


@with_error_handling
def post_background_job_retry(service: BackgroundJobService, job_id: str, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    job = service.retry_job(job_id, tenant_id=str(payload['tenant_id']), actor_role=str(payload.get('actor_role') or 'Admin'), trace_id=trace_id)
    return 202, job.to_dict()


@with_error_handling
def post_background_job_cancel(service: BackgroundJobService, job_id: str, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    job = service.cancel_job(job_id, tenant_id=str(payload['tenant_id']), actor_role=str(payload.get('actor_role') or 'Admin'))
    return 200, job.to_dict()
