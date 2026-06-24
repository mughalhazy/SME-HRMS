# Pending — Active Work Tracker
## AURA HRMS — What Is Blocking, Deferred, and Open

> **Read this on every session start.** This is the "what do I do next" doc.
> Keep it ruthlessly current. Mark things done the moment they are done.

*Last updated: 2026-04-14 (Session 8)*

> NOTE (2026-06-13): This file's "Last updated" date (2026-04-14, Session 8) and the "Blocking Certification" table below (esp. "Full QC suite run NOT RUN since Session 4") are stale relative to `progress.md` (last updated 2026-06-10) and `gap-register.md` (86 gaps, all DONE as of 2026-06-10), which record multiple clean QC runs through 2026-06-11 ("403 passed, 9 skipped, 0 failed"). Per the divergence-resolution policy this is logged as an annotation rather than rewritten — treat `progress.md`/`gap-register.md` as canonical for current status; the only items still genuinely open/blocking per those files are the G28a–G28j UI pages.

---

## Blocking Certification

These must be resolved before `intent_build_alignment.md` can be updated.

| Item | Status | Notes |
|---|---|---|
| Full QC suite run (pytest + QC 11/11 + RE-QC) | 🔴 NOT RUN | No clean run since Session 4. New code from Sessions 5–7 needs verification. |
| 10 UI pages (G28a–G28j) | 🔴 OPEN | All backends ready. Pages are the only remaining frontend deliverable. |
| G22 — check_payroll_gate() not wired into mark_paid() | 🟡 DEFERRED | Gate function exists in decision_api.py; mark_paid() does not call it. Partial only. |

---

## UI Pages — All Open (G28a–G28j)

Backends are implemented and tested. Pages are not built.

| Gap | Page | Backend |
|---|---|---|
| G28a | `ui/app/compliance/page.tsx` | `compliance_api.py` ✅ |
| G28b | `ui/app/decisions/page.tsx` | `decision_api.py` ✅ |
| G28c | `ui/app/financial-wellness/page.tsx` | `services/finance/ewa.py` ✅ |
| G28d | `ui/app/banking/page.tsx` | `banking_api.py` ✅ |
| G28e | `ui/app/analytics/page.tsx` | `reporting_analytics_api.py` ✅ |
| G28f | `ui/app/helpdesk/page.tsx` | `helpdesk_api.py` ✅ |
| G28g | `ui/app/automations/page.tsx` | `automation_api.py` ✅ |
| G28h | `ui/app/engagement/page.tsx` | `engagement_api.py` ✅ |
| G28i | `ui/app/whatsapp-admin/page.tsx` | `whatsapp_api.py` ✅ |
| G28j | `ui/app/expenses/page.tsx` | `expense_api.py` ✅ |

---

## Deferred — Intentional, Not Forgotten

| Item | Gap | Why Deferred |
|---|---|---|
| Export sector / International Labor Standards | MN-G07 | Low priority — not a Pakistan core requirement; export sector is a future vertical |

---

## Session 8 Gap Analysis — New Items Identified

From overlay of 3 master docs against repo. Full detail in session 8 gap analysis report.

| Item | Severity | Description |
|---|---|---|
| Pre-run confidence signal missing from payroll_service.py | P1 | PayrollGuardian exists in services/ai/ but not called as mandatory pre-run gate; no "safe to run / issues require review" surface |
| travel-service and project-service marked PLANNED in BUILD SPEC but code exists | P2 | travel_service.py, project_service.py, travel_api.py, project_api.py all exist — BUILD SPEC §10 service registry is out of date |
| Shift templates / rosters in BUILD SPEC C05 not implemented | P2 | BUILD SPEC §06 C05 lists shift templates and rosters as core. attendance_service.py has shift_rules but no roster management |
| Manager dashboard UI not decision-first per BEHAVIOR SPEC | P2 | manager_dashboard.py (G29 DONE) but no decisions/page.tsx (G28b open) — manager has no decision-first web UI |
| Bank service audit trail missing | P2 | payroll_service has audit trail; bank_service.py has no audit logging on disbursement state transitions |

---

## Done This Session (Session 8)

| Item | Status |
|---|---|
| pending.md recreated | ✅ DONE |
| MASTER BEHAVIOR SPEC.md created (merge of 2 behavior docs) | ✅ DONE |
| Gap analysis against 3 master docs conducted | ✅ DONE |
| S8-G01/02/03 — PayrollGuardian wired into run_payroll() with confidence signal | ✅ DONE |
| S8-G04 — Service registry corrected (travel + project marked IMPLEMENTED) | ✅ DONE |
| S8-G05 — Shift templates/roster deferred note added to BUILD SPEC C05 | ✅ DONE |
| S8-G06 — expire_overdue_decisions() added to decision_api.py + registered as background job | ✅ DONE |
| S8-G07 — decisions/page.tsx | DEFERRED — UI pages not yet in scope |
| S8-G08 — Audit logging added to bank_service.py all state transitions | ✅ DONE |

---

## Completed in Prior Sessions (for reference)

| Session | Key Completions |
|---|---|
| S1–S4 | G01–G48: architecture, Pakistan payroll, decision engine, WhatsApp, multi-country framework, canon overlay |
| S5 | MN-G01–G06, SB-G01–G05: market research overlay, behavior spec overlay |
| S6 | SPEC-G01–G08: HRMS spec overlay — full decision schema, AI output fields, disbursement states, compliance states, manual fallback |
| S7 | S7-G01–G05: bank_service country-agnostic, DummyAdapter, docker-compose, e2e tests, import health; doc merges (3 master docs created) |
