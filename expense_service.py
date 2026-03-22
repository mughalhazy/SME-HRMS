from __future__ import annotations

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


class ExpenseServiceError(Exception):
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
class ExpenseCategory:
    tenant_id: str
    category_id: str
    code: str
    name: str
    requires_attachment: bool
    reimbursable: bool
    max_amount: float | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['created_at'] = self.created_at.isoformat()
        payload['updated_at'] = self.updated_at.isoformat()
        return payload


@dataclass(slots=True)
class ExpenseAttachment:
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
class ExpenseClaim:
    tenant_id: str
    expense_claim_id: str
    employee_id: str
    category_id: str
    category_code: str
    amount: float
    currency: str
    expense_date: date
    description: str
    status: str
    approver_employee_id: str | None
    workflow_id: str | None
    submitted_at: datetime | None
    approved_at: datetime | None
    rejected_at: datetime | None
    reimbursed_at: datetime | None
    reimbursed_by: str | None
    reimbursement_reference: str | None
    created_at: datetime
    updated_at: datetime
    attachments: list[ExpenseAttachment] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['expense_date'] = self.expense_date.isoformat()
        for field_name in ('submitted_at', 'approved_at', 'rejected_at', 'reimbursed_at', 'created_at', 'updated_at'):
            value = getattr(self, field_name)
            payload[field_name] = value.isoformat() if value else None
        payload['attachments'] = [item.to_dict() for item in self.attachments]
        return payload


