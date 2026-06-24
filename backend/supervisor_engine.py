from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
import inspect
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from background_jobs import BackgroundJobService, JobStatus
from event_outbox import EventOutbox, OutboxEvent
from outbox_system import OutboxManager
from resilience import CentralErrorLogger, CircuitBreaker, Observability
from workflow_service import WorkflowService

RecoveryHook = Callable[["SupervisorIncident", dict[str, Any]], dict[str, Any] | None]
EventDispatcher = Callable[[OutboxEvent], Any]
ServiceHealthCheck = Callable[[Any], dict[str, Any]]


@dataclass(slots=True)
class ServiceRegistration:
    service_name: str
    service: Any
    dependencies: tuple[str, ...] = ()
    health_check: ServiceHealthCheck | None = None


@dataclass(slots=True)
class SupervisorIncident:
    incident_id: str
    tenant_id: str | None
    source_type: str
    source_id: str
    service_name: str | None
    classification: str
    retryable: bool
    escalation_required: bool
    summary: str
    details: dict[str, Any]
    detected_at: str
    recovered_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RecoveryAction:
    action_id: str
    incident_id: str
    action_type: str
    status: str
    summary: str
    details: dict[str, Any]
    executed_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SupervisorEngine:
    """Non-invasive orchestration layer for cross-service failure detection and auto-healing."""

    def __init__(
        self,
        *,
        services: dict[str, Any] | None = None,
        background_jobs: BackgroundJobService | None = None,
        workflow_service: WorkflowService | None = None,
        event_outbox: EventOutbox | None = None,
        event_system: OutboxManager | None = None,
        event_dispatcher: EventDispatcher | None = None,
        workflow_stall_after: timedelta = timedelta(hours=1),
        service_error_rate_threshold: float = 0.2,
        service_error_count_threshold: int = 1,
        circuit_breaker_threshold: int = 2,
    ) -> None:
        self.background_jobs = background_jobs
        self.workflow_service = workflow_service
        self.event_outbox = event_outbox or (background_jobs.outbox if background_jobs is not None else None)
        self.event_system = event_system
        self.event_dispatcher = event_dispatcher
        self.workflow_stall_after = workflow_stall_after
        self.service_error_rate_threshold = service_error_rate_threshold
        self.service_error_count_threshold = service_error_count_threshold
        self.registrations: dict[str, ServiceRegistration] = {}
        self.incidents: list[SupervisorIncident] = []
        self.actions: list[RecoveryAction] = []
        self.escalation_handlers: list[RecoveryHook] = []
        self.fallback_handlers: dict[str, list[RecoveryHook]] = {}
        self.reroute_handlers: dict[str, list[RecoveryHook]] = {}
        self.observability = Observability("supervisor-engine")
        self.error_logger = CentralErrorLogger("supervisor-engine")
        self._action_breakers: dict[str, CircuitBreaker] = {}
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self._lock = RLock()
        if services:
            for service_name, service in services.items():
                self.register_service(service_name, service)
        if background_jobs is not None:
            self.register_service("background-jobs", background_jobs)
        if workflow_service is not None:
            self.register_service("workflow-service", workflow_service)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def register_service(
        self,
        service_name: str,
        service: Any,
        *,
        dependencies: list[str] | tuple[str, ...] | None = None,
        health_check: ServiceHealthCheck | None = None,
    ) -> None:
        self.registrations[service_name] = ServiceRegistration(
            service_name=service_name,
            service=service,
            dependencies=tuple(dependencies or ()),
            health_check=health_check,
        )

    def register_escalation_handler(self, handler: RecoveryHook) -> None:
        self.escalation_handlers.append(handler)

    def register_fallback_handler(self, subject: str, handler: RecoveryHook) -> None:
        self.fallback_handlers.setdefault(subject, []).append(handler)

    def register_reroute_handler(self, subject: str, handler: RecoveryHook) -> None:
        self.reroute_handlers.setdefault(subject, []).append(handler)

    def set_event_dispatcher(self, dispatcher: EventDispatcher) -> None:
        self.event_dispatcher = dispatcher

    def detect_failures(self, *, now: datetime | None = None) -> list[SupervisorIncident]:
        current = now or self._now()
        incidents: list[SupervisorIncident] = []
        service_state = self._build_service_state(current)
        incidents.extend(self._detect_service_failures(service_state, detected_at=current))
        incidents.extend(self._detect_job_failures(detected_at=current))
        incidents.extend(self._detect_event_failures(detected_at=current))
        incidents.extend(self._detect_workflow_stalls(current))
        return incidents

    def run_cycle(self, *, now: datetime | None = None, max_recovery_actions: int = 25) -> dict[str, Any]:
        started = perf_counter()
        current = now or self._now()
        detected = self.detect_failures(now=current)
        actions: list[RecoveryAction] = []
        for incident in detected[:max_recovery_actions]:
            actions.extend(self._recover_incident(incident, current))
        summary = {
            "detected_count": len(detected),
            "recovered_count": len([incident for incident in detected if incident.recovered_at is not None]),
            "incident_breakdown": self._count_by(lambda item: item.source_type, detected),
            "classification_breakdown": self._count_by(lambda item: item.classification, detected),
            "action_breakdown": self._count_by(lambda item: item.action_type, actions),
            "state": self.get_system_state(now=current),
            "incidents": [incident.to_dict() for incident in detected],
            "actions": [action.to_dict() for action in actions],
        }
        self.observability.track(
            "supervisor.run_cycle",
            trace_id=self.observability.trace_id(),
            started_at=started,
            success=True,
            context={"detected_count": len(detected), "action_count": len(actions)},
        )
        return summary

    def get_system_state(self, *, now: datetime | None = None) -> dict[str, Any]:
        current = now or self._now()
        service_state = self._build_service_state(current)
        workflow_state = self._workflow_state(current)
        job_state = self._job_state()
        event_state = self._event_state()
        return {
            "services": service_state,
            "workflows": workflow_state,
            "jobs": job_state,
            "events": event_state,
        }

    def _build_service_state(self, current: datetime) -> dict[str, Any]:
        state: dict[str, Any] = {}
        for service_name, registration in self.registrations.items():
            health = self._service_health(registration)
            observability = getattr(registration.service, "observability", None)
            metrics = (observability.metrics.snapshot() if observability is not None else {"request_count": 0, "error_count": 0, "error_rate": 0.0})
            log_records = list(getattr(getattr(observability, "logger", None), "records", [])) if observability is not None else []
            recent_errors = [record for record in log_records[-20:] if record.get("level") == "ERROR"]
            derived_status = "ok"
            reasons: list[str] = []
            if health.get("status") not in {None, "ok"}:
                derived_status = str(health.get("status"))
                reasons.append(f"health:{health.get('status')}")
            if metrics.get("error_count", 0) >= self.service_error_count_threshold and metrics.get("error_rate", 0.0) >= self.service_error_rate_threshold:
                derived_status = "degraded"
                reasons.append("observability-error-rate")
            elif recent_errors:
                derived_status = "degraded"
                reasons.append("recent-error-logs")
            dead_letters = len(getattr(getattr(registration.service, "dead_letters", None), "entries", []))
            if dead_letters:
                derived_status = "degraded"
                reasons.append("dead-letters")
            state[service_name] = {
                "status": derived_status,
                "health": health,
                "metrics": metrics,
                "recent_error_count": len(recent_errors),
                "dead_letter_count": dead_letters,
                "dependency_failures": [],
                "dependencies": list(registration.dependencies),
                "updated_at": current.isoformat(),
                "reasons": reasons,
            }
        for service_name, registration in self.registrations.items():
            failures = [dependency for dependency in registration.dependencies if state.get(dependency, {}).get("status") != "ok"]
            state[service_name]["dependency_failures"] = failures
            if failures and state[service_name]["status"] == "ok":
                state[service_name]["status"] = "degraded"
                state[service_name]["reasons"].append("dependency-failure")
        return state

    def _service_health(self, registration: ServiceRegistration) -> dict[str, Any]:
        service = registration.service
        if registration.health_check is not None:
            return registration.health_check(service)
        if hasattr(service, "health_snapshot"):
            return dict(service.health_snapshot())
        observability = getattr(service, "observability", None)
        if observability is not None:
            return observability.health_status(checks={})
        return {"service": registration.service_name, "status": "unknown", "checks": {}}

    def _detect_service_failures(self, service_state: dict[str, Any], *, detected_at: datetime) -> list[SupervisorIncident]:
        incidents: list[SupervisorIncident] = []
        for service_name, payload in service_state.items():
            if payload["status"] == "ok":
                continue
            dependency_failures = list(payload.get("dependency_failures") or [])
            classification = "critical" if payload.get("dead_letter_count") or not dependency_failures else "escalation_required"
            retryable = not payload.get("dead_letter_count")
            summary = "dependency failures detected" if dependency_failures else "service health degraded"
            details = {
                "service": service_name,
                "reasons": payload.get("reasons", []),
                "dependency_failures": dependency_failures,
                "health": payload.get("health", {}),
                "metrics": payload.get("metrics", {}),
            }
            incidents.append(
                self._incident(
                    source_type="service",
                    source_id=service_name,
                    service_name=service_name,
                    classification=classification,
                    retryable=retryable,
                    escalation_required=True,
                    summary=summary,
                    details=details,
                    detected_at=detected_at,
                )
            )
        return incidents

    def _detect_job_failures(self, *, detected_at: datetime) -> list[SupervisorIncident]:
        if self.background_jobs is None:
            return []
        incidents: list[SupervisorIncident] = []
        for job in self.background_jobs.jobs.values():
            if job.status not in {JobStatus.FAILED, JobStatus.DEAD_LETTERED}:
                continue
            classification = "retryable" if job.status == JobStatus.FAILED else "critical"
            incidents.append(
                self._incident(
                    source_type="job",
                    source_id=job.job_id,
                    service_name="background-jobs",
                    classification=classification,
                    retryable=job.status == JobStatus.FAILED,
                    escalation_required=job.status == JobStatus.DEAD_LETTERED,
                    summary=f"job {job.status.value.lower()}",
                    details={
                        "job_id": job.job_id,
                        "job_type": job.job_type,
                        "tenant_id": job.tenant_id,
                        "attempts": job.attempts,
                        "max_attempts": job.max_attempts,
                        "failure_reason": job.failure_reason,
                    },
                    detected_at=detected_at,
                    tenant_id=job.tenant_id,
                )
            )
        return incidents

    def _detect_event_failures(self, *, detected_at: datetime) -> list[SupervisorIncident]:
        incidents: list[SupervisorIncident] = []
        if self.event_outbox is not None:
            for event in self.event_outbox.pending_events():
                if event.failed_attempts <= 0:
                    continue
                classification = "transient" if event.failed_attempts < 3 else "critical"
                incidents.append(
                    self._incident(
                        source_type="event",
                        source_id=event.event_id,
                        service_name=None,
                        classification=classification,
                        retryable=True,
                        escalation_required=event.failed_attempts >= 3,
                        summary="outbox event delivery failed",
                        details={
                            "event_id": event.event_id,
                            "tenant_id": event.tenant_id,
                            "event_name": event.event_name,
                            "failed_attempts": event.failed_attempts,
                        },
                        detected_at=detected_at,
                        tenant_id=event.tenant_id,
                    )
                )
        if self.event_system is not None:
            for record in self.event_system.records.values():
                if getattr(record, "status", None) != "failed":
                    continue
                incidents.append(
                    self._incident(
                        source_type="event",
                        source_id=record.event_id,
                        service_name=None,
                        classification="critical",
                        retryable=True,
                        escalation_required=True,
                        summary="event bus dispatch failed",
                        details={
                            "event_id": record.event_id,
                            "event_type": record.event_type,
                            "tenant_id": record.tenant_id,
                            "attempt_count": record.attempt_count,
                            "last_error": record.last_error,
                        },
                        detected_at=detected_at,
                        tenant_id=record.tenant_id,
                    )
                )
        return incidents

    def _detect_workflow_stalls(self, current: datetime) -> list[SupervisorIncident]:
        if self.workflow_service is None:
            return []
        incidents: list[SupervisorIncident] = []
        for instance in self.workflow_service.instances.values():
            if instance.status != "pending":
                continue
            active_pending = [step for step in instance.steps if step["status"] == "pending" and step.get("metadata", {}).get("active")]
            if not active_pending:
                incidents.append(
                    self._incident(
                        source_type="workflow",
                        source_id=instance.workflow_id,
                        service_name="workflow-service",
                        classification="critical",
                        retryable=True,
                        escalation_required=True,
                        summary="workflow stalled without active steps",
                        details={
                            "workflow_id": instance.workflow_id,
                            "tenant_id": instance.tenant_id,
                            "definition_code": instance.definition_code,
                            "subject_id": instance.subject_id,
                        },
                        detected_at=current,
                        tenant_id=instance.tenant_id,
                    )
                )
                continue
            last_updated = instance.updated_at if isinstance(instance.updated_at, datetime) else datetime.fromisoformat(str(instance.updated_at))
            if last_updated > current:
                incidents.append(
                    self._incident(
                        source_type="workflow",
                        source_id=instance.workflow_id,
                        service_name="workflow-service",
                        classification="escalation_required",
                        retryable=True,
                        escalation_required=True,
                        summary="workflow timestamp drift detected",
                        details={
                            "workflow_id": instance.workflow_id,
                            "tenant_id": instance.tenant_id,
                            "definition_code": instance.definition_code,
                            "updated_at": last_updated.isoformat(),
                            "monitor_time": current.isoformat(),
                            "drift_seconds": (last_updated - current).total_seconds(),
                        },
                        detected_at=current,
                        tenant_id=instance.tenant_id,
                    )
                )
                continue
            for step in active_pending:
                metadata = dict(step.get("metadata") or {})
                deadline_at = metadata.get("deadline_at")
                if deadline_at:
                    deadline = datetime.fromisoformat(str(deadline_at).replace("Z", "+00:00"))
                    if deadline <= current:
                        incidents.append(
                            self._incident(
                                source_type="workflow",
                                source_id=instance.workflow_id,
                                service_name="workflow-service",
                                classification="escalation_required",
                                retryable=True,
                                escalation_required=True,
                                summary="workflow step overdue",
                                details={
                                    "workflow_id": instance.workflow_id,
                                    "tenant_id": instance.tenant_id,
                                    "definition_code": instance.definition_code,
                                    "step_id": step["step_id"],
                                    "assignee": step["assignee"],
                                    "deadline_at": deadline_at,
                                },
                                detected_at=current,
                                tenant_id=instance.tenant_id,
                            )
                        )
                        continue
                if last_updated + self.workflow_stall_after <= current:
                    incidents.append(
                        self._incident(
                            source_type="workflow",
                            source_id=instance.workflow_id,
                            service_name="workflow-service",
                            classification="escalation_required",
                            retryable=True,
                            escalation_required=True,
                            summary="workflow exceeded stall threshold",
                            details={
                                "workflow_id": instance.workflow_id,
                                "tenant_id": instance.tenant_id,
                                "definition_code": instance.definition_code,
                                "step_id": step["step_id"],
                                "assignee": step["assignee"],
                                "updated_at": last_updated.isoformat(),
                            },
                            detected_at=current,
                            tenant_id=instance.tenant_id,
                        )
                    )
        return incidents

    def _recover_incident(self, incident: SupervisorIncident, current: datetime) -> list[RecoveryAction]:
        with self._lock:
            self.incidents.append(incident)
        if incident.source_type == "job":
            actions = self._recover_job(incident, current)
        elif incident.source_type == "event":
            actions = self._recover_event(incident, current)
        elif incident.source_type == "workflow":
            actions = self._recover_workflow(incident, current)
        else:
            actions = self._recover_service(incident, current)
        with self._lock:
            self.actions.extend(actions)
        return actions

    def _recover_job(self, incident: SupervisorIncident, current: datetime) -> list[RecoveryAction]:
        if self.background_jobs is None:
            return [self._action(incident, "retry", "skipped", "background jobs unavailable", {}, current)]
        job_id = str(incident.details["job_id"])
        tenant_id = str(incident.details["tenant_id"])
        if not incident.retryable:
            return self._run_escalations(incident, current, default_summary="job requires escalation")
        try:
            self.background_jobs.retry_job(job_id, tenant_id=tenant_id)
            recovered = self.background_jobs.execute_job(job_id, tenant_id=tenant_id)
            success = recovered.status == JobStatus.SUCCEEDED
            if success:
                incident.recovered_at = current.isoformat()
            action = self._action(
                incident,
                "retry",
                "succeeded" if success else "failed",
                "background job retried",
                {"job_id": job_id, "status": recovered.status.value, "attempts": recovered.attempts},
                current,
            )
            extra = [] if success else self._run_escalations(incident, current, default_summary="job retry did not recover")
            return [action, *extra]
        except Exception as exc:  # noqa: BLE001
            self.error_logger.log("recover_job", exc, details={"job_id": job_id})
            return [
                self._action(incident, "retry", "failed", "background job retry raised", {"job_id": job_id, "error": str(exc)}, current),
                *self._run_escalations(incident, current, default_summary="job recovery failed"),
            ]

    def _recover_event(self, incident: SupervisorIncident, current: datetime) -> list[RecoveryAction]:
        actions: list[RecoveryAction] = []
        if self.event_outbox is not None and self.event_dispatcher is not None:
            try:
                result = self.event_outbox.dispatch_pending(
                    lambda event: self.event_dispatcher(event),
                    tenant_id=incident.tenant_id,
                    max_events=1,
                )
                recovered = result["dispatched_count"] > 0 and not result["failed_count"]
                if recovered:
                    incident.recovered_at = current.isoformat()
                actions.append(
                    self._action(
                        incident,
                        "reprocess",
                        "succeeded" if recovered else "failed",
                        "event outbox reprocessed",
                        result,
                        current,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                self.error_logger.log("recover_event_outbox", exc, details={"incident_id": incident.incident_id})
                actions.append(self._action(incident, "reprocess", "failed", "event outbox reprocess raised", {"error": str(exc)}, current))
        if self.event_system is not None and incident.recovered_at is None:
            before = len([record for record in self.event_system.records.values() if getattr(record, "status", None) == "failed"])
            self.event_system.dispatch_pending(lambda event: None)
            after = len([record for record in self.event_system.records.values() if getattr(record, "status", None) == "failed"])
            recovered = after < before
            if recovered:
                incident.recovered_at = current.isoformat()
            actions.append(
                self._action(
                    incident,
                    "reprocess",
                    "succeeded" if recovered else "failed",
                    "event system replay attempted",
                    {"failed_before": before, "failed_after": after},
                    current,
                )
            )
        if not actions:
            actions.append(self._action(incident, "reprocess", "skipped", "no event dispatcher registered", {}, current))
        if incident.recovered_at is None:
            actions.extend(self._run_escalations(incident, current, default_summary="event recovery requires escalation"))
        return actions

    def _recover_workflow(self, incident: SupervisorIncident, current: datetime) -> list[RecoveryAction]:
        actions: list[RecoveryAction] = []
        reroutes = self._run_hooks("workflow-service", self.reroute_handlers, incident, current, action_type="reroute")
        actions.extend(reroutes)
        if self.workflow_service is not None:
            before = self.workflow_service.get_instance(incident.source_id, tenant_id=incident.tenant_id or "tenant-default")
            escalated = self.workflow_service.escalate_due_workflows(
                now=current,
                tenant_id=incident.tenant_id,
                workflow_id=incident.source_id,
                include_stalled=incident.summary in {"workflow exceeded stall threshold", "workflow timestamp drift detected"},
            )
            after = self.workflow_service.get_instance(incident.source_id, tenant_id=incident.tenant_id or "tenant-default")
            recovered = any(item["workflow_id"] == incident.source_id for item in escalated)
            if recovered:
                incident.recovered_at = current.isoformat()
            actions.append(
                self._action(
                    incident,
                    "unblock",
                    "succeeded" if recovered else "failed",
                    "workflow escalation/unblock attempted",
                    {
                        "workflow_id": incident.source_id,
                        "active_before": [step["assignee"] for step in before["steps"] if step["status"] == "pending" and step.get("metadata", {}).get("active")],
                        "active_after": [step["assignee"] for step in after["steps"] if step["status"] == "pending" and step.get("metadata", {}).get("active")],
                        "escalated_count": len(escalated),
                    },
                    current,
                )
            )
        actions.extend(self._run_escalations(incident, current, default_summary="workflow requires user/admin escalation"))
        return actions

    def _recover_service(self, incident: SupervisorIncident, current: datetime) -> list[RecoveryAction]:
        actions: list[RecoveryAction] = []
        registration = self.registrations.get(incident.source_id)
        service = registration.service if registration is not None else None
        if service is not None and hasattr(service, "replay_dead_letters"):
            replay = getattr(service, "replay_dead_letters")
            signature = inspect.signature(replay)
            required = [
                parameter
                for parameter in signature.parameters.values()
                if parameter.default is inspect._empty and parameter.kind in {inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
            ]
            if not required:
                try:
                    recovered = replay()
                    healed = bool(recovered)
                    if healed:
                        incident.recovered_at = current.isoformat()
                    actions.append(
                        self._action(
                            incident,
                            "retry",
                            "succeeded" if healed else "skipped",
                            "service dead-letter replay attempted",
                            {"recovered_count": len(recovered)},
                            current,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    self.error_logger.log("recover_service_replay", exc, details={"service": incident.source_id})
                    actions.append(self._action(incident, "retry", "failed", "service dead-letter replay raised", {"error": str(exc)}, current))
            else:
                actions.append(self._action(incident, "retry", "skipped", "service dead-letter replay requires explicit inputs", {"required_parameters": [parameter.name for parameter in required]}, current))
        actions.extend(self._run_hooks(incident.source_id, self.fallback_handlers, incident, current, action_type="fallback"))
        if incident.recovered_at is None:
            actions.extend(self._run_escalations(incident, current, default_summary="service degradation escalated"))
        return actions

    def _run_escalations(self, incident: SupervisorIncident, current: datetime, *, default_summary: str) -> list[RecoveryAction]:
        if not incident.escalation_required:
            return []
        if not self.escalation_handlers:
            return [self._action(incident, "escalate", "queued", default_summary, {}, current)]
        actions: list[RecoveryAction] = []
        for index, handler in enumerate(self.escalation_handlers, start=1):
            try:
                result = handler(incident, self.get_system_state(now=current)) or {}
                actions.append(self._action(incident, "escalate", "queued", default_summary, {"handler": index, **result}, current))
            except Exception as exc:  # noqa: BLE001
                self.error_logger.log("escalation_handler", exc, details={"incident_id": incident.incident_id})
                actions.append(self._action(incident, "escalate", "failed", "escalation handler failed", {"handler": index, "error": str(exc)}, current))
        return actions

    def _run_hooks(
        self,
        subject: str,
        registry: dict[str, list[RecoveryHook]],
        incident: SupervisorIncident,
        current: datetime,
        *,
        action_type: str,
    ) -> list[RecoveryAction]:
        actions: list[RecoveryAction] = []
        handlers = registry.get(subject, []) + registry.get("*", [])
        state = self.get_system_state(now=current)
        for index, handler in enumerate(handlers, start=1):
            breaker_key = f"{action_type}:{subject}:{index}"
            breaker = self._action_breakers.setdefault(breaker_key, CircuitBreaker(failure_threshold=self.circuit_breaker_threshold, recovery_timeout=60.0))
            try:
                result = breaker.call(lambda: handler(incident, state) or {})
                actions.append(self._action(incident, action_type, "succeeded", f"{action_type} hook executed", {"handler": index, **result}, current))
            except Exception as exc:  # noqa: BLE001
                self.error_logger.log(f"{action_type}_hook", exc, details={"subject": subject, "incident_id": incident.incident_id})
                status = "skipped" if "circuit breaker is open" in str(exc).lower() else "failed"
                actions.append(self._action(incident, action_type, status, f"{action_type} hook failed", {"handler": index, "error": str(exc)}, current))
        return actions

    def _incident(
        self,
        *,
        source_type: str,
        source_id: str,
        service_name: str | None,
        classification: str,
        retryable: bool,
        escalation_required: bool,
        summary: str,
        details: dict[str, Any],
        detected_at: datetime,
        tenant_id: str | None = None,
    ) -> SupervisorIncident:
        return SupervisorIncident(
            incident_id=str(uuid4()),
            tenant_id=tenant_id,
            source_type=source_type,
            source_id=source_id,
            service_name=service_name,
            classification=classification,
            retryable=retryable,
            escalation_required=escalation_required,
            summary=summary,
            details=details,
            detected_at=detected_at.isoformat(),
        )

    def _action(
        self,
        incident: SupervisorIncident,
        action_type: str,
        status: str,
        summary: str,
        details: dict[str, Any],
        current: datetime,
    ) -> RecoveryAction:
        return RecoveryAction(
            action_id=str(uuid4()),
            incident_id=incident.incident_id,
            action_type=action_type,
            status=status,
            summary=summary,
            details=details,
            executed_at=current.isoformat(),
        )

    def _job_state(self) -> dict[str, Any]:
        if self.background_jobs is None:
            return {"failed": 0, "dead_lettered": 0, "scheduled": 0}
        jobs = list(self.background_jobs.jobs.values())
        return {
            "failed": len([job for job in jobs if job.status == JobStatus.FAILED]),
            "dead_lettered": len([job for job in jobs if job.status == JobStatus.DEAD_LETTERED]),
            "scheduled": len([job for job in jobs if job.status == JobStatus.SCHEDULED]),
            "running": len([job for job in jobs if job.status == JobStatus.RUNNING]),
        }

    def _workflow_state(self, current: datetime) -> dict[str, Any]:
        if self.workflow_service is None:
            return {"pending": 0, "stalled": 0}
        pending = [instance for instance in self.workflow_service.instances.values() if instance.status == "pending"]
        stalled = self._detect_workflow_stalls(current)
        return {
            "pending": len(pending),
            "stalled": len(stalled),
        }

    def _event_state(self) -> dict[str, Any]:
        pending = self.event_outbox.pending_events() if self.event_outbox is not None else []
        failed_pending = [event for event in pending if event.failed_attempts > 0]
        bus_failed = []
        if self.event_system is not None:
            bus_failed = [record for record in self.event_system.records.values() if getattr(record, "status", None) == "failed"]
        return {
            "pending": len(pending),
            "failed_pending": len(failed_pending),
            "bus_failed": len(bus_failed),
        }

    @staticmethod
    def _count_by(key: Callable[[Any], str], rows: list[Any]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            item = key(row)
            counts[item] = counts.get(item, 0) + 1
        return counts
