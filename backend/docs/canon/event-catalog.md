# Event Catalog

This catalog defines the canonical domain events emitted across SME-HRMS services. Every state transition referenced in the domain model and workflow catalog maps to one or more events in this registry.

## Event conventions

- Event names use `PastTense` business language.
- Every event payload includes `event_id`, `event_name`, `occurred_at`, `producer_service`, and `trace_id` metadata.
- Business payloads include the aggregate identifier and the minimum fields required for downstream consumers.
- Events are immutable; corrections emit a new event rather than mutating a prior one.
- Events are published after a successful state transition or side effect commit.

## Registry summary

**Verified event count: 126** (recounted 2026-06-15 from the table below; prior documentation references of 143 or 119 were stale — see EG-002 in `docs/08_reports/BACKEND_GAP_REGISTER.md`).

| Event | Producer | Primary entity | Trigger |
|---|---|---|---|
| `EmployeeCreated` | `employee-service` | `Employee` | Employee onboarding record created. |
| `EmployeeUpdated` | `employee-service` | `Employee` | Non-status employee attributes updated. |
| `EmployeeStatusChanged` | `employee-service` | `Employee` | Employee lifecycle state changes. |
| `DepartmentCreated` | `employee-service` | `Department` | Department created. |
| `DepartmentUpdated` | `employee-service` | `Department` | Department metadata/status updated. |
| `RoleCreated` | `employee-service` | `Role` | Role created. |
| `RoleUpdated` | `employee-service` | `Role` | Role metadata/status updated. |
| `BusinessUnitCreated` | `employee-service` | `BusinessUnit` | Business unit created. |
| `BusinessUnitUpdated` | `employee-service` | `BusinessUnit` | Business unit metadata/status updated. |
| `LegalEntityCreated` | `employee-service` | `LegalEntity` | Legal entity created. |
| `LegalEntityUpdated` | `employee-service` | `LegalEntity` | Legal entity metadata/status updated. |
| `LocationCreated` | `employee-service` | `Location` | Location created. |
| `LocationUpdated` | `employee-service` | `Location` | Location metadata/status updated. |
| `CostCenterCreated` | `employee-service` | `CostCenter` | Cost center created. |
| `CostCenterUpdated` | `employee-service` | `CostCenter` | Cost center metadata/status updated. |
| `GradeBandCreated` | `employee-service` | `GradeBand` | Grade/band created. |
| `GradeBandUpdated` | `employee-service` | `GradeBand` | Grade/band metadata/status updated. |
| `JobPositionCreated` | `employee-service` | `JobPosition` | Job position created. |
| `JobPositionUpdated` | `employee-service` | `JobPosition` | Job position metadata/status updated. |
| `PerformanceReviewCycleCreated` | `performance-service` | `ReviewCycle` | Review cycle created in draft. |
| `PerformanceReviewCycleOpened` | `performance-service` | `ReviewCycle` | Review cycle approved and opened. |
| `PerformanceReviewCycleClosed` | `performance-service` | `ReviewCycle` | Review cycle closed. |
| `PerformanceGoalCreated` | `performance-service` | `Goal` | Goal/OKR drafted. |
| `PerformanceGoalSubmitted` | `performance-service` | `Goal` | Goal submitted for approval. |
| `PerformanceGoalApproved` | `performance-service` | `Goal` | Goal approved through workflow. |
| `PerformanceGoalRejected` | `performance-service` | `Goal` | Goal rejected through workflow. |
| `PerformanceFeedbackRecorded` | `performance-service` | `Feedback` | Continuous feedback recorded. |
| `PerformanceCalibrationCreated` | `performance-service` | `CalibrationSession` | Calibration session drafted. |
| `PerformanceCalibrationSubmitted` | `performance-service` | `CalibrationSession` | Calibration sign-off requested. |
| `PerformanceCalibrationFinalized` | `performance-service` | `CalibrationSession` | Calibration approved and finalized. |
| `PerformanceCalibrationRejected` | `performance-service` | `CalibrationSession` | Calibration rejected. |
| `PerformancePipCreated` | `performance-service` | `PipPlan` | Performance improvement plan drafted. |
| `PerformancePipSubmitted` | `performance-service` | `PipPlan` | PIP submitted for approval. |
| `PerformancePipActive` | `performance-service` | `PipPlan` | PIP approved and activated. |
| `PerformancePipRejected` | `performance-service` | `PipPlan` | PIP rejected. |
| `PerformancePipProgressUpdated` | `performance-service` | `PipPlan` | PIP milestone progress updated. |
| `EngagementSurveyCreated` | `engagement-service` | `Survey` | Engagement survey created in draft. |
| `EngagementSurveyPublished` | `engagement-service` | `Survey` | Engagement survey opened for responses. |
| `EngagementSurveyClosed` | `engagement-service` | `Survey` | Engagement survey closed for response intake. |
| `EngagementSurveyResponseSubmitted` | `engagement-service` | `SurveyResponse` | Employee response submitted to a survey. |
| `EngagementSurveyResultsAggregated` | `engagement-service` | `AggregatedSurveyResult` | Survey rollups recomputed for analytics consumers. |
| `AttendanceCaptured` | `attendance-service` | `AttendanceRecord` | Attendance record captured. |
| `AttendanceValidated` | `attendance-service` | `AttendanceRecord` | Attendance validated. |
| `AttendanceApproved` | `attendance-service` | `AttendanceRecord` | Attendance approved for payroll/reporting. |
| `AttendanceLocked` | `attendance-service` | `AttendanceRecord` | Attendance record locked. |
| `AttendancePeriodClosed` | `attendance-service` | `AttendanceRecord` | Payroll-safe attendance period closed. |
| `LeaveRequestSubmitted` | `leave-service` | `LeaveRequest` | Leave submitted for approval. |
| `LeaveRequestApproved` | `leave-service` | `LeaveRequest` | Leave approved. |
| `LeaveRequestRejected` | `leave-service` | `LeaveRequest` | Leave rejected. |
| `LeaveRequestCancelled` | `leave-service` | `LeaveRequest` | Leave cancelled. |
| `PayrollDrafted` | `payroll-service` | `PayrollRecord` | Payroll draft created. |
| `PayrollProcessed` | `payroll-service` | `PayrollRecord` | Payroll processed and finalized for payment. |
| `PayrollPaid` | `payroll-service` | `PayrollRecord` | Payroll disbursement completed. |
| `PayrollCancelled` | `payroll-service` | `PayrollRecord` | Payroll invalidated or reversed. |
| `JobPostingOpened` | `hiring-service` | `JobPosting` | Job posting opened. |
| `JobPostingOnHold` | `hiring-service` | `JobPosting` | Job posting placed on hold. |
| `JobPostingClosed` | `hiring-service` | `JobPosting` | Job posting closed or filled. |
| `CandidateApplied` | `hiring-service` | `Candidate` | Candidate application created. |
| `CandidateStageChanged` | `hiring-service` | `Candidate` | Candidate moves between pipeline states. |
| `InterviewScheduled` | `hiring-service` | `Interview` | Interview created in `Scheduled`. |
| `InterviewCompleted` | `hiring-service` | `Interview` | Interview marked `Completed`. |
| `InterviewCancelled` | `hiring-service` | `Interview` | Interview marked `Cancelled`. |
| `InterviewNoShow` | `hiring-service` | `Interview` | Interview marked `NoShow`. |
| `InterviewCalendarSynced` | `hiring-service` | `Interview` | Interview synced to Google Calendar. |
| `CandidateImported` | `hiring-service` | `Candidate` | Candidate imported from external source. |
| `LinkedInCandidatesImported` | `hiring-service` | `Candidate` | Batch LinkedIn import completed. |
| `CandidateHired` | `hiring-service` | `Candidate` | Candidate transitioned to `Hired`. |
| `UserAuthenticated` | `auth-service` | `Session` | Successful login completed. |
| `SessionRevoked` | `auth-service` | `Session` | Logout or forced revocation completed. |
| `UserProvisioned` | `auth-service` | `UserAccount` | New user account provisioned or invited. |
| `UserAccountStatusChanged` | `auth-service` | `UserAccount` | User account locked, unlocked, or disabled. |
| `RoleBindingChanged` | `auth-service` | `RoleBinding` | Role binding granted, revoked, or scope-adjusted. |
| `RefreshTokenRotated` | `auth-service` | `RefreshToken` | Refresh token rotated to continue a session safely. |
| `AuthorizationPolicyUpdated` | `auth-service` | `PermissionPolicy` | Policy or role binding model updated. |
| `NotificationQueued` | `notification-service` | `NotificationMessage` | Notification accepted for delivery. |
| `NotificationSent` | `notification-service` | `NotificationMessage` | Notification delivered successfully. |
| `NotificationFailed` | `notification-service` | `NotificationMessage` | Notification failed after attempt(s). |
| `NotificationSuppressed` | `notification-service` | `NotificationMessage` | Notification intentionally suppressed by preference or policy. |
| `TravelRequestCreated` | `travel-service` | `TravelRequest` | Travel request drafted. |
| `TravelRequestSubmitted` | `travel-service` | `TravelRequest` | Travel request submitted for approval. |
| `TravelRequestApproved` | `travel-service` | `TravelRequest` | Travel request fully approved through workflow. |
| `TravelRequestRejected` | `travel-service` | `TravelRequest` | Travel request rejected through workflow. |
| `TravelItineraryUpdated` | `travel-service` | `TravelRequest` | Itinerary details or booking references updated. |
| `TravelRequestCancelled` | `travel-service` | `TravelRequest` | Travel request cancelled before completion. |
| `TravelRequestCompleted` | `travel-service` | `TravelRequest` | Travel request completed after travel concludes. |
| `ComplianceSubmissionCreated` | `compliance-service` | `ComplianceSubmission` | Compliance submission record created in `DRAFT`. |
| `ComplianceValidationPassed` | `compliance-service` | `ComplianceSubmission` | Pre-payroll validation run — zero violations found. |
| `ComplianceValidationFailed` | `compliance-service` | `ComplianceSubmission` | Pre-payroll validation run — one or more violations found. |
| `ComplianceReportGenerated` | `compliance-service` | `ComplianceSubmission` | Statutory report artifact generated (FBR/EOBI/PESSI). |
| `ComplianceSubmitted` | `compliance-service` | `ComplianceSubmission` | Submission dispatched to government authority. |
| `ComplianceAcknowledged` | `compliance-service` | `ComplianceSubmission` | Government authority acknowledged receipt. |
| `ComplianceSubmissionFailed` | `compliance-service` | `ComplianceSubmission` | Submission failed at government authority. |
| `ComplianceRetryQueued` | `compliance-service` | `ComplianceSubmission` | Failed submission re-queued for retry dispatch. |
| `AnomalyDetected` | `decision-service` | `AnomalyRecord` | Anomaly detected during payroll/attendance/compliance scan. |
| `DecisionCardCreated` | `decision-service` | `DecisionCard` | Decision Card created from detected anomaly. |
| `DecisionCardAcknowledged` | `decision-service` | `DecisionCard` | Operator acknowledged the Decision Card. |
| `DecisionCardOverridden` | `decision-service` | `DecisionCard` | Operator overrode the card with supplied reason. |
| `DecisionCardDismissed` | `decision-service` | `DecisionCard` | Operator dismissed the card as not actionable. |
| `DecisionCardExpired` | `decision-service` | `DecisionCard` | Card TTL exceeded — expired without operator action. |
| `EWARequested` | `ewa-financial-service` | `EWARequest` | Earned Wage Access disbursement requested. |
| `EWAApproved` | `ewa-financial-service` | `EWARequest` | EWA request approved. |
| `EWADisbursed` | `ewa-financial-service` | `EWARequest` | EWA funds disbursed to employee. |
| `EWARejected` | `ewa-financial-service` | `EWARequest` | EWA request rejected. |
| `AdvanceRequested` | `ewa-financial-service` | `SalaryAdvance` | Salary advance requested. |
| `AdvanceApproved` | `ewa-financial-service` | `SalaryAdvance` | Salary advance approved. |
| `AdvanceDisbursed` | `ewa-financial-service` | `SalaryAdvance` | Salary advance funds disbursed. |
| `AdvanceRejected` | `ewa-financial-service` | `SalaryAdvance` | Salary advance rejected. |
| `RepaymentDeductionInjected` | `ewa-financial-service` | `RepaymentSchedule` | Advance repayment deduction injected into payroll. |
| `DisbursementBatchCreated` | `bank-service` | `DisbursementBatch` | Salary disbursement batch initiated. |
| `DisbursementSubmitted` | `bank-service` | `DisbursementBatch` | Disbursement batch submitted to bank/Raast. |
| `DisbursementConfirmed` | `bank-service` | `DisbursementBatch` | Bank confirmed all credits in the batch processed. |
| `DisbursementFailed` | `bank-service` | `DisbursementBatch` | Bank rejected or failed the disbursement batch. |
| `PaymentConfirmed` | `bank-service` | `PaymentRecord` | Individual employee payment confirmed by bank. |
| `PaymentFailed` | `bank-service` | `PaymentRecord` | Individual employee payment failed. |
| `ReconciliationCompleted` | `bank-service` | `ReconciliationReport` | Payroll-to-disbursement reconciliation completed — balanced. |
| `ReconciliationExceptionRaised` | `bank-service` | `ReconciliationReport` | Reconciliation completed with mismatches or exceptions. |
| `WhatsAppIdentityRegistered` | `whatsapp-service` | `WhatsAppIdentityMap` | Phone–employee identity mapping registered, OTP dispatched. |
| `WhatsAppIdentityVerified` | `whatsapp-service` | `WhatsAppIdentityMap` | OTP verified; identity mapping activated. |
| `WhatsAppIdentityRevoked` | `whatsapp-service` | `WhatsAppIdentityMap` | Identity mapping revoked. |
| `WhatsAppSessionStarted` | `whatsapp-service` | `WhatsAppSession` | New WhatsApp session created for an employee. |
| `WhatsAppSessionExpired` | `whatsapp-service` | `WhatsAppSession` | Session expired after inactivity timeout. |
| `WhatsAppMessageReceived` | `whatsapp-service` | `WhatsAppConversationEvent` | Inbound WhatsApp message processed and intent parsed. |
| `WhatsAppMessageSent` | `whatsapp-service` | `WhatsAppConversationEvent` | Outbound WhatsApp message dispatched to employee. |
| `WhatsAppApprovalActioned` | `whatsapp-service` | `WhatsAppConversationEvent` | HR approval actioned via WhatsApp channel. |
| `ReportGenerated` | `reporting-analytics-service` | `ReportExecution` | Analytics or operational report generated and available. |
| `AnomalySignalEmitted` | `reporting-analytics-service` | `AnalyticsProjection` | Anomaly signal emitted from analytics projections to decision-service. |

