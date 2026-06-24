# FEATURE SCOPE

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-15
Owner: Shared

---

## PURPOSE

This document defines what is in scope, what is out of scope, and the status of every feature in the system. It is the authoritative reference for scope decisions.

**Primary Evidence Source:** `/backend/docs/canon/release-scope.md`, `docker-compose.yml`, service directories

**Cross-Reference:** `PROJECT_CHARTER.md` §5–§7 lists the same 24 capabilities using F-XXX identifiers (e.g., "F-001 Workforce Management") in place of its prior plain sequential numbering, to keep the two registers in sync. If either list is reordered or extended, update both documents together.

---

## STATUS LEGEND

| Status | Meaning |
|--------|---------|
| IMPLEMENTED | Code exists, tests exist, service deployed, feature accessible in UI |
| ADD-ON | Code exists but packaged as optional add-on; may require separate enablement |
| PLANNED | Service scaffolded but not functionally implemented |
| TBD | Status cannot be verified from current codebase inspection |

---

## FEATURE REGISTER

### CORE FEATURES (IMPLEMENTED)

#### F-001: Workforce Management
- **Service:** employee-service (port 8001)
- **Entities:** Employee, Department, Role, BusinessUnit, LegalEntity, Location, CostCenter, GradeBand, JobPosition
- **Key Operations:** Hire, transfer, terminate, update profile, org structure management
- **UI Routes:** `/employees`, `/employee-profile`, `/departments`, `/organization`, `/roles`
- **API Prefix:** `/api/v1/employees`, `/api/v1/departments`, `/api/v1/roles`, `/api/v1/org/*`
- **Status:** IMPLEMENTED

#### F-002: Attendance Management
- **Service:** attendance-service (port 8002)
- **Entities:** AttendanceRecord
- **Key Operations:** Clock-in/out, attendance validation, period closure, late arrival tracking
- **UI Routes:** `/attendance`
- **API Prefix:** `/api/v1/attendance`
- **Status:** IMPLEMENTED

#### F-003: Leave Management
- **Service:** leave-service (port 8003)
- **Entities:** LeaveRequest
- **Key Operations:** Submit leave, approve/reject, policy enforcement, balance tracking
- **UI Routes:** `/leave`, `/leave-requests`
- **API Prefix:** `/api/v1/leave`
- **Status:** IMPLEMENTED

#### F-004: Payroll Processing
- **Service:** payroll-service (port 8004)
- **Entities:** PayrollRecord
- **Key Operations:** Payroll run, gross/deductions/net calculation, disbursement initiation, period closure
- **UI Routes:** `/payroll`
- **API Prefix:** `/api/v1/payroll`
- **Country Layer:** Pakistan tax engine (`/backend/country/pakistan/tax_engine.py`)
- **Status:** IMPLEMENTED

#### F-005: Recruitment / Hiring
- **Service:** hiring-service (port 8005)
- **Entities:** JobPosting, Candidate, Interview
- **Key Operations:** Post job, manage candidate pipeline, schedule interviews, hire candidate
- **UI Routes:** `/hiring`, `/job-postings`, `/candidates-pipeline`
- **API Prefix:** `/api/v1/hiring`
- **Status:** IMPLEMENTED

#### F-006: Authentication & Authorization
- **Service:** auth-service (port 8006)
- **Entities:** UserAccount, Session, RefreshToken, RoleBinding, PermissionPolicy
- **Key Operations:** Login, token issuance, refresh, logout, role binding management
- **UI Routes:** `/login`
- **API Prefix:** `/api/v1/auth`
- **Status:** IMPLEMENTED

#### F-007: Workflow Engine
- **Service:** workflow-service (port 8009)
- **Entities:** WorkflowDefinition, WorkflowInstance, WorkflowStep, WorkflowHistory
- **Key Operations:** Workflow definition, instance creation, step progression, approval routing
- **UI Routes:** `/approvals` (H05 Approval Inbox archetype) — confirmed Phase 2.95 + Phase 3
- **API Prefix:** `/api/v1/workflows`
- **Status:** IMPLEMENTED

