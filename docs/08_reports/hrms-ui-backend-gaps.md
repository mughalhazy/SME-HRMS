# Meridian HCM — UI Backend Gap Register
## Version: 2.7 | Date: 2026-03-30
## Status: OPEN

---

## GAP TAXONOMY

```
Backend Gap  → missing endpoint, wrong response shape, no filter/sort/pagination
UI Gap       → presentation issue with no backend cause
Contract Gap → field exists but value/type inconsistent with what UI needs
Design Gap   → design language rule conflicts with real-world constraint
```

Rule: Log BEFORE building. Fix at source layer only. Never paper over a gap.

---

## SUMMARY

| Category     | Total | P1 | P2 | P3 | Open | Closed |
|---|---|---|---|---|---|---|
| Backend Gap  | 34    | 0  | 33 | 1  | 34   | 0      |
| UI Gap       | 2     | 0  | 2  | 0  | 1    | 1      |
| Contract Gap | 1     | 0  | 1  | 0  | 1    | 0      |
| Design Gap   | 0     | 0  | 0  | 0  | 0    | 0      |

---

## CHANGE LOG

| Date | Action | IDs | Notes |
|---|---|---|---|
| 2026-03-22 | CREATED | — | Register initialised. No pages built yet. |
| 2026-03-22 | ADDED | BG-001, BG-002, BG-003 | H01 HR Manager Dashboard — pre-build gap scan. |
| 2026-03-22 | ADDED | BG-004 | H01 Recruitment Dashboard — pre-build gap scan. |
| 2026-03-22 | ADDED | BG-005, CG-001 | H02 List pages — pre-build gap scan. |
| 2026-03-23 | ADDED | BG-006 | H03 Employee Profile — pre-build gap scan. |
| 2026-03-23 | ADDED + RESOLVED | UG-001 | H03 all pages — flex scroll container scroll failure. Fixed same session. |
| 2026-03-23 | ADDED | BG-007, BG-008 | H04 Add Employee — pre-build gap scan. |
| 2026-03-23 | UPDATED | UG-001 | Full P-32 fix applied to H01, H02, H03 all pages. Resolution notes corrected. |
| 2026-03-23 | ADDED | BG-009, BG-010, BG-011, BG-012 | H05 Approval Inbox — pre-build gap scan. |
| 2026-03-23 | BUILT | — | H05 Approval Inbox built. BG-009/010/011/012 workarounds applied in page. Contract hrms-h05-approval-inbox-contract.json sealed. |
| 2026-03-24 | ADDED | BG-013, BG-014 | H06 Leave Calendar — pre-build gap scan. |
| 2026-03-24 | ADDED | BG-015 | H06 Attendance Timeline — pre-build gap scan. |
| 2026-03-24 | ADDED | BG-016, BG-017 | H06 Shift Roster — pre-build gap scan. |
| 2026-03-28 | ADDED | BG-018, BG-019 | H07 HR Analytics — pre-build gap scan. |
| 2026-03-29 | ADDED | BG-020 | H07 Compliance Reports — pre-build gap scan. |
| 2026-03-29 | ADDED | BG-021 | H08 Global Search — pre-build gap scan. |
| 2026-03-29 | ADDED | BG-022 | H09 Notifications Inbox — pre-build gap scan. |
| 2026-03-29 | ADDED | BG-023, BG-024, BG-025, BG-026, BG-027 | H10 Organisation Settings — pre-build gap scan. |
| 2026-03-29 | ADDED | BG-028, BG-029 | H11 Workflow Builder — pre-build gap scan. |
| 2026-03-29 | ADDED | BG-030 | H11 Survey Builder — pre-build gap scan. |
| 2026-03-30 | ADDED | BG-031 | H11 Report Builder — pre-build gap scan. |
| 2026-03-30 | ADDED | BG-032 | H12 Helpdesk — pre-build gap scan. |
| 2026-03-30 | ADDED | UG-002 | H12 Helpdesk — reply-area textarea scroll broken. Open. |

---

## GAPS

### BG-001
**Title:** No dashboard aggregate summary endpoint
**Urgency:** P2
**Surface:** H01 HR Manager Dashboard · KPI_ROW · CHART_PRIMARY
**Discovered:** Service scan during H01 pre-build · 2026-03-22

**What the backend has today:**
Five separate services expose list/detail endpoints (employee-service, leave_service, payroll_service, performance_service, attendance_service). There is no single endpoint that aggregates headcount, attrition rate, payroll total, open positions, and attendance stats into a dashboard summary response.

**Current workaround:**
Mock data used for all KPI values. In a live implementation, the UI would issue multiple parallel requests across services.

**What needs to be built:**
A dedicated `GET /api/v1/dashboard/hr-summary` endpoint (or BFF layer) returning: `{ headcount, active_count, on_leave_count, attrition_rate, monthly_payroll_total, payroll_status, open_positions, avg_time_to_hire, attendance_today }`.

---

### BG-002
**Title:** No AI attrition risk scoring endpoint
**Urgency:** P3
**Surface:** H01 HR Manager Dashboard · AI_BAR
**Discovered:** Service scan during H01 pre-build · 2026-03-22

**What the backend has today:**
No AI scoring service exists in the repo. The AI bar pattern (P-12) is defined in the design system but there is no `/api/v1/ai/attrition-risk` or equivalent endpoint.

**Current workaround:**
Mock AI insight with hardcoded text and confidence score (83%). AI bar is displayed but not data-driven.

**What needs to be built:**
An AI inference endpoint returning: `{ risk_type, affected_count, department, signal_description, confidence_score, dismissed }`. Pattern P-12 rules apply: teal only, confidence visible, dismissable, never red.

---

### BG-003
**Title:** No payroll statistical anomaly detection endpoint
**Urgency:** P2
**Surface:** H01 HR Manager Dashboard · KPI_ROW (payroll KPI) · ACTION_ITEMS
**Discovered:** Service scan during H01 pre-build · 2026-03-22

