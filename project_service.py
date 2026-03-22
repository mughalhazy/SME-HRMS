from __future__ import annotations

import base64
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from threading import RLock
from time import perf_counter
from typing import Any
from uuid import uuid4

from audit_service.service import emit_audit_record
from event_contract import EventRegistry, emit_canonical_event
from event_outbox import EventOutbox
from notification_service import NotificationService
from persistent_store import PersistentKVStore
from resilience import Observability
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id
from workflow_support import require_terminal_workflow_result, resolve_workflow_action
from workflow_service import WorkflowService, WorkflowServiceError


class ProjectServiceError(Exception):
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
    email: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Project:
    tenant_id: str
    project_id: str
    project_code: str
    name: str
    description: str | None
    client_name: str | None
    department_id: str
    department_name: str
    project_manager_employee_id: str
    status: str
    start_date: date
    end_date: date | None
    currency: str
    budget_amount: float | None
    requires_assignment_approval: bool
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['start_date'] = self.start_date.isoformat()
        payload['end_date'] = self.end_date.isoformat() if self.end_date else None
        payload['created_at'] = self.created_at.isoformat()
        payload['updated_at'] = self.updated_at.isoformat()
        return payload


@dataclass(slots=True)
class ProjectAssignment:
    tenant_id: str
    assignment_id: str
    project_id: str
    employee_id: str
    role_name: str
    allocation_percentage: float
    allocation_status: str
    effective_from: date
    effective_to: date | None
    approval_required: bool
    approver_employee_id: str | None
    workflow_id: str | None
    notes: str | None
    approved_at: datetime | None
    rejected_at: datetime | None
    released_at: datetime | None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['effective_from'] = self.effective_from.isoformat()
        payload['effective_to'] = self.effective_to.isoformat() if self.effective_to else None
        for field_name in ('approved_at', 'rejected_at', 'released_at', 'created_at', 'updated_at'):
            value = getattr(self, field_name)
            payload[field_name] = value.isoformat() if value else None
        return payload


@dataclass(slots=True)
class AllocationLedgerEntry:
    tenant_id: str
    ledger_entry_id: str
    assignment_id: str
    project_id: str
    employee_id: str
    action: str
    previous_allocation_percentage: float | None
    new_allocation_percentage: float | None
    status: str
    actor_id: str
    actor_type: str
    created_at: datetime
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['created_at'] = self.created_at.isoformat()
        return payload


