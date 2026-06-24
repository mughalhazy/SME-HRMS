# SAFE-DEFAULT REGISTER

Layer: Project Memory
Status: Active
Created: 2026-06-18
Rule: Defaults here were adopted because repository evidence strongly supported one path. They may be revisited if evidence changes. Do not re-derive — update this entry instead.

---

## §1 — TYPESCRIPT ARCHIVE EXECUTION (SD-001, SD-002, SD-003)

**Item ID:** SD-001 / SD-002 / SD-003
**Title:** 60 confirmed-dead TypeScript files archived
**Classification:** SAFE-DEFAULT
**Current Status:** EXECUTED
**Original Source:** OA-004/005/006; ROD-002; D-001
**Evidence Source:** grep: zero Python import callers for all TypeScript files; Python runtime cannot import TypeScript
**Resolution Source:** Mandate 2 execution (2026-06-18)
**Resolution Date:** 2026-06-18
**Resolved By:** SAFE_REPOSITORY_HYGIENE execution
**Decision Summary:** 60 TypeScript files moved to archive. Default: confirmed-dead code with zero callers is archived, not deleted, for reference.
**Detailed Explanation:** Files moved: 43 from `backend/services/employee-service/` → `backend/docs/system/archive/typescript-employee-service/`; 6 from `backend/services/settings-service/` → `backend/docs/system/archive/typescript-settings-service/`; 11 from `backend/middleware/` → `backend/docs/system/archive/typescript-middleware/`.
**Affected Components:** None (dead code)
**Affected Routes:** None
**Affected APIs:** None
**Affected Workflows:** None
**Affected Roles:** None
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** NONE
**Reopen Criteria:** If a Node.js runtime is added and TypeScript files are needed
**Related Documents:** `backend/docs/system/archive/`
**Related Register Entries:** AC-019/020/021 (dead code confirmed)

---

## §2 — CI WORKFLOW ARCHIVE (SD-004)

**Item ID:** SD-004
**Title:** 3 dead CI workflow files archived from `backend/.github/workflows/`
**Classification:** SAFE-DEFAULT
**Current Status:** EXECUTED
**Original Source:** OA-007
**Evidence Source:** GitHub Actions only reads `.github/workflows/` at repo root; `backend/.github/workflows/` files never execute
**Resolution Source:** OWNER-REQUIRED compression execution (2026-06-18)
**Resolution Date:** 2026-06-18
**Resolved By:** SAFE_REPOSITORY_HYGIENE execution
**Decision Summary:** `build.yml`, `deploy.yml`, `test.yml` moved to `backend/docs/system/archive/dead-ci-workflows/`. File-level move only; no YAML content modification; not activated in root CI. CI activation strategy is OUT-OF-SCOPE (OS-002/003/004).
**Affected Components:** None (dead files)
**Affected Routes:** None
**Affected APIs:** None
**Affected Workflows:** None
**Affected Roles:** None
**Owner Required:** NO (archive action); YES (activation — see OS-002)
**External Dependency:** NO
**Future Impact:** LOW — archived files available for reference when CI strategy is decided
**Reopen Criteria:** If owner decides to migrate and activate CI workflows
**Related Documents:** `backend/docs/system/archive/dead-ci-workflows/`; `.github/workflows/ci.yml` (live pipeline)
**Related Register Entries:** OS-002/003/004 (CI activation is OUT-OF-SCOPE)

---

## §3 — OPENAPI CONTACT EMAIL FIX (SD-005)

**Item ID:** SD-005
**Title:** OpenAPI contact email updated from `aura-hrms.internal` to `meridian-hcm.internal`
**Classification:** SAFE-DEFAULT
**Current Status:** EXECUTED
**Original Source:** OA-002 (partial — title was already fixed; contact email remained stale)
**Evidence Source:** `backend/docker/api_gateway_service.py` line 208 grep: `support@aura-hrms.internal`
**Resolution Source:** OWNER-REQUIRED compression (2026-06-18)
**Resolution Date:** 2026-06-18
**Resolved By:** TIER 1 safe refactor — cosmetic string constant in OpenAPI metadata
**Decision Summary:** `support@aura-hrms.internal` → `support@meridian-hcm.internal`. Cosmetic metadata fix; no functional impact. Default: product identity strings should match the confirmed product name "Meridian HCM" across all documents and code.
**Affected Components:** `api_gateway_service.py` OpenAPI spec; `/openapi.json` endpoint
**Affected Routes:** `/openapi.json` (served by gateway)
**Affected APIs:** OpenAPI spec metadata only
**Affected Workflows:** None
**Affected Roles:** None
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** NONE
**Reopen Criteria:** If contact email changes
**Related Documents:** `backend/docker/api_gateway_service.py`
**Related Register Entries:** AC-025 (product name auto-closed)

