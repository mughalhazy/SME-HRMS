# Meridian HCM — Archetype System
## Version: 2.2 | Date: 2026-03-30
## Anchored to: design-language.html · SME-HRMS-main repo (now `backend/`, restructured 2026-06-07) · seed pages p1–p13 (now `frontend/seeds/`)

> **Scope note:** This file maps the 13 Meridian HCM pages (H01–H13) to service contracts, data shapes, and layout archetypes. Its governing design authority is `design-language.html` (source of truth for layout, tokens, and components) and the seed pages (`p1-p13.html`) as layout references. The 13 H-archetypes instantiate the 5 abstract structural archetypes defined in `docs/design/design-system-anchor.md` (Command Center → H01, Data Directory → H02, Form/Config → H04, Pipeline → H13, etc.). For the abstract structural rules, see design-system-anchor.md §19.

---

## GOVERNING RULES

```
design-language.html  = source of truth for layout · tokens · components · patterns
Repo (SME-HRMS-main)  = source of truth for data shape · fields · enums · endpoints   [now backend/, restructured 2026-06-07]
Seed pages (p1–p13)   = source of truth for archetype layout · density · visual pattern  [now frontend/seeds/]
Gap register          = source of truth for what is deferred

Archetype = layout + slots
Page      = data + configuration
Surface   = density + behaviour

Navigation layer:
  H01 Dashboard → H02 List → H03 Detail → H04 Edit Form
  H02 List → H05 Create Form (new record)
  H05 Workflow Inbox → H03 Detail (view request)
  H07 Analytics ← feeds from all operational archetypes

STATUS KEY
  📋 To build
  🔧 Configured from base (copy + adjust)
  ✅ Built & sealed
```

---

## CHROME (all archetypes)

```
Sidebar:   54px icon-only (collapsed) · 216px full (expanded)
           Background: white · border-right: 1px #E4E7EC
Topbar:    52px · white · border-bottom: 1px #E4E7EC
           Contains: breadcrumb (left) · actions (right) · avatar (right)
Content:   scrollable below topbar · background: #F5F7FA
Font:      Inter (UI) · JetBrains Mono (numbers, codes, IDs)
```

---

## H01 — DASHBOARD

**Seed page:** `p1-dashboard.html`
**Layout:** Icon sidebar · topbar · scrollable canvas
**Slots:** TOPBAR · KPI_ROW · CHART_PRIMARY · CHART_SECONDARY · ACTIVITY_FEED · AI_BAR

### Pages

#### HR Manager Dashboard ✅
- **Service(s):** employee-service · leave_service · payroll_service · performance_service · attendance_service
- **Key data:** Headcount KPIs · Payroll summary · Leave calendar strip · Attrition risk AI bar · Department headcount bars · Activity feed
- **AI bar:** Teal · attrition risk score · confidence % · dismissable
- **Leads to:** H02 Employees · H02 Leave Requests · H07 Analytics

#### Employee Self-Service Dashboard ✅
- **Service(s):** leave_service · attendance_service · payroll_service · performance_service
- **Key data:** My leave balance · Next payslip · My goals · My attendance this month
- **Leads to:** H03 My Profile · H02 My Leave · H05 Raise Leave Request

#### Payroll Admin Dashboard ✅
- **Service(s):** payroll_service · employee-service
- **Key data:** Current cycle status · Batch anomalies · Headcount cost · Processing timeline
- **Leads to:** H02 Payroll Records · H07 Payroll Reports

#### Recruitment Dashboard ✅
- **Service(s):** hiring_service
- **Key data:** Open roles · Pipeline by stage · Time-to-hire · Offer accept rate
- **Leads to:** H13 Candidate Pipeline · H02 Job Postings

---

## H02 — LIST / TABLE

**Seed page:** `p2-list.html`
**Layout:** Icon sidebar · topbar with filter bar · scrollable table · pagination
**Slots:** TOPBAR · FILTER_BAR · DATA_TABLE · PAGINATION
**Density:** Single-line rows · 40px row height · sticky header

