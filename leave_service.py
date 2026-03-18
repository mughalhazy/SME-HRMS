from __future__ import annotations

import base64
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from enum import Enum

from resilience import CentralErrorLogger, DeadLetterQueue, IdempotencyStore


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


@dataclass
class EmployeeRecord:
    employee_id: str
    department_id: str
    manager_employee_id: str | None
    status: EmployeeStatus


@dataclass
class LeaveRequest:
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
                "traceId": trace_id,
            }
        }
        super().__init__(message)


class LeaveService:
    def __init__(self):
        self.requests: dict[str, LeaveRequest] = {}
        self.events: list[dict] = []
        self.error_logger = CentralErrorLogger("leave-service")
        self.dead_letters = DeadLetterQueue()
        self.idempotency = IdempotencyStore()
        self.employees: dict[str, EmployeeRecord] = {
            "emp-admin": EmployeeRecord("emp-admin", "dept-admin", None, EmployeeStatus.ACTIVE),
            "emp-manager": EmployeeRecord("emp-manager", "dept-eng", None, EmployeeStatus.ACTIVE),
            "emp-001": EmployeeRecord("emp-001", "dept-eng", "emp-manager", EmployeeStatus.ACTIVE),
            "emp-002": EmployeeRecord("emp-002", "dept-eng", "emp-manager", EmployeeStatus.ACTIVE),
        }

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _trace(self, trace_id: str | None) -> str:
        return trace_id or uuid.uuid4().hex

    def _fail(self, status_code: int, code: str, message: str, trace_id: str | None, details: list[dict] | None = None):
        trace = self._trace(trace_id)
        error = LeaveServiceError(status_code, code, message, trace, details)
        self.error_logger.log(code, error, trace_id=trace, details={"details": details or []})
        raise error

    def _total_days(self, start: date, end: date) -> float:
        return float((end - start).days + 1)

    def _can_access(self, role: Role, actor_employee_id: str, leave: LeaveRequest) -> bool:
        if role == Role.ADMIN:
            return True
        if role == Role.EMPLOYEE:
            return leave.employee_id == actor_employee_id
        manager = self.employees.get(actor_employee_id)
        employee = self.employees.get(leave.employee_id)
        return bool(manager and employee and manager.department_id == employee.department_id)

    def _ensure_employee_eligible(self, employee_id: str, trace_id: str | None):
        employee = self.employees.get(employee_id)
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

    def _overlap_exists(self, employee_id: str, start: date, end: date, exclude_id: str | None = None) -> bool:
        tracked = {LeaveStatus.SUBMITTED, LeaveStatus.APPROVED}
        for item in self.requests.values():
            if item.employee_id != employee_id or item.status not in tracked:
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
            self.events.append({"event": event, **payload})
        except Exception as exc:  # noqa: BLE001
            trace = self._trace(trace_id)
            self.error_logger.log(event, exc, trace_id=trace, details={"workflow": workflow})
            self.dead_letters.push(workflow, event, payload, str(exc), trace_id=trace)

    def replay_dead_letters(self) -> list[dict]:
        recovered = self.dead_letters.recover(
            lambda entry: entry.workflow == "leave_request",
            lambda entry: True,
        )
        for entry in recovered:
            payload = dict(entry.payload)
            payload.pop("simulate_failure", None)
            self.events.append({"event": entry.operation, **payload, "recovered_from_dead_letter": True})
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
    ) -> tuple[int, dict]:
        role = Role(actor_role)
        if end_date < start_date:
            self._fail(422, "VALIDATION_ERROR", "end_date must be >= start_date", trace_id)
        self._ensure_employee_eligible(employee_id, trace_id)
        self._ensure_lifecycle_scope(role, actor_employee_id, employee_id, trace_id)
        if self._overlap_exists(employee_id, start_date, end_date):
            self._fail(409, "LEAVE_OVERLAP", "Leave range overlaps with existing submitted/approved leave", trace_id)

        now = self._now()
        leave = LeaveRequest(
            leave_request_id=str(uuid.uuid4()),
            employee_id=employee_id,
            leave_type=LeaveType(leave_type),
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
        return 201, leave.to_dict()

    def submit_request(self, actor_role: str, actor_employee_id: str, leave_request_id: str, trace_id: str | None = None, idempotency_key: str | None = None, simulate_event_failure: bool = False) -> tuple[int, dict]:
        role = Role(actor_role)
        leave = self.requests.get(leave_request_id)
        if not leave:
            self._fail(404, "LEAVE_NOT_FOUND", "Leave request not found", trace_id)
        self._ensure_lifecycle_scope(role, actor_employee_id, leave.employee_id, trace_id)

        key = idempotency_key or f"leave-submit:{leave_request_id}:{actor_employee_id}"
        fingerprint = f"submit:{leave_request_id}:{actor_role}:{actor_employee_id}"
        replay = self.idempotency.replay_or_conflict(key, fingerprint)
        if replay is not None:
            return replay.status_code, replay.payload

        if leave.status == LeaveStatus.SUBMITTED:
            payload = leave.to_dict()
            self.idempotency.record(key, fingerprint, 200, payload)
            return 200, payload
        if leave.status != LeaveStatus.DRAFT:
            self._fail(409, "INVALID_TRANSITION", "Only Draft requests can be submitted", trace_id)
        if self._overlap_exists(leave.employee_id, leave.start_date, leave.end_date, exclude_id=leave.leave_request_id):
            self._fail(409, "LEAVE_OVERLAP", "Leave range overlaps with existing submitted/approved leave", trace_id)

        ts = self._now()
        leave.status = LeaveStatus.SUBMITTED
        leave.submitted_at = ts
        leave.updated_at = ts
        payload = leave.to_dict()
        self._emit_event("LeaveRequestSubmitted", {"leave_request_id": leave.leave_request_id, "at": ts.isoformat(), "simulate_failure": simulate_event_failure}, workflow="leave_request", trace_id=trace_id, simulate_failure=simulate_event_failure)
        self.idempotency.record(key, fingerprint, 200, payload)
        return 200, payload

    def decide_request(self, action: str, actor_role: str, actor_employee_id: str, leave_request_id: str, reason: str | None = None, trace_id: str | None = None, idempotency_key: str | None = None, simulate_event_failure: bool = False) -> tuple[int, dict]:
        role = Role(actor_role)
        leave = self.requests.get(leave_request_id)
        if not leave:
            self._fail(404, "LEAVE_NOT_FOUND", "Leave request not found", trace_id)
        self._ensure_decision_scope(role, actor_employee_id, leave, trace_id)

        key = idempotency_key or f"leave-decision:{leave_request_id}:{action}:{actor_employee_id}"
        fingerprint = f"{action}:{leave_request_id}:{actor_role}:{actor_employee_id}:{reason or ''}"
        replay = self.idempotency.replay_or_conflict(key, fingerprint)
        if replay is not None:
            return replay.status_code, replay.payload

        if action == "approve" and leave.status == LeaveStatus.APPROVED:
            payload = leave.to_dict()
            self.idempotency.record(key, fingerprint, 200, payload)
            return 200, payload
        if action == "reject" and leave.status == LeaveStatus.REJECTED:
            payload = leave.to_dict()
            self.idempotency.record(key, fingerprint, 200, payload)
            return 200, payload
        if leave.status != LeaveStatus.SUBMITTED:
            self._fail(409, "INVALID_TRANSITION", "Only Submitted requests can be decided", trace_id)

        ts = self._now()
        if action == "approve":
            leave.status = LeaveStatus.APPROVED
            event = "LeaveRequestApproved"
        elif action == "reject":
            leave.status = LeaveStatus.REJECTED
            if reason:
                leave.reason = f"{leave.reason or ''}\n[Rejection] {reason}".strip()
            event = "LeaveRequestRejected"
        else:
            self._fail(400, "BAD_REQUEST", "Unknown action", trace_id)
        leave.approver_employee_id = actor_employee_id
        leave.decision_at = ts
        leave.updated_at = ts
        payload = leave.to_dict()
        self._emit_event(event, {"leave_request_id": leave.leave_request_id, "at": ts.isoformat(), "simulate_failure": simulate_event_failure}, workflow="leave_request", trace_id=trace_id, simulate_failure=simulate_event_failure)
        self.idempotency.record(key, fingerprint, 200, payload)
        return 200, payload

    def patch_request(self, actor_role: str, actor_employee_id: str, leave_request_id: str, patch: dict, trace_id: str | None = None) -> tuple[int, dict]:
        role = Role(actor_role)
        leave = self.requests.get(leave_request_id)
        if not leave:
            self._fail(404, "LEAVE_NOT_FOUND", "Leave request not found", trace_id)
        if not self._can_access(role, actor_employee_id, leave):
            self._fail(403, "FORBIDDEN", "Insufficient permissions for CAP-LEV-001", trace_id)
        if leave.status in {LeaveStatus.APPROVED, LeaveStatus.REJECTED, LeaveStatus.CANCELLED}:
            self._fail(409, "INVALID_TRANSITION", "Finalized leave cannot be modified", trace_id)
        if leave.status == LeaveStatus.SUBMITTED and set(patch) != {"status"}:
            self._fail(409, "INVALID_TRANSITION", "Submitted leave can only be cancelled", trace_id)

        if patch.get("status") == LeaveStatus.CANCELLED.value:
            leave.status = LeaveStatus.CANCELLED
            leave.updated_at = self._now()
            self._emit_event("LeaveRequestCancelled", {"leave_request_id": leave.leave_request_id, "at": leave.updated_at.isoformat()}, workflow="leave_request", trace_id=trace_id)
            return 200, leave.to_dict()

        start = date.fromisoformat(patch.get("start_date")) if patch.get("start_date") else leave.start_date
        end = date.fromisoformat(patch.get("end_date")) if patch.get("end_date") else leave.end_date
        if end < start:
            self._fail(422, "VALIDATION_ERROR", "end_date must be >= start_date", trace_id)
        if self._overlap_exists(leave.employee_id, start, end, exclude_id=leave.leave_request_id):
            self._fail(409, "LEAVE_OVERLAP", "Leave range overlaps with existing submitted/approved leave", trace_id)

        if "leave_type" in patch:
            leave.leave_type = LeaveType(patch["leave_type"])
        leave.start_date = start
        leave.end_date = end
        if "reason" in patch:
            leave.reason = patch["reason"]
        if "approver_employee_id" in patch:
            leave.approver_employee_id = patch["approver_employee_id"]
        leave.total_days = self._total_days(start, end)
        leave.updated_at = self._now()
        return 200, leave.to_dict()

    def get_request(self, actor_role: str, actor_employee_id: str, leave_request_id: str, trace_id: str | None = None) -> tuple[int, dict]:
        role = Role(actor_role)
        leave = self.requests.get(leave_request_id)
        if not leave:
            self._fail(404, "LEAVE_NOT_FOUND", "Leave request not found", trace_id)
        if not self._can_access(role, actor_employee_id, leave):
            self._fail(403, "FORBIDDEN", "Insufficient permissions for CAP-LEV-001", trace_id)
        return 200, leave.to_dict()

    def list_requests(self, actor_role: str, actor_employee_id: str, employee_id: str | None = None, status: str | None = None) -> tuple[int, dict]:
        role = Role(actor_role)
        rows = []
        for leave in self.requests.values():
            if employee_id and leave.employee_id != employee_id:
                continue
            if status and leave.status.value != status:
                continue
            if self._can_access(role, actor_employee_id, leave):
                rows.append(leave.to_dict())
        rows.sort(key=lambda item: (item["created_at"], item["leave_request_id"]))
        return 200, {"data": rows}


def encode_token(role: str, employee_id: str, department_id: str | None = None) -> str:
    payload = {"role": role, "employee_id": employee_id, "department_id": department_id}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
