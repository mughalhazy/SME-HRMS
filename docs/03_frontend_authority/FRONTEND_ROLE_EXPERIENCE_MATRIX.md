# FRONTEND ROLE EXPERIENCE MATRIX

Status: Complete
Created: 2026-06-17
Phase: 3 — Frontend Authority Capture
Source: security-model.md, PRODUCT_DECISION_REGISTER.md, archetype-system-v1.md, PRODUCT_WORKFLOWS.md

---

## PURPOSE

Defines the complete frontend experience for each user role. For every role: which screens are accessible, which actions are available, what the primary user journey looks like, and what restrictions apply.

---

## ROLE 1: ADMIN

**Definition:** Super-user with global scope. Full access to all features.
**JWT role claim:** `Admin`
**Scope:** Global (all tenants' data within own tenant)

### Accessible Routes

All Phase 3 core routes. Every nav item is visible.

### Dashboard Variant

HR Manager Dashboard (global scope — all departments, all employees).

### Primary Capabilities

| Capability | UI Access |
|-----------|-----------|
| CAP-EMP-001/002 | View, create, edit all employees |
| CAP-ATT-001/002 | View all attendance; manage attendance rules |
| CAP-LEV-001/002 | View all leave; approve/reject; manage policies |
| CAP-PAY-001/002 | View, run, disburse payroll |
| CAP-HIR-001/002 | All hiring screens and actions |
| CAP-AUT-001/002/003 | Manage roles, automations, workflow builder, sessions |
| CAP-NOT-001/002 | Receive + send broadcast notifications |
| CAP-COM-001/002 | View + manage compliance |
| CAP-DEC-001/002 | View all decision cards + resolve them |
| CAP-BNK-001/002 | View banking details + trigger disbursements |
| CAP-EWA-002 | Approve EWA requests |
| CAP-RPT-001/002 | View all reports + build custom reports |
| CAP-WA-001 | Manage WhatsApp integration |

### Primary Journey

1. Login → `/dashboard` (HR Manager Dashboard)
2. Monitor KPIs: total employees, pending approvals, leave today, open positions
3. Handle pending approvals → `/approvals`
4. Manage employees → `/employees` → `/employees/[id]` → edit or add
5. Run payroll → `/payroll` → `/payroll/run`
6. Review compliance → `/compliance`
7. View decision cards → `/decisions`
8. Configure organisation → `/settings`
9. Review audit log → `/audit`
10. Build automations → `/automations`

### Unique Admin-Only Screens

- `/roles` and `/roles/new` — role management
- `/audit` — immutable audit log
- `/automations` — automation rule management
- `/builders/workflow` — workflow builder
- `/builders/report` — report builder
- `/settings` — org settings (full access)
- `/compliance` — compliance reports + management
- `/decisions` — all decision cards with resolve action

---

## ROLE 2: PAYROLLADMIN

**Definition:** Payroll specialist with payroll + compliance focus.
**JWT role claim:** `PayrollAdmin`
**Scope:** Global for payroll and compliance data

### Accessible Routes

```
/dashboard (Payroll Admin variant)
/leave (own leave)
/leave/new (raise own leave)
/payroll (full access)
/payroll/[id]
/payroll/run
/compliance
/decisions (payroll-scoped cards only)
/notifications
```

### Dashboard Variant

Payroll Admin Dashboard — focused on payroll status, cost breakdowns, compliance deadlines.

### Primary Capabilities

| Capability | UI Access |
|-----------|-----------|
| CAP-PAY-001/002 | Full payroll view + run + disburse |
| CAP-COM-001 | View compliance reports |
| CAP-BNK-001/002 | View banking details + trigger disbursements |
| CAP-DEC-001 | View payroll-domain decision cards |
| CAP-LEV-001/002 | Own leave only |
| CAP-EWA-002 | Approve EWA requests |
| CAP-NOT-001 | Receive notifications |

### Primary Journey

1. Login → `/dashboard` (Payroll Admin Dashboard)
2. Check payroll status for current period
3. Initiate payroll run → `/payroll/run`
4. Review payroll records → `/payroll/[id]`
5. Trigger disbursement (CAP-BNK-002)
6. View compliance status → `/compliance`
7. Review decision cards for payroll domain → `/decisions`
8. Receive notifications → `/notifications`

### Restrictions for PayrollAdmin

- Cannot view `/employees` list (no CAP-EMP-001 full access)
- Cannot view `/hiring`, `/job-postings`, `/candidates-pipeline`
- Cannot view `/audit`
- Cannot access `/settings`
- Cannot access `/automations` or builders
- `/decisions` shows only payroll-domain cards

---

## ROLE 3: MANAGER

**Definition:** Team/department lead. Access to own team's data.
**JWT role claim:** `Manager`
**Scope:** Department-scoped (own department(s) only)

### Accessible Routes

```
/dashboard (HR Manager variant — dept-scoped)
/employees (own dept employees only)
/employees/[id] (own dept only)
/departments (own dept only)
/organization (view org tree)
/attendance (own dept)
/attendance/timeline (own dept)
/leave (own dept + own)
/leave/requests (own dept)
/leave/requests/[id] (own dept)
/leave/new (raise own)
/leave/calendar (team view)
/payroll (own dept only)
/payroll/[id] (own dept)
/hiring (all posting)
/job-postings (all)
/job-postings/[id]
/job-postings/new
/candidates-pipeline
/candidates-pipeline/[id]
/approvals (pending for own team)
/reporting (dept-scoped HR analytics + attendance)
/decisions (dept-scoped cards)
/notifications
```

### Dashboard Variant

HR Manager Dashboard — same layout as Admin, data scoped to own department.

### Primary Capabilities

| Capability | UI Access |
|-----------|-----------|
| CAP-EMP-001 | View own-dept employees (read) |
| CAP-EMP-002 | Edit own-dept employees (limited field set) |
| CAP-ATT-001 | View own-dept attendance |
| CAP-LEV-001/002 | View + approve own-dept leave; raise own leave |
| CAP-PAY-001 | View own-dept payroll (read-only) |
| CAP-HIR-001/002 | Full hiring access |
| CAP-DEC-001 | View dept-scoped decision cards |
| CAP-EWA-002 | Approve EWA requests from own team |
| CAP-RPT-001 | View HR + attendance reports (dept-scoped) |
| CAP-NOT-001 | Receive notifications |

### Primary Journey

1. Login → `/dashboard` (HR Manager Dashboard, dept-scoped)
2. Review pending approvals → `/approvals`
3. Approve/reject leave requests for team
4. Check team attendance → `/attendance`
5. Manage hiring → `/candidates-pipeline`
6. View team reports → `/reporting`
7. Review AI decision cards → `/decisions`

### Restrictions for Manager

- Cannot view employees outside own department
- Cannot run payroll (CAP-PAY-002 denied — no "Run Payroll" button)
- Cannot trigger disbursement (CAP-BNK-002 denied)
- Cannot access `/settings`
- Cannot access `/audit`
- Cannot access `/compliance`
- Cannot access `/automations` or builders
- `/decisions` filtered to dept-relevant cards only

---

## ROLE 4: RECRUITER

**Definition:** Hiring specialist. Access to hiring screens only.
**JWT role claim:** `Recruiter`
**Scope:** Global for hiring data

### Accessible Routes

```
/dashboard (Recruitment Dashboard)
/hiring
/job-postings
/job-postings/[id]
/job-postings/new
/candidates-pipeline
/candidates-pipeline/[id]
/notifications
```

### Dashboard Variant

Recruitment Dashboard — hiring funnel, pipeline overview, open positions, interviews this week.

### Primary Capabilities

| Capability | UI Access |
|-----------|-----------|
| CAP-HIR-001/002 | Full hiring access — create postings, manage pipeline |
| CAP-LEV-002 | Raise own leave requests |
| CAP-NOT-001 | Receive notifications |

### Primary Journey

1. Login → `/dashboard` (Recruitment Dashboard)
2. Review hiring funnel KPIs
3. View candidate pipeline → `/candidates-pipeline`
4. Move candidates through stages
5. Schedule interviews from candidate detail
6. Create new job posting → `/job-postings/new`
7. Review notifications → `/notifications`

### Restrictions for Recruiter

- No access to `/employees` (CAP-EMP-001 denied — employee management is not HR responsibility for Recruiter)
- No access to `/payroll`, `/attendance`, `/leave/requests` (team view)
- No access to `/approvals` (Recruiter does not approve leave/payroll)
- No access to `/reporting`, `/compliance`, `/audit`, `/decisions`
- No access to `/settings`, `/automations`, `/roles`
- Sidebar shows only Dashboard, Hiring section, Notifications

---

## ROLE 5: EMPLOYEE

**Definition:** Individual contributor. Access to own data only.
**JWT role claim:** `Employee`
**Scope:** Own records only (X-User-Id enforced at API level)

### Accessible Routes

```
/dashboard (Employee Self-Service variant)
/employees/[id] (own ID only)
/attendance (own records)
/leave (own leave)
/leave/new
/leave/calendar (team calendar — read-only, approved leave only)
/payroll/[id] (own payslips only — linked from dashboard)
/employees/[id]/ewa (own EWA requests)
/notifications
```

### Dashboard Variant

Employee Self-Service Dashboard — leave balance, attendance this month, latest payslip, pending requests.

### Primary Capabilities

| Capability | UI Access |
|-----------|-----------|
| CAP-ATT-001 (own) | View own attendance records |
| CAP-LEV-001 (own) | View own leave requests + balance |
| CAP-LEV-002 | Raise leave requests |
| CAP-PAY-001 (own) | View own payslips |
| CAP-EWA-001 | Request salary advance |
| CAP-NOT-001 | Receive notifications |

### Primary Journey

1. Login → `/dashboard` (Employee Self-Service Dashboard)
2. Check leave balance on dashboard KPI
3. Raise leave request → `/leave/new`
4. Check own attendance history → `/attendance`
5. View latest payslip from dashboard → `/payroll/[id]` (own)
6. Read approval notifications → `/notifications`
7. View own profile → `/employees/[id]` (own)

### Restrictions for Employee

- Cannot view any other employee's records
- Cannot access `/employees` list
- Cannot access `/payroll` list (only linked to own payslip via direct ID)
- Cannot access `/hiring`, `/job-postings`, `/candidates-pipeline`
- Cannot access `/approvals` (no approval authority)
- Cannot access `/reporting`, `/compliance`, `/audit`, `/decisions`
- Cannot access `/settings`, `/automations`, `/roles`
- Nav: only Dashboard, Attendance, Leave, (own) Payslip link, Notifications

---

## CROSS-ROLE COMPARISON TABLE

| Screen | Admin | PayrollAdmin | Manager | Recruiter | Employee |
|--------|-------|-------------|---------|-----------|----------|
| `/dashboard` | HR Mgr (global) | Payroll Admin | HR Mgr (dept) | Recruitment | Self-Service |
| `/employees` | ✅ Full | ❌ | ✅ Dept-scoped | ❌ | ❌ |
| `/employees/new` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/departments` | ✅ | ❌ | ✅ Own dept | ❌ | ❌ |
| `/attendance` | ✅ All | ❌ | ✅ Dept-scoped | ❌ | ✅ Own |
| `/leave` | ✅ All | ✅ Own | ✅ Team + Own | ✅ Own | ✅ Own |
| `/leave/requests` | ✅ All | ❌ | ✅ Dept | ❌ | ❌ |
| `/approvals` | ✅ | ❌ | ✅ | ❌ | ❌ |
| `/payroll` | ✅ | ✅ Full | ✅ Dept | ❌ | Own link only |
| `/payroll/run` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/hiring` | ✅ | ❌ | ✅ | ✅ | ❌ |
| `/candidates-pipeline` | ✅ | ❌ | ✅ | ✅ | ❌ |
| `/notifications` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `/settings` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/compliance` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `/audit` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/decisions` | ✅ All | ✅ Payroll | ✅ Dept | ❌ | ❌ |
| `/automations` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/reporting` | ✅ | ✅ Payroll | ✅ Dept | ❌ | ❌ |
| `/roles` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/search` | ✅ | ✅ | ✅ | ✅ | ✅ |
