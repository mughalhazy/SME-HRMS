# FRONTEND PERMISSION MATRIX

Status: Complete
Created: 2026-06-17
Phase: 3 — Frontend Authority Capture
Source: backend/docs/canon/security-model.md (authoritative), API_CONTRACT.md §4

---

## PURPOSE

Maps every confirmed capability from the security model to its frontend rendering impact. For each capability, defines:
- Which roles hold it
- What the frontend renders when the role has it (ALLOW)
- What the frontend renders when the role lacks it (DENY)
- Scope restrictions that affect data filtering

**Rule:** Frontend RBAC is enforcement-in-depth. Gateway enforces role restrictions at the API level. Frontend only renders UI elements the user can actually use — it never relies solely on hiding elements to secure data.

---

## NOTATION

- A = Admin | PA = PayrollAdmin | M = Manager | R = Recruiter | E = Employee | S = Service
- ✅ = ALLOW | ❌ = DENY | 🔒 = SCOPED (allow with data restriction)
- **(own)** = Employee can only access their own record
- **(dept)** = Manager can only access records within their department(s)

---

## CAPABILITY MATRIX

### EMPLOYEE CAPABILITIES

#### CAP-EMP-001: View Employee Records

| Role | Access | Scope | Frontend ALLOW | Frontend DENY |
|------|--------|-------|----------------|---------------|
| Admin | ✅ | Global | Full employee list, all fields, all departments | — |
| PayrollAdmin | ✅ | Global | View compensation and personal details (read-only) | Cannot edit employee records |
| Manager | 🔒 | Department | List + profile for own dept employees only | Filter applied on API response; no cross-dept access |
| Recruiter | ❌ | — | — | Employee list + profile hidden from nav; redirect to `/hiring` |
| Employee | 🔒 | Own | Own profile tab in `/employees/[id]` (own ID only) | Cannot list all employees; `/employees` not in nav |
| Service | ✅ | Global | N/A (machine principal) | — |

**Frontend impact:** `/employees`, `/employees/[id]`, `/departments`, `/organization` are nav-visible only to Admin and Manager. Employee can access `/employees/[id]` with own ID via direct link (from dashboard).

---

#### CAP-EMP-002: Create/Edit Employee Records

| Role | Access | Scope | Frontend ALLOW | Frontend DENY |
|------|--------|-------|----------------|---------------|
| Admin | ✅ | Global | Add Employee button, Edit Employee form, all fields editable | — |
| PayrollAdmin | ❌ | — | — | No add/edit controls on any employee screen |
| Manager | 🔒 | Department | Edit button visible only for own-dept employees; limited field set | Cannot edit employees outside dept |
| Recruiter | ❌ | — | — | No edit controls |
| Employee | ❌ | — | — | No edit controls on own profile (contact details self-service is future scope) |

**Frontend impact:** "Add Employee" button and "Edit" button are conditional on CAP-EMP-002. Manager sees edit button only for dept-scoped employees. Form fields like compensation grade, role assignment, system access are Admin-only subsets of the form.

---

### ATTENDANCE CAPABILITIES

#### CAP-ATT-001: View Attendance Records

| Role | Access | Scope | Frontend ALLOW | Frontend DENY |
|------|--------|-------|----------------|---------------|
| Admin | ✅ | Global | Full attendance list, all employees, timeline view | — |
| Manager | 🔒 | Department | Attendance records for own dept employees | Cross-dept records filtered out |
| Employee | 🔒 | Own | Own attendance records only at `/attendance` | No list of other employees |

**Frontend impact:** `/attendance` and `/attendance/timeline` are in nav for Admin, Manager, Employee. Employee sees own records only (API enforces with X-User-Id scope).

---

#### CAP-ATT-002: Manage Attendance Rules

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | Attendance Rules section in `/settings` | — |
| All others | ❌ | — | Attendance Rules section hidden from Settings |

---

### LEAVE CAPABILITIES

#### CAP-LEV-001: View Leave Requests

| Role | Access | Scope | Frontend ALLOW | Frontend DENY |
|------|--------|-------|----------------|---------------|
| Admin | ✅ | Global | Full leave list, all employees, approval controls | — |
| Manager | 🔒 | Department | Leave list for own dept; approve/reject actions | Cross-dept filtered |
| Employee | 🔒 | Own | Own leave requests only; balance visible | Cannot see others' leave requests |
| PayrollAdmin | ✅ | Global | Read-only view of leave records (payroll integration) | No approval actions |
| Recruiter | ✅ | Own | Own leave only | Cannot see team leave |

**Frontend impact:** `/leave/requests` (team view) is only visible to Admin and Manager. Employee and Recruiter only see `/leave` (own calendar + own requests).

---

