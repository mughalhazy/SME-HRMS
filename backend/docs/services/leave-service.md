# Leave Service

Leave request lifecycle management and approval workflow with payroll linkage.

## Scope
- Manages leave policies, entitlements, and accrual rules (configured via `settings-service`).
- Manages leave request drafting, submission, approval, rejection, and cancellation.
- Tracks approver decisions and timestamps.
- Validates against policy, calendar, and overlap constraints.
- Publishes approved leave impacts for payroll and availability projections.

## HTTP surface (`/api/v1`)
- `POST /api/v1/leave/requests`
- `PATCH /api/v1/leave/requests/{leave_request_id}`
- `POST /api/v1/leave/requests/{leave_request_id}/submit`
- `POST /api/v1/leave/requests/{leave_request_id}/approve`
- `POST /api/v1/leave/requests/{leave_request_id}/reject`
- `POST /api/v1/leave/requests/{leave_request_id}/cancel`
- `GET /api/v1/leave/requests/{leave_request_id}`
- `GET /api/v1/leave/requests?employee_id=&approver_employee_id=&status=&start_date_from=&end_date_to=&limit=&cursor=`
- `GET /api/v1/leave/balances/{employee_id}` — current balances by leave type
- `GET /api/v1/leave/calendar?department_id=&month=` — team leave calendar

## Leave types supported
- Annual / Earned leave
- Sick leave
- Unpaid leave
- Casual leave
- Maternity / Paternity
- Custom types (policy-configured)

## Domain rules
- Leave submission triggers centralized `leave_request_approval` workflow via `workflow-service` [name diverges from canonical `leave_request` per `canon/workflow-catalog.md` — see `workflow-service.md` NOTE / Cross-File Finding #11].
- Manager approval decisions routed through workflow engine before applying domain side effects.
- Overlap validation: rejects requests conflicting with approved leave in same period.
- Policy constraints: minimum notice period, maximum consecutive days, carry-forward limits.
- Approved leave impact injected into `payroll-service` for the relevant pay period.

## Authorization capabilities
- `CAP-LEV-001`: leave request lifecycle (Admin full; Manager scoped to team; Employee create/read/update own)
- `CAP-LEV-002`: leave decision workflow (Admin full; Manager approve/reject team; Employee denied)

## Owned entities
- `LeaveRequest`

## Supported workflows
- `leave_request`

## Events published
- `LeaveRequestSubmitted`
- `LeaveRequestApproved`
- `LeaveRequestRejected`
- `LeaveRequestCancelled`

## Events subscribed
- `EmployeeCreated` — initialize leave entitlement
- `EmployeeStatusChanged` — freeze pending requests for terminated employees
- `LeavePolicyConfigured` (from settings-service) — update entitlement defaults

## Read models produced
- `leave_requests_view` — per-employee request history and status
- Contributes approved leave inputs to `payroll_summary_view`

## Dependencies
- `employee-service` — employee and manager lookup
- `settings-service` — leave policy definitions, accrual defaults, approval rules
- `auth-service` — submitter and approver authorization
- `workflow-service` — approval routing and escalation
- `notification-service` — submission and decision notifications
- `payroll-service` — downstream consumer of approved leave impact
