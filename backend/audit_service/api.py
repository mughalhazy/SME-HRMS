from __future__ import annotations

from uuid import uuid4

from api_contract import error_response, success_response

from .service import AuditQueryError, get_audit_service


def get_audit_records(query: dict[str, str] | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace = trace_id or uuid4().hex
    params = query or {}
    tenant_id = params.get('tenant_id')
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return error_response(422, 'VALIDATION_ERROR', 'tenant_id is required', request_id=trace, details=[{'field': 'tenant_id', 'reason': 'must be a non-empty string'}])

    try:
        limit = int(params.get('limit', 25))
    except (TypeError, ValueError):
        return error_response(422, 'VALIDATION_ERROR', 'limit must be an integer', request_id=trace, details=[{'field': 'limit', 'reason': 'must be an integer'}])

    try:
        rows, pagination = get_audit_service().list_records(
            tenant_id=tenant_id,
            actor_id=params.get('actor_id'),
            actor_type=params.get('actor_type'),
            entity=params.get('entity'),
            entity_id=params.get('entity_id'),
            action=params.get('action'),
            timestamp_from=params.get('timestamp_from'),
            timestamp_to=params.get('timestamp_to'),
            limit=limit,
            cursor=params.get('cursor'),
        )
    except AuditQueryError as exc:
        return error_response(422, 'VALIDATION_ERROR', str(exc), request_id=trace)

    return success_response(200, rows, request_id=trace, pagination=pagination)
