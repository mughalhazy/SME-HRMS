# SERVICE CATALOG

Status: Draft
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

Catalog of all 24 domain microservices plus the API Gateway, as deployed in `D:\SaaS\HRMS\backend\docker-compose.yml`. For each service: name, port, purpose, primary source location(s), owned entities (per `docs/00_authority/DOMAIN_MODEL.md` and `backend/docs/canon/service-map.md`), key dependencies, and API Gateway route status (CONFIRMED / TBD).

**Gateway route status legend:**
- **CONFIRMED** — path prefix appears in both `/backend/api-gateway/routes.py` (25 entries, lines 31-55) and `/backend/deployment/config/gateway-routes.json`.

**Note:** As of 2026-06-16 delta audit, all 24 domain services have CONFIRMED gateway routes. The prior "TBD – REQUIRES VERIFICATION" annotation for compliance, decisions, banking, and whatsapp has been resolved — all 4 are present in both `routes.py` (lines 52-55) and `gateway-routes.json` (lines 25-28). See `docs/08_reports/DOC_TO_CODE_DELTA_MATRIX.md` DELTA-001, DELTA-002.

**Evidence sources:** `D:\SaaS\HRMS\backend\docker-compose.yml`, `D:\SaaS\HRMS\backend\api-gateway\routes.py`, `D:\SaaS\HRMS\backend\deployment\config\gateway-routes.json`, `D:\SaaS\HRMS\backend\docs\canon\service-map.md`, `D:\SaaS\HRMS\backend\docs\services\*.md`, `docs\00_authority\DOMAIN_MODEL.md`, `docs\00_authority\FEATURE_SCOPE.md`.

---

## 1. employee-service (port 8001)

- **Purpose:** Workforce master data, employment lifecycle, organizational reference data (departments, business units, legal entities, locations, cost centers, grade/bands, job positions, roles).
- **Primary source:** `backend/employee_service.py` (Python `EmployeeService` class — PersistentKVStore, OutboxManager, full CRUD for employees/departments/roles, event publishing); `backend/employee_api.py` (14 API handlers, `with_error_handling` decorator); `backend/employee_ui.py`; `backend/api/employee_portal.py`. The TypeScript files in `backend/services/employee-service/` are dead code — they predate the Python implementation and are no longer referenced by `service_runtime.py`. Canon doc: `backend/docs/services/employee-service.md`. **Updated 2026-06-16: Python implementation (EG-001 resolution). See DELTA-003.**
- **Owned entities:** `Employee`, `Department`, `BusinessUnit`, `LegalEntity`, `Location`, `CostCenter`, `GradeBand`, `JobPosition`, `Role` (per `backend/docs/canon/service-map.md` and `docs/00_authority/DOMAIN_MODEL.md`).
- **Key dependencies:** `auth-service` (auth), `notification-service` (onboarding/status notifications), upstream consumer of `CandidateHired` from `hiring-service`.
- **docker-compose env wiring:** `AUTH_SERVICE_URL` (lines 47-58).
- **Gateway route status:** CONFIRMED — `/api/v1/employees`, `/api/v1/departments` (`routes.py` lines 31-32).

---

## 2. attendance-service (port 8002)

- **Purpose:** Attendance capture, validation against policy, approval/lock for payroll-safe period closure.
- **Primary source:** `backend/attendance_service/service.py`; `backend/services/attendance_service.py`; `backend/services/attendance/` (helper modules). Canon doc: `backend/docs/services/attendance-service.md`.
- **Owned entities:** `AttendanceRecord`.
- **Key dependencies:** `employee-service` (employment validation), `auth-service`, `notification-service` (anomaly/closure alerts).
- **docker-compose env wiring:** `EMPLOYEE_SERVICE_URL`, `AUTH_SERVICE_URL` (lines 60-72).
- **Gateway route status:** CONFIRMED — `/api/v1/attendance` (`routes.py` line 34).

---

## 3. leave-service (port 8003)

