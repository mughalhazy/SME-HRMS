# L0 DESIGN CONSTRAINTS FOR CLAUDE DESIGN

Phase: 3.5 — L0 Frontend Authority Input Freeze
Status: FROZEN
Created: 2026-06-20
Audience: Claude Design — archetype work
Freeze: L0 FROZEN

---

## PURPOSE

This document defines the hard constraints that Claude Design MUST obey when producing UI/UX archetype work. All constraints are derived from Phase 3 authority documents. No constraint here was invented in Phase 3.5.

**Priority rule:** If any design decision conflicts with this document, this document wins.

---

## CONSTRAINT CLASS 1 — SCOPE (WHAT CANNOT BE INVENTED)

### 1.1 Routes — DO NOT INVENT

Claude Design may only reference routes from L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md §1. The approved Phase 4 core route list is fixed at 45 routes (3 auth + 42 feature routes). The 10 ADD-ON routes are defined but MUST NOT be implemented in core Phase 4 work.

**Specifically prohibited:**
- Do not add routes not in the approved list
- Do not add screens for PLANNED or OUT-OF-SCOPE features
- Do not add a document management screen (no backend exists)
- Do not add a shift/roster screen (no backend exists)
- Do not add travel request screens (F-023 is PLANNED only)
- Do not add project management screens (F-024 is PLANNED only)
- Do not add a standalone WhatsApp messaging screen
- Do not add a standalone banking management screen

### 1.2 Screens — DO NOT INVENT

Claude Design may only design the 36 core screens listed in L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md §2. The 8 ADD-ON screens and 5 out-of-scope screens must not be designed in Phase 4 core work.

### 1.3 Roles — DO NOT INVENT

Exactly 5 roles: Admin, PayrollAdmin, Manager, Recruiter, Employee. Do not design UI for any role not in this list. Do not design a "SuperAdmin" or "Finance" role. Do not create a 6th dashboard variant.

### 1.4 APIs — DO NOT INVENT

Do not reference API endpoints not listed in L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md §7 or FRONTEND_API_DEPENDENCY_MAP.md. If a design requires data that has no confirmed API endpoint, flag it as a gap — do not assume an endpoint exists.

### 1.5 Workflows — DO NOT INVENT

Only 6 core workflows exist for Phase 4: WF-001 to WF-004, WF-007, WF-008. Do not add workflow steps not in FRONTEND_WORKFLOW_TO_SCREEN_MAP.md.

---

## CONSTRAINT CLASS 2 — CHROME AND LAYOUT (MUST MATCH ARCHETYPE SYSTEM)

### 2.1 Fixed Chrome Dimensions

| Element | Value | Source |
|---------|-------|--------|
| Sidebar collapsed | 54px | archetype-system-v1.md |
| Sidebar expanded | 216px | archetype-system-v1.md |
| Topbar height | 52px | archetype-system-v1.md |
| Content background | `#F5F7FA` | archetype-system-v1.md |
| Primary font | Inter | archetype-system-v1.md |
| Monospace font | JetBrains Mono (numbers, IDs) | archetype-system-v1.md |

These values are FIXED. Do not alter chrome dimensions in archetype work.

### 2.2 Topbar (All Roles — Consistent)

The topbar is identical across all roles:
- Product logo / tenant name (left-aligned) → `/dashboard`
- Global search trigger (center or right) → `/search` or inline modal
- Notifications bell with unread count badge → `/notifications`
- Approvals pending count badge → `/approvals` (Admin, Manager only)
- User avatar + role chip (right-aligned) → user dropdown menu
- User dropdown: Profile | Account Settings | Logout

Do not add topbar elements not in this list.

### 2.3 Archetype System

All screens must use the H01–H13 archetype system from `design/hrms-archetype-system-v1.md`. Mapping is established in FRONTEND_SCREEN_CATALOG.md. Do not assign a screen to an archetype that differs from the established mapping without a documented reason.

