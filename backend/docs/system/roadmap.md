# Roadmap — Execution Order

## Overview

Five sequential phases. Each phase must be stable before the next begins.
Phase 1 is the prerequisite for all others.

---

## Phase 1 — Architecture Cleanup (Foundation)

**Goal:** Enforce clean architecture so all subsequent work builds on solid ground.

### Deliverables
- Country abstraction layer enforced across all services
- No hardcoded country logic in any service
- Canonical service map with all service boundaries defined
- API standards applied across all services (envelope, status codes, pagination)
- Event catalog and read-model catalog complete
- Domain model canonical and internally consistent
- All services isolated with clean interfaces

### Status (as of Session 8 — 2026-04-14)
- ✅ Country abstraction layer: implemented and data-driven (`core/country_resolver.py`)
- ✅ Service map: complete (23 services, plus `workflow-service`/`audit-service` as cross-cutting infra)
- ✅ API standards: documented and enforced via QC gates
- ✅ Event catalog, read-model catalog, domain model: documented and overlaid (Pass 3 complete — G43–G48 closed)
- ✅ All new services implemented: `compliance_api.py`, `decision_api.py`, `bank_service.py` + `banking_api.py`, `whatsapp_service.py` + `whatsapp_api.py`, helpdesk, automation, engagement, expense
- ✅ Central error registry (SB-G03): `error_registry.py` — 22 codes, typed with resolution_steps, extensible via `register_error()`
- ✅ HRMS Spec overlay (Session 6, SPEC-G01–SPEC-G08): DecisionCard fields, AI output contract, DisbursementState, StatutoryValidatorInterface, leave→payroll effect, manual compliance fallback, service manifest
- ✅ Session 7 final integrity (S7-G01–S7-G05): Pakistan import isolation, DummyAdapter, docker-compose + service-map updated, E2E payroll-to-bank test, import health test
- ✅ Session 8 master docs overlay (S8-G01–S8-G08): BankingInterface, dual-country proof, travel/project IMPLEMENTED, MASTER BUILD SPEC updated, behavior spec merged, market research merged

---

## Phase 2 — Pakistan Payroll + Compliance Hardening

**Goal:** Zero-error payroll and fully automated statutory compliance for Pakistan.

### Deliverables
- Pakistan tax engine (FBR slabs, filer/non-filer, CNIC validation)
- Pakistan payroll rules (allowances, deductions, gratuity/PF)
- Compliance validation gate: blocks payroll finalization if not passed
- FBR Annexure-C generation
- EOBI PR-01 contribution reports
- PESSI/SESSI returns (multi-province)
- Compliance submission lifecycle (DRAFT → ACK)
- Audit trail for all statutory submissions
- Bank disbursement files + Raast payout integration
- Reconciliation engine

### Status (as of Session 8 — 2026-04-14)
- ✅ Pakistan tax engine: implemented (`country/pakistan/tax_engine.py`)
- ✅ Pakistan payroll rules: implemented with statutory violations (`country/pakistan/payroll_rules.py`)
- ✅ Pakistan statutory: fully implemented (`country/pakistan/statutory.py`) — filer surcharge, exempt allowances, EOBI/PESSI math, WPPF, WWF, ATL filer verification, runtime slab update (G33–G42 all DONE)
- ✅ Specs: `docs/specs/country/pakistan/compliance.md`, `payroll.md`
- ✅ Compliance service: `services/compliance_service.py` + `compliance_api.py` (9 endpoints)
- ✅ Bank service + Raast: `bank_service.py` + `banking_api.py` (11 endpoints)
- ⚠️ S3 partial: `check_payroll_gate()` implemented in `decision_api.py` but full wiring into `payroll_service.py mark_paid()` deferred (G22) — needs integration test coverage first

---

## Phase 3 — Decision Engine + AI Guardian

**Goal:** Replace dashboards with decisions. Surface actionable intelligence across all domains.

### Deliverables
- AI Payroll Guardian: salary spike, overtime anomaly, missing deductions, ghost employee detection
- Decision Cards with risk score, confidence, explanation, reversibility
- Human-in-the-loop gates for High-risk cards
- Manager dashboard decision-first redesign
- Cross-domain anomaly signals from attendance, compliance, performance
- Reporting analytics service with predictive insights

### Status (as of Session 8 — 2026-04-14)
- ✅ Decision system canon: `docs/canon/decision-system.md`
- ✅ Manager dashboard spec: `docs/specs/ui/manager_dashboard.md`
- ✅ Decision service: `decision_api.py` — 7 endpoints + copilot. Wires DecisionEngine, PayrollGuardian, GovernanceService, HRCopilot
- ✅ Reporting analytics: `reporting_analytics_api.py` + InsightEngine wired (`get_anomaly_insights()`)
- ✅ Manager dashboard verified decision-first (G29 DONE)
- ✅ AI output contract complete (SB-G01): all 3 predictive models now return `{prediction, confidence, explanation, supporting_signals}` (renamed from `supporting_data` under SPEC-G02 — see `qc-suite.md` Tier 5 SPEC-G02 row)
- ✅ Payroll guardian thresholds configurable per tenant (SB-G04): `PayrollGuardian(thresholds={...})` — no hardcoded limits

---

## Phase 4 — WhatsApp + Mobile Expansion

**Goal:** Full HRMS functionality through WhatsApp and low-bandwidth mobile.

### Deliverables
- WhatsApp service: identity mapping, OTP, session management
- Payslip retrieval via WhatsApp (secure, expiring links)
- Leave application and balance check via WhatsApp
- Manager approval actions via WhatsApp
- Attendance alerts push via WhatsApp
- Mobile-optimized API payloads (compact, step-by-step)
- Low-bandwidth mode for unstable network environments

