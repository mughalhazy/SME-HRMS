# FINAL CLASSIFIED REGISTER

Layer: Project Memory
Status: Active
Created: 2026-06-18
Last Updated: 2026-06-20
Authority: This file is the single entry point for future AI sessions before any audit, redesign, frontend work, backend work, deployment work, or gap analysis.

---

## USAGE RULE

Read this file first. If an item is listed here, do not re-investigate it. Update the entry if evidence changes. Do not create duplicate items.

---

## CLASSIFICATION LEGEND

| Class | Register | Meaning |
|-------|----------|---------|
| AUTO-CLOSED | AUTO_CLOSED_REGISTER.md | Proven from repository evidence, authority docs, or contracts |
| SAFE-DEFAULT | SAFE_DEFAULT_REGISTER.md | Resolved by adopting a safe, evidence-supported default |
| OUT-OF-SCOPE | OUT_OF_SCOPE_REGISTER.md | Intentionally deferred, future phase, or regional expansion |
| OWNER-DECISION | OWNER_DECISION_REGISTER.md | Requires a genuine product/business/legal owner decision |
| EXTERNAL-DEPENDENCY | EXTERNAL_DEPENDENCY_REGISTER.md | Requires external credentials, registration, or vendor onboarding |

---

## MASTER INDEX

### AUTO-CLOSED (84 items)

