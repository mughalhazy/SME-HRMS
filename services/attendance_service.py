from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
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
    late_minutes: int
    late_penalty: Decimal
    missing_punch_resolved: bool
    missing_punch_unresolved: bool
    shift_template: str | None


class AttendanceService:
    """Attendance capture + overtime + payroll-input sync aligned to country payroll flow docs."""

    def __init__(self) -> None:
        self._entries: list[AttendanceEntry] = []
        self._face_service = FaceRecognitionService()
        self._face_records: list[FaceRecognitionAttendanceRecord] = []
        self._shift_templates: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        return Decimal(str(value or "0"))

    @classmethod
    def _hours(cls, value: Any) -> Decimal:
        return cls._decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def assign_shift(self, *, shift_hours: Any) -> Decimal:
        return self._hours(shift_hours)

    def register_shift_template(
        self,
        *,
        template_name: str,
        shift_hours: Any,
        scheduled_start_hour: int | None = None,
        scheduled_end_hour: int | None = None,
        grace_period_minutes: int = 0,
    ) -> None:
        self._shift_templates[template_name] = {
            "shift_hours": self._hours(shift_hours),
            "scheduled_start_hour": scheduled_start_hour,
            "scheduled_end_hour": scheduled_end_hour,
            "grace_period_minutes": max(0, int(grace_period_minutes)),
        }

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

    @staticmethod
    def _minutes_late(*, check_in: datetime | None, attendance_date: date, scheduled_start_hour: int | None, grace_period_minutes: int) -> int:
        if check_in is None or scheduled_start_hour is None:
            return 0
        scheduled_start = datetime(attendance_date.year, attendance_date.month, attendance_date.day, scheduled_start_hour, 0, 0)
        raw_minutes = int((check_in - scheduled_start).total_seconds() // 60)
        return max(0, raw_minutes - max(0, grace_period_minutes))

    @classmethod
    def _late_penalty_from_ladder(cls, *, late_minutes: int, late_penalty_ladder: list[dict[str, Any]] | None) -> Decimal:
        if late_minutes <= 0 or not late_penalty_ladder:
            return Decimal("0.00")

        normalized = sorted(late_penalty_ladder, key=lambda step: cls._decimal(step.get("up_to_minutes", "0")))
        for step in normalized:
            up_to = int(cls._decimal(step.get("up_to_minutes", "0")))
            penalty = cls._hours(step.get("penalty", "0"))
            if late_minutes <= up_to:
                return penalty
        return cls._hours(normalized[-1].get("penalty", "0"))

    def _resolve_missing_punch(
        self,
        *,
        attendance_date: date,
        shift_hours: Decimal,
        check_in: datetime | None,
        check_out: datetime | None,
        scheduled_start_hour: int | None,
        scheduled_end_hour: int | None,
        missing_punch_resolution: str | None,
    ) -> tuple[datetime | None, datetime | None, bool]:
        resolved = False
        if check_in is not None and check_out is not None:
            return check_in, check_out, resolved
        if missing_punch_resolution != "assume_shift_window":
            return check_in, check_out, resolved

        if check_in is None and scheduled_start_hour is not None:
            check_in = datetime(attendance_date.year, attendance_date.month, attendance_date.day, scheduled_start_hour, 0, 0)
            resolved = True
        if check_out is None:
            if scheduled_end_hour is not None:
                check_out = datetime(attendance_date.year, attendance_date.month, attendance_date.day, scheduled_end_hour, 0, 0)
            elif check_in is not None:
                shift_seconds = int((shift_hours * Decimal("3600")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
                check_out = check_in + timedelta(seconds=shift_seconds)
            if check_out is not None:
                resolved = True
        return check_in, check_out, resolved

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
        shift_template: str | None = None,
        grace_period_minutes: int = 0,
        late_penalty_ladder: list[dict[str, Any]] | None = None,
        scheduled_start_hour: int | None = None,
        scheduled_end_hour: int | None = None,
        missing_punch_resolution: str | None = None,
    ) -> AttendanceEntry:
        if source not in {"biometric", "gps", "manual", "face_recognition"}:
            raise ValueError("source must be biometric, gps, manual, or face_recognition")

        template = self._shift_templates.get(shift_template or "")
        had_missing_punch = check_in is None or check_out is None
        assigned_shift_hours = self.assign_shift(shift_hours=template.get("shift_hours", shift_hours) if template else shift_hours)
        effective_start_hour = template.get("scheduled_start_hour", scheduled_start_hour) if template else scheduled_start_hour
        effective_end_hour = template.get("scheduled_end_hour", scheduled_end_hour) if template else scheduled_end_hour
        effective_grace_minutes = int(template.get("grace_period_minutes", grace_period_minutes)) if template else int(grace_period_minutes)

        resolved_check_in, resolved_check_out, missing_punch_resolved = self._resolve_missing_punch(
            attendance_date=attendance_date,
            shift_hours=assigned_shift_hours,
            check_in=check_in,
            check_out=check_out,
            scheduled_start_hour=effective_start_hour,
            scheduled_end_hour=effective_end_hour,
            missing_punch_resolution=missing_punch_resolution,
        )

        computed_worked = self._hours(worked_hours) if worked_hours is not None else self.calculate_hours(check_in=resolved_check_in, check_out=resolved_check_out)
        overtime_hours = self.calculate_overtime(worked_hours=computed_worked, shift_hours=assigned_shift_hours)
        late_minutes = self._minutes_late(
            check_in=resolved_check_in,
            attendance_date=attendance_date,
            scheduled_start_hour=effective_start_hour,
            grace_period_minutes=effective_grace_minutes,
        )
        late_penalty = self._late_penalty_from_ladder(late_minutes=late_minutes, late_penalty_ladder=late_penalty_ladder)
        entry = AttendanceEntry(
            employee_id=employee_id,
            attendance_date=attendance_date,
            source=source,
            check_in=resolved_check_in,
            check_out=resolved_check_out,
            shift_hours=assigned_shift_hours,
            worked_hours=computed_worked,
            overtime_hours=overtime_hours,
            late_minutes=late_minutes,
            late_penalty=late_penalty,
            missing_punch_resolved=missing_punch_resolved,
            missing_punch_unresolved=had_missing_punch and (not missing_punch_resolved) and worked_hours is None,
            shift_template=shift_template,
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
        late_penalties = sum((row.late_penalty for row in rows), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        unresolved_missing_punches = sum(1 for row in rows if row.missing_punch_unresolved)
        return {
            "employee_id": employee_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "records": str(len(rows)),
            "total_hours": str(total_hours),
            "overtime_hours": str(overtime_hours),
            "late_penalties": str(late_penalties),
            "unresolved_missing_punches": str(unresolved_missing_punches),
        }
