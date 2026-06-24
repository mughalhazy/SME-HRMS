# DECISION COLLAPSE REGISTER

Status: Complete
Created: 2026-06-17
Phase: 3.25 — Autonomous Gap Elimination and Determinism Enforcement

---

## PURPOSE

Records every decision that was collapsed (resolved autonomously) during Phase 3.25, applying the Decision Collapse Rule:

> An item may be resolved if: (A) derivable from code, (B) derivable from documentation, (C) derivable from workflows, (D) derivable from architecture, (E) derivable from existing patterns, or (F) has only one rational interpretation.

---

## COLLAPSE DECISIONS

### DC-001: Gateway routes 22–25 (compliance, decisions, banking, whatsapp)

**Collapse trigger:** A / B — derivable from code + documentation  
**Evidence:** `backend/api-gateway/routes.py` lines 52–55; `backend/deployment/config/gateway-routes.json` lines 25–28  
**Collapsed items:** FEATURE_SCOPE.md F-011/F-014/F-015/F-016 API Prefix TBDs; FULLSTACK_STITCHING_CONTRACT.md KNOWN GAPS table entries; FULLSTACK_STITCHING_CONTRACT.md Status Change Note; FULLSTACK_STITCHING_CONTRACT.md T-012/T-006 addendum; api-standards.md route TBDs  
**Result:** All 4 routes confirmed IMPLEMENTED with non-standard envelope `{status, data, service}`

---

### DC-002: Employee service handler location

**Collapse trigger:** A — derivable from code  
**Evidence:** `backend/employee_api.py` lines 1–124; `backend/employee_service.py`; `service_runtime.py` lines 445–469  
**Collapsed items:** FULLSTACK_STITCHING_CONTRACT.md T-001/T-002/T-003/T-015 Phase 2 evidence handler TBDs; UC-006  
**Result:** `backend/employee_api.py` has 14 handlers; TypeScript files are dead code

---

### DC-003: `/health` and `/ready` endpoint registration

**Collapse trigger:** A — derivable from code  
**Evidence:** `backend/docker/service_runtime.py` line 410  
**Collapsed items:** UC-004, TO-001, BACKEND_ARCHITECTURE.md §8 note  
**Result:** Single `if path in ("/health", "/ready"):` block handles both; returns standard success envelope

---

### DC-004: CircuitBreaker usage pattern

**Collapse trigger:** A — derivable from code  
**Evidence:** grep `CircuitBreaker` in `backend/**/*.py`: definition in `resilience.py`, usage in `hiring_service/service.py` and `supervisor_engine.py`, tested in `test_failure_resilience.py`  
**Collapsed items:** UC-003, TO-002, BACKEND_ARCHITECTURE.md §10 note  
**Result:** CircuitBreaker used selectively; not all 24 services use it directly

---

### DC-005: OutboxManager purpose

**Collapse trigger:** A — derivable from code  
**Evidence:** `backend/outbox_system.py` lines 1–60  
**Collapsed items:** UC-001, TO-003  
**Result:** `OutboxManager` class with `PersistentKVStore` namespaces `outbox_records`, `processed_events`, `dispatch_log`

---

### DC-006: 007_event_outbox.sql existence

**Collapse trigger:** A — derivable from code (file system)  
**Evidence:** Glob `backend/deployment/migrations/007_event_outbox.sql` confirmed  
**Collapsed items:** UC-002, TO-004  
**Result:** File exists; defines `service_outbox` table

---

### DC-007: 19 capability TBDs in USER_ROLES_AND_PERMISSIONS.md

**Collapse trigger:** B — derivable from documentation (canon doc is authoritative)  
**Evidence:** `backend/docs/canon/security-model.md` capability-to-role table lines 16–48  
**Collapsed items:** 19 "TBD – REQUIRES VERIFICATION" entries in §3.3 table  
**Result:** All 31 capabilities marked ✓ (canon); security-model.md is the authoritative source

---

### DC-008: Requisition scope type

**Collapse trigger:** A + F — derivable from code; only one rational interpretation  
**Evidence:** `AuthService.assign_role_binding` validation set `{'Global', 'Department', 'Employee', 'Service'}` (`service.py` line 521); `_service_scopes_for_user` logic  
**Collapsed items:** `USER_ROLES_AND_PERMISSIONS.md` §4 Requisition TBD  
**Result:** `Requisition` is NOT a validated `scope_type` at the auth-service layer. Recruiter uses `Department` scope; requisition-level scoping delegated to hiring-service layer. No code gap — behavior is achievable.

---

### DC-009: ewa-financial-service architecture

**Collapse trigger:** A — derivable from code  
**Evidence:** `backend/services/finance/ewa.py` (FinancialWellnessService); `backend/payroll_service.py` line 392; `backend/banking_api.py` (Raast payout); `backend/docker-compose.yml` (no ewa container)  
**Collapsed items:** `service-map.md` 3 ewa-financial-service TBDs; `api-standards.md` `/api/v1/financial-wellness` TBD; ARG-002 full resolution  
**Result:** No standalone service. EWA is in-process within payroll-service. Payouts via banking_api.py.

---

### DC-010: automation-service trigger model

**Collapse trigger:** A — derivable from code  
**Evidence:** `backend/automation_contract.py` — only event-type trigger matching (EG-003 confirmed)  
**Collapsed items:** `service-map.md` automation-service description; `FEATURE_SCOPE.md` F-013 Key Operations  
**Result:** Event-triggered only; scheduled and threshold triggers NOT implemented

