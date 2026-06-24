# DOCUMENTATION PLACEMENT AUDIT

Status: Active
Created: 2026-06-16
Phase: Full Repository Normalization and Reality Audit

---

## PURPOSE

Verifies that all documentation lives in the correct location within the docs/ framework. Identifies documentation stored outside docs/, documentation competing with authority docs, and docs that belong in docs/ but don't exist yet.

---

## DOCS FRAMEWORK VERIFICATION

### `docs/00_authority/` — Governance Authority Layer

| Document | Placement | Status |
|----------|-----------|--------|
| `PROJECT_CHARTER.md` | ✅ Correct | Active authority |
| `DOMAIN_MODEL.md` | ✅ Correct | Active authority — needs minor update (57→58 tables, per CON-004) |
| `FEATURE_SCOPE.md` | ✅ Correct | Active authority |
| `PRODUCT_WORKFLOWS.md` | ✅ Correct | Active authority |
| `FULLSTACK_STITCHING_CONTRACT.md` | ✅ Correct | Active authority |

**Status: COMPLETE**

---

### `docs/01_backend/` — Backend Authority Layer

| Document | Placement | Status |
|----------|-----------|--------|
| `API_CONTRACT.md` | ✅ Correct | Active authority |
| `BACKEND_ARCHITECTURE.md` | ✅ Correct | Active authority |
| `DATABASE_SCHEMA.md` | ✅ Correct | Active authority |
| `ERROR_CONTRACT.md` | ✅ Correct | Active authority |
| `EVENT_AND_QUEUE_ARCHITECTURE.md` | ✅ Correct | Active authority |
| `INTEGRATION_CATALOG.md` | ✅ Correct | Active authority |
| `SERVICE_CATALOG.md` | ✅ Correct | Active authority |
| `VALIDATION_RULES.md` | ✅ Correct | Active authority |

**Status: COMPLETE**

**Missing authority docs (identified gaps):**
- `COMPLIANCE_ARCHITECTURE.md` — Pakistan country layer (gap D-016)
- `DECISION_SERVICE_ARCHITECTURE.md` — Decision intelligence (gap D-020)
- `READ_MODEL_CATALOG.md` — Query projection spec (gap D-021) — note: `backend/docs/canon/read-model-catalog.md` and `backend/docs/canon/read-models.md` exist but no authority version

---

### `docs/02_frontend/` — EMPTY

**Expected but missing:**
- Frontend architecture authority
- UI component catalog
- Page-to-API mapping
- Frontend error handling patterns

All frontend authority content currently lives in `design/`:
- `design/hrms-archetype-system-v1.md` — should eventually move here
- `design/hrms-api-contracts.md` — should eventually move here
- `design/hrms-doc-catalogue-v1.md` — should eventually move here

**Status: AWAITING Frontend Authority Capture (mandate constraint — do not start)**

---

### `docs/03_fullstack_contracts/` — Fullstack Contracts Layer

| Document | Placement | Status |
|----------|-----------|--------|
| `AUTH_AND_TENANCY_CONTRACT.md` | ✅ Correct | Active authority |
| `CONTRACT_VERSION_REGISTRY.md` | ✅ Correct | Active authority |
| `DATA_SHAPE_REGISTRY.md` | ✅ Correct | Active authority |
| `USER_ROLES_AND_PERMISSIONS.md` | ✅ Correct | Active authority |
| `VALIDATION_PARITY.md` | ✅ Correct | Active authority |

**Status: COMPLETE**

---

### `docs/04_testing/` — EMPTY

**Expected but missing:**
- Testing strategy authority
- Test coverage baseline
- QC validation suite documentation

Currently scattered:
- `backend/docs/system/qc-suite.md` — QC suite reference, not in docs/
- `backend/deployment/qc_validate*.py` — QC scripts, no authority doc
- `backend/tests/` — 85 test files, no testing strategy doc

**Status: AWAITING Testing Authority Capture**

---

### `docs/05_deployment/` — EMPTY

**Expected but missing:**
- Deployment architecture authority
- Environment configuration reference
- Service startup sequence

Currently scattered:
- `backend/docs/deployment.md` — deployment notes in backend/docs/ root (not in docs/)
- `backend/deployment/config/gateway-routes.json` — gateway config
- `backend/deployment/config/postgres-init.sql` — DB init
- `backend/deployment/config/services.env` — env vars
- `backend/docs/system/infrastructure.md` — infrastructure notes (legacy)
- `backend/.github/workflows/` — deployment workflows

**Status: AWAITING Deployment Authority Capture**

---

### `docs/06_decisions/` — Decision Records

| Document | Placement | Status |
|----------|-----------|--------|
| `ADR-001_PROJECT_FOUNDATION.md` | ✅ Correct | Active authority |

**Missing:** ADR-002 through ADR-N (informal decisions in `ops/answers.md` C1–C5 not yet formalized as ADRs). See `docs/08_reports/RECOMMENDED_ADR_ROADMAP.md`.

---

### `docs/07_governance/` — Governance Layer

| Document | Placement | Status |
|----------|-----------|--------|
| `AI_OPERATING_CONTEXT.md` | ✅ Correct | Active authority |
| `DECISION_ESCALATION_MATRIX.md` | ✅ Correct | Active authority |