#### F-008: Audit Logging
- **Service:** audit-service (port 8008)
- **Entities:** AuditRecord
- **Key Operations:** Capture all mutations, immutable log, compliance queries
- **UI Routes:** `/audit` (H02 Audit Log — Admin-only) — confirmed Phase 2.95 + Phase 3
- **API Prefix:** `/api/v1/audit`
- **Status:** IMPLEMENTED

#### F-009: Notification System
- **Service:** notification-service (port 8007)
- **Entities:** NotificationTemplate, NotificationMessage, DeliveryAttempt, NotificationPreference
- **Key Operations:** Template management, message queueing, multi-channel delivery, preference management
- **UI Routes:** `/notifications`
- **API Prefix:** `/api/v1/notifications`
- **Status:** IMPLEMENTED

#### F-010: Settings & HR Policy Configuration
- **Service:** settings-service (port 8020)
- **Entities:** AttendanceRule, LeavePolicy, PayrollSettings
- **Key Operations:** Configure HR policies, attendance rules, payroll defaults
- **UI Routes:** `/settings`
- **API Prefix:** `/api/v1/settings`
- **Status:** IMPLEMENTED

#### F-011: Pakistan Statutory Compliance
- **Service:** compliance-service (port 8021)
- **Entities:** Compliance submissions (FBR, EOBI, PESSI)
- **Key Operations:** Generate compliance reports, submit to regulatory bodies, track filing status
- **Integrations:** `fbr_adapter.py`, `eobi_adapter.py`
- **UI Routes:** `/compliance` (H07 Compliance Reports — Admin + PayrollAdmin) — confirmed Phase 2.95 + Phase 3
- **API Prefix:** `/api/v1/compliance` — CONFIRMED gateway route 22 (`routes.py` line 52, `gateway-routes.json` line 25 — Phase 2.8 TR-003)
- **Status:** IMPLEMENTED

#### F-012: Reporting & Analytics
- **Service:** reporting-analytics-service (port 8013)
- **Entities:** Reports, Dashboards, Analytics projections
- **Key Operations:** Generate reports, view dashboards, predictive analytics
- **UI Routes:** `/dashboard`
- **API Prefix:** `/api/v1/reporting`
- **Status:** IMPLEMENTED

#### F-013: Automation Engine
- **Service:** automation-service (port 8017)
- **Key Operations:** Event-triggered rules (event-type matching against canonical event types via `automation_contract.py`; scheduled and threshold triggers are NOT implemented — see BACKEND_GAP_REGISTER EG-003)
- **UI Routes:** `/automations` (H11 Automation Rules — Admin-only) + `/builders/workflow` (H11 Workflow Builder) — confirmed Phase 2.95 + Phase 3
- **API Prefix:** `/api/v1/automations`
- **Status:** IMPLEMENTED

#### F-014: Decision Intelligence
- **Service:** decision-service (port 8022)
- **Key Operations:** Anomaly detection, Decision Card creation, risk scoring, remediation suggestions
- **UI Routes:** `/decisions` (custom detail archetype — Admin + Manager + PayrollAdmin scoped) — confirmed Phase 3
- **API Prefix:** `/api/v1/decisions` — CONFIRMED gateway route 23 (`routes.py` line 53, `gateway-routes.json` line 26 — Phase 2.8 TR-004). Non-standard envelope: `{status, data, service}`. DecisionCard is in-memory only (not persisted).
- **Evidence:** `backend/decision_api.py`, `backend/services/decision_engine.py`, `backend/docs/canon/decision-system.md`
- **Status:** IMPLEMENTED

#### F-015: Banking Integration
- **Service:** bank-service (port 8023)
- **Key Operations:** Salary disbursement, Raast instant payments, bank reconciliation
- **Integrations:** `backend/integrations/pakistan/raast_payment.py`, `bank_salary.py`, `payment_reconciliation.py`
- **API Prefix:** `/api/v1/banking` — CONFIRMED gateway route 24 (`routes.py` line 54, `gateway-routes.json` line 27 — Phase 2.8 TR-005). Non-standard envelope: `{status, data, service}`. No standalone frontend screen — surfaces through payroll detail only.
- **Status:** IMPLEMENTED