**What the backend has today:**
`PayrollBatch.failures[]` tracks processing errors (bad data, system errors) but not statistical deviations. There is no endpoint that compares the current cycle gross/net to previous cycle and flags employees whose pay deviates >N% from the prior period.

**Current workaround:**
Mock anomaly flag shown in the Payroll KPI card (warning style) and action items list. Count hardcoded to 3.

**What needs to be built:**
`GET /payroll-api/anomalies?period_start=&period_end=&deviation_threshold=0.15` returning: `{ anomaly_count, records: [{ employee_id, current_pay, previous_pay, deviation_pct }] }`.

---

### BG-004
**Title:** No hiring metrics aggregate endpoint
**Urgency:** P2
**Surface:** H01 Recruitment Dashboard · KPI_ROW · CHART_PRIMARY
**Discovered:** Service scan during H01 pre-build · 2026-03-22

**What the backend has today:**
`hiring_service` exposes individual endpoints for job postings and candidates but no aggregate endpoint for dashboard metrics. Deriving time-to-hire requires fetching all CandidateStageTransition records and computing avg(Completed.changed_at − Applied.changed_at). Offer accept rate requires counting Offered→Completed vs Offered→other transitions. No aggregate or analytics endpoint exists.

**Current workaround:**
Mock KPI values. In a live implementation, the UI would perform client-side aggregation across paginated candidate and transition records.

**What needs to be built:**
`GET /api/v1/hiring/metrics?period_start=&period_end=` returning: `{ open_roles_count, total_candidates, candidates_by_stage: {Applied, Interviewing, Offered}, avg_time_to_hire_days, offer_accept_rate_pct, new_applications_this_week }`.

---

### BG-005
**Title:** No list aggregate / stats-strip endpoint for any entity
**Urgency:** P2
**Surface:** H02 All List pages · STATS_STRIP
**Discovered:** Service scan during H02 pre-build · 2026-03-22

**What the backend has today:**
All services expose paginated list endpoints (e.g. `GET /api/v1/employees`, `GET /api/v1/leave/requests`) that return records. None return aggregate counts by status (e.g. total / active / on_leave / new_this_month) or computed metrics (avg tenure, avg processing time) needed to populate the stats strip above each list.

**Current workaround:**
Mock stats strip values on all H02 pages. In a live implementation, the UI would derive counts from pagination metadata plus supplementary aggregate calls.

**What needs to be built:**
Per-entity summary endpoints, e.g. `GET /api/v1/employees/summary` → `{ total, by_status: {Active, Draft, OnLeave, Suspended, Terminated}, new_this_month, avg_tenure_years }`. Pattern repeated for leave_service, payroll_service, expense_service, attendance_service, performance_service.

---

### CG-001
**Title:** Candidate status enum mismatch between api-contracts doc and hiring_service
**Urgency:** P2
**Surface:** H01 Recruitment Dashboard · H02 Job Postings · H13 Candidate Pipeline
**Discovered:** Service scan during H02 pre-build · 2026-03-22

**What the backend has today:**
`hiring_service.CANDIDATE_STATUSES` = `Applied, Screening, Interviewing, Offered, Hired, Rejected, Withdrawn`. Interview-level NoShow is a separate `INTERVIEW_STATUSES` value.

**What hrms-api-contracts.md documents:**
`Hiring.candidate.stage` was documented as `Applied, Interviewing, Offered, Completed, NoShow` — conflating interview status with candidate status and using "Completed" instead of "Hired".

**Current workaround:**
H01 recruitment dashboard uses the incorrect enum values from the contracts doc. H02 Job Postings and H13 Pipeline will use the correct service values going forward.

**What needs to be built:**
Update `hrms-api-contracts.md` Hiring section to reflect actual service enums. H01 recruitment dashboard chip colours may need updating in a future stabilisation pass (NoShow → not a candidate stage; Completed → Hired; add Screening, Rejected, Withdrawn).

---

### BG-006
**Title:** No per-employee leave balance API endpoint
**Urgency:** P2
**Surface:** H03 Employee Profile · Overview tab (Leave Balance card) · Leave tab
**Discovered:** Service scan during H03 pre-build · 2026-03-23

**What the backend has today:**
`leave_service.py` internally tracks `LeaveBalance` objects keyed by `(employee_id, leave_type)` and exposes `_balances_for_employee(employee_id)` as a private method. However `leave_api.py` exposes no corresponding HTTP route — only `get_leave_requests`, `get_leave_request`, `post_leave_submit`, `post_leave_decision`, and `patch_leave_request` are defined. There is no `GET /api/v1/leave/employees/:employeeId/balances` or equivalent.

**Current workaround:**
Mock leave balance data on H03 Employee Profile (Overview and Leave tabs). Each leave type (Annual, Sick, Casual, Unpaid, Other) shows hardcoded used/entitlement values.

**What needs to be built:**
`GET /api/v1/leave/employees/:employeeId/balances` returning: `[{ leave_type, entitlement_days, accrued_days, carried_forward_days, reserved_days, approved_days, remaining_days }]` — one entry per `LeaveType` enum value.

---

### UG-001
**Title:** Flex scroll container fails to scroll on tall content — missing min-height:0
**Urgency:** P2
**Status:** ✅ RESOLVED 2026-03-23
**Surface:** H03 all 8 detail/profile pages — `.tab-scroll` container
**Discovered:** Post-build review — h03-role-detail and h03-job-posting-detail overview tabs reported by user as not scrolling fully · 2026-03-23

**What was happening:**
`.tab-scroll { flex:1; overflow-y:auto }` without `min-height:0` causes a flex item's implicit minimum size to equal its content height. The item refuses to shrink, so `overflow-y:auto` never activates a scrollbar. The parent `overflow:hidden` silently clips the bottom of tall content instead. Only surfaces when content height exceeds the viewport — short pages (e.g. h03-department-detail) did not trigger it.

