from __future__ import annotations

import base64
import calendar
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from threading import RLock
from time import perf_counter
from typing import Any
from uuid import uuid4

from event_contract import EventRegistry, emit_canonical_event
from notification_service import NotificationService
from outbox_system import OutboxManager
from persistent_store import PersistentKVStore
from resilience import CentralErrorLogger, DeadLetterQueue, IdempotencyStore, Observability
from workflow_service import WorkflowService, WorkflowServiceError


class Role(str, Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    EMPLOYEE = "Employee"


class PayrollStatus(str, Enum):
    DRAFT = "Draft"
    PROCESSED = "Processed"
    PAID = "Paid"
    CANCELLED = "Cancelled"


class PayrollBatchStatus(str, Enum):
    PENDING = "Pending"
    PROCESSED = "Processed"
    PARTIAL_FAILURE = "PartialFailure"
    PAID = "Paid"
    FAILED = "Failed"


@dataclass(frozen=True)
class AuthContext:
    role: Role
    employee_id: str | None = None
    department_id: str | None = None


@dataclass
class PayrollRecord:
    payroll_record_id: str
    employee_id: str
    salary_structure_id: str | None
    payroll_cycle_id: str | None
    pay_period_start: date
    pay_period_end: date
    base_salary: Decimal
    allowances: Decimal
    deductions: Decimal
    overtime_pay: Decimal
    gross_pay: Decimal
    net_pay: Decimal
    currency: str
    payment_date: date | None
    payment_workflow_id: str | None
    status: PayrollStatus
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "payroll_record_id": self.payroll_record_id,
            "employee_id": self.employee_id,
            "salary_structure_id": self.salary_structure_id,
            "payroll_cycle_id": self.payroll_cycle_id,
            "pay_period_start": self.pay_period_start.isoformat(),
            "pay_period_end": self.pay_period_end.isoformat(),
            "base_salary": str(self.base_salary),
            "allowances": str(self.allowances),
            "deductions": str(self.deductions),
            "overtime_pay": str(self.overtime_pay),
            "gross_pay": str(self.gross_pay),
            "net_pay": str(self.net_pay),
            "currency": self.currency,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment_workflow_id": self.payment_workflow_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class PayrollBatch:
    batch_id: str
    period_start: date
    period_end: date
    status: PayrollBatchStatus
    record_ids: list[str] = field(default_factory=list)
    processed_count: int = 0
    paid_count: int = 0
    failed_count: int = 0
    failures: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "status": self.status.value,
            "record_ids": list(self.record_ids),
            "processed_count": self.processed_count,
            "paid_count": self.paid_count,
            "failed_count": self.failed_count,
            "failures": [dict(item) for item in self.failures],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class PayrollCycle:
    payroll_cycle_id: str
    name: str
    pay_period_start: date
    pay_period_end: date
    payment_date: date
    status: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "payroll_cycle_id": self.payroll_cycle_id,
            "name": self.name,
            "pay_period_start": self.pay_period_start.isoformat(),
            "pay_period_end": self.pay_period_end.isoformat(),
            "payment_date": self.payment_date.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class SalaryStructure:
    salary_structure_id: str
    employee_id: str
    base_salary: Decimal
    allowances: Decimal
    deductions: Decimal
    overtime_rate: Decimal
    currency: str
    effective_from: date
    effective_to: date | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "salary_structure_id": self.salary_structure_id,
            "employee_id": self.employee_id,
            "base_salary": str(self.base_salary),
            "allowances": str(self.allowances),
            "deductions": str(self.deductions),
            "overtime_rate": str(self.overtime_rate),
            "currency": self.currency,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class EmployeePayrollProfile:
    employee_id: str
    department_id: str | None = None
    role_id: str | None = None
    status: str = "Active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "department_id": self.department_id,
            "role_id": self.role_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ServiceError(Exception):
    def __init__(self, code: str, message: str, status: int, details: list[dict[str, Any]] | None = None):
        self.code = code
        self.message = message
        self.status = status
        self.details = details or []
        super().__init__(message)

    def to_error(self, trace_id: str | None = None) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "trace_id": trace_id or uuid4().hex,
            }
        }


