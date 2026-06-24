# QC Suite — Standard Quality Control Process

Standard process for validating build integrity after every major build or gap closure.
Run this suite in full before updating `docs/system/intent_build_alignment.md`.

---

## Provenance

All scripts in `deployment/` were created as part of the original V3 convergence passes (P28–P51).
They were not written during sessions 2/3. Last verified clean run: **2026-03-31** (281 pytest passed, QC 11/11, RE-QC all green).

> **UPDATE (2026-06-11, Security Hardening Pass):** Most recent full `pytest -q` run: **403 passed, 9 skipped** (0:21:36). The 281-passed figure above is retained as the historical 2026-03-31 baseline; see `docs/system/success-criteria.md` S32–S35 and `docs/system/roadmap.md` Phase 6 for the work that grew the suite.

---

## When to Run

| Trigger | Suite level |
|---|---|
| Gap(s) closed in existing files | Tier 1 + Tier 2 (targeted) |
| New service file added | Tier 1 + Tier 2 (full) + Tier 3 (new script needed) |
| Major build session complete | Full suite — all tiers |
| Before final alignment pass | Full suite — all tiers, must be all green |

---

## Suite Structure

```
Tier 1 — Pytest (unit + integration)
Tier 2 — Primary QC gate (infrastructure)
Tier 3 — RE-QC gates (architecture + certification)
Tier 4 — Domain integrity validators
Tier 5 — Coverage gap register (what is NOT covered)
```

---

## Tier 1 — Pytest Suite

**Command:**
```bash
cd D:\HRMS\backend
pytest -q
```

**Target:** 0 failures. Last verified: 403 passed, 9 skipped (2026-06-11). (Historical baseline 2026-03-31: 281 passed — see Provenance note above.)

**Test files (80+ in `tests/`):**

| File | Covers |
|---|---|
| `test_pakistan_compliance_service.py` | Tax slab formula, report schema, province routing |
| `test_pakistan_integrations.py` | FBR/EOBI/PESSI adapter submissions |
| `test_country_resolver.py` | Resolver registration, adapter resolution |
| `test_country_architecture_validation.py` | P5 — no country imports in services |
| `test_decision_engine.py` | Decision Cards lifecycle |
| `test_payroll_guardian.py` | Anomaly detection methods |
| `test_anomaly_engine.py` | Anomaly scoring |
| `test_hr_copilot.py` | HR Q&A + RBAC |
| `test_governance_service.py` | Human-in-loop gates |
| `test_insight_engine.py` | Insight generation |
| `test_whatsapp_webhook.py` | Webhook commands + intent parsing |
| `test_mobile_gateway.py` | Mobile contracts, decision-first, low-bandwidth |
| `test_experience_layer_service.py` | Tier gating, PaaS mode, EWA |
| `test_payroll_country_adapter_integration.py` | Payroll → country adapter integration |
| `test_payroll_api.py` | Payroll HTTP endpoints |
| `test_leave_service.py` | Leave lifecycle |
| `test_hiring_service.py` | Hiring workflow |
| `test_auth_service.py` | Auth, RBAC, tenant isolation |
| `test_audit_service.py` | Audit trail |
| `test_attendance_service.py` | Attendance capture |
| `test_background_jobs.py` | Job scheduler |
| `test_outbox_system.py` | At-least-once delivery |
| `test_chaos_engine.py` | Fault injection |
| `test_supervisor_engine.py` | Infrastructure supervision |
| `test_gateway_runtime_alignment_e2e.py` | End-to-end gateway routing |
| `test_data_integrity.py` | Cross-service entity integrity |
| `test_security_compliance_lock.py` | Security model enforcement |
| `test_security_logging.py` | Sensitive field redaction |

