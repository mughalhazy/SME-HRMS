# System Docs Catalogue

> **Read this first on any session start, restart, dropout, or mid-build continuation.**
> This file is the single entry point to all operational documentation for the AURA HRMS build.
> It does not contain decisions — it tells you where every decision lives.

> **Related catalogue:** This is the backend/ops-layer catalogue. For the UI design-layer catalogue (Meridian HCM, 48 pages), see `D:\HRMS\design\hrms-doc-catalogue-v1.md`, which already cross-references this file (its `catalogue.md` entry, Category: backend/docs/system/) as "the backend equivalent of the UI hrms-doc-catalogue-v1.md".

---

## Workspace

All build work lives under:
```
D:\HRMS\backend\
```
All system/ops docs live under:
```
backend/docs/system/
```
Do not reference docs outside this workspace unless explicitly told to.

---

## Document Index

### 1. `system-purpose.md`
**Purpose:** Defines what AURA HRMS is, why it exists, and the 7 non-negotiable design principles (P1–P7).

**Read when:** Starting a new session cold, or when a design decision needs to be validated against principles.

**Key content:**
- System identity: *TRUST INFRASTRUCTURE for workforce operations*
- P1 — Compliance is the product
- P2 — Payroll must never break
- P3 — Decisions > Dashboards
- P4 — AI must be explainable and reversible
- P5 — Country logic must be isolated
- P6 — Mobile-first
- P7 — WhatsApp is a real access channel

**Feeds into:** Every architectural decision. If a proposed change conflicts with P1–P7, it is wrong.

---

### 2. `success-criteria.md`
**Purpose:** Defines binary completion gates (S1–S35) across 5 tiers. The system is done when all are met.

> NOTE (2026-06-13): Updated from "S1–S18 across 4 tiers" — Tier 5 (Production Infrastructure, S19–S35) was added 2026-06-11 during the Security Hardening Pass. See `success-criteria.md` L53 onward.

**Read when:** Assessing whether the build is complete, or deciding if a gap is truly a gap.

**Key content:**
- Tier 1 (S1–S5): Non-negotiable — payroll accuracy, compliance automation, country isolation, audit trail
- Tier 2 (S6–S10): Core product — Decision Cards, explainable AI, human-in-loop, WhatsApp
- Tier 3 (S11–S14): Architecture — new country = adapter only, multi-entity, API-first, independent deploy
- Tier 4 (S15–S18): QC gates — pytest 0 failures, QC 11/11, RE-QC all green, intent/build aligned
- Tier 5 (S19–S35): Production Infrastructure — safe serialisation, ASGI server, structured logging, rate limiting, JWT/RBAC, OpenAPI, migrations, CI, TLS, tracing, CORS, metrics, idempotency, JSON validation (added 2026-06-11, Security Hardening Pass)

**Feeds into:** `roadmap.md` (phase gates), `qc-suite.md` (Tier 4 measurement), final certification decision.

**Known partial:** S3 (compliance validates before payroll) — `check_payroll_gate()` exists but G22 full wiring into `payroll_service.py mark_paid()` deferred.

---

### 3. `roadmap.md`
**Purpose:** Defines the 5 sequential build phases, their deliverables, and current completion status.

**Read when:** Resuming a build session to understand what phase work is in and what is next.

**Key content:**
- Phase 1 — Architecture cleanup (foundation) ✅ Complete
- Phase 2 — Pakistan payroll + compliance hardening ✅ Complete (G22 deferred)
- Phase 3 — Decision engine + AI guardian ✅ Complete
- Phase 4 — WhatsApp + mobile expansion ✅ Complete
- Phase 5 — Multi-country rollout ✅ Complete — framework done, DummyAdapter proves architecture

**Feeds into:** `progress.md` (per-gap detail), `success-criteria.md` (phase gates).

**Relationship rule:** Phases are sequential. Phase 2 cannot be hardened without Phase 1. Phase 3 depends on Phase 2 data quality. Phase 4 depends on Phases 2 and 3. Phase 5 is purely additive.

---

### 4. `progress.md`
**Purpose:** Single source of truth for all 86 registered gaps — status, phase, severity, and done/deferred/open state.