### Pages

#### Employees ✅
- **Service(s):** employee-service
- **Key columns:** Employee (name + ID + avatar) · Department · Role · Employment Type · Status · Hire Date
- **Filters:** Status · Department · Employment Type · Location
- **Leads to:** H03 Employee Profile → H04 Edit Employee

#### Departments ✅
- **Service(s):** employee-service (department controller)
- **Key columns:** Department (name + code) · Head · Status · Employee Count · Created
- **Leads to:** H03 Department Detail → H04 Edit Department

#### Roles ✅
- **Service(s):** employee-service (role controller)
- **Key columns:** Role (title + level) · Category · Status · Headcount
- **Leads to:** H03 Role Detail → H04 Edit Role

#### Job Postings ✅
- **Service(s):** hiring_service
- **Key columns:** Job Title · Department · Status · Applicants · Created · Closing Date
- **Filters:** Status · Department
- **Leads to:** H03 Job Posting Detail → H13 Candidate Pipeline

#### Leave Requests ✅
- **Service(s):** leave_service
- **Key columns:** Employee · Leave Type · From · To · Days · Status · Submitted
- **Filters:** Status · Leave Type · Department · Date range
- **Leads to:** H05 Workflow Inbox (approve) · H03 Leave Detail

#### Payroll Records ✅
- **Service(s):** payroll_service
- **Key columns:** Employee · Period · Gross · Net · Status · Processed
- **Filters:** Status · Pay Period · Department
- **Leads to:** H03 Payroll Record Detail

#### Expense Claims ✅
- **Service(s):** expense_service
- **Key columns:** Employee · Category · Amount · Submitted · Status · Reimbursed
- **Filters:** Status · Category · Date range
- **Leads to:** H05 Workflow Inbox (approve) · H03 Expense Detail

#### Travel Requests ✅
- **Service(s):** travel_service
- **Key columns:** Employee · Destination · Departure · Return · Status · Submitted
- **Filters:** Status · Date range
- **Leads to:** H05 Workflow Inbox (approve) · H03 Travel Detail

#### Attendance Records ✅
- **Service(s):** attendance_service
- **Key columns:** Employee · Date · Status · Check-in · Check-out · Source · Record State
- **Filters:** Status · Source · Date range · Department
- **Leads to:** H03 Attendance Detail (correction)

#### Performance Reviews ✅
- **Service(s):** performance_service
- **Key columns:** Employee · Review Cycle · Status · Reviewer · Due Date
- **Filters:** Status · Cycle · Department
- **Leads to:** H03 Review Detail

#### Documents ✅
- **Service(s):** employee-service (document-compliance controller)
- **Key columns:** Document Name · Employee · Type · Expiry · Status
- **Leads to:** H03 Document Detail

---

## H03 — DETAIL / PROFILE

**Seed page:** `p3-profile.html`
**Layout:** Icon sidebar · topbar with breadcrumb · tabbed content · action rail
**Slots:** TOPBAR · PROFILE_HEADER · TAB_NAV · TAB_CONTENT · ACTION_RAIL

### Pages

#### Employee Profile ✅
- **Service(s):** employee-service · compensation.model · leave_service · attendance_service · performance_service
- **Tabs:** Overview · Compensation · Documents · Leave · Performance · History
- **Key actions:** Edit · Suspend · Terminate · Transfer
- **Leads to:** H04 Edit Employee

#### Department Detail ✅
- **Service(s):** employee-service
- **Tabs:** Overview · Members · Sub-departments
- **Leads to:** H04 Edit Department

#### Role Detail ✅
- **Service(s):** employee-service
- **Tabs:** Overview · Employees in Role
- **Leads to:** H04 Edit Role

#### Job Posting Detail ✅
- **Service(s):** hiring_service
- **Tabs:** Overview · Candidates · Interview Schedule
- **Leads to:** H13 Pipeline · H04 Edit Job

#### Leave Request Detail ✅
- **Service(s):** leave_service
- **Shows:** Request details · Leave balance · AI assessment · Approval history
- **Leads to:** H05 Workflow (approve/reject)