**Root cause:**
CSS flexbox spec: `min-height` defaults to `auto` for flex items, meaning the item's minimum size equals its intrinsic content size. This prevents the flex item from shrinking below content height regardless of `flex:1` or `overflow` settings.

**Fix applied:**
Full P-32 scroll pattern applied to all 33 built pages (H01, H02, H03) on 2026-03-23:
- H03 (8 pages): `.page{flex:1;overflow-y:auto;min-height:0}` · `.prof-head{position:sticky;top:0;z-index:10}` · `.tab-scroll{display:block;padding-bottom:12vh}` — removed nested scroll chain entirely
- H01 (4 pages): `.page` padding changed to `24px 24px 12vh` + `min-height:0` added
- H02 (11 pages): `.table-wrap{min-height:0;padding-bottom:12vh}` added
Root cause 2 discovered: `html{zoom:1.1}` creates a ~10vh gap between CSS scroll end and physical viewport — `padding-bottom:12vh` compensates.
Pattern documented as **P-32** in hrms-design-register-v1.md (v1.1).
Build protocol (Step 7) updated with full per-archetype patterns.

---

### BG-007
**Title:** No HTTP endpoint to provision user accounts or assign system roles during employee onboarding
**Urgency:** P2
**Surface:** H04 Add Employee · Step 5 (Access & Roles)
**Discovered:** auth-service scan during H04 pre-build · 2026-03-23

**What the backend has today:**
`auth-service` exposes login/logout/session endpoints only. `register_user()`, `assign_role_binding()`, `revoke_role_binding()`, and `upsert_permission_policy()` exist as internal service methods but are **not exposed via any HTTP route** in `auth-service/api.py`.

**Current workaround:**
Access & Roles step is mocked — shows HCM role selector and system permission toggles but submits no real payload. Provisioning must be handled out-of-band.

**What needs to be built:**
`POST /api/v1/auth/users` — provision user account for employee: `{ employee_id, username, role, tenant_id }`.
`POST /api/v1/auth/users/:userId/role-bindings` — assign role: `{ role, department_id?, scope }`.

---

### BG-008
**Title:** Personal demographic fields absent from Employee model — onboarding form captures data with no persistence path
**Urgency:** P2
**Surface:** H04 Add Employee · Step 1 (Personal Info) · Step 2 (Employment)
**Discovered:** employee.model.ts scan during H04 pre-build · 2026-03-23

**What the backend has today:**
`CreateEmployeeInput` (employee.model.ts) has no fields for: `date_of_birth`, `nationality`, `home_address`, `personal_email` (pre-boarding), `preferred_name`, or `probation_end_date`. These are standard HR onboarding data points collected before the employee starts.

**Current workaround:**
Form captures these fields for UX completeness but they are UI-only and not included in the `POST /api/v1/employees` request body. Mock data only.

**What needs to be built:**
Extend `CreateEmployeeInput` and `Employee` model with: `date_of_birth?: string`, `nationality?: string`, `home_address?: string`, `personal_email?: string`, `preferred_name?: string`, `probation_end_date?: string`. Or create a separate `EmployeeOnboardingProfile` model linked to employee_id.

---

### BG-009
**Title:** `list_inbox` API has no subject_type or definition_code filter
**Urgency:** P2
**Surface:** H05 Approval Inbox · FILTER_TABS (Leave / Expense / Travel)
**Discovered:** workflow_api.py scan during H05 pre-build · 2026-03-23

**What the backend has today:**
`get_workflow_inbox()` accepts only a `status` query param. There is no way to filter by `subject_type` (e.g. `LeaveRequest`) or `definition_code` (e.g. `leave_request`). The full inbox is returned and all type-based filtering must be done client-side.

**Current workaround:**
Filter tabs (All / Leave / Expense / Travel) perform client-side filtering on `subject_type` after loading the full inbox response.

**What needs to be built:**
Add optional `subject_type` and `definition_code` query params to `GET /workflow/inbox` so the server can filter before returning results.

---

### BG-010
**Title:** No bulk approve endpoint — "Approve All Eligible" has no backing API
**Urgency:** P2
**Surface:** H05 Approval Inbox · TOPBAR ("Approve All Eligible" button)
**Discovered:** workflow_api.py scan during H05 pre-build · 2026-03-23

**What the backend has today:**
`approve_step()` operates on a single `workflow_id`. There is no batch endpoint that accepts multiple workflow IDs and approves all in one operation.

**Current workaround:**
"Approve All Eligible" button is mocked — shows visual affordance but issues no API call.

**What needs to be built:**
`POST /workflow/approve-batch` accepting `{ workflow_ids: [str], comment?: str, actor_id: str, actor_role?: str }` — approves all listed workflows in a single atomic call where the actor has an eligible step.

---

### BG-011
**Title:** No BFF/context endpoint — detail panel requires cross-service data fetch
**Urgency:** P2
**Surface:** H05 Approval Inbox · DETAIL_PANEL
**Discovered:** workflow_service.py + workflow_api.py scan during H05 pre-build · 2026-03-23

**What the backend has today:**
`list_inbox` returns `subject_type` and `subject_id` but NOT the source record data (e.g. leave dates, expense amounts, travel itinerary). To render the detail panel, H05 must call the originating service separately (`leave_service GET /leave/requests/{id}`, `expense_service`, `travel_service`) using `subject_id`. No aggregation layer exists.

**Current workaround:**
Detail panel uses mock data for all request-specific fields.

**What needs to be built:**
`GET /workflow/{id}/context` returning the workflow instance plus the full source record, or a BFF aggregation layer that joins `WorkflowInstance` with the originating service record by `source_service` + `subject_id`.

---

### BG-012
**Title:** `expense_claim` workflow not registered in workflow catalog
**Urgency:** P2
**Surface:** H05 Approval Inbox · expense claim approval cards
**Discovered:** workflow-catalog.md scan during H05 pre-build · 2026-03-23

