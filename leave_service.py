from __future__ import annotations

import base64
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from enum import Enum
from threading import RLock
from time import perf_counter

from event_contract import EventRegistry, emit_canonical_event
from persistent_store import PersistentKVStore
from resilience import CentralErrorLogger, DeadLetterQueue, IdempotencyStore, Observability
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id


class Role(str, Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    EMPLOYEE = "Employee"


class EmployeeStatus(str, Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    ON_LEAVE = "OnLeave"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"


class LeaveType(str, Enum):
    ANNUAL = "Annual"
    SICK = "Sick"
    CASUAL = "Casual"
    UNPAID = "Unpaid"
    OTHER = "Other"


class LeaveStatus(str, Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"


BALANCE_CAPS: dict[LeaveType, float | None] = {
    LeaveType.ANNUAL: 18.0,
    LeaveType.SICK: 10.0,
    LeaveType.CASUAL: 7.0,
    LeaveType.UNPAID: None,
    LeaveType.OTHER: 5.0,
}


@dataclass
class EmployeeRecord:
    tenant_id: str
    employee_id: str
    department_id: str
    manager_employee_id: str | None
    status: EmployeeStatus


@dataclass
class LeaveBalance:
    tenant_id: str
    employee_id: str
    leave_type: LeaveType
    entitlement_days: float | None
    reserved_days: float
    approved_days: float

    @property
    def remaining_days(self) -> float | None:
        if self.entitlement_days is None:
            return None
        return float(self.entitlement_days - self.reserved_days - self.approved_days)

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "employee_id": self.employee_id,
            "leave_type": self.leave_type.value,
            "entitlement_days": self.entitlement_days,
            "reserved_days": self.reserved_days,
            "approved_days": self.approved_days,
            "remaining_days": self.remaining_days,
        }


@dataclass
class LeaveRequest:
    tenant_id: str
    leave_request_id: str
    employee_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    total_days: float
    reason: str | None
    approver_employee_id: str | None
    status: LeaveStatus
    submitted_at: datetime | None
    decision_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["tenant_id"] = self.tenant_id
        payload["leave_type"] = self.leave_type.value
        payload["status"] = self.status.value
        for f in ["start_date", "end_date"]:
            payload[f] = payload[f].isoformat()
        for f in ["submitted_at", "decision_at", "created_at", "updated_at"]:
            payload[f] = payload[f].isoformat() if payload[f] else None
        return payload


class LeaveServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str, trace_id: str, details: list[dict] | None = None):
        self.status_code = status_code
        self.payload = {
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "trace_id": trace_id,
            }
        }
        super().__init__(message)


