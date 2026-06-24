# Attendance Service

Attendance capture, validation, and period closure — supporting biometric, GPS, and face recognition sources with a full exception management engine.

## Scope
- Captures daily attendance records from multiple sources: biometric, GPS check-in, face recognition, manual.
- Validates time entries against policy rules (shifts, grace periods, late penalties).
- Manages shift templates and multi-shift configurations.
- Runs the overtime engine.
- Resolves missing punch exceptions.
- Approves and locks attendance for payroll-safe period closure.
- Publishes attendance summaries and period-close events consumed by `payroll-service`.

## HTTP surface (`/api/v1`)
- `POST /api/v1/attendance/records`
- `PATCH /api/v1/attendance/records/{attendance_id}`
- `GET /api/v1/attendance/records/{attendance_id}`
- `GET /api/v1/attendance/records?employee_id=&attendance_date_from=&attendance_date_to=&attendance_status=&limit=&cursor=`
- `POST /api/v1/attendance/records/{attendance_id}/validate`
- `POST /api/v1/attendance/records/{attendance_id}/approve`
- `POST /api/v1/attendance/periods/{period_id}/lock` — lock period; triggers `AttendancePeriodClosed`
- `GET /api/v1/attendance/summaries?employee_id=&period_start=&period_end=`
- `GET /api/v1/attendance/exceptions?employee_id=&type=&status=&limit=&cursor=` — missing punch, anomalies
- `POST /api/v1/attendance/exceptions/{exception_id}/resolve`

## Capture sources
- Biometric device integration (fingerprint, card)
- GPS check-in (location-bounded)
- Face recognition
- Manual entry (admin override with audit)

## Advanced features
- Grace period configuration (per shift, per policy)
- Late penalty ladder (tiered deductions per late severity)
- Missing punch resolution workflow
- Multi-shift templates (rotating, split, flexible)
- Overtime engine: computes overtime hours vs. threshold; flags anomalies

## Authorization capabilities
- `CAP-ATT-001`: attendance capture and monitoring (Admin full; Manager scoped to team; Employee create/read/update own)
- `CAP-ATT-002`: attendance validation and period lock (Admin full; Manager for team periods; Employee denied)

## Owned entities
- `AttendanceRecord`
- `AttendancePeriod`
- `AttendanceException`
- `ShiftTemplate`

## Supported workflows
- `attendance_tracking`

## Events published
- `AttendanceCaptured`
- `AttendanceValidated`
- `AttendanceApproved`
- `AttendanceLocked`
- `AttendancePeriodClosed`

## Events subscribed
- `EmployeeCreated` — initialize attendance eligibility
- `EmployeeStatusChanged` — update active roster for period

## Read models produced
- `attendance_dashboard_view` — per-employee per-day: status, hours, source, exceptions
- Contributes attendance inputs to `payroll_summary_view`

## Dependencies
- `employee-service` — employee existence and employment-status validation
- `settings-service` — attendance rule templates (grace periods, overtime thresholds)
- `auth-service` — access control
- `notification-service` — anomaly alerts, period closure notices
- `decision-service` — overtime anomaly signals
  > NOTE (2026-06-13): this is a downstream/consumer relationship, not an upstream dependency — attendance-service supplies raw attendance/overtime data that `decision-service` scans and turns into `AnomalyDetected` signals (decision-service.md confirms decision-service is the publisher of `AnomalyDetected`). Listed under Dependencies for discoverability; see Notes below for the correct flow direction.

## Notes
- Period lock is irreversible in the current period; corrections require admin override with audit entry.
- Overtime anomalies detected here are scanned by `decision-service`, which publishes the resulting `AnomalyDetected` signal (attendance-service itself does not publish `AnomalyDetected` — see Events published above).
- **Biometric integration:** `integrations/biometric/device_adapter.py` (67 lines) — adapter for biometric hardware devices. Feeds raw attendance events (punch-in/punch-out timestamps) into the attendance service capture pipeline. GPS-based capture goes through a separate mobile gateway path.
