# BACKEND ARCHITECTURE REPORT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This report summarizes findings from the PHASE 2 BACKEND AUTHORITY CAPTURE for architecture, services, and integrations. It documents what was produced, what was confirmed, what discrepancies were found between canon documentation and the actual repository, and what items require further verification.

**Companion documents produced:**
- `docs/01_backend/BACKEND_ARCHITECTURE.md` — full architecture narrative
- `docs/01_backend/SERVICE_CATALOG.md` — per-service catalog
- `docs/01_backend/INTEGRATION_CATALOG.md` — external integration catalog

**Primary evidence sources used:** `backend/docker-compose.yml`, `backend/docker/api_gateway_service.py`, `backend/docker/service_runtime.py`, `backend/api-gateway/routes.py`, `backend/deployment/config/gateway-routes.json`, `backend/docs/canon/service-map.md`, `backend/docs/canon/country-layer.md`, `backend/core/country_resolver.py`, `backend/resilience.py`.

---

## MODULES AND SERVICES DISCOVERED

### Deployed Services (docker-compose.yml)
**28 containers total:**
- 1 PostgreSQL 16 (`postgres` container)
- 1 one-shot migrations runner (`migrations` container)
- 24 domain microservices (ports 8001–8024)
- 1 API Gateway (port 8000)
- 1 Next.js frontend (port 3000→80)

### Domain Services (ports 8001–8024)
| Port | Service | Gateway Route | Status |
|------|---------|--------------|--------|
| 8001 | employee-service | `/api/v1/employees`, `/api/v1/departments` | CONFIRMED |
| 8002 | attendance-service | `/api/v1/attendance` | CONFIRMED |
| 8003 | leave-service | `/api/v1/leave` | CONFIRMED |
| 8004 | payroll-service | `/api/v1/payroll` | CONFIRMED |
| 8005 | hiring-service | `/api/v1/hiring` | CONFIRMED |
| 8006 | auth-service | `/api/v1/auth` | CONFIRMED (JWT-exempt) |
| 8007 | notification-service | `/api/v1/notifications` | CONFIRMED |
| 8008 | audit-service | `/api/v1/audit` | CONFIRMED |
| 8009 | workflow-service | `/api/v1/workflows` | CONFIRMED |
| 8010 | performance-service | `/api/v1/performance` | CONFIRMED |
| 8011 | engagement-service | `/api/v1/engagement` | CONFIRMED |
| 8012 | helpdesk-service | `/api/v1/helpdesk` | CONFIRMED |
| 8013 | reporting-analytics-service | `/api/v1/reporting` | CONFIRMED |
| 8014 | search-service | `/api/v1/search` | CONFIRMED |
| 8015 | expense-service | `/api/v1/expense` | CONFIRMED |
| 8016 | integration-service | `/api/v1/integrations` | CONFIRMED |
| 8017 | automation-service | `/api/v1/automations` | CONFIRMED |
| 8018 | travel-service | `/api/v1/travel` | CONFIRMED route; service PLANNED |
| 8019 | project-service | `/api/v1/projects` | CONFIRMED route; service PLANNED |
| 8020 | settings-service | `/api/v1/settings` | CONFIRMED |
| 8021 | compliance-service | `/api/v1/compliance` | TBD – REQUIRES VERIFICATION |
| 8022 | decision-service | `/api/v1/decisions` | TBD – REQUIRES VERIFICATION |
| 8023 | bank-service | `/api/v1/banking` | TBD – REQUIRES VERIFICATION |
| 8024 | whatsapp-service | `/api/v1/whatsapp` | TBD – REQUIRES VERIFICATION |

### Key Shared Modules (Python, under `backend/`)
`resilience.py`, `structured_logging.py`, `jwt_utils.py`, `rate_limiting.py`, `api_contract.py`, `event_outbox.py`, `outbox_system.py`, `persistent_store.py`, `tenant_support.py`, `error_registry.py`, `secrets_config.py`, `data_integrity.py`, `chaos_engine.py`, `background_jobs.py`, `background_jobs_api.py`

### Country Layer (`backend/country/`)
`base/` (interfaces), `pakistan/` (PK adapter — tax, compliance, payroll rules, statutory, banking), `dummy/` (test adapter)

---

## INTEGRATIONS DISCOVERED

