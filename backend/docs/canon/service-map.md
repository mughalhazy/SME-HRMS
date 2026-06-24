# Service Map

This document defines the canonical bounded-service decomposition for SME-HRMS, including responsibilities, owned entities, APIs, dependencies, workflows, published events, subscribed events, and read-model contributions.

## Canonical service registry

Status values: **IMPLEMENTED** — live runtime code exists and is deployable. **ADD-ON** — code exists but is optional/not in core release. **PLANNED** — defined in canon, not yet implemented.

| Service | Primary scope | Route prefix | Status |
|---|---|---|---|
| `employee-service` | Workforce master data and organizational structure | `/api/v1/employees`, `/api/v1/departments`, `/api/v1/roles`, `/api/v1/org/*` | IMPLEMENTED |
| `attendance-service` | Attendance capture, validation, and period closure | `/api/v1/attendance` | IMPLEMENTED |
| `leave-service` | Leave lifecycle and approval workflow | `/api/v1/leave` | IMPLEMENTED |
| `payroll-service` | Payroll processing and payout lifecycle | `/api/v1/payroll` | IMPLEMENTED |
| `compliance-service` | Statutory compliance lifecycle: validation, report generation, and submission for FBR, EOBI, PESSI | `/api/v1/compliance` | IMPLEMENTED |
| `decision-service` | Cross-domain intelligence: anomaly detection, risk scoring, and Decision Cards | `/api/v1/decisions` | IMPLEMENTED |
| `bank-service` | Salary disbursement, Raast payouts, payment tracking, and reconciliation | `/api/v1/banking` | IMPLEMENTED |
| `hiring-service` | Job postings, candidates, interviews, and hire handoff | `/api/v1/hiring` | IMPLEMENTED |
| `auth-service` | Identity, sessions, tokens, role bindings, and policy | `/api/v1/auth` | IMPLEMENTED |
| `notification-service` | Notification templates, queueing, delivery, and preferences | `/api/v1/notifications` | IMPLEMENTED |
| `whatsapp-service` | WhatsApp access channel: identity mapping, session management, and domain action dispatch | `/api/v1/whatsapp` | IMPLEMENTED |
| `reporting-analytics-service` | Operational, compliance, predictive, and anomaly reports | `/api/v1/analytics` | IMPLEMENTED |
| `automation-service` | Infrastructure orchestration: event-triggered automation rules (event-type matching via `automation_contract.py`; scheduled and threshold triggers NOT implemented — see BACKEND_GAP_REGISTER EG-003) | `/api/v1/automations` | IMPLEMENTED |
| `helpdesk-service` | HR service delivery: employee query tickets, SLA tracking, knowledge base | `/api/v1/helpdesk` | ADD-ON |
| `expense-service` | Employee expense reimbursement: claims, receipts, approvals, and accounting export | `/api/v1/expenses` | ADD-ON |
| `ewa-financial-service` | Earned wage access and salary advances with payroll-linked repayment | N/A — no standalone service | RESOLVED: No `ewa-financial-service` microservice. EWA is implemented as `FinancialWellnessService` in `backend/services/finance/ewa.py`, used as an in-process dependency of `payroll-service`. EWA payouts route through `bank-service` (`banking_api.py` Raast payout endpoint). No standalone gateway route for EWA exists — access via payroll + banking service APIs. CAP-EWA-001/002 capabilities apply to these services. |
| `performance-service` | Performance cycles, goals/OKRs, feedback, calibration, and PIP tracking | `/api/v1/performance/*` | ADD-ON |
| `engagement-service` | Employee engagement surveys, response capture, and aggregated sentiment results | `/api/v1/engagement/*` | ADD-ON |
| `integration-service` | Outbound webhooks, connector dispatch, delivery attempts, and replay operations | `/api/v1/integrations` | ADD-ON |
| `settings-service` | Administrative HR policy configuration and defaults | `/api/v1/settings` | ADD-ON |
| `search-service` | Cross-domain projection-backed search and indexing | `/api/v1/search` | ADD-ON |
| `travel-service` | Travel requests, itineraries, and approval-driven travel coordination | `/api/v1/travel` | PLANNED |
| `project-service` | Project planning, staffing assignments, and resource allocation governance | `/api/v1/projects` | PLANNED |

Canonical public prefixes for project/integration/automation/workflow domains are plural (`/api/v1/projects`, `/api/v1/integrations`, `/api/v1/automations`, `/api/v1/workflows`). Singular gateway aliases were removed in the final convergence pass to eliminate stale and ambiguous route mappings.

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
- 13 endpoints (`/api/v1/employees`, `/api/v1/departments`, `/api/v1/roles`, `/api/v1/org/*`). Full surface: `docs/services/employee-service.md`.

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
- 10 endpoints (`/api/v1/projects`). Full surface: `docs/services/project-service.md`.

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
- 4 endpoints (`/api/v1/search`). Full surface: `docs/services/search-service.md`.