- **Purpose:** Leave request drafting, submission, approval, rejection, cancellation; approver decision tracking.
- **Primary source:** `backend/leave_service.py`, `backend/leave_api.py`. Canon doc: `backend/docs/services/leave-service.md`.
- **Owned entities:** `LeaveRequest`.
- **Key dependencies:** `employee-service`, `auth-service`, `notification-service`, downstream `payroll-service` (approved leave impact).
- **docker-compose env wiring:** `EMPLOYEE_SERVICE_URL`, `AUTH_SERVICE_URL`, `PAYROLL_SERVICE_URL` (lines 74-87).
- **Gateway route status:** CONFIRMED — `/api/v1/leave` (`routes.py` line 35).

---

## 4. payroll-service (port 8004)

- **Purpose:** Draft, process, pay, and cancel payroll records by pay period; combines compensation, attendance, and leave impacts.
- **Primary source:** `backend/payroll_service.py`, `backend/payroll_api.py`, `backend/payroll_ui.py`; `backend/services/payroll_service.py`; `backend/services/payroll/` (helper modules incl. `backend/services/payroll_policy_engine.py`); `backend/test_payroll_service.py`. Canon doc: `backend/docs/services/payroll-service.md`.
- **Owned entities:** `PayrollRecord`.
- **Key dependencies:** `employee-service` (roster/compensation), `attendance-service` (approved/locked attendance), `leave-service` (approved leave), `auth-service`.
- **docker-compose env wiring:** `EMPLOYEE_SERVICE_URL`, `ATTENDANCE_SERVICE_URL`, `LEAVE_SERVICE_URL`, `AUTH_SERVICE_URL` (lines 89-103).
- **Country-layer integration:** consumes `TaxEngineInterface`, `PayrollRulesInterface`, `StatutoryValidatorInterface` via `CountryResolver` (`backend/core/country_resolver.py`, `backend/docs/canon/country-layer.md`).
- **Gateway route status:** CONFIRMED — `/api/v1/payroll` (`routes.py` line 38).

---

## 5. hiring-service (port 8005)

- **Purpose:** Job posting lifecycle, candidate applications, stage transitions, interview scheduling, hire handoff to onboarding.
- **Primary source:** `backend/services/hiring_service/`. Canon doc: `backend/docs/services/hiring-service.md`.
- **Owned entities:** `JobPosting`, `Candidate`, `Interview`.
- **Key dependencies:** `employee-service` (department/role/interviewer validation), `auth-service`, `notification-service`; external: Google Calendar (interview sync), LinkedIn (candidate import) per canon.
- **docker-compose env wiring:** `EMPLOYEE_SERVICE_URL`, `AUTH_SERVICE_URL` (lines 105-117).
- **Gateway route status:** CONFIRMED — `/api/v1/hiring` (`routes.py` line 39).

---

## 6. auth-service (port 8006)

- **Purpose:** Identity, sessions, tokens, role bindings, policy evaluation for human and service principals.
- **Primary source:** `backend/services/auth-service/`. Canon doc: `backend/docs/services/auth-service.md`. Loaded dynamically by `service_runtime.py` via `_auth_module()` (`backend/docker/service_runtime.py` lines 75-85) — other services import auth-service modules at runtime from `backend/services/auth-service/`.
- **Owned entities:** `UserAccount`, `RoleBinding`, `PermissionPolicy`, `Session`, `RefreshToken`.
- **Key dependencies:** `employee-service` (identity linkage), `notification-service` (password reset/security alerts).
- **docker-compose env wiring:** `JWT_ISSUER`, `JWT_AUDIENCE` (no upstream `_SERVICE_URL` vars) (lines 119-131).
- **Gateway route status:** CONFIRMED — `/api/v1/auth` (`routes.py` line 40); also exempted from gateway JWT enforcement for its own prefix (`api_gateway_service.py` line 55: `_AUTH_EXEMPT_PREFIXES` includes `/api/v1/auth/`).

---

## 7. notification-service (port 8007)

- **Purpose:** Queue, render, send, track notifications; subject preferences and channel routing.
- **Primary source:** `backend/notification_service.py`, `backend/notification_api.py`. Canon doc: `backend/docs/services/notification-service.md`.
- **Owned entities:** `NotificationTemplate`, `NotificationMessage`, `DeliveryAttempt`, `NotificationPreference`.
- **Key dependencies:** `auth-service` (operator/service-principal authz); external SMTP/SMS/push providers per canon.
- **docker-compose env wiring:** `AUTH_SERVICE_URL` (lines 133-144).
- **Gateway route status:** CONFIRMED — `/api/v1/notifications` (`routes.py` line 43).

