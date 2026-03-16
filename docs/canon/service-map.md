# Service Map

This document defines the bounded-service decomposition for the HRMS domain model and establishes responsibilities, ownership, integration points, and event flows.

## employee-service

### Responsibilities
- Manage employee master data and employment lifecycle (`Draft`, `Active`, `OnLeave`, `Suspended`, `Terminated`).
- Manage organizational reference data for departments and roles.
- Maintain reporting lines (manager relationships) and department leadership metadata.
- Provide employee profile/search views for downstream services.

### Owned entities
- Employee
- Department
- Role
- PerformanceReview

### APIs
- `POST /employees` — create employee profile.
- `GET /employees/{employee_id}` — fetch employee details.
- `PATCH /employees/{employee_id}` — update employee profile/status.
- `GET /employees?department_id=&status=` — query/filter employees.
- `POST /departments` / `PATCH /departments/{department_id}` — manage department catalog.
- `POST /roles` / `PATCH /roles/{role_id}` — manage role catalog.
- `POST /performance-reviews` / `PATCH /performance-reviews/{performance_review_id}` — manage review cycles.

### Dependencies
- **auth-service** for authentication and authorization (admin/manager/employee scopes).
- **notification-service** to deliver review reminders, manager-assignment updates, and lifecycle notices.

### Events
- Publishes:
  - `EmployeeCreated`
  - `EmployeeUpdated`
  - `EmployeeStatusChanged`
  - `DepartmentCreated`
  - `DepartmentUpdated`
  - `RoleCreated`
  - `RoleUpdated`
  - `PerformanceReviewSubmitted`
  - `PerformanceReviewFinalized`
- Subscribes:
  - `CandidateHired` (from hiring-service) to convert onboarding payload into an employee record.

## attendance-service

### Responsibilities
- Capture attendance events and maintain daily attendance records.
- Validate attendance against schedule/policy and support approval/lock workflow.
- Publish period summaries for payroll consumption.

### Owned entities
- AttendanceRecord

### APIs
- `POST /attendance/records` — create an attendance record (manual/biometric/import).
- `PATCH /attendance/records/{attendance_id}` — update check-in/check-out/status.
- `GET /attendance/records/{attendance_id}` — fetch a single attendance record.
- `GET /attendance/records?employee_id=&from=&to=` — list attendance by employee/date range.
- `POST /attendance/periods/{period_id}/lock` — lock period records for payroll.
- `GET /attendance/summaries?employee_id=&period_start=&period_end=` — period summary endpoint.

### Dependencies
- **employee-service** for employee existence/status validation.
- **auth-service** for access control.
- **notification-service** for anomaly alerts (late/absent) and lock notifications.

### Events
- Publishes:
  - `AttendanceCaptured`
  - `AttendanceValidated`
  - `AttendanceApproved`
  - `AttendanceLocked`
  - `AttendancePeriodClosed`
- Subscribes:
  - `EmployeeCreated`
  - `EmployeeStatusChanged`

## leave-service

### Responsibilities
- Manage leave request lifecycle (`Draft` → `Submitted` → `Approved/Rejected/Cancelled`).
- Apply approval workflow and decision tracking.
- Maintain leave-day totals used for payroll/time deductions.

### Owned entities
- LeaveRequest

### APIs
- `POST /leave/requests` — create leave request.
- `PATCH /leave/requests/{leave_request_id}` — edit/cancel request.
- `POST /leave/requests/{leave_request_id}/submit` — submit for approval.
- `POST /leave/requests/{leave_request_id}/approve` — approve request.
- `POST /leave/requests/{leave_request_id}/reject` — reject request.
- `GET /leave/requests/{leave_request_id}` — fetch request details.
- `GET /leave/requests?employee_id=&status=&from=&to=` — query requests.

### Dependencies
- **employee-service** for employee/manager lookups and status checks.
- **auth-service** for submitter/approver permissions.
- **notification-service** for submission and decision notifications.
- **payroll-service** as downstream consumer of approved leave impacts.

### Events
- Publishes:
  - `LeaveRequestSubmitted`
  - `LeaveRequestApproved`
  - `LeaveRequestRejected`
  - `LeaveRequestCancelled`
- Subscribes:
  - `EmployeeCreated`
  - `EmployeeStatusChanged`

## payroll-service

### Responsibilities
- Calculate and persist payroll outcomes by pay period.
- Combine salary, allowances, deductions, overtime, attendance summaries, and leave impacts.
- Manage payroll lifecycle (`Draft`, `Processed`, `Paid`, `Cancelled`) and payment state.

### Owned entities
- PayrollRecord

### APIs
- `POST /payroll/records` — create payroll draft for employee/period.
- `POST /payroll/run?period_start=&period_end=` — process payroll for a pay period.
- `PATCH /payroll/records/{payroll_record_id}` — adjust record components.
- `POST /payroll/records/{payroll_record_id}/mark-paid` — mark disbursement completion.
- `GET /payroll/records/{payroll_record_id}` — fetch payroll record.
- `GET /payroll/records?employee_id=&period_start=&period_end=&status=` — query payroll records.

