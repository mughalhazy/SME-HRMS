# Service Map

This document defines the canonical bounded-service decomposition for SME-HRMS, including responsibilities, owned entities, APIs, dependencies, workflows, published events, subscribed events, and read-model contributions.

## Canonical service registry

| Service | Primary scope | Route prefix |
|---|---|---|
| `employee-service` | Workforce master data and organizational structure | `/api/v1/employees`, `/api/v1/departments`, `/api/v1/roles`, `/api/v1/performance-reviews` |
| `attendance-service` | Attendance capture, validation, and period closure | `/api/v1/attendance` |
| `leave-service` | Leave lifecycle and approval workflow | `/api/v1/leave` |
| `payroll-service` | Payroll processing and payout lifecycle | `/api/v1/payroll` |
| `hiring-service` | Job postings, candidates, interviews, and hire handoff | `/api/v1/hiring` |
| `auth-service` | Identity, sessions, tokens, role bindings, and policy | `/api/v1/auth` |
| `notification-service` | Notification templates, queueing, delivery, and preferences | `/api/v1/notifications` |
| `settings-service` | Administrative HR policy configuration and defaults | `/api/v1/settings` |

## employee-service

### Responsibilities
- Manage employee master data and employment lifecycle.
- Manage organizational reference data for departments and roles.
- Manage performance review cycles and outcomes.
- Publish authoritative employee and organization changes to downstream services.

### Owned entities
- `Employee`
- `Department`
- `Role`
- `PerformanceReview`

### Canonical APIs
- `POST /api/v1/employees`
- `GET /api/v1/employees/{employee_id}`
- `PATCH /api/v1/employees/{employee_id}`
- `GET /api/v1/employees?department_id=&status=&manager_employee_id=&limit=&cursor=`
- `POST /api/v1/departments`
- `PATCH /api/v1/departments/{department_id}`
- `GET /api/v1/departments?status=&limit=&cursor=`
- `POST /api/v1/roles`
- `PATCH /api/v1/roles/{role_id}`
- `GET /api/v1/roles?status=&limit=&cursor=`
- `POST /api/v1/performance-reviews`
- `GET /api/v1/performance-reviews/{performance_review_id}`
- `PATCH /api/v1/performance-reviews/{performance_review_id}`
- `POST /api/v1/performance-reviews/{performance_review_id}/submit`
- `POST /api/v1/performance-reviews/{performance_review_id}/finalize`
- `GET /api/v1/performance-reviews?employee_id=&reviewer_employee_id=&status=&limit=&cursor=`

### Dependencies
- `auth-service` for authentication and authorization.
- `notification-service` for onboarding, status-change, and performance-review notifications.
- `hiring-service` as upstream producer of `CandidateHired` for recruitment-driven onboarding.

### Supported workflows
- `employee_onboarding`
- `performance_review`

### Publishes
- `EmployeeCreated`
- `EmployeeUpdated`
- `EmployeeStatusChanged`
- `DepartmentCreated`
- `DepartmentUpdated`
- `RoleCreated`
- `RoleUpdated`
- `PerformanceReviewSubmitted`
- `PerformanceReviewFinalized`

### Subscribes
- `CandidateHired`

### Read models produced or enriched
- `employee_directory_view`
- `organization_structure_view`
- `performance_review_view`
- enriches `attendance_dashboard_view`, `leave_requests_view`, `payroll_summary_view`, `job_posting_directory_view`, and `candidate_pipeline_view`

## attendance-service

### Responsibilities
- Capture daily attendance records.
- Validate time entries against policy.
- Approve and lock attendance for payroll-safe period closure.
- Publish attendance summaries and closure events.

### Owned entities
- `AttendanceRecord`

### Canonical APIs
- `POST /api/v1/attendance/records`
- `PATCH /api/v1/attendance/records/{attendance_id}`
- `GET /api/v1/attendance/records/{attendance_id}`
- `GET /api/v1/attendance/records?employee_id=&attendance_date_from=&attendance_date_to=&attendance_status=&limit=&cursor=`
- `POST /api/v1/attendance/records/{attendance_id}/validate`
- `POST /api/v1/attendance/records/{attendance_id}/approve`
- `POST /api/v1/attendance/periods/{period_id}/lock`
- `GET /api/v1/attendance/summaries?employee_id=&period_start=&period_end=`

### Dependencies
- `employee-service` for employee existence and employment-status validation.
- `auth-service` for access control.
- `notification-service` for anomaly alerts and closure notices.

### Supported workflows
- `attendance_tracking`

### Publishes
- `AttendanceCaptured`
- `AttendanceValidated`
- `AttendanceApproved`
- `AttendanceLocked`
- `AttendancePeriodClosed`

### Subscribes
- `EmployeeCreated`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `attendance_dashboard_view`
- contributes attendance inputs to `payroll_summary_view`

## leave-service

### Responsibilities
- Manage leave request drafting, submission, approval, rejection, and cancellation.
- Track approver decisions and timestamps.
- Publish approved leave impacts for payroll and availability projections.

