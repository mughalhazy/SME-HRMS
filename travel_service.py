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


class TravelServiceError(Exception):
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
class ItinerarySegment:
    segment_id: str
    segment_type: str
    departure_city: str
    arrival_city: str
    departure_at: datetime
    arrival_at: datetime
    provider_name: str | None = None
    booking_reference: str | None = None
    lodging_name: str | None = None
    lodging_address: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['departure_at'] = self.departure_at.isoformat()
        payload['arrival_at'] = self.arrival_at.isoformat()
        return payload


@dataclass(slots=True)
class TravelRequest:
    tenant_id: str
    travel_request_id: str
    employee_id: str
    manager_employee_id: str
    purpose: str
    trip_type: str
    origin_city: str
    destination_city: str
    start_date: date
    end_date: date
    estimated_cost: float
    currency: str
    status: str
    workflow_id: str | None
    submitted_at: datetime | None
    decision_at: datetime | None
    approved_at: datetime | None
    booked_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    itinerary_segments: list[ItinerarySegment] = field(default_factory=list)
    notes: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            'tenant_id': self.tenant_id,
            'travel_request_id': self.travel_request_id,
            'employee_id': self.employee_id,
            'manager_employee_id': self.manager_employee_id,
            'purpose': self.purpose,
            'trip_type': self.trip_type,
            'origin_city': self.origin_city,
            'destination_city': self.destination_city,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'estimated_cost': self.estimated_cost,
            'currency': self.currency,
            'status': self.status,
            'workflow_id': self.workflow_id,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'decision_at': self.decision_at.isoformat() if self.decision_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'booked_at': self.booked_at.isoformat() if self.booked_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'itinerary_segments': [segment.to_dict() for segment in self.itinerary_segments],
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class TravelService:
    REQUEST_STATUSES = {'Draft', 'Submitted', 'Approved', 'Booked', 'Completed', 'Rejected', 'Cancelled'}
    TRIP_TYPES = {'OneWay', 'RoundTrip', 'MultiCity'}
    SEGMENT_TYPES = {'Flight', 'Rail', 'Hotel', 'Car', 'Other'}

    def __init__(self, db_path: str | None = None, *, workflow_service: WorkflowService | None = None, notification_service: NotificationService | None = None) -> None:
        self.employee_snapshots = PersistentKVStore[str, EmployeeSnapshot](service='travel-service', namespace='employee_snapshots', db_path=db_path)
        shared_db_path = self.employee_snapshots.db_path
        self.travel_requests = PersistentKVStore[str, TravelRequest](service='travel-service', namespace='travel_requests', db_path=shared_db_path)
        self.events: list[dict[str, Any]] = []
        self.tenant_id = DEFAULT_TENANT_ID
        self.event_registry = EventRegistry()
        self.notification_service = notification_service or NotificationService()
        self.workflow_service = workflow_service or WorkflowService(notification_service=self.notification_service)
        self.error_logger = CentralErrorLogger('travel-service')
        self.observability = Observability('travel-service')
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
            email=str(payload['email']) if payload.get('email') else None,
        )
        self.employee_snapshots[snapshot.employee_id] = snapshot
        return snapshot.to_dict()

    def create_request(self, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        started = perf_counter()
        trace = trace_id or self.observability.trace_id()
        tenant_id = normalize_tenant_id(payload.get('tenant_id'))
        employee = self._require_employee(payload['employee_id'], tenant_id=tenant_id, field='employee_id')
        manager = self._require_employee(payload.get('manager_employee_id') or employee.manager_employee_id, tenant_id=tenant_id, field='manager_employee_id')
        trip_type = str(payload.get('trip_type') or 'OneWay')
        if trip_type not in self.TRIP_TYPES:
            raise self._error(422, 'VALIDATION_ERROR', 'invalid trip_type', trace, [{'field': 'trip_type', 'reason': f'must be one of {sorted(self.TRIP_TYPES)}'}])
        start_date = self._coerce_date(payload['start_date'], 'start_date')
        end_date = self._coerce_date(payload['end_date'], 'end_date')
        if end_date < start_date:
            raise self._error(422, 'VALIDATION_ERROR', 'end_date must be on or after start_date', trace, [{'field': 'end_date', 'reason': 'must be >= start_date'}])
        estimated_cost = self._coerce_float(payload.get('estimated_cost', 0.0), 'estimated_cost', minimum=0.0)
        now = self._now()
        request = TravelRequest(
            tenant_id=tenant_id,
            travel_request_id=str(uuid4()),
            employee_id=employee.employee_id,
            manager_employee_id=manager.employee_id,
            purpose=str(payload['purpose']).strip(),
            trip_type=trip_type,
            origin_city=str(payload['origin_city']).strip(),
            destination_city=str(payload['destination_city']).strip(),
            start_date=start_date,
            end_date=end_date,
            estimated_cost=estimated_cost,
            currency=str(payload.get('currency') or 'USD').strip().upper(),
            status='Draft',
            workflow_id=None,
            submitted_at=None,
            decision_at=None,
            approved_at=None,
            booked_at=None,
            completed_at=None,
            cancelled_at=None,
            itinerary_segments=self._normalize_segments(payload.get('itinerary_segments') or [], start_date=start_date, end_date=end_date, trace_id=trace),
            notes=str(payload.get('notes')).strip() if payload.get('notes') is not None else None,
            created_at=now,
            updated_at=now,
        )
        self.travel_requests[request.travel_request_id] = request
        self._audit('travel_request_created', 'TravelRequest', request.travel_request_id, {}, request.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=tenant_id, trace_id=trace)
        self._emit('TravelRequestCreated', {'travel_request_id': request.travel_request_id, 'employee_id': request.employee_id, 'status': request.status}, tenant_id=tenant_id, correlation_id=trace)
        self.observability.track('create_travel_request', trace_id=trace, started_at=started, success=True, context={'status': 201})
        return 201, self._request_payload(request)

    def submit_request(self, travel_request_id: str, *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        request = self._require_request(travel_request_id)
        trace = trace_id or self.observability.trace_id()
        if request.status != 'Draft':
            raise self._error(409, 'CONFLICT', 'only Draft travel requests can be submitted', trace)
        workflow = self.workflow_service.start_workflow(
            tenant_id=request.tenant_id,
            definition_code='travel_request_approval',
            source_service='travel-service',
            subject_type='TravelRequest',
            subject_id=request.travel_request_id,
            actor_id=actor_id,
            actor_type=actor_type,
            context={
                'manager_assignee': request.manager_employee_id,
                'travel_ops_assignee': 'travel-desk',
                'escalation_assignee': 'travel-admin',
            },
            trace_id=trace,
        )
        before = request.to_dict()
        request.status = 'Submitted'
        request.workflow_id = workflow['workflow_id']
        request.submitted_at = self._now()
        request.updated_at = self._now()
        self.travel_requests[request.travel_request_id] = request
        self._audit('travel_request_submitted', 'TravelRequest', request.travel_request_id, before, request.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=request.tenant_id, trace_id=trace)
        self._emit('TravelRequestSubmitted', {'travel_request_id': request.travel_request_id, 'employee_id': request.employee_id, 'status': request.status, 'manager_employee_id': request.manager_employee_id}, tenant_id=request.tenant_id, correlation_id=trace)
        return 200, self._request_payload(request)

    def decide_request(self, travel_request_id: str, *, action: str, actor_id: str, actor_type: str = 'user', actor_role: str | None = None, comment: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        request = self._require_request(travel_request_id)
        trace = trace_id or self.observability.trace_id()
        if request.status != 'Submitted' or not request.workflow_id:
            raise self._error(409, 'CONFLICT', 'travel request is not awaiting approval', trace)
        before = request.to_dict()
        workflow = self._resolve_workflow(request.workflow_id, request.tenant_id, action=action, actor_id=actor_id, actor_type=actor_type, actor_role=actor_role, comment=comment, trace_id=trace)
        terminal_result = self._require_terminal_workflow_result(workflow, action=action, trace_id=trace)
        if terminal_result == 'approved':
            request.status = 'Approved'
            request.decision_at = self._now()
            request.approved_at = request.decision_at
            audit_action = 'travel_request_approved'
            event_name = 'TravelRequestApproved'
        elif terminal_result == 'rejected':
            request.status = 'Rejected'
            request.decision_at = self._now()
            audit_action = 'travel_request_rejected'
            event_name = 'TravelRequestRejected'
        else:
            request.status = 'Submitted'
            audit_action = 'travel_request_step_approved'
            event_name = None
        request.updated_at = self._now()
        self.travel_requests[request.travel_request_id] = request
        self._audit(audit_action, 'TravelRequest', request.travel_request_id, before, request.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=request.tenant_id, trace_id=trace)
        if event_name:
            self._emit(event_name, {'travel_request_id': request.travel_request_id, 'employee_id': request.employee_id, 'status': request.status, 'workflow_id': request.workflow_id}, tenant_id=request.tenant_id, correlation_id=trace)
        payload = self._request_payload(request)
        payload['workflow'] = workflow
        return 200, payload

    def update_itinerary(self, travel_request_id: str, payload: dict[str, Any], *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        request = self._require_request(travel_request_id)
        trace = trace_id or self.observability.trace_id()
        if request.status not in {'Approved', 'Booked'}:
            raise self._error(409, 'CONFLICT', 'itinerary details can only be updated after approval', trace)
        segments = self._normalize_segments(payload.get('itinerary_segments') or [], start_date=request.start_date, end_date=request.end_date, trace_id=trace)
        if not segments:
            raise self._error(422, 'VALIDATION_ERROR', 'itinerary_segments are required', trace, [{'field': 'itinerary_segments', 'reason': 'must contain at least one segment'}])
        before = request.to_dict()
        request.itinerary_segments = segments
        request.status = 'Booked'
        request.booked_at = self._now()
        request.updated_at = self._now()
        self.travel_requests[request.travel_request_id] = request
        self._audit('travel_itinerary_updated', 'TravelRequest', request.travel_request_id, before, request.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=request.tenant_id, trace_id=trace)
        self._emit('TravelItineraryUpdated', {'travel_request_id': request.travel_request_id, 'employee_id': request.employee_id, 'status': request.status, 'segment_count': len(request.itinerary_segments)}, tenant_id=request.tenant_id, correlation_id=trace)
        return 200, self._request_payload(request)

    def cancel_request(self, travel_request_id: str, *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        request = self._require_request(travel_request_id)
        trace = trace_id or self.observability.trace_id()
        if request.status in {'Completed', 'Cancelled', 'Rejected'}:
            raise self._error(409, 'CONFLICT', f'cannot cancel a {request.status} travel request', trace)
        before = request.to_dict()
        request.status = 'Cancelled'
        request.cancelled_at = self._now()
        request.updated_at = self._now()
        self.travel_requests[request.travel_request_id] = request
        self._audit('travel_request_cancelled', 'TravelRequest', request.travel_request_id, before, request.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=request.tenant_id, trace_id=trace)
        self._emit('TravelRequestCancelled', {'travel_request_id': request.travel_request_id, 'employee_id': request.employee_id, 'status': request.status}, tenant_id=request.tenant_id, correlation_id=trace)
        return 200, self._request_payload(request)

    def complete_request(self, travel_request_id: str, *, actor_id: str, actor_type: str = 'user', trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        request = self._require_request(travel_request_id)
        trace = trace_id or self.observability.trace_id()
        if request.status != 'Booked':
            raise self._error(409, 'CONFLICT', 'only Booked travel requests can be completed', trace)
        before = request.to_dict()
        request.status = 'Completed'
        request.completed_at = self._now()
        request.updated_at = self._now()
        self.travel_requests[request.travel_request_id] = request
        self._audit('travel_request_completed', 'TravelRequest', request.travel_request_id, before, request.to_dict(), actor_id=actor_id, actor_type=actor_type, tenant_id=request.tenant_id, trace_id=trace)
        self._emit('TravelRequestCompleted', {'travel_request_id': request.travel_request_id, 'employee_id': request.employee_id, 'status': request.status}, tenant_id=request.tenant_id, correlation_id=trace)
        return 200, self._request_payload(request)

    def get_request(self, travel_request_id: str, *, tenant_id: str | None = None) -> tuple[int, dict[str, Any]]:
        request = self._require_request(travel_request_id)
        if tenant_id is not None:
            assert_tenant_access(request.tenant_id, normalize_tenant_id(tenant_id))
        return 200, self._request_payload(request)

    def list_requests(self, *, tenant_id: str | None = None, employee_id: str | None = None, status: str | None = None, limit: int = 25, cursor: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [item for item in self.travel_requests.values() if item.tenant_id == tenant]
        if employee_id is not None:
            rows = [item for item in rows if item.employee_id == employee_id]
        if status is not None:
            rows = [item for item in rows if item.status == status]
        rows.sort(key=lambda item: (item.updated_at.isoformat(), item.travel_request_id), reverse=True)
        page_items, pagination = self._paginate([self._request_payload(item) for item in rows], limit=limit, cursor=cursor)
        return 200, {'items': page_items, 'data': page_items, '_pagination': pagination}

    def _register_workflows(self) -> None:
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code='travel_request_approval',
            source_service='travel-service',
            subject_type='TravelRequest',
            description='Manager then travel desk approval for employee travel requests.',
            steps=[
                {'name': 'manager-approval', 'type': 'approval', 'assignee_template': '{manager_assignee}', 'sla': 'PT24H', 'escalation_assignee_template': '{escalation_assignee}'},
                {'name': 'travel-desk-approval', 'type': 'approval', 'assignee_template': '{travel_ops_assignee}', 'sla': 'PT24H', 'escalation_assignee_template': '{escalation_assignee}'},
            ],
        )

    def _request_payload(self, request: TravelRequest) -> dict[str, Any]:
        employee = self._require_employee(request.employee_id, tenant_id=request.tenant_id, field='employee_id')
        manager = self._require_employee(request.manager_employee_id, tenant_id=request.tenant_id, field='manager_employee_id')
        return {
            **request.to_dict(),
            'employee': employee.to_dict(),
            'manager': manager.to_dict(),
            'trip_duration_days': (request.end_date - request.start_date).days + 1,
            'segment_count': len(request.itinerary_segments),
            'workflow': self.workflow_service.get_instance(request.workflow_id, tenant_id=request.tenant_id) if request.workflow_id else None,
        }

    def _normalize_segments(self, raw_segments: list[dict[str, Any]], *, start_date: date, end_date: date, trace_id: str) -> list[ItinerarySegment]:
        normalized: list[ItinerarySegment] = []
        for index, item in enumerate(raw_segments):
            segment_type = str(item.get('segment_type') or 'Other')
            if segment_type not in self.SEGMENT_TYPES:
                raise self._error(422, 'VALIDATION_ERROR', 'invalid segment_type', trace_id, [{'field': f'itinerary_segments[{index}].segment_type', 'reason': f'must be one of {sorted(self.SEGMENT_TYPES)}'}])
            departure_at = self._coerce_datetime(item['departure_at'], f'itinerary_segments[{index}].departure_at')
            arrival_at = self._coerce_datetime(item['arrival_at'], f'itinerary_segments[{index}].arrival_at')
            if arrival_at <= departure_at:
                raise self._error(422, 'VALIDATION_ERROR', 'arrival_at must be after departure_at', trace_id, [{'field': f'itinerary_segments[{index}].arrival_at', 'reason': 'must be > departure_at'}])
            if departure_at.date() < start_date or arrival_at.date() > end_date:
                raise self._error(422, 'VALIDATION_ERROR', 'itinerary segment must fit within the request travel window', trace_id, [{'field': f'itinerary_segments[{index}]', 'reason': 'must be within start_date/end_date'}])
            normalized.append(
                ItinerarySegment(
                    segment_id=str(item.get('segment_id') or uuid4()),
                    segment_type=segment_type,
                    departure_city=str(item['departure_city']).strip(),
                    arrival_city=str(item['arrival_city']).strip(),
                    departure_at=departure_at,
                    arrival_at=arrival_at,
                    provider_name=str(item['provider_name']).strip() if item.get('provider_name') else None,
                    booking_reference=str(item['booking_reference']).strip() if item.get('booking_reference') else None,
                    lodging_name=str(item['lodging_name']).strip() if item.get('lodging_name') else None,
                    lodging_address=str(item['lodging_address']).strip() if item.get('lodging_address') else None,
                    notes=str(item['notes']).strip() if item.get('notes') else None,
                )
            )
        return normalized

    def _audit(self, action: str, entity: str, entity_id: str, before: dict[str, Any], after: dict[str, Any], *, actor_id: str, actor_type: str, tenant_id: str, trace_id: str) -> None:
        emit_audit_record(
            service_name='travel-service',
            tenant_id=tenant_id,
            actor={'id': actor_id, 'type': actor_type},
            action=action,
            entity=entity,
            entity_id=entity_id,
            before=before,
            after=after,
            trace_id=trace_id,
            source={'bounded_context': 'travel-management'},
        )

    def _emit(self, legacy_event_name: str, data: dict[str, Any], *, tenant_id: str, correlation_id: str | None) -> None:
        identity = data.get('travel_request_id') or str(uuid4())
        enriched_data = {'tenant_id': tenant_id, **data}
        employee_id = data.get('employee_id')
        manager_employee_id = data.get('manager_employee_id')
        if employee_id:
            employee = self.employee_snapshots.get(str(employee_id))
            if employee is not None:
                enriched_data.setdefault('employee_email', employee.email)
        if manager_employee_id:
            manager = self.employee_snapshots.get(str(manager_employee_id))
            if manager is not None:
                enriched_data.setdefault('manager_email', manager.email)
        event = emit_canonical_event(
            self.events,
            legacy_event_name=legacy_event_name,
            data=enriched_data,
            source='travel-service',
            tenant_id=tenant_id,
            registry=self.event_registry,
            correlation_id=correlation_id,
            idempotency_key=f"{identity}:{json.dumps(enriched_data, sort_keys=True, default=str)}",
        )
        notification_events = {'TravelRequestSubmitted', 'TravelRequestApproved', 'TravelRequestRejected', 'TravelItineraryUpdated', 'TravelRequestCancelled', 'TravelRequestCompleted'}
        if legacy_event_name not in notification_events:
            return
        try:
            self.notification_service.ingest_event(event)
        except Exception:
            self.observability.logger.info('travel.notification_skipped', trace_id=correlation_id, message=legacy_event_name, context={'travel_request_id': identity})

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
            on_mismatch=lambda _actual, expected: self._error(409, 'WORKFLOW_BYPASS_DETECTED', f'workflow decision did not produce a valid terminal result: {expected}', trace_id),
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

    def _require_request(self, travel_request_id: str) -> TravelRequest:
        request = self.travel_requests.get(travel_request_id)
        if request is None:
            raise self._error(404, 'NOT_FOUND', 'travel request not found', self.observability.trace_id())
        return request

    @staticmethod
    def _coerce_date(raw: Any, field: str) -> date:
        try:
            return date.fromisoformat(str(raw))
        except Exception as exc:
            raise ValueError(f'{field} must be an ISO date') from exc

    @staticmethod
    def _coerce_datetime(raw: Any, field: str) -> datetime:
        try:
            value = datetime.fromisoformat(str(raw).replace('Z', '+00:00'))
        except Exception as exc:
            raise ValueError(f'{field} must be an ISO datetime') from exc
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

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
    def _error(status_code: int, code: str, message: str, trace_id: str, details: list[dict[str, Any]] | None = None) -> TravelServiceError:
        return TravelServiceError(status_code, code, message, trace_id, details)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)