class ProjectService:
    PROJECT_STATUSES = {'Draft', 'Planned', 'Active', 'OnHold', 'Completed', 'Cancelled'}
    ASSIGNMENT_STATUSES = {'PendingApproval', 'Allocated', 'Rejected', 'Released'}
    ACTIVE_ASSIGNMENT_STATUSES = {'PendingApproval', 'Allocated'}

    def __init__(self, db_path: str | None = None, *, workflow_service: WorkflowService | None = None, notification_service: NotificationService | None = None) -> None:
        self.employee_snapshots = PersistentKVStore[str, EmployeeSnapshot](service='project-service', namespace='employee_snapshots', db_path=db_path)
        shared_db_path = self.employee_snapshots.db_path
        self.projects = PersistentKVStore[str, Project](service='project-service', namespace='projects', db_path=shared_db_path)
        self.assignments = PersistentKVStore[str, ProjectAssignment](service='project-service', namespace='assignments', db_path=shared_db_path)
        self.allocation_ledger = PersistentKVStore[str, AllocationLedgerEntry](service='project-service', namespace='allocation_ledger', db_path=shared_db_path)
        self.events: list[dict[str, Any]] = []
        self.event_registry = EventRegistry()
        self.event_outbox = EventOutbox(db_path=shared_db_path)
        self.notification_service = notification_service or NotificationService()
        self.workflow_service = workflow_service or WorkflowService(notification_service=self.notification_service)
        self.observability = Observability('project-service')
        self.tenant_id = DEFAULT_TENANT_ID
        self._lock = RLock()
        self._registered_workflow_tenants: set[str] = set()

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
            email=str(payload['email']) if payload.get('email') else None,
        )
        self.employee_snapshots[snapshot.employee_id] = snapshot
        return snapshot.to_dict()

    def create_project(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        self._register_workflows_for_tenant(tenant_id)
        code = str(payload.get('project_code') or '').strip().upper()
        name = str(payload.get('name') or '').strip()
        if not code:
            raise self._error(422, 'VALIDATION_ERROR', 'project_code is required', trace, [{'field': 'project_code', 'reason': 'must be a non-empty string'}])
        if not name:
            raise self._error(422, 'VALIDATION_ERROR', 'name is required', trace, [{'field': 'name', 'reason': 'must be a non-empty string'}])
        if self._find_project_by_code(tenant_id, code) is not None:
            raise self._error(409, 'CONFLICT', 'project_code already exists', trace, [{'field': 'project_code', 'reason': 'must be unique per tenant'}])
        manager = self._require_employee(payload.get('project_manager_employee_id'), tenant_id=tenant_id, field='project_manager_employee_id', trace_id=trace)
        department_id = str(payload.get('department_id') or manager.department_id).strip()
        department_name = str(payload.get('department_name') or manager.department_name).strip() or department_id
        status = str(payload.get('status') or 'Draft')
        if status not in self.PROJECT_STATUSES:
            raise self._error(422, 'VALIDATION_ERROR', 'invalid status', trace, [{'field': 'status', 'reason': f'must be one of {sorted(self.PROJECT_STATUSES)}'}])
        start_date = self._coerce_date(payload.get('start_date'), 'start_date', trace)
        end_date = self._coerce_optional_date(payload.get('end_date'), 'end_date', trace)
        if end_date and end_date < start_date:
            raise self._error(422, 'VALIDATION_ERROR', 'end_date must be on or after start_date', trace, [{'field': 'end_date', 'reason': 'must be >= start_date'}])
        budget_amount = self._coerce_optional_float(payload.get('budget_amount'), 'budget_amount', trace, minimum=0.0)
        now = self._now()
        project = Project(
            tenant_id=tenant_id,
            project_id=str(uuid4()),
            project_code=code,
            name=name,
            description=str(payload['description']).strip() if payload.get('description') is not None else None,
            client_name=str(payload['client_name']).strip() if payload.get('client_name') is not None else None,
            department_id=department_id,
            department_name=department_name,
            project_manager_employee_id=manager.employee_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            currency=str(payload.get('currency') or 'USD').strip().upper(),
            budget_amount=budget_amount,
            requires_assignment_approval=bool(payload.get('requires_assignment_approval', False)),
            created_at=now,
            updated_at=now,
            metadata={
                'source_service': 'project-service',
                'employee_service_reference': 'employee-service',
            },
        )
        with self._lock:
            self.projects[project.project_id] = project
            response = self._project_payload(project)
            self._audit('project_created', 'Project', project.project_id, {}, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
            self._emit('ProjectCreated', response, tenant_id=tenant_id, correlation_id=trace, aggregate_type='Project', aggregate_id=project.project_id)
        self.observability.track('project.create_project', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant_id, 'status': 201})
        return 201, response

    def update_project_status(self, project_id: str, status: str, *, actor_id: str, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id)
        if status not in self.PROJECT_STATUSES:
            raise self._error(422, 'VALIDATION_ERROR', 'invalid status', trace, [{'field': 'status', 'reason': f'must be one of {sorted(self.PROJECT_STATUSES)}'}])
        with self._lock:
            project = self._require_project(project_id, tenant_id=tenant, trace_id=trace)
            before = self._project_payload(project)
            project.status = status
            project.updated_at = self._now()
            self.projects[project.project_id] = project
            response = self._project_payload(project)
            self._audit('project_status_changed', 'Project', project.project_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=project.tenant_id, trace_id=trace)
            self._emit('ProjectStatusChanged', {'project_id': project.project_id, 'status': project.status, 'project_code': project.project_code}, tenant_id=project.tenant_id, correlation_id=trace, aggregate_type='Project', aggregate_id=project.project_id)
        self.observability.track('project.update_status', trace_id=trace, started_at=started, success=True, context={'tenant_id': project.tenant_id, 'status': 200})
        return 200, response

    def assign_employee(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        self._register_workflows_for_tenant(tenant_id)
        with self._lock:
            project = self._require_project(str(payload.get('project_id') or ''), tenant_id=tenant_id, trace_id=trace)
            if project.status not in {'Draft', 'Planned', 'Active', 'OnHold'}:
                raise self._error(409, 'INVALID_TRANSITION', 'project is not accepting assignments', trace)
            employee = self._require_employee(payload.get('employee_id'), tenant_id=tenant_id, field='employee_id', trace_id=trace)
            effective_from = self._coerce_date(payload.get('effective_from') or project.start_date.isoformat(), 'effective_from', trace)
            effective_to = self._coerce_optional_date(payload.get('effective_to') or (project.end_date.isoformat() if project.end_date else None), 'effective_to', trace)
            if effective_to and effective_to < effective_from:
                raise self._error(422, 'VALIDATION_ERROR', 'effective_to must be on or after effective_from', trace, [{'field': 'effective_to', 'reason': 'must be >= effective_from'}])
            allocation_percentage = self._coerce_float(payload.get('allocation_percentage'), 'allocation_percentage', trace, minimum=0.01, maximum=100.0)
            role_name = str(payload.get('role_name') or '').strip()
            if not role_name:
                raise self._error(422, 'VALIDATION_ERROR', 'role_name is required', trace, [{'field': 'role_name', 'reason': 'must be a non-empty string'}])
            self._ensure_no_duplicate_active_assignment(project.project_id, employee.employee_id, trace)
            self._ensure_employee_allocation_capacity(employee.employee_id, tenant_id=tenant_id, effective_from=effective_from, effective_to=effective_to, requested_allocation=allocation_percentage, trace_id=trace)
            approver = self._resolve_assignment_approver(payload, project=project, employee=employee, tenant_id=tenant_id, trace_id=trace)
            approval_required = bool(payload.get('approval_required', project.requires_assignment_approval))
            now = self._now()
            assignment = ProjectAssignment(
                tenant_id=tenant_id,
                assignment_id=str(uuid4()),
                project_id=project.project_id,
                employee_id=employee.employee_id,
                role_name=role_name,
                allocation_percentage=allocation_percentage,
                allocation_status='PendingApproval' if approval_required else 'Allocated',
                effective_from=effective_from,
                effective_to=effective_to,
                approval_required=approval_required,
                approver_employee_id=approver.employee_id if approver else None,
                workflow_id=None,
                notes=str(payload['notes']).strip() if payload.get('notes') is not None else None,
                approved_at=None if approval_required else now,
                rejected_at=None,
                released_at=None,
                created_at=now,
                updated_at=now,
                metadata={},
            )
            if approval_required:
                workflow = self.workflow_service.start_workflow(
                    tenant_id=tenant_id,
                    definition_code='project_assignment_approval',
                    source_service='project-service',
                    subject_type='ProjectAssignment',
                    subject_id=assignment.assignment_id,
                    actor_id=actor_id,
                    actor_type=actor_type,
                    context={
                        'approver_assignee': assignment.approver_employee_id,
                        'escalation_assignee': project.project_manager_employee_id,
                    },
                    trace_id=trace,
                )
                assignment.workflow_id = workflow['workflow_id']
            self.assignments[assignment.assignment_id] = assignment
            self._record_allocation_ledger(
                assignment=assignment,
                action='assignment_requested' if approval_required else 'assignment_allocated',
                previous_allocation_percentage=None,
                new_allocation_percentage=assignment.allocation_percentage,
                actor_id=actor_id,
                actor_type=actor_type,
                details={'project_code': project.project_code, 'approval_required': approval_required},
            )
            response = self._assignment_payload(assignment)
            self._audit('project_assignment_created', 'ProjectAssignment', assignment.assignment_id, {}, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
            self._emit('ProjectAssignmentRequested' if approval_required else 'ProjectAssignmentAllocated', response, tenant_id=tenant_id, correlation_id=trace, aggregate_type='ProjectAssignment', aggregate_id=assignment.assignment_id)
        self.observability.track('project.assign_employee', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant_id, 'status': 201})
        return 201, response

    def update_assignment_allocation(self, assignment_id: str, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id or payload.get('tenant_id'))
        requested = self._coerce_float(payload.get('allocation_percentage'), 'allocation_percentage', trace, minimum=0.01, maximum=100.0)
        with self._lock:
            assignment = self._require_assignment(assignment_id, tenant_id=tenant, trace_id=trace)
            if assignment.allocation_status == 'Released':
                raise self._error(409, 'INVALID_TRANSITION', 'released assignments cannot be updated', trace)
            if assignment.allocation_status == 'PendingApproval':
                raise self._error(409, 'INVALID_TRANSITION', 'assignment already has a pending approval flow', trace)
            if requested == assignment.allocation_percentage:
                return 200, self._assignment_payload(assignment)
            self._ensure_employee_allocation_capacity(
                assignment.employee_id,
                tenant_id=assignment.tenant_id,
                effective_from=assignment.effective_from,
                effective_to=assignment.effective_to,
                requested_allocation=requested,
                trace_id=trace,
                exclude_assignment_id=assignment.assignment_id,
            )
            before = self._assignment_payload(assignment)
            previous_allocation = assignment.allocation_percentage
            project = self._require_project(assignment.project_id, tenant_id=assignment.tenant_id, trace_id=trace)
            if assignment.approval_required:
                workflow = self.workflow_service.start_workflow(
                    tenant_id=assignment.tenant_id,
                    definition_code='project_assignment_approval',
                    source_service='project-service',
                    subject_type='ProjectAssignment',
                    subject_id=assignment.assignment_id,
                    actor_id=actor_id,
                    actor_type=actor_type,
                    context={
                        'approver_assignee': assignment.approver_employee_id or project.project_manager_employee_id,
                        'escalation_assignee': project.project_manager_employee_id,
                    },
                    trace_id=trace,
                )
                assignment.workflow_id = workflow['workflow_id']
                assignment.allocation_status = 'PendingApproval'
                assignment.metadata['pending_allocation_percentage'] = requested
                assignment.metadata['change_type'] = 'allocation_update'
                event_name = 'ProjectAssignmentRequested'
                ledger_action = 'allocation_change_requested'
            else:
                assignment.allocation_percentage = requested
                assignment.updated_at = self._now()
                event_name = 'ProjectAllocationUpdated'
                ledger_action = 'allocation_updated'
            assignment.updated_at = self._now()
            self.assignments[assignment.assignment_id] = assignment
            self._record_allocation_ledger(
                assignment=assignment,
                action=ledger_action,
                previous_allocation_percentage=previous_allocation,
                new_allocation_percentage=requested,
                actor_id=actor_id,
                actor_type=actor_type,
                details={'change_type': assignment.metadata.get('change_type', 'direct_update')},
            )
            response = self._assignment_payload(assignment)
            self._audit('project_assignment_updated', 'ProjectAssignment', assignment.assignment_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=assignment.tenant_id, trace_id=trace)
            self._emit(event_name, response, tenant_id=assignment.tenant_id, correlation_id=trace, aggregate_type='ProjectAssignment', aggregate_id=assignment.assignment_id)
        self.observability.track('project.update_assignment_allocation', trace_id=trace, started_at=started, success=True, context={'tenant_id': assignment.tenant_id, 'status': 200})
        return 200, response

    def decide_assignment(self, assignment_id: str, *, action: str, actor_id: str, actor_type: str = 'user', actor_role: str | None = None, tenant_id: str | None = None, comment: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id)
        with self._lock:
            assignment = self._require_assignment(assignment_id, tenant_id=tenant, trace_id=trace)
            if assignment.allocation_status != 'PendingApproval' or not assignment.workflow_id:
                raise self._error(409, 'INVALID_TRANSITION', 'assignment is not awaiting approval', trace)
            before = self._assignment_payload(assignment)
            workflow = self._resolve_workflow(
                assignment.workflow_id,
                assignment.tenant_id,
                action=action,
                actor_id=actor_id,
                actor_type=actor_type,
                actor_role=actor_role,
                comment=comment,
                trace_id=trace,
            )
            terminal_result = self._require_terminal_workflow_result(workflow, action=action, trace_id=trace)
            previous_allocation = assignment.allocation_percentage
            pending_allocation = assignment.metadata.pop('pending_allocation_percentage', None)
            change_type = assignment.metadata.pop('change_type', 'initial_assignment')
            if terminal_result == 'approved':
                if pending_allocation is not None:
                    assignment.allocation_percentage = float(pending_allocation)
                assignment.allocation_status = 'Allocated'
                assignment.approved_at = self._now()
                assignment.rejected_at = None
                event_name = 'ProjectAllocationUpdated' if change_type == 'allocation_update' else 'ProjectAssignmentAllocated'
                ledger_action = 'allocation_updated' if change_type == 'allocation_update' else 'assignment_allocated'
            elif terminal_result == 'rejected':
                if change_type == 'allocation_update':
                    assignment.allocation_status = 'Allocated'
                else:
                    assignment.allocation_status = 'Rejected'
                assignment.rejected_at = self._now()
                event_name = 'ProjectAssignmentRejected'
                ledger_action = 'assignment_rejected'
            assignment.updated_at = self._now()
            self.assignments[assignment.assignment_id] = assignment
            self._record_allocation_ledger(
                assignment=assignment,
                action=ledger_action,
                previous_allocation_percentage=previous_allocation,
                new_allocation_percentage=assignment.allocation_percentage,
                actor_id=actor_id,
                actor_type=actor_type,
                details={'decision': terminal_result, 'change_type': change_type},
            )
            response = self._assignment_payload(assignment)
            self._audit('project_assignment_decided', 'ProjectAssignment', assignment.assignment_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=assignment.tenant_id, trace_id=trace)
            self._emit(event_name, response, tenant_id=assignment.tenant_id, correlation_id=trace, aggregate_type='ProjectAssignment', aggregate_id=assignment.assignment_id)
        self.observability.track('project.decide_assignment', trace_id=trace, started_at=started, success=True, context={'tenant_id': assignment.tenant_id, 'status': 200})
        return 200, response

    def release_assignment(self, assignment_id: str, payload: dict[str, Any] | None = None, *, actor_id: str, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id or (payload or {}).get('tenant_id'))
        release_payload = payload or {}
        with self._lock:
            assignment = self._require_assignment(assignment_id, tenant_id=tenant, trace_id=trace)
            if assignment.allocation_status != 'Allocated':
                raise self._error(409, 'INVALID_TRANSITION', 'only Allocated assignments can be released', trace)
            before = self._assignment_payload(assignment)
            release_date = self._coerce_optional_date(release_payload.get('effective_to'), 'effective_to', trace) or self._now().date()
            if release_date < assignment.effective_from:
                raise self._error(422, 'VALIDATION_ERROR', 'effective_to must be on or after effective_from', trace, [{'field': 'effective_to', 'reason': 'must be >= effective_from'}])
            assignment.effective_to = release_date
            assignment.released_at = self._now()
            assignment.allocation_status = 'Released'
            assignment.updated_at = self._now()
            self.assignments[assignment.assignment_id] = assignment
            self._record_allocation_ledger(
                assignment=assignment,
                action='assignment_released',
                previous_allocation_percentage=assignment.allocation_percentage,
                new_allocation_percentage=0.0,
                actor_id=actor_id,
                actor_type=actor_type,
                details={'effective_to': release_date.isoformat()},
            )
            response = self._assignment_payload(assignment)
            self._audit('project_assignment_released', 'ProjectAssignment', assignment.assignment_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=assignment.tenant_id, trace_id=trace)
            self._emit('ProjectAssignmentReleased', response, tenant_id=assignment.tenant_id, correlation_id=trace, aggregate_type='ProjectAssignment', aggregate_id=assignment.assignment_id)
        self.observability.track('project.release_assignment', trace_id=trace, started_at=started, success=True, context={'tenant_id': assignment.tenant_id, 'status': 200})
        return 200, response

    def get_project(self, project_id: str, *, tenant_id: str | None = None, actor_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        project = self._require_project(project_id, tenant_id=normalize_tenant_id(tenant_id), trace_id=trace)
        return 200, self._project_payload(project, actor_id=actor_id)

    def list_projects(self, *, tenant_id: str | None = None, status: str | None = None, manager_employee_id: str | None = None, limit: int = 25, cursor: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [project for project in self.projects.values() if project.tenant_id == tenant]
        if status is not None:
            rows = [project for project in rows if project.status == status]
        if manager_employee_id is not None:
            rows = [project for project in rows if project.project_manager_employee_id == manager_employee_id]
        rows.sort(key=lambda item: (item.updated_at.isoformat(), item.project_id), reverse=True)
        page_items, pagination = self._paginate([self._project_payload(item) for item in rows], limit=limit, cursor=cursor)
        return 200, {'items': page_items, 'data': page_items, '_pagination': pagination}

    def list_assignments(self, *, tenant_id: str | None = None, project_id: str | None = None, employee_id: str | None = None, allocation_status: str | None = None, limit: int = 25, cursor: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [assignment for assignment in self.assignments.values() if assignment.tenant_id == tenant]
        if project_id is not None:
            rows = [assignment for assignment in rows if assignment.project_id == project_id]
        if employee_id is not None:
            rows = [assignment for assignment in rows if assignment.employee_id == employee_id]
        if allocation_status is not None:
            rows = [assignment for assignment in rows if assignment.allocation_status == allocation_status]
        rows.sort(key=lambda item: (item.updated_at.isoformat(), item.assignment_id), reverse=True)
        page_items, pagination = self._paginate([self._assignment_payload(item) for item in rows], limit=limit, cursor=cursor)
        return 200, {'items': page_items, 'data': page_items, '_pagination': pagination}

    def list_allocation_history(self, assignment_id: str, *, tenant_id: str | None = None, limit: int = 50, cursor: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        assignment = self._require_assignment(assignment_id, tenant_id=tenant, trace_id=self._trace())
        rows = [entry for entry in self.allocation_ledger.values() if entry.tenant_id == assignment.tenant_id and entry.assignment_id == assignment_id]
        rows.sort(key=lambda item: (item.created_at.isoformat(), item.ledger_entry_id), reverse=True)
        page_items, pagination = self._paginate([row.to_dict() for row in rows], limit=limit, cursor=cursor)
        return 200, {'items': page_items, 'data': page_items, '_pagination': pagination}

    def _register_workflows_for_tenant(self, tenant_id: str) -> None:
        tenant = normalize_tenant_id(tenant_id)
        if tenant in self._registered_workflow_tenants:
            return
        self.workflow_service.register_definition(
            tenant_id=tenant,
            code='project_assignment_approval',
            source_service='project-service',
            subject_type='ProjectAssignment',
            description='Approval gate for project assignment and allocation changes when resource governance requires sign-off.',
            steps=[
                {
                    'name': 'resource-manager-approval',
                    'type': 'approval',
                    'assignee_template': '{approver_assignee}',
                    'sla': 'PT48H',
                    'escalation_assignee_template': '{escalation_assignee}',
                }
            ],
        )
        self._registered_workflow_tenants.add(tenant)

    def _project_payload(self, project: Project, *, actor_id: str | None = None) -> dict[str, Any]:
        manager = self._require_employee(project.project_manager_employee_id, tenant_id=project.tenant_id, field='project_manager_employee_id', trace_id=self._trace())
        assignments = [assignment for assignment in self.assignments.values() if assignment.tenant_id == project.tenant_id and assignment.project_id == project.project_id]
        active_assignments = [assignment for assignment in assignments if assignment.allocation_status == 'Allocated']
        pending_assignments = [assignment for assignment in assignments if assignment.allocation_status == 'PendingApproval']
        return {
            **project.to_dict(),
            'project_manager': manager.to_dict(),
            'assignment_count': len(assignments),
            'active_assignment_count': len(active_assignments),
            'pending_assignment_count': len(pending_assignments),
            'total_allocated_percentage': round(sum(assignment.allocation_percentage for assignment in active_assignments), 2),
            'assignments': [self._assignment_payload(assignment, actor_id=actor_id) for assignment in assignments],
        }

    def _assignment_payload(self, assignment: ProjectAssignment, *, actor_id: str | None = None) -> dict[str, Any]:
        employee = self._require_employee(assignment.employee_id, tenant_id=assignment.tenant_id, field='employee_id', trace_id=self._trace())
        project = self._require_project(assignment.project_id, tenant_id=assignment.tenant_id, trace_id=self._trace())
        approver = self._require_employee(assignment.approver_employee_id, tenant_id=assignment.tenant_id, field='approver_employee_id', trace_id=self._trace()) if assignment.approver_employee_id else None
        return {
            **assignment.to_dict(),
            'employee': employee.to_dict(),
            'project': {
                'project_id': project.project_id,
                'project_code': project.project_code,
                'name': project.name,
                'status': project.status,
            },
            'approver': approver.to_dict() if approver else None,
            'workflow': self.workflow_service.get_instance(assignment.workflow_id, tenant_id=assignment.tenant_id, actor_id=actor_id) if assignment.workflow_id else None,
            'allocation_history_count': sum(1 for entry in self.allocation_ledger.values() if entry.assignment_id == assignment.assignment_id and entry.tenant_id == assignment.tenant_id),
        }

    def _resolve_assignment_approver(self, payload: dict[str, Any], *, project: Project, employee: EmployeeSnapshot, tenant_id: str, trace_id: str) -> EmployeeSnapshot | None:
        approver_id = payload.get('approver_employee_id') or project.project_manager_employee_id or employee.manager_employee_id
        if not approver_id:
            return None
        return self._require_employee(approver_id, tenant_id=tenant_id, field='approver_employee_id', trace_id=trace_id)

    def _ensure_no_duplicate_active_assignment(self, project_id: str, employee_id: str, trace_id: str) -> None:
        for assignment in self.assignments.values():
            if assignment.project_id == project_id and assignment.employee_id == employee_id and assignment.allocation_status in self.ACTIVE_ASSIGNMENT_STATUSES:
                raise self._error(409, 'CONFLICT', 'employee already has an active assignment for this project', trace_id)

    def _ensure_employee_allocation_capacity(
        self,
        employee_id: str,
        *,
        tenant_id: str,
        effective_from: date,
        effective_to: date | None,
        requested_allocation: float,
        trace_id: str,
        exclude_assignment_id: str | None = None,
    ) -> None:
        total = 0.0
        for assignment in self.assignments.values():
            if assignment.tenant_id != tenant_id or assignment.employee_id != employee_id:
                continue
            if exclude_assignment_id and assignment.assignment_id == exclude_assignment_id:
                continue
            if assignment.allocation_status not in self.ACTIVE_ASSIGNMENT_STATUSES:
                continue
            if self._date_ranges_overlap(effective_from, effective_to, assignment.effective_from, assignment.effective_to):
                total += assignment.metadata.get('pending_allocation_percentage', assignment.allocation_percentage) if assignment.allocation_status == 'PendingApproval' else assignment.allocation_percentage
        if total + requested_allocation > 100.0 + 1e-9:
            raise self._error(
                422,
                'ALLOCATION_LIMIT_EXCEEDED',
                'employee allocation exceeds 100 percent across overlapping assignments',
                trace_id,
                [{'field': 'allocation_percentage', 'reason': f'overlapping allocations total {round(total + requested_allocation, 2)}'}],
            )

    @staticmethod
    def _date_ranges_overlap(start_a: date, end_a: date | None, start_b: date, end_b: date | None) -> bool:
        normalized_end_a = end_a or date.max
        normalized_end_b = end_b or date.max
        return start_a <= normalized_end_b and start_b <= normalized_end_a

    def _record_allocation_ledger(
        self,
        *,
        assignment: ProjectAssignment,
        action: str,
        previous_allocation_percentage: float | None,
        new_allocation_percentage: float | None,
        actor_id: str,
        actor_type: str,
        details: dict[str, Any],
    ) -> None:
        entry = AllocationLedgerEntry(
            tenant_id=assignment.tenant_id,
            ledger_entry_id=str(uuid4()),
            assignment_id=assignment.assignment_id,
            project_id=assignment.project_id,
            employee_id=assignment.employee_id,
            action=action,
            previous_allocation_percentage=previous_allocation_percentage,
            new_allocation_percentage=new_allocation_percentage,
            status=assignment.allocation_status,
            actor_id=actor_id,
            actor_type=actor_type,
            created_at=self._now(),
            details=details,
        )
        self.allocation_ledger[entry.ledger_entry_id] = entry

    def _emit(self, event_name: str, payload: dict[str, Any], *, tenant_id: str, correlation_id: str, aggregate_type: str, aggregate_id: str) -> None:
        event = emit_canonical_event(
            self.events,
            legacy_event_name=event_name,
            data=payload,
            source='project-service',
            tenant_id=tenant_id,
            registry=self.event_registry,
            correlation_id=correlation_id,
            idempotency_key=f'{aggregate_type}:{aggregate_id}:{event_name}:{correlation_id}',
        )
        self.event_outbox.stage_canonical_event(event, aggregate_type=aggregate_type, aggregate_id=aggregate_id)

    def _audit(self, action: str, entity: str, entity_id: str, before: dict[str, Any], after: dict[str, Any], *, actor_id: str, actor_type: str, tenant_id: str, trace_id: str) -> None:
        emit_audit_record(
            service_name='project-service',
            tenant_id=tenant_id,
            actor={'id': actor_id, 'type': actor_type},
            action=action,
            entity=entity,
            entity_id=entity_id,
            before=before,
            after=after,
            trace_id=trace_id,
        )

    def _find_project_by_code(self, tenant_id: str, project_code: str) -> Project | None:
        for project in self.projects.values():
            if project.tenant_id == tenant_id and project.project_code == project_code:
                return project
        return None

    def _require_project(self, project_id: str, *, tenant_id: str, trace_id: str) -> Project:
        project = self.projects.get(project_id)
        if project is None:
            raise self._error(404, 'NOT_FOUND', 'project was not found', trace_id)
        try:
            assert_tenant_access(project.tenant_id, tenant_id)
        except PermissionError as exc:
            raise self._error(403, 'TENANT_SCOPE_VIOLATION', 'project is outside the requested tenant scope', trace_id) from exc
        return project

    def _require_assignment(self, assignment_id: str, *, tenant_id: str, trace_id: str) -> ProjectAssignment:
        assignment = self.assignments.get(assignment_id)
        if assignment is None:
            raise self._error(404, 'NOT_FOUND', 'project assignment was not found', trace_id)
        try:
            assert_tenant_access(assignment.tenant_id, tenant_id)
        except PermissionError as exc:
            raise self._error(403, 'TENANT_SCOPE_VIOLATION', 'project assignment is outside the requested tenant scope', trace_id) from exc
        return assignment

    def _require_employee(self, employee_id: str | None, *, tenant_id: str, field: str, trace_id: str) -> EmployeeSnapshot:
        if not employee_id:
            raise self._error(422, 'VALIDATION_ERROR', f'{field} is required', trace_id, [{'field': field, 'reason': 'must be provided'}])
        employee = self.employee_snapshots.get(str(employee_id))
        if employee is None or employee.tenant_id != tenant_id:
            raise self._error(404, 'NOT_FOUND', f'{field} was not found in employee-service read model', trace_id)
        if employee.status in {'Terminated', 'Suspended'}:
            raise self._error(409, 'INVALID_REFERENCE', f'{field} references an ineligible employee', trace_id, [{'field': field, 'reason': f'employee status is {employee.status}'}])
        return employee

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
            map_error=lambda exc: self._error(exc.status_code, exc.payload['error']['code'], exc.payload['error']['message'], trace_id, exc.payload['error'].get('details')),
            invalid_action=lambda _action: self._error(422, 'VALIDATION_ERROR', 'action must be approve or reject', trace_id, [{'field': 'action', 'reason': 'must be approve or reject'}]),
        )

    def _require_terminal_workflow_result(self, workflow: dict[str, Any], *, action: str, trace_id: str) -> str:
        return require_terminal_workflow_result(
            workflow,
            action=action,
            on_mismatch=lambda _actual, _expected: self._error(409, 'WORKFLOW_BYPASS_DETECTED', 'workflow decision did not produce a valid assignment terminal result', trace_id),
            invalid_action=lambda _action: self._error(422, 'VALIDATION_ERROR', 'action must be approve or reject', trace_id, [{'field': 'action', 'reason': 'must be approve or reject'}]),
        )

    def _paginate(self, items: list[dict[str, Any]], *, limit: int, cursor: str | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        page_limit = min(max(limit, 1), 100)
        offset = self._decode_cursor(cursor)
        page = items[offset: offset + page_limit]
        next_cursor = self._encode_cursor(offset + page_limit) if offset + page_limit < len(items) else None
        return page, {'limit': page_limit, 'cursor': cursor, 'next_cursor': next_cursor, 'count': len(page)}

    @staticmethod
    def _encode_cursor(offset: int) -> str:
        return base64.urlsafe_b64encode(str(offset).encode('utf-8')).decode('utf-8').rstrip('=')

    @staticmethod
    def _decode_cursor(cursor: str | None) -> int:
        if not cursor:
            return 0
        padded = cursor + '=' * (-len(cursor) % 4)
        try:
            return int(base64.urlsafe_b64decode(padded.encode('utf-8')).decode('utf-8'))
        except Exception as exc:  # pragma: no cover - defensive guard
            raise ValueError('invalid cursor') from exc

    def _trace(self, trace_id: str | None = None) -> str:
        return self.observability.trace_id(trace_id)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _error(self, status_code: int, code: str, message: str, trace_id: str, details: list[dict[str, Any]] | None = None) -> ProjectServiceError:
        return ProjectServiceError(status_code, code, message, trace_id, details)

    def _coerce_date(self, value: Any, field: str, trace_id: str) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if not value:
            raise self._error(422, 'VALIDATION_ERROR', f'{field} is required', trace_id, [{'field': field, 'reason': 'must be provided'}])
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise self._error(422, 'VALIDATION_ERROR', f'{field} must be a valid ISO date', trace_id, [{'field': field, 'reason': 'must use YYYY-MM-DD'}]) from exc

    def _coerce_optional_date(self, value: Any, field: str, trace_id: str) -> date | None:
        if value in (None, ''):
            return None
        return self._coerce_date(value, field, trace_id)

    def _coerce_float(self, value: Any, field: str, trace_id: str, *, minimum: float, maximum: float | None = None) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise self._error(422, 'VALIDATION_ERROR', f'{field} must be numeric', trace_id, [{'field': field, 'reason': 'must be numeric'}]) from exc
        if number < minimum or (maximum is not None and number > maximum):
            comparator = f'between {minimum} and {maximum}' if maximum is not None else f'>= {minimum}'
            raise self._error(422, 'VALIDATION_ERROR', f'{field} is out of range', trace_id, [{'field': field, 'reason': f'must be {comparator}'}])
        return round(number, 2)

    def _coerce_optional_float(self, value: Any, field: str, trace_id: str, *, minimum: float) -> float | None:
        if value in (None, ''):
            return None
        return self._coerce_float(value, field, trace_id, minimum=minimum)