---

### `docs/08_reports/` — Generated Reports

All 14 report files correctly placed. ✅

---

### `docs/09_normalization/` — Normalization Phase Outputs

All 7 normalization files correctly placed. ✅

---

## DOCUMENTATION OUTSIDE THE DOCS FRAMEWORK

### Category 1: Documentation in `design/` that belongs in `docs/02_frontend/`

| File | Current Location | Should Be In | When to Move |
|------|-----------------|--------------|-------------|
| `design/hrms-archetype-system-v1.md` | `design/` | `docs/02_frontend/` | Frontend Authority Capture |
| `design/hrms-api-contracts.md` | `design/` | `docs/02_frontend/` or `docs/03_fullstack_contracts/` | Frontend Authority Capture |
| `design/hrms-doc-catalogue-v1.md` | `design/` | `docs/02_frontend/` | Frontend Authority Capture |
| `design/hrms-design-register-v1.md` | `design/` | `docs/02_frontend/` | Frontend Authority Capture |
| `design/hrms-ui-backend-gaps.md` | `design/` | `docs/08_reports/` | Safe to move now |
| `design/hrms-build-protocol-sop-v1.md` | `design/` | `docs/mandates/` | Safe to move now |
| `design/hrms-stabilisation-sop-v1.md` | `design/` | `docs/mandates/` | Safe to move now |
| `design/hrms-claude-code-prompt-v1.md` | `design/` | `docs/mandates/` | Safe to move now |
| `design/hrms-contract-structure-v1.md` | `design/` | `docs/02_frontend/` | Frontend Authority Capture |

### Category 2: Documentation in `backend/docs/` competing with authority docs

Already documented in `docs/09_normalization/DOCUMENT_RETIREMENT_PLAN.md`. Summary:
- `backend/docs/canon/` — 14 files, all superseded by docs/ authority layer
- `backend/docs/system/` — 14 files (excl. archive), mostly superseded
- `backend/docs/system/archive/` — 7 files, correctly archived

**Status: Retirement annotations specified in DOCUMENT_RETIREMENT_PLAN.md. Not yet applied.**

### Category 3: Documentation in `ops/` that should be in `docs/`

| File | Current Location | Should Be In | Action |
|------|-----------------|--------------|--------|
| `ops/HRMS PRODUCT SPEC.md` | `ops/` | — | Self-annotated superseded; keep as historical |
| `ops/answers.md` | `ops/` | `docs/06_decisions/` (as ADRs) | Formalize decisions; keep ops copy as history |
| `ops/hrms-audit-manifest-v1.json` | `ops/` | `docs/08_reports/` | Move — it's a report artifact |

### Category 4: Root-level mandate files

| File | Current Location | Should Be In |
|------|-----------------|--------------|
| `GOVERNANCE IMPLEMENTATION PHASE 1.md` | Root | `docs/mandates/` |
| `PHASE 1 GOVERNANCE VALIDATION.md` | Root | `docs/mandates/` |
| `AUDIT REMEDIATION.md` | Root | `docs/mandates/` |
| `PHASE 2 – BACKEND AUTHORITY CAPTURE.md` | Root | `docs/mandates/` |
| `DOCUMENTATION NORMALIZATION AND AUTHORITY CONSOLIDATION.md` | Root | `docs/mandates/` |
| `FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md` | Root | `docs/mandates/` |

### Category 5: Backend service documentation that is correctly placed

The 29 service documentation files in `backend/docs/services/*.md` are correctly placed for their layer (legacy canon service docs). These are the per-service specifications and do not yet have replacements in `docs/01_backend/services/`. No authority conflict — these are the only service-level docs. **Keep as-is.**

---

## DOCUMENTATION NOT IN DOCS THAT SHOULD BE (GAPS)

| Missing Document | Domain | Recommended Location |
|-----------------|--------|---------------------|
| Compliance/country layer architecture | D-016 | `docs/01_backend/COMPLIANCE_ARCHITECTURE.md` |
| Decision service architecture | D-020 | `docs/01_backend/DECISION_SERVICE_ARCHITECTURE.md` |
| Read model catalog (authority version) | D-021 | `docs/01_backend/READ_MODEL_CATALOG.md` |
| Frontend architecture | D-022 | `docs/02_frontend/FRONTEND_ARCHITECTURE.md` |
| Testing strategy | D-026 | `docs/04_testing/TESTING_STRATEGY.md` |
| Deployment architecture | D-025 | `docs/05_deployment/DEPLOYMENT_ARCHITECTURE.md` |
| ADR-002 through ADR-006 | Decisions | `docs/06_decisions/` |

---

## DOCUMENTATION PLACEMENT SUMMARY

| Status | Count | Notes |
|--------|-------|-------|
| Correctly placed | 43 | docs/ framework files |
| Correctly placed (legacy) | ~85 | backend/docs/ (retired layer, no action needed) |
| Needs move (safe now) | 8 | design/ SOPs → mandates; design/ UI gaps → reports |
| Needs move (Frontend Authority Capture) | 6 | design/ authority docs |
| Root-level → docs/mandates/ | 6 | Mandate .md files |
| Missing (authority gaps) | 7 | Identified above |