**What the backend has today:**
`workflow-catalog.md` defines `leave_request`, `travel_request`, `payroll_processing`, `candidate_hiring`, `performance_management`, `employee_onboarding`, `attendance_tracking`. `expense_service` has approval states (`Submitted → Approved/Rejected`) but no corresponding `expense_claim` workflow definition is registered in the catalog or in `workflow_service`.

**Current workaround:**
Expense claim approval cards mocked in H05 using `expense_claim` as definition_code (not in catalog). Approve/Reject actions are UI-only.

**What needs to be built:**
Add `expense_claim` workflow to `workflow-catalog.md` with owning service `expense_service`, steps: [Manager Approval (PT48H), Finance Review (PT24H)]. Register definition in `workflow_service` at startup.

---

### BG-013
**Title:** `list_requests` has no date-range or department filter — calendar must over-fetch
**Urgency:** P2
**Surface:** H06 Leave Calendar · CALENDAR_GRID · FILTER_STRIP
**Discovered:** leave_service.py scan during H06 pre-build · 2026-03-24

**What the backend has today:**
`list_requests(actor_role, actor_employee_id, employee_id, approver_employee_id, status, tenant_id)` — no `start_date`, `end_date`, or `department_id` params. To render a calendar month, the UI must fetch all leave requests for the tenant and filter client-side to the visible month and selected department.

**Current workaround:**
Mock event data embedded in JS. In a live implementation, the UI would load the full leave request list and filter by `start_date ≤ month_end AND end_date ≥ month_start` client-side.

**What needs to be built:**
Add optional `start_date`, `end_date`, and `department_id` query params to `GET /api/v1/leave/requests` so the server returns only requests overlapping the date range and/or matching the department.

---

### BG-014
**Title:** No HTTP endpoint for `HolidayCalendar` — public holidays cannot be fetched by the UI
**Urgency:** P2
**Surface:** H06 Leave Calendar · CALENDAR_GRID · MINI_CAL
**Discovered:** leave_service.py + leave_api.py scan during H06 pre-build · 2026-03-24

**What the backend has today:**
`leave_service.holiday_calendars` is a `PersistentKVStore[str, HolidayCalendar]` keyed by `calendar_id`. `HolidayCalendar` has `calendar_id`, `location_code`, `tenant_id`, `holidays: dict[str, str]` (ISO-date → label). `_resolve_holiday_calendar(employee_id)` is a private method. No HTTP route is defined in `leave_api.py` to fetch holiday calendars.

**Current workaround:**
Public holiday dates hardcoded in the calendar page JS. UI cannot reflect tenant-specific or location-specific holiday calendars.

**What needs to be built:**
`GET /api/v1/leave/holiday-calendars?location_code=&year=` returning `[{ calendar_id, location_code, year, holidays: { "YYYY-MM-DD": "label" } }]`.

---

### BG-015
**Title:** No team/department attendance endpoint — timeline roster view requires N per-employee calls
**Urgency:** P2
**Surface:** H06 Attendance Timeline · ROSTER_GRID
**Discovered:** attendance_service/api.py scan during H06 pre-build · 2026-03-24

**What the backend has today:**
`get_attendance_records(employee_id, from_date, to_date)` and `get_attendance_summary(employee_id, period_start, period_end)` both require a mandatory `employee_id`. There is no endpoint that returns attendance records for all employees in a department or team for a given date range in a single call.

**Current workaround:**
Mock roster data for all employees. In a live implementation, the UI would call `get_attendance_records` once per employee in the team (N calls), then assemble the grid client-side.

**What needs to be built:**
`GET /api/v1/attendance/team?department_id=&from_date=&to_date=` returning `[{ employee_id, employee_name, records: [{ attendance_date, attendance_status, check_in_time, check_out_time }] }]` — one entry per employee with their daily records for the requested range.

---

### BG-016
**Title:** `get_roster` requires mandatory `employee_id` — no department-level roster view
**Urgency:** P2
**Surface:** H06 Shift Roster · ROSTER_GRID
**Discovered:** attendance_service/api.py scan during H06 pre-build · 2026-03-24

**What the backend has today:**
`get_roster(employee_id, from_date, to_date)` requires a mandatory `employee_id`. There is no endpoint to fetch all roster assignments for a department or schedule in a single call. Rendering the full shift roster grid requires one call per employee.

**Current workaround:**
Mock roster assignments for all employees. In live implementation, UI calls `get_roster` once per employee and assembles the grid client-side.

**What needs to be built:**
`GET /api/v1/attendance/roster?schedule_id=&department_id=&from_date=&to_date=` returning all `RosterAssignment` records matching the criteria, with shift detail joined: `[{ roster_id, employee_id, employee_name, shift_id, shift_name, shift_start, shift_end, roster_date, status }]`.

---

### BG-017
**Title:** No GET endpoints for Shift or Schedule — shift catalog and published schedules cannot be fetched
**Urgency:** P2
**Surface:** H06 Shift Roster · SIDEBAR (shift definitions) · ROSTER_GRID (shift column headers)
**Discovered:** attendance_service/api.py scan during H06 pre-build · 2026-03-24

**What the backend has today:**
`post_shift` and `post_schedule` create shifts and schedules. `post_schedule_publish` publishes a schedule. No `get_shifts`, `get_shift`, `get_schedules`, or `get_schedule` endpoints exist — the shift catalog and schedule list are write-only from an HTTP perspective.

**Current workaround:**
Shift definitions (Morning 09:00–17:00, Afternoon 14:00–22:00, Night 22:00–06:00) hardcoded in UI. Schedule status (Draft/Published) hardcoded.

**What needs to be built:**
`GET /api/v1/attendance/shifts?department_id=` returning shift catalog.
`GET /api/v1/attendance/schedules?department_id=&status=` returning schedule list with status.

---

