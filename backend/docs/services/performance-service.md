# Performance Service

Enterprise performance management: review cycles, OKRs/goals, 360 feedback, calibration sessions, and performance improvement plans.

## Scope
- Manages performance review cycle lifecycle from creation through close.
- Manages employee goals and OKRs with approval workflow.
- Captures continuous 360-degree feedback.
- Orchestrates calibration sessions and finalization decisions.
- Manages Performance Improvement Plans (PIP) from creation through resolution.
- Routes all approvals through centralized `workflow-service`.
- Reuses `employee-service` as read-only source for employee and manager references.

## HTTP surface (`/api/v1`)
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

## Authorization capabilities
- `CAP-PRF-001`: performance review lifecycle (Admin full; Manager for team reviews; Employee reads own)

## Owned entities
- `ReviewCycle`
- `Goal`
- `Feedback`
- `CalibrationSession`
- `PipPlan`

## Supported workflows
- `performance_management`

## Events published
- `PerformanceReviewCycleCreated` / `Opened` / `Closed`
- `PerformanceGoalCreated` / `Submitted` / `Approved` / `Rejected`
- `PerformanceFeedbackRecorded`
- `PerformanceCalibrationCreated` / `Submitted` / `Finalized` / `Rejected`
- `PerformancePipCreated` / `Submitted` / `Active` / `Rejected` / `ProgressUpdated`

## Events subscribed
- `EmployeeCreated` / `EmployeeUpdated` / `EmployeeStatusChanged`

## Read models produced
- `performance_review_view` — active cycles, goal status, PIP flags
- `employee_profile_view` — enriched with performance context

## Dependencies
- `employee-service` — employee existence, department context, reporting-line lookup
- `auth-service` — access control
- `workflow-service` — review-cycle, goal, calibration, and PIP approvals
- `audit-service` — mutation logging
- `notification-service` — manager, HR, and employee notifications
- `decision-service` — surfaces PIP creation and performance drop signals to manager dashboard
