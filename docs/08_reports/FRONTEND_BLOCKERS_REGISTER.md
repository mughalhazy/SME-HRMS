# FRONTEND BLOCKERS REGISTER

Status: Complete — No Blockers
Created: 2026-06-16
Phase: Repository Determinability Review, Approval Elimination, and Pre-Frontend Go/No-Go

---

## PURPOSE

Registers any finding that would prevent Frontend Authority Capture (Phase 3) from beginning. A blocker is a condition where the backend reality, authority documentation, or security model is so unclear that frontend planning would build on false assumptions.

---

## BLOCKER ASSESSMENT

### B-001 — Backend Authority Documentation Accuracy

**Status: CLEAR**

All authority documents (`SERVICE_CATALOG.md`, `API_CONTRACT.md`, `BACKEND_ARCHITECTURE.md`) now accurately reflect repository reality after 4 rounds of correction:
- Phase 2: Initial backend authority capture
- Phase 2.5: Normalization and retirement
- Phase 2.7: Pre-frontend doc-to-code delta audit (13 deltas resolved)
- Phase 2.9 (this phase): Determinability review (12 items resolved, ARG-003 corrected)

**Not a blocker.**

---

### B-002 — API Contract Completeness

**Status: CLEAR**

The API contract (`API_CONTRACT.md`) now documents:
- All 25 gateway routes (confirmed from routes.py + gateway-routes.json)
- JWT enforcement mechanism (confirmed from api_gateway_service.py)
- JWT claim propagation headers (X-User-Id, X-User-Role, X-Tenant-Id)
- Route-level RBAC (payroll, audit, hiring, reporting)
- Auth-exempt prefixes
- Employee-service full 14-endpoint table (confirmed from service_runtime.py + employee_api.py)
- Settings-service: in-memory stub (non-persistent)
- 4 non-standard envelope services documented

**Not a blocker.** Frontend developers have a complete and accurate API contract.

---

### B-003 — Security Model Clarity

**Status: CLEAR**

Security model confirmed from code:
- JWT HS256 enforcement at gateway layer
- 6 auth-exempt prefixes (health, ready, metrics, openapi, docs, /api/v1/auth/)
- 4 RBAC-restricted routes with confirmed role sets
- Claims forwarded as X-User-Id, X-User-Role, X-Tenant-Id headers

**Not a blocker.**

---

### B-004 — Frontend App Location

**Status: KNOWN, NON-BLOCKING**

The Next.js frontend app is at `backend/ui/` (structurally wrong location). This is documented. Frontend Authority Capture can proceed using `backend/ui/` as the known location. The relocation (ROD-001) is a post-Phase-3 task.

**Not a blocker.**

---

### B-005 — Non-Standard Envelope Services

**Status: KNOWN, NON-BLOCKING WITH AWARENESS**

4 services (compliance, decision, banking, whatsapp) use a non-standard response envelope `{status, data, service}` without the `meta` field. Frontend code consuming these 4 services must handle this difference. This is now documented in `API_CONTRACT.md` §6.

**Not a blocker — but frontend implementation must account for it.**

---

### B-006 — Settings-Service Non-Persistence

**Status: KNOWN, NON-BLOCKING WITH AWARENESS**

The settings-service uses an in-memory dict stub that resets on service restart. Settings are not persisted. Frontend should not assume settings survive deployment cycles.

**Not a blocker — but frontend should treat settings as volatile in dev.**

---

### B-007 — Repository Normalization

**Status: CLEAR**

Repository normalization outputs are complete (`docs/10_repo_audit/`). Known structural issues are documented with resolution paths. No normalization gap prevents frontend authority capture.

**Not a blocker.**

---

### B-008 — CountryResolver Production Bootstrap

**Status: CLEAR — RESOLVED**

ARG-003 (country resolver bootstrap not wired) was a documentation error. `_bootstrap_country_resolver()` IS called at lifespan startup via `COUNTRY_ORG_MAPPINGS` env var. No gap exists.

**Not a blocker.**

---

## BLOCKER SUMMARY

| Blocker | Status | Impact |
|---|---|---|
| B-001 Backend authority accuracy | CLEAR | — |
| B-002 API contract completeness | CLEAR | — |
| B-003 Security model | CLEAR | — |
| B-004 Frontend app location | KNOWN, NON-BLOCKING | Document as known during Phase 3 |
| B-005 Non-standard envelope (4 services) | AWARENESS NEEDED | Frontend must handle both envelope shapes |
| B-006 Settings non-persistence | AWARENESS NEEDED | Treat settings as volatile in dev |
| B-007 Repository normalization | CLEAR | — |
| B-008 Country resolver bootstrap | CLEAR | — |

**Active blockers: 0**
**Awareness items: 2 (B-005, B-006)**

---

## VERDICT

**No blockers to Frontend Authority Capture (Phase 3).**

Phase 3 may begin. The two awareness items (non-standard envelope, settings non-persistence) are documented constraints, not unknowns.
