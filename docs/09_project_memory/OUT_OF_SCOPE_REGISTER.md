# OUT-OF-SCOPE REGISTER

Layer: Project Memory
Status: Active
Created: 2026-06-18
Rule: Items in this register are intentionally excluded from Phase 4 and do not constitute gaps. Do not reopen without explicit owner authorization to add scope.

---

## Classification Criteria

An item qualifies as OUT-OF-SCOPE only if:
- Intentionally deferred to a future phase
- Future regional expansion
- Optional/ADD-ON capability not active in current scope
- Explicitly classified PLANNED or ADD-ON in FEATURE_SCOPE.md
- Requires external decision not yet made

---

## §1 — REPOSITORY STRUCTURE (OS-001)

**Item ID:** OS-001
**Title:** Frontend Relocation from `backend/ui/` to `frontend/` root directory
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — Phase 5+ decision
**Original Source:** Phase 3 authority capture; C-003; AI_OPERATING_CONTEXT.md
**Evidence Source:** `backend/ui/` confirmed as frontend location; C-003 explicitly states "Frontend stays at `backend/ui/` through Phase 4"
**Resolution Source:** C-003 (Phase 4 condition — no relocation)
**Resolution Date:** 2026-06-17
**Resolved By:** Phase 3 governance decision; C-003 authorization condition
**Decision Summary:** Frontend location is `backend/ui/` through Phase 4. The `frontend/` directory at repo root is a placeholder (unconfirmed state). Relocation is out of scope for all current work.
**Affected Components:** `backend/ui/`; build system; Docker compose
**Owner Required:** YES — if relocation is ever decided
**Future Impact:** MEDIUM — relocation would require Docker compose update (REQUIRES_APPROVAL) and path reference updates
**Reopen Criteria:** Owner authorization for a post-Phase 4 relocation sprint
**Related Register Entries:** AC-040 (frontend location confirmed)

---

## §2, §3, §4 — CI ACTIVATION STRATEGY (OS-002, OS-003, OS-004)

**Item ID:** OS-002 / OS-003 / OS-004
**Title:** CI workflow activation, CI/CD pipeline strategy, container registry selection
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — infrastructure decision
**Original Source:** OA-007; dead CI workflow files (archived SD-004)
**Evidence Source:** `backend/.github/workflows/` files archived to `backend/docs/system/archive/dead-ci-workflows/`; root `.github/workflows/ci.yml` exists (live pipeline) but activation strategy undecided
**Resolution Source:** SD-004 (archive executed); OA-007 compressed to OUT-OF-SCOPE
**Resolution Date:** 2026-06-18
**Resolved By:** OWNER-REQUIRED compression
**Decision Summary:** CI activation strategy (what to run, on which branches, with what container registry) is an owner infrastructure decision. Archived workflow files are available for reference. The existing root `ci.yml` is the live pipeline. Activating, expanding, or migrating CI is out of scope for Phase 4.
**Affected Components:** `.github/workflows/ci.yml`; container registry
**Owner Required:** YES — if CI expansion is decided
**Future Impact:** MEDIUM — CI activation requires OD-002 (scaling strategy) decision first
**Reopen Criteria:** Owner authorizes CI/CD sprint
**Related Register Entries:** SD-004 (CI archive); OD-002 (scaling strategy)

---

## §5 — QUICKBOOKS CREDENTIALS / INTEGRATION (OS-005)

