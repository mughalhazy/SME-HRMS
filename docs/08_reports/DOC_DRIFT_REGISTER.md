# DOC DRIFT REGISTER

Status: Active
Created: 2026-06-16
Phase: Pre-Frontend Doc-to-Code Delta Audit and Remediation

---

## PURPOSE

Registers all documentation drift instances found in this audit — cases where a document's content diverged from the repository reality it was supposed to describe. Drift can occur via code changes that were not reflected in docs, incomplete initial documentation, or TBDs that were never resolved.

Each entry records the cause of drift and whether it has been corrected.

---

## DRIFT REGISTER

### DD-001 — Gateway route count stale across 3 documents

| Attribute | Detail |
|---|---|
| **Type** | Stale count — code added routes, docs not updated |
| **Affected documents** | `API_CONTRACT.md` §2, §4, §4 Notes; `SERVICE_CATALOG.md` §PURPOSE, §25; `BACKEND_ARCHITECTURE.md` §3.3, §4.1 |
| **Old claim** | 21 routes |
| **Actual** | 25 routes — compliance, decisions, banking, whatsapp added after initial documentation |
| **Cause** | The initial documentation pass counted 21 routes. Four services (compliance, decision, bank, whatsapp) were subsequently added to `routes.py` and `gateway-routes.json` but the documentation was not updated. |
| **Status** | CORRECTED — all 6 locations updated |
| **Correction date** | 2026-06-16 |

---

### DD-002 — 4 services incorrectly marked TBD in SERVICE_CATALOG.md

| Attribute | Detail |
|---|---|
| **Type** | Stale TBD — verification was possible but not performed |
| **Affected document** | `SERVICE_CATALOG.md` §21–24 section headers and SUMMARY TABLE rows 21–24 |
| **Old claim** | "TBD – REQUIRES VERIFICATION" for compliance, decision, bank, whatsapp gateway routes |
| **Actual** | All 4 confirmed in `routes.py` lines 52–55 and `gateway-routes.json` lines 25–28 |
| **Cause** | The initial documentation pass did not read `routes.py` past line 51, so routes 22–25 were not seen. The TBD was placed correctly at the time but never resolved. |
| **Status** | CORRECTED — all 4 services updated to CONFIRMED with evidence citations |
| **Correction date** | 2026-06-16 |

---

### DD-003 — Employee-service source pointed at dead TypeScript code

| Attribute | Detail |
|---|---|
| **Type** | Major drift — live implementation replaced with Python but docs still pointed at TypeScript |
| **Affected documents** | `SERVICE_CATALOG.md` §1, `API_CONTRACT.md` §5.18 |
| **Old claim** | Primary source: `backend/services/employee-service/` TypeScript files |
| **Actual** | Active implementation: `backend/employee_service.py` + `backend/employee_api.py`; TypeScript is dead code |
| **Cause** | Employee-service was migrated from TypeScript to Python (EG-001, resolved 2026-06-16) but documentation was not updated to reflect the new Python implementation. |
| **Status** | CORRECTED — both documents updated to reflect Python primary source |
| **Correction date** | 2026-06-16 |

---

### DD-004 — Settings-service source pointed at unused TypeScript code

| Attribute | Detail |
|---|---|
| **Type** | Drift — documented implementation was never the runtime implementation |
| **Affected documents** | `SERVICE_CATALOG.md` §20, `API_CONTRACT.md` §5.19 |
| **Old claim** | Primary source: `backend/services/settings-service/` TypeScript files |
| **Actual** | Runtime: inline in-memory Python dict stub in `service_runtime.py` lines 324–342; TypeScript not used |
| **Cause** | The TypeScript settings-service files describe the intended persistent implementation. The actual deployed runtime is a temporary in-memory stub that was never documented as such. |
| **Status** | CORRECTED — both documents updated to reflect inline stub as current runtime |
| **Correction date** | 2026-06-16 |

---

### DD-005 — JWT enforcement marked TBD despite being fully implemented

| Attribute | Detail |
|---|---|
| **Type** | Unresolved TBD — implementation existed, TBD was never cleared |
| **Affected document** | `API_CONTRACT.md` §3.3 |
| **Old claim** | "The exact gateway-level JWT enforcement mechanism is TBD — REQUIRES VERIFICATION (no gateway middleware handler file was located in the sampled files)" |
| **Actual** | Fully implemented in `api_gateway_service.py` lines 421–430: `verify_hs256_jwt` call with `_AUTH_EXEMPT_PREFIXES` exemption list; JWT claims propagated as `X-User-Id`, `X-User-Role`, `X-Tenant-Id` headers (lines 468–471) |
| **Cause** | The initial documentation pass sampled files but did not read `api_gateway_service.py` in full, so the JWT enforcement implementation was not located. |
| **Status** | CORRECTED — §3.3 updated with full implementation details; §3.5 Route-Level RBAC section added |
| **Correction date** | 2026-06-16 |

