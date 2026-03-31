# Service Map

This document defines the canonical bounded-service decomposition for SME-HRMS, including responsibilities, owned entities, APIs, dependencies, workflows, published events, subscribed events, and read-model contributions.

## Canonical service registry

| Service | Primary scope | Route prefix |
|---|---|---|
| `employee-service` | Workforce master data and organizational structure | `/api/v1/employees`, `/api/v1/departments`, `/api/v1/roles`, `/api/v1/org/*` |
| `performance-service` | Performance cycles, goals/OKRs, feedback, calibration, and PIP tracking | `/api/v1/performance/*` |
| `engagement-service` | Employee engagement surveys, response capture, and aggregated sentiment results | `/api/v1/engagement/*` |
| `attendance-service` | Attendance capture, validation, and period closure | `/api/v1/attendance` |
| `leave-service` | Leave lifecycle and approval workflow | `/api/v1/leave` |
| `travel-service` | Travel requests, itineraries, and approval-driven travel coordination | `/api/v1/travel` |
| `payroll-service` | Payroll processing and payout lifecycle | `/api/v1/payroll` |
| `hiring-service` | Job postings, candidates, interviews, and hire handoff | `/api/v1/hiring` |
| `auth-service` | Identity, sessions, tokens, role bindings, and policy | `/api/v1/auth` |
| `notification-service` | Notification templates, queueing, delivery, and preferences | `/api/v1/notifications` |
| `integration-service` | Outbound webhooks, connector dispatch, delivery attempts, and replay operations | `/api/v1/integrations` |
| `settings-service` | Administrative HR policy configuration and defaults | `/api/v1/settings` |
| `search-service` | Cross-domain projection-backed search and indexing | `/api/v1/search` |
| `project-service` | Project planning, staffing assignments, and resource allocation governance | `/api/v1/projects` |

Canonical public prefixes for project/integration/automation/workflow domains are plural (`/api/v1/projects`, `/api/v1/integrations`, `/api/v1/automations`, `/api/v1/workflows`). Gateway-level singular aliases are compatibility shims and must translate to these canonical runtime paths.

## employee-service

### Responsibilities
- Manage employee master data and employment lifecycle.
- Manage organizational reference data for departments, business units, legal entities, locations, cost centers, grades/bands, job positions, and roles.
- Publish authoritative employee and organization changes to downstream services.

### Owned entities
- `Employee`
- `Department`
- `BusinessUnit`
- `LegalEntity`
- `Location`
- `CostCenter`
- `GradeBand`
- `JobPosition`
- `Role`

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
- `POST /api/v1/org/{kind}`
- `PATCH /api/v1/org/{kind}/{entity_id}`
- `GET /api/v1/org/{kind}?status=&department_id=&business_unit_id=&legal_entity_id=&limit=&cursor=`

### Dependencies
- `auth-service` for authentication and authorization.
- `notification-service` for onboarding, status-change, and performance-review notifications.
- `hiring-service` as upstream producer of `CandidateHired` for recruitment-driven onboarding.

### Supported workflows
- `employee_onboarding`

### Publishes
- `EmployeeCreated`
- `EmployeeUpdated`
- `EmployeeStatusChanged`
- `DepartmentCreated`
- `DepartmentUpdated`
- `RoleCreated`
- `RoleUpdated`
- `BusinessUnitCreated`
- `BusinessUnitUpdated`
- `LegalEntityCreated`
- `LegalEntityUpdated`
- `LocationCreated`
- `LocationUpdated`
- `CostCenterCreated`
- `CostCenterUpdated`
- `GradeBandCreated`
- `GradeBandUpdated`
- `JobPositionCreated`
- `JobPositionUpdated`

### Subscribes
- `CandidateHired`

### Read models produced or enriched
- `employee_directory_view`
- `organization_structure_view`
- `employee_reporting_view`
- enriches `attendance_dashboard_view`, `leave_requests_view`, `payroll_summary_view`, `job_posting_directory_view`, and `candidate_pipeline_view`
- produces `employee_compensation_view` and payroll-context projections consumed by `payroll-service`