---

## §4 — CROSS-SERVICE DEPENDENCY TRACE (SD-006)

**Item ID:** SD-006
**Title:** service-map.md + docker-compose.yml adopted as authoritative dependency specification
**Classification:** SAFE-DEFAULT
**Current Status:** Closed
**Original Source:** UC-005; TO-005; BACKEND_ARCHITECTURE.md §12 TBDs; UI-003
**Evidence Source:** `backend/docs/canon/service-map.md` (intended dependencies); `backend/docker-compose.yml` env vars (infrastructure-wired dependencies)
**Resolution Source:** Phase 3.25 UI-003; Mandate 2 SAFE-DEFAULT
**Resolution Date:** 2026-06-17
**Resolved By:** Safe default — two authoritative sources accepted as sufficient
**Decision Summary:** Full code-level HTTP call tracing across all 24 services was classified as too large for a single resolution pass (UI-003). Default adopted: `service-map.md` is the authoritative intended-dependency specification; `docker-compose.yml` env vars provide the infrastructure-wired topology. These two together are sufficient for Phase 4 implementation.
**Affected Components:** All 24 microservices
**Affected Routes:** None
**Affected APIs:** None
**Affected Workflows:** None
**Affected Roles:** None
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** MEDIUM — if service dependencies change, update service-map.md; if new services are added, update docker-compose.yml
**Reopen Criteria:** If a specific dependency edge is required for a Phase 4 implementation decision
**Related Documents:** `backend/docs/canon/service-map.md`; `backend/docker-compose.yml`
**Related Register Entries:** None

---

## §5 — EVENT ARCHITECTURE DEFAULTS (SD-007 to SD-012)

**Item ID:** SD-007 / SD-008 / SD-009 / SD-010 / SD-011 / SD-012
**Title:** Event delivery, run_due_jobs wiring, outbox vs KV store, read-model update mechanism, LISTEN/NOTIFY — all defaulted
**Classification:** SAFE-DEFAULT
**Current Status:** Closed
**Original Source:** EVENT_AND_QUEUE_ARCHITECTURE.md TBDs (lines 59, 374–379)
**Evidence Source:** `backend/outbox_system.py`; `backend/background_jobs.py`; `backend/background_jobs_api.py`
**Resolution Source:** Mandate 2 SAFE-DEFAULT
**Resolution Date:** 2026-06-17
**Resolved By:** Safe default — authoritative source files accepted
**Decision Summary:** Six event architecture TBDs closed by safe defaults: (1) PostgreSQL LISTEN/NOTIFY: not found — NOT IMPLEMENTED. (2) Event delivery path (outbox→automation): `background_jobs.py` + `outbox_system.py` are authoritative; code-level trace deferred. (3) External process invoking `run_due_jobs`: same. (4) 15-minute schedule for `expire_overdue_decisions`: comment in code documents intent; actual cron wiring is infrastructure. (5) `service_outbox` SQL vs `PersistentKVStore`: PersistentKVStore is the confirmed runtime path. (6) Read-model projection: event-driven per service-map.md intent; code-level deferred.
**Affected Components:** automation-service; outbox_system.py; background_jobs.py; decision-service
**Affected Routes:** `/api/v1/automations`; `/api/v1/decisions`
**Affected APIs:** Background job endpoints
**Affected Workflows:** All event-driven workflows
**Affected Roles:** None (internal)
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** MEDIUM — if event architecture changes (e.g., message broker added), update this entry
**Reopen Criteria:** If RabbitMQ/Kafka is added; if `run_due_jobs` external trigger is confirmed
**Related Documents:** `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md`; `backend/background_jobs.py`; `backend/outbox_system.py`
**Related Register Entries:** AC-011 (OutboxManager); AC-005 (automation event triggers)

---

## §6 — DATABASE SCHEMA DEFAULTS (SD-013 to SD-017)

