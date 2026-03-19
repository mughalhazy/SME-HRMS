from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from .service import HiringService, HiringValidationError


def _error_status(exc: HiringValidationError) -> int:
    message = str(exc)
    if message.endswith("does not exist"):
        return 404
    if "cannot be deleted" in message:
        return 409
    return 422


def _error_response(exc: HiringValidationError, *, trace_id: str) -> tuple[int, dict]:
    status = _error_status(exc)
    return (
        status,
        {
            "error": {
                "code": "NOT_FOUND" if status == 404 else "VALIDATION_ERROR" if status == 422 else "CONFLICT",
                "message": str(exc),
                "details": [],
                "traceId": trace_id,
            }
        },
    )


def _invalid_payload(trace_id: str, message: str = "Invalid request payload.") -> tuple[int, dict]:
    return (
        422,
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "details": [],
                "traceId": trace_id,
            }
        },
    )


def post_job_postings(service: HiringService, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    if not isinstance(payload, dict):
        service.observability.track("post_job_postings", trace_id=trace_id, started_at=started, success=False, context={"status": 422})
        return _invalid_payload(trace_id, "Request body must be an object")
    try:
        created = service.create_job_posting(payload)
        service.observability.track("post_job_postings", trace_id=trace_id, started_at=started, success=True, context={"status": 201})
        return 201, {"data": service.get_job_posting(created["job_posting_id"])}
    except HiringValidationError as exc:
        service.observability.track("post_job_postings", trace_id=trace_id, started_at=started, success=False, context={"status": _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def get_job_posting(service: HiringService, job_posting_id: str, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    try:
        payload = service.get_job_posting(job_posting_id)
        service.observability.track("get_job_posting", trace_id=trace_id, started_at=started, success=True, context={"status": 200})
        return 200, {"data": payload}
    except HiringValidationError as exc:
        service.observability.track("get_job_posting", trace_id=trace_id, started_at=started, success=False, context={"status": _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def get_job_postings(service: HiringService, query: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    params = query or {}
    try:
        limit = params.get("limit")
        if limit is not None:
            limit = int(limit)
        rows = service.list_job_postings(
            status=params.get("status"),
            department_id=params.get("department_id"),
            limit=limit,
            cursor=params.get("cursor"),
        )
        next_cursor = rows[-1]["job_posting_id"] if limit is not None and len(rows) == limit else None
        service.observability.track("get_job_postings", trace_id=trace_id, started_at=started, success=True, context={"status": 200, "count": len(rows)})
        return (
            200,
            {
                "data": rows,
                "pagination": {
                    "limit": limit,
                    "cursor": params.get("cursor"),
                    "next_cursor": next_cursor,
                    "count": len(rows),
                },
            },
        )
    except (TypeError, ValueError):
        service.observability.track("get_job_postings", trace_id=trace_id, started_at=started, success=False, context={"status": 422})
        return _invalid_payload(trace_id, "limit must be an integer")
    except HiringValidationError as exc:
        service.observability.track("get_job_postings", trace_id=trace_id, started_at=started, success=False, context={"status": _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def patch_job_posting(service: HiringService, job_posting_id: str, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    if not isinstance(payload, dict):
        service.observability.track("patch_job_posting", trace_id=trace_id, started_at=started, success=False, context={"status": 422})
        return _invalid_payload(trace_id, "Request body must be an object")
    try:
        updated = service.update_job_posting(job_posting_id, payload)
        service.observability.track("patch_job_posting", trace_id=trace_id, started_at=started, success=True, context={"status": 200})
        return 200, {"data": service.get_job_posting(updated["job_posting_id"])}
    except HiringValidationError as exc:
        service.observability.track("patch_job_posting", trace_id=trace_id, started_at=started, success=False, context={"status": _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)


def delete_job_posting(service: HiringService, job_posting_id: str, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    try:
        deleted = service.delete_job_posting(job_posting_id)
        service.observability.track("delete_job_posting", trace_id=trace_id, started_at=started, success=True, context={"status": 200})
        return 200, {"data": deleted}
    except HiringValidationError as exc:
        service.observability.track("delete_job_posting", trace_id=trace_id, started_at=started, success=False, context={"status": _error_status(exc)})
        return _error_response(exc, trace_id=trace_id)