## employee-service events

### `EmployeeCreated`
- **Aggregate:** `Employee`
- **Transition:** `Employee` instantiated, typically in `Draft`.
- **Minimum payload:** `employee_id`, `employee_number`, `department_id`, `role_id`, `status`, `hire_date`.
- **Consumers:** `attendance-service`, `leave-service`, `payroll-service`, `auth-service`, `notification-service`.

### `EmployeeUpdated`
- **Aggregate:** `Employee`
- **Transition:** material non-status fields changed.
- **Minimum payload:** `employee_id`, `changed_fields`, `updated_at`.
- **Consumers:** read-model rebuilders, audit pipelines.

### `EmployeeStatusChanged`
- **Aggregate:** `Employee`
- **Transition:** one of `Draft -> Active`, `Active -> OnLeave`, `OnLeave -> Active`, `Active -> Suspended`, `Suspended -> Active`, `Active/OnLeave/Suspended -> Terminated`.
- **Minimum payload:** `employee_id`, `from_status`, `to_status`, `effective_at`.
- **Consumers:** `attendance-service`, `leave-service`, `payroll-service`, `auth-service`, `notification-service`.

### `DepartmentCreated`
- **Aggregate:** `Department`
- **Transition:** department created.
- **Minimum payload:** `department_id`, `code`, `status`.
- **Consumers:** search/read-model pipelines.