---

## 8. audit-service (port 8008)

- **Purpose:** Immutable audit record store; emits/records audit entries for mutation events across services.
- **Primary source:** `backend/audit_service/` (`__init__.py`, `api.py`, `service.py`) — `emit_audit_record` from `audit_service.service` is imported by `backend/resilience.py` (line 14) and by `backend/integrations/pakistan/submission_tracking.py` (line 10), confirming cross-module use. Canon doc: `backend/docs/services/audit-service.md`.
- **Owned entities:** TBD – REQUIRES VERIFICATION (not explicitly enumerated as a top-level entry in `service-map.md`'s per-service sections read; likely `AuditRecord`/`AuditLogEntry` per `backend/docs/services/audit-service.md` — not opened in this pass).
- **Key dependencies:** Consumed by nearly all domain services for mutation audit logging (per `service-map.md` "Dependencies" sections across multiple services, e.g., compliance-service, decision-service, performance-service, travel-service, helpdesk-service, automation-service).
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 146-156).
- **Gateway route status:** CONFIRMED — `/api/v1/audit` (`routes.py` line 42).

---

## 9. workflow-service (port 8009)

- **Purpose:** Centralized workflow/approval engine used by multiple domain services (performance, travel, project, expense approvals, etc.).
- **Primary source:** `backend/workflow_service.py`, `backend/workflow_api.py`, `backend/workflow_contract.py`, `backend/workflow_support.py`. Canon docs: `backend/docs/services/workflow-service.md`, `backend/docs/canon/workflow-catalog.md`, `backend/docs/design/workflow-integrity-report-p31.md`.
- **Owned entities:** TBD – REQUIRES VERIFICATION (workflow definitions/instances — not enumerated from `service-map.md` top-level sections read in this pass).
- **Key dependencies:** Consumed by performance-service, travel-service, project-service (per `service-map.md` "Dependencies" sections: "`workflow-service` for ... approvals").
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 158-168).
- **Gateway route status:** CONFIRMED — `/api/v1/workflows` (`routes.py` line 41).

---

## 10. performance-service (port 8010)

- **Purpose:** Performance review cycles, goals/OKRs, continuous feedback, calibration, PIP tracking.
- **Primary source:** `backend/performance_service.py`, `backend/performance_api.py`; `backend/services/performance/`. Canon doc: `backend/docs/services/performance-service.md`.
- **Owned entities:** `ReviewCycle`, `Goal`, `Feedback`, `CalibrationSession`, `PipPlan`. **Note:** per `docs/08_reports/GOVERNANCE_CONSISTENCY_AUDIT.md` H-002, these entities are referenced in `FEATURE_SCOPE.md`/`PRODUCT_WORKFLOWS.md`/`service-map.md` but have **no entry** in `docs/00_authority/DOMAIN_MODEL.md` — flagged as a documentation gap, not a code gap.
- **Key dependencies:** `employee-service`, `auth-service`, `workflow-service` (cycle/goal/calibration/PIP approvals), `audit-service`, `notification-service`.
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 170-180).
- **Gateway route status:** CONFIRMED — `/api/v1/performance` (`routes.py` line 33). Status: ADD-ON per `service-map.md`.

---

## 11. engagement-service (port 8011)

- **Purpose:** Employee engagement surveys/pulse campaigns, response capture, aggregated sentiment results.
- **Primary source:** `backend/engagement_service.py`, `backend/engagement_api.py`. Canon doc: `backend/docs/services/engagement-service.md`.
- **Owned entities:** `Survey`, `SurveyQuestion`, `SurveyResponse`, `AggregatedSurveyResult`. Per `docs/08_reports/GOVERNANCE_CONSISTENCY_AUDIT.md` H-002, these are not in `docs/00_authority/DOMAIN_MODEL.md`.
- **Key dependencies:** `employee-service` (target population/department context), `notification-service` (pulse reminders).
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 182-192).
- **Gateway route status:** CONFIRMED — `/api/v1/engagement` (`routes.py` line 44). **Note:** `docs/08_reports/GOVERNANCE_CONSISTENCY_AUDIT.md` H-001 records a prior cross-document contradiction (ADR-001 vs. FEATURE_SCOPE vs. FULLSTACK_STITCHING_CONTRACT) about whether this route was confirmed; this Phase 2 pass independently re-verified `routes.py` line 44 and `gateway-routes.json` line 17 both list `"engagement"` — the route IS present in both route tables as of this review. Status: ADD-ON per `service-map.md`.

