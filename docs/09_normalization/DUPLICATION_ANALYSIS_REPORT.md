# DUPLICATION ANALYSIS REPORT

Status: Active
Authority Level: Medium
Created: 2026-06-16
Owner: AI
Phase: Documentation Normalization and Authority Consolidation

---

## PURPOSE

Identifies all instances of duplicated definitions, descriptions, registers, and governance rules across the 150 project documents. For each duplication cluster, recommends a consolidation action.

---

## DUPLICATION CLUSTERS

### DUP-001: Domain Model — Three Competing Definitions

**Severity:** High

**Files involved:**
- `docs/00_authority/DOMAIN_MODEL.md` (new authority — most complete)
- `backend/docs/canon/domain-model.md` (legacy canon — predates multi-tenancy corrections)
- `backend/docs/canon/data-architecture.md` (legacy schema — predates migrations 014/015)

**What is duplicated:**
Entity definitions, entity relationships, column lists, and status enums for all major domain entities (Employee, Department, Role, LeaveRequest, PayrollRecord, etc.) appear in all three documents with varying levels of completeness and accuracy.

**Key divergence:** `data-architecture.md` pre-dates compound FK corrections (migration 014) and parental leave addition (migration 015). `domain-model.md` (canon) predates the multi-tenancy invariant documentation. `DOMAIN_MODEL.md` (new authority) is the most correct and complete.

**Consolidation action:** Annotate `backend/docs/canon/domain-model.md` and `backend/docs/canon/data-architecture.md` as SUPERSEDED with pointer to `docs/00_authority/DOMAIN_MODEL.md`. See DOCUMENT_RETIREMENT_PLAN.md.

---

### DUP-002: Feature Scope — Two Competing Definitions

**Severity:** High

**Files involved:**
- `docs/00_authority/FEATURE_SCOPE.md` (new authority — F-XXX IDs, IN/OUT/PLANNED status)
- `backend/docs/canon/release-scope.md` (legacy canon — predates F-XXX ID system)

**What is duplicated:**
Feature lists, service assignments, implementation status. Same information in two documents with different naming conventions (F-XXX IDs vs. plain names) and different completeness levels.

**Key divergence:** `release-scope.md` does not use F-XXX identifiers and lacks the Document Management OUT-OF-SCOPE entry added in Phase 2.

**Consolidation action:** Annotate `backend/docs/canon/release-scope.md` as SUPERSEDED. See DOCUMENT_RETIREMENT_PLAN.md.

---

### DUP-003: Service Catalog — Three Competing Sources

**Severity:** High

**Files involved:**
- `docs/01_backend/SERVICE_CATALOG.md` (new authority — most complete)
- `backend/docs/canon/service-map.md` (legacy canon — TBD annotations added)
- `backend/docs/system/service-manifest.md` (legacy system — stale TypeScript employee-service claim)

**What is duplicated:**
Service names, ports, runtime status, owned entities, and dependencies. All three describe the same 24 services.

**Key divergence:** `service-manifest.md` lists employee-service as TypeScript implementation — now incorrect (Python implemented). `service-map.md` has TBD annotations for ewa-financial-service. SERVICE_CATALOG.md is current.

**Consolidation action:** Annotate both legacy files as SUPERSEDED. The `service-manifest.md` also contains a false factual claim (employee-service = TypeScript) that must be flagged. See DOCUMENT_RETIREMENT_PLAN.md.

---

### DUP-004: System Identity / Project Purpose — Four Sources

**Severity:** Medium

**Files involved:**
- `docs/00_authority/PROJECT_CHARTER.md` (new authority)
- `backend/docs/system/system-purpose.md` (legacy — same 7 principles)
- `backend/docs/system/MASTER BUILD SPEC.md` (legacy — system identity section)
- `ops/build-progress.md` (§ "What This Project Is" — inline summary)

**What is duplicated:**
System identity statement ("TRUST INFRASTRUCTURE"), the 7 design principles (P1–P7), core non-negotiables (payroll accuracy, compliance automation, AI decisions).

**Key divergence:** All agree on content; `system-purpose.md` and MASTER BUILD SPEC.md predate PROJECT_CHARTER.md but contain the same principles. The `ops/build-progress.md` section is a condensed summary useful for session continuity.