### Dependencies
- **employee-service** for employee salary metadata and active roster.
- **attendance-service** for approved/locked attendance summaries.
- **leave-service** for approved leave days and unpaid leave impacts.
- **auth-service** for payroll admin access.
- **notification-service** for payslip-ready and payment completion messages.

### Events
- Publishes:
  - `PayrollDrafted`
  - `PayrollProcessed`
  - `PayrollPaid`
  - `PayrollCancelled`
- Subscribes:
  - `AttendancePeriodClosed`
  - `LeaveRequestApproved`
  - `EmployeeStatusChanged`

## hiring-service

### Responsibilities
- Manage hiring pipeline from job posting to candidate conversion.
- Handle interview scheduling/feedback workflow.
- Execute hire decision and publish candidate-to-employee handoff event.

### Owned entities
- JobPosting
- Candidate
- Interview

### APIs
- `POST /hiring/job-postings` / `PATCH /hiring/job-postings/{job_posting_id}` — manage job postings.
- `GET /hiring/job-postings?status=&department_id=` — list/filter postings.
- `POST /hiring/candidates` / `PATCH /hiring/candidates/{candidate_id}` — manage candidate applications/stages.
- `POST /hiring/interviews` / `PATCH /hiring/interviews/{interview_id}` — schedule/update interviews.
- `POST /hiring/candidates/{candidate_id}/mark-hired` — finalize hiring decision.
- `GET /hiring/candidates/{candidate_id}` — fetch candidate details.

### Dependencies
- **employee-service** for department/role reference validation and interviewer lookups.
- **auth-service** for recruiter/hiring-manager authorization.
- **notification-service** for candidate/interviewer communications.

### Events
- Publishes:
  - `JobPostingOpened`
  - `JobPostingClosed`
  - `CandidateApplied`
  - `CandidateStageChanged`
  - `InterviewScheduled`
  - `InterviewCompleted`
  - `CandidateHired`
- Subscribes:
  - `DepartmentUpdated`
  - `RoleUpdated`

## auth-service

### Responsibilities
- Provide identity, authentication, and token issuance.
- Manage authorization policies (RBAC/claims/scopes) for HRMS actors.
- Handle session lifecycle and credential management.

### Owned entities
- UserAccount
- RoleBinding
- PermissionPolicy
- Session
- RefreshToken

### APIs
- `POST /auth/login` — authenticate principal and issue tokens.
- `POST /auth/refresh` — refresh access token.
- `POST /auth/logout` — revoke active session/token.
- `GET /auth/me` — introspect authenticated principal.
- `POST /auth/users` / `PATCH /auth/users/{user_id}` — manage user accounts.
- `POST /auth/roles/bindings` / `DELETE /auth/roles/bindings/{binding_id}` — manage authorization bindings.

### Dependencies
- **employee-service** for employee-to-user identity linkage.
- **notification-service** for password reset and security alerts.

### Events
- Publishes:
  - `UserAuthenticated`
  - `SessionRevoked`
  - `UserProvisioned`
  - `AuthorizationPolicyUpdated`
- Subscribes:
  - `EmployeeCreated`
  - `EmployeeStatusChanged`

## notification-service

### Responsibilities
- Deliver asynchronous outbound communications (email/SMS/push/in-app).
- Template, queue, and track notification delivery outcomes.
- Centralize event-to-notification routing rules for all domain services.

### Owned entities
- NotificationTemplate
- NotificationMessage
- DeliveryAttempt
- NotificationPreference

### APIs
- `POST /notifications/send` — send ad hoc notification.
- `POST /notifications/bulk-send` — send batch notifications.
- `POST /notifications/templates` / `PATCH /notifications/templates/{template_id}` — manage templates.
- `GET /notifications/messages/{message_id}` — retrieve message/delivery status.
- `PATCH /notifications/preferences/{subject_id}` — update user notification preferences.

### Dependencies
- **auth-service** for service-to-service auth and operator permissions.
- External providers (SMTP, SMS gateway, push providers) for delivery execution.

### Events
- Publishes:
  - `NotificationQueued`
  - `NotificationSent`
  - `NotificationFailed`
- Subscribes:
  - `LeaveRequestSubmitted`
  - `LeaveRequestApproved`
  - `AttendanceCaptured`
  - `PayrollProcessed`
  - `PayrollPaid`
  - `InterviewScheduled`
  - `CandidateHired`
  - `PerformanceReviewSubmitted`
  - `EmployeeStatusChanged`

## Cross-service dependency summary

- `employee-service` is the authoritative source for workforce core records and is depended on by attendance, leave, payroll, hiring, and auth.
- `attendance-service` and `leave-service` feed payroll inputs; payroll should only process finalized/approved upstream records.
- `hiring-service` hands off successful candidates to employee-service through `CandidateHired`.
- `notification-service` is shared infrastructure subscribed to business events across domains.
- `auth-service` is a platform dependency for all protected APIs.
