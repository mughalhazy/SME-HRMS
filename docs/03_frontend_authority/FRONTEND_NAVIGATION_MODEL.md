# FRONTEND NAVIGATION MODEL

Status: Complete
Created: 2026-06-17
Phase: 3 — Frontend Authority Capture
Source: security-model.md, archetype-system-v1.md, PRODUCT_DECISION_REGISTER §2.1

---

## PURPOSE

Defines the complete role-based navigation structure including sidebar, topbar, and contextual menus. Every nav item is justified by a confirmed route, confirmed role capability, and confirmed backend API.

---

## CHROME DIMENSIONS (from archetype system)

| Element | Collapsed | Expanded |
|---------|-----------|----------|
| Sidebar width | 54px | 216px |
| Topbar height | 52px | — |
| Content background | #F5F7FA | — |
| Primary font | Inter | — |
| Monospace font | JetBrains Mono (numbers, IDs) | — |

---

## TOPBAR ELEMENTS (ALL ROLES)

The topbar is consistent across all roles and contains:

| Element | Component | Action |
|---------|-----------|--------|
| Product logo / tenant name | Left-aligned | Navigate to `/dashboard` |
| Global search trigger | Center or right | Open `/search` or inline search modal |
| Notifications bell | Icon + unread count badge | Navigate to `/notifications` |
| Approvals pending count | Icon + count badge | Navigate to `/approvals` (A, M only) |
| User avatar + role chip | Right-aligned | Open user menu |
| User menu | Dropdown | Profile, Account Settings, Logout |

---

## SIDEBAR NAVIGATION — BY ROLE

Each sidebar entry shows: Label | Route | Icon | Roles | Feature

### SECTION A: CORE (ALL AUTHENTICATED ROLES)

| Label | Route | Roles | Feature |
|-------|-------|-------|---------|
| Dashboard | `/dashboard` | A, PA, M, R, E | F-001 |
| Notifications | `/notifications` | A, PA, M, R, E | F-009 |

### SECTION B: PEOPLE & ORG (A, M)

| Label | Route | Roles | Feature |
|-------|-------|-------|---------|
| Employees | `/employees` | A, M | F-001 |
| Departments | `/departments` | A, M | F-001 |
| Organisation | `/organization` | A, M | F-001 |
| Roles | `/roles` | A | F-001 |

### SECTION C: ATTENDANCE & LEAVE

| Label | Route | Roles | Feature |
|-------|-------|-------|---------|
| Attendance | `/attendance` | A, M, E | F-002 |
| Leave | `/leave` | A, PA, M, R, E | F-003 |

### SECTION D: PAYROLL (PA, A, M)

| Label | Route | Roles | Feature |
|-------|-------|-------|---------|
| Payroll | `/payroll` | PA, A, M | F-004 |

### SECTION E: HIRING (A, M, R)

| Label | Route | Roles | Feature |
|-------|-------|-------|---------|
| Hiring | `/hiring` | A, M, R | F-005 |
| Job Postings | `/job-postings` | A, M, R | F-005 |
| Pipeline | `/candidates-pipeline` | A, M, R | F-005 |

### SECTION F: APPROVALS (A, M)

| Label | Route | Roles | Feature |
|-------|-------|-------|---------|
| Approvals | `/approvals` | A, M | F-007 |

### SECTION G: ANALYTICS & COMPLIANCE (A, PA, M)

| Label | Route | Roles | Feature |
|-------|-------|-------|---------|
| Reporting | `/reporting` | A, M | F-012 |
| Compliance | `/compliance` | A, PA | F-011 |
| Audit Log | `/audit` | A | F-008 |
| Decision Cards | `/decisions` | A, M, PA | F-014 |

### SECTION H: AUTOMATION (A)

| Label | Route | Roles | Feature |
|-------|-------|-------|---------|
| Automations | `/automations` | A | F-013 |
| Workflow Builder | `/builders/workflow` | A | F-007, F-013 |
| Report Builder | `/builders/report` | A | F-012 |

### SECTION I: SETTINGS (A)

| Label | Route | Roles | Feature |
|-------|-------|-------|---------|
| Settings | `/settings` | A | F-010 |

### ADD-ON SECTIONS (deferred — render when feature enabled)

| Label | Route | Roles | Feature |
|-------|-------|-------|---------|
| Performance | `/performance` | A, M | F-017 ADD-ON |
| Expense Claims | `/expense-claims` | A, M, E | F-021 ADD-ON |
| Helpdesk | `/helpdesk` | A, PA, M, R, E | F-019 ADD-ON |
| Engagement | `/reporting/engagement` | A, M | F-018 ADD-ON |
| Survey Builder | `/builders/survey` | A | F-018 ADD-ON |

---

## COMPLETE SIDEBAR BY ROLE

### Admin Sidebar