| ID | Title | Evidence Source | Register Entry |
|----|-------|----------------|----------------|
| AC-001 | Gateway routes 1–21 confirmed | `backend/api-gateway/routes.py`, `gateway-routes.json` | AUTO_CLOSED_REGISTER §1 |
| AC-002 | Gateway routes 22–25 confirmed (compliance, decisions, banking, whatsapp) | `routes.py` lines 52–55; `gateway-routes.json` lines 25–28 | AUTO_CLOSED_REGISTER §1 |
| AC-003 | Non-standard envelope for routes 22–25 | Source code: `{status, data, service}` | AUTO_CLOSED_REGISTER §1 |
| AC-004 | EWA is in-process in payroll-service (no standalone container) | `backend/services/finance/ewa.py`; `payroll_service.py` line 392 | AUTO_CLOSED_REGISTER §2 |
| AC-005 | Automation engine is event-triggered only | `backend/automation_contract.py` | AUTO_CLOSED_REGISTER §3 |
| AC-006 | Helpdesk ticket priority enum confirmed | `helpdesk_service.py` line 128 | AUTO_CLOSED_REGISTER §4 |
| AC-007 | Helpdesk ticket status enum confirmed | `helpdesk_service.py` line 127 | AUTO_CLOSED_REGISTER §4 |
| AC-008 | Settings handler is in-memory stub in service_runtime.py | `service_runtime.py` lines 236–254 | AUTO_CLOSED_REGISTER §5 |
| AC-009 | /health and /ready endpoints confirmed | `service_runtime.py` line 410 | AUTO_CLOSED_REGISTER §6 |
| AC-010 | CircuitBreaker usage confirmed | `resilience.py`; `hiring_service/service.py`; `supervisor_engine.py` | AUTO_CLOSED_REGISTER §7 |
| AC-011 | OutboxManager confirmed | `backend/outbox_system.py` | AUTO_CLOSED_REGISTER §8 |
| AC-012 | 007_event_outbox.sql confirmed | `backend/deployment/migrations/007_event_outbox.sql` | AUTO_CLOSED_REGISTER §8 |
| AC-013 | All 31 capabilities confirmed from canon | `backend/docs/canon/security-model.md` lines 16–48 | AUTO_CLOSED_REGISTER §9 |
| AC-014 | 5 roles confirmed | `api_gateway_service.py` JWT claims; `_ROUTE_ROLE_MAP` | AUTO_CLOSED_REGISTER §9 |
| AC-015 | Requisition scope not in auth-service; Recruiter uses Department scope | `service.py` line 521 `assign_role_binding` | AUTO_CLOSED_REGISTER §9 |
| AC-016 | `/api/v1/roles` and `/api/v1/org` served by employee-service | `employee_api.py`; C-004 | AUTO_CLOSED_REGISTER §10 |
| AC-017 | `/api/v1/financial-wellness` does not exist as gateway route | No route in `routes.py`; EWA is in-process | AUTO_CLOSED_REGISTER §2 |
| AC-018 | `/api/v1/analytics` is not the correct prefix; correct is `/api/v1/reporting` | `routes.py` line 12 | AUTO_CLOSED_REGISTER §1 |
| AC-019 | TypeScript files in employee-service are dead code (zero Python callers) | grep confirmed; 43 files archived | AUTO_CLOSED_REGISTER §11 |
| AC-020 | TypeScript files in settings-service are dead code | grep confirmed; 6 files archived | AUTO_CLOSED_REGISTER §11 |
| AC-021 | TypeScript files in middleware are dead code | grep confirmed; 11 files archived | AUTO_CLOSED_REGISTER §11 |
| AC-022 | Python tests test Python behavior only; TypeScript cannot be imported by Python | All 80+ test files are .py | AUTO_CLOSED_REGISTER §11 |
| AC-023 | No general-purpose cache layer exists | ADR-001 §4; cache.service.ts is dead code | AUTO_CLOSED_REGISTER §12 |
| AC-024 | Dead function `_employee_domain_departments()` already deleted | grep: no matches in backend/docker/ | AUTO_CLOSED_REGISTER §13 |
| AC-025 | "Aura HRMS API" title already updated to "Meridian HCM API" | `api_gateway_service.py` line 205 | AUTO_CLOSED_REGISTER §13 |
| AC-026 | `backend/attendance_service/` (dir) and `services/attendance_service.py` (file) both valid | Code inspection; AttendanceService confirmed | AUTO_CLOSED_REGISTER §14 |
| AC-027 | OS artifact `(C) Phoenix LiteOS.lnk` already absent | Root directory scan | AUTO_CLOSED_REGISTER §13 |
| AC-028 | Root `.gitignore` already exists with Python + Node patterns | File read confirmed | AUTO_CLOSED_REGISTER §13 |
| AC-029 | Root `README.md` already exists with accurate Meridian HCM content | File read confirmed | AUTO_CLOSED_REGISTER §13 |
| AC-030 | Frontend confirmed at `backend/ui/` through Phase 4 (OCR-001) | DETERMINISM_CERTIFICATION_REPORT; C-003 | AUTO_CLOSED_REGISTER §15 |
| AC-031 | Native mobile app confirmed OUT OF SCOPE | `FEATURE_SCOPE.md` OUT OF SCOPE section | AUTO_CLOSED_REGISTER §16 |
| AC-032 | Shift/Roster scheduling confirmed OUT OF SCOPE | No service, schema, or gateway route | AUTO_CLOSED_REGISTER §16 |
| AC-033 | LMS confirmed OUT OF SCOPE | No learning-service in docker-compose.yml | AUTO_CLOSED_REGISTER §16 |
| AC-034 | Document Management confirmed OUT OF SCOPE | No `/api/v1/documents` route; no service | AUTO_CLOSED_REGISTER §16 |
| AC-035 | All 21 product decisions STABLE | PRODUCT_DECISION_REGISTER.md | AUTO_CLOSED_REGISTER §17 |
| AC-036 | Navigation structure (21 routes) STABLE | PRODUCT_DECISION_REGISTER.md §2 | AUTO_CLOSED_REGISTER §17 |
| AC-037 | Gateway RBAC (4 restricted routes) STABLE | `_ROUTE_ROLE_MAP` confirmed | AUTO_CLOSED_REGISTER §17 |
| AC-038 | Dashboard composition STABLE | PRODUCT_DECISION_REGISTER.md §5 | AUTO_CLOSED_REGISTER §17 |
| AC-039 | API contract (versioning, auth, rate limiting) STABLE | `api_gateway_service.py` confirmed | AUTO_CLOSED_REGISTER §18 |
| AC-040 | All 8 workflows (WF-001 to WF-008) classified | PRODUCT_WORKFLOWS.md; FULLSTACK_STITCHING_CONTRACT.md | AUTO_CLOSED_REGISTER §19 |
| AC-041 | employee_api.py 14 handlers confirmed | `backend/employee_api.py` lines 1–124 | AUTO_CLOSED_REGISTER §10 |
| AC-042 | `POST /api/v1/payroll/run` confirmed | `payroll_api.py`; tests confirmed | AUTO_CLOSED_REGISTER §10 |
| AC-043 | 13 reporting endpoints confirmed | `backend/tests/test_reporting_analytics.py` | AUTO_CLOSED_REGISTER §10 |
| AC-044 | WhatsApp gateway route 25 confirmed (stale TBD fixed) | `routes.py` line 55 | AUTO_CLOSED_REGISTER §20 |
| AC-045 | Helpdesk priority/status DB TBD resolved (stale) | `helpdesk_service.py` lines 127–128 | AUTO_CLOSED_REGISTER §20 |
| AC-046 | attendance_service.py existence confirmed (stale TBD fixed) | `backend/services/attendance_service.py` read | AUTO_CLOSED_REGISTER §20 |
| AC-047 | CONTRACT_VERSION_REGISTRY routes 22–25 confirmed (stale TBD fixed) | Phase 2.8 TR-003 to TR-006 | AUTO_CLOSED_REGISTER §20 |
| AC-048 | Roles contracts use `/api/v1/employees` not `/api/v1/auth` (stale TBD fixed) | C-004; employee_api.py `post_roles` | AUTO_CLOSED_REGISTER §20 |
| AC-049 | G-020 to G-024 Settings chrome-only (no backend needed) | No confirmed API endpoints; correct implementation | AUTO_CLOSED_REGISTER §21 |
| AC-050 | G-030 Employee draft — implementation detail | No dedicated workflow needed | AUTO_CLOSED_REGISTER §21 |
| AC-051 | G-031 Employee suspended — Admin PATCH via edit form | Role + API confirmed | AUTO_CLOSED_REGISTER §21 |
| AC-052 | G-032 Employee terminated — Admin PATCH via edit form | Role + API confirmed | AUTO_CLOSED_REGISTER §21 |
| AC-053 | G-033 WorkflowInstance intermediate steps — implementation detail | Approval inbox handles pending items | AUTO_CLOSED_REGISTER §21 |
| AC-054 | G-037 Compensation entities — surfaced through employee profile | Employee profile Compensation tab | AUTO_CLOSED_REGISTER §21 |
| AC-055 | G-038 JobPosition — job postings cover open positions | No separate screen needed | AUTO_CLOSED_REGISTER §21 |
| AC-056 | G-040 to G-044 API endpoint uncertainty — implementation details | Fallback patterns documented | AUTO_CLOSED_REGISTER §21 |
| AC-057 | G-050 Manager payroll dept-filtered — scope enforcement handles | API scope enforcement confirmed | AUTO_CLOSED_REGISTER §21 |
| AC-058 | G-051 Employee payslip deep-link — Dashboard + Profile path | ROLE_EXPERIENCE_MATRIX documents path | AUTO_CLOSED_REGISTER §21 |
| AC-059 | G-052 Recruiter leave (own only) — documented in matrix | ROLE_EXPERIENCE_MATRIX | AUTO_CLOSED_REGISTER §21 |
| AC-060 | G-053 Compliance role-based actions — implementation detail | Render per role claim | AUTO_CLOSED_REGISTER §21 |
| AC-061 | G-062 Banking non-standard envelope — documented C-001 | FRONTEND_API_DEPENDENCY_MAP; C-001 | AUTO_CLOSED_REGISTER §21 |
| AC-062 | G-070 PROJECT_CHARTER stale note — routes confirmed | Routes 22–25 confirmed Phase 2.8 | AUTO_CLOSED_REGISTER §20 |
| AC-063 | G-071 FEATURE_SCOPE.md stale TBD markers — resolved Phase 3.25 | Phase 3.25 report | AUTO_CLOSED_REGISTER §20 |
| AC-064 | G-072 FULLSTACK_STITCHING_CONTRACT stale gaps table — resolved | T-001 to T-015 traces authoritative | AUTO_CLOSED_REGISTER §20 |
| AC-065 | WF-001 Document Collection step — OUT OF SCOPE | Document management OUT OF SCOPE | AUTO_CLOSED_REGISTER §19 |
| AC-066 | WF-002 Calendar Updated — attendance-service reads leave records | Standard leave→attendance data flow | AUTO_CLOSED_REGISTER §19 |
| AC-067 | WF-002 No OnLeave employee status — leave record status = Approved | No OnLeave status in codebase | AUTO_CLOSED_REGISTER §19 |
| AC-068 | WF-003 No approval step — direct Draft→Processed | No payroll approval workflow wired | AUTO_CLOSED_REGISTER §19 |
| AC-069 | DG-001 grade_bands table — RESOLVED (migration 014) | `014_schema_integrity_fixes.sql` §1 | AUTO_CLOSED_REGISTER §22 |
| AC-070 | DG-002 Multi-tenancy FK pattern — RESOLVED (migration 014) | `014_schema_integrity_fixes.sql` §2 | AUTO_CLOSED_REGISTER §22 |
| AC-071 | All 19 backend gaps (DG/AG/ARG/EG) — RESOLVED Phase 2 | BACKEND_GAP_REGISTER.md | AUTO_CLOSED_REGISTER §22 |
| AC-072 | Phase 3 frontend authority (12 docs) — COMPLETE | docs/03_frontend_authority/ | AUTO_CLOSED_REGISTER §23 |
| AC-073 | 55 frontend components identified with archetypes | FRONTEND_COMPONENT_INVENTORY.md | AUTO_CLOSED_REGISTER §23 |
| AC-074 | 55 frontend routes defined | FRONTEND_ROUTE_CATALOG.md | AUTO_CLOSED_REGISTER §23 |
| AC-075 | Decision Cards: in-memory, not persisted; gateway route 23 | `decision_engine.py`; `routes.py` line 53 | AUTO_CLOSED_REGISTER §2 |
| AC-076 | `backend/.github/workflows/` CI files never execute (wrong location) | GitHub Actions only reads root `.github/workflows/` | AUTO_CLOSED_REGISTER §13 |
| AC-077 | All 19 DB migrations (001–015) confirmed | Glob of migrations directory | AUTO_CLOSED_REGISTER §22 |
| AC-078 | Payroll to bank happy path tested | `test_payroll_to_bank_happy_path.py` | AUTO_CLOSED_REGISTER §10 |
| AC-079 | Scope enforcement model confirmed | service.py `_service_scopes_for_user`; DOMAIN_MODEL.md | AUTO_CLOSED_REGISTER §9 |
| AC-080 | ATS inbound integration OUT OF SCOPE | integration-service (F-022) is outbound only | AUTO_CLOSED_REGISTER §16 |
| AC-081 | Time tracking beyond attendance OUT OF SCOPE | No time-tracking service | AUTO_CLOSED_REGISTER §16 |
| AC-082 | Video interview integration OUT OF SCOPE | No service or contract | AUTO_CLOSED_REGISTER §16 |
| AC-083 | OAQ-001 to OAQ-010 — zero frontend impact | PRODUCT_DECISION_REGISTER.md §7 | AUTO_CLOSED_REGISTER §17 |
| AC-084 | compliance reports route 22 confirmed (stale CONTRACT_VERSION_REGISTRY note fixed) | `routes.py` line 52; TR-003 | AUTO_CLOSED_REGISTER §20 |
| AC-085 | Phase 3.5 L0 FROZEN — 13 Phase 3 authority docs reviewed; 0 blocking gaps found; L0 FROZEN verdict issued 2026-06-20 | `FRONTEND_GAP_REGISTER.md` (43 items, 0 blocking); `POST_COLLAPSE_FRONTEND_READINESS.md` (7/7 gates PASS); `DETERMINISM_CERTIFICATION_REPORT.md` (FULLY DETERMINED) | AUTO_CLOSED_REGISTER §24 |
| AC-086 | L0 output pack created — 4 frozen authority files in `docs/03_frontend_authority/` (L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md, L0_ROUTE_SCREEN_WORKFLOW_MATRIX.md, L0_DESIGN_CONSTRAINTS_FOR_CLAUDE_DESIGN.md, L0_CLAUDE_DESIGN_BRIEF.md) | All 4 files created 2026-06-20; L0 freeze confirmed complete | AUTO_CLOSED_REGISTER §24 |

