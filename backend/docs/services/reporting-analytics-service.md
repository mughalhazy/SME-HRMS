# Reporting Analytics Service

Operational, compliance, and predictive analytics — converts HR data into decision-ready intelligence and anomaly signals.

## Scope
- Aggregates data from read models across all domain services.
- Produces four report tiers: operational, compliance, predictive, and anomaly.
- Provides historical trend data and forecasting inputs for the manager dashboard and HR admin console.
- Does NOT own source data — reads from canonical read models and event projections only.
- Feeds anomaly signals to `decision-service` for Guardian processing.

## HTTP surface (`/api/v1`)
- `GET /api/v1/analytics/reports?type=&period=&department_id=&format=` — generate or retrieve report
- `GET /api/v1/analytics/reports/{report_id}` — retrieve cached report
- `GET /api/v1/analytics/headcount?as_of=&department_id=&status=` — headcount snapshot
- `GET /api/v1/analytics/payroll-summary?period=&department_id=` — payroll cost aggregates
- `GET /api/v1/analytics/attendance-trends?period=&department_id=` — attendance patterns
- `GET /api/v1/analytics/compliance-status?period=` — compliance submission and violation summary
- `GET /api/v1/analytics/turnover?period=&department_id=` — headcount movement and attrition
- `GET /api/v1/analytics/anomalies?type=&period=&risk_level=` — anomaly signal feed
- `POST /api/v1/analytics/reports/schedule` — schedule a recurring report

## Report tiers

### Operational reports
- Headcount by department, status, employment type
- Attendance summary: present, absent, late, overtime by period
- Leave utilization by type and department
- Payroll run status and cost breakdown

### Compliance reports
- FBR Annexure-C summary
- EOBI contribution compliance
- PESSI/SESSI filing status
- Outstanding violations and remediation status

### Predictive insights
- Attrition risk by department (trend-based)
- Payroll cost forecast for next period
- Overtime escalation probability
- Leave liability projection

### Anomaly signals (feeds decision-service)
- Salary anomalies vs. role band and historical pattern
- Overtime spike detection vs. shift baseline
- Missing deduction patterns
- Ghost employee signals

## Authorization capabilities
- `CAP-RPT-001`: operational and compliance reports (Admin, PayrollAdmin, Manager scoped)
- `CAP-RPT-002`: predictive insights and anomaly feed (Admin, Manager scoped)
- `CAP-RPT-003`: report scheduling (Admin)

## Owned entities
- `ReportDefinition`
- `ReportExecution`
- `AnalyticsProjection`

## Supported workflows
- `report_generation`

## Events published
- `ReportGenerated`
- `AnomalySignalEmitted` — consumed by `decision-service`

## Events subscribed
- `PayrollProcessed` / `PayrollPaid` — refresh payroll aggregates
- `AttendancePeriodClosed` — refresh attendance trend projections
- `ComplianceSubmitted` / `ComplianceAcknowledged` / `ComplianceSubmissionFailed` — update compliance status view
- `EmployeeStatusChanged` — update headcount projections

## Read models consumed
- `payroll_summary_view`
- `attendance_dashboard_view`
- `leave_requests_view`
- `compliance_status_view`
- `employee_directory_view`
- `performance_review_view`

## Read models produced
- `analytics_dashboard_view` — aggregated KPIs for executive and HR admin surfaces

## Dependencies
- All domain services (read-model consumers only; no direct DB access to transactional stores)
- `decision-service` — anomaly signal consumer
- `audit-service` — report generation audit trail

## Sub-module: CostPlanningService

**File:** `cost_planning_service.py` (91 lines)

Budget and fiscal period cost planning with a submit/approve/reject workflow.

Responsibilities:
- `submit_plan(payload)` — create a cost plan for an owner and fiscal period
- `decide_plan(plan_id, action)` — approve or reject a submitted plan
- Emits `CostPlanningPlanSubmitted`, `CostPlanningPlanApproved`, `CostPlanningPlanRejected` events

Placement: scoped under reporting-analytics because it produces forward-looking cost projections consumed by the predictive insights tier. It is NOT a standalone service and has no separate HTTP surface — expose via `/api/v1/analytics/cost-plans` if HTTP access is required.

## Notes
- Decisions > dashboards: this service supplies the intelligence layer; the UI must surface actionable recommendations, not raw data tables.
- Predictive models are heuristic/rule-based in the initial implementation; ML-based scoring deferred to roadmap Phase 3.