class PayrollService:
    """Canonical payroll-service business logic and API-compatible handlers."""

    def __init__(self, db_path: str | None = None, *, workflow_service: WorkflowService | None = None, notification_service: NotificationService | None = None):
        self.records = PersistentKVStore[str, PayrollRecord](service='payroll-service', namespace='records', db_path=db_path)
        shared_db_path = self.records.db_path
        self.employee_profiles = PersistentKVStore[str, EmployeePayrollProfile](service='payroll-service', namespace='employee_profiles', db_path=shared_db_path)
        self.attendance_summaries = PersistentKVStore[tuple[str, date, date], dict[str, Any]](service='payroll-service', namespace='attendance_summaries', db_path=shared_db_path)
        self.period_index = PersistentKVStore[tuple[str, date, date], str](service='payroll-service', namespace='period_index', db_path=shared_db_path)
        self.payroll_cycles = PersistentKVStore[str, PayrollCycle](service='payroll-service', namespace='payroll_cycles', db_path=shared_db_path)
        self.payroll_cycle_index = PersistentKVStore[tuple[date, date], str](service='payroll-service', namespace='payroll_cycle_index', db_path=shared_db_path)
        self.salary_structures = PersistentKVStore[str, SalaryStructure](service='payroll-service', namespace='salary_structures', db_path=shared_db_path)
        self.salary_structure_index = PersistentKVStore[str, list[str]](service='payroll-service', namespace='salary_structure_index', db_path=shared_db_path)
        self.batches = PersistentKVStore[str, PayrollBatch](service='payroll-service', namespace='batches', db_path=shared_db_path)
        self.batch_index = PersistentKVStore[tuple[date, date], str](service='payroll-service', namespace='batch_index', db_path=shared_db_path)
        self.record_batches = PersistentKVStore[str, str](service='payroll-service', namespace='record_batches', db_path=shared_db_path)
        self.events: list[dict[str, Any]] = []
        self.dead_letters = DeadLetterQueue()
        self.error_logger = CentralErrorLogger("payroll-service")
        self.idempotency = IdempotencyStore()
        self.observability = Observability("payroll-service")
        self.tenant_id = "tenant-default"
        self.event_registry = EventRegistry()
        self.notification_service = notification_service or NotificationService()
        self.workflow_service = workflow_service or WorkflowService(notification_service=self.notification_service)
        self.outbox = OutboxManager(
            service_name='payroll-service',
            tenant_id=self.tenant_id,
            db_path=shared_db_path,
            observability=self.observability,
            dead_letters=self.dead_letters,
            event_registry=self.event_registry,
        )
        self._lock = RLock()
        self.workflow_service.register_definition(
            tenant_id=self.tenant_id,
            code="payroll_disbursement_approval",
            source_service="payroll-service",
            subject_type="PayrollRecord",
            description="Centralized payroll disbursement approval workflow.",
            steps=[
                {
                    "name": "payroll-disbursement-approval",
                    "type": "approval",
                    "assignee_template": "{approver_assignee}",
                    "sla": "PT4H",
                    "escalation_assignee_template": "{escalation_assignee}",
                }
            ],
        )

    def _trace(self, trace_id: str | None = None) -> str:
        return self.observability.trace_id(trace_id)


    def _audit_payroll_mutation(self, action: str, ctx: AuthContext, entity: str, entity_id: str, before: dict[str, Any], after: dict[str, Any], *, trace_id: str | None = None) -> None:
        self.observability.logger.audit(
            action,
            trace_id=trace_id,
            actor={'id': ctx.employee_id or ctx.role.value, 'type': 'user', 'role': ctx.role.value, 'department_id': ctx.department_id},
            entity=entity,
            entity_id=entity_id,
            context={'tenant_id': self.tenant_id, 'before': before, 'after': after},
        )

    def _finalize_observation(self, operation: str, trace_id: str, started: float, success: bool, context: dict[str, Any] | None = None) -> None:
        self.observability.track(operation, trace_id=trace_id, started_at=started, success=success, context=context)

    def _emit_event(self, event_name: str, data: dict[str, Any], *, correlation_id: str, idempotency_key: str) -> None:
        self.outbox.tenant_id = self.tenant_id
        self.outbox.enqueue(
            legacy_event_name=event_name,
            data=data,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )
        self.outbox.dispatch_pending(self.events.append)

    @staticmethod
    def decode_bearer_token(authorization: str | None) -> AuthContext:
        if not authorization or not authorization.startswith("Bearer "):
            raise ServiceError("UNAUTHORIZED", "Missing bearer token", 401)
        token = authorization[7:]
        try:
            payload = json.loads(base64.urlsafe_b64decode(token + "==").decode("utf-8"))
            return AuthContext(
                role=Role(payload["role"]),
                employee_id=payload.get("employee_id"),
                department_id=payload.get("department_id"),
            )
        except Exception as exc:  # noqa: BLE001
            raise ServiceError("UNAUTHORIZED", "Invalid token", 401) from exc

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _money(value: Decimal | str | int | float | None, field: str, min_zero: bool = True) -> Decimal:
        if value is None:
            return Decimal("0.00")
        try:
            val = Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ServiceError("VALIDATION_ERROR", f"{field} must be a valid decimal amount", 422) from exc
        if min_zero and val < 0:
            raise ServiceError("VALIDATION_ERROR", f"{field} must be >= 0", 422)
        return val

    @staticmethod
    def _calc(base_salary: Decimal, allowances: Decimal, overtime_pay: Decimal, deductions: Decimal) -> tuple[Decimal, Decimal]:
        gross = (base_salary + allowances + overtime_pay).quantize(Decimal("0.01"))
        net = (gross - deductions).quantize(Decimal("0.01"))
        return gross, net

    @staticmethod
    def _coerce_date(value: str | date, field: str) -> date:
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise ServiceError("VALIDATION_ERROR", f"{field} must be a valid ISO date", 422) from exc

    @staticmethod
    def _validate_currency(value: str | None) -> str:
        currency = str(value or "USD").upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ServiceError("VALIDATION_ERROR", "currency must be a 3-letter ISO code", 422)
        return currency

    @staticmethod
    def _require_field(payload: dict[str, Any], field: str) -> Any:
        value = payload.get(field)
        if value in {None, ""}:
            raise ServiceError("VALIDATION_ERROR", f"{field} is required", 422)
        return value

    def _validate_record_fields(
        self,
        *,
        employee_id: str | None,
        pay_period_start: date,
        pay_period_end: date,
        currency: str,
        net_pay: Decimal,
    ) -> None:
        if not employee_id:
            raise ServiceError("VALIDATION_ERROR", "employee_id is required", 422)
        if self.employee_profiles and employee_id not in self.employee_profiles:
            raise ServiceError("NOT_FOUND", "Employee not found", 404)
        if pay_period_end < pay_period_start:
            raise ServiceError("VALIDATION_ERROR", "pay_period_end must be on or after pay_period_start", 422)
        if net_pay < 0:
            raise ServiceError("VALIDATION_ERROR", "net_pay must be >= 0", 422)
        self._validate_currency(currency)

    def register_employee_profile(self, employee_id: str, *, department_id: str | None = None, role_id: str | None = None, status: str = "Active") -> dict[str, Any]:
        ts = self._now()
        profile = self.employee_profiles.get(employee_id)
        if profile is None:
            profile = EmployeePayrollProfile(employee_id=employee_id, department_id=department_id, role_id=role_id, status=status, created_at=ts, updated_at=ts)
            self.employee_profiles[employee_id] = profile
        else:
            profile.department_id = department_id if department_id is not None else profile.department_id
            profile.role_id = role_id if role_id is not None else profile.role_id
            profile.status = status or profile.status
            profile.updated_at = ts
        return profile.to_dict()

    def sync_attendance_summary(self, employee_id: str, period_start: str | date, period_end: str | date, summary: dict[str, Any]) -> dict[str, Any]:
        start = self._coerce_date(period_start, "period_start")
        end = self._coerce_date(period_end, "period_end")
        key = (employee_id, start, end)
        normalized = {**summary, "employee_id": employee_id, "period_start": start.isoformat(), "period_end": end.isoformat()}
        self.attendance_summaries[key] = normalized
        if employee_id not in self.employee_profiles:
            self.register_employee_profile(employee_id)
        return normalized

    def get_employee_payroll_summary(self, employee_id: str) -> dict[str, Any]:
        profile = self.employee_profiles.get(employee_id)
        records = [record.to_dict() for record in self.records.values() if record.employee_id == employee_id]
        records.sort(key=lambda item: (item["pay_period_start"], item["payroll_record_id"]))
        return {
            "employee": profile.to_dict() if profile else {"employee_id": employee_id},
            "attendance_summaries": [
                value for (emp_id, _, _), value in sorted(self.attendance_summaries.items(), key=lambda item: (item[0][1], item[0][2])) if emp_id == employee_id
            ],
            "payroll_records": records,
            "paid_record_count": sum(1 for record in self.records.values() if record.employee_id == employee_id and record.status == PayrollStatus.PAID),
        }

    def _validate_declared_totals(self, payload: dict[str, Any], gross: Decimal, net: Decimal) -> None:
        if "gross_pay" in payload and self._money(payload["gross_pay"], "gross_pay") != gross:
            raise ServiceError("VALIDATION_ERROR", "gross_pay does not match validated calculation", 422)
        if "net_pay" in payload and self._money(payload["net_pay"], "net_pay") != net:
            raise ServiceError("VALIDATION_ERROR", "net_pay does not match validated calculation", 422)

    def _resolve_salary_structure_for_period(self, employee_id: str, period_start: date, period_end: date) -> SalaryStructure | None:
        structure_ids = self.salary_structure_index.get(employee_id, [])
        eligible: list[SalaryStructure] = []
        for structure_id in structure_ids:
            structure = self.salary_structures[structure_id]
            if structure.effective_from <= period_start and (structure.effective_to is None or structure.effective_to >= period_end):
                eligible.append(structure)
        if not eligible:
            return None
        return max(eligible, key=lambda item: (item.effective_from, item.created_at))

    def _resolve_or_create_cycle(self, payload: dict[str, Any]) -> PayrollCycle | None:
        cycle_id = payload.get("payroll_cycle_id")
        if cycle_id:
            cycle = self.payroll_cycles.get(cycle_id)
            if not cycle:
                raise ServiceError("NOT_FOUND", "Payroll cycle not found", 404)
            return cycle
        cycle_payload = payload.get("payroll_cycle")
        if cycle_payload:
            _, cycle_data = self.upsert_payroll_cycle(cycle_payload, payload.get("_authorization"))
            return self.payroll_cycles[cycle_data["payroll_cycle_id"]]
        return None

    def _resolve_or_create_salary_structure(self, payload: dict[str, Any], employee_id: str) -> SalaryStructure | None:
        structure_id = payload.get("salary_structure_id")
        if structure_id:
            structure = self.salary_structures.get(structure_id)
            if not structure:
                raise ServiceError("NOT_FOUND", "Salary structure not found", 404)
            return structure
        structure_payload = payload.get("salary_structure")
        if structure_payload:
            structure_payload = {**structure_payload, "employee_id": structure_payload.get("employee_id", employee_id)}
            _, structure_data = self.create_salary_structure(structure_payload, payload.get("_authorization"))
            return self.salary_structures[structure_data["salary_structure_id"]]
        return None

    def _build_record_from_payload(
        self,
        payload: dict[str, Any],
        *,
        salary_structure: SalaryStructure | None = None,
        payroll_cycle: PayrollCycle | None = None,
    ) -> PayrollRecord:
        employee_id = payload.get("employee_id") or (salary_structure.employee_id if salary_structure else None)
        attendance_summary = None
        pay_period_start = self._coerce_date(
            payload.get("pay_period_start") or (payroll_cycle.pay_period_start if payroll_cycle else None),
            "pay_period_start",
        )
        pay_period_end = self._coerce_date(
            payload.get("pay_period_end") or (payroll_cycle.pay_period_end if payroll_cycle else None),
            "pay_period_end",
        )

        base_salary = self._money(payload.get("base_salary", salary_structure.base_salary if salary_structure else None), "base_salary")
        allowances = self._money(payload.get("allowances", salary_structure.allowances if salary_structure else None), "allowances")
        deductions = self._money(payload.get("deductions", salary_structure.deductions if salary_structure else None), "deductions")

        if employee_id is not None:
            attendance_summary = self.attendance_summaries.get((employee_id, pay_period_start, pay_period_end))
        overtime_source = payload.get("overtime_hours")
        if overtime_source is None and attendance_summary is not None:
            overtime_source = attendance_summary.get("overtime_hours") or attendance_summary.get("overtimeHours")
        overtime_hours = self._money(overtime_source, "overtime_hours")
        default_overtime_pay = (
            (overtime_hours * salary_structure.overtime_rate).quantize(Decimal("0.01"))
            if salary_structure
            else Decimal("0.00")
        )
        overtime_pay = self._money(payload.get("overtime_pay", default_overtime_pay), "overtime_pay")
        gross, net = self._calc(base_salary, allowances, overtime_pay, deductions)
        self._validate_declared_totals(payload, gross, net)
        currency = self._validate_currency(payload.get("currency", salary_structure.currency if salary_structure else "USD"))
        self._validate_record_fields(
            employee_id=employee_id,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            currency=currency,
            net_pay=net,
        )

        if salary_structure and salary_structure.employee_id != employee_id:
            raise ServiceError("VALIDATION_ERROR", "salary_structure employee_id does not match payroll employee_id", 422)
        if salary_structure and salary_structure.currency != currency:
            raise ServiceError("VALIDATION_ERROR", "salary_structure currency does not match payroll currency", 422)
        if payroll_cycle:
            if payroll_cycle.pay_period_start != pay_period_start or payroll_cycle.pay_period_end != pay_period_end:
                raise ServiceError("VALIDATION_ERROR", "payroll_cycle period does not match payroll record period", 422)

        ts = self._now()
        return PayrollRecord(
            payroll_record_id=str(uuid4()),
            employee_id=employee_id,
            salary_structure_id=salary_structure.salary_structure_id if salary_structure else None,
            payroll_cycle_id=payroll_cycle.payroll_cycle_id if payroll_cycle else None,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            base_salary=base_salary,
            allowances=allowances,
            deductions=deductions,
            overtime_pay=overtime_pay,
            gross_pay=gross,
            net_pay=net,
            currency=currency,
            payment_date=payroll_cycle.payment_date if payroll_cycle else None,
            payment_workflow_id=None,
            status=PayrollStatus.DRAFT,
            created_at=ts,
            updated_at=ts,
        )

    @staticmethod
    def _encode_cursor(last_id: str) -> str:
        return base64.urlsafe_b64encode(json.dumps({"last_id": last_id}).encode("utf-8")).decode("utf-8").rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str | None) -> str | None:
        if not cursor:
            return None
        try:
            return json.loads(base64.urlsafe_b64decode(cursor + "==").decode("utf-8")).get("last_id")
        except (ValueError, json.JSONDecodeError) as exc:
            raise ServiceError("VALIDATION_ERROR", "cursor is invalid", 422) from exc

    @staticmethod
    def _require_admin(ctx: AuthContext) -> None:
        if ctx.role != Role.ADMIN:
            raise ServiceError("FORBIDDEN", "Insufficient permissions", 403)

    @staticmethod
    def _assert_read_scope(ctx: AuthContext, record: PayrollRecord) -> None:
        if ctx.role in {Role.ADMIN, Role.MANAGER}:
            return
        if ctx.role == Role.EMPLOYEE and ctx.employee_id == record.employee_id:
            return
        raise ServiceError("FORBIDDEN", "Insufficient permissions", 403)

    @staticmethod
    def _coerce_period(period_start: str, period_end: str) -> tuple[date, date]:
        start = date.fromisoformat(period_start)
        end = date.fromisoformat(period_end)
        if end < start:
            raise ServiceError("VALIDATION_ERROR", "period_end must be on or after period_start", 422)
        return start, end

    @staticmethod
    def _batch_lookup_key(period_start: date, period_end: date) -> tuple[date, date]:
        return period_start, period_end

    @staticmethod
    def _normalize_failure(employee_id: str | None, reason: str, dead_letter_id: str | None = None) -> dict[str, Any]:
        failure = {"employee_id": employee_id, "reason": reason}
        if dead_letter_id:
            failure["dead_letter_id"] = dead_letter_id
        return failure

    def _record_idempotent_result(self, key: str, fingerprint: str, status: int, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        self.idempotency.record(key, fingerprint, status, payload)
        return status, payload

    def _recompute_batch(self, batch: PayrollBatch) -> None:
        records = [self.records[record_id] for record_id in batch.record_ids if record_id in self.records]
        batch.processed_count = sum(1 for record in records if record.status in {PayrollStatus.PROCESSED, PayrollStatus.PAID})
        batch.paid_count = sum(1 for record in records if record.status == PayrollStatus.PAID)
        batch.failed_count = len(batch.failures)
        if batch.processed_count == 0 and batch.failed_count > 0:
            batch.status = PayrollBatchStatus.FAILED
        elif batch.record_ids and batch.paid_count == len(batch.record_ids) and batch.failed_count == 0:
            batch.status = PayrollBatchStatus.PAID
        elif batch.record_ids and batch.paid_count == len(batch.record_ids):
            batch.status = PayrollBatchStatus.PAID
        elif batch.failed_count > 0:
            batch.status = PayrollBatchStatus.PARTIAL_FAILURE if batch.processed_count > 0 else PayrollBatchStatus.FAILED
        elif batch.processed_count > 0:
            batch.status = PayrollBatchStatus.PROCESSED
        else:
            batch.status = PayrollBatchStatus.PENDING
        batch.updated_at = self._now()

    def _get_or_create_batch(self, period_start: date, period_end: date) -> PayrollBatch:
        batch_key = self._batch_lookup_key(period_start, period_end)
        batch_id = self.batch_index.get(batch_key)
        if batch_id and batch_id in self.batches:
            batch = self.batches[batch_id]
            batch.updated_at = self._now()
            return batch
        now = self._now()
        batch = PayrollBatch(
            batch_id=str(uuid4()),
            period_start=period_start,
            period_end=period_end,
            status=PayrollBatchStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        self.batches[batch.batch_id] = batch
        self.batch_index[batch_key] = batch.batch_id
        return batch

    def _attach_record_to_batch(self, batch: PayrollBatch, record_id: str) -> None:
        if record_id not in batch.record_ids:
            batch.record_ids.append(record_id)
        self.record_batches[record_id] = batch.batch_id

    def _validate_batch_consistency(self, batch: PayrollBatch) -> dict[str, Any]:
        issues: list[str] = []
        seen_ids: set[str] = set()
        for record_id in batch.record_ids:
            if record_id in seen_ids:
                issues.append(f"duplicate record reference: {record_id}")
                continue
            seen_ids.add(record_id)
            record = self.records.get(record_id)
            if record is None:
                issues.append(f"missing record reference: {record_id}")
                continue
            if record.pay_period_start != batch.period_start or record.pay_period_end != batch.period_end:
                issues.append(f"record period mismatch: {record_id}")
            if self.record_batches.get(record_id) != batch.batch_id:
                issues.append(f"record batch index mismatch: {record_id}")
        derived_processed = sum(
            1
            for record_id in batch.record_ids
            if record_id in self.records and self.records[record_id].status in {PayrollStatus.PROCESSED, PayrollStatus.PAID}
        )
        derived_paid = sum(
            1 for record_id in batch.record_ids if record_id in self.records and self.records[record_id].status == PayrollStatus.PAID
        )
        if batch.processed_count != derived_processed:
            issues.append("processed_count mismatch")
        if batch.paid_count != derived_paid:
            issues.append("paid_count mismatch")
        if batch.failed_count != len(batch.failures):
            issues.append("failed_count mismatch")
        return {
            "batch_id": batch.batch_id,
            "period_start": batch.period_start.isoformat(),
            "period_end": batch.period_end.isoformat(),
            "record_count": len(batch.record_ids),
            "processed_count": batch.processed_count,
            "paid_count": batch.paid_count,
            "failed_count": batch.failed_count,
            "consistent": len(issues) == 0,
            "issues": issues,
        }

    def upsert_payroll_cycle(self, payload: dict[str, Any], authorization: str | None, idempotency_key: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        started = perf_counter()
        try:
            ctx = self.decode_bearer_token(authorization)
            self._require_admin(ctx)
            with self._lock:
                period_start = self._coerce_date(self._require_field(payload, "pay_period_start"), "pay_period_start")
                period_end = self._coerce_date(self._require_field(payload, "pay_period_end"), "pay_period_end")
                payment_date = self._coerce_date(self._require_field(payload, "payment_date"), "payment_date")
                if period_end < period_start:
                    raise ServiceError("VALIDATION_ERROR", "pay_period_end must be on or after pay_period_start", 422)
                if payment_date < period_end:
                    raise ServiceError("VALIDATION_ERROR", "payment_date must be on or after pay_period_end", 422)

                cycle_key = (period_start, period_end)
                cycle_id = payload.get("payroll_cycle_id") or self.payroll_cycle_index.get(cycle_key)
                cycle = self.payroll_cycles.get(cycle_id) if cycle_id else None
                ts = self._now()
                if cycle:
                    cycle.name = str(payload.get("name", cycle.name))
                    cycle.payment_date = payment_date
                    cycle.status = str(payload.get("status", cycle.status))
                    cycle.updated_at = ts
                    status_code = 200
                else:
                    cycle = PayrollCycle(
                        payroll_cycle_id=str(uuid4()),
                        name=str(payload.get("name", f"{period_start.isoformat()}:{period_end.isoformat()}")),
                        pay_period_start=period_start,
                        pay_period_end=period_end,
                        payment_date=payment_date,
                        status=str(payload.get("status", "Open")),
                        created_at=ts,
                        updated_at=ts,
                    )
                    self.payroll_cycles[cycle.payroll_cycle_id] = cycle
                    self.payroll_cycle_index[cycle_key] = cycle.payroll_cycle_id
                    status_code = 201
            self._audit_payroll_mutation('payroll_cycle_upserted', ctx, 'PayrollCycle', cycle.payroll_cycle_id, {}, cycle.to_dict(), trace_id=trace)
            self._finalize_observation("upsert_payroll_cycle", trace, started, True, {"status": status_code})
            return status_code, cycle.to_dict()
        except Exception as exc:
            self.error_logger.log("upsert_payroll_cycle", exc, trace_id=trace, details={"name": payload.get("name")})
            self._finalize_observation("upsert_payroll_cycle", trace, started, False, {"name": payload.get("name")})
            raise

    def create_salary_structure(
        self,
        payload: dict[str, Any],
        authorization: str | None,
        idempotency_key: str | None = None,
        trace_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        started = perf_counter()
        try:
            ctx = self.decode_bearer_token(authorization)
            self._require_admin(ctx)
            with self._lock:
                employee_id = str(self._require_field(payload, "employee_id"))
                if employee_id not in self.employee_profiles:
                    self.register_employee_profile(employee_id)
                effective_from = self._coerce_date(self._require_field(payload, "effective_from"), "effective_from")
                effective_to_value = payload.get("effective_to")
                effective_to = self._coerce_date(effective_to_value, "effective_to") if effective_to_value else None
                if effective_to and effective_to < effective_from:
                    raise ServiceError("VALIDATION_ERROR", "effective_to must be on or after effective_from", 422)

                fingerprint = json.dumps(payload, sort_keys=True)
                replay_key = idempotency_key or f"salary-structure:{employee_id}:{effective_from.isoformat()}"
                replay = self.idempotency.replay_or_conflict(replay_key, fingerprint)
                if replay is not None:
                    self._finalize_observation("create_salary_structure", trace, started, True, {"status": replay.status_code, "replayed": True})
                    return replay.status_code, replay.payload

                ts = self._now()
                structure = SalaryStructure(
                    salary_structure_id=str(uuid4()),
                    employee_id=employee_id,
                    base_salary=self._money(payload.get("base_salary"), "base_salary"),
                    allowances=self._money(payload.get("allowances"), "allowances"),
                    deductions=self._money(payload.get("deductions"), "deductions"),
                    overtime_rate=self._money(payload.get("overtime_rate"), "overtime_rate"),
                    currency=self._validate_currency(payload.get("currency", "USD")),
                    effective_from=effective_from,
                    effective_to=effective_to,
                    created_at=ts,
                    updated_at=ts,
                )
                self.salary_structures[structure.salary_structure_id] = structure
                self.salary_structure_index.setdefault(employee_id, []).append(structure.salary_structure_id)
            self._audit_payroll_mutation('salary_structure_created', ctx, 'SalaryStructure', structure.salary_structure_id, {}, structure.to_dict(), trace_id=trace)
            self._finalize_observation("create_salary_structure", trace, started, True, {"status": 201})
            return self._record_idempotent_result(replay_key, fingerprint, 201, structure.to_dict())
        except Exception as exc:
            self.error_logger.log("create_salary_structure", exc, trace_id=trace, details={"employee_id": payload.get("employee_id")})
            self._finalize_observation("create_salary_structure", trace, started, False, {"employee_id": payload.get("employee_id")})
            raise

    def generate_payroll(
        self,
        payload: dict[str, Any],
        authorization: str | None,
        idempotency_key: str | None = None,
        trace_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return self.create_payroll_record(payload, authorization, idempotency_key=idempotency_key, trace_id=trace_id)

    def create_payroll_record(self, payload: dict[str, Any], authorization: str | None, idempotency_key: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        started = perf_counter()
        try:
            ctx = self.decode_bearer_token(authorization)
            self._require_admin(ctx)
            with self._lock:
                enriched_payload = {**payload, "_authorization": authorization}
                employee_id = enriched_payload.get("employee_id")
                if not employee_id and enriched_payload.get("salary_structure_id"):
                    salary_structure = self.salary_structures.get(str(enriched_payload["salary_structure_id"]))
                    if not salary_structure:
                        raise ServiceError("NOT_FOUND", "Salary structure not found", 404)
                    employee_id = salary_structure.employee_id
                    enriched_payload["employee_id"] = employee_id
                cycle_for_key = None
                if "pay_period_start" in enriched_payload and "pay_period_end" in enriched_payload:
                    pay_period_start = self._coerce_date(enriched_payload["pay_period_start"], "pay_period_start")
                    pay_period_end = self._coerce_date(enriched_payload["pay_period_end"], "pay_period_end")
                else:
                    cycle_for_key = self._resolve_or_create_cycle(enriched_payload)
                    if cycle_for_key is None:
                        raise ServiceError("VALIDATION_ERROR", "pay_period_start and pay_period_end are required when payroll_cycle is not provided", 422)
                    pay_period_start = cycle_for_key.pay_period_start
                    pay_period_end = cycle_for_key.pay_period_end

                key = (employee_id, pay_period_start, pay_period_end)
                fingerprint = json.dumps(payload, sort_keys=True)
                replay_key = idempotency_key or f"payroll-record:{employee_id}:{pay_period_start.isoformat()}:{pay_period_end.isoformat()}"
                replay = self.idempotency.replay_or_conflict(replay_key, fingerprint)
                if replay is not None:
                    self._finalize_observation("create_payroll_record", trace, started, True, {"status": replay.status_code, "replayed": True})
                    return replay.status_code, replay.payload

                if key in self.period_index:
                    record = self.records[self.period_index[key]]
                    self._finalize_observation("create_payroll_record", trace, started, True, {"status": 201, "replayed": True})
                    return self._record_idempotent_result(replay_key, fingerprint, 201, record.to_dict())

                if employee_id not in self.employee_profiles:
                    self.register_employee_profile(str(employee_id))
                payroll_cycle = cycle_for_key or self._resolve_or_create_cycle(enriched_payload)
                salary_structure = self._resolve_or_create_salary_structure(enriched_payload, employee_id)
                if salary_structure is None:
                    salary_structure = self._resolve_salary_structure_for_period(employee_id, pay_period_start, pay_period_end)

                record = self._build_record_from_payload(enriched_payload, salary_structure=salary_structure, payroll_cycle=payroll_cycle)
                self.records[record.payroll_record_id] = record
                self.period_index[key] = record.payroll_record_id
                emit_canonical_event(self.events, legacy_event_name="PayrollDrafted", data={"payroll_record_id": record.payroll_record_id, "at": record.created_at.isoformat()}, source="payroll-service", tenant_id=self.tenant_id, registry=self.event_registry, correlation_id=trace, idempotency_key=record.payroll_record_id)
            self._audit_payroll_mutation('payroll_record_drafted', ctx, 'PayrollRecord', record.payroll_record_id, {}, record.to_dict(), trace_id=trace)
            self._finalize_observation("create_payroll_record", trace, started, True, {"status": 201})
            return self._record_idempotent_result(replay_key, fingerprint, 201, record.to_dict())
        except Exception as exc:
            self.error_logger.log("create_payroll_record", exc, trace_id=trace, details={"employee_id": payload.get("employee_id")})
            self._finalize_observation("create_payroll_record", trace, started, False, {"employee_id": payload.get("employee_id")})
            raise

    def run_payroll(self, period_start: str, period_end: str, authorization: str | None, records: list[dict[str, Any]] | None = None, idempotency_key: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        started = perf_counter()
        try:
            ctx = self.decode_bearer_token(authorization)
            self._require_admin(ctx)
            with self._lock:
                start, end = self._coerce_period(period_start, period_end)
                fingerprint = json.dumps({"period_start": period_start, "period_end": period_end, "records": records or []}, sort_keys=True)
                replay_key = idempotency_key or f"payroll-run:{period_start}:{period_end}"
                replay = self.idempotency.replay_or_conflict(replay_key, fingerprint)
                if replay is not None:
                    self._finalize_observation("run_payroll", trace, started, True, {"status": replay.status_code, "replayed": True})
                    return replay.status_code, replay.payload

                batch = self._get_or_create_batch(start, end)
                batch.failures = []
                processed_ids: set[str] = set()

                for item in records or []:
                    if item["pay_period_start"] != period_start or item["pay_period_end"] != period_end:
                        dead_letter = self.dead_letters.push(
                            "payroll_processing",
                            "PayrollRecordRejected",
                            item,
                            "record period does not match run period",
                            trace_id=trace,
                        )
                        batch.failures.append(self._normalize_failure(item.get("employee_id"), dead_letter.reason, dead_letter.dead_letter_id))
                        continue
                    try:
                        _, created = self.create_payroll_record(item, authorization, trace_id=trace)
                        record_id = created["payroll_record_id"]
                    except (ServiceError, ValueError) as exc:
                        self.error_logger.log("run_payroll", exc, trace_id=trace, details={"employee_id": item.get("employee_id")})
                        dead_letter = self.dead_letters.push(
                            "payroll_processing",
                            "PayrollRecordFailed",
                            item,
                            str(exc),
                            trace_id=trace,
                        )
                        batch.failures.append(self._normalize_failure(item.get("employee_id"), str(exc), dead_letter.dead_letter_id))
                        continue
                    record = self.records[record_id]
                    self._attach_record_to_batch(batch, record_id)
                    if record.status == PayrollStatus.DRAFT:
                        record.status = PayrollStatus.PROCESSED
                        record.updated_at = self._now()
                        self._emit_event(
                            "PayrollProcessed",
                            {
                                "payroll_record_id": record_id,
                                "employee_id": record.employee_id,
                                "pay_period_start": record.pay_period_start.isoformat(),
                                "pay_period_end": record.pay_period_end.isoformat(),
                                "gross_pay": str(record.gross_pay),
                                "net_pay": str(record.net_pay),
                                "currency": record.currency,
                                "status": record.status.value,
                            },
                            correlation_id=trace,
                            idempotency_key=record_id,
                        )
                    if record.status in {PayrollStatus.PROCESSED, PayrollStatus.PAID}:
                        processed_ids.add(record_id)

                for record in self.records.values():
                    if record.pay_period_start == start and record.pay_period_end == end and record.status in {PayrollStatus.DRAFT, PayrollStatus.PROCESSED, PayrollStatus.PAID}:
                        self._attach_record_to_batch(batch, record.payroll_record_id)
                        if record.status == PayrollStatus.DRAFT:
                            record.status = PayrollStatus.PROCESSED
                            record.updated_at = self._now()
                            self._emit_event(
                                "PayrollProcessed",
                                {
                                    "payroll_record_id": record.payroll_record_id,
                                    "employee_id": record.employee_id,
                                    "pay_period_start": record.pay_period_start.isoformat(),
                                    "pay_period_end": record.pay_period_end.isoformat(),
                                    "gross_pay": str(record.gross_pay),
                                    "net_pay": str(record.net_pay),
                                    "currency": record.currency,
                                    "status": record.status.value,
                                },
                                correlation_id=trace,
                                idempotency_key=record.payroll_record_id,
                            )
                        if record.status in {PayrollStatus.PROCESSED, PayrollStatus.PAID}:
                            processed_ids.add(record.payroll_record_id)

                self._recompute_batch(batch)
                validation = self._validate_batch_consistency(batch)
                response = {
                    "data": {
                        "batch": batch.to_dict(),
                        "period_start": period_start,
                        "period_end": period_end,
                        "processed_count": len(processed_ids),
                        "record_ids": sorted(processed_ids),
                        "failed_count": len(batch.failures),
                        "failures": [dict(item) for item in batch.failures],
                        "consistency": validation,
                    }
                }
            self._audit_payroll_mutation('payroll_run_processed', ctx, 'PayrollRun', f'{period_start}:{period_end}', {}, {'batch': batch.to_dict(), 'period_start': period_start, 'period_end': period_end, 'processed_count': batch.processed_count, 'failed_count': batch.failed_count}, trace_id=trace)
            self._finalize_observation(
                "run_payroll",
                trace,
                started,
                True,
                {"status": 200, "processed_count": batch.processed_count, "failed_count": batch.failed_count, "batch_id": batch.batch_id},
            )
            return self._record_idempotent_result(replay_key, fingerprint, 200, response)
        except Exception as exc:
            self.error_logger.log("run_payroll", exc, trace_id=trace, details={"period_start": period_start, "period_end": period_end})
            self._finalize_observation("run_payroll", trace, started, False, {"period_start": period_start, "period_end": period_end})
            raise

    def payroll_monthly_trigger(
        self,
        run_date: str,
        authorization: str | None,
        records: list[dict[str, Any]] | None = None,
        idempotency_key: str | None = None,
        trace_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        """Trigger a monthly payroll run based on the month from run_date."""

        trigger_date = date.fromisoformat(run_date)
        period_start = trigger_date.replace(day=1)
        period_end = trigger_date.replace(day=calendar.monthrange(trigger_date.year, trigger_date.month)[1])

        status, payload = self.run_payroll(
            period_start.isoformat(),
            period_end.isoformat(),
            authorization,
            records=records,
            idempotency_key=idempotency_key or f"payroll-monthly:{run_date}",
            trace_id=trace_id,
        )
        event = {
            "type": "PayrollMonthlyTriggerExecuted",
            "run_date": trigger_date.isoformat(),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "processed_count": payload["data"]["processed_count"],
            "failed_count": payload["data"]["failed_count"],
            "at": self._now().isoformat(),
        }
        if not self.events or self.events[-1] != event:
            self._emit_event(
                "PayrollMonthlyTriggerExecuted",
                {k: v for k, v in event.items() if k != "type"},
                correlation_id=trace_id or self._trace(None),
                idempotency_key=f"monthly:{trigger_date.isoformat()}",
            )
        return status, {
            "data": {
                "trigger": "monthly",
                "run_date": trigger_date.isoformat(),
                **payload["data"],
            }
        }

    def patch_payroll_record(self, payroll_record_id: str, payload: dict[str, Any], authorization: str | None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        started = perf_counter()
        ctx = self.decode_bearer_token(authorization)
        self._require_admin(ctx)
        with self._lock:
            record = self.records.get(payroll_record_id)
            before = record.to_dict() if record else {}
            if not record:
                raise ServiceError("NOT_FOUND", "Payroll record not found", 404)
            if record.status in {PayrollStatus.PAID, PayrollStatus.CANCELLED}:
                raise ServiceError("CONFLICT", "Cannot modify paid or cancelled records", 409)

            if "allowances" in payload:
                record.allowances = self._money(payload["allowances"], "allowances")
            if "deductions" in payload:
                record.deductions = self._money(payload["deductions"], "deductions")
            if "overtime_pay" in payload:
                record.overtime_pay = self._money(payload["overtime_pay"], "overtime_pay")
            if "currency" in payload:
                record.currency = self._validate_currency(payload["currency"])
            if "payment_date" in payload and payload["payment_date"] is not None:
                record.payment_date = self._coerce_date(payload["payment_date"], "payment_date")

            record.gross_pay, record.net_pay = self._calc(record.base_salary, record.allowances, record.overtime_pay, record.deductions)
            self._validate_declared_totals(payload, record.gross_pay, record.net_pay)
            self._validate_record_fields(
                employee_id=record.employee_id,
                pay_period_start=record.pay_period_start,
                pay_period_end=record.pay_period_end,
                currency=record.currency,
                net_pay=record.net_pay,
            )
            record.updated_at = self._now()
            batch_id = self.record_batches.get(record.payroll_record_id)
            if batch_id and batch_id in self.batches:
                self._recompute_batch(self.batches[batch_id])
        self._audit_payroll_mutation('payroll_record_adjusted', ctx, 'PayrollRecord', record.payroll_record_id, before, record.to_dict(), trace_id=trace)
        self._finalize_observation("patch_payroll_record", trace, started, True, {"status": 200})
        return 200, record.to_dict()

    def update_payroll(
        self,
        payroll_record_id: str,
        payload: dict[str, Any],
        authorization: str | None,
        trace_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        return self.patch_payroll_record(payroll_record_id, payload, authorization, trace_id=trace_id)

    def mark_paid(self, payroll_record_id: str, authorization: str | None, payment_date: str | None = None, idempotency_key: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        started = perf_counter()
        ctx = self.decode_bearer_token(authorization)
        self._require_admin(ctx)
        with self._lock:
            record = self.records.get(payroll_record_id)
            before = record.to_dict() if record else {}
            if not record:
                raise ServiceError("NOT_FOUND", "Payroll record not found", 404)

            fingerprint = json.dumps({"payroll_record_id": payroll_record_id, "payment_date": payment_date}, sort_keys=True)
            replay_key = idempotency_key or f"payroll-paid:{payroll_record_id}:{payment_date or 'default'}"
            replay = self.idempotency.replay_or_conflict(replay_key, fingerprint)
            if replay is not None:
                self._finalize_observation("mark_paid", trace, started, True, {"status": replay.status_code, "replayed": True})
                return replay.status_code, replay.payload

            if record.status == PayrollStatus.PAID:
                self._finalize_observation("mark_paid", trace, started, True, {"status": 200, "replayed": True})
                return self._record_idempotent_result(replay_key, fingerprint, 200, record.to_dict())
            if record.status != PayrollStatus.PROCESSED:
                raise ServiceError("CONFLICT", "Only processed records can be marked paid", 409)

            if not record.payment_workflow_id:
                workflow = self.workflow_service.start_workflow(
                    tenant_id=self.tenant_id,
                    definition_code="payroll_disbursement_approval",
                    source_service="payroll-service",
                    subject_type="PayrollRecord",
                    subject_id=record.payroll_record_id,
                    actor_id=ctx.employee_id or ctx.role.value,
                    actor_type="user",
                    context={
                        "approver_assignee": f"role:{ctx.role.value}",
                        "escalation_assignee": "role:Admin",
                    },
                    trace_id=trace,
                )
                record.payment_workflow_id = workflow["workflow_id"]
            try:
                workflow = self.workflow_service.approve_step(
                    record.payment_workflow_id,
                    tenant_id=self.tenant_id,
                    actor_id=ctx.employee_id or ctx.role.value,
                    actor_type="user",
                    actor_role=ctx.role.value,
                    comment="Payroll disbursement approved",
                    trace_id=trace,
                )
            except WorkflowServiceError as exc:
                raise ServiceError(exc.code, exc.message, exc.status_code, exc.details) from exc
            if workflow.get("metadata", {}).get("terminal_result") != "approved":
                raise ServiceError("CONFLICT", "Workflow approval did not complete payroll disbursement", 409)

            record.payment_date = date.fromisoformat(payment_date) if payment_date else date.today()
            record.status = PayrollStatus.PAID
            record.updated_at = self._now()
            self._emit_event(
                "PayrollPaid",
                {
                    "payroll_record_id": record.payroll_record_id,
                    "employee_id": record.employee_id,
                    "payment_date": record.payment_date.isoformat() if record.payment_date else None,
                    "net_pay": str(record.net_pay),
                    "currency": record.currency,
                    "status": record.status.value,
                },
                correlation_id=trace,
                idempotency_key=record.payroll_record_id,
            )
            batch_id = self.record_batches.get(record.payroll_record_id)
            batch_payload = None
            if batch_id and batch_id in self.batches:
                batch = self.batches[batch_id]
                self._recompute_batch(batch)
                batch_payload = batch.to_dict()
        self._audit_payroll_mutation('payroll_record_paid', ctx, 'PayrollRecord', record.payroll_record_id, before, record.to_dict(), trace_id=trace)
        self._finalize_observation("mark_paid", trace, started, True, {"status": 200})
        payload = record.to_dict()
        if batch_payload is not None:
            payload["batch"] = batch_payload
        return self._record_idempotent_result(replay_key, fingerprint, 200, payload)

    def validate_batch_processing(self, batch_id: str, authorization: str | None) -> tuple[int, dict[str, Any]]:
        ctx = self.decode_bearer_token(authorization)
        self._require_admin(ctx)
        with self._lock:
            batch = self.batches.get(batch_id)
            if not batch:
                raise ServiceError("NOT_FOUND", "Payroll batch not found", 404)
            self._recompute_batch(batch)
            validation = self._validate_batch_consistency(batch)
            return 200, {"data": {"batch": batch.to_dict(), "validation": validation}}

    def validate_consistency(self, authorization: str | None) -> tuple[int, dict[str, Any]]:
        ctx = self.decode_bearer_token(authorization)
        self._require_admin(ctx)
        with self._lock:
            batch_results = []
            for batch in self.batches.values():
                self._recompute_batch(batch)
                batch_results.append(self._validate_batch_consistency(batch))
            orphan_records = sorted(record_id for record_id in self.records if record_id not in self.record_batches)
            status = "ok" if all(result["consistent"] for result in batch_results) and not orphan_records else "inconsistent"
            return 200, {
                "data": {
                    "status": status,
                    "batch_count": len(self.batches),
                    "record_count": len(self.records),
                    "orphan_record_ids": orphan_records,
                    "batches": batch_results,
                }
            }

    def replay_dead_letters(self, authorization: str | None) -> tuple[int, dict[str, Any]]:
        ctx = self.decode_bearer_token(authorization)
        self._require_admin(ctx)
        with self._lock:
            recovered = self.dead_letters.recover(
                lambda entry: entry.workflow == "payroll_processing",
                lambda entry: entry.payload.get("pay_period_start") and entry.payload.get("pay_period_end"),
            )
        return 200, {"data": {"recovered_count": len(recovered), "recovered_dead_letters": [entry.dead_letter_id for entry in recovered]}}

    def get_payroll_record(self, payroll_record_id: str, authorization: str | None) -> tuple[int, dict[str, Any]]:
        ctx = self.decode_bearer_token(authorization)
        with self._lock:
            record = self.records.get(payroll_record_id)
            before = record.to_dict() if record else {}
            if not record:
                raise ServiceError("NOT_FOUND", "Payroll record not found", 404)
            self._assert_read_scope(ctx, record)
            payload = record.to_dict()
            batch_id = self.record_batches.get(payroll_record_id)
            if batch_id and batch_id in self.batches:
                payload["batch"] = self.batches[batch_id].to_dict()
            return 200, {"data": payload}

    def list_payroll_records(
        self,
        authorization: str | None,
        employee_id: str | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
        status: str | None = None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        if limit < 1 or limit > 100:
            raise ServiceError("VALIDATION_ERROR", "limit must be between 1 and 100", 422)

        ctx = self.decode_bearer_token(authorization)
        cursor_id = self._decode_cursor(cursor)
        if status is not None and status not in {item.value for item in PayrollStatus}:
            raise ServiceError("VALIDATION_ERROR", "status is invalid", 422)

        with self._lock:
            records = sorted(self.records.values(), key=lambda r: (r.created_at, r.payroll_record_id))
            if employee_id:
                records = [record for record in records if record.employee_id == employee_id]
            if period_start:
                start = date.fromisoformat(period_start)
                records = [record for record in records if record.pay_period_start >= start]
            if period_end:
                end = date.fromisoformat(period_end)
                records = [record for record in records if record.pay_period_end <= end]
            if status:
                records = [record for record in records if record.status.value == status]

            scoped: list[PayrollRecord] = []
            for record in records:
                try:
                    self._assert_read_scope(ctx, record)
                except ServiceError:
                    continue
                scoped.append(record)

        start_index = 0
        if cursor_id:
            for idx, record in enumerate(scoped):
                if record.payroll_record_id == cursor_id:
                    start_index = idx + 1
                    break

        page_data = scoped[start_index:start_index + limit]
        has_next = start_index + limit < len(scoped)
        next_cursor = self._encode_cursor(page_data[-1].payroll_record_id) if has_next and page_data else None

        return 200, {
            "data": [record.to_dict() for record in page_data],
            "page": {
                "nextCursor": next_cursor,
                "hasNext": has_next,
                "limit": limit,
            },
        }

    def health_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self.observability.health_status(
                checks={
                    "records": len(self.records),
                    "batches": len(self.batches),
                    "dead_letters": len(self.dead_letters.entries),
                }
            )