## project-service

### Responsibilities
- Manage project master data, staffing assignments, and allocation changes without duplicating payroll logic.
- Reuse `employee-service` read models for employee, manager, and department references.
- Route optional assignment/allocation approvals through the centralized workflow engine and publish audit-ready resource-allocation events.

### Owned entities
- `Project`
- `ProjectAssignment`
- `AllocationLedgerEntry`

### Canonical APIs
- `POST /api/v1/projects`
- `PATCH /api/v1/projects/{project_id}/status`
- `GET /api/v1/projects/{project_id}`
- `GET /api/v1/projects?status=&manager_employee_id=&limit=&cursor=`
- `POST /api/v1/projects/assignments`
- `PATCH /api/v1/projects/assignments/{assignment_id}/allocation`
- `POST /api/v1/projects/assignments/{assignment_id}/approve`
- `POST /api/v1/projects/assignments/{assignment_id}/reject`
- `POST /api/v1/projects/assignments/{assignment_id}/release`
- `GET /api/v1/projects/assignments?project_id=&employee_id=&allocation_status=&limit=&cursor=`

### Dependencies
- `employee-service` for employee existence, department context, and reporting-line lookup.
- `workflow-service` for optional assignment and allocation approvals.
- `audit-service` for mutation logging.
- `notification-service` for approval assignment and escalation notifications.

### Supported workflows
- `project_resource_allocation`

### Publishes
- `ProjectCreated`
- `ProjectStatusChanged`
- `ProjectAssignmentRequested`
- `ProjectAssignmentAllocated`
- `ProjectAssignmentRejected`
- `ProjectAssignmentReleased`
- `ProjectAllocationUpdated`

### Subscribes
- `EmployeeCreated`
- `EmployeeUpdated`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `project_staffing_view`
- `resource_allocation_view`


## search-service

### Responsibilities
- Provide fast, projection-backed cross-domain search over HRMS entities without reading transactional domain stores for search-heavy queries.
- Consume D2-aligned events from the outbox pipeline and schedule asynchronous reindex jobs through the background-jobs service.
- Build and serve tenant-safe search documents from canonical read models and search-owned projections.

### Owned entities
- `SearchDocument`
- `SearchProjectionState`
- `SearchEventCheckpoint`

### Canonical APIs
- `GET /api/v1/search?tenant_id=&q=&entity_type=&domain=&department_id=&role_id=&status=&limit=&cursor=&sort=`
- `GET /api/v1/search/employees?tenant_id=&q=&department_id=&role_id=&status=&limit=&cursor=&sort=`
- `GET /api/v1/search/candidates?tenant_id=&q=&department_id=&status=&limit=&cursor=&sort=`
- `GET /api/v1/search/documents?tenant_id=&q=&department_id=&status=&limit=&cursor=&sort=`

### Dependencies
- `employee-service` read models for workforce and organizational search surfaces.
- `hiring-service` read models for candidate search surfaces.
- `documents` metadata projections for document search.
- `payroll-service` summary projections for optional payroll run search.
- `background-jobs` for asynchronous indexing.
- `integration-service` / event-outbox pipeline for canonical event delivery.

### Supported workflows
- `projection_search_indexing`

### Publishes
- None required; indexing side effects remain internal projections.

### Subscribes
- `EmployeeCreated`
- `EmployeeUpdated`
- `EmployeeStatusChanged`
- `DepartmentCreated`
- `DepartmentUpdated`
- `RoleCreated`
- `RoleUpdated`
- `CandidateApplied`
- `CandidateStageChanged`
- `InterviewScheduled`
- `InterviewCompleted`
- `CandidateHired`
- `DocumentStored`
- `DocumentUpdated`
- `PayrollProcessed`
- `PayrollPaid`
- `PayrollCancelled`