---

### DD-006 — common_service.py described with wrong purpose (TBD)

| Attribute | Detail |
|---|---|
| **Type** | Wrong assumption + unresolved TBD |
| **Affected document** | `BACKEND_ARCHITECTURE.md` §2 |
| **Old claim** | "TBD – REQUIRES VERIFICATION (not read in full; expected to contain shared service bootstrap helpers based on naming convention)" |
| **Actual** | Lightweight `BaseHTTPRequestHandler`-based health-check stub (78 lines); responds only to `/health`, `/ready`, `/`; contains no business logic; is NOT a shared service bootstrap helper |
| **Cause** | File was not read during initial Phase 2 documentation pass. The assumption about its purpose (based on naming convention) was wrong. |
| **Status** | CORRECTED — `BACKEND_ARCHITECTURE.md` §2 updated with confirmed description |
| **Correction date** | 2026-06-16 |

---

### DD-007 — Route-level audit RBAC undocumented

| Attribute | Detail |
|---|---|
| **Type** | Missing documentation — feature existed but was not captured |
| **Affected document** | `API_CONTRACT.md` |
| **Old claim** | RBAC section listed `/api/v1/payroll`, `/api/v1/hiring`, `/api/v1/reporting` only |
| **Actual** | `_ROUTE_ROLE_MAP` in `api_gateway_service.py` lines 66–71 also restricts `/api/v1/audit` to `Admin` role only — not documented anywhere |
| **Cause** | The initial documentation pass captured only 3 of the 4 RBAC-restricted routes. The audit route restriction was missed. |
| **Status** | CORRECTED — `/api/v1/audit` (`Admin` only) added to new §3.5 Route-Level RBAC table |
| **Correction date** | 2026-06-16 |

---

### DD-008 — JWT header propagation undocumented

| Attribute | Detail |
|---|---|
| **Type** | Missing documentation — mechanism existed but was not captured |
| **Affected document** | `API_CONTRACT.md` §3.3 |
| **Old claim** | Described JWT enforcement but said nothing about downstream header forwarding |
| **Actual** | `api_gateway_service.py` lines 468–471: after JWT verification, gateway forwards `X-User-Id`, `X-User-Role`, `X-Tenant-Id` headers to all upstream services; this is how domain services receive actor context |
| **Cause** | The initial documentation pass did not read the claim-propagation section of `api_gateway_service.py`. |
| **Status** | CORRECTED — propagation table added to `API_CONTRACT.md` §3.3 |
| **Correction date** | 2026-06-16 |

---

### DD-009 — §6 of API_CONTRACT.md titled with wrong characterisation

| Attribute | Detail |
|---|---|
| **Type** | Stale classification — gateway routing status changed, title not updated |
| **Affected document** | `API_CONTRACT.md` §6 header |
| **Old claim** | "Services without Gateway Routes — NO GATEWAY ROUTE — INTERNAL ONLY" (for compliance, bank, whatsapp, decision) |
| **Actual** | All 4 are registered in `routes.py` lines 52–55. The real concern is their non-standard response envelope. |
| **Cause** | DD-001/DD-002 — when the TBD routes were not confirmed, §6 was incorrectly maintained as "no gateway route". Now that routes are confirmed, the section title was wrong. |
| **Status** | CORRECTED — title updated to "Services with Non-Standard Response Envelope"; text clarified |
| **Correction date** | 2026-06-16 |

---

## DRIFT CAUSE ANALYSIS

| Cause Category | Count | Items |
|---|---|---|
| Code changed, docs not updated | 2 | DD-001 (route count), DD-003 (employee-service migration) |
| TBD never resolved | 3 | DD-002 (4 TBD routes), DD-005 (JWT TBD), DD-006 (common_service.py TBD) |
| Implementation never documented | 3 | DD-004 (settings stub), DD-007 (audit RBAC), DD-008 (JWT headers) |
| Cascading from other drift | 1 | DD-009 (§6 title from DD-001/DD-002) |

**Primary root cause:** The initial Backend Authority Capture (Phase 2) documented what was discoverable from a sampling pass without reading every file. Four files were not fully read: `routes.py` (only 21 of 25 entries seen), `api_gateway_service.py` (JWT section not reached), `common_service.py` (not read), `employee_service.py`/`employee_api.py` (not yet written at the time, resolved 2026-06-16 as EG-001).

---

## STATUS SUMMARY

All 9 drift instances resolved. No open drift items.
