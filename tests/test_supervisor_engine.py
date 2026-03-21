from __future__ import annotations

from datetime import datetime, timedelta, timezone

from background_jobs import BackgroundJobError, BackgroundJobService, JobStatus
from leave_service import LeaveService
from notification_service import NotificationService
from payroll_service import PayrollService
from supervisor_engine import SupervisorEngine
from workflow_service import WorkflowService


def test_supervisor_retries_failed_jobs_and_reprocesses_failed_events() -> None:
    jobs = BackgroundJobService()
    attempts = {"job": 0, "event": 0}

    def flaky_job(context):
        attempts["job"] += 1
        if attempts["job"] == 1:
            raise BackgroundJobError(422, "TEMPORARY_FAILURE", "first attempt should fail and be retried later")
        return {"ok": True, "job_id": context.job.job_id}

    def flaky_dispatcher(event):
        attempts["event"] += 1
        if attempts["event"] == 1:
            raise RuntimeError("temporary event transport issue")
        return {"event_id": event.event_id}

    jobs.register_handler("test.flaky", flaky_job, max_attempts=3)
    job = jobs.enqueue_job(tenant_id="tenant-default", job_type="test.flaky", payload={"hello": "world"})
    first_result = jobs.execute_job(job.job_id, tenant_id="tenant-default")
    assert first_result.status == JobStatus.FAILED

    jobs.outbox.stage_event(
        tenant_id="tenant-default",
        aggregate_type="Payroll",
        aggregate_id="batch-1",
        event_name="PayrollProcessed",
        payload={"tenant_id": "tenant-default", "record_ids": ["pay-1"]},
        trace_id="trace-supervisor-event",
    )
    failed_dispatch = jobs.outbox.dispatch_pending(flaky_dispatcher, tenant_id="tenant-default")
    assert failed_dispatch["failed_count"] == 1

    engine = SupervisorEngine(background_jobs=jobs, event_dispatcher=flaky_dispatcher)
    summary = engine.run_cycle(now=datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc))

    assert jobs.get_job(job.job_id, tenant_id="tenant-default").status == JobStatus.SUCCEEDED
    assert jobs.outbox.pending_events(tenant_id="tenant-default") == []
    assert summary["incident_breakdown"]["job"] == 1
    assert summary["incident_breakdown"]["event"] == 1
    assert summary["action_breakdown"]["retry"] >= 1
    assert summary["action_breakdown"]["reprocess"] >= 1



def test_supervisor_escalates_stalled_workflows_and_invokes_escalation_hooks() -> None:
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    workflows.register_definition(
        tenant_id="tenant-default",
        code="leave-escalation",
        source_service="leave-service",
        subject_type="LeaveRequest",
        description="Escalation-capable leave workflow.",
        steps=[
            {
                "type": "approval",
                "assignee_template": "{manager_id}",
                "sla": "PT1H",
                "escalation_assignee_template": "{admin_id}",
            }
        ],
    )
    workflow = workflows.start_workflow(
        tenant_id="tenant-default",
        definition_code="leave-escalation",
        source_service="leave-service",
        subject_type="LeaveRequest",
        subject_id="leave-1",
        actor_id="emp-1",
        actor_type="user",
        context={"manager_id": "mgr-1", "admin_id": "admin-1"},
    )

    engine = SupervisorEngine(workflow_service=workflows, workflow_stall_after=timedelta(minutes=15))
    escalations: list[dict[str, str]] = []
    engine.register_escalation_handler(
        lambda incident, state: escalations.append({"incident": incident.source_id, "type": incident.source_type}) or {"recipient": "admin-1"}
    )

    summary = engine.run_cycle(now=datetime(2026, 3, 21, 14, 0, tzinfo=timezone.utc))
    updated = workflows.get_instance(workflow["workflow_id"], tenant_id="tenant-default")

    assert updated["steps"][0]["assignee"] == "admin-1"
    assert any(item["type"] == "workflow" for item in escalations)
    assert summary["classification_breakdown"]["escalation_required"] >= 1
    assert summary["action_breakdown"]["unblock"] >= 1
    assert summary["action_breakdown"]["escalate"] >= 1



def test_supervisor_tracks_dependency_failures_and_prevents_cascading_recovery_failures() -> None:
    leave = LeaveService()
    payroll = PayrollService(notification_service=NotificationService())

    leave.observability.metrics.record_request(
        "leave.approve",
        trace_id="trace-leave-fail",
        latency_ms=12.0,
        success=False,
        context={"status": 500},
    )
    leave.observability.logger.error("leave.failure", trace_id="trace-leave-fail", context={"reason": "db timeout"})

    engine = SupervisorEngine(
        services={
            "leave-service": leave,
            "payroll-service": payroll,
        },
        service_error_rate_threshold=0.1,
        service_error_count_threshold=1,
        circuit_breaker_threshold=1,
    )
    engine.register_service("payroll-service", payroll, dependencies=["leave-service"])

    fallback_attempts = {"count": 0}

    def failing_fallback(incident, state):
        fallback_attempts["count"] += 1
        raise RuntimeError("fallback endpoint unavailable")

    escalations: list[str] = []
    engine.register_fallback_handler("payroll-service", failing_fallback)
    engine.register_escalation_handler(lambda incident, state: escalations.append(incident.source_id) or {"recipient": "ops"})

    first = engine.run_cycle(now=datetime(2026, 3, 21, 15, 0, tzinfo=timezone.utc))
    second = engine.run_cycle(now=datetime(2026, 3, 21, 15, 5, tzinfo=timezone.utc))

    assert first["state"]["services"]["leave-service"]["status"] == "degraded"
    assert "leave-service" in first["state"]["services"]["payroll-service"]["dependency_failures"]
    assert fallback_attempts["count"] == 1
    assert second["action_breakdown"]["fallback"] >= 1
    assert any(action["status"] == "skipped" for action in second["actions"] if action["action_type"] == "fallback")
    assert "leave-service" in escalations
    assert "payroll-service" in escalations
