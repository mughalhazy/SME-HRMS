# UNDOCUMENTED CODE REGISTER

Status: Active
Created: 2026-06-16
Phase: Pre-Frontend Doc-to-Code Delta Audit and Remediation

---

## PURPOSE

Registers code that exists in the repository but is either undocumented in the authority documents or was documented incorrectly. Includes dead code, implementation-only code, and code whose documentation was fixed during this audit.

---

## REGISTER

### UDC-001 — `_employee_domain_departments()` in service_runtime.py (DEAD CODE)

| Attribute | Detail |
|---|---|
| **File** | `backend/docker/service_runtime.py` lines 132–218 |
| **Description** | Function that parses `domain-seed.ts` and returns a list of fallback department dicts. Was used by the old employee-service inline stub. |
| **Why undocumented** | Dead code — never called after the Python `EmployeeService` implementation replaced the inline stub. The new employee-service block (lines 445–469) seeds departments via `EmployeeService` directly. |
| **Documentation status** | Documented as DELTA-012 in `DOC_TO_CODE_DELTA_MATRIX.md`. Awaiting owner approval to remove (OA-001 in `OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md`). |
| **Risk** | None if removed — no callers. If retained, increases cognitive overhead for anyone reading `service_runtime.py`. |

---

### UDC-002 — settings-service inline dict stub (NOW DOCUMENTED)

| Attribute | Detail |
|---|---|
| **File** | `backend/docker/service_runtime.py` lines 324–342 |
| **Description** | Inline in-memory Python dict (`settings_state`) with two inline handler functions (`_handle_settings_get`, `_handle_settings_update`). No external module imported. |
| **Why previously undocumented** | `SERVICE_CATALOG.md` §20 and `API_CONTRACT.md` §5.19 both listed the TypeScript files in `backend/services/settings-service/` as the primary source — wrong. |
| **Documentation status** | Fixed in this audit (DELTA-004 APPLIED). `SERVICE_CATALOG.md` §20 and `API_CONTRACT.md` §5.19 now document the inline stub correctly. |
| **Risk** | The stub is non-persistent — all settings reset on restart. This is a known limitation documented in `API_CONTRACT.md` §5.19. |

---

### UDC-003 — `backend/employee_service.py` and `backend/employee_api.py` (NOW DOCUMENTED)

| Attribute | Detail |
|---|---|
| **Files** | `backend/employee_service.py` (EmployeeService class), `backend/employee_api.py` (14 handler functions) |
| **Description** | Active Python employee-service implementation. `service_runtime.py` lines 445–469 import and register 14 routes from these files. |
| **Why previously undocumented** | `SERVICE_CATALOG.md` §1 and `API_CONTRACT.md` §5.18 both pointed to the dead TypeScript files in `backend/services/employee-service/` as the primary source. |
| **Documentation status** | Fixed in this audit (DELTA-003 APPLIED). Both documents now correctly reference the Python files. |
| **Gap remaining** | `API_CONTRACT.md` §5.18 still lists only 5 endpoint rows from contract evidence. The full 14-route list requires reading `backend/employee_api.py` (registered as UC-006). |

---

### UDC-004 — `backend/api/employee_portal.py` (partially documented)

| Attribute | Detail |
|---|---|
| **File** | `backend/api/employee_portal.py` |
| **Description** | Self-service portal helper. Exposes `get_payslip`, `post_leave_apply`, `get_attendance`, `get_profile` for employee portal endpoints (`/payslip`, `/leave/apply`, `/attendance`, `/profile`). |
| **Why partially documented** | Was investigated during the employee-service handler search (AG-003). Not the employee-service route handler. No authority document currently describes it. |
| **Documentation status** | Noted in `API_CONTRACT.md` §5.18 investigation notes. Not yet formally catalogued as a standalone API surface. |
| **Action** | Add to `API_CONTRACT.md` or `SERVICE_CATALOG.md` as a self-service portal endpoint group in a future pass. Not blocking Phase 3. |

---

### UDC-005 — `backend/employee_ui.py` (partially documented)

| Attribute | Detail |
|---|---|
| **File** | `backend/employee_ui.py` |
| **Description** | UI surface configuration builder. `build_employee_ui()` returns a dict of UI surface configs (e.g., field visibility, action availability per role). Not an HTTP handler. |
| **Why partially documented** | Investigated during AG-003; confirmed role. No authority document describes its purpose or the UI surface config format it produces. |
| **Documentation status** | Noted in `API_CONTRACT.md` §5.18 investigation notes. Not catalogued as a standalone module. |
| **Action** | Relevant to Frontend Authority Capture (Phase 3) — the UI config it returns informs frontend field/action visibility. Add to Phase 3 scope. |

---

### UDC-006 — Compliance/bank/whatsapp/decision services — non-standard response envelope

| Attribute | Detail |
|---|---|
| **Files** | `backend/compliance_api.py`, `backend/banking_api.py`, `backend/whatsapp_api.py`, `backend/decision_api.py` |
| **Description** | These 4 services use `_ok()` / `_err()` helper functions that return `{"status": ..., "data": ..., "service": ...}` — missing the required `meta` field from the `api_contract.py` standard envelope. |
| **Why previously undocumented** | `API_CONTRACT.md` §6 titled the section "Services without Gateway Routes" — conflating the envelope issue with the routing status. The routing status is now corrected (all 4 have gateway routes). |
| **Documentation status** | Fixed in this audit — `API_CONTRACT.md` §6 title updated to "Services with Non-Standard Response Envelope"; text clarified. |
| **Risk** | Frontend consumers expecting the standard `{status, data, meta, error}` envelope will receive a different shape from these 4 services. This is a breaking contract inconsistency to resolve before or during Phase 3. |

---

### UDC-007 — `backend/background_jobs_api.py` (no gateway route — internal only)

| Attribute | Detail |
|---|---|
| **File** | `backend/background_jobs_api.py` |
| **Description** | Background job HTTP API. Registered in `service_runtime.py` but not in `api-gateway/routes.py` — internal-only. |
| **Why partially documented** | Documented in `API_CONTRACT.md` §6.5 as internal-only. Confirmed correct. |
| **Documentation status** | Adequate for current phase. |
| **Action** | None required for Phase 3. |

---

## SUMMARY

| ID | File | Status | Blocks Phase 3? |
|----|------|--------|-----------------|
| UDC-001 | `service_runtime.py` lines 132–218 | Dead code — OWNER APPROVAL to remove | No |
| UDC-002 | `service_runtime.py` lines 324–342 | Now documented | No |
| UDC-003 | `employee_service.py`, `employee_api.py` | Now documented (partial) | No |
| UDC-004 | `api/employee_portal.py` | Partially documented | No — future pass |
| UDC-005 | `employee_ui.py` | Partially documented | No — Phase 3 scope |
| UDC-006 | 4 non-standard envelope services | Now documented (envelope gap noted) | Awareness needed |
| UDC-007 | `background_jobs_api.py` | Documented as internal | No |