> NOTE (2026-06-13): Updated from "83 registered gaps" — `gap-register.md` now has 86 gaps total, all DONE as of 2026-06-10.

**Read when:** Picking up work mid-session, or choosing the next gap to fix.

**Key content:**
- Overall status table (all phases at a glance)
- Per-phase gap tables with G-numbers, severity, title, status
- Key Files Quick Reference (code location ↔ doc location for every major concept)

**Feeds into:** `gap-register.md` (detail), `pending.md` (what is actively blocking certification).

**Rule:** Update this file every time a gap status changes. It is the scoreboard.

---

### 5. `gap-register.md`
**Purpose:** Full detail record for every gap ever registered (G01–G48, plus MR-G, SB-G, MN-G, SPEC-G, S7-G, S8-G, BG, CG, UG series, and normalisation findings). Every gap has type, severity, file, issue, action, dependencies, and final status.

**Read when:** Understanding the full history and rationale behind any specific gap fix.

**Key content:**
- G01–G12: Phase 1 architecture gaps
- G13–G18: Phase 2 Pakistan payroll/compliance gaps
- G19–G22: Phase 3 decision engine gaps
- G23–G25: Phase 4 WhatsApp/mobile gaps
- G26–G27: Phase 5 multi-country gaps
- G28–G29: UI gaps
- G30–G32: Docs-to-code gaps
- G33–G42: Pakistan statutory gaps (Session 3)
- G43–G48: Canon overlay Pass 3 gaps (Session 4)
- MR-G01/G02: Market research overlay (Session 4)
- SB-G01–SB-G05: Behavior spec overlay (Session 5)
- MN-G01–MN-G07: Manus AI research overlay (Session 5)
- SPEC-G01–SPEC-G08: HRMS Spec overlay (Session 6)
- S7-G01–S7-G05: Session 7 final integrity
- S8-G01–S8-G08: Session 8 master docs overlay
- Summary table: counts by phase, P0/P1/P2/P3 breakdown

**Feeds into:** `progress.md` (status summary), `pending.md` (open/deferred items).

**Rule:** Never fix a gap without registering it here first. Never mark DONE without updating both this file and `progress.md`.

---

### 6. `pending.md`
**Purpose:** Active work tracker. Lists everything blocking final certification, everything deferred, and everything still open.

**Read when:** Starting any session — this is the "what do I do next" doc.

**Key content:**
- Blocking items (must close before final alignment pass):
  - Canon Overlay Pass 3 ✅ DONE (G43–G48)
  - Tier 5 QC coverage gaps (test files for session 2/3 services) 🔴 OPEN
  - Full QC suite run 🔴 NOT YET RUN
- UI pages G28a–G28j (all backends ready, 10 pages open)
- Deferred: G22 full wiring (check_payroll_gate into mark_paid)

**Feeds into:** `gap-register.md` (when a pending item becomes a registered gap), `intent_build_alignment.md` (when a pending item is resolved and verified).

**Rule:** Keep this ruthlessly current. If something is done, mark it done here immediately.

---

### 7. `qc-suite.md`
**Purpose:** Standard reference for running the full QC validation suite. Defines all tiers, scripts, commands, pass criteria, and known coverage gaps.

**Read when:** About to run QC, or deciding whether a new file needs a test.

**Key content:**
- Tier 1: pytest (`pytest -q`) — target 0 failures, last verified 403 passed, 9 skipped, 0 failed (2026-06-11). Historical baseline: 281 passed (2026-03-31, pre-session 2).
- Tier 2: `deployment/qc_validate.py` — target 11/11
- Tier 3: RE-QC scripts — master certification (5/5), addon convergence (5/5), data integrity (6/6)
- Tier 4: 12 domain integrity validators — all must exit 0
- Tier 5: Coverage gap register — 15 known gaps in test coverage for session 2/3 code

**Feeds into:** `success-criteria.md` (S15–S17), `intent_build_alignment.md` (verified evidence after clean run).

**Rule:** Run the full suite in order (Tier 1 → 4). Do not update `intent_build_alignment.md` until all tiers pass.