---

### DC-011: Helpdesk ticket priority and status enums

**Collapse trigger:** A — derivable from code  
**Evidence:** `backend/helpdesk_service.py` lines 127–128: `TICKET_STATUSES = {'Draft', 'Open', 'InProgress', 'Resolved', 'Closed'}`, `PRIORITIES = {'Low', 'Medium', 'High', 'Urgent'}`  
**Collapsed items:** `DOMAIN_MODEL.md` lines 1029–1030 TBDs  
**Result:** Both enums fully confirmed

---

### DC-012: LMS service owner

**Collapse trigger:** B + F — derivable from documentation; only one rational interpretation  
**Evidence:** `FEATURE_SCOPE.md` OUT OF SCOPE section confirms LMS not in codebase; no `learning-service` in docker-compose.yml  
**Collapsed items:** `DOMAIN_MODEL.md` LEARNING PATH service owner TBD  
**Result:** No service owner — table is a forward migration artifact; feature is OUT OF SCOPE

---

### DC-013: Decision Cards gateway access

**Collapse trigger:** A + B — derivable from code and documentation  
**Evidence:** `backend/api-gateway/routes.py` line 53 (TR-004); `gateway-routes.json` line 26  
**Collapsed items:** `DOMAIN_MODEL.md` line 1147 TBD note; FULLSTACK_STITCHING_CONTRACT.md T-012 "NO GATEWAY ROUTE"  
**Result:** Gateway route 23 confirmed; Decision Cards are client-accessible

---

### DC-014: Settings service handler

**Collapse trigger:** A — derivable from code  
**Evidence:** `backend/docker/service_runtime.py` lines 236–254 (in-memory dict stub)  
**Collapsed items:** `FULLSTACK_STITCHING_CONTRACT.md` T-013 handler TBD; TR-008 note  
**Result:** In-process inline stub in service_runtime.py; no separate file; resets on restart (C-002)

---

### DC-015: WF-001 Document Collection step

**Collapse trigger:** B + F — derivable from documentation; only one rational interpretation  
**Evidence:** `FEATURE_SCOPE.md` OUT OF SCOPE confirms document management not in codebase  
**Collapsed items:** `PRODUCT_WORKFLOWS.md` WF-001 step 6 TBD  
**Result:** OUT OF SCOPE — no backend service; UI-only checklist item if needed

---

### DC-016: WF-002 Calendar Updated and OnLeave status

**Collapse trigger:** D + E — derivable from architecture; derivable from existing patterns  
**Evidence:** leave-service status transitions (Approved); attendance-service reads leave records during period closure (standard leave-service → attendance-service data flow)  
**Collapsed items:** `PRODUCT_WORKFLOWS.md` WF-002 steps 6 and lifecycle TBDs  
**Result:** No employee status `OnLeave`; leave record status = `Approved`; attendance-service queries leave records

---

### DC-017: WF-003 Optional approval workflow

**Collapse trigger:** D — derivable from architecture (no approval workflow wired for payroll)  
**Evidence:** Payroll status transitions: Draft → Processed → Paid (per `002_workflow_schema.sql`); no payroll approval workflow definition found  
**Collapsed items:** `PRODUCT_WORKFLOWS.md` WF-003 step 8 TBD  
**Result:** Not implemented by default; PayrollAdmin directly transitions Draft → Processed

---

### DC-018: TypeScript test cross-references

**Collapse trigger:** A + F — derivable from code; only one rational interpretation  
**Evidence:** All 80+ test files in `backend/tests/` are `.py` files; TypeScript cannot be imported by Python; Python test filenames match domain concepts, not TypeScript filenames  
**Collapsed items:** UC-007; BACKEND_ARCHITECTURE.md §5 TBD  
**Result:** Python tests test Python behavior; TypeScript files are dead code; no cross-language test execution

---

### DC-019: General-purpose cache layer

**Collapse trigger:** A + B — derivable from code and documentation  
**Evidence:** ADR-001 §4 "No caching layer (Redis/Memcached not present)"; `cache.service.ts` is TypeScript dead code; only `_IdempotencyCache` (gateway) and `_atl_cache` (ATL adapter) confirmed in Python runtime  
**Collapsed items:** BACKEND_ARCHITECTURE.md §7 TBD  
**Result:** No general-purpose cache layer for domain services

---

### DC-020: `/api/v1/roles` and `/api/v1/org` gateway routing

**Collapse trigger:** A — derivable from code  
**Evidence:** `backend/employee_api.py` registers `post_roles`, `get_roles`, `get_role`, `patch_role`; routes through `/api/v1/employees` gateway prefix (C-004); `service_runtime.py` confirms employee-service handles all employee, department, role, org endpoints  
**Collapsed items:** `api-standards.md` `/api/v1/roles` and `/api/v1/org` TBDs  
**Result:** CONFIRMED — served by employee-service; no separate gateway route needed

---

## SUMMARY

| Category | Count |
|----------|-------|
| Total decisions collapsed | 20 |
| Collapse trigger A (code) | 13 |
| Collapse trigger B (documentation) | 4 |
| Collapse trigger D (architecture) | 2 |
| Collapse trigger F (single rational interpretation) | 3 |
| Multi-trigger collapses | 8 |