#### Payroll Record Detail ✅
- **Service(s):** payroll_service
- **Shows:** Earnings breakdown · Deductions · Net pay · Status history

#### Expense Claim Detail ✅
- **Service(s):** expense_service
- **Shows:** Line items · Attachments · Approval history · Policy compliance AI
- **Leads to:** H05 Workflow (approve/reject)

#### Performance Review Detail ✅
- **Service(s):** performance_service
- **Tabs:** Overview · Goals · Feedback & Ratings · Calibration
- **Shows:** Goals · Ratings · 360 Feedback · Competency scores · Calibration grid

---

## H04 — CREATE / EDIT FORM

**Seed page:** `p4-form.html`
**Layout:** Icon sidebar · topbar with breadcrumb · step header · scrollable form · sticky footer
**Slots:** TOPBAR · STEP_HEADER · FORM_BODY · FORM_FOOTER
**Variants:** Simple (single section) · Stepped (multi-section with progress)

### Pages

#### Add Employee (stepped) ✅
- **Service(s):** employee-service · auth-service
- **Steps:** Personal Info → Employment → Role & Department → Compensation → Access & Roles → Review
- **Leads to:** H03 Employee Profile

#### Edit Employee ✅
- **Service(s):** employee-service
- **Variant:** Simple (section tabs)

#### Create Department ✅
- **Service(s):** employee-service

#### Create Role ✅
- **Service(s):** employee-service

#### Create Job Posting ✅
- **Service(s):** hiring_service
- **Steps:** Job Details → Requirements → Pipeline Template → Publish

#### Raise Leave Request ✅
- **Service(s):** leave_service
- **Variant:** Simple

#### Raise Expense Claim ✅
- **Service(s):** expense_service
- **Variant:** Stepped (Claim Details → Line Items → Attachments → Submit)

#### Raise Travel Request ✅
- **Service(s):** travel_service
- **Variant:** Simple

#### Salary Revision ✅
- **Service(s):** employee-service (compensation controller)
- **Variant:** Simple

---

## H05 — WORKFLOW / APPROVAL

**Seed page:** `p5-workflow.html`
**Layout:** Icon sidebar · topbar · split view (list left 340px · detail right flex)
**Slots:** TOPBAR · FILTER_TABS · APPROVAL_LIST · DETAIL_PANEL · ACTION_BAR
**Key pattern:** Action-in-place — approve/reject/delegate without leaving the page

### Pages

#### Approval Inbox ✅
- **Service(s):** workflow_service
- **List:** Pending approvals grouped by type (Leave · Expense · Travel · Hiring · Payroll)
- **Detail:** Request details · AI assessment · Policy check · Comment field · Approve / Reject / Delegate
- **Leads to:** H03 Detail (view full record)

---

## H06 — CALENDAR / TIMELINE

**Seed page:** `p6-calendar.html`
**Layout:** Icon sidebar · topbar · mini-cal sidebar (left) · main calendar grid (right)
**Slots:** TOPBAR · MINI_CAL · FILTER_STRIP · CALENDAR_GRID · EVENT_TOOLTIP
**Views:** Month · Week · Day (toggle)

### Pages

#### Leave Calendar ✅
- **Service(s):** leave_service · employee-service
- **Events:** Approved leaves · Holidays · Pending requests
- **Filter strip:** By department · By leave type · Team/individual toggle

#### Attendance Timeline ✅
- **Service(s):** attendance_service
- **Events:** Present · Absent · Late · Half Day per employee per day
- **View:** Team roster view by week

#### Shift Roster ✅
- **Service(s):** attendance_service (schedule + roster)
- **Events:** Assigned shifts · Published rosters

---

## H07 — ANALYTICS / REPORTS

**Seed page:** `p7-analytics.html`
**Layout:** Icon sidebar · topbar · tab nav · filter bar · chart grid
**Slots:** TOPBAR · REPORT_TABS · FILTER_BAR · CHART_GRID · DATA_TABLE · EXPORT_BAR
**Modes:** Explore (interactive) · Export (static snapshot · PDF · CSV)

