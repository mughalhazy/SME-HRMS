"""Attendance service implementation aligned with canonical HRMS docs."""

from attendance_service.models import (
    AttendanceAnomaly,
    AttendanceLogEvent,
    AttendanceRecord,
    AttendanceSource,
    AttendanceStatus,
    RecordState,
)
from attendance_service.ui import build_attendance_ui
from attendance_service.service import (
    Actor,
    AttendanceService,
    AttendanceServiceError,
    EmployeeSnapshot,
    InMemoryEmployeeDirectory,
)

__all__ = [
    "Actor",
    "AttendanceAnomaly",
    "AttendanceLogEvent",
    "AttendanceRecord",
    "AttendanceService",
    "AttendanceServiceError",
    "AttendanceSource",
    "AttendanceStatus",
    "EmployeeSnapshot",
    "InMemoryEmployeeDirectory",
    "RecordState",
    "build_attendance_ui",
]
