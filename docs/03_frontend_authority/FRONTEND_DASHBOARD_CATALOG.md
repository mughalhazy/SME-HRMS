# FRONTEND DASHBOARD CATALOG

Status: Complete
Created: 2026-06-17
Phase: 3 — Frontend Authority Capture
Source: archetype-system-v1.md H01, security-model.md, API_CONTRACT.md, PRODUCT_DECISION_REGISTER.md

---

## PURPOSE

Defines each of the four H01 Dashboard variants. All four variants render at `/dashboard`. The role claim in JWT determines which variant is shown. No separate routes per role.

**Archetype:** H01 — Dashboard
**Layout:** Full-width content area. Sidebar 54px collapsed / 216px expanded. Topbar 52px.
**Widget grid:** Responsive grid layout. KPI metric cards in top row; charts and tables below.

---

## DASHBOARD SELECTION LOGIC

```
JWT role claim → dashboard variant

Admin         → HR Manager Dashboard
PayrollAdmin  → Payroll Admin Dashboard
Manager       → HR Manager Dashboard (dept-scoped)
Recruiter     → Recruitment Dashboard
Employee      → Employee Self-Service Dashboard
```

**Note:** Admin and Manager share the same dashboard variant (HR Manager Dashboard). Manager's data is scoped to their department via X-User-Id / X-Tenant-Id scope enforcement in the API. The dashboard does not branch on Admin vs Manager for layout — only for action availability (e.g., "Add Employee" button visible to Admin only).

---

## DASHBOARD 1: HR MANAGER DASHBOARD

**Roles:** Admin (global scope), Manager (department scope)
**Wireframe:** `frontend/pages/h01-hr-manager-dashboard.html`
**Feature:** F-001, F-002, F-003, F-004, F-012

### KPI Row (top metric cards)

| Metric | API Source | Admin Scope | Manager Scope |
|--------|-----------|-------------|---------------|
| Total Employees | `GET /api/v1/employees/summary` | All employees | Dept employees |
| On Leave Today | `GET /api/v1/leave?today=true` | All | Dept |
| Open Positions | `GET /api/v1/hiring/postings?status=open` | All | Dept (if any) |
| Pending Approvals | `GET /api/v1/workflows?status=pending` | All pending | Approver=self |
| Attendance Rate Today | `GET /api/v1/attendance/summary?today=true` | Org-wide | Dept |

### Charts Row

| Widget | Type | API Source | Description |
|--------|------|-----------|-------------|
| Headcount Trend | Line chart | `GET /api/v1/reporting/dashboards?widget=headcount` | 12-month employee count trend |
| Department Breakdown | Bar / pie | `GET /api/v1/departments` + employee count | Employees per department |
| Attendance Heatmap | Calendar heatmap | `GET /api/v1/attendance/summary` | Attendance over last 30 days |
| Attrition Rate | KPI + sparkline | `GET /api/v1/reporting/dashboards?widget=attrition` | Monthly attrition % |

### Action Tables / Lists

| Widget | API Source | Admin Actions | Manager Actions |
|--------|-----------|---------------|-----------------|
| Recent Employees | `GET /api/v1/employees?sort=created_at&limit=5` | View, Edit, Add | View |
| Pending Leave Requests | `GET /api/v1/leave?status=pending&limit=5` | Approve, Reject, View | Approve (dept), View |
| Pending Approvals | `GET /api/v1/workflows?status=pending&limit=5` | Approve, Reject | Approve, Reject |

### Quick Actions (Admin only)

| Action | Route |
|--------|-------|
| Add Employee | `/employees/new` |
| Run Payroll | `/payroll/run` |
| Create Job Posting | `/job-postings/new` |
| View Audit Log | `/audit` |

---

## DASHBOARD 2: EMPLOYEE SELF-SERVICE DASHBOARD

**Roles:** Employee
**Wireframe:** `frontend/pages/h01-employee-self-service.html`
**Feature:** F-002, F-003, F-009

### KPI Row

| Metric | API Source | Description |
|--------|-----------|-------------|
| Leave Balance | `GET /api/v1/leave/balance` | Remaining annual/sick/casual leave days |
| Attendance This Month | `GET /api/v1/attendance?me=true&month=current` | Present days / working days |
| Pending Requests | `GET /api/v1/leave?me=true&status=pending` | Own leave requests awaiting approval |
| Next Payday | `GET /api/v1/payroll?me=true&latest=true` | Days until next payroll disbursement |

### Main Content

| Widget | Type | API Source | Description |
|--------|------|-----------|-------------|
| Leave Calendar | Mini H06 | `GET /api/v1/leave?me=true&calendar=true` | Own approved leave on calendar |
| Recent Attendance | Timeline snippet | `GET /api/v1/attendance?me=true&limit=7` | Last 7 days punch-in/out |
| Latest Payslip | Summary card | `GET /api/v1/payroll?me=true&latest=true` | Net pay for last period |
| Notifications Preview | Feed | `GET /api/v1/notifications?me=true&unread=true&limit=5` | 5 most recent unread notifications |