### `DepartmentUpdated`
- **Aggregate:** `Department`
- **Transition:** department metadata or status updated.
- **Minimum payload:** `department_id`, `changed_fields`, `status`, `updated_at`.
- **Consumers:** `hiring-service`, read-model pipelines.

### `RoleCreated`
- **Aggregate:** `Role`
- **Transition:** role created.
- **Minimum payload:** `role_id`, `title`, `status`.
- **Consumers:** search/read-model pipelines.

### `RoleUpdated`
- **Aggregate:** `Role`
- **Transition:** role metadata or status updated.
- **Minimum payload:** `role_id`, `changed_fields`, `status`, `updated_at`.
- **Consumers:** `hiring-service`, read-model pipelines.

### `PerformanceGoalSubmitted`
- **Aggregate:** `Goal`
- **Transition:** `Draft -> Submitted`.
- **Minimum payload:** `goal_id`, `employee_id`, `review_cycle_id`, `status`, `workflow_id`.
- **Consumers:** `workflow-service`, `notification-service`, talent analytics.

### `PerformanceGoalApproved`
- **Aggregate:** `Goal`
- **Transition:** `Submitted -> Approved`.
- **Minimum payload:** `goal_id`, `employee_id`, `approved_at`, `status`.
- **Consumers:** dashboards, compensation planning, talent analytics.

### `PerformanceFeedbackRecorded`
- **Aggregate:** `Feedback`
- **Transition:** feedback persisted.
- **Minimum payload:** `feedback_id`, `employee_id`, `provider_employee_id`, `feedback_type`, `created_at`.
- **Consumers:** dashboards, employee profile, analytics.

### `PerformanceCalibrationFinalized`
- **Aggregate:** `CalibrationSession`
- **Transition:** `Submitted -> Finalized`.
- **Minimum payload:** `calibration_id`, `review_cycle_id`, `final_rating`, `status`.
- **Consumers:** talent analytics, compensation planning, audit.

### `PerformancePipActive`
- **Aggregate:** `PipPlan`
- **Transition:** `Submitted -> Active`.
- **Minimum payload:** `pip_id`, `employee_id`, `manager_employee_id`, `status`, `started_at`.
- **Consumers:** HR operations, audit, notification pipelines.

### `PerformancePipProgressUpdated`
- **Aggregate:** `PipPlan`
- **Transition:** milestone progress mutation while `Active`.
- **Minimum payload:** `pip_id`, `employee_id`, `milestone_index`, `status`, `updated_at`.
- **Consumers:** HR operations, dashboards, audit.

### `CompensationBandCreated`
- **Aggregate:** `CompensationBand`
- **Transition:** compensation band created.
- **Minimum payload:** `compensation_band_id`, `grade_band_id`, `code`, `status`.
- **Consumers:** compensation planning, payroll context builders.

### `CompensationBandUpdated`
- **Aggregate:** `CompensationBand`
- **Transition:** compensation band metadata or status updated.
- **Minimum payload:** `compensation_band_id`, `grade_band_id`, `changed_fields`, `status`, `updated_at`.
- **Consumers:** compensation planning, payroll context builders.

### `SalaryRevisionCreated`
- **Aggregate:** `SalaryRevision`
- **Transition:** salary revision created or materially updated.
- **Minimum payload:** `salary_revision_id`, `employee_id`, `effective_from`, `base_salary`, `currency`, `status`.
- **Consumers:** `payroll-service`, analytics, audit.

### `BenefitsPlanCreated`
- **Aggregate:** `BenefitsPlan`
- **Transition:** benefits plan created.
- **Minimum payload:** `benefits_plan_id`, `code`, `plan_type`, `status`.
- **Consumers:** enrollment workflows, payroll context builders.