**⚠️ Session 2/3 gaps in test coverage (no test files exist for):**
- `compliance_api.py` — no test
- `bank_service.py` + `banking_api.py` — no test
- `decision_api.py` — no test
- `whatsapp_service.py` + `whatsapp_api.py` — no test
- `integrations/pakistan/atl_adapter.py` — no test
- G33–G42 new methods (`calculate_eobi`, `calculate_social_security`, `calculate_wppf`, `calculate_wwf`, non-filer surcharge, exemptions) — not yet in `test_pakistan_compliance_service.py`
- `country/pakistan/payroll_rules.py` statutory_violations — not yet tested

**⚠️ Session 5 gaps in test coverage (SB-G01–SB-G05):**
- `services/analytics/predictive.py` — `explanation` and `supporting_signals` fields — add assertions to existing analytics tests
- `attendance_service/service.py` — `detect_missing_punches()` — add test cases to `test_attendance_service.py`
- `error_registry.py` — `get_error_descriptor()`, `register_error()`, `update_error()` — write `tests/test_error_registry.py`
- `services/ai/payroll_guardian.py` — configurable thresholds via `__init__` — add threshold-override test cases to `test_payroll_guardian.py`
- `integrations/whatsapp/webhook.py` — `CommandRegistry` class + `register_command()` — add registry extension test cases to `test_whatsapp_webhook.py`

---

## Tier 2 — Primary QC Gate

**Script:** `deployment/qc_validate.py`
**Command:**
```bash
python deployment/qc_validate.py
```
**Target:** `QC score: 11/11`

| # | Check | Files inspected |
|---|---|---|
| 1 | Service containers in compose | `docker-compose.yml` |
| 2 | Environment variables defined | `.env.example` |
| 3 | API gateway connectivity | `docker-compose.yml` |
| 4 | Database connectivity | `docker-compose.yml` |
| 5 | Migrations wired | `docker-compose.yml` |
| 6 | Health checks (≥9) | `docker-compose.yml` |
| 7 | Tests run before build in CI | `.github/workflows/build.yml` |
| 8 | All 3 Dockerfiles in CI build | `.github/workflows/build.yml` |
| 9 | Schema matches data architecture | `deployment/migrations/001_core_schema.sql`, `002_workflow_schema.sql` |
| 10 | Multi-tenant `tenant_id` on all tables | `deployment/migrations/` |
| 11 | No committed secrets | `.env.example`, `docker-compose.yml` |

**Coverage scope:** Infrastructure and deployment configuration only. Does not validate business logic.

---

## Tier 3 — RE-QC Gates

### 3a. Master Certification
**Script:** `deployment/re_qc_validate_master_certification.py`
**Command:**
```bash
python deployment/re_qc_validate_master_certification.py
```
**Target:** `RE-QC master-certification score: 5/5`

| # | Check | Files inspected |
|---|---|---|
| 1 | QC categories cover all 5 integrity dimensions | `master_certification.py` |
| 2 | 7 auto-fix actions map to P51 repair requirements | `master_certification.py` |
| 3 | Loop enforces fail-below-10/10 | `master_certification.py` |
| 4 | Tests lock 10/10 convergence behaviour | `tests/test_master_certification.py` |
| 5 | Report captures P51 objective and constraints | `docs/design/addon-certification-pass-p51.md` |

### 3b. Add-on Convergence
**Script:** `deployment/re_qc_validate_addon_convergence.py`
**Command:**
```bash
python deployment/re_qc_validate_addon_convergence.py
```
**Target:** `RE-QC addon-convergence score: 5/5`

| # | Check | Files inspected |
|---|---|---|
| 1 | 7 QC dimensions enforced | `addon_convergence.py` |
| 2 | 7 auto-fix actions map to P50 repair paths | `addon_convergence.py` |
| 3 | Loop enforces fail-below-10/10 | `addon_convergence.py` |
| 4 | Tests lock convergence behaviour | `tests/test_addon_convergence.py` |
| 5 | Report captures P50 objective | `docs/design/addon-convergence-report-p50.md` |

