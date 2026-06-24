# BACKEND ARCHITECTURE

Status: Draft
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This document describes the backend architecture of Meridian HCM exactly as implemented in the repository at `D:\SaaS\HRMS\backend`. It is a Phase 2 (Backend Authority Capture) deliverable: it documents reality, not intended/future-state design. All claims cite a file path. Anything not directly verifiable is marked `TBD – REQUIRES VERIFICATION`.

**Primary evidence sources:** `docker-compose.yml`, `/backend/docker/service_runtime.py`, `/backend/docker/api_gateway_service.py`, `/backend/api-gateway/routes.py`, `/backend/deployment/config/gateway-routes.json`, `/backend/docs/canon/service-map.md`, `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md`.

---

## 1. OVERALL ARCHITECTURE

**Pattern:** Microservices with a shared PostgreSQL database, fronted by a single API Gateway.

**Composition (verified in `D:\SaaS\HRMS\backend\docker-compose.yml`):**
- 1 PostgreSQL 16 instance (`postgres:16-alpine`, lines 14-29)
- 1 one-shot `migrations` container that runs SQL migrations before any service starts (lines 31-45)
- 24 domain microservices (employee-service through whatsapp-service, ports 8001-8024, lines 47-355)
- 1 API Gateway (`api-gateway`, port 8000, lines 357-443)
- 1 Next.js frontend (`frontend-ui`, port 3000→80, lines 445-458)

All 24 domain services share the same build context/Dockerfile (`Dockerfile.services`) via the `service-base` YAML anchor (`docker-compose.yml` lines 3-11) and the same `DATABASE_URL` pointing at the single `postgres` container — i.e., shared-database microservices, not database-per-service.

**Evidence:** `D:\SaaS\HRMS\backend\docker-compose.yml`

---

## 2. RUNTIME MODEL — CUSTOM ASGI HANDLER (NO FASTAPI/FLASK)

Per `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` §3, the chosen web framework is "None (custom ASGI handler)". This is implemented in:

- `D:\SaaS\HRMS\backend\docker\service_runtime.py` — generic per-service ASGI runtime. Provides:
  - `Route` dataclass (method, regex-style `{param}` pattern, handler) — `service_runtime.py` lines 38-43
  - `_match()` — converts `{name}` path segments into a regex and extracts path params — lines 51-57
  - `_build_response()` — builds the standard JSON response with security headers (`x-content-type-options: nosniff`, `x-frame-options: DENY`, `cache-control: no-store`, trace/request-id headers) — lines 60-72
  - `build_service_runtime(service_name)` — assembles the route table and shared context (`ctx`) for a given service — line 88 onward
  - Uses `uvicorn` as the ASGI server (imported line 16)

- `D:\SaaS\HRMS\backend\docker\api_gateway_service.py` — the API Gateway's own ASGI app, also built on `uvicorn`, using `urllib` for upstream HTTP calls (no `requests`/`httpx` dependency) — lines 14-18.

- `D:\SaaS\HRMS\backend\docker\common_service.py` — A lightweight `BaseHTTPRequestHandler`-based HTTP server (Python stdlib, **not** uvicorn). Responds only to `/health`, `/ready`, and `/` with standard success payloads. Contains no service business logic. It is a minimal stub/fallback server for health-check-only deployments — **not** a shared service bootstrap helper. (Read in full 2026-06-16: confirmed 78 lines.)

**Response envelope:** `api_contract.py` provides `success_payload` / `error_payload`, imported by both `service_runtime.py` (line 18) and `api_gateway_service.py` (line 20), implementing the `{status, data, meta, error}` envelope referenced in ADR-001 §7 principle 7.

**Evidence:** `D:\SaaS\HRMS\backend\docker\service_runtime.py`, `D:\SaaS\HRMS\backend\docker\api_gateway_service.py`, `D:\SaaS\HRMS\backend\api_contract.py`, `docs\06_decisions\ADR-001_PROJECT_FOUNDATION.md` §3 ("Web Framework: None (custom ASGI handler)").

---

## 3. SERVICE WIRING — docker-compose.yml

### 3.1 Service-to-port map (verified)

All 24 domain services plus gateway and frontend are declared with `SERVICE_NAME`, `PORT`, and `DATABASE_URL` environment variables. Full port table is in `docs/01_backend/SERVICE_CATALOG.md`.

### 3.2 Inter-service URL wiring (compile-time env vars)

Each service receives only the upstream service URLs it depends on, injected as `<SERVICE>_URL` environment variables pointing at the Docker Compose service DNS name and port, e.g.:

| Service | Injected upstream URLs | Evidence (docker-compose.yml) |
|---|---|---|
| `attendance-service` | `EMPLOYEE_SERVICE_URL`, `AUTH_SERVICE_URL` | lines 60-73 |
| `leave-service` | `EMPLOYEE_SERVICE_URL`, `AUTH_SERVICE_URL`, `PAYROLL_SERVICE_URL` | lines 74-88 |
| `payroll-service` | `EMPLOYEE_SERVICE_URL`, `ATTENDANCE_SERVICE_URL`, `LEAVE_SERVICE_URL`, `AUTH_SERVICE_URL` | lines 89-104 |
| `hiring-service` | `EMPLOYEE_SERVICE_URL`, `AUTH_SERVICE_URL` | lines 105-118 |
| `auth-service` | `JWT_ISSUER`, `JWT_AUDIENCE` (no upstream service URLs) | lines 119-132 |
| `notification-service` | `AUTH_SERVICE_URL` | lines 133-145 |
| `compliance-service` | `AUTH_SERVICE_URL`, `PAYROLL_SERVICE_URL` | lines 303-316 |
| `decision-service` | `AUTH_SERVICE_URL` | lines 317-329 |
| `bank-service` | `AUTH_SERVICE_URL`, `PAYROLL_SERVICE_URL` | lines 330-343 |
| `whatsapp-service` | `AUTH_SERVICE_URL` | lines 344-356 |
| all other services (employee, audit, workflow, performance, engagement, helpdesk, reporting-analytics, search, expense, integration, automation, travel, project, settings) | `DATABASE_URL` only (no inter-service URL env vars declared) | lines 47-302 |

Note: absence of an `<X>_SERVICE_URL` env var does not prove a service makes no HTTP call to that dependency — it only documents what is wired via Compose environment injection. Any additional runtime dependency resolution (e.g., hardcoded defaults, service discovery) is `TBD – REQUIRES VERIFICATION`.

### 3.3 API Gateway wiring

The `api-gateway` service (docker-compose.yml lines 357-443) is the only service exposed on a host port (8000) other than `postgres` (5432) and `frontend-ui` (3000). It receives a `<SERVICE>_SERVICE_URL` environment variable for **all 24** domain services (lines 366-389) and has a Compose `depends_on: condition: service_healthy` dependency on all 24 (lines 390-438), ensuring it starts only after every domain service passes its healthcheck.

The gateway's actual route table (which path prefixes it proxies) is defined in code (`/backend/api-gateway/routes.py`) and config (`/backend/deployment/config/gateway-routes.json`), independent of the full env-var map. The gateway exposes **25** routes (all 24 domain services except `background-jobs-service` have a gateway route prefix) — see §4.

**Evidence:** `D:\SaaS\HRMS\backend\docker-compose.yml` lines 357-443.

---

## 4. API GATEWAY ROUTE TABLE

### 4.1 Route resolution

`D:\SaaS\HRMS\backend\api-gateway\routes.py` defines `ROUTES: tuple[Route, ...]` — exactly **25** entries (lines 31–55), each mapping a path prefix (e.g. `/employees`) to an `upstream_service` (e.g. `employee-service`). All paths are prefixed with `API_VERSION_PREFIX = "/api/v1"` (line 6).

`D:\SaaS\HRMS\backend\deployment\config\gateway-routes.json` contains the same 25 route names mapped to `http://<service>:<port>` upstream base URLs. The two files agree exactly on the set of 25 route names (`employees, departments, performance, attendance, leave, travel, projects, payroll, hiring, auth, workflows, audit, notifications, engagement, helpdesk, reporting, search, expense, integrations, automations, settings, compliance, decisions, banking, whatsapp`). (Verified 2026-06-16.)

`resolve_route()` (routes.py lines 67–77) matches the longest applicable prefix against `full_path_prefix` (`/api/v1/<prefix>`) first, then falls back to `legacy_path_prefix` (bare `/<prefix>`).

### 4.2 Confirmed routes — all 24 domain services covered

All 24 domain services except `background-jobs-service` (which has no gateway route by design) have confirmed gateway route entries in both `routes.py` and `gateway-routes.json` (verified 2026-06-16):

- Routes 1–21: `employees, departments, performance, attendance, leave, travel, projects, payroll, hiring, auth, workflows, audit, notifications, engagement, helpdesk, reporting, search, expense, integrations, automations, settings`
- Routes 22–25 (previously unconfirmed — now verified): `compliance` (line 52 / `gateway-routes.json` line 25), `decisions` (line 53 / line 26), `banking` (line 54 / line 27), `whatsapp` (line 55 / line 28)