**Consolidation action:** Annotate `system-purpose.md` and MASTER BUILD SPEC.md (identity sections) as SUPERSEDED. Retain `ops/build-progress.md` summary as operational artifact — acceptable duplication in an ops context.

---

### DUP-005: Security / Auth Model — Two Sources

**Severity:** Medium

**Files involved:**
- `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` (new authority)
- `backend/docs/canon/security-model.md` (legacy canon)

**What is duplicated:**
JWT HS256 model, role definitions, tenant isolation rules, RBAC deny-by-default principle.

**Key divergence:** `AUTH_AND_TENANCY_CONTRACT.md` is more complete, includes token lifecycle, session management, and was validated against actual code. `security-model.md` predates formal tenancy contract.

**Consolidation action:** Annotate `backend/docs/canon/security-model.md` as SUPERSEDED. See DOCUMENT_RETIREMENT_PLAN.md.

---

### DUP-006: API Standards — Split Authority

**Severity:** Medium

**Files involved:**
- `docs/01_backend/API_CONTRACT.md` (new authority — route/endpoint content)
- `backend/docs/canon/api-standards.md` (retained — coding standards)
- `design/hrms-api-contracts.md` (UI-layer contracts)

**What is duplicated:**
Response envelope shape (`{status, data, meta, error}`), versioning (`/api/v1/`), HTTP status conventions, pagination shape. These appear in all three documents.

**Key divergence:** `api-standards.md` is actively referenced by backend tests (test files assert against it). Cannot be retired without updating test anchors. `design/hrms-api-contracts.md` describes frontend expectations — partially overlaps with DATA_SHAPE_REGISTRY.md.

**Consolidation action:** Split authority is intentional and acceptable: `API_CONTRACT.md` owns endpoint catalog; `api-standards.md` owns coding standards; `hrms-api-contracts.md` covers UI expectations. Add cross-references between all three. Ensure each document explicitly states what it does and does not own. No retirement needed.

---

### DUP-007: Roles and Permissions / Capability Matrix — Partial Overlap

**Severity:** Medium

**Files involved:**
- `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md` (new authority — roles, scopes, deny-by-default)
- `backend/docs/canon/capability-matrix.md` (retained — CAP-XXX codes)

**What is duplicated:**
Role definitions (Admin, Manager, Employee, HR, Finance, Service), scope types (write, read, salary, team, service), some capability descriptions.

**Key divergence:** `capability-matrix.md` contains 40+ CAP-XXX codes actively referenced in code (`CAP-EMP-001`, etc.). These codes do not appear in `USER_ROLES_AND_PERMISSIONS.md`. `USER_ROLES_AND_PERMISSIONS.md` covers role/scope governance.

**Consolidation action:** These documents are complementary, not competing. Add cross-reference pointers. `USER_ROLES_AND_PERMISSIONS.md` is the role/permission authority; `capability-matrix.md` retains the CAP-XXX code registry. No retirement needed.

---

### DUP-008: Gap Register — Two Registers

**Severity:** Medium

**Files involved:**
- `docs/08_reports/BACKEND_GAP_REGISTER.md` (current — 19 gaps, all resolved)
- `backend/docs/system/gap-register.md` (legacy — G01–Gxx, from pre-Sessions-2 baseline)

**What is duplicated:**
Both are gap registers. The legacy register tracks gaps from the original refactor pass (G01–Gxx); the backend gap register tracks Phase 2 discovery gaps (AG-001–EG-003).

**Key divergence:** The legacy register covers architectural violations (VIOLATION type), code-missing items, and doc-missing items from the original build. The backend gap register covers documentation/implementation gaps discovered in Phase 2. They address different generations of work.

**Consolidation action:** Both are valid for their respective phases. Legacy register should be annotated as SUPERSEDED FOR BACKEND GAPS (Phase 2 register is authoritative) but retained as historical record of the original build refactor.

---

### DUP-009: Progress Tracking — Multiple Trackers

**Severity:** Low

