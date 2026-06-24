# AUTO-CLOSED REGISTER

Layer: Project Memory
Status: Active
Created: 2026-06-18
Rule: Items here are proven facts. Do not re-investigate. Update if evidence changes.

---

## §1 — GATEWAY ROUTE CONFIRMATIONS (AC-001, AC-002, AC-003, AC-018)

**Item ID:** AC-001 / AC-002 / AC-003 / AC-018
**Title:** All 25 gateway routes confirmed; non-standard envelope for routes 22–25
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** FEATURE_SCOPE.md TBDs; FULLSTACK_STITCHING_CONTRACT.md; api-standards.md
**Evidence Source:** `backend/api-gateway/routes.py` lines 1–55; `backend/deployment/config/gateway-routes.json` lines 1–28
**Resolution Source:** Phase 2.8 (TR-001 to TR-006); Phase 3.25 DC-001
**Resolution Date:** 2026-06-16
**Resolved By:** Autonomous — code evidence
**Decision Summary:** All 25 gateway routes are confirmed in code. Routes 22–25 (compliance, decisions, banking, whatsapp) use `{status, data, service}` envelope. `/api/v1/analytics` does not exist; correct prefix is `/api/v1/reporting`. `/api/v1/financial-wellness` does not exist as a gateway route.
**Detailed Explanation:** `routes.py` lines 1–55 define all 25 routes. Lines 52–55 add routes 22–25 (`/api/v1/compliance`, `/api/v1/decisions`, `/api/v1/banking`, `/api/v1/whatsapp`). These four services return `{status, data, service}` not the standard `{status, data, meta, error}` envelope (C-001 condition).
**Affected Components:** API Gateway; all frontend API consumers; FRONTEND_API_DEPENDENCY_MAP
**Affected Routes:** All 25 — `/api/v1/auth`, `/api/v1/employees`, `/api/v1/departments`, `/api/v1/roles`, `/api/v1/attendance`, `/api/v1/leave`, `/api/v1/payroll`, `/api/v1/hiring`, `/api/v1/workflows`, `/api/v1/audit`, `/api/v1/notifications`, `/api/v1/settings`, `/api/v1/reporting`, `/api/v1/performance`, `/api/v1/helpdesk`, `/api/v1/search`, `/api/v1/expense`, `/api/v1/integrations`, `/api/v1/automations`, `/api/v1/engagement`, `/api/v1/settings`, `/api/v1/compliance`, `/api/v1/decisions`, `/api/v1/banking`, `/api/v1/whatsapp`
**Affected APIs:** All 25 gateway-registered APIs
**Affected Workflows:** All workflows that call backend APIs
**Affected Roles:** All roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW — if routes are added/removed, update routes.py and this entry
**Reopen Criteria:** Only if `routes.py` or `gateway-routes.json` is modified to add/remove/rename routes
**Related Documents:** `backend/api-gateway/routes.py`; `backend/deployment/config/gateway-routes.json`; `backend/docs/canon/api-standards.md`; `docs/08_reports/FINAL_CLASSIFIED_REGISTER.md`
**Related Register Entries:** AC-016 (roles/org served by employee-service); AC-044 (WhatsApp route)

---

## §2 — EWA / FINANCIAL WELLNESS ARCHITECTURE (AC-004, AC-017, AC-075)

**Item ID:** AC-004 / AC-017 / AC-075
**Title:** EWA is in-process within payroll-service; no standalone container; `/api/v1/financial-wellness` does not exist; Decision Cards are in-memory
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** service-map.md TBDs; ARG-002; api-standards.md TBD
**Evidence Source:** `backend/services/finance/ewa.py` (FinancialWellnessService); `backend/payroll_service.py` line 392; `backend/banking_api.py` (Raast payout); `backend/docker-compose.yml` (no ewa container); `backend/services/decision_engine.py` (DecisionCard class)
**Resolution Source:** Phase 3.25 DC-009, DC-013
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — code evidence
**Decision Summary:** `FinancialWellnessService` lives in `backend/services/finance/ewa.py` and is instantiated in-process by `payroll_service.py` (line 392). EWA payouts route through `banking_api.py` using the Raast endpoint. There is no `ewa-financial-service` container. `/api/v1/financial-wellness` is not a gateway route. Decision Cards are runtime/in-memory objects (no `decision_cards` DB table exists).
**Affected Components:** payroll-service; banking-service; dashboard Decision Cards widget
**Affected Routes:** None — EWA has no independent route
**Affected APIs:** `/api/v1/payroll` (EWA embedded); `/api/v1/decisions` (Decision Cards via gateway route 23)
**Affected Workflows:** WF-003 (Payroll Run — disbursement step)
**Affected Roles:** PayrollAdmin, Admin
**Owner Required:** NO
**External Dependency:** YES — Raast payment credentials (see ED-004)
**Future Impact:** LOW — architecture is confirmed; EWA remains in-process unless a future ADR creates a standalone service
**Reopen Criteria:** Only if a new `ewa-financial-service` container is added to docker-compose.yml
**Related Documents:** `backend/services/finance/ewa.py`; `backend/payroll_service.py`; `backend/docs/canon/service-map.md`
**Related Register Entries:** ED-004 (Raast credentials); AC-001 (gateway route 23 for decisions)

---

## §3 — AUTOMATION ENGINE TRIGGER MODEL (AC-005)