The earlier TBD annotation for these 4 services is resolved. Per `docs/00_authority/FEATURE_SCOPE.md` F-014 (compliance), F-015 (banking), F-016 (WhatsApp) and ADR-001 §2, all 4 are client-facing via the standard `/api/v1/{prefix}` path.

### 4.3 Gateway middleware / cross-cutting behavior (in `api_gateway_service.py`)

| Concern | Implementation | Evidence |
|---|---|---|
| JWT validation | `verify_hs256_jwt` from `jwt_utils.py`; exempt prefixes `/health`, `/ready`, `/metrics`, `/openapi.json`, `/docs`, `/api/v1/auth/` | `api_gateway_service.py` lines 21, 50-55 |
| Rate limiting | `SlidingWindowRateLimiter` — default 200 req/min/IP (`GATEWAY_RATE_LIMIT`, `GATEWAY_RATE_WINDOW_SECONDS`) | `api_gateway_service.py` lines 22, 44-47; `rate_limiting.py` |
| Route-level RBAC | `_ROUTE_ROLE_MAP` — restricts `/api/v1/payroll`, `/api/v1/audit`, `/api/v1/hiring`, `/api/v1/reporting` to specific roles | `api_gateway_service.py` lines 65-71 |
| CORS | `CORS_ALLOWED_ORIGINS` (default `*`), fixed allowed methods/headers list | `api_gateway_service.py` lines 57-60 |
| Body size limit | 1 MB default (`MAX_REQUEST_BODY_BYTES`) | `api_gateway_service.py` line 63 |
| Idempotency | In-process `_IdempotencyCache` (TTL 24h, max 10,000 entries), keyed presumably by `Idempotency-Key` header | `api_gateway_service.py` lines 74-102 |
| Metrics | In-process Prometheus-text accumulator (`_build_metrics_text`) — `gateway_requests_total`, `gateway_request_duration_seconds_total`, `gateway_errors_total` | `api_gateway_service.py` lines 104-137 |
| Circuit breaker / retry | `CircuitBreaker`, `CircuitBreakerOpenError`, `run_with_retry` from `resilience.py` | `api_gateway_service.py` line 23; `resilience.py` |
| Structured logging | `configure_logging`, `set_correlation_id` from `structured_logging.py` | `api_gateway_service.py` line 24 |

**Evidence:** `D:\SaaS\HRMS\backend\api-gateway\routes.py`, `D:\SaaS\HRMS\backend\deployment\config\gateway-routes.json`, `D:\SaaS\HRMS\backend\docker\api_gateway_service.py`.

---

## 5. MIDDLEWARE STACK — `/backend/middleware/`

