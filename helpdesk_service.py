from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import RLock
from time import perf_counter
from typing import Any
from uuid import uuid4

from audit_service.service import emit_audit_record
from event_contract import EventRegistry, emit_canonical_event
from notification_service import NotificationService
from persistent_store import PersistentKVStore
from resilience import Observability
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id
from workflow_service import WorkflowService, WorkflowServiceError


class HelpdeskServiceError(Exception):
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
class TicketAttachment:
    attachment_id: str
    file_name: str
    content_type: str
    storage_key: str
    uploaded_by: str
    uploaded_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['uploaded_at'] = self.uploaded_at.isoformat()
        return payload


@dataclass(slots=True)
class TicketComment:
    comment_id: str
    author_employee_id: str
    body: str
    visibility: str
    created_at: datetime
    attachment_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['created_at'] = self.created_at.isoformat()
        return payload


@dataclass(slots=True)
class HelpdeskTicket:
    tenant_id: str
    ticket_id: str
    requester_employee_id: str
    subject: str
    category_code: str
    description: str
    priority: str
    status: str
    assigned_team: str
    queue_assignee_id: str
    resolver_employee_id: str
    workflow_id: str | None
    resolution_summary: str | None
    submitted_at: datetime | None
    first_response_due_at: datetime | None
    resolution_due_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    reopened_at: datetime | None
    created_at: datetime
    updated_at: datetime
    attachments: list[TicketAttachment] = field(default_factory=list)
    comments: list[TicketComment] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for field_name in (
            'submitted_at',
            'first_response_due_at',
            'resolution_due_at',
            'resolved_at',
            'closed_at',
            'reopened_at',
            'created_at',
            'updated_at',
        ):
            value = getattr(self, field_name)
            payload[field_name] = value.isoformat() if value else None
        payload['attachments'] = [item.to_dict() for item in self.attachments]
        payload['comments'] = [item.to_dict() for item in self.comments]
        return payload


