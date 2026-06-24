# PRODUCT DECISION REGISTER

Status: Complete
Created: 2026-06-17
Phase: 2.95 — Residual Decision Collapse

---

## PURPOSE

Registers all product-level decisions affecting feature scope, navigation, permissions, workflows, and dashboard composition. Every entry has a status: STABLE (confirmed, no ambiguity), CONFIRMED_BY_CODE (verified from repository), DEFERRED (ADD-ON or future scope), or COLLAPSED (was TBD, now resolved by this phase).

This document is the single source of truth for "what product decisions have been made" before Phase 3 frontend authority capture begins.

---

## SECTION 1: FEATURE SCOPE DECISIONS

### 1.1 Core Features (IMPLEMENTED) — All STABLE

| Feature | Status | Gateway Route | UI Route | Evidence |
|---------|--------|--------------|---------|---------|
| F-001 Workforce Management | STABLE | `/api/v1/employees`, `/departments`, `/roles` | `/employees`, `/departments`, `/organization`, `/roles`, `/employee-profile` | `routes.py`, `employee_api.py` |
| F-002 Attendance Management | STABLE | `/api/v1/attendance` | `/attendance` | `routes.py`, `attendance_service/` |
| F-003 Leave Management | STABLE | `/api/v1/leave` | `/leave`, `/leave-requests` | `routes.py`, `leave_api.py` |
| F-004 Payroll Processing | STABLE | `/api/v1/payroll` | `/payroll` | `routes.py`, `payroll_api.py` |
| F-005 Recruitment / Hiring | STABLE | `/api/v1/hiring` | `/hiring`, `/job-postings`, `/candidates-pipeline` | `routes.py`, `hiring_service/` |
| F-006 Authentication & Authorization | STABLE | `/api/v1/auth` | `/login` | `routes.py`, `auth-service/` |
| F-007 Workflow Engine | STABLE | `/api/v1/workflows` | `/approvals` (COLLAPSED from TBD) | `routes.py`, `automation_service.py` |
| F-008 Audit Logging | STABLE | `/api/v1/audit` | `/audit` (COLLAPSED from TBD) | `routes.py`, `audit_api.py` |
| F-009 Notification System | STABLE | `/api/v1/notifications` | `/notifications` | `routes.py`, `notification_api.py` |
| F-010 Settings & HR Policy | STABLE | `/api/v1/settings` | `/settings` | `routes.py`, in-memory stub confirmed |
| F-011 Pakistan Statutory Compliance | STABLE | `/api/v1/compliance` (CONFIRMED from TBD) | `/compliance` (COLLAPSED from TBD) | Route 22 confirmed in `routes.py` |
| F-012 Reporting & Analytics | STABLE | `/api/v1/reporting` | `/dashboard` | `routes.py`, `reporting/` |
| F-013 Automation Engine | STABLE | `/api/v1/automations` | `/automations` (COLLAPSED from TBD) | Route 20 confirmed in `routes.py` |
| F-014 Decision Intelligence | STABLE | `/api/v1/decisions` (CONFIRMED from TBD) | `/decisions` | Route 23 confirmed in `routes.py` |
| F-015 Banking Integration | STABLE | `/api/v1/banking` (CONFIRMED from TBD) | No public screen (backend integration) | Route 24 confirmed in `routes.py` |
| F-016 WhatsApp Channel | STABLE | `/api/v1/whatsapp` (CONFIRMED from TBD) | No dedicated screen (messaging channel) | Route 25 confirmed in `routes.py` |

**Decision: All 16 core features are STABLE with confirmed gateway routes and resolved UI routes. No open product scope questions for core features.**

---

### 1.2 Add-On Features — All DEFERRED

| Feature | Status | Decision |
|---------|--------|---------|
| F-017 Performance Management | ADD-ON | Phase 3 builds core first. Performance screens (`/performance`, `/performance-reviews`) deferred to ADD-ON implementation phase. |
| F-018 Employee Engagement (Surveys) | ADD-ON | Phase 3 deferred. Gateway route `/api/v1/engagement` confirmed; frontend implementation deferred. |
| F-019 Helpdesk | ADD-ON | Phase 3 deferred. Gateway route `/api/v1/helpdesk` confirmed. |
| F-020 Cross-Domain Search | ADD-ON | Phase 3 deferred. Gateway route `/api/v1/search` confirmed. |
| F-021 Expense Management | ADD-ON | Phase 3 deferred. Gateway route `/api/v1/expense` confirmed. |
| F-022 Integration Hub | ADD-ON | Phase 3 deferred. Gateway route `/api/v1/integrations` confirmed. |

**Decision: ADD-ON features are not part of Phase 3 core scope. They may be included in later sprints but do not affect core navigation structure decisions.**

---

### 1.3 Planned Features — Out of Phase 3 Scope

