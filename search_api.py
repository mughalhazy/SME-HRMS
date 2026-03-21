from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from api_contract import error_response, success_response

from search_service import SearchIndexingService, SearchServiceError


SERVICE_NAME = 'search-service'


def _error(exc: SearchServiceError, *, trace_id: str, service: SearchIndexingService, tenant_id: str | None = None) -> tuple[int, dict]:
    return error_response(
        exc.status_code,
        exc.code,
        exc.message,
        request_id=trace_id,
        details=exc.details,
        tenant_id=tenant_id,
        service=SERVICE_NAME,
    )


def _parse_limit(query: dict[str, object]) -> int | None:
    limit = query.get('limit')
    if limit is None:
        return None
    return int(limit)


def _parse_multi(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(',') if part.strip()]


def get_search(service: SearchIndexingService, query: dict | None = None, *, trace_id: str | None = None) -> tuple[int, dict]:
    trace = trace_id or uuid4().hex
    started = perf_counter()
    params = query or {}
    tenant_id = params.get('tenant_id')
    try:
        if not tenant_id:
            raise SearchServiceError(422, 'VALIDATION_ERROR', 'tenant_id is required', details=[{'field': 'tenant_id', 'reason': 'is required'}])
        payload = service.search(
            tenant_id=str(tenant_id),
            q=params.get('q') or params.get('query'),
            department_id=str(params['department_id']) if params.get('department_id') is not None else None,
            role_id=str(params['role_id']) if params.get('role_id') is not None else None,
            status=str(params['status']) if params.get('status') is not None else None,
            entity_types=_parse_multi(params.get('entity_type')),
            domains=_parse_multi(params.get('domain')),
            limit=_parse_limit(params),
            cursor=str(params['cursor']) if params.get('cursor') is not None else None,
            sort=str(params['sort']) if params.get('sort') is not None else None,
        )
        service.query_audit['last_api_call'] = {
            'operation': 'get_search',
            'request_id': trace,
            'duration_ms': round((perf_counter() - started) * 1000, 3),
        }
        return success_response(
            200,
            payload['items'],
            request_id=trace,
            pagination=payload['_pagination'],
            tenant_id=str(tenant_id),
            service=SERVICE_NAME,
        )
    except (TypeError, ValueError) as exc:
        error = SearchServiceError(422, 'VALIDATION_ERROR', 'limit must be an integer')
        service.query_audit['last_api_error'] = {'operation': 'get_search', 'request_id': trace, 'message': str(exc)}
        return _error(error, trace_id=trace, service=service, tenant_id=str(tenant_id) if tenant_id else None)
    except SearchServiceError as exc:
        service.query_audit['last_api_error'] = {'operation': 'get_search', 'request_id': trace, 'message': exc.message}
        return _error(exc, trace_id=trace, service=service, tenant_id=str(tenant_id) if tenant_id else None)


def get_employee_search(service: SearchIndexingService, query: dict | None = None, *, trace_id: str | None = None) -> tuple[int, dict]:
    params = dict(query or {})
    params['entity_type'] = 'employee'
    return get_search(service, params, trace_id=trace_id)


def get_candidate_search(service: SearchIndexingService, query: dict | None = None, *, trace_id: str | None = None) -> tuple[int, dict]:
    params = dict(query or {})
    params['entity_type'] = 'candidate'
    return get_search(service, params, trace_id=trace_id)


def get_document_search(service: SearchIndexingService, query: dict | None = None, *, trace_id: str | None = None) -> tuple[int, dict]:
    params = dict(query or {})
    params['entity_type'] = 'document'
    return get_search(service, params, trace_id=trace_id)
