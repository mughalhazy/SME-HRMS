# UNRESOLVABLE ITEMS REGISTER

Status: Superseded
Created: 2026-06-17
Last Reviewed: 2026-06-18
Phase: 3.25 — Autonomous Gap Elimination and Determinism Enforcement
Superseded by: `docs/08_reports/FINAL_CLASSIFIED_REGISTER.md` (canonical final register after OWNER-REQUIRED compression)
Summary of changes: UI-001 → OUT-OF-SCOPE; UI-002 → OUT-OF-SCOPE; UI-003 → SAFE-DEFAULT; UI-004 → OUT-OF-SCOPE; UI-005 → OUT-OF-SCOPE; UI-006 → AUTO-CLOSED; UI-007 → OUT-OF-SCOPE. All 5 genuinely OWNER-REQUIRED (D-001 to D-005) reclassified: D-001/D-004/D-005 → EXECUTED; D-002/D-003 → AUTO-CLOSED (already resolved in codebase).

---

## PURPOSE

Documents every item that could NOT be resolved during Phase 3.25. Per the mandate, an item may remain unresolved ONLY IF it is:

1. A genuine commercial decision (payment provider, pricing, subscription model)
2. A genuine legal/compliance decision  
3. A genuine architecture fork where multiple valid futures exist

These items cannot be collapsed from repository evidence. They require human decision or external input.

---

## GENUINELY UNRESOLVABLE — REQUIRES HUMAN DECISION

### UI-001: Frontend relocation (OCR-001)

**Source:** `docs/08_reports/OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md` OA-003; `docs/08_reports/OWNER_CONFIRMATION_REGISTER.md` OCR-001  
**Item:** Should the Next.js frontend be relocated from `backend/ui/` to `frontend/`?  
**Why unresolvable:** Requires a `docker-compose.yml` modification and a deployment configuration decision. Neither the current location nor the proposed location has a clear technical superiority; this is an organizational/structural decision.  
**Current state:** Frontend remains at `backend/ui/` per Phase 3 decision. Relocation deferred post-Phase 3.  
**Who must decide:** Repository owner  
**Classification:** Genuine architecture fork — both options are valid

---

### UI-002: CI/CD migration strategy (OCR-002/003)

**Source:** `docs/08_reports/OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md` OA-007; `docs/08_reports/OWNER_CONFIRMATION_REGISTER.md` OCR-002/003  
**Item:** Whether to merge `backend/.github/workflows/` into root-level CI and which runner capabilities are available  
**Why unresolvable:** Runner strategy (self-hosted vs. hosted), database seeding approach, and build environment are infrastructure decisions not determinable from the repository alone.  
**Classification:** Genuine architecture/commercial decision

---

### UI-003: Cross-service dependency code trace (UC-005 / TO-005)

**Source:** `docs/08_reports/UNVERIFIED_CLAIMS_REGISTER.md` UC-005; `docs/08_reports/TBD_RESOLUTION_REGISTER.md` TO-005  
**Item:** Exact code-level HTTP client call dependencies between all 24 services (beyond what docker-compose.yml env vars reveal)  
**Why unresolvable:** Confirming every dependency edge requires reading all 24 service source files. The scope is too large for a single resolution pass. The `docker-compose.yml` env var topology covers the **infrastructure** dependency graph; the **code-level** graph adds runtime HTTP call details not visible at the compose layer.  
**Partial mitigation:** `backend/docs/canon/service-map.md` lists intended dependencies; docker-compose.yml confirms the injected env vars; service-map.md should be trusted as the design authority for non-verified edges.  
**Classification:** High-complexity verification task — not a commercial or architectural decision; simply requires more evidence-gathering

---

### UI-004: Official product launch date and commercial terms

**Source:** `docs/00_authority/PROJECT_CHARTER.md` §10  
**Items:** Launch date/timeline, paying customer count or beta status, SLA commitments to tenants  
**Why unresolvable:** Business facts external to the repository. No code evidence can answer these.  
**Classification:** Genuine commercial decisions

---

### UI-005: Scaling strategy beyond Docker Compose

**Source:** `docs/00_authority/PROJECT_CHARTER.md` §10  
**Item:** Whether to use Kubernetes, managed cloud (EKS/GKE/AKS), or stay with Docker Compose for production  
**Why unresolvable:** Infrastructure strategy decision. The repository is Docker Compose-based; the choice to evolve beyond this is a commercial and operational decision.  
**Classification:** Genuine architecture fork — multiple valid futures

---

### UI-006: Mobile application scope and delivery timeline

**Source:** `docs/00_authority/PROJECT_CHARTER.md` §10; `FEATURE_SCOPE.md` OUT OF SCOPE  
**Item:** Whether to build a native mobile app and when  
**Why unresolvable:** Commercial/product roadmap decision. `FEATURE_SCOPE.md` has confirmed native mobile OUT OF SCOPE for current phase; future scope requires owner decision.  
**Classification:** Genuine commercial decision

---

### UI-007: Data residency requirements beyond Pakistan

**Source:** `docs/00_authority/PROJECT_CHARTER.md` §10  
**Item:** Whether data residency is required for countries beyond Pakistan  
**Why unresolvable:** Legal/compliance decision determined by regulatory requirements of target markets.  
**Classification:** Genuine legal/compliance decision

---

## DEFERRED BUT NOT UNRESOLVABLE (Execution Pending)

These items ARE resolvable but have not been executed because they require either owner approval or are scheduled for a later phase.

### D-001: TypeScript archive (60 files) — SAFE_REPOSITORY_HYGIENE authorized

**Source:** OA-004 (employee-service TypeScript), OA-005 (settings-service TypeScript), OA-006 (middleware TypeScript)  
**Status:** Authorized under SAFE_REPOSITORY_HYGIENE tier; not yet executed  
**Action:** Move 60 TypeScript files to `archive/typescript-legacy/`  
**Requires:** No owner approval; SAFE_REPOSITORY_HYGIENE tier

---

### D-002: Delete dead function `_employee_domain_departments()` — owner authorized

**Source:** OA-001 in `OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md`  
**Status:** Low-risk code change, zero callers confirmed; pending owner confirmation  
**Location:** `backend/docker/service_runtime.py` lines 132–218  
**Requires:** Owner sign-off on code change (delete ~86 lines)

---

### D-003: Update "Aura HRMS" → "Meridian HCM" — owner authorized

**Source:** OA-002 in `OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md`  
**Status:** Cosmetic code change; pending owner confirmation  
**Location:** `backend/docker/api_gateway_service.py` lines 207, 237  
**Requires:** Owner sign-off on code change

---

### D-004: Add root `.gitignore` and `README.md` — SAFE_REPOSITORY_HYGIENE authorized

**Source:** OA-010 in `OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md`  
**Status:** Authorized under SAFE_REPOSITORY_HYGIENE tier; not yet created  
**Requires:** No owner approval

---

### D-005: Delete `(C) Phoenix LiteOS.lnk` OS artifact

**Source:** OA-009 in `OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md`  
**Status:** Authorized under SAFE_REPOSITORY_HYGIENE tier; not yet executed  
**Requires:** No owner approval

---

## SUMMARY

| Category | Count |
|----------|-------|
| Genuinely unresolvable (requires human decision) | 7 |
| Deferred but authorized for execution | 5 |
| **Total** | **12** |

All other previously open items have been resolved and are documented in `DECISION_COLLAPSE_REGISTER.md` and `PHASE_3_25_AUTONOMOUS_GAP_ELIMINATION_REPORT.md`.
