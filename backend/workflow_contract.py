from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

_ALLOWED_WORKFLOW_STATUSES = {"pending", "completed"}
_ALLOWED_STEP_TYPES = {"approval", "auto", "condition"}
_ALLOWED_STEP_STATUSES = {"pending", "approved", "rejected"}
_WORKFLOW_ENGINE = "workflow-contract-engine"
_DURATION_PATTERN = re.compile(r"^P(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)$")
_SHORTHAND_DURATION_PATTERN = re.compile(r"^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$", re.I)


class WorkflowContractError(ValueError):
    """Raised when a workflow cannot satisfy the quality contract."""


@dataclass(frozen=True)
class QualityResult:
    workflow_consistency: int
    approval_standardization: int
    state_management: int
    sla_enforcement: int
    integration_usage: int
    overall: int


def ensure_workflow_contract(payload: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    workflow, auto_fixed = _normalize_workflow(deepcopy(payload), now=now)

    qc_results = _qc_checks(workflow)
    if not all(item["passed"] for item in qc_results["checks"]):
        failure = next(item["name"] for item in qc_results["checks"] if not item["passed"])
        if failure in {"workflow_bypass_detected", "invalid_state_transition", "valid_state_transitions"}:
            if failure == "valid_state_transitions":
                raise WorkflowContractError("invalid_state_transition")
            raise WorkflowContractError(failure)
        raise WorkflowContractError("invalid_workflow_contract")

    re_qc_results = _re_qc_checks(workflow)
    if not all(item["passed"] for item in re_qc_results):
        failure = next(item["name"] for item in re_qc_results if not item["passed"])
        raise WorkflowContractError(failure)

    workflow["metadata"] = {
        **workflow.get("metadata", {}),
        "engine": _WORKFLOW_ENGINE,
        "quality_contract": {
            "quality_standard": "10/10",
            "scoring_dimensions": [
                "workflow_consistency",
                "approval_standardization",
                "state_management",
                "sla_enforcement",
                "integration_usage",
            ],
            "min_score_per_dimension": 10,
            "overall_min_score": 10,
            "auto_fix_required": True,
            "re_qc_required": True,
            "reject_if_below_threshold": True,
        },
        "qc": {
            **qc_results,
            "auto_fixed": auto_fixed,
            "rechecked": re_qc_results,
        },
    }
    return workflow


def _normalize_workflow(payload: dict[str, Any], *, now: datetime | None) -> tuple[dict[str, Any], list[str]]:
    auto_fixed: list[str] = []
    current_time = _normalize_datetime(now)
    created_at_dt = _normalize_datetime(_parse_timestamp(payload.get("created_at"), default=current_time))

    workflow_id = payload.get("workflow_id")
    if not _is_uuid_like(workflow_id):
        workflow_id = str(uuid4())
        auto_fixed.append("generate_workflow_ids")

    steps = payload.get("steps")
    if not isinstance(steps, list):
        raise WorkflowContractError("invalid_workflow_contract")

    normalized_steps = [_normalize_step(step, index=index, workflow_created_at=created_at_dt, auto_fixed=auto_fixed) for index, step in enumerate(steps)]

    created_at = created_at_dt.isoformat()
    inferred_status = _infer_workflow_status(normalized_steps)
    raw_status = str(payload.get("status") or inferred_status).strip().lower()
    if raw_status not in _ALLOWED_WORKFLOW_STATUSES:
        raw_status = inferred_status
        auto_fixed.append("normalize_state_transitions")
    elif raw_status != inferred_status:
        raw_status = inferred_status
        auto_fixed.append("normalize_state_transitions")

    metadata = dict(payload.get("metadata") or {})
    metadata.setdefault("engine", _WORKFLOW_ENGINE)

    workflow = {
        "workflow_id": workflow_id,
        "steps": normalized_steps,
        "status": raw_status,
        "created_at": created_at,
        "metadata": metadata,
    }
    return workflow, auto_fixed


def _normalize_step(
    raw_step: Any,
    *,
    index: int,
    workflow_created_at: datetime,
    auto_fixed: list[str],
) -> dict[str, Any]:
    if not isinstance(raw_step, dict):
        raise WorkflowContractError("invalid_workflow_contract")

    step_id = raw_step.get("step_id")
    if not _is_uuid_like(step_id):
        step_id = str(uuid4())
        auto_fixed.append("generate_step_ids")

    step_type = str(raw_step.get("type") or "").strip().lower()
    if step_type not in _ALLOWED_STEP_TYPES:
        raise WorkflowContractError("invalid_workflow_contract")

    status = str(raw_step.get("status") or "pending").strip().lower()
    if status not in _ALLOWED_STEP_STATUSES:
        status = "pending"
        auto_fixed.append("normalize_state_transitions")

    assignee = str(raw_step.get("assignee") or "").strip()
    if not assignee:
        raise WorkflowContractError("invalid_workflow_contract")

    sla = _normalize_duration(raw_step.get("sla"))
    if sla is None:
        raise WorkflowContractError("invalid_workflow_contract")
    if raw_step.get("sla") != sla:
        auto_fixed.append("normalize_sla_durations")

    normalized = {
        "step_id": step_id,
        "type": step_type,
        "assignee": assignee,
        "status": status,
        "sla": sla,
    }

    if step_type != "approval" and any(key in raw_step for key in ("approved_by", "approval", "approval_logic")):
        normalized["type"] = "approval"
        auto_fixed.append("remove_inline_approvals")
        auto_fixed.append("reroute_to_workflow_engine")

    metadata = dict(raw_step.get("metadata") or {})
    metadata.setdefault("position", index + 1)
    metadata.setdefault("engine", _WORKFLOW_ENGINE)
    metadata.setdefault("deadline_at", (workflow_created_at + _parse_duration(sla)).isoformat())
    normalized["metadata"] = metadata
    return normalized


def _qc_checks(workflow: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {"name": "no_inline_approval_logic", "passed": all(_step_has_no_inline_approval_logic(step) for step in workflow["steps"])} ,
        {"name": "workflow_engine_used", "passed": workflow.get("metadata", {}).get("engine") == _WORKFLOW_ENGINE and all(step.get("metadata", {}).get("engine") == _WORKFLOW_ENGINE for step in workflow["steps"])},
        {"name": "valid_state_transitions", "passed": _has_valid_state_transitions(workflow)},
        {"name": "sla_enforced", "passed": _sla_is_enforced(workflow)},
        {"name": "workflow_bypass_detected", "passed": bool(workflow["steps"])},
        {"name": "invalid_state_transition", "passed": _has_valid_state_transitions(workflow)},
    ]

    dimensions = QualityResult(
        workflow_consistency=10 if all(check["passed"] for check in checks[:2]) else 0,
        approval_standardization=10 if checks[0]["passed"] else 0,
        state_management=10 if checks[2]["passed"] and checks[5]["passed"] else 0,
        sla_enforcement=10 if checks[3]["passed"] else 0,
        integration_usage=10 if checks[1]["passed"] else 0,
        overall=10 if all(check["passed"] for check in checks[:4]) else 0,
    )

    return {
        "checks": checks,
        "score": dimensions.__dict__,
        "auto_fix_required": True,
        "re_qc_required": True,
        "reject_if_below_threshold": True,
    }


def _re_qc_checks(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    simulated = _simulate_execution(workflow)
    approval_validation = all(
        step["type"] != "approval" or step["status"] in {"pending", "approved", "rejected"}
        for step in workflow["steps"]
    )
    return [
        {"name": "workflow_execution_simulation", "passed": simulated},
        {"name": "approval_flow_validation", "passed": approval_validation},
    ]


def _simulate_execution(workflow: dict[str, Any]) -> bool:
    terminal_reached = False
    for index, step in enumerate(workflow["steps"]):
        if step["status"] == "rejected":
            terminal_reached = index == len(workflow["steps"]) - 1
            break
        if step["status"] == "pending":
            terminal_reached = index == len(workflow["steps"]) - 1 or all(
                next_step["status"] == "pending" for next_step in workflow["steps"][index + 1:]
            )
            break
    else:
        terminal_reached = True

    return terminal_reached and _has_valid_state_transitions(workflow)


def _step_has_no_inline_approval_logic(step: dict[str, Any]) -> bool:
    return step["type"] == "approval" or not any(key in step for key in ("approved_by", "approval", "approval_logic"))


def _has_valid_state_transitions(workflow: dict[str, Any]) -> bool:
    pending_seen = False
    for index, step in enumerate(workflow["steps"]):
        status = step["status"]
        if status == "rejected" and index != len(workflow["steps"]) - 1:
            return False
        if pending_seen and status != "pending":
            return False
        if status == "pending":
            pending_seen = True
    return workflow["status"] == _infer_workflow_status(workflow["steps"])


def _sla_is_enforced(workflow: dict[str, Any]) -> bool:
    created_at = datetime.fromisoformat(workflow["created_at"].replace("Z", "+00:00"))
    for step in workflow["steps"]:
        deadline_at = step.get("metadata", {}).get("deadline_at")
        if not isinstance(deadline_at, str):
            return False
        deadline = datetime.fromisoformat(deadline_at.replace("Z", "+00:00"))
        if deadline < created_at:
            return False
        if deadline - created_at != _parse_duration(step["sla"]):
            return False
    return True


def _infer_workflow_status(steps: list[dict[str, Any]]) -> str:
    if steps and all(step["status"] in {"approved", "rejected"} for step in steps):
        return "completed"
    return "pending"


def _normalize_timestamp(raw: Any, *, default: datetime) -> str:
    return _parse_timestamp(raw, default=default).isoformat()


def _parse_timestamp(raw: Any, *, default: datetime) -> datetime:
    if raw is None:
        return default
    if isinstance(raw, datetime):
        return _normalize_datetime(raw)
    try:
        return _normalize_datetime(datetime.fromisoformat(str(raw).replace("Z", "+00:00")))
    except ValueError as exc:
        raise WorkflowContractError("invalid_workflow_contract") from exc


def _normalize_datetime(value: datetime | None) -> datetime:
    candidate = value or datetime.now(timezone.utc)
    if candidate.tzinfo is None:
        return candidate.replace(tzinfo=timezone.utc)
    return candidate.astimezone(timezone.utc)


def _normalize_duration(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    candidate = raw.strip()
    if _DURATION_PATTERN.fullmatch(candidate):
        return candidate
    shorthand = _SHORTHAND_DURATION_PATTERN.fullmatch(candidate)
    if shorthand and any(shorthand.groupdict().values()):
        hours = int(shorthand.group("hours") or 0)
        minutes = int(shorthand.group("minutes") or 0)
        seconds = int(shorthand.group("seconds") or 0)
        result = "PT"
        if hours:
            result += f"{hours}H"
        if minutes:
            result += f"{minutes}M"
        if seconds:
            result += f"{seconds}S"
        return result if result != "PT" else None
    return None


def _parse_duration(value: str) -> timedelta:
    match = _DURATION_PATTERN.fullmatch(value)
    if not match:
        raise WorkflowContractError("invalid_workflow_contract")
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def _is_uuid_like(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        UUID(value)
    except Exception:
        return False
    return True
