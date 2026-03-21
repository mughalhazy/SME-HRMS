from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from typing import Dict, Iterable, List, Optional
from uuid import UUID

from attendance_service.models import (
    AttendanceAnomaly,
    AttendanceLogEvent,
    AttendanceRecord,
    AttendanceSource,
    AttendanceStatus,
    RecordState,
)
from event_contract import EventRegistry, emit_canonical_event
from persistent_store import PersistentKVStore
from resilience import Observability


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
    def __init__(self, employee_directory: EmployeeDirectory, *, late_after: time = time(9, 15), db_path: str | None = None):
        self._employee_directory = employee_directory
        self._records = PersistentKVStore[UUID, AttendanceRecord](service='attendance-service', namespace='records', db_path=db_path)
        self._employee_date_index = PersistentKVStore[tuple[UUID, date], UUID](service='attendance-service', namespace='employee_date_index', db_path=db_path)
        self.events: List[dict] = []
        self.observability = Observability("attendance-service")
        self._late_after = late_after
        self.tenant_id = "tenant-default"
        self.event_registry = EventRegistry()

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
        correction_note: Optional[str] = None,
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
            correction_note=correction_note,
        )
        self._normalize_record(record)

        self._records[record.attendance_id] = record
        self._employee_date_index[key] = record.attendance_id
        emit_canonical_event(self.events, legacy_event_name="AttendanceCaptured", data={"attendance_id": str(record.attendance_id), "employee_id": str(record.employee_id), "attendance_date": record.attendance_date.isoformat()}, source="attendance-service", tenant_id=self.tenant_id, registry=self.event_registry, idempotency_key=str(record.attendance_id))
        self.observability.logger.info(
            "attendance.captured",
            context={"employee_id": str(record.employee_id), "attendance_id": str(record.attendance_id)},
        )

        self._auto_validate(record)
        return record

    def log_attendance(
        self,
        actor: Actor,
        *,
        employee_id: UUID,
        event_type: AttendanceLogEvent,
        occurred_at: datetime,
        source: Optional[AttendanceSource] = None,
    ) -> AttendanceRecord:
        self._authorize_capture(actor, employee_id)
        attendance_date = occurred_at.date()
        key = (employee_id, attendance_date)
        attendance_id = self._employee_date_index.get(key)

        if attendance_id is None:
            record = self.create_record(
                actor,
                employee_id=employee_id,
                attendance_date=attendance_date,
                attendance_status=AttendanceStatus.PRESENT,
                source=source,
                check_in_time=occurred_at if event_type == AttendanceLogEvent.CHECK_IN else None,
                check_out_time=occurred_at if event_type == AttendanceLogEvent.CHECK_OUT else None,
            )
        else:
            record = self._get_record(attendance_id)
            if record.lifecycle_state == RecordState.LOCKED:
                raise AttendanceServiceError("ATTENDANCE_LOCKED", "Locked records cannot be modified")
            if source is not None:
                record.source = source
            if event_type == AttendanceLogEvent.CHECK_IN:
                if record.check_in_time and occurred_at > record.check_in_time:
                    raise AttendanceServiceError("TIME_LOGIC_INVALID", "check-in cannot move later than existing check-in")
                record.check_in_time = occurred_at
            if event_type == AttendanceLogEvent.CHECK_OUT:
                if record.check_out_time and occurred_at < record.check_out_time:
                    raise AttendanceServiceError("TIME_LOGIC_INVALID", "check-out cannot move earlier than existing check-out")
                record.check_out_time = occurred_at
            self._normalize_record(record)
            record.lifecycle_state = RecordState.CAPTURED
            self._auto_validate(record)

        emit_canonical_event(self.events, legacy_event_name="AttendanceLogged", data={"attendance_id": str(record.attendance_id), "employee_id": str(record.employee_id), "event_type": event_type.value, "occurred_at": occurred_at.isoformat()}, source="attendance-service", tenant_id=self.tenant_id, registry=self.event_registry, idempotency_key=f"{record.attendance_id}:{event_type.value}:{occurred_at.isoformat()}")
        self.observability.logger.info(
            "attendance.logged",
            context={
                "employee_id": str(record.employee_id),
                "attendance_id": str(record.attendance_id),
                "event_type": event_type.value,
            },
        )
        return record

    def update_record(
        self,
        actor: Actor,
        attendance_id: UUID,
        *,
        attendance_status: Optional[AttendanceStatus] = None,
        check_in_time: Optional[datetime] = None,
        check_out_time: Optional[datetime] = None,
        correction_note: Optional[str] = None,
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
        if correction_note is not None:
            record.correction_note = correction_note
        self._normalize_record(record)
        record.lifecycle_state = RecordState.CAPTURED
        self._auto_validate(record)
        emit_canonical_event(self.events, legacy_event_name="AttendanceCorrected", data={"attendance_id": str(record.attendance_id), "employee_id": str(record.employee_id)}, source="attendance-service", tenant_id=self.tenant_id, registry=self.event_registry, idempotency_key=str(record.attendance_id))
        self.observability.logger.info(
            "attendance.updated",
            context={"employee_id": str(record.employee_id), "attendance_id": str(record.attendance_id)},
        )
        return record

    def approve_record(self, actor: Actor, attendance_id: UUID) -> AttendanceRecord:
        record = self._get_record(attendance_id)
        self._authorize_validate_and_lock(actor, record.employee_id)
        if record.lifecycle_state == RecordState.LOCKED:
            raise AttendanceServiceError("ATTENDANCE_LOCKED", "Locked records cannot be approved")
        if record.lifecycle_state == RecordState.CAPTURED:
            self._auto_validate(record)
        if record.lifecycle_state != RecordState.VALIDATED:
            raise AttendanceServiceError(
                "APPROVAL_REQUIRES_VALIDATED",
                "Only validated attendance records can be approved.",
                [{"attendance_id": str(record.attendance_id), "lifecycle_state": record.lifecycle_state.value}],
            )
        record.lifecycle_state = RecordState.APPROVED
        record.updated_at = datetime.utcnow()
        emit_canonical_event(self.events, legacy_event_name="AttendanceApproved", data={"attendance_id": str(record.attendance_id)}, source="attendance-service", tenant_id=self.tenant_id, registry=self.event_registry, idempotency_key=str(record.attendance_id))
        self.observability.logger.info(
            "attendance.approved",
            context={"employee_id": str(record.employee_id), "attendance_id": str(record.attendance_id)},
        )
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

    def aggregate_period(self, actor: Actor, *, employee_id: UUID, from_date: date, to_date: date) -> dict:
        rows = self.list_records(actor, employee_id=employee_id, from_date=from_date, to_date=to_date)
        total_hours = sum((record.total_hours or Decimal("0")) for record in rows)
        status_breakdown: dict[str, int] = {}
        anomaly_breakdown: dict[str, int] = {}
        for record in rows:
            status_breakdown[record.attendance_status.value] = status_breakdown.get(record.attendance_status.value, 0) + 1
            for anomaly in record.anomalies:
                anomaly_breakdown[anomaly.value] = anomaly_breakdown.get(anomaly.value, 0) + 1
        return {
            "employeeId": str(employee_id),
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "records": len(rows),
            "totalHours": str(total_hours.quantize(Decimal("0.01"))),
            "statusBreakdown": status_breakdown,
            "anomalyBreakdown": anomaly_breakdown,
            "anomalousRecords": sum(1 for row in rows if row.anomalies),
            "completeRecords": sum(1 for row in rows if not row.anomalies),
        }

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

        emit_canonical_event(self.events, legacy_event_name="AttendanceLocked", data={"period_id": period_id, "record_ids": locked_ids}, source="attendance-service", tenant_id=self.tenant_id, registry=self.event_registry, idempotency_key=period_id)
        emit_canonical_event(self.events, legacy_event_name="AttendancePeriodClosed", data={
                "period_id": period_id,
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
            }, source="attendance-service", tenant_id=self.tenant_id, registry=self.event_registry, idempotency_key=period_id)
        self.observability.logger.info(
            "attendance.period_locked",
            context={"period_id": period_id, "locked_count": len(locked_ids)},
        )
        return {"periodId": period_id, "lockedCount": len(locked_ids)}

    def sync_approved_leave(
        self,
        actor: Actor,
        *,
        employee_id: UUID,
        from_date: date,
        to_date: date,
        leave_request_id: str,
        leave_type: str,
    ) -> list[AttendanceRecord]:
        self._authorize_validate_and_lock(actor, employee_id)
        if to_date < from_date:
            raise AttendanceServiceError("DATE_RANGE_INVALID", "from_date must be on or before to_date")

        records: list[AttendanceRecord] = []
        current = from_date
        while current <= to_date:
            key = (employee_id, current)
            attendance_id = self._employee_date_index.get(key)
            if attendance_id is None:
                record = self.create_record(
                    actor,
                    employee_id=employee_id,
                    attendance_date=current,
                    attendance_status=AttendanceStatus.ABSENT,
                    source=AttendanceSource.API_IMPORT,
                    correction_note=f"Approved leave: {leave_type} ({leave_request_id})",
                )
            else:
                record = self._get_record(attendance_id)
                if record.attendance_status in {AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY} and record.total_hours:
                    raise AttendanceServiceError(
                        "ATTENDANCE_CONFLICT",
                        "Cannot mark approved leave on a worked attendance date",
                        [{"attendance_id": str(record.attendance_id), "attendance_date": current.isoformat()}],
                    )
                record.attendance_status = AttendanceStatus.ABSENT
                record.source = AttendanceSource.API_IMPORT
                record.check_in_time = None
                record.check_out_time = None
                record.correction_note = f"Approved leave: {leave_type} ({leave_request_id})"
                self._normalize_record(record)
                record.lifecycle_state = RecordState.APPROVED
            records.append(record)
            current = date.fromordinal(current.toordinal() + 1)

        emit_canonical_event(self.events, legacy_event_name="AttendanceSyncedFromLeave", data={
                "employee_id": str(employee_id),
                "leave_request_id": leave_request_id,
                "from_date": from_date.isoformat(),
                "to_date": to_date.isoformat(),
            }, source="attendance-service", tenant_id=self.tenant_id, registry=self.event_registry, idempotency_key=leave_request_id)
        return records

    def get_employee_detail(self, actor: Actor, *, employee_id: UUID, period_start: date, period_end: date) -> dict:
        employee = self._employee_directory.get(employee_id)
        summary = self.get_summary(actor, employee_id=employee_id, period_start=period_start, period_end=period_end)
        records = self.list_records(actor, employee_id=employee_id, from_date=period_start, to_date=period_end)
        return {
            "employee": {
                "employeeId": str(employee.employee_id),
                "status": employee.status,
                "departmentId": str(employee.department_id),
                "managerEmployeeId": str(employee.manager_employee_id) if employee.manager_employee_id else None,
            },
            "summary": summary,
            "records": [self._record_payload(record) for record in records],
        }

    def get_summary(self, actor: Actor, *, employee_id: UUID, period_start: date, period_end: date) -> dict:
        summary = self.aggregate_period(actor, employee_id=employee_id, from_date=period_start, to_date=period_end)
        return {
            "employeeId": summary["employeeId"],
            "periodStart": period_start.isoformat(),
            "periodEnd": period_end.isoformat(),
            "totalHours": summary["totalHours"],
            "statusBreakdown": summary["statusBreakdown"],
            "records": summary["records"],
            "anomalyBreakdown": summary["anomalyBreakdown"],
            "anomalousRecords": summary["anomalousRecords"],
        }

    def attendance_absence_alerts(self, actor: Actor, *, attendance_date: date) -> dict:
        """Return absence alert candidates for a specific date."""

        if actor.role not in {"Admin", "Manager"}:
            raise AttendanceServiceError("FORBIDDEN", "Not allowed to generate absence alerts")

        alert_records: list[dict] = []
        for record in self._records.values():
            if record.attendance_date != attendance_date or record.attendance_status != AttendanceStatus.ABSENT:
                continue

            employee = self._employee_directory.get(record.employee_id)
            if actor.role == "Manager" and actor.department_id != employee.department_id:
                continue

            alert_records.append(
                {
                    "attendanceId": str(record.attendance_id),
                    "employeeId": str(record.employee_id),
                    "attendanceDate": record.attendance_date.isoformat(),
                    "attendanceStatus": record.attendance_status.value,
                    "managerEmployeeId": str(employee.manager_employee_id) if employee.manager_employee_id else None,
                }
            )

        emit_canonical_event(self.events, legacy_event_name="AttendanceAbsenceAlertsGenerated", data={
                "attendance_date": attendance_date.isoformat(),
                "count": len(alert_records),
            }, source="attendance-service", tenant_id=self.tenant_id, registry=self.event_registry, idempotency_key=f"absence-alerts:{attendance_date.isoformat()}")
        self.observability.logger.info(
            "attendance.absence_alerts_generated",
            context={"attendance_date": attendance_date.isoformat(), "count": len(alert_records)},
        )
        return {
            "attendanceDate": attendance_date.isoformat(),
            "alerts": alert_records,
            "count": len(alert_records),
        }

    def health_snapshot(self) -> dict:
        return self.observability.health_status(
            checks={
                "employee_directory": self._employee_directory.__class__.__name__,
                "records": len(self._records),
            }
        )

    def _get_record(self, attendance_id: UUID) -> AttendanceRecord:
        record = self._records.get(attendance_id)
        if not record:
            raise AttendanceServiceError("ATTENDANCE_NOT_FOUND", "Attendance record not found")
        return record

    def _normalize_record(self, record: AttendanceRecord) -> None:
        try:
            record.validate_time_consistency()
            record.recalculate_total_hours()
            record.derive_anomalies(late_after=self._late_after)
        except ValueError as exc:
            raise AttendanceServiceError(
                "TIME_LOGIC_INVALID",
                "Attendance time logic is invalid.",
                [{"reason": str(exc)}],
            ) from exc

    def _auto_validate(self, record: AttendanceRecord) -> None:
        if record.attendance_status in {AttendanceStatus.ABSENT, AttendanceStatus.HOLIDAY} or record.total_hours is not None:
            record.lifecycle_state = RecordState.VALIDATED
            record.updated_at = datetime.utcnow()
            emit_canonical_event(
                self.events,
                legacy_event_name="AttendanceValidated",
                data={
                    "attendance_id": str(record.attendance_id),
                    "anomalies": [anomaly.value for anomaly in record.anomalies],
                },
                source="attendance-service",
                tenant_id=self.tenant_id,
                registry=self.event_registry,
                idempotency_key=str(record.attendance_id),
            )

    @staticmethod
    def _record_payload(record: AttendanceRecord) -> dict:
        return {
            "attendanceId": str(record.attendance_id),
            "employeeId": str(record.employee_id),
            "attendanceDate": record.attendance_date.isoformat(),
            "attendanceStatus": record.attendance_status.value,
            "source": record.source.value if record.source else None,
            "checkInTime": record.check_in_time.isoformat() if record.check_in_time else None,
            "checkOutTime": record.check_out_time.isoformat() if record.check_out_time else None,
            "totalHours": str(record.total_hours) if record.total_hours is not None else None,
            "lifecycleState": record.lifecycle_state.value,
            "anomalies": [anomaly.value for anomaly in record.anomalies],
            "correctionNote": record.correction_note,
        }

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