| Integration | Purpose | Source | Owner Service |
|-------------|---------|--------|--------------|
| FBR adapter | Pakistan tax authority statutory filings | `backend/integrations/pakistan/fbr_adapter.py` | compliance-service |
| EOBI adapter | Employee old-age benefits institution filings | `backend/integrations/pakistan/eobi_adapter.py` | compliance-service |
| ATL adapter | Active taxpayer list verification (cached, 30-day TTL) | `backend/integrations/pakistan/atl_adapter.py` | compliance-service |
| Raast payment | Pakistan instant payment network | `backend/integrations/pakistan/raast_payment.py` | bank-service |
| Bank salary export | Bank salary disbursement CSV/Excel | `backend/integrations/pakistan/bank_salary.py` | bank-service |
| Payment reconciliation | Post-disbursement reconciliation | `backend/integrations/pakistan/payment_reconciliation.py` | bank-service |
| Biometric | Biometric device attendance import | `backend/integrations/biometric/` | attendance-service |
| WhatsApp | WhatsApp HR channel (identity mapping, message routing) | `backend/integrations/whatsapp/` | whatsapp-service |
| Accounting | Payroll accounting export | `backend/integrations/accounting/` | TBD – REQUIRES VERIFICATION (no confirmed gateway route for accounting/finance prefix) |

---

## DISCREPANCIES AND FINDINGS

### FINDING 1 (High): Parallel TypeScript Implementation — Not Wired to Production

`backend/middleware/*.ts`, `backend/cache/cache.service.ts`, `backend/health/health.controller.ts`, and `backend/metrics/metrics.ts` are TypeScript/Express modules. The actual deployed Python services run via a custom ASGI handler (`backend/docker/service_runtime.py`, uvicorn). No import path from any production `.py` service file to these `.ts` modules was found.

**Conclusion:** These TypeScript modules appear to be a parallel/prototype implementation (possibly an earlier Express-based design, a reference spec, or scaffolding for a future Node.js service layer) that is NOT wired into the `docker-compose.yml` deployment of the 24 domain services. Equivalent functionality is implemented in Python: `resilience.py` (circuit breaker), `rate_limiting.py` (rate limiting), `structured_logging.py` (logging), `api_contract.py` (response envelope), `api_gateway_service.py` (health/metrics endpoint).

**Action required:** Human review to confirm intended status — dead code, active spec, or roadmap item. Per "do not invent functionality" rule, no claim about these TypeScript modules' production role was made in `BACKEND_ARCHITECTURE.md` beyond documenting their existence and the unconfirmed wiring.

**Evidence:** `backend/middleware/*.ts`, `backend/cache/cache.service.ts`, `backend/docker/service_runtime.py`, `backend/docker-compose.yml`.

---

### FINDING 2 (High): `ewa-financial-service` Referenced in Canon but Not in docker-compose.yml

`backend/docs/canon/service-map.md` (the canonical service dependency map) references `ewa-financial-service` as a dependency of `bank-service` and `payroll-service` in at least one location. This service name does **not appear** in `docker-compose.yml` (24 domain services verified, ports 8001–8024). No `ewa_financial_service.py` or `ewa-financial-service/` directory was found in the backend.

**Conclusion:** Either (a) `ewa-financial-service` was planned/renamed and `service-map.md` was not updated, or (b) its functionality was merged into `bank-service` or another service. Flagged as a canon-vs-code discrepancy requiring human verification.

**Evidence:** `backend/docs/canon/service-map.md`, `backend/docker-compose.yml`.

---

### FINDING 3 (Medium): Country Resolver dev-seed is NOT Production-Ready

`backend/core/country_resolver.py` contains `seed_dev_defaults(resolver)` which registers the Pakistan adapter for `ORG_DEFAULT`. The module explicitly documents: "NOT for production use; production startup must load mappings from the database." No evidence of the database-driven country mapping loader was found in this discovery pass.

**Status:** TBD – REQUIRES VERIFICATION — how production deployments register country-to-adapter mappings at service startup.

**Evidence:** `backend/core/country_resolver.py`.

---

### FINDING 4 (Medium): In-Process Idempotency Cache (Not Persistent)

The API Gateway's idempotency enforcement (`_IdempotencyCache`, `api_gateway_service.py` lines 74-102) is an in-process memory structure (max 10,000 entries, 24h TTL). On gateway restart, all cached idempotency keys are lost. Under Docker Compose single-instance deployment this may be acceptable, but it is a known gap for multi-instance or restart-tolerant deployments.

