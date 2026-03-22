from datetime import datetime, timedelta, timezone
from pathlib import Path

from audit_service.service import get_audit_service
from helpdesk_service import HelpdeskService
from notification_service import NotificationService
from workflow_service import WorkflowService


def test_helpdesk_ticket_lifecycle_runs_through_workflow_with_comments_attachments_and_self_service(tmp_path: Path) -> None:
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    service = HelpdeskService(db_path=str(tmp_path / 'helpdesk.sqlite3'), workflow_service=workflows, notification_service=notifications)

    _, created = service.create_ticket(
        {
            'tenant_id': 'tenant-default',
            'requester_employee_id': 'emp-001',
            'subject': 'Need employment verification letter',
            'category_code': 'DOCUMENTS',
            'description': 'I need an employment verification letter for a mortgage application.',
            'priority': 'High',
            'attachments': [
                {
                    'file_name': 'mortgage-request.pdf',
                    'content_type': 'application/pdf',
                    'storage_key': 'helpdesk/mortgage-request.pdf',
                }
            ],
            'initial_comment': 'Please process this before Friday.',
        },
        actor_id='emp-001',
        actor_role='Employee',
        trace_id='trace-helpdesk-create',
    )
    assert created['status'] == 'Draft'
    assert created['attachments'][0]['file_name'] == 'mortgage-request.pdf'
    assert created['comments'][0]['body'] == 'Please process this before Friday.'

    _, commented = service.add_comment(
        created['ticket_id'],
        {
            'tenant_id': 'tenant-default',
            'body': 'Adding my mortgage lender deadline for context.',
            'visibility': 'public',
        },
        actor_id='emp-001',
        actor_role='Employee',
        trace_id='trace-helpdesk-comment-public',
    )
    assert len(commented['comments']) == 2

    _, submitted = service.submit_ticket(
        created['ticket_id'],
        actor_id='emp-001',
        actor_role='Employee',
        tenant_id='tenant-default',
        trace_id='trace-helpdesk-submit',
    )
    assert submitted['status'] == 'Open'
    assert submitted['workflow']['definition_code'] == 'hr_helpdesk_ticket_lifecycle'
    assert submitted['sla']['status'] == 'on_track'
    assert submitted['sla']['current_assignee'] == 'helpdesk-agent'

    inbox = workflows.list_inbox(tenant_id='tenant-default', actor_id='helpdesk-agent')
    assert inbox['data'][0]['subject_id'] == created['ticket_id']

    _, in_progress = service.decide_ticket(
        created['ticket_id'],
        action='approve',
        actor_id='helpdesk-agent',
        actor_role='Helpdesk',
        tenant_id='tenant-default',
        comment='Validated the request and assigned to specialist.',
        trace_id='trace-helpdesk-triage',
    )
    assert in_progress['status'] == 'InProgress'
    assert in_progress['sla']['current_assignee'] == 'hr-helpdesk-specialist'

    _, internal = service.add_comment(
        created['ticket_id'],
        {
            'tenant_id': 'tenant-default',
            'body': 'Document request verified against employee profile.',
            'visibility': 'internal',
        },
        actor_id='hr-helpdesk-specialist',
        actor_role='Helpdesk',
        trace_id='trace-helpdesk-comment-internal',
    )
    assert any(comment['visibility'] == 'internal' for comment in internal['comments'])

    _, resolved = service.decide_ticket(
        created['ticket_id'],
        action='approve',
        actor_id='hr-helpdesk-specialist',
        actor_role='Helpdesk',
        tenant_id='tenant-default',
        comment='Verification letter generated and shared securely.',
        resolution_summary='Employment verification letter delivered to employee.',
        trace_id='trace-helpdesk-resolve',
    )
    assert resolved['status'] == 'Resolved'
    assert resolved['workflow']['metadata']['terminal_result'] == 'approved'
    assert resolved['sla']['status'] == 'completed'

    _, closed = service.close_ticket(
        created['ticket_id'],
        {'tenant_id': 'tenant-default', 'closure_comment': 'Received the letter. Thanks!'},
        actor_id='emp-001',
        actor_role='Employee',
        trace_id='trace-helpdesk-close',
    )
    assert closed['status'] == 'Closed'

    _, employee_view = service.get_ticket(
        created['ticket_id'],
        tenant_id='tenant-default',
        actor_id='emp-001',
        actor_role='Employee',
        trace_id='trace-helpdesk-get-employee',
    )
    assert all(comment['visibility'] == 'public' for comment in employee_view['comments'])

    _, staff_view = service.get_ticket(
        created['ticket_id'],
        tenant_id='tenant-default',
        actor_id='hr-helpdesk-specialist',
        actor_role='Helpdesk',
        trace_id='trace-helpdesk-get-staff',
    )
    assert any(comment['visibility'] == 'internal' for comment in staff_view['comments'])

    _, self_service = service.list_tickets(
        tenant_id='tenant-default',
        requester_employee_id='emp-001',
        actor_id='emp-001',
        actor_role='Employee',
    )
    assert len(self_service['items']) == 1
    assert self_service['items'][0]['ticket_id'] == created['ticket_id']

    records, _ = get_audit_service().list_records(tenant_id='tenant-default', entity='HelpdeskTicket', limit=50)
    actions = {record['action'] for record in records if record['entity_id'] == created['ticket_id']}
    assert {
        'helpdesk_ticket_created',
        'helpdesk_ticket_comment_added',
        'helpdesk_ticket_submitted',
        'helpdesk_ticket_in_progress',
        'helpdesk_ticket_resolved',
        'helpdesk_ticket_closed',
    } <= actions



