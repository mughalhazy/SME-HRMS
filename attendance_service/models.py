from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class AttendanceStatus(str, Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"
    HALF_DAY = "HalfDay"
    HOLIDAY = "Holiday"


class AttendanceSource(str, Enum):
    MANUAL = "Manual"
    BIOMETRIC = "Biometric"
    API_IMPORT = "APIImport"


class RecordState(str, Enum):
    CAPTURED = "Captured"
    VALIDATED = "Validated"
    APPROVED = "Approved"
    LOCKED = "Locked"


class AttendanceLogEvent(str, Enum):
    CHECK_IN = "CheckIn"
    CHECK_OUT = "CheckOut"


class AttendanceAnomaly(str, Enum):
    LATE = "Late"
    MISSING_CHECK_IN = "MissingCheckIn"
    MISSING_CHECK_OUT = "MissingCheckOut"
    EARLY_DEPARTURE = "EarlyDeparture"
    MISSING_ROSTER = "MissingRoster"
    UNSCHEDULED_ATTENDANCE = "UnscheduledAttendance"
    OVERTIME = "Overtime"
    SHORT_SHIFT = "ShortShift"


class ScheduleStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"


class RosterStatus(str, Enum):
    ASSIGNED = "Assigned"
    PUBLISHED = "Published"
    CANCELLED = "Cancelled"


class CorrectionStatus(str, Enum):
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    REJECTED = "Rejected"


@dataclass
class Shift:
    code: str
    name: str
    start_time: time
    end_time: time
    break_minutes: int = 0
    late_grace_minutes: int = 15
    overtime_eligible: bool = True
    department_id: Optional[UUID] = None
    shift_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def scheduled_hours(self) -> Decimal:
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        if end_minutes < start_minutes:
            raise ValueError("shift end_time cannot be before start_time")
        total_minutes = end_minutes - start_minutes - self.break_minutes
        if total_minutes < 0:
            raise ValueError("break_minutes cannot exceed shift duration")
        return Decimal(str(round(total_minutes / 60, 2)))


@dataclass
class Schedule:
    name: str
    effective_from: date
    effective_to: date
    department_id: Optional[UUID] = None
    status: ScheduleStatus = ScheduleStatus.DRAFT
    schedule_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RosterAssignment:
    employee_id: UUID
    shift_id: UUID
    roster_date: date
    schedule_id: Optional[UUID] = None
    status: RosterStatus = RosterStatus.ASSIGNED
    roster_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OvertimeRule:
    name: str
    applies_after_hours: Decimal
    multiplier: Decimal
    max_overtime_hours: Decimal
    department_id: Optional[UUID] = None
    active: bool = True
    rule_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AttendanceCorrection:
    attendance_id: UUID
    employee_id: UUID
    requested_by_employee_id: UUID
    reason: str
    approver_employee_id: Optional[UUID] = None
    requested_status: Optional[AttendanceStatus] = None
    requested_check_in_time: Optional[datetime] = None
    requested_check_out_time: Optional[datetime] = None
    requested_correction_note: Optional[str] = None
    status: CorrectionStatus = CorrectionStatus.SUBMITTED
    workflow_id: Optional[str] = None
    decision_note: Optional[str] = None
    correction_id: UUID = field(default_factory=uuid4)
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AttendanceRecord:
    employee_id: UUID
    attendance_date: date
    attendance_status: AttendanceStatus
    source: Optional[AttendanceSource] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    attendance_id: UUID = field(default_factory=uuid4)
    total_hours: Optional[Decimal] = None
    lifecycle_state: RecordState = RecordState.CAPTURED
    anomalies: list[AttendanceAnomaly] = field(default_factory=list)
    correction_note: Optional[str] = None
    scheduled_shift_id: Optional[UUID] = None
    scheduled_start_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    scheduled_hours: Optional[Decimal] = None
    roster_assignment_id: Optional[UUID] = None
    overtime_hours: Optional[Decimal] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def recalculate_total_hours(self) -> None:
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            if duration.total_seconds() < 0:
                raise ValueError("check_out_time cannot be before check_in_time")
            self.total_hours = Decimal(str(round(duration.total_seconds() / 3600, 2)))
        else:
            self.total_hours = None
        self.updated_at = datetime.utcnow()

    def validate_time_consistency(self) -> None:
        for field_name, value in (("check_in_time", self.check_in_time), ("check_out_time", self.check_out_time)):
            if value and value.date() != self.attendance_date:
                raise ValueError(f"{field_name} must be on attendance_date")

        if self.attendance_status in {AttendanceStatus.ABSENT, AttendanceStatus.HOLIDAY}:
            if self.check_in_time or self.check_out_time:
                raise ValueError("absent or holiday records cannot include check-in/check-out times")

    def derive_base_anomalies(self, *, late_after: time) -> list[AttendanceAnomaly]:
        anomalies: list[AttendanceAnomaly] = []
        if self.check_in_time and self.check_in_time.time() > late_after:
            anomalies.append(AttendanceAnomaly.LATE)
            if self.attendance_status == AttendanceStatus.PRESENT:
                self.attendance_status = AttendanceStatus.LATE
        elif self.attendance_status == AttendanceStatus.LATE and self.check_in_time and self.check_in_time.time() <= late_after:
            self.attendance_status = AttendanceStatus.PRESENT

        if self.attendance_status not in {AttendanceStatus.ABSENT, AttendanceStatus.HOLIDAY}:
            if self.check_in_time is None:
                anomalies.append(AttendanceAnomaly.MISSING_CHECK_IN)
            if self.check_out_time is None:
                anomalies.append(AttendanceAnomaly.MISSING_CHECK_OUT)
        return anomalies