### Owned entities
- `LeaveRequest`

### Canonical APIs
- `POST /api/v1/leave/requests`
- `PATCH /api/v1/leave/requests/{leave_request_id}`
- `POST /api/v1/leave/requests/{leave_request_id}/submit`
- `POST /api/v1/leave/requests/{leave_request_id}/approve`
- `POST /api/v1/leave/requests/{leave_request_id}/reject`
- `POST /api/v1/leave/requests/{leave_request_id}/cancel`
- `GET /api/v1/leave/requests/{leave_request_id}`
- `GET /api/v1/leave/requests?employee_id=&approver_employee_id=&status=&start_date_from=&end_date_to=&limit=&cursor=`

### Dependencies
- `employee-service` for employee and manager lookup.
- `auth-service` for submitter and approver authorization.
- `notification-service` for submission and decision notifications.
- `payroll-service` as downstream consumer of approved leave impact.

### Supported workflows
- `leave_request`

### Publishes
- `LeaveRequestSubmitted`
- `LeaveRequestApproved`
- `LeaveRequestRejected`
- `LeaveRequestCancelled`

### Subscribes
- `EmployeeCreated`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `leave_requests_view`
- contributes approved leave inputs to `payroll_summary_view`

## payroll-service

### Responsibilities
- Draft, process, pay, and cancel payroll records by pay period.
- Combine compensation, attendance, and leave impacts into final pay.
- Provide payroll records for dashboards, self-service, and audit.

### Owned entities
- `PayrollRecord`

### Canonical APIs
- `POST /api/v1/payroll/records`
- `PATCH /api/v1/payroll/records/{payroll_record_id}`
- `GET /api/v1/payroll/records/{payroll_record_id}`
- `GET /api/v1/payroll/records?employee_id=&pay_period_start=&pay_period_end=&status=&limit=&cursor=`
- `POST /api/v1/payroll/run?period_start=&period_end=`
- `POST /api/v1/payroll/records/{payroll_record_id}/process`
- `POST /api/v1/payroll/records/{payroll_record_id}/mark-paid`
- `POST /api/v1/payroll/records/{payroll_record_id}/cancel`

### Dependencies
- `employee-service` for roster and compensation context.
- `attendance-service` for approved/locked attendance summaries.
- `leave-service` for approved leave impacts.
- `auth-service` for payroll-admin authorization.
- `notification-service` for payslip-ready and payment notifications.

### Supported workflows
- `payroll_processing`

### Publishes
- `PayrollDrafted`
- `PayrollProcessed`
- `PayrollPaid`
- `PayrollCancelled`

### Subscribes
- `AttendancePeriodClosed`
- `LeaveRequestApproved`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `payroll_summary_view`

## hiring-service

### Responsibilities
- Manage job posting lifecycle.
- Manage candidate applications, stage transitions, and interview scheduling.
- Support Google Calendar interview sync and LinkedIn candidate import in the reference implementation.
- Publish hire handoff events for employee onboarding.

### Owned entities
- `JobPosting`
- `Candidate`
- `Interview`

### Canonical APIs
- `POST /api/v1/hiring/job-postings`
- `PATCH /api/v1/hiring/job-postings/{job_posting_id}`
- `POST /api/v1/hiring/job-postings/{job_posting_id}/hold`
- `POST /api/v1/hiring/job-postings/{job_posting_id}/reopen`
- `GET /api/v1/hiring/job-postings?status=&department_id=&limit=&cursor=`
- `POST /api/v1/hiring/candidates`
- `PATCH /api/v1/hiring/candidates/{candidate_id}`
- `GET /api/v1/hiring/candidates/{candidate_id}`
- `POST /api/v1/hiring/interviews`
- `POST /api/v1/hiring/interviews/google-calendar`
- `PATCH /api/v1/hiring/interviews/{interview_id}`
- `POST /api/v1/hiring/interviews/{interview_id}/cancel`
- `POST /api/v1/hiring/interviews/{interview_id}/mark-no-show`
- `POST /api/v1/hiring/candidates/{candidate_id}/mark-hired`
- `POST /api/v1/hiring/candidates/import/linkedin`

### Dependencies
- `employee-service` for department, role, and interviewer validation.
- `auth-service` for recruiter and hiring-manager authorization.
- `notification-service` for candidate/interviewer communications.
- Google Calendar as an external interview scheduling provider.
- LinkedIn as an optional candidate source provider.

### Supported workflows
- `candidate_hiring`

### Publishes
- `JobPostingOpened`
- `JobPostingOnHold`
- `JobPostingClosed`
- `CandidateApplied`
- `CandidateStageChanged`
- `InterviewScheduled`
- `InterviewCompleted`
- `InterviewCancelled`
- `InterviewNoShow`
- `InterviewCalendarSynced`
- `CandidateImported`
- `LinkedInCandidatesImported`
- `CandidateHired`

### Subscribes
- `DepartmentUpdated`
- `RoleUpdated`