### `BenefitsPlanUpdated`
- **Aggregate:** `BenefitsPlan`
- **Transition:** benefits plan updated.
- **Minimum payload:** `benefits_plan_id`, `changed_fields`, `status`, `updated_at`.
- **Consumers:** enrollment workflows, payroll context builders.

### `BenefitsEnrollmentCreated`
- **Aggregate:** `BenefitsEnrollment`
- **Transition:** enrollment created or materially updated.
- **Minimum payload:** `benefits_enrollment_id`, `employee_id`, `benefits_plan_id`, `employee_contribution`, `status`, `effective_from`.
- **Consumers:** `payroll-service`, benefits analytics, audit.

### `AllowanceCreated`
- **Aggregate:** `Allowance`
- **Transition:** allowance created.
- **Minimum payload:** `allowance_id`, `employee_id`, `code`, `amount`, `status`, `effective_from`.
- **Consumers:** `payroll-service`, analytics, audit.

### `AllowanceUpdated`
- **Aggregate:** `Allowance`
- **Transition:** allowance updated.
- **Minimum payload:** `allowance_id`, `employee_id`, `code`, `amount`, `status`, `updated_at`.
- **Consumers:** `payroll-service`, analytics, audit.

## attendance-service events

### `AttendanceCaptured`
- **Aggregate:** `AttendanceRecord`
- **Transition:** record created or raw time data first persisted in `Captured`.
- **Minimum payload:** `attendance_id`, `employee_id`, `attendance_date`, `attendance_status`, `record_state`.
- **Consumers:** `notification-service`, dashboards.

### `AttendanceValidated`
- **Aggregate:** `AttendanceRecord`
- **Transition:** `Captured -> Validated`.
- **Minimum payload:** `attendance_id`, `employee_id`, `attendance_date`, `record_state`, `total_hours`.
- **Consumers:** dashboards, policy analytics.

### `AttendanceApproved`
- **Aggregate:** `AttendanceRecord`
- **Transition:** `Validated -> Approved`.
- **Minimum payload:** `attendance_id`, `employee_id`, `attendance_date`, `record_state`.
- **Consumers:** payroll summary builders.

### `AttendanceLocked`
- **Aggregate:** `AttendanceRecord`
- **Transition:** `Approved -> Locked`.
- **Minimum payload:** `attendance_id`, `employee_id`, `attendance_date`, `record_state`, `period_id`.
- **Consumers:** payroll pipelines, audit.

### `AttendancePeriodClosed`
- **Aggregate:** attendance period projection
- **Transition:** period-level closure after all records are locked.
- **Minimum payload:** `period_id`, `period_start`, `period_end`, `employee_count`, `closed_at`.
- **Consumers:** `payroll-service`.

## leave-service events

### `LeaveRequestSubmitted`
- **Aggregate:** `LeaveRequest`
- **Transition:** `Draft -> Submitted`.
- **Minimum payload:** `leave_request_id`, `employee_id`, `approver_employee_id`, `start_date`, `end_date`, `status`, `submitted_at`.
- **Consumers:** `notification-service`, leave dashboards.

### `LeaveRequestApproved`
- **Aggregate:** `LeaveRequest`
- **Transition:** `Submitted -> Approved`.
- **Minimum payload:** `leave_request_id`, `employee_id`, `approver_employee_id`, `total_days`, `leave_type`, `status`, `decision_at`.
- **Consumers:** `payroll-service`, `notification-service`, availability projections.

### `LeaveRequestRejected`
- **Aggregate:** `LeaveRequest`
- **Transition:** `Submitted -> Rejected`.
- **Minimum payload:** `leave_request_id`, `employee_id`, `approver_employee_id`, `status`, `decision_at`.
- **Consumers:** `notification-service`, dashboards.

### `LeaveRequestCancelled`
- **Aggregate:** `LeaveRequest`
- **Transition:** `Draft/Submitted/Approved -> Cancelled` subject to policy.
- **Minimum payload:** `leave_request_id`, `employee_id`, `status`, `updated_at`.
- **Consumers:** payroll adjustment pipelines, notifications.

## payroll-service events

### `PayrollDrafted`
- **Aggregate:** `PayrollRecord`
- **Transition:** payroll record created in `Draft`.
- **Minimum payload:** `payroll_record_id`, `employee_id`, `pay_period_start`, `pay_period_end`, `status`.
- **Consumers:** payroll dashboards, audit.

### `PayrollProcessed`
- **Aggregate:** `PayrollRecord`
- **Transition:** `Draft -> Processed`.
- **Minimum payload:** `payroll_record_id`, `employee_id`, `pay_period_start`, `pay_period_end`, `gross_pay`, `net_pay`, `currency`, `status`.
- **Consumers:** `notification-service`, finance integrations.

### `PayrollPaid`
- **Aggregate:** `PayrollRecord`
- **Transition:** `Processed -> Paid`.
- **Minimum payload:** `payroll_record_id`, `employee_id`, `payment_date`, `net_pay`, `currency`, `status`.
- **Consumers:** `notification-service`, audit.

### `PayrollCancelled`
- **Aggregate:** `PayrollRecord`
- **Transition:** `Draft/Processed -> Cancelled`.
- **Minimum payload:** `payroll_record_id`, `employee_id`, `pay_period_start`, `pay_period_end`, `status`, `updated_at`.
- **Consumers:** finance adjustment pipelines, audit.

## hiring-service events

### `JobPostingOpened`
- **Aggregate:** `JobPosting`
- **Transition:** `Draft/OnHold -> Open` or create directly in `Open`.
- **Minimum payload:** `job_posting_id`, `department_id`, `role_id`, `openings_count`, `status`, `posting_date`.
- **Consumers:** job-posting read models, recruitment notifications.

### `JobPostingOnHold`
- **Aggregate:** `JobPosting`
- **Transition:** `Open -> OnHold`.
- **Minimum payload:** `job_posting_id`, `department_id`, `role_id`, `status`, `updated_at`.
- **Consumers:** recruiter work queues, recruitment notifications.

### `JobPostingClosed`
- **Aggregate:** `JobPosting`
- **Transition:** `Open/OnHold -> Closed` or `Open -> Filled`.
- **Minimum payload:** `job_posting_id`, `status`, `updated_at`.
- **Consumers:** job-posting read models, analytics.

### `CandidateApplied`
- **Aggregate:** `Candidate`
- **Transition:** candidate created in `Applied`.
- **Minimum payload:** `candidate_id`, `job_posting_id`, `email`, `application_date`, `status`.
- **Consumers:** candidate pipeline projections, recruiter notifications.