### BG-018
**Title:** `payroll_service` not integrated into `reporting_analytics` — no payroll aggregate types
**Urgency:** P2
**Surface:** H07 HR Analytics · Payroll Reports tab
**Discovered:** reporting_analytics.py REPORT_TYPES scan during H07 pre-build · 2026-03-28

**What the backend has today:**
`reporting_analytics.REPORT_TYPES` contains 8 entries covering workforce, hiring, and org analytics. `payroll_service` is never imported or called in `reporting_analytics.py`. No `sync_payroll_service()` method exists. There are no `payroll.*` aggregate types, so `GET /api/v1/reporting/aggregates?aggregate_type=payroll.*` would return empty or 404.

**Current workaround:**
Payroll Reports tab shows a stub panel with a gap notice. Mock payroll KPI data cannot be derived from any reporting_analytics endpoint. In a live implementation, payroll reports would require a dedicated `sync_payroll_service()` integration and new aggregate types such as `payroll.summary`, `payroll.cost_by_department`.

**What needs to be built:**
Add `sync_payroll_service()` to `ReportingAnalyticsService` that pulls from `payroll_service` read models.
Register new aggregate types: `payroll.summary`, `payroll.cost_by_department`, `payroll.headcount_cost`.
Expose via existing `GET /api/v1/reporting/aggregates?aggregate_type=` endpoint.

---

### BG-019
**Title:** `performance_service` not integrated into `reporting_analytics` — no performance aggregate types
**Urgency:** P2
**Surface:** H07 HR Analytics · Performance tab
**Discovered:** reporting_analytics.py REPORT_TYPES scan during H07 pre-build · 2026-03-28

**What the backend has today:**
`reporting_analytics.REPORT_TYPES` has no `performance.*` entries. `performance_service` is never imported or referenced in `reporting_analytics.py`. No `sync_performance_service()` method exists. Performance scores, review completion rates, and goal attainment metrics cannot be aggregated via the reporting service.

**Current workaround:**
Performance tab shows a stub panel with a gap notice. In a live implementation, performance analytics would require a new sync integration and aggregate types such as `performance.review_completion`, `performance.score_distribution`, `performance.goal_attainment`.

**What needs to be built:**
Add `sync_performance_service()` to `ReportingAnalyticsService` pulling from `performance_service` read models.
Register new aggregate types: `performance.review_completion`, `performance.score_distribution`, `performance.goal_attainment_by_dept`.
Expose via existing `GET /api/v1/reporting/aggregates?aggregate_type=` endpoint.

---

### BG-020
**Title:** `reporting_analytics` has no compliance aggregate type — H07 Compliance Reports hits `employee-service` directly
**Urgency:** P2
**Surface:** H07 Compliance Reports (all tabs)
**Discovered:** reporting_analytics.py REPORT_TYPES scan during H07 Compliance Reports pre-build · 2026-03-29

**What the backend has today:**
`reporting_analytics.REPORT_TYPES` contains 8 entries covering workforce, hiring, and org analytics. There is no `compliance.*` aggregate type. `employee-service` (document-compliance.controller.ts) provides full document and task data directly via its own endpoints but does not push aggregated compliance metrics into `reporting_analytics`. Pre-aggregated compliance KPIs (documents expiring, task overdue rates by department, acknowledgement completion rates) are not available from the reporting layer.

**Current workaround:**
H07 Compliance Reports hits `employee-service` document-compliance endpoints directly (`GET /api/v1/documents`, `GET /api/v1/documents/expiring`, `GET /api/v1/compliance-tasks`). Overview KPIs are client-derived from the raw lists. This is the same direct-service pattern used by H07 Payroll Reports (BG-018) and Engagement Results (engagement_service direct).

**What needs to be built:**
Add `sync_document_compliance()` to `ReportingAnalyticsService` that aggregates from `employee-service` read models.
Register new aggregate types: `compliance.document_status_summary`, `compliance.expiry_forecast`, `compliance.task_completion_by_dept`.
Expose via `GET /api/v1/reporting/aggregates?aggregate_type=compliance.*`.

---

### BG-021
**Title:** `SearchDocument` model does not expose salary, location, or skills — H08 result cards cannot surface these fields from the search index
**Urgency:** P2
**Surface:** H08 Global Search — employee result cards
**Discovered:** search_service.py `_employee_documents()` method scan during H08 Global Search pre-build · 2026-03-29

**What the backend has today:**
`SearchDocument` for entity_type=`employee` stores metadata keys: `employee_id`, `employee_number`, `email`, `phone`, `manager_employee_id`, `manager_name`, `hire_date`, `employment_type`. There is no `salary`, `location`/`office`, or `skills` field in the search index. The `keywords` list is built from name + role + department + employee_number + email + status — skills are not indexed.

**Current workaround:**
H08 Global Search shows salary and skills as stub/placeholder values in employee result cards. Result card salary slot is populated with mock data in the UI. A real implementation would require a secondary call to `employee-service GET /api/v1/employees/:id` per result item, or enrichment at index-build time from the employee read model.

**What needs to be built:**
Extend `_employee_documents()` in `SearchIndexingService` to include `salary` (from payroll read model via compensation band) and `skills` (from employee profile) in both `keywords` (for search matching) and `metadata` (for display). Add `location` / `office` to the `employee_directory_view` source rows and map to `SearchDocument.metadata.location`.

---

### BG-022
**Title:** `notification_service` is unidirectional (system-generated only) — H09 Compose and Reply are UI chrome with no backing endpoint
**Urgency:** P2
**Surface:** H09 Notifications Inbox — Compose button · Reply textarea · Forward action
**Discovered:** notification_api.py + notification_service.py scan during H09 Notifications Inbox pre-build · 2026-03-29