class LeaveService:
    def __init__(self, db_path: str | None = None):
        self.requests = PersistentKVStore[str, LeaveRequest](service='leave-service', namespace='requests', db_path=db_path)
        self.events: list[dict] = []
        self.error_logger = CentralErrorLogger("leave-service")
        self.dead_letters = DeadLetterQueue()
        self.idempotency = IdempotencyStore()
        self.observability = Observability("leave-service")
        self.tenant_id = DEFAULT_TENANT_ID
        self.event_registry = EventRegistry()
        self.employees = PersistentKVStore[str, EmployeeRecord](service='leave-service', namespace='employees', db_path=db_path)
        seeded_employees = {
            "emp-admin": EmployeeRecord(self.tenant_id, "emp-admin", "dept-admin", None, EmployeeStatus.ACTIVE),
            "emp-manager": EmployeeRecord(self.tenant_id, "emp-manager", "dept-eng", None, EmployeeStatus.ACTIVE),
            "emp-001": EmployeeRecord(self.tenant_id, "emp-001", "dept-eng", "emp-manager", EmployeeStatus.ACTIVE),
            "emp-002": EmployeeRecord(self.tenant_id, "emp-002", "dept-eng", "emp-manager", EmployeeStatus.ACTIVE),
        }
        for employee_id, employee in seeded_employees.items():
            if employee_id not in self.employees:
                self.employees[employee_id] = employee
        self.leave_balances = PersistentKVStore[tuple[str, LeaveType], LeaveBalance](service='leave-service', namespace='leave_balances', db_path=db_path)
        self.attendance_impacts = PersistentKVStore[str, list[dict]](service='leave-service', namespace='attendance_impacts', db_path=db_path)
        self._lock = RLock()
        self._seed_leave_balances()

    def _seed_leave_balances(self) -> None:
        for employee_id in self.employees:
            for leave_type, entitlement_days in BALANCE_CAPS.items():
                self.leave_balances[(employee_id, leave_type)] = LeaveBalance(
                    tenant_id=self.tenant_id,
                    employee_id=employee_id,
                    leave_type=leave_type,
                    entitlement_days=entitlement_days,
                    reserved_days=0.0,
                    approved_days=0.0,
                )


    def _resolve_tenant(self, tenant_id: str | None = None) -> str:
        return normalize_tenant_id(tenant_id or self.tenant_id)

    def _assert_resource_tenant(self, tenant_id: str, trace_id: str | None = None) -> None:
        try:
            assert_tenant_access(tenant_id, self.tenant_id)
        except PermissionError:
            self._fail(403, "TENANT_SCOPE_VIOLATION", "Tenant scope does not permit this operation", trace_id)

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _today(self) -> date:
        return self._now().date()

    def _trace(self, trace_id: str | None) -> str:
        return self.observability.trace_id(trace_id)

    def _fail(self, status_code: int, code: str, message: str, trace_id: str | None, details: list[dict] | None = None):
        trace = self._trace(trace_id)
        error = LeaveServiceError(status_code, code, message, trace, details)
        self.error_logger.log(code, error, trace_id=trace, details={"details": details or []})
        raise error

    def _total_days(self, start: date, end: date) -> float:
        return float((end - start).days + 1)

    def _can_access(self, role: Role, actor_employee_id: str, leave: LeaveRequest) -> bool:
        if leave.tenant_id != self.tenant_id:
            return False
        if role == Role.ADMIN:
            return True
        if role == Role.EMPLOYEE:
            return leave.employee_id == actor_employee_id
        manager = self.employees.get(actor_employee_id)
        employee = self.employees.get(leave.employee_id)
        return bool(manager and employee and manager.department_id == employee.department_id)

    def _ensure_employee_eligible(self, employee_id: str, trace_id: str | None):
        employee = self.employees.get(employee_id)
        if employee and employee.tenant_id != self.tenant_id:
            employee = None
        if employee and employee.tenant_id != self.tenant_id:
            employee = None
        if not employee:
            self._fail(404, "EMPLOYEE_NOT_FOUND", "Employee not found", trace_id)
        if employee.status not in {EmployeeStatus.ACTIVE, EmployeeStatus.ON_LEAVE}:
            self._fail(409, "EMPLOYEE_INELIGIBLE", "Employee status does not allow leave requests", trace_id)

    def _ensure_lifecycle_scope(self, role: Role, actor_employee_id: str, target_employee_id: str, trace_id: str | None):
        if role == Role.ADMIN:
            return
        if role == Role.EMPLOYEE and actor_employee_id == target_employee_id:
            return
        if role == Role.MANAGER:
            manager = self.employees.get(actor_employee_id)
            target = self.employees.get(target_employee_id)
            if manager and target and manager.department_id == target.department_id:
                return
        self._fail(403, "FORBIDDEN", "Insufficient permissions for CAP-LEV-001", trace_id)

    def _ensure_decision_scope(self, role: Role, actor_employee_id: str, leave: LeaveRequest, trace_id: str | None):
        if role not in {Role.ADMIN, Role.MANAGER}:
            self._fail(403, "FORBIDDEN", "Insufficient permissions for CAP-LEV-002", trace_id)
        if role == Role.MANAGER and not self._can_access(role, actor_employee_id, leave):
            self._fail(403, "FORBIDDEN", "Insufficient team scope", trace_id)

    def _get_balance(self, employee_id: str, leave_type: LeaveType) -> LeaveBalance:
        return self.leave_balances[(employee_id, leave_type)]

    def _balance_snapshot(self, employee_id: str, leave_type: LeaveType) -> dict:
        return self._get_balance(employee_id, leave_type).to_dict()

    def _balances_for_employee(self, employee_id: str) -> list[dict]:
        return [
            self.leave_balances[(employee_id, leave_type)].to_dict()
            for leave_type in LeaveType
        ]

    def _ensure_balance_capacity(self, employee_id: str, leave_type: LeaveType, days: float, trace_id: str | None) -> None:
        balance = self._get_balance(employee_id, leave_type)
        remaining = balance.remaining_days
        if remaining is not None and remaining < days:
            self._fail(
                409,
                "INSUFFICIENT_LEAVE_BALANCE",
                "Requested leave exceeds the employee balance.",
                trace_id,
                details=[
                    {
                        "employee_id": employee_id,
                        "leave_type": leave_type.value,
                        "requested_days": days,
                        "remaining_days": remaining,
                    }
                ],
            )

    def _reserve_balance(self, leave: LeaveRequest, trace_id: str | None) -> None:
        self._ensure_balance_capacity(leave.employee_id, leave.leave_type, leave.total_days, trace_id)
        balance = self._get_balance(leave.employee_id, leave.leave_type)
        balance.reserved_days += leave.total_days

    def _release_reserved_balance(self, leave: LeaveRequest) -> None:
        balance = self._get_balance(leave.employee_id, leave.leave_type)
        balance.reserved_days = max(0.0, balance.reserved_days - leave.total_days)

    def _consume_reserved_balance(self, leave: LeaveRequest) -> None:
        balance = self._get_balance(leave.employee_id, leave.leave_type)
        balance.reserved_days = max(0.0, balance.reserved_days - leave.total_days)
        balance.approved_days += leave.total_days

    def _restore_approved_balance(self, leave: LeaveRequest) -> None:
        balance = self._get_balance(leave.employee_id, leave.leave_type)
        balance.approved_days = max(0.0, balance.approved_days - leave.total_days)

    def _sync_employee_leave_status(self, employee_id: str) -> None:
        employee = self.employees[employee_id]
        self._assert_resource_tenant(employee.tenant_id)
        today = self._today()
        has_active_approved_leave = any(
            leave.tenant_id == self.tenant_id
            and leave.employee_id == employee_id
            and leave.status == LeaveStatus.APPROVED
            and leave.start_date <= today <= leave.end_date
            for leave in self.requests.values()
        )
        if has_active_approved_leave:
            employee.status = EmployeeStatus.ON_LEAVE
        elif employee.status == EmployeeStatus.ON_LEAVE:
            employee.status = EmployeeStatus.ACTIVE

    def _overlap_exists(self, employee_id: str, start: date, end: date, exclude_id: str | None = None) -> bool:
        tracked = {LeaveStatus.SUBMITTED, LeaveStatus.APPROVED}
        for item in self.requests.values():
            if item.tenant_id != self.tenant_id or item.employee_id != employee_id or item.status not in tracked:
                continue
            if exclude_id and item.leave_request_id == exclude_id:
                continue
            if not (end < item.start_date or start > item.end_date):
                return True
        return False

    def _emit_event(self, event: str, payload: dict, *, workflow: str, trace_id: str | None = None, simulate_failure: bool = False) -> None:
        try:
            if simulate_failure:
                raise RuntimeError(f"simulated failure while emitting {event}")
            emit_canonical_event(self.events, legacy_event_name=event, data={**payload, "tenant_id": self.tenant_id}, source="leave-service", tenant_id=self.tenant_id, registry=self.event_registry, correlation_id=self._trace(trace_id), idempotency_key=payload.get("leave_request_id"))
            self.observability.logger.info(
                "leave.event_emitted",
                trace_id=self._trace(trace_id),
                message=event,
                context={"workflow": workflow, "payload_keys": sorted(payload.keys())},
            )
        except Exception as exc:  # noqa: BLE001
            trace = self._trace(trace_id)
            self.error_logger.log(event, exc, trace_id=trace, details={"workflow": workflow})
            self.dead_letters.push(workflow, event, payload, str(exc), trace_id=trace)

    def _finalize_observation(self, operation: str, trace_id: str, started: float, success: bool, context: dict | None = None) -> None:
        self.observability.track(operation, trace_id=trace_id, started_at=started, success=success, context=context)

    def _sync_attendance_impacts(self, leave: LeaveRequest) -> None:
        if leave.status != LeaveStatus.APPROVED:
            self.attendance_impacts.pop(leave.leave_request_id, None)
            return

        impacts = []
        cursor = leave.start_date
        while cursor <= leave.end_date:
            impacts.append(
                {
                    "attendance_date": cursor.isoformat(),
                    "attendance_status": "Absent",
                    "employee_id": leave.employee_id,
                    "leave_request_id": leave.leave_request_id,
                    "leave_type": leave.leave_type.value,
                    "source": "leave_approval",
                    "tenant_id": leave.tenant_id,
                }
            )
            cursor = date.fromordinal(cursor.toordinal() + 1)
        self.attendance_impacts[leave.leave_request_id] = impacts

    def get_employee_detail(self, employee_id: str) -> dict:
        employee = self.employees.get(employee_id)
        if employee and employee.tenant_id != self.tenant_id:
            employee = None
        if not employee:
            self._fail(404, "EMPLOYEE_NOT_FOUND", "Employee not found", None)
        leaves = [self._response_payload(leave) for leave in self.requests.values() if leave.tenant_id == self.tenant_id and leave.employee_id == employee_id]
        leaves.sort(key=lambda item: (item["start_date"], item["leave_request_id"]))
        active_leave = next((leave for leave in leaves if leave["status"] == LeaveStatus.APPROVED.value and leave["start_date"] <= self._today().isoformat() <= leave["end_date"]), None)
        return {
            "employee": {
                "employee_id": employee.employee_id,
                "department_id": employee.department_id,
                "manager_employee_id": employee.manager_employee_id,
                "status": employee.status.value,
            },
            "leave_balances": self._balances_for_employee(employee_id),
            "leave_requests": leaves,
            "attendance_impacts": [impact for leave_id, items in self.attendance_impacts.items() for impact in items if impact.get("tenant_id") == self.tenant_id and impact["employee_id"] == employee_id],
            "active_leave": active_leave,
        }

    def _response_payload(self, leave: LeaveRequest) -> dict:
        payload = leave.to_dict()
        payload["leave_balance"] = self._balance_snapshot(leave.employee_id, leave.leave_type)
        payload["attendance_impacts"] = list(self.attendance_impacts.get(leave.leave_request_id, []))
        payload["employee_status"] = self.employees[leave.employee_id].status.value
        payload["tenant_id"] = leave.tenant_id
        return payload


    def _actor_payload(self, actor_role: str, actor_employee_id: str, *, actor_type: str = 'user') -> dict[str, str | None]:
        return {
            'id': actor_employee_id or actor_role,
            'type': actor_type,
            'role': actor_role,
        }

    def _audit_leave_mutation(self, action: str, actor_role: str, actor_employee_id: str, leave_request_id: str, before: dict, after: dict, trace_id: str | None) -> None:
        self.observability.logger.audit(
            action,
            trace_id=trace_id,
            actor=self._actor_payload(actor_role, actor_employee_id),
            entity='LeaveRequest',
            entity_id=leave_request_id,
            context={'tenant_id': self.tenant_id, 'before': before, 'after': after},
        )

    def replay_dead_letters(self) -> list[dict]:
        recovered = self.dead_letters.recover(
            lambda entry: entry.workflow == "leave_request",
            lambda entry: True,
        )
        for entry in recovered:
            payload = dict(entry.payload)
            payload.pop("simulate_failure", None)
            emit_canonical_event(self.events, legacy_event_name=entry.operation, data={**payload, "tenant_id": self.tenant_id, "recovered_from_dead_letter": True}, source="leave-service", tenant_id=self.tenant_id, registry=self.event_registry, correlation_id=entry.trace_id, idempotency_key=payload.get("leave_request_id"))
        return [entry.__dict__ for entry in recovered]

    def create_request(
        self,
        actor_role: str,
        actor_employee_id: str,
        employee_id: str,
        leave_type: str,
        start_date: date,
        end_date: date,
        reason: str | None = None,
        approver_employee_id: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
    ) -> tuple[int, dict]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        trace = self._trace(trace_id)
        started = perf_counter()
        role = Role(actor_role)
        try:
            with self._lock:
                if end_date < start_date:
                    self._fail(422, "VALIDATION_ERROR", "end_date must be >= start_date", trace)
                self._ensure_employee_eligible(employee_id, trace)
                self._ensure_lifecycle_scope(role, actor_employee_id, employee_id, trace)
                if self._overlap_exists(employee_id, start_date, end_date):
                    self._fail(409, "LEAVE_OVERLAP", "Leave range overlaps with existing submitted/approved leave", trace)

                leave_type_enum = LeaveType(leave_type)
                self._ensure_balance_capacity(employee_id, leave_type_enum, self._total_days(start_date, end_date), trace)
                now = self._now()
                leave = LeaveRequest(
                    tenant_id=self.tenant_id,
                    leave_request_id=str(uuid.uuid4()),
                    employee_id=employee_id,
                    leave_type=leave_type_enum,
                    start_date=start_date,
                    end_date=end_date,
                    total_days=self._total_days(start_date, end_date),
                    reason=reason,
                    approver_employee_id=approver_employee_id,
                    status=LeaveStatus.DRAFT,
                    submitted_at=None,
                    decision_at=None,
                    created_at=now,
                    updated_at=now,
                )
                self.requests[leave.leave_request_id] = leave
            self._audit_leave_mutation('leave_request_created', actor_role, actor_employee_id, leave.leave_request_id, {}, self._response_payload(leave), trace)
            self.observability.logger.info(
                "leave.request_created",
                trace_id=trace,
                context={"leave_request_id": leave.leave_request_id, "employee_id": employee_id},
            )
            self._finalize_observation("create_request", trace, started, True, {"status": 201})
            return 201, self._response_payload(leave)
        except Exception:
            self._finalize_observation("create_request", trace, started, False)
            raise

    def submit_request(self, actor_role: str, actor_employee_id: str, leave_request_id: str, trace_id: str | None = None, idempotency_key: str | None = None, simulate_event_failure: bool = False, tenant_id: str | None = None) -> tuple[int, dict]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        trace = self._trace(trace_id)
        started = perf_counter()
        role = Role(actor_role)
        with self._lock:
            leave = self.requests.get(leave_request_id)
            before = self._response_payload(leave) if leave else {}
            if not leave:
                self._fail(404, "LEAVE_NOT_FOUND", "Leave request not found", trace)
            self._assert_resource_tenant(leave.tenant_id, trace)
            self._ensure_lifecycle_scope(role, actor_employee_id, leave.employee_id, trace)

            key = idempotency_key or f"leave-submit:{leave_request_id}:{actor_employee_id}"
            fingerprint = f"submit:{leave_request_id}:{actor_role}:{actor_employee_id}"
            replay = self.idempotency.replay_or_conflict(key, fingerprint)

            if leave.status == LeaveStatus.SUBMITTED:
                payload = self._response_payload(leave)
                self.idempotency.record(key, fingerprint, 200, payload)
                self._finalize_observation("submit_request", trace, started, True, {"status": 200, "replayed": True})
                return 200, payload
            if leave.status != LeaveStatus.DRAFT:
                self._fail(409, "INVALID_TRANSITION", "Only Draft requests can be submitted", trace)
            if replay is not None:
                self._finalize_observation("submit_request", trace, started, True, {"status": replay.status_code, "replayed": True})
                return replay.status_code, replay.payload
            if self._overlap_exists(leave.employee_id, leave.start_date, leave.end_date, exclude_id=leave.leave_request_id):
                self._fail(409, "LEAVE_OVERLAP", "Leave range overlaps with existing submitted/approved leave", trace)

            self._reserve_balance(leave, trace)
            ts = self._now()
            leave.status = LeaveStatus.SUBMITTED
            leave.submitted_at = ts
            leave.updated_at = ts
            payload = self._response_payload(leave)
            self._emit_event(
                "LeaveRequestSubmitted",
                {
                    "leave_request_id": leave.leave_request_id,
                    "employee_id": leave.employee_id,
                    "approver_employee_id": leave.approver_employee_id,
                    "start_date": leave.start_date.isoformat(),
                    "end_date": leave.end_date.isoformat(),
                    "status": leave.status.value,
                    "submitted_at": ts.isoformat(),
                    "simulate_failure": simulate_event_failure,
                },
                workflow="leave_request",
                trace_id=trace,
                simulate_failure=simulate_event_failure,
            )
            self.idempotency.record(key, fingerprint, 200, payload)
        self._audit_leave_mutation('leave_request_submitted', actor_role, actor_employee_id, leave.leave_request_id, before, payload, trace)
        self._finalize_observation("submit_request", trace, started, True, {"status": 200})
        return 200, payload

    def decide_request(self, action: str, actor_role: str, actor_employee_id: str, leave_request_id: str, reason: str | None = None, trace_id: str | None = None, idempotency_key: str | None = None, simulate_event_failure: bool = False, tenant_id: str | None = None) -> tuple[int, dict]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        trace = self._trace(trace_id)
        started = perf_counter()
        role = Role(actor_role)
        with self._lock:
            leave = self.requests.get(leave_request_id)
            before = self._response_payload(leave) if leave else {}
            if not leave:
                self._fail(404, "LEAVE_NOT_FOUND", "Leave request not found", trace)
            self._assert_resource_tenant(leave.tenant_id, trace)
            self._ensure_decision_scope(role, actor_employee_id, leave, trace)

            key = idempotency_key or f"leave-decision:{leave_request_id}:{action}:{actor_employee_id}"
            fingerprint = f"{action}:{leave_request_id}:{actor_role}:{actor_employee_id}:{reason or ''}"
            replay = self.idempotency.replay_or_conflict(key, fingerprint)

            if action == "approve" and leave.status == LeaveStatus.APPROVED:
                payload = self._response_payload(leave)
                self.idempotency.record(key, fingerprint, 200, payload)
                self._finalize_observation("decide_request", trace, started, True, {"status": 200, "replayed": True, "action": action})
                return 200, payload
            if action == "reject" and leave.status == LeaveStatus.REJECTED:
                payload = self._response_payload(leave)
                self.idempotency.record(key, fingerprint, 200, payload)
                self._finalize_observation("decide_request", trace, started, True, {"status": 200, "replayed": True, "action": action})
                return 200, payload
            if leave.status != LeaveStatus.SUBMITTED:
                self._fail(409, "INVALID_TRANSITION", "Only Submitted requests can be decided", trace)
            if replay is not None:
                self._finalize_observation("decide_request", trace, started, True, {"status": replay.status_code, "replayed": True, "action": action})
                return replay.status_code, replay.payload

            ts = self._now()
            if action == "approve":
                self._consume_reserved_balance(leave)
                leave.status = LeaveStatus.APPROVED
                event = "LeaveRequestApproved"
            elif action == "reject":
                self._release_reserved_balance(leave)
                leave.status = LeaveStatus.REJECTED
                if reason:
                    leave.reason = f"{leave.reason or ''}\n[Rejection] {reason}".strip()
                event = "LeaveRequestRejected"
            else:
                self._fail(400, "BAD_REQUEST", "Unknown action", trace)
            leave.approver_employee_id = actor_employee_id
            leave.decision_at = ts
            leave.updated_at = ts
            self._sync_employee_leave_status(leave.employee_id)
            self._sync_attendance_impacts(leave)
            payload = self._response_payload(leave)
            event_payload = {
                "leave_request_id": leave.leave_request_id,
                "employee_id": leave.employee_id,
                "approver_employee_id": leave.approver_employee_id,
                "status": leave.status.value,
                "decision_at": ts.isoformat(),
                "simulate_failure": simulate_event_failure,
            }
            if action == "approve":
                event_payload.update({"total_days": leave.total_days, "leave_type": leave.leave_type.value})
            self._emit_event(event, event_payload, workflow="leave_request", trace_id=trace, simulate_failure=simulate_event_failure)
            self.idempotency.record(key, fingerprint, 200, payload)
        self._audit_leave_mutation(f'leave_request_{action}', actor_role, actor_employee_id, leave.leave_request_id, before, payload, trace)
        self._finalize_observation("decide_request", trace, started, True, {"status": 200, "action": action})
        return 200, payload

    def patch_request(self, actor_role: str, actor_employee_id: str, leave_request_id: str, patch: dict, trace_id: str | None = None, tenant_id: str | None = None) -> tuple[int, dict]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        trace = self._trace(trace_id)
        started = perf_counter()
        role = Role(actor_role)
        with self._lock:
            leave = self.requests.get(leave_request_id)
            before = self._response_payload(leave) if leave else {}
            if not leave:
                self._fail(404, "LEAVE_NOT_FOUND", "Leave request not found", trace)
            self._assert_resource_tenant(leave.tenant_id, trace)
            if not self._can_access(role, actor_employee_id, leave):
                self._fail(403, "FORBIDDEN", "Insufficient permissions for CAP-LEV-001", trace)
            if leave.status in {LeaveStatus.REJECTED, LeaveStatus.CANCELLED}:
                self._fail(409, "INVALID_TRANSITION", "Finalized leave cannot be modified", trace)
            if leave.status == LeaveStatus.SUBMITTED and set(patch) != {"status"}:
                self._fail(409, "INVALID_TRANSITION", "Submitted leave can only be cancelled", trace)
            if leave.status == LeaveStatus.APPROVED and set(patch) != {"status"}:
                self._fail(409, "INVALID_TRANSITION", "Approved leave can only be cancelled", trace)

            if patch.get("status") == LeaveStatus.CANCELLED.value:
                if leave.status == LeaveStatus.APPROVED and leave.end_date < self._today():
                    self._fail(409, "INVALID_TRANSITION", "Past approved leave cannot be cancelled", trace)
                if leave.status == LeaveStatus.SUBMITTED:
                    self._release_reserved_balance(leave)
                elif leave.status == LeaveStatus.APPROVED:
                    self._restore_approved_balance(leave)
                leave.status = LeaveStatus.CANCELLED
                leave.updated_at = self._now()
                self._sync_employee_leave_status(leave.employee_id)
                self._sync_attendance_impacts(leave)
                self._emit_event(
                    "LeaveRequestCancelled",
                    {
                        "leave_request_id": leave.leave_request_id,
                        "employee_id": leave.employee_id,
                        "status": leave.status.value,
                        "updated_at": leave.updated_at.isoformat(),
                    },
                    workflow="leave_request",
                    trace_id=trace,
                )
                payload = self._response_payload(leave)
                self._audit_leave_mutation('leave_request_cancelled', actor_role, actor_employee_id, leave.leave_request_id, before, payload, trace)
                self._finalize_observation("patch_request", trace, started, True, {"status": 200, "cancelled": True})
                return 200, payload

            start = date.fromisoformat(patch.get("start_date")) if patch.get("start_date") else leave.start_date
            end = date.fromisoformat(patch.get("end_date")) if patch.get("end_date") else leave.end_date
            if end < start:
                self._fail(422, "VALIDATION_ERROR", "end_date must be >= start_date", trace)
            if self._overlap_exists(leave.employee_id, start, end, exclude_id=leave.leave_request_id):
                self._fail(409, "LEAVE_OVERLAP", "Leave range overlaps with existing submitted/approved leave", trace)

            next_type = LeaveType(patch["leave_type"]) if "leave_type" in patch else leave.leave_type
            next_total_days = self._total_days(start, end)
            self._ensure_balance_capacity(leave.employee_id, next_type, next_total_days, trace)

            if "leave_type" in patch:
                leave.leave_type = next_type
            leave.start_date = start
            leave.end_date = end
            if "reason" in patch:
                leave.reason = patch["reason"]
            if "approver_employee_id" in patch:
                leave.approver_employee_id = patch["approver_employee_id"]
            leave.total_days = next_total_days
            leave.updated_at = self._now()
        payload = self._response_payload(leave)
        self._audit_leave_mutation('leave_request_updated', actor_role, actor_employee_id, leave.leave_request_id, before, payload, trace)
        self.observability.logger.info(
            "leave.request_patched",
            trace_id=trace,
            context={"leave_request_id": leave.leave_request_id, "fields": sorted(patch.keys())},
        )
        self._finalize_observation("patch_request", trace, started, True, {"status": 200, "cancelled": False})
        return 200, payload

    def get_request(self, actor_role: str, actor_employee_id: str, leave_request_id: str, trace_id: str | None = None, tenant_id: str | None = None) -> tuple[int, dict]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        role = Role(actor_role)
        with self._lock:
            leave = self.requests.get(leave_request_id)
            if not leave:
                self._fail(404, "LEAVE_NOT_FOUND", "Leave request not found", trace_id)
            self._assert_resource_tenant(leave.tenant_id, trace_id)
            if not self._can_access(role, actor_employee_id, leave):
                self._fail(403, "FORBIDDEN", "Insufficient permissions for CAP-LEV-001", trace_id)
            return 200, self._response_payload(leave)

    def list_requests(self, actor_role: str, actor_employee_id: str, employee_id: str | None = None, approver_employee_id: str | None = None, status: str | None = None, tenant_id: str | None = None) -> tuple[int, dict]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        role = Role(actor_role)
        rows = []
        with self._lock:
            for leave in self.requests.values():
                if leave.tenant_id != self.tenant_id:
                    continue
                if employee_id and leave.employee_id != employee_id:
                    continue
                if approver_employee_id and leave.approver_employee_id != approver_employee_id:
                    continue
                if status and leave.status.value != status:
                    continue
                if self._can_access(role, actor_employee_id, leave):
                    rows.append(self._response_payload(leave))
            balances = self._balances_for_employee(employee_id or actor_employee_id) if (role == Role.EMPLOYEE or employee_id) else None
        rows.sort(key=lambda item: (item["created_at"], item["leave_request_id"]))
        payload = {"data": rows}
        if balances is not None:
            payload["leave_balances"] = balances
        return 200, payload

    def health_snapshot(self) -> dict:
        with self._lock:
            return self.observability.health_status(
                checks={
                    "requests": len(self.requests),
                    "dead_letters": len(self.dead_letters.entries),
                    "leave_balances": len(self.leave_balances),
                }
            )


def encode_token(role: str, employee_id: str, department_id: str | None = None) -> str:
    payload = {"role": role, "employee_id": employee_id, "department_id": department_id}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