### `CandidateStageChanged`
- **Aggregate:** `Candidate`
- **Transition:** any valid pipeline move among `Applied`, `Screening`, `Interviewing`, `Offered`, `Hired`, `Rejected`, `Withdrawn`.
- **Minimum payload:** `candidate_id`, `job_posting_id`, `from_status`, `to_status`, `updated_at`.
- **Consumers:** pipeline dashboards, notification routing.

### `InterviewScheduled`
- **Aggregate:** `Interview`
- **Transition:** interview created in `Scheduled`.
- **Minimum payload:** `interview_id`, `candidate_id`, `scheduled_start`, `scheduled_end`, `interviewer_employee_ids`, `status`.
- **Consumers:** `notification-service`, hiring dashboards.

### `InterviewCompleted`
- **Aggregate:** `Interview`
- **Transition:** `Scheduled -> Completed`.
- **Minimum payload:** `interview_id`, `candidate_id`, `recommendation`, `status`, `updated_at`.
- **Consumers:** hiring analytics, recruiter notifications.

### `InterviewCancelled`
- **Aggregate:** `Interview`
- **Transition:** `Scheduled -> Cancelled`.
- **Minimum payload:** `interview_id`, `candidate_id`, `status`, `updated_at`, `cancellation_reason`.
- **Consumers:** recruiter notifications, calendar reconciliations.

### `InterviewNoShow`
- **Aggregate:** `Interview`
- **Transition:** `Scheduled -> NoShow`.
- **Minimum payload:** `interview_id`, `candidate_id`, `status`, `updated_at`.
- **Consumers:** recruiter dashboards, candidate follow-up workflows.

### `InterviewCalendarSynced`
- **Aggregate:** `Interview`
- **Transition:** external Google Calendar sync succeeds.
- **Minimum payload:** `interview_id`, `candidate_id`, `provider`, `external_event_id`, `updated_at`.
- **Consumers:** notification workflows, operational telemetry.

### `CandidateImported`
- **Aggregate:** `Candidate`
- **Transition:** external-source candidate successfully created.
- **Minimum payload:** `candidate_id`, `job_posting_id`, `provider`, `source_candidate_id`, `status`.
- **Consumers:** hiring analytics, data lineage.

### `LinkedInCandidatesImported`
- **Aggregate:** import batch summary
- **Transition:** LinkedIn batch import completed.
- **Minimum payload:** `job_posting_id`, `provider`, `imported_count`, `skipped_count`, `occurred_at`.
- **Consumers:** import monitoring and reconciliation.

### `CandidateHired`
- **Aggregate:** `Candidate`
- **Transition:** `Offered -> Hired`.
- **Minimum payload:** `candidate_id`, `job_posting_id`, `department_id` (if available in projection), `role_id` (if available in projection), `occurred_at`.
- **Consumers:** `employee-service`, `notification-service`, analytics.

## auth-service events

### `UserAuthenticated`
- **Aggregate:** `Session`
- **Transition:** successful login creates or refreshes an active session.
- **Minimum payload:** `session_id`, `user_id`, `client_type`, `expires_at`.
- **Consumers:** security monitoring, audit, notification routing.

### `SessionRevoked`
- **Aggregate:** `Session`
- **Transition:** active session revoked on logout, policy action, or compromise response.
- **Minimum payload:** `session_id`, `user_id`, `revoked_at`, `reason`.
- **Consumers:** `notification-service`, security monitoring.

### `UserProvisioned`
- **Aggregate:** `UserAccount`
- **Transition:** new account created or invited.
- **Minimum payload:** `user_id`, `employee_id`, `email`, `status`, `identity_provider`.
- **Consumers:** `notification-service`, access reporting.

### `UserAccountStatusChanged`
- **Aggregate:** `UserAccount`
- **Transition:** `Invited/Active/Locked -> Active/Locked/Disabled`.
- **Minimum payload:** `user_id`, `employee_id`, `from_status`, `to_status`, `updated_at`.
- **Consumers:** `notification-service`, access-control read models, audit.

### `RoleBindingChanged`
- **Aggregate:** `RoleBinding`
- **Transition:** binding granted, revoked, or materially scope-adjusted.
- **Minimum payload:** `binding_id`, `user_id`, `role_name`, `scope_type`, `scope_id`, `state`, `updated_at`.
- **Consumers:** authorization caches, access-control read models, audit.

### `RefreshTokenRotated`
- **Aggregate:** `RefreshToken`
- **Transition:** `Active -> Rotated` with successor token issued.
- **Minimum payload:** `refresh_token_id`, `session_id`, `user_id`, `rotated_from_token_id`, `updated_at`.
- **Consumers:** security monitoring, token lineage audit.

### `AuthorizationPolicyUpdated`
- **Aggregate:** `PermissionPolicy`
- **Transition:** authorization policy, binding semantics, or effective policy version changes.
- **Minimum payload:** `policy_id`, `capability_id`, `role_name`, `effect`, `version`.
- **Consumers:** policy caches, access-control read models.

## notification-service events

### `NotificationQueued`
- **Aggregate:** `NotificationMessage`
- **Transition:** message accepted and queued.
- **Minimum payload:** `message_id`, `subject_type`, `subject_id`, `channel`, `status`, `queued_at`.
- **Consumers:** delivery dashboards.

### `NotificationSent`
- **Aggregate:** `NotificationMessage`
- **Transition:** `Queued -> Sent`.
- **Minimum payload:** `message_id`, `subject_type`, `subject_id`, `channel`, `status`, `sent_at`.
- **Consumers:** audit, engagement analytics.

### `NotificationFailed`
- **Aggregate:** `NotificationMessage`
- **Transition:** `Queued -> Failed` after provider attempt(s).
- **Minimum payload:** `message_id`, `subject_type`, `subject_id`, `channel`, `status`, `failure_reason`, `updated_at`.
- **Consumers:** support dashboards, retry workflows.

### `NotificationSuppressed`
- **Aggregate:** `NotificationMessage`
- **Transition:** `Queued -> Suppressed` due to preference, quiet-hours, or policy rules.
- **Minimum payload:** `message_id`, `subject_type`, `subject_id`, `channel`, `status`, `failure_reason`, `updated_at`.
- **Consumers:** support dashboards, preference analytics, audit.

## travel-service events

### `TravelRequestCreated`
- **Aggregate:** `TravelRequest`
- **Transition:** request created in `Draft`.
- **Minimum payload:** `travel_request_id`, `employee_id`, `manager_employee_id`, `status`, `start_date`, `end_date`.
- **Consumers:** travel operations inboxes, notifications, analytics.

