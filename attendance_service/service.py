from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Iterable, List, Optional
from uuid import UUID

from attendance_service.models import (
    AttendanceRecord,
    AttendanceSource,
    AttendanceStatus,
    RecordState,
)


class AttendanceServiceError(Exception):
    def __init__(self, code: str, message: str, details: Optional[list] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


@dataclass(frozen=True)
class Actor:
    employee_id: Optional[UUID]
    role: str
    department_id: Optional[UUID] = None


@dataclass(frozen=True)
class EmployeeSnapshot:
    employee_id: UUID
    status: str
    department_id: UUID
    manager_employee_id: Optional[UUID] = None


class EmployeeDirectory:
    """Minimal dependency contract from employee-service."""

    def get(self, employee_id: UUID) -> EmployeeSnapshot:  # pragma: no cover - interface contract
        raise NotImplementedError


class InMemoryEmployeeDirectory(EmployeeDirectory):
    def __init__(self, employees: Iterable[EmployeeSnapshot]):
        self._employees = {employee.employee_id: employee for employee in employees}

    def get(self, employee_id: UUID) -> EmployeeSnapshot:
        employee = self._employees.get(employee_id)
        if not employee:
            raise AttendanceServiceError("EMPLOYEE_NOT_FOUND", "Employee does not exist")
        return employee


class AttendanceService:
    def __init__(self, employee_directory: EmployeeDirectory):
        self._employee_directory = employee_directory
        self._records: Dict[UUID, AttendanceRecord] = {}
        self._employee_date_index: Dict[tuple[UUID, date], UUID] = {}
        self.events: List[dict] = []

    def create_record(
        self,
        actor: Actor,
        *,
        employee_id: UUID,
        attendance_date: date,
        attendance_status: AttendanceStatus,
        source: Optional[AttendanceSource] = None,
        check_in_time: Optional[datetime] = None,
        check_out_time: Optional[datetime] = None,
    ) -> AttendanceRecord:
        self._authorize_capture(actor, employee_id)
        employee = self._employee_directory.get(employee_id)
        if employee.status not in {"Active", "OnLeave"}:
            raise AttendanceServiceError(
                "EMPLOYEE_STATUS_INVALID",
                "Attendance can only be captured for active or on-leave employees",
            )

        key = (employee_id, attendance_date)
        if key in self._employee_date_index:
            raise AttendanceServiceError(
                "ATTENDANCE_DUPLICATE",
                "Attendance record already exists for employee/date",
                [{"field": "attendance_date", "reason": "duplicate for employee"}],
            )

        record = AttendanceRecord(
            employee_id=employee_id,
            attendance_date=attendance_date,
            attendance_status=attendance_status,
            source=source,
            check_in_time=check_in_time,
            check_out_time=check_out_time,
        )
        record.recalculate_total_hours()

        self._records[record.attendance_id] = record
        self._employee_date_index[key] = record.attendance_id
        self.events.append(
            {
                "type": "AttendanceCaptured",
                "attendance_id": str(record.attendance_id),
                "employee_id": str(record.employee_id),
                "attendance_date": record.attendance_date.isoformat(),
            }
        )

        self._auto_validate(record)
        return record

    def update_record(
        self,
        actor: Actor,
        attendance_id: UUID,
        *,
        attendance_status: Optional[AttendanceStatus] = None,
        check_in_time: Optional[datetime] = None,
        check_out_time: Optional[datetime] = None,
    ) -> AttendanceRecord:
        record = self._get_record(attendance_id)
        self._authorize_capture(actor, record.employee_id)

        if record.lifecycle_state == RecordState.LOCKED:
            raise AttendanceServiceError("ATTENDANCE_LOCKED", "Locked records cannot be modified")

        if attendance_status:
            record.attendance_status = attendance_status
        if check_in_time is not None:
            record.check_in_time = check_in_time
        if check_out_time is not None:
            record.check_out_time = check_out_time
        record.recalculate_total_hours()
        record.lifecycle_state = RecordState.CAPTURED
        self._auto_validate(record)
        return record

    def approve_record(self, actor: Actor, attendance_id: UUID) -> AttendanceRecord:
        record = self._get_record(attendance_id)
        self._authorize_validate_and_lock(actor, record.employee_id)
        if record.lifecycle_state == RecordState.LOCKED:
            raise AttendanceServiceError("ATTENDANCE_LOCKED", "Locked records cannot be approved")
        if record.lifecycle_state == RecordState.CAPTURED:
            self._auto_validate(record)
        record.lifecycle_state = RecordState.APPROVED
        record.updated_at = datetime.utcnow()
        self.events.append({"type": "AttendanceApproved", "attendance_id": str(record.attendance_id)})
        return record

    def get_record(self, actor: Actor, attendance_id: UUID) -> AttendanceRecord:
        record = self._get_record(attendance_id)
        self._authorize_read(actor, record.employee_id)
        return record

    def list_records(
        self,
        actor: Actor,
        *,
        employee_id: UUID,
        from_date: date,
        to_date: date,
    ) -> list[AttendanceRecord]:
        self._authorize_read(actor, employee_id)
        if to_date < from_date:
            raise AttendanceServiceError("DATE_RANGE_INVALID", "to must be >= from")

        results = [
            record
            for record in self._records.values()
            if record.employee_id == employee_id and from_date <= record.attendance_date <= to_date
        ]
        return sorted(results, key=lambda x: x.attendance_date)

    def lock_period(self, actor: Actor, *, period_id: str, from_date: date, to_date: date) -> dict:
        self._authorize_period_lock(actor)
        if to_date < from_date:
            raise AttendanceServiceError("DATE_RANGE_INVALID", "to must be >= from")

        locked_ids: list[str] = []
        for record in self._records.values():
            if from_date <= record.attendance_date <= to_date:
                if record.lifecycle_state not in {RecordState.APPROVED, RecordState.LOCKED}:
                    raise AttendanceServiceError(
                        "LOCK_REQUIRES_APPROVAL",
                        "All records in range must be approved before lock",
                    )
                record.lifecycle_state = RecordState.LOCKED
                record.updated_at = datetime.utcnow()
                locked_ids.append(str(record.attendance_id))

        self.events.append({"type": "AttendanceLocked", "period_id": period_id, "record_ids": locked_ids})
        self.events.append(
            {
                "type": "AttendancePeriodClosed",
                "period_id": period_id,
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
            }
        )
        return {"periodId": period_id, "lockedCount": len(locked_ids)}

    def get_summary(self, actor: Actor, *, employee_id: UUID, period_start: date, period_end: date) -> dict:
        self._authorize_read(actor, employee_id)
        rows = self.list_records(actor, employee_id=employee_id, from_date=period_start, to_date=period_end)
        total_hours = sum((record.total_hours or Decimal("0")) for record in rows)
        by_status: dict[str, int] = {}
        for record in rows:
            by_status[record.attendance_status.value] = by_status.get(record.attendance_status.value, 0) + 1
        return {
            "employeeId": str(employee_id),
            "periodStart": period_start.isoformat(),
            "periodEnd": period_end.isoformat(),
            "totalHours": str(total_hours.quantize(Decimal("0.01"))),
            "statusBreakdown": by_status,
            "records": len(rows),
        }

    def _get_record(self, attendance_id: UUID) -> AttendanceRecord:
        record = self._records.get(attendance_id)
        if not record:
            raise AttendanceServiceError("ATTENDANCE_NOT_FOUND", "Attendance record not found")
        return record

    def _auto_validate(self, record: AttendanceRecord) -> None:
        if (
            record.attendance_status in {AttendanceStatus.ABSENT, AttendanceStatus.HOLIDAY}
            or record.total_hours is not None
        ):
            record.lifecycle_state = RecordState.VALIDATED
            record.updated_at = datetime.utcnow()
            self.events.append({"type": "AttendanceValidated", "attendance_id": str(record.attendance_id)})

    def _authorize_capture(self, actor: Actor, target_employee_id: UUID) -> None:
        if actor.role == "Admin":
            return
        if actor.role == "Employee" and actor.employee_id == target_employee_id:
            return
        if actor.role == "Manager":
            target = self._employee_directory.get(target_employee_id)
            if actor.department_id and actor.department_id == target.department_id:
                return
        raise AttendanceServiceError("FORBIDDEN", "Not allowed to capture attendance for target employee")

    def _authorize_validate_and_lock(self, actor: Actor, target_employee_id: UUID) -> None:
        if actor.role == "Admin":
            return
        if actor.role == "Manager":
            target = self._employee_directory.get(target_employee_id)
            if actor.department_id and actor.department_id == target.department_id:
                return
        raise AttendanceServiceError("FORBIDDEN", "Not allowed to validate/lock attendance")

    def _authorize_read(self, actor: Actor, target_employee_id: UUID) -> None:
        if actor.role == "Admin":
            return
        if actor.role == "Employee" and actor.employee_id == target_employee_id:
            return
        if actor.role == "Manager":
            target = self._employee_directory.get(target_employee_id)
            if actor.department_id and actor.department_id == target.department_id:
                return
        raise AttendanceServiceError("FORBIDDEN", "Not allowed to read attendance for target employee")

    def _authorize_period_lock(self, actor: Actor) -> None:
        if actor.role in {"Admin", "Manager"}:
            return
        raise AttendanceServiceError("FORBIDDEN", "Not allowed to lock attendance periods")
