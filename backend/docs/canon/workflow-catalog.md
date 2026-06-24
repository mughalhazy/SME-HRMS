# Workflow Catalog

This catalog defines deterministic HR workflows and maps each workflow to services, entities, states, and events.

> NOTE (Group C fix, 2026-06-13): This catalog defines 27 workflows (`##` sections below the service registry), covering all services in the registry below. The `compliance_submission` workflow (compliance-service) was the last of the 18 workflows added under the OIG-12/B1 resolution series to be completed.

## Valid service registry
- `employee-service`
- `attendance-service`
- `leave-service`
- `travel-service`
- `payroll-service`
- `hiring-service`
- `auth-service`
- `notification-service`
- `settings-service`
- `project-service`
- `workflow-service`
- `search-service`
- `engagement-service`
- `automation-service`
- `decision-service`
- `ewa-financial-service`
- `bank-service`
- `expense-service`
- `helpdesk-service`
- `whatsapp-service`
- `reporting-analytics-service`
- `audit-service`
- `integration-service`
- `compliance-service`

## employee_onboarding

### Owning service
- `employee-service`

### Participating services
- `hiring-service` (optional upstream source)
- `auth-service`
- `notification-service`
- `settings-service`
- `attendance-service` (consumer of eligibility)
- `leave-service` (consumer of eligibility)
- `payroll-service` (consumer of eligibility)

### Entities referenced
- `Employee`
- `Department`
- `Role`
- `Candidate`
- `UserAccount`

### Trigger
- HR initiates a direct hire, or `CandidateHired` is received from `hiring-service`.

### State transitions
- `Employee: none -> Draft -> Active`
- `UserAccount: none -> Invited/Active` when access is provisioned as part of onboarding

### Events
- Consumes:
  - `CandidateHired`
- Publishes:
  - `EmployeeCreated`
  - `EmployeeStatusChanged`
- Downstream follow-on events:
  - `UserProvisioned` is emitted by `auth-service` when onboarding invokes access provisioning.

### Steps
1. Validate that `Department` and `Role` exist and are assignable.
2. Create `Employee` in `Draft` with required employment metadata.
3. Assign reporting line, department, and role references.
4. Enforce uniqueness for `employee_number` and `email`.
5. Activate the employee on the effective hire date.
6. Optionally provision a linked `UserAccount` and baseline `RoleBinding`.
7. Notify downstream services and read-model projections.

## attendance_tracking

### Owning service
- `attendance-service`

### Participating services
- `employee-service`
- `auth-service`
- `notification-service`
- `settings-service`

### Entities referenced
- `AttendanceRecord`
- `Employee`

### Trigger
- Employee check-in/out event, biometric import, or administrative correction.

### State transitions
- `AttendanceRecord: none -> Captured -> Validated -> Approved -> Locked`

### Events
- Consumes:
  - `EmployeeCreated`
  - `EmployeeStatusChanged`
- Publishes:
  - `AttendanceCaptured`
  - `AttendanceValidated`
  - `AttendanceApproved`
  - `AttendanceLocked`
  - `AttendancePeriodClosed`

### Steps
1. Create or update `AttendanceRecord` in `Captured`.
2. Normalize timestamps and calculate `total_hours`.
3. Classify `attendance_status` and validate against policy.
4. Transition validated records to `Validated`.
5. Approve records for payroll inclusion.
6. Lock the pay period and emit a period-closure event.

## leave_request

### Owning service
- `leave-service`
- `travel-service`

### Participating services
- `employee-service`
- `auth-service`
- `notification-service`
- `settings-service`
- `payroll-service`

### Entities referenced
- `LeaveRequest`
- `Employee`

### Trigger
- Employee creates and submits a leave request.

### State transitions
- `LeaveRequest: none -> Draft -> Submitted -> Approved/Rejected/Cancelled`

### Events
- Consumes:
  - `EmployeeCreated`
  - `EmployeeStatusChanged`
- Publishes:
  - `LeaveRequestSubmitted`
  - `LeaveRequestApproved`
  - `LeaveRequestRejected`
  - `LeaveRequestCancelled`

### Steps
1. Create `LeaveRequest` in `Draft`.
2. Calculate `total_days` and validate overlap/policy rules.
3. Submit the request and assign an approver.
4. Notify the approver.
5. Approve or reject the request with a decision timestamp.
6. Allow policy-governed cancellation when applicable.
7. Propagate approved leave to payroll consumers.

