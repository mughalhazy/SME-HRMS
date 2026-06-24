from __future__ import annotations

from pathlib import Path

from audit_service.service import get_audit_service
from performance_service import PerformanceService
from workflow_service import WorkflowService
from notification_service import NotificationService


def _seed_employees(service: PerformanceService) -> None:
    service.register_employee_profile({
        'employee_id': 'emp-hr-1',
        'employee_number': 'E-001',
        'full_name': 'Harper HR',
        'department_id': 'dep-hr',
        'department_name': 'People Operations',
        'manager_employee_id': 'hr-admin',
    })
    service.register_employee_profile({
        'employee_id': 'emp-mgr-1',
        'employee_number': 'E-002',
        'full_name': 'Mina Manager',
        'department_id': 'dep-eng',
        'department_name': 'Engineering',
        'manager_employee_id': 'hr-admin',
    })
    service.register_employee_profile({
        'employee_id': 'emp-1',
        'employee_number': 'E-003',
        'full_name': 'Noah Bennett',
        'department_id': 'dep-eng',
        'department_name': 'Engineering',
        'manager_employee_id': 'emp-mgr-1',
    })
    service.register_employee_profile({
        'employee_id': 'hr-admin',
        'employee_number': 'E-004',
        'full_name': 'Ari Admin',
        'department_id': 'dep-hr',
        'department_name': 'People Operations',
        'manager_employee_id': None,
    })
    service.register_employee_profile({
        'employee_id': 'hr-director',
        'employee_number': 'E-005',
        'full_name': 'Dana Director',
        'department_id': 'dep-hr',
        'department_name': 'People Operations',
        'manager_employee_id': None,
    })


def test_performance_service_supports_cycles_goals_feedback_calibration_and_pips(tmp_path: Path) -> None:
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    service = PerformanceService(db_path=str(tmp_path / 'performance.sqlite3'), workflow_service=workflows, notification_service=notifications)
    _seed_employees(service)

    _, cycle = service.create_review_cycle(
        {
            'code': 'FY26-H1',
            'name': 'FY26 H1 Review Cycle',
            'review_period_start': '2026-01-01',
            'review_period_end': '2026-06-30',
            'owner_employee_id': 'emp-hr-1',
        },
        actor_id='emp-hr-1',
        trace_id='trace-cycle-create',
    )
    assert cycle['status'] == 'Draft'

    _, submitted_cycle = service.submit_review_cycle(cycle['review_cycle_id'], actor_id='emp-hr-1', trace_id='trace-cycle-submit')
    assert submitted_cycle['status'] == 'PendingApproval'
    assert submitted_cycle['workflow']['definition_code'] == 'performance_cycle_approval'

    _, opened = service.decide_review_cycle(cycle['review_cycle_id'], action='approve', actor_id='hr-admin', actor_role='Admin', trace_id='trace-cycle-open')
    assert opened['status'] == 'Open'
    assert opened['workflow']['metadata']['terminal_result'] == 'approved'

    _, goal = service.create_goal(
        {
            'review_cycle_id': cycle['review_cycle_id'],
            'employee_id': 'emp-1',
            'owner_employee_id': 'emp-1',
            'title': 'Ship workflow hardening',
            'description': 'Reduce approval latency and improve SLA compliance.',
            'metric_name': 'approval_sla_percent',
            'target_value': 99,
            'current_value': 45,
            'weight': 40,
        },
        actor_id='emp-1',
        trace_id='trace-goal-create',
    )
    assert goal['status'] == 'Draft'
    assert goal['progress_percent'] == round(45 / 99 * 100, 2)

    _, submitted_goal = service.submit_goal(goal['goal_id'], actor_id='emp-1', trace_id='trace-goal-submit')
    assert submitted_goal['status'] == 'Submitted'
    assert workflows.list_inbox(tenant_id='tenant-default', actor_id='emp-mgr-1')['data'][0]['subject_id'] == goal['goal_id']

    _, approved_goal = service.decide_goal(goal['goal_id'], action='approve', actor_id='emp-mgr-1', actor_role='Manager', trace_id='trace-goal-approve')
    assert approved_goal['status'] == 'Approved'
    assert approved_goal['workflow']['metadata']['terminal_result'] == 'approved'

    _, feedback = service.record_feedback(
        {
            'employee_id': 'emp-1',
            'provider_employee_id': 'emp-mgr-1',
            'review_cycle_id': cycle['review_cycle_id'],
            'feedback_type': 'Manager',
            'strengths': 'Consistent delivery',
            'opportunities': 'Delegate more often',
            'visibility': 'ManagerAndHR',
        },
        actor_id='emp-mgr-1',
        trace_id='trace-feedback',
    )
    assert feedback['employee']['full_name'] == 'Noah Bennett'

    _, calibration = service.create_calibration_session(
        {
            'review_cycle_id': cycle['review_cycle_id'],
            'facilitator_employee_id': 'emp-hr-1',
            'department_id': 'dep-eng',
            'proposed_rating': 4.3,
            'notes': 'High performance against strategic OKRs.',
        },
        actor_id='emp-hr-1',
        trace_id='trace-calibration-create',
    )
    _, submitted_calibration = service.submit_calibration_session(calibration['calibration_id'], actor_id='emp-hr-1', trace_id='trace-calibration-submit')
    assert submitted_calibration['status'] == 'Submitted'
    _, finalized_calibration = service.decide_calibration_session(calibration['calibration_id'], action='approve', actor_id='hr-admin', actor_role='Admin', final_rating=4.5, trace_id='trace-calibration-approve')
    assert finalized_calibration['status'] == 'Finalized'
    assert finalized_calibration['final_rating'] == 4.5

    _, pip = service.create_pip_plan(
        {
            'employee_id': 'emp-1',
            'manager_employee_id': 'emp-mgr-1',
            'review_cycle_id': cycle['review_cycle_id'],
            'reason': 'Need tighter release predictability.',
            'milestones': [
                {'title': 'Publish weekly recovery plan', 'due_date': '2026-07-07', 'success_metric': 'Plan shared every Monday'},
                {'title': 'Close high-priority delivery gaps', 'due_date': '2026-07-21', 'success_metric': 'Zero overdue P1 tasks'},
            ],
        },
        actor_id='emp-mgr-1',
        trace_id='trace-pip-create',
    )
    _, submitted_pip = service.submit_pip_plan(pip['pip_id'], actor_id='emp-mgr-1', trace_id='trace-pip-submit')
    assert submitted_pip['status'] == 'Submitted'
    _, active_pip = service.decide_pip_plan(pip['pip_id'], action='approve', actor_id='hr-admin', actor_role='Admin', trace_id='trace-pip-approve')
    assert active_pip['status'] == 'Active'

    _, progressed = service.update_pip_progress(pip['pip_id'], {'milestone_index': 0, 'completed': True}, actor_id='emp-mgr-1', trace_id='trace-pip-progress-1')
    assert progressed['completion_percent'] == 50.0
    _, completed = service.update_pip_progress(pip['pip_id'], {'milestone_index': 1, 'completed': True}, actor_id='emp-mgr-1', trace_id='trace-pip-progress-2')
    assert completed['status'] == 'Completed'
    assert completed['completion_percent'] == 100.0

    _, listed_goals = service.list_goals(employee_id='emp-1', status='Approved', limit=10)
    assert listed_goals['_pagination']['count'] == 1
    _, listed_feedback = service.list_feedback(employee_id='emp-1')
    assert len(listed_feedback['items']) == 1
    _, listed_pips = service.list_pip_plans(employee_id='emp-1', status='Completed')
    assert len(listed_pips['items']) == 1

    records, _ = get_audit_service().list_records(tenant_id='tenant-default', entity='PipPlan', limit=20)
    assert any(record['action'] == 'performance_pip_progress_updated' for record in records)
    assert any(event['legacy_event_name'] == 'PerformanceGoalApproved' for event in service.events)
    assert any(event['legacy_event_name'] == 'PerformancePipProgressUpdated' for event in service.events)