---

### 8. `infrastructure.md`
**Purpose:** Documents the platform-level infrastructure modules that underpin all business services.

**Read when:** Touching resilience, event delivery, background jobs, or chaos testing.

**Key content:**
- `chaos_engine.py` — fault injection (test/staging only, gated by env flag)
- `resilience.py` — circuit breakers, retries, bulkheads, trace IDs
- `outbox_system.py` — at-least-once event delivery (all canonical events dispatched here)
- `background_jobs.py` — cron + deferred job scheduler
- `persistent_store.py` — thin persistence abstraction (get/set/delete/list)
- `supervisor_engine.py` — infrastructure incident supervisor

**Feeds into:** Any service that uses events (must go via outbox), any service making external calls (must use resilience.py wrappers).

**Rule:** No domain service may depend on another domain service's DB. All external calls via resilience.py. All events via outbox_system.py. Chaos engine never active in production.

---

### 9. `intent_build_alignment.md`
**Purpose:** The final certification document. Records verified evidence that intent, build artifacts, runtime handlers, and tests are mutually consistent.

**Read when:** Preparing for a final alignment pass, or understanding what was verified in a previous session.

**Key content:**
- Original V3 alignment (2026-03-31): 281 pytest passed, QC 11/11, RE-QC all green
- Country-layer alignment (2026-04-01)
- WhatsApp integration alignment (2026-04-01)
- Pakistan integration alignment (2026-04-01)
- Session 2 — service layer completion (2026-04-12)
- Session 3 — spec alignment fixes + Pakistan audit (2026-04-12)
- Session 3 follow-up — G33–G42 implemented (2026-04-12)
- Session 4 — Canon Overlay Pass 3, G43–G48 closed (2026-04-12)

**Feeds into:** Nothing downstream — this is the terminal certification record.

**Rule:** Only update this file after a full clean QC suite run with verified evidence. Never update speculatively.

---

## Document Relationships

```
system-purpose.md  ──────────────────────────────────────────────────┐
  (P1–P7 principles)                                                  │
                                                                      ▼
success-criteria.md  ──► roadmap.md  ──► progress.md  ──► gap-register.md
  (S1–S35 gates, 5 tiers) (phases)        (scoreboard)     (full detail)
                                               │
                                               ▼
                                          pending.md
                                       (next actions)
                                               │
                                               ▼
                                         qc-suite.md
                                       (how to verify)
                                               │
                                               ▼
                                  intent_build_alignment.md
                                    (certified evidence)

infrastructure.md  ──► referenced by all services (not build-flow)
catalogue.md       ──► entry point for all sessions (this file)
```

---

---

### 10. `MASTER MARKET RESEARCH.md`
**Purpose:** Single authoritative market intelligence document for AURA HRMS. Merged from Manus AI Pakistan HRMS Report (2024–2026) and ChatGPT HRMS Strategic Research. Supersedes both source documents.

**Read when:** Validating product decisions against market reality, assessing competitive positioning, or understanding Pakistan-specific buyer needs.

**Key content:**
- Global HRMS landscape and limitations
- Pakistan market structure, segmentation, and 70–80% Excel reality
- Regulatory complexity (FBR/EOBI/PESSI/SESSI fragmentation)
- Detailed competitor analysis (PayPeople, Resourceinn, Sidat Hyder, Decibel, WebHR, SAP)
- 7 validated customer pain points
- Regional insights (Karachi/Lahore/Islamabad/Industrial Punjab)
- 7 market gaps (Compliance Autopilot, AI Auditor, Decision-First UX, WhatsApp layer, Trust Infrastructure, etc.)
- Strategic product model (5 layers) and capability benchmark
- Winning in 2026 criteria

**Supersedes:** `archive/Pakistan_HRMS_Market_Research_Report_(2024–2026) MANUS AI.md`, `archive/RMS MARKET RESEARCH--CHAT GPT.md`

**Feeds into:** `MASTER BUILD SPEC.md` (product thesis and principles), `system-purpose.md` (product identity).

---

