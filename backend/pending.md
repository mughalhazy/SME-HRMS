# Pending Work

> **⚠️ SUPERSEDED — This is the repo-root pending.md reflecting Sessions 5–7 state. The authoritative current pending tracker is `docs/system/pending.md` (last updated Session 8, 2026-04-14). Read that file for current blocking items, deferred items, and open UI pages. This file is preserved for historical reference only.**

> **New session?** Read `docs/system/catalogue.md` first — it is the entry point for all system docs and contains the session start checklist.

## Session 7 — Final Integrity 🔴 IN PROGRESS

| Gap | What | Status |
|---|---|---|
| S7-G01 | Fix bank service — remove direct Pakistan imports | DONE |
| S7-G02 | Create dummy country adapter to prove architecture | DONE |
| S7-G03 | Update docker-compose + service map + release scope doc | DONE |
| S7-G04 | Write end-to-end test — happy path and blocked path | DONE |
| S7-G05 | Write import health test and smoke script | DONE |

---

## HRMS Spec Overlay ✅ ALL DONE (Session 6)

| Gap | Fixed |
|---|---|
| SPEC-G01 — DecisionCard spec §15 fields | `services/decision_engine.py` — `DecisionSeverity` enum, `source_domain`, `severity`, `resolved_at`, `actor` fields + `resolve_card()` method |
| SPEC-G02 — AI mandatory output fields | `services/analytics/predictive.py` — `supporting_data` → `supporting_signals`, `suggested_action` added to all 3 models; `services/ai/payroll_guardian.py` — `suggested_action` added to all 4 detect methods |
| SPEC-G03 — Compliance error type classification | `services/compliance_service.py` — `ComplianceErrorType` enum, `classify_compliance_error()`, violations enriched with `error_type`, `mark_failed()` typed |
| SPEC-G04 — DisbursementState SENT/ACCEPTED/REJECTED | `bank_service.py` — 3 new states + `mark_sent()`, `mark_accepted()`, `mark_rejected()` lifecycle methods |
| SPEC-G05 — StatutoryValidatorInterface | `country/base/statutory_validator.py` created + registered in `__init__.py` |
| SPEC-G06 — Leave → payroll effect | `leave_service.py` — `get_unpaid_leave_days()`; `payroll_service.py` — `leave_service` injection + `unpaid_leave_deduction` in `_build_record_from_payload()` |
| SPEC-G07 — Manual compliance fallback | `services/compliance_service.py` — `MANUAL` state, `manual_mode`/`manual_reference` on submission, `record_manual_submission()` |
| SPEC-G08 — Service manifest | `docs/system/service-manifest.md` created (7 core + 6 support + 12 add-on services enumerated) |

---

## Pakistan Statutory Gaps ✅ ALL DONE

| # | Gap | Severity | File |
|---|---|---|---|
| G33 | Filer/non-filer surcharge — Finance Act 2023/2024: non-filers pay 100% additional salary tax | P0 | `country/pakistan/statutory.py` |
| G34 | Tax slabs identical for 2024/2025/2026 — no update path | P0 | `country/pakistan/statutory.py` |
| G35 | Exempt allowances not applied before tax calculation | P0 | `country/pakistan/statutory.py` |
| G36 | EOBI contribution amounts not calculated | P1 | `country/pakistan/statutory.py` |
| G37 | PESSI/SESSI contribution math missing | P1 | `country/pakistan/statutory.py` |
| G38 | WPPF not implemented | P1 | `country/pakistan/statutory.py` |
| G39 | WWF not implemented | P1 | `country/pakistan/statutory.py` |
| G40 | payroll_rules.py generic — no Pakistan-specific rules | P2 | `country/pakistan/payroll_rules.py` |
| G41 | No slab update mechanism | P2 | `country/pakistan/statutory.py` |
| G42 | ATL/FBR filer verification missing | P2 | `integrations/pakistan/atl_adapter.py` (new) |

## UI Pages (G28 — all backends ready)

| Page | Backend |
|---|---|
| `/app/compliance/page.tsx` | `compliance_api.py` |
| `/app/decisions/page.tsx` | `decision_api.py` |
| `/app/financial-wellness/page.tsx` | `services/finance/ewa.py` |
| `/app/banking/page.tsx` | `banking_api.py` |
| `/app/analytics/page.tsx` | `reporting_analytics_api.py` |
| `/app/helpdesk/page.tsx` | `helpdesk_api.py` |
| `/app/automations/page.tsx` | `automation_api.py` |
| `/app/engagement/page.tsx` | `engagement_api.py` |
| `/app/whatsapp-admin/page.tsx` | `whatsapp_api.py` |
| `/app/expenses/page.tsx` | `expense_api.py` |

## Manus AI Market Research Overlay ✅ ALL DONE (Session 5)

