# PRE-FRONTEND READINESS REPORT

Status: Complete
Created: 2026-06-16
Phase: Pre-Frontend Doc-to-Code Delta Audit and Remediation

---

## PURPOSE

Final readiness assessment for Frontend Authority Capture (Phase 3). Confirms that all documentation accurately reflects backend and repository reality before frontend planning and authority documentation begins.

---

## ASSESSMENT SUMMARY

**Verdict: READY. Frontend Authority Capture (Phase 3) may begin.**

All critical and high-severity doc/code deltas have been fixed. No documentation built on false assumptions remains. Owner-approval items are bounded and do not block Phase 3.

---

## WORK COMPLETED IN THIS AUDIT

### Documents Corrected

| Document | Corrections |
|---|---|
| `docs/01_backend/SERVICE_CATALOG.md` | 10 corrections — route counts, 4 service gateway statuses, 2 service primary sources, section headers, summary table |
| `docs/01_backend/API_CONTRACT.md` | 11 corrections — route count in 3 locations, 4 new routes added to table, JWT section rewritten, RBAC section added, header propagation documented, §5.18/§5.19 updated, §6 header corrected |
| `docs/01_backend/BACKEND_ARCHITECTURE.md` | 4 corrections — common_service.py description, route count references, §4.2 TBD removed |

### Output Documents Created

| Document | Purpose |
|---|---|
| `docs/08_reports/DOC_TO_CODE_DELTA_MATRIX.md` | Master delta register — 13 deltas, all dispositioned |
| `docs/08_reports/PRE_FRONTEND_DELTA_AUDIT.md` | Master audit report |
| `docs/08_reports/UNVERIFIED_CLAIMS_REGISTER.md` | 7 remaining claims not verifiable in this pass |
| `docs/08_reports/UNDOCUMENTED_CODE_REGISTER.md` | 7 code items that were undocumented or incorrectly documented |
| `docs/08_reports/DOC_DRIFT_REGISTER.md` | 9 drift instances — all corrected |
| `docs/08_reports/TBD_RESOLUTION_REGISTER.md` | 9 TBDs resolved; 5 remaining (non-blocking) |
| `docs/08_reports/OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md` | 10 items requiring owner decisions |

---

## BACKEND REALITY — CONFIRMED FACTS

The following backend facts are now confirmed in authority documents and ready for Phase 3 to build on:

### API Gateway

- 25 routes in `backend/api-gateway/routes.py` (lines 31–55)
- 25 matching entries in `backend/deployment/config/gateway-routes.json`
- JWT enforcement: `verify_hs256_jwt()` in `api_gateway_service.py` lines 421–430
- JWT claim propagation: `X-User-Id`, `X-User-Role`, `X-Tenant-Id` headers to all upstream services
- Route-level RBAC: `/api/v1/payroll` (Admin/PayrollAdmin/Manager), `/api/v1/audit` (Admin only), `/api/v1/hiring` (Admin/Manager/Recruiter), `/api/v1/reporting` (Admin/Manager)
- Auth-exempt prefixes: `/health`, `/ready`, `/metrics`, `/openapi.json`, `/docs`, `/api/v1/auth/`

### Service Implementations

| Service | Runtime | Source |
|---|---|---|
| employee-service | Python | `backend/employee_service.py` + `backend/employee_api.py` (14 routes) |
| settings-service | Inline Python dict stub | `service_runtime.py` lines 324–342 (non-persistent) |
| compliance-service | Python | `backend/compliance_api.py` + `services/compliance_service.py` |
| decision-service | Python | `backend/decision_api.py` + `services/decision_engine.py` |
| bank-service | Python | `backend/bank_service.py` + `backend/banking_api.py` |
| whatsapp-service | Python | `backend/whatsapp_service.py` + `backend/whatsapp_api.py` |

### common_service.py

`backend/docker/common_service.py` is a minimal health-check-only `BaseHTTPRequestHandler` stub (78 lines). Not a shared service bootstrap helper.

### Non-Standard Envelope Services

Services 22–25 (compliance, decision, banking, whatsapp) have gateway routes but use a non-standard `{"status", "data", "service"}` envelope without the `meta` field. The frontend must handle this difference for these 4 services.

---

## GAPS REMAINING (NON-BLOCKING)

These gaps are known and documented but do not prevent Phase 3:

| Gap | Detail | Documented in |
|---|---|---|
| Settings-service non-persistent | `settings_state` dict resets on restart — not a production-ready implementation | `API_CONTRACT.md` §5.19; `SERVICE_CATALOG.md` §20 |
| 4 services use non-standard envelope | compliance, decision, banking, whatsapp do not use `api_contract.py` | `API_CONTRACT.md` §6 |
| `_employee_domain_departments()` dead code | 87 lines of dead code in `service_runtime.py` | `OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md` OA-001 |
| Legacy product name in OpenAPI | "Aura HRMS API" in `api_gateway_service.py` | `OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md` OA-002 |
| Frontend at `backend/ui/` | Next.js app is inside `backend/` directory | `OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md` OA-003 |
| TypeScript dead code | 60 TypeScript files in `backend/services/` | `OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md` OA-004–006 |
| 5 unresolved TBDs in BACKEND_ARCHITECTURE.md | All non-blocking; outbox, health endpoints, per-service circuit breaker | `TBD_RESOLUTION_REGISTER.md` TO-001 to TO-005 |

---

## PHASE 3 PREREQUISITES CHECKLIST

| # | Prerequisite | Status |
|---|---|---|
| 1 | All authority backend docs reflect code reality | COMPLETE |
| 2 | Gateway route table confirmed (25 routes) | COMPLETE |
| 3 | JWT and auth contract confirmed | COMPLETE |
| 4 | Service implementations confirmed (Python vs TypeScript) | COMPLETE |
| 5 | Non-standard envelope services identified | COMPLETE |
| 6 | Dead code and structural issues documented for owner | COMPLETE |
| 7 | No vague TBDs where code evidence exists | COMPLETE |
| 8 | Frontend location documented (backend/ui/) | COMPLETE |
| 9 | Normalization framework complete (docs/09_normalization/) | COMPLETE (from Phase 2.5) |
| 10 | Repository audit complete (docs/10_repo_audit/) | COMPLETE (from repo audit) |

---

## PHASE 3 STARTING POINT

Frontend Authority Capture should begin with:

1. **Read `backend/ui/`** — the Next.js 15 app directory (app router, TypeScript, Tailwind, shadcn/ui or similar)
2. **Read `design/` and `frontend/`** — HTML wireframes and design artifacts
3. **Read `docs/02_frontend/`** — existing frontend authority documents (if any)
4. **Confirm the frontend ↔ API contract** — which of the 25 gateway routes the frontend calls; how it handles the 4 non-standard envelope services
5. **Document `backend/employee_ui.py`** — the UI surface config builder is relevant to Phase 3

---

**Signed off:** 2026-06-16
**Audit phase:** Pre-Frontend Doc-to-Code Delta Audit and Remediation
**Next phase:** Frontend Authority Capture (Phase 3)
