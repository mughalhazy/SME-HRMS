# L0 CLAUDE DESIGN BRIEF

Phase: 3.5 — L0 Frontend Authority Input Freeze
Status: FROZEN
Created: 2026-06-20
Audience: Claude Design — begin archetype work
Freeze: L0 FROZEN

---

## CLEARANCE STATEMENT

L0 is FROZEN. Claude Design is cleared to begin archetype work.

All inputs in this brief are derived from verified repository evidence. No scope has been invented. Claude Design must not add any product scope beyond what is defined in this brief and the supporting L0 documents.

**Authority pack location:** `docs/03_frontend_authority/`

---

## PART 1 — PRODUCT IDENTITY

**Product name:** Meridian HCM
**Product type:** Multi-tenant SaaS HR Management System
**Target market:** SME enterprises, Pakistan launch
**Frontend stack:** Next.js 15, React 19, TypeScript, Tailwind CSS, TanStack React Query
**Frontend location:** `backend/ui/`
**API gateway:** `http://localhost:8000` (dev)
**Frontend port:** 3000 (dev)

---

## PART 2 — WHAT MERIDIAN HCM DOES

Meridian HCM is a Human Capital Management platform. It provides:

1. **Workforce Management** (F-001): Employee records, departments, org chart, roles, onboarding
2. **Attendance Management** (F-002): Attendance records, timelines, summaries
3. **Leave Management** (F-003): Leave requests, approvals, calendar, balances
4. **Payroll Processing** (F-004): Payroll runs, payslips, disbursements
5. **Recruitment / Hiring** (F-005): Job postings, candidate pipeline, interviews
6. **Authentication & Authorization** (F-006): JWT-based, 5 roles, RBAC
7. **Workflow Engine** (F-007): Approval workflows, automation rules
8. **Audit Logging** (F-008): Immutable audit trail of all mutations
9. **Notification System** (F-009): In-app notifications with folder organization
10. **Settings & HR Policy** (F-010): Organisation settings, leave policies, payroll config
11. **Pakistan Statutory Compliance** (F-011): FBR, EOBI, PESSI compliance reports
12. **Reporting & Analytics** (F-012): HR analytics, payroll reports, custom report builder
13. **Automation Engine** (F-013): Automation rules, workflow definitions
14. **Decision Intelligence** (F-014): AI-generated decision cards for HR operations
15. **EWA (Earned Wage Access)** (F-015): Employee salary advance requests
16. **Banking/Disbursement** (F-016): Payroll disbursement via Raast

---

## PART 3 — THE 5 USER ROLES

| Role | Description | Dashboard | Scope |
|------|-------------|-----------|-------|
| Admin | Full system access, tenant administrator | HR Manager Dashboard (global) | Global |
| PayrollAdmin | Payroll + compliance specialist | Payroll Admin Dashboard | Global (payroll/compliance) |
| Manager | Team/department lead | HR Manager Dashboard (dept-scoped) | Department |
| Recruiter | Hiring specialist | Recruitment Dashboard | Global (hiring only) |
| Employee | Self-service only | Employee Self-Service Dashboard | Own records |

---

## PART 4 — THE ARCHETYPE SYSTEM

Meridian HCM uses a defined set of 13 archetypes (H01–H13). Every screen maps to exactly one archetype. Wireframes exist at `frontend/pages/`. Authority (not wireframe) takes precedence where they conflict.

| Archetype | Purpose | Example Screens |
|-----------|---------|-----------------|
| H01 | Role-adaptive dashboard with widget grid | All 4 dashboard variants |
| H02 | List/table with filters, search, pagination, export | Employee list, Leave requests, Payroll records |
| H03 | Detail/profile with tabs and content sections | Employee profile, Job posting detail, Payroll record detail |
| H04 | Create/edit form (single or multi-step) | Add Employee (6-step), Create Job Posting (4-step), Raise Leave |
| H05 | Workflow approval split-view | Approval Inbox (340px list + flex detail) |
| H06 | Calendar/timeline visualization | Leave Calendar, Attendance Timeline |
| H07 | Analytics/reports with charts and filters | HR Analytics, Payroll Reports, Compliance Reports |
| H08 | Search with query input and results | Global Search |
| H09 | Inbox/feed with folder navigation | Notifications Inbox |
| H10 | Settings panel with section navigation | Organisation Settings |
| H11 | Visual builder/canvas | Workflow Builder, Report Builder |
| H12 | Support ticket interface (ADD-ON) | Helpdesk |
| H13 | Kanban pipeline board with slide-over detail | Candidate Pipeline |