| Gap | Fixed |
|---|---|
| MN-G01 — Gratuity + PF in statutory adapter | `country/pakistan/statutory.py` — `calculate_gratuity()`, `calculate_provident_fund()`, `update_provident_fund_rates()`, `_PF_DEFAULTS` |
| MN-G02 — Bonus taxation | `country/pakistan/statutory.py` — `bonus_income` param added to `calculate_tax()` |
| MN-G03 — Arrears taxation | `country/pakistan/statutory.py` — `calculate_arrears_tax()` added |
| MN-G04 — Geo-fencing attendance source + location metadata | `attendance_service/models.py` — `GEO_FENCE`, `FACE_RECOGNITION`, `MOBILE` + `location_metadata` field |
| MN-G05 — PESSI C-1 form naming | `integrations/pakistan/pessi_adapter.py` — all "contribution_return" → "C-1" |
| MN-G06 — Compliance readiness Decision Card | `services/compliance_service.py` + `decision_api.py` — `get_compliance_readiness_card()` + endpoint |
| MN-G07 — Export sector compliance | DEFERRED — needs SA8000/WRAP/BSCI domain research |

---

## Behavior Spec Overlay ✅ ALL DONE (Session 5)

| Gap | Fixed |
|---|---|
| SB-G01 — AI output contract: explanation + supporting_data | `services/analytics/predictive.py` — all 3 models updated |
| SB-G02 — Attendance punch_status + detect_missing_punches() | `attendance_service/service.py` — field + method added |
| SB-G03 — Central error registry | `error_registry.py` created (22 codes, get/register/update API) |
| SB-G04 — Configurable payroll guardian thresholds | `services/ai/payroll_guardian.py` — __init__ + _DEFAULT_THRESHOLDS |
| SB-G05 — WhatsApp command registry | `integrations/whatsapp/webhook.py` — CommandRegistry class |

---

## Blocking — Must Close Before Final Certification

### 1. Canon Overlay Pass 3 — 5 unread canon docs ✅ DONE
All 5 docs read. 6 gaps found (G43–G48) and closed in one pass (Session 4).

| Gap | Fixed |
|---|---|
| G43 — 7 travel events | `event_contract.py` updated |
| G44 — 8 comp/benefits events | `event_contract.py` updated |
| G45 — 2 auth/engagement events | `event_contract.py` updated |
| G46 — 4 settings events | `event_contract.py` updated |
| G47 — comp/salary/benefits/allowance schema | `012_compensation_domain.sql` created |
| G48 — travel schema | `013_travel_domain.sql` created |

---

### 2. Tier 5 QC Coverage Gaps — Missing Test Files
Session 2/3 services have no test coverage. Must be written before QC suite can pass Tier 5.

| File needed | Covers |
|---|---|
| `tests/test_compliance_api.py` | compliance_api.py 9 endpoints |
| `tests/test_bank_service.py` | bank_service.py + banking_api.py |
| `tests/test_decision_api.py` | decision_api.py 7 endpoints + copilot |
| `tests/test_whatsapp_service.py` | whatsapp_service.py + whatsapp_api.py |
| `tests/test_atl_adapter.py` | integrations/pakistan/atl_adapter.py |
| Add to `test_pakistan_compliance_service.py` | G33 non-filer surcharge, G35 exemptions, G36 EOBI, G37 PESSI/SESSI, G38 WPPF, G39 WWF, G41 update_tax_slabs |
| Add to `test_whatsapp_webhook.py` | attendance command (4th command — currently only 3 tested) |
| Add to `test_pakistan_compliance_service.py` | G40 statutory_violations in payroll_rules |

---

### 3. Stale Doc — gap-register.md Summary Table
Summary row still shows: `Pakistan Statutory (Session 3) | 🔴 G33–G42 all OPEN`
Should read: `✅ All DONE`

**Action:** Update summary table row in `docs/system/gap-register.md`.

---

### 4. Stale Doc — intent_build_alignment.md Session 3 Entry
Session 3 entry shows G33–G42 as "OPEN (registered)". They have all been fixed.

**Action:** Add a Session 3 follow-up note confirming G33–G42 implemented. Evidence: code changes in `country/pakistan/statutory.py`, `country/pakistan/payroll_rules.py`, `integrations/pakistan/atl_adapter.py`.

---

### 5. Full QC Suite Run
No QC run has been executed since sessions 2/3 work. Last verified clean run was 2026-03-31 (pre-session 2).

**Action:** Run full suite in order:
```
pytest -q
python deployment/qc_validate.py
python deployment/re_qc_validate_master_certification.py
python deployment/re_qc_validate_addon_convergence.py
python deployment/re_qc_validate_data_integrity.py
# + all Tier 4 domain validators
```
**Target:** 0 failures, 11/11, 5/5, 5/5, 6/6, all domain validators exit 0.

---

## Deferred (must resolve before final alignment pass)

| Item | Gap | Reason | Blocks |
|---|---|---|---|
| G22 full wiring — `check_payroll_gate()` into `payroll_service.py mark_paid()` | G22 | Needs integration test coverage first | S3 success criterion (compliance gates payroll) |
| UAE statutory adapter — `country/uae/` | G27 | Needs WPS/MOHRE/DEWS statutory knowledge | Out of scope for current certification pass |