### `TravelRequestSubmitted`
- **Aggregate:** `TravelRequest`
- **Transition:** `Draft -> Submitted`.
- **Minimum payload:** `travel_request_id`, `employee_id`, `manager_employee_id`, `status`, `workflow_id`.
- **Consumers:** `workflow-service`, `notification-service`, travel operations dashboards.

### `TravelRequestApproved`
- **Aggregate:** `TravelRequest`
- **Transition:** `Submitted -> Approved`.
- **Minimum payload:** `travel_request_id`, `employee_id`, `status`, `approved_at`.
- **Consumers:** travel booking tools, notification pipelines, analytics.

### `TravelRequestRejected`
- **Aggregate:** `TravelRequest`
- **Transition:** `Submitted -> Rejected`.
- **Minimum payload:** `travel_request_id`, `employee_id`, `status`, `decision_at`.
- **Consumers:** notification pipelines, audit, analytics.

### `TravelItineraryUpdated`
- **Aggregate:** `TravelRequest`
- **Transition:** itinerary or booking metadata updated while approved/booked.
- **Minimum payload:** `travel_request_id`, `employee_id`, `status`, `segment_count`.
- **Consumers:** traveler inboxes, operations dashboards, audit.

### `TravelRequestCancelled`
- **Aggregate:** `TravelRequest`
- **Transition:** active request cancelled before completion.
- **Minimum payload:** `travel_request_id`, `employee_id`, `status`, `cancelled_at`.
- **Consumers:** notification pipelines, finance reconciliation, audit.

### `TravelRequestCompleted`
- **Aggregate:** `TravelRequest`
- **Transition:** `Booked -> Completed`.
- **Minimum payload:** `travel_request_id`, `employee_id`, `status`, `completed_at`.
- **Consumers:** analytics, travel history projections, audit.

## project-service events

> **Source:** Events added from `docs/canon/workflow-catalog.md` `project_resource_allocation` workflow (OIG-12 resolution, 2026-06-06). These events were declared in workflow-catalog.md but absent from this catalog.

### `ProjectCreated`
- **Aggregate:** `Project`
- **Transition:** Project instantiated in `Draft`.
- **Minimum payload:** `project_id`, `tenant_id`, `name`, `status`, `created_at`.
- **Consumers:** `notification-service`, dashboards, search projections.

### `ProjectStatusChanged`
- **Aggregate:** `Project`
- **Transition:** any valid project lifecycle state transition (e.g., `Draft -> Active`, `Active -> OnHold`, `Active -> Completed`).
- **Minimum payload:** `project_id`, `from_status`, `to_status`, `updated_at`.
- **Consumers:** dashboards, analytics, `workflow-service`.

### `ProjectAssignmentRequested`
- **Aggregate:** `ProjectAssignment`
- **Transition:** assignment request created in `PendingApproval`.
- **Minimum payload:** `assignment_id`, `project_id`, `employee_id`, `requested_by`, `status`, `requested_at`.
- **Consumers:** `workflow-service`, `notification-service`, resource planning dashboards.

### `ProjectAssignmentAllocated`
- **Aggregate:** `ProjectAssignment`
- **Transition:** `PendingApproval -> Allocated` — assignment approved and resource allocated to project.
- **Minimum payload:** `assignment_id`, `project_id`, `employee_id`, `allocation_percentage`, `start_date`, `end_date`, `status`, `allocated_at`.
- **Consumers:** `notification-service`, resource dashboards, analytics.

### `ProjectAssignmentRejected`
- **Aggregate:** `ProjectAssignment`
- **Transition:** `PendingApproval -> Rejected`.
- **Minimum payload:** `assignment_id`, `project_id`, `employee_id`, `status`, `rejected_at`.
- **Consumers:** `notification-service`, audit, resource planning dashboards.

### `ProjectAssignmentReleased`
- **Aggregate:** `ProjectAssignment`
- **Transition:** `Allocated -> Released` — resource released from project before end date.
- **Minimum payload:** `assignment_id`, `project_id`, `employee_id`, `status`, `released_at`.
- **Consumers:** `notification-service`, resource planning dashboards, analytics.

### `ProjectAllocationUpdated`
- **Aggregate:** `ProjectAssignment`
- **Transition:** allocation percentage or date range updated on an active assignment.
- **Minimum payload:** `assignment_id`, `project_id`, `employee_id`, `allocation_percentage`, `updated_at`.
- **Consumers:** resource planning dashboards, analytics, audit.

## settings-service events

> **Source:** Events added from `docs/canon/workflow-catalog.md` `settings_administration` workflow (OIG-12 resolution, 2026-06-06). These events were declared in workflow-catalog.md but absent from this catalog.

### `AttendanceRuleConfigured`
- **Aggregate:** `AttendanceRule`
- **Transition:** attendance rule created or transitioned to `Draft`/`Active`.
- **Minimum payload:** `rule_id`, `tenant_id`, `status`, `configured_at`.
- **Consumers:** `attendance-service`, analytics, audit.

### `LeavePolicyConfigured`
- **Aggregate:** `LeavePolicy`
- **Transition:** leave policy created or transitioned to `Draft`/`Active`.
- **Minimum payload:** `policy_id`, `tenant_id`, `status`, `configured_at`.
- **Consumers:** `leave-service`, analytics, audit.

### `PayrollSettingsConfigured`
- **Aggregate:** `PayrollSettings`
- **Transition:** payroll settings created or transitioned to `Draft`/`Active`.
- **Minimum payload:** `settings_id`, `tenant_id`, `status`, `configured_at`.
- **Consumers:** `payroll-service`, analytics, audit.

### `SettingsPublished`
- **Aggregate:** `SettingsConfiguration`
- **Transition:** settings configuration published — all downstream-consuming services notified of effective config version.
- **Minimum payload:** `config_version`, `tenant_id`, `scope`, `published_at`.
- **Consumers:** `attendance-service`, `leave-service`, `payroll-service`, `notification-service`, audit.

## compliance-service events

> **Source:** G49 fix (2026-06-10). Events added to `event_contract.py` CANONICAL_EVENT_TYPES and `compliance_service.py` wired to emit them.

### `ComplianceSubmissionCreated`
- **Aggregate:** `ComplianceSubmission`
- **Transition:** Submission record created in `DRAFT` state.
- **Minimum payload:** `submission_id`, `organization_id`, `period`, `submission_type`.
- **Consumers:** `notification-service`, audit, compliance dashboard.

### `ComplianceValidationPassed`
- **Aggregate:** `ComplianceSubmission`
- **Transition:** `DRAFT → VALIDATED` — pre-payroll validation run with zero violations.
- **Minimum payload:** `submission_id`, `organization_id`, `is_valid`, `violation_count`.
- **Consumers:** `payroll-service` (unblocks finalization gate), audit.