**Evidence:** `backend/docker/api_gateway_service.py` lines 74-102.

---

### FINDING 5 (Medium): Dual Event Outbox Implementations

Two parallel outbox implementations coexist (see `EVENT_DISCOVERY_REPORT.md` for full detail):
- `event_outbox.py` → `EventOutbox` (KV-store-backed via `PersistentKVStore`, polling relay via `outbox.dispatch` background job)
- `outbox_system.py` → `OutboxManager` (SQL record-based with synchronous `enqueue`+`dispatch_pending`, retry/dead-letter support)

Which path is used by which services at runtime is TBD – REQUIRES VERIFICATION. The SQL schema (`007_event_outbox.sql`) and the `PersistentKVStore`-backed path are both present but their live usage split is unconfirmed.

**Evidence:** `backend/event_outbox.py`, `backend/outbox_system.py`, `backend/deployment/migrations/007_event_outbox.sql`.

---

### FINDING 6 (Low): `employee-service` Written Primarily in TypeScript

`backend/services/employee-service/` contains TypeScript files (`employee.controller.ts`, `employee.model.ts`, `employee.repository.ts`, `employee.routes.ts`, `employee.service.ts`, `employee.validation.ts`). The service is deployed via `docker-compose.yml` port 8001, but the docker-compose build uses `Dockerfile.services` (a Python-based image per service-base anchor). This means either (a) the TypeScript files are unused spec/prototype files while a Python handler exists elsewhere, or (b) there is a separate TS build not represented in the current Dockerfile.

**Parallel evidence:** `backend/employee_ui.py` and `backend/api/employee_portal.py` exist as Python files that likely implement the actual employee-service API routes.

**Status:** TBD – REQUIRES VERIFICATION — which files are the live employee-service implementation.

**Evidence:** `backend/services/employee-service/*.ts`, `backend/employee_ui.py`, `backend/api/employee_portal.py`, `backend/docker-compose.yml`.

---

### FINDING 7 (Low): Documents Contract for Missing Gateway Route

`contracts/hrms-h02-documents-contract.json` exists in the contracts directory (frontend page-archetype for a document management list view) but there is no `/api/v1/documents` gateway route in `routes.py` or `gateway-routes.json`, and no `documents-service` or document management service is found in `docker-compose.yml`.

**Status:** Gap — document management is either handled by another service under a different prefix, or the contract is aspirational/out-of-scope. Listed in `BACKEND_GAP_REGISTER.md`.

**Evidence:** `contracts/hrms-h02-documents-contract.json`, `backend/api-gateway/routes.py`.

---

## ITEMS REQUIRING VERIFICATION (TBD SUMMARY)

| Item | Where Documented |
|------|-----------------|
| Production country-adapter registration mechanism | `BACKEND_ARCHITECTURE.md` §12.3 |
| TypeScript middleware/cache/health/metrics — intended production role | `BACKEND_ARCHITECTURE.md` §5–§8 |
| `ewa-financial-service` — renamed, removed, or merged? | `BACKEND_ARCHITECTURE.md` §13 |
| Which outbox implementation (EventOutbox vs OutboxManager) is used per service | `EVENT_AND_QUEUE_ARCHITECTURE.md` |
| No publisher found for any `employee-service` domain events (EmployeeCreated, etc.) | `EVENT_DISCOVERY_REPORT.md` |
| event-catalog.md claims 143 events; table has 119 rows | `EVENT_DISCOVERY_REPORT.md` |
| Gateway routes for compliance/decision/banking/whatsapp | `BACKEND_ARCHITECTURE.md` §4.2, `ADR-001` §2 |
| Document management service / `/api/v1/documents` endpoint | `BACKEND_GAP_REGISTER.md` |
| Live employee-service implementation (TypeScript vs Python) | This report, Finding 6 |

---

## DOCUMENTS THAT REFERENCE MODULES NOT IN PRODUCTION DOCKER COMPOSE

| Canon/Document Reference | Actual Status |
|--------------------------|--------------|
| `service-map.md` → `ewa-financial-service` | Not in docker-compose.yml |
| `BACKEND_ARCHITECTURE.md` §5–§8 → TypeScript middleware/cache/health/metrics | Not wired to Python ASGI runtime |
| `automation_service.py` trigger model described as "event-triggered, scheduled, threshold-triggered" | Only event-triggered triggers found in `automation_contract.py` |