| Feature | Status | Decision |
|---------|--------|---------|
| F-023 Travel Management | PLANNED (scaffolded only) | Not in Phase 3. No frontend work. |
| F-024 Project Management | PLANNED (scaffolded only) | Not in Phase 3. No frontend work. |

---

### 1.4 Out of Scope — Confirmed Not In Codebase

| Item | Decision |
|------|---------|
| Document Management | OUT OF SCOPE. `hrms-h02-documents-contract.json` is orphaned. No screen. |
| LMS (Learning Management) | OUT OF SCOPE |
| Shift/Roster Scheduling | OUT OF SCOPE. No shift-service in codebase. No screen. |
| Native Mobile App | FUTURE SCOPE. Web frontend is current delivery. Not Phase 3. |
| Time Tracking beyond attendance | OUT OF SCOPE |
| Video interview integration | OUT OF SCOPE |

---

## SECTION 2: NAVIGATION DECISIONS

### 2.1 Primary Navigation Structure — STABLE

Derived from FEATURE_SCOPE.md UI Routes + Phase 2.95 collapses:

| Navigation Item | Route | Visible To | Feature |
|----------------|-------|-----------|---------|
| Dashboard | `/dashboard` | All roles | F-012 |
| Employees | `/employees` | Admin, Manager, Recruiter | F-001 |
| Employee Profile | `/employee-profile` | All roles (own profile for Employee) | F-001 |
| Departments | `/departments` | Admin, Manager | F-001 |
| Organization | `/organization` | Admin, Manager | F-001 |
| Roles | `/roles` | Admin | F-001 |
| Attendance | `/attendance` | All roles | F-002 |
| Leave | `/leave` | All roles | F-003 |
| Leave Requests | `/leave-requests` | Manager, Admin | F-003 |
| Payroll | `/payroll` | PayrollAdmin, Admin, Manager | F-004 |
| Hiring | `/hiring` | Admin, Manager, Recruiter | F-005 |
| Job Postings | `/job-postings` | Admin, Manager, Recruiter | F-005 |
| Candidates Pipeline | `/candidates-pipeline` | Recruiter, Manager, Admin | F-005 |
| Approvals | `/approvals` | Manager, Admin | F-007 (COLLAPSED from TBD) |
| Notifications | `/notifications` | All roles | F-009 |
| Settings | `/settings` | Admin only | F-010 |
| Compliance | `/compliance` | Admin, PayrollAdmin | F-011 (COLLAPSED from TBD) |
| Decisions | `/decisions` | Admin, Manager | F-014 |
| Audit | `/audit` | Admin only | F-008 (COLLAPSED from TBD) |
| Automations | `/automations` | Admin | F-013 (COLLAPSED from TBD) |
| Login | `/login` | Public | F-006 |

**Decision: Navigation structure is STABLE. 21 routes defined. No open navigation decisions remain.**

---

## SECTION 3: PERMISSION MODEL DECISIONS — STABLE

### 3.1 Roles — STABLE (confirmed from code)

| Role | Description | Confirmed Source |
|------|-------------|-----------------|
| Admin | Full access; tenant administrator | `api_gateway_service.py` JWT claims |
| PayrollAdmin | Payroll data access; compliance | `_ROUTE_ROLE_MAP` confirmed |
| Manager | Team management; department-scoped | `_ROUTE_ROLE_MAP` confirmed |
| Recruiter | Hiring pipeline access | `_ROUTE_ROLE_MAP` confirmed |
| Employee | Self-service access only | JWT claims; scope enforcement |

**Decision: 5 roles. Role set is STABLE. No new roles needed for Phase 3.**

### 3.2 Gateway-Level RBAC — STABLE (confirmed from code)

| Route | Allowed Roles | Source |
|-------|--------------|--------|
| `/api/v1/payroll` | Admin, PayrollAdmin, Manager | `_ROUTE_ROLE_MAP` line 66–71 |
| `/api/v1/audit` | Admin | `_ROUTE_ROLE_MAP` |
| `/api/v1/hiring` | Admin, Manager, Recruiter | `_ROUTE_ROLE_MAP` |
| `/api/v1/reporting` | Admin, Manager | `_ROUTE_ROLE_MAP` |

All other routes: any authenticated role. **Decision: RBAC is STABLE.**

### 3.3 Scope Enforcement Model — STABLE

- Gateway validates role (who you are)
- Service validates scope (what data you can see)
- Manager scope: department-scoped for employees, leave, attendance
- Employee scope: own records only for profile, attendance, leave, payslip, notifications

**Decision: Scope model is STABLE. No product decisions pending.**

---

## SECTION 4: WORKFLOW MODEL DECISIONS — STABLE

