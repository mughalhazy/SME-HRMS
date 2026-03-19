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

    def derive_anomalies(self, *, late_after: time) -> None:
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

        self.anomalies = anomalies
        self.updated_at = datetime.utcnow()