class ExpenseService:
    CLAIM_STATUSES = {'Draft', 'Submitted', 'Approved', 'Rejected', 'Reimbursed'}

    def __init__(self, db_path: str | None = None, *, workflow_service: WorkflowService | None = None, notification_service: NotificationService | None = None) -> None:
        self.employee_snapshots = PersistentKVStore[str, EmployeeSnapshot](service='expense-service', namespace='employee_snapshots', db_path=db_path)
        shared_db_path = self.employee_snapshots.db_path
        self.categories = PersistentKVStore[str, ExpenseCategory](service='expense-service', namespace='categories', db_path=shared_db_path)
        self.claims = PersistentKVStore[str, ExpenseClaim](service='expense-service', namespace='claims', db_path=shared_db_path)
        self.events: list[dict[str, Any]] = []
        self.event_registry = EventRegistry()
        self.event_outbox = EventOutbox(db_path=shared_db_path)
        self.notification_service = notification_service or NotificationService()
        self.workflow_service = workflow_service or WorkflowService(notification_service=self.notification_service)
        self.observability = Observability('expense-service')
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
        )
        self.employee_snapshots[snapshot.employee_id] = snapshot
        return snapshot.to_dict()

    def create_category(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        self._register_workflows_for_tenant(tenant_id)
        code = str(payload.get('code') or '').strip().upper()
        name = str(payload.get('name') or '').strip()
        if not code:
            raise self._error(422, 'VALIDATION_ERROR', 'code is required', trace, [{'field': 'code', 'reason': 'must be a non-empty string'}])
        if not name:
            raise self._error(422, 'VALIDATION_ERROR', 'name is required', trace, [{'field': 'name', 'reason': 'must be a non-empty string'}])
        with self._lock:
            existing = self._find_category_by_code(tenant_id, code)
            before = existing.to_dict() if existing else {}
            now = self._now()
            if existing is None:
                category = ExpenseCategory(
                    tenant_id=tenant_id,
                    category_id=str(uuid4()),
                    code=code,
                    name=name,
                    requires_attachment=bool(payload.get('requires_attachment', False)),
                    reimbursable=bool(payload.get('reimbursable', True)),
                    max_amount=float(payload['max_amount']) if payload.get('max_amount') is not None else None,
                    description=str(payload['description']).strip() if payload.get('description') is not None else None,
                    created_at=now,
                    updated_at=now,
                )
                self.categories[category.category_id] = category
                action = 'expense_category_created'
                event_name = 'ExpenseCategoryCreated'
                status_code = 201
            else:
                category = existing
                category.name = name
                category.requires_attachment = bool(payload.get('requires_attachment', category.requires_attachment))
                category.reimbursable = bool(payload.get('reimbursable', category.reimbursable))
                category.max_amount = float(payload['max_amount']) if payload.get('max_amount') is not None else None
                category.description = str(payload['description']).strip() if payload.get('description') is not None else category.description
                category.updated_at = now
                self.categories[category.category_id] = category
                action = 'expense_category_updated'
                event_name = 'ExpenseCategoryUpdated'
                status_code = 200
            response = category.to_dict()
            self._audit(action, 'ExpenseCategory', category.category_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
            self._emit(event_name, response, tenant_id=tenant_id, correlation_id=trace, aggregate_type='ExpenseCategory', aggregate_id=category.category_id)
        self.observability.track('expense.create_category', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant_id, 'status': status_code})
        return status_code, response

    def create_claim(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        self._register_workflows_for_tenant(tenant_id)
        employee = self._require_employee(payload.get('employee_id'), tenant_id=tenant_id, field='employee_id', trace_id=trace)
        category = self._require_category(payload.get('category_code'), tenant_id=tenant_id, trace_id=trace)
        amount = self._coerce_amount(payload.get('amount'), trace)
        if category.max_amount is not None and amount > category.max_amount:
            raise self._error(422, 'VALIDATION_ERROR', 'amount exceeds configured category limit', trace, [{'field': 'amount', 'reason': f'must be <= {category.max_amount}'}])
        attachments = self._normalize_attachments(payload.get('attachments') or [], actor_id=actor_id)
        if category.requires_attachment and not attachments:
            raise self._error(422, 'VALIDATION_ERROR', 'at least one attachment is required for this category', trace, [{'field': 'attachments', 'reason': 'required by category policy'}])
        now = self._now()
        claim = ExpenseClaim(
            tenant_id=tenant_id,
            expense_claim_id=str(uuid4()),
            employee_id=employee.employee_id,
            category_id=category.category_id,
            category_code=category.code,
            amount=amount,
            currency=str(payload.get('currency') or 'USD').strip().upper(),
            expense_date=self._coerce_date(payload.get('expense_date'), 'expense_date', trace),
            description=str(payload.get('description') or '').strip(),
            status='Draft',
            approver_employee_id=str(payload['approver_employee_id']).strip() if payload.get('approver_employee_id') else employee.manager_employee_id,
            workflow_id=None,
            submitted_at=None,
            approved_at=None,
            rejected_at=None,
            reimbursed_at=None,
            reimbursed_by=None,
            reimbursement_reference=None,
            created_at=now,
            updated_at=now,
            attachments=attachments,
            metadata={'employee_department_id': employee.department_id},
        )
        if not claim.description:
            raise self._error(422, 'VALIDATION_ERROR', 'description is required', trace, [{'field': 'description', 'reason': 'must be a non-empty string'}])
        with self._lock:
            self.claims[claim.expense_claim_id] = claim
            response = self._claim_payload(claim)
            self._audit('expense_claim_created', 'ExpenseClaim', claim.expense_claim_id, {}, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
            self._emit('ExpenseClaimCreated', response, tenant_id=tenant_id, correlation_id=trace, aggregate_type='ExpenseClaim', aggregate_id=claim.expense_claim_id)
        self.observability.track('expense.create_claim', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant_id, 'status': 201})
        return 201, response

    def add_attachment(self, expense_claim_id: str, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id or payload.get('tenant_id'))
        with self._lock:
            claim = self._require_claim(expense_claim_id, tenant_id=tenant, trace_id=trace)
            if claim.status != 'Draft':
                raise self._error(409, 'INVALID_TRANSITION', 'attachments can only be added while the claim is Draft', trace)
            before = self._claim_payload(claim)
            attachment = self._normalize_attachment(payload, actor_id=actor_id)
            claim.attachments.append(attachment)
            claim.updated_at = self._now()
            self.claims[claim.expense_claim_id] = claim
            response = self._claim_payload(claim)
            self._audit('expense_attachment_added', 'ExpenseClaim', claim.expense_claim_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant, trace_id=trace)
            self._emit(
                'ExpenseAttachmentAdded',
                {
                    'expense_claim_id': claim.expense_claim_id,
                    'employee_id': claim.employee_id,
                    'attachment': attachment.to_dict(),
                    'status': claim.status,
                },
                tenant_id=tenant,
                correlation_id=trace,
                aggregate_type='ExpenseClaim',
                aggregate_id=claim.expense_claim_id,
            )
        self.observability.track('expense.add_attachment', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant, 'status': 200})
        return 200, response

    def submit_claim(self, expense_claim_id: str, *, actor_id: str, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id)
        self._register_workflows_for_tenant(tenant)
        with self._lock:
            claim = self._require_claim(expense_claim_id, tenant_id=tenant, trace_id=trace)
            before = self._claim_payload(claim)
            if claim.status == 'Submitted':
                return 200, before
            if claim.status != 'Draft':
                raise self._error(409, 'INVALID_TRANSITION', 'only Draft claims can be submitted', trace)
            category = self._require_category(claim.category_code, tenant_id=tenant, trace_id=trace)
            if category.requires_attachment and not claim.attachments:
                raise self._error(422, 'VALIDATION_ERROR', 'attachments are required before submission', trace, [{'field': 'attachments', 'reason': 'required by category policy'}])
            approver = claim.approver_employee_id or self._require_employee(claim.employee_id, tenant_id=tenant, field='employee_id', trace_id=trace).manager_employee_id
            if not approver:
                raise self._error(422, 'VALIDATION_ERROR', 'approver_employee_id could not be resolved', trace, [{'field': 'approver_employee_id', 'reason': 'missing employee manager assignment'}])
            workflow = self.workflow_service.start_workflow(
                tenant_id=tenant,
                definition_code='expense_claim_approval',
                source_service='expense-service',
                subject_type='ExpenseClaim',
                subject_id=claim.expense_claim_id,
                actor_id=actor_id,
                actor_type=actor_type,
                context={
                    'approver_assignee': approver,
                    'escalation_assignee': 'finance-admin',
                    'category_code': claim.category_code,
                    'employee_id': claim.employee_id,
                    'amount': claim.amount,
                    'currency': claim.currency,
                },
                trace_id=trace,
            )
            now = self._now()
            claim.workflow_id = workflow['workflow_id']
            claim.approver_employee_id = approver
            claim.status = 'Submitted'
            claim.submitted_at = now
            claim.updated_at = now
            self.claims[claim.expense_claim_id] = claim
            response = self._claim_payload(claim)
            self._audit('expense_claim_submitted', 'ExpenseClaim', claim.expense_claim_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant, trace_id=trace)
            self._emit('ExpenseClaimSubmitted', response, tenant_id=tenant, correlation_id=trace, aggregate_type='ExpenseClaim', aggregate_id=claim.expense_claim_id)
        self.observability.track('expense.submit_claim', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant, 'status': 200})
        return 200, response

    def decide_claim(self, expense_claim_id: str, *, action: str, actor_id: str, actor_role: str | None, actor_type: str = 'user', tenant_id: str | None = None, comment: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id)
        with self._lock:
            claim = self._require_claim(expense_claim_id, tenant_id=tenant, trace_id=trace)
            before = self._claim_payload(claim)
            if claim.status == 'Approved' and action == 'approve':
                return 200, before
            if claim.status == 'Rejected' and action == 'reject':
                return 200, before
            if claim.status != 'Submitted':
                raise self._error(409, 'INVALID_TRANSITION', 'only Submitted claims can be decided', trace)
            if not claim.workflow_id:
                raise self._error(409, 'WORKFLOW_MISSING', 'expense claim is missing centralized workflow', trace)
            workflow = self._resolve_workflow(claim.workflow_id, tenant, action=action, actor_id=actor_id, actor_type=actor_type, actor_role=actor_role, comment=comment, trace_id=trace)
            terminal_result = self._require_terminal_workflow_result(workflow, action=action, trace_id=trace)
            now = self._now()
            if action == 'approve' and terminal_result == 'approved':
                claim.status = 'Approved'
                claim.approved_at = now
                claim.rejected_at = None
                event_name = 'ExpenseClaimApproved'
                audit_action = 'expense_claim_approved'
            elif action == 'reject' and terminal_result == 'rejected':
                claim.status = 'Rejected'
                claim.rejected_at = now
                claim.approved_at = None
                event_name = 'ExpenseClaimRejected'
                audit_action = 'expense_claim_rejected'
            else:
                raise self._error(409, 'WORKFLOW_BYPASS_DETECTED', 'workflow decision did not produce a valid expense claim terminal result', trace)
            claim.updated_at = now
            claim.approver_employee_id = actor_id
            self.claims[claim.expense_claim_id] = claim
            response = self._claim_payload(claim)
            self._audit(audit_action, 'ExpenseClaim', claim.expense_claim_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant, trace_id=trace)
            self._emit(event_name, response, tenant_id=tenant, correlation_id=trace, aggregate_type='ExpenseClaim', aggregate_id=claim.expense_claim_id)
        self.observability.track('expense.decide_claim', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant, 'status': 200, 'action': action})
        return 200, response

    def reimburse_claim(self, expense_claim_id: str, payload: dict[str, Any], *, actor_id: str, actor_role: str | None, actor_type: str = 'user', tenant_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id or payload.get('tenant_id'))
        if actor_role not in {'Finance', 'Admin'}:
            raise self._error(403, 'FORBIDDEN', 'only Finance/Admin actors can reimburse approved claims', trace)
        with self._lock:
            claim = self._require_claim(expense_claim_id, tenant_id=tenant, trace_id=trace)
            before = self._claim_payload(claim)
            if claim.status == 'Reimbursed':
                return 200, before
            if claim.status != 'Approved':
                raise self._error(409, 'INVALID_TRANSITION', 'only Approved claims can be reimbursed', trace)
            now = self._now()
            claim.status = 'Reimbursed'
            claim.reimbursed_at = now
            claim.reimbursed_by = actor_id
            claim.reimbursement_reference = str(payload.get('reimbursement_reference') or '').strip() or None
            claim.updated_at = now
            self.claims[claim.expense_claim_id] = claim
            response = self._claim_payload(claim)
            self._audit('expense_claim_reimbursed', 'ExpenseClaim', claim.expense_claim_id, before, response, actor_id=actor_id, actor_type=actor_type, tenant_id=tenant, trace_id=trace)
            self._emit('ExpenseClaimReimbursed', response, tenant_id=tenant, correlation_id=trace, aggregate_type='ExpenseClaim', aggregate_id=claim.expense_claim_id)
        self.observability.track('expense.reimburse_claim', trace_id=trace, started_at=started, success=True, context={'tenant_id': tenant, 'status': 200})
        return 200, response

    def get_claim(self, expense_claim_id: str, *, tenant_id: str | None = None, actor_id: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        tenant = normalize_tenant_id(tenant_id)
        claim = self._require_claim(expense_claim_id, tenant_id=tenant, trace_id=trace)
        return 200, self._claim_payload(claim, actor_id=actor_id)

    def list_claims(
        self,
        *,
        tenant_id: str | None = None,
        employee_id: str | None = None,
        approver_employee_id: str | None = None,
        status: str | None = None,
        category_code: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [
            self._claim_payload(claim)
            for claim in self.claims.values()
            if claim.tenant_id == tenant
            and (employee_id is None or claim.employee_id == employee_id)
            and (approver_employee_id is None or claim.approver_employee_id == approver_employee_id)
            and (status is None or claim.status == status)
            and (category_code is None or claim.category_code == category_code.upper())
        ]
        rows.sort(key=lambda item: (item['created_at'], item['expense_claim_id']))
        return 200, {'items': rows, 'data': rows, '_pagination': {'count': len(rows)}}

    def _seed_defaults(self) -> None:
        if not any(category.tenant_id == DEFAULT_TENANT_ID for category in self.categories.values()):
            now = self._now()
            defaults = [
                ExpenseCategory(DEFAULT_TENANT_ID, str(uuid4()), 'TRAVEL', 'Travel', True, True, 5000.0, 'Flights, taxis, hotels, and transit.', now, now),
                ExpenseCategory(DEFAULT_TENANT_ID, str(uuid4()), 'MEALS', 'Meals', True, True, 250.0, 'Client or business meals.', now, now),
                ExpenseCategory(DEFAULT_TENANT_ID, str(uuid4()), 'OFFICE', 'Office Supplies', False, True, 1000.0, 'Office-related purchases.', now, now),
            ]
            for category in defaults:
                self.categories[category.category_id] = category
        if not self.employee_snapshots.values():
            self.register_employee_profile({'employee_id': 'emp-001', 'employee_number': 'E-001', 'full_name': 'Nina Employee', 'department_id': 'dep-eng', 'department_name': 'Engineering', 'manager_employee_id': 'emp-manager'})
            self.register_employee_profile({'employee_id': 'emp-manager', 'employee_number': 'E-002', 'full_name': 'Manny Manager', 'department_id': 'dep-eng', 'department_name': 'Engineering', 'manager_employee_id': 'finance-admin'})
            self.register_employee_profile({'employee_id': 'finance-admin', 'employee_number': 'E-003', 'full_name': 'Faye Finance', 'department_id': 'dep-fin', 'department_name': 'Finance', 'manager_employee_id': None})
            self.register_employee_profile({'employee_id': 'emp-admin', 'employee_number': 'E-004', 'full_name': 'Ari Admin', 'department_id': 'dep-ops', 'department_name': 'Operations', 'manager_employee_id': None})

    def _register_workflows_for_tenant(self, tenant_id: str) -> None:
        tenant = normalize_tenant_id(tenant_id)
        if tenant in self._registered_workflow_tenants:
            return
        self.workflow_service.register_definition(
            tenant_id=tenant,
            code='expense_claim_approval',
            source_service='expense-service',
            subject_type='ExpenseClaim',
            description='Manager approval for employee expense claims before reimbursement.',
            steps=[
                {
                    'name': 'manager-approval',
                    'type': 'approval',
                    'assignee_template': '{approver_assignee}',
                    'sla': 'PT48H',
                    'escalation_assignee_template': '{escalation_assignee}',
                }
            ],
        )
        self._registered_workflow_tenants.add(tenant)

    def _claim_payload(self, claim: ExpenseClaim, *, actor_id: str | None = None) -> dict[str, Any]:
        employee = self._require_employee(claim.employee_id, tenant_id=claim.tenant_id, field='employee_id', trace_id=self.observability.trace_id())
        category = self._require_category(claim.category_code, tenant_id=claim.tenant_id, trace_id=self.observability.trace_id())
        return {
            **claim.to_dict(),
            'employee': employee.to_dict(),
            'category': category.to_dict(),
            'workflow': self.workflow_service.get_instance(claim.workflow_id, tenant_id=claim.tenant_id, actor_id=actor_id) if claim.workflow_id else None,
        }

    def _require_employee(self, employee_id: str | None, *, tenant_id: str, field: str, trace_id: str) -> EmployeeSnapshot:
        if not employee_id:
            raise self._error(422, 'VALIDATION_ERROR', f'{field} is required', trace_id, [{'field': field, 'reason': 'must be provided'}])
        employee = self.employee_snapshots.get(str(employee_id))
        if employee is None or employee.tenant_id != tenant_id:
            raise self._error(404, 'NOT_FOUND', f'{field} was not found in employee-service read model', trace_id)
        if employee.status == 'Terminated':
            raise self._error(409, 'INVALID_REFERENCE', f'{field} references a terminated employee', trace_id, [{'field': field, 'reason': 'employee is terminated'}])
        return employee

    def _require_category(self, category_code: str | None, *, tenant_id: str, trace_id: str) -> ExpenseCategory:
        if not category_code:
            raise self._error(422, 'VALIDATION_ERROR', 'category_code is required', trace_id, [{'field': 'category_code', 'reason': 'must be provided'}])
        category = self._find_category_by_code(tenant_id, str(category_code).upper())
        if category is None:
            raise self._error(404, 'NOT_FOUND', 'expense category was not found', trace_id, [{'field': 'category_code', 'reason': 'unknown category'}])
        return category

    def _find_category_by_code(self, tenant_id: str, code: str) -> ExpenseCategory | None:
        for category in self.categories.values():
            if category.tenant_id == tenant_id and category.code == code:
                return category
        return None

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

    def _require_terminal_workflow_result(self, workflow: dict[str, Any], *, action: str, trace_id: str) -> str:
        return require_terminal_workflow_result(
            workflow,
            action=action,
            on_mismatch=lambda _actual, expected: self._error(409, 'WORKFLOW_BYPASS_DETECTED', f'workflow did not reach expected terminal result: {expected}', trace_id),
            invalid_action=lambda _action: self._error(422, 'VALIDATION_ERROR', 'action must be approve or reject', trace_id, [{'field': 'action', 'reason': 'must be approve or reject'}]),
        )

    def _require_claim(self, expense_claim_id: str, *, tenant_id: str, trace_id: str) -> ExpenseClaim:
        claim = self.claims.get(expense_claim_id)
        if claim is None:
            raise self._error(404, 'NOT_FOUND', 'expense claim was not found', trace_id)
        try:
            assert_tenant_access(claim.tenant_id, tenant_id)
        except PermissionError as exc:
            raise self._error(403, 'TENANT_SCOPE_VIOLATION', 'expense claim is outside the requested tenant scope', trace_id) from exc
        return claim

    def _audit(self, action: str, entity: str, entity_id: str, before: dict[str, Any], after: dict[str, Any], *, actor_id: str, actor_type: str, tenant_id: str, trace_id: str) -> None:
        emit_audit_record(
            service_name='expense-service',
            tenant_id=tenant_id,
            actor={'id': actor_id, 'type': actor_type},
            action=action,
            entity=entity,
            entity_id=entity_id,
            before=before,
            after=after,
            trace_id=trace_id,
            source={'bounded_context': 'expense-management'},
        )

    def _emit(self, legacy_event_name: str, data: dict[str, Any], *, tenant_id: str, correlation_id: str | None, aggregate_type: str, aggregate_id: str) -> None:
        event = emit_canonical_event(
            self.events,
            legacy_event_name=legacy_event_name,
            data={'tenant_id': tenant_id, **data},
            source='expense-service',
            tenant_id=tenant_id,
            registry=self.event_registry,
            correlation_id=correlation_id,
            idempotency_key=f'{aggregate_id}:{legacy_event_name}:{data.get("status", "mutation")}',
        )
        self.event_outbox.stage_canonical_event(event, aggregate_type=aggregate_type, aggregate_id=aggregate_id)

    @staticmethod
    def _normalize_attachment(payload: dict[str, Any], *, actor_id: str) -> ExpenseAttachment:
        file_name = str(payload.get('file_name') or '').strip()
        content_type = str(payload.get('content_type') or '').strip() or 'application/octet-stream'
        storage_key = str(payload.get('storage_key') or '').strip()
        if not file_name or not storage_key:
            raise ValueError('attachment requires file_name and storage_key')
        return ExpenseAttachment(
            attachment_id=str(uuid4()),
            file_name=file_name,
            content_type=content_type,
            storage_key=storage_key,
            uploaded_by=actor_id,
            uploaded_at=datetime.now(timezone.utc),
        )

    def _normalize_attachments(self, rows: list[dict[str, Any]], *, actor_id: str) -> list[ExpenseAttachment]:
        attachments: list[ExpenseAttachment] = []
        for row in rows:
            attachments.append(self._normalize_attachment(row, actor_id=actor_id))
        return attachments

    @staticmethod
    def _coerce_amount(raw: Any, trace_id: str) -> float:
        try:
            amount = round(float(raw), 2)
        except (TypeError, ValueError) as exc:
            raise ExpenseServiceError(422, 'VALIDATION_ERROR', 'amount must be a valid number', trace_id, [{'field': 'amount', 'reason': 'must be numeric'}]) from exc
        if amount <= 0:
            raise ExpenseServiceError(422, 'VALIDATION_ERROR', 'amount must be greater than zero', trace_id, [{'field': 'amount', 'reason': 'must be > 0'}])
        return amount

    @staticmethod
    def _coerce_date(raw: Any, field: str, trace_id: str) -> date:
        try:
            return raw if isinstance(raw, date) else date.fromisoformat(str(raw))
        except (TypeError, ValueError) as exc:
            raise ExpenseServiceError(422, 'VALIDATION_ERROR', f'{field} must be a valid ISO date', trace_id, [{'field': field, 'reason': 'must use YYYY-MM-DD'}]) from exc

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _trace(self, trace_id: str | None = None) -> str:
        return self.observability.trace_id(trace_id)

    @staticmethod
    def _error(status_code: int, code: str, message: str, trace_id: str, details: list[dict[str, Any]] | None = None) -> ExpenseServiceError:
        return ExpenseServiceError(status_code, code, message, trace_id, details)
