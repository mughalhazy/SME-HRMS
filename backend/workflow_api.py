from __future__ import annotations

from uuid import uuid4

from api_contract import error_payload, success_response
from workflow_service import WorkflowService, WorkflowServiceError


def _error(exc: WorkflowServiceError, trace_id: str) -> tuple[int, dict]:
    return exc.status_code, error_payload(exc.code, exc.message, trace_id, exc.details)


def get_workflow_instance(service: WorkflowService, workflow_id: str, *, tenant_id: str, actor_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    try:
        payload = service.get_instance(workflow_id, tenant_id=tenant_id, actor_id=actor_id)
        return success_response(200, payload, request_id=trace_id)
    except WorkflowServiceError as exc:
        return _error(exc, trace_id)


def get_workflow_inbox(service: WorkflowService, *, tenant_id: str, actor_id: str, actor_role: str | None = None, query: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    params = query or {}
    try:
        payload = service.list_inbox(tenant_id=tenant_id, actor_id=actor_id, actor_role=actor_role, status=params.get("status", "pending"))
        return success_response(200, payload["data"], request_id=trace_id, pagination={"count": len(payload["data"])})
    except WorkflowServiceError as exc:
        return _error(exc, trace_id)


def post_workflow_approve(service: WorkflowService, workflow_id: str, *, tenant_id: str, actor_id: str, actor_type: str, actor_role: str | None = None, payload: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    body = payload or {}
    try:
        data = service.approve_step(workflow_id, tenant_id=tenant_id, actor_id=actor_id, actor_type=actor_type, actor_role=actor_role, comment=body.get("comment"), trace_id=trace_id)
        return success_response(200, data, request_id=trace_id)
    except WorkflowServiceError as exc:
        return _error(exc, trace_id)


def post_workflow_reject(service: WorkflowService, workflow_id: str, *, tenant_id: str, actor_id: str, actor_type: str, actor_role: str | None = None, payload: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    body = payload or {}
    try:
        data = service.reject_step(workflow_id, tenant_id=tenant_id, actor_id=actor_id, actor_type=actor_type, actor_role=actor_role, comment=body.get("comment"), trace_id=trace_id)
        return success_response(200, data, request_id=trace_id)
    except WorkflowServiceError as exc:
        return _error(exc, trace_id)


def post_workflow_delegate(service: WorkflowService, workflow_id: str, *, tenant_id: str, actor_id: str, actor_role: str | None = None, payload: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    body = payload or {}
    try:
        data = service.delegate_step(workflow_id, tenant_id=tenant_id, actor_id=actor_id, actor_role=actor_role, delegate_to=str(body["delegate_to"]), trace_id=trace_id)
        return success_response(200, data, request_id=trace_id)
    except (KeyError, TypeError, ValueError):
        return 422, error_payload("VALIDATION_ERROR", "delegate_to is required", trace_id)
    except WorkflowServiceError as exc:
        return _error(exc, trace_id)


def post_workflow_escalate(service: WorkflowService, *, tenant_id: str, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    try:
        payload = service.escalate_due_workflows(tenant_id=tenant_id, trace_id=trace_id)
        return success_response(200, payload, request_id=trace_id, pagination={"count": len(payload)})
    except WorkflowServiceError as exc:
        return _error(exc, trace_id)
