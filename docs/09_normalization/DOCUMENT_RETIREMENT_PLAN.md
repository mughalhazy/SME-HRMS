# DOCUMENT RETIREMENT PLAN

Status: Active
Authority Level: Medium
Created: 2026-06-16
Owner: AI
Phase: Documentation Normalization and Authority Consolidation

---

## PURPOSE

For every document classified as Retired, Legacy, or Operational Artifact in the classification matrix, this plan defines the disposition: Keep (as-is), Annotate (add superseded header), Merge (content into authority doc), or Archive (move to archive folder).

Per the execution rules: **Do not delete documentation.** All dispositions use status annotations, cross-references, and archiving — not deletion.

---

## DISPOSITION DEFINITIONS

| Disposition | Action |
|-------------|--------|
| **ANNOTATE-SUPERSEDED** | Add a header block to the document stating it is superseded, what supersedes it, and the date. Do not edit body content. |
| **ANNOTATE-HISTORICAL** | Add a header block stating the document is a historical snapshot valid only as of its creation date. Do not edit body content. |
| **ANNOTATE-COMPLETED** | Add a header block stating the document is a completed operational artifact. No further updates needed. |
| **ANNOTATE-STALE** | Add a header note to a specific section or claim identifying it as stale, pointing to current authority. |
| **KEEP-AS-IS** | No annotation needed. Document is appropriately classified and labeled. |
| **MERGE-INTO** | Valuable content should be merged into an authority document before annotation. |
| **RETAIN-ACTIVE** | Document remains active; no retirement action needed. |

---

## RETIREMENT ACTIONS BY DOCUMENT

### 1. `backend/docs/canon/domain-model.md`

**Disposition:** ANNOTATE-SUPERSEDED

**Superseded by:** `docs/00_authority/DOMAIN_MODEL.md`

**Header to add:**
```
> ⚠️ SUPERSEDED (2026-06-16)
> This document has been superseded by `docs/00_authority/DOMAIN_MODEL.md`.
> That document is the authoritative domain entity model — more complete, includes
> the multi-tenancy invariant and compound FK correction from migration 014.
> Do not update this file. Read from the authority doc.
```

---

### 2. `backend/docs/canon/data-architecture.md`

**Disposition:** ANNOTATE-SUPERSEDED

**Superseded by:** `docs/01_backend/DATABASE_SCHEMA.md` (schema) and `docs/00_authority/DOMAIN_MODEL.md` (entities)

**Header to add:**
```
> ⚠️ SUPERSEDED (2026-06-16)
> This document has been superseded by:
>   • `docs/01_backend/DATABASE_SCHEMA.md` — authoritative schema (migrations 001–015,
>     compound FK pattern corrected in migration 014, parental leave in 015)
>   • `docs/00_authority/DOMAIN_MODEL.md` — authoritative entity definitions
> This file pre-dates compound FK corrections and migration 014/015.
> Do not use for schema decisions.
```

---

### 3. `backend/docs/canon/release-scope.md`

**Disposition:** ANNOTATE-SUPERSEDED

**Superseded by:** `docs/00_authority/FEATURE_SCOPE.md`

**Header to add:**
```
> ⚠️ SUPERSEDED (2026-06-16)
> This document has been superseded by `docs/00_authority/FEATURE_SCOPE.md`.
> The new document uses F-XXX identifiers, includes Document Management as OUT OF SCOPE,
> and reflects the current 24-feature scope with IMPLEMENTED/ADD-ON/PLANNED status.
> Do not update this file.
```

---

### 4. `backend/docs/canon/security-model.md`

**Disposition:** ANNOTATE-SUPERSEDED

**Superseded by:** `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md`

**Header to add:**
```
> ⚠️ SUPERSEDED (2026-06-16)
> This document has been superseded by `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md`.
> The new document covers JWT HS256 model, token lifecycle, tenant_id propagation,
> session management, rate limiting, and exempt routes — validated against actual code.
> Do not update this file.
```

---

### 5. `backend/docs/canon/service-map.md`