`D:\SaaS\HRMS\backend\middleware\` contains **TypeScript** files: `audit-store.ts`, `audit.ts`, `circuit-breaker.ts`, `error-handler.ts`, `logger.ts`, `rate-limit.ts`, `request-id.ts`, `retry.ts`, `tenant-context.ts`, `throttle.ts`, `validation.ts`.

These files reference Express types (`Request`, `Response`, `NextFunction` from `'express'` — confirmed by reading `D:\SaaS\HRMS\backend\health\health.controller.ts` and `D:\SaaS\HRMS\backend\metrics\metrics.ts`, both of which `import { ... } from 'express'`).

**Discrepancy:** The actual deployed Python domain services (`docker-compose.yml`) run via the custom ASGI runtime (`/backend/docker/service_runtime.py`, uvicorn) — not Express/Node. A repository-wide search for references to these `.ts` middleware modules from `.py` files found **no imports from production service code**. Python test files (`test_settings_domain.py`, `test_audit_logging_standard.py`, `test_employee_service_domain.py`, etc.) test Python domain behavior — they do not and cannot import TypeScript files. The grep matches were on filename/keyword coincidence (shared domain concepts). **Resolved (Phase 3.25 UC-007):** TypeScript middleware files are confirmed dead code; Python tests test Python implementations only.

**Conclusion:** The `/backend/middleware/`, `/backend/cache/`, `/backend/health/`, `/backend/metrics/` TypeScript modules appear to be a separate, parallel implementation (possibly a reference/spec implementation or earlier prototype for an Express-based runtime) that is **not wired into the docker-compose deployment** of the 24 domain services or the API gateway. Equivalent cross-cutting behavior for the live Python services is implemented instead in `resilience.py`, `rate_limiting.py`, `structured_logging.py`, `jwt_utils.py`, and per-service code under `/backend/docker/`. This is flagged for the consistency report (§ BACKEND_ARCHITECTURE_REPORT.md).

**Evidence:** `D:\SaaS\HRMS\backend\middleware\*.ts`, `D:\SaaS\HRMS\backend\health\health.controller.ts`, `D:\SaaS\HRMS\backend\cache\cache.service.ts`, `D:\SaaS\HRMS\backend\metrics\metrics.ts`.

---

## 6. CORE SHARED MODULES — `/backend/core/`

`D:\SaaS\HRMS\backend\core\` contains:
- `__init__.py`
- `country_resolver.py` — `CountryResolver` class. Routes an `organization_id` to a country adapter (e.g., Pakistan) via registered mappings (`register_adapter`, `register_mapping`, `resolve`/`get_adapter`). Per its own docstring: "no service may import any country module directly. All country logic is accessed through this resolver." Includes `seed_dev_defaults()` which registers the Pakistan adapter for `ORG_DEFAULT` and a `dummy` adapter for `ORG_DUMMY` — explicitly marked "NOT for production use; production startup must load mappings from the database."

**Evidence:** `D:\SaaS\HRMS\backend\core\country_resolver.py`.

Other shared modules live directly under `/backend/` (not under `/backend/core/`):

| Module | Role | Evidence |
|---|---|---|
| `resilience.py` | `Observability`, `CircuitBreaker`, `CircuitBreakerOpenError`, `run_with_retry`, `run_with_timeout`, log sanitization (`SENSITIVE_FIELD_NAMES`), error classification | `D:\SaaS\HRMS\backend\resilience.py` |
| `structured_logging.py` | `configure_logging`, `set_correlation_id` | `D:\SaaS\HRMS\backend\structured_logging.py` |
| `jwt_utils.py` | `verify_hs256_jwt` and related JWT helpers | `D:\SaaS\HRMS\backend\jwt_utils.py` |
| `rate_limiting.py` | `SlidingWindowRateLimiter` | `D:\SaaS\HRMS\backend\rate_limiting.py` |
| `api_contract.py` | `success_payload`, `error_payload` response envelope | `D:\SaaS\HRMS\backend\api_contract.py` |
| `event_outbox.py` / `outbox_system.py` | Event outbox pattern (see §9) | `D:\SaaS\HRMS\backend\event_outbox.py`, `D:\SaaS\HRMS\backend\outbox_system.py` |
| `persistent_store.py` | `PersistentKVStore` — generic persistence helper used by `EventOutbox` | `D:\SaaS\HRMS\backend\persistent_store.py` |
| `tenant_support.py` | `DEFAULT_TENANT_ID`, `assert_tenant_access`, `normalize_tenant_id` | `D:\SaaS\HRMS\backend\tenant_support.py` |
| `error_registry.py` | Central error code registry | `D:\SaaS\HRMS\backend\error_registry.py` |
| `secrets_config.py` | Secrets/config loading | `D:\SaaS\HRMS\backend\secrets_config.py` |
| `data_integrity.py` | Data integrity helpers | `D:\SaaS\HRMS\backend\data_integrity.py` |
| `chaos_engine.py` | Resilience/chaos testing harness (per ADR-001 R-003 "chaos engine tests resilience") | `D:\SaaS\HRMS\backend\chaos_engine.py` |
| `background_jobs.py` / `background_jobs_api.py` | In-process background job execution (no external broker per ADR-001 §4) | `D:\SaaS\HRMS\backend\background_jobs.py`, `D:\SaaS\HRMS\backend\background_jobs_api.py` |

---

## 7. CACHING — `/backend/cache/`

`D:\SaaS\HRMS\backend\cache\cache.service.ts` defines `CacheService`, an in-memory TTL map (`Map<string, CacheEntry<unknown>>`) with `get`/`set`/`invalidate`, max-entries eviction, and JSON deep-clone on read/write.

Per ADR-001 §4 ("Known Constraints — Technical"): "No caching layer (Redis/Memcached not present in codebase)."

As with §5, `cache.service.ts` is a TypeScript module with no confirmed import path from the Python ASGI services that are actually deployed via `docker-compose.yml`. The only in-process caching confirmed in the live Python runtime is the API Gateway's `_IdempotencyCache` (`api_gateway_service.py` lines 76-102) and the ATL verification cache in `integrations/pakistan/atl_adapter.py` (`_atl_cache` module-level dict, 30-day TTL). **No general-purpose cache layer exists for domain services** in the Python runtime — resolved Phase 3.25. The TypeScript `cache.service.ts` is dead code (see §5). Live Python caching is limited to: (1) API Gateway `_IdempotencyCache` (in-process), (2) ATL adapter `_atl_cache` (module-level dict, 30-day TTL). Domain services operate without caching (consistent with ADR-001 §4 "No caching layer").

**Evidence:** `D:\SaaS\HRMS\backend\cache\cache.service.ts`, `D:\SaaS\HRMS\backend\docker\api_gateway_service.py` lines 76-102, `D:\SaaS\HRMS\backend\integrations\pakistan\atl_adapter.py`, `docs\06_decisions\ADR-001_PROJECT_FOUNDATION.md` §4.

---

## 8. HEALTH CHECKS — `/backend/health/`

`D:\SaaS\HRMS\backend\health\health.controller.ts` defines an Express `HealthController` with `getHealth` (returns service name, status, traceId, metrics snapshot), `getReady`, and `getMetrics` (metrics snapshot + last 20 structured log records). This is again a TypeScript/Express module of unconfirmed production wiring (see §5).

The **actual, deployed** health checks are defined per-service in `docker-compose.yml` as Docker healthchecks:
```
CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:<port>/health')"
```
for all 24 domain services (e.g., lines 54-58 for employee-service), and the API Gateway uses `/ready` (lines 439-443).

**`/health` and `/ready` implementation confirmed** (`service_runtime.py` lines 498–508): These are handled inline in the `_dispatch()` function, BEFORE any registered route is matched:
```python
if path in ("/health", "/ready"):
    return _build_response(200, success_payload({
        "service": SERVICE_NAME, "service_status": "ok",
        "runtime": "domain", "routes": CONTEXT.get("routes", []),
        "metrics": OBSERVABILITY.metrics.snapshot(),
    }, trace_id))