### Dependencies
- `employee-service` read models for workforce and organizational search surfaces.
- `hiring-service` read models for candidate search surfaces.
- `employee-service` document-compliance module metadata projections for document search.
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
- 8 endpoints (`/api/v1/engagement/*`). Full surface: `docs/services/engagement-service.md`.

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
- 21 endpoints (`/api/v1/performance/*`). Full surface: `docs/services/performance-service.md`.

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
- 8 endpoints (`/api/v1/attendance`). Full surface: `docs/services/attendance-service.md`.

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
- 8 endpoints (`/api/v1/leave`). Full surface: `docs/services/leave-service.md`.

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
- 8 endpoints (`/api/v1/payroll`). Full surface: `docs/services/payroll-service.md`.

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
- 15 endpoints (`/api/v1/hiring/*`). Full surface: `docs/services/hiring-service.md`.

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
- 16 endpoints (`/api/v1/auth`). Full surface: `docs/services/auth-service.md`.

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
- 9 endpoints (`/api/v1/notifications`). Full surface: `docs/services/notification-service.md`.

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
- 6 endpoints (`/api/v1/settings`). Full surface: `docs/services/settings-service.md`.

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
- 6 endpoints (`/api/v1/integrations`). Full surface: `docs/services/integration-service.md`.

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
- 9 endpoints (`/api/v1/travel`). Full surface: `docs/services/travel-service.md`.

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


## compliance-service

### Responsibilities
- Orchestrate the statutory compliance lifecycle for all configured country jurisdictions.
- Run pre-payroll validation gate via country compliance engine before payroll finalization is permitted.
- Generate statutory report artifacts (FBR Annexure-C, EOBI PR-01, PESSI/SESSI returns) via country adapter.
- Track submission state through `DRAFT → VALIDATED → SUBMITTED → ACK → FAILED → RETRY`.
- Maintain immutable compliance audit trail for all submission events.

### Owned entities
- `ComplianceSubmission`
- `ComplianceReport`
- `ComplianceAuditRecord`

### Canonical APIs
- 9 endpoints (`/api/v1/compliance`). Full surface: `docs/services/compliance-service.md`.

### Dependencies
- `payroll-service` for payroll data as validation input.
- `employee-service` for employee roster and statutory identifiers (CNIC, NTN).
- `government-adapters` layer for FBR, EOBI, PESSI dispatch.
- `audit-service` for immutable compliance audit records.
- `notification-service` for compliance alerts and failure notifications.

### Supported workflows
- `compliance_submission`

### Publishes
- `ComplianceSubmissionCreated`
- `ComplianceValidationPassed`
- `ComplianceValidationFailed`
- `ComplianceReportGenerated`
- `ComplianceSubmitted`
- `ComplianceAcknowledged`
- `ComplianceSubmissionFailed`
- `ComplianceRetryQueued`

### Subscribes
- `PayrollProcessed`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `compliance_status_view`
- enriches `payroll_summary_view` with compliance gate status


## decision-service

### Responsibilities
- Detect payroll, attendance, compliance, and performance anomalies as a cross-domain intelligence layer.
- Score risk and confidence for each detected anomaly.
- Produce Decision Cards with recommended actions, reversibility, and expiry.
- Enforce human-in-the-loop gates for high-risk decisions.
- Maintain immutable audit trail for all card state transitions.

### Owned entities
- `DecisionCard`
- `AnomalyRecord`
- `DecisionAuditEntry`

### Canonical APIs
- 7 endpoints (`/api/v1/decisions`). Full surface: `docs/services/decision-service.md`.

### Dependencies
- `payroll-service` for payroll anomaly scan input.
- `attendance-service` for overtime and absence anomaly data.
- `compliance-service` for compliance violation signals.
- `employee-service` for role band and compensation history.
- `audit-service` for immutable decision records.
- `notification-service` for high-risk alerts.

### Supported workflows
- `anomaly_review`

### Publishes
- `AnomalyDetected`
- `DecisionCardCreated`
- `DecisionCardAcknowledged`
- `DecisionCardOverridden`
- `DecisionCardDismissed`
- `DecisionCardExpired`

### Subscribes
- `PayrollProcessed`
- `AttendancePeriodClosed`
- `ComplianceValidationFailed`
- `PerformancePipCreated`

### Read models produced or enriched
- `decision_cards_view`
- enriches `manager_dashboard_view` with actionable anomaly signals


## ewa (FinancialWellnessService — in-process)