**What the backend has today:**
`notification_service` is a one-way delivery pipeline: external events (LeaveRequestSubmitted, PayrollProcessed, etc.) trigger `ingest_event()` which generates `NotificationMessage` records and delivers them to recipients via InApp/Email/SMS/Push channels. There is no `POST /notifications/send`, `POST /notifications/reply`, or `POST /notifications/compose` endpoint. Employees can only receive and read notifications — they cannot send or reply through this service.

**Current workaround:**
H09 Notifications Inbox shows the Compose button and Reply textarea as chrome-only (no submission handler). The Inbox is read-only in the current implementation — mark-as-read via `POST /api/v1/notifications/inbox/:subject_id/:message_id/read` is the only write operation available.

**What needs to be built:**
A separate `messaging_service` or extension to `notification_service` with: `POST /api/v1/messages` (compose), `POST /api/v1/messages/:id/reply` (thread reply), and `GET /api/v1/messages/thread/:id`. Alternatively, scope H09 as a read-only notification feed and remove Compose/Reply from the design.

---

---

### BG-023
**Title:** No user profile / personal settings model in `settings-service` — H10 Profile section is chrome-only
**Urgency:** P2
**Surface:** H10 Organisation Settings — Profile tab (name, photo, locale preferences)
**Discovered:** settings-service settings.model.ts scan during H10 pre-build · 2026-03-29

**What the backend has today:**
`settings-service` models are tenant-level (AttendanceRule, LeavePolicy, PayrollSettings, TenantConfig). There is no per-user profile settings model. Employee contact/name data lives in `employee-service` Employee model but there is no "user preferences" entity (display name, avatar, locale, dark mode, compact density).

**Current workaround:**
H10 Profile tab is rendered as a chrome form — inputs display seed mock values but have no Save endpoint.

**What needs to be built:**
A `UserPreference` entity in `settings-service` (or `employee-service`) with: display_name, avatar_url, locale, timezone, date_format, currency_display, density_mode (compact | default), theme (light | dark | system). Endpoint: `GET/PATCH /api/v1/settings/preferences/:employee_id`.

---

### BG-024
**Title:** Security settings (2FA, SSO, session timeout, password change) not exposed through `settings-service`
**Urgency:** P2
**Surface:** H10 Organisation Settings — Security tab
**Discovered:** settings-service settings.model.ts + routes scan during H10 pre-build · 2026-03-29

**What the backend has today:**
`auth-service` handles authentication but it is a separate service with no settings-service bridge. `settings-service` has no authentication or session models. No `/api/v1/settings/security` endpoint exists.

**Current workaround:**
H10 Security tab is chrome-only — toggles and password fields render but have no submission handler.

**What needs to be built:**
Either expose auth settings via `settings-service` proxy (GET/PATCH /api/v1/settings/security/:employee_id) or provide a dedicated `auth-service` security preferences endpoint that the Settings UI can call.

---

### BG-025
**Title:** Notification preference matrix in Settings page requires cross-service call to `notification_service` — not integrated
**Urgency:** P2
**Surface:** H10 Organisation Settings — Notifications tab (delivery channels + event matrix)
**Discovered:** notification_service scan (H09 build) + H10 pre-build settings-service scan · 2026-03-29

**What the backend has today:**
`notification_service` has `GET /api/v1/notifications/preferences/:subject_id` (E03 in H09 contract) returning NotificationPreference[] with topic_code, email_enabled, sms_enabled, push_enabled, in_app_enabled. However, the seed's notification matrix maps to org-level event categories (not per-topic_code), and the Settings page would need a separate read+write flow than the Notifications Inbox.

**Current workaround:**
H10 Notifications tab renders the delivery channel toggles and event matrix as chrome — checkboxes and toggles are interactive but have no PATCH handler.

**What needs to be built:**
Wire H10 Notifications tab to `GET + PATCH /api/v1/notifications/preferences/:subject_id` from notification_service. Map notification matrix rows to the canonical topic_codes (leave.submission, payroll.processed, etc.) from api-contracts.

---

### BG-026
**Title:** `integration_service` is a webhook delivery engine only — no app connector registry for H10 Integrations section
**Urgency:** P2
**Surface:** H10 Organisation Settings — Integrations tab (Slack, Google Workspace, GitHub, Jira, Stripe, Looker, Okta, AWS IAM)
**Discovered:** integration_service.py scan during H10 pre-build · 2026-03-29

**What the backend has today:**
`integration_service` manages `WebhookEndpoint` and `WebhookDelivery` records — it is an outbound event delivery service. It has no concept of app connectors, OAuth flows, or a connector registry. There is no model for "connected app" with provider_key, status (Connected | Disconnected), config, or credentials.

**Current workaround:**
H10 Integrations tab renders the Connected Apps grid as chrome — status dots, Configure/Connect buttons are decorative. No connector state is read from backend.

**What needs to be built:**
An `IntegrationConnector` model with: connector_id, provider_key (slack | google_workspace | github | jira | stripe | okta | aws_iam), status (Connected | Pending | Disconnected | Error), config JSON, oauth_redirect_url. Endpoints: GET /api/v1/integrations/connectors, POST /api/v1/integrations/connectors/:provider_key/connect, DELETE /api/v1/integrations/connectors/:connector_id.

---

### BG-027
**Title:** No AI / automation configuration model in any service — H10 AI & Automation tab is chrome-only
**Urgency:** P2
**Surface:** H10 Organisation Settings — AI & Automation tab (feature toggles + confidence thresholds)
**Discovered:** settings-service + all service scan during H10 pre-build · 2026-03-29

**What the backend has today:**
`settings-service TenantConfig.feature_flags` is a `Record<string, boolean>` which could hypothetically store AI feature flags, but there are no defined keys and no schema. There is no model for confidence thresholds, AI feature enable/disable, or sensitivity parameters.

**Current workaround:**
H10 AI & Automation tab renders feature toggles and threshold selects as chrome. TenantConfig.feature_flags noted as the intended home for these settings once keys are defined.