```
They return the standard `api_contract.py` success envelope. The `/` root path (line 510) returns `{"service", "message": "domain runtime active", "routes": [...]}`. All three are not registered in the route table — they are hardcoded guards in `_dispatch()`. Verified 2026-06-16.

**Evidence:** `D:\SaaS\HRMS\backend\health\health.controller.ts`, `D:\SaaS\HRMS\backend\docker-compose.yml` (healthcheck blocks for all services).

---

## 9. METRICS / OBSERVABILITY — `/backend/metrics/`

`D:\SaaS\HRMS\backend\metrics\metrics.ts` defines `ServiceMetrics` (Express-oriented): tracks `requestCount`, `errorCount`, latency totals/max, last 50 requests, per-route and per-tenant buckets, exposed via `snapshot()`. Same TS/Express caveat as §5/§7/§8 applies.

The **deployed** Python observability stack is:
- `resilience.py` → `Observability` class — used by `EventOutbox` (`event_outbox.py` line 28, 35) and the API Gateway (`OBSERVABILITY = Observability("api-gateway")`, `api_gateway_service.py` line 42). Provides `.logger` (structured logging) and `.record_trace(...)`.
- `structured_logging.py` → `configure_logging`, `set_correlation_id` — used by both `service_runtime.py` and `api_gateway_service.py`.
- API Gateway in-process Prometheus-text metrics accumulator (`_build_metrics_text`, `api_gateway_service.py` lines 104-137) exposing `gateway_requests_total`, `gateway_request_duration_seconds_total`, `gateway_errors_total` — likely served at `/metrics` (exempted from JWT at line 55).
- `CentralErrorLogger` from `resilience.py`, instantiated as `ERROR_LOGGER = CentralErrorLogger("api-gateway")` (`api_gateway_service.py` line 41).

**Evidence:** `D:\SaaS\HRMS\backend\metrics\metrics.ts`, `D:\SaaS\HRMS\backend\resilience.py`, `D:\SaaS\HRMS\backend\docker\api_gateway_service.py`.

---

## 10. RESILIENCE / CIRCUIT BREAKER — `/backend/resilience.py`

`D:\SaaS\HRMS\backend\resilience.py` (read in part; ~700 lines based on line offsets observed) provides:

| Component | Description | Lines |
|---|---|---|
| `Observability` | Structured logging + trace recording class | line 407 |
| `CircuitBreakerOpenError` | Exception raised when breaker is open | line 465 |
| `CircuitBreaker` | Failure-threshold-based breaker (`failure_threshold=3` default, `recovery_timeout=5.0`s default); `.call(func)` wraps a callable, opens after N consecutive failures, half-opens after `recovery_timeout` | lines 608-636 |
| `run_with_timeout` | Runs a callable in a `ThreadPoolExecutor` with a timeout, raises `OperationTimeoutError` | lines 639-646 |
| `run_with_retry` | Exponential-backoff retry wrapper (`attempts=3`, `base_delay=0.05`, `timeout_seconds=1.0` defaults), with `retryable` predicate and `on_retry` callback | lines 649-670+ |
| `sanitize_log_context` | Redacts `SENSITIVE_FIELD_NAMES` (password, tokens, bank_account, tax_id, ssn, etc.) from logged dicts/lists | lines 53-64 |
| `classify_error` | Maps exceptions/status codes to error categories (`validation`, etc.); `DEPENDENCY_ERROR_TYPES` set includes `ConnectionError`, `TimeoutError`, `CircuitBreakerOpenError` | lines 32-40, 90-100+ |
| `new_trace_id`, `infer_tenant_id`, `infer_correlation_id` | Tracing/tenant helper functions | lines 45-87 |

`CircuitBreaker` and `run_with_retry` are imported and used directly by the API Gateway (`api_gateway_service.py` line 23). **Domain service usage confirmed** (grep 2026-06-16): `CircuitBreaker` is also used in `backend/services/hiring_service/service.py` (wraps external integration calls) and `backend/supervisor_engine.py` (service orchestration layer). These are the only confirmed domain-level usages; other services may use `run_with_retry` without `CircuitBreaker` directly — not exhaustively verified.

ADR-001 R-001 states: "Circuit breaker in place; migration plan TBD" for the single-DB bottleneck risk — consistent with this module's existence.

**Evidence:** `D:\SaaS\HRMS\backend\resilience.py`, `D:\SaaS\HRMS\backend\docker\api_gateway_service.py` line 23, `docs\06_decisions\ADR-001_PROJECT_FOUNDATION.md` §6 (R-001).

---

## 11. EVENT OUTBOX PATTERN

Per ADR-001 §2 "Event Architecture": "All domain events written to `service_outbox` table atomically with triggering mutation. Outbox processor publishes events asynchronously. 143 domain events cataloged in `/backend/docs/canon/event-catalog.md`. No external message broker — in-process event processing."

**Two complementary outbox implementations** (both confirmed 2026-06-16):

**Implementation 1 — `event_outbox.py` → `EventOutbox`** (simpler staging layer):
- `OutboxEvent` dataclass: `event_id`, `tenant_id`, `aggregate_type`, `aggregate_id`, `event_name`, `payload`, `trace_id`, `occurred_at`, `published_at`, `failed_attempts`, `created_at`
- `stage_event()` / `stage_canonical_event()` — write events via `PersistentKVStore` (namespace `event_outbox`, service `background-jobs`); thread-safe via `RLock`
- `dispatch_pending(dispatcher, *, tenant_id, max_events)` — calls dispatcher callable per pending event; marks published/failed; returns `{dispatched_count, failed_count, dispatched_event_ids, failures}`
- `pending_events()` / `list_events()` / `mark_published()` / `mark_failed()` / `get_event()` — management API

**Implementation 2 — `outbox_system.py` → `OutboxManager`** (full-featured, newer):
- Wraps `ensure_event_contract()` from `event_contract.py` — validates events against `EventRegistry` before staging
- Uses `PersistentKVStore` for three stores: `outbox_records`, `processed_events`, `dispatch_log`
- `enqueue()` — validates against EventRegistry, creates `OutboxRecord` with status `pending`; supports `correlation_id` and `idempotency_key`
- `dispatch_pending(publisher, *, attempts, retryable)` — uses `run_with_retry()` with configurable backoff; on failure pushes to `DeadLetterQueue`
- `consume_once(consumer_name, event, handler)` — idempotent consumer using `IdempotencyStore`; deduplication key is `{consumer_name}:{event_id}`

**Relationship:** `EventOutbox` is the simpler legacy layer; `OutboxManager` is the production-grade successor with event contract enforcement, retry, DLQ, and at-least-once consumer semantics. Both use `PersistentKVStore`.

**SQL migration:** `backend/deployment/migrations/007_event_outbox.sql` — confirmed present (glob 2026-06-16). Defines the `service_outbox` table.

`D:\SaaS\HRMS\backend\persistent_store.py` — `PersistentKVStore`, the generic key-value persistence layer used by both outbox implementations.

**Evidence:** `D:\SaaS\HRMS\backend\event_outbox.py`, `D:\SaaS\HRMS\backend\outbox_system.py`, `D:\SaaS\HRMS\backend\persistent_store.py`, `docs\06_decisions\ADR-001_PROJECT_FOUNDATION.md` §2.

---

## 12. COUNTRY-LAYER ISOLATION — `/backend/country/`

Per `D:\SaaS\HRMS\backend\docs\canon\country-layer.md`: the country abstraction layer keeps payroll core logic country-agnostic while isolating tax/compliance/statutory/banking logic per jurisdiction. Architecture rule (also stated in `core/country_resolver.py`): "no service may import any country module directly. All country logic is accessed through [`CountryResolver`]."

### 12.1 Directory layout (verified via glob)

```
backend/country/
├── __init__.py
├── base/                       # interface definitions
│   ├── compliance_engine.py
│   ├── payroll_rules.py
│   ├── tax_engine.py
│   ├── statutory_validator.py
│   ├── banking_interface.py
│   └── __init__.py
├── pakistan/                    # PK adapter implementation
│   ├── compliance_engine.py
│   ├── tax_engine.py
│   ├── payroll_rules.py
│   ├── statutory.py
│   ├── banking.py
│   └── __init__.py
└── dummy/                       # test/architecture-test adapter
    ├── tax_engine.py
    ├── compliance_engine.py
    ├── payroll_rules.py
    ├── banking.py
    ├── statutory_validator.py
    └── __init__.py