### Quick Actions

| Action | Route |
|--------|-------|
| Raise Leave Request | `/leave/new` |
| View My Payslips | `/payroll` (own only) |
| View Attendance | `/attendance` (own only) |
| View Notifications | `/notifications` |

---

## DASHBOARD 3: PAYROLL ADMIN DASHBOARD

**Roles:** PayrollAdmin
**Wireframe:** `frontend/pages/h01-payroll-admin-dashboard.html`
**Feature:** F-004, F-011, F-016

### KPI Row

| Metric | API Source | Description |
|--------|-----------|-------------|
| Payroll Status | `GET /api/v1/payroll/status?period=current` | Current period: Draft / Processing / Completed |
| Total Payroll Cost | `GET /api/v1/payroll/summary?period=current` | Gross payroll cost this period |
| Employees on Payroll | `GET /api/v1/payroll/summary` | Count of employees included in current run |
| Pending Disbursements | `GET /api/v1/payroll?status=pending_disbursement` | Payroll runs awaiting bank transfer |
| Compliance Filing Due | `GET /api/v1/compliance?upcoming=true` | Upcoming statutory filing deadlines |

### Charts / Tables

| Widget | Type | API Source | Description |
|--------|------|-----------|-------------|
| Payroll Cost Trend | Line chart | `GET /api/v1/reporting/payroll?widget=cost_trend` | 12-month payroll cost |
| Cost by Department | Bar chart | `GET /api/v1/reporting/payroll?widget=dept_cost` | Dept-level cost breakdown |
| Recent Payroll Runs | Table | `GET /api/v1/payroll?limit=5&sort=created_at` | Last 5 payroll runs with status |
| Decision Cards | Card list | `GET /api/v1/decisions?scope=payroll` | AI-generated payroll decisions |

### Quick Actions

| Action | Route |
|--------|-------|
| Run Payroll | `/payroll/run` |
| View Compliance Reports | `/compliance` |
| View Decision Cards | `/decisions` |
| Review Pending Disbursements | `/payroll?status=pending_disbursement` |

---

## DASHBOARD 4: RECRUITMENT DASHBOARD

**Roles:** Recruiter
**Wireframe:** `frontend/pages/h01-recruitment-dashboard.html`
**Feature:** F-005

### KPI Row

| Metric | API Source | Description |
|--------|-----------|-------------|
| Open Positions | `GET /api/v1/hiring/postings?status=open` | Active job postings |
| Total Applicants | `GET /api/v1/hiring/candidates?status=active` | Candidates in pipeline |
| Interviews This Week | `GET /api/v1/hiring/interviews?this_week=true` | Scheduled interviews |
| Offers Extended | `GET /api/v1/hiring/candidates?stage=Offer Sent` | Candidates at offer stage |
| Hires This Month | `GET /api/v1/hiring/candidates?stage=Hired&month=current` | Conversions this month |

### Charts / Tables

| Widget | Type | API Source | Description |
|--------|------|-----------|-------------|
| Pipeline Funnel | Funnel chart | `GET /api/v1/hiring/pipeline/summary` | Candidates per stage |
| Days-to-Hire Trend | Line chart | `GET /api/v1/reporting/hiring?widget=days_to_hire` | Average hiring cycle length |
| Active Postings | Card list | `GET /api/v1/hiring/postings?status=open&limit=5` | Latest open positions |
| Candidates to Review | Table | `GET /api/v1/hiring/candidates?status=pending_review&limit=10` | Candidates awaiting action |

### Quick Actions

| Action | Route |
|--------|-------|
| Create Job Posting | `/job-postings/new` |
| View Pipeline | `/candidates-pipeline` |
| View All Job Postings | `/job-postings` |

---

## DASHBOARD WIDGET STATES

All dashboard widgets must handle:

| State | Behavior |
|-------|----------|
| Loading | Skeleton / shimmer placeholder matching widget size |
| Empty | Friendly empty state message with primary action CTA (e.g., "No employees yet — Add Employee") |
| Error | Error card with retry button; partial dashboard must still render other widgets |
| Data | Rendered content |

**Partial failure rule:** A single widget API failure must NOT prevent the dashboard from rendering. Each widget fetches independently via TanStack React Query. A widget failure shows its own error state; other widgets continue to render.

---

## EMPTY DASHBOARD POLICY

If a dashboard's key data source returns zero records (e.g., new tenant, no employees added yet), the dashboard renders an onboarding state with a checklist:
1. Add your first employee → `/employees/new`
2. Configure organization settings → `/settings`
3. Set leave policies → `/settings#leave-policies`
4. Create first job posting → `/job-postings/new` (Admin only)

This onboarding state replaces the charts and tables but keeps the KPI row (all values show 0 with a "Get started" prompt).
