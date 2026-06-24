# Success Criteria

The system is complete when all criteria below are met. These are binary gates, not targets.

---

## Tier 1 — Non-Negotiable (System is broken without these)

| # | Criterion | Measurement |
|---|---|---|
| S1 | Payroll errors ≈ 0 | Zero payroll runs finalized with incorrect tax, missing deductions, or wrong net pay |
| S2 | Compliance fully automated | FBR Annexure-C, EOBI PR-01, PESSI/SESSI generated and submitted without manual data entry |
| S3 | Compliance validates BEFORE payroll | Payroll finalization is blocked if compliance validation has not passed for the same period |
| S4 | Country abstraction enforced | Zero country conditionals (`if country == ...`) inside any core service |
| S5 | Audit trail complete | Every payroll action, compliance submission, and access change has an immutable audit record |

---

## Tier 2 — Core Product Complete (System is not useful without these)

| # | Criterion | Measurement |
|---|---|---|
| S6 | Decisions replace dashboards | Manager dashboard shows Decision Cards and exception queues, not static data tables |
| S7 | AI outputs are explainable | Every anomaly flag includes `why_flagged` with evidence, risk score, confidence level |
| S8 | Human-in-loop gates enforced | High-risk Decision Cards block payroll approval until operator acknowledges or overrides |
| S9 | WhatsApp fully usable | Employees can retrieve payslips, check leave balance, and apply for leave via WhatsApp |
| S10 | Manager approvals work via WhatsApp | Managers can approve/reject leave and attendance corrections in WhatsApp chat |

---

## Tier 3 — Architecture Complete (System is not scalable without these)

| # | Criterion | Measurement |
|---|---|---|
| S11 | New country = adapter only | Adding a new country requires only a new adapter; zero changes to any service |
| S12 | Multi-entity support | Single deployment supports multiple legal entities, each with independent payroll and compliance |
| S13 | API-first, no DB coupling | No cross-service database joins; all integration via events and read models |
| S14 | Services independently deployable | Each service can be deployed and scaled independently |

---

## Tier 4 — Quality Gates (from V3 QC framework)

| # | Criterion | Measurement |
|---|---|---|
| S15 | All tests pass | `pytest -q` → 0 failures |
| S16 | QC score 11/11 | `python deployment/qc_validate.py` → `QC score: 11/11` |
| S17 | RE-QC gates pass | `re_qc_validate_master_certification.py` (5/5), `re_qc_validate_addon_convergence.py` (5/5), `re_qc_validate_data_integrity.py` (6/6) |
| S18 | Intent/build alignment verified | Gateway routes, runtime handlers, and service topology are mutually consistent |

---

## Tier 5 — Production Infrastructure (System is not deployable without these)

> **NOTE (naming collision):** This "Tier 5" is this document's own tier numbering (Tiers 1–5 = non-negotiable → core product → architecture → quality gates → production infrastructure) and is **unrelated** to `docs/system/qc-suite.md`'s "Tier 5 — Coverage Gap Register", which is that document's independent QC-suite-stage numbering. The two "Tier 5"s do not refer to the same content.

| # | Criterion | Status | Measurement |
|---|---|---|---|
| S19 | No unsafe serialisation | ✅ | Zero `pickle` usage in any production code path |
| S20 | Production-grade server | ✅ | Services run on uvicorn ASGI, not `http.server` |
| S21 | Structured logging | ✅ | All log output is JSON with `ts`, `level`, `correlation_id`; no plain `logging.basicConfig` |
| S22 | Rate limiting enforced | ✅ | Gateway returns 429 + `X-RateLimit-*` headers beyond configured threshold |
| S23 | JWT enforced at gateway | ✅ | All non-auth API routes require valid HS256 bearer token; ±5s clock-skew tolerance |
| S24 | OpenAPI spec served | ✅ | `GET /openapi.json` returns OpenAPI 3.0 document; `GET /docs` serves Swagger UI |
| S25 | DB migrations tracked | ✅ | `deployment/migrate.py` applies SQL files in version order; `schema_migrations` table tracks state |
| S26 | CI pipeline green | ✅ | `.github/workflows/ci.yml` — test matrix, lint, security audit, migration dry-run |
| S27 | Secrets validated at startup | ✅ | `secrets_config.require_secrets()` validates env vars; missing secrets exit cleanly |
| S28 | TLS configurable | ✅ | `SSL_CERT_FILE` + `SSL_KEY_FILE` activate uvicorn SSL in gateway and service runtime |
| S29 | W3C Trace Context propagated | ✅ | Gateway parses `traceparent`, generates child span, forwards to upstream, echoes in response |
| S30 | CORS headers on all responses | ✅ | `access-control-allow-*` headers set; `OPTIONS` preflight returns 204 instantly |
| S31 | Prometheus metrics endpoint | ✅ | `GET /metrics` returns Prometheus text exposition (`gateway_requests_total`, durations, errors) |
| S32 | Per-tenant RBAC enforced | ✅ | `_ROUTE_ROLE_MAP` gates sensitive routes by role; cross-tenant `X-Tenant-Id` vs JWT `tenant_id` checked; 403 on mismatch |
| S33 | Request body size limited | ✅ | `MAX_REQUEST_BODY_BYTES` (default 1 MB) enforced during ASGI streaming; 413 `REQUEST_TOO_LARGE` on overflow |
| S34 | Idempotency key support | ✅ | POST/PATCH/PUT replay from TTL cache keyed by `client_ip:Idempotency-Key`; `X-Idempotent-Replayed: true` header on replay |
| S35 | Input JSON validated at gateway | ✅ | Gateway pre-validates JSON body before forwarding; 400 `INVALID_JSON` on parse error |

---

## Definition of Done per Phase

| Phase | Gate |
|---|---|
| Phase 1 (Architecture) | S4 + S13 + S14 + S15 + S16 + S17 |
| Phase 2 (Pakistan Payroll/Compliance) | S1 + S2 + S3 + S5 |
| Phase 3 (Decision Engine) | S6 + S7 + S8 |
| Phase 4 (WhatsApp + Mobile) | S9 + S10 |
| Phase 5 (Multi-Country) | S11 + S12 |
| Phase 6 (Production Hardening) | S19–S28 |

---

## Related Documents
- System purpose: `docs/system/system-purpose.md`
- Roadmap: `docs/system/roadmap.md`
- QC validation: `deployment/qc_validate.py`
