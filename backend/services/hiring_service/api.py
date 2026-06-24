from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from api_contract import error_payload, success_response

from .service import HiringService, HiringValidationError


SERVICE_NAME = 'hiring-service'


def _error_status(exc: HiringValidationError) -> int:
    message = str(exc)
    if message.endswith('does not exist'):
        return 404
    if 'cannot be deleted' in message:
        return 409
    return 422


def _error_response(exc: HiringValidationError, *, trace_id: str) -> tuple[int, dict]:
    status = _error_status(exc)
    return status, error_payload(
        'NOT_FOUND' if status == 404 else 'VALIDATION_ERROR' if status == 422 else 'CONFLICT',
        str(exc),
        trace_id,
        service=SERVICE_NAME,
    )


def _invalid_payload(trace_id: str, message: str = 'Invalid request payload.') -> tuple[int, dict]:
    return 422, error_payload('VALIDATION_ERROR', message, trace_id, service=SERVICE_NAME)


def _parse_limit(params: dict) -> int | None:
    limit = params.get('limit')
    if limit is None:
        return None
    return int(limit)


def _ensure_object(payload: dict, service: HiringService, operation: str, trace_id: str, started: float) -> tuple[int, dict] | None:
    if isinstance(payload, dict):
        return None
    service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={'status': 422})
    return _invalid_payload(trace_id, 'Request body must be an object')


def _success(status: int, data: object, *, trace_id: str, service: HiringService, pagination: dict | None = None) -> tuple[int, dict]:
    return success_response(status, data, request_id=trace_id, pagination=pagination, tenant_id=service.tenant_id, service=SERVICE_NAME)