**Disposition:** ANNOTATE-SUPERSEDED

**Superseded by:** `docs/01_backend/SERVICE_CATALOG.md`

**Header to add:**
```
> ⚠️ SUPERSEDED (2026-06-16)
> This document has been superseded by `docs/01_backend/SERVICE_CATALOG.md`.
> Existing TBD annotations remain for traceability. Note: ewa-financial-service
> references were annotated TBD in Phase 2 (ARG-002).
> Do not update this file.
```

---

### 6. `backend/docs/system/service-manifest.md`

**Disposition:** ANNOTATE-SUPERSEDED + ANNOTATE-STALE (employee-service claim)

**Superseded by:** `docs/01_backend/SERVICE_CATALOG.md`

**Header to add:**
```
> ⚠️ SUPERSEDED (2026-06-16)
> This document has been superseded by `docs/01_backend/SERVICE_CATALOG.md`.
>
> ⚠️ KNOWN STALE CLAIM: The employee-service entry lists `services/employee-service/`
> (TypeScript) as the implementation. This is INCORRECT as of 2026-06-16.
> The employee-service is now implemented in Python:
>   • `backend/employee_service.py`
>   • `backend/employee_api.py`
> See EG-001 resolution in `docs/08_reports/BACKEND_GAP_REGISTER.md`.
> Do not use this manifest for service implementation status.
```

---

### 7. `backend/docs/system/system-purpose.md`

**Disposition:** ANNOTATE-SUPERSEDED

**Superseded by:** `docs/00_authority/PROJECT_CHARTER.md`

**Header to add:**
```
> ⚠️ SUPERSEDED (2026-06-16)
> This document has been superseded by `docs/00_authority/PROJECT_CHARTER.md`.
> The 7 design principles (P1–P7) documented here are fully preserved in the Charter.
> Do not update this file.
```

---

### 8. `backend/docs/system/MASTER BUILD SPEC.md`

**Disposition:** ANNOTATE-SUPERSEDED

**Superseded by:** `docs/01_backend/BACKEND_ARCHITECTURE.md` (architecture) and `docs/00_authority/PROJECT_CHARTER.md` (identity/purpose)

**Header to add:**
```
> ⚠️ SUPERSEDED (2026-06-16)
> The architecture content in this document has been superseded by
> `docs/01_backend/BACKEND_ARCHITECTURE.md`. The system identity and design
> principles have been superseded by `docs/00_authority/PROJECT_CHARTER.md`.
> This document remains a valuable historical record of the build specification intent.
> Do not use for current architecture decisions.
```

---

### 9. `backend/docs/system/MASTER BEHAVIOR SPEC.md`

**Disposition:** ANNOTATE-SUPERSEDED

**Superseded by:** `docs/00_authority/PRODUCT_WORKFLOWS.md` (behavior) and `docs/00_authority/PROJECT_CHARTER.md` (principles)

**Header to add:**
```
> ⚠️ SUPERSEDED (2026-06-16)
> The system behavior content has been superseded by `docs/00_authority/PRODUCT_WORKFLOWS.md`
> and the design principles by `docs/00_authority/PROJECT_CHARTER.md`.
> This document remains a historical record of the merged behavior specification.
> Do not use for current behavior decisions.
```

---

### 10. `backend/docs/system/gap-register.md`

**Disposition:** ANNOTATE-SUPERSEDED (as active gap register) + ANNOTATE-HISTORICAL (as build-phase record)

**Superseded by:** `docs/08_reports/BACKEND_GAP_REGISTER.md` (for backend gaps)

**Header to add:**
```
> ⚠️ SUPERSEDED AS ACTIVE GAP REGISTER (2026-06-16)
> For current backend gap status, see `docs/08_reports/BACKEND_GAP_REGISTER.md`
> (Phase 2 discovery gaps — all 19 resolved).
>
> HISTORICAL VALUE: This register documents the original refactor pass gaps (G01–Gxx)
> from the initial backend build sessions. It remains a valid historical record of
> the architectural violations and missing implementations found during build.
```