**Item ID:** AC-005
**Title:** Automation engine is event-triggered only; scheduled and threshold triggers NOT implemented
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** service-map.md automation-service description; FEATURE_SCOPE.md F-013
**Evidence Source:** `backend/automation_contract.py` — only event-type trigger matching; no scheduled/threshold trigger logic
**Resolution Source:** Phase 3.25 DC-010; EG-003
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — code evidence
**Decision Summary:** `automation_contract.py` implements only event-type trigger matching. There are no scheduled job triggers or threshold-based triggers in the automation engine. F-013 key operations were incorrectly described as "scheduled jobs, threshold-triggered" — this has been corrected in FEATURE_SCOPE.md.
**Affected Components:** automation-service
**Affected Routes:** `/api/v1/automations` (gateway route 20)
**Affected APIs:** `POST /api/v1/automations/trigger`
**Affected Workflows:** Any workflow using automation rules
**Affected Roles:** Admin
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** MEDIUM — if scheduled/threshold triggers are added, automation_contract.py must be updated and this entry reopened
**Reopen Criteria:** If `automation_contract.py` gains scheduled or threshold trigger support
**Related Documents:** `backend/automation_contract.py`; `docs/00_authority/FEATURE_SCOPE.md` F-013
**Related Register Entries:** AC-001 (gateway route 20)

---

## §4 — HELPDESK ENUMS (AC-006, AC-007)

**Item ID:** AC-006 / AC-007
**Title:** Helpdesk ticket priority and status application-level enums confirmed
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** DOMAIN_MODEL.md lines 1029–1030 TBDs; DATABASE_SCHEMA.md lines 1889–1894
**Evidence Source:** `backend/helpdesk_service.py` line 128 (PRIORITIES); line 127 (TICKET_STATUSES)
**Resolution Source:** Phase 3.25 DC-011
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — code evidence
**Decision Summary:** Priority values: `{Low, Medium, High, Urgent}`. Status values: `{Draft, Open, InProgress, Resolved, Closed}`. These are application-enforced; DB has no CHECK constraints on the `helpdesk_tickets` table.
**Affected Components:** helpdesk-service; Helpdesk screen (G-017 — ADD-ON deferred)
**Affected Routes:** `/api/v1/helpdesk`
**Affected APIs:** `POST /api/v1/helpdesk/tickets`; `GET /api/v1/helpdesk/tickets`
**Affected Workflows:** Helpdesk ticket lifecycle
**Affected Roles:** All roles (Employee creates; Manager/Admin manages)
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW — if enums change, update helpdesk_service.py and this entry
**Reopen Criteria:** If `helpdesk_service.py` PRIORITIES or TICKET_STATUSES sets are modified
**Related Documents:** `backend/helpdesk_service.py`; `docs/01_backend/DATABASE_SCHEMA.md`; `docs/00_authority/DOMAIN_MODEL.md`
**Related Register Entries:** OS-014 (Helpdesk screen is ADD-ON)

---

## §5 — SETTINGS HANDLER (AC-008)

**Item ID:** AC-008
**Title:** Settings-service handler is an in-memory dict stub in service_runtime.py; resets on restart
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** FULLSTACK_STITCHING_CONTRACT.md T-013 handler TBD
**Evidence Source:** `backend/docker/service_runtime.py` lines 236–254
**Resolution Source:** Phase 3.25 DC-014; C-002
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — code evidence
**Decision Summary:** Settings-service has no separate file. It is an inline in-memory dict stub in `service_runtime.py`. Settings reset on process restart (C-002 condition). Frontend must not cache settings aggressively.
**Affected Components:** settings-service; Settings screen (H10)
**Affected Routes:** `/api/v1/settings`
**Affected APIs:** `GET /api/v1/settings`; `PATCH /api/v1/settings`
**Affected Workflows:** HR policy configuration
**Affected Roles:** Admin only
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** HIGH — if settings-service is upgraded to a persistent store, C-002 condition changes and this entry must be updated
**Reopen Criteria:** If a persistent settings store (DB or KV) is wired into settings-service
**Related Documents:** `backend/docker/service_runtime.py`; `docs/09_project_memory/SAFE_DEFAULT_REGISTER.md` C-002 note
**Related Register Entries:** SD-033 (rate limiter single-replica — same architectural tier)

---

## §6 — HEALTH / READY ENDPOINTS (AC-009)

**Item ID:** AC-009
**Title:** /health and /ready endpoints registered in service_runtime.py
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** TBD_RESOLUTION_REGISTER.md TO-001; UNVERIFIED_CLAIMS_REGISTER.md UC-004
**Evidence Source:** `backend/docker/service_runtime.py` line 410: `if path in ("/health", "/ready"):`
**Resolution Source:** Phase 3.25 DC-003
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — code evidence
**Decision Summary:** Single `if path in ("/health", "/ready"):` block handles both endpoints. Returns standard success envelope. No JWT required.
**Affected Components:** All 24 microservices (all use service_runtime.py)
**Affected Routes:** `GET /health`; `GET /ready`
**Affected APIs:** Health check endpoints
**Affected Workflows:** Deployment readiness; Docker Compose health checks
**Affected Roles:** None (public endpoints)
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** NONE
**Reopen Criteria:** Only if service_runtime.py health check logic is modified
**Related Documents:** `backend/docker/service_runtime.py`
**Related Register Entries:** None

---

## §7 — CIRCUITBREAKER USAGE (AC-010)