class HelpdeskService:
    TICKET_STATUSES = {'Draft', 'Open', 'InProgress', 'Resolved', 'Closed'}
    PRIORITIES = {'Low', 'Medium', 'High', 'Urgent'}
    COMMENT_VISIBILITY = {'public', 'internal'}
    STAFF_ROLES = {'Admin', 'HR', 'Helpdesk', 'Manager'}

    def __init__(self, db_path: str | None = None, *, workflow_service: WorkflowService | None = None, notification_service: NotificationService | None = None) -> None:
        self.employee_snapshots = PersistentKVStore[str, EmployeeSnapshot](service='helpdesk-service', namespace='employee_snapshots', db_path=db_path)
        shared_db_path = self.employee_snapshots.db_path
        self.tickets = PersistentKVStore[str, HelpdeskTicket](service='helpdesk-service', namespace='tickets', db_path=shared_db_path)
        self.events: list[dict[str, Any]] = []
        self.event_registry = EventRegistry()
        self.notification_service = notification_service or NotificationService()
        self.workflow_service = workflow_service or WorkflowService(notification_service=self.notification_service)
        self.observability = Observability('helpdesk-service')
        self.tenant_id = DEFAULT_TENANT_ID
        self._lock = RLock()
        self._registered_workflow_tenants: set[str] = set()
        self._seed_defaults()
        self._register_workflows_for_tenant(DEFAULT_TENANT_ID)

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

    def create_ticket(self, payload: dict[str, Any], *, actor_id: str, actor_role: str | None = None, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        self._register_workflows_for_tenant(tenant_id)
        requester = self._require_employee(payload.get('requester_employee_id') or actor_id, tenant_id=tenant_id, field='requester_employee_id', trace_id=trace)
        subject = str(payload.get('subject') or '').strip()
        description = str(payload.get('description') or '').strip()
        category_code = str(payload.get('category_code') or 'GENERAL').strip().upper()
        priority = str(payload.get('priority') or 'Medium').strip().title()
        if not subject:
            raise self._error(422, 'VALIDATION_ERROR', 'subject is required', trace, [{'field': 'subject', 'reason': 'must be a non-empty string'}])
        if not description:
            raise self._error(422, 'VALIDATION_ERROR', 'description is required', trace, [{'field': 'description', 'reason': 'must be a non-empty string'}])
        if priority not in self.PRIORITIES:
            raise self._error(422, 'VALIDATION_ERROR', 'priority is invalid', trace, [{'field': 'priority', 'reason': f'must be one of {sorted(self.PRIORITIES)}'}])
        now = self._now()
        ticket = HelpdeskTicket(
            tenant_id=tenant_id,
            ticket_id=str(uuid4()),
            requester_employee_id=requester.employee_id,
            subject=subject,
            category_code=category_code,
            description=description,
            priority=priority,
            status='Draft',
            assigned_team='HR Helpdesk',
            queue_assignee_id=str(payload.get('queue_assignee_id') or 'helpdesk-agent'),
            resolver_employee_id=str(payload.get('resolver_employee_id') or 'hr-helpdesk-specialist'),
            workflow_id=None,
            resolution_summary=None,
            submitted_at=None,
            first_response_due_at=None,
            resolution_due_at=None,
            resolved_at=None,
            closed_at=None,
            reopened_at=None,
            created_at=now,
            updated_at=now,
            attachments=self._normalize_attachments(payload.get('attachments') or [], actor_id=actor_id),
            comments=[],
            metadata={'requester_department_id': requester.department_id, 'last_sla_status': 'draft'},
        )
        initial_comment = str(payload.get('initial_comment') or '').strip()
        if initial_comment:
            ticket.comments.append(self._make_comment(initial_comment, actor_id=actor_id, visibility='public'))
        with self._lock:
            self.tickets[ticket.ticket_id] = ticket
            response = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            self._audit('helpdesk_ticket_created', 'HelpdeskTicket', ticket.ticket_id, {}, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
            self._emit('HelpdeskTicketCreated', response, tenant_id=tenant_id, correlation_id=trace, aggregate_id=ticket.ticket_id)
        self.observability.track('helpdesk.create_ticket', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant_id, 'status': 201})
        return 201, response

    def add_attachment(self, ticket_id: str, payload: dict[str, Any], *, actor_id: str, actor_role: str | None = None, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id or payload.get('tenant_id'))
        with self._lock:
            ticket = self._require_ticket(ticket_id, tenant_id=tenant, trace_id=trace)
            self._assert_ticket_visibility(ticket, actor_id=actor_id, actor_role=actor_role, trace_id=trace)
            before = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            attachment = self._normalize_attachment(payload, actor_id=actor_id)
            ticket.attachments.append(attachment)
            ticket.updated_at = self._now()
            self.tickets[ticket.ticket_id] = ticket
            response = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            self._audit('helpdesk_ticket_attachment_added', 'HelpdeskTicket', ticket.ticket_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant, trace_id=trace)
            self._emit('HelpdeskTicketAttachmentAdded', {'ticket_id': ticket.ticket_id, 'attachment': attachment.to_dict(), 'status': ticket.status}, tenant_id=tenant, correlation_id=trace, aggregate_id=ticket.ticket_id)
        self.observability.track('helpdesk.add_attachment', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant, 'status': 200})
        return 200, response

    def add_comment(self, ticket_id: str, payload: dict[str, Any], *, actor_id: str, actor_role: str | None = None, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id or payload.get('tenant_id'))
        body = str(payload.get('body') or '').strip()
        visibility = str(payload.get('visibility') or 'public').strip().lower()
        if not body:
            raise self._error(422, 'VALIDATION_ERROR', 'comment body is required', trace, [{'field': 'body', 'reason': 'must be a non-empty string'}])
        if visibility not in self.COMMENT_VISIBILITY:
            raise self._error(422, 'VALIDATION_ERROR', 'comment visibility is invalid', trace, [{'field': 'visibility', 'reason': f'must be one of {sorted(self.COMMENT_VISIBILITY)}'}])
        if visibility == 'internal' and actor_role not in self.STAFF_ROLES:
            raise self._error(403, 'FORBIDDEN', 'only helpdesk staff can post internal comments', trace)
        attachment_ids = [str(item).strip() for item in payload.get('attachment_ids') or [] if str(item).strip()]
        with self._lock:
            ticket = self._require_ticket(ticket_id, tenant_id=tenant, trace_id=trace)
            self._assert_ticket_visibility(ticket, actor_id=actor_id, actor_role=actor_role, trace_id=trace)
            if attachment_ids:
                valid_ids = {attachment.attachment_id for attachment in ticket.attachments}
                missing = [item for item in attachment_ids if item not in valid_ids]
                if missing:
                    raise self._error(422, 'VALIDATION_ERROR', 'attachment_ids contain unknown values', trace, [{'field': 'attachment_ids', 'reason': f'unknown attachment ids: {missing}'}])
            before = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            comment = self._make_comment(body, actor_id=actor_id, visibility=visibility, attachment_ids=attachment_ids)
            ticket.comments.append(comment)
            ticket.updated_at = self._now()
            self.tickets[ticket.ticket_id] = ticket
            response = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            self._audit('helpdesk_ticket_comment_added', 'HelpdeskTicket', ticket.ticket_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant, trace_id=trace)
            self._emit('HelpdeskTicketCommentAdded', {'ticket_id': ticket.ticket_id, 'comment': comment.to_dict(), 'status': ticket.status}, tenant_id=tenant, correlation_id=trace, aggregate_id=ticket.ticket_id)
        self.observability.track('helpdesk.add_comment', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant, 'status': 200})
        return 200, response

    def submit_ticket(self, ticket_id: str, *, actor_id: str, actor_role: str | None = None, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id)
        self._register_workflows_for_tenant(tenant)
        with self._lock:
            ticket = self._require_ticket(ticket_id, tenant_id=tenant, trace_id=trace)
            if ticket.requester_employee_id != actor_id and actor_role not in self.STAFF_ROLES:
                raise self._error(403, 'FORBIDDEN', 'only the requester or helpdesk staff can submit the ticket', trace)
            before = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            if ticket.status == 'Open':
                return 200, before
            if ticket.status != 'Draft':
                raise self._error(409, 'INVALID_TRANSITION', 'only Draft tickets can be submitted', trace)
            workflow = self.workflow_service.start_workflow(
                tenant_id=tenant,
                definition_code='hr_helpdesk_ticket_lifecycle',
                source_service='helpdesk-service',
                subject_type='HelpdeskTicket',
                subject_id=ticket.ticket_id,
                actor_id=actor_id,
                actor_type=actor_type,
                context={
                    'queue_assignee': ticket.queue_assignee_id,
                    'queue_escalation_assignee': 'hr-helpdesk-lead',
                    'resolver_assignee': ticket.resolver_employee_id,
                    'resolver_escalation_assignee': 'hr-ops-manager',
                    'priority': ticket.priority,
                },
                trace_id=trace,
            )
            now = self._now()
            ticket.workflow_id = workflow['workflow_id']
            ticket.status = 'Open'
            ticket.submitted_at = now
            ticket.updated_at = now
            ticket.first_response_due_at = self._parse_datetime(workflow['steps'][0]['metadata'].get('deadline_at'))
            ticket.resolution_due_at = self._parse_datetime(workflow['steps'][1]['metadata'].get('deadline_at')) if len(workflow['steps']) > 1 else None
            ticket.metadata['last_sla_status'] = 'on_track'
            self.tickets[ticket.ticket_id] = ticket
            response = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            self._audit('helpdesk_ticket_submitted', 'HelpdeskTicket', ticket.ticket_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant, trace_id=trace)
            self._emit('HelpdeskTicketSubmitted', response, tenant_id=tenant, correlation_id=trace, aggregate_id=ticket.ticket_id)
        self.observability.track('helpdesk.submit_ticket', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant, 'status': 200})
        return 200, response

    def decide_ticket(self, ticket_id: str, *, action: str, actor_id: str, actor_role: str | None, actor_type: str = 'user', tenant_id: str | None = None, comment: str | None = None, resolution_summary: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id)
        with self._lock:
            ticket = self._require_ticket(ticket_id, tenant_id=tenant, trace_id=trace)
            before = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            if ticket.status not in {'Open', 'InProgress'}:
                raise self._error(409, 'INVALID_TRANSITION', 'ticket is not awaiting workflow action', trace)
            if not ticket.workflow_id:
                raise self._error(409, 'WORKFLOW_MISSING', 'helpdesk ticket is missing centralized workflow', trace)
            try:
                workflow = (
                    self.workflow_service.approve_step(ticket.workflow_id, tenant_id=tenant, actor_id=actor_id, actor_type=actor_type, actor_role=actor_role, comment=comment, trace_id=trace)
                    if action == 'approve'
                    else self.workflow_service.reject_step(ticket.workflow_id, tenant_id=tenant, actor_id=actor_id, actor_type=actor_type, actor_role=actor_role, comment=comment, trace_id=trace)
                )
            except WorkflowServiceError as exc:
                raise self._error(exc.status_code, exc.code, exc.message, trace, exc.details) from exc
            terminal_result = workflow.get('metadata', {}).get('terminal_result')
            now = self._now()
            active_steps = [step for step in workflow['steps'] if step['status'] == 'pending' and step.get('metadata', {}).get('active')]
            if action == 'approve' and terminal_result == 'approved':
                ticket.status = 'Resolved'
                ticket.resolved_at = now
                ticket.resolution_summary = str(resolution_summary or comment or ticket.resolution_summary or 'Resolved by HR helpdesk').strip()
                audit_action = 'helpdesk_ticket_resolved'
                event_name = 'HelpdeskTicketResolved'
            elif action == 'reject' and terminal_result == 'rejected':
                ticket.status = 'Closed'
                ticket.closed_at = now
                ticket.resolution_summary = str(resolution_summary or comment or 'Ticket closed during triage').strip()
                audit_action = 'helpdesk_ticket_closed'
                event_name = 'HelpdeskTicketClosed'
            elif action == 'approve' and active_steps:
                ticket.status = 'InProgress'
                audit_action = 'helpdesk_ticket_in_progress'
                event_name = 'HelpdeskTicketInProgress'
            else:
                raise self._error(409, 'WORKFLOW_BYPASS_DETECTED', 'workflow decision did not produce a valid helpdesk lifecycle result', trace)
            ticket.updated_at = now
            ticket.metadata['last_sla_status'] = self._derive_sla_status(workflow)
            self.tickets[ticket.ticket_id] = ticket
            response = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            self._audit(audit_action, 'HelpdeskTicket', ticket.ticket_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant, trace_id=trace)
            self._emit(event_name, response, tenant_id=tenant, correlation_id=trace, aggregate_id=ticket.ticket_id)
        self.observability.track('helpdesk.decide_ticket', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant, 'status': 200, 'action': action})
        return 200, response

    def close_ticket(self, ticket_id: str, payload: dict[str, Any] | None = None, *, actor_id: str, actor_role: str | None = None, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        body = payload or {}
        tenant = normalize_tenant_id(tenant_id or body.get('tenant_id'))
        with self._lock:
            ticket = self._require_ticket(ticket_id, tenant_id=tenant, trace_id=trace)
            if ticket.requester_employee_id != actor_id and actor_role not in self.STAFF_ROLES:
                raise self._error(403, 'FORBIDDEN', 'only the requester or helpdesk staff can close the ticket', trace)
            before = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            if ticket.status == 'Closed':
                return 200, before
            if ticket.status != 'Resolved':
                raise self._error(409, 'INVALID_TRANSITION', 'only Resolved tickets can be closed', trace)
            ticket.status = 'Closed'
            ticket.closed_at = self._now()
            ticket.updated_at = ticket.closed_at
            if body.get('closure_comment'):
                ticket.comments.append(self._make_comment(str(body['closure_comment']).strip(), actor_id=actor_id, visibility='public'))
            self.tickets[ticket.ticket_id] = ticket
            response = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            self._audit('helpdesk_ticket_closed', 'HelpdeskTicket', ticket.ticket_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant, trace_id=trace)
            self._emit('HelpdeskTicketClosed', response, tenant_id=tenant, correlation_id=trace, aggregate_id=ticket.ticket_id)
        self.observability.track('helpdesk.close_ticket', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant, 'status': 200})
        return 200, response

    def reopen_ticket(self, ticket_id: str, payload: dict[str, Any] | None = None, *, actor_id: str, actor_role: str | None = None, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        body = payload or {}
        tenant = normalize_tenant_id(tenant_id or body.get('tenant_id'))
        self._register_workflows_for_tenant(tenant)
        with self._lock:
            ticket = self._require_ticket(ticket_id, tenant_id=tenant, trace_id=trace)
            if ticket.requester_employee_id != actor_id and actor_role not in self.STAFF_ROLES:
                raise self._error(403, 'FORBIDDEN', 'only the requester or helpdesk staff can reopen the ticket', trace)
            before = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            if ticket.status != 'Closed':
                raise self._error(409, 'INVALID_TRANSITION', 'only Closed tickets can be reopened', trace)
            workflow = self.workflow_service.start_workflow(
                tenant_id=tenant,
                definition_code='hr_helpdesk_ticket_lifecycle',
                source_service='helpdesk-service',
                subject_type='HelpdeskTicket',
                subject_id=ticket.ticket_id,
                actor_id=actor_id,
                actor_type=actor_type,
                context={
                    'queue_assignee': ticket.queue_assignee_id,
                    'queue_escalation_assignee': 'hr-helpdesk-lead',
                    'resolver_assignee': ticket.resolver_employee_id,
                    'resolver_escalation_assignee': 'hr-ops-manager',
                    'priority': ticket.priority,
                },
                trace_id=trace,
            )
            ticket.status = 'Open'
            ticket.workflow_id = workflow['workflow_id']
            ticket.closed_at = None
            ticket.resolved_at = None
            ticket.reopened_at = self._now()
            ticket.updated_at = ticket.reopened_at
            ticket.metadata['last_sla_status'] = 'on_track'
            if body.get('reopen_comment'):
                ticket.comments.append(self._make_comment(str(body['reopen_comment']).strip(), actor_id=actor_id, visibility='public'))
            self.tickets[ticket.ticket_id] = ticket
            response = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            self._audit('helpdesk_ticket_reopened', 'HelpdeskTicket', ticket.ticket_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant, trace_id=trace)
            self._emit('HelpdeskTicketReopened', response, tenant_id=tenant, correlation_id=trace, aggregate_id=ticket.ticket_id)
        self.observability.track('helpdesk.reopen_ticket', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant, 'status': 200})
        return 200, response

    def run_sla_monitor(self, *, now: datetime | None = None, tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id)
        current = now or self._now()
        escalated = self.workflow_service.escalate_due_workflows(now=current, tenant_id=tenant, trace_id=trace)
        affected: list[dict[str, Any]] = []
        with self._lock:
            workflows_by_id = {item['workflow_id']: item for item in escalated}
            for ticket in self.tickets.values():
                if ticket.tenant_id != tenant or not ticket.workflow_id or ticket.workflow_id not in workflows_by_id:
                    continue
                before = self._ticket_payload(ticket)
                workflow = workflows_by_id[ticket.workflow_id]
                ticket.updated_at = current
                ticket.metadata['last_sla_status'] = self._derive_sla_status(workflow)
                self.tickets[ticket.ticket_id] = ticket
                after = self._ticket_payload(ticket)
                self._audit('helpdesk_ticket_sla_escalated', 'HelpdeskTicket', ticket.ticket_id, before, after, actor_id='workflow-engine', actor_type='service', tenant_id=ticket.tenant_id, trace_id=trace)
                self._emit('HelpdeskTicketSlaEscalated', after, tenant_id=ticket.tenant_id, correlation_id=trace, aggregate_id=ticket.ticket_id)
                affected.append(after)
        return 200, {'items': affected, 'data': affected}

    def get_ticket(self, ticket_id: str, *, tenant_id: str | None = None, actor_id: str | None = None, actor_role: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        ticket = self._require_ticket(ticket_id, tenant_id=normalize_tenant_id(tenant_id), trace_id=trace)
        if actor_id:
            self._assert_ticket_visibility(ticket, actor_id=actor_id, actor_role=actor_role, trace_id=trace)
        return 200, self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)

    def list_tickets(
        self,
        *,
        tenant_id: str | None = None,
        requester_employee_id: str | None = None,
        assigned_employee_id: str | None = None,
        status: str | None = None,
        actor_id: str | None = None,
        actor_role: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        rows: list[dict[str, Any]] = []
        for ticket in self.tickets.values():
            if ticket.tenant_id != tenant:
                continue
            if requester_employee_id is not None and ticket.requester_employee_id != requester_employee_id:
                continue
            if status is not None and ticket.status != status:
                continue
            payload = self._ticket_payload(ticket, actor_id=actor_id, actor_role=actor_role)
            current_assignee = payload.get('sla', {}).get('current_assignee')
            if assigned_employee_id is not None and current_assignee != assigned_employee_id:
                continue
            if actor_id and actor_role not in self.STAFF_ROLES and ticket.requester_employee_id != actor_id:
                continue
            rows.append(payload)
        rows.sort(key=lambda item: (item['created_at'], item['ticket_id']))
        return 200, {'items': rows, 'data': rows, '_pagination': {'count': len(rows)}}

    def _seed_defaults(self) -> None:
        if self.employee_snapshots.values():
            return
        defaults = [
            {'employee_id': 'emp-001', 'employee_number': 'E-001', 'full_name': 'Nina Employee', 'department_id': 'dep-eng', 'department_name': 'Engineering', 'manager_employee_id': 'emp-manager', 'email': 'nina@example.com'},
            {'employee_id': 'emp-manager', 'employee_number': 'E-002', 'full_name': 'Manny Manager', 'department_id': 'dep-eng', 'department_name': 'Engineering', 'manager_employee_id': 'helpdesk-agent', 'email': 'manager@example.com'},
            {'employee_id': 'helpdesk-agent', 'employee_number': 'E-003', 'full_name': 'Harper Helpdesk', 'department_id': 'dep-hr', 'department_name': 'HR Operations', 'manager_employee_id': 'hr-helpdesk-lead', 'email': 'helpdesk@example.com'},
            {'employee_id': 'hr-helpdesk-specialist', 'employee_number': 'E-004', 'full_name': 'Rowan Specialist', 'department_id': 'dep-hr', 'department_name': 'HR Operations', 'manager_employee_id': 'hr-helpdesk-lead', 'email': 'specialist@example.com'},
            {'employee_id': 'hr-helpdesk-lead', 'employee_number': 'E-005', 'full_name': 'Lena Lead', 'department_id': 'dep-hr', 'department_name': 'HR Operations', 'manager_employee_id': 'hr-ops-manager', 'email': 'lead@example.com'},
            {'employee_id': 'hr-ops-manager', 'employee_number': 'E-006', 'full_name': 'Owen Ops', 'department_id': 'dep-hr', 'department_name': 'HR Operations', 'manager_employee_id': None, 'email': 'ops@example.com'},
        ]
        for row in defaults:
            self.register_employee_profile(row)

    def _register_workflows_for_tenant(self, tenant_id: str) -> None:
        tenant = normalize_tenant_id(tenant_id)
        if tenant in self._registered_workflow_tenants:
            return
        self.workflow_service.register_definition(
            tenant_id=tenant,
            code='hr_helpdesk_ticket_lifecycle',
            source_service='helpdesk-service',
            subject_type='HelpdeskTicket',
            description='HR helpdesk lifecycle with triage and resolution SLA enforcement.',
            steps=[
                {
                    'name': 'triage',
                    'type': 'approval',
                    'assignee_template': '{queue_assignee}',
                    'sla': 'PT2H',
                    'escalation_assignee_template': '{queue_escalation_assignee}',
                },
                {
                    'name': 'resolution',
                    'type': 'approval',
                    'assignee_template': '{resolver_assignee}',
                    'sla': 'PT8H',
                    'escalation_assignee_template': '{resolver_escalation_assignee}',
                },
            ],
        )
        self._registered_workflow_tenants.add(tenant)

    def _ticket_payload(self, ticket: HelpdeskTicket, *, actor_id: str | None = None, actor_role: str | None = None) -> dict[str, Any]:
        requester = self._require_employee(ticket.requester_employee_id, tenant_id=ticket.tenant_id, field='requester_employee_id', trace_id=self.observability.trace_id())
        workflow = self.workflow_service.get_instance(ticket.workflow_id, tenant_id=ticket.tenant_id, actor_id=actor_id) if ticket.workflow_id else None
        visible_comments = [
            comment.to_dict()
            for comment in ticket.comments
            if self._comment_visible(comment, actor_id=actor_id, actor_role=actor_role, requester_employee_id=ticket.requester_employee_id)
        ]
        return {
            **ticket.to_dict(),
            'requester': requester.to_dict(),
            'comments': visible_comments,
            'workflow': workflow,
            'sla': self._sla_summary(ticket, workflow),
        }

    @classmethod
    def _comment_visible(cls, comment: TicketComment, *, actor_id: str | None, actor_role: str | None, requester_employee_id: str) -> bool:
        if comment.visibility == 'public':
            return True
        if actor_role in cls.STAFF_ROLES:
            return True
        return actor_id == comment.author_employee_id == requester_employee_id

    def _sla_summary(self, ticket: HelpdeskTicket, workflow: dict[str, Any] | None) -> dict[str, Any]:
        if not workflow:
            return {'status': ticket.metadata.get('last_sla_status', 'draft')}
        active = next((step for step in workflow['steps'] if step['status'] == 'pending' and step.get('metadata', {}).get('active')), None)
        if active is None:
            return {'status': 'completed', 'current_assignee': None, 'deadline_at': None, 'escalated_at': None}
        metadata = active.get('metadata') or {}
        status = 'escalated' if metadata.get('escalated_at') else 'on_track'
        return {
            'status': status,
            'current_step': active.get('step_id'),
            'current_step_name': metadata.get('name') or active.get('type'),
            'current_assignee': active.get('assignee'),
            'deadline_at': metadata.get('deadline_at'),
            'escalated_at': metadata.get('escalated_at'),
            'escalated_from': metadata.get('escalated_from'),
        }

    @staticmethod
    def _derive_sla_status(workflow: dict[str, Any]) -> str:
        active = next((step for step in workflow['steps'] if step['status'] == 'pending' and step.get('metadata', {}).get('active')), None)
        if active is None:
            return 'completed'
        return 'escalated' if active.get('metadata', {}).get('escalated_at') else 'on_track'

    def _assert_ticket_visibility(self, ticket: HelpdeskTicket, *, actor_id: str, actor_role: str | None, trace_id: str) -> None:
        if actor_role in self.STAFF_ROLES or ticket.requester_employee_id == actor_id:
            return
        raise self._error(403, 'FORBIDDEN', 'ticket is outside the actor visibility scope', trace_id)

    def _require_employee(self, employee_id: str | None, *, tenant_id: str, field: str, trace_id: str) -> EmployeeSnapshot:
        if not employee_id:
            raise self._error(422, 'VALIDATION_ERROR', f'{field} is required', trace_id, [{'field': field, 'reason': 'must be provided'}])
        employee = self.employee_snapshots.get(str(employee_id))
        if employee is None or employee.tenant_id != tenant_id:
            raise self._error(404, 'NOT_FOUND', f'{field} was not found in employee-service read model', trace_id)
        if employee.status == 'Terminated':
            raise self._error(409, 'INVALID_REFERENCE', f'{field} references a terminated employee', trace_id, [{'field': field, 'reason': 'employee is terminated'}])
        return employee

    def _require_ticket(self, ticket_id: str, *, tenant_id: str, trace_id: str) -> HelpdeskTicket:
        ticket = self.tickets.get(ticket_id)
        if ticket is None:
            raise self._error(404, 'NOT_FOUND', 'helpdesk ticket was not found', trace_id)
        try:
            assert_tenant_access(ticket.tenant_id, tenant_id)
        except PermissionError as exc:
            raise self._error(403, 'TENANT_SCOPE_VIOLATION', 'helpdesk ticket is outside the requested tenant scope', trace_id) from exc
        return ticket

    def _audit(self, action: str, entity: str, entity_id: str, before: dict[str, Any], after: dict[str, Any], *, actor_id: str, actor_type: str, tenant_id: str, trace_id: str) -> None:
        emit_audit_record(
            service_name='helpdesk-service',
            tenant_id=tenant_id,
            actor={'id': actor_id, 'type': actor_type},
            action=action,
            entity=entity,
            entity_id=entity_id,
            before=before,
            after=after,
            trace_id=trace_id,
            source={'bounded_context': 'hr-helpdesk'},
        )

    def _emit(self, legacy_event_name: str, data: dict[str, Any], *, tenant_id: str, correlation_id: str | None, aggregate_id: str) -> None:
        emit_canonical_event(
            self.events,
            legacy_event_name=legacy_event_name,
            data={'tenant_id': tenant_id, **data},
            source='helpdesk-service',
            tenant_id=tenant_id,
            registry=self.event_registry,
            correlation_id=correlation_id,
            idempotency_key=f'{aggregate_id}:{legacy_event_name}:{data.get("status", "mutation")}',
        )

    @staticmethod
    def _make_comment(body: str, *, actor_id: str, visibility: str, attachment_ids: list[str] | None = None) -> TicketComment:
        return TicketComment(
            comment_id=str(uuid4()),
            author_employee_id=actor_id,
            body=body,
            visibility=visibility,
            created_at=datetime.now(timezone.utc),
            attachment_ids=list(attachment_ids or []),
        )

    @staticmethod
    def _normalize_attachment(payload: dict[str, Any], *, actor_id: str) -> TicketAttachment:
        file_name = str(payload.get('file_name') or '').strip()
        content_type = str(payload.get('content_type') or '').strip() or 'application/octet-stream'
        storage_key = str(payload.get('storage_key') or '').strip()
        if not file_name or not storage_key:
            raise ValueError('attachment requires file_name and storage_key')
        return TicketAttachment(
            attachment_id=str(uuid4()),
            file_name=file_name,
            content_type=content_type,
            storage_key=storage_key,
            uploaded_by=actor_id,
            uploaded_at=datetime.now(timezone.utc),
        )

    def _normalize_attachments(self, rows: list[dict[str, Any]], *, actor_id: str) -> list[TicketAttachment]:
        return [self._normalize_attachment(row, actor_id=actor_id) for row in rows]

    @staticmethod
    def _parse_datetime(raw: Any) -> datetime | None:
        if not raw:
            return None
        return datetime.fromisoformat(str(raw).replace('Z', '+00:00'))

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _trace(self, trace_id: str | None = None) -> str:
        return self.observability.trace_id(trace_id)

    @staticmethod
    def _error(status_code: int, code: str, message: str, trace_id: str, details: list[dict[str, Any]] | None = None) -> HelpdeskServiceError:
        return HelpdeskServiceError(status_code, code, message, trace_id, details)