---

## 12. helpdesk-service (port 8012)

- **Purpose:** Employee-initiated HR support tickets — creation, routing, SLA tracking, knowledge base.
- **Primary source:** `backend/helpdesk_service.py`, `backend/helpdesk_api.py`. Canon doc: `backend/docs/services/helpdesk-service.md`.
- **Owned entities:** `HelpDeskTicket`, `TicketComment`, `TicketCategory`, `KnowledgeBaseArticle`.
- **Key dependencies:** `employee-service`, `auth-service`, `notification-service`, `audit-service`.
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 194-204).
- **Gateway route status:** CONFIRMED — `/api/v1/helpdesk` (`routes.py` line 45). Status: ADD-ON per `service-map.md`.

---

## 13. reporting-analytics-service (port 8013)

- **Purpose:** Aggregates data from read models across all domain services; operational, compliance, predictive, anomaly reports; forecasting.
- **Primary source:** `backend/reporting_analytics.py`, `backend/reporting_analytics_api.py`; `backend/services/analytics/`. Canon doc: `backend/docs/services/reporting-analytics-service.md`.
- **Owned entities:** `ReportDefinition`, `ReportExecution`, `AnalyticsProjection`.
- **Key dependencies:** All domain read models (read-only), `decision-service` (anomaly signal consumer), `audit-service`.
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 206-216).
- **Gateway route status:** CONFIRMED — `/api/v1/reporting` (`routes.py` line 46). Also subject to gateway RBAC: `/api/v1/reporting` restricted to `Admin, Manager` (`api_gateway_service.py` line 70).

---

## 14. search-service (port 8014)

- **Purpose:** Cross-domain projection-backed search and indexing without reading transactional domain stores directly.
- **Primary source:** `backend/search_service.py`, `backend/search_api.py`. Canon doc: `backend/docs/services/search-service.md`.
- **Owned entities:** `SearchDocument`, `SearchProjectionState`, `SearchEventCheckpoint`.
- **Key dependencies:** `employee-service` and `hiring-service` read models, `payroll-service` summary projections, `background-jobs` (async indexing), event-outbox pipeline.
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 218-228).
- **Gateway route status:** CONFIRMED — `/api/v1/search` (`routes.py` line 47). Status: ADD-ON per `service-map.md`.

---

## 15. expense-service (port 8015)

- **Purpose:** Employee expense claims — draft through approval to reimbursement; receipt attachments, category policy validation; accounting export.
- **Primary source:** `backend/expense_service.py`, `backend/expense_api.py`. Canon doc: `backend/docs/services/expense-service.md`.
- **Owned entities:** `ExpenseClaim`, `ExpenseReceipt`, `ExpenseCategory`.
- **Key dependencies:** `employee-service`, `auth-service`, `notification-service`, `audit-service`. Accounting export targets `backend/integrations/accounting/` (QuickBooks/SAP adapters) — see `INTEGRATION_CATALOG.md`.
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 230-240).
- **Gateway route status:** CONFIRMED — `/api/v1/expense` (`routes.py` line 48). Status: ADD-ON per `service-map.md`.

---

## 16. integration-service (port 8016)

- **Purpose:** Centralizes outbound webhook registration/delivery for tenant-scoped external integrations; consumes canonical events and fans out to subscribed endpoints; signs payloads, tracks delivery attempts, replay/failure visibility.
- **Primary source:** `backend/integration_service.py`, `backend/integration_api.py`. Canon doc: `backend/docs/services/integration-service.md`. (Distinct from `/backend/integrations/` directory, which holds country-specific third-party adapters — see `INTEGRATION_CATALOG.md`.)
- **Owned entities:** `WebhookEndpoint`, `WebhookDelivery`, `WebhookDeliveryAttempt`.
- **Key dependencies:** `auth-service` (registration/replay authz), `audit-service`, event/outbox pipeline, background-jobs.
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 242-252).
- **Gateway route status:** CONFIRMED — `/api/v1/integrations` (`routes.py` line 49). Status: ADD-ON per `service-map.md`.

---