---

## PART 5 — SCREENS TO DESIGN (PHASE 4 CORE)

Design the 36 core screens. Reference L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md §2 for the full list. Key screens:

### Dashboards (H01) — 4 variants at `/dashboard`

| Variant | Role | Key Widgets |
|---------|------|-------------|
| HR Manager Dashboard | Admin, Manager | Employee KPIs, Attendance Rate, Pending Approvals, Pending Leave, Headcount Trend, Recent Employees |
| Payroll Admin Dashboard | PayrollAdmin | Payroll Status, Total Cost, Compliance Deadlines, Cost Trend, Decision Cards (payroll) |
| Recruitment Dashboard | Recruiter | Open Positions, Applicants, Interviews This Week, Pipeline Funnel, Active Postings |
| Employee Self-Service | Employee | Leave Balance, Attendance This Month, Latest Payslip, Notifications, Mini Leave Calendar |

### High-Priority Core Screens

**Employee Management:**
- `/employees` (H02) — List with search, filters (status, dept, role), export
- `/employees/[id]` (H03) — 6-tab profile: Overview / Compensation / Documents / Leave / Performance / History
- `/employees/new` (H04) — 6-step form: Personal Info → Employment → Role & Dept → Compensation → Access & Roles → Review
- `/employees/[id]/edit` (H04) — Edit form (Admin: all fields; Manager: limited fields)

**Leave:**
- `/leave/new` (H04) — Raise leave request with calendar date picker, leave type, reason
- `/leave/calendar` (H06) — Monthly team leave calendar, employee filter
- `/leave/requests` (H02) — Manager/Admin list with Approve/Reject actions
- `/approvals` (H05) — Split-view approval inbox (340px list + flex detail)

**Payroll:**
- `/payroll` (H02) — Payroll records list with Run Payroll CTA (PA/Admin)
- `/payroll/[id]` (H03) — Payroll detail with disbursement trigger
- `/payroll/run` (H04) — Payroll run form: period selection → validate → confirm

**Hiring:**
- `/candidates-pipeline` (H13) — Kanban board: Applied / Screening / Interview / Final Round / Offer Sent
- `/candidates-pipeline/[id]` — Candidate slide-over with profile, interviews, stage actions
- `/job-postings/new` (H04) — 4-step: Job Details → Requirements → Pipeline Template → Publish

**Analytics:**
- `/reporting` (H07) — HR Analytics tabs: HR Analytics / Payroll Reports / Attendance Summary / Compliance Reports
- `/compliance` (H07) — Compliance reports with non-standard API envelope

**Operations:**
- `/automations` (H11) — Automation rules list + create
- `/builders/workflow` (H11) — Visual workflow designer
- `/decisions` — Decision cards with severity indicators (critical / notify / passive)
- `/audit` (H02) — Immutable audit log with expand-row detail

---

## PART 6 — KEY DESIGN CONSTRAINTS SUMMARY

Full constraints are in `L0_DESIGN_CONSTRAINTS_FOR_CLAUDE_DESIGN.md`. Key points:

### Chrome (Fixed — Do Not Change)

| Element | Value |
|---------|-------|
| Sidebar collapsed | 54px |
| Sidebar expanded | 216px |
| Topbar height | 52px |
| Content background | #F5F7FA |
| Primary font | Inter |
| Monospace font | JetBrains Mono |

### API Envelope — CRITICAL

- 21 services: `{status, data, meta, error}` — standard pagination via `meta`
- 4 services: `{status, data, service}` — NO `meta` — compliance, decisions, banking, whatsapp
- Compliance screen and Decisions screen must explicitly handle missing `meta`

### State Requirements — ALL Screens