**Item ID:** AC-010
**Title:** CircuitBreaker used selectively in hiring-service and supervisor-engine; not all 24 services use it
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** UNVERIFIED_CLAIMS_REGISTER.md UC-003; TBD_RESOLUTION_REGISTER.md TO-002
**Evidence Source:** `backend/resilience.py` (definition); `backend/hiring_service/service.py` (usage); `backend/supervisor_engine.py` (usage); `backend/tests/test_failure_resilience.py` (tests)
**Resolution Source:** Phase 3.25 DC-004
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — code evidence
**Decision Summary:** CircuitBreaker is defined in `resilience.py` and used in hiring-service and supervisor-engine. It is not applied to all 24 services — selective usage is the confirmed pattern.
**Affected Components:** hiring-service; supervisor-engine
**Affected Routes:** `/api/v1/hiring`
**Affected APIs:** Hiring pipeline endpoints
**Affected Workflows:** WF-004 (Hiring Pipeline)
**Affected Roles:** Admin, Manager, Recruiter
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW
**Reopen Criteria:** If CircuitBreaker usage is extended to other services
**Related Documents:** `backend/resilience.py`; `backend/hiring_service/service.py`
**Related Register Entries:** None

---

## §8 — OUTBOX SYSTEM (AC-011, AC-012)

**Item ID:** AC-011 / AC-012
**Title:** OutboxManager confirmed in outbox_system.py; 007_event_outbox.sql confirmed
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** UNVERIFIED_CLAIMS_REGISTER.md UC-001/002; TBD_RESOLUTION_REGISTER.md TO-003/004
**Evidence Source:** `backend/outbox_system.py` lines 1–60 (`OutboxManager` class, `PersistentKVStore`, 3 namespaces: `outbox_records`, `processed_events`, `dispatch_log`); `backend/deployment/migrations/007_event_outbox.sql` (defines `service_outbox` table)
**Resolution Source:** Phase 3.25 DC-005, DC-006
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — code evidence
**Decision Summary:** OutboxManager uses PersistentKVStore with 3 namespaces. The `service_outbox` SQL table exists in migration 007. The PersistentKVStore is the confirmed runtime path; SQL tables are migration artifacts for persistence.
**Affected Components:** All services that publish events
**Affected Routes:** None directly
**Affected APIs:** Event publication mechanisms
**Affected Workflows:** All event-driven workflows
**Affected Roles:** None (internal)
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** MEDIUM — if outbox is migrated to a message broker (RabbitMQ/Kafka), this entry must be updated
**Reopen Criteria:** If outbox_system.py is replaced or message broker is introduced
**Related Documents:** `backend/outbox_system.py`; `backend/deployment/migrations/007_event_outbox.sql`
**Related Register Entries:** SD-011 (service_outbox vs PersistentKVStore default)

---

## §9 — PERMISSIONS AND ROLES (AC-013, AC-014, AC-015, AC-079)

**Item ID:** AC-013 / AC-014 / AC-015 / AC-079
**Title:** All 31 capabilities confirmed; 5 roles confirmed; Recruiter uses Department scope; scope enforcement model confirmed
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** USER_ROLES_AND_PERMISSIONS.md §3.3 (19 TBDs); §4 Requisition scope TBD
**Evidence Source:** `backend/docs/canon/security-model.md` lines 16–48; `backend/auth-service/service.py` line 521 `assign_role_binding` validation set; `_service_scopes_for_user` logic
**Resolution Source:** Phase 3.25 DC-007, DC-008; Phase 2 Phase 2.95
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — canon document + code evidence
**Decision Summary:** 31 capabilities confirmed from security-model.md (canon). 5 roles: Admin, PayrollAdmin, Manager, Recruiter, Employee. `Requisition` is NOT a validated `scope_type` in auth-service; Recruiter uses `Department` scope; requisition-level scoping is delegated to hiring-service layer. Gateway validates role; service validates scope.
**Affected Components:** auth-service; API Gateway RBAC; all protected routes
**Affected Routes:** All 25 gateway routes
**Affected APIs:** `POST /api/v1/auth/login`; `POST /api/v1/auth/refresh`; all protected endpoints
**Affected Workflows:** All workflows (auth gates entry)
**Affected Roles:** All 5 roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** HIGH — if roles or capabilities are added, security-model.md and auth-service must both be updated
**Reopen Criteria:** If new roles are added; if capability set changes; if scope_type enum changes
**Related Documents:** `backend/docs/canon/security-model.md`; `backend/auth-service/service.py`; `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md`
**Related Register Entries:** AC-037 (gateway RBAC); AC-016 (roles served by employee-service)

---

## §10 — EMPLOYEE SERVICE HANDLERS (AC-016, AC-041, AC-042, AC-043, AC-078)