**Item ID:** OS-005
**Title:** QuickBooks API Credentials (External Accounting Integration)
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — ADD-ON feature
**Original Source:** INTEGRATION_CATALOG.md §QuickBooks; Mandate 2 OWNER-REQUIRED compression
**Evidence Source:** FEATURE_SCOPE.md: accounting integration is ADD-ON; no QuickBooks code found in `backend/integrations/`
**Resolution Source:** OWNER-REQUIRED compression — classified OUT-OF-SCOPE not EXTERNAL-DEPENDENCY (code doesn't exist yet)
**Resolution Date:** 2026-06-18
**Resolved By:** Mandate 2 compression
**Decision Summary:** QuickBooks integration is an ADD-ON feature. No implementation code exists. Credentials are irrelevant until the feature is built. Out of scope for Phase 4.
**Affected Components:** None (not yet implemented)
**Owner Required:** YES — if ADD-ON is activated
**Future Impact:** LOW (Phase 4); MEDIUM (when ADD-ON activated — requires integration sprint)
**Reopen Criteria:** Owner activates QuickBooks ADD-ON feature
**Related Register Entries:** OS-006 (SAP — same pattern)

---

## §6 — SAP CREDENTIALS / INTEGRATION (OS-006)

**Item ID:** OS-006
**Title:** SAP API Credentials (Enterprise ERP Integration)
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — ADD-ON feature
**Original Source:** INTEGRATION_CATALOG.md §SAP; Mandate 2 OWNER-REQUIRED compression
**Evidence Source:** FEATURE_SCOPE.md: SAP integration is ADD-ON; no SAP code in `backend/integrations/`
**Resolution Source:** OWNER-REQUIRED compression — classified OUT-OF-SCOPE
**Resolution Date:** 2026-06-18
**Resolved By:** Mandate 2 compression
**Decision Summary:** SAP integration is an ADD-ON feature with no implementation code. Credentials are not applicable until implementation. Out of scope for Phase 4.
**Affected Components:** None (not yet implemented)
**Owner Required:** YES — if ADD-ON is activated
**Future Impact:** LOW (Phase 4); HIGH (when ADD-ON activated — SAP onboarding is complex)
**Reopen Criteria:** Owner activates SAP ADD-ON feature
**Related Register Entries:** OS-005 (QuickBooks — same pattern)

---

## §7 — FRONTEND GAP REGISTER OOS ITEMS (OS-007 to OS-011)

**Item ID:** OS-007 / OS-008 / OS-009 / OS-010 / OS-011
**Title:** G-001 (OKR screen), G-002 (LMS screen), G-003 (expense analytics), G-004 (project tracking screen), G-005 (asset management screen)
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — PLANNED or ADD-ON screens
**Original Source:** `docs/03_frontend_authority/FRONTEND_GAP_REGISTER.md` items G-001 to G-005
**Evidence Source:** FEATURE_SCOPE.md: OKR, LMS, expense analytics, project tracking, asset management are PLANNED/ADD-ON features
**Resolution Source:** Phase 3 frontend authority gap register — classified OOS at creation
**Resolution Date:** 2026-06-17
**Resolved By:** Phase 3 authority capture
**Decision Summary:** These 5 screens correspond to features that are either PLANNED or ADD-ON in FEATURE_SCOPE.md. No backend routes exist for them in Phase 4. Do not build these screens during Phase 4 frontend implementation.
**Affected Components:** None (screens not to be built)
**Owner Required:** YES — if feature status changes
**Future Impact:** LOW (Phase 4); MEDIUM (when activated — each requires full frontend + backend sprint)
**Reopen Criteria:** Owner changes feature status from PLANNED/ADD-ON to LIVE
**Related Register Entries:** OS-012 to OS-020 (other ADD-ON screens)

---

## §8 — ADD-ON SCREENS (OS-012 to OS-020)

**Item ID:** OS-012 / OS-013 / OS-014 / OS-015 / OS-016 / OS-017 / OS-018 / OS-019 / OS-020
**Title:** G-010 (expense claim submission), G-011 (expense approval), G-012 (asset tracking), G-013 (biometric enrollment), G-014 (shift scheduling), G-015 (succession planning), G-016 (engagement surveys), G-017 (benefits enrollment), G-018 (document management)
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — ADD-ON screens
**Original Source:** `docs/03_frontend_authority/FRONTEND_GAP_REGISTER.md` items G-010 to G-018
**Evidence Source:** FEATURE_SCOPE.md: all these features are ADD-ON or PLANNED; no gateway routes exist for expense-claim, asset, biometric, succession, engagement, document-management services
**Resolution Source:** Phase 3 frontend authority gap register — classified OOS at creation
**Resolution Date:** 2026-06-17
**Resolved By:** Phase 3 authority capture
**Decision Summary:** Nine ADD-ON screens excluded from Phase 4. No backend routes or service implementations exist for them. Do not build during Phase 4 frontend implementation.
**Affected Components:** None (screens not to be built)
**Owner Required:** YES — if ADD-ON is activated
**Future Impact:** LOW (Phase 4); VARIES per feature (when activated)
**Reopen Criteria:** Owner activates each specific ADD-ON feature
**Related Register Entries:** OS-007 to OS-011 (PLANNED screens); AC-031 (LMS OOS)

---

## §9 — WHATSAPP STANDALONE SCREEN (OS-021)

**Item ID:** OS-021
**Title:** Dedicated WhatsApp Management / Conversation Screen
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — notification delivery only; no management screen scoped
**Original Source:** Phase 3 frontend gap analysis; FRONTEND_GAP_REGISTER.md
**Evidence Source:** Gateway route 25 confirmed (`/api/v1/whatsapp`); whatsapp-service is outbound notification only per service-map.md; no inbound conversation management in feature scope
**Resolution Source:** Mandate 2 SAFE-DEFAULT; frontend gap register
**Resolution Date:** 2026-06-18
**Resolved By:** Feature scope analysis — outbound notifications only
**Decision Summary:** WhatsApp integration is outbound notification only (leave approvals, payslip delivery, workflow notifications). No dedicated WhatsApp management/conversation screen is in scope. The `/api/v1/whatsapp` endpoint is used by backend notification service, not directly by frontend screens.
**Affected Components:** whatsapp-service (backend only)
**Owner Required:** YES — if inbound conversation management is desired
**Future Impact:** LOW (no frontend screen needed)
**Reopen Criteria:** Owner adds WhatsApp inbound conversation management to feature scope
**Related Register Entries:** ED-005 (WhatsApp credentials); AC-006 (gateway route 25 confirmed)

---

## §10 — BANKING STANDALONE SCREEN (OS-022)

**Item ID:** OS-022
**Title:** Dedicated Banking / Disbursement Management Screen
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — disbursement status shown via payroll workflow only
**Original Source:** Phase 3 frontend gap analysis
**Evidence Source:** Gateway route 24 confirmed (`/api/v1/banking`); banking-service provides disbursement status; EWA status shown via finance screens; no standalone banking management screen in PRODUCT_WORKFLOWS.md
**Resolution Source:** Phase 3 frontend authority; Mandate 2
**Resolution Date:** 2026-06-18
**Resolved By:** Feature scope analysis
**Decision Summary:** Banking/disbursement status is accessible via the payroll workflow screens. No dedicated standalone banking management screen is in scope for Phase 4.
**Affected Components:** bank-service (backend only for disbursement)
**Owner Required:** YES — if standalone banking screen is required
**Future Impact:** LOW
**Reopen Criteria:** Owner adds dedicated banking management screen to feature scope
**Related Register Entries:** ED-004 (Raast credentials); SD-034 (Raast protocol default)

---

## §11 — PLANNED FEATURES F-023 / F-024 (OS-023, OS-024)

**Item ID:** OS-023 / OS-024
**Title:** Travel Management (F-023) and Project Tracker (F-024) — PLANNED features
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — PLANNED feature status
**Original Source:** FEATURE_SCOPE.md F-023, F-024; SERVICE_CATALOG.md
**Evidence Source:** FEATURE_SCOPE.md: F-023 (Travel) = PLANNED; F-024 (Project) = PLANNED; gateway routes confirmed (`/api/v1/travel`, `/api/v1/projects`) but services are feature-incomplete
**Resolution Source:** FEATURE_SCOPE.md authority
**Resolution Date:** 2026-06-17
**Resolved By:** FEATURE_SCOPE.md classification
**Decision Summary:** Travel and Project services have confirmed gateway routes but PLANNED feature status means backend implementation is not complete. Frontend screens for these features must not be built until FEATURE_SCOPE.md status changes to LIVE.
**Affected Components:** travel-service; project-service
**Affected Routes:** `/api/v1/travel`; `/api/v1/projects`
**Owner Required:** YES — to promote from PLANNED to LIVE
**Future Impact:** MEDIUM — when promoted to LIVE, both frontend and backend sprints required
**Reopen Criteria:** Owner changes F-023/F-024 status to LIVE in FEATURE_SCOPE.md
**Related Register Entries:** SD-019/020 (service catalog defaults); AC-034 (document management OOS)

---

## §12 — ADD-ON WORKFLOWS (OS-025, OS-026)

**Item ID:** OS-025 / OS-026
**Title:** WF-005 (Expense Claim Workflow) and WF-006 (EWA Request Workflow) as ADD-ON
**Classification:** OUT-OF-SCOPE
**Current Status:** WF-006 (EWA) is partially implemented (architecture confirmed); WF-005 (expense) is ADD-ON
**Original Source:** PRODUCT_WORKFLOWS.md WF-005/006; Mandate 2 classification
**Evidence Source:** FEATURE_SCOPE.md (Expense Claims = ADD-ON); `backend/services/finance/ewa.py` (EWA architecture confirmed — AC-004); EWA requires ED-004 (Raast credentials)
**Resolution Source:** Mandate 2 SAFE-DEFAULT; feature scope
**Resolution Date:** 2026-06-18
**Resolved By:** Feature scope analysis
**Decision Summary:** WF-005 (Expense Claim) is ADD-ON — no expense claim backend exists. WF-006 (EWA) architecture is confirmed (FinancialWellnessService + Raast) but requires ED-004 (Raast credentials) for production — frontend EWA screens can be built but disbursement requires credentials.
**Affected Components:** expense-service (ADD-ON, not built); finance/ewa.py (EWA confirmed)
**Owner Required:** YES — for WF-005 ADD-ON activation; ED-004 for WF-006 production readiness
**Future Impact:** MEDIUM (WF-006 frontend buildable now; disbursement blocked on ED-004); HIGH (WF-005 requires full ADD-ON sprint)
**Reopen Criteria:** Owner activates Expense Claim ADD-ON; or Raast credentials provisioned for EWA
**Related Register Entries:** AC-004 (EWA architecture); ED-004 (Raast); OS-012 (expense screen OOS)

---

## §13 — BIOMETRIC VENDOR SPECIFICS (OS-027)

**Item ID:** OS-027
**Title:** Biometric Device Vendor Selection and Hardware Integration
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — hardware vendor decision
**Original Source:** INTEGRATION_CATALOG.md §Biometric; Mandate 2 OWNER-REQUIRED compression
**Evidence Source:** `backend/country/pakistan/` (attendance logic exists); no biometric vendor SDK or client found; FEATURE_SCOPE.md biometric attendance is ADD-ON
**Resolution Source:** OWNER-REQUIRED compression
**Resolution Date:** 2026-06-18
**Resolved By:** Mandate 2 compression — classified OUT-OF-SCOPE (no implementation code; hardware vendor choice)
**Decision Summary:** Biometric attendance integration is ADD-ON. No implementation exists. Vendor selection (ZKTeco, Suprema, Anviz, etc.) and hardware integration are both out of scope for Phase 4. Manual check-in/check-out via attendance-service is the LIVE path.
**Affected Components:** attendance-service (manual path LIVE); biometric module (ADD-ON, not built)
**Owner Required:** YES — vendor selection; hardware procurement
**Future Impact:** LOW (Phase 4); HIGH (when activated — hardware + SDK integration sprint required)
**Reopen Criteria:** Owner selects biometric vendor and authorizes ADD-ON sprint
**Related Register Entries:** OS-013 (biometric enrollment screen OOS)

---

## §14 — MULTI-COUNTRY EXPANSION (OS-028)

**Item ID:** OS-028
**Title:** Multi-Country Expansion Architecture and Country-Specific Modules
**Classification:** OUT-OF-SCOPE
**Current Status:** Deferred — post-launch decision
**Original Source:** OAQ-005 (AI_OPERATING_CONTEXT.md); OD-003 (data residency)
**Evidence Source:** `backend/country/pakistan/` (only Pakistan implemented); FD-007 (country isolation architecture correct); FEATURE_SCOPE.md (Pakistan launch only)
**Resolution Source:** OWNER-REQUIRED compression; OD-003
**Resolution Date:** 2026-06-18
**Resolved By:** Feature scope — Pakistan only for Phase 4
**Decision Summary:** India, UAE, Saudi Arabia, or other country modules are entirely out of scope. The architecture correctly supports future expansion (FD-007) but no country module other than Pakistan is to be built.
**Affected Components:** `backend/country/` (only `pakistan/` subdirectory)
**Owner Required:** YES — country-by-country expansion decisions
**Future Impact:** HIGH (when activated — requires full country compliance + data residency research)
**Reopen Criteria:** Owner authorizes specific country expansion
**Related Register Entries:** OD-003 (data residency decision); AC-039 (architecture confirmed)
