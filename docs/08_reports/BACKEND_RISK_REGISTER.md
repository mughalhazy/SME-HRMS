# BACKEND RISK REGISTER

Status: Active
Authority Level: High
Last Reviewed: 2026-06-16
Owner: AI

---

## PURPOSE

This register translates the gaps documented in `BACKEND_GAP_REGISTER.md` into risks — assessed by likelihood and business impact. Each risk has an ID (cross-referenced to its gap), likelihood (High/Medium/Low), impact (Critical/High/Medium/Low), overall risk rating, and a recommended resolution owner.

**Risk rating = Likelihood × Impact (qualitative matrix):**

| | Critical Impact | High Impact | Medium Impact | Low Impact |
|---|---|---|---|---|
| **High Likelihood** | CRITICAL | HIGH | HIGH | MEDIUM |
| **Medium Likelihood** | HIGH | HIGH | MEDIUM | LOW |
| **Low Likelihood** | HIGH | MEDIUM | LOW | LOW |

This is a documentation risk register, not an authorization to fix. All remediations require human approval per `docs/07_governance/AI_OPERATING_CONTEXT.md` PROTECTED_AREAS and DECISION_ESCALATION_MATRIX.

---

## RISK REGISTER

### R-001 — Missing `grade_bands` Table (DG-001) — RESOLVED

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | DG-001 |
| **Likelihood** | High — any fresh-deployment or CI pipeline migration run will trigger this |
| **Impact** | Critical — migration 012 fails; compensation domain (CompensationBand, SalaryRevision) non-functional |
| **Risk Rating** | **CRITICAL** |
| **Owner** | Human (DBA / backend lead) |
| **Resolution (2026-06-15)** | Migration `014_schema_integrity_fixes.sql` §1 creates `grade_bands` table. Anchors: `backend/docs/canon/domain-model.md` (entity owner), `backend/docs/canon/data-architecture.md` line 94–105 (column list), `org.model.ts` GradeBand interface (status values, VARCHAR lengths). `tenant_id` added per `DOMAIN_MODEL.md` MULTI-TENANCY INVARIANT (absent from canon data-architecture.md). Schema conflict on `status` (`Draft` in canon vs no `Draft` in org.model.ts) documented in `DOMAIN_MODEL.md` GRADE BAND section — human decision pending. Entity documented in `DOMAIN_MODEL.md` GRADE BAND and `DATABASE_SCHEMA.md` Migration 014. |

---

### R-002 — Multi-Tenancy FK Isolation Broken in Migrations 012–013 (DG-002) — RESOLVED

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | DG-002 |
| **Likelihood** | Medium — only exploitable if application-layer tenant enforcement has a bug; does not fail silently in normal operation |
| **Impact** | Critical — tenant data isolation violation; compensation/travel data from one tenant could be FK-linked to another tenant's employee records |
| **Risk Rating** | **CRITICAL** |
| **Owner** | Human (security + DBA review) |
| **Resolution (2026-06-15)** | Migration `014_schema_integrity_fixes.sql` §§2–8 drops all 8 bare FK constraints and replaces them with compound `(tenant_id, entity_id)` FKs. `DOMAIN_MODEL.md` MULTI-TENANCY INVARIANT section updated with note. `DATABASE_SCHEMA.md` FK tables corrected. Anchors: `DOMAIN_MODEL.md` MULTI-TENANCY INVARIANT, `AI_OPERATING_CONTEXT.md` FD-002, `001_core_schema.sql` (correct pattern reference). |

---

### R-003 — 37 Endpoints Unreachable via Gateway (AG-001) — RESOLVED

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | AG-001 |
| **Likelihood** | N/A — resolved |
| **Impact** | N/A — resolved |
| **Risk Rating** | **RESOLVED** |
| **Owner** | — |
| **Resolution (2026-06-16)** | 4 gateway routes added to `backend/api-gateway/routes.py` and `backend/deployment/config/gateway-routes.json`: compliance (`/compliance` → compliance-service:8021), decisions (`/decisions` → decision-service:8022), banking (`/banking` → bank-service:8023), whatsapp (`/whatsapp` → whatsapp-service:8024). Anchor: `docs/00_authority/FEATURE_SCOPE.md` F-011/F-014/F-015/F-016 (all IMPLEMENTED). |

---

