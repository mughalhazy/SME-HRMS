from __future__ import annotations

from pathlib import Path

import pytest

from audit_service.service import get_audit_service
from notification_service import NotificationService
from project_service import ProjectService, ProjectServiceError
from workflow_service import WorkflowService


def _seed_employees(service: ProjectService) -> None:
    service.register_employee_profile(
        {
            'tenant_id': 'tenant-default',
            'employee_id': 'pm-001',
            'employee_number': 'E-001',
            'full_name': 'Priya Project',
            'department_id': 'dep-delivery',
            'department_name': 'Delivery',
            'manager_employee_id': 'ops-001',
        }
    )
    service.register_employee_profile(
        {
            'tenant_id': 'tenant-default',
            'employee_id': 'emp-001',
            'employee_number': 'E-002',
            'full_name': 'Alex Analyst',
            'department_id': 'dep-delivery',
            'department_name': 'Delivery',
            'manager_employee_id': 'pm-001',
        }
    )
    service.register_employee_profile(
        {
            'tenant_id': 'tenant-default',
            'employee_id': 'emp-002',
            'employee_number': 'E-003',
            'full_name': 'Sam Engineer',
            'department_id': 'dep-eng',
            'department_name': 'Engineering',
            'manager_employee_id': 'pm-001',
        }
    )
    service.register_employee_profile(
        {
            'tenant_id': 'tenant-default',
            'employee_id': 'ops-001',
            'employee_number': 'E-004',
            'full_name': 'Olivia Ops',
            'department_id': 'dep-ops',
            'department_name': 'Operations',
            'manager_employee_id': None,
        }
    )


