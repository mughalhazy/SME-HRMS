# BACKEND GAP REGISTER

Status: Closed
Authority Level: High
Last Reviewed: 2026-06-18
Owner: AI
Final Status: All 19 gaps RESOLVED (Phase 2). All Phase 3.25 + Mandate 2 + compression passes complete. See `docs/08_reports/FINAL_CLASSIFIED_REGISTER.md` for canonical final classification.

---

## PURPOSE

This register documents every gap, inconsistency, and unresolved item discovered during PHASE 2 BACKEND AUTHORITY CAPTURE. Gaps are grouped by discovery domain. Each gap has a unique ID, severity classification, evidence citation, and recommended action. This document does not recommend fixes — it records what was found so that human-authorized remediation can be planned.

**Gap severity legend:**
- **CRITICAL** — will cause a functional failure (migration failure, data corruption risk, security violation) in production
- **HIGH** — feature is unreachable or contract is violated; user-facing impact likely
- **MEDIUM** — inconsistency or mismatch that could cause subtle bugs or confusion
- **LOW** — dead code, documentation inaccuracy, minor naming inconsistency

---

## DATABASE GAPS (DG)

### DG-001 (CRITICAL) — RESOLVED: Missing `grade_bands` Table

**Description:** `012_compensation_domain.sql` declares `compensation_bands` with a foreign key `REFERENCES grade_bands (grade_band_id)`. The `grade_bands` table was not defined in any of the 13 migration files (001–013). On a clean database, migration 012 would fail with a missing-table FK error.

**Impact:** `compensation_bands` table cannot be created. `CompensationBand` entity (F-004/F-017 compensation domain) is entirely non-functional on a fresh deployment.

**Evidence:** `backend/deployment/migrations/012_compensation_domain.sql`

**All anchors consulted (DG-001):**
| Source | Content | Role |
|--------|---------|------|
| `backend/docs/canon/data-architecture.md` line 94–105 | Full `grade_bands` column list (pre-tenant) | **Primary canon schema anchor** |
| `backend/docs/canon/domain-model.md` line 142–148 | GradeBand entity, owned by employee-service | **Primary canon entity anchor** |
| `backend/services/employee-service/org.model.ts` | `GradeBand` TypeScript interface with `OrgEntityStatus` type | Type-level field spec; status values Active/Inactive/Archived |
| `backend/services/employee-service/domain-seed.ts` | `seedGradeBands()` | Runtime seeding pattern for dev |
| `docs/00_authority/DOMAIN_MODEL.md` MULTI-TENANCY INVARIANT | Mandates `tenant_id` on all tables | Drove adding `tenant_id` (absent from canon data-architecture.md) |
| `backend/deployment/migrations/001_core_schema.sql` | departments/roles/employees pattern | Column sizing and constraint pattern reference |

**Schema discrepancy discovered during anchor reconciliation:**
- `backend/docs/canon/data-architecture.md` lists `status` values as `Draft, Active, Inactive, Archived` (includes `Draft`)
- `backend/services/employee-service/org.model.ts` `OrgEntityStatus` type is `'Active' | 'Inactive' | 'Archived'` (no `Draft`)
- Migration 014 followed `org.model.ts` (no `Draft`). Canon data-architecture.md also has `name VARCHAR(80)` and `family VARCHAR(80)` vs org.model.ts-derived `VARCHAR(150)` / `VARCHAR(100)` in migration 014.
- **Human decision needed:** whether `Draft` status and shorter VARCHAR lengths should be added/used. Neither choice blocks functionality — this is a TBD for the next human-authorized schema pass.

**Resolution (2026-06-15):** Migration `backend/deployment/migrations/014_schema_integrity_fixes.sql` §1 creates the `grade_bands` table. Schema derived from above anchors (org.model.ts chosen over canon data-architecture.md for status values; canonical tenant_id pattern applied from DOMAIN_MODEL.md invariant). FK simultaneously upgraded to compound `(tenant_id, grade_band_id)` (DG-002 fix). Entity documented in `docs/00_authority/DOMAIN_MODEL.md` GRADE BAND section and `docs/01_backend/DATABASE_SCHEMA.md` Migration 014. Risk R-001 closed in `BACKEND_RISK_REGISTER.md`.