## payroll_processing

### Owning service
- `payroll-service`

### Participating services
- `employee-service`
- `attendance-service`
- `leave-service`
- `travel-service`
- `auth-service`
- `notification-service`
- `settings-service`

### Entities referenced
- `PayrollRecord`
- `Employee`
- `AttendanceRecord`
- `LeaveRequest`

### Trigger
- Period close, scheduled payroll run, or off-cycle payroll request.

### State transitions
- `PayrollRecord: none -> Draft -> Processed -> Paid`
- `PayrollRecord: Draft/Processed -> Cancelled`

### Events
- Consumes:
  - `AttendancePeriodClosed`
  - `LeaveRequestApproved`
  - `EmployeeStatusChanged`
- Publishes:
  - `PayrollDrafted`
  - `PayrollProcessed`
  - `PayrollPaid`
  - `PayrollCancelled`

### Steps
1. Select eligible employees for the pay period.
2. Create `PayrollRecord` drafts.
3. Join approved attendance and leave impacts.
4. Calculate gross and net pay.
5. Transition valid records to `Processed`.
6. Mark paid records on successful disbursement.
7. Cancel records only for reversal or invalidation scenarios.


## project_resource_allocation

### Owning service
- `project-service`

### Participating services
- `employee-service`
- `workflow-service`
- `notification-service`
- `auth-service`

### Entities referenced
- `Project`
- `ProjectAssignment`
- `Employee`

### Trigger
- PMO, delivery, or operations creates a project assignment or adjusts an allocation.

### State transitions
- `Project: none -> Draft -> Planned/Active -> OnHold/Completed/Cancelled`
- `ProjectAssignment: none -> PendingApproval/Allocated -> Rejected/Released`

### Events
- Consumes:
  - `EmployeeCreated`
  - `EmployeeUpdated`
  - `EmployeeStatusChanged`
- Publishes:
  - `ProjectCreated`
  - `ProjectStatusChanged`
  - `ProjectAssignmentRequested`
  - `ProjectAssignmentAllocated`
  - `ProjectAssignmentRejected`
  - `ProjectAssignmentReleased`
  - `ProjectAllocationUpdated`

### Steps
1. Create `Project` with staffing-governance settings and planned dates.
2. Resolve employee/manager references through `employee-service` read models only.
3. Validate overlapping allocations so an employee cannot exceed 100 percent across active assignments.
4. Create an immediate assignment or route it through centralized approval when sign-off is required.
5. Record every allocation request, approval, rejection, update, and release in the allocation ledger.
6. Publish audit-ready events for downstream reporting, notifications, and projection refresh.


## settings_administration

### Owning service
- `settings-service`

### Participating services
- `auth-service`
- `attendance-service`
- `leave-service`
- `travel-service`
- `payroll-service`
- `notification-service`

### Entities referenced
- `AttendanceRule`
- `LeavePolicy`
- `PayrollSettings`

### Trigger
- HR operations or payroll administration updates company-wide configuration.

### State transitions
- `AttendanceRule: none -> Draft -> Active/Archived`
- `LeavePolicy: none -> Draft -> Active/Archived`
- `PayrollSettings: none -> Draft -> Active/Archived`

### Events
- Publishes:
  - `AttendanceRuleConfigured`
  - `LeavePolicyConfigured`
  - `PayrollSettingsConfigured`
  - `SettingsPublished`

### Steps
1. Draft or revise attendance rules for schedule and lateness compliance.
2. Draft or revise leave policies for accrual, carry-forward, and approval behavior.
3. Draft or revise payroll settings for pay schedule, cutoff, and deduction controls.
4. Validate cross-domain guardrails before activation.
5. Activate the approved configuration and publish settings events for downstream consumers.
6. Refresh `settings_configuration_view` and any dependent operational projections.

## candidate_hiring

### Owning service
- `hiring-service`

### Participating services
- `employee-service`
- `auth-service`
- `notification-service`

### Entities referenced
- `JobPosting`
- `Candidate`
- `Interview`
- `Department`
- `Role`
- `Employee`

### Trigger
- Recruiter opens a job posting or receives a candidate application.