#### CAP-LEV-002: Submit Leave Requests

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | "Raise Leave Request" button visible | — |
| Manager | ✅ | "Raise Leave Request" button visible | — |
| Employee | ✅ | "Raise Leave Request" button visible | — |
| PayrollAdmin | ✅ | "Raise Leave Request" button visible | — |
| Recruiter | ✅ | "Raise Leave Request" button visible | — |

**Frontend impact:** All authenticated users can raise leave requests. The `/leave/new` form is accessible to all roles.

---

### PAYROLL CAPABILITIES

#### CAP-PAY-001: View Payroll Records

| Role | Access | Scope | Frontend ALLOW | Frontend DENY |
|------|--------|-------|----------------|---------------|
| Admin | ✅ | Global | Full payroll list, all employees, all periods | — |
| PayrollAdmin | ✅ | Global | Full payroll list, initiate run, disbursement | — |
| Manager | 🔒 | Department | Payroll records for own dept only | Cross-dept filtered |
| Employee | 🔒 | Own | Own payslips only via `/payroll/[id]` | No payroll list |
| Recruiter | ❌ | — | — | `/payroll` hidden; no payroll nav item |

**Frontend impact:** Gateway enforces payroll route access. Frontend must not render `/payroll` nav link for Recruiter or Employee. Employee can link to own payslip from dashboard.

---

#### CAP-PAY-002: Process Payroll

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | "Run Payroll" button, confirm payroll run | — |
| PayrollAdmin | ✅ | "Run Payroll" button, confirm payroll run | — |
| All others | ❌ | — | "Run Payroll" button hidden |

---

### HIRING CAPABILITIES

#### CAP-HIR-001: View Hiring Data

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | All hiring screens, full candidate data | — |
| Manager | ✅ | All hiring screens, dept-relevant postings | — |
| Recruiter | ✅ | All hiring screens | — |
| PayrollAdmin | ❌ | — | `/hiring` hidden |
| Employee | ❌ | — | `/hiring` hidden |

**Frontend impact:** Gateway enforces hiring route access. Hiring nav section omitted for Employee and PayrollAdmin.

---

#### CAP-HIR-002: Manage Hiring

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | Create/edit job postings, update candidate stages | — |
| Manager | ✅ | Create/edit job postings, update candidate stages | — |
| Recruiter | ✅ | Create/edit job postings, update candidate stages | — |
| All others | ❌ | — | No create/edit controls |

---

### PERFORMANCE CAPABILITY (ADD-ON)

#### CAP-PRF-001: View Performance Data (ADD-ON — F-017)

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | Performance dashboard, review list | — |
| Manager | 🔒 | Team performance reviews | Cross-dept filtered |
| Employee | 🔒 | Own performance reviews only | Cannot view others |

---

### AUTH CAPABILITIES

#### CAP-AUT-001: Manage Roles

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | `/roles` nav item, create/edit roles | — |
| All others | ❌ | — | `/roles` hidden |

---

#### CAP-AUT-002: Manage Automation Rules

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | `/automations` nav item, `/builders/workflow`, create/edit rules | — |
| All others | ❌ | — | Automations hidden |

---

#### CAP-AUT-003: Token & Session Management

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | Security settings section (session management) | — |
| All others | ❌ (own session only) | Own logout only | No session management UI |

---

### NOTIFICATION CAPABILITIES

#### CAP-NOT-001: Receive Notifications

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| All | ✅ | Notifications bell, `/notifications` inbox | — |

---

#### CAP-NOT-002: Send Notifications (Admin)

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | Broadcast notification control in settings | — |
| All others | ❌ | — | No send control |

---

### ENGAGEMENT CAPABILITIES (ADD-ON)

#### CAP-ENG-001: View Engagement Data (ADD-ON)

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | `/reporting/engagement` tab, survey results | — |
| Manager | 🔒 | Own team survey results | — |
| Employee | ❌ | — | No engagement analytics |

---

### COMPLIANCE CAPABILITIES

#### CAP-COM-001: View Compliance Reports

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | `/compliance` nav item, full compliance reports | — |
| PayrollAdmin | ✅ | `/compliance` nav item, payroll compliance reports | — |
| All others | ❌ | — | `/compliance` hidden |

---

#### CAP-COM-002: Manage Compliance (Admin)

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | Compliance settings, filing controls | — |
| All others | ❌ | — | Read-only compliance view |

---

### DECISION CARDS CAPABILITIES

#### CAP-DEC-001: View Decision Cards

| Role | Access | Scope | Frontend ALLOW | Frontend DENY |
|------|--------|-------|----------------|---------------|
| Admin | ✅ | Global | `/decisions` nav item, all cards, all domains | — |
| PayrollAdmin | ✅ | Payroll scope | `/decisions` nav item, payroll-domain cards only | Non-payroll cards filtered |
| Manager | 🔒 | Dept scope | `/decisions` nav item, dept-relevant cards | Cross-dept cards filtered |
| All others | ❌ | — | — | `/decisions` hidden |