| Archetype | Purpose | Screen Count |
|-----------|---------|--------------|
| H01 | Dashboard (role-adaptive, widget grid) | 4 variants |
| H02 | List/Table (data grid, filters, export) | 7 core |
| H03 | Detail/Profile (tabs, content sections) | 6 core |
| H04 | Create/Edit Form (single or multi-step) | 6 core |
| H05 | Workflow/Approval (split-view inbox) | 1 core |
| H06 | Calendar/Timeline (visual scheduling) | 2 core |
| H07 | Analytics/Reports (charts, filters) | 4 core |
| H08 | Search (query + results list) | 1 core |
| H09 | Inbox/Feed (notification list + folders) | 1 core |
| H10 | Settings (section-based admin panel) | 1 core |
| H11 | Builder (visual editor canvas) | 2 core |
| H12 | Support/Ticket | ADD-ON |
| H13 | Candidate Pipeline (Kanban board) | 1 core |

---

## CONSTRAINT CLASS 3 — NAVIGATION (ROLE-BASED SIDEBAR)

### 3.1 Sidebar Sections by Role — Fixed

Each role has a fixed sidebar composition. Do not add nav items to a role that has no permission for the route.

| Section | Routes | Roles |
|---------|--------|-------|
| A: Core | Dashboard, Notifications | All |
| B: People & Org | Employees, Departments, Organisation, Roles | A (all 4), M (no Roles) |
| C: Attendance & Leave | Attendance, Leave | A, M, E (Attendance + Leave); PA (Leave only); R (Leave only) |
| D: Payroll | Payroll | PA, A, M |
| E: Hiring | Hiring, Job Postings, Pipeline | A, M, R |
| F: Approvals | Approvals | A, M |
| G: Analytics & Compliance | Reporting, Compliance, Audit Log, Decision Cards | A (all 4); M (Reporting + Decisions); PA (Compliance + Decisions) |
| H: Automation | Automations, Workflow Builder, Report Builder | A only |
| I: Settings | Settings | A only |

**Empty section rule:** If a role has zero items in a section, OMIT the section heading. Do not render an empty section.

**ADD-ON nav items:** Performance, Expense Claims, Helpdesk, Engagement, Survey Builder — render ONLY when the feature is enabled. Do not show by default in Phase 4 core.

### 3.2 Sidebar Compositions (Exact)

**Admin:** Dashboard → People & Org (Employees, Departments, Organisation, Roles) → Attendance & Leave (Attendance, Leave) → Payroll → Hiring (Hiring, Job Postings, Pipeline) → Approvals → Analytics (Reporting, Compliance, Audit Log, Decision Cards) → Automation (Automations, Workflow Builder, Report Builder) → Settings → Notifications

**PayrollAdmin:** Dashboard → Attendance & Leave (Leave only) → Payroll → Analytics (Compliance, Decision Cards) → Notifications

**Manager:** Dashboard → People & Org (Employees, Departments, Organisation — no Roles) → Attendance & Leave (Attendance, Leave) → Payroll → Hiring (Hiring, Job Postings, Pipeline) → Approvals → Analytics (Reporting, Decision Cards) → Notifications

**Recruiter:** Dashboard → Hiring (Hiring, Job Postings, Pipeline) → Notifications

**Employee:** Dashboard → Attendance → Leave → Payslip (own payslip deep-link) → Notifications

---

## CONSTRAINT CLASS 4 — PERMISSION RENDERING RULES

### 4.1 Navigation

- Render nav items ONLY for routes the JWT role can access
- Never render a nav item and then disable it — omit it entirely

### 4.2 Action Buttons

- Render action buttons (Add, Edit, Delete, Approve, Run Payroll, Trigger Disbursement) ONLY for roles with the required capability
- DISABLED state is not acceptable for capability-restricted actions — the button must not exist
- "Trigger Disbursement" button: Admin, PayrollAdmin only (CAP-BNK-002)
- "Run Payroll" button: Admin, PayrollAdmin only (CAP-PAY-002)
- "Add Employee" button: Admin only (CAP-EMP-002)
- "Mark Resolved" on Decision Cards: Admin only (CAP-DEC-002)

### 4.3 Scope Filtering