### 3c. Data Integrity
**Script:** `deployment/re_qc_validate_data_integrity.py`
**Command:**
```bash
python deployment/re_qc_validate_data_integrity.py
```
**Target:** `RE-QC data-integrity score: 6/6`

| # | Check | Files inspected |
|---|---|---|
| 1 | Entity integrity (leave balance, candidate handoff, payroll totals) | `data_integrity.py` |
| 2 | Projection integrity + tenant normalisation | `data_integrity.py` |
| 3 | Audit/event alignment (hire, payroll, leave events) | `data_integrity.py` |
| 4 | Repair script has `--auto-fix` and uses `AuditService` | `deployment/repair_data_integrity.py` |
| 5 | Tests lock runtime integrity behaviour | `tests/test_data_integrity.py` |
| 6 | Report documents scope and repairs | `docs/design/data-integrity-report-p29.md` |

---

## Tier 4 — Domain Integrity Validators

Run all of these. Each must exit 0.

```bash
python deployment/re_qc_validate_security_compliance_lock.py
python deployment/re_qc_validate_audit_service.py
python deployment/re_qc_validate_employee_domain_integrity.py
python deployment/re_qc_validate_candidate_domain_integrity.py
python deployment/re_qc_validate_engagement_domain_integrity.py
python deployment/re_qc_validate_performance_domain_integrity.py
python deployment/re_qc_validate_role_integrity.py
python deployment/re_qc_validate_settings_domain_integrity.py
python deployment/qc_validate_engagement.py
python deployment/qc_validate_performance.py
python deployment/qc_validate_role_mapping.py
python deployment/qc_validate_settings.py
```

### Security + Compliance Lock (12 checks)
**Script:** `re_qc_validate_security_compliance_lock.py`

| # | Check | Files inspected |
|---|---|---|
| 1 | Tenant foundation schema | `migrations/005_tenant_foundation.sql` |
| 2 | Tenant access helper blocks cross-tenant access | `tenant_support.py` |
| 3 | Tenant isolation enforced across critical services | `leave_service.py`, `hiring_service`, `integration_service.py`, `notification_service.py`, `search_service.py` |
| 4 | Cross-tenant repository filters rejected server-side | `services/employee-service/role.repository.ts`, `department.repository.ts` |
| 5 | Audit store append-only + tenant-scoped | `migrations/009_audit_service.sql` |
| 6 | Audit query requires tenant filtering | `audit_service/service.py` |
| 7 | Privileged domains emit audit records (≥4–6 per service) | `leave_service.py`, `hiring_service`, `payroll_service.py`, `auth-service` |
| 8 | Security model deny-by-default | `docs/canon/security-model.md` |
| 9 | Auth service capability matrix complete | `services/auth-service/service.py` |
| 10 | RBAC middleware denies (≥4 deny paths) | `services/employee-service/rbac.middleware.ts` |
| 11 | Sensitive fields redacted in logs | `resilience.py`, `auth-service/service.py` |
| 12 | Tests cover tenant boundaries, audit, redaction | `tests/test_auth_service.py`, `test_leave_service.py`, `test_notification_service.py`, `test_integration_service.py`, `test_security_logging.py`, `test_audit_service.py` |

### Audit Service (9 checks)
**Script:** `re_qc_validate_audit_service.py`

Validates audit schema D4 fields, append-only SQL triggers, and that attendance/leave/payroll/hiring/auth all emit audit records (minimum counts enforced).

---

## Tier 5 — Coverage Gap Register

> **NOTE (naming collision):** This "Tier 5" is a QC-suite-local tier numbering (Tiers 1–5 = pytest → primary QC → RE-QC → domain validators → coverage gap register) and is **unrelated** to `docs/system/success-criteria.md`'s "Tier 5 — Production Infrastructure" (S19–S35), which uses an independent tier numbering for product success criteria. The two "Tier 5"s are different documents' internal section numbering and do not refer to the same content — see [[feedback_normalisation_scope]] cross-file findings log.

