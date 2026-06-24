from __future__ import annotations

from pathlib import Path

from audit_service.service import get_audit_service
from automation_api import get_executions, get_rules, post_event, post_rule
from automation_service import AutomationService
from notification_service import NotificationChannel, NotificationService
from workflow_service import WorkflowService


def test_automation_studio_executes_rules_with_workflow_notify_update_and_idempotency(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv('HRMS_AUDIT_LOG_PATH', str(tmp_path / 'audit.jsonl'))
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    workflows.register_definition(
        tenant_id='tenant-acme',
        code='project_assignment_review',
        source_service='project-service',
        subject_type='ProjectAssignment',
        description='Review assignment risks raised by automation.',
        steps=[
            {'name': 'Manager Approval', 'type': 'approval', 'assignee': 'mgr-1', 'sla': 'PT24H'},
        ],
    )
    service = AutomationService(
        db_path=str(tmp_path / 'automation.sqlite3'),
        workflow_service=workflows,
        notification_service=notifications,
    )
    notifications.register_template(
        tenant_id='tenant-acme',
        code='automation.assignment.flagged',
        channel=NotificationChannel.IN_APP,
        topic_code='automation.assignment',
        subject_template='Assignment flagged',
        body_template='Assignment {assignment_id} requires review.',
    )

    rule = service.create_rule(
        {
            'tenant_id': 'tenant-acme',
            'name': 'Flag high allocation projects',
            'status': 'enabled',
            'trigger': {'events': ['ProjectAssignmentRequested'], 'source_services': ['project-service']},
            'conditions': [{'path': 'data.allocation_percentage', 'operator': '>=', 'value': 75}],
            'actions': [
                {
                    'type': 'workflow',
                    'config': {
                        'definition_code': 'project_assignment_review',
                        'subject_type': 'ProjectAssignment',
                        'subject_id': {'from': 'data.assignment_id'},
                    },
                },
                {
                    'type': 'notification',
                    'config': {
                        'template_code': 'automation.assignment.flagged',
                        'channel': 'IN_APP',
                        'subject_type': 'Employee',
                        'subject_id': {'from': 'data.approver_employee_id'},
                        'destination': {'from': 'data.destination'},
                        'topic_code': 'automation.assignment',
                    },
                },
                {
                    'type': 'patch',
                    'config': {
                        'resource_type': 'ProjectAssignment',
                        'resource_id': {'from': 'data.assignment_id'},
                        'set': {
                            'risk_level': 'High',
                            'last_trigger_event_type': {'from': 'event_type'},
                        },
                    },
                },
            ],
        },
        actor={'id': 'admin-1', 'type': 'user'},
        trace_id='trace-rule-create',
    )
    assert rule.status == 'Active'
    assert rule.metadata['qc']['score']['rule_engine_consistency'] == 10
    assert 'normalize_trigger_event_types' in rule.metadata['qc']['auto_fixed']
    assert 'enforce_idempotent_execution' in rule.metadata['qc']['auto_fixed']

    event = {
        'event_name': 'ProjectAssignmentRequested',
        'tenant_id': 'tenant-acme',
        'source': 'project-service',
        'data': {
            'assignment_id': 'assign-1',
            'project_id': 'project-1',
            'employee_id': 'emp-1',
            'approver_employee_id': 'mgr-1',
            'allocation_percentage': 80,
            'destination': 'inbox:mgr-1',
        },
        'metadata': {'idempotency_key': 'assign-1-review', 'correlation_id': 'corr-assignment-1'},
    }

    first = service.consume_event(event, trace_id='trace-consume-1')
    second = service.consume_event(event, trace_id='trace-consume-2')

    assert first['matched_rules'] == 1
    assert len(first['results']) == 1
    assert first['results'][0]['status'] == 'executed'
    assert second['results'][0]['duplicate'] is True

    inbox = workflows.list_inbox(tenant_id='tenant-acme', actor_id='mgr-1')
    assert len(inbox['data']) == 1
    assert inbox['data'][0]['definition_code'] == 'project_assignment_review'
    assert len(notifications.messages) >= 1
    assert any(message.template_code == 'automation.assignment.flagged' for message in notifications.messages.values())
    state = service.get_subject_state(tenant_id='tenant-acme', resource_type='ProjectAssignment', resource_id='assign-1')
    assert state is not None
    assert state['risk_level'] == 'High'
    assert state['last_trigger_event_type'] == 'project.assignment.requested'

    records, _ = get_audit_service(str(tmp_path / 'audit.jsonl')).list_records(
        tenant_id='tenant-acme',
        entity='AutomationRule',
        limit=20,
    )
    assert any(record['action'] == 'automation_rule_created' for record in records)
    assert any(record['action'] == 'automation_rule_executed' for record in records)
    assert any(event_row['event_type'] == 'automation.rule.executed' for event_row in service.events)


def test_automation_api_wraps_d1_responses_and_lists_rules_and_executions(tmp_path: Path) -> None:
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    workflows.register_definition(
        tenant_id='tenant-default',
        code='candidate_followup',
        source_service='hiring-service',
        subject_type='Candidate',
        description='Follow up with candidates when interviews are scheduled.',
        steps=[
            {'name': 'Recruiter review', 'type': 'approval', 'assignee': 'recruiter-1', 'sla': 'PT4H'},
        ],
    )
    service = AutomationService(
        db_path=str(tmp_path / 'automation-api.sqlite3'),
        workflow_service=workflows,
        notification_service=notifications,
    )

    create_status, created = post_rule(
        service,
        {
            'tenant_id': 'tenant-default',
            'name': 'Interview follow-up',
            'trigger': {'event_types': ['InterviewScheduled']},
            'actions': [
                {
                    'kind': 'workflow',
                    'config': {
                        'definition_code': 'candidate_followup',
                        'subject_type': 'Candidate',
                        'subject_id': {'from': 'data.candidate_id'},
                    },
                },
            ],
        },
        trace_id='trace-api-rule',
    )
    assert create_status == 201
    assert created['status'] == 'success'
    rule_id = created['data']['rule_id']
    assert created['meta']['request_id'] == 'trace-api-rule'

    event_status, consumed = post_event(
        service,
        {
            'event_name': 'InterviewScheduled',
            'tenant_id': 'tenant-default',
            'source': 'hiring-service',
            'data': {'candidate_id': 'cand-1', 'scheduled_start': '2026-03-22T09:00:00+00:00'},
            'metadata': {'idempotency_key': 'cand-1-interview'},
        },
        trace_id='trace-api-event',
    )
    assert event_status == 202
    assert consumed['status'] == 'success'
    assert consumed['data']['matched_rules'] == 1

    list_status, listed = get_rules(service, {'tenant_id': 'tenant-default'}, trace_id='trace-api-list')
    assert list_status == 200
    assert listed['status'] == 'success'
    assert listed['data']['items'][0]['rule_id'] == rule_id
    assert listed['meta']['pagination']['count'] == 1

    execution_status, executions = get_executions(service, {'tenant_id': 'tenant-default', 'rule_id': rule_id}, trace_id='trace-api-exec')
    assert execution_status == 200
    assert executions['status'] == 'success'
    assert executions['data']['items'][0]['rule_id'] == rule_id
    assert executions['data']['items'][0]['status'] == 'executed'


def test_automation_studio_rejects_rules_that_embed_workflow_steps(tmp_path: Path) -> None:
    service = AutomationService(db_path=str(tmp_path / 'automation-invalid.sqlite3'))

    status, payload = post_rule(
        service,
        {
            'tenant_id': 'tenant-default',
            'name': 'Invalid workflow clone',
            'trigger': {'event_types': ['PayrollProcessed']},
            'actions': [
                {
                    'kind': 'workflow',
                    'config': {
                        'definition_code': 'payroll_review',
                        'subject_id': {'from': 'data.payroll_record_id'},
                        'steps': [{'name': 'Inline approval', 'assignee': 'fin-1'}],
                    },
                },
            ],
        },
        trace_id='trace-api-invalid',
    )

    assert status == 422
    assert payload['status'] == 'error'
    assert payload['error']['code'] == 'VALIDATION_ERROR'
    assert 'workflow_engine_duplication' in payload['error']['message']