### Pages

#### HR Analytics ✅
- **Service(s):** reporting_analytics · employee-service
- **Tabs:** Workforce (built) · Payroll (stub BG-018) · Attendance & Leave (built) · Recruiting (built) · Performance (stub BG-019) · Saved Reports (built)
- **Key charts:** Headcount SVG bar chart · Attrition inline bars · Dept breakdown table · Hiring funnel · Source effectiveness
- **Built:** 2026-03-28 · Contract sealed

#### Payroll Reports ✅
- **Service(s):** payroll_service (direct — not via reporting_analytics)
- **Tabs:** Overview · Monthly Breakdown · Department Costs · Payslips · Run History
- **Models:** PayrollRecord · PayrollBatch · PayrollCycle
- **Built:** 2026-03-28 · Contract sealed

#### Attendance Summary ✅
- **Service(s):** reporting_analytics (workforce.attendance.trend) · attendance_service (corrections)
- **Tabs:** Overview · Daily Attendance · Department Breakdown · Anomalies · Corrections
- **Aggregate dimensions:** attendance_date · department_id · metrics: record_count, present_count, late_count, absent_count, half_day_count, total_hours, attendance_rate, average_hours
- **Built:** 2026-03-28 · Contract sealed

#### Engagement Results ✅
- **Service(s):** engagement_service (direct — not via reporting_analytics)
- **Tabs:** Overview · Survey Results · Dimension Scores · Question Analysis · Responses
- **Models:** Survey (Draft/Open/Closed) · SurveyQuestion (Likert5) · SurveyResponse · AggregatedSurveyResult (participation_rate, overall_average_score, favorable_ratio, question_scores[], dimension_scores[], score_distribution{})
- **Dimensions:** D1 Wellbeing · D2 Management · D3 Learning · D4 Culture · D5 Purpose · FAVORABLE_THRESHOLD=4
  > NOTE (normalisation pass, 2026-06-08): these labels diverge from both this file's own L416 ("D1 Clarity & Direction · D2 Manager Effectiveness · D3 Wellbeing & Balance...") and the canonical `Engagement.question.dimension` enum in `hrms-api-contracts.md` L258–266 ("D1 Clarity & Direction · D2 Manager Effectiveness · D3 Wellbeing & Balance · D4 Growth & Development · D5 Recognition & Reward"). This line appears to be unreconciled placeholder text — `hrms-api-contracts.md` is the canonical source for dimension labels. Flagged per [[feedback_divergence_resolution]] (annotate, don't overwrite) — see Cross-File Finding #1 in `ops/normalisation-tracker.md`.
- **Accent colour:** violet #5B21B6
- **Built:** 2026-03-28 · Contract sealed

#### Compliance Reports ✅
- **Service(s):** employee-service (document-compliance · direct) — reporting_analytics has no compliance aggregate type (BG-020)
- **Tabs:** Overview · Documents · Expiring · Acknowledgements · Compliance Tasks
- **Models:** EmployeeDocument · PolicyAcknowledgement · ComplianceTask
- **Enums:** DOCUMENT_TYPES · DOCUMENT_STATUSES · COMPLIANCE_TASK_TYPES · COMPLIANCE_TASK_STATUSES · CONTRACT_KINDS
- **Accent colour:** amber #B45309 (compliance/risk theme)
- **Built:** 2026-03-29 · Contract sealed

---

## H08 — SEARCH / DISCOVERY

**Seed page:** `p8-search.html`
**Layout:** Icon sidebar · topbar · search bar · facet panel (left) · results list (right)
**Slots:** TOPBAR · SEARCH_BAR · FACET_PANEL · RESULT_LIST · RESULT_ACTIONS

### Pages

