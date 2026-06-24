# GOVERNANCE CONSISTENCY AUDIT — PHASE 1 VALIDATION

Status: Active
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This audit performs a cross-document consistency review of the seven Phase 1 governance documents, checking for contradictions, duplicate definitions, missing terminology, inconsistent naming, workflow mismatches, domain entity mismatches, feature scope mismatches, and architectural assumption conflicts.

**Documents Audited:**
1. `docs/00_authority/PROJECT_CHARTER.md`
2. `docs/00_authority/FEATURE_SCOPE.md`
3. `docs/00_authority/DOMAIN_MODEL.md`
4. `docs/00_authority/PRODUCT_WORKFLOWS.md`
5. `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md`
6. `docs/07_governance/AI_OPERATING_CONTEXT.md`
7. `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md`

**Audit Method:** Manual cross-reference of entity names, service names, ports, route prefixes, feature IDs, workflow IDs, lifecycle states, role names, and architectural claims across all seven documents.

---

## CRITICAL ISSUES

**None identified.**

No contradiction was found that would cause a future AI session to take a security-compromising, data-destructive, or tenant-isolation-violating action based on these documents. All audit/tenant-isolation/security-related statements (audit immutability, `tenant_id` constraints, JWT model, deny-by-default authorization) are consistent across all seven documents.

---

## HIGH ISSUES

### H-001: Engagement-Service Gateway Route Contradiction

**Documents in Conflict:** `ADR-001_PROJECT_FOUNDATION.md` vs. `FEATURE_SCOPE.md` vs. `FULLSTACK_STITCHING_CONTRACT.md`

- `ADR-001` §2 Service Topology diagram presents `/api/v1/engagement → engagement-service :8011` as a confirmed, live API Gateway route — listed identically to all other (confirmed) routes, with no caveat.
- `FEATURE_SCOPE.md` F-018 (Employee Engagement) states: *"API Prefix: `/api/v1/engagement` — TBD – REQUIRES VERIFICATION (not in gateway route table)"*.
- `FULLSTACK_STITCHING_CONTRACT.md` "Known Gaps in Stitching" lists *"Employee Surveys ... engagement-service route not in gateway route table"* as an open gap.

**Impact:** ADR-001 is the highest-authority architectural document (Critical, Active). A future AI session reading only ADR-001 would treat `/api/v1/engagement` as an existing, routable endpoint and could build features against it, while FEATURE_SCOPE and the stitching contract explicitly flag it as unverified/possibly absent.

**Recommendation:** Annotate ADR-001's topology diagram to mark `/api/v1/engagement` (and any other unverified routes) with a status flag (e.g., "UNCONFIRMED"), or remove it from the diagram until GAP-C-001 is resolved.

---

### H-002: Domain Entities Referenced Outside DOMAIN_MODEL.md (Authoritative Entity Reference Incomplete)

**Documents in Conflict:** `DOMAIN_MODEL.md` vs. `FEATURE_SCOPE.md` and `PRODUCT_WORKFLOWS.md`

`DOMAIN_MODEL.md` states its purpose is to be *"the authoritative domain entity reference"* and that *"all service implementations must conform to the entity definitions ... documented here."* However, the following entities are referenced as real, named domain entities in other authority documents but have **no entry** in `DOMAIN_MODEL.md`:

| Entity | Referenced In | Missing From |
|--------|---------------|---------------|
| ReviewCycle, Goal, Feedback, CalibrationSession, PipPlan | `FEATURE_SCOPE.md` F-017, `PRODUCT_WORKFLOWS.md` WF-005 | `DOMAIN_MODEL.md` |
| Survey, SurveyQuestion, SurveyResponse, AggregatedSurveyResult | `FEATURE_SCOPE.md` F-018 | `DOMAIN_MODEL.md` |
| AttendanceRule, LeavePolicy, PayrollSettings | `FEATURE_SCOPE.md` F-010 | `DOMAIN_MODEL.md` |
| Decision Card | `FULLSTACK_STITCHING_CONTRACT.md` T-012, `FEATURE_SCOPE.md` F-014 | `DOMAIN_MODEL.md` |
| WorkflowStep, WorkflowHistory | `FULLSTACK_STITCHING_CONTRACT.md` T-005 (endpoint references `/steps/{step_id}`) | `DOMAIN_MODEL.md` (only WorkflowDefinition and WorkflowInstance are documented) |