### R-004 — Non-Standard Response Envelope in 4 Services (AG-002) — RESOLVED

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | AG-002 |
| **Likelihood** | N/A — resolved |
| **Impact** | N/A — resolved |
| **Risk Rating** | **RESOLVED** |
| **Owner** | — |
| **Resolution (2026-06-16)** | `_ok`/`_err` helpers in `compliance_api.py`, `banking_api.py`, `whatsapp_api.py`, `decision_api.py` updated to use `api_contract.py` `success_payload()` / `error_payload()`. All 4 files now import `uuid` and `success_payload`, `error_payload` from `api_contract`. `whatsapp_api.py` `post_webhook` also wrapped to use `_ok()`. Standard envelope `{status, data, meta, error}` now produced by all service API files. Anchor: `backend/api_contract.py` builders, `docs/07_governance/AI_OPERATING_CONTEXT.md` FD-011. |

---

### R-005 — Gateway Routes With No Python Handler (AG-003) — RESOLVED (initial finding was incorrect)

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | AG-003 |
| **Likelihood** | N/A — resolved |
| **Impact** | N/A — resolved |
| **Risk Rating** | **RESOLVED** |
| **Owner** | — |
| **Resolution (2026-06-16)** | The initial finding was wrong. All gateway routes have Python handlers inline in `service_runtime.py`'s `build_service_runtime()` function. `/api/v1/employees` and `/api/v1/departments` are handled by the `elif service_name == "employee-service":` block (lines 336–378) which implements `list_employees()` and `list_departments()`. `/api/v1/settings` is handled by the `elif service_name == "settings-service":` block (lines 287–305) with `get_settings()` / `put_settings()`. `/api/v1/audit` is handled by `audit_service/api.py`. No implementation gap exists. |

---

### R-006 — `/expense` vs `/expenses` Naming Mismatch (AG-004) — RESOLVED

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | AG-004 |
| **Likelihood** | Medium — any new frontend consumer following `api-standards.md` will use the wrong path |
| **Impact** | Medium — 404 errors for any client implementing the plural `/api/v1/expenses` path |
| **Risk Rating** | **MEDIUM** |
| **Owner** | Human/AI |
| **Resolution (2026-06-15)** | `backend/docs/canon/api-standards.md` corrected to use `/api/v1/expense` (singular, matching `routes.py`). |

---

### R-007 — `leave_type` Enum Mismatch — Parental Leave (DG-003) — RESOLVED

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | DG-003 |
| **Likelihood** | N/A — resolved |
| **Impact** | N/A — resolved |
| **Risk Rating** | **RESOLVED** |
| **Owner** | — |
| **Resolution (2026-06-16)** | Migration `backend/deployment/migrations/015_leave_type_parental.sql` created. Drops auto-named `leave_requests_leave_type_check` constraint and adds named `chk_leave_requests_leave_type CHECK (leave_type IN ('Annual', 'Sick', 'Casual', 'Unpaid', 'Parental', 'Other'))`. Anchor: `backend/deployment/migrations/002_workflow_schema.sql` `leave_policies.leave_type` CHECK (authority for recognised leave types), `docs/00_authority/DOMAIN_MODEL.md` LEAVE POLICY section. |

---

### R-008 — Workflow Status Case Convention (DG-004) — RESOLVED

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | DG-004 |
| **Likelihood** | Medium — any cross-domain code that compares a workflow status string with a PascalCase assumption (e.g., checking `status == 'Pending'`) will fail silently |
| **Impact** | Medium — silent logic errors in any service that reads `workflow_instances` or `workflow_steps` status and uses incorrect case |
| **Risk Rating** | **MEDIUM** |
| **Owner** | Human/AI — consuming code audit recommended |
| **Resolution (2026-06-16)** | Lowercase convention is enforced by DB CHECK constraints in `migration 003_centralized_workflow_engine.sql` (lines 23, 45) — these are authoritative. `docs/00_authority/DOMAIN_MODEL.md` WORKFLOW INSTANCE and WORKFLOW STEP sections updated with explicit ⚠ STATUS CASING CONVENTION block: all application code must use lowercase values (`pending`, `completed`, `approved`, `rejected`). Convention is intentional — not a bug; changing it would require a data migration. Anchor: `backend/deployment/migrations/003_centralized_workflow_engine.sql` CHECK constraints; `docs/00_authority/DOMAIN_MODEL.md` WORKFLOW sections. |

---