def post_job_postings(service: HiringService, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    invalid = _ensure_object(payload, service, 'post_job_postings', trace_id, started)
    if invalid:
        return invalid
    try:
        created = service.create_job_posting(payload)
        service.observability.track('post_job_postings', trace_id=trace_id, started_at=started, success=True, context={'status': 201})
        return _success(201, service.get_job_posting(created['job_posting_id']), trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('post_job_postings', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def get_job_posting(service: HiringService, job_posting_id: str, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    try:
        payload = service.get_job_posting(job_posting_id)
        service.observability.track('get_job_posting', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return _success(200, payload, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('get_job_posting', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def get_job_postings(service: HiringService, query: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    params = query or {}
    try:
        limit = _parse_limit(params)
        rows = service.list_job_postings(
            status=params.get('status'),
            department_id=params.get('department_id'),
            limit=limit,
            cursor=params.get('cursor'),
        )
        next_cursor = rows[-1]['job_posting_id'] if limit is not None and len(rows) == limit else None
        service.observability.track('get_job_postings', trace_id=trace_id, started_at=started, success=True, context={'status': 200, 'count': len(rows)})
        return _success(
            200,
            rows,
            trace_id=trace_id,
            service=service,
            pagination={
                'limit': limit,
                'cursor': params.get('cursor'),
                'next_cursor': next_cursor,
                'count': len(rows),
            },
        )
    except (TypeError, ValueError):
        service.observability.track('get_job_postings', trace_id=trace_id, started_at=started, success=False, context={'status': 422})
        return _invalid_payload(trace_id, 'limit must be an integer')
    except HiringValidationError as exc:
        service.observability.track('get_job_postings', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def patch_job_posting(service: HiringService, job_posting_id: str, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    invalid = _ensure_object(payload, service, 'patch_job_posting', trace_id, started)
    if invalid:
        return invalid
    try:
        updated = service.update_job_posting(job_posting_id, payload)
        service.observability.track('patch_job_posting', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return _success(200, service.get_job_posting(updated['job_posting_id']), trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('patch_job_posting', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def delete_job_posting(service: HiringService, job_posting_id: str, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    try:
        deleted = service.delete_job_posting(job_posting_id)
        service.observability.track('delete_job_posting', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return _success(200, deleted, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('delete_job_posting', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def post_candidates(service: HiringService, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    invalid = _ensure_object(payload, service, 'post_candidates', trace_id, started)
    if invalid:
        return invalid
    try:
        created = service.create_candidate(payload)
        service.observability.track('post_candidates', trace_id=trace_id, started_at=started, success=True, context={'status': 201})
        return _success(201, created, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('post_candidates', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def post_candidates_import_linkedin(service: HiringService, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    invalid = _ensure_object(payload, service, 'post_candidates_import_linkedin', trace_id, started)
    if invalid:
        return invalid
    try:
        imported = service.import_candidates_from_linkedin(payload)
        service.observability.track('post_candidates_import_linkedin', trace_id=trace_id, started_at=started, success=True, context={'status': 201, 'count': len(imported['imported'])})
        return _success(201, imported, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('post_candidates_import_linkedin', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def get_candidate(service: HiringService, candidate_id: str, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    try:
        payload = service.get_candidate(candidate_id)
        service.observability.track('get_candidate', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return _success(200, payload, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('get_candidate', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def get_candidates(service: HiringService, query: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    params = query or {}
    try:
        limit = _parse_limit(params)
        rows = service.list_candidates(
            job_posting_id=params.get('job_posting_id'),
            status=params.get('status'),
            limit=limit,
            cursor=params.get('cursor'),
        )
        next_cursor = rows[-1]['candidate_id'] if limit is not None and len(rows) == limit else None
        service.observability.track('get_candidates', trace_id=trace_id, started_at=started, success=True, context={'status': 200, 'count': len(rows)})
        return _success(
            200,
            rows,
            trace_id=trace_id,
            service=service,
            pagination={'limit': limit, 'cursor': params.get('cursor'), 'next_cursor': next_cursor, 'count': len(rows)},
        )
    except (TypeError, ValueError):
        service.observability.track('get_candidates', trace_id=trace_id, started_at=started, success=False, context={'status': 422})
        return _invalid_payload(trace_id, 'limit must be an integer')
    except HiringValidationError as exc:
        service.observability.track('get_candidates', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def patch_candidate(service: HiringService, candidate_id: str, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    invalid = _ensure_object(payload, service, 'patch_candidate', trace_id, started)
    if invalid:
        return invalid
    try:
        updated = service.update_candidate(candidate_id, payload)
        service.observability.track('patch_candidate', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return _success(200, updated, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('patch_candidate', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def get_candidate_pipeline(service: HiringService, query: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    params = query or {}
    try:
        rows = service.list_candidate_pipeline_view(
            pipeline_stage=params.get('pipeline_stage') or params.get('status'),
            department_id=params.get('department_id'),
            job_posting_id=params.get('job_posting_id'),
        )
        service.observability.track('get_candidate_pipeline', trace_id=trace_id, started_at=started, success=True, context={'status': 200, 'count': len(rows)})
        return _success(200, rows, trace_id=trace_id, service=service, pagination={'count': len(rows)})
    except HiringValidationError as exc:
        service.observability.track('get_candidate_pipeline', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def post_interviews(service: HiringService, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    invalid = _ensure_object(payload, service, 'post_interviews', trace_id, started)
    if invalid:
        return invalid
    try:
        created = service.create_interview(payload)
        service.observability.track('post_interviews', trace_id=trace_id, started_at=started, success=True, context={'status': 201})
        return _success(201, created, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('post_interviews', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def post_interviews_google_calendar(service: HiringService, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    invalid = _ensure_object(payload, service, 'post_interviews_google_calendar', trace_id, started)
    if invalid:
        return invalid
    try:
        created = service.schedule_interview_with_google_calendar(payload)
        service.observability.track('post_interviews_google_calendar', trace_id=trace_id, started_at=started, success=True, context={'status': 201})
        return _success(201, created, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('post_interviews_google_calendar', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def get_interview(service: HiringService, interview_id: str, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    try:
        payload = service.get_interview(interview_id)
        service.observability.track('get_interview', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return _success(200, payload, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('get_interview', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def get_interviews(service: HiringService, query: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    params = query or {}
    try:
        limit = _parse_limit(params)
        rows = service.list_interviews(
            candidate_id=params.get('candidate_id'),
            status=params.get('status'),
            limit=limit,
            cursor=params.get('cursor'),
        )
        next_cursor = rows[-1]['interview_id'] if limit is not None and len(rows) == limit else None
        service.observability.track('get_interviews', trace_id=trace_id, started_at=started, success=True, context={'status': 200, 'count': len(rows)})
        return _success(
            200,
            rows,
            trace_id=trace_id,
            service=service,
            pagination={'limit': limit, 'cursor': params.get('cursor'), 'next_cursor': next_cursor, 'count': len(rows)},
        )
    except (TypeError, ValueError):
        service.observability.track('get_interviews', trace_id=trace_id, started_at=started, success=False, context={'status': 422})
        return _invalid_payload(trace_id, 'limit must be an integer')
    except HiringValidationError as exc:
        service.observability.track('get_interviews', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def patch_interview(service: HiringService, interview_id: str, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    invalid = _ensure_object(payload, service, 'patch_interview', trace_id, started)
    if invalid:
        return invalid
    try:
        updated = service.update_interview(interview_id, payload)
        service.observability.track('patch_interview', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return _success(200, updated, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('patch_interview', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def post_candidate_hire(service: HiringService, candidate_id: str, payload: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    body = payload or {}
    invalid = _ensure_object(body, service, 'post_candidate_hire', trace_id, started)
    if invalid:
        return invalid
    try:
        hired = service.mark_candidate_hired(candidate_id, body)
        service.observability.track('post_candidate_hire', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return _success(200, hired, trace_id=trace_id, service=service)
    except HiringValidationError as exc:
        service.observability.track('post_candidate_hire', trace_id=trace_id, started_at=started, success=False, context={'status': _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)
