from __future__ import annotations

import base64
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from threading import RLock
from time import perf_counter
from typing import Any

from audit_service.service import emit_audit_record
from event_contract import EventRegistry
from notification_service import NotificationService
from outbox_system import OutboxManager
from persistent_store import PersistentKVStore
from resilience import CentralErrorLogger, DeadLetterQueue, IdempotencyStore, Observability
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id
from workflow_support import require_terminal_workflow_result, resolve_workflow_action
from workflow_service import WorkflowService, WorkflowServiceError


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


class AccrualFrequency(str, Enum):
    NONE = "None"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"


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
    location_code: str = "GLOBAL"
    grade_code: str = "G7"
    hire_date: date = field(default_factory=lambda: date(2026, 1, 1))


@dataclass
class LeavePolicy:
    tenant_id: str
    leave_policy_id: str
    code: str
    name: str
    leave_type: LeaveType
    location_codes: list[str]
    grade_codes: list[str]
    annual_entitlement_days: float | None
    accrual_frequency: AccrualFrequency
    accrual_rate_days: float
    carry_forward_limit_days: float | None
    requires_approval: bool
    allow_negative_balance: bool
    allow_partial_days: bool
    status: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["leave_type"] = self.leave_type.value
        payload["accrual_frequency"] = self.accrual_frequency.value
        payload["created_at"] = self.created_at.isoformat()
        payload["updated_at"] = self.updated_at.isoformat()
        return payload


@dataclass
class HolidayCalendar:
    tenant_id: str
    calendar_id: str
    location_code: str
    name: str
    holidays: dict[str, str]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["created_at"] = self.created_at.isoformat()
        payload["updated_at"] = self.updated_at.isoformat()
        payload["holidays"] = dict(sorted(self.holidays.items()))
        return payload


@dataclass
class LeaveBalance:
    tenant_id: str
    employee_id: str
    leave_type: LeaveType
    entitlement_days: float | None
    reserved_days: float
    approved_days: float
    accrued_days: float = 0.0
    carried_forward_days: float = 0.0
    policy_id: str | None = None
    last_accrual_at: str | None = None
    last_carry_forward_at: str | None = None

    @property
    def remaining_days(self) -> float | None:
        if self.entitlement_days is None:
            return None
        return float(self.entitlement_days + self.accrued_days + self.carried_forward_days - self.reserved_days - self.approved_days)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "employee_id": self.employee_id,
            "leave_type": self.leave_type.value,
            "policy_id": self.policy_id,
            "entitlement_days": self.entitlement_days,
            "accrued_days": self.accrued_days,
            "carried_forward_days": self.carried_forward_days,
            "reserved_days": self.reserved_days,
            "approved_days": self.approved_days,
            "remaining_days": self.remaining_days,
            "last_accrual_at": self.last_accrual_at,
            "last_carry_forward_at": self.last_carry_forward_at,
        }


@dataclass
class LeaveLedgerEntry:
    tenant_id: str
    ledger_entry_id: str
    employee_id: str
    leave_type: LeaveType
    entry_type: str
    delta_days: float
    balance_after: float | None
    effective_on: str
    created_at: datetime
    leave_request_id: str | None = None
    policy_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["leave_type"] = self.leave_type.value
        payload["created_at"] = self.created_at.isoformat()
        return payload


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
    workflow_id: str | None
    status: LeaveStatus
    submitted_at: datetime | None
    decision_at: datetime | None
    created_at: datetime
    updated_at: datetime
    partial_day_portion: float = 1.0
    policy_id: str | None = None
    holiday_dates: list[str] = field(default_factory=list)

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
                "trace_id": trace_id,
            }
        }
        super().__init__(message)