| Scope | Roles | Rule |
|-------|-------|------|
| Global | Admin, PayrollAdmin | All data, no filter |
| Department-scoped | Manager | Only own-dept data; filter applied at API level |
| Own-records | Employee, Recruiter (own leave) | Only own records; X-User-Id scope at API level |

### 4.4 Sensitive Data

- Salary/compensation data: visible to Admin and PayrollAdmin in full; Manager sees own-dept only; Employee sees own only (compensation tab on own profile)
- Banking details (disbursement): Admin, PayrollAdmin only (CAP-BNK-001)
- `/api/v1/audit`: Admin only — omit from all other role experiences

---

## CONSTRAINT CLASS 5 — API ENVELOPE HANDLING

### 5.1 Non-Standard Envelope (C-001)

Four services return `{status, data, service}` instead of `{status, data, meta, error}`:

| Service | Gateway Route | Implication |
|---------|--------------|-------------|
| compliance-service | `/api/v1/compliance` | No `meta` — no pagination cursor |
| decision-engine | `/api/v1/decisions` | No `meta` — in-memory; may be empty after restart |
| banking-service | `/api/v1/banking` | No `meta` — surfaces through payroll detail |
| whatsapp-service | `/api/v1/whatsapp` | No `meta` — chrome-only config |

**Design implication:** Screens consuming these 4 services must not show pagination controls. Decision Cards screen and Compliance screen must handle the `service` identifier field and the absence of `meta`.

### 5.2 Settings Volatility (C-002)

Settings-service uses an in-memory dict stub. Settings reset on service restart in development.

**Design implication:** Settings screen (H10) must never show a "cached" or "saved to device" state. Always fetch fresh. Leave type list and grade bands (used in leave and employee forms) come from settings and may reset.

### 5.3 Decision Cards (In-Memory)

Decision Cards (`/decisions`) are NOT persisted. After service restart, the list may be empty.

**Design implication:** Decision Cards screen must have a robust empty state: "No active decision cards" with an explanation that cards are generated during payroll processing. Do not show an error for empty list.

---

## CONSTRAINT CLASS 6 — FRONTEND STATES (MANDATORY FOR ALL SCREENS)

Every screen, every widget, every data table MUST implement these 4 states:

| State | Design Requirement |
|-------|-------------------|
| Loading | Skeleton / shimmer that matches the layout of the expected rendered content (matching column widths, heights, shapes) |
| Empty | Meaningful empty state: illustration or icon + explanation + primary CTA (not just blank space) |
| Error | Error card/banner with retry action; partial failures must not crash the full screen |
| Data | Rendered content |

**Dashboard-specific:** Widget-level isolation. Each widget must have its own loading/empty/error state. Dashboard does not fail if one widget fails.

**Empty dashboard (new tenant):** Show onboarding checklist: (1) Add your first employee, (2) Configure organization settings, (3) Set leave policies, (4) Create first job posting. KPI row stays visible with 0 values.

---

## CONSTRAINT CLASS 7 — MULTI-STEP FORMS (H04)

### 7.1 Add Employee (H04-01) — 6 Steps

Step 1: Personal Info → Step 2: Employment → Step 3: Role & Department → Step 4: Compensation → Step 5: Access & Roles → Step 6: Review

- Cannot advance without completing required fields for current step
- Step 3 requires role and department dropdowns (calls `GET /api/v1/roles`, `GET /api/v1/departments`)
- Step 6 is a read-only review with Edit button per section before final submit

### 7.2 Create Job Posting (H04-05) — 4 Steps

Step 1: Job Details → Step 2: Requirements → Step 3: Pipeline Template → Step 4: Publish

### 7.3 All Multi-Step Forms

- Progress indicator is required
- Back navigation must not lose completed step data
- Submission navigates to the created resource detail screen

---

## CONSTRAINT CLASS 8 — CANDIDATE PIPELINE (H13)

### 8.1 Kanban Board Rules

| Frontend Column | Backend Stage | Notes |
|----------------|--------------|-------|
| Applied | `Applied` | Entry column |
| Screening | `Screening` | — |
| Interview | `Interviewing` | Maps to backend `Interviewing` |
| Final Round | `Interviewing` | UI-ONLY stage — no separate backend value |
| Offer Sent | `Offered` | Backend uses `Offered` |
| (Hired) | `Hired` | Removed from active kanban; shown in summary |
| (Rejected) | `Rejected` | Removed from active kanban; shown in filter |