**Known gaps in the existing QC suite as of 2026-04-13 (sessions 2/3 + sessions 5/6).**
These services/methods are not yet covered by any QC script or test.

> **STALENESS FLAG (2026-06-13):** A spot-check found that several items in this table (e.g. `compliance_api.py`, `bank_service.py`/`banking_api.py`, `decision_api.py`, `whatsapp_service.py`, `error_registry.py`, `country/pakistan/statutory.py` MN-G01–MN-G03, `services/decision_engine.py` SPEC-G01, `leave_service.py`/`payroll_service.py` SPEC-G06) still have **no matching test file or assertion** in `backend/tests/`, even though `docs/system/gap-register.md` marks the corresponding gaps (G33–G42, SB-G01–SB-G05, MN-G01–MN-G06, SPEC-G01–SPEC-G07) as DONE. This table has not been re-validated against the current test suite (403 passed, 9 skipped as of 2026-06-11) and is likely substantially stale. Logged as a new gap in `docs/system/gap-register.md` (see Full-Workspace Normalisation Pass section) — not fixed here, as closing it means writing ~20-30 new test cases, a separate scoped effort.

| Service / File | Gap type | Action needed |
|---|---|---|
| `compliance_api.py` | No test, no QC check | Write `tests/test_compliance_api.py` |
| `services/compliance_service.py` | No QC check | Add to new compliance QC script |
| `bank_service.py` + `banking_api.py` | No test, no QC check | Write `tests/test_bank_service.py` |
| `decision_api.py` | No test, no QC check | Write `tests/test_decision_api.py` |
| `whatsapp_service.py` + `whatsapp_api.py` | No test | Write `tests/test_whatsapp_service.py` |
| `integrations/pakistan/atl_adapter.py` | No test | Write `tests/test_atl_adapter.py` |
| G33 — non-filer surcharge | Not in `test_pakistan_compliance_service.py` | Add test cases |
| G35 — exempt allowances | Not in `test_pakistan_compliance_service.py` | Add test cases |
| G36 — `calculate_eobi()` | Not tested | Add test cases |
| G37 — `calculate_social_security()` | Not tested | Add test cases |
| G38 — `calculate_wppf()` | Not tested | Add test cases |
| G39 — `calculate_wwf()` | Not tested | Add test cases |
| G40 — `statutory_violations` in payroll_rules | Not tested | Add test cases |
| G41 — `update_tax_slabs()` | Not tested | Add test cases |
| WhatsApp attendance command (webhook.py) | `test_whatsapp_webhook.py` only tests 3 commands | Add attendance test case |
| `services/analytics/predictive.py` SB-G01 | `explanation` + `supporting_signals` not asserted | Add assertions to analytics test |
| `attendance_service/service.py` SB-G02 | `detect_missing_punches()` not tested | Add to `test_attendance_service.py` |
| `error_registry.py` SB-G03 | No test file | Write `tests/test_error_registry.py` |
| `services/ai/payroll_guardian.py` SB-G04 | Threshold overrides not tested | Add to `test_payroll_guardian.py` |
| `integrations/whatsapp/webhook.py` SB-G05 | `CommandRegistry.register_command()` not tested | Add to `test_whatsapp_webhook.py` |
| `country/pakistan/statutory.py` MN-G01 | `calculate_gratuity()`, `calculate_provident_fund()`, `update_provident_fund_rates()` not tested | Add to `test_pakistan_compliance_service.py` |
| `country/pakistan/statutory.py` MN-G02 | `bonus_income` param in `calculate_tax()` not tested | Add to `test_pakistan_compliance_service.py` |
| `country/pakistan/statutory.py` MN-G03 | `calculate_arrears_tax()` not tested | Add to `test_pakistan_compliance_service.py` |
| `attendance_service/models.py` MN-G04 | `GEO_FENCE`/`FACE_RECOGNITION`/`MOBILE` sources + `location_metadata` not tested | Add to `test_attendance_service.py` |
| `integrations/pakistan/pessi_adapter.py` MN-G05 | C-1 format label in submission result not asserted | Add to `test_pakistan_integrations.py` |
| `services/compliance_service.py` MN-G06 | `get_compliance_readiness_card()` not tested | Add to new `tests/test_compliance_api.py` |
| `decision_api.py` MN-G06 | `get_compliance_readiness()` endpoint not tested | Add to `tests/test_decision_api.py` |
| `services/decision_engine.py` SPEC-G01 | `DecisionSeverity` enum, `source_domain`, `severity`, `resolved_at`, `actor`, `resolve_card()` not asserted | Add to `test_decision_engine.py` |
| `services/analytics/predictive.py` SPEC-G02 | `supporting_signals` rename + `suggested_action` not asserted | Update analytics test assertions |
| `services/ai/payroll_guardian.py` SPEC-G02 | `suggested_action` in all 4 detect methods not tested | Add to `test_payroll_guardian.py` |
| `services/compliance_service.py` SPEC-G03 | `ComplianceErrorType`, `classify_compliance_error()`, enriched violations, typed `mark_failed()` not tested | Add to new `tests/test_compliance_api.py` |
| `bank_service.py` SPEC-G04 | `SENT`/`ACCEPTED`/`REJECTED` states + `mark_sent()`/`mark_accepted()`/`mark_rejected()` not tested | Add to `tests/test_bank_service.py` |
| `country/base/statutory_validator.py` SPEC-G05 | `StatutoryValidatorInterface` not tested | Add interface contract test to `tests/test_country_architecture_validation.py` |
| `leave_service.py` SPEC-G06 | `get_unpaid_leave_days()` not tested | Add to `tests/test_leave_service.py` |
| `payroll_service.py` SPEC-G06 | `leave_service` injection + `unpaid_leave_deduction` not tested | Add integration test to `tests/test_payroll_api.py` |
| `services/compliance_service.py` SPEC-G07 | `MANUAL` state + `record_manual_submission()` not tested | Add to new `tests/test_compliance_api.py` |