**What needs to be built:**
Define canonical `feature_flag` keys in settings-service TenantConfig (e.g. `ai.attrition_risk`, `ai.payroll_anomaly`, `ai.smart_suggestions`, `ai.candidate_scoring`, `ai.approval_risk`) and add `ai_thresholds: Record<string, number>` to TenantConfig. Expose via PATCH /api/v1/settings/tenant-config.

---

### BG-028
**Title:** No workflow definition CRUD API — `workflow_service.register_definition()` is internal; Workflow Builder has no save/list/edit/delete endpoints
**Urgency:** P2
**Surface:** H11 Workflow Builder — Save · Version History · workflow switcher · all definition persistence
**Discovered:** workflow_api.py scan during H11 Workflow Builder pre-build · 2026-03-29

**What the backend has today:**
`workflow_service` has `register_definition()` (upserts a WorkflowDefinition by code) and `start_workflow()` but `workflow_api.py` exposes only runtime endpoints: `get_workflow_instance`, `get_workflow_inbox`, `post_workflow_approve`, `post_workflow_reject`, `post_workflow_delegate`, `post_workflow_escalate`. There is no `GET /api/v1/workflow-definitions`, `POST /api/v1/workflow-definitions`, `PATCH /api/v1/workflow-definitions/:code`, or `DELETE /api/v1/workflow-definitions/:code` endpoint. The builder cannot load, save, version, or list definitions via API.

**Current workaround:**
H11 Workflow Builder renders with a hard-coded "Leave Approval Flow" definition. The Publish, Version History, and workflow-switcher controls are chrome-only (no backend call).

**What needs to be built:**
Expose `register_definition()` via `POST /api/v1/workflow-definitions`. Add `GET /api/v1/workflow-definitions` (list), `GET /api/v1/workflow-definitions/:code` (get), `PATCH /api/v1/workflow-definitions/:code` (update), `DELETE /api/v1/workflow-definitions/:code` (delete) in `workflow_api.py`.

---

### BG-029
**Title:** Form field schema not modeled in `workflow_service` — visual canvas "Form Fields" section is chrome-only
**Urgency:** P2
**Surface:** H11 Workflow Builder — canvas Form section (Text Input · Date Picker · Dropdown · Checkbox · etc.)
**Discovered:** workflow_service.py model scan during H11 Workflow Builder pre-build · 2026-03-29

**What the backend has today:**
`WorkflowDefinition.steps[]` only models workflow routing steps with `type` (approval), `assignee`, `sla`, `name`, and `metadata` (sequence, parallel_group, condition_key). There is no "form schema" entity — no concept of form fields, field types, labels, validation rules, or field ordering within a step or definition.

**Current workaround:**
H11 Workflow Builder canvas shows form fields (Leave Type, Duration, Start Date, End Date, Reason) as read-only chrome representing what the leave submission form collects. These are driven by `leave_service` data shape, not `workflow_service`. The Form Fields palette components are decorative.

**What needs to be built:**
Add a `FormSchema` model to `workflow_service` (or `leave_service`) with fields[]: { field_id, type (text|date|select|checkbox|textarea|file|rating), label, required, options[], validation_rules{}, visibility_condition }. Reference `form_schema_id` in `WorkflowDefinition` or expose via `GET /api/v1/workflow-definitions/:code/form-schema`.

---

### BG-030
**Title:** `engagement_service` supports only `Likert5` question kind — other question types in Survey Builder palette are chrome-only
**Urgency:** P2
**Surface:** H11 Survey Builder — palette Question Types section (Short Text · Long Text · Rating Stars · Multi-choice · NPS)
**Discovered:** engagement_service.py model scan during H11 Survey Builder pre-build · 2026-03-29

**What the backend has today:**
`EngagementService.QUESTION_KINDS = {'Likert5'}` — only one question type is accepted. Any `kind` value other than `Likert5` raises a 422 validation error. `SurveyQuestion` has `scale_min`/`scale_max` fixed at 1–5; there is no `options[]`, `placeholder`, `validation_rules`, or `max_length` field.

**Current workaround:**
H11 Survey Builder palette shows Short Text, Long Text, Rating Stars, Multi-choice, and NPS as chrome items (opacity:.6, tooltip citing BG-030). Only the Likert Scale (Likert5) palette component is active and can be added to a dimension group.

**What needs to be built:**
Extend `QUESTION_KINDS` to include: `ShortText`, `LongText`, `RatingStar`, `MultiChoice`, `Checkbox`, `NPS`. Add `options: list[str]` and `max_length: int | None` to `SurveyQuestion`. Validate kind-specific constraints (e.g. NPS scale 0–10, MultiChoice requires `options[]`).

---

### BG-031
**Title:** `reporting_analytics` has no `PATCH /api/v1/reporting/schedules/{schedule_id}` and no delivery schema — schedule edit/toggle and delivery configuration are chrome-only
**Urgency:** P2
**Surface:** H11 Report Builder — Schedule card (active toggle, edit cadence) · Delivery card (method, recipients, subject)
**Discovered:** reporting_analytics.py model scan during H11 Report Builder pre-build · 2026-03-30

**What the backend has today:**
`create_schedule()` accepts `report_id`, `cadence`, `export_format`, `next_run_at`, and sets `active=True` at creation. There is no update or deactivate endpoint. The `delivery` field on `ReportDefinition` is an untyped `dict` — no schema, no validated keys, no documentation of expected shape.

**Current workaround:**
H11 Report Builder Schedule card shows the active toggle with a BG-031 warning note in properties. The Delivery card is rendered as a chrome-only section (opacity:.65, `chrome-tag`, title tooltip) with all inputs disabled.

**What needs to be built:**
1. Add `PATCH /api/v1/reporting/schedules/{schedule_id}` exposing `update_schedule()` — at minimum `active` toggle and `cadence` / `next_run_at` update.
2. Define a `DeliveryConfig` schema on `ReportDefinition` — fields: `method` (enum: email | webhook | sftp), `recipients: list[str]`, `subject_template: str`, `webhook_url: str`, `sftp_path: str`. Validate in `create_report_definition()`.