**Item ID:** AC-016 / AC-041 / AC-042 / AC-043 / AC-078
**Title:** employee_api.py 14 handlers confirmed; `/api/v1/roles` and `/api/v1/org` served by employee-service; payroll run confirmed; reporting endpoints confirmed
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** FULLSTACK_STITCHING_CONTRACT.md T-001/002/003/006/011/015 TBDs; api-standards.md `/api/v1/roles` TBD
**Evidence Source:** `backend/employee_api.py` lines 1–124 (14 handlers); `backend/payroll_api.py` (`post_payroll_records`); `backend/tests/test_reporting_analytics.py` (13 endpoints); `backend/tests/test_payroll_to_bank_happy_path.py`
**Resolution Source:** Phase 2 EG-001; Phase 3.25 DC-002, DC-020
**Resolution Date:** 2026-06-16
**Resolved By:** Autonomous — code implementation
**Decision Summary:** `backend/employee_api.py` has 14 handlers registered in service_runtime.py for full CRUD on employees, departments, roles. `/api/v1/roles` and `/api/v1/org` are served by employee-service (C-004 condition — no separate gateway prefix). `POST /api/v1/payroll/run` confirmed. 13 reporting endpoints confirmed.
**Affected Components:** employee-service; payroll-service; reporting-analytics-service
**Affected Routes:** `/api/v1/employees`; `/api/v1/departments`; `/api/v1/payroll`; `/api/v1/reporting`
**Affected APIs:** All employee CRUD, payroll run, reporting aggregates
**Affected Workflows:** WF-001 (Onboarding); WF-003 (Payroll Run)
**Affected Roles:** Admin, Manager, PayrollAdmin
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** MEDIUM — if employee-service handlers are added/removed, update employee_api.py and this entry
**Reopen Criteria:** If employee_api.py handler count changes; if roles routes are moved to a separate service
**Related Documents:** `backend/employee_api.py`; `backend/employee_service.py`; `docs/01_backend/SERVICE_CATALOG.md`
**Related Register Entries:** AC-013 (roles/permissions); AC-001 (gateway routes)

---

## §11 — DEAD TYPESCRIPT CODE (AC-019, AC-020, AC-021, AC-022)

**Item ID:** AC-019 / AC-020 / AC-021 / AC-022
**Title:** 60 TypeScript files confirmed dead; Python tests test Python only
**Classification:** AUTO-CLOSED
**Current Status:** Closed — files archived
**Original Source:** OA-004/005/006; UC-007; BACKEND_ARCHITECTURE.md §5
**Evidence Source:** grep: zero Python import callers for any TypeScript file; all 80+ test files in `backend/tests/` are `.py`; TypeScript cannot be imported by Python
**Resolution Source:** Phase 3.25 DC-018; Mandate 2 execution
**Resolution Date:** 2026-06-17 (confirmed); 2026-06-18 (archived)
**Resolved By:** Autonomous — grep + code evidence; SAFE_REPOSITORY_HYGIENE execution
**Decision Summary:** 43 TypeScript files in `backend/services/employee-service/`, 6 in `backend/services/settings-service/`, 11 in `backend/middleware/` are dead code with zero Python callers. All 60 have been archived to `backend/docs/system/archive/`. Python tests only test Python code; TypeScript test files (if any) cannot be imported.
**Affected Components:** None (dead code)
**Affected Routes:** None
**Affected APIs:** None
**Affected Workflows:** None
**Affected Roles:** None
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** NONE — archived files are reference-only
**Reopen Criteria:** If TypeScript files are restored to active paths (would require architectural decision to add Node.js runtime)
**Related Documents:** `backend/docs/system/archive/typescript-employee-service/`; `backend/docs/system/archive/typescript-settings-service/`; `backend/docs/system/archive/typescript-middleware/`
**Related Register Entries:** SD-001/002/003 (archive actions)

---

## §12 — CACHE LAYER (AC-023)

**Item ID:** AC-023
**Title:** No general-purpose cache layer exists for domain services
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** BACKEND_ARCHITECTURE.md §7 TBD
**Evidence Source:** ADR-001 §4 ("No caching layer — Redis/Memcached not present"); `cache.service.ts` is TypeScript dead code; only `_IdempotencyCache` (gateway) and `_atl_cache` (ATL adapter) exist in Python runtime
**Resolution Source:** Phase 3.25 DC-019
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — ADR + code evidence
**Decision Summary:** No Redis or Memcached. No domain-level cache. Two in-process caches exist: `_IdempotencyCache` in the gateway (idempotency key deduplication) and `_atl_cache` in the ATL adapter (tax lookup caching). `cache.service.ts` is dead TypeScript code.
**Affected Components:** API Gateway; ATL compliance adapter
**Affected Routes:** None
**Affected APIs:** None
**Affected Workflows:** None
**Affected Roles:** None
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** MEDIUM — if Redis is added, update ADR-001 and this entry
**Reopen Criteria:** If Redis/Memcached is added to docker-compose.yml
**Related Documents:** `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md`
**Related Register Entries:** AC-008 (settings in-memory)

---

## §13 — RESOLVED DEAD/STALE CODE ITEMS (AC-024, AC-025, AC-027, AC-028, AC-029, AC-076)

**Item ID:** AC-024 / AC-025 / AC-027 / AC-028 / AC-029 / AC-076
**Title:** Dead function deleted; product name updated; OS artifact absent; root files present; dead CI files archived
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** OA-001/002/009/010; backend/.github/workflows/
**Evidence Source:** grep: `_employee_domain_departments` not found; `api_gateway_service.py` line 205 = "Meridian HCM API"; root directory scan: no .lnk file; `.gitignore` and `README.md` read confirmed; `backend/.github/workflows/` files archived
**Resolution Source:** Mandate 2 + OWNER-REQUIRED compression 2026-06-18
**Resolution Date:** 2026-06-18
**Resolved By:** Autonomous — grep + file inspection; SAFE_REPOSITORY_HYGIENE execution
**Decision Summary:** (1) `_employee_domain_departments()` was already deleted — not found in codebase. (2) "Aura HRMS API" title was already updated to "Meridian HCM API"; contact email fixed (`support@meridian-hcm.internal`). (3) OS artifact `.lnk` file was already absent. (4) Root `.gitignore` and `README.md` existed and are accurate. (5) Dead CI files (`build.yml`, `deploy.yml`, `test.yml` from `backend/.github/workflows/`) archived — these files never executed because GitHub Actions only reads root `.github/workflows/`.
**Affected Components:** `api_gateway_service.py` OpenAPI spec; repository root
**Affected Routes:** `/openapi.json` (OpenAPI spec served by gateway)
**Affected APIs:** OpenAPI spec metadata
**Affected Workflows:** None
**Affected Roles:** None
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** NONE
**Reopen Criteria:** None — all items fully resolved
**Related Documents:** `backend/docker/api_gateway_service.py`; `backend/docs/system/archive/dead-ci-workflows/`
**Related Register Entries:** SD-004 (CI archive action); OS-002 (CI activation is out of scope)