### State transitions
- `JobPosting: Draft -> Open -> Closed/Filled` with optional `OnHold`
- `Candidate: none -> Applied -> Screening -> Interviewing -> Offered -> Hired`
- `Candidate: Applied/Screening/Interviewing/Offered -> Rejected/Withdrawn`
- `Interview: none -> Scheduled -> Completed/Cancelled/NoShow`

### Events
- Consumes:
  - `DepartmentUpdated`
  - `RoleUpdated`
- Publishes:
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

### Steps
1. Create a `JobPosting` and open it for applications.
2. Capture direct or imported `Candidate` applications.
3. Progress candidates through screening and interviewing stages.
4. Schedule `Interview` rounds and optionally sync with Google Calendar.
5. Capture interview outcomes and recommendations.
6. Move successful candidates to `Offered`.
7. Mark accepted candidates as `Hired` and emit `CandidateHired`.

## performance_management

### Owning service
- `performance-service`

### Participating services
- `employee-service`
- `auth-service`
- `workflow-service`
- `audit-service`
- `notification-service`

### Entities referenced
- `ReviewCycle`
- `Goal`
- `Feedback`
- `CalibrationSession`
- `PipPlan`
- `Employee`

### Trigger
- HR opens a review cycle, an employee submits a goal/OKR, calibration sign-off is requested, or a manager launches a PIP.

### State transitions
- `ReviewCycle: none -> Draft -> PendingApproval -> Open -> Closed`
- `Goal: none -> Draft -> Submitted -> Approved/Rejected`
- `CalibrationSession: none -> Draft -> Submitted -> Finalized/Rejected`
- `PipPlan: none -> Draft -> Submitted -> Active/Rejected -> Completed/Cancelled`

### Events
- Consumes:
  - `EmployeeCreated`
  - `EmployeeUpdated`
  - `EmployeeStatusChanged`
- Publishes:
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

### Steps
1. Create the `ReviewCycle` in `Draft` and validate the owner against the `employee-service` read model.
2. Open the cycle through the centralized workflow engine so performance windows are approval-gated.
3. Create `Goal` records in `Draft`, then submit them for manager approval via workflow.
4. Record continuous `Feedback` entries against the employee and optionally the active review cycle.
5. Create `CalibrationSession` records, submit them to HR sign-off, and persist finalized ratings.
6. Create `PipPlan` records with milestones, route them for approval, and track milestone completion until closure.
7. Emit audit records and canonical events for every privileged state transition.




## travel_request

### Owning service
- `travel-service`

### Participating services
- `employee-service`
- `auth-service`
- `notification-service`
- `settings-service`

### Entities referenced
- `TravelRequest`
- `TravelItinerarySegment`
- `Employee`

### Trigger
- Employee or manager creates and submits a travel request for approval.

### State transitions
- `TravelRequest: none -> Draft -> Submitted -> Approved/Rejected`
- `TravelRequest: Approved -> Booked -> Completed`
- `TravelRequest: Draft/Submitted/Approved/Booked -> Cancelled`

### Events
- Consumes:
  - `EmployeeCreated`
  - `EmployeeUpdated`
  - `EmployeeStatusChanged`
- Publishes:
  - `TravelRequestCreated`
  - `TravelRequestSubmitted`
  - `TravelRequestApproved`
  - `TravelRequestRejected`
  - `TravelItineraryUpdated`
  - `TravelRequestCancelled`
  - `TravelRequestCompleted`

### Steps
1. Create `TravelRequest` in `Draft` and validate traveler/manager references against the `employee-service` read model.
2. Submit the request through the centralized workflow engine using manager approval followed by travel-desk approval.
3. Emit tenant-scoped audit records for submission and every workflow-backed decision.
4. Notify the approver(s) and traveler as the workflow progresses.
5. Capture itinerary segments and booking references after approval.
6. Allow cancellation prior to completion and preserve the full mutation trail.
7. Mark the request `Completed` after the booked trip concludes.

## projection_search_indexing

### Owning service
- `search-service`

### Participating services
- `employee-service`
- `hiring-service`
- `integration-service`
- `notification-service`

### Entities referenced
- `SearchDocument`
- `SearchProjectionState`
- `SearchEventCheckpoint`

### Trigger
- Canonical domain event received via integration-service outbox pipeline.

### State transitions
- `SearchDocument: none -> Indexed -> Updated -> Archived`