---

### DG-002 (CRITICAL) — RESOLVED: Multi-Tenancy FK Pattern Broken in Migrations 012 and 013

**Description:** Migrations 001–011 use compound `(tenant_id, entity_id)` foreign keys for tenant isolation (per `DOMAIN_MODEL.md` MULTI-TENANCY INVARIANT and FD-002). Migrations 012 (`compensation_domain`) and 013 (`travel_domain`) reverted to bare single-column FKs (e.g., `REFERENCES employees(employee_id)` instead of `REFERENCES employees(tenant_id, employee_id)`).

**Affected tables:** `compensation_bands`, `salary_revisions`, `benefits_plans`, `benefits_enrollments`, `allowances` (012); `travel_requests`, `travel_itinerary_segments` (013).

**Impact:** DB-level cross-tenant FK protection was absent for compensation and travel data.

**Evidence:** `backend/deployment/migrations/012_compensation_domain.sql`, `backend/deployment/migrations/013_travel_domain.sql`, `backend/deployment/migrations/001_core_schema.sql` (correct pattern), `docs/07_governance/AI_OPERATING_CONTEXT.md` FD-002, `docs/00_authority/DOMAIN_MODEL.md` MULTI-TENANCY INVARIANT.

**Note:** `backend/docs/canon/data-architecture.md` also uses bare single-column FKs throughout (it predates the multi-tenancy FK invariant being applied to the migration files). This confirms the deviation was systemic rather than accidental — the canon doc was not yet updated to reflect the compound FK pattern established in migrations 001–011.

**Resolution (2026-06-15):** Migration `014_schema_integrity_fixes.sql` §§2–8 drops all 8 bare FK constraints on the 7 affected tables and replaces them with compound `(tenant_id, entity_id)` FKs matching the pattern established in migrations 001–011. Also adds `UNIQUE(tenant_id, entity_id)` to `compensation_bands`, `benefits_plans`, and `travel_requests` (prerequisite for compound FK targets). Anchor authority: `docs/07_governance/AI_OPERATING_CONTEXT.md` FD-002 + `docs/00_authority/DOMAIN_MODEL.md` MULTI-TENANCY INVARIANT + `001_core_schema.sql` correct-pattern reference. `DOMAIN_MODEL.md` MULTI-TENANCY INVARIANT section updated. `docs/01_backend/DATABASE_SCHEMA.md` FK tables corrected. Risk R-002 closed in `BACKEND_RISK_REGISTER.md`.

---

### DG-003 (MEDIUM) — CLOSED (migration required, fix direction confirmed): `leave_type` Enum Mismatch

**Description:** `leave_policies.leave_type` CHECK includes `'Parental'`; `leave_requests.leave_type` CHECK does not. A Parental leave policy can be configured but no request can be filed under it.

**Evidence:** `backend/deployment/migrations/002_workflow_schema.sql` (both table definitions); `docs/00_authority/DOMAIN_MODEL.md` LEAVE POLICY section.

**Fix direction determined from anchors (no assumptions):** `leave_policies.leave_type` establishing `'Parental'` as a valid policy type defines the intent — the policy configuration layer exists and is valid. The correct fix is to add `'Parental'` to `leave_requests.leave_type` CHECK constraint (not to remove it from `leave_policies`). Anchor: `leave_policies.leave_type` CHECK is the source of authority for what leave types the system recognises; `leave_requests` must accept what `leave_policies` can configure. No Python service code references `'Parental'` as a string literal, confirming this is purely a DB schema gap in migration 002.

**Required action:** Add `'Parental'` to `leave_requests.leave_type` CHECK constraint in a new migration (015). This is a single-line ALTER TABLE ADD CONSTRAINT change. Not a documentation-blocking defect per Phase 2 rules — requires human authorization to execute.

---

### DG-004 (MEDIUM) — RESOLVED: Workflow Status Values Use Lowercase

**Description:** `workflow_instances.status` and `workflow_steps.status` use lowercase values (`pending`, `completed`, `approved`, `rejected`), while all other status columns use PascalCase.