---

### SAFE-DEFAULT (34 items)

| ID | Title | Default Adopted | Register Entry |
|----|-------|----------------|----------------|
| SD-001 | TypeScript archive (43 employee-service files) | Moved to `backend/docs/system/archive/typescript-employee-service/` | SAFE_DEFAULT_REGISTER §1 |
| SD-002 | TypeScript archive (6 settings-service files) | Moved to `backend/docs/system/archive/typescript-settings-service/` | SAFE_DEFAULT_REGISTER §1 |
| SD-003 | TypeScript archive (11 middleware files) | Moved to `backend/docs/system/archive/typescript-middleware/` | SAFE_DEFAULT_REGISTER §1 |
| SD-004 | CI workflow archive (build.yml, deploy.yml, test.yml) | Moved to `backend/docs/system/archive/dead-ci-workflows/` | SAFE_DEFAULT_REGISTER §2 |
| SD-005 | OpenAPI contact email updated | `support@aura-hrms.internal` → `support@meridian-hcm.internal` | SAFE_DEFAULT_REGISTER §3 |
| SD-006 | Cross-service dependency trace | service-map.md + docker-compose.yml are the authoritative dependency specs | SAFE_DEFAULT_REGISTER §4 |
| SD-007 | PostgreSQL LISTEN/NOTIFY | Not implemented — not found in any file reviewed | SAFE_DEFAULT_REGISTER §5 |
| SD-008 | Event delivery / outbox-to-automation path | background_jobs.py + outbox_system.py are authoritative; code-level trace deferred | SAFE_DEFAULT_REGISTER §5 |
| SD-009 | External process invoking run_due_jobs | background_jobs.py is authoritative; wiring detail deferred | SAFE_DEFAULT_REGISTER §5 |
| SD-010 | 15-minute schedule for expire_overdue_decisions | Comment in code documents intent; actual cron wiring is infrastructure concern | SAFE_DEFAULT_REGISTER §5 |
| SD-011 | service_outbox SQL tables vs PersistentKVStore | PersistentKVStore is the confirmed runtime path; SQL tables are migration artifacts | SAFE_DEFAULT_REGISTER §5 |
| SD-012 | Read-model projection update mechanism | Event-driven per service-map.md design intent; code-level verification deferred | SAFE_DEFAULT_REGISTER §5 |
| SD-013 | workdays column application-level enforcement | attendance-service enforces; DB has no CHECK constraint | SAFE_DEFAULT_REGISTER §6 |
| SD-014 | D1–D5 dimension semantics | ADD-ON analytics feature detail; semantic mapping is implementer concern | SAFE_DEFAULT_REGISTER §6 |
| SD-015 | learning_path status allowed values | LMS is OUT OF SCOPE; forward migration artifact; ignore | SAFE_DEFAULT_REGISTER §6 |
| SD-016 | forecast_currency USD default | Reporting feature default; implementer may override | SAFE_DEFAULT_REGISTER §6 |
| SD-017 | plan_type allowed values | ADD-ON feature; implementer determines from service code | SAFE_DEFAULT_REGISTER §6 |
| SD-018 | 502/503/504 error handlers | Defined in api-standards.md; not yet observed in handlers; frontend handles all 5xx generically | SAFE_DEFAULT_REGISTER §7 |
| SD-019 | audit-service owned entities | AuditRecord/AuditLogEntry per backend/docs/services/audit-service.md | SAFE_DEFAULT_REGISTER §8 |
| SD-020 | workflow-service owned entities | WorkflowInstance/WorkflowDefinition per DOMAIN_MODEL.md | SAFE_DEFAULT_REGISTER §8 |
| SD-021 | travel-service functional completeness | PLANNED (F-023); route confirmed; implementation is future scope | SAFE_DEFAULT_REGISTER §8 |
| SD-022 | project-service functional completeness | PLANNED (F-024); route confirmed; implementation is future scope | SAFE_DEFAULT_REGISTER §8 |
| SD-023 | Documents contract orphaned file | Document management OUT OF SCOPE; contract file is wireframe artifact | SAFE_DEFAULT_REGISTER §9 |
| SD-024 | salary revision exact sub-path | `/api/v1/payroll/[sub-path]` — implementer determines from payroll API | SAFE_DEFAULT_REGISTER §9 |
| SD-025 | legacy_key usage per-service | Implementer handles as encountered per service response | SAFE_DEFAULT_REGISTER §10 |
| SD-026 | lifecycle_state / record_state field on AttendanceRecord | Contract-only/computed field; frontend renders if service returns it | SAFE_DEFAULT_REGISTER §10 |
| SD-027 | base_salary string vs number in API | Follow contract type (string); coerce on read | SAFE_DEFAULT_REGISTER §10 |
| SD-028 | hiring_manager_id / recruiter_ids not in DB DDL | Stored in JSONB or contract-only fields; implementer handles | SAFE_DEFAULT_REGISTER §10 |
| SD-029 | ADD-ON/PLANNED entity shape TBDs (travel, expense, engagement) | Not Phase 4 core; implementer verifies during feature sprint | SAFE_DEFAULT_REGISTER §10 |
| SD-030 | Unsampled entity validation parity (Department create, Expense Claim, etc.) | Implementer verifies during feature implementation | SAFE_DEFAULT_REGISTER §11 |
| SD-031 | Expense claim backend validation parity | Implementer verifies create-expense-claim contract during F-021 sprint | SAFE_DEFAULT_REGISTER §11 |
| SD-032 | Travel request validation parity | PLANNED (F-023); verify during feature sprint | SAFE_DEFAULT_REGISTER §11 |
| SD-033 | Rate limiter in-process per-replica state | Single-replica Docker Compose deployment assumed; scaling deferred | SAFE_DEFAULT_REGISTER §12 |
| SD-034 | Raast protocol (file export vs live API) | Deployment-specific; bank-service implementation is authoritative | SAFE_DEFAULT_REGISTER §13 |

