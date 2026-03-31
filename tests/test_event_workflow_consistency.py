from __future__ import annotations

from pathlib import Path

from engagement_service import EngagementService
from helpdesk_service import HelpdeskService
from reporting_analytics import ReportingAnalyticsService
from workflow_service import WorkflowService


def test_helpdesk_engagement_and_workforce_intelligence_emit_canonical_events(tmp_path: Path) -> None:
    workflows = WorkflowService()
    helpdesk = HelpdeskService(db_path=str(tmp_path / "helpdesk-events.sqlite3"), workflow_service=workflows)
    _, ticket = helpdesk.create_ticket(
        {
            "tenant_id": "tenant-default",
            "requester_employee_id": "emp-001",
            "subject": "Laptop issue",
            "category_code": "IT",
            "description": "Need support with setup.",
        },
        actor_id="emp-001",
        actor_role="Employee",
    )
    _, _ = helpdesk.submit_ticket(ticket["ticket_id"], actor_id="emp-001", actor_role="Employee", tenant_id="tenant-default")
    assert any(event["event_type"] == "helpdesk.ticket.submitted" for event in helpdesk.events)

    engagement = EngagementService(db_path=str(tmp_path / "engagement-events.sqlite3"))
    engagement.register_employee_profile(
        {
            "tenant_id": "tenant-default",
            "employee_id": "emp-hr",
            "employee_number": "E-1",
            "full_name": "HR Owner",
            "department_id": "dep-hr",
            "department_name": "HR",
            "manager_employee_id": "emp-manager",
        }
    )
    _, survey = engagement.create_survey(
        {
            "tenant_id": "tenant-default",
            "code": "ENG-1",
            "title": "Pulse",
            "owner_employee_id": "emp-hr",
            "questions": [{"question_id": "q1", "prompt": "Q", "dimension": "D1", "kind": "Likert5", "required": True}],
        },
        actor_id="emp-hr",
    )
    _, _ = engagement.publish_survey(survey["survey_id"], tenant_id="tenant-default", actor_id="emp-hr")
    assert any(event["event_type"] == "engagement.survey.published" for event in engagement.events)

    reporting = ReportingAnalyticsService(db_path=str(tmp_path / "reporting-events.sqlite3"))
    report = reporting.create_report_definition({"name": "Workforce Dashboard", "report_type": "workforce.dashboard.summary"})
    run = reporting.run_report(report["report_id"])
    assert any(event["event_type"] == "workforce_intelligence.report.defined" for event in reporting.events)
    assert any(event["event_type"] == "workforce_intelligence.report_run.generated" and event["data"]["report_run_id"] == run["report_run_id"] for event in reporting.events)


def test_workflow_consumes_events_for_integrated_domains() -> None:
    service = WorkflowService()
    events = [
        {"event_name": "HelpdeskTicketSubmitted", "tenant_id": "tenant-default", "source": "helpdesk-service", "data": {"ticket_id": "t-1", "requester_employee_id": "emp-1"}},
        {"event_name": "EngagementSurveyPublished", "tenant_id": "tenant-default", "source": "engagement-service", "data": {"survey_id": "s-1", "owner_employee_id": "emp-hr"}},
        {"event_name": "LearningEnrollmentCreated", "tenant_id": "tenant-default", "source": "employee-service", "data": {"enrollment_id": "enr-1", "employee_id": "emp-2", "course_id": "c-1"}},
        {"event_name": "WorkforceIntelligenceReportRunGenerated", "tenant_id": "tenant-default", "source": "reporting-analytics", "data": {"report_run_id": "run-1", "report_id": "r-1", "report_type": "workforce.dashboard.summary"}},
        {"event_name": "CostPlanningPlanSubmitted", "tenant_id": "tenant-default", "source": "cost-planning-service", "data": {"plan_id": "cp-1", "owner_employee_id": "fin-1", "fiscal_period": "2026-Q2"}},
    ]

    results = [service.consume_event(item) for item in events]
    assert all(result["triggered"] for result in results)
    assert len({result["workflow_id"] for result in results}) == 5
    assert any(event["event_type"] == "workflow.event.consumed" for event in service.events)
