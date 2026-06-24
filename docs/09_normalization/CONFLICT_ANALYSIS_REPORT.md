# CONFLICT ANALYSIS REPORT

Status: Active
Authority Level: Medium
Created: 2026-06-16
Owner: AI
Phase: Documentation Normalization and Authority Consolidation

---

## PURPOSE

Identifies all instances of conflicting authorities, terminology, architecture descriptions, entity definitions, and governance rules across the 150 project documents. For each conflict, identifies which document is authoritative and what resolution is recommended.

---

## CONFLICT REGISTER

### CON-001: Employee-Service Implementation Language — Critical Factual Conflict

**Severity:** Critical

**Conflicting statements:**
- `backend/docs/system/service-manifest.md`: Lists employee-service as `implemented` with code file `services/employee-service/` (TypeScript).
- `backend/docs/canon/service-map.md`: Describes employee-service with TypeScript implementation.
- `docs/01_backend/SERVICE_CATALOG.md` (current): Employee-service is now Python (`backend/employee_service.py`, `backend/employee_api.py`), implemented 2026-06-16.
- `BACKEND_AUTHORITY_CAPTURE_REPORT.md`: EG-001 resolved — Python employee-service implemented.

**Authority:** `docs/01_backend/SERVICE_CATALOG.md` is authoritative for current service implementation status.

**Resolution:** `service-manifest.md` and `service-map.md` contain a false claim about employee-service being TypeScript-only. Both should be annotated as SUPERSEDED and the `service-manifest.md` entry specifically flagged with a correction note. The `backend/docs/services/employee-service.md` file may also need updating to reflect the Python implementation.

---

### CON-002: System Product Name — "AURA HRMS" vs. "Meridian HCM"

**Severity:** High

**Conflicting statements:**
- `backend/docs/system/system-purpose.md`, `MASTER BUILD SPEC.md`, `MASTER BEHAVIOR SPEC.md`, `ops/build-progress.md`: Use "AURA HRMS — Pakistan Compliance OS + AI Workforce Decision System."
- `docs/00_authority/PROJECT_CHARTER.md`, `docs/01_backend/BACKEND_ARCHITECTURE.md`, `design/hrms-doc-catalogue-v1.md`, governance layer: Use "Meridian HCM."
- `docs/08_reports/GOVERNANCE_IMPLEMENTATION_REPORT.md`: Uses "Meridian HCM (HRMS)."

**Authority:** `docs/00_authority/PROJECT_CHARTER.md` is the project identity authority.

**Resolution:** The product name evolved from "AURA HRMS" (used in early build sessions) to "Meridian HCM" (established in governance layer). Per PROJECT_CHARTER.md, "Meridian HCM" is the current product name. All governance and authority documents use "Meridian HCM." Legacy documents retain "AURA HRMS" as a historical artifact — no edits needed to legacy docs, but any active documents (READMEs, canon docs being updated) should use "Meridian HCM."

**No immediate edit required** for legacy docs; the conflict is resolved by the authority hierarchy. New documents must use "Meridian HCM."

---

### CON-003: Service Count — "24" vs. Various Other Counts

**Severity:** High

**Conflicting statements:**
- `docs/01_backend/BACKEND_ARCHITECTURE.md`: "24 Python microservices + API Gateway + Next.js 15 frontend."
- `backend/docs/system/service-manifest.md`: Lists services in a different grouping structure.
- `backend/docs/canon/service-map.md`: Lists services with annotations.
- `backend/docs/system/MASTER BUILD SPEC.md`: Lists services from an earlier count.
- `ops/answers.md` final service map: Uses category-based grouping with fewer named services.

**Authority:** `docs/01_backend/SERVICE_CATALOG.md` is authoritative for service count and list.

**Resolution:** SERVICE_CATALOG.md lists 24 services. Legacy documents with different counts are historical artifacts reflecting earlier stages of development. No edit needed to legacy docs. Annotate legacy as superseded per DOCUMENT_RETIREMENT_PLAN.md.

---

### CON-004: Database Table Count — 57 vs. 58

**Severity:** Medium

**Conflicting statements:**
- `docs/08_reports/BACKEND_AUTHORITY_CAPTURE_REPORT.md` (§ KEY BACKEND FACTS): "58 tables across 14 migrations (001–014)."
- `docs/00_authority/DOMAIN_MODEL.md`: References "57+ DB tables."
- `docs/01_backend/DATABASE_SCHEMA.md`: Lists tables across migrations 001–015. Migration 015 (`leave_type_parental.sql`) modifies a constraint but does not add a table. 

**Authority:** `docs/01_backend/DATABASE_SCHEMA.md` is the database authority.

**Resolution:** Migration 015 adds a constraint, not a table — the table count remains 58 (from migrations 001–014, noting migration 014 added `grade_bands`). The "57+" in DOMAIN_MODEL.md is a rounding/approximation. Both DOMAIN_MODEL.md and BACKEND_AUTHORITY_CAPTURE_REPORT.md should be updated to consistently state "58 tables." This is a minor numeric inconsistency, not a structural conflict.

