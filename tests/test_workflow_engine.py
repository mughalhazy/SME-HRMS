from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from leave_service import LeaveService
from notification_service import NotificationService
from payroll_service import PayrollService
from services.hiring_service.service import HiringService, HiringValidationError
from workflow_service import WorkflowService, WorkflowServiceError


def test_workflow_engine_handles_sequential_parallel_delegation_and_completion() -> None:
    notifications = NotificationService()
    service = WorkflowService(notification_service=notifications)
    service.register_definition(
        tenant_id="tenant-default",
        code="expense-approval",
        source_service="finance-service",
        subject_type="Expense",
        description="Sequential then parallel approval flow.",
        steps=[
            {"name": "manager", "type": "approval", "assignee_template": "{manager_id}", "sla": "PT1H"},
            {"name": "finance-a", "type": "approval", "assignee_template": "{finance_a}", "sla": "PT1H", "parallel_group": "finance"},
            {"name": "finance-b", "type": "approval", "assignee_template": "{finance_b}", "sla": "PT1H", "parallel_group": "finance"},
        ],
    )

    workflow = service.start_workflow(
        tenant_id="tenant-default",
        definition_code="expense-approval",
        source_service="finance-service",
        subject_type="Expense",
        subject_id="expense-1",
        actor_id="emp-001",
        actor_type="user",
        context={"manager_id": "mgr-1", "finance_a": "fin-1", "finance_b": "fin-2"},
    )

    inbox = service.list_inbox(tenant_id="tenant-default", actor_id="mgr-1")
    assert len(inbox["data"]) == 1
    service.delegate_step(workflow["workflow_id"], tenant_id="tenant-default", actor_id="mgr-1", actor_role=None, delegate_to="mgr-2")
    delegated_inbox = service.list_inbox(tenant_id="tenant-default", actor_id="mgr-2")
    assert delegated_inbox["data"][0]["step"]["assignee"] == "mgr-2"

    workflow = service.approve_step(workflow["workflow_id"], tenant_id="tenant-default", actor_id="mgr-2", actor_type="user", actor_role=None)
    finance_inbox_a = service.list_inbox(tenant_id="tenant-default", actor_id="fin-1")
    finance_inbox_b = service.list_inbox(tenant_id="tenant-default", actor_id="fin-2")
    assert len(finance_inbox_a["data"]) == 1
    assert len(finance_inbox_b["data"]) == 1

    service.approve_step(workflow["workflow_id"], tenant_id="tenant-default", actor_id="fin-1", actor_type="user", actor_role=None)
    workflow = service.approve_step(workflow["workflow_id"], tenant_id="tenant-default", actor_id="fin-2", actor_type="user", actor_role=None)
    assert workflow["status"] == "completed"
    assert workflow["metadata"]["terminal_result"] == "approved"
    assert any(item["message"] == "workflow_step_approved" for item in service.observability.logger.records)


def test_workflow_engine_escalates_overdue_tasks_and_respects_tenants() -> None:
    service = WorkflowService(notification_service=NotificationService())
    service.register_definition(
        tenant_id="tenant-default",
        code="leave-escalation",
        source_service="leave-service",
        subject_type="LeaveRequest",
        description="Escalation workflow.",
        steps=[{"type": "approval", "assignee_template": "{manager}", "sla": "PT1H", "escalation_assignee_template": "{admin}"}],
    )
    workflow = service.start_workflow(
        tenant_id="tenant-default",
        definition_code="leave-escalation",
        source_service="leave-service",
        subject_type="LeaveRequest",
        subject_id="leave-1",
        actor_id="emp-1",
        actor_type="user",
        context={"manager": "mgr-1", "admin": "emp-admin"},
    )

    escalated = service.escalate_due_workflows(now=datetime.now(timezone.utc) + timedelta(hours=2), tenant_id="tenant-default")
    assert escalated[0]["steps"][0]["assignee"] == "emp-admin"

    with pytest.raises(PermissionError):
        service.get_instance(workflow["workflow_id"], tenant_id="tenant-other")


def test_leave_approval_is_centralized_through_workflow_engine() -> None:
    shared_notifications = NotificationService()
    shared_workflow = WorkflowService(notification_service=shared_notifications)
    svc = LeaveService(workflow_service=shared_workflow, notification_service=shared_notifications)

    _, created = svc.create_request("Employee", "emp-001", "emp-001", "Annual", date(2026, 3, 10), date(2026, 3, 11))
    _, submitted = svc.submit_request("Employee", "emp-001", created["leave_request_id"])

    assert submitted["workflow"]["definition_code"] == "leave_request_approval"
    inbox = shared_workflow.list_inbox(tenant_id="tenant-default", actor_id="emp-manager")
    assert inbox["data"][0]["subject_id"] == created["leave_request_id"]

    _, approved = svc.decide_request("approve", "Manager", "emp-manager", created["leave_request_id"])
    assert approved["status"] == "Approved"
    assert approved["workflow"]["metadata"]["terminal_result"] == "approved"
    assert all(event["data"]["tenant_id"] == "tenant-default" for event in svc.events)


def test_payroll_and_hiring_use_workflow_engine_for_terminal_approval_paths() -> None:
    notifications = NotificationService()
    workflow = WorkflowService(notification_service=notifications)
    payroll = PayrollService(workflow_service=workflow, notification_service=notifications)
    admin_token = "Bearer eyJyb2xlIjogIkFkbWluIn0"  # {"role": "Admin"}

    _, created = payroll.create_payroll_record(
        {
            "employee_id": "emp-200",
            "pay_period_start": "2026-09-01",
            "pay_period_end": "2026-09-30",
            "base_salary": "1000.00",
            "currency": "USD",
        },
        admin_token,
    )
    payroll.run_payroll("2026-09-01", "2026-09-30", admin_token)
    _, paid = payroll.mark_paid(created["payroll_record_id"], admin_token)
    assert paid["payment_workflow_id"] is not None
    assert workflow.get_instance(paid["payment_workflow_id"], tenant_id="tenant-default")["metadata"]["terminal_result"] == "approved"

    hiring = HiringService(workflow_service=workflow, notification_service=notifications)
    posting = hiring.create_job_posting(
        {
            "title": "Backend Engineer",
            "department_id": "dept-eng",
            "employment_type": "FullTime",
            "description": "Build workflows",
            "openings_count": 1,
            "posting_date": "2026-09-01",
            "status": "Open",
        }
    )
    candidate = hiring.create_candidate(
        {
            "job_posting_id": posting["job_posting_id"],
            "first_name": "Ava",
            "last_name": "Stone",
            "email": "ava@example.com",
            "application_date": "2026-09-02",
        }
    )
    hiring.update_candidate(candidate["candidate_id"], {"status": "Screening"})
    hiring.update_candidate(candidate["candidate_id"], {"status": "Interviewing"})
    candidate = hiring.update_candidate(candidate["candidate_id"], {"status": "Offered"})
    hired = hiring.mark_candidate_hired(candidate["candidate_id"], {"changed_by": "admin-1", "approver_role": "Admin"})
    assert hired["status"] == "Hired"
    assert hired["hire_workflow_id"] is not None