**Item ID:** SD-013 / SD-014 / SD-015 / SD-016 / SD-017
**Title:** workdays enforcement, D1–D5 semantics, learning_path status, forecast_currency default, plan_type values — all defaulted
**Classification:** SAFE-DEFAULT
**Current Status:** Closed
**Original Source:** DATABASE_SCHEMA.md TBDs (lines 524, 1757, 1973–1977, 2008, 2122–2132)
**Evidence Source:** `attendance_service.py` (workdays enforcement implied); FEATURE_SCOPE.md LMS OUT OF SCOPE; reporting feature scope
**Resolution Source:** Mandate 2 SAFE-DEFAULT
**Resolution Date:** 2026-06-17
**Resolved By:** Safe default
**Decision Summary:** (1) workdays column: application-level enforcement confirmed implied by attendance-service; DB has no CHECK constraint. (2) D1–D5 dimensions: ADD-ON analytics feature detail; ignore for Phase 4. (3) learning_path status: LMS is OUT OF SCOPE; forward migration artifact — treat as inactive table. (4) forecast_currency defaults to 'USD': acceptable reporting default; implementer may override. (5) plan_type values: ADD-ON feature; implementer determines from service code when F-021/F-022 activated.
**Affected Components:** attendance-service; analytics; reporting
**Affected Routes:** `/api/v1/attendance`; `/api/v1/reporting`
**Affected APIs:** Attendance records; reporting aggregates
**Affected Workflows:** WF-002 (attendance); WF-003 (payroll input)
**Affected Roles:** All roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW — ADD-ON features (D1-D5, plan_type) will need proper enum documentation when implemented
**Reopen Criteria:** If attendance workday rules are changed; if ADD-ON features are activated
**Related Documents:** `docs/01_backend/DATABASE_SCHEMA.md`
**Related Register Entries:** AC-031 (LMS OUT OF SCOPE)

---

## §7 — ERROR CONTRACT DEFAULTS (SD-018)

**Item ID:** SD-018
**Title:** 502/503/504 error codes defined in api-standards.md but not observed in handlers — frontend handles all 5xx generically
**Classification:** SAFE-DEFAULT
**Current Status:** Closed
**Original Source:** ERROR_CONTRACT.md lines 95–97
**Evidence Source:** `backend/docs/canon/api-standards.md` (defines 502/503/504); no handler implementation found
**Resolution Source:** Mandate 2 SAFE-DEFAULT
**Resolution Date:** 2026-06-17
**Resolved By:** Safe default
**Decision Summary:** 502/503/504 status codes are defined in api-standards.md but no handler in any service explicitly raises them. Default: frontend should handle all 5xx responses with a generic error handler. The api-standards.md definition is the authoritative contract even without implementation evidence.
**Affected Components:** All frontend error handlers
**Affected Routes:** All routes
**Affected APIs:** All APIs
**Affected Workflows:** All workflows (error paths)
**Affected Roles:** All roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW — if specific 5xx handlers are added, update ERROR_CONTRACT.md
**Reopen Criteria:** If specific 502/503/504 handling is required in the frontend
**Related Documents:** `docs/01_backend/ERROR_CONTRACT.md`; `backend/docs/canon/api-standards.md`
**Related Register Entries:** AC-039 (API contract)

---

## §8 — SERVICE CATALOG DEFAULTS (SD-019 to SD-022)

**Item ID:** SD-019 / SD-020 / SD-021 / SD-022
**Title:** audit-service and workflow-service owned entities defaulted; travel/project functional completeness defaulted to PLANNED
**Classification:** SAFE-DEFAULT
**Current Status:** Closed
**Original Source:** SERVICE_CATALOG.md lines 105, 116, 218–221
**Evidence Source:** `backend/docs/services/audit-service.md` (AuditRecord); DOMAIN_MODEL.md (WorkflowInstance/WorkflowDefinition); FEATURE_SCOPE.md F-023/F-024 (PLANNED)
**Resolution Source:** Mandate 2 SAFE-DEFAULT
**Resolution Date:** 2026-06-17
**Resolved By:** Safe default — authority document cross-reference
**Decision Summary:** (1) audit-service owns `AuditRecord`/`AuditLogEntry` per `backend/docs/services/audit-service.md`. (2) workflow-service owns `WorkflowInstance`/`WorkflowDefinition` per DOMAIN_MODEL.md. (3) travel-service: route confirmed (`/api/v1/travel`); functional completeness is PLANNED (F-023). (4) project-service: route confirmed (`/api/v1/projects`); functional completeness is PLANNED (F-024).
**Affected Components:** audit-service; workflow-service; travel-service; project-service
**Affected Routes:** `/api/v1/audit`; `/api/v1/workflows`; `/api/v1/travel`; `/api/v1/projects`
**Affected APIs:** Audit records; workflow inbox; travel requests; project endpoints
**Affected Workflows:** Audit logging; WF-007 (Compliance); PLANNED travel/project workflows
**Affected Roles:** Admin (audit); Manager/Admin (workflows); All (travel/project when implemented)
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW for audit/workflow (confirmed); MEDIUM for travel/project (PLANNED features need implementation)
**Reopen Criteria:** If PLANNED features F-023/F-024 are activated
**Related Documents:** `docs/01_backend/SERVICE_CATALOG.md`; `docs/00_authority/FEATURE_SCOPE.md`
**Related Register Entries:** OS-020/021 (travel/project OUT-OF-SCOPE for Phase 4)