```
Dashboard            /dashboard
───────────────────
People & Org
  Employees          /employees
  Departments        /departments
  Organisation       /organization
  Roles              /roles
───────────────────
Attendance & Leave
  Attendance         /attendance
  Leave              /leave
───────────────────
Payroll              /payroll
───────────────────
Hiring
  Hiring             /hiring
  Job Postings       /job-postings
  Pipeline           /candidates-pipeline
───────────────────
Approvals            /approvals
───────────────────
Analytics
  Reporting          /reporting
  Compliance         /compliance
  Audit Log          /audit
  Decision Cards     /decisions
───────────────────
Automation
  Automations        /automations
  Workflow Builder   /builders/workflow
  Report Builder     /builders/report
───────────────────
Settings             /settings
───────────────────
Notifications        /notifications
```

### PayrollAdmin Sidebar

```
Dashboard            /dashboard
───────────────────
Attendance & Leave
  Leave              /leave
───────────────────
Payroll              /payroll
───────────────────
Analytics
  Compliance         /compliance
  Decision Cards     /decisions
───────────────────
Notifications        /notifications
```

### Manager Sidebar

```
Dashboard            /dashboard
───────────────────
People & Org
  Employees          /employees
  Departments        /departments
  Organisation       /organization
───────────────────
Attendance & Leave
  Attendance         /attendance
  Leave              /leave
───────────────────
Payroll              /payroll
───────────────────
Hiring
  Hiring             /hiring
  Job Postings       /job-postings
  Pipeline           /candidates-pipeline
───────────────────
Approvals            /approvals
───────────────────
Analytics
  Reporting          /reporting
  Decision Cards     /decisions
───────────────────
Notifications        /notifications
```

### Recruiter Sidebar

```
Dashboard            /dashboard
───────────────────
Hiring
  Hiring             /hiring
  Job Postings       /job-postings
  Pipeline           /candidates-pipeline
───────────────────
Notifications        /notifications
```

### Employee Sidebar

```
Dashboard            /dashboard
───────────────────
Attendance           /attendance
Leave                /leave
Payslip              /payroll  (own records only)
───────────────────
Notifications        /notifications
```

---

## BREADCRUMB MODEL

Breadcrumbs follow the navigation hierarchy. Rules:

| Level | Example |
|-------|---------|
| 1-level | Dashboard |
| 2-level (list → detail) | Employees / Jane Smith |
| 2-level (section → sub) | Payroll / March 2026 |
| 3-level (list → detail → action) | Employees / Jane Smith / Edit |
| 3-level (section → sub → detail) | Hiring / Job Postings / Senior Engineer |

Breadcrumbs always link: every segment except the last is a clickable link.

---

## IN-PAGE NAVIGATION

### H03 Employee Profile Tabs

| Tab | Content |
|-----|---------|
| Overview | Key info: role, department, start date, contact, manager |
| Compensation | Salary history, grade band, allowances |
| Documents | Contracts, ID, certificates |
| Leave | Leave balance, recent requests |
| Performance | Review history, goals (ADD-ON) |
| History | Audit trail: all changes to this employee's record |

### H07 Reporting Tabs

| Tab | Feature |
|-----|---------|
| HR Analytics | F-012 — headcount, attrition, hiring funnel |
| Payroll Reports | F-012 + F-004 — period cost, disbursement |
| Attendance Summary | F-012 + F-002 — absences, late arrivals |
| Engagement Results | F-018 ADD-ON — survey scores |
| Compliance Reports | F-011 — statutory filings |

### H10 Settings Sections

| Section | Backend Persistent |
|---------|-------------------|
| Company Details | Yes — settings-service |
| Leave Policies | Yes — settings-service |
| Payroll Config | Yes — settings-service |
| Roles & Permissions | Yes — auth-service |
| Attendance Rules | Yes — settings-service |
| Profile | Chrome-only (no backend in Phase 3) |
| Security | Chrome-only (no backend in Phase 3) |
| Notifications | Chrome-only (no backend in Phase 3) |
| Integrations | Chrome-only (no backend in Phase 3) — integration-service future |
| AI & Automation | Chrome-only (no backend in Phase 3) |

---

## CONTEXTUAL ACTIONS (NOT NAVIGATION)

Contextual actions appear in-screen, not in the sidebar. They do not constitute navigation routes but must be accounted for in UI rendering:

| Action | Location | Route/API |
|--------|----------|-----------|
| Add Employee | Employees list header | → `/employees/new` |
| Export employees | Employees list header | `GET /api/v1/employees?export=csv` |
| Initiate Payroll Run | Payroll list header | → `/payroll/run` |
| Create Job Posting | Job Postings header | → `/job-postings/new` |
| Raise Leave Request | Leave calendar / My Leave | → `/leave/new` |
| Salary Revision | Employee profile actions | → `/salary-revision` (H04) |
| Mark notification read | Notification inbox | `PATCH /api/v1/notifications/{id}/read` |
| Approve / Reject | Approvals inbox split-view | `PUT /api/v1/workflows/{id}/steps/{step_id}` |

---

## EMPTY SIDEBAR STATES

If a role has no items in a sidebar section, that section heading is omitted entirely (not rendered as empty). This applies to:
- Recruiter: sections B (People & Org), C (Attendance), D (Payroll), F (Approvals), G (Analytics), H (Automation), I (Settings) — all omitted
- Employee: sections B, D (full), E, F, G, H, I — all omitted
- PayrollAdmin: sections B, E, F, H, I — all omitted