## 17. automation-service (port 8017)

- **Purpose:** Executes automation rules (event-triggered, schedule-triggered, threshold-triggered); dispatches actions to domain services via canonical APIs; manages rule lifecycle/execution history.
- **Primary source:** `backend/automation_service.py`, `backend/automation_api.py`, `backend/automation_contract.py`. Canon doc: `backend/docs/services/automation-service.md`.
- **Owned entities:** `AutomationRule`, `AutomationExecution`, `AutomationExecutionLog`.
- **Key dependencies:** All domain services (action targets), `auth-service` (admin-only rule management), `notification-service`, `audit-service`, background jobs.
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 254-264).
- **Gateway route status:** CONFIRMED — `/api/v1/automations` (`routes.py` line 50).

---

## 18. travel-service (port 8018)

- **Purpose:** Employee travel requests — draft through approval, booking, cancellation, completion; itinerary segments and booking details.
- **Primary source:** `backend/travel_service.py`, `backend/travel_api.py`. Canon doc: `backend/docs/services/travel-service.md`.
- **Owned entities:** `TravelRequest`, `TravelItinerarySegment`.
- **Key dependencies:** `employee-service`, `auth-service`, `workflow-service` (approvals), `audit-service`, `notification-service`.
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 266-276).
- **Gateway route status:** CONFIRMED — `/api/v1/travel` (`routes.py` line 36). Per ADR-001 §2, route is CONFIRMED but service implementation status is noted as PLANNED in `FEATURE_SCOPE.md` F-023 — i.e., the route exists, but functional completeness is TBD – REQUIRES VERIFICATION.

---

## 19. project-service (port 8019)

- **Purpose:** Project master data, staffing assignments, allocation changes; reuses employee-service read models for employee/manager/department references.
- **Primary source:** `backend/project_service.py`, `backend/project_api.py`. Canon doc: `backend/docs/services/project-service.md`.
- **Owned entities:** `Project`, `ProjectAssignment`, `AllocationLedgerEntry`.
- **Key dependencies:** `employee-service`, `workflow-service` (optional approvals), `audit-service`, `notification-service`.
- **docker-compose env wiring:** none beyond `DATABASE_URL` (lines 278-288).
- **Gateway route status:** CONFIRMED — `/api/v1/projects` (`routes.py` line 37). Per ADR-001 §2, route is CONFIRMED but service implementation status is noted as PLANNED in `FEATURE_SCOPE.md` F-024 — functional completeness is TBD – REQUIRES VERIFICATION.

---

## 20. settings-service (port 8020)

- **Purpose:** Administrative HR policy configuration — attendance rule templates, leave policy definitions/accrual defaults, payroll schedule/cutoff/deduction/approval settings; consolidated admin read model.
- **Primary source:** Inline in-memory Python dict stub in `backend/docker/service_runtime.py` lines 324–342. No external Python module is imported; no TypeScript files are used at runtime. The `settings_state` dict (keys: `tenant_id`, `attendance_policy`, `leave_policy`, `payroll`) is initialised inline and served by two handler functions (`_handle_settings_get`, `_handle_settings_update`) registered directly in the runtime block. Canon doc: `backend/docs/services/settings-service.md` (documents the TypeScript model design; the in-memory stub is the current runtime implementation).
- **Owned entities:** `AttendanceRule`, `LeavePolicy`, `PayrollSettings`.
- **Key dependencies:** `auth-service`; downstream consumers: `attendance-service`, `leave-service`, `payroll-service` (per canon — config defaults, not direct calls from settings-service).
- **docker-compose env wiring:** `DEFAULT_TENANT_ID` (default `tenant-default`) (lines 290-301).
- **Gateway route status:** CONFIRMED — `/api/v1/settings` (`routes.py` line 51). Status: ADD-ON per `service-map.md`.

---

## 21. compliance-service (port 8021)