#### F-016: WhatsApp Channel
- **Service:** whatsapp-service (port 8024)
- **Key Operations:** WhatsApp as HR access channel, identity mapping, message routing
- **API Prefix:** `/api/v1/whatsapp` — CONFIRMED gateway route 25 (`routes.py` line 55, `gateway-routes.json` line 28 — Phase 2.8 TR-006). Non-standard envelope: `{status, data, service}`. No standalone frontend screen — configuration surfaces in Settings → Integrations (chrome-only Phase 3).
- **Status:** IMPLEMENTED

---

### ADD-ON FEATURES

#### F-017: Performance Management
- **Service:** performance-service (port 8010)
- **Entities:** ReviewCycle, Goal, Feedback, CalibrationSession, PipPlan
- **UI Routes:** `/performance`, `/performance-reviews`
- **API Prefix:** `/api/v1/performance`
- **Status:** ADD-ON

#### F-018: Employee Engagement
- **Service:** engagement-service (port 8011)
- **Entities:** Survey, SurveyQuestion, SurveyResponse, SurveyAnswer, SurveyAggregate
- **API Prefix:** `/api/v1/engagement` — CONFIRMED (present in gateway ROUTES table, `/backend/api-gateway/routes.py` and `/backend/deployment/config/gateway-routes.json`)
- **Status:** ADD-ON

#### F-019: Helpdesk
- **Service:** helpdesk-service (port 8012)
- **API Prefix:** `/api/v1/helpdesk`
- **Status:** ADD-ON

#### F-020: Cross-Domain Search
- **Service:** search-service (port 8014)
- **API Prefix:** `/api/v1/search`
- **Status:** ADD-ON

#### F-021: Expense Management
- **Service:** expense-service (port 8015)
- **API Prefix:** `/api/v1/expense`
- **Status:** ADD-ON

#### F-022: Integration Hub
- **Service:** integration-service (port 8016)
- **Key Operations:** Outbound webhooks, connector dispatch, delivery replay
- **API Prefix:** `/api/v1/integrations`
- **Status:** ADD-ON

---

### PLANNED FEATURES (NOT IMPLEMENTED)

#### F-023: Travel Management
- **Service:** travel-service (port 8018)
- **Entities:** Defined in `013_travel_domain.sql`
- **API Prefix:** `/api/v1/travel`
- **Status:** PLANNED

#### F-024: Project Management
- **Service:** project-service (port 8019)
- **API Prefix:** `/api/v1/projects`
- **Status:** PLANNED

---

## OUT OF SCOPE (CONFIRMED NOT IN CODEBASE)

- Document Management — no service, no gateway route, no DB table; `contracts/hrms-h02-documents-contract.json` is an orphaned frontend contract artifact (AG-006)
- Learning Management System (LMS)
- Time Tracking beyond basic attendance
- Shift/Roster scheduling — CONFIRMED OUT OF SCOPE: no backend service, no docker-compose entry, no DB schema, no gateway route. `h06-shift-roster.html` wireframe is orphaned (Phase 3 G-001). Do not implement.
- Native mobile app — CONFIRMED OUT OF SCOPE: no mobile service in docker-compose.yml, no mobile API surface defined, no gateway mobile prefix. Any `mobile/` directory is frontend scaffolding only with no production backing.
- Video interview integration
- Third-party ATS integration — CONFIRMED OUT OF SCOPE for inbound connectors: hiring-service manages candidates natively. Integration-service (F-022, ADD-ON) provides outbound webhooks only. No inbound ATS connector is implemented or scaffolded.
- Payroll for countries other than Pakistan (base layer exists but no other country implementation)

---

## SCOPE CHANGE PROTOCOL

Any change to this document requires:
1. Human Owner approval
2. Impact assessment on `FULLSTACK_STITCHING_CONTRACT.md`
3. Update to `DOMAIN_MODEL.md` if new entities are introduced
4. New ADR entry in `docs/06_decisions/`
