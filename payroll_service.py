from __future__ import annotations

import base64
import calendar
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from threading import RLock
from time import perf_counter
from typing import Any
from uuid import uuid4

from resilience import CentralErrorLogger, DeadLetterQueue, IdempotencyStore, Observability


class Role(str, Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    EMPLOYEE = "Employee"


class PayrollStatus(str, Enum):
    DRAFT = "Draft"
    PROCESSED = "Processed"
    PAID = "Paid"
    CANCELLED = "Cancelled"


@dataclass(frozen=True)
class AuthContext:
    role: Role
    employee_id: str | None = None
    department_id: str | None = None


@dataclass
class PayrollRecord:
    payroll_record_id: str
    employee_id: str
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
    status: PayrollStatus
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "payroll_record_id": self.payroll_record_id,
            "employee_id": self.employee_id,
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
            "status": self.status.value,
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
                "traceId": trace_id or uuid4().hex,
            }
        }


class PayrollService:
    """Canonical payroll-service business logic and API-compatible handlers."""

    def __init__(self):
        self.records: dict[str, PayrollRecord] = {}
        self.period_index: dict[tuple[str, date, date], str] = {}
        self.events: list[dict[str, Any]] = []
        self.dead_letters = DeadLetterQueue()
        self.error_logger = CentralErrorLogger("payroll-service")
        self.idempotency = IdempotencyStore()
        self.observability = Observability("payroll-service")
        self._lock = RLock()

    def _trace(self, trace_id: str | None = None) -> str:
        return self.observability.trace_id(trace_id)

    def _finalize_observation(self, operation: str, trace_id: str, started: float, success: bool, context: dict[str, Any] | None = None) -> None:
        self.observability.track(operation, trace_id=trace_id, started_at=started, success=success, context=context)

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

    def _key(self, payload: dict[str, Any]) -> tuple[str, date, date]:
        return (payload.get("employee_id"), date.fromisoformat(payload["pay_period_start"]), date.fromisoformat(payload["pay_period_end"]))

    def _record_idempotent_result(self, key: str, fingerprint: str, status: int, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        self.idempotency.record(key, fingerprint, status, payload)
        return status, payload

    def create_payroll_record(self, payload: dict[str, Any], authorization: str | None, idempotency_key: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        started = perf_counter()
        try:
            ctx = self.decode_bearer_token(authorization)
            self._require_admin(ctx)
            with self._lock:
                employee_id = payload.get("employee_id")
                pay_period_start = date.fromisoformat(payload["pay_period_start"])
                pay_period_end = date.fromisoformat(payload["pay_period_end"])
                if pay_period_end < pay_period_start:
                    raise ServiceError("VALIDATION_ERROR", "pay_period_end must be on or after pay_period_start", 422)

                key = (employee_id, pay_period_start, pay_period_end)
                fingerprint = json.dumps(payload, sort_keys=True)
                replay_key = idempotency_key or f"payroll-record:{employee_id}:{pay_period_start.isoformat()}:{pay_period_end.isoformat()}"
                replay = self.idempotency.replay_or_conflict(replay_key, fingerprint)
                if replay is not None:
                    self._finalize_observation("create_payroll_record", trace, started, True, {"status": replay.status_code, "replayed": True})
                    return replay.status_code, replay.payload

                if key in self.period_index:
                    record = self.records[self.period_index[key]]
                    self._finalize_observation("create_payroll_record", trace, started, True, {"status": 200, "replayed": True})
                    return self._record_idempotent_result(replay_key, fingerprint, 200, record.to_dict())

                base_salary = self._money(payload.get("base_salary"), "base_salary")
                allowances = self._money(payload.get("allowances"), "allowances")
                deductions = self._money(payload.get("deductions"), "deductions")
                overtime_pay = self._money(payload.get("overtime_pay"), "overtime_pay")
                gross, net = self._calc(base_salary, allowances, overtime_pay, deductions)
                ts = self._now()
                record = PayrollRecord(
                    payroll_record_id=str(uuid4()),
                    employee_id=employee_id,
                    pay_period_start=pay_period_start,
                    pay_period_end=pay_period_end,
                    base_salary=base_salary,
                    allowances=allowances,
                    deductions=deductions,
                    overtime_pay=overtime_pay,
                    gross_pay=gross,
                    net_pay=net,
                    currency=str(payload.get("currency", "USD")).upper(),
                    payment_date=None,
                    status=PayrollStatus.DRAFT,
                    created_at=ts,
                    updated_at=ts,
                )
                self.records[record.payroll_record_id] = record
                self.period_index[key] = record.payroll_record_id
                self.events.append({"type": "PayrollDrafted", "payroll_record_id": record.payroll_record_id, "at": ts.isoformat()})
            self.observability.logger.audit(
                "payroll_record_drafted",
                trace_id=trace,
                actor=ctx.employee_id or ctx.role.value,
                entity="PayrollRecord",
                entity_id=record.payroll_record_id,
                context={"employee_id": employee_id, "status": record.status.value},
            )
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
                start = date.fromisoformat(period_start)
                end = date.fromisoformat(period_end)
                if end < start:
                    raise ServiceError("VALIDATION_ERROR", "period_end must be on or after period_start", 422)

                fingerprint = json.dumps({"period_start": period_start, "period_end": period_end, "records": records or []}, sort_keys=True)
                replay_key = idempotency_key or f"payroll-run:{period_start}:{period_end}"
                replay = self.idempotency.replay_or_conflict(replay_key, fingerprint)
                if replay is not None:
                    self._finalize_observation("run_payroll", trace, started, True, {"status": replay.status_code, "replayed": True})
                    return replay.status_code, replay.payload

                processed_ids: set[str] = set()
                failures: list[dict[str, Any]] = []
                for item in records or []:
                    if item["pay_period_start"] != period_start or item["pay_period_end"] != period_end:
                        dead_letter = self.dead_letters.push("payroll_processing", "PayrollRecordRejected", item, "record period does not match run period")
                        failures.append({"employee_id": item.get("employee_id"), "dead_letter_id": dead_letter.dead_letter_id, "reason": dead_letter.reason})
                        continue
                    try:
                        _, created = self.create_payroll_record(item, authorization, trace_id=trace)
                        record_id = created["payroll_record_id"]
                    except ServiceError as exc:
                        self.error_logger.log("run_payroll", exc, trace_id=trace, details={"employee_id": item.get("employee_id")})
                        dead_letter = self.dead_letters.push("payroll_processing", "PayrollRecordFailed", item, exc.message)
                        failures.append({"employee_id": item.get("employee_id"), "dead_letter_id": dead_letter.dead_letter_id, "reason": exc.message})
                        continue
                    record = self.records[record_id]
                    if record.status != PayrollStatus.PAID:
                        record.status = PayrollStatus.PROCESSED
                        record.updated_at = self._now()
                        processed_ids.add(record_id)
                        self.events.append({"type": "PayrollProcessed", "payroll_record_id": record_id, "at": record.updated_at.isoformat()})

                for record in self.records.values():
                    if record.pay_period_start == start and record.pay_period_end == end and record.status == PayrollStatus.DRAFT:
                        record.status = PayrollStatus.PROCESSED
                        record.updated_at = self._now()
                        processed_ids.add(record.payroll_record_id)
                        self.events.append({"type": "PayrollProcessed", "payroll_record_id": record.payroll_record_id, "at": record.updated_at.isoformat()})

                response = {
                    "data": {
                        "period_start": period_start,
                        "period_end": period_end,
                        "processed_count": len(processed_ids),
                        "record_ids": sorted(processed_ids),
                        "failed_count": len(failures),
                        "failures": failures,
                    }
                }
            self.observability.logger.audit(
                "payroll_run_processed",
                trace_id=trace,
                actor=ctx.employee_id or ctx.role.value,
                entity="PayrollRun",
                entity_id=f"{period_start}:{period_end}",
                context={"processed_count": len(processed_ids), "failed_count": len(failures)},
            )
            self._finalize_observation("run_payroll", trace, started, True, {"status": 200, "processed_count": len(processed_ids), "failed_count": len(failures)})
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
            self.events.append(event)
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

            record.gross_pay, record.net_pay = self._calc(record.base_salary, record.allowances, record.overtime_pay, record.deductions)
            record.updated_at = self._now()
        self.observability.logger.audit(
            "payroll_record_adjusted",
            trace_id=trace,
            actor=ctx.employee_id or ctx.role.value,
            entity="PayrollRecord",
            entity_id=record.payroll_record_id,
            context={"fields": sorted(payload.keys())},
        )
        self._finalize_observation("patch_payroll_record", trace, started, True, {"status": 200})
        return 200, record.to_dict()

    def mark_paid(self, payroll_record_id: str, authorization: str | None, payment_date: str | None = None, idempotency_key: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        started = perf_counter()
        ctx = self.decode_bearer_token(authorization)
        self._require_admin(ctx)
        with self._lock:
            record = self.records.get(payroll_record_id)
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

            record.payment_date = date.fromisoformat(payment_date) if payment_date else date.today()
            record.status = PayrollStatus.PAID
            record.updated_at = self._now()
            self.events.append({"type": "PayrollPaid", "payroll_record_id": record.payroll_record_id, "at": record.updated_at.isoformat()})
        self.observability.logger.audit(
            "payroll_record_paid",
            trace_id=trace,
            actor=ctx.employee_id or ctx.role.value,
            entity="PayrollRecord",
            entity_id=record.payroll_record_id,
            context={"payment_date": record.payment_date.isoformat()},
        )
        self._finalize_observation("mark_paid", trace, started, True, {"status": 200})
        return self._record_idempotent_result(replay_key, fingerprint, 200, record.to_dict())

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
            if not record:
                raise ServiceError("NOT_FOUND", "Payroll record not found", 404)
            self._assert_read_scope(ctx, record)
            return 200, {"data": record.to_dict()}

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
                    "dead_letters": len(self.dead_letters.entries),
                }
            )
