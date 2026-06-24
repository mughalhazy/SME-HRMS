from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from threading import RLock
from time import perf_counter
from typing import Any
from uuid import uuid4

from audit_service.service import emit_audit_record
from event_contract import EventRegistry, emit_canonical_event
from notification_service import NotificationService
from persistent_store import PersistentKVStore
from resilience import CentralErrorLogger, Observability
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id
from workflow_support import require_terminal_workflow_result, resolve_workflow_action
from workflow_service import WorkflowService, WorkflowServiceError


class PerformanceServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str, trace_id: str, details: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = {
            'error': {
                'code': code,
                'message': message,
                'details': details or [],
                'trace_id': trace_id,
            }
        }


@dataclass(slots=True)
class EmployeeSnapshot:
    tenant_id: str
    employee_id: str
    employee_number: str
    full_name: str
    department_id: str
    department_name: str
    manager_employee_id: str | None
    status: str = 'Active'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReviewCycle:
    tenant_id: str
    review_cycle_id: str
    code: str
    name: str
    review_period_start: date
    review_period_end: date
    status: str
    owner_employee_id: str
    workflow_id: str | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['review_period_start'] = self.review_period_start.isoformat()
        payload['review_period_end'] = self.review_period_end.isoformat()
        payload['created_at'] = self.created_at.isoformat()
        payload['updated_at'] = self.updated_at.isoformat()
        return payload


@dataclass(slots=True)
class GoalRecord:
    tenant_id: str
    goal_id: str
    review_cycle_id: str
    employee_id: str
    owner_employee_id: str
    title: str
    description: str
    metric_name: str
    target_value: float
    current_value: float
    weight: float
    status: str
    workflow_id: str | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['approved_at'] = self.approved_at.isoformat() if self.approved_at else None
        payload['created_at'] = self.created_at.isoformat()
        payload['updated_at'] = self.updated_at.isoformat()
        return payload


@dataclass(slots=True)
class FeedbackRecord:
    tenant_id: str
    feedback_id: str
    employee_id: str
    provider_employee_id: str
    review_cycle_id: str | None
    feedback_type: str
    strengths: str
    opportunities: str
    visibility: str
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['created_at'] = self.created_at.isoformat()
        return payload


@dataclass(slots=True)
class CalibrationSession:
    tenant_id: str
    calibration_id: str
    review_cycle_id: str
    facilitator_employee_id: str
    department_id: str
    proposed_rating: float
    final_rating: float | None
    notes: str
    status: str
    workflow_id: str | None
    finalized_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['finalized_at'] = self.finalized_at.isoformat() if self.finalized_at else None
        payload['created_at'] = self.created_at.isoformat()
        payload['updated_at'] = self.updated_at.isoformat()
        return payload