---

### CON-005: Event Count — 119 vs. 126 vs. 143

**Severity:** Medium

**Conflicting statements:**
- `backend/docs/canon/event-catalog.md`: Header corrected to "Verified event count: 126" (2026-06-15 correction).
- `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md`: States 126 events.
- Legacy references in some backend/docs/design reports: May reference 119 or 143 (pre-correction values).
- `event_contract.py` `CANONICAL_EVENT_TYPES` dict: 143 entries (includes events registered but not yet in catalog table).

**Authority:** `backend/docs/canon/event-catalog.md` (registry table row count, 126) and `event_contract.py` (code-registered events, 143) are both valid — they measure different things.

**Resolution:** The discrepancy between 126 (catalog table) and 143 (CANONICAL_EVENT_TYPES) is intentional — some events are registered in code but not yet added to the catalog table. This is documented in the catalog header. The historical values (119, 143 as "total") in older design reports are stale and should be ignored. No conflict for current documents — both 126 and 143 are correct for their respective scopes.

---

### CON-006: Workflow Count — "8" vs. "9"

**Severity:** Low

**Conflicting statements:**
- `backend/docs/system/catalogue.md` (§ workflow-catalog.md description): States "8 workflows."
- `backend/docs/canon/workflow-catalog.md`: Contains 9 workflow definitions (as noted in `ops/normalisation-tracker.md` finding).
- `docs/00_authority/PRODUCT_WORKFLOWS.md`: Documents 9 core workflows.

**Authority:** `docs/00_authority/PRODUCT_WORKFLOWS.md` and `backend/docs/canon/workflow-catalog.md` are authoritative for workflow definitions. Both show 9.

**Resolution:** `catalogue.md` miscounts — says "8" but catalog contains 9. The catalogue.md is a navigation document (operational artifact), not an authority document. The error in the count should be annotated in the retirement plan but is low-impact since `catalogue.md` is legacy.

---

### CON-007: Engagement Survey Dimensions — Enum Mismatch

**Severity:** Medium

**Conflicting statements:**
- `design/hrms-archetype-system-v1.md` (L322): Lists engagement dimensions as "D1 Wellbeing · D2 Management · D3 Learning · D4 Culture · D5 Purpose."
- `design/hrms-api-contracts.md` (canonical enum): Lists "D1 Clarity & Direction · D2 Manager Effectiveness · D3 Wellbeing & Balance · D4 Growth & Development · D5 Recognition & Reward."

**Authority:** `design/hrms-api-contracts.md` contains the canonical enum per `ops/normalisation-tracker.md` finding #1. The archetype system L322 has placeholder text that was never reconciled.

**Resolution:** `design/hrms-archetype-system-v1.md` L322 contains stale placeholder text. This should be corrected to match `hrms-api-contracts.md` during the next UI session or at minimum annotated as a known stale placeholder. This was logged as Cross-File Finding #1 in the normalisation tracker.

---

### CON-008: Payroll Compliance Check Location — Architecture Conflict

**Severity:** Medium

**Conflicting statements:**
- `ops/pending.md` (G22 deferred item): "G22 full wiring — `check_payroll_gate()` into `payroll_service.py mark_paid()`"
- `backend/docs/system/gap-register.md` (G22): G22 status shows deferred — "Needs integration test coverage first."
- `docs/00_authority/PRODUCT_WORKFLOWS.md`: Payroll workflow includes compliance gate step.

**Authority:** The deferred status in `ops/pending.md` reflects current state. The compliance gate exists architecturally but the wiring to `mark_paid()` is deferred.

**Resolution:** No documentation conflict — both documents accurately reflect the deferred state. The compliance gate is designed but not fully wired. This is a code implementation gap, not a documentation conflict. ARCHITECTURAL_GAP_REGISTER.md may need a formal entry if not already present.

---

### CON-009: ewa-financial-service — Existence Conflict

**Severity:** Medium

**Conflicting statements:**
- `backend/docs/canon/service-map.md` (annotated): ewa-financial-service references marked "TBD – REQUIRES VERIFICATION (not found in docker-compose.yml)."
- `docs/01_backend/SERVICE_CATALOG.md`: Lists ewa-financial-service as a service with port 8025.
- `docker-compose.yml`: Per Phase 2 discovery, no ewa-financial-service container found.
- `backend/docs/services/ewa-financial-service.md`: Service documentation exists.

**Authority:** `docker-compose.yml` is the deployment truth. `docs/01_backend/SERVICE_CATALOG.md` reflects planned/code-exists status.

**Resolution:** ewa-financial-service has code (`services/finance/ewa.py`) and a service doc but no docker-compose.yml entry. SERVICE_CATALOG.md should reflect this ambiguity. The ARG-002 finding in BACKEND_GAP_REGISTER.md documents this. No further documentation conflict — the discrepancy is documented. The service should be treated as "code exists, not deployed."

---

### CON-010: Terminology — "Capability" vs. "Permission" vs. "Scope"