**Design implication:** "Final Round" is a frontend-only visual stage. Drag from Interview → Final Round does NOT call the API. Only dragging from Final Round → Offer Sent triggers `PATCH {stage: "Offered"}`.

### 8.2 Candidate Slide-Over

- Detail panel is a slide-over (H03 pattern)
- Contains: candidate profile, interview history, notes, stage action buttons
- Accessible from H13 pipeline by clicking a candidate card

---

## CONSTRAINT CLASS 9 — APPROVAL INBOX (H05)

### 9.1 Split-View Layout

- Left panel: 340px fixed — pending approval list, sorted by `created_at` DESC
- Right panel: flex — detail view for selected item

### 9.2 Approval Types

The approval inbox aggregates from workflow-service. Approval types:

| Type | Source | Workflow |
|------|--------|---------|
| Leave approval | `GET /api/v1/workflows?status=pending&type=leave_approval` | WF-002 |
| EWA approval | `GET /api/v1/workflows?status=pending&type=ewa_approval` | WF-008 |
| Expense approval (ADD-ON) | `GET /api/v1/workflows?status=pending&type=expense_approval` | WF-006 |
| Payroll approval (optional) | `GET /api/v1/workflows?status=pending&type=payroll_approval` | WF-003 |

### 9.3 Actions

- Approve: inline confirmation; no separate page
- Reject: reason input required (not optional)
- On approve/reject: item removed from list; next item selected or empty state shown
- "Delegate" is future scope — do not design in Phase 4

---

## CONSTRAINT CLASS 10 — SETTINGS SCREEN (H10)

### 10.1 Backend-Persistent Sections (Must Call API)

| Section | API |
|---------|-----|
| Company Details | `GET /api/v1/settings`, `PUT /api/v1/settings` |
| Leave Policies | `GET /api/v1/settings`, `PUT /api/v1/settings` |
| Payroll Config | `GET /api/v1/settings`, `PUT /api/v1/settings` |
| Roles & Permissions | auth-service (separate from settings-service) |
| Attendance Rules | `GET /api/v1/settings`, `PUT /api/v1/settings` |

### 10.2 Chrome-Only Sections (No Backend Persistence in Phase 3)

These sections render UI but have NO backend persistence:
- Profile (no `/api/v1/auth/profile` endpoint confirmed)
- Security (session management chrome-only)
- Notifications preferences (no `/api/v1/notifications/preferences`)
- Integrations (WhatsApp config chrome-only)
- AI & Automation preferences (no confirmed API)

**Design implication:** Chrome-only sections must show a clear "Settings are not saved to server" notice or be disabled/placeholder state. Do not design full persistence UX for these sections.

---

## CONSTRAINT CLASS 11 — BREADCRUMB MODEL

| Pattern | Example |
|---------|---------|
| 1 level | Dashboard |
| 2 levels (list → detail) | Employees / Jane Smith |
| 2 levels (section → sub) | Payroll / March 2026 |
| 3 levels (list → detail → action) | Employees / Jane Smith / Edit |
| 3 levels (section → sub → detail) | Hiring / Job Postings / Senior Engineer |

**Rule:** Every breadcrumb segment except the final one must be a clickable link.

---

## CONSTRAINT CLASS 12 — WHAT CLAUDE DESIGN MAY DECIDE

The following are implementation details within the constraints above. Claude Design has discretion:

- Exact color palette within brand guidelines
- Typography scale (sizes, weights) within the Inter + JetBrains Mono requirement
- Icon library selection
- Specific animation/transition timing
- Card vs. table layout within an archetype's content area
- Exact empty-state illustration style
- Loading skeleton shape refinements
- Color coding for status badges (must be semantically consistent: green = active/success, red = error/terminated, yellow/orange = pending/warning)
- Exact form field layout within a step (ordering of fields, groupings)
- Toast vs. inline notification for form success/error