### 11. `MASTER BUILD SPEC.md`
**Purpose:** The single authoritative product and architecture specification for AURA HRMS. Merged from *Complete Build Spec v1.0* and *HRMS Spec v1.0*. Supersedes both source documents.

**Read when:** Validating any design decision, architecture rule, behavior contract, or acceptance criterion.

**Key content:**
- Product thesis, principles (P1–P7), target users, core problems
- 6-layer architecture (data → domain → country abstraction → services → integrations → experience)
- Country-agnostic rules (R1–R6) and resolution model
- Core capabilities (C01–C09) and add-on capabilities (A01–A07)
- Pakistan country profile with full statutory coverage list
- Behavior contracts: payroll, compliance, attendance, decision, AI, disbursement, WhatsApp
- Security/audit canon, UX system, scalability, roadmap, non-goals
- Acceptance criteria: architecture (AC1–AC10) and Pakistan-ready (PK1–PK8)

**Supersedes:** `archive/COMPLETE HRMS BUILD SPEC.md`, `archive/HRMS SPEC.md` (both archived for reference, this is canonical)

**Feeds into:** All architectural decisions, gap registration, acceptance testing.

---

### 12. `MASTER BEHAVIOR SPEC.md`
**Purpose:** Single authoritative behavior specification for AURA HRMS. Merged from MARKET-VALIDATED BEHAVIOR SPEC v1.0 and HRMS SYSTEM BEHAVIOR SPEC. Covers runtime step flows, market-grounded WHY statements, audit canon, security rules, system defaults, and competitive differentiation behaviors.

**Read when:** Designing new features, validating UX decisions, implementing or reviewing any domain service behavior, or assessing whether a behavior is genuinely needed or speculative.

**Key content:**
- Core behavior philosophy (B1–B6 runtime rules + market grounding)
- Trust-first behaviors (pre-run confidence signal, anomaly report, reproducibility, confidence scores)
- Payroll 5-step runtime flow with guards and rules
- Compliance 4-step runtime flow with full state machine (including MANUAL state)
- Decision object full 15-field schema; AI output canonical format (supporting_signals, not supporting_data)
- WhatsApp, bank/disbursement, error and recovery behaviors — each grounded in market pain
- Audit behavior: what to log, audit record fields (timestamp, actor, action, affected_entities, result)
- Security behavior: RBAC, no plaintext storage, no log-leaking
- System defaults: safe > risky, explicit > implicit, guided > manual
- Market gap closure map (GAP 1–7 → specific system behaviors)
- Competitive differentiation behaviors vs each named Pakistan vendor
- Success signal — what "working" looks like in market terms

**Supersedes:** `archive/MARKET-VALIDATED BEHAVIOR SPEC.md`, `archive/HRMS SYSTEM BEHAVIOR SPEC.md`

**Relationship:** Does NOT replace `MASTER BUILD SPEC.md` (architecture contracts, acceptance criteria, full schema definitions). Extends it with behavior rules, market WHY statements, and runtime step flows.

---

## Session Start Checklist

Use this on every session start, restart, or dropout recovery:

1. Read `pending.md` — what is blocking, what is next
2. Read `progress.md` overall status table — where are we
3. Check `gap-register.md` if picking up a specific gap
4. Check `roadmap.md` if unsure which phase work belongs to
5. Check `success-criteria.md` if validating whether something is truly done
6. Run `qc-suite.md` procedures when ready to certify

---

## Build Protocol Reminders

- **Workspace:** `D:\HRMS\backend\` — never work outside `D:\HRMS\` unless told
- **Gap rule:** Register before fix. Mark DONE in both `gap-register.md` and `progress.md`
- **No scope creep:** Fix the gap surgically. No refactoring beyond what the gap requires
- **Country rule:** No `if country ==` in any service. All country logic via `CountryResolver → adapter`
- **Event rule:** All domain events dispatched via `outbox_system.py`. All registered in `event_contract.py`
- **QC rule:** Full suite must pass before updating `intent_build_alignment.md`
- **Doc rule:** Backend system docs live in `backend/docs/system/`; workspace ops docs (tracker.md, build-progress.md, normalisation-tracker.md, etc.) live in `ops/`