### Status (as of Session 8 — 2026-04-14)
- ✅ WhatsApp spec: `docs/specs/integrations/whatsapp.md`
- ✅ Experience layer spec: `docs/specs/experience-layer.md`
- ✅ WhatsApp service: `whatsapp_service.py` + `whatsapp_api.py` — identity/OTP/session/inbound/outbound (8 endpoints)
- ✅ Mobile layer: `services/mobile_gateway.py` + `docs/specs/mobile-layer.md`
- ✅ WhatsApp command registry (SB-G05): `CommandRegistry` class — extensible, adapters add commands without touching webhook.py

---

## Phase 5 — Multi-Country Rollout

**Goal:** Add new countries without changing any core service.

### Deliverables
- Country abstraction layer (base interfaces)
- Pakistan adapter as reference implementation
- Second adapter proving architecture requires no service changes
- Resolver handles multiple country mappings per tenant

### Status
- ✅ Country abstraction layer: complete and tested
- ✅ Pakistan adapter: implemented and QC-passing
- ✅ DummyAdapter (country/dummy/): proves architecture — zero service changes required
- ✅ Phase complete. Additional country adapters added on demand as new markets require them.

---

## Execution Constraints

- Phases are sequential. Phase 2 cannot be hardened without Phase 1 clean architecture.
- Phase 3 depends on Phase 2 payroll data quality (can't detect anomalies in broken payroll data).
- Phase 4 depends on Phase 2 (payslip via WhatsApp requires accurate payroll) and Phase 3 (approval actions require decision-first workflows).
- Phase 5 is additive — new adapters only, no core service changes permitted.

---

## Related Documents
- System purpose: `docs/system/system-purpose.md`
- Success criteria: `docs/system/success-criteria.md`
- Intent/build alignment: `docs/system/intent_build_alignment.md`

---

## Phase 6 — Production Hardening (Infrastructure Uplift)

**Goal:** Take the backend from functional to production-grade: safe serialisation, proper server stack, security primitives, observability, and CI.

### Deliverables
- Safe serialisation (no pickle)
- PostgreSQL support
- Production server (uvicorn ASGI)
- Structured JSON logging with correlation IDs
- In-process rate limiting (sliding window)
- JWT enforcement at API gateway
- OpenAPI 3.0 spec + Swagger UI
- HTTPS/TLS configuration
- Secrets management (`.env` + `require_secrets()`)
- Python DB migration runner (SQLite + PostgreSQL)
- GitHub Actions CI pipeline (test, lint, security audit)
- W3C Trace Context (`traceparent`) header propagation
- CORS middleware
- Prometheus `/metrics` endpoint
- Clock-skew tolerance in JWT verification

### Status (2026-06-11)
- ✅ Safe serialisation: `persistent_store.py` — pickle replaced with JSON type-tag codec (UUID, datetime, date, time, Decimal, bytes, Enum, dataclass, dict, tuple, set, list)
- ✅ PostgreSQL: `HRMS_DATABASE_URL` env var activates psycopg2 backend
- ✅ uvicorn ASGI: `docker/api_gateway_service.py` and `docker/service_runtime.py` converted; `asyncio.to_thread` for sync dispatch
- ✅ Structured JSON logging: `structured_logging.py` — `StructuredJSONFormatter`, `configure_logging()`, `ContextVar` correlation IDs
- ✅ Rate limiting: `rate_limiting.py` — `SlidingWindowRateLimiter` wired into gateway (200 req/min/IP, configurable)
- ✅ JWT enforcement: `jwt_utils.py` — `verify_hs256_jwt()`; gateway enforces on all non-exempt routes; propagates principal headers
- ✅ OpenAPI: `GET /openapi.json` + `GET /docs` (Swagger UI) auto-generated from ROUTES
- ✅ TLS: `SSL_CERT_FILE` + `SSL_KEY_FILE` activate uvicorn SSL in gateway and service runtime
- ✅ Secrets management: `secrets_config.py` — `require_secrets()`, `.env` auto-load
- ✅ DB migrations: `deployment/migrate.py` — tracks applied files in `schema_migrations`, supports SQLite + PostgreSQL
- ✅ CI pipeline: `.github/workflows/ci.yml` — Python 3.11/3.12, ruff, pip-audit, migration dry-run
- ✅ W3C Trace Context (`traceparent`) propagation — gateway parses incoming `traceparent`, generates new span ID, propagates to upstream via `_new_traceparent()`; returns `traceparent` response header
- ✅ CORS middleware — `access-control-allow-origin/methods/headers/max-age` on every response; `OPTIONS` preflight returns 204 instantly (configurable via `CORS_ALLOWED_ORIGINS`)
- ✅ Prometheus `/metrics` endpoint — `GET /metrics` returns Prometheus text exposition: `gateway_requests_total`, `gateway_request_duration_seconds_total`, `gateway_errors_total`
- ✅ JWT clock-skew tolerance — `verify_hs256_jwt(clock_skew_seconds=5)` allows ±5s grace window on `exp`/`nbf`
- ✅ Per-tenant RBAC — `_ROUTE_ROLE_MAP` + cross-tenant header enforcement; 403 on role/tenant mismatch
- ✅ Request body size limits — `MAX_REQUEST_BODY_BYTES` (1 MB default); 413 enforced during ASGI streaming
- ✅ Idempotency keys — `_IdempotencyCache` (24h TTL, 10k cap); POST/PATCH/PUT replay with `X-Idempotent-Replayed: true`
- ✅ JSON body validation — pre-forward `json.loads()` check; 400 `INVALID_JSON` on invalid body