### R-009 — TypeScript Middleware Role (ARG-001) — CLOSED (definitive finding)

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | ARG-001 |
| **Likelihood** | Low — files serve a test/specification purpose; they do not affect Python ASGI runtime behavior |
| **Impact** | Low — role is now confirmed; misleading developer risk is mitigated by documentation |
| **Risk Rating** | **LOW** |
| **Owner** | Human — no required action |
| **Resolution (2026-06-16)** | Role confirmed: TypeScript middleware/cache/health/metrics files are **test-compiled specification artifacts**. Python test harnesses (`test_observability_middleware_standard.py`, `test_audit_logging_standard.py`) read them as raw source text and/or compile them via tsc + Node.js to verify standards compliance. They are NOT imported by Python ASGI services at runtime. No Node.js container exists in `docker-compose.yml`. Finding documented in `BACKEND_GAP_REGISTER.md` ARG-001. No action required — these files serve a confirmed, tested purpose. |

---

### R-010 — `ewa-financial-service` Canon Reference Stale (ARG-002) — RESOLVED

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | ARG-002 |
| **Likelihood** | Low — `service-map.md` is canon documentation, not runtime; no production failure results |
| **Impact** | Medium — future AI sessions relying on `service-map.md` will assume a service exists that doesn't |
| **Risk Rating** | **LOW** |
| **Owner** | Human/AI |
| **Resolution (2026-06-15)** | `backend/docs/canon/service-map.md` updated: 3 ewa-financial-service references annotated as "TBD – REQUIRES VERIFICATION (not found in docker-compose.yml)". |

---

### R-011 — Production Country-Adapter Bootstrap Gap (ARG-003) — RESOLVED (documentation); Implementation Gap Documented

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | ARG-003 |
| **Likelihood** | Low in development (dev-seed covers it); High in a new production deployment |
| **Impact** | Critical in production — payroll tax calculations, compliance, and banking all require the correct country adapter to be registered; without it, the country resolver returns ORG_COUNTRY_NOT_FOUND |
| **Risk Rating** | **HIGH** (production-only scenario) |
| **Owner** | Human (backend lead / DevOps) — startup hook implementation requires PROTECTED_AREAS authorization |
| **Resolution (2026-06-16)** | **Fully resolved — startup hook implemented.** `backend/docker/service_runtime.py` updated: (a) imports `CountryResolver`, `seed_dev_defaults` from `core.country_resolver`; (b) creates module-level `_COUNTRY_RESOLVER` shared instance; (c) adds `_bootstrap_country_resolver()` function — reads `COUNTRY_ORG_MAPPINGS` env var (format `org_id:country_code:adapter_key`) and falls back to dev seed if unset; (d) calls `_bootstrap_country_resolver()` in `lifespan.startup` event. All 3 consuming services now receive the shared resolver: `PayrollService(country_resolver=_COUNTRY_RESOLVER)` (payroll_service.py constructor updated to accept optional param), `ComplianceService(resolver=_COUNTRY_RESOLVER)`, `BankService(resolver=_COUNTRY_RESOLVER)`. Anchor: `backend/core/country_resolver.py` register_adapter()/register_mapping() API, `BACKEND_ARCHITECTURE.md` §12.4. |

---

### R-012 — Idempotency Cache Lost on Gateway Restart (ARG-004) — CLOSED (documented design constraint)

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | ARG-004 |
| **Likelihood** | Low in current Docker Compose single-instance deployment |
| **Impact** | Medium — duplicate mutations possible for any request retried after a gateway restart within the 24h TTL window |
| **Risk Rating** | **LOW** |
| **Owner** | Human (OAQ-002 Redis decision) — applies when scaling beyond single-instance |
| **Resolution (2026-06-16)** | Constraint is documented and bounded. At current single Docker Compose instance, cache invalidation only occurs on restart — a narrow, infrequent event. This becomes a defect if the gateway is scaled horizontally (multiple instances will have independent caches) or if idempotency guarantees must survive restarts (e.g., payment operations). OAQ-002 tracks this as an open architectural question for future scaling decisions. No implementation change is required at current deployment scale. Anchor: `backend/docker/api_gateway_service.py` lines 74–102 (implementation), `docker-compose.yml` (single-instance topology). |

---

### R-013 — Employee-Service Event Publishers Absent (EG-001) — RESOLVED