> **RESOLVED (Phase 3.25):** No standalone `ewa-financial-service` microservice exists. EWA functionality is implemented as `FinancialWellnessService` in `backend/services/finance/ewa.py`, used as an in-process dependency of `payroll-service` (`payroll_service.py` line 392: `financial_wellness_service: FinancialWellnessService | None = None`). EWA payouts are executed through `banking_api.py` (Raast payout). No standalone gateway route `/api/v1/financial-wellness` exists. ARG-002 in BACKEND_GAP_REGISTER.md is CLOSED.

### Responsibilities
- Manage earned wage access disbursements and salary advances (in-process within payroll-service).
- Enforce eligibility rules (tenure, active status, outstanding advance limits).
- Inject repayment deductions into payroll-service for active advance schedules.
- Route disbursements through `bank-service` via `banking_api.py`.

### Owned entities
- `EWARequest`
- `SalaryAdvance`
- `RepaymentSchedule`
- `PayrollDeduction`

### Canonical APIs
- No standalone API endpoints. EWA operations are accessed via payroll-service and bank-service endpoints. `banking_api.py` handles EWA/salary advance Raast payouts.

### Dependencies
- `payroll-service` for deduction injection.
- `employee-service` for employment status and compensation context.
- `bank-service` for disbursement execution.
- `auth-service` for advance approval authorization.
- `notification-service` for approval and repayment reminders.

### Supported workflows
- `ewa_disbursement`
- `advance_request`

### Publishes
- `EWARequested`, `EWAApproved`, `EWADisbursed`, `EWARejected`
- `AdvanceRequested`, `AdvanceApproved`, `AdvanceDisbursed`, `AdvanceRejected`
- `RepaymentDeductionInjected`

### Subscribes
- `PayrollProcessed`
- `EmployeeStatusChanged`
- `AttendancePeriodClosed`

### Read models produced or enriched
- `financial_wellness_view`


## bank-service

### Responsibilities
- Generate bank-specific salary disbursement files per bank format requirements.
- Execute Raast instant payment payouts for salary and EWA disbursements.
- Track payment status per employee per period.
- Run reconciliation engine against payroll and disbursement records.

### Owned entities
- `DisbursementBatch`
- `PaymentRecord`
- `ReconciliationReport`
- `EmployeeBankAccount`

### Canonical APIs
- 11 endpoints (`/api/v1/banking`). Full surface: `docs/services/bank-service.md`.

### Dependencies
- `payroll-service` for finalized payroll records.
- `FinancialWellnessService` (in-process in payroll-service) for EWA and advance disbursement requests — RESOLVED: no standalone ewa-financial-service container.
- `employee-service` for bank account and CNIC validation context.
- `audit-service` for immutable payment records.
- `notification-service` for payment confirmations and failure alerts.
- Raast API and bank APIs (per-bank adapters).

### Supported workflows
- `salary_disbursement`
- `payment_reconciliation`

### Publishes
- `DisbursementBatchCreated`, `DisbursementSubmitted`, `DisbursementConfirmed`, `DisbursementFailed`
- `PaymentConfirmed`, `PaymentFailed`
- `ReconciliationCompleted`, `ReconciliationExceptionRaised`

### Subscribes
- `PayrollPaid`
- `EWADisbursed`
- `AdvanceDisbursed`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `disbursement_status_view`
- `reconciliation_view`


## reporting-analytics-service

### Responsibilities
- Aggregate data from read models across all domain services.
- Produce operational, compliance, predictive, and anomaly reports.
- Emit anomaly signals to `decision-service` for Guardian processing.
- Provide historical trend data and forecasting for dashboards.

### Owned entities
- `ReportDefinition`
- `ReportExecution`
- `AnalyticsProjection`

### Canonical APIs
- 9 endpoints (`/api/v1/analytics`). Full surface: `docs/services/reporting-analytics-service.md`.

### Dependencies
- All domain read models (read-only consumers; no transactional store access).
- `decision-service` as anomaly signal consumer.
- `audit-service` for report generation audit.

### Supported workflows
- `report_generation`

### Publishes
- `ReportGenerated`
- `AnomalySignalEmitted`

### Subscribes
- `PayrollProcessed`, `PayrollPaid`
- `AttendancePeriodClosed`
- `ComplianceSubmitted`, `ComplianceAcknowledged`, `ComplianceSubmissionFailed`
- `EmployeeStatusChanged`

### Read models produced or enriched
- `analytics_dashboard_view`


## whatsapp-service

### Responsibilities
- Handle inbound WhatsApp messages: intent parsing, session management, identity verification, and domain action dispatch.
- Manage phone ↔ employee identity mapping with OTP verification.
- Enforce RBAC through session-bound role context.
- Log all conversation events for analytics and audit.

### Owned entities
- `WhatsAppIdentityMap`
- `WhatsAppSession`
- `WhatsAppConversationEvent`

### Canonical APIs
- 7 endpoints (`/api/v1/whatsapp`). Full surface: `docs/services/whatsapp-service.md`.