- **Purpose:** Statutory compliance lifecycle for configured country jurisdictions — pre-payroll validation gate, statutory report generation (FBR Annexure-C, EOBI PR-01, PESSI/SESSI returns), submission tracking (`DRAFT → VALIDATED → SUBMITTED → ACK → FAILED → RETRY`), immutable compliance audit trail.
- **Primary source:** `backend/compliance_api.py`; `backend/services/compliance_service.py`; `backend/services/compliance_autopilot.py`. Canon doc: `backend/docs/services/compliance-service.md`.
- **Owned entities:** `ComplianceSubmission`, `ComplianceReport`, `ComplianceAuditRecord`.
- **Key dependencies:** `payroll-service` (validation input), `employee-service` (roster, CNIC/NTN), government adapter layer (`backend/integrations/pakistan/` — FBR/EOBI/PESSI), `audit-service`, `notification-service`.
- **docker-compose env wiring:** `AUTH_SERVICE_URL`, `PAYROLL_SERVICE_URL` (lines 303-315).
- **Gateway route status:** CONFIRMED — `/api/v1/compliance` (`routes.py` line 52; `gateway-routes.json` line 25; `service_runtime.py` lines 365–383: 9 routes registered). Per ADR-001 §2 and `docs/00_authority/FEATURE_SCOPE.md` F-014.

---

## 22. decision-service (port 8022)

- **Purpose:** Cross-domain intelligence layer — payroll/attendance/compliance/performance anomaly detection, risk/confidence scoring, Decision Cards with recommended actions, human-in-the-loop gates for high-risk decisions, immutable audit trail of card transitions.
- **Primary source:** `backend/decision_api.py`; `backend/services/decision_engine.py`. Canon doc: `backend/docs/services/decision-service.md`.
- **Owned entities:** `DecisionCard`, `AnomalyRecord`, `DecisionAuditEntry`.
- **Key dependencies:** `payroll-service`, `attendance-service`, `compliance-service`, `employee-service`, `audit-service`, `notification-service`.
- **docker-compose env wiring:** `AUTH_SERVICE_URL` (lines 317-328).
- **Gateway route status:** CONFIRMED — `/api/v1/decisions` (`routes.py` line 53; `gateway-routes.json` line 26; `service_runtime.py` lines 421–436: 9 routes registered). Per ADR-001 §2.

---

## 23. bank-service (port 8023)

- **Purpose:** Bank-specific salary disbursement file generation, Raast instant payment payouts (salary and EWA disbursements), per-employee per-period payment status tracking, reconciliation engine against payroll/disbursement records.
- **Primary source:** `backend/bank_service.py`; `backend/banking_api.py`. Canon doc: `backend/docs/services/bank-service.md`.
- **Owned entities:** `DisbursementBatch`, `PaymentRecord`, `ReconciliationReport`, `EmployeeBankAccount`.
- **Key dependencies:** `payroll-service` (finalized payroll records), `ewa-financial-service` (EWA/advance disbursement requests — see `BACKEND_ARCHITECTURE_REPORT.md` for the discrepancy that `ewa-financial-service` is not a docker-compose service), `employee-service`, `audit-service`, `notification-service`; Raast API and per-bank adapters via `backend/integrations/pakistan/` and `backend/country/pakistan/banking.py`.
- **docker-compose env wiring:** `AUTH_SERVICE_URL`, `PAYROLL_SERVICE_URL` (lines 330-342).
- **Gateway route status:** CONFIRMED — `/api/v1/banking` (`routes.py` line 54; `gateway-routes.json` line 27; `service_runtime.py` lines 384–404: 11 routes registered). Per ADR-001 §2 and `docs/00_authority/FEATURE_SCOPE.md` F-015.

---

## 24. whatsapp-service (port 8024)

- **Purpose:** WhatsApp access channel — inbound message intent parsing, session management, phone↔employee identity mapping with OTP verification, RBAC via session-bound role context, domain action dispatch, conversation logging.
- **Primary source:** `backend/whatsapp_service.py`, `backend/whatsapp_api.py`; `backend/integrations/whatsapp/webhook.py` (`CommandRegistry`, intent mappings for `payslip`, `leave`, `approval`, `attendance`). Canon doc: `backend/docs/services/whatsapp-service.md`.
- **Owned entities:** `WhatsAppIdentityMap`, `WhatsAppSession`, `WhatsAppConversationEvent`.
- **Key dependencies:** `employee-service` (identity/role resolution), `auth-service` (OTP/session authz), `payroll-service` (payslip data), `leave-service` (balance/leave application), `notification-service`; external WhatsApp Business API provider.
- **docker-compose env wiring:** `AUTH_SERVICE_URL` (lines 344-355).
- **Gateway route status:** CONFIRMED — `/api/v1/whatsapp` (`routes.py` line 55; `gateway-routes.json` line 28; `service_runtime.py` lines 405–420: 8 routes registered). Per ADR-001 §2 and `docs/00_authority/FEATURE_SCOPE.md` F-016.