```

### 12.2 Country-layer interfaces (per `country-layer.md`)

| Interface | Method(s) | Used by |
|---|---|---|
| `TaxEngineInterface` | `calculate_tax(input)` | payroll-service (via resolver) |
| `ComplianceEngineInterface` | `validate_payroll(input)`, `generate_reports(input)` | compliance-service |
| `PayrollRulesInterface` | `apply_rules(input)` | payroll-service |
| `StatutoryValidatorInterface` | `validate_employee(employee_data)`, `validate_payroll_readiness(payroll_input)`, `get_validation_rules()` | compliance-service / payroll pre-payroll gate |
| `BankingInterface` | `build_raast_payment_export(payload)`, `generate_salary_bank_csv(payload)`, `generate_salary_bank_excel_rows(payload)`, `reconcile_payroll_payments(data)` | bank-service |

`country-layer.md` explicitly states `BankService` accepts `CountryResolver` at construction and "no country conditionals (`if country == ...`) inside `BankService`."

### 12.3 Resolution mechanism

`D:\SaaS\HRMS\backend\core\country_resolver.py` — `CountryResolver`:
- `register_adapter(adapter_key, adapter_cls)` / `register_mapping(organization_id, country_code, adapter_key)` — startup-time registration.
- `resolve(organization_id)` / `get_adapter(organization_id)` — per-request lookup, returns an adapter instance.
- `seed_dev_defaults(resolver)` — dev/test-only seed mapping `ORG_DEFAULT → PK → pakistan` adapter and `ORG_DUMMY → XX → dummy` adapter. Explicitly documented as "NOT for production use."

### 12.4 Production bootstrap procedure (ARG-003 — RESOLVED)

**Status: IMPLEMENTED.** The earlier finding that "the startup wiring is NOT yet implemented" was incorrect — the bootstrap was implemented in `service_runtime.py` and not seen during the initial documentation pass.

**Implementation** (`backend/docker/service_runtime.py` lines 34–65, called at line 550):

`_bootstrap_country_resolver()` is called in the ASGI `lifespan.startup` handler:
```python
if event["type"] == "lifespan.startup":
    _bootstrap_country_resolver()
