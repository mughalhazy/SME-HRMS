from __future__ import annotations

from typing import Any, Callable

from workflow_service import WorkflowService, WorkflowServiceError


def resolve_workflow_action(
    *,
    workflow_service: WorkflowService,
    workflow_id: str,
    tenant_id: str,
    action: str,
    actor_id: str,
    actor_type: str,
    actor_role: str | None,
    comment: str | None,
    trace_id: str | None = None,
    map_error: Callable[[WorkflowServiceError], Exception],
    invalid_action: Callable[[str], Exception],
) -> dict[str, Any]:
    handler = _resolve_action_handler(workflow_service, action, invalid_action=invalid_action)
    try:
        return handler(
            workflow_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_role=actor_role,
            comment=comment,
            trace_id=trace_id,
        )
    except WorkflowServiceError as exc:
        raise map_error(exc) from exc


def require_terminal_workflow_result(
    workflow: dict[str, Any],
    *,
    action: str,
    on_mismatch: Callable[[str | None, str], Exception],
    invalid_action: Callable[[str], Exception],
) -> str:
    expected = _expected_terminal_result(action, invalid_action=invalid_action)
    terminal_result = workflow.get("metadata", {}).get("terminal_result")
    if terminal_result != expected:
        raise on_mismatch(terminal_result, expected)
    return expected


def _resolve_action_handler(
    workflow_service: WorkflowService,
    action: str,
    *,
    invalid_action: Callable[[str], Exception],
):
    if action == "approve":
        return workflow_service.approve_step
    if action == "reject":
        return workflow_service.reject_step
    raise invalid_action(action)


def _expected_terminal_result(action: str, *, invalid_action: Callable[[str], Exception]) -> str:
    if action == "approve":
        return "approved"
    if action == "reject":
        return "rejected"
    raise invalid_action(action)