---

## §14 — ATTENDANCE SERVICE NAMING (AC-026)

**Item ID:** AC-026
**Title:** `backend/attendance_service/` (directory package) and `backend/services/attendance_service.py` (standalone module) coexist validly
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** OA-008 naming conflict concern
**Evidence Source:** `backend/services/attendance_service.py` read: `AttendanceService` class with `AttendanceEntry` dataclass; `backend/attendance_service/` directory: containerized service package with `service.py` and `api.py`
**Resolution Source:** Phase 3.25 DETERMINISM_CERTIFICATION_REPORT; this session
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — code inspection
**Decision Summary:** Two distinct implementations coexist: `backend/attendance_service/` is the containerized service package (used by service_runtime.py as `from attendance_service.api import ...`); `backend/services/attendance_service.py` is a standalone module with `AttendanceService` class used for advanced attendance logic (biometric, GPS, face recognition, overtime calculation). No naming conflict — different paths, different purposes.
**Affected Components:** attendance-service
**Affected Routes:** `/api/v1/attendance`
**Affected APIs:** Attendance record endpoints
**Affected Workflows:** WF-002 (Leave + Attendance); WF-003 (Payroll — attendance input)
**Affected Roles:** All roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW
**Reopen Criteria:** If the two implementations are consolidated into one
**Related Documents:** `backend/services/attendance_service.py`; `backend/attendance_service/`
**Related Register Entries:** None

---

## §15 — FRONTEND LOCATION (AC-030)

**Item ID:** AC-030
**Title:** Frontend confirmed at `backend/ui/` through Phase 4
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** OCR-001; UI-001; OA-003
**Evidence Source:** DETERMINISM_CERTIFICATION_REPORT; C-003 condition; docker-compose.yml `frontend-ui` service context
**Resolution Source:** Phase 3.25 OCR-001 decision
**Resolution Date:** 2026-06-17
**Resolved By:** Decision — phase constraint
**Decision Summary:** Next.js 15 frontend lives at `backend/ui/`. This location is confirmed for all of Phase 4 implementation. Relocation to `frontend/` is deferred post-Phase 4 (see OS-001).
**Affected Components:** Next.js 15 frontend; Docker Compose `frontend-ui` service
**Affected Routes:** All frontend routes (served from `backend/ui/`)
**Affected APIs:** None
**Affected Workflows:** All UI workflows
**Affected Roles:** All roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** MEDIUM — relocation post-Phase 4 requires docker-compose.yml update and import path verification
**Reopen Criteria:** When owner authorizes frontend relocation (post-Phase 4)
**Related Documents:** `backend/docker-compose.yml`; `backend/ui/`; `docs/09_project_memory/OUT_OF_SCOPE_REGISTER.md` OS-001
**Related Register Entries:** OS-001 (relocation is out of scope)

---

## §16 — CONFIRMED OUT-OF-SCOPE FEATURES (AC-031–AC-034, AC-080–AC-082)

**Item ID:** AC-031 / AC-032 / AC-033 / AC-034 / AC-080 / AC-081 / AC-082
**Title:** Mobile app, Shift/Roster, LMS, Document Management, ATS inbound, Time Tracking, Video Interview confirmed OUT OF SCOPE
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** FEATURE_SCOPE.md OUT OF SCOPE section; multiple TBDs
**Evidence Source:** No service, schema, gateway route, or docker-compose entry for any of these features
**Resolution Source:** Phase 3.25; FEATURE_SCOPE.md authority
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — absence of evidence + FEATURE_SCOPE.md confirmation
**Decision Summary:** All seven features are confirmed absent from the codebase. They are not in scope for Phase 4 or any current phase.
**Affected Components:** None
**Affected Routes:** None
**Affected APIs:** None
**Affected Workflows:** None
**Affected Roles:** None
**Owner Required:** NO — scope decisions already made
**External Dependency:** NO
**Future Impact:** NONE for current phases; future phases may introduce these
**Reopen Criteria:** If owner authorizes development of any of these features
**Related Documents:** `docs/00_authority/FEATURE_SCOPE.md` OUT OF SCOPE section
**Related Register Entries:** OS-007/008/009/010 (frontend gap entries for these features)

---

## §17 — PRODUCT DECISIONS (AC-035–AC-038, AC-083)