def test_project_service_assignment_workflow_and_allocation_tracking(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('HRMS_AUDIT_LOG_PATH', str(tmp_path / 'audit.jsonl'))
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    service = ProjectService(db_path=str(tmp_path / 'projects.sqlite3'), workflow_service=workflows, notification_service=notifications)
    _seed_employees(service)

    _, project = service.create_project(
        {
            'tenant_id': 'tenant-default',
            'project_code': 'P-DELTA',
            'name': 'Delta Modernization',
            'description': 'ERP modernization rollout',
            'department_id': 'dep-delivery',
            'department_name': 'Delivery',
            'project_manager_employee_id': 'pm-001',
            'status': 'Active',
            'start_date': '2026-04-01',
            'end_date': '2026-08-31',
            'budget_amount': 250000,
            'requires_assignment_approval': True,
        },
        actor_id='pm-001',
        trace_id='trace-project-create',
    )
    assert project['project_code'] == 'P-DELTA'
    assert project['project_manager']['full_name'] == 'Priya Project'

    _, requested = service.assign_employee(
        {
            'tenant_id': 'tenant-default',
            'project_id': project['project_id'],
            'employee_id': 'emp-001',
            'role_name': 'Business Analyst',
            'allocation_percentage': 40,
            'effective_from': '2026-04-01',
            'effective_to': '2026-06-30',
        },
        actor_id='pm-001',
        trace_id='trace-project-assign',
    )
    assert requested['allocation_status'] == 'PendingApproval'
    assert requested['workflow']['definition_code'] == 'project_assignment_approval'

    _, approved = service.decide_assignment(
        requested['assignment_id'],
        action='approve',
        actor_id='pm-001',
        actor_role='Manager',
        tenant_id='tenant-default',
        trace_id='trace-project-approve',
    )
    assert approved['allocation_status'] == 'Allocated'
    assert approved['workflow']['metadata']['terminal_result'] == 'approved'

    _, update_requested = service.update_assignment_allocation(
        requested['assignment_id'],
        {'tenant_id': 'tenant-default', 'allocation_percentage': 60},
        actor_id='pm-001',
        trace_id='trace-project-update-request',
    )
    assert update_requested['allocation_status'] == 'PendingApproval'

    _, updated = service.decide_assignment(
        requested['assignment_id'],
        action='approve',
        actor_id='pm-001',
        actor_role='Manager',
        tenant_id='tenant-default',
        trace_id='trace-project-update-approve',
    )
    assert updated['allocation_status'] == 'Allocated'
    assert updated['allocation_percentage'] == 60

    _, released = service.release_assignment(
        requested['assignment_id'],
        {'tenant_id': 'tenant-default', 'effective_to': '2026-06-30'},
        actor_id='pm-001',
        trace_id='trace-project-release',
    )
    assert released['allocation_status'] == 'Released'

    _, history = service.list_allocation_history(requested['assignment_id'], tenant_id='tenant-default')
    actions = [row['action'] for row in history['items']]
    assert 'assignment_requested' in actions
    assert 'assignment_allocated' in actions
    assert 'allocation_change_requested' in actions
    assert 'allocation_updated' in actions
    assert 'assignment_released' in actions

    _, project_view = service.get_project(project['project_id'], tenant_id='tenant-default')
    assert project_view['assignment_count'] == 1
    assert project_view['active_assignment_count'] == 0
    assert project_view['total_allocated_percentage'] == 0

    audit_records, _ = get_audit_service(log_path=str(tmp_path / 'audit.jsonl')).list_records(
        tenant_id='tenant-default',
        entity='ProjectAssignment',
        entity_id=requested['assignment_id'],
        limit=20,
    )
    assert {record['action'] for record in audit_records} >= {
        'project_assignment_created',
        'project_assignment_decided',
        'project_assignment_updated',
        'project_assignment_released',
    }

    legacy_names = [event['legacy_event_name'] for event in service.events]
    assert 'ProjectCreated' in legacy_names
    assert 'ProjectAssignmentRequested' in legacy_names
    assert 'ProjectAssignmentAllocated' in legacy_names
    assert 'ProjectAllocationUpdated' in legacy_names
    assert 'ProjectAssignmentReleased' in legacy_names
    assert any(message.event_name == 'WorkflowTaskAssigned' for message in notifications.messages.values())
    assert any(row.payload['tenant_id'] == 'tenant-default' for row in service.event_outbox.list_events(tenant_id='tenant-default'))


def test_project_service_enforces_cross_project_allocation_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('HRMS_AUDIT_LOG_PATH', str(tmp_path / 'audit-limit.jsonl'))
    service = ProjectService(db_path=str(tmp_path / 'projects-limit.sqlite3'))
    _seed_employees(service)

    _, first_project = service.create_project(
        {
            'tenant_id': 'tenant-default',
            'project_code': 'P-ALPHA',
            'name': 'Alpha Rollout',
            'project_manager_employee_id': 'pm-001',
            'status': 'Active',
            'start_date': '2026-04-01',
        },
        actor_id='pm-001',
    )
    _, second_project = service.create_project(
        {
            'tenant_id': 'tenant-default',
            'project_code': 'P-BETA',
            'name': 'Beta Rollout',
            'project_manager_employee_id': 'pm-001',
            'status': 'Active',
            'start_date': '2026-04-01',
        },
        actor_id='pm-001',
    )

    _, allocated = service.assign_employee(
        {
            'tenant_id': 'tenant-default',
            'project_id': first_project['project_id'],
            'employee_id': 'emp-002',
            'role_name': 'Engineer',
            'allocation_percentage': 70,
            'effective_from': '2026-04-01',
        },
        actor_id='pm-001',
    )
    assert allocated['allocation_status'] == 'Allocated'

    with pytest.raises(ProjectServiceError) as exc:
        service.assign_employee(
            {
                'tenant_id': 'tenant-default',
                'project_id': second_project['project_id'],
                'employee_id': 'emp-002',
                'role_name': 'Engineer',
                'allocation_percentage': 40,
                'effective_from': '2026-04-15',
            },
            actor_id='pm-001',
            trace_id='trace-project-overalloc',
        )
    assert exc.value.status_code == 422
    assert exc.value.payload['error']['code'] == 'ALLOCATION_LIMIT_EXCEEDED'


def test_project_service_guards_tenant_scope_and_rejected_assignments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('HRMS_AUDIT_LOG_PATH', str(tmp_path / 'audit-tenant.jsonl'))
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    service = ProjectService(db_path=str(tmp_path / 'projects-tenant.sqlite3'), workflow_service=workflows, notification_service=notifications)
    _seed_employees(service)
    service.register_employee_profile(
        {
            'tenant_id': 'tenant-other',
            'employee_id': 'other-pm',
            'employee_number': 'E-101',
            'full_name': 'Other Tenant PM',
            'department_id': 'dep-other',
            'department_name': 'Other',
            'manager_employee_id': None,
        }
    )
    service.register_employee_profile(
        {
            'tenant_id': 'tenant-other',
            'employee_id': 'other-emp',
            'employee_number': 'E-102',
            'full_name': 'Other Tenant Employee',
            'department_id': 'dep-other',
            'department_name': 'Other',
            'manager_employee_id': 'other-pm',
        }
    )

    _, project = service.create_project(
        {
            'tenant_id': 'tenant-other',
            'project_code': 'P-OTHER',
            'name': 'Other Tenant Project',
            'project_manager_employee_id': 'other-pm',
            'status': 'Active',
            'start_date': '2026-05-01',
            'requires_assignment_approval': True,
        },
        actor_id='other-pm',
    )
    _, requested = service.assign_employee(
        {
            'tenant_id': 'tenant-other',
            'project_id': project['project_id'],
            'employee_id': 'other-emp',
            'role_name': 'Consultant',
            'allocation_percentage': 50,
            'effective_from': '2026-05-01',
        },
        actor_id='other-pm',
    )

    with pytest.raises(ProjectServiceError) as tenant_exc:
        service.get_project(project['project_id'], tenant_id='tenant-default')
    assert tenant_exc.value.payload['error']['code'] == 'TENANT_SCOPE_VIOLATION'

    _, rejected = service.decide_assignment(
        requested['assignment_id'],
        action='reject',
        actor_id='other-pm',
        actor_role='Manager',
        tenant_id='tenant-other',
    )
    assert rejected['allocation_status'] == 'Rejected'