class LeavePolicyEngine:
    """Centralizes policy resolution, leave-day calculation, accrual, and carry-forward rules."""

    def resolve_policy(
        self,
        *,
        tenant_id: str,
        employee: EmployeeRecord,
        leave_type: LeaveType,
        policies: list[LeavePolicy],
        assignments: dict[tuple[str, LeaveType], str],
    ) -> LeavePolicy:
        assigned_policy_id = assignments.get((employee.employee_id, leave_type))
        active = [
            policy
            for policy in policies
            if policy.tenant_id == tenant_id and policy.leave_type == leave_type and policy.status == "Active"
        ]
        if assigned_policy_id:
            for policy in active:
                if policy.leave_policy_id == assigned_policy_id:
                    return policy
        for policy in active:
            if self._scope_matches(policy.location_codes, employee.location_code) and self._scope_matches(policy.grade_codes, employee.grade_code):
                return policy
        raise ValueError(f"No active leave policy configured for {employee.employee_id} / {leave_type.value}")

    @staticmethod
    def _scope_matches(scope_values: list[str], employee_value: str) -> bool:
        if not scope_values:
            return True
        normalized = {value.upper() for value in scope_values}
        return "*" in normalized or employee_value.upper() in normalized

    def calculate_leave_days(
        self,
        *,
        start: date,
        end: date,
        policy: LeavePolicy,
        partial_day_portion: float,
        holiday_calendar: HolidayCalendar | None,
    ) -> tuple[float, list[str]]:
        if end < start:
            raise ValueError("end_date must be >= start_date")
        if partial_day_portion not in {0.5, 1.0}:
            raise ValueError("partial_day_portion must be 0.5 or 1.0")
        if partial_day_portion != 1.0 and not policy.allow_partial_days:
            raise ValueError("policy does not allow partial-day leave")

        holiday_dates: list[str] = []
        if holiday_calendar is not None:
            holiday_dates = [
                current.isoformat()
                for current in self._date_range(start, end)
                if current.isoformat() in holiday_calendar.holidays
            ]
        working_days = float((end - start).days + 1 - len(holiday_dates))
        if working_days <= 0:
            raise ValueError("leave range resolves entirely to holidays")
        if start != end and partial_day_portion != 1.0:
            raise ValueError("partial-day leave is only supported for single-day requests")
        total_days = partial_day_portion if start == end and partial_day_portion != 1.0 else working_days
        return total_days, holiday_dates

    def ensure_balance_capacity(self, *, balance: LeaveBalance, policy: LeavePolicy, days: float) -> None:
        remaining = balance.remaining_days
        if policy.allow_negative_balance or remaining is None:
            return
        if remaining < days:
            raise ValueError(f"Requested leave exceeds available balance ({remaining} < {days})")

    def accrued_days_between(self, *, policy: LeavePolicy, last_accrual_on: date | None, as_of: date) -> float:
        if policy.accrual_frequency == AccrualFrequency.NONE or policy.accrual_rate_days <= 0:
            return 0.0
        anchor = last_accrual_on or date(as_of.year, 1, 1)
        periods = 0
        cursor = anchor
        while True:
            next_cursor = self._advance(cursor, policy.accrual_frequency)
            if next_cursor > as_of:
                break
            periods += 1
            cursor = next_cursor
        return round(periods * policy.accrual_rate_days, 2)

    def apply_carry_forward(self, *, balance: LeaveBalance, policy: LeavePolicy) -> float:
        if balance.entitlement_days is None:
            return 0.0
        carry_limit = policy.carry_forward_limit_days or 0.0
        unused = max(0.0, balance.remaining_days or 0.0)
        return round(min(unused, carry_limit), 2)

    @staticmethod
    def _advance(anchor: date, frequency: AccrualFrequency) -> date:
        if frequency == AccrualFrequency.MONTHLY:
            month = anchor.month + 1
            year = anchor.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            return date(year, month, 1)
        if frequency == AccrualFrequency.QUARTERLY:
            month = anchor.month + 3
            year = anchor.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            return date(year, month, 1)
        if frequency == AccrualFrequency.YEARLY:
            return date(anchor.year + 1, 1, 1)
        return anchor

    @staticmethod
    def _date_range(start: date, end: date) -> list[date]:
        cursor = start
        rows: list[date] = []
        while cursor <= end:
            rows.append(cursor)
            cursor = date.fromordinal(cursor.toordinal() + 1)
        return rows