| Workflow | Status | Decision |
|---------|--------|---------|
| WF-001 Employee Onboarding | STABLE | hire → employee create → user account → workflow → activate |
| WF-002 Leave Request & Approval | STABLE | submit → manager approve/reject → notify |
| WF-003 Payroll Run | STABLE | initiate → calculate → review → process → disbursement |
| WF-004 Hiring Pipeline | STABLE | post job → candidates → interview → hire decision → handoff |
| WF-005 Performance Review | DEFERRED | ADD-ON feature. Not Phase 3 core. |
| WF-006 Expense Claim | DEFERRED | ADD-ON feature. Not Phase 3 core. |
| WF-007 Audit & Compliance | STABLE | generate report → review → submit to FBR/EOBI/PESSI |
| WF-008 Employee Self-Service | STABLE | composite workflow; individual endpoints confirmed |

**Decision: WF-001 through WF-004, WF-007, WF-008 are STABLE. WF-005 and WF-006 are ADD-ON, deferred.**

---

## SECTION 5: DASHBOARD COMPOSITION — STABLE

### Primary Dashboard (`/dashboard`) — H01 Archetype

| Widget | Data Source | Roles |
|--------|------------|-------|
| Workforce overview (headcount, departments) | `GET /api/v1/reporting/dashboards/workforce` | All managers + Admin |
| Attendance summary (today/week) | `GET /api/v1/attendance` + reporting | Manager, Admin |
| Leave pending approvals | `GET /api/v1/leave?status=pending` | Manager, Admin |
| Payroll status (current period) | `GET /api/v1/payroll?period=current` | PayrollAdmin, Admin |
| Open job postings | `GET /api/v1/hiring?status=open` | Manager, Admin, Recruiter |
| Active decision cards | `GET /api/v1/decisions?status=active` | Manager, Admin |
| Notifications count | `GET /api/v1/notifications?unread=true` | All roles |

**Decision: Dashboard composition is STABLE for Phase 3. Widget list determined from feature set and reporting-analytics-service capabilities.**

---

## SECTION 6: API CONTRACT DECISIONS — STABLE

| Decision | Status | Detail |
|---------|--------|--------|
| Standard response envelope | STABLE | `{status, data, meta, error}` — 21 services |
| Non-standard envelope (4 services) | STABLE/KNOWN | compliance, decision, banking, whatsapp use `{status, data, service}` — no `meta` |
| API versioning prefix | STABLE | `/api/v1/` prefix on all routes |
| JWT authentication | STABLE | HS256, Bearer token, header-forwarded claims |
| Rate limiting | STABLE | 200 req/min per IP at gateway |
| Base URL (dev) | STABLE | `http://localhost:8000` |

**Decision: API contract is STABLE. Frontend must handle both envelope shapes (documented in conditions C-001 to C-004 of PRE_FRONTEND_GO_NO_GO_REPORT.md).**

---

## SECTION 7: OPEN ARCHITECTURAL QUESTIONS (OAQs) — FRONTEND IMPACT ASSESSMENT

From `AI_OPERATING_CONTEXT.md` OPEN_ARCHITECTURAL_QUESTIONS:

| OAQ | Question | Frontend Impact | Phase 3 Action |
|-----|----------|----------------|---------------|
| OAQ-001 | Kubernetes vs Docker Compose | None | Ignore for Phase 3 |
| OAQ-002 | Redis caching | None on UI behavior | Ignore for Phase 3 |
| OAQ-003 | Message queue (RabbitMQ/Kafka) | None | Ignore for Phase 3 |
| OAQ-004 | Mobile app scope | None on web frontend | Future scope; no Phase 3 impact |
| OAQ-005 | Multi-country expansion | Minor — country selector in UI if expanded | Future scope; no Phase 3 impact |
| OAQ-006 | SLA guarantees | None | Ignore for Phase 3 |
| OAQ-007 | APM / tracing | None | Ignore for Phase 3 |
| OAQ-008 | DB backup / DR | None | Ignore for Phase 3 |
| OAQ-009 | Feature flags / A/B testing | None — no feature flag system exists | Ignore for Phase 3 |
| OAQ-010 | API v2 timeline | None — v1 is current | Ignore for Phase 3 |

**Decision: ZERO open architectural questions impact Phase 3 frontend authority capture.**

---

## REGISTER SUMMARY

| Section | Decision Status |
|---------|----------------|
| Core feature scope (16 features) | STABLE — all routes confirmed |
| Add-on features (6 features) | DEFERRED — not Phase 3 scope |
| Planned features (2 features) | OUT OF PHASE SCOPE |
| Out-of-scope items | CONFIRMED OUT OF SCOPE |
| Navigation structure (21 routes) | STABLE |
| Permission model (5 roles, 4 RBAC restrictions) | STABLE |
| Workflow model (WF-001 to WF-004, WF-007/008) | STABLE |
| Dashboard composition | STABLE |
| API contract | STABLE |
| Open architectural questions | ZERO frontend impact |

**All product decisions required for Phase 3 frontend authority capture are STABLE or DEFERRED. No open product scope questions remain.**