---

### 11. `ops/HRMS PRODUCT SPEC.md`

**Disposition:** KEEP-AS-IS (already self-annotated as superseded)

**Note:** This document is already labeled "SUPERSEDED... kept as a reference for original intent. Do not edit." The existing annotation is sufficient. The stale path references (pointing to old `v3_extracted/SME-HRMS-main/docs/system/` paths) should not be corrected per the document's own "Do not edit" directive. Annotating the stale paths alongside the existing superseded header would satisfy both concerns; however, per "do not edit" instruction on this document, this is a decision for the human owner.

---

### 12. `backend/docs/reports/alignment_final.md`

**Disposition:** ANNOTATE-HISTORICAL

**Note:** Already effectively a stub pointing to `intent_build_alignment.md`. Valid for 2026-03-31 baseline only.

**Header to add:**
```
> HISTORICAL RECORD — 2026-03-31 baseline snapshot only.
> See `backend/docs/system/intent_build_alignment.md` for the full alignment record.
> This snapshot does not reflect Sessions 2–8 changes (50+ new service files).
```

---

### 13. `backend/docs/system/intent_build_alignment.md`

**Disposition:** ANNOTATE-HISTORICAL

**Note:** This document already self-disclaims its scope limitation (Sessions 2–8 not re-validated). The existing disclaimer is sufficient. No additional annotation needed.

---

### 14. `backend/docs/system/pending.md`

**Disposition:** ANNOTATE-SUPERSEDED (as pending tracker)

**Superseded by:** `ops/pending.md`

**Header to add:**
```
> LEGACY PENDING LIST — superseded by `ops/pending.md` for current pending items.
> This file reflects the backend refactor phase pending state. Review `ops/pending.md`
> for the current 10 UI pages and 2 deferred items.
```

---

### 15. `backend/pending.md`

**Disposition:** ANNOTATE-SUPERSEDED

Same as above — point to `ops/pending.md`.

---

### 16. `ops/hrms-directory-structure-v1.md`

**Disposition:** ANNOTATE-HISTORICAL

**Header to add:**
```
> HISTORICAL RECORD — Pre-2026-06-07 directory structure.
> The workspace was restructured on 2026-06-07: `v3_extracted/SME-HRMS-main/` renamed
> to `backend/`; docs moved to `ops/`. This file reflects the pre-restructure layout.
```

---

### 17. `ops/normalisation-tracker.md`

**Disposition:** ANNOTATE-COMPLETED

**Header to add:**
```
> COMPLETED ARTIFACT — Full-workspace normalisation read-through pass is complete
> (109/109 files read). This tracker is a historical record of that pass.
> 16 cross-file findings are logged here. Follow-up actions are in
> `docs/09_normalization/` outputs from the Documentation Normalization phase.
```

---

### 18. `ops/tracker.md`

**Disposition:** ANNOTATE-COMPLETED

**Header to add:**
```
> COMPLETED ARTIFACT — Full workspace cataloguing read tracker (2026-06-06).
> All files have been read and catalogued. This tracker is a historical record.
```

---

### 19. Archive Documents (`backend/docs/system/archive/`)

**Disposition:** KEEP-AS-IS

All 7 archive documents are already in the `/archive/` subdirectory, which signals their archived status. No additional annotation needed. They are origin artifacts and should be preserved intact.

---

### 20. Build Pass Stubs (`backend/docs/design/backward-compatibility-report-p28.md`, `data-integrity-report-p29.md`, `event-reliability-report-p30.md`, `workflow-integrity-report-p31.md`, `final-convergence-report-p32.md`, `final-system-certification-pass-p33.md`)

**Disposition:** KEEP-AS-IS

These stubs already contain pointers to `convergence-history.md`. Their stub status is self-evident. No additional annotation needed.

---

## NON-RETIREMENT ACTIONS REQUIRED

These documents are not being retired but require specific updates identified in the conflict and duplication analysis.