**Files involved:**
- `ops/hrms-progress.md` (UI build session history, 1,113 lines)
- `ops/build-progress.md` (UI archetype build status, H01–H13)
- `backend/docs/system/progress.md` (backend refactor progress, G01–Gxx)
- `ops/tracker.md` (file read tracker for cataloguing pass)
- `ops/normalisation-tracker.md` (file read tracker for normalisation pass)
- `backend/docs/system/pending.md` (legacy backend pending)
- `ops/pending.md` (current pending — 10 UI pages + 2 deferred)
- `backend/pending.md` (legacy backend pending)

**What is duplicated:**
Multiple documents track project progress and pending work. They represent different scopes (UI vs. backend, different sessions).

**Key divergence:** All are operational artifacts for session continuity. They do not compete on authority. The pending items in `ops/pending.md` are the current active work items.

**Consolidation action:** No structural change needed. Operational artifacts may coexist. However, `backend/pending.md` and `backend/docs/system/pending.md` should be annotated as superseded by `ops/pending.md` for pending work items, and the legacy tracker files (`ops/tracker.md`, `ops/normalisation-tracker.md`) should be annotated as completed artifacts.

---

### DUP-010: HRMS Build Specs — Archive Redundancy

**Severity:** Low

**Files involved:**
- `backend/docs/system/MASTER BUILD SPEC.md` (v2.0 merged)
- `backend/docs/system/MASTER BEHAVIOR SPEC.md` (merged canonical)
- `backend/docs/system/archive/COMPLETE HRMS BUILD SPEC.md`
- `backend/docs/system/archive/HRMS SPEC.md`
- `backend/docs/system/archive/HRMS SYSTEM BEHAVIOR SPEC.md`
- `backend/docs/system/archive/HRMS Repo Surgical Upgrade Spec.md`
- `backend/docs/system/archive/MARKET-VALIDATED BEHAVIOR SPEC.md`

**What is duplicated:**
System specifications at different evolution stages. The MASTER docs are merged versions of the archive docs. Architecture section of MASTER BUILD SPEC also duplicated by `BACKEND_ARCHITECTURE.md`.

**Consolidation action:** Archive directory exists for these — correct placement. MASTER BUILD SPEC and MASTER BEHAVIOR SPEC should be annotated as superseded by governance layer docs. Archive files need no change (they are already archived).

---

### DUP-011: Architectural Decisions — Informal vs. Formal

**Severity:** Low

**Files involved:**
- `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` (formal ADR)
- `ops/answers.md` (informal C1–C5 decisions)
- `docs/08_reports/RECOMMENDED_ADR_ROADMAP.md` (recommended future ADRs)

**What is duplicated:**
Some decisions in `ops/answers.md` (C3: automation-service as infrastructure, C4: decision-service standalone, C5: WhatsApp as access channel) also appear in ADR-001 or should appear as formal ADRs.

**Consolidation action:** `ops/answers.md` should be retained as a historical record. Its decisions should be formalized into ADR-002 onward (per RECOMMENDED_ADR_ROADMAP.md). Duplication is low risk — informal record supplementing formal record.

---

## DUPLICATION SUMMARY

| ID | Domains Affected | Severity | Action Required |
|----|-----------------|----------|----------------|
| DUP-001 | Domain Model | High | Retire 2 legacy docs (annotate as superseded) |
| DUP-002 | Feature Scope | High | Retire 1 legacy doc (annotate as superseded) |
| DUP-003 | Service Catalog | High | Retire 2 legacy docs (annotate as superseded); correct stale claim |
| DUP-004 | Project Identity | Medium | Retire 2 legacy docs (annotate as superseded) |
| DUP-005 | Auth/Security | Medium | Retire 1 legacy doc (annotate as superseded) |
| DUP-006 | API Standards | Medium | Retain split authority; add cross-references |
| DUP-007 | Roles/Capabilities | Medium | Retain both; add cross-references |
| DUP-008 | Gap Registers | Medium | Annotate legacy as historical; retain both |
| DUP-009 | Progress Tracking | Low | Annotate legacy pending docs as superseded |
| DUP-010 | Build Specs | Low | Annotate MASTER docs as superseded; archive untouched |
| DUP-011 | Decision Records | Low | Formalize informal decisions into future ADRs |

**Documents requiring retirement annotation: 11**
**Documents requiring cross-reference additions: 5**
**Documents requiring no action: many (coexist correctly)**
