"""Attendance service implementation aligned with canonical HRMS docs."""

from attendance_service.models import (
    AttendanceAnomaly,
    AttendanceCorrection,
    AttendanceLogEvent,
    AttendanceRecord,
    AttendanceSource,
    AttendanceStatus,
    CorrectionStatus,
    OvertimeRule,
    RecordState,
    RosterAssignment,
    RosterStatus,
    Schedule,
    ScheduleStatus,
    Shift,
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
    "AttendanceCorrection",
    "AttendanceLogEvent",
    "AttendanceRecord",
    "AttendanceService",
    "AttendanceServiceError",
    "AttendanceSource",
    "AttendanceStatus",
    "CorrectionStatus",
    "EmployeeSnapshot",
    "InMemoryEmployeeDirectory",
    "OvertimeRule",
    "RecordState",
    "RosterAssignment",
    "RosterStatus",
    "Schedule",
    "ScheduleStatus",
    "Shift",
    "build_attendance_ui",
]
