from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
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