Every screen and widget must have: Loading (skeleton) | Empty (with CTA) | Error (with retry) | Data (rendered)

### Settings Volatility

Settings-service is in-memory. Settings reset on service restart. Do not design a persistent local cache UX for settings. Always show fresh-fetched data.

### Decision Cards

Decision Cards are in-memory (not persisted). The decisions screen must have a clear empty state for when no cards are active (common after service restart).

---

## PART 7 — WORKFLOW UX PATTERNS

### Approval Inbox (H05)

The `/approvals` screen is a split-view:
- Left panel: 340px fixed — list of pending approval cards, sorted newest first
- Right panel: flex — detail view for selected card (leave detail, EWA detail, etc.)
- Actions: Approve (inline confirm), Reject (reason required), no Delegate in Phase 4

### Candidate Pipeline (H13)

- Kanban columns: Applied | Screening | Interview | Final Round | Offer Sent
- "Final Round" is a UI-only column — maps to backend `Interviewing`; drag into Final Round does not call API
- Drag from Final Round → Offer Sent triggers `PATCH {stage: "Offered"}`
- Each card: candidate name, posting title, days in stage, primary action button
- Clicking a card opens a slide-over (H03 pattern) with full candidate detail

### Multi-Step Forms (H04)

- Step progress indicator required
- Cannot advance without completing required fields
- Back navigation does not lose data
- Final submit navigates to created resource detail screen

---

## PART 8 — NAVIGATION MODEL

### Sidebar by Role (Summary)

**Admin:** All 9 sections (A through I + Notifications)
**PayrollAdmin:** Dashboard | Leave | Payroll | Compliance + Decisions | Notifications
**Manager:** Dashboard | People & Org (no Roles) | Attendance + Leave | Payroll | Hiring | Approvals | Reporting + Decisions | Notifications
**Recruiter:** Dashboard | Hiring (Hiring, Job Postings, Pipeline) | Notifications
**Employee:** Dashboard | Attendance | Leave | Payslip link | Notifications

### Topbar (All Roles — Identical)

Logo → Search → Notifications bell → Approvals badge (Admin/Manager) → User avatar/role chip → User menu

---

## PART 9 — DATA AND ENTITY REFERENCES

### Status Badge Colors (Semantic — Required)

| Entity | Status | Badge Style |
|--------|--------|------------|
| Employee | `active` | Green |
| Employee | `draft` | Grey |
| Employee | `on_leave` | Blue |
| Employee | `suspended` | Orange |
| Employee | `terminated` | Red |
| Leave | `pending` | Yellow |
| Leave | `approved` | Green |
| Leave | `rejected` | Red |
| Leave | `cancelled` | Grey |
| Payroll | `draft` | Grey |
| Payroll | `processing` | Blue + spinner |
| Payroll | `completed` | Green |
| Payroll | `pending_disbursement` | Yellow |
| Payroll | `disbursed` | Green |
| Payroll | `failed` | Red |
| Job Posting | `Draft` | Grey |
| Job Posting | `Open` | Green |
| Job Posting | `Closed` | Red |
| Job Posting | `Filled` | Blue |
| Decision Card | `critical` | Red (mandatory action) |
| Decision Card | `notify` | Yellow (visible non-blocking) |
| Decision Card | `passive` | Grey (logged only) |

### Employee Profile Tabs (H03-01)

Tab order: Overview | Compensation | Documents | Leave | Performance (ADD-ON) | History

- Performance tab: renders with "ADD-ON not enabled" notice if F-017 is not active
- History tab: immutable audit trail — read-only; no edit/delete

### Settings Sections (H10-01)

Backend-persistent: Company Details | Leave Policies | Payroll Config | Roles & Permissions | Attendance Rules
Chrome-only (no backend persistence): Profile | Security | Notifications | Integrations | AI & Automation

---

## PART 10 — WIREFRAME REFERENCES

Source wireframes exist at `frontend/pages/`. Filenames follow the archetype naming convention:

| Wireframe | Screen |
|-----------|--------|
| `h01-hr-manager-dashboard.html` | HR Manager Dashboard |
| `h01-employee-self-service.html` | Employee Self-Service Dashboard |
| `h01-payroll-admin-dashboard.html` | Payroll Admin Dashboard |
| `h01-recruitment-dashboard.html` | Recruitment Dashboard |
| `h02-employees.html` | Employees List |
| `h02-departments.html` | Departments List |
| `h02-roles.html` | Roles List |
| `h02-job-postings.html` | Job Postings List |
| `h02-leave-requests.html` | Leave Requests List |
| `h02-payroll-records.html` | Payroll Records List |
| `h02-attendance-records.html` | Attendance Records List |
| `h03-employee-profile.html` | Employee Profile |
| `h03-department-detail.html` | Department Detail |
| `h03-role-detail.html` | Role Detail |
| `h03-job-posting-detail.html` | Job Posting Detail |
| `h03-leave-request-detail.html` | Leave Request Detail |
| `h03-payroll-record-detail.html` | Payroll Record Detail |
| `h04-add-employee.html` | Add Employee Form |
| `h04-edit-employee.html` | Edit Employee Form |
| `h04-create-department.html` | Create Department Form |
| `h04-create-role.html` | Create Role Form |
| `h04-create-job-posting.html` | Create Job Posting Form |
| `h04-raise-leave-request.html` | Raise Leave Request Form |
| `h04-salary-revision.html` | Salary Revision Form |
| `h05-approval-inbox.html` | Approval Inbox |
| `h06-leave-calendar.html` | Leave Calendar |
| `h06-attendance-timeline.html` | Attendance Timeline |
| `h07-hr-analytics.html` | HR Analytics |
| `h07-payroll-reports.html` | Payroll Reports |
| `h07-attendance-summary.html` | Attendance Summary |
| `h07-compliance-reports.html` | Compliance Reports |
| `h08-global-search.html` | Global Search |
| `h09-notifications-inbox.html` | Notifications Inbox |
| `h10-org-settings.html` | Organisation Settings |
| `h11-workflow-builder.html` | Workflow Builder |
| `h11-report-builder.html` | Report Builder |
| `h13-candidate-pipeline.html` | Candidate Pipeline |

**Authority note:** Where a wireframe conflicts with FRONTEND_SCREEN_CATALOG.md or this brief, the authority document takes precedence.

---

## PART 11 — SUCCESS CRITERIA FOR ARCHETYPE WORK

Claude Design's archetype work is successful if:

1. Every screen maps to exactly one archetype from H01–H13
2. Chrome dimensions match fixed values exactly (54px/216px sidebar, 52px topbar)
3. Role-based nav items match the exact sidebar compositions in §8
4. All 4 UI states (Loading, Empty, Error, Data) are present for every screen
5. Non-standard envelope services (compliance, decisions) have no pagination controls
6. Action buttons are absent (not disabled) for roles without the required capability
7. No screen has been designed for an OUT-OF-SCOPE or PLANNED feature
8. The Approval Inbox is a split-view with 340px left panel
9. The Candidate Pipeline is a Kanban with the defined 5 active columns
10. Multi-step forms have progress indicators and cannot advance without required fields

---

## PART 12 — DOCUMENT CROSS-REFERENCES

| Need | Document |
|------|---------|
| Full route list (55 routes) | `L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md` §1 |
| Full screen list (49 screens) | `L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md` §2 |
| Dashboard widget specifications | `FRONTEND_DASHBOARD_CATALOG.md` |
| Per-role experience and journey | `FRONTEND_ROLE_EXPERIENCE_MATRIX.md` |
| Permission rendering rules | `FRONTEND_PERMISSION_MATRIX.md` |
| Workflow step-by-step traces | `FRONTEND_WORKFLOW_TO_SCREEN_MAP.md` |
| API endpoint → screen mapping | `FRONTEND_API_DEPENDENCY_MAP.md` |
| Navigation sidebar details | `FRONTEND_NAVIGATION_MODEL.md` |
| All design constraints | `L0_DESIGN_CONSTRAINTS_FOR_CLAUDE_DESIGN.md` |
| Route × screen × workflow matrix | `L0_ROUTE_SCREEN_WORKFLOW_MATRIX.md` |
| Blocked/excluded items | `L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md` §10 |
