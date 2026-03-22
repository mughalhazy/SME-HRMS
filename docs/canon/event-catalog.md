# Event Catalog

This catalog defines the canonical domain events emitted across SME-HRMS services. Every state transition referenced in the domain model and workflow catalog maps to one or more events in this registry.

## Event conventions

- Event names use `PastTense` business language.
- Every event payload includes `event_id`, `event_name`, `occurred_at`, `producer_service`, and `trace_id` metadata.
- Business payloads include the aggregate identifier and the minimum fields required for downstream consumers.
- Events are immutable; corrections emit a new event rather than mutating a prior one.
- Events are published after a successful state transition or side effect commit.

## Registry summary

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

## Coverage checklist

- Every event published or subscribed to in `docs/canon/service-map.md` is defined here.
- Every state transition in `docs/canon/workflow-catalog.md` maps to at least one event in this document.
- No workflow relies on an undefined event name.


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