---

### OUT-OF-SCOPE (24 items)

| ID | Title | Reason | Register Entry |
|----|-------|--------|----------------|
| OS-001 | Frontend relocation `backend/ui/` → `frontend/` | Deferred post-Phase 4; C-003 confirms current location | OUT_OF_SCOPE_REGISTER §1 |
| OS-002 | CI workflow activation / migration to root | Infrastructure decision; not current development scope | OUT_OF_SCOPE_REGISTER §2 |
| OS-003 | CI runner type + DB seeding strategy | Infrastructure; not blocking development | OUT_OF_SCOPE_REGISTER §2 |
| OS-004 | Docker CLI availability on CI runner | Infrastructure; not blocking development | OUT_OF_SCOPE_REGISTER §2 |
| OS-005 | QuickBooks integration credentials | ADD-ON (F-021 expense-service); not Phase 4 scope | OUT_OF_SCOPE_REGISTER §3 |
| OS-006 | SAP integration credentials | ADD-ON; not Phase 4 scope | OUT_OF_SCOPE_REGISTER §3 |
| OS-007 | G-001 Shift Roster screen | Shift/roster scheduling confirmed OUT OF SCOPE | OUT_OF_SCOPE_REGISTER §4 |
| OS-008 | G-002 Documents List screen | Document management confirmed OUT OF SCOPE | OUT_OF_SCOPE_REGISTER §4 |
| OS-009 | G-003/G-004 Travel Request screens | PLANNED (F-023); not Phase 4 core | OUT_OF_SCOPE_REGISTER §4 |
| OS-010 | G-005 Project Management screens | PLANNED (F-024); not Phase 4 core | OUT_OF_SCOPE_REGISTER §4 |
| OS-011 | G-010/G-011 Performance Review screens | ADD-ON (F-017); deferred | OUT_OF_SCOPE_REGISTER §5 |
| OS-012 | G-012/G-013/G-014 Expense Claim screens | ADD-ON (F-021); deferred | OUT_OF_SCOPE_REGISTER §5 |
| OS-013 | G-015/G-016 Engagement / Survey screens | ADD-ON (F-018); deferred | OUT_OF_SCOPE_REGISTER §5 |
| OS-014 | G-017 Helpdesk screen | ADD-ON (F-019); deferred | OUT_OF_SCOPE_REGISTER §5 |
| OS-015 | G-018 Performance Dashboard tab | ADD-ON (F-017); deferred | OUT_OF_SCOPE_REGISTER §5 |
| OS-016 | G-034/G-035 ReviewCycle / Goal / Feedback entities | ADD-ON (F-017); no Phase 4 UI | OUT_OF_SCOPE_REGISTER §5 |
| OS-017 | G-036 Survey entities | ADD-ON (F-018); no Phase 4 UI | OUT_OF_SCOPE_REGISTER §5 |
| OS-018 | G-060 Standalone WhatsApp screen | Out of scope by design; WhatsApp is backend integration only | OUT_OF_SCOPE_REGISTER §6 |
| OS-019 | G-061 Standalone Banking screen | Out of scope by design; banking surfaces in payroll detail only | OUT_OF_SCOPE_REGISTER §6 |
| OS-020 | F-023 Travel Management (scaffolded only) | PLANNED; not Phase 4 core | OUT_OF_SCOPE_REGISTER §7 |
| OS-021 | F-024 Project Management (scaffolded only) | PLANNED; not Phase 4 core | OUT_OF_SCOPE_REGISTER §7 |
| OS-022 | WF-005 Performance Review workflow | ADD-ON (F-017); deferred | OUT_OF_SCOPE_REGISTER §5 |
| OS-023 | WF-006 Expense Claim workflow | ADD-ON (F-021); deferred | OUT_OF_SCOPE_REGISTER §5 |
| OS-024 | Biometric device vendor specifics and transport mechanism | Implementation detail for attendance-service; not Phase 4 frontend concern | OUT_OF_SCOPE_REGISTER §8 |