### Events
- Consumes:
  - `EmployeeCreated`
  - `EmployeeUpdated`
  - `EmployeeStatusChanged`
  - `DepartmentCreated`
  - `DepartmentUpdated`
  - `RoleCreated`
  - `RoleUpdated`
  - `CandidateApplied`
  - `CandidateStageChanged`
  - `CandidateHired`
  - `DocumentStored`
  - `DocumentUpdated`
  - `PayrollProcessed`
  - `PayrollPaid`
  - `PayrollCancelled`
- Publishes:
  - None; indexing side effects remain internal projections.

### Steps
1. Receive domain event via integration-service outbox pipeline.
2. Extract indexable fields per entity type.
3. Upsert `SearchDocument` projection with tenant-safe scope.
4. Update `SearchProjectionState` checkpoint to mark event processed.
5. Serve updated results via `/api/v1/search`.

## engagement_feedback_collection

### Owning service
- `engagement-service`

### Participating services
- `employee-service`
- `notification-service`
- `workflow-service`

### Entities referenced
- `EngagementSurvey`
- `EngagementSurveyQuestion`
- `EngagementSurveyResponse`
- `EngagementSurveyAnswer`
- `EngagementSurveyAggregate`

### Trigger
- HR initiates a survey campaign or pulse check.

### State transitions
- `EngagementSurvey: Draft -> Active -> Closed -> Archived`

### Events
- Publishes:
  - `SurveyLaunched`
  - `SurveyResponseRecorded`
  - `SurveyClosed`

### Steps
1. Create survey with questions and set target population scope.
2. Resolve target employees via employee-service read model.
3. Notify employees of open survey via notification-service.
4. Collect responses within campaign window.
5. Aggregate results per survey.
6. Close survey and publish `SurveyClosed`.
7. Archive survey after reporting window.

## automation_execution

### Owning service
- `automation-service`

### Participating services
- `notification-service`
- `workflow-service`
- `integration-service`

### Entities referenced
- `AutomationRule`
- `AutomationExecution`

### Trigger
- Domain event matching a registered tenant automation rule.

### State transitions
- `AutomationExecution: none -> Triggered -> Running -> Completed/Failed`

### Events
- Consumes:
  - All registered canonical domain events (filtered by automation rules per tenant).
- Publishes:
  - `AutomationTriggered`
  - `AutomationCompleted`
  - `AutomationFailed`

### Steps
1. Receive trigger event.
2. Match against active automation rules for the tenant.
3. Evaluate rule conditions.
4. Execute configured action steps in order.
5. Record execution result in `AutomationExecution`.
6. Notify on failure if the rule has a failure notification configured.

## anomaly_review

### Owning service
- `decision-service`

### Participating services
- `payroll-service`
- `attendance-service`
- `notification-service`
- `audit-service`

### Entities referenced
- `DecisionCard`
- `AnomalyReport`

### Trigger
- Payroll anomaly detector or compliance engine flags an out-of-range signal.

### State transitions
- `AnomalyReport: Flagged -> UnderReview -> Resolved/Dismissed`

### Events
- Consumes:
  - `PayrollProcessed`
  - `AttendanceValidated`
- Publishes:
  - `AnomalyFlagged`
  - `AnomalyResolved`

### Steps
1. Detect anomaly from input signal.
2. Create `DecisionCard` with rationale, confidence score, source domain, and severity.
3. Route to HR/Finance reviewer.
4. Reviewer approves, overrides, or dismisses the anomaly.
5. Publish audit record with actor, action, and timestamp.
6. Notify affected parties of resolution.

## ewa_disbursement

### Owning service
- `ewa-financial-service`

### Participating services
- `employee-service`
- `payroll-service`
- `bank-service`
- `notification-service`

### Entities referenced
- `EWARequest`
- `PayrollDeduction`

### Trigger
- Employee submits an earned wage access request.

### State transitions
- `EWARequest: Draft -> Pending -> Approved/Rejected -> Disbursed`

### Events
- Publishes:
  - `EWARequested`
  - `EWAApproved`
  - `EWARejected`
  - `EWADisbursed`

### Steps
1. Validate employee eligibility and available earned balance.
2. Create `EWARequest` in `Pending`.
3. Evaluate request against tenant EWA policy limits.
4. Approve or reject; notify employee.
5. On approval, trigger bank disbursement via bank-service.
6. Register `PayrollDeduction` entry for repayment in next payroll cycle.
7. Notify employee of disbursement confirmation.

## advance_request