#### Global Search ✅
- **Service(s):** search_service
- **Searches:** Employees · Candidates · Documents
- **Entity types:** employee · candidate · document (entity type filter chips)
- **Facets:** Department · Status · Employment Type · Location · Domain · Skills
- **Result cards:** Avatar · Name · Role/Title · Department · Skills tags · Salary stub (BG-021) · Status chip · Entity type badge · Actions (View / Message / Edit)
- **Built:** 2026-03-29 · Contract sealed · BG-021 logged (salary/location/skills not in SearchDocument)

---

## H09 — INBOX / FEED

**Seed page:** `p9-inbox.html`
**Layout:** Icon sidebar · topbar · folder nav (left) · message list (centre) · detail panel (right)
**Slots:** TOPBAR · FOLDER_NAV · MESSAGE_LIST · DETAIL_PANEL

### Pages

#### Notifications Inbox ✅
- **Service(s):** notification_service
- **Folders:** All Messages · Approvals · AI Alerts · Leave · Payroll · Hiring · Performance · Starred · Sent · Archive
- **topic_codes:** leave.submission/approval/rejection/cancellation · travel.submission · attendance.capture · performance.review_submission/finalized · payroll.processed/paid · hiring.candidate_stage/interview_scheduled
- **Leads to:** H05 Workflow (from approval notifications)
- **Built:** 2026-03-29 · Contract sealed · BG-022 logged (notification_service is read-only — compose/reply chrome-only)

---

## H10 — SETTINGS / CONFIGURATION

**Seed page:** `p10-settings.html`
**Layout:** Icon sidebar · topbar · settings nav (left) · content (right) · save bar (bottom)
**Slots:** TOPBAR · SETTINGS_NAV · SETTINGS_CONTENT · SAVE_BAR

### Pages

#### Organisation Settings ✅
- **Service(s):** settings-service · employee-service
- **File:** pages/h10-org-settings.html [now `frontend/pages/h10-org-settings.html`, restructured 2026-06-07] · built 2026-03-29
- **Real sections:** Company Details (TenantConfig) · Leave Policies (LeavePolicy[]) · Payroll Config (PayrollSettings) · Roles & Permissions (Role[]) · Attendance Rules (AttendanceRule[])
- **Chrome sections:** Profile (BG-023) · Security (BG-024) · Notifications (BG-025) · Integrations (BG-026) · AI & Automation (BG-027)
- **Leave Policies:** LEAVE_POLICY_TYPES · ACCRUAL_FREQUENCIES · LEAVE_DEDUCTION_MODES · 5 mock policies
- **Payroll Config:** PAY_SCHEDULES · pay periods · currency · overtime_multiplier · leave_deduction_mode
- **Roles:** ROLE_PERMISSION_CODES · EMPLOYMENT_CATEGORIES · 8 mock roles

#### Integrations 📋
- **Service(s):** integration_service
- **Sections:** Connected apps · Webhooks · API keys

---

## H11 — BUILDER

**Seed page:** `p11-builder.html`
**Layout:** Icon sidebar · builder topbar · palette (left 240px) · canvas (flex-1) · properties (right 280px)
**Slots:** BUILDER_TOPBAR · PALETTE · CANVAS · PROPERTIES_PANEL · BUILDER_FOOTER
**Auto-save:** Every 30s · Manual publish required · Draft | Published states

### Pages

#### Workflow Builder ✅
- **Service(s):** workflow_service
- **Built:** 2026-03-29 · BG-028 (no definition CRUD) · BG-029 (no form field schema)
- **Components (real):** Approval · Condition · SLA/Escalation
- **Components (chrome):** Form Fields palette (BG-029) · Notification steps (BG-028) · AI Pre-check (BG-029)
- **Canvas sections:** s1 Leave Details (chrome) · s2 Approval Routing (real) · s3 Auto Notification (chrome) · s4 SLA & Escalation (real) · s5 AI Pre-check (chrome)
- **Actions:** Publish (chrome BG-028) · Version History (chrome BG-028) · Auto-save dot (real)