**These gaps must be closed before the final alignment pass can be declared complete.**

---

## Full Suite Execution Order

```bash
# 1. Pytest
pytest -q

# 2. Primary QC
python deployment/qc_validate.py

# 3. RE-QC gates
python deployment/re_qc_validate_master_certification.py
python deployment/re_qc_validate_addon_convergence.py
python deployment/re_qc_validate_data_integrity.py

# 4. Domain integrity
python deployment/re_qc_validate_security_compliance_lock.py
python deployment/re_qc_validate_audit_service.py
python deployment/re_qc_validate_employee_domain_integrity.py
python deployment/re_qc_validate_candidate_domain_integrity.py
python deployment/re_qc_validate_engagement_domain_integrity.py
python deployment/re_qc_validate_performance_domain_integrity.py
python deployment/re_qc_validate_role_integrity.py
python deployment/re_qc_validate_settings_domain_integrity.py
python deployment/qc_validate_engagement.py
python deployment/qc_validate_performance.py
python deployment/qc_validate_role_mapping.py
python deployment/qc_validate_settings.py
```

---

## Pass Criteria

All of the following must be true before updating `intent_build_alignment.md`:

| Gate | Target |
|---|---|
| `pytest -q` | 0 failures |
| `qc_validate.py` | 11/11 |
| `re_qc_validate_master_certification.py` | 5/5 |
| `re_qc_validate_addon_convergence.py` | 5/5 |
| `re_qc_validate_data_integrity.py` | 6/6 |
| All domain integrity validators | Exit 0 |
| Tier 5 coverage gaps | All closed (tests written) |

---

## After Full Pass

1. Update `docs/system/intent_build_alignment.md` with session entry and verified evidence
2. Update `docs/system/progress.md` overall status
3. Update `docs/system/gap-register.md` if any new gaps found during QC run
4. Close relevant items in `pending.md`