### Owning service
- `ewa-financial-service`

### Participating services
- `employee-service`
- `payroll-service`
- `notification-service`
- `workflow-service`

### Entities referenced
- `AdvanceRequest`
- `PayrollDeduction`

### Trigger
- Employee or HR submits an advance salary request.

### State transitions
- `AdvanceRequest: Draft -> PendingApproval -> Approved/Rejected -> Deducted`

### Events
- Publishes:
  - `AdvanceRequested`
  - `AdvanceApproved`
  - `AdvanceRejected`

### Steps
1. Submit advance request with amount and rationale.
2. Route for manager/HR approval via workflow-service.
3. On approval, record advance amount and repayment schedule.
4. Register `PayrollDeduction` entries for repayment across future payroll cycles.
5. Notify employee of outcome.

## access_provisioning

### Owning service
- `auth-service`

### Participating services
- `employee-service`
- `settings-service`
- `notification-service`

### Entities referenced
- `UserAccount`
- `RoleBinding`
- `PermissionPolicy`

### Trigger
- `EmployeeCreated` event or HR-initiated role change.

### State transitions
- `UserAccount: none -> Invited -> Active -> Suspended/Deactivated`

### Events
- Consumes:
  - `EmployeeCreated`
  - `EmployeeStatusChanged`
- Publishes:
  - `UserProvisioned`
  - `UserDeprovisioned`
  - `RoleBindingAssigned`

### Steps
1. Create `UserAccount` linked to employee record.
2. Assign baseline `RoleBinding` per employment type and tier from settings-service.
3. Apply `PermissionPolicy` rules.
4. Send activation invitation to employee.
5. Activate account on first login.
6. Deprovision account on `EmployeeStatusChanged: Terminated`.

## notification_dispatch

### Owning service
- `notification-service`

### Participating services
- `employee-service`
- `settings-service`
- `whatsapp-service`
- `integration-service`

### Entities referenced
- `NotificationTemplate`
- `NotificationLog`

### Trigger
- Any service emitting an event that maps to a registered tenant notification rule.

### State transitions
- `NotificationLog: Queued -> Sent -> Delivered/Failed`

### Events
- Consumes:
  - All tenant-configured notification trigger events.
- Publishes:
  - `NotificationSent`
  - `NotificationFailed`

### Steps
1. Receive trigger event.
2. Match to notification template.
3. Resolve recipient(s) via employee-service.
4. Render message from template.
5. Deliver via configured channel (email, SMS, WhatsApp, in-app).
6. Log delivery result in `NotificationLog`.

## salary_disbursement

### Owning service
- `payroll-service`

### Participating services
- `bank-service`
- `notification-service`
- `audit-service`

### Entities referenced
- `PayrollRecord`
- `DisbursementBatch`

### Trigger
- `PayrollProcessed` event after HR/Finance approval.

### State transitions
- `PayrollRecord: Processed -> DisbursementPending -> Paid/DisbursementFailed`

### Events
- Consumes:
  - `PayrollProcessed`
- Publishes:
  - `DisbursementInitiated`
  - `PayrollPaid`
  - `DisbursementConfirmed`

### Steps
1. Validate approved payroll records.
2. Generate disbursement batch file.
3. Submit to bank-service for processing.
4. Await bank confirmation.
5. Mark records `Paid` on confirmed transfer.
6. Post payslips and notify employees.
7. Publish audit record with actor and timestamp.

## payment_reconciliation

### Owning service
- `bank-service`

### Participating services
- `payroll-service`
- `audit-service`
- `notification-service`

### Entities referenced
- `DisbursementBatch`
- `BankTransaction`

### Trigger
- Bank statement or transaction feed received after disbursement.

### State transitions
- `BankTransaction: Received -> Matched/Unmatched -> Reconciled/Flagged`

### Events
- Consumes:
  - `DisbursementInitiated`
- Publishes:
  - `PaymentReconciled`
  - `PaymentDiscrepancyFlagged`

### Steps
1. Receive bank transaction records.
2. Match against submitted disbursement batch.
3. Mark matched records as reconciled.
4. Flag unmatched or short-payment transactions.
5. Escalate discrepancies for anomaly review via decision-service.
6. Publish reconciliation outcome and audit record.

## expense_reimbursement

### Owning service
- `expense-service`

### Participating services
- `employee-service`
- `payroll-service`
- `workflow-service`
- `notification-service`