class LeaveService:
    def __init__(
        self,
        db_path: str | None = None,
        *,
        workflow_service: WorkflowService | None = None,
        notification_service: NotificationService | None = None,
    ):
        self.requests = PersistentKVStore[str, LeaveRequest](service='leave-service', namespace='requests', db_path=db_path)
        shared_db_path = self.requests.db_path
        self.events: list[dict] = []
        self.error_logger = CentralErrorLogger("leave-service")
        self.dead_letters = DeadLetterQueue()
        self.idempotency = IdempotencyStore()
        self.observability = Observability("leave-service")
        self.tenant_id = DEFAULT_TENANT_ID
        self.event_registry = EventRegistry()
        self.notification_service = notification_service or NotificationService()
        self.workflow_service = workflow_service or WorkflowService(notification_service=self.notification_service)
        self.outbox = OutboxManager(
            service_name='leave-service',
            tenant_id=self.tenant_id,
            db_path=shared_db_path,
            observability=self.observability,
            dead_letters=self.dead_letters,
            event_registry=self.event_registry,
        )
        self.employees = PersistentKVStore[str, EmployeeRecord](service='leave-service', namespace='employees', db_path=db_path)
        self.leave_balances = PersistentKVStore[tuple[str, LeaveType], LeaveBalance](service='leave-service', namespace='leave_balances', db_path=shared_db_path)
        self.leave_policies = PersistentKVStore[str, LeavePolicy](service='leave-service', namespace='leave_policies', db_path=shared_db_path)
        self.employee_policy_assignments = PersistentKVStore[tuple[str, LeaveType], str](service='leave-service', namespace='leave_policy_assignments', db_path=shared_db_path)
        self.holiday_calendars = PersistentKVStore[str, HolidayCalendar](service='leave-service', namespace='holiday_calendars', db_path=shared_db_path)
        self.leave_balance_ledger = PersistentKVStore[str, LeaveLedgerEntry](service='leave-service', namespace='leave_balance_ledger', db_path=shared_db_path)
        self.attendance_impacts = PersistentKVStore[str, list[dict]](service='leave-service', namespace='attendance_impacts', db_path=shared_db_path)
        self._lock = RLock()
        self.policy_engine = LeavePolicyEngine()

        self._seed_employees()
        self._seed_leave_policies()
        self._seed_leave_balances()
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code="leave_request_approval",
            source_service="leave-service",
            subject_type="LeaveRequest",
            description="Centralized leave approval workflow aligned to the workflow catalog.",
            steps=[
                {
                    "name": "manager-approval",
                    "type": "approval",
                    "assignee_template": "{approver_employee_id}",
                    "sla": "PT24H",
                    "escalation_assignee_template": "{escalation_assignee}",
                }
            ],
        )

    def _seed_employees(self) -> None:
        seeded_employees = {
            "emp-admin": EmployeeRecord(self.tenant_id, "emp-admin", "dept-admin", None, EmployeeStatus.ACTIVE, location_code="US-HQ", grade_code="G10"),
            "emp-manager": EmployeeRecord(self.tenant_id, "emp-manager", "dept-eng", None, EmployeeStatus.ACTIVE, location_code="US-NY", grade_code="G9"),
            "emp-001": EmployeeRecord(self.tenant_id, "emp-001", "dept-eng", "emp-manager", EmployeeStatus.ACTIVE, location_code="US-NY", grade_code="G7"),
            "emp-002": EmployeeRecord(self.tenant_id, "emp-002", "dept-eng", "emp-manager", EmployeeStatus.ACTIVE, location_code="US-CA", grade_code="G6"),
        }
        for employee_id, employee in seeded_employees.items():
            if employee_id not in self.employees:
                self.employees[employee_id] = employee

    def _seed_leave_policies(self) -> None:
        if self.leave_policies:
            return
        now = self._now()
        defaults = [
            (LeaveType.ANNUAL, "ANNUAL-STD", "Annual Standard", 18.0, AccrualFrequency.MONTHLY, 1.5, 5.0, True, False, True),
            (LeaveType.SICK, "SICK-STD", "Sick Standard", 10.0, AccrualFrequency.NONE, 0.0, 0.0, True, False, True),
            (LeaveType.CASUAL, "CASUAL-STD", "Casual Standard", 7.0, AccrualFrequency.NONE, 0.0, 0.0, True, False, True),
            (LeaveType.UNPAID, "UNPAID-STD", "Unpaid Standard", None, AccrualFrequency.NONE, 0.0, None, False, True, True),
            (LeaveType.OTHER, "OTHER-STD", "Other Standard", 5.0, AccrualFrequency.NONE, 0.0, 0.0, True, False, True),
        ]
        for leave_type, code, name, entitlement, frequency, rate, carry_limit, requires_approval, allow_negative, allow_partial in defaults:
            policy = LeavePolicy(
                tenant_id=self.tenant_id,
                leave_policy_id=str(uuid.uuid4()),
                code=code,
                name=name,
                leave_type=leave_type,
                location_codes=["*"],
                grade_codes=["*"],
                annual_entitlement_days=entitlement,
                accrual_frequency=frequency,
                accrual_rate_days=rate,
                carry_forward_limit_days=carry_limit,
                requires_approval=requires_approval,
                allow_negative_balance=allow_negative,
                allow_partial_days=allow_partial,
                status="Active",
                created_at=now,
                updated_at=now,
            )
            self.leave_policies[policy.leave_policy_id] = policy

    def _seed_leave_balances(self) -> None:
        for employee_id in self.employees:
            employee = self.employees[employee_id]
            for leave_type in LeaveType:
                policy = self._resolve_policy(employee_id, leave_type)
                if (employee_id, leave_type) not in self.leave_balances:
                    self.leave_balances[(employee_id, leave_type)] = LeaveBalance(
                        tenant_id=self.tenant_id,
                        employee_id=employee_id,
                        leave_type=leave_type,
                        entitlement_days=policy.annual_entitlement_days,
                        reserved_days=0.0,
                        approved_days=0.0,
                        policy_id=policy.leave_policy_id,
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

    def _resolve_policy(self, employee_id: str, leave_type: LeaveType) -> LeavePolicy:
        employee = self.employees.get(employee_id)
        if not employee:
            raise ValueError(f"Unknown employee {employee_id}")
        return self.policy_engine.resolve_policy(
            tenant_id=self.tenant_id,
            employee=employee,
            leave_type=leave_type,
            policies=list(self.leave_policies.values()),
            assignments=dict(self.employee_policy_assignments.items()),
        )

    def _policy_snapshot(self, employee_id: str, leave_type: LeaveType) -> dict[str, Any]:
        return self._resolve_policy(employee_id, leave_type).to_dict()

    def _resolve_holiday_calendar(self, employee_id: str) -> HolidayCalendar | None:
        employee = self.employees[employee_id]
        for calendar in self.holiday_calendars.values():
            if calendar.tenant_id == self.tenant_id and calendar.location_code == employee.location_code:
                return calendar
        return None

    def _calculate_leave_days(
        self,
        *,
        employee_id: str,
        leave_type: LeaveType,
        start_date: date,
        end_date: date,
        partial_day_portion: float,
        trace_id: str | None,
    ) -> tuple[float, list[str], LeavePolicy]:
        policy = self._resolve_policy(employee_id, leave_type)
        holiday_calendar = self._resolve_holiday_calendar(employee_id)
        try:
            total_days, holiday_dates = self.policy_engine.calculate_leave_days(
                start=start_date,
                end=end_date,
                policy=policy,
                partial_day_portion=partial_day_portion,
                holiday_calendar=holiday_calendar,
            )
        except ValueError as exc:
            self._fail(422, "VALIDATION_ERROR", str(exc), trace_id)
        return total_days, holiday_dates, policy

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
        return [self.leave_balances[(employee_id, leave_type)].to_dict() for leave_type in LeaveType]

    def _record_ledger(
        self,
        *,
        employee_id: str,
        leave_type: LeaveType,
        entry_type: str,
        delta_days: float,
        trace_id: str | None,
        leave_request_id: str | None = None,
        effective_on: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        balance = self._get_balance(employee_id, leave_type)
        entry = LeaveLedgerEntry(
            tenant_id=self.tenant_id,
            ledger_entry_id=str(uuid.uuid4()),
            employee_id=employee_id,
            leave_type=leave_type,
            entry_type=entry_type,
            delta_days=round(delta_days, 2),
            balance_after=balance.remaining_days,
            effective_on=effective_on or self._today().isoformat(),
            created_at=self._now(),
            leave_request_id=leave_request_id,
            policy_id=balance.policy_id,
            metadata=metadata or {},
        )
        self.leave_balance_ledger[entry.ledger_entry_id] = entry
        audit = emit_audit_record(
            service_name='leave-service',
            tenant_id=self.tenant_id,
            actor={'id': 'system', 'type': 'system'},
            action='leave_balance_ledger_recorded',
            entity='LeaveBalanceLedger',
            entity_id=entry.ledger_entry_id,
            before={},
            after=entry.to_dict(),
            trace_id=self._trace(trace_id),
            source={'entry_type': entry_type, 'employee_id': employee_id, 'leave_type': leave_type.value},
        )
        self.observability.logger.info(
            'leave.balance_ledger_recorded',
            trace_id=self._trace(trace_id),
            message=entry_type,
            context={'employee_id': employee_id, 'leave_type': leave_type.value, 'audit_record': audit},
        )
        return entry.to_dict()

    def _ensure_balance_capacity(self, employee_id: str, leave_type: LeaveType, days: float, trace_id: str | None) -> None:
        balance = self._get_balance(employee_id, leave_type)
        policy = self._resolve_policy(employee_id, leave_type)
        try:
            self.policy_engine.ensure_balance_capacity(balance=balance, policy=policy, days=days)
        except ValueError:
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
                        "remaining_days": balance.remaining_days,
                        "policy_id": policy.leave_policy_id,
                    }
                ],
            )

    def _reserve_balance(self, leave: LeaveRequest, trace_id: str | None) -> None:
        self._ensure_balance_capacity(leave.employee_id, leave.leave_type, leave.total_days, trace_id)
        balance = self._get_balance(leave.employee_id, leave.leave_type)
        balance.reserved_days += leave.total_days
        self._record_ledger(
            employee_id=leave.employee_id,
            leave_type=leave.leave_type,
            entry_type='reservation',
            delta_days=-leave.total_days,
            leave_request_id=leave.leave_request_id,
            trace_id=trace_id,
            metadata={'status': LeaveStatus.SUBMITTED.value},
        )

    def _release_reserved_balance(self, leave: LeaveRequest, trace_id: str | None = None) -> None:
        balance = self._get_balance(leave.employee_id, leave.leave_type)
        balance.reserved_days = max(0.0, balance.reserved_days - leave.total_days)
        self._record_ledger(
            employee_id=leave.employee_id,
            leave_type=leave.leave_type,
            entry_type='reservation_released',
            delta_days=leave.total_days,
            leave_request_id=leave.leave_request_id,
            trace_id=trace_id,
            metadata={'status': leave.status.value},
        )

    def _consume_reserved_balance(self, leave: LeaveRequest, trace_id: str | None = None) -> None:
        balance = self._get_balance(leave.employee_id, leave.leave_type)
        balance.reserved_days = max(0.0, balance.reserved_days - leave.total_days)
        balance.approved_days += leave.total_days
        self._record_ledger(
            employee_id=leave.employee_id,
            leave_type=leave.leave_type,
            entry_type='consumption',
            delta_days=-leave.total_days,
            leave_request_id=leave.leave_request_id,
            trace_id=trace_id,
            metadata={'status': LeaveStatus.APPROVED.value},
        )

    def _restore_approved_balance(self, leave: LeaveRequest, trace_id: str | None = None) -> None:
        balance = self._get_balance(leave.employee_id, leave.leave_type)
        balance.approved_days = max(0.0, balance.approved_days - leave.total_days)
        self._record_ledger(
            employee_id=leave.employee_id,
            leave_type=leave.leave_type,
            entry_type='approved_balance_restored',
            delta_days=leave.total_days,
            leave_request_id=leave.leave_request_id,
            trace_id=trace_id,
            metadata={'status': LeaveStatus.CANCELLED.value},
        )

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
            self.outbox.tenant_id = self.tenant_id
            self.outbox.enqueue(
                legacy_event_name=event,
                data={**payload, "tenant_id": self.tenant_id},
                correlation_id=self._trace(trace_id),
                idempotency_key=payload.get("leave_request_id") or payload.get("employee_id"),
            )
            self.outbox.dispatch_pending(self.events.append)
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
        holiday_dates = set(leave.holiday_dates)
        while cursor <= leave.end_date:
            if cursor.isoformat() not in holiday_dates:
                impacts.append(
                    {
                        "attendance_date": cursor.isoformat(),
                        "attendance_status": "Absent" if leave.partial_day_portion == 1.0 or cursor != leave.start_date else "HalfDayAbsent",
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
                "location_code": employee.location_code,
                "grade_code": employee.grade_code,
                "hire_date": employee.hire_date.isoformat(),
            },
            "leave_balances": self._balances_for_employee(employee_id),
            "leave_requests": leaves,
            "attendance_impacts": [impact for items in self.attendance_impacts.values() for impact in items if impact.get("tenant_id") == self.tenant_id and impact["employee_id"] == employee_id],
            "active_leave": active_leave,
        }

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
            map_error=lambda exc: self._fail(exc.status_code, exc.code, exc.message, trace_id, exc.details),
            invalid_action=lambda _action: self._fail(422, "VALIDATION_ERROR", "Action must be approve or reject", trace_id, [{"field": "action", "reason": "must be approve or reject"}]),
        )

    def _require_terminal_workflow_result(self, workflow: dict[str, Any], *, action: str, trace_id: str, mismatch_code: str, mismatch_message: str) -> str:
        return require_terminal_workflow_result(
            workflow,
            action=action,
            on_mismatch=lambda _actual, _expected: self._fail(409, mismatch_code, mismatch_message, trace_id),
            invalid_action=lambda _action: self._fail(422, "VALIDATION_ERROR", "Action must be approve or reject", trace_id, [{"field": "action", "reason": "must be approve or reject"}]),
        )

    def _response_payload(self, leave: LeaveRequest) -> dict:
        payload = leave.to_dict()
        payload["leave_balance"] = self._balance_snapshot(leave.employee_id, leave.leave_type)
        payload["attendance_impacts"] = list(self.attendance_impacts.get(leave.leave_request_id, []))
        payload["employee_status"] = self.employees[leave.employee_id].status.value
        payload["tenant_id"] = leave.tenant_id
        payload["policy"] = self._policy_snapshot(leave.employee_id, leave.leave_type)
        payload["workflow"] = self.workflow_service.get_instance(leave.workflow_id, tenant_id=leave.tenant_id) if leave.workflow_id else None
        return payload

    def _actor_payload(self, actor_role: str, actor_employee_id: str, *, actor_type: str = 'user') -> dict[str, str | None]:
        return {'id': actor_employee_id or actor_role, 'type': actor_type, 'role': actor_role}

    def _audit_leave_mutation(self, action: str, actor_role: str, actor_employee_id: str, leave_request_id: str, before: dict, after: dict, trace_id: str | None) -> None:
        self.observability.logger.audit(
            action,
            trace_id=trace_id,
            actor=self._actor_payload(actor_role, actor_employee_id),
            entity='LeaveRequest',
            entity_id=leave_request_id,
            context={'tenant_id': self.tenant_id, 'before': before, 'after': after},
        )

    def _audit_domain_change(self, action: str, entity: str, entity_id: str, before: Any, after: Any, trace_id: str | None, actor: dict[str, Any] | None = None) -> dict[str, Any]:
        return emit_audit_record(
            service_name='leave-service',
            tenant_id=self.tenant_id,
            actor=actor or {'id': 'system', 'type': 'system'},
            action=action,
            entity=entity,
            entity_id=entity_id,
            before=before,
            after=after,
            trace_id=self._trace(trace_id),
        )

    def replay_dead_letters(self) -> list[dict]:
        recovered = self.dead_letters.recover(
            lambda entry: entry.workflow == "leave_request",
            lambda entry: True,
        )
        for entry in recovered:
            payload = dict(entry.payload)
            payload.pop("simulate_failure", None)
            self.outbox.tenant_id = self.tenant_id
            self.outbox.enqueue(
                legacy_event_name=entry.operation,
                data={**payload, "tenant_id": self.tenant_id, "recovered_from_dead_letter": True},
                correlation_id=entry.trace_id,
                idempotency_key=payload.get("leave_request_id"),
            )
        self.outbox.dispatch_pending(self.events.append)
        return [entry.__dict__ for entry in recovered]

    def create_or_update_policy(self, payload: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        self.tenant_id = self._resolve_tenant(payload.get('tenant_id'))
        leave_type = LeaveType(payload['leave_type'])
        now = self._now()
        policy_id = payload.get('leave_policy_id')
        existing = self.leave_policies.get(policy_id) if policy_id else None
        before = existing.to_dict() if existing else {}
        policy = LeavePolicy(
            tenant_id=self.tenant_id,
            leave_policy_id=policy_id or str(uuid.uuid4()),
            code=payload['code'],
            name=payload['name'],
            leave_type=leave_type,
            location_codes=list(payload.get('location_codes') or ['*']),
            grade_codes=list(payload.get('grade_codes') or ['*']),
            annual_entitlement_days=payload.get('annual_entitlement_days'),
            accrual_frequency=AccrualFrequency(payload.get('accrual_frequency', 'None')),
            accrual_rate_days=float(payload.get('accrual_rate_days', 0.0)),
            carry_forward_limit_days=payload.get('carry_forward_limit_days'),
            requires_approval=bool(payload.get('requires_approval', True)),
            allow_negative_balance=bool(payload.get('allow_negative_balance', False)),
            allow_partial_days=bool(payload.get('allow_partial_days', True)),
            status=payload.get('status', 'Active'),
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self.leave_policies[policy.leave_policy_id] = policy
        action = 'leave_policy_updated' if existing else 'leave_policy_created'
        audit = self._audit_domain_change(action, 'LeavePolicy', policy.leave_policy_id, before, policy.to_dict(), trace_id)
        self.observability.logger.info('leave.policy_upserted', trace_id=self._trace(trace_id), message=action, context={'leave_policy_id': policy.leave_policy_id, 'audit_record': audit})
        for employee_id in self.employees:
            employee = self.employees[employee_id]
            if employee.tenant_id != self.tenant_id:
                continue
            try:
                resolved = self._resolve_policy(employee_id, policy.leave_type)
            except Exception:
                continue
            balance = self._get_balance(employee_id, policy.leave_type)
            balance.policy_id = resolved.leave_policy_id
            if balance.entitlement_days is None or resolved.annual_entitlement_days is not None:
                balance.entitlement_days = resolved.annual_entitlement_days
        return policy.to_dict()

    def assign_policy_to_employee(self, employee_id: str, leave_type: str, leave_policy_id: str, *, trace_id: str | None = None) -> dict[str, Any]:
        self.tenant_id = self._resolve_tenant(None)
        leave_type_enum = LeaveType(leave_type)
        before = {'leave_policy_id': self.employee_policy_assignments.get((employee_id, leave_type_enum))}
        self.employee_policy_assignments[(employee_id, leave_type_enum)] = leave_policy_id
        balance = self._get_balance(employee_id, leave_type_enum)
        policy = self._resolve_policy(employee_id, leave_type_enum)
        balance.policy_id = policy.leave_policy_id
        if policy.annual_entitlement_days is not None:
            balance.entitlement_days = policy.annual_entitlement_days
        after = {'employee_id': employee_id, 'leave_type': leave_type_enum.value, 'leave_policy_id': leave_policy_id}
        self._audit_domain_change('leave_policy_assigned', 'EmployeeLeavePolicy', f'{employee_id}:{leave_type_enum.value}', before, after, trace_id)
        return after

    def upsert_holiday_calendar(self, location_code: str, payload: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        self.tenant_id = self._resolve_tenant(payload.get('tenant_id'))
        existing = next((calendar for calendar in self.holiday_calendars.values() if calendar.tenant_id == self.tenant_id and calendar.location_code == location_code), None)
        before = existing.to_dict() if existing else {}
        now = self._now()
        calendar = HolidayCalendar(
            tenant_id=self.tenant_id,
            calendar_id=existing.calendar_id if existing else str(uuid.uuid4()),
            location_code=location_code,
            name=payload.get('name', f'{location_code} holiday calendar'),
            holidays=dict(payload.get('holidays') or {}),
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self.holiday_calendars[calendar.calendar_id] = calendar
        action = 'holiday_calendar_updated' if existing else 'holiday_calendar_created'
        self._audit_domain_change(action, 'HolidayCalendar', calendar.calendar_id, before, calendar.to_dict(), trace_id)
        return calendar.to_dict()

    def list_holiday_calendars(self, *, tenant_id: str | None = None) -> list[dict[str, Any]]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        return [calendar.to_dict() for calendar in self.holiday_calendars.values() if calendar.tenant_id == self.tenant_id]

    def list_policies(self, *, tenant_id: str | None = None, leave_type: str | None = None) -> list[dict[str, Any]]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        rows = [policy.to_dict() for policy in self.leave_policies.values() if policy.tenant_id == self.tenant_id]
        if leave_type:
            rows = [row for row in rows if row['leave_type'] == leave_type]
        rows.sort(key=lambda item: (item['leave_type'], item['code']))
        return rows

    def get_leave_ledger(self, employee_id: str, *, leave_type: str | None = None, tenant_id: str | None = None) -> list[dict[str, Any]]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        rows = []
        for entry in self.leave_balance_ledger.values():
            if entry.tenant_id != self.tenant_id or entry.employee_id != employee_id:
                continue
            if leave_type and entry.leave_type.value != leave_type:
                continue
            rows.append(entry.to_dict())
        rows.sort(key=lambda item: (item['effective_on'], item['created_at'], item['ledger_entry_id']))
        return rows

    def accrue_balances(self, *, as_of: date | None = None, employee_id: str | None = None, tenant_id: str | None = None, trace_id: str | None = None) -> dict[str, Any]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        effective_date = as_of or self._today()
        updated: list[dict[str, Any]] = []
        for candidate_employee_id in self.employees:
            if employee_id and candidate_employee_id != employee_id:
                continue
            employee = self.employees[candidate_employee_id]
            if employee.tenant_id != self.tenant_id:
                continue
            for leave_type in LeaveType:
                policy = self._resolve_policy(candidate_employee_id, leave_type)
                balance = self._get_balance(candidate_employee_id, leave_type)
                last = date.fromisoformat(balance.last_accrual_at) if balance.last_accrual_at else None
                accrued = self.policy_engine.accrued_days_between(policy=policy, last_accrual_on=last, as_of=effective_date)
                if accrued <= 0:
                    continue
                if balance.entitlement_days is not None and policy.annual_entitlement_days is not None and policy.annual_entitlement_days > 0:
                    available_room = max(0.0, policy.annual_entitlement_days - balance.accrued_days)
                    accrued = min(accrued, available_room)
                if accrued <= 0:
                    balance.last_accrual_at = effective_date.isoformat()
                    continue
                balance.accrued_days = round(balance.accrued_days + accrued, 2)
                balance.last_accrual_at = effective_date.isoformat()
                ledger = self._record_ledger(
                    employee_id=candidate_employee_id,
                    leave_type=leave_type,
                    entry_type='accrual',
                    delta_days=accrued,
                    trace_id=trace_id,
                    effective_on=effective_date.isoformat(),
                    metadata={'policy_id': policy.leave_policy_id},
                )
                updated.append({'employee_id': candidate_employee_id, 'leave_type': leave_type.value, 'accrued_days': accrued, 'ledger_entry': ledger})
        self._audit_domain_change('leave_accrual_processed', 'LeaveAccrualBatch', effective_date.isoformat(), {}, {'items': updated}, trace_id)
        return {'as_of': effective_date.isoformat(), 'items': updated}

    def apply_carry_forward(self, *, year: int, employee_id: str | None = None, tenant_id: str | None = None, trace_id: str | None = None) -> dict[str, Any]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        items: list[dict[str, Any]] = []
        for candidate_employee_id in self.employees:
            if employee_id and candidate_employee_id != employee_id:
                continue
            employee = self.employees[candidate_employee_id]
            if employee.tenant_id != self.tenant_id:
                continue
            for leave_type in LeaveType:
                policy = self._resolve_policy(candidate_employee_id, leave_type)
                balance = self._get_balance(candidate_employee_id, leave_type)
                carry = self.policy_engine.apply_carry_forward(balance=balance, policy=policy)
                if carry <= 0:
                    continue
                balance.carried_forward_days = carry
                balance.last_carry_forward_at = date(year, 1, 1).isoformat()
                ledger = self._record_ledger(
                    employee_id=candidate_employee_id,
                    leave_type=leave_type,
                    entry_type='carry_forward',
                    delta_days=carry,
                    trace_id=trace_id,
                    effective_on=date(year, 1, 1).isoformat(),
                    metadata={'policy_id': policy.leave_policy_id, 'year': year},
                )
                items.append({'employee_id': candidate_employee_id, 'leave_type': leave_type.value, 'carried_forward_days': carry, 'ledger_entry': ledger})
        self._audit_domain_change('leave_carry_forward_processed', 'LeaveCarryForwardBatch', str(year), {}, {'items': items}, trace_id)
        return {'year': year, 'items': items}

    def recompute_employee_balance(self, employee_id: str, *, tenant_id: str | None = None, trace_id: str | None = None) -> dict[str, Any]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        self._ensure_employee_eligible(employee_id, trace_id)
        balances: list[dict[str, Any]] = []
        for leave_type in LeaveType:
            policy = self._resolve_policy(employee_id, leave_type)
            balance = self._get_balance(employee_id, leave_type)
            balance.policy_id = policy.leave_policy_id
            balance.reserved_days = round(
                sum(
                    leave.total_days
                    for leave in self.requests.values()
                    if leave.tenant_id == self.tenant_id and leave.employee_id == employee_id and leave.leave_type == leave_type and leave.status == LeaveStatus.SUBMITTED
                ),
                2,
            )
            balance.approved_days = round(
                sum(
                    leave.total_days
                    for leave in self.requests.values()
                    if leave.tenant_id == self.tenant_id and leave.employee_id == employee_id and leave.leave_type == leave_type and leave.status == LeaveStatus.APPROVED
                ),
                2,
            )
            if balance.entitlement_days is None or policy.annual_entitlement_days is not None:
                balance.entitlement_days = policy.annual_entitlement_days
            balances.append(balance.to_dict())
        employee = self.employees[employee_id]
        employee_payload = {
            'employee_id': employee.employee_id,
            'department_id': employee.department_id,
            'manager_employee_id': employee.manager_employee_id,
            'status': employee.status.value,
            'location_code': employee.location_code,
            'grade_code': employee.grade_code,
            'hire_date': employee.hire_date.isoformat(),
        }
        self._audit_domain_change('leave_balance_recomputed', 'LeaveBalance', employee_id, {}, {'employee': employee_payload, 'leave_balances': balances}, trace_id)
        return {'employee_id': employee_id, 'employee': employee_payload, 'leave_balances': balances}

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
        partial_day_portion: float = 1.0,
    ) -> tuple[int, dict]:
        self.tenant_id = self._resolve_tenant(tenant_id)
        trace = self._trace(trace_id)
        started = perf_counter()
        role = Role(actor_role)
        try:
            with self._lock:
                self._ensure_employee_eligible(employee_id, trace)
                self._ensure_lifecycle_scope(role, actor_employee_id, employee_id, trace)
                if self._overlap_exists(employee_id, start_date, end_date):
                    self._fail(409, "LEAVE_OVERLAP", "Leave range overlaps with existing submitted/approved leave", trace)

                leave_type_enum = LeaveType(leave_type)
                total_days, holiday_dates, policy = self._calculate_leave_days(
                    employee_id=employee_id,
                    leave_type=leave_type_enum,
                    start_date=start_date,
                    end_date=end_date,
                    partial_day_portion=partial_day_portion,
                    trace_id=trace,
                )
                self._ensure_balance_capacity(employee_id, leave_type_enum, total_days, trace)
                now = self._now()
                leave = LeaveRequest(
                    tenant_id=self.tenant_id,
                    leave_request_id=str(uuid.uuid4()),
                    employee_id=employee_id,
                    leave_type=leave_type_enum,
                    start_date=start_date,
                    end_date=end_date,
                    total_days=total_days,
                    reason=reason,
                    approver_employee_id=approver_employee_id,
                    workflow_id=None,
                    status=LeaveStatus.DRAFT,
                    submitted_at=None,
                    decision_at=None,
                    created_at=now,
                    updated_at=now,
                    partial_day_portion=partial_day_portion,
                    policy_id=policy.leave_policy_id,
                    holiday_dates=holiday_dates,
                )
                self.requests[leave.leave_request_id] = leave
            self._audit_leave_mutation('leave_request_created', actor_role, actor_employee_id, leave.leave_request_id, {}, self._response_payload(leave), trace)
            self.observability.logger.info(
                "leave.request_created",
                trace_id=trace,
                context={"leave_request_id": leave.leave_request_id, "employee_id": employee_id, "policy_id": leave.policy_id},
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
            if leave.status == LeaveStatus.APPROVED:
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

            policy = self._resolve_policy(leave.employee_id, leave.leave_type)
            self._reserve_balance(leave, trace)
            ts = self._now()
            if not leave.approver_employee_id:
                employee = self.employees[leave.employee_id]
                leave.approver_employee_id = employee.manager_employee_id or "emp-admin"
            workflow = self.workflow_service.start_workflow(
                tenant_id=self.tenant_id,
                definition_code="leave_request_approval",
                source_service="leave-service",
                subject_type="LeaveRequest",
                subject_id=leave.leave_request_id,
                actor_id=actor_employee_id,
                actor_type="user",
                context={
                    "approver_employee_id": leave.approver_employee_id if policy.requires_approval else "system-auto-approver",
                    "escalation_assignee": "emp-admin",
                    "policy_id": policy.leave_policy_id,
                    "requires_approval": policy.requires_approval,
                },
                trace_id=trace,
            )
            leave.workflow_id = workflow["workflow_id"]
            leave.status = LeaveStatus.SUBMITTED
            leave.submitted_at = ts
            leave.updated_at = ts

            if not policy.requires_approval:
                workflow = self._resolve_workflow(
                    leave.workflow_id,
                    self.tenant_id,
                    action="approve",
                    actor_id="system-auto-approver",
                    actor_type="system",
                    actor_role=None,
                    comment="Auto-approved by leave policy engine",
                    trace_id=trace,
                )
                self._require_terminal_workflow_result(workflow, action="approve", trace_id=trace, mismatch_code='WORKFLOW_BYPASS_DETECTED', mismatch_message='Leave workflow did not auto-complete as expected')
                self._consume_reserved_balance(leave, trace)
                leave.status = LeaveStatus.APPROVED
                leave.decision_at = ts
                leave.updated_at = ts
                self._sync_employee_leave_status(leave.employee_id)
                self._sync_attendance_impacts(leave)
                event_name = 'LeaveRequestApproved'
            else:
                event_name = 'LeaveRequestSubmitted'
            payload = self._response_payload(leave)
            self._emit_event(
                event_name,
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
            if not leave.workflow_id:
                self._fail(409, "WORKFLOW_MISSING", "Leave request is missing its centralized workflow", trace)

            workflow = self._resolve_workflow(
                leave.workflow_id,
                self.tenant_id,
                action=action,
                actor_id=actor_employee_id,
                actor_type="user",
                actor_role=actor_role,
                comment=reason,
                trace_id=trace,
            )

            ts = self._now()
            terminal_result = self._require_terminal_workflow_result(workflow, action=action, trace_id=trace, mismatch_code="WORKFLOW_BYPASS_DETECTED", mismatch_message="Leave workflow did not reach the expected decision")
            if action == "approve" and terminal_result == "approved":
                self._consume_reserved_balance(leave, trace)
                leave.status = LeaveStatus.APPROVED
                event = "LeaveRequestApproved"
            elif action == "reject" and terminal_result == "rejected":
                self._release_reserved_balance(leave, trace)
                leave.status = LeaveStatus.REJECTED
                if reason:
                    leave.reason = f"{leave.reason or ''}\n[Rejection] {reason}".strip()
                event = "LeaveRequestRejected"
            else:
                self._fail(409, "WORKFLOW_BYPASS_DETECTED", "Workflow resolution did not produce a valid leave decision", trace)
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
                    self._release_reserved_balance(leave, trace)
                elif leave.status == LeaveStatus.APPROVED:
                    self._restore_approved_balance(leave, trace)
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
            if self._overlap_exists(leave.employee_id, start, end, exclude_id=leave.leave_request_id):
                self._fail(409, "LEAVE_OVERLAP", "Leave range overlaps with existing submitted/approved leave", trace)
            next_type = LeaveType(patch["leave_type"]) if "leave_type" in patch else leave.leave_type
            partial_day_portion = float(patch.get('partial_day_portion', leave.partial_day_portion))
            next_total_days, holiday_dates, policy = self._calculate_leave_days(
                employee_id=leave.employee_id,
                leave_type=next_type,
                start_date=start,
                end_date=end,
                partial_day_portion=partial_day_portion,
                trace_id=trace,
            )
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
            leave.partial_day_portion = partial_day_portion
            leave.holiday_dates = holiday_dates
            leave.policy_id = policy.leave_policy_id
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
                    "leave_policies": len(self.leave_policies),
                    "leave_balance_ledger": len(self.leave_balance_ledger),
                }
            )


def encode_token(role: str, employee_id: str, department_id: str | None = None) -> str:
    payload = {"role": role, "employee_id": employee_id, "department_id": department_id}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