### `ComplianceValidationFailed`
- **Aggregate:** `ComplianceSubmission`
- **Transition:** Validation run completed with one or more violations; submission remains in `DRAFT`.
- **Minimum payload:** `submission_id`, `organization_id`, `is_valid`, `violation_count`.
- **Consumers:** `notification-service`, `decision-service` (anomaly signal), audit, compliance dashboard.

### `ComplianceReportGenerated`
- **Aggregate:** `ComplianceSubmission`
- **Transition:** Statutory report artifact generated via country adapter (FBR Annexure-C, EOBI PR-01, PESSI/SESSI return).
- **Minimum payload:** `submission_id`, `organization_id`, `submission_type`, `period`.
- **Consumers:** audit, compliance dashboard.

### `ComplianceSubmitted`
- **Aggregate:** `ComplianceSubmission`
- **Transition:** `VALIDATED → SUBMITTED` — submission dispatched to government authority.
- **Minimum payload:** `submission_id`, `organization_id`, `submission_type`, `period`.
- **Consumers:** `notification-service`, audit, compliance dashboard.

### `ComplianceAcknowledged`
- **Aggregate:** `ComplianceSubmission`
- **Transition:** `SUBMITTED → ACK` — government authority acknowledged receipt.
- **Minimum payload:** `submission_id`, `organization_id`, `authority_ref`.
- **Consumers:** `notification-service`, audit, compliance dashboard.

### `ComplianceSubmissionFailed`
- **Aggregate:** `ComplianceSubmission`
- **Transition:** `SUBMITTED → FAILED` — submission rejected or errored at government authority.
- **Minimum payload:** `submission_id`, `organization_id`, `reason`, `error_type`.
- **Consumers:** `notification-service`, audit, compliance dashboard.

### `ComplianceRetryQueued`
- **Aggregate:** `ComplianceSubmission`
- **Transition:** `FAILED → RETRY` — submission re-queued for retry dispatch.
- **Minimum payload:** `submission_id`, `organization_id`.
- **Consumers:** `notification-service`, audit.

---

## decision-service events

> **Source:** G49 fix (2026-06-10). Events added to `event_contract.py` and `decision_api.py` wired to emit them. Canonical status enum defined in `docs/canon/decision-system.md` (G50 fix).

### `AnomalyDetected`
- **Aggregate:** `AnomalyRecord`
- **Transition:** Payroll Guardian or anomaly scan detects an anomaly for an employee in a period.
- **Minimum payload:** `employee_id`, `period`, `anomaly_type`, `risk_score`.
- **Consumers:** `notification-service`, audit, analytics.

### `DecisionCardCreated`
- **Aggregate:** `DecisionCard`
- **Transition:** Decision Card instantiated from a detected anomaly; initial `status: active`.
- **Minimum payload:** `card_id`, `employee_id`, `period`, `risk_level`, `domain`.
- **Consumers:** `notification-service`, manager dashboard, audit.

### `DecisionCardAcknowledged`
- **Aggregate:** `DecisionCard`
- **Transition:** Operator acknowledged the card; `status → acknowledged`.
- **Minimum payload:** `card_id`, `actor`.
- **Consumers:** audit, analytics.

### `DecisionCardOverridden`
- **Aggregate:** `DecisionCard`
- **Transition:** Operator overrode the recommendation with supplied reason; `status → overridden`.
- **Minimum payload:** `card_id`, `actor`, `reason`.
- **Consumers:** `governance-service` audit log, analytics.

### `DecisionCardDismissed`
- **Aggregate:** `DecisionCard`
- **Transition:** Operator dismissed the card as not actionable; `status → dismissed`.
- **Minimum payload:** `card_id`, `actor`, `reason`.
- **Consumers:** audit, analytics.

### `DecisionCardExpired`
- **Aggregate:** `DecisionCard`
- **Transition:** Card TTL (`expires_at`) exceeded; `status → expired`.
- **Minimum payload:** `card_id`, `reason`, `employee_id`.
- **Consumers:** audit, analytics, payroll gate release.

---

## ewa-financial-service events

> **Source:** G49 fix (2026-06-10). Events added to `event_contract.py` and `services/finance/ewa.py` wired for Advance lifecycle; EWA lifecycle events registered for future implementation.

### `EWARequested`
- **Aggregate:** `EWARequest`
- **Transition:** Earned Wage Access disbursement request submitted by employee.
- **Minimum payload:** `request_id`, `employee_id`, `amount`, `currency`.
- **Consumers:** `bank-service`, `notification-service`, audit.

### `EWAApproved`
- **Aggregate:** `EWARequest`
- **Transition:** EWA request approved by system eligibility check or manager.
- **Minimum payload:** `request_id`, `employee_id`, `approved_by`, `amount`.
- **Consumers:** `bank-service`, `notification-service`, audit.

### `EWADisbursed`
- **Aggregate:** `EWARequest`
- **Transition:** EWA funds disbursed to employee's bank account via Raast.
- **Minimum payload:** `request_id`, `employee_id`, `amount`, `disbursed_at`.
- **Consumers:** `payroll-service` (deduction tracking), `notification-service`, audit.

### `EWARejected`
- **Aggregate:** `EWARequest`
- **Transition:** EWA request rejected — eligibility rules or limit exceeded.
- **Minimum payload:** `request_id`, `employee_id`, `reason`.
- **Consumers:** `notification-service`, audit.

### `AdvanceRequested`
- **Aggregate:** `SalaryAdvance`
- **Transition:** Salary advance request created in `PendingApproval`.
- **Minimum payload:** `request_id`, `employee_id`, `amount`, `currency`.
- **Consumers:** `notification-service`, audit, financial wellness dashboard.

### `AdvanceApproved`
- **Aggregate:** `SalaryAdvance`
- **Transition:** `PendingApproval → Approved`.
- **Minimum payload:** `request_id`, `employee_id`, `approved_by`, `amount`.
- **Consumers:** `bank-service`, `notification-service`, audit.

### `AdvanceDisbursed`
- **Aggregate:** `SalaryAdvance`
- **Transition:** `Approved → Disbursed` — funds transferred to employee.
- **Minimum payload:** `request_id`, `employee_id`, `amount`, `disbursed_at`.
- **Consumers:** `payroll-service` (repayment schedule injection), `notification-service`, audit.

### `AdvanceRejected`
- **Aggregate:** `SalaryAdvance`
- **Transition:** `PendingApproval → Rejected`.
- **Minimum payload:** `request_id`, `employee_id`, `reason`.
- **Consumers:** `notification-service`, audit.