### Read models produced or enriched
- `job_posting_directory_view`
- `candidate_pipeline_view`

## auth-service

### Responsibilities
- Authenticate principals and issue tokens.
- Maintain user accounts, sessions, refresh tokens, and role bindings.
- Evaluate role/capability policy for human and service principals.

### Owned entities
- `UserAccount`
- `RoleBinding`
- `PermissionPolicy`
- `Session`
- `RefreshToken`

### Canonical APIs
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/users`
- `PATCH /api/v1/auth/users/{user_id}`
- `POST /api/v1/auth/users/{user_id}/lock`
- `POST /api/v1/auth/users/{user_id}/unlock`
- `GET /api/v1/auth/sessions?user_id=&status=&limit=&cursor=`
- `POST /api/v1/auth/sessions/{session_id}/revoke`
- `POST /api/v1/auth/roles/bindings`
- `DELETE /api/v1/auth/roles/bindings/{binding_id}`
- `POST /api/v1/auth/policies`
- `PATCH /api/v1/auth/policies/{policy_id}`
- `GET /api/v1/auth/policies?capability_id=&role_name=&effect=&limit=&cursor=`
- `GET /api/v1/auth/access?user_id=`

### Dependencies
- `employee-service` for workforce identity linkage.
- `notification-service` for password reset and security alerts.

### Supported workflows
- `access_provisioning`

### Publishes
- `UserAuthenticated`
- `SessionRevoked`
- `UserProvisioned`
- `UserAccountStatusChanged`
- `RoleBindingChanged`
- `RefreshTokenRotated`
- `AuthorizationPolicyUpdated`

### Subscribes
- `EmployeeCreated`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `access_control_view`

## notification-service

### Responsibilities
- Queue, render, send, and track notifications.
- Apply subject preferences and channel routing.
- Translate domain events into outbound communications.

### Owned entities
- `NotificationTemplate`
- `NotificationMessage`
- `DeliveryAttempt`
- `NotificationPreference`

### Canonical APIs
- `POST /api/v1/notifications/send`
- `POST /api/v1/notifications/bulk-send`
- `POST /api/v1/notifications/templates`
- `PATCH /api/v1/notifications/templates/{template_id}`
- `GET /api/v1/notifications/templates?code=&channel=&status=&limit=&cursor=`
- `GET /api/v1/notifications/messages/{message_id}`
- `GET /api/v1/notifications/preferences/{subject_id}`
- `PATCH /api/v1/notifications/preferences/{subject_id}`
- `GET /api/v1/notifications/delivery?subject_id=&status=&channel=&limit=&cursor=`

### Dependencies
- `auth-service` for operator and service-principal authorization.
- External providers (SMTP, SMS, push) for channel delivery.

### Supported workflows
- `notification_dispatch`

### Publishes
- `NotificationQueued`
- `NotificationSent`
- `NotificationFailed`
- `NotificationSuppressed`

### Subscribes
- `LeaveRequestSubmitted`
- `LeaveRequestApproved`
- `AttendanceCaptured`
- `PayrollProcessed`
- `PayrollPaid`
- `InterviewScheduled`
- `InterviewCalendarSynced`
- `UserProvisioned`
- `SessionRevoked`

### Read models produced or enriched
- `notification_delivery_view`



## settings-service

### Responsibilities
- Manage attendance rule templates and compliance thresholds.
- Manage leave policy definitions, accrual defaults, and activation rules.
- Manage payroll schedule, cutoff, deduction, and approval settings.
- Publish a consolidated administrative read model for the settings workspace.

### Owned entities
- `AttendanceRule`
- `LeavePolicy`
- `PayrollSettings`

### Canonical APIs
- `GET /api/v1/settings`
- `POST /api/v1/settings/attendance-rules`
- `PATCH /api/v1/settings/attendance-rules/{attendance_rule_id}`
- `POST /api/v1/settings/leave-policies`
- `PATCH /api/v1/settings/leave-policies/{leave_policy_id}`
- `PUT /api/v1/settings/payroll`

### Dependencies
- `auth-service` for administrative authentication and authorization.
- `attendance-service` as downstream consumer of attendance defaults.
- `leave-service` as downstream consumer of leave entitlement defaults.
- `payroll-service` as downstream consumer of payroll controls.

### Supported workflows
- `settings_administration`

### Publishes
- `AttendanceRuleConfigured`
- `LeavePolicyConfigured`
- `PayrollSettingsConfigured`
- `SettingsPublished`

### Subscribes
- None in the reference implementation.

### Read models produced or enriched
- `settings_configuration_view`
- enriches `attendance_dashboard_view`, `leave_requests_view`, and `payroll_summary_view` through configuration defaults


## Coverage checklist

- Every service listed by the API gateway route registry is represented here.
- Every owned entity is defined in `docs/canon/domain-model.md`.
- Every published and subscribed event is defined in `docs/canon/event-catalog.md`.
- Every supported workflow is defined in `docs/canon/workflow-catalog.md`.