**Impact:** Any AI session relying on `DOMAIN_MODEL.md` as the single source of truth for entities will be unaware these entities exist, risking re-definition, naming drift, or incorrect assumptions about their structure when implementing performance, engagement, settings, decision, or workflow-step features.

**Recommendation:** Add stub entries for each entity above to `DOMAIN_MODEL.md`, marked `TBD – REQUIRES VERIFICATION` for field-level detail where schema has not been read (e.g., `011_addon_domains.sql`, `012_compensation_domain.sql`).

---

### H-003: ADR-001 Gateway Topology Overstates Route Confirmation for PLANNED Services

**Documents in Conflict:** `ADR-001_PROJECT_FOUNDATION.md` vs. `FEATURE_SCOPE.md`

`ADR-001` §2 Service Topology diagram lists `/api/v1/travel → travel-service :8018` and `/api/v1/projects → project-service :8019` alongside all other routes with no distinguishing annotation. `FEATURE_SCOPE.md` F-023 and F-024 explicitly classify both `travel-service` and `project-service` as **Status: PLANNED** (i.e., "scaffolded but not functionally implemented").

Additionally, the original repository exploration (referenced in `08_reports/GOVERNANCE_IMPLEMENTATION_REPORT.md`) found only **~21 confirmed route prefixes**, while ADR-001's diagram presents **24** routes uniformly — a 3-route gap that aligns with the engagement (H-001), travel, and project discrepancies.

**Impact:** A reader of ADR-001 alone would conclude all 24 services are equally live and routable, contradicting the FEATURE_SCOPE status register for at least 3 services.

**Recommendation:** Add a status column or annotation to ADR-001's topology diagram distinguishing IMPLEMENTED / ADD-ON / PLANNED / UNCONFIRMED routes, consistent with `FEATURE_SCOPE.md`.

---

## MEDIUM ISSUES

### M-001: Missing Terminology — No Glossary for Cross-Cutting Concepts

Several terms are used across documents without a formal definition in any of the seven audited documents:

- **"Decision Card"** — used in `FULLSTACK_STITCHING_CONTRACT.md` (T-012), `FEATURE_SCOPE.md` (F-014), and `AI_OPERATING_CONTEXT.md` (via decision-service references), but never defined as a structured entity or concept.
- **"Read Model" / "Projection"** — implied in `FULLSTACK_STITCHING_CONTRACT.md` T-011 ("Read models / projections") and `ADR-001` event architecture, but not defined.
- **"Capability"** — used in `AI_OPERATING_CONTEXT.md` KNOWN_CONSTRAINTS ("requires both capability grant + matching scope") without a definition of what a capability is, how many exist, or where they are enumerated (the canonical capability matrix lives outside the audited document set, in `/backend/docs/canon/capability-matrix.md`).
- **"Scope"** (as in scope_type) — defined with values (Global/Department/Employee/Requisition/Service) in `DOMAIN_MODEL.md` RoleBinding, but the *behavioral meaning* of each scope value is not defined in any of the seven documents.

**Impact:** Medium — these terms are load-bearing for authorization logic (`AI_OPERATING_CONTEXT.md` constraints reference "capability grant + matching scope" as the enforcement rule), but their precise meaning requires cross-referencing documents outside the governance layer.

**Recommendation:** Add a short "Terminology" or "Glossary" section to `AI_OPERATING_CONTEXT.md` defining: Decision Card, Read Model/Projection, Capability, and the five Scope types — even if definitions point to `/backend/docs/canon/` as the detailed source.

---

### M-002: Workflow Coverage Gap — WF-005 through WF-008 Have No Stitching Contract Traces

`PRODUCT_WORKFLOWS.md` defines 8 workflows (WF-001 through WF-008). `FULLSTACK_STITCHING_CONTRACT.md` defines 15 traces (T-001 through T-015), of which only WF-001 through WF-004 are referenced:

| Workflow | Referenced by Trace(s)? |
|----------|--------------------------|
| WF-001 Employee Onboarding | T-003 |
| WF-002 Leave Request & Approval | T-004, T-005 |
| WF-003 Payroll Run | T-006 |
| WF-004 Hiring Pipeline | T-008, T-009 |
| WF-005 Performance Review Cycle | **No trace** |
| WF-006 Expense Claim | **No trace** |
| WF-007 Audit & Compliance Reporting | **No trace** |
| WF-008 Employee Self-Service | **No trace** (though T-001, T-002, T-007, T-014 cover individual self-service reads without WF-008 reference) |

**Impact:** Medium — Not a contradiction, but an incompleteness that could cause WF-005–WF-008 to be treated as lower priority or forgotten when stitching contract work resumes in a future phase.

**Recommendation:** When `FULLSTACK_STITCHING_CONTRACT.md` is expanded (Phase 2+), add traces for WF-005 through WF-008, or explicitly note in `PRODUCT_WORKFLOWS.md` that these workflows are pending stitching-contract coverage.

---

### M-003: Dual Numbering Schemes for the Same Feature Set (PROJECT_CHARTER vs FEATURE_SCOPE)

`PROJECT_CHARTER.md` §5–§7 lists the same 24 features as `FEATURE_SCOPE.md` F-001–F-024, but uses plain sequential numbering (1–16, 1–6, 1–2 within each section) rather than the F-XXX identifiers. The item order and content match 1:1 at present, but there is no cross-reference (e.g., "see F-001") linking the two lists.

**Impact:** Medium — If either document's feature list is reordered, renamed, or extended independently in a future edit, the two lists could silently drift out of sync with no structural link to detect it.

**Recommendation:** Add F-XXX identifiers to `PROJECT_CHARTER.md`'s capability lists (§5–§7), or replace those lists with a reference to `FEATURE_SCOPE.md`.

---

## LOW ISSUES

### L-001: Naming Variance — "Search" vs "Cross-Domain Search"

`PROJECT_CHARTER.md` §6 (ADD-ON Capabilities) lists item 4 as **"Search"** ("Cross-domain projection-backed search" as description). `FEATURE_SCOPE.md` F-020 titles the same feature **"Cross-Domain Search"**. Same feature, same service (search-service, port 8014), minor title variance only.

**Recommendation:** Standardize on "Cross-Domain Search" (the more descriptive `FEATURE_SCOPE.md` title) in `PROJECT_CHARTER.md`.

---

### L-002: Duplicate Definitions — Frozen Decisions vs Architectural Principles

`AI_OPERATING_CONTEXT.md` FROZEN_DECISIONS (FD-001–FD-013) substantially restates content already present in `ADR-001_PROJECT_FOUNDATION.md` §3 (Core Technology Choices) and §7 (Architectural Principles). For example:

- FD-001 (JWT HS256) ≈ ADR-001 §3 Backend table "Authentication: JWT (HS256)"
- FD-006 (Outbox pattern) ≈ ADR-001 §7 Principle 5 "Outbox for Events"
- FD-008 (Deny-by-default) ≈ ADR-001 §7 Principle 6 "Deny by Default"

**Impact:** Low — This is intentional layering (AI_OPERATING_CONTEXT is meant to be a fast-reference summary; ADR-001 holds full rationale). However, the duplication creates a maintenance burden: if ADR-001 is amended (e.g., via a future ADR superseding a decision), `AI_OPERATING_CONTEXT.md`'s FROZEN_DECISIONS table must be updated in lockstep or it will present stale "frozen" status.

**Recommendation:** No structural change needed now. Add a note to `AI_OPERATING_CONTEXT.md` FROZEN_DECISIONS stating "Derived from ADR-001 §3 and §7 — any ADR that supersedes a decision here must update this table in the same change."

---

### L-003: Product Naming — "Meridian HCM" vs "HRMS"

`PROJECT_CHARTER.md` introduces two names: *"Product Name: Meridian HCM (Human Capital Management)"* and *"Working Name: HRMS SaaS"*. `ADR-001` and `AI_OPERATING_CONTEXT.md` both refer to the system primarily as "Meridian HCM" but the repository, directory names, and most file paths use "HRMS" / "hrms-*". Both names are used interchangeably across documents without confusion in context, but no document formally states the relationship (e.g., "Meridian HCM is the product brand name; HRMS is the internal/repository codename").

