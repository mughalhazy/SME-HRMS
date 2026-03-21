from __future__ import annotations

from dataclasses import asdict, dataclass, field
import time
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4

from event_contract import EventRegistry, emit_canonical_event
from notification_service import NotificationService, NotificationServiceError
from resilience import Observability
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id
from workflow_contract import ensure_workflow_contract


class WorkflowServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


@dataclass(slots=True)
class WorkflowDefinition:
    definition_id: str
    code: str
    tenant_id: str
    source_service: str
    subject_type: str
    description: str
    steps: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["created_at"] = self.created_at.isoformat()
        payload["updated_at"] = self.updated_at.isoformat()
        return payload


@dataclass(slots=True)
class WorkflowHistory:
    history_id: str
    workflow_id: str
    tenant_id: str
    action: str
    actor_id: str
    actor_type: str
    step_id: str | None
    from_status: str | None
    to_status: str
    details: dict[str, Any]
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["created_at"] = self.created_at.isoformat()
        return payload


@dataclass(slots=True)
class WorkflowInstance:
    workflow_id: str
    tenant_id: str
    definition_code: str
    source_service: str
    subject_type: str
    subject_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    created_by_type: str
    steps: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)
    history: list[WorkflowHistory] = field(default_factory=list)

    def to_contract_payload(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "steps": [
                {
                    "step_id": step["step_id"],
                    "type": step["type"],
                    "assignee": step["assignee"],
                    "status": step["status"],
                    "sla": step["sla"],
                    "metadata": dict(step.get("metadata") or {}),
                }
                for step in self.steps
            ],
            "metadata": {
                **self.metadata,
                "tenant_id": self.tenant_id,
                "definition_code": self.definition_code,
                "source_service": self.source_service,
                "subject_type": self.subject_type,
                "subject_id": self.subject_id,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        payload = ensure_workflow_contract(self.to_contract_payload(), now=self.created_at)
        payload.update(
            {
                "tenant_id": self.tenant_id,
                "definition_code": self.definition_code,
                "source_service": self.source_service,
                "subject_type": self.subject_type,
                "subject_id": self.subject_id,
                "created_by": {"id": self.created_by, "type": self.created_by_type},
                "updated_at": self.updated_at.isoformat(),
                "history": [item.to_dict() for item in self.history],
            }
        )
        return payload


class WorkflowService:
    """Centralized workflow engine aligned to the canonical workflow contract."""

    def __init__(self, *, notification_service: NotificationService | None = None) -> None:
        self.definitions: dict[tuple[str, str], WorkflowDefinition] = {}
        self.instances: dict[str, WorkflowInstance] = {}
        self.events: list[dict[str, Any]] = []
        self.notification_service = notification_service or NotificationService()
        self.observability = Observability("workflow-service")
        self.event_registry = EventRegistry()
        self._lock = RLock()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _trace(self, trace_id: str | None = None) -> str:
        return self.observability.trace_id(trace_id)

    def register_definition(
        self,
        *,
        tenant_id: str | None,
        code: str,
        source_service: str,
        subject_type: str,
        description: str,
        steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        tenant = normalize_tenant_id(tenant_id)
        now = self._now()
        normalized_steps = [self._normalize_definition_step(index=index, step=step) for index, step in enumerate(steps)]
        definition = self.definitions.get((tenant, code))
        if definition is None:
            definition = WorkflowDefinition(
                definition_id=str(uuid4()),
                code=code,
                tenant_id=tenant,
                source_service=source_service,
                subject_type=subject_type,
                description=description,
                steps=normalized_steps,
                created_at=now,
                updated_at=now,
            )
            self.definitions[(tenant, code)] = definition
        else:
            definition.source_service = source_service
            definition.subject_type = subject_type
            definition.description = description
            definition.steps = normalized_steps
            definition.updated_at = now
        return definition.to_dict()

    def start_workflow(
        self,
        *,
        tenant_id: str,
        definition_code: str,
        source_service: str,
        subject_type: str,
        subject_id: str,
        actor_id: str,
        actor_type: str,
        context: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        tenant = normalize_tenant_id(tenant_id)
        trace = self._trace(trace_id)
        started = self._now()
        started_at = time.perf_counter()
        definition = self._require_definition(tenant, definition_code)
        ctx = dict(context or {})
        with self._lock:
            existing = self._find_open_instance(tenant, definition_code, subject_id)
            if existing is not None:
                return existing.to_dict()
            now = self._now()
            steps = [self._instantiate_step(index=index, raw=step, context=ctx, workflow_created_at=now) for index, step in enumerate(definition.steps)]
            instance = WorkflowInstance(
                workflow_id=str(uuid4()),
                tenant_id=tenant,
                definition_code=definition_code,
                source_service=source_service,
                subject_type=subject_type,
                subject_id=subject_id,
                status="pending",
                created_at=now,
                updated_at=now,
                created_by=actor_id,
                created_by_type=actor_type,
                steps=steps,
                metadata={"context": ctx, "terminal_result": None},
            )
            self.instances[instance.workflow_id] = instance
            self._activate_next_steps(instance, actor_id=actor_id, actor_type=actor_type)
            self._append_history(instance, action="workflow_started", actor_id=actor_id, actor_type=actor_type, to_status=instance.status, details={"definition_code": definition_code})
            self._emit_workflow_event(
                "WorkflowInstanceCreated",
                instance,
                trace,
                {"definition_code": definition_code, "subject_id": subject_id, "source_service": source_service},
            )
            self._notify_assignment(instance, trace)
            self.observability.logger.audit(
                "workflow_instance_started",
                trace_id=trace,
                actor=actor_id,
                entity="WorkflowInstance",
                entity_id=instance.workflow_id,
                context={"tenant_id": tenant, "definition_code": definition_code, "subject_id": subject_id},
            )
            self.observability.track('workflow.start', trace_id=trace, started_at=started_at, success=True, context={'tenant_id': tenant, 'workflow_id': instance.workflow_id, 'workflow_definition': definition_code, 'status': instance.status, 'source_service': source_service, 'trace_stage': 'workflow'})
            return instance.to_dict()

    def get_instance(self, workflow_id: str, *, tenant_id: str, actor_id: str | None = None) -> dict[str, Any]:
        instance = self._require_instance(workflow_id)
        assert_tenant_access(instance.tenant_id, normalize_tenant_id(tenant_id))
        payload = instance.to_dict()
        if actor_id:
            payload["actor_view"] = {"actor_id": actor_id, "inbox_tasks": [step for step in payload["steps"] if self._step_visible_to_actor(step, actor_id=actor_id, actor_role=None)]}
        return payload

    def list_inbox(
        self,
        *,
        tenant_id: str,
        actor_id: str,
        actor_role: str | None = None,
        status: str = "pending",
    ) -> dict[str, Any]:
        tenant = normalize_tenant_id(tenant_id)
        rows: list[dict[str, Any]] = []
        with self._lock:
            for instance in self.instances.values():
                if instance.tenant_id != tenant:
                    continue
                for step in instance.steps:
                    if step["status"] != status:
                        continue
                    if not step.get("metadata", {}).get("active"):
                        continue
                    if self._step_visible_to_actor(step, actor_id=actor_id, actor_role=actor_role):
                        rows.append(
                            {
                                "workflow_id": instance.workflow_id,
                                "definition_code": instance.definition_code,
                                "source_service": instance.source_service,
                                "subject_type": instance.subject_type,
                                "subject_id": instance.subject_id,
                                "status": instance.status,
                                "created_at": instance.created_at.isoformat(),
                                "step": self._public_step(step),
                            }
                        )
        rows.sort(key=lambda item: (item["step"]["metadata"].get("deadline_at"), item["created_at"], item["workflow_id"]))
        return {"data": rows}

    def approve_step(
        self,
        workflow_id: str,
        *,
        tenant_id: str,
        actor_id: str,
        actor_type: str,
        actor_role: str | None,
        comment: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        return self._resolve_step(
            workflow_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_role=actor_role,
            action="approve",
            comment=comment,
            trace_id=trace_id,
        )

    def reject_step(
        self,
        workflow_id: str,
        *,
        tenant_id: str,
        actor_id: str,
        actor_type: str,
        actor_role: str | None,
        comment: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        return self._resolve_step(
            workflow_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_role=actor_role,
            action="reject",
            comment=comment,
            trace_id=trace_id,
        )

    def delegate_step(
        self,
        workflow_id: str,
        *,
        tenant_id: str,
        actor_id: str,
        actor_role: str | None,
        delegate_to: str,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        trace = self._trace(trace_id)
        started_at = time.perf_counter()
        with self._lock:
            instance = self._require_instance(workflow_id)
            assert_tenant_access(instance.tenant_id, normalize_tenant_id(tenant_id))
            step = self._current_actor_step(instance, actor_id=actor_id, actor_role=actor_role)
            if step is None:
                raise WorkflowServiceError(403, "FORBIDDEN", "No delegable task is assigned to this actor")
            metadata = step.setdefault("metadata", {})
            metadata.setdefault("delegations", []).append({"from": step["assignee"], "to": delegate_to, "at": self._now().isoformat(), "by": actor_id})
            step["assignee"] = delegate_to
            instance.updated_at = self._now()
            self._append_history(instance, action="step_delegated", actor_id=actor_id, actor_type="user", step_id=step["step_id"], from_status=step["status"], to_status=step["status"], details={"delegate_to": delegate_to})
            self._emit_workflow_event("WorkflowTaskDelegated", instance, trace, {"step_id": step["step_id"], "delegate_to": delegate_to})
            self._notify_assignment(instance, trace, target_steps=[step])
            self.observability.track('workflow.delegate', trace_id=trace, started_at=started_at, success=True, context={'tenant_id': instance.tenant_id, 'workflow_id': instance.workflow_id, 'workflow_definition': instance.definition_code, 'status': instance.status, 'trace_stage': 'workflow'})
            return instance.to_dict()

    def escalate_due_workflows(self, *, now: datetime | None = None, tenant_id: str | None = None, trace_id: str | None = None) -> list[dict[str, Any]]:
        trace = self._trace(trace_id)
        started_at = time.perf_counter()
        current = now or self._now()
        tenant_filter = normalize_tenant_id(tenant_id) if tenant_id else None
        escalated: list[dict[str, Any]] = []
        with self._lock:
            for instance in self.instances.values():
                if tenant_filter and instance.tenant_id != tenant_filter:
                    continue
                if instance.status != "pending":
                    continue
                for step in instance.steps:
                    metadata = step.get("metadata", {})
                    if step["status"] != "pending" or not metadata.get("active"):
                        continue
                    deadline_at = metadata.get("deadline_at")
                    escalation_assignee = metadata.get("escalation_assignee")
                    if not deadline_at or not escalation_assignee:
                        continue
                    if metadata.get("escalated_at"):
                        continue
                    deadline = datetime.fromisoformat(str(deadline_at).replace("Z", "+00:00"))
                    if deadline > current:
                        continue
                    previous_assignee = step["assignee"]
                    step["assignee"] = escalation_assignee
                    metadata["escalated_at"] = current.isoformat()
                    metadata["escalated_from"] = previous_assignee
                    instance.updated_at = current
                    self._append_history(instance, action="step_escalated", actor_id="workflow-engine", actor_type="service", step_id=step["step_id"], from_status=step["status"], to_status=step["status"], details={"from": previous_assignee, "to": escalation_assignee})
                    self._emit_workflow_event("WorkflowTaskEscalated", instance, trace, {"step_id": step["step_id"], "from": previous_assignee, "to": escalation_assignee})
                    self._notify_assignment(instance, trace, target_steps=[step], event_name="WorkflowTaskEscalated")
                    escalated.append(instance.to_dict())
        self.observability.track('workflow.escalate', trace_id=trace, started_at=started_at, success=True, context={'tenant_id': tenant_filter, 'workflow_definition': 'workflow.escalation', 'status': 'completed', 'trace_stage': 'workflow'})
        return escalated

    def _resolve_step(
        self,
        workflow_id: str,
        *,
        tenant_id: str,
        actor_id: str,
        actor_type: str,
        actor_role: str | None,
        action: str,
        comment: str | None,
        trace_id: str | None,
    ) -> dict[str, Any]:
        trace = self._trace(trace_id)
        started_at = time.perf_counter()
        with self._lock:
            instance = self._require_instance(workflow_id)
            assert_tenant_access(instance.tenant_id, normalize_tenant_id(tenant_id))
            if instance.status != "pending":
                return instance.to_dict()
            step = self._current_actor_step(instance, actor_id=actor_id, actor_role=actor_role)
            if step is None:
                raise WorkflowServiceError(403, "FORBIDDEN", "No actionable task is assigned to this actor")
            previous_status = step["status"]
            step["status"] = "approved" if action == "approve" else "rejected"
            step.setdefault("metadata", {})["acted_at"] = self._now().isoformat()
            step["metadata"]["acted_by"] = actor_id
            if comment:
                step["metadata"]["comment"] = comment
            instance.updated_at = self._now()
            self._append_history(instance, action=f"step_{action}d", actor_id=actor_id, actor_type=actor_type, step_id=step["step_id"], from_status=previous_status, to_status=step["status"], details={"comment": comment})
            if action == "reject":
                instance.status = "completed"
                instance.metadata["terminal_result"] = "rejected"
                self._deactivate_all_steps(instance)
            else:
                self._advance_after_approval(instance)
            self._emit_workflow_event(
                "WorkflowStepApproved" if action == "approve" else "WorkflowStepRejected",
                instance,
                trace,
                {"step_id": step["step_id"], "actor_id": actor_id, "comment": comment, "terminal_result": instance.metadata.get("terminal_result")},
            )
            self._notify_assignment(instance, trace)
            self.observability.logger.audit(
                f"workflow_step_{action}d",
                trace_id=trace,
                actor=actor_id,
                entity="WorkflowInstance",
                entity_id=instance.workflow_id,
                context={"step_id": step["step_id"], "tenant_id": instance.tenant_id, "terminal_result": instance.metadata.get("terminal_result")},
            )
            self.observability.track(f'workflow.{action}', trace_id=trace, started_at=started_at, success=True, context={'tenant_id': instance.tenant_id, 'workflow_id': instance.workflow_id, 'workflow_definition': instance.definition_code, 'status': instance.status, 'trace_stage': 'workflow'})
            return instance.to_dict()

    def _advance_after_approval(self, instance: WorkflowInstance) -> None:
        self._activate_next_steps(instance, actor_id="workflow-engine", actor_type="service")
        active_pending = [step for step in instance.steps if step["status"] == "pending" and step.get("metadata", {}).get("active")]
        if not active_pending:
            instance.status = "completed"
            instance.metadata["terminal_result"] = "approved"

    def _activate_next_steps(self, instance: WorkflowInstance, *, actor_id: str, actor_type: str) -> None:
        while True:
            current_group = self._active_parallel_group(instance)
            if current_group:
                return
            next_steps = [step for step in instance.steps if step["status"] == "pending" and not step.get("metadata", {}).get("active")]
            if not next_steps:
                return
            seed = next_steps[0]
            group = seed.get("metadata", {}).get("parallel_group")
            activation_set = [step for step in next_steps if step.get("metadata", {}).get("parallel_group") == group] if group else [seed]
            for step in activation_set:
                step.setdefault("metadata", {})["active"] = True
                self._append_history(instance, action="step_activated", actor_id=actor_id, actor_type=actor_type, step_id=step["step_id"], from_status=None, to_status=step["status"], details={"assignee": step["assignee"]})
            if any(step["type"] == "auto" for step in activation_set):
                for step in activation_set:
                    if step["type"] == "auto":
                        step["status"] = "approved"
                        step["metadata"]["acted_at"] = self._now().isoformat()
                        step["metadata"]["acted_by"] = "workflow-engine"
                        step["metadata"]["active"] = False
                        self._append_history(instance, action="step_auto_completed", actor_id="workflow-engine", actor_type="service", step_id=step["step_id"], from_status="pending", to_status="approved", details={})
                continue
            return

    def _active_parallel_group(self, instance: WorkflowInstance) -> list[dict[str, Any]]:
        return [step for step in instance.steps if step["status"] == "pending" and step.get("metadata", {}).get("active")]

    def _deactivate_all_steps(self, instance: WorkflowInstance) -> None:
        for step in instance.steps:
            step.setdefault("metadata", {})["active"] = False

    def _find_open_instance(self, tenant_id: str, definition_code: str, subject_id: str) -> WorkflowInstance | None:
        for instance in self.instances.values():
            if instance.tenant_id == tenant_id and instance.definition_code == definition_code and instance.subject_id == subject_id and instance.status == "pending":
                return instance
        return None

    def _require_definition(self, tenant_id: str, definition_code: str) -> WorkflowDefinition:
        definition = self.definitions.get((tenant_id, definition_code)) or self.definitions.get((DEFAULT_TENANT_ID, definition_code))
        if definition is None:
            raise WorkflowServiceError(404, "WORKFLOW_DEFINITION_NOT_FOUND", f"Workflow definition '{definition_code}' was not found")
        return definition

    def _require_instance(self, workflow_id: str) -> WorkflowInstance:
        instance = self.instances.get(workflow_id)
        if instance is None:
            raise WorkflowServiceError(404, "WORKFLOW_NOT_FOUND", "Workflow instance not found")
        return instance

    def _current_actor_step(self, instance: WorkflowInstance, *, actor_id: str, actor_role: str | None) -> dict[str, Any] | None:
        for step in instance.steps:
            if step["status"] == "pending" and step.get("metadata", {}).get("active") and self._step_visible_to_actor(step, actor_id=actor_id, actor_role=actor_role):
                return step
        return None

    @staticmethod
    def _step_visible_to_actor(step: dict[str, Any], *, actor_id: str, actor_role: str | None) -> bool:
        assignee = str(step.get("assignee") or "")
        if assignee == actor_id:
            return True
        if assignee.startswith("role:") and actor_role:
            return assignee.split(":", 1)[1].lower() == actor_role.lower()
        return False

    def _normalize_definition_step(self, *, index: int, step: dict[str, Any]) -> dict[str, Any]:
        raw = dict(step)
        step_type = str(raw.get("type") or "approval").lower()
        assignee = str(raw.get("assignee") or raw.get("assignee_template") or "role:admin")
        sla = raw.get("sla") or "PT24H"
        payload = ensure_workflow_contract(
            {
                "workflow_id": str(uuid4()),
                "created_at": self._now().isoformat(),
                "steps": [{"step_id": str(uuid4()), "type": step_type, "assignee": assignee, "status": "pending", "sla": sla}],
                "status": "pending",
            },
            now=self._now(),
        )
        normalized = payload["steps"][0]
        normalized["name"] = str(raw.get("name") or f"step-{index + 1}")
        normalized["metadata"].update(
            {
                "sequence": raw.get("sequence", index + 1),
                "parallel_group": raw.get("parallel_group"),
                "assignee_template": raw.get("assignee_template"),
                "escalation_assignee_template": raw.get("escalation_assignee_template"),
                "condition_key": raw.get("condition_key"),
                "active": False,
            }
        )
        return normalized

    def _instantiate_step(self, *, index: int, raw: dict[str, Any], context: dict[str, Any], workflow_created_at: datetime) -> dict[str, Any]:
        normalized = ensure_workflow_contract(
            {
                "workflow_id": str(uuid4()),
                "created_at": workflow_created_at.isoformat(),
                "steps": [
                    {
                        "step_id": str(uuid4()),
                        "type": raw["type"],
                        "assignee": self._resolve_template(raw.get("metadata", {}).get("assignee_template") or raw["assignee"], context),
                        "status": "pending",
                        "sla": raw["sla"],
                    }
                ],
                "status": "pending",
            },
            now=workflow_created_at,
        )
        step = normalized["steps"][0]
        raw_metadata = dict(raw.get("metadata") or {})
        extra_metadata = {
            "sequence": raw_metadata.get("sequence", index + 1),
            "parallel_group": raw_metadata.get("parallel_group"),
            "assignee_template": raw_metadata.get("assignee_template"),
            "escalation_assignee_template": raw_metadata.get("escalation_assignee_template"),
            "condition_key": raw_metadata.get("condition_key"),
        }
        step["metadata"] = {**dict(step.get("metadata") or {}), **extra_metadata}
        step["metadata"]["sequence"] = raw.get("metadata", {}).get("sequence", index + 1)
        step["metadata"]["parallel_group"] = raw.get("metadata", {}).get("parallel_group")
        step["metadata"]["active"] = False
        step["metadata"]["condition_key"] = raw.get("metadata", {}).get("condition_key")
        escalation_template = raw.get("metadata", {}).get("escalation_assignee_template")
        if escalation_template:
            step["metadata"]["escalation_assignee"] = self._resolve_template(escalation_template, context)
        condition_key = step["metadata"].get("condition_key")
        if condition_key and not context.get(condition_key, False):
            step["status"] = "approved"
            step["metadata"]["acted_by"] = "workflow-engine"
            step["metadata"]["acted_at"] = workflow_created_at.isoformat()
            step["metadata"]["auto_skipped"] = True
            step["metadata"]["active"] = False
        return step

    @staticmethod
    def _resolve_template(template: str, context: dict[str, Any]) -> str:
        if not isinstance(template, str):
            return str(template)
        if template.startswith("{") and template.endswith("}"):
            key = template[1:-1]
            return str(context.get(key) or "")
        return template.format(**context) if "{" in template and "}" in template else template

    def _append_history(
        self,
        instance: WorkflowInstance,
        *,
        action: str,
        actor_id: str,
        actor_type: str,
        to_status: str,
        step_id: str | None = None,
        from_status: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        instance.history.append(
            WorkflowHistory(
                history_id=str(uuid4()),
                workflow_id=instance.workflow_id,
                tenant_id=instance.tenant_id,
                action=action,
                actor_id=actor_id,
                actor_type=actor_type,
                step_id=step_id,
                from_status=from_status,
                to_status=to_status,
                details=dict(details or {}),
                created_at=self._now(),
            )
        )

    def _emit_workflow_event(self, event_name: str, instance: WorkflowInstance, trace_id: str, extra: dict[str, Any]) -> None:
        payload = {
            "workflow_id": instance.workflow_id,
            "definition_code": instance.definition_code,
            "source_service": instance.source_service,
            "subject_type": instance.subject_type,
            "subject_id": instance.subject_id,
            "status": instance.status,
            "terminal_result": instance.metadata.get("terminal_result"),
            **extra,
        }
        emit_canonical_event(
            self.events,
            legacy_event_name=event_name,
            data=payload,
            source="workflow-service",
            tenant_id=instance.tenant_id,
            registry=self.event_registry,
            correlation_id=trace_id,
            idempotency_key=f"{instance.workflow_id}:{event_name}:{payload.get('step_id', 'workflow')}",
        )

    def _notify_assignment(self, instance: WorkflowInstance, trace_id: str, *, target_steps: list[dict[str, Any]] | None = None, event_name: str = "WorkflowTaskAssigned") -> None:
        steps = target_steps or [step for step in instance.steps if step["status"] == "pending" and step.get("metadata", {}).get("active")]
        for step in steps:
            assignee = step.get("assignee")
            if not assignee or assignee.startswith("role:"):
                continue
            event = {
                "event_name": event_name,
                "tenant_id": instance.tenant_id,
                "data": {
                    "workflow_id": instance.workflow_id,
                    "step_id": step["step_id"],
                    "employee_id": assignee,
                    "destination": f"inbox:{assignee}",
                    "subject_id": assignee,
                    "subject_type": "Employee",
                    "workflow_definition": instance.definition_code,
                    "subject_type_name": instance.subject_type,
                    "subject_record_id": instance.subject_id,
                    "deadline_at": step.get("metadata", {}).get("deadline_at"),
                },
            }
            try:
                self.notification_service.ingest_event(event)
            except NotificationServiceError:
                self.observability.logger.error(
                    "workflow.notification_failed",
                    trace_id=trace_id,
                    message=event_name,
                    context={"workflow_id": instance.workflow_id, "step_id": step["step_id"]},
                )

    @staticmethod
    def _public_step(step: dict[str, Any]) -> dict[str, Any]:
        return {
            "step_id": step["step_id"],
            "type": step["type"],
            "assignee": step["assignee"],
            "status": step["status"],
            "sla": step["sla"],
            "metadata": dict(step.get("metadata") or {}),
        }