#### Survey Builder ✅
- **Service(s):** engagement_service
- **Built:** 2026-03-29 · BG-030 (only Likert5 question kind)
- **Components (real):** Likert Scale (Likert5) · Dimension Group · Target Audience
- **Components (chrome):** Short Text · Long Text · Rating Stars · Multi-choice · NPS (BG-030) · Page Break · Anonymity · Response Window
- **Canvas sections:** s0 Survey Details (real) · s1 D1 Clarity & Direction (real) · s2 D2 Manager Effectiveness (real) · s3 D3 Wellbeing & Balance (real)
- **Lifecycle actions:** Publish Survey (real → Draft→Open) · Close Survey (real → Open→Closed)

#### Report Builder ✅
- **Service(s):** reporting_analytics
- **Built:** 2026-03-30 · BG-031 (no PATCH schedule endpoint · no delivery schema)
- **Palette (real):** 8 REPORT_TYPES — Pipeline Summary · Funnel Summary · Source Effectiveness · Time to Hire · Attrition Summary · Attendance Trend · Dashboard Summary · Manager Span
- **Palette (chrome):** Visualization Config · Delivery Destination (BG-031)
- **Canvas cards:** s0 Report Identity (real) · s1 Data & Filters (real) · s2 Schedule (real, active toggle chrome BG-031) · s3 Delivery (chrome BG-031)
- **Topbar actions:** Run Report (real E04) · Export (real E05) · Save Report (real E03)

---

## H12 — SUPPORT / TICKET

**Seed page:** `p12-support.html`
**Layout:** Icon sidebar · topbar · status summary strip · ticket list · detail panel
**Slots:** TOPBAR · STATUS_STRIP · TICKET_LIST · TICKET_DETAIL · COMMENT_INPUT

### Pages

#### Helpdesk ✅
- **Built:** `pages/h12-helpdesk.html` [now `frontend/pages/h12-helpdesk.html`, restructured 2026-06-07] · 2026-03-30 · sealed 102/102
- **Service(s):** helpdesk_service
- **Layout:** Two-panel grid (340px ticket-list | 1fr ticket-detail) · stat strip · thread + rail grid inside detail
- **Ticket list:** 7 tickets · P-07 priority/status chips · SLA deadline · assignee avatar
- **Ticket detail (TKT-0148):** Description · Comment thread (td-main) · Rail: SLA tracker · Workflow Actions · Reporter · Related Tickets · Activity Log (td-rail) · Reply area (flex-shrink:0)
- **Workflow actions (real):** Approve triage (→ InProgress) · Approve resolution (→ Resolved) · Reject · Resolve (→ Closed)
- **Chrome (BG-032):** Priority select disabled · Reassign button disabled · Merge button non-functional · Forward tab non-functional — no PATCH /tickets/{id}
- **P-32 pattern:** `.support-body{display:grid;grid-template-columns:340px 1fr;min-height:0}` · `.ticket-list{flex-direction:column;overflow:hidden;min-height:0}` · `.tl-scroll{overflow-y:auto;flex:1;min-height:0}` · `.ticket-detail{overflow:hidden;min-height:0}` · `.td-body{display:grid;min-height:0}` · `.td-main/.td-rail{overflow-y:auto;min-height:0;padding-bottom:12vh}` · `.reply-area{flex-shrink:0}`
- **Leads to:** H05 Workflow (escalation)

---

## H13 — CANDIDATE PIPELINE ✅

**Seed page:** `p13-pipeline.html`
**Layout:** Icon sidebar · topbar · KPI strip · sub-toolbar with role tabs · Kanban board (column per stage) · slide-in detail panel
**Slots:** TOPBAR · KPI_STRIP · TOOLBAR · PIPELINE_BOARD · CANDIDATE_CARD · SLIDE_PANEL

### Pages