**Item ID:** AC-035 / AC-036 / AC-037 / AC-038 / AC-083
**Title:** All 21 product decisions STABLE; navigation, RBAC, dashboard, OAQs resolved
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** PRODUCT_DECISION_REGISTER.md Phase 2.95; multiple TBDs
**Evidence Source:** PRODUCT_DECISION_REGISTER.md (all sections STABLE); `_ROUTE_ROLE_MAP` in `api_gateway_service.py`
**Resolution Source:** Phase 2.95 residual decision collapse
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — authority document
**Decision Summary:** All 21 product decisions in PRODUCT_DECISION_REGISTER.md are STABLE. Navigation structure: 21 routes defined. RBAC: 4 restricted routes (`/payroll`, `/audit`, `/hiring`, `/reporting`). Dashboard composition: 7 widgets confirmed. OAQ-001 to OAQ-010: zero Phase 4 impact.
**Affected Components:** All frontend screens; API Gateway RBAC
**Affected Routes:** All 21 navigation routes
**Affected APIs:** Dashboard data endpoints
**Affected Workflows:** All 8 workflows
**Affected Roles:** All 5 roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** MEDIUM — if product scope changes, PRODUCT_DECISION_REGISTER.md must be updated first
**Reopen Criteria:** If owner authorizes product scope changes
**Related Documents:** `docs/08_reports/PRODUCT_DECISION_REGISTER.md`
**Related Register Entries:** AC-013 (permissions); AC-001 (gateway routes)

---

## §18 — API CONTRACT (AC-039)

**Item ID:** AC-039
**Title:** API contract (versioning, auth, rate limiting, envelope shapes) STABLE
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** api-standards.md; PRODUCT_DECISION_REGISTER.md §6
**Evidence Source:** `api_gateway_service.py` (JWT HS256 enforcement; 200 req/min rate limit; `/api/v1/` prefix); `backend/docs/canon/api-standards.md`
**Resolution Source:** Phase 2.95; Phase 3.25
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — code + documentation
**Decision Summary:** Standard envelope: `{status, data, meta, error}` for 21 services. Non-standard: `{status, data, service}` for compliance/decisions/banking/whatsapp (C-001). API versioning: `/api/v1/` prefix. Auth: JWT HS256, Bearer token. Rate limiting: 200 req/min per IP. Base URL (dev): `http://localhost:8000`.
**Affected Components:** API Gateway; all frontend API consumers
**Affected Routes:** All 25 routes
**Affected APIs:** All APIs
**Affected Workflows:** All
**Affected Roles:** All
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** HIGH — if envelope format changes, update ADR-001 and notify all consumers
**Reopen Criteria:** If envelope format changes; if auth mechanism changes; if versioning strategy changes
**Related Documents:** `backend/docs/canon/api-standards.md`; `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md`
**Related Register Entries:** AC-001 (routes); AC-013 (auth/RBAC)

---

## §19 — WORKFLOW CLASSIFICATIONS (AC-040, AC-065–AC-068)

**Item ID:** AC-040 / AC-065 / AC-066 / AC-067 / AC-068
**Title:** All 8 workflows classified; specific WF TBDs resolved
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** PRODUCT_WORKFLOWS.md TBDs; FULLSTACK_STITCHING_CONTRACT.md workflow coverage
**Evidence Source:** DOMAIN_MODEL.md; leave_service.py; payroll schema (`002_workflow_schema.sql`); FEATURE_SCOPE.md
**Resolution Source:** Phase 3.25 DC-015/016/017; Phase 2.95
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — code + authority docs
**Decision Summary:** WF-001/002/003/004/007/008 STABLE. WF-005/006 ADD-ON deferred. Specific resolutions: (1) WF-001 Document Collection step — OUT OF SCOPE. (2) WF-002 Calendar Updated — attendance-service reads leave records during period close; no OnLeave employee status. (3) WF-003 No approval step — PayrollAdmin transitions Draft→Processed directly.
**Affected Components:** workflow-service; leave-service; attendance-service; payroll-service
**Affected Routes:** `/api/v1/workflows`; `/api/v1/leave`; `/api/v1/attendance`; `/api/v1/payroll`
**Affected APIs:** Workflow inbox; leave approval; attendance period close; payroll run
**Affected Workflows:** WF-001 to WF-008
**Affected Roles:** All roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** MEDIUM — if workflow steps are added, update PRODUCT_WORKFLOWS.md
**Reopen Criteria:** If payroll approval step is implemented; if document collection is added
**Related Documents:** `docs/00_authority/PRODUCT_WORKFLOWS.md`; `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md`
**Related Register Entries:** OS-022/023 (WF-005/006 ADD-ON)

---

## §20 — STALE TBD FIXES (AC-044–AC-048, AC-062–AC-064, AC-084)