---

## 25. api-gateway (port 8000)

- **Purpose:** Single entry point for all client traffic; JWT validation, rate limiting (200 req/min/IP default), route resolution to the 25 confirmed routes, CORS, route-level RBAC, idempotency caching, in-process metrics, circuit breaker/retry for upstream calls.
- **Primary source:** `backend/docker/api_gateway_service.py`; `backend/api-gateway/routes.py`, `backend/api-gateway/tenant.py`, `backend/api-gateway/load_control.py`, `backend/api-gateway/dashboard_ui.py`.
- **Owned entities:** None (stateless proxy; in-process idempotency cache and metrics accumulator only).
- **Key dependencies:** All 24 domain services (full `<SERVICE>_URL` map injected, docker-compose.yml lines 366-389); `depends_on: service_healthy` for all 24 (lines 390-438).
- **docker-compose env wiring:** Full map of all 24 `<SERVICE>_SERVICE_URL` variables.
- **Gateway route status:** N/A (this IS the gateway). Exposed on host port 8000 (line 363).

---

## SUMMARY TABLE

| # | Service | Port | Status (per service-map.md) | Gateway Route |
|---|---|---|---|---|
| 1 | employee-service | 8001 | IMPLEMENTED | CONFIRMED |
| 2 | attendance-service | 8002 | IMPLEMENTED | CONFIRMED |
| 3 | leave-service | 8003 | IMPLEMENTED | CONFIRMED |
| 4 | payroll-service | 8004 | IMPLEMENTED | CONFIRMED |
| 5 | hiring-service | 8005 | IMPLEMENTED | CONFIRMED |
| 6 | auth-service | 8006 | IMPLEMENTED | CONFIRMED |
| 7 | notification-service | 8007 | IMPLEMENTED | CONFIRMED |
| 8 | audit-service | 8008 | IMPLEMENTED (implied) | CONFIRMED |
| 9 | workflow-service | 8009 | IMPLEMENTED (implied) | CONFIRMED |
| 10 | performance-service | 8010 | ADD-ON | CONFIRMED |
| 11 | engagement-service | 8011 | ADD-ON | CONFIRMED |
| 12 | helpdesk-service | 8012 | ADD-ON | CONFIRMED |
| 13 | reporting-analytics-service | 8013 | IMPLEMENTED | CONFIRMED |
| 14 | search-service | 8014 | ADD-ON | CONFIRMED |
| 15 | expense-service | 8015 | ADD-ON | CONFIRMED |
| 16 | integration-service | 8016 | ADD-ON | CONFIRMED |
| 17 | automation-service | 8017 | IMPLEMENTED | CONFIRMED |
| 18 | travel-service | 8018 | PLANNED (route confirmed, impl TBD) | CONFIRMED |
| 19 | project-service | 8019 | PLANNED (route confirmed, impl TBD) | CONFIRMED |
| 20 | settings-service | 8020 | ADD-ON | CONFIRMED |
| 21 | compliance-service | 8021 | IMPLEMENTED | CONFIRMED |
| 22 | decision-service | 8022 | IMPLEMENTED | CONFIRMED |
| 23 | bank-service | 8023 | IMPLEMENTED | CONFIRMED |
| 24 | whatsapp-service | 8024 | IMPLEMENTED | CONFIRMED |
| — | api-gateway | 8000 | N/A | N/A |

**Note on "ewa-financial-service":** `docs/canon/service-map.md` does not include a dedicated `ewa-financial-service` section in the portion read, but `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` and `FEATURE_SCOPE.md` reference it (F-015 area) with owned entities `EWARequest`, `SalaryAdvance`, `RepaymentSchedule`, `PayrollDeduction` and canonical API prefix `/api/v1/financial-wellness`. No `ewa-financial-service` entry exists in `docker-compose.yml` (24 services enumerated above are exhaustive). A related module `backend/services/finance/ewa.py` exists. This is flagged as a discrepancy in `BACKEND_ARCHITECTURE_REPORT.md`.