### `RepaymentDeductionInjected`
- **Aggregate:** `RepaymentSchedule`
- **Transition:** Advance repayment deduction amount injected into the current payroll run.
- **Minimum payload:** `request_id`, `employee_id`, `deduction_amount`, `period`.
- **Consumers:** `payroll-service`, audit.

---

## bank-service events

> **Source:** G49 fix (2026-06-10). Events added to `event_contract.py` and `bank_service.py` wired to emit them.

### `DisbursementBatchCreated`
- **Aggregate:** `DisbursementBatch`
- **Transition:** Disbursement batch initiated in `PENDING` state.
- **Minimum payload:** `disbursement_id`, `organization_id`, `period`, `method`, `employee_count`, `total_amount`.
- **Consumers:** audit, disbursement status dashboard.

### `DisbursementSubmitted`
- **Aggregate:** `DisbursementBatch`
- **Transition:** `PENDING → SUBMITTED` — batch file generated and submitted to bank or Raast.
- **Minimum payload:** `disbursement_id`, `organization_id`, `method`, `period`.
- **Consumers:** `notification-service`, audit, disbursement status dashboard.

### `DisbursementConfirmed`
- **Aggregate:** `DisbursementBatch`
- **Transition:** `SENT → ACCEPTED` — bank confirmed all individual credits processed.
- **Minimum payload:** `disbursement_id`, `organization_id`, `period`, `confirmed_at`.
- **Consumers:** `notification-service`, audit, disbursement status dashboard.

### `DisbursementFailed`
- **Aggregate:** `DisbursementBatch`
- **Transition:** `SUBMITTED/SENT → REJECTED` — bank rejected or errored on the batch.
- **Minimum payload:** `disbursement_id`, `organization_id`, `reason`.
- **Consumers:** `notification-service`, audit.

### `PaymentConfirmed`
- **Aggregate:** `PaymentRecord`
- **Transition:** Individual employee payment confirmed and credited.
- **Minimum payload:** `payment_id`, `disbursement_id`, `employee_id`, `paid_amount`.
- **Consumers:** `notification-service`, `ewa-financial-service`, audit.

### `PaymentFailed`
- **Aggregate:** `PaymentRecord`
- **Transition:** Individual employee payment failed.
- **Minimum payload:** `payment_id`, `disbursement_id`, `employee_id`, `reason`.
- **Consumers:** `notification-service`, audit.

### `ReconciliationCompleted`
- **Aggregate:** `ReconciliationReport`
- **Transition:** Payroll-to-disbursement reconciliation completed — all amounts balanced.
- **Minimum payload:** `reconciliation_id`, `disbursement_id`, `organization_id`, `period`, `is_balanced`.
- **Consumers:** audit, finance dashboard.

### `ReconciliationExceptionRaised`
- **Aggregate:** `ReconciliationReport`
- **Transition:** Reconciliation completed with mismatches, missing payments, or unmatched entries.
- **Minimum payload:** `reconciliation_id`, `disbursement_id`, `organization_id`, `mismatch_count`.
- **Consumers:** `notification-service`, audit, finance dashboard.

---

## whatsapp-service events

> **Source:** G49 fix (2026-06-10). Events added to `event_contract.py` and `whatsapp_service.py` wired to emit them.

### `WhatsAppIdentityRegistered`
- **Aggregate:** `WhatsAppIdentityMap`
- **Transition:** Phone–employee identity mapping created in `pending` state; OTP dispatched.
- **Minimum payload:** `employee_id`, `phone_e164`.
- **Consumers:** audit, identity dashboard.

### `WhatsAppIdentityVerified`
- **Aggregate:** `WhatsAppIdentityMap`
- **Transition:** OTP verified; mapping transitions to `active`.
- **Minimum payload:** `employee_id`, `phone_e164`.
- **Consumers:** `notification-service`, audit.

### `WhatsAppIdentityRevoked`
- **Aggregate:** `WhatsAppIdentityMap`
- **Transition:** Mapping transitions to `revoked`; phone number freed for re-registration.
- **Minimum payload:** `employee_id`, `phone_e164`.
- **Consumers:** `auth-service`, audit.

### `WhatsAppSessionStarted`
- **Aggregate:** `WhatsAppSession`
- **Transition:** New session created for a verified employee with 15-minute expiry.
- **Minimum payload:** `session_id`, `employee_id`, `role_context`.
- **Consumers:** audit, analytics.

### `WhatsAppSessionExpired`
- **Aggregate:** `WhatsAppSession`
- **Transition:** Session passed its `expires_at` without activity — expired.
- **Minimum payload:** `session_id`, `employee_id`.
- **Consumers:** audit, analytics.

### `WhatsAppMessageReceived`
- **Aggregate:** `WhatsAppConversationEvent`
- **Transition:** Inbound message processed through webhook; intent parsed and domain dispatch initiated.
- **Minimum payload:** `session_id`, `employee_id`, `intent`, `message_type`.
- **Consumers:** audit, analytics, conversation log.

### `WhatsAppMessageSent`
- **Aggregate:** `WhatsAppConversationEvent`
- **Transition:** Outbound message queued for dispatch to employee's verified phone.
- **Minimum payload:** `employee_id`, `message_type`, `phone_e164`.
- **Consumers:** audit, analytics, conversation log.

### `WhatsAppApprovalActioned`
- **Aggregate:** `WhatsAppConversationEvent`
- **Transition:** HR approval (leave, expense, etc.) actioned via WhatsApp channel.
- **Minimum payload:** `employee_id`, `approval_type`, `actioned_at`.
- **Consumers:** originating domain service, audit.

---

## reporting-analytics-service events

> **Source:** G49 fix (2026-06-10). Events added to `event_contract.py`; `reporting_analytics.py` was already wired via `emit_canonical_event`.

### `ReportGenerated`
- **Aggregate:** `ReportExecution`
- **Transition:** Analytics or operational report run completed and output is available for consumers.
- **Minimum payload:** `report_id`, `report_type`, `period`, `generated_at`.
- **Consumers:** `notification-service`, audit, reporting dashboard.

### `AnomalySignalEmitted`
- **Aggregate:** `AnalyticsProjection`
- **Transition:** Analytics engine detected a cross-domain anomaly pattern and emits a signal to decision-service.
- **Minimum payload:** `signal_id`, `anomaly_type`, `period`, `risk_score`.
- **Consumers:** `decision-service`, audit.

---

## Coverage checklist

- Every event published or subscribed to in `docs/canon/service-map.md` is defined here.
- Every state transition in `docs/canon/workflow-catalog.md` maps to at least one event in this document.
- No workflow relies on an undefined event name.