### Entities referenced
- `ExpenseClaim`
- `ExpenseLineItem`

### Trigger
- Employee submits an expense claim.

### State transitions
- `ExpenseClaim: Draft -> Submitted -> UnderReview -> Approved/Rejected -> Reimbursed`

### Events
- Publishes:
  - `ExpenseClaimSubmitted`
  - `ExpenseClaimApproved`
  - `ExpenseClaimRejected`
  - `ExpenseReimbursed`

### Steps
1. Submit expense claim with line items and receipts.
2. Route for manager approval via workflow-service.
3. Validate against expense policy limits.
4. Approve or reject with notes; notify employee.
5. On approval, trigger reimbursement via payroll integration or direct payment.
6. Mark claim `Reimbursed` and publish audit record.

## report_generation

### Owning service
- `reporting-analytics-service`

### Participating services
- `employee-service`
- `payroll-service`
- `attendance-service`
- `audit-service`

### Entities referenced
- `ReportTemplate`
- `ReportExecution`

### Trigger
- Scheduled report job or on-demand report request.

### State transitions
- `ReportExecution: Queued -> Running -> Completed/Failed`

### Events
- Publishes:
  - `ReportGenerated`
  - `ReportFailed`

### Steps
1. Accept report request with parameters (scope, period, filters).
2. Resolve data from read models; do not read transactional stores directly.
3. Apply tenant-safe access filters.
4. Render report output (PDF/CSV/JSON).
5. Deliver or store output.
6. Log execution record in `ReportExecution`.

## hr_ticket_resolution

### Owning service
- `helpdesk-service`

### Participating services
- `employee-service`
- `notification-service`
- `workflow-service`
- `audit-service`

### Entities referenced
- `HRTicket`
- `TicketComment`

### Trigger
- Employee or manager submits an HR support ticket.

### State transitions
- `HRTicket: Open -> Assigned -> InProgress -> PendingEmployee -> Resolved/Closed`

### Events
- Publishes:
  - `TicketOpened`
  - `TicketAssigned`
  - `TicketResolved`
  - `TicketClosed`

### Steps
1. Employee submits ticket with category and description.
2. Auto-assign to HR queue based on category.
3. HR acknowledges and investigates.
4. Resolve or escalate to specialist.
5. Notify employee at each stage transition.
6. Close with resolution summary.
7. Publish audit record with actor, action, and timestamp.

## whatsapp_payslip_request

### Owning service
- `whatsapp-service`

### Participating services
- `payroll-service`
- `auth-service`
- `notification-service`

### Entities referenced
- `WhatsAppSession`
- `PayrollRecord`

### Trigger
- Employee sends a payslip request via WhatsApp.

### State transitions
- `WhatsAppSession: Intent -> Verified -> Fulfilled/Rejected`

### Events
- Consumes:
  - `WhatsAppIntentReceived`
- Publishes:
  - `PayslipDelivered`
  - `WhatsAppRequestFailed`

### Steps
1. Receive intent from WhatsApp channel.
2. Verify employee identity via auth-service.
3. Retrieve latest payslip from payroll-service.
4. Format payslip for WhatsApp delivery.
5. Deliver to employee WhatsApp number.
6. Log delivery result.

## whatsapp_leave_application

### Owning service
- `whatsapp-service`

### Participating services
- `leave-service`
- `auth-service`
- `notification-service`
- `employee-service`

### Entities referenced
- `WhatsAppSession`
- `LeaveRequest`

### Trigger
- Employee sends a leave request via WhatsApp.

### State transitions
- `WhatsAppSession: Intent -> Verified -> RequestCreated -> Notified`

### Events
- Consumes:
  - `WhatsAppIntentReceived`
- Publishes:
  - `LeaveRequestCreatedViaWhatsApp`

### Steps
1. Receive leave intent from WhatsApp channel.
2. Verify employee identity via auth-service.
3. Parse leave type, dates, and reason from message.
4. Create `LeaveRequest` via leave-service.
5. Notify employee of submission confirmation.
6. Route approval via standard leave_request workflow.

## whatsapp_approval_action

### Owning service
- `whatsapp-service`

### Participating services
- `workflow-service`
- `auth-service`
- `notification-service`
- `leave-service`

### Entities referenced
- `WhatsAppSession`
- `WorkflowApproval`

### Trigger
- Manager receives an approval notification and responds via WhatsApp.