def test_helpdesk_sla_escalation_reuses_workflow_engine_and_updates_assignees(tmp_path: Path) -> None:
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    service = HelpdeskService(db_path=str(tmp_path / 'helpdesk-sla.sqlite3'), workflow_service=workflows, notification_service=notifications)

    _, created = service.create_ticket(
        {
            'tenant_id': 'tenant-default',
            'requester_employee_id': 'emp-001',
            'subject': 'Need benefit enrollment correction',
            'category_code': 'BENEFITS',
            'description': 'Dental plan selection needs to be corrected after onboarding.',
            'priority': 'Urgent',
        },
        actor_id='emp-001',
        actor_role='Employee',
        trace_id='trace-helpdesk-sla-create',
    )
    _, submitted = service.submit_ticket(
        created['ticket_id'],
        actor_id='emp-001',
        actor_role='Employee',
        tenant_id='tenant-default',
        trace_id='trace-helpdesk-sla-submit',
    )

    first_deadline = datetime.fromisoformat(submitted['sla']['deadline_at'])
    status, escalated_payload = service.run_sla_monitor(
        tenant_id='tenant-default',
        now=first_deadline + timedelta(minutes=30),
        trace_id='trace-helpdesk-sla-escalate-triage',
    )
    assert status == 200
    assert escalated_payload['items'][0]['sla']['status'] == 'escalated'
    assert escalated_payload['items'][0]['sla']['current_assignee'] == 'hr-helpdesk-lead'

    escalated_inbox = workflows.list_inbox(tenant_id='tenant-default', actor_id='hr-helpdesk-lead')
    assert escalated_inbox['data'][0]['subject_id'] == created['ticket_id']

    _, after_triage = service.decide_ticket(
        created['ticket_id'],
        action='approve',
        actor_id='hr-helpdesk-lead',
        actor_role='Helpdesk',
        tenant_id='tenant-default',
        comment='Escalated triage handled by lead.',
        trace_id='trace-helpdesk-sla-triage-approve',
    )
    assert after_triage['status'] == 'InProgress'

    resolution_deadline = datetime.fromisoformat(after_triage['sla']['deadline_at'])
    _, second_escalation = service.run_sla_monitor(
        tenant_id='tenant-default',
        now=resolution_deadline + timedelta(minutes=15),
        trace_id='trace-helpdesk-sla-escalate-resolution',
    )
    assert second_escalation['items'][0]['sla']['current_assignee'] == 'hr-ops-manager'
    assert second_escalation['items'][0]['sla']['status'] == 'escalated'

    _, resolved = service.decide_ticket(
        created['ticket_id'],
        action='approve',
        actor_id='hr-ops-manager',
        actor_role='Admin',
        tenant_id='tenant-default',
        comment='Benefits correction completed after escalation.',
        resolution_summary='Benefits enrollment corrected and confirmed with employee.',
        trace_id='trace-helpdesk-sla-resolve',
    )
    assert resolved['status'] == 'Resolved'
    assert resolved['workflow']['metadata']['terminal_result'] == 'approved'
    assert resolved['sla']['status'] == 'completed'

    escalation_actions = [event['legacy_event_name'] for event in service.events if event['legacy_event_name'] == 'HelpdeskTicketSlaEscalated']
    assert len(escalation_actions) == 2