@dataclass(slots=True)
class PipMilestone:
    title: str
    due_date: str
    success_metric: str
    completed: bool = False
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PipPlan:
    tenant_id: str
    pip_id: str
    employee_id: str
    manager_employee_id: str
    reason: str
    review_cycle_id: str | None
    status: str
    workflow_id: str | None
    started_at: datetime | None
    closed_at: datetime | None
    milestones: list[PipMilestone]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            'tenant_id': self.tenant_id,
            'pip_id': self.pip_id,
            'employee_id': self.employee_id,
            'manager_employee_id': self.manager_employee_id,
            'reason': self.reason,
            'review_cycle_id': self.review_cycle_id,
            'status': self.status,
            'workflow_id': self.workflow_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'milestones': [milestone.to_dict() for milestone in self.milestones],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class PerformanceService:
    REVIEW_CYCLE_STATUSES = {'Draft', 'PendingApproval', 'Open', 'Closed'}
    GOAL_STATUSES = {'Draft', 'Submitted', 'Approved', 'Rejected'}
    FEEDBACK_TYPES = {'Manager', 'Peer', 'Self', 'Upward'}
    FEEDBACK_VISIBILITY = {'Private', 'Employee', 'ManagerAndHR'}
    CALIBRATION_STATUSES = {'Draft', 'Submitted', 'Finalized', 'Rejected'}
    PIP_STATUSES = {'Draft', 'Submitted', 'Active', 'Completed', 'Cancelled', 'Rejected'}

    def __init__(self, db_path: str | None = None, *, workflow_service: WorkflowService | None = None, notification_service: NotificationService | None = None) -> None:
        self.employee_snapshots = PersistentKVStore[str, EmployeeSnapshot](service='performance-service', namespace='employee_snapshots', db_path=db_path)
        shared_db_path = self.employee_snapshots.db_path
        self.review_cycles = PersistentKVStore[str, ReviewCycle](service='performance-service', namespace='review_cycles', db_path=shared_db_path)
        self.goals = PersistentKVStore[str, GoalRecord](service='performance-service', namespace='goals', db_path=shared_db_path)
        self.feedback = PersistentKVStore[str, FeedbackRecord](service='performance-service', namespace='feedback', db_path=shared_db_path)
        self.calibrations = PersistentKVStore[str, CalibrationSession](service='performance-service', namespace='calibrations', db_path=shared_db_path)
        self.pips = PersistentKVStore[str, PipPlan](service='performance-service', namespace='pips', db_path=shared_db_path)
        self.events: list[dict[str, Any]] = []
        self.tenant_id = DEFAULT_TENANT_ID
        self.event_registry = EventRegistry()
        self.notification_service = notification_service or NotificationService()
        self.workflow_service = workflow_service or WorkflowService(notification_service=self.notification_service)
        self.error_logger = CentralErrorLogger('performance-service')
        self.observability = Observability('performance-service')
        self._lock = RLock()
        self._register_workflows()

    def register_employee_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        snapshot = EmployeeSnapshot(
            tenant_id=tenant_id,
            employee_id=str(payload['employee_id']),
            employee_number=str(payload.get('employee_number') or payload['employee_id']),
            full_name=str(payload['full_name']),
            department_id=str(payload['department_id']),
            department_name=str(payload.get('department_name') or payload['department_id']),
            manager_employee_id=str(payload['manager_employee_id']) if payload.get('manager_employee_id') else None,
            status=str(payload.get('status') or 'Active'),
        )
        self.employee_snapshots[snapshot.employee_id] = snapshot
        return snapshot.to_dict()

    def create_review_cycle(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = trace_id or self.observability.trace_id()
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        owner = self._require_employee(payload['owner_employee_id'], tenant_id=tenant_id, field='owner_employee_id')
        review_period_start = self._coerce_date(payload['review_period_start'], 'review_period_start')
        review_period_end = self._coerce_date(payload['review_period_end'], 'review_period_end')
        if review_period_end < review_period_start:
            raise self._error(422, 'VALIDATION_ERROR', 'review_period_end must be on or after review_period_start', trace, [{'field': 'review_period_end', 'reason': 'must be >= review_period_start'}])

        code = str(payload['code']).strip()
        if not code:
            raise self._error(422, 'VALIDATION_ERROR', 'code is required', trace, [{'field': 'code', 'reason': 'must be a non-empty string'}])
        if any(cycle.tenant_id == tenant_id and cycle.code == code for cycle in self.review_cycles.values()):
            raise self._error(409, 'CONFLICT', 'review cycle code already exists', trace)

        now = self._now()
        cycle = ReviewCycle(
            tenant_id=tenant_id,
            review_cycle_id=str(uuid4()),
            code=code,
            name=str(payload['name']).strip(),
            review_period_start=review_period_start,
            review_period_end=review_period_end,
            status='Draft',
            owner_employee_id=owner.employee_id,
            workflow_id=None,
            created_at=now,
            updated_at=now,
        )
        self.review_cycles[cycle.review_cycle_id] = cycle
        self._audit('performance_review_cycle_created', 'ReviewCycle', cycle.review_cycle_id, {}, cycle.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
        self._emit('PerformanceReviewCycleCreated', {'review_cycle_id': cycle.review_cycle_id, 'code': cycle.code, 'status': cycle.status}, tenant_id=tenant_id, correlation_id=trace)
        self.observability.track('create_review_cycle', trace_id=trace, started_at=started, success=True, context={'status': 201})
        return 201, self._review_cycle_payload(cycle)

    def submit_review_cycle(self, review_cycle_id: str, *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        cycle = self._require_review_cycle(review_cycle_id)
        trace = trace_id or self.observability.trace_id()
        if cycle.status != 'Draft':
            raise self._error(409, 'CONFLICT', 'only Draft review cycles can be submitted', trace)
        owner = self._require_employee(cycle.owner_employee_id, tenant_id=cycle.tenant_id, field='owner_employee_id')
        approver_assignee = owner.manager_employee_id or 'hr-admin'
        workflow = self.workflow_service.start_workflow(
            tenant_id=cycle.tenant_id,
            definition_code='performance_cycle_approval',
            source_service='performance-service',
            subject_type='ReviewCycle',
            subject_id=cycle.review_cycle_id,
            actor_id=actor_id,
            actor_type=actor_type,
            context={'approver_assignee': approver_assignee, 'escalation_assignee': 'hr-admin'},
            trace_id=trace,
        )
        before = cycle.to_dict()
        cycle.status = 'PendingApproval'
        cycle.workflow_id = workflow['workflow_id']
        cycle.updated_at = self._now()
        self.review_cycles[cycle.review_cycle_id] = cycle
        self._audit('performance_review_cycle_submitted', 'ReviewCycle', cycle.review_cycle_id, before, cycle.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=cycle.tenant_id, trace_id=trace)
        return 200, self._review_cycle_payload(cycle)

    def decide_review_cycle(self, review_cycle_id: str, *, action: str, actor_id: str, actor_type: str = 'user', actor_role: str | None = None, comment: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        cycle = self._require_review_cycle(review_cycle_id)
        trace = trace_id or self.observability.trace_id()
        if cycle.status != 'PendingApproval' or not cycle.workflow_id:
            raise self._error(409, 'CONFLICT', 'review cycle is not awaiting approval', trace)
        before = cycle.to_dict()
        workflow = self._resolve_workflow(cycle.workflow_id, cycle.tenant_id, action=action, actor_id=actor_id, actor_type=actor_type, actor_role=actor_role, comment=comment, trace_id=trace)
        terminal_result = self._require_terminal_workflow_result(workflow, action=action, trace_id=trace)
        cycle.status = 'Open' if terminal_result == 'approved' else 'Draft'
        cycle.updated_at = self._now()
        self.review_cycles[cycle.review_cycle_id] = cycle
        if terminal_result == 'approved':
            self._audit('performance_review_cycle_opened', 'ReviewCycle', cycle.review_cycle_id, before, cycle.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=cycle.tenant_id, trace_id=trace)
            self._emit('PerformanceReviewCycleOpened', {'review_cycle_id': cycle.review_cycle_id, 'status': cycle.status, 'workflow_id': cycle.workflow_id}, tenant_id=cycle.tenant_id, correlation_id=trace)
        else:
            self._audit('performance_review_cycle_rejected', 'ReviewCycle', cycle.review_cycle_id, before, cycle.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=cycle.tenant_id, trace_id=trace)
        payload = self._review_cycle_payload(cycle)
        payload['workflow'] = workflow
        return 200, payload

    def close_review_cycle(self, review_cycle_id: str, *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        cycle = self._require_review_cycle(review_cycle_id)
        trace = trace_id or self.observability.trace_id()
        if cycle.status != 'Open':
            raise self._error(409, 'CONFLICT', 'only Open review cycles can be closed', trace)
        before = cycle.to_dict()
        cycle.status = 'Closed'
        cycle.updated_at = self._now()
        self.review_cycles[cycle.review_cycle_id] = cycle
        self._audit('performance_review_cycle_closed', 'ReviewCycle', cycle.review_cycle_id, before, cycle.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=cycle.tenant_id, trace_id=trace)
        self._emit('PerformanceReviewCycleClosed', {'review_cycle_id': cycle.review_cycle_id, 'status': cycle.status}, tenant_id=cycle.tenant_id, correlation_id=trace)
        return 200, self._review_cycle_payload(cycle)

    def create_goal(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = trace_id or self.observability.trace_id()
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        cycle = self._require_review_cycle(payload['review_cycle_id'])
        assert_tenant_access(cycle.tenant_id, tenant_id)
        employee = self._require_employee(payload['employee_id'], tenant_id=tenant_id, field='employee_id')
        owner = self._require_employee(payload.get('owner_employee_id') or payload['employee_id'], tenant_id=tenant_id, field='owner_employee_id')
        if cycle.status == 'Closed':
            raise self._error(409, 'CONFLICT', 'cannot add goals to a Closed review cycle', trace)
        target_value = self._coerce_float(payload['target_value'], 'target_value', minimum=0.0)
        weight = self._coerce_float(payload['weight'], 'weight', minimum=0.0, maximum=100.0)
        now = self._now()
        goal = GoalRecord(
            tenant_id=tenant_id,
            goal_id=str(uuid4()),
            review_cycle_id=cycle.review_cycle_id,
            employee_id=employee.employee_id,
            owner_employee_id=owner.employee_id,
            title=str(payload['title']).strip(),
            description=str(payload.get('description') or '').strip(),
            metric_name=str(payload['metric_name']).strip(),
            target_value=target_value,
            current_value=self._coerce_float(payload.get('current_value', 0.0), 'current_value', minimum=0.0),
            weight=weight,
            status='Draft',
            workflow_id=None,
            approved_at=None,
            created_at=now,
            updated_at=now,
        )
        self.goals[goal.goal_id] = goal
        self._audit('performance_goal_created', 'Goal', goal.goal_id, {}, goal.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
        self._emit('PerformanceGoalCreated', {'goal_id': goal.goal_id, 'employee_id': goal.employee_id, 'status': goal.status}, tenant_id=tenant_id, correlation_id=trace)
        self.observability.track('create_goal', trace_id=trace, started_at=started, success=True, context={'status': 201})
        return 201, self._goal_payload(goal)

    def submit_goal(self, goal_id: str, *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        goal = self._require_goal(goal_id)
        trace = trace_id or self.observability.trace_id()
        if goal.status != 'Draft':
            raise self._error(409, 'CONFLICT', 'only Draft goals can be submitted', trace)
        employee = self._require_employee(goal.employee_id, tenant_id=goal.tenant_id, field='employee_id')
        approver_assignee = employee.manager_employee_id or 'hr-admin'
        workflow = self.workflow_service.start_workflow(
            tenant_id=goal.tenant_id,
            definition_code='performance_goal_approval',
            source_service='performance-service',
            subject_type='Goal',
            subject_id=goal.goal_id,
            actor_id=actor_id,
            actor_type=actor_type,
            context={'approver_assignee': approver_assignee, 'escalation_assignee': 'hr-admin'},
            trace_id=trace,
        )
        before = goal.to_dict()
        goal.status = 'Submitted'
        goal.workflow_id = workflow['workflow_id']
        goal.updated_at = self._now()
        self.goals[goal.goal_id] = goal
        self._audit('performance_goal_submitted', 'Goal', goal.goal_id, before, goal.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=goal.tenant_id, trace_id=trace)
        self._emit('PerformanceGoalSubmitted', {'goal_id': goal.goal_id, 'employee_id': goal.employee_id, 'status': goal.status}, tenant_id=goal.tenant_id, correlation_id=trace)
        return 200, self._goal_payload(goal)

    def decide_goal(self, goal_id: str, *, action: str, actor_id: str, actor_type: str = 'user', actor_role: str | None = None, comment: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        goal = self._require_goal(goal_id)
        trace = trace_id or self.observability.trace_id()
        if goal.status != 'Submitted' or not goal.workflow_id:
            raise self._error(409, 'CONFLICT', 'goal is not awaiting approval', trace)
        before = goal.to_dict()
        workflow = self._resolve_workflow(goal.workflow_id, goal.tenant_id, action=action, actor_id=actor_id, actor_type=actor_type, actor_role=actor_role, comment=comment, trace_id=trace)
        self._require_terminal_workflow_result(workflow, action=action, trace_id=trace)
        goal.status = 'Approved' if action == 'approve' else 'Rejected'
        goal.approved_at = self._now() if action == 'approve' else None
        goal.updated_at = self._now()
        self.goals[goal.goal_id] = goal
        self._audit(f'performance_goal_{goal.status.lower()}', 'Goal', goal.goal_id, before, goal.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=goal.tenant_id, trace_id=trace)
        self._emit(f'PerformanceGoal{goal.status}', {'goal_id': goal.goal_id, 'employee_id': goal.employee_id, 'status': goal.status}, tenant_id=goal.tenant_id, correlation_id=trace)
        payload = self._goal_payload(goal)
        payload['workflow'] = workflow
        return 200, payload

    def record_feedback(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = trace_id or self.observability.trace_id()
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        employee = self._require_employee(payload['employee_id'], tenant_id=tenant_id, field='employee_id')
        provider = self._require_employee(payload['provider_employee_id'], tenant_id=tenant_id, field='provider_employee_id')
        feedback_type = str(payload['feedback_type'])
        visibility = str(payload.get('visibility') or 'ManagerAndHR')
        if feedback_type not in self.FEEDBACK_TYPES:
            raise self._error(422, 'VALIDATION_ERROR', 'invalid feedback_type', trace, [{'field': 'feedback_type', 'reason': f'must be one of {sorted(self.FEEDBACK_TYPES)}'}])
        if visibility not in self.FEEDBACK_VISIBILITY:
            raise self._error(422, 'VALIDATION_ERROR', 'invalid visibility', trace, [{'field': 'visibility', 'reason': f'must be one of {sorted(self.FEEDBACK_VISIBILITY)}'}])
        review_cycle_id = payload.get('review_cycle_id')
        if review_cycle_id is not None:
            cycle = self._require_review_cycle(review_cycle_id)
            assert_tenant_access(cycle.tenant_id, tenant_id)
        feedback = FeedbackRecord(
            tenant_id=tenant_id,
            feedback_id=str(uuid4()),
            employee_id=employee.employee_id,
            provider_employee_id=provider.employee_id,
            review_cycle_id=str(review_cycle_id) if review_cycle_id else None,
            feedback_type=feedback_type,
            strengths=str(payload.get('strengths') or '').strip(),
            opportunities=str(payload.get('opportunities') or '').strip(),
            visibility=visibility,
            created_at=self._now(),
        )
        self.feedback[feedback.feedback_id] = feedback
        self._audit('performance_feedback_recorded', 'Feedback', feedback.feedback_id, {}, feedback.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
        self._emit('PerformanceFeedbackRecorded', {'feedback_id': feedback.feedback_id, 'employee_id': feedback.employee_id, 'feedback_type': feedback.feedback_type}, tenant_id=tenant_id, correlation_id=trace)
        return 201, self._feedback_payload(feedback)

    def create_calibration_session(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = trace_id or self.observability.trace_id()
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        cycle = self._require_review_cycle(payload['review_cycle_id'])
        assert_tenant_access(cycle.tenant_id, tenant_id)
        facilitator = self._require_employee(payload['facilitator_employee_id'], tenant_id=tenant_id, field='facilitator_employee_id')
        department_id = str(payload['department_id'])
        session = CalibrationSession(
            tenant_id=tenant_id,
            calibration_id=str(uuid4()),
            review_cycle_id=cycle.review_cycle_id,
            facilitator_employee_id=facilitator.employee_id,
            department_id=department_id,
            proposed_rating=self._coerce_float(payload['proposed_rating'], 'proposed_rating', minimum=1.0, maximum=5.0),
            final_rating=None,
            notes=str(payload.get('notes') or '').strip(),
            status='Draft',
            workflow_id=None,
            finalized_at=None,
            created_at=self._now(),
            updated_at=self._now(),
        )
        self.calibrations[session.calibration_id] = session
        self._audit('performance_calibration_created', 'CalibrationSession', session.calibration_id, {}, session.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
        self._emit('PerformanceCalibrationCreated', {'calibration_id': session.calibration_id, 'review_cycle_id': session.review_cycle_id, 'status': session.status}, tenant_id=tenant_id, correlation_id=trace)
        return 201, self._calibration_payload(session)

    def submit_calibration_session(self, calibration_id: str, *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        session = self._require_calibration(calibration_id)
        trace = trace_id or self.observability.trace_id()
        if session.status != 'Draft':
            raise self._error(409, 'CONFLICT', 'only Draft calibration sessions can be submitted', trace)
        workflow = self.workflow_service.start_workflow(
            tenant_id=session.tenant_id,
            definition_code='performance_calibration_signoff',
            source_service='performance-service',
            subject_type='CalibrationSession',
            subject_id=session.calibration_id,
            actor_id=actor_id,
            actor_type=actor_type,
            context={'approver_assignee': 'hr-admin', 'escalation_assignee': 'hr-director'},
            trace_id=trace,
        )
        before = session.to_dict()
        session.status = 'Submitted'
        session.workflow_id = workflow['workflow_id']
        session.updated_at = self._now()
        self.calibrations[session.calibration_id] = session
        self._audit('performance_calibration_submitted', 'CalibrationSession', session.calibration_id, before, session.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=session.tenant_id, trace_id=trace)
        self._emit('PerformanceCalibrationSubmitted', {'calibration_id': session.calibration_id, 'status': session.status}, tenant_id=session.tenant_id, correlation_id=trace)
        return 200, self._calibration_payload(session)

    def decide_calibration_session(self, calibration_id: str, *, action: str, actor_id: str, actor_type: str = 'user', actor_role: str | None = None, final_rating: float | None = None, comment: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        session = self._require_calibration(calibration_id)
        trace = trace_id or self.observability.trace_id()
        if session.status != 'Submitted' or not session.workflow_id:
            raise self._error(409, 'CONFLICT', 'calibration session is not awaiting sign-off', trace)
        before = session.to_dict()
        workflow = self._resolve_workflow(session.workflow_id, session.tenant_id, action=action, actor_id=actor_id, actor_type=actor_type, actor_role=actor_role, comment=comment, trace_id=trace)
        self._require_terminal_workflow_result(workflow, action=action, trace_id=trace)
        session.status = 'Finalized' if action == 'approve' else 'Rejected'
        session.final_rating = self._coerce_float(final_rating if final_rating is not None else session.proposed_rating, 'final_rating', minimum=1.0, maximum=5.0) if action == 'approve' else None
        session.finalized_at = self._now() if action == 'approve' else None
        session.updated_at = self._now()
        self.calibrations[session.calibration_id] = session
        self._audit(f'performance_calibration_{session.status.lower()}', 'CalibrationSession', session.calibration_id, before, session.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=session.tenant_id, trace_id=trace)
        self._emit(f'PerformanceCalibration{session.status}', {'calibration_id': session.calibration_id, 'status': session.status}, tenant_id=session.tenant_id, correlation_id=trace)
        payload = self._calibration_payload(session)
        payload['workflow'] = workflow
        return 200, payload

    def create_pip_plan(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = trace_id or self.observability.trace_id()
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        employee = self._require_employee(payload['employee_id'], tenant_id=tenant_id, field='employee_id')
        manager = self._require_employee(payload.get('manager_employee_id') or employee.manager_employee_id, tenant_id=tenant_id, field='manager_employee_id')
        milestones_payload = payload.get('milestones') or []
        if not isinstance(milestones_payload, list) or not milestones_payload:
            raise self._error(422, 'VALIDATION_ERROR', 'milestones are required', trace, [{'field': 'milestones', 'reason': 'must contain at least one milestone'}])
        milestones = [
            PipMilestone(
                title=str(item['title']).strip(),
                due_date=self._coerce_date(item['due_date'], 'milestones.due_date').isoformat(),
                success_metric=str(item['success_metric']).strip(),
            )
            for item in milestones_payload
        ]
        plan = PipPlan(
            tenant_id=tenant_id,
            pip_id=str(uuid4()),
            employee_id=employee.employee_id,
            manager_employee_id=manager.employee_id,
            reason=str(payload['reason']).strip(),
            review_cycle_id=str(payload['review_cycle_id']) if payload.get('review_cycle_id') else None,
            status='Draft',
            workflow_id=None,
            started_at=None,
            closed_at=None,
            milestones=milestones,
            created_at=self._now(),
            updated_at=self._now(),
        )
        self.pips[plan.pip_id] = plan
        self._audit('performance_pip_created', 'PipPlan', plan.pip_id, {}, plan.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
        self._emit('PerformancePipCreated', {'pip_id': plan.pip_id, 'employee_id': plan.employee_id, 'status': plan.status}, tenant_id=tenant_id, correlation_id=trace)
        return 201, self._pip_payload(plan)

    def submit_pip_plan(self, pip_id: str, *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        plan = self._require_pip(pip_id)
        trace = trace_id or self.observability.trace_id()
        if plan.status != 'Draft':
            raise self._error(409, 'CONFLICT', 'only Draft PIP plans can be submitted', trace)
        workflow = self.workflow_service.start_workflow(
            tenant_id=plan.tenant_id,
            definition_code='performance_pip_approval',
            source_service='performance-service',
            subject_type='PipPlan',
            subject_id=plan.pip_id,
            actor_id=actor_id,
            actor_type=actor_type,
            context={'approver_assignee': 'hr-admin', 'escalation_assignee': 'hr-director'},
            trace_id=trace,
        )
        before = plan.to_dict()
        plan.status = 'Submitted'
        plan.workflow_id = workflow['workflow_id']
        plan.updated_at = self._now()
        self.pips[plan.pip_id] = plan
        self._audit('performance_pip_submitted', 'PipPlan', plan.pip_id, before, plan.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=plan.tenant_id, trace_id=trace)
        self._emit('PerformancePipSubmitted', {'pip_id': plan.pip_id, 'employee_id': plan.employee_id, 'status': plan.status}, tenant_id=plan.tenant_id, correlation_id=trace)
        return 200, self._pip_payload(plan)

    def decide_pip_plan(self, pip_id: str, *, action: str, actor_id: str, actor_type: str = 'user', actor_role: str | None = None, comment: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        plan = self._require_pip(pip_id)
        trace = trace_id or self.observability.trace_id()
        if plan.status != 'Submitted' or not plan.workflow_id:
            raise self._error(409, 'CONFLICT', 'PIP plan is not awaiting approval', trace)
        before = plan.to_dict()
        workflow = self._resolve_workflow(plan.workflow_id, plan.tenant_id, action=action, actor_id=actor_id, actor_type=actor_type, actor_role=actor_role, comment=comment, trace_id=trace)
        self._require_terminal_workflow_result(workflow, action=action, trace_id=trace)
        plan.status = 'Active' if action == 'approve' else 'Rejected'
        plan.started_at = self._now() if action == 'approve' else None
        plan.updated_at = self._now()
        self.pips[plan.pip_id] = plan
        self._audit(f'performance_pip_{plan.status.lower()}', 'PipPlan', plan.pip_id, before, plan.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=plan.tenant_id, trace_id=trace)
        self._emit(f'PerformancePip{plan.status}', {'pip_id': plan.pip_id, 'employee_id': plan.employee_id, 'status': plan.status}, tenant_id=plan.tenant_id, correlation_id=trace)
        payload = self._pip_payload(plan)
        payload['workflow'] = workflow
        return 200, payload

    def update_pip_progress(self, pip_id: str, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        plan = self._require_pip(pip_id)
        trace = trace_id or self.observability.trace_id()
        if plan.status != 'Active':
            raise self._error(409, 'CONFLICT', 'only Active PIP plans can be updated', trace)
        milestone_index = int(payload['milestone_index'])
        if milestone_index < 0 or milestone_index >= len(plan.milestones):
            raise self._error(422, 'VALIDATION_ERROR', 'milestone_index is invalid', trace, [{'field': 'milestone_index', 'reason': 'must refer to an existing milestone'}])
        before = plan.to_dict()
        milestone = plan.milestones[milestone_index]
        milestone.completed = bool(payload.get('completed', True))
        milestone.completed_at = self._now().isoformat() if milestone.completed else None
        if all(item.completed for item in plan.milestones):
            plan.status = 'Completed'
            plan.closed_at = self._now()
        plan.updated_at = self._now()
        self.pips[plan.pip_id] = plan
        self._audit('performance_pip_progress_updated', 'PipPlan', plan.pip_id, before, plan.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=plan.tenant_id, trace_id=trace)
        self._emit('PerformancePipProgressUpdated', {'pip_id': plan.pip_id, 'status': plan.status, 'milestone_index': milestone_index}, tenant_id=plan.tenant_id, correlation_id=trace)
        return 200, self._pip_payload(plan)

    def get_review_cycle(self, review_cycle_id: str, *, tenant_id: str | None = None) -> tuple[int, dict[str, Any]]:
        cycle = self._require_review_cycle(review_cycle_id)
        if tenant_id is not None:
            assert_tenant_access(cycle.tenant_id, normalize_tenant_id(tenant_id))
        return 200, self._review_cycle_payload(cycle)

    def list_goals(self, *, tenant_id: str | None = None, employee_id: str | None = None, status: str | None = None, limit: int = 25, cursor: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [goal for goal in self.goals.values() if goal.tenant_id == tenant]
        if employee_id is not None:
            rows = [goal for goal in rows if goal.employee_id == employee_id]
        if status is not None:
            rows = [goal for goal in rows if goal.status == status]
        rows.sort(key=lambda item: (item.updated_at.isoformat(), item.goal_id), reverse=True)
        page_items, pagination = self._paginate([self._goal_payload(goal) for goal in rows], limit=limit, cursor=cursor)
        return 200, {'items': page_items, 'data': page_items, '_pagination': pagination}

    def list_feedback(self, *, tenant_id: str | None = None, employee_id: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [item for item in self.feedback.values() if item.tenant_id == tenant]
        if employee_id is not None:
            rows = [item for item in rows if item.employee_id == employee_id]
        rows.sort(key=lambda item: (item.created_at.isoformat(), item.feedback_id), reverse=True)
        payload = [self._feedback_payload(item) for item in rows]
        return 200, {'items': payload, 'data': payload, '_pagination': {'count': len(payload), 'limit': None, 'cursor': None, 'next_cursor': None}}

    def list_pip_plans(self, *, tenant_id: str | None = None, employee_id: str | None = None, status: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [item for item in self.pips.values() if item.tenant_id == tenant]
        if employee_id is not None:
            rows = [item for item in rows if item.employee_id == employee_id]
        if status is not None:
            rows = [item for item in rows if item.status == status]
        rows.sort(key=lambda item: (item.updated_at.isoformat(), item.pip_id), reverse=True)
        payload = [self._pip_payload(item) for item in rows]
        return 200, {'items': payload, 'data': payload, '_pagination': {'count': len(payload), 'limit': None, 'cursor': None, 'next_cursor': None}}

    def _register_workflows(self) -> None:
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code='performance_goal_approval',
            source_service='performance-service',
            subject_type='Goal',
            description='Manager approval for submitted goals/OKRs.',
            steps=[{'name': 'manager-approval', 'type': 'approval', 'assignee_template': '{approver_assignee}', 'sla': 'PT72H', 'escalation_assignee_template': '{escalation_assignee}'}],
        )
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code='performance_cycle_approval',
            source_service='performance-service',
            subject_type='ReviewCycle',
            description='Approval gate before a review cycle opens enterprise-wide.',
            steps=[{'name': 'cycle-approval', 'type': 'approval', 'assignee_template': '{approver_assignee}', 'sla': 'PT48H', 'escalation_assignee_template': '{escalation_assignee}'}],
        )
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code='performance_calibration_signoff',
            source_service='performance-service',
            subject_type='CalibrationSession',
            description='HR sign-off for calibration outcomes.',
            steps=[{'name': 'hr-signoff', 'type': 'approval', 'assignee_template': '{approver_assignee}', 'sla': 'PT48H', 'escalation_assignee_template': '{escalation_assignee}'}],
        )
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code='performance_pip_approval',
            source_service='performance-service',
            subject_type='PipPlan',
            description='HR approval for employee performance improvement plans.',
            steps=[{'name': 'pip-approval', 'type': 'approval', 'assignee_template': '{approver_assignee}', 'sla': 'PT24H', 'escalation_assignee_template': '{escalation_assignee}'}],
        )

    def _review_cycle_payload(self, cycle: ReviewCycle) -> dict[str, Any]:
        owner = self._require_employee(cycle.owner_employee_id, tenant_id=cycle.tenant_id, field='owner_employee_id')
        goals = [goal for goal in self.goals.values() if goal.review_cycle_id == cycle.review_cycle_id and goal.tenant_id == cycle.tenant_id]
        return {
            **cycle.to_dict(),
            'owner': owner.to_dict(),
            'goal_count': len(goals),
            'approved_goal_count': sum(1 for goal in goals if goal.status == 'Approved'),
            'workflow': self.workflow_service.get_instance(cycle.workflow_id, tenant_id=cycle.tenant_id) if cycle.workflow_id else None,
        }

    def _goal_payload(self, goal: GoalRecord) -> dict[str, Any]:
        employee = self._require_employee(goal.employee_id, tenant_id=goal.tenant_id, field='employee_id')
        owner = self._require_employee(goal.owner_employee_id, tenant_id=goal.tenant_id, field='owner_employee_id')
        progress = round((goal.current_value / goal.target_value) * 100, 2) if goal.target_value > 0 else 0.0
        return {
            **goal.to_dict(),
            'employee': employee.to_dict(),
            'owner': owner.to_dict(),
            'progress_percent': min(progress, 100.0),
            'workflow': self.workflow_service.get_instance(goal.workflow_id, tenant_id=goal.tenant_id) if goal.workflow_id else None,
        }

    def _feedback_payload(self, feedback: FeedbackRecord) -> dict[str, Any]:
        employee = self._require_employee(feedback.employee_id, tenant_id=feedback.tenant_id, field='employee_id')
        provider = self._require_employee(feedback.provider_employee_id, tenant_id=feedback.tenant_id, field='provider_employee_id')
        return {
            **feedback.to_dict(),
            'employee': employee.to_dict(),
            'provider': provider.to_dict(),
        }

    def _calibration_payload(self, session: CalibrationSession) -> dict[str, Any]:
        facilitator = self._require_employee(session.facilitator_employee_id, tenant_id=session.tenant_id, field='facilitator_employee_id')
        return {
            **session.to_dict(),
            'facilitator': facilitator.to_dict(),
            'workflow': self.workflow_service.get_instance(session.workflow_id, tenant_id=session.tenant_id) if session.workflow_id else None,
        }

    def _pip_payload(self, plan: PipPlan) -> dict[str, Any]:
        employee = self._require_employee(plan.employee_id, tenant_id=plan.tenant_id, field='employee_id')
        manager = self._require_employee(plan.manager_employee_id, tenant_id=plan.tenant_id, field='manager_employee_id')
        return {
            **plan.to_dict(),
            'employee': employee.to_dict(),
            'manager': manager.to_dict(),
            'completion_percent': round(sum(1 for item in plan.milestones if item.completed) / len(plan.milestones) * 100, 2) if plan.milestones else 0.0,
            'workflow': self.workflow_service.get_instance(plan.workflow_id, tenant_id=plan.tenant_id) if plan.workflow_id else None,
        }

    def _audit(self, action: str, entity: str, entity_id: str, before: dict[str, Any], after: dict[str, Any], *, actor_id: str, actor_type: str, tenant_id: str, trace_id: str) -> None:
        emit_audit_record(
            service_name='performance-service',
            tenant_id=tenant_id,
            actor={'id': actor_id, 'type': actor_type},
            action=action,
            entity=entity,
            entity_id=entity_id,
            before=before,
            after=after,
            trace_id=trace_id,
            source={'bounded_context': 'performance-management'},
        )

    def _emit(self, legacy_event_name: str, data: dict[str, Any], *, tenant_id: str, correlation_id: str | None) -> None:
        identity = (
            data.get('goal_id')
            or data.get('review_cycle_id')
            or data.get('calibration_id')
            or data.get('pip_id')
            or data.get('feedback_id')
            or str(uuid4())
        )
        idempotency_key = f"{identity}:{json.dumps(data, sort_keys=True, default=str)}"
        emit_canonical_event(
            self.events,
            legacy_event_name=legacy_event_name,
            data={'tenant_id': tenant_id, **data},
            source='performance-service',
            tenant_id=tenant_id,
            registry=self.event_registry,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )

    def _require_terminal_workflow_result(self, workflow: dict[str, Any], *, action: str, trace_id: str) -> str:
        return require_terminal_workflow_result(
            workflow,
            action=action,
            on_mismatch=lambda _actual, expected: self._error(409, 'WORKFLOW_STATE_MISMATCH', f'workflow did not reach expected terminal result: {expected}', trace_id),
            invalid_action=lambda _action: self._error(422, 'VALIDATION_ERROR', 'action must be approve or reject', trace_id, [{'field': 'action', 'reason': 'must be approve or reject'}]),
        )

    def _resolve_workflow(self, workflow_id: str, tenant_id: str, *, action: str, actor_id: str, actor_type: str, actor_role: str | None, comment: str | None, trace_id: str) -> dict[str, Any]:
        return resolve_workflow_action(
            workflow_service=self.workflow_service,
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_role=actor_role,
            comment=comment,
            trace_id=trace_id,
            map_error=lambda exc: self._error(exc.status_code, exc.code, exc.message, trace_id, exc.details),
            invalid_action=lambda _action: self._error(422, 'VALIDATION_ERROR', 'action must be approve or reject', trace_id, [{'field': 'action', 'reason': 'must be approve or reject'}]),
        )

    def _require_employee(self, employee_id: str | None, *, tenant_id: str, field: str) -> EmployeeSnapshot:
        if not employee_id:
            raise self._error(422, 'VALIDATION_ERROR', f'{field} is required', self.observability.trace_id(), [{'field': field, 'reason': 'must be provided'}])
        snapshot = self.employee_snapshots.get(str(employee_id))
        if snapshot is None or snapshot.tenant_id != tenant_id:
            raise self._error(404, 'NOT_FOUND', f'{field} was not found in employee-service read model', self.observability.trace_id())
        if snapshot.status == 'Terminated':
            raise self._error(422, 'VALIDATION_ERROR', f'{field} cannot reference a Terminated employee', self.observability.trace_id())
        return snapshot

    def _require_review_cycle(self, review_cycle_id: str) -> ReviewCycle:
        cycle = self.review_cycles.get(review_cycle_id)
        if cycle is None:
            raise self._error(404, 'NOT_FOUND', 'review cycle not found', self.observability.trace_id())
        return cycle

    def _require_goal(self, goal_id: str) -> GoalRecord:
        goal = self.goals.get(goal_id)
        if goal is None:
            raise self._error(404, 'NOT_FOUND', 'goal not found', self.observability.trace_id())
        return goal

    def _require_calibration(self, calibration_id: str) -> CalibrationSession:
        session = self.calibrations.get(calibration_id)
        if session is None:
            raise self._error(404, 'NOT_FOUND', 'calibration session not found', self.observability.trace_id())
        return session

    def _require_pip(self, pip_id: str) -> PipPlan:
        plan = self.pips.get(pip_id)
        if plan is None:
            raise self._error(404, 'NOT_FOUND', 'PIP plan not found', self.observability.trace_id())
        return plan

    @staticmethod
    def _coerce_date(raw: Any, field: str) -> date:
        try:
            return date.fromisoformat(str(raw))
        except Exception as exc:
            raise ValueError(f'{field} must be an ISO date') from exc

    @staticmethod
    def _coerce_float(raw: Any, field: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
        try:
            value = float(raw)
        except Exception as exc:
            raise ValueError(f'{field} must be numeric') from exc
        if minimum is not None and value < minimum:
            raise ValueError(f'{field} must be >= {minimum}')
        if maximum is not None and value > maximum:
            raise ValueError(f'{field} must be <= {maximum}')
        return round(value, 2)

    @staticmethod
    def _paginate(items: list[dict[str, Any]], *, limit: int, cursor: str | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if limit < 1 or limit > 100:
            raise ValueError('limit must be between 1 and 100')
        offset = 0
        if cursor:
            padded = cursor + '=' * (-len(cursor) % 4)
            offset = int(base64.urlsafe_b64decode(padded.encode('utf-8')).decode('utf-8'))
        page_items = items[offset: offset + limit]
        next_cursor = None
        if offset + limit < len(items):
            next_cursor = base64.urlsafe_b64encode(str(offset + limit).encode('utf-8')).decode('utf-8').rstrip('=')
        return page_items, {'limit': limit, 'cursor': cursor, 'next_cursor': next_cursor, 'count': len(page_items)}

    @staticmethod
    def _error(status_code: int, code: str, message: str, trace_id: str, details: list[dict[str, Any]] | None = None) -> PerformanceServiceError:
        return PerformanceServiceError(status_code, code, message, trace_id, details)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)