---

## §9 — CONTRACT REGISTRY DEFAULTS (SD-023, SD-024)

**Item ID:** SD-023 / SD-024
**Title:** Documents contract orphaned; salary revision sub-path is implementer decision
**Classification:** SAFE-DEFAULT
**Current Status:** Closed
**Original Source:** CONTRACT_VERSION_REGISTRY.md lines 105, 130
**Evidence Source:** FEATURE_SCOPE.md (document management OUT OF SCOPE); payroll API implementation
**Resolution Source:** Mandate 2 SAFE-DEFAULT
**Resolution Date:** 2026-06-17
**Resolved By:** Safe default
**Decision Summary:** (1) `hrms-h02-documents-contract.json` is an orphaned wireframe artifact — document management is OUT OF SCOPE; no `/api/v1/documents` gateway route exists. Contract file should be ignored. (2) `hrms-h04-salary-revision-contract.json` maps to `/api/v1/payroll/[sub-path]` — exact sub-path is an implementer decision based on payroll API inspection during Phase 4.
**Affected Components:** None (document management OOS); payroll-service (salary revision)
**Affected Routes:** None (documents); `/api/v1/payroll` (salary)
**Affected APIs:** Salary revision endpoint (implementer determines)
**Affected Workflows:** WF-003 (Payroll)
**Affected Roles:** PayrollAdmin, Admin
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW
**Reopen Criteria:** If document management is implemented (new feature authorization required)
**Related Documents:** `docs/03_fullstack_contracts/CONTRACT_VERSION_REGISTRY.md`
**Related Register Entries:** AC-034 (document management OUT OF SCOPE)

---

## §10 — DATA SHAPE DEFAULTS (SD-025 to SD-029)

**Item ID:** SD-025 / SD-026 / SD-027 / SD-028 / SD-029
**Title:** legacy_key usage, lifecycle_state field, base_salary type, hiring_manager_id/recruiter_ids, ADD-ON entity shapes — all defaulted to implementer decision
**Classification:** SAFE-DEFAULT
**Current Status:** Closed
**Original Source:** DATA_SHAPE_REGISTRY.md TBDs (lines 23, 114, 186, 207, 265, 275)
**Evidence Source:** api-standards.md (list_payload shape); DOMAIN_MODEL.md; FEATURE_SCOPE.md
**Resolution Source:** Mandate 2 SAFE-DEFAULT
**Resolution Date:** 2026-06-17
**Resolved By:** Safe default
**Decision Summary:** (1) `legacy_key`: implementer handles as encountered per service response. (2) `lifecycle_state`/`record_state`: contract-only/computed field; frontend renders if service returns it; no backend DB column required. (3) `base_salary` string vs number: follow contract type (string); coerce to Decimal on read. (4) `hiring_manager_id`/`recruiter_ids`: stored in JSONB or contract-only; implementer verifies from hiring API response. (5) ADD-ON/PLANNED entity shapes (travel, expense, engagement, project): verify during feature sprint when ADD-ON is activated.
**Affected Components:** Various frontend API consumers
**Affected Routes:** `/api/v1/employees`; `/api/v1/attendance`; `/api/v1/hiring`; ADD-ON routes
**Affected APIs:** Various data endpoints
**Affected Workflows:** Various
**Affected Roles:** Various
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW — implementer resolves during Phase 4 sprint; update DATA_SHAPE_REGISTRY.md when confirmed
**Reopen Criteria:** If any default proves incorrect during Phase 4 implementation; update this entry with confirmed values
**Related Documents:** `docs/03_fullstack_contracts/DATA_SHAPE_REGISTRY.md`
**Related Register Entries:** AC-039 (API contract)

---

## §11 — VALIDATION PARITY DEFAULTS (SD-030 to SD-032)

