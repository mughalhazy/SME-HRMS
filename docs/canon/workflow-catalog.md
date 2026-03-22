# Workflow Catalog

This catalog defines deterministic HR workflows and maps each workflow to services, entities, states, and events.

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
