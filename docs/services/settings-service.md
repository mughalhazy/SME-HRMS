# Settings Service

The `settings-service` owns the administrative configuration surface for company-wide HR policies.

## Owned entities
- `AttendanceRule`
- `LeavePolicy`
- `PayrollSettings`

## Responsibilities
- Store and validate workforce attendance rules.
- Store and validate leave policy definitions and approval defaults.
- Store and validate payroll schedule, cutoff, and approval controls.
- Publish a consolidated `settings_configuration_view` read model for administrative UIs.

## Canonical APIs
- `GET /api/v1/settings`
- `POST /api/v1/settings/attendance-rules`
- `PATCH /api/v1/settings/attendance-rules/{attendance_rule_id}`
- `POST /api/v1/settings/leave-policies`
- `PATCH /api/v1/settings/leave-policies/{leave_policy_id}`
- `PUT /api/v1/settings/payroll`

## Domain rules
- Attendance rule `code` values are unique.
- Leave policy `code` values are unique.
- Only one `Active` leave policy is allowed per `leave_type`.
- Unpaid leave policies must have `annual_entitlement_days = 0`.
- `carry_forward_limit_days` cannot exceed `annual_entitlement_days`.
- Payroll settings require at least one approval stage and valid pay-day constraints per schedule.