### Read models produced or enriched
- consumes `employee_directory_view`, `organization_structure_view`, `candidate_pipeline_view`, `document_library_view`, and `payroll_summary_view`
- produces `global_search_view`

## engagement-service

### Responsibilities
- Manage employee engagement surveys and pulse campaigns without duplicating workforce master data.
- Reuse `employee-service` read models for employee, manager, and department references plus target-population scoping.
- Capture survey responses and publish aggregated results for people analytics consumers.

### Owned entities
- `Survey`
- `SurveyQuestion`
- `SurveyResponse`
- `AggregatedSurveyResult`

### Canonical APIs
- `POST /api/v1/engagement/surveys`
- `POST /api/v1/engagement/surveys/{survey_id}/publish`
- `POST /api/v1/engagement/surveys/{survey_id}/close`
- `GET /api/v1/engagement/surveys?status=`
- `GET /api/v1/engagement/surveys/{survey_id}`
- `POST /api/v1/engagement/responses`
- `GET /api/v1/engagement/surveys/{survey_id}/responses`
- `GET /api/v1/engagement/surveys/{survey_id}/aggregates`

### Dependencies
- `employee-service` for employee existence, department context, and target-population lookup.
- `notification-service` for optional pulse reminders and survey launch communication.

### Supported workflows
- `engagement_feedback_collection`

### Publishes
- `EngagementSurveyCreated`
- `EngagementSurveyPublished`
- `EngagementSurveyClosed`
- `EngagementSurveyResponseSubmitted`
- `EngagementSurveyResultsAggregated`

### Subscribes
- `EmployeeCreated`
- `EmployeeUpdated`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `engagement_survey_view`
- enriches people analytics and executive sentiment dashboards


## performance-service

### Responsibilities
- Manage enterprise performance review cycles and publish cycle state changes.
- Manage goals/OKRs, continuous feedback, calibration decisions, and performance improvement plans.
- Integrate performance approvals through the centralized workflow engine and emit audit-ready mutations.
- Reuse `employee-service` as the read-only source for employee and manager references.

### Owned entities
- `ReviewCycle`
- `Goal`
- `Feedback`
- `CalibrationSession`
- `PipPlan`

### Canonical APIs
- `POST /api/v1/performance/review-cycles`
- `POST /api/v1/performance/review-cycles/{review_cycle_id}/submit`
- `POST /api/v1/performance/review-cycles/{review_cycle_id}/close`
- `GET /api/v1/performance/review-cycles/{review_cycle_id}`
- `POST /api/v1/performance/goals`
- `POST /api/v1/performance/goals/{goal_id}/submit`
- `POST /api/v1/performance/goals/{goal_id}/approve`
- `POST /api/v1/performance/goals/{goal_id}/reject`
- `GET /api/v1/performance/goals?employee_id=&status=&limit=&cursor=`
- `POST /api/v1/performance/feedback`
- `GET /api/v1/performance/feedback?employee_id=`
- `POST /api/v1/performance/calibrations`
- `POST /api/v1/performance/calibrations/{calibration_id}/submit`
- `POST /api/v1/performance/calibrations/{calibration_id}/approve`
- `POST /api/v1/performance/calibrations/{calibration_id}/reject`
- `POST /api/v1/performance/pips`
- `POST /api/v1/performance/pips/{pip_id}/submit`
- `POST /api/v1/performance/pips/{pip_id}/approve`
- `POST /api/v1/performance/pips/{pip_id}/reject`
- `PATCH /api/v1/performance/pips/{pip_id}/progress`
- `GET /api/v1/performance/pips?employee_id=&status=`

### Dependencies
- `employee-service` for employee existence, department context, and reporting-line lookup.
- `auth-service` for access control.
- `workflow-service` for review-cycle, goal, calibration, and PIP approvals.
- `audit-service` for mutation logging.
- `notification-service` for manager, HR, and employee notifications.

### Supported workflows
- `performance_management`