**Item ID:** AC-044 / AC-045 / AC-046 / AC-047 / AC-048 / AC-062 / AC-063 / AC-064 / AC-084
**Title:** 9 stale TBD markers fixed across DATABASE_SCHEMA.md, INTEGRATION_CATALOG.md, VALIDATION_RULES.md, CONTRACT_VERSION_REGISTRY.md, FRONTEND_GAP_REGISTER.md
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** Various documentation TBDs that were stale after Phase 2.8 route confirmations
**Evidence Source:** Same as underlying items (route confirmations, helpdesk enums, attendance service file)
**Resolution Source:** Mandate 2 (2026-06-17/18)
**Resolution Date:** 2026-06-17 / 2026-06-18
**Resolved By:** Autonomous — cross-reference with already-confirmed evidence
**Decision Summary:** 9 stale TBD markers corrected in documentation. Key fixes: WhatsApp gateway route 25 confirmed in INTEGRATION_CATALOG; helpdesk enums filled in DATABASE_SCHEMA; attendance_service.py confirmed in VALIDATION_RULES; routes 22–25 confirmed in CONTRACT_VERSION_REGISTRY; roles contracts corrected to `/api/v1/employees`; compliance reports route confirmed.
**Affected Components:** Documentation only — no runtime impact
**Affected Routes:** None (documentation fixes)
**Affected APIs:** None
**Affected Workflows:** None
**Affected Roles:** None
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** NONE
**Reopen Criteria:** None
**Related Documents:** `docs/01_backend/DATABASE_SCHEMA.md`; `docs/01_backend/INTEGRATION_CATALOG.md`; `docs/01_backend/VALIDATION_RULES.md`; `docs/03_fullstack_contracts/CONTRACT_VERSION_REGISTRY.md`
**Related Register Entries:** AC-006/007 (helpdesk enums); AC-001 (routes)

---

## §21 — FRONTEND GAP AUTO-CLOSURES (AC-049–AC-061)

**Item ID:** AC-049 to AC-061
**Title:** 13 frontend gap items AUTO-CLOSED as implementation details or documented known gaps
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** FRONTEND_GAP_REGISTER.md G-020 to G-053, G-061 to G-062
**Evidence Source:** FRONTEND_API_DEPENDENCY_MAP; FRONTEND_ROLE_EXPERIENCE_MATRIX; PRODUCT_DECISION_REGISTER.md; C-001 condition
**Resolution Source:** Phase 3 authority capture; FRONTEND_GAP_REGISTER.md Phase 3 classification
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — authority documentation
**Decision Summary:** Settings sections G-020 to G-024 are chrome-only by design (no backend for profile/security/notification preferences). Entity lifecycle gaps G-030 to G-038 are either implementation details or covered by existing Admin edit capabilities. API endpoint uncertainty G-040 to G-044 are implementation details with documented fallback patterns. RBAC edge cases G-050 to G-053 are handled by API scope enforcement and documented in ROLE_EXPERIENCE_MATRIX. G-062 (banking envelope) is covered by C-001 documentation.
**Affected Components:** Settings screen (H10); Employee Profile (H03); Approval Inbox (H05); Compliance screen; Dashboard
**Affected Routes:** `/settings`; `/employees/[id]`; `/approvals`; `/compliance`; `/dashboard`
**Affected APIs:** Various (see gap details in FRONTEND_GAP_REGISTER.md)
**Affected Workflows:** Various
**Affected Roles:** All roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW — implementation details resolved during Phase 4 sprint work
**Reopen Criteria:** Only if API contract changes make documented fallback patterns invalid
**Related Documents:** `docs/03_frontend_authority/FRONTEND_GAP_REGISTER.md`; `docs/03_frontend_authority/FRONTEND_API_DEPENDENCY_MAP.md`
**Related Register Entries:** OS-011 to OS-019 (ADD-ON and out-of-scope gap items)

---

## §22 — BACKEND GAP RESOLUTIONS (AC-069–AC-071, AC-077)

**Item ID:** AC-069 / AC-070 / AC-071 / AC-077
**Title:** All 19 backend gaps RESOLVED in Phase 2; all 15+ migrations confirmed
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** BACKEND_GAP_REGISTER.md DG-001 to EG-003
**Evidence Source:** `backend/deployment/migrations/014_schema_integrity_fixes.sql`; `backend/deployment/migrations/015_employee_service.sql`; `backend/employee_api.py`; `backend/employee_service.py`
**Resolution Source:** Phase 2 Backend Authority Capture (2026-06-16)
**Resolution Date:** 2026-06-16
**Resolved By:** Autonomous — implementation + migration creation
**Decision Summary:** All 19 gaps (DG-001/002, AG-001/006, ARG-001/004, EG-001/003) resolved. grade_bands table created (migration 014). Multi-tenancy FK pattern fixed (migration 014). Employee-service implemented (migration 015 + employee_api.py + employee_service.py). Country resolver startup hook implemented. All backend risks CLOSED.
**Affected Components:** All services with DB dependencies; employee-service; compliance-service
**Affected Routes:** All employee-related routes
**Affected APIs:** All employee CRUD
**Affected Workflows:** WF-001 (Onboarding)
**Affected Roles:** Admin, Manager
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW — all gaps resolved; future schema changes require new migrations
**Reopen Criteria:** If new schema integrity issues are discovered
**Related Documents:** `docs/08_reports/BACKEND_GAP_REGISTER.md`; `backend/deployment/migrations/`
**Related Register Entries:** AC-010 (employee service)

---

## §23 — PHASE 3 FRONTEND AUTHORITY (AC-072–AC-074)