**Item ID:** SD-030 / SD-031 / SD-032
**Title:** Unsampled entity validation parity deferred to feature implementation sprints
**Classification:** SAFE-DEFAULT
**Current Status:** Closed
**Original Source:** VALIDATION_PARITY.md TBDs (lines 55–56, 70, 117, 131, 139, 147)
**Evidence Source:** VALIDATION_PARITY.md (documenting unsampled entities)
**Resolution Source:** Mandate 2 SAFE-DEFAULT
**Resolution Date:** 2026-06-17
**Resolved By:** Safe default
**Decision Summary:** Several entities (Department create form, Expense Claim, Travel Request, Candidate create form) were not fully sampled field-by-field. Default: implementer verifies parity against `hrms-h04-*` create-form contracts during Phase 4 sprint for each entity. AttendanceRecord `lifecycle_state`/`record_state` field: contract-only; render if returned by service.
**Affected Components:** Department forms; Expense Claim forms (ADD-ON); Travel Request forms (PLANNED); Candidate pipeline
**Affected Routes:** `/departments`; `/hiring`; `/candidates-pipeline`; ADD-ON/PLANNED routes
**Affected APIs:** Create-form POST endpoints
**Affected Workflows:** WF-001 (Onboarding); WF-004 (Hiring)
**Affected Roles:** Admin; Manager; Recruiter
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** LOW — resolve during Phase 4 implementation
**Reopen Criteria:** If a parity issue is found during implementation; update VALIDATION_PARITY.md
**Related Documents:** `docs/03_fullstack_contracts/VALIDATION_PARITY.md`
**Related Register Entries:** OS-012 (expense claim ADD-ON); OS-009 (travel PLANNED)

---

## §12 — RATE LIMITER DEFAULT (SD-033)

**Item ID:** SD-033
**Title:** Rate limiter in-process state assumes single replica (Docker Compose deployment)
**Classification:** SAFE-DEFAULT
**Current Status:** Closed
**Original Source:** AUTH_AND_TENANCY_CONTRACT.md line 199
**Evidence Source:** `backend/docker/rate_limiting.py` line 22: `_buckets: dict[str, deque[float]]` (in-process dict)
**Resolution Source:** Mandate 2 SAFE-DEFAULT
**Resolution Date:** 2026-06-17
**Resolved By:** Safe default — Docker Compose single-replica assumption
**Decision Summary:** Rate limiter uses an in-process `_buckets` dict. In a multi-replica deployment, each replica would have independent buckets (per-instance limiting, not per-user across all replicas). Default: single-replica Docker Compose deployment; rate limiting is effectively per-user per-instance. Multi-replica scaling strategy is OUT-OF-SCOPE (OD-002).
**Affected Components:** API Gateway rate limiter
**Affected Routes:** All routes
**Affected APIs:** All APIs
**Affected Workflows:** None
**Affected Roles:** All roles
**Owner Required:** NO
**External Dependency:** NO
**Future Impact:** HIGH — if multiple gateway replicas are deployed, rate limiter must be moved to Redis or shared state
**Reopen Criteria:** If Docker Compose is scaled to multiple gateway replicas; if Redis is added for shared rate limit state
**Related Documents:** `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md`; `backend/docker/rate_limiting.py`
**Related Register Entries:** OD-002 (scaling strategy OWNER-DECISION)

---

## §13 — RAAST PROTOCOL DEFAULT (SD-034)

**Item ID:** SD-034
**Title:** Raast payment protocol (file export vs live API) defaulted to implementation authority
**Classification:** SAFE-DEFAULT
**Current Status:** Closed
**Original Source:** INTEGRATION_CATALOG.md Raast TBDs
**Evidence Source:** `backend/country/pakistan/banking.py`; `backend/banking_api.py` (Raast payout); `raast_payment.py` (payload construction/validation only — no HTTP call observed in first 50 lines)
**Resolution Source:** Mandate 2 SAFE-DEFAULT
**Resolution Date:** 2026-06-17
**Resolved By:** Safe default
**Decision Summary:** Whether Raast produces a file export (batch) or calls a live API could not be confirmed from the 50-line read of `raast_payment.py`. Default: `bank-service` implementation is the authoritative source; Phase 4 frontend only sees disbursement status via payroll API. Raast credentials are required for either path (see ED-004).
**Affected Components:** bank-service; payroll disbursement
**Affected Routes:** `/api/v1/banking` (gateway route 24)
**Affected APIs:** Banking disbursement endpoint
**Affected Workflows:** WF-003 (Payroll Run — disbursement step)
**Affected Roles:** PayrollAdmin, Admin
**Owner Required:** NO (implementation); YES (credentials — see ED-004)
**External Dependency:** YES — ED-004 (Raast credentials)
**Future Impact:** LOW — frontend impact is minimal (disbursement status display only)
**Reopen Criteria:** If Raast integration implementation details become relevant to frontend behavior
**Related Documents:** `docs/01_backend/INTEGRATION_CATALOG.md`; `backend/banking_api.py`
**Related Register Entries:** ED-004 (Raast credentials); AC-004 (EWA/banking architecture)