### State transitions
- `WhatsAppSession: Intent -> VerifiedApprover -> ActionApplied`

### Events
- Consumes:
  - `WhatsAppIntentReceived`
- Publishes:
  - `ApprovalActionTakenViaWhatsApp`

### Steps
1. Receive approval intent from WhatsApp channel.
2. Verify approver identity and active pending approvals via auth-service.
3. Parse approve/reject action from message.
4. Apply action to workflow engine.
5. Notify submitter of outcome.
6. Publish audit record with actor, action, and timestamp.

## whatsapp_alert_dispatch

### Owning service
- `whatsapp-service`

### Participating services
- `notification-service`
- `employee-service`
- `integration-service`

### Entities referenced
- `WhatsAppSession`
- `NotificationLog`

### Trigger
- Alert-triggering domain event (anomaly flagged, payroll paid, leave approved, etc.).

### State transitions
- `NotificationLog: Queued -> Sent -> Delivered/Failed`

### Events
- Consumes:
  - Tenant-configured alert trigger events.
- Publishes:
  - `WhatsAppAlertSent`
  - `WhatsAppAlertFailed`

### Steps
1. Receive alert trigger event.
2. Evaluate tenant WhatsApp alert policy.
3. Resolve recipient WhatsApp number via employee-service.
4. Format alert message per template.
5. Deliver via WhatsApp Business API.
6. Log delivery result in `NotificationLog`.

> NOTE (Group C fix, 2026-06-13): The events listed above (`PayslipDelivered`, `WhatsAppRequestFailed`, `LeaveRequestCreatedViaWhatsApp`, `ApprovalActionTakenViaWhatsApp`, `WhatsAppAlertSent`, `WhatsAppAlertFailed`) do not match the canonical `whatsapp-service events` section in `docs/canon/event-catalog.md` (which defines `WhatsAppMessageSent`, `WhatsAppApprovalActioned`, etc.). The event-catalog.md names are canonical (added under the G49 fix and registered in `event_contract.py`'s CANONICAL_EVENT_TYPES). The names in these four whatsapp workflows are workflow-level descriptive aliases for the underlying canonical events and have not been added to event_contract.py — treat as additional context, not separate registry entries.

## compliance_submission

### Owning service
- `compliance-service`

### Participating services
- `payroll-service`
- `employee-service`
- `audit-service`
- `notification-service`

### Entities referenced
- `ComplianceSubmission`
- `ComplianceReport`
- `ComplianceAuditRecord`

### Trigger
- `PayrollProcessed` event triggers the pre-payroll validation gate for the same period, or HR/Finance manually initiates a compliance submission for a pay period.

### State transitions
- `ComplianceSubmission: none -> DRAFT -> VALIDATED -> SUBMITTED -> ACK`
- `ComplianceSubmission: SUBMITTED -> FAILED -> RETRY -> SUBMITTED`

### Events
- Consumes:
  - `PayrollProcessed`
  - `EmployeeStatusChanged`
- Publishes:
  - `ComplianceSubmissionCreated`
  - `ComplianceValidationPassed`
  - `ComplianceValidationFailed`
  - `ComplianceReportGenerated`
  - `ComplianceSubmitted`
  - `ComplianceAcknowledged`
  - `ComplianceSubmissionFailed`
  - `ComplianceRetryQueued`

### Steps
1. Create `ComplianceSubmission` in `DRAFT` for `(organization_id, legal_entity_id, period, submission_type)`.
2. Run pre-payroll validation gate via the country compliance engine against payroll data.
3. On zero violations, transition to `VALIDATED` and publish `ComplianceValidationPassed`; on violations, publish `ComplianceValidationFailed` and block payroll finalization until resolved.
4. Generate statutory report artifacts (FBR Annexure-C, EOBI PR-01, PESSI/SESSI returns) via the country adapter and publish `ComplianceReportGenerated`.
5. Dispatch the submission to the government authority via `government-adapters`, transitioning to `SUBMITTED`.
6. On authority acknowledgement, transition to `ACK` and publish `ComplianceAcknowledged`; on failure, transition to `FAILED` and publish `ComplianceSubmissionFailed`.
7. Failed submissions may be re-queued to `RETRY` and resubmitted, publishing `ComplianceRetryQueued`.
8. Record every transition as an immutable `ComplianceAuditRecord`.