### Publishes
- `PerformanceReviewCycleCreated`
- `PerformanceReviewCycleOpened`
- `PerformanceReviewCycleClosed`
- `PerformanceGoalCreated`
- `PerformanceGoalSubmitted`
- `PerformanceGoalApproved`
- `PerformanceGoalRejected`
- `PerformanceFeedbackRecorded`
- `PerformanceCalibrationCreated`
- `PerformanceCalibrationSubmitted`
- `PerformanceCalibrationFinalized`
- `PerformanceCalibrationRejected`
- `PerformancePipCreated`
- `PerformancePipSubmitted`
- `PerformancePipActive`
- `PerformancePipRejected`
- `PerformancePipProgressUpdated`

### Subscribes
- `EmployeeCreated`
- `EmployeeUpdated`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `performance_review_view`
- `employee_profile_view`

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


## integration-service

### Responsibilities
- Centralize outbound webhook registration and delivery for tenant-scoped external integrations.
- Consume canonical D2-aligned events and fan them out to subscribed endpoints.
- Sign outbound payloads, track delivery attempts, and expose replay/failure visibility.
- Keep domain services free of partner-specific dispatch logic.

### Owned entities
- `WebhookEndpoint`
- `WebhookDelivery`
- `WebhookDeliveryAttempt`

### Canonical APIs
- `POST /api/v1/integrations/webhooks`
- `PATCH /api/v1/integrations/webhooks/{webhook_id}`
- `DELETE /api/v1/integrations/webhooks/{webhook_id}`
- `GET /api/v1/integrations/webhooks?status=&limit=&cursor=`
- `GET /api/v1/integrations/deliveries?webhook_id=&delivery_status=&event_type=&limit=&cursor=`
- `POST /api/v1/integrations/deliveries/{delivery_id}/replay`

### Dependencies
- `auth-service` for privileged registration and replay authorization.
- `audit-service` for immutable management-operation audit records.
- P6 event/outbox pipeline as the upstream event source.
- P7 background jobs for queued delivery execution and scheduling.

### Publishes
- None required for the initial centralized webhook dispatch implementation.

### Subscribes
- Canonical outbound business events listed in `docs/canon/event-catalog.md`.

### Read models produced or enriched
- `integration_delivery_view`

## travel-service

### Responsibilities
- Manage employee travel requests from draft through approval, booking, cancellation, and completion.
- Store itinerary segments and booking details for approved travel.
- Reuse `employee-service` read models for traveler and manager references.
- Route approvals through the centralized workflow engine and emit tenant-scoped audit records.

### Owned entities
- `TravelRequest`
- `TravelItinerarySegment`

### Canonical APIs
- `POST /api/v1/travel/requests`
- `POST /api/v1/travel/requests/{travel_request_id}/submit`
- `POST /api/v1/travel/requests/{travel_request_id}/approve`
- `POST /api/v1/travel/requests/{travel_request_id}/reject`
- `PUT /api/v1/travel/requests/{travel_request_id}/itinerary`
- `POST /api/v1/travel/requests/{travel_request_id}/cancel`
- `POST /api/v1/travel/requests/{travel_request_id}/complete`
- `GET /api/v1/travel/requests/{travel_request_id}`
- `GET /api/v1/travel/requests?employee_id=&status=&limit=&cursor=`

### Dependencies
- `employee-service` for employee existence, department context, and reporting-line lookup.
- `auth-service` for access control.
- `workflow-service` for request approvals.
- `audit-service` for mutation logging.
- `notification-service` for traveler, manager, and travel-desk notifications.

### Supported workflows
- `travel_request`

### Publishes
- `TravelRequestCreated`
- `TravelRequestSubmitted`
- `TravelRequestApproved`
- `TravelRequestRejected`
- `TravelItineraryUpdated`
- `TravelRequestCancelled`
- `TravelRequestCompleted`

### Subscribes
- `EmployeeCreated`
- `EmployeeUpdated`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `travel_requests_view`
- enriches travel operations inboxes and employee travel history projections