| Document | Action | Reason |
|----------|--------|--------|
| `docs/00_authority/DOMAIN_MODEL.md` | Update "57+ DB tables" → "58 tables" | CON-004: numeric consistency with DATABASE_SCHEMA.md |
| `backend/docs/services/employee-service.md` | Add note that Python implementation now exists | CON-001: service-level doc may describe TypeScript only |
| `backend/docs/canon/workflow-catalog.md` | Add cross-reference to `PRODUCT_WORKFLOWS.md` | DUP-004: make complementary relationship explicit |
| `backend/docs/canon/capability-matrix.md` | Add cross-reference to `USER_ROLES_AND_PERMISSIONS.md` | DUP-007: make complementary relationship explicit |
| `backend/docs/canon/event-catalog.md` | Add cross-reference to `EVENT_AND_QUEUE_ARCHITECTURE.md` | DUP-009: make complementary relationship explicit |
| `design/hrms-archetype-system-v1.md` | Flag L322 engagement dimensions as stale placeholder | CON-007: enum mismatch with hrms-api-contracts.md |

---

## RETIREMENT SUMMARY

| # | Document | Disposition | Replaced By |
|---|----------|-------------|-------------|
| 1 | `backend/docs/canon/domain-model.md` | ANNOTATE-SUPERSEDED | `docs/00_authority/DOMAIN_MODEL.md` |
| 2 | `backend/docs/canon/data-architecture.md` | ANNOTATE-SUPERSEDED | `docs/01_backend/DATABASE_SCHEMA.md` |
| 3 | `backend/docs/canon/release-scope.md` | ANNOTATE-SUPERSEDED | `docs/00_authority/FEATURE_SCOPE.md` |
| 4 | `backend/docs/canon/security-model.md` | ANNOTATE-SUPERSEDED | `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` |
| 5 | `backend/docs/canon/service-map.md` | ANNOTATE-SUPERSEDED | `docs/01_backend/SERVICE_CATALOG.md` |
| 6 | `backend/docs/system/service-manifest.md` | ANNOTATE-SUPERSEDED + STALE CLAIM | `docs/01_backend/SERVICE_CATALOG.md` |
| 7 | `backend/docs/system/system-purpose.md` | ANNOTATE-SUPERSEDED | `docs/00_authority/PROJECT_CHARTER.md` |
| 8 | `backend/docs/system/MASTER BUILD SPEC.md` | ANNOTATE-SUPERSEDED | `docs/01_backend/BACKEND_ARCHITECTURE.md` |
| 9 | `backend/docs/system/MASTER BEHAVIOR SPEC.md` | ANNOTATE-SUPERSEDED | `docs/00_authority/PRODUCT_WORKFLOWS.md` |
| 10 | `backend/docs/system/gap-register.md` | ANNOTATE-SUPERSEDED + HISTORICAL | `docs/08_reports/BACKEND_GAP_REGISTER.md` |
| 11 | `ops/HRMS PRODUCT SPEC.md` | KEEP-AS-IS (self-annotated) | Self-labeled superseded |
| 12 | `backend/docs/reports/alignment_final.md` | ANNOTATE-HISTORICAL | Stub; see intent_build_alignment.md |
| 13 | `backend/docs/system/intent_build_alignment.md` | ANNOTATE-HISTORICAL (already self-disclaimed) | Snapshot only |
| 14 | `backend/docs/system/pending.md` | ANNOTATE-SUPERSEDED | `ops/pending.md` |
| 15 | `backend/pending.md` | ANNOTATE-SUPERSEDED | `ops/pending.md` |
| 16 | `ops/hrms-directory-structure-v1.md` | ANNOTATE-HISTORICAL | Restructured 2026-06-07 |
| 17 | `ops/normalisation-tracker.md` | ANNOTATE-COMPLETED | Completed artifact |
| 18 | `ops/tracker.md` | ANNOTATE-COMPLETED | Completed artifact |
| 19 | `backend/docs/system/archive/*.md` (7 files) | KEEP-AS-IS | Already archived |
| 20 | Build pass stubs (6 files) | KEEP-AS-IS | Self-evident stubs |