**Severity:** Low

**Conflicting terminology:**
- `backend/docs/canon/capability-matrix.md`: Uses "CAP-XXX codes" for granular capabilities.
- `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md`: Uses "permissions" and "scope types."
- `docs/07_governance/AI_OPERATING_CONTEXT.md`: Uses "capabilities" in a different context (AI capabilities).
- Code: Uses both "role" and "scope" in JWT token context.

**Authority:** `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md` is authoritative for role/permission/scope terminology. `capability-matrix.md` is authoritative for CAP-XXX codes.

**Resolution:** These terms are used in different contexts and do not conflict. "Capability" in the context of CAP-XXX codes (capability matrix) = a specific feature action. "Capability" in AI_OPERATING_CONTEXT.md = what the AI system can do. "Permission" and "scope" in USER_ROLES_AND_PERMISSIONS.md = RBAC model. No terminology conflict — different domains using the word in domain-appropriate ways. No action needed beyond ensuring each document defines its own terms clearly.

---

### CON-011: "WhatsApp as standalone service" vs. "Integration adapter"

**Severity:** Low

**Conflicting framing:**
- `ops/answers.md` (C5): "WhatsApp is a STANDALONE SERVICE (NOT JUST INTEGRATION)" — access channel service.
- Legacy description in some docs: WhatsApp described as an integration.
- `docs/00_authority/FEATURE_SCOPE.md` (F-016): "whatsapp-service (port 8024)" — correctly frames as a service.

**Authority:** `docs/00_authority/FEATURE_SCOPE.md` and `docs/01_backend/SERVICE_CATALOG.md` are authoritative.

**Resolution:** No active conflict in current authority documents. `ops/answers.md` decision (C5) is consistent with the authority documents. Legacy integration framing exists only in older archived docs. No action needed.

---

### CON-012: Gateway Route Count Conflicts

**Severity:** Low

**Conflicting counts:**
- Pre-Phase-2 docs: 17 gateway route prefixes.
- Post-Phase-2 docs (`API_CONTRACT.md`, `SERVICE_CATALOG.md`): 21 gateway route prefixes (4 added in Phase 2: compliance, decisions, banking, whatsapp).
- `backend/docs/canon/api-standards.md`: May reference older route counts.

**Authority:** `docs/01_backend/API_CONTRACT.md` is authoritative for gateway route count and list.

**Resolution:** The 4 additional routes were added in Phase 2. Any document referencing "17 routes" is pre-Phase-2 and should be treated as historical. `api-standards.md` should be reviewed for route count references and annotated if it contains the old count.

---

## CONFLICT SUMMARY

| ID | Domain | Severity | Authority | Resolution |
|----|--------|----------|-----------|------------|
| CON-001 | Employee-service implementation | **Critical** | `SERVICE_CATALOG.md` | Annotate legacy docs as superseded; flag false claim |
| CON-002 | Product name (AURA vs. Meridian) | High | `PROJECT_CHARTER.md` | Historical artifact; new docs must use Meridian HCM |
| CON-003 | Service count | High | `SERVICE_CATALOG.md` | Legacy counts are historical; no edit needed |
| CON-004 | Table count (57 vs. 58) | Medium | `DATABASE_SCHEMA.md` | Update DOMAIN_MODEL.md to state "58 tables" consistently |
| CON-005 | Event count (119/126/143) | Medium | `event-catalog.md` (126 table rows) | Documented; no action needed for current docs |
| CON-006 | Workflow count (8 vs. 9) | Low | `PRODUCT_WORKFLOWS.md` (9) | Legacy catalogue.md count is stale; low impact |
| CON-007 | Engagement survey dimensions | Medium | `hrms-api-contracts.md` | Fix stale placeholder in `hrms-archetype-system-v1.md` L322 during next UI session |
| CON-008 | Payroll compliance gate wiring | Medium | Deferred state is correct | No doc conflict; implementation gap only |
| CON-009 | ewa-financial-service existence | Medium | `docker-compose.yml` + `SERVICE_CATALOG.md` | Documented in ARG-002; no further action needed |
| CON-010 | Capability/Permission terminology | Low | Domain-specific; no conflict | No action needed |
| CON-011 | WhatsApp framing | Low | `FEATURE_SCOPE.md` | Resolved; no action needed |
| CON-012 | Gateway route count | Low | `API_CONTRACT.md` | Historical docs show old count; review `api-standards.md` |

---

## REQUIRED ACTIONS

1. **CON-001:** Add superseded annotation to `service-manifest.md` and `service-map.md` with correction note on employee-service language.
2. **CON-002:** Establish governance rule: all new documents must use "Meridian HCM."
3. **CON-004:** Update `docs/00_authority/DOMAIN_MODEL.md` to consistently state "58 tables."
4. **CON-007:** Flag `design/hrms-archetype-system-v1.md` L322 engagement dimension conflict for correction in next UI session.
5. **CON-012:** Review `backend/docs/canon/api-standards.md` for hardcoded route counts referencing old 17-route configuration.