```

The function reads the `COUNTRY_ORG_MAPPINGS` environment variable (format: `org_id:country_code:adapter_key[,...]`, e.g. `ORG_DEFAULT:PK:pakistan,ORG_ACME:PK:pakistan`). If set:
1. Registers the `PakistanAdapter` via `_COUNTRY_RESOLVER.register_adapter("pakistan", PakistanAdapter)`
2. Parses each `org_id:country_code:adapter_key` triplet and calls `_COUNTRY_RESOLVER.register_mapping(org_id, country_code, adapter_key)`

If `COUNTRY_ORG_MAPPINGS` is not set, falls back to `seed_dev_defaults(_COUNTRY_RESOLVER)` (dev only, logs a warning).

**Env var required for production:** `COUNTRY_ORG_MAPPINGS` must be set per-service for each tenant organisation that uses payroll/compliance/banking. The shared `_COUNTRY_RESOLVER` module-level instance (line 31) is populated at startup and injected into service constructors.

**Gap ARG-003: CLOSED.** The production bootstrap is fully implemented. No additional service startup hook is required.

**Evidence:** `backend/docker/service_runtime.py` lines 31–65 (`_COUNTRY_RESOLVER` definition and `_bootstrap_country_resolver()`), line 550 (lifespan startup call), verified 2026-06-16.

**Evidence:** `D:\SaaS\HRMS\backend\docs\canon\country-layer.md`, `D:\SaaS\HRMS\backend\core\country_resolver.py`, `D:\SaaS\HRMS\backend\country\**`.

---

## 13. SERVICE DEPENDENCY RELATIONSHIPS

Two complementary sources document inter-service dependencies:

1. **`docker-compose.yml` environment wiring** (§3.2) — shows which `<SERVICE>_URL` variables are injected, i.e., what a service *can* call directly via Compose DNS.
2. **`/backend/docs/canon/service-map.md`** — narrative "Dependencies" sections per service, which include both HTTP-API dependencies and read-model/event dependencies that aren't necessarily reflected as env vars (e.g., `decision-service` depends on `payroll-service`, `attendance-service`, `compliance-service`, `employee-service`, `audit-service`, `notification-service` per canon, but `docker-compose.yml` only injects `AUTH_SERVICE_URL` for `decision-service`, lines 317-329).

This means cross-service calls beyond `auth-service`/`employee-service`/`payroll-service` (the most commonly-injected URLs) may occur via mechanisms not visible in `docker-compose.yml` — e.g., hardcoded defaults in service code, or via read models / event outbox rather than direct HTTP. Exhaustive verification of every dependency edge in `service-map.md` against actual HTTP client code in each service's source is `TBD – REQUIRES VERIFICATION`.

**High-confidence dependency edges (confirmed by both `docker-compose.yml` env wiring AND canon):**

| Service | Confirmed upstream dependencies |
|---|---|
| attendance-service | employee-service, auth-service |
| leave-service | employee-service, auth-service, payroll-service |
| payroll-service | employee-service, attendance-service, leave-service, auth-service |
| hiring-service | employee-service, auth-service |
| notification-service | auth-service |
| compliance-service | auth-service, payroll-service |
| decision-service | auth-service |
| bank-service | auth-service, payroll-service |
| whatsapp-service | auth-service |

All other canon-documented dependency edges (e.g., `bank-service → ewa-financial-service`, `decision-service → attendance-service/compliance-service`, `search-service → background-jobs`) are **not** reflected in `docker-compose.yml` environment variables and are therefore `TBD – REQUIRES VERIFICATION` as direct-HTTP edges — they may be implemented via event outbox / read-model consumption instead. Note also that `ewa-financial-service` and `audit-service`/`workflow-service` are referenced extensively in `service-map.md` dependency lists; `audit-service` and `workflow-service` ARE present in `docker-compose.yml` (ports 8008, 8009) but `ewa-financial-service` was **not found** as a docker-compose service — see `BACKEND_ARCHITECTURE_REPORT.md` for this discrepancy.

**Evidence:** `D:\SaaS\HRMS\backend\docker-compose.yml`, `D:\SaaS\HRMS\backend\docs\canon\service-map.md`.

---

## 14. SUMMARY TABLE — KEY ARCHITECTURAL FILES

| Concern | File(s) |
|---|---|
| Service runtime (ASGI) | `backend/docker/service_runtime.py`, `backend/docker/common_service.py` |
| API Gateway | `backend/docker/api_gateway_service.py`, `backend/api-gateway/routes.py`, `backend/api-gateway/tenant.py`, `backend/api-gateway/load_control.py`, `backend/api-gateway/dashboard_ui.py` |
| Gateway route config | `backend/deployment/config/gateway-routes.json` |
| Response envelope | `backend/api_contract.py` |
| Resilience | `backend/resilience.py` |
| Rate limiting | `backend/rate_limiting.py` |
| JWT | `backend/jwt_utils.py` |
| Structured logging | `backend/structured_logging.py` |
| Country layer | `backend/core/country_resolver.py`, `backend/country/**` |
| Event outbox | `backend/event_outbox.py`, `backend/outbox_system.py`, `backend/persistent_store.py` |
| Tenant support | `backend/tenant_support.py` |
| Error registry | `backend/error_registry.py` |
| Background jobs | `backend/background_jobs.py`, `backend/background_jobs_api.py` |
| Deployment orchestration | `backend/docker-compose.yml`, `backend/Dockerfile*`, `backend/deployment/**` |
| (Unwired/TS) Middleware, cache, health, metrics | `backend/middleware/*.ts`, `backend/cache/cache.service.ts`, `backend/health/health.controller.ts`, `backend/metrics/metrics.ts` |