**Impact:** Low — no functional ambiguity observed, but could confuse a new AI session searching for "Meridian" in a codebase that uses "hrms" file naming conventions almost exclusively.

**Recommendation:** Add one sentence to `PROJECT_CHARTER.md` §1 clarifying: "Meridian HCM is the product/brand name; 'HRMS' is used throughout the codebase, file paths, and contracts as the internal project identifier. Both refer to the same system."

---

### L-004: FULLSTACK_STITCHING_CONTRACT.md Status = Draft (Only Outlier)

All six other audited documents are `Status: Active`. `FULLSTACK_STITCHING_CONTRACT.md` alone is `Status: Draft`. This is appropriate given the volume of TBD markers and the H-001/H-002/H-003 findings above, but it means one of the five required `00_authority/` documents remains in Draft state.

**Recommendation:** See "Documents Ready to Move from Draft → Active" below — keep as Draft pending resolution of H-001 and H-002.

---

## SUMMARY TABLE

| Severity | Count | IDs |
|----------|-------|-----|
| Critical | 0 | — |
| High | 3 | H-001, H-002, H-003 |
| Medium | 3 | M-001, M-002, M-003 |
| Low | 4 | L-001, L-002, L-003, L-004 |

---

## DOCUMENTS READY TO MOVE FROM DRAFT → ACTIVE

| Document | Current Status | Recommendation |
|----------|----------------|-----------------|
| `PROJECT_CHARTER.md` | Active | **Remain Active.** L-003 (naming clarification) is a minor addition that does not block authority status. |
| `FEATURE_SCOPE.md` | Active | **Remain Active.** M-003 (numbering cross-reference) is an enhancement, not a blocker. |
| `DOMAIN_MODEL.md` | Active | **Remain Active, but schedule correction.** H-002 identifies real gaps in entity coverage; recommend a follow-up revision adding stub entries before the next 90-day freshness review (per `AI_OPERATING_CONTEXT.md` DOCUMENT_FRESHNESS_POLICY), but the existing content is accurate and does not warrant reverting to Draft. |
| `PRODUCT_WORKFLOWS.md` | Active | **Remain Active.** M-002 (coverage gap with stitching contract) does not affect the correctness of WF-001–WF-008 as written. |
| `FULLSTACK_STITCHING_CONTRACT.md` | Draft | **Remain Draft.** This document has the highest concentration of findings (H-001, H-002 directly implicate it; M-002 originates from it). Promote to Active only after: (1) H-001 engagement-service route is verified or annotated, (2) GAP-C-001 through GAP-C-006 (from `ARCHITECTURAL_GAP_REGISTER.md`) are resolved or explicitly re-confirmed as TBD with no contradiction to other docs, (3) WF-005–WF-008 traces are added or formally deferred. |
| `AI_OPERATING_CONTEXT.md` | Active | **Remain Active.** No issue here rises to a level requiring status change; M-001 (glossary) and L-002 (duplication note) are additive improvements. |
| `ADR-001_PROJECT_FOUNDATION.md` | Active | **Remain Active, but schedule correction.** H-001 and H-003 both implicate ADR-001's topology diagram. As a foundation ADR documenting decisions already implemented in code, its core content (technology choices, principles, constraints) remains valid; only the topology diagram needs annotation. Do not revert to Draft — instead, the next revision should add the status annotations described in H-001/H-003 recommendations. |

---

## AUDIT SCOPE LIMITATIONS

- This audit compared the seven listed documents against **each other only** — it did not re-verify claims against the live codebase (that verification work is tracked separately in `ARCHITECTURAL_GAP_REGISTER.md` and `RECOMMENDED_ADR_ROADMAP.md`).
- Documents outside the seven listed (e.g., `08_reports/*`, `/backend/docs/canon/*`) were used only as background context where directly relevant to a finding, not as audit targets.
- No code was read, modified, or executed as part of this audit.

---

## STOP CONDITION

Per the validation instructions:

- DO NOT MODIFY CODE — not done ✅
- DO NOT CREATE NEW ARCHITECTURE — not done ✅ (no new architectural decisions introduced; findings only reference existing content)
- DO NOT START PHASE 2 — not done ✅

**Audit complete. Findings and recommendations are advisory pending human review.**