def test_performance_service_rejects_invalid_cross_service_references(tmp_path: Path) -> None:
    service = PerformanceService(db_path=str(tmp_path / 'performance-invalid.sqlite3'))
    _seed_employees(service)

    _, cycle = service.create_review_cycle(
        {
            'code': 'FY26-H2',
            'name': 'FY26 H2 Review Cycle',
            'review_period_start': '2026-07-01',
            'review_period_end': '2026-12-31',
            'owner_employee_id': 'emp-hr-1',
        },
        actor_id='emp-hr-1',
        trace_id='trace-cycle-2',
    )

    try:
        service.create_goal(
            {
                'review_cycle_id': cycle['review_cycle_id'],
                'employee_id': 'missing-employee',
                'owner_employee_id': 'missing-employee',
                'title': 'Broken goal',
                'description': 'Should fail',
                'metric_name': 'metric',
                'target_value': 1,
                'weight': 10,
            },
            actor_id='emp-1',
            trace_id='trace-invalid-goal',
        )
    except Exception as exc:  # pragma: no cover - exercised by assertions below
        assert 'employee-service read model' in str(exc)
    else:  # pragma: no cover
        raise AssertionError('expected missing employee reference to fail')


def test_performance_review_cycle_rejection_returns_to_draft(tmp_path: Path) -> None:
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    service = PerformanceService(db_path=str(tmp_path / 'performance-reject.sqlite3'), workflow_service=workflows, notification_service=notifications)
    _seed_employees(service)

    _, cycle = service.create_review_cycle(
        {
            'code': 'FY26-H2',
            'name': 'FY26 H2 Review Cycle',
            'review_period_start': '2026-07-01',
            'review_period_end': '2026-12-31',
            'owner_employee_id': 'emp-hr-1',
        },
        actor_id='emp-hr-1',
        trace_id='trace-cycle-create-reject',
    )

    _, submitted = service.submit_review_cycle(cycle['review_cycle_id'], actor_id='emp-hr-1', trace_id='trace-cycle-submit-reject')
    assert submitted['status'] == 'PendingApproval'

    _, rejected = service.decide_review_cycle(cycle['review_cycle_id'], action='reject', actor_id='hr-admin', actor_role='Admin', comment='Need revised dates', trace_id='trace-cycle-reject')
    assert rejected['status'] == 'Draft'
    assert rejected['workflow']['metadata']['terminal_result'] == 'rejected'
