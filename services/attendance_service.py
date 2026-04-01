from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Literal

from services.attendance.face_recognition import FaceRecognitionAttendanceRecord, FaceRecognitionService

AttendanceInputSource = Literal["biometric", "gps", "manual", "face_recognition"]


@dataclass(slots=True)
class AttendanceEntry:
    employee_id: str
    attendance_date: date
    source: AttendanceInputSource
    check_in: datetime | None
    check_out: datetime | None
    shift_hours: Decimal
    worked_hours: Decimal
    overtime_hours: Decimal


class AttendanceService:
    """Attendance capture + overtime + payroll-input sync aligned to country payroll flow docs."""

    def __init__(self) -> None:
        self._entries: list[AttendanceEntry] = []
        self._face_service = FaceRecognitionService()
        self._face_records: list[FaceRecognitionAttendanceRecord] = []

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        return Decimal(str(value or "0"))

    @classmethod
    def _hours(cls, value: Any) -> Decimal:
        return cls._decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def assign_shift(self, *, shift_hours: Any) -> Decimal:
        return self._hours(shift_hours)

    def calculate_hours(self, *, check_in: datetime | None, check_out: datetime | None) -> Decimal:
        if check_in is None or check_out is None:
            return Decimal("0.00")
        if check_out < check_in:
            raise ValueError("check_out cannot be before check_in")
        seconds = Decimal(str((check_out - check_in).total_seconds()))
        return (seconds / Decimal("3600")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_overtime(self, *, worked_hours: Any, shift_hours: Any) -> Decimal:
        overtime = self._hours(worked_hours) - self._hours(shift_hours)
        if overtime <= Decimal("0"):
            return Decimal("0.00")
        return overtime.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def ingest_face_encodings(self, *, employee_database: dict[str, list[float] | tuple[float, ...]]) -> None:
        self._face_service.ingest_employee_encodings(employee_database)

    def record_face_attendance(
        self,
        *,
        frame: list[float] | tuple[float, ...],
        attendance_date: date,
        shift_hours: Any,
        check_in: datetime | None = None,
        check_out: datetime | None = None,
        worked_hours: Any | None = None,
    ) -> FaceRecognitionAttendanceRecord:
        match = self._face_service.match_employee_identity(frame)
        if match is None:
            raise ValueError("unable to match employee identity")

        self._face_records.append(match)
        self.record_attendance(
            employee_id=match.employee_id,
            attendance_date=attendance_date,
            source="face_recognition",
            shift_hours=shift_hours,
            check_in=check_in,
            check_out=check_out,
            worked_hours=worked_hours,
        )
        return match

    def record_attendance(
        self,
        *,
        employee_id: str,
        attendance_date: date,
        source: AttendanceInputSource,
        shift_hours: Any,
        check_in: datetime | None = None,
        check_out: datetime | None = None,
        worked_hours: Any | None = None,
    ) -> AttendanceEntry:
        if source not in {"biometric", "gps", "manual", "face_recognition"}:
            raise ValueError("source must be biometric, gps, manual, or face_recognition")

        assigned_shift_hours = self.assign_shift(shift_hours=shift_hours)
        computed_worked = self._hours(worked_hours) if worked_hours is not None else self.calculate_hours(check_in=check_in, check_out=check_out)
        overtime_hours = self.calculate_overtime(worked_hours=computed_worked, shift_hours=assigned_shift_hours)
        entry = AttendanceEntry(
            employee_id=employee_id,
            attendance_date=attendance_date,
            source=source,
            check_in=check_in,
            check_out=check_out,
            shift_hours=assigned_shift_hours,
            worked_hours=computed_worked,
            overtime_hours=overtime_hours,
        )
        self._entries.append(entry)
        return entry

    def sync_attendance_to_payroll_inputs(self, *, employee_id: str, period_start: date, period_end: date) -> dict[str, str]:
        rows = [
            row
            for row in self._entries
            if row.employee_id == employee_id and period_start <= row.attendance_date <= period_end
        ]
        total_hours = sum((row.worked_hours for row in rows), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        overtime_hours = sum((row.overtime_hours for row in rows), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "employee_id": employee_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "records": str(len(rows)),
            "total_hours": str(total_hours),
            "overtime_hours": str(overtime_hours),
        }