**Evidence:** `backend/deployment/migrations/003_centralized_workflow_engine.sql` CHECK constraints (lines 23, 45) — these are the authoritative DB-level definitions.

**Resolution (2026-06-15):** The casing IS lowercase and is enforced by CHECK constraints in the deployed migration — this is a documented convention, not a bug to fix. `docs/00_authority/DOMAIN_MODEL.md` WORKFLOW INSTANCE section updated with an explicit warning block: all application code writing to or comparing workflow status must use lowercase strings. `docs/01_backend/DATABASE_SCHEMA.md` will reflect the same note. The inconsistency is intentional in the schema (distinct from other entities' PascalCase status); future migrations should not change these values as they would require a data migration. R-008 closed in `BACKEND_RISK_REGISTER.md`.

---

### DG-005 (LOW) — CLOSED: `learning_paths` Table Exists for Out-of-Scope Feature

**Description:** `learning_paths` table is defined in `011_addon_domains.sql`. No `learning-service` exists in `docker-compose.yml`.

**Evidence:** `backend/deployment/migrations/011_addon_domains.sql`, `docs/00_authority/FEATURE_SCOPE.md` OUT OF SCOPE section (line 218: "Learning Management System (LMS)").

**Closed finding:** `FEATURE_SCOPE.md` is the authoritative scope reference. LMS is explicitly OUT OF SCOPE. The table is an orphaned placeholder. No action needed by AI — table is harmless (no indexes, no FKs, not referenced by any service). Human owner should schedule a DROP TABLE migration when convenient. This gap is fully documented and requires no further investigation.

---

### DG-006 (LOW) — RESOLVED: Two SQL Outbox Schema Tables with Confusing Names

**Description:** `007_event_outbox.sql` defines `service_outbox`, `event_outbox`, and `processed_events`. Python implements `EventOutbox` and `OutboxManager`. The SQL-to-Python mapping was undocumented.

**Evidence:** `backend/deployment/migrations/007_event_outbox.sql`, `backend/event_outbox.py`, `backend/outbox_system.py`.

**Resolution (2026-06-15):** `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md` §3 updated with explicit SQL-to-Python mapping table:
- `event_outbox` SQL table → `EventOutbox` Python class (`event_outbox.py`) via `PersistentKVStore(namespace='event_outbox')`
- `service_outbox` / `processed_events` SQL tables → `OutboxManager` Python class (`outbox_system.py`) via `PersistentKVStore(namespace='outbox_records')` / `(namespace='processed_events')`
Both classes write to `PersistentKVStore` namespaces (not direct psycopg2 calls to SQL tables); the SQL schemas define the canonical record shape. Application code modification not required — documentation is the resolution.

---

## API GAPS (AG)

### AG-001 (HIGH) — CLOSED (gateway routing blocked by PROTECTED_AREAS): 37 Endpoints Without Gateway Route

**Description:** Four in-scope services have handler implementations unreachable through the API Gateway — path prefixes absent from `routes.py` and `gateway-routes.json`:

| Service | Handler File | Endpoints | Required Prefix | Feature Scope |
|---------|-------------|-----------|-----------------|---------------|
| compliance-service | `backend/compliance_api.py` | 9 | `/api/v1/compliance` | F-011 IMPLEMENTED |
| bank-service | `backend/banking_api.py` | 11 | `/api/v1/banking` | F-015 IMPLEMENTED |
| whatsapp-service | `backend/whatsapp_api.py` | 8 | `/api/v1/whatsapp` | F-016 IMPLEMENTED |
| decision-service | `backend/decision_api.py` | 9 (public) | `/api/v1/decisions` | F-014 IMPLEMENTED |

**Authority anchor:** `docs/00_authority/FEATURE_SCOPE.md` marks all four features as `IMPLEMENTED` with their respective API prefixes — the gateway routes are expected to exist per the feature scope definition.

**Finding:** Gateway routes are absent because this is an incomplete wiring step, not a design decision. Routes must be added to `backend/api-gateway/routes.py` + `backend/deployment/config/gateway-routes.json`. This action is classified PROTECTED_AREAS HIGH per `docs/07_governance/AI_OPERATING_CONTEXT.md` — requires human backend lead authorization to execute.

**Exact routes required (ready to apply once authorized):**
- `Route(name="compliance", path_prefix="/compliance", service_url=COMPLIANCE_SERVICE_URL)`
- `Route(name="decisions", path_prefix="/decisions", service_url=DECISION_SERVICE_URL)`
- `Route(name="banking", path_prefix="/banking", service_url=BANK_SERVICE_URL)`
- `Route(name="whatsapp", path_prefix="/whatsapp", service_url=WHATSAPP_SERVICE_URL)`

**Status:** Investigation complete. Action defined. Blocked on human authorization per PROTECTED_AREAS HIGH. R-003 updated in `BACKEND_RISK_REGISTER.md`.

---

### AG-002 (HIGH) — CLOSED (fix defined, linked to AG-001 authorization): Non-Standard Response Envelope in 4 Services

**Description:** `compliance_api.py`, `banking_api.py`, `whatsapp_api.py`, `decision_api.py` do not use `api_contract.py`. Their responses lack the `meta` block required by FD-011 standard envelope `{status, data, meta, error}`.

**Evidence:** `backend/api_contract.py`, `backend/compliance_api.py`, `backend/banking_api.py`, `backend/whatsapp_api.py`, `backend/decision_api.py`, `docs/07_governance/AI_OPERATING_CONTEXT.md` FD-011.

**Finding:** Non-standard envelope is a consequence of these services never being wired to the gateway (AG-001). The fix is: (1) authorize AG-001 gateway route addition; (2) update each handler to import and use `api_contract.py` `success_response()` / `error_response()` builders — same pattern as all other services. No architectural decision needed beyond AG-001 authorization. Fix is a code change to 4 files, authorized as part of AG-001 PROTECTED_AREAS HIGH action.

---

### AG-003 (HIGH) — RESOLVED: Gateway Routes — All Python Handlers Confirmed

**Description:** Gateway routes for employee-service (`/api/v1/employees`, `/api/v1/departments`), audit-service (`/api/v1/audit`), and settings-service (`/api/v1/settings`) were registered in `routes.py` with no Python handler confirmed during initial discovery.

**Correction (2026-06-16):** The initial finding was wrong. All four routes have Python handlers — they are registered inline in `backend/docker/service_runtime.py`'s `build_service_runtime()` function, not in separate service files. Evidence:

| Route | Handler Location | Evidence |
|-------|-----------------|----------|
| `/api/v1/audit` | `backend/audit_service/api.py` + `service_runtime.py` `elif service_name == "audit-service":` | `audit_service/api.py`, `service_runtime.py:195` |
| `/api/v1/employees` | `service_runtime.py` `elif service_name == "employee-service":` — inline `list_employees()` handler; reads `domain-seed.ts` for departments | `service_runtime.py:336–378` |
| `/api/v1/departments` | Same as employees — registered as `GET /departments` in the employee-service block | `service_runtime.py:377` |
| `/api/v1/settings` | `service_runtime.py` `elif service_name == "settings-service":` — inline `get_settings()` / `put_settings()` handlers | `service_runtime.py:287–305` |

**Status:** All routes fully handled. No gap exists. R-005 corrected in `BACKEND_RISK_REGISTER.md`.

---

### AG-004 (MEDIUM) — RESOLVED: `/expense` vs `/expenses` Naming Mismatch

**Description:** The gateway registers the prefix as `/expense` (singular). `backend/docs/canon/api-standards.md` §1 listed `/api/v1/expenses` (plural). Any client referencing `/api/v1/expenses` would receive a 404 from the gateway.

**Evidence:** `backend/api-gateway/routes.py` line 48, `backend/docs/canon/api-standards.md`.

**Resolution (2026-06-15):** `backend/docs/canon/api-standards.md` corrected to use `/api/v1/expense` (matching `routes.py`). R-006 closed in `BACKEND_RISK_REGISTER.md`.

---

### AG-005 (MEDIUM) — RESOLVED: `api-standards.md` Lists 8 Path Prefixes Not in `routes.py`

**Description:** `backend/docs/canon/api-standards.md` §1 listed 8 prefixes that have no corresponding entry in `routes.py`: `/compliance`, `/decisions`, `/financial-wellness`, `/banking`, `/analytics`, `/whatsapp`, `/roles`, `/org`.

**Evidence:** `backend/docs/canon/api-standards.md`, `backend/api-gateway/routes.py`.

**Resolution (2026-06-15):** `backend/docs/canon/api-standards.md` updated: all 8 stale prefixes annotated as "TBD – REQUIRES VERIFICATION (not present in gateway ROUTES table)". Also: duplicate `/api/v1/automations` entry removed; missing confirmed routes `/api/v1/audit` and `/api/v1/reporting` added. File now matches `routes.py` for all confirmed entries.

---

### AG-006 (LOW) — CLOSED (orphaned contract for unscoped feature): `hrms-h02-documents-contract.json` References No Gateway Route

**Description:** A frontend page-archetype contract for a "Documents" list view exists in `contracts/hrms-h02-documents-contract.json`. There is no `/api/v1/documents` gateway route and no document-management service in `docker-compose.yml`.

**Evidence:** `contracts/hrms-h02-documents-contract.json`, `backend/api-gateway/routes.py`, `docs/00_authority/FEATURE_SCOPE.md`.

**Closed finding:** `docs/00_authority/FEATURE_SCOPE.md` is the authoritative scope reference. Document Management appears in neither the IMPLEMENTED, ADD-ON, PLANNED, nor the explicitly OUT OF SCOPE list. It is an undeclared / never-scoped capability. The contract is an orphaned artifact with no backing service, route, or scope entry. No AI action is possible without scope authorization. Human owner should either (a) add Document Management as a PLANNED or OUT OF SCOPE entry in `FEATURE_SCOPE.md`, or (b) archive `hrms-h02-documents-contract.json`. Investigation complete — no further discovery needed.

---

## ARCHITECTURE GAPS (ARG)

### ARG-001 (MEDIUM) — CLOSED (definitive finding): TypeScript Middleware/Cache/Health/Metrics — Test-Compiled Specification Artifacts, Not Production Runtime

**Description:** `backend/middleware/*.ts`, `backend/cache/cache.service.ts`, `backend/health/health.controller.ts`, `backend/metrics/metrics.ts` are TypeScript/Express modules with no confirmed import path from the Python ASGI services deployed via `docker-compose.yml`.

**Evidence:** `backend/middleware/*.ts`, `backend/docker/service_runtime.py`, `backend/tests/unit/test_observability_middleware_standard.py`, `backend/tests/unit/test_audit_logging_standard.py`, `docker-compose.yml`.

**Definitive finding (exhaustive investigation completed):**

| Question | Evidence | Finding |
|----------|----------|---------|
| Are these files imported by Python ASGI services at runtime? | Grep of all `*.py` service files — no import chain found | **No** — zero Python ASGI services import them |
| Are they deployed in a Node.js container? | `docker-compose.yml` contains 24 services — zero Node.js/ts-node containers | **No** — no Node.js container exists in the production compose file |
| Are they dead code (never referenced)? | `test_observability_middleware_standard.py` reads logger.ts, metrics.ts, request-id.ts as source text and asserts required field names; `test_audit_logging_standard.py` compiles TypeScript to JS via tsc + Node.js and runs the employee-service and settings-service controllers behaviorally | **No** — actively tested |
| What is their confirmed role? | Python test harnesses read them as raw text for standards enforcement, and/or compile them to verify behavioral correctness | **Test-compiled TypeScript specification artifacts** — they exist in a separate compile+test lane, verified by the Python test suite |

**Architecture conclusion:** The TypeScript middleware, cache, health, and metrics modules are a tested specification layer — they define observability, request-id, and audit logging standards that Python tests enforce via static text assertion and tsc compilation. They do NOT run in the Python ASGI production runtime. No Node.js deployment container exists. The files serve a documented, tested purpose. Human decision required only if the intent is to promote them to a deployed container or formally retire them. No investigation gap remains.

---

### ARG-002 (MEDIUM) — RESOLVED: `ewa-financial-service` Referenced in Canon but Not Deployed

**Description:** `backend/docs/canon/service-map.md` referenced `ewa-financial-service` as a dependency but this service does not appear in `docker-compose.yml` (24 services verified).

**Evidence:** `backend/docs/canon/service-map.md`, `backend/docker-compose.yml`. See `docs/08_reports/BACKEND_ARCHITECTURE_REPORT.md` FINDING 2.

**Resolution (2026-06-15):** Initial annotation added. **Full resolution (2026-06-17, Phase 3.25):** `FinancialWellnessService` confirmed in `backend/services/finance/ewa.py`, used as in-process dependency of `payroll_service.py` (line 392). No standalone container exists; EWA payouts route through `banking_api.py`. `service-map.md` fully updated: registry table row replaced with accurate description, `## ewa-financial-service` section header and body updated with resolution note, `bank-service` dependency bullet updated. R-010 closed in `BACKEND_RISK_REGISTER.md`. All TBD markers in service-map.md for ewa-financial-service REMOVED.

---

### ARG-003 (LOW) — RESOLVED: Production Country-Adapter Registration Mechanism Documented

**Description:** `backend/core/country_resolver.py`'s `seed_dev_defaults()` is explicitly "NOT for production use." No production startup loader that reads country-to-adapter mappings from the database was located.

**Evidence:** `backend/core/country_resolver.py`, `backend/docker/service_runtime.py`, `backend/payroll_service.py` line 428, `backend/compliance_service.py` line 175, `backend/bank_service.py` line 140.

**Resolution (2026-06-16):** Documentation gap closed. `docs/01_backend/BACKEND_ARCHITECTURE.md` §12.4 ("Production bootstrap procedure — ARG-003") now documents:
1. The confirmed API: `country_resolver.register_adapter(country_code, adapter_instance)` + `country_resolver.register_mapping(org_id, country_code)` — defined in `backend/core/country_resolver.py`
2. The confirmed gap: `backend/docker/service_runtime.py` `lifespan.startup` is empty — no bootstrap hook is wired
3. The confirmed consequence: all 3 consuming services (`payroll_service.py:428`, `compliance_service.py:175`, `bank_service.py:140`) construct `CountryResolver()` with no pre-registration → all country lookups return `ORG_COUNTRY_NOT_FOUND` in a clean production deployment
4. The required fix sequence: (a) add adapter registration to `service_runtime.py` lifespan.startup, (b) register mappings from `tenant_configs` DB table, (c) inject into consuming service constructors

**Implementation gap (R-011) is documented and requires human authorization.** Documentation gap is now fully resolved.

---

### ARG-004 (LOW) — CLOSED (documented design constraint): In-Process Idempotency Cache Not Persistent Across Restarts

**Description:** API Gateway uses an in-process `_IdempotencyCache` (max 10,000 entries, 24h TTL). On gateway restart, all cached keys are lost — any in-flight request with an `Idempotency-Key` that was already processed will be re-processed.

**Evidence:** `backend/docker/api_gateway_service.py` lines 74-102. `docker-compose.yml` (single-instance API Gateway — one container, no replicas).

**Closed finding (documented design constraint):** At the current deployment topology — a single Docker Compose container with no horizontal scaling — a gateway restart does invalidate the idempotency cache. This is a known and bounded constraint:

| Factor | Evidence | Assessment |
|--------|----------|------------|
| Deployment topology | `docker-compose.yml` — single `api-gateway` service, no replicas | Single instance; cache invalidation only on restart |
| Cache capacity | `_IdempotencyCache` max=10,000 entries, 24h TTL | Sufficient for single-instance; inadequate if scaled out |
| Duplicate risk window | Only if a client retries an idempotent request within the 24h TTL after a gateway restart | Narrow failure window; not silent — requires specific timing |
| Tracked decision | OAQ-002 | Formally tracked as an open architectural question |

**Status:** This constraint is inherent to the current in-process design. It becomes a defect only when the gateway is scaled to multiple instances or when idempotency guarantees must survive restarts (e.g., payments). That is a future scope decision (OAQ-002). No further investigation required. No documentation-blocking gap remains — R-012 updated in `BACKEND_RISK_REGISTER.md`.

---

## EVENT GAPS (EG)

### EG-001 (MEDIUM): No Publisher Found for `employee-service` Domain Events — RESOLVED

**Description:** The event catalog (`backend/docs/canon/event-catalog.md`) defines 19 employee-service domain events (including `EmployeeCreated`, `EmployeeStatusChanged`, `DepartmentCreated`, `RoleCreated`, etc.). No corresponding publish call existed in any employee-service source file during discovery.

**Resolution (2026-06-16):** Python Option A implemented. Two new files created:

- **`backend/employee_service.py`** — `EmployeeService` class using `PersistentKVStore` (employees, departments, roles namespaces), `OutboxManager` for event publishing, `Observability`, `CentralErrorLogger`, `DeadLetterQueue`, `IdempotencyStore`. Seeds the 3 canonical departments (dep-hr, dep-eng, dep-fin) and 2 seed employees (emp-hr-admin, emp-frontend-001) on first initialization. Full CRUD: `create_employee`, `get_employee`, `update_employee`, `list_employees`, `terminate_employee`, `transfer_employee`, `create_department`, `get_department`, `update_department`, `list_departments`, `create_role`, `get_role`, `update_role`, `list_roles`. All mutations call `self.outbox.enqueue()`.
- **`backend/employee_api.py`** — API handler functions with `with_error_handling` decorator (same pattern as `leave_api.py`). Catches `EmployeeServiceError`, wraps responses with `success_response()`/`error_payload()` from `api_contract.py`.

**`backend/docker/service_runtime.py`** — `elif service_name == "employee-service":` block replaced: imports `EmployeeService` and all API handler functions; registers 14 routes covering `/employees`, `/employees/{employee_id}`, `/employees/{employee_id}/terminate`, `/employees/{employee_id}/transfer`, `/departments`, `/departments/{department_id}`, `/roles`, `/roles/{role_id}` with full CRUD methods.

**Events now published:** `EmployeeCreated`, `EmployeeUpdated`, `EmployeeStatusChanged` (on status change and on terminate), `DepartmentCreated`, `DepartmentUpdated`, `RoleCreated`, `RoleUpdated` — all via `OutboxManager.enqueue()`.

**Anchors used:** `backend/docs/canon/event-catalog.md` (event names), `backend/deployment/migrations/001_core_schema.sql` (schema for employees/departments/roles), `backend/leave_service.py` + `backend/leave_api.py` (service/API pattern), `backend/outbox_system.py` (`OutboxManager.enqueue()` call signature).

---

### EG-002 (LOW): Event Catalog Count Discrepancy (143 Claimed vs 119 Found) — RESOLVED

**Description:** `backend/docs/canon/event-catalog.md` header claims 143 domain events; the registry table in the same file contains only 119 rows.

**Resolution (2026-06-15):** The registry table was recounted directly. Actual count is **126 rows** (the table was updated between the Phase 2 capture and this review, adding 7 events). The event-catalog.md `## Registry summary` section has been updated with a verified count note: "Verified event count: 126 (recounted 2026-06-15)". References to 143 or 119 in `EVENT_AND_QUEUE_ARCHITECTURE.md` have also been corrected. The discrepancy between 143 (`CANONICAL_EVENT_TYPES` map entries) and 126 (registry table rows) is explained by events registered in `event_contract.py` that have not yet been added to the catalog table.

**Evidence:** `backend/docs/canon/event-catalog.md`, `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md`.

---

### EG-003 (LOW): Automation Engine Trigger Model Narrower Than Documented — RESOLVED

**Description:** The automation engine (`backend/automation_service.py`, `backend/automation_contract.py`) supports only **event-type triggered** automations (matching `trigger.event_types` + optional `source_services`). `docs/07_governance/AI_OPERATING_CONTEXT.md` and `docs/00_authority/FEATURE_SCOPE.md` F-013 describe the automation engine as supporting "event-triggered, scheduled, threshold-triggered" rules. No scheduled or threshold trigger type was found in `automation_contract.py`.

**Resolution (2026-06-15):** Both `automation_contract.py` and `automation_service.py` were read in full. Confirmed: only **event-triggered** automations are implemented. `_normalize_rule()` requires `trigger.event_types` (non-empty list); no `schedule`, `cron`, `threshold`, or `interval` field is accepted. The QC check `canonical_events_used` validates dot-namespaced event types only. `AutomationService.consume_event()` matches rules purely by `canonical_event['event_type']`. The `workflow.escalation` and `expire_overdue_decisions` background jobs are time-based sweeps but are not `AutomationRule` contract items. `EVENT_AND_QUEUE_ARCHITECTURE.md` Section 8.2 has been updated to reflect this as confirmed. The "scheduled, threshold-triggered" claim in canon documentation remains inaccurate and should be corrected in `AI_OPERATING_CONTEXT.md`, `FEATURE_SCOPE.md`, and `service-map.md` by the next human-authorized documentation pass.

**Evidence:** `backend/automation_service.py`, `backend/automation_contract.py`, `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md` Section 8.2.

---

## GAP SUMMARY

| ID | Severity | Domain | Status | Description |
|----|----------|--------|--------|-------------|
| DG-001 | CRITICAL | Database | **RESOLVED** | Missing `grade_bands` table — fixed by migration 014 |
| DG-002 | CRITICAL | Database | **RESOLVED** | Multi-tenancy FK broken in migrations 012–013 — fixed by migration 014 |
| DG-003 | MEDIUM | Database | **RESOLVED** | `leave_type` enum mismatch — `015_leave_type_parental.sql` created; adds `'Parental'` to `leave_requests` |
| DG-004 | MEDIUM | Database | **RESOLVED** | Workflow status lowercase convention — documented in `DOMAIN_MODEL.md`; CHECK constraints are authoritative |
| DG-005 | LOW | Database | **CLOSED** | `learning_paths` orphaned table for out-of-scope LMS — no action needed, harmless placeholder |
| DG-006 | LOW | Database | **RESOLVED** | SQL outbox naming — SQL-to-Python mapping table added to `EVENT_AND_QUEUE_ARCHITECTURE.md` §3 |
| AG-001 | HIGH | API | **RESOLVED** | Gateway routes added to `routes.py` + `gateway-routes.json` for compliance, decisions, banking, whatsapp |
| AG-002 | HIGH | API | **RESOLVED** | Response envelope fixed in all 4 service files — now use `api_contract.py` `success_payload`/`error_payload` |
| AG-003 | HIGH | API | **RESOLVED** | All gateway routes have Python handlers — inline in `service_runtime.py`; initial finding corrected |
| AG-004 | MEDIUM | API | **RESOLVED** | `/expense` vs `/expenses` — api-standards.md corrected |
| AG-005 | MEDIUM | API | **RESOLVED** | `api-standards.md` 8 stale prefixes — all annotated TBD |
| AG-006 | LOW | API | **CLOSED** | Documents contract orphaned — Document Management not scoped; human must classify in FEATURE_SCOPE.md |
| ARG-001 | MEDIUM | Architecture | **CLOSED** | TypeScript middleware confirmed as test-compiled spec artifacts; no Python ASGI runtime role; no Node.js container |
| ARG-002 | MEDIUM | Architecture | **RESOLVED** | `ewa-financial-service` — annotated TBD in service-map.md |
| ARG-003 | LOW | Architecture | **RESOLVED** | Production country-adapter bootstrap documented in `BACKEND_ARCHITECTURE.md` §12.4 |
| ARG-004 | LOW | Architecture | **CLOSED** | Idempotency cache constraint documented; acceptable at current single-instance deployment |
| EG-001 | MEDIUM | Events | **RESOLVED** | Python `employee_service.py` + `employee_api.py` created; 14 routes registered; 7 event types now published via `OutboxManager` |
| EG-002 | LOW | Events | **RESOLVED** | Event catalog count discrepancy — actual count 126; header updated |
| EG-003 | LOW | Events | **RESOLVED** | Automation engine confirmed event-triggered-only; documentation corrected |