#### Candidate Pipeline ✅ `pages/h13-candidate-pipeline.html` [now `frontend/pages/h13-candidate-pipeline.html`, restructured 2026-06-07]
- **Service(s):** hiring_service
- **Built:** 2026-03-30 · Stab Pass 13 clean
- **Endpoints used:** GET /pipeline · GET /job-postings · GET /candidates/{id} · PATCH /candidates/{id} (stage advance / reject) · POST /candidates/{id}/hire · POST /interviews · GET /interviews · POST /candidates/import/linkedin · POST /candidates
- **Kanban stages (display):** Applied · Screening · Interview · Final Round (UI-only, BG-034) · Offer Sent
- **Backend stages:** Applied · Screening · Interviewing · Offered · Hired · Rejected (CANONICAL_PIPELINE_STAGES)
- **Card:** Avatar · Name · Role · AI match bar · Status chips · Source tag · Days-in-stage badge · Interviewer avatar stack · Hover actions (advance / reject)
- **Slide panel:** AI match score + signals · Application details · Interviewer feedback (stars + recommendation) · Timeline · Primary advance button + Message / Schedule / Reject
- **Stats (BG-033):** Total Candidates (computed) · Avg Time-to-Hire (mocked) · Offer Accept Rate (mocked) · Interviews This Week (mocked) · SLA at Risk (computed from days-over cards)
- **Gaps:** BG-033 (no summary endpoint), BG-034 (no FinalRound backend stage)
- **Contract:** `contracts/hrms-h13-candidate-pipeline-contract.json`
- **Leads to:** H03 Candidate Detail · H04 Create Job Posting

---

## BUILD STATUS SUMMARY

```
Status   Count   Archetypes
✅ Built  45      H01 (all 4 dashboard pages · stab pass 2026-03-22 · P-32 scroll fix 2026-03-23)
                 H02 (all 11 list pages · stab pass 2026-03-22 · P-32 scroll fix 2026-03-23)
                 H03 (all 8 detail pages · stab pass 2026-03-23 · P-32 scroll fix 2026-03-23)
                 H04 (all 9 form pages · built 2026-03-23 · P-32 applied at build time)
                 H05 (1 page — Approval Inbox · built 2026-03-23 · P-32 applied at build time)
                 H06 (all 3 pages — Leave Calendar + Attendance Timeline + Shift Roster · built 2026-03-24 · P-32 applied at build time)
                 H07 (all 5 pages — HR Analytics + Payroll Reports + Attendance Summary + Engagement Results + Compliance Reports · built 2026-03-28–29 · P-32 applied at build time)
                 H08 (1 page — Global Search · built 2026-03-29 · P-32 applied at build time)
                 H09 (1 page — Notifications Inbox · built 2026-03-29 · P-32 applied at build time)
                 H10 (1 page — Organisation Settings · built 2026-03-29 · BG-023/024/025/026/027)
                 H11 (3 pages — Workflow Builder · Survey Builder · Report Builder · built 2026-03-29/30 · BG-028/029/030/031)
                 H12 (1 page — Helpdesk · built 2026-03-30 · BG-032)
                 H13 (1 page — Candidate Pipeline · built 2026-03-30 · BG-033/034)
✅ Built   48     ALL 13 ARCHETYPES COMPLETE · H01–H13 sealed
```

---

## DEPENDENCY MAP — repo-accurate service names only

```
employee-service          → H01 · H02 Employees/Depts/Roles · H03 · H04 · H07 · H08
settings-service          → H10 Settings
auth-service              → H04 Add Employee (access) · H12 (auth)
hiring_service            → H01 Recruitment · H02 Jobs · H03 Job Detail · H13 Pipeline
leave_service             → H01 · H02 Leave · H03 · H04 Raise Leave · H05 · H06 Calendar
payroll_service           → H01 · H02 Payroll · H03 · H07
performance_service       → H01 · H02 Reviews · H03 · H07
attendance_service        → H01 · H02 Attendance · H06 · H07
expense_service           → H02 Expenses · H03 · H04 · H05
travel_service            → H02 Travel · H03 · H04 · H05
helpdesk_service          → H12
engagement_service        → H07 Engagement · H11 Survey Builder
workflow_service          → H05 Inbox · H11 Workflow Builder
reporting_analytics       → H07 · H11 Report Builder
search_service            → H08
notification_service      → H09
integration_service       → H10 Integrations
```