### BG-032
**Title:** No `PATCH /api/v1/helpdesk/tickets/{id}` — ticket fields cannot be updated in-place
**Urgency:** P2
**Surface:** H12 Helpdesk — Priority select · Reassign button · Merge button · Forward tab
**Discovered:** Service scan during H12 pre-build · 2026-03-30

**What the backend has today:**
`helpdesk_service.py` exposes `create_ticket()`, `submit_ticket()`, `add_comment()`, and `get_ticket()` but no general update endpoint. The workflow decision endpoint (`POST /tickets/{id}/decision`) handles triage/resolution approvals. There is no endpoint to change `priority`, `assignee_id`, `merge_into_id`, or `forward_to` on an existing ticket.

**Current workaround:**
H12 Helpdesk priority select is rendered disabled (`opacity:.6`, `pointer-events:none`) with a title tooltip citing BG-032. Reassign button is disabled with the same treatment. Merge and Forward actions show a tooltip citing BG-032 but are otherwise hidden/disabled.

**What needs to be built:**
Add `PATCH /api/v1/helpdesk/tickets/{ticket_id}` accepting a partial body — minimum fields: `priority` (enum), `assignee_id` (UUID | null), `merge_into_id` (UUID | null), `forward_to_service` (str | null). Route to a new `update_ticket()` method in `helpdesk_service.py`.

### BG-033
**Title:** No pipeline KPI summary endpoint — stat strip metrics cannot be derived from a single call
**Urgency:** P2
**Surface:** H13 Candidate Pipeline — stat strip (Total Candidates, Avg Time-to-Hire, Offer Accept Rate, Interviews This Week, SLA at Risk)
**Discovered:** hiring_service.py / api.py model scan during H13 pre-build · 2026-03-30

**What the backend has today:**
`GET /api/v1/hiring/candidates` returns a paginated candidate list and `GET /api/v1/hiring/pipeline` returns candidates grouped by stage, but there is no aggregation endpoint. Metrics such as avg time-to-hire (requires `application_date` → `hired_at` diff), offer accept rate (Accepted / Sent), and SLA-at-risk count (days in current stage > SLA threshold) must all be computed client-side by iterating full candidate and interview datasets.

**Current workaround:**
H13 stat strip values are mocked client-side. Total count is computed from the CANDIDATES array length. All other KPIs are static mock values.

**What needs to be built:**
Add `GET /api/v1/hiring/pipeline/summary?job_posting_id=&department_id=` returning `{ total_candidates, avg_time_to_hire_days, offer_accept_rate_pct, interviews_this_week, sla_at_risk_count }`.

### BG-034
**Title:** `CANONICAL_PIPELINE_STAGES` has no "FinalRound" — seed-page "Final Round" kanban column has no backend stage equivalent
**Urgency:** P2
**Surface:** H13 Candidate Pipeline — "Final Round" kanban column and "Advance to Final" card action
**Discovered:** hiring_service.py CANONICAL_PIPELINE_STAGES scan during H13 pre-build · 2026-03-30

**What the backend has today:**
`CANONICAL_PIPELINE_STAGES = ("Applied", "Screening", "Interview", "Offer", "Hired", "Rejected")`. All interview-stage candidates share `status=Interviewing` regardless of whether they are in an early screening interview or a final-round loop. There is no `final_round` flag on the `Candidate` model and no way to filter by sub-stage via `GET /api/v1/hiring/pipeline?pipeline_stage=FinalRound`.

**Current workaround:**
H13 "Final Round" is a UI-only column. Candidates in that column carry a local `is_final_round:true` flag in mock data and are stored with `status=Interviewing`. The "Advance to Final" card action performs a client-side column move only — no PATCH call is made.

**What needs to be built:**
Add `final_round: bool` field to the `Candidate` model and expose it via `PATCH /api/v1/hiring/candidates/{id}`. Include `final_round` as a filterable param on `GET /api/v1/hiring/pipeline`.

### UG-002
**Title:** H12 reply-area textarea does not scroll when text overflows
**Urgency:** P2
**Surface:** H12 Helpdesk — `.reply-inp` textarea under Reply to Reporter / Internal Note / Forward tabs
**Discovered:** Manual browser test during H12 post-build review · 2026-03-30

**What the UI does today:**
The `.reply-inp` textarea has `height:78px;resize:none;overflow-y:auto`. Despite `overflow-y:auto` being set explicitly, typing beyond the visible height does not produce a functional scrollbar in the browser under `html{zoom:1.1}`. Multiple CSS attempts were made (grid-template-rows, height:100%, overflow-y:auto on textarea, transition:all→specific properties) — none resolved the scroll in browser testing.

**Root cause (suspected):**
`html{zoom:1.1}` combined with `resize:none` on a fixed-height textarea causes scroll event coordinates to misalign in Chromium, rendering the scrollbar non-interactive. This is a known rendering quirk with CSS `zoom` on form elements.

**Current workaround:**
None. The textarea is functional for short replies (≤ 4 lines). Longer replies are truncated visually but the content is still submitted via POST /comments.

**What needs to be fixed:**
Investigate whether replacing `height:78px` with `min-height:78px; max-height:200px` and a JS auto-resize listener (textarea `input` event → adjust scrollHeight) resolves the scroll under zoom:1.1. Alternatively, wrap the textarea in a `div` scroll container and apply overflow to the wrapper rather than the native textarea element.

---

## GAP ENTRY FORMAT

```
### BG-001
**Title:** Short descriptive title
**Urgency:** P1 · P2 · P3
**Surface:** Which page/archetype is affected
**Discovered:** How it was found · date

**What the backend has today:**
Description of current state.

**Current workaround:**
What the UI does in the absence of this.

**What needs to be built:**
Exact endpoint or field spec needed.
```