---

### OWNER-DECISION (3 items)

| ID | Title | Decision Type | Register Entry |
|----|-------|--------------|----------------|
| OD-001 | Commercial launch date and customer terms | Commercial/business | OWNER_DECISION_REGISTER §1 |
| OD-002 | Scaling strategy (Docker Compose vs. Kubernetes/cloud) | Commercial/infrastructure | OWNER_DECISION_REGISTER §2 |
| OD-003 | Data residency requirements beyond Pakistan | Legal/regulatory | OWNER_DECISION_REGISTER §3 |

---

### EXTERNAL-DEPENDENCY (5 items)

| ID | Title | Dependency Type | Register Entry |
|----|-------|----------------|----------------|
| ED-001 | FBR statutory compliance credentials | Regulatory — Pakistan Federal Board of Revenue | EXTERNAL_DEPENDENCY_REGISTER §1 |
| ED-002 | EOBI statutory compliance credentials | Regulatory — Employees' Old-Age Benefits Institution | EXTERNAL_DEPENDENCY_REGISTER §2 |
| ED-003 | PESSI/SESSI statutory compliance credentials | Regulatory — Provincial Employees Social Security Institution | EXTERNAL_DEPENDENCY_REGISTER §3 |
| ED-004 | Raast payment network credentials | Payment — State Bank of Pakistan Raast instant payment | EXTERNAL_DEPENDENCY_REGISTER §4 |
| ED-005 | WhatsApp Business API account and credentials | Vendor account — Meta WhatsApp Business API | EXTERNAL_DEPENDENCY_REGISTER §5 |

---

## TOTALS

| Class | Count |
|-------|-------|
| AUTO-CLOSED | 86 |
| SAFE-DEFAULT | 34 |
| OUT-OF-SCOPE | 24 |
| OWNER-DECISION | 3 |
| EXTERNAL-DEPENDENCY | 5 |
| **Total** | **152** |

---

## PHASE HISTORY

| Date | Event | Impact on Register |
|------|-------|--------------------|
| 2026-06-18 | Memory layer established (Phase M1) | Initial 150 items across 5 classes |
| 2026-06-20 | Phase 3.5 L0 FROZEN completed | +2 AUTO-CLOSED (AC-085, AC-086); total 152 |
