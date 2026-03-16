from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import uuid4


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
        val = Decimal(str(value)).quantize(Decimal("0.01"))
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
        return json.loads(base64.urlsafe_b64decode(cursor + "==").decode("utf-8")).get("last_id")

    @staticmethod
    def _require_admin(ctx: AuthContext) -> None:
        if ctx.role != Role.ADMIN:
            raise ServiceError("FORBIDDEN", "Insufficient permissions", 403)

    @staticmethod
    def _assert_read_scope(ctx: AuthContext, record: PayrollRecord) -> None:
        if ctx.role == Role.ADMIN:
            return
        if ctx.role == Role.EMPLOYEE and ctx.employee_id == record.employee_id:
            return
        raise ServiceError("FORBIDDEN", "Insufficient permissions", 403)

    def create_payroll_record(self, payload: dict[str, Any], authorization: str | None) -> tuple[int, dict[str, Any]]:
        ctx = self.decode_bearer_token(authorization)
        self._require_admin(ctx)

        employee_id = payload.get("employee_id")
        pay_period_start = date.fromisoformat(payload["pay_period_start"])
        pay_period_end = date.fromisoformat(payload["pay_period_end"])
        if pay_period_end < pay_period_start:
            raise ServiceError("VALIDATION_ERROR", "pay_period_end must be on or after pay_period_start", 422)

        key = (employee_id, pay_period_start, pay_period_end)
        if key in self.period_index:
            raise ServiceError("CONFLICT", "Payroll record for employee and period already exists", 409)

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
        return 201, record.to_dict()

    def run_payroll(self, period_start: str, period_end: str, authorization: str | None, records: list[dict[str, Any]] | None = None) -> tuple[int, dict[str, Any]]:
        ctx = self.decode_bearer_token(authorization)
        self._require_admin(ctx)

        start = date.fromisoformat(period_start)
        end = date.fromisoformat(period_end)
        if end < start:
            raise ServiceError("VALIDATION_ERROR", "period_end must be on or after period_start", 422)

        processed_ids: set[str] = set()
        for item in records or []:
            if item["pay_period_start"] != period_start or item["pay_period_end"] != period_end:
                raise ServiceError("VALIDATION_ERROR", "All provided records must match query period", 422)
            try:
                _, created = self.create_payroll_record(item, authorization)
                record_id = created["payroll_record_id"]
            except ServiceError as exc:
                if exc.status == 409:
                    key = (item["employee_id"], start, end)
                    record_id = self.period_index[key]
                else:
                    raise
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

        return 200, {
            "data": {
                "period_start": period_start,
                "period_end": period_end,
                "processed_count": len(processed_ids),
                "record_ids": sorted(processed_ids),
            }
        }

    def patch_payroll_record(self, payroll_record_id: str, payload: dict[str, Any], authorization: str | None) -> tuple[int, dict[str, Any]]:
        ctx = self.decode_bearer_token(authorization)
        self._require_admin(ctx)
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
        return 200, record.to_dict()

    def mark_paid(self, payroll_record_id: str, authorization: str | None, payment_date: str | None = None) -> tuple[int, dict[str, Any]]:
        ctx = self.decode_bearer_token(authorization)
        self._require_admin(ctx)
        record = self.records.get(payroll_record_id)
        if not record:
            raise ServiceError("NOT_FOUND", "Payroll record not found", 404)
        if record.status != PayrollStatus.PROCESSED:
            raise ServiceError("CONFLICT", "Only processed records can be marked paid", 409)

        record.payment_date = date.fromisoformat(payment_date) if payment_date else date.today()
        record.status = PayrollStatus.PAID
        record.updated_at = self._now()
        self.events.append({"type": "PayrollPaid", "payroll_record_id": record.payroll_record_id, "at": record.updated_at.isoformat()})
        return 200, record.to_dict()

    def get_payroll_record(self, payroll_record_id: str, authorization: str | None) -> tuple[int, dict[str, Any]]:
        ctx = self.decode_bearer_token(authorization)
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
        records = sorted(self.records.values(), key=lambda r: (r.created_at, r.payroll_record_id))

        if ctx.role == Role.EMPLOYEE:
            records = [r for r in records if r.employee_id == ctx.employee_id]
        if employee_id:
            records = [r for r in records if r.employee_id == employee_id]
        if period_start:
            d = date.fromisoformat(period_start)
            records = [r for r in records if r.pay_period_start >= d]
        if period_end:
            d = date.fromisoformat(period_end)
            records = [r for r in records if r.pay_period_end <= d]
        if status:
            s = PayrollStatus(status)
            records = [r for r in records if r.status == s]

        cursor_id = self._decode_cursor(cursor)
        start_idx = 0
        if cursor_id:
            for idx, record in enumerate(records):
                if record.payroll_record_id == cursor_id:
                    start_idx = idx + 1
                    break

        page_data = records[start_idx : start_idx + limit]
        has_next = start_idx + limit < len(records)
        next_cursor = self._encode_cursor(page_data[-1].payroll_record_id) if has_next and page_data else None
        return 200, {
            "data": [r.to_dict() for r in page_data],
            "page": {"nextCursor": next_cursor, "hasNext": has_next, "limit": limit},
        }