### Dependencies
- `employee-service` for identity resolution and role context.
- `auth-service` for OTP issuance and session authorization.
- `payroll-service` for payslip data.
- `leave-service` for balance check and leave application dispatch.
- `notification-service` for shared outbound channel.
- WhatsApp Business API provider.

### Supported workflows
- `whatsapp_payslip_request`
- `whatsapp_leave_application`
- `whatsapp_approval_action`
- `whatsapp_alert_dispatch`

### Publishes
- `WhatsAppIdentityRegistered`, `WhatsAppIdentityVerified`, `WhatsAppIdentityRevoked`
- `WhatsAppSessionStarted`, `WhatsAppSessionExpired`
- `WhatsAppMessageReceived`, `WhatsAppMessageSent`
- `WhatsAppApprovalActioned`

### Subscribes
- `PayrollProcessed`
- `LeaveRequestSubmitted`, `LeaveRequestApproved`, `LeaveRequestRejected`
- `NotificationQueued` (WhatsApp channel)

### Read models produced or enriched
- `whatsapp_session_view`
- `whatsapp_conversation_view`


## expense-service

### Responsibilities
- Manage employee expense claims from draft through approval to reimbursement.
- Handle receipt attachments and category-based policy validation.
- Export approved claims to accounting systems.
- Separate from `ewa-financial-service` (payroll-linked finance).

### Owned entities
- `ExpenseClaim`
- `ExpenseReceipt`
- `ExpenseCategory`

### Canonical APIs
- 10 endpoints (`/api/v1/expenses`). Full surface: `docs/services/expense-service.md`.

### Dependencies
- `employee-service` for employee and manager context.
- `auth-service` for submitter and approver authorization.
- `notification-service` for submission and decision notifications.
- `audit-service` for claim approval audit trail.

### Supported workflows
- `expense_reimbursement`

### Publishes
- `ExpenseClaimSubmitted`, `ExpenseClaimApproved`, `ExpenseClaimRejected`, `ExpenseClaimReimbursed`

### Subscribes
- `EmployeeStatusChanged`

### Read models produced or enriched
- `expense_claims_view`


## helpdesk-service

### Responsibilities
- Manage employee-initiated HR support tickets: creation, routing, SLA tracking, and resolution.
- Provide knowledge base for self-service resolution.
- Emit SLA breach events for automation-driven escalation.
- Does NOT own or mutate core HR domain data.

### Owned entities
- `HelpDeskTicket`
- `TicketComment`
- `TicketCategory`
- `KnowledgeBaseArticle`

### Canonical APIs
- 13 endpoints (`/api/v1/helpdesk`). Full surface: `docs/services/helpdesk-service.md`.

### Dependencies
- `employee-service` for employee identity and department routing context.
- `auth-service` for authorization.
- `notification-service` for ticket status updates and SLA breach alerts.
- `audit-service` for ticket mutation audit trail.

### Supported workflows
- `hr_ticket_resolution`

### Publishes
- `TicketCreated`
- `TicketAssigned`
- `TicketResolved`
- `TicketClosed`
- `TicketReopened`
- `TicketCommentAdded`
- `SLABreached`

### Subscribes
- `EmployeeStatusChanged`
- `PayrollProcessed`

### Read models produced or enriched
- `helpdesk_tickets_view`
- `helpdesk_sla_view`


## automation-service

### Responsibilities
- Execute automation rules: event-triggered only (event-type matching against canonical event types via `automation_contract.py`). Schedule-triggered and threshold-triggered are NOT implemented — see BACKEND_GAP_REGISTER EG-003.
- Dispatch actions to domain services via canonical APIs.
- Manage automation rule lifecycle and execution history.
- Does NOT own business logic — orchestrates; domain services execute.

### Owned entities
- `AutomationRule`
- `AutomationExecution`
- `AutomationExecutionLog`

### Canonical APIs
- 10 endpoints (`/api/v1/automations`). Full surface: `docs/services/automation-service.md`.

### Dependencies
- All domain services (as action targets via their canonical APIs).
- `auth-service` for admin-only rule management authorization.
- `notification-service` for notification-type action dispatch.
- `audit-service` for execution audit trail.
- Background jobs infrastructure for schedule execution.

### Supported workflows
- `automation_execution`

### Publishes
- `AutomationTriggered`
- `AutomationExecuted`
- `AutomationFailed`
- `AutomationDisabled`

### Subscribes
- All canonical domain events (filtered by registered automation rules per tenant).

### Read models produced or enriched
- `automation_execution_view`


## Coverage checklist

- Every service listed by the API gateway route registry is represented here.
- Every owned entity is defined in `docs/canon/domain-model.md`.
- Every published and subscribed event is defined in `docs/canon/event-catalog.md`.
- Every supported workflow is defined in `docs/canon/workflow-catalog.md`.