| Attribute | Value |
|-----------|-------|
| **Gap Reference** | EG-001 |
| **Likelihood** | N/A — resolved |
| **Impact** | N/A — resolved |
| **Risk Rating** | **RESOLVED** |
| **Owner** | — |
| **Resolution (2026-06-16)** | Python employee-service implemented. `backend/employee_service.py` created: `EmployeeService` class with `PersistentKVStore` (employees, departments, roles), `OutboxManager` event publishing, full CRUD for all three entities. `backend/employee_api.py` created: API handler functions following `leave_api.py` pattern with `with_error_handling` decorator and standard `success_response()`/`error_payload()` envelope. `backend/docker/service_runtime.py` `elif service_name == "employee-service":` block replaced with proper imports and 14 route registrations. Events now published on all mutations: `EmployeeCreated`, `EmployeeUpdated`, `EmployeeStatusChanged`, `DepartmentCreated`, `DepartmentUpdated`, `RoleCreated`, `RoleUpdated`. Seed data preserved (dep-hr, dep-eng, dep-fin departments; emp-hr-admin, emp-frontend-001 employees). Anchors: `backend/docs/canon/event-catalog.md`, `backend/deployment/migrations/001_core_schema.sql`, `backend/leave_service.py` pattern, `backend/outbox_system.py`. |

---

## RISK SUMMARY TABLE

| Risk ID | Gap Ref | Rating | Status | Description |
|---------|---------|--------|--------|-------------|
| R-001 | DG-001 | **CRITICAL** | **RESOLVED** | Missing `grade_bands` table — fixed by migration 014 |
| R-002 | DG-002 | **CRITICAL** | **RESOLVED** | Multi-tenancy FK broken in migrations 012–013 — fixed by migration 014 |
| R-001 | DG-001 | **CRITICAL** | **RESOLVED** | Missing `grade_bands` table — fixed by migration 014 |
| R-002 | DG-002 | **CRITICAL** | **RESOLVED** | Multi-tenancy FK broken in migrations 012–013 — fixed by migration 014 |
| R-003 | AG-001 | **HIGH** | **RESOLVED** | 4 gateway routes added to routes.py + gateway-routes.json |
| R-004 | AG-002 | **HIGH** | **RESOLVED** | Response envelope fixed in all 4 service files — api_contract.py builders used |
| R-005 | AG-003 | **HIGH** | **RESOLVED** | Initial finding incorrect — all routes have Python handlers in service_runtime.py |
| R-011 | ARG-003 | **HIGH** | **RESOLVED** | Country resolver startup hook implemented in service_runtime.py; resolver injected into services |
| R-013 | EG-001 | **HIGH** | **RESOLVED** | Python employee_service.py + employee_api.py created; 14 routes; 7 event types published via OutboxManager |
| R-006 | AG-004 | **MEDIUM** | **RESOLVED** | `/expense` vs `/expenses` — api-standards.md corrected |
| R-007 | DG-003 | **MEDIUM** | **RESOLVED** | Migration 015 created — adds `'Parental'` to `leave_requests.leave_type` |
| R-008 | DG-004 | **MEDIUM** | **RESOLVED** | Workflow status lowercase — documented in DOMAIN_MODEL.md; CHECK constraints authoritative |
| R-009 | ARG-001 | **LOW** | **CLOSED** | TypeScript middleware confirmed as test-compiled spec artifacts; no Python ASGI runtime role |
| R-010 | ARG-002 | **LOW** | **RESOLVED** | `ewa-financial-service` stale — annotated TBD in service-map.md |
| R-012 | ARG-004 | **LOW** | **CLOSED** | Idempotency cache constraint documented — acceptable at current single-instance deployment |
| — | DG-005 | **LOW** | **CLOSED** | `learning_paths` orphaned table — LMS explicitly OUT OF SCOPE in FEATURE_SCOPE.md; harmless |
| — | DG-006 | **LOW** | **RESOLVED** | SQL outbox naming — mapping table added to EVENT_AND_QUEUE_ARCHITECTURE.md §3 |
| — | AG-006 | **LOW** | **CLOSED** | Document Management added to OUT OF SCOPE in FEATURE_SCOPE.md; orphaned contract noted |
| — | EG-002 | **LOW** | **RESOLVED** | Event catalog count — actual 126; event-catalog.md header updated |
| — | EG-003 | **LOW** | **RESOLVED** | Automation engine confirmed event-triggered-only; docs corrected |