---

#### CAP-DEC-002: Resolve Decision Cards

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | "Mark Resolved", "Override" buttons | — |
| All others | ❌ | — | Read-only decision cards |

---

### EWA CAPABILITIES (F-015)

#### CAP-EWA-001: Request EWA (Employee)

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Employee | ✅ | "Request Advance" button on own profile / dashboard | — |
| All others | ❌ | — | No EWA request button |

---

#### CAP-EWA-002: Approve EWA

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | EWA approval in approvals inbox | — |
| PayrollAdmin | ✅ | EWA approval in approvals inbox | — |
| Manager | ✅ | EWA approval in approvals inbox | — |
| Employee | ❌ | — | No approval control |

---

### BANKING CAPABILITIES (F-016)

#### CAP-BNK-001: View Banking Details

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | Disbursement status in payroll detail | — |
| PayrollAdmin | ✅ | Disbursement status in payroll detail | — |
| All others | ❌ | — | Banking details hidden in payroll screen |

---

#### CAP-BNK-002: Trigger Disbursement

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | "Trigger Disbursement" button in payroll run workflow | — |
| PayrollAdmin | ✅ | "Trigger Disbursement" button in payroll run workflow | — |
| All others | ❌ | — | No disbursement control |

---

### REPORTING CAPABILITIES

#### CAP-RPT-001: View Reports

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | `/reporting` nav item, all report tabs | — |
| Manager | 🔒 | `/reporting` nav item, HR + attendance tabs (dept-scoped) | Payroll report tab hidden |
| PayrollAdmin | ✅ | Payroll report tab only | HR analytics tab hidden |
| All others | ❌ | — | `/reporting` hidden |

---

#### CAP-RPT-002: Build Custom Reports

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | `/builders/report` nav item, report builder UI | — |
| All others | ❌ | — | Report builder hidden |

---

### WHATSAPP CAPABILITIES (F-016)

#### CAP-WA-001: WhatsApp Notifications

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | WhatsApp integration toggle in Settings (Integrations) | — |
| All others | ❌ | — | No WhatsApp controls visible |

**Note:** WhatsApp integration is backend-only. No standalone WhatsApp screen exists. Configuration surfaces only in Admin → Settings → Integrations (chrome-only in Phase 3).

---

### EXPENSE CAPABILITY (ADD-ON)

#### CAP-EXP-001: Manage Expenses (ADD-ON — F-021)

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | Expense claims list, approve/reject | — |
| Manager | 🔒 | Team expense claims, approve/reject | — |
| Employee | ✅ | Own expense claims, raise new claim | — |

---

### HELPDESK CAPABILITY (ADD-ON)

#### CAP-HLP-001: Submit Helpdesk Tickets (ADD-ON — F-019)

| Role | Access | Frontend ALLOW |
|------|--------|----------------|
| All | ✅ | `/helpdesk` — submit tickets, view own tickets |

---

#### CAP-HLP-002: Manage Helpdesk Tickets (ADD-ON — F-019)

| Role | Access | Frontend ALLOW | Frontend DENY |
|------|--------|----------------|---------------|
| Admin | ✅ | Full ticket queue, priority/reassign/merge | — |
| All others | ❌ | — | Own tickets only |

---

## GATEWAY-ENFORCED ROUTE RESTRICTIONS

These restrictions are enforced at the API gateway level. Frontend must NOT render the navigation item for unauthorized roles — but even if it does, the API will reject the request.

| Route Prefix | Allowed Roles | Gateway Enforcement |
|-------------|---------------|---------------------|
| `/api/v1/payroll` | Admin, PayrollAdmin, Manager | `_ROUTE_ROLE_MAP` in api_gateway_service.py |
| `/api/v1/audit` | Admin | `_ROUTE_ROLE_MAP` |
| `/api/v1/hiring` | Admin, Manager, Recruiter | `_ROUTE_ROLE_MAP` |
| `/api/v1/reporting` | Admin, Manager | `_ROUTE_ROLE_MAP` |

---

## FRONTEND RENDERING RULES

1. **Navigation items** are conditionally rendered based on role claims from JWT. Never show a nav item for a route the user cannot access.
2. **Action buttons** (Add, Edit, Delete, Approve, Run Payroll) are conditionally rendered based on capability. Disabled state is not acceptable — the button should not exist.
3. **Scope filtering** (dept-scoped, own-only) is enforced by the API. Frontend must not pass cross-scope IDs and must handle 403 responses gracefully with a "Not Authorized" message.
4. **Detail screens** (H03) for sensitive resources must check the API response rather than URL parameters for access control — do not assume that reaching the URL means the user has permission.
5. **Non-standard envelope** services (compliance, decision, banking, whatsapp) return `{status, data, service}` — frontend API client must normalize this to the standard shape or handle the missing `meta` field explicitly.