**Item ID:** AC-072 / AC-073 / AC-074
**Title:** Phase 3 frontend authority complete — 12 docs, 55 components, 55 routes
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** Phase 3 Frontend Authority Capture mandate
**Evidence Source:** `docs/03_frontend_authority/` — 12 documents confirmed
**Resolution Source:** Phase 3 (2026-06-17)
**Resolution Date:** 2026-06-17
**Resolved By:** Autonomous — authority document creation
**Decision Summary:** Phase 3 produced 12 authority documents in `docs/03_frontend_authority/`: FRONTEND_AUTHORITY_MASTER.md, FRONTEND_ROUTE_CATALOG.md, FRONTEND_NAVIGATION_MODEL.md, FRONTEND_PERMISSION_MATRIX.md, FRONTEND_DASHBOARD_CATALOG.md, FRONTEND_WORKFLOW_TO_SCREEN_MAP.md, FRONTEND_ROLE_EXPERIENCE_MATRIX.md, FRONTEND_SCREEN_CATALOG.md, FRONTEND_API_DEPENDENCY_MAP.md, FRONTEND_COMPONENT_INVENTORY.md, FRONTEND_GAP_REGISTER.md, FRONTEND_AUTHORITY_READINESS_REPORT.md. 55 components and 55 routes defined.
**Affected Components:** All 55 identified frontend components
**Affected Routes:** All 55 frontend routes
**Affected APIs:** All backend APIs with frontend consumers
**Affected Workflows:** All 8 workflows
**Affected Roles:** All 5 roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** HIGH — Phase 4 implementation follows these authority documents
**Reopen Criteria:** If product scope changes require new screens or routes
**Related Documents:** `docs/03_frontend_authority/FRONTEND_AUTHORITY_MASTER.md`
**Related Register Entries:** AC-035 (product decisions); AC-040 (workflows)

---

## §24 — PHASE 3.5 L0 FRONTEND AUTHORITY INPUT FREEZE (AC-085, AC-086)

**Item ID:** AC-085 / AC-086
**Title:** Phase 3.5 L0 FROZEN — 0 blocking gaps confirmed; L0 output pack created
**Classification:** AUTO-CLOSED
**Current Status:** Closed
**Original Source:** `# PHASE 3.5 — L0 FRONTEND AUTHORITY INPUT FREEZE.md` protocol
**Evidence Source:** `docs/03_frontend_authority/FRONTEND_GAP_REGISTER.md` (43 gaps, 0 blocking); `docs/08_reports/POST_COLLAPSE_FRONTEND_READINESS.md` (7/7 gates PASS); `docs/08_reports/DETERMINISM_CERTIFICATION_REPORT.md` (FULLY DETERMINED); all 13 Phase 3 authority docs reviewed (2026-06-20)
**Resolution Source:** Phase 3.5 protocol execution (2026-06-20)
**Resolution Date:** 2026-06-20
**Resolved By:** Autonomous — systematic review of all 13 source documents
**Decision Summary:** Phase 3.5 reviewed all 13 source documents required by the protocol: FRONTEND_AUTHORITY_MASTER.md, FRONTEND_ROUTE_CATALOG.md, FRONTEND_SCREEN_CATALOG.md, FRONTEND_DASHBOARD_CATALOG.md, FRONTEND_NAVIGATION_MODEL.md, FRONTEND_ROLE_EXPERIENCE_MATRIX.md, FRONTEND_PERMISSION_MATRIX.md, FRONTEND_WORKFLOW_TO_SCREEN_MAP.md, FRONTEND_API_DEPENDENCY_MAP.md, FRONTEND_GAP_REGISTER.md, PRODUCT_DECISION_REGISTER.md, POST_COLLAPSE_FRONTEND_READINESS.md, DETERMINISM_CERTIFICATION_REPORT.md. Zero blocking gaps were found. Final verdict: L0 FROZEN.
**Detailed Explanation:** (AC-085) The protocol required checking every route, screen, workflow, role, permission, API dependency, navigation group, frontend state, and blocked/excluded item for any frontend-impacting gap that would require a NO-GO ruling. None was found. FRONTEND_GAP_REGISTER.md confirms 43 gaps across 8 categories — all non-blocking. POST_COLLAPSE_FRONTEND_READINESS.md confirms GO on all 7 gates (Navigation, Menus, Screens, Workflows, Permissions, User Journeys, Product Scope). DETERMINISM_CERTIFICATION_REPORT.md confirms REPOSITORY FULLY DETERMINED with Phase 4 clearance. (AC-086) Four L0 output files were created: L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md (master freeze, 13 §sections), L0_ROUTE_SCREEN_WORKFLOW_MATRIX.md (full cross-reference), L0_DESIGN_CONSTRAINTS_FOR_CLAUDE_DESIGN.md (12 constraint classes), L0_CLAUDE_DESIGN_BRIEF.md (actionable design brief with 12 parts).
**Affected Components:** All 36 Phase 4 core screens; all 55 routes; all 4 dashboard variants
**Affected Routes:** All 55 frontend routes (45 core + 10 ADD-ON)
**Affected APIs:** All 25 gateway routes
**Affected Workflows:** WF-001 to WF-008 (6 core STABLE, 2 ADD-ON)
**Affected Roles:** All 5 roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** HIGH — Claude Design may begin archetype work using the L0 output pack; Claude Code may validate any design against the frozen inputs
**Reopen Criteria:** If owner changes product scope (adds routes/screens not in the freeze); if a blocking gap is discovered during Phase 4 implementation that was not captured in FRONTEND_GAP_REGISTER.md
**Related Documents:** `docs/03_frontend_authority/L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md`; `docs/03_frontend_authority/L0_ROUTE_SCREEN_WORKFLOW_MATRIX.md`; `docs/03_frontend_authority/L0_DESIGN_CONSTRAINTS_FOR_CLAUDE_DESIGN.md`; `docs/03_frontend_authority/L0_CLAUDE_DESIGN_BRIEF.md`
**Related Register Entries:** AC-072/073/074 (Phase 3 frontend authority); AC-049 to AC-064 (frontend gap auto-closures)
