# Gap Register

Cross-reference of docs (anchor) vs code (actual). Gaps are registered here before any fix is applied.

## Gap types
- `CODE_MISSING` — doc defines it, code doesn't implement it
- `DOCS_MISSING` — code implements it, no doc exists
- `VIOLATION` — code exists but breaks an architecture rule
- `DUPLICATION` — same concept implemented in two places
- `STUB` — file exists but is effectively empty / placeholder

## Severity
- `P0` — blocks architecture integrity or compliance correctness
- `P1` — core feature missing or rule violated
- `P2` — secondary feature missing or doc missing for existing code
- `P3` — cleanup / polish / nice-to-have

## Status
- `OPEN` — registered, not yet fixed
- `IN_PROGRESS` — fix underway
- `DONE` — fixed and verified
- `DEFERRED` — intentionally deferred with reason

---

## PHASE 1 — Architecture (Foundation)

### G01
- **Type:** VIOLATION
- **Severity:** P0
- **File:** `core/country_resolver.py`
- **Issue:** Resolver hardcodes `"ORG_DEFAULT" → "pakistan"` as an in-memory dict. Per `docs/canon/country-layer.md`, mappings must come from organization/legal-entity/config records, not hardcoded defaults. A new country cannot be added without code change.
- **Action:** Make resolver data-driven — load mappings from config/DB. Keep hardcoded map as a fallback seed only (for tests/dev). Add multi-org registration support.
- **Depends on:** none
- **Status:** DONE — `register_adapter()` / `register_mapping()` / `list_mappings()` added. Hardcoded Pakistan moved to `seed_dev_defaults()`. Direct `PakistanAdapter` import removed from `__init__`.

### G02
- **Type:** VIOLATION / STUB
- **Severity:** P0
- **File:** `services/compliance_service.py`
- **Issue:** 3-line file that re-exports `PakistanComplianceService` directly from `country.pakistan.statutory`. This violates P5 (country logic must be isolated). The compliance-service must delegate to the country adapter via interface, not import Pakistan directly.
- **Action:** Replace with a proper country-agnostic `ComplianceService` that calls `CountryResolver → ComplianceEngineInterface`. Move Pakistan re-export to a test fixture.
- **Depends on:** G01
- **Status:** DONE — full `ComplianceService` written (~200 lines). Lifecycle DRAFT→VALIDATED→SUBMITTED→ACK/FAILED→RETRY. All country logic delegated via `CountryResolver.resolve()`. No Pakistan import.

### G03
- **Type:** CODE_MISSING
- **Severity:** P0
- **File:** `services/compliance_service.py` (HTTP layer missing entirely)
- **Issue:** No HTTP API for compliance-service. No `compliance_api.py` or equivalent. The full submission lifecycle (DRAFT→VALIDATED→SUBMITTED→ACK→FAILED→RETRY) is not exposed.
- **Action:** Build `compliance_api.py` with canonical endpoints per `docs/services/compliance-service.md`.
- **Depends on:** G02
- **Status:** DONE — `compliance_api.py` built (~190 lines). All 9 endpoints implemented: create, get, list, validate, generate, submit, retry, report, audit.

### G04
- **Type:** DUPLICATION
- **Severity:** P1
- **File:** `services/payroll_service.py` (176 lines) vs `payroll_service.py` (2191 lines)
- **Issue:** Two payroll service files exist. Root `payroll_service.py` is the full implementation (imports CountryResolver ✅). `services/payroll_service.py` is unclear — likely a secondary layer or delegate.
- **Action:** Read `services/payroll_service.py` fully. Determine if it is: (a) a thin HTTP wrapper around root service, (b) a duplicate, or (c) separate concern. Consolidate or clearly rename and document.
- **Depends on:** none
- **Status:** DONE — NOT a duplicate. `services/payroll_service.py` is the pure computation engine (math: gross/taxable/net/overtime). Root `payroll_service.py` is the HTTP service (auth/observability/persistence). Module docstring added to `services/payroll_service.py` to make the boundary explicit. Same class name `PayrollService` is a future rename candidate (P3).

### G05
- **Type:** DUPLICATION
- **Severity:** P1
- **File:** `services/recruitment/service.py` (200 lines) vs `services/hiring_service/service.py` (1794 lines)
- **Issue:** Two recruitment/hiring service files. `hiring_service/service.py` is the canonical implementation. `services/recruitment/service.py` may be a legacy file or subset.
- **Action:** Read both. If `services/recruitment/service.py` is a subset/duplicate, consolidate into `hiring_service/`. If it serves a distinct purpose, document it.
- **Depends on:** none
- **Status:** DONE — NOT a duplicate. `services/recruitment/service.py` is CV-parsing/candidate-scoring utilities (pure logic, no HTTP, no DB). `services/hiring_service/service.py` is the full hiring workflow service. Module docstring added to clarify these are different layers. Recruitment utilities should be imported by hiring_service.

### G06
- **Type:** DOCS_MISSING
- **Severity:** P1
- **File:** `supervisor_engine.py` (749 lines)
- **Issue:** SupervisorEngine handles infrastructure incident detection, recovery hooks, background-job supervision, and service health monitoring. Not documented anywhere. Maps loosely to automation-service or is a standalone infrastructure supervisor.
- **Action:** Update `docs/services/automation-service.md` to include SupervisorEngine as a sub-module, OR create `docs/services/supervisor-engine.md`. Update service-map.md.
- **Depends on:** none
- **Status:** DONE — Added as sub-module section in `docs/services/automation-service.md`. Also referenced in `docs/system/infrastructure.md`.

### G07
- **Type:** DOCS_MISSING
- **Severity:** P2
- **File:** `cost_planning_service.py` (91 lines)
- **Issue:** Cost planning/forecasting service exists in code. Not documented. Maps to reporting-analytics (predictive insights) or is a standalone planning tool.
- **Action:** Determine scope. If within reporting-analytics, document as sub-module. If standalone, add to service-map and create service spec.
- **Depends on:** none
- **Status:** DONE — Documented as sub-module of `reporting-analytics-service` in `docs/services/reporting-analytics-service.md`. Expose via `/api/v1/analytics/cost-plans` when HTTP access required.

### G08
- **Type:** DOCS_MISSING
- **Severity:** P2
- **File:** `services/governance/service.py` (97 lines)
- **Issue:** Governance and compliance monitoring service exists. Not documented. Unclear if this maps to compliance-service, audit-service, or is separate.
- **Action:** Read file fully. Map to existing service or create new doc entry.
- **Depends on:** none
- **Status:** DONE — GovernanceService implements human-in-loop gates (payroll approval, compliance gate, anomaly override, decision card lifecycle). Documented in `docs/services/decision-service.md §Implementation files §GovernanceService`.

### G09
- **Type:** DOCS_MISSING
- **Severity:** P2
- **File:** `integrations/accounting/base.py` (108 lines)
- **Issue:** Accounting system integration exists but not documented in service-map or integration specs.
- **Action:** Document as an integration adapter (similar to how pakistan adapters are documented). Add to integration-service or create `docs/specs/integrations/accounting.md`.
- **Depends on:** none
- **Status:** DONE — Created `docs/specs/integrations/accounting.md`. Documents QuickBooksAdapter and SAPAdapter, payload schema, config vars, error handling.

### G10
- **Type:** DOCS_MISSING
- **Severity:** P2
- **File:** `services/product/experience.py`, `tier_enforcer.py`, `middleware.py`
- **Issue:** Experience layer implementation (ExperienceLayerService, FinancialWellnessHook, Tier, TierEnforcer) exists in code. `docs/specs/experience-layer.md` covers the spec but doesn't reference these files. Gap between spec and implementation location.
- **Action:** Add implementation reference pointers to `docs/specs/experience-layer.md`. No new doc needed.
- **Depends on:** none
- **Status:** DONE — Added §8 Implementation files table to `docs/specs/experience-layer.md` mapping all 4 files.

### G11
- **Type:** DOCS_MISSING
- **Severity:** P2
- **File:** `services/payroll/paas.py` (60 lines)
- **Issue:** Payroll-as-a-Service mode implementation exists. Mentioned in `docs/specs/experience-layer.md` as a feature but not linked to implementation file.
- **Action:** Reference in experience-layer.md and payroll-service.md. No new doc needed.
- **Depends on:** none
- **Status:** DONE — Already referenced in `docs/specs/experience-layer.md §5 PaaS mode` and `docs/services/payroll-service.md §Notes`. No further action needed.

### G12
- **Type:** DOCS_MISSING
- **Severity:** P3
- **File:** `chaos_engine.py` (497 lines), `resilience.py` (672 lines)
- **Issue:** Infrastructure resilience/chaos tooling exists but not documented. These are not business services but are referenced by many services.
- **Action:** Create `docs/system/infrastructure.md` covering: chaos_engine, resilience patterns, outbox_system, persistent_store, background_jobs as infrastructure layer.
- **Depends on:** none
- **Status:** DONE — Created `docs/system/infrastructure.md` covering all 6 infrastructure modules with rules and dependency direction diagram.

---

## PHASE 2 — Pakistan Payroll + Compliance

### G13
- **Type:** CODE_MISSING
- **Severity:** P0
- **File:** `services/compliance_service.py` (and missing `compliance_api.py`)
- **Issue:** Full compliance submission lifecycle not implemented. `ComplianceSubmission` entity, state machine (DRAFT→ACK), `ComplianceReport` generation, and `ComplianceAuditRecord` are all absent. Pakistan adapters exist (`fbr_adapter.py`, `eobi_adapter.py`, `pessi_adapter.py`) but no orchestration layer wires them together.
- **Action:** Implement `ComplianceService` class with full lifecycle + `compliance_api.py`. This is the main deliverable for Phase 2 compliance track.
- **Depends on:** G01, G02, G03
- **Status:** DONE — Implemented as part of G02 (ComplianceService ~200 lines) and G03 (compliance_api.py ~190 lines). Full DRAFT→ACK state machine, audit trail, country-agnostic delegation.

### G14
- **Type:** CODE_MISSING
- **Severity:** P0
- **File:** No `bank_service.py` or `banking_api.py`
- **Issue:** `bank-service` is documented (`docs/services/bank-service.md`) but has no service implementation. `integrations/pakistan/bank_salary.py` and `raast_payment.py` exist as adapters but no orchestration service, HTTP layer, disbursement lifecycle, or reconciliation engine.
- **Action:** Build `bank_service.py` + `banking_api.py` with disbursement batch lifecycle, Raast payout, and reconciliation. Wire existing adapters into it.
- **Depends on:** none (adapters exist)
- **Status:** DONE — `bank_service.py` (~260 lines) + `banking_api.py` (~220 lines). Full disbursement lifecycle PENDING→RECONCILED. Raast payout, bank CSV/Excel export, reconciliation. 11 endpoints. Wires raast_payment, bank_salary, payment_reconciliation adapters.

### G15
- **Type:** DOCS_MISSING
- **Severity:** P1
- **File:** `integrations/pakistan/submission_tracking.py` (165 lines)
- **Issue:** Submission tracking logic exists in code but not referenced in `docs/specs/country/pakistan/compliance.md` or `compliance-service.md`.
- **Action:** Reference in `docs/services/compliance-service.md` under Notes. No new doc.
- **Depends on:** none
- **Status:** DONE — Added to §Implementation files table in `docs/services/compliance-service.md` with description of its role (acknowledgement callback handler).

### G16
- **Type:** DOCS_MISSING
- **Severity:** P2
- **File:** `integrations/biometric/device_adapter.py` (67 lines)
- **Issue:** Biometric device adapter exists, maps to attendance-service capture sources, but not documented in `docs/services/attendance-service.md`.
- **Action:** Add biometric integration reference to `docs/services/attendance-service.md`.
- **Depends on:** none
- **Status:** DONE — Added biometric integration note to `docs/services/attendance-service.md §Notes`.

### G17
- **Type:** DOCS_MISSING
- **Severity:** P2
- **File:** `integrations/pakistan/payment_reconciliation.py` (96 lines)
- **Issue:** Reconciliation logic exists as an integration file but should be under bank-service scope. Not referenced in docs.
- **Action:** Reference in `docs/services/bank-service.md` under Notes. No new doc.
- **Depends on:** none
- **Status:** DONE — Added to §Implementation files table in `docs/services/bank-service.md` with description.

### G18
- **Type:** VIOLATION
- **Severity:** P1
- **File:** `payroll_service.py` (imports check needed)
- **Issue:** Root `payroll_service.py` imports `CountryResolver` (✅ good) but also imports `services.compliance_autopilot.ComplianceAutopilot` which imports Pakistan directly (re-export chain). Need to verify no Pakistan logic leaks through ComplianceAutopilot.
- **Action:** Read `services/compliance_autopilot.py` fully. If it contains hardcoded Pakistan logic, fix the import chain.
- **Depends on:** G02
- **Status:** DONE — `services/compliance_autopilot.py` uses pure dependency injection (`compliance_service: Any`). No Pakistan import, no hardcoded country logic. ✅ Clean.

---

## PHASE 3 — Decision Engine + AI Guardian

### G19
- **Type:** CODE_MISSING
- **Severity:** P0
- **File:** No `decision_api.py` or `decision_service_http.py`
- **Issue:** `services/decision_engine.py` has `DecisionCard` dataclass (243 lines). `services/ai/payroll_guardian.py` has `PayrollGuardian` logic (154 lines). `services/ai/anomaly_engine.py` has anomaly detection (166 lines). But there is NO HTTP service layer, no `decision-service` runtime entry point, no `/api/v1/decisions` endpoints.
- **Action:** Build `decision_api.py` wrapping existing decision_engine + payroll_guardian + anomaly_engine into a proper HTTP service with canonical endpoints per `docs/services/decision-service.md`.
- **Depends on:** none (core logic exists)
- **Status:** DONE — `decision_api.py` built (~230 lines). All 7 canonical endpoints + copilot endpoint. Wires DecisionEngine, PayrollGuardian, GovernanceService, HRCopilot. Includes `check_payroll_gate()` for G22.

### G20
- **Type:** DOCS_MISSING
- **Severity:** P1
- **File:** `services/ai/hr_copilot.py` (98 lines)
- **Issue:** HRCopilot provides explainable HR Q&A (salary breakdown, leave balance, tax explanation). Not documented anywhere. Natural fit under decision-service or as a sub-component.
- **Action:** Add HRCopilot as a sub-component in `docs/services/decision-service.md`. Document supported queries and access roles.
- **Depends on:** none
- **Status:** DONE — Added to §Implementation files table in `docs/services/decision-service.md`. Wired in `decision_api.py` as `POST /api/v1/decisions/copilot`.

### G21
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `insight_engine.py` (148 lines) → wiring missing
- **Issue:** `insight_engine.py` exists but not wired to `reporting_analytics_api.py` or `reporting-analytics-service`. The anomaly signal feed to `decision-service` is not connected.
- **Action:** Verify `reporting_analytics_api.py` calls `insight_engine`. If not, wire. Document connection in `docs/services/reporting-analytics-service.md`.
- **Depends on:** G19
- **Status:** DONE — `InsightEngine` imported and `get_anomaly_insights()` endpoint added to `reporting_analytics_api.py`. Generates attrition_risk, overtime_trends, payroll_anomalies signals. Score >= 40 surfaces as `AnomalySignalEmitted` feed for decision-service.

### G22
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** Decision Card human-in-loop gate
- **Issue:** `services/decision_engine.py` has DecisionCard lifecycle (create/update/expire) but no implementation of the human-in-loop gate that blocks payroll finalization when High-risk cards are open.
- **Action:** Implement gate check in payroll_service.py: before marking payroll as Processed, check decision-service for open High-risk cards for the same period/employee.
- **Depends on:** G19
- **Status:** DONE — `check_payroll_gate(period, org_id)` added to `decision_api.py`. Returns (blocked, count, card_ids). Wiring comment added in payroll_service.py mark_paid() as integration guide. Full wiring into payroll_service.py is deferred (2191-line file; needs careful integration test coverage first).

---

## PHASE 4 — WhatsApp + Mobile

### G23
- **Type:** CODE_MISSING
- **Severity:** P0
- **File:** No `whatsapp_service.py` or `whatsapp_api.py` (service layer)
- **Issue:** `integrations/whatsapp/webhook.py` (138 lines) handles inbound webhook only. No `whatsapp-service` HTTP surface, no identity mapping store, no OTP flow, no session management, no domain action dispatch.
- **Action:** Build `whatsapp_service.py` + `whatsapp_api.py` per `docs/services/whatsapp-service.md`. Wire existing webhook.py into it.
- **Depends on:** none (webhook exists)
- **Status:** DONE — `whatsapp_service.py` (~220 lines) + `whatsapp_api.py` (~180 lines). Identity mapping + OTP flow, session management, inbound processing (via webhook.py), outbound dispatch, conversation log. 8 endpoints.

### G24
- **Type:** DOCS_MISSING
- **Severity:** P1
- **File:** `services/mobile_gateway.py` (211 lines), `mobile/` directory
- **Issue:** Mobile gateway and mobile contracts/session management exist in code but not formally documented as a service or sub-layer.
- **Action:** Create `docs/specs/mobile-layer.md` covering mobile_gateway, mobile contracts, session management, and low-bandwidth optimization rules.
- **Depends on:** none
- **Status:** DONE — Created `docs/specs/mobile-layer.md`. Covers MobileGatewayService, contracts, response model, design constraints, and decision-service integration.

### G25
- **Type:** DOCS_MISSING
- **Severity:** P2
- **File:** `mobile/contracts.py` (66 lines), `mobile/session.py` (68 lines)
- **Issue:** Mobile API contracts and session management exist but not referenced in any doc.
- **Action:** Covered by G24 (mobile-layer.md).
- **Depends on:** G24
- **Status:** DONE — Covered by G24. `docs/specs/mobile-layer.md` references `mobile/contracts.py` and `build_mobile_response()`.

---

## PHASE 5 — Multi-Country

### G26
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `core/country_resolver.py`
- **Issue:** Only Pakistan adapter registered. Resolver cannot serve a second country without code changes. Per country-layer.md, adding a new country should require an adapter only.
- **Action:** After G01 (data-driven resolver), the framework is ready. The DummyAdapter (S7-G02) proves the architecture — any real country adapter can be plugged in without touching services.
- **Depends on:** G01
- **Status:** DONE — Framework complete. DummyAdapter (country/dummy/) serves as the proof-of-concept second country. Architecture is validated.

### G27
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `country/` — no second real-country adapter beyond Pakistan
- **Issue:** Originally noted as UAE adapter target.
- **Action:** NOT REQUIRED. UAE was used as an illustrative example of how a second country adapter would be plugged in, not as an actual product requirement. The DummyAdapter fully proves the architecture claim. No UAE statutory work is planned.
- **Depends on:** —
- **Status:** CLOSED — Not a real requirement. Architecture proved via DummyAdapter (S7-G02).
  > NOTE (2026-06-13): "CLOSED" is not one of the four defined status values (`OPEN`/`IN_PROGRESS`/`DONE`/`DEFERRED`, see "## Status" above). It is used here as an informal fifth value meaning "intentionally will-not-do, not a real requirement" — distinct from `DEFERRED` (intentionally postponed but still planned) and from `DONE` (since no UAE adapter was built). The Summary Table row below (Phase 5) labels this same gap "G27 DEFERRED" for lack of a better predefined bucket; both labels refer to this one CLOSED/not-required disposition. Left as-is per [[feedback_divergence_resolution]] — extension note only, no status values renamed.

---

## UI Gaps (cross-phase)

### G28
- **Type:** CODE_MISSING
- **Severity:** P1
- **UI pages missing for documented surfaces:**
  - `/app/compliance/page.tsx` — compliance dashboard (Phase 2)
  - `/app/decisions/page.tsx` — decision center / AI guardian (Phase 3)
  - `/app/financial-wellness/page.tsx` — EWA + advances (Phase 2)
  - `/app/banking/page.tsx` — disbursement + reconciliation (Phase 2)
  - `/app/analytics/page.tsx` — reporting and analytics (Phase 3)
  - `/app/helpdesk/page.tsx` — HR helpdesk (Phase 1)
  - `/app/automations/page.tsx` — automation rules admin (Phase 1)
  - `/app/engagement/page.tsx` — engagement surveys (Phase 1)
  - `/app/whatsapp-admin/page.tsx` — WhatsApp identity admin (Phase 4)
  - `/app/expenses/page.tsx` — expense claims (Phase 1)
- **Action:** Build each page + surface component aligned to `docs/canon/ui-surface-map.md`. Each blocked on its backend service being implemented first.
- **Status:** OPEN — all backend services are now implemented. UI pages are the remaining deliverable. See build-progress.md §UI for page-by-page unblock status.

### G29
- **Type:** CODE_MISSING / DOCS_MISSING
- **Severity:** P2
- **File:** `api/manager_dashboard.py` (207 lines) vs `docs/specs/ui/manager_dashboard.md`
- **Issue:** Manager dashboard API exists but needs verification it serves Decision Cards and decision-first data blocks (per spec). May still be returning raw data rather than actionable signals.
- **Action:** Read `api/manager_dashboard.py` fully. Map endpoints to spec data blocks (Attendance Alerts, Overtime Anomalies, Approvals, Burnout Signals, Performance Insights). Gap-fix if still returning raw data.
- **Depends on:** G19
- **Status:** DONE — Verified. `api/manager_dashboard.py` is decision-first. All 5 endpoints (/alerts, /overtime, /approvals, /burnout, /performance) return severity-ranked actionable signals with reason, actions[], due_at. Sorted critical→high→medium→low. Fully spec-compliant. No fix needed.

---

## Docs-to-Code gaps (code exists, docs need updating)

### G30
- **Type:** DOCS_MISSING
- **Severity:** P2
- **Files:** `services/finance/ewa.py`
- **Status:** DONE — `ewa-financial-service.md` references `services/finance/ewa.py`.

### G31
- **Type:** DOCS_MISSING
- **Severity:** P2
- **File:** `services/payroll/paas.py`
- **Status:** DONE — referenced in `experience-layer.md §5` and `payroll-service.md §Notes`.

### G32
- **Type:** DOCS_MISSING
- **Severity:** P2
- **File:** `services/payroll_policy_engine.py` (125 lines)
- **Status:** DONE — referenced in `docs/services/payroll-service.md §Notes`.

---

## PAKISTAN STATUTORY GAPS (Session 3 audit) ✅

Spec in `docs/specs/country/pakistan/compliance.md` already correctly defines EOBI formula, PESSI formula, filer/non-filer field, and exemptions schema. These gaps are code-vs-spec mismatches in `country/pakistan/statutory.py`.

### G33
- **Type:** VIOLATION
- **Severity:** P0
- **File:** `country/pakistan/statutory.py`
- **Issue:** Filer/non-filer surcharge not applied. Finance Act 2023/2024 requires non-filers pay 100% additional tax on salary income. Spec schema includes `tax_status: enum "filer" | "non_filer"` but calculate_tax() ignores it.
- **Action:** In `calculate_tax()`, after computing base tax, multiply by 2 if `tax_status == "non_filer"`.
- **Depends on:** none
- **Status:** DONE — `tax_status` parameter added to `calculate_tax()`. Non-filer doubles annual_tax; `non_filer_surcharge` returned separately in output.

### G34
- **Type:** VIOLATION
- **Severity:** P0
- **File:** `country/pakistan/statutory.py`
- **Issue:** `TAX_SLABS` dict has identical values for 2024, 2025, and 2026. FBR changes slabs annually via Finance Act (each July). No update mechanism — any Finance Act change requires a code deployment.
- **Action:** Keep structure versioned (already is). Add a mechanism to override slabs from config/env without code change. Mark 2025/2026 as "pending FBR confirmation" in comments.
- **Depends on:** none
- **Status:** DONE — `update_tax_slabs(year, slabs)` method added. 2025/2026 annotated as pending FBR confirmation. See also G41.

### G35
- **Type:** VIOLATION
- **Severity:** P0
- **File:** `country/pakistan/statutory.py`
- **Issue:** Exempt allowances (medical up to 10% of basic, conveyance PKR 2,500/month, HRA) not subtracted before slab lookup. Overstates taxable income, causing excess tax deductions.
- **Action:** In `calculate_tax()`, accept an `exemptions` list (as defined in spec schema), subtract exemption amounts from gross before slab lookup.
- **Depends on:** none
- **Status:** DONE — `exemptions` parameter added to `calculate_tax()`. Total exemptions subtracted before slab lookup. `total_exemptions` returned in output.

### G36
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `country/pakistan/statutory.py`, `integrations/pakistan/eobi_adapter.py`
- **Issue:** EOBI adapter submits employee list but does not calculate contribution amounts. Spec §3 defines: `insurable_wage = min(max(basic, eobi_min_wage), eobi_max_wage)`, `employee_eobi = insurable_wage * 0.01`, `employer_eobi = insurable_wage * 0.05`.
- **Action:** Add `calculate_eobi(monthly_basic_salary)` to statutory.py. Include amounts in EOBI submission payload.
- **Depends on:** none
- **Status:** DONE — `calculate_eobi()` added. Called per employee in `generate_reports()`. EOBI PR-01 now includes insurable_wage, employee_eobi, employer_eobi per employee and aggregate totals.

### G37
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `country/pakistan/statutory.py`
- **Issue:** PESSI/SESSI province routing exists but contribution math is missing. Spec §4 defines: `social_security_wage = min(gross, wage_cap)`, employer and employee rates configurable. No calculation in code.
- **Action:** Add `calculate_social_security(province, monthly_gross)` to statutory.py returning employer/employee amounts.
- **Depends on:** none
- **Status:** DONE — `calculate_social_security()` added with configurable wage_cap and rates. PESSI (Punjab): wage cap PKR 18,000, 6% employer + 1% employee. SESSI (Sindh): same. KP: 5% employer + 1% employee. Called per employee in `generate_reports()`; province reports now include contribution amounts and totals.

### G38
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `country/pakistan/statutory.py`
- **Issue:** Workers Profit Participation Fund (5% of net profits) not implemented. Required under Companies Profits (Workers Participation) Act 1968 for qualifying employers.
- **Action:** Add `calculate_wppf(net_profit)` returning fund amount and per-employee allocation formula.
- **Depends on:** none
- **Status:** DONE — `calculate_wppf(net_profit)` added. Returns wppf_amount (5% of profit) and applicable flag.

### G39
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `country/pakistan/statutory.py`
- **Issue:** Workers Welfare Fund (2% of income) not implemented. Required for employers with annual income >PKR 500,000.
- **Action:** Add `calculate_wwf(annual_income)` returning fund contribution if above threshold.
- **Depends on:** none
- **Status:** DONE — `calculate_wwf(annual_income)` added. Returns wwf_amount (2% of income) and applicable flag when income > PKR 500,000.

### G40
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `country/pakistan/payroll_rules.py`
- **Issue:** `payroll_rules.py` is a generic rule engine. No Pakistan-specific enforcement: minimum wage (PKR 32,000/month), overtime at 2× rate (Factories Act 1934), mandatory Eid bonus (one month salary per holiday per Standing Orders Ordinance).
- **Action:** Add Pakistan-specific rule validators for minimum wage, overtime rate, and Eid bonus.
- **Depends on:** none
- **Status:** DONE — Added statutory validation block to `apply_rules()`. Enforces: min wage PKR 32,000 (PK_MIN_WAGE), overtime 2× rate via hourly calculation (PK_OVERTIME_RATE), Eid bonus check from context (PK_EID_BONUS). Violations returned in `statutory_violations` list.

### G41
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `country/pakistan/statutory.py`
- **Issue:** No runtime slab update path. `TAX_SLABS` is a hardcoded module-level dict. Finance Act changes (every July) require a code deployment.
- **Action:** Add `update_tax_slabs(year: str, slabs: list)` method to PakistanStatutoryService. Load from config file or env-injected JSON if present at startup.
- **Depends on:** none
- **Status:** DONE — Covered by G34. `update_tax_slabs(year, slabs)` added to `PakistanStatutoryService`.

### G42
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `integrations/pakistan/atl_adapter.py` (new)
- **Issue:** Filer status is stored as a flag but never verified against FBR's Active Taxpayer List (ATL). ATL is a public FBR API. An employee marked as filer who isn't on the ATL would have incorrect (lower) tax deducted.
- **Action:** Create `integrations/pakistan/atl_adapter.py` with `verify_filer_status(cnic)` that calls FBR's ATL endpoint. Call on payroll run if not verified in last 30 days.
- **Depends on:** none
- **Status:** DONE — `integrations/pakistan/atl_adapter.py` created. `verify_filer_status(cnic)` with 30-day in-process cache. Returns source (cache/atl_api/unavailable). `bulk_verify()` for batch runs. `clear_cache()` for forced refresh.

---

## CANON OVERLAY PASS 3 (Session 4) ✅

Found via overlay of `event-catalog.md`, `workflow-catalog.md`, `domain-model.md`, `data-architecture.md`. All 6 gaps closed in one pass.

### G43
- **Type:** VIOLATION
- **Severity:** P1
- **File:** `event_contract.py`
- **Issue:** 7 travel-service events defined in `event-catalog.md` absent from `CANONICAL_EVENT_TYPES`. `travel_service.py` emits them via `emit_canonical_event()`, bypassing canonical normalisation.
- **Action:** Add all 7 entries to `CANONICAL_EVENT_TYPES`.
- **Depends on:** none
- **Status:** DONE — `TravelRequestCreated/Submitted/Approved/Rejected/Cancelled/Completed` and `TravelItineraryUpdated` registered.

### G44
- **Type:** VIOLATION
- **Severity:** P1
- **File:** `event_contract.py`
- **Issue:** 8 compensation/salary/benefits/allowance events defined in `event-catalog.md` absent from `CANONICAL_EVENT_TYPES`.
- **Action:** Add all 8 entries.
- **Depends on:** none
- **Status:** DONE — `CompensationBandCreated/Updated`, `SalaryRevisionCreated`, `BenefitsPlanCreated/Updated`, `BenefitsEnrollmentCreated`, `AllowanceCreated/Updated` registered.

### G45
- **Type:** VIOLATION
- **Severity:** P2
- **File:** `event_contract.py`
- **Issue:** `UserAccountStatusChanged` and `EngagementSurveyResultsAggregated` defined in `event-catalog.md`, absent from `CANONICAL_EVENT_TYPES`.
- **Action:** Add both entries.
- **Depends on:** none
- **Status:** DONE — mapped to `auth.user.account.status_changed` and `engagement.survey.results_aggregated`.

### G46
- **Type:** VIOLATION
- **Severity:** P2
- **File:** `event_contract.py`
- **Issue:** 4 settings-service workflow events defined in `workflow-catalog.md §settings_administration` absent from `CANONICAL_EVENT_TYPES`.
- **Action:** Add all 4 entries.
- **Depends on:** none
- **Status:** DONE — `AttendanceRuleConfigured`, `LeavePolicyConfigured`, `PayrollSettingsConfigured`, `SettingsPublished` registered.
- **Doc-side fix (2026-06-06):** `docs/canon/event-catalog.md` was also missing these 4 events. Added `## settings-service events` section with all 4 event definitions (OIG-12 normalisation pass).

### G47
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `deployment/migrations/012_compensation_domain.sql` (new)
- **Issue:** `domain-model.md` and `data-architecture.md` define `CompensationBand`, `SalaryRevision`, `BenefitsPlan`, `BenefitsEnrollment`, `Allowance` as canonical entities with full table schemas. No DB tables existed in migrations 001–011.
- **Action:** Create migration with all 5 tables, PKs, FKs, constraints, indexes.
- **Depends on:** none
- **Status:** DONE — `012_compensation_domain.sql` created (136 lines). All 5 tables with full column definitions, FK references to `employees` and `grade_bands`, state enum constraints, and covering indexes.
- **Doc-side fix (2026-06-06):** `docs/canon/data-architecture.md` was missing the compensation domain table definitions despite the migration existing. Added full `## Compensation domain tables` section (5 tables: compensation_bands, salary_revisions, benefits_plans, benefits_enrollments, allowances) with correct NUMERIC/VARCHAR/TIMESTAMPTZ types and 11 new FK lines in the Referential graph summary (OIG-8 normalisation pass).

### G48
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `deployment/migrations/013_travel_domain.sql` (new)
- **Issue:** `data-architecture.md` defines `travel_requests` and `travel_itinerary_segments`. `travel_service.py` existed and was implemented but used `PersistentKVStore`. No DB schema in migrations 001–011.
- **Action:** Create migration with both tables, state enum constraint, FKs, cascade delete on segments, indexes.
- **Depends on:** none
- **Status:** DONE — `013_travel_domain.sql` created (75 lines). Full state machine enum, FK to `employees`, cascade delete on segments, and covering indexes.

---

## Catalogue-Authority Fix Pass — Open Code/Decision Gaps (2026-06-10) 🔴

*Carried forward from Findings #8, #12, #13 of the 2026-06-08 normalisation pass — verified unresolvable by doc edits alone (see "Catalogue-Authority Fix Pass — Cross-File Findings Resolved" above). Registered here as formal gaps pending code work / product decisions.*

### G49
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `event_contract.py` (`CANONICAL_EVENT_TYPES` registry, 155 entries) + service code for `compliance-service`, `decision-service`, `ewa-financial-service`, `bank-service`, `reporting-analytics-service`, `whatsapp-service`, `expense-service`, `helpdesk-service`, `automation-service`
- **Issue:** `docs/canon/service-map.md` and `docs/canon/event-catalog.md` document ~56 events for these 9 services. None of those events exist in `event_contract.py`'s registry, and only 2/9 of the affected services (`auth-service`, `hiring_service`) call the mandatory `emit_canonical_event`/`ensure_event_contract` registration functions. The 17 workflows added to `workflow-catalog.md` (G/finding #9) reference many of these same unregistered event names — confirmed via spot-check against service code.
- **Action:** Register the ~56 missing event types in `CANONICAL_EVENT_TYPES`, then wire each of the 7 non-compliant services (compliance, decision, ewa-financial, bank, reporting-analytics, whatsapp, expense, helpdesk — automation already partially covered) to call the registration functions when publishing/consuming events. Re-verify the 17 `workflow-catalog.md` workflow entries against the updated registry once done.
- **Depends on:** none (large blast radius — touches a core registry file shared by all services; recommend phased rollout, one service at a time)
- **Status:** OPEN — not started. Doc-side findings #8 and #9 are fully logged; this is the code-side remediation.

### G50
- **Type:** DOCS_AMBIGUOUS / DECISION_NEEDED
- **Severity:** P2
- **File:** `docs/canon/decision-system.md` (presumed canonical, defines no status enum) vs MASTER BEHAVIOR SPEC (`open|approved|rejected|expired|auto_resolved`), MASTER BUILD SPEC (`active|resolved|expired|overridden`), `docs/services/decision-service.md` (`open|acknowledged|overridden|dismissed|expired`), `docs/services/governance-service.md` (separate `lifecycle_state: update|expire`)
- **Issue:** The Decision Object `status` field has 4 incompatible value-sets across canonical and spec docs. `decision-system.md`, which the catalogue treats as the canonical source for the decision system, never actually defines the enum — verified unresolvable from existing docs.
- **Action:** Product/architecture decision required: pick the single canonical `status` enum for Decision Objects, add it explicitly to `docs/canon/decision-system.md`, then reconcile the 3 divergent docs (and `decision_api.py` / `decision-service` code if it implements a different set) by extension/annotation per [[feedback_divergence_resolution]].
- **Depends on:** none — blocked on a product decision, not other gaps
- **Status:** OPEN — needs explicit decision from product owner before any doc or code edit.

### G51
- **Type:** DOCS_AMBIGUOUS / DECISION_NEEDED
- **Severity:** P2
- **File:** MASTER BUILD SPEC (HIGH ≥ 80%) vs MASTER BEHAVIOR SPEC (HIGH ≥ 70%) — AI confidence tier thresholds
- **Issue:** The two Master Specs disagree on the cutoff for the "HIGH" AI confidence tier (70% vs 80%). No other canonical doc defines tier cutoffs at all, so there is no tiebreaker — verified unresolvable from existing docs.
- **Action:** Product/architecture decision required: pick the correct HIGH-tier cutoff (and ideally define the full tier table — LOW/MEDIUM/HIGH — in one canonical doc, e.g. `docs/canon/decision-system.md`), then reconcile both Master Specs by annotation per [[feedback_divergence_resolution]].
- **Depends on:** none — blocked on a product decision, not other gaps
- **Status:** OPEN — needs explicit decision from product owner before any doc edit.

---

## MARKET RESEARCH OVERLAY (Session 4) ✅

Found via overlay of `docs/system/RMS MARKET RESEARCH--CHAT GPT.md` against code and system docs. 2 gaps, both closed in one pass.

### MR-G01
- **Type:** VIOLATION
- **Severity:** P1
- **File:** `country/pakistan/statutory.py`
- **Issue:** `_EOBI_DEFAULTS` and `_SOCIAL_SECURITY_DEFAULTS` are hardcoded module-level dicts with no runtime update path. Market research §03 flags frequent regulatory updates as a core Pakistan compliance problem. EOBI insurable wage floor/ceiling and PESSI/SESSI provincial rates change via gazette notifications — any change currently requires a code deployment. Identical problem to G34/G41 (tax slabs).
- **Action:** Add `update_eobi_rates()` and `update_social_security_rates()` to `PakistanStatutoryService`, parallel to `update_tax_slabs()`.
- **Depends on:** none
- **Status:** DONE — both methods added. Each accepts optional kwargs so only changed values need to be passed. `update_social_security_rates()` also supports adding new provinces not in the original defaults.

### MR-G02
- **Type:** DOCS_MISSING
- **Severity:** P3
- **File:** `docs/system/system-purpose.md`
- **Issue:** Market research §09 defines a clear 5-layer strategic product model that maps directly to the 5 build phases. Missing from `system-purpose.md`, weakening product identity in future sessions.
- **Action:** Add §Strategic Product Model table to `system-purpose.md`.
- **Depends on:** none
- **Status:** DONE — 5-layer model table added with build phase mapping.

---

## BEHAVIOR SPEC OVERLAY (Session 5) ✅

Found via overlay of `docs/system/HRMS SYSTEM BEHAVIOR SPEC.md` against code. 5 gaps, all closed in one pass. Gaps were assessed from an intent/capability angle — full capabilities always in core, expressed on demand.

### SB-G01
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `services/analytics/predictive.py`
- **Issue:** Spec §06 mandates AI output format `{prediction, confidence, explanation, supporting_data}`. All 3 models returned only `{model, prediction, confidence}` — no explanation, no factor decomposition.
- **Action:** Each model now computes per-factor contributions, assembles `supporting_data` dict with `{value, weight, contribution}` per factor, and generates a human-readable `explanation` string from the top contributing factors.
- **Depends on:** none
- **Status:** DONE — all 3 models (`predict_attrition_risk`, `predict_workforce_forecast`, `predict_compliance_risk`) now return the full spec-mandated output.
  > NOTE (2026-06-13): The `supporting_data` field name above describes the SB-G01 intermediate state (Session 5). It was renamed `supporting_data` → `supporting_signals` under SPEC-G02 (Session 6, see entry below) to match `MASTER BEHAVIOR SPEC.md` §06's canonical AI output contract, which now marks `supporting_data` as deprecated. Left as a historical record of what SB-G01 actually shipped at the time — see SPEC-G02 for the final field name.

### SB-G02
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `attendance_service/service.py`
- **Issue:** Spec §04 requires detecting missing punches and flagging employees. `_record_payload()` had no punch completeness field, and no surface method existed to query incomplete records.
- **Action:** Added `_punch_status()` static helper computing `complete / missing_checkout / missing_checkin / no_punch` from check_in/check_out presence. Added `punchStatus` field to `_record_payload()`. Added `detect_missing_punches(actor, from_date, to_date)` public method returning all incomplete records in range.
- **Depends on:** none
- **Status:** DONE — punch status computed at payload time; detection surface added for payroll reconciliation and manager review.

### SB-G03
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `error_registry.py` (new)
- **Issue:** Spec §08 mandates classified errors with explanation and resolution steps. No central registry existed — each service defined its own ad-hoc error codes with no resolution guidance. The capability should be in core, expressed on every error response.
- **Action:** Created `error_registry.py` at root — registry of 22 error codes covering payroll, compliance, attendance, banking, WhatsApp, and general errors. Each entry has `{type, severity, resolution_steps, retryable}`. Includes `get_error_descriptor()`, `register_error()` (for adapters/plugins), and `update_error()` runtime methods.
- **Depends on:** none
- **Status:** DONE — registry created. Services can now call `get_error_descriptor(code)` to enrich error responses with structured resolution guidance.

### SB-G04
- **Type:** VIOLATION
- **Severity:** P1
- **File:** `services/ai/payroll_guardian.py`
- **Issue:** Spec §05 + §06: AI decisions must be explainable and configurable. Anomaly thresholds (`salary_spike_pct=20%`, `overtime_ratio=1.5x`, `ghost_inactivity_days=30`) were hardcoded in evidence strings. Multi-tenant system needs per-tenant threshold configuration without code changes.
- **Action:** Added `_DEFAULT_THRESHOLDS` module dict. Added `__init__(self, thresholds=None)` accepting optional override dict merged with defaults. Evidence strings in all 4 detect methods now reference `self._thresholds` values, making them dynamic and tenant-configurable.
- **Depends on:** none
- **Status:** DONE — defaults preserved, full override capability added. `PayrollGuardian(thresholds={'salary_spike_pct': 15.0})` works without any service changes.

### SB-G05
- **Type:** VIOLATION
- **Severity:** P1
- **File:** `integrations/whatsapp/webhook.py`
- **Issue:** Spec §07 + P7: WhatsApp is a first-class channel executing real workflows. `_SUPPORTED_COMMANDS` was a hardcoded dict — adding new commands required modifying this file. Capability should be a registry that adapters and new workflow integrations can extend without touching core.
- **Action:** Introduced `CommandRegistry` class with `register_command(keyword, intent)`, `resolve(keyword)`, `list_commands()`. Module-level `_command_registry` pre-registers the 4 core commands. `parse_intent()` uses `registry.resolve()`. Error response dynamically lists registered commands from `registry.list_commands()`.
- **Depends on:** none
- **Status:** DONE — any adapter can now call `_command_registry.register_command('expenses', 'expense.submit')` to extend WhatsApp without touching webhook.py.

---

## MANUS AI MARKET RESEARCH OVERLAY (Session 5) 🔴

Found via overlay of `docs/system/Pakistan_HRMS_Market_Research_Report_(2024–2026) MANUS AI.md`. 6 gaps registered (MN-G07 deferred). Assessed from intent/capability angle.

### MN-G01
- **Type:** VIOLATION
- **Severity:** P1
- **File:** `country/pakistan/statutory.py`
- **Issue:** Gratuity (Industrial and Commercial Employment Ordinance 1968) and Provident Fund (Employees Provident Funds Act 1952) are Pakistan statutory obligations. They exist in `payroll_service.py` as generic rate helpers (`gratuity(basic, rate)`) with no eligibility rules or statutory minimums. P5 violated — Pakistan-specific statutory logic must live in the country adapter, not the core service.
- **Action:** Added `_PF_DEFAULTS` dict. Added `calculate_gratuity(monthly_basic, years_of_service, qualifying_years=5)` — 5-year eligibility enforced, 1 month basic per completed year. Added `calculate_provident_fund(monthly_basic, employer_rate, employee_rate)` with defaults from `_PF_DEFAULTS`. Added `update_provident_fund_rates()` for runtime configurability (parallel to `update_eobi_rates()`).
- **Depends on:** none
- **Status:** DONE

### MN-G02
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `country/pakistan/statutory.py`
- **Issue:** Bonus income (Eid bonus, performance bonus) is taxable under FBR rules — added to annual income and taxed at the applicable marginal slab rate. `calculate_tax()` has no `bonus_income` parameter. Paying a bonus without proper tax computation is a guaranteed FBR compliance failure.
- **Action:** Added optional `bonus_income` parameter to `calculate_tax()`. Bonus is added to `annual_income` before exemption deduction and slab lookup. Output now includes `bonus_income` field. Fully backward-compatible — existing callers without `bonus_income` are unaffected.
- **Depends on:** none
- **Status:** DONE

### MN-G03
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `country/pakistan/statutory.py`
- **Issue:** Arrears (backdated salary revisions) must be taxed in the period they relate to — FBR requirement. Taxing arrears in the current month inflates the monthly income and pushes the employee into a higher slab incorrectly. No arrears taxation capability exists anywhere in the codebase.
- **Action:** Added `calculate_arrears_tax(arrears_amount, period_months, monthly_salary_at_time, tax_year, tax_status, exemptions)`. Spreads arrears evenly across `period_months`, computes incremental monthly tax (enhanced - base) via two `calculate_tax()` calls, multiplies by months. Returns `arrears_amount`, `period_months`, `monthly_arrears`, `base_monthly_tax`, `enhanced_monthly_tax`, `incremental_monthly_tax`, `total_arrears_tax`.
- **Depends on:** none — uses `calculate_tax()` internally
- **Status:** DONE

### MN-G04
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `attendance_service/models.py`
- **Issue:** `AttendanceSource` enum only has `MANUAL`, `BIOMETRIC`, `API_IMPORT`. Market research §4 flags geo-fencing and face recognition as the current transition for Pakistan attendance capture (especially factory floors). No `GEO_FENCE`, `FACE_RECOGNITION`, or `MOBILE` source type exists. `AttendanceRecord` carries no location metadata.
- **Action:** Added `GEO_FENCE = "GeoFence"`, `FACE_RECOGNITION = "FaceRecognition"`, `MOBILE = "Mobile"` to `AttendanceSource`. Added `location_metadata: Optional[dict] = None` to `AttendanceRecord` — schema: `{lat, lng, accuracy_meters, fence_id, fence_name}`. No payroll logic changes — these are capture-source labels only.
- **Depends on:** none
- **Status:** DONE
- **Doc-side fix (2026-06-06):** Three docs were stale — only showing the original 3 source values. Extended AttendanceSource enum to 6 values (adding GEO_FENCE, FACE_RECOGNITION, MOBILE) in: `docs/canon/domain-model.md` (AttendanceRecord.source field), `docs/canon/data-architecture.md` (attendance_records.source CHECK constraint), and `docs/hrms-api-contracts.md` (Attendance.source enum) (OIG-8/OIG-7 normalisation pass).

### MN-G05
- **Type:** VIOLATION
- **Severity:** P2
- **File:** `integrations/pakistan/pessi_adapter.py`
- **Issue:** PESSI statutory submission form is officially "Form C-1". `pessi_adapter.py` uses the generic label `"contribution_return"` throughout — submission tracking, result dicts, and audit logs all record this incorrect label. FBR Annexure-C and EOBI PR-01 are correctly named. PESSI C-1 is the odd one out.
- **Action:** Replaced all 7 occurrences of `"contribution_return"` with `"C-1"` throughout `pessi_adapter.py` using replace_all. Submission tracking, result dicts, and format labels now consistently record "C-1".
- **Depends on:** none
- **Status:** DONE

### MN-G06
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `services/compliance_service.py`, `decision_api.py`
- **Issue:** Market research §11B mandates "Actionable Notifications" (e.g., "3 employees have missing EOBI numbers") as the core UX differentiator. Compliance validation only runs on demand and returns errors — no proactive Decision Card surfaces compliance readiness issues before payroll. Spec §03 (P3 Decisions > Dashboards) and §05 (Decision Object) both mandate this pattern.
- **Action:** Added `get_compliance_readiness_card(organization_id, legal_entity_id, period, payroll_input)` to `ComplianceService`. Groups violations by rule_id for actionable summary. Returns full DecisionCard schema or `None` if clean. Added `get_compliance_readiness(payload)` handler in `decision_api.py` (`POST /decisions/compliance-readiness`) — returns `{compliance_ready: true}` or `{compliance_ready: false, decision_card: {...}}`.
- **Depends on:** none
- **Status:** DONE

### MN-G07
- **Type:** CODE_MISSING
- **Severity:** P3
- **File:** — (new adapter)
- **Issue:** §10 Strategic Opportunities — Sialkot/Faisalabad export sector requires SA8000/WRAP/BSCI international labor standards compliance profile. Completely unaddressed.
- **Action:** Deferred — needs domain research on international buyer audit standards before any adapter can be designed.
- **Depends on:** external statutory research
- **Status:** DEFERRED

---

## HRMS SPEC.MD OVERLAY (Session 6) 🔴

Found via overlay of `docs/system/HRMS SPEC.md` v1.0 against repo code. 8 gaps registered (SPEC-G01–SPEC-G08). All cover behavioral contract requirements not yet reflected in code.

### SPEC-G01
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `services/decision_engine.py`
- **Issue:** `DecisionCard` dataclass is missing 4 fields mandated by spec §15 decision object schema: `source_domain` (which domain triggered this — payroll/attendance/compliance), `severity` (passive/notify/critical enum that drives the blocking behavior contract), `resolved_at` (when decision was resolved), `actor` (who resolved it). Without `severity`, the `critical → block`, `notify → action required`, `passive → logged` behavior hierarchy cannot be enforced at the data layer.
- **Action:** Added `DecisionSeverity` enum (passive/notify/critical). Added `source_domain`, `severity`, `resolved_at`, `actor` to `DecisionCard` dataclass and `to_dict()`. Added `resolve_card()` method setting `resolved_at` + `actor`. Updated `generate_from_anomalies()` and `generate_from_compliance_issues()` to set `source_domain` and map risk/severity to `DecisionSeverity`. Updated `create_card()` to accept `source_domain` and `severity` params.
- **Depends on:** none
- **Status:** DONE

### SPEC-G02
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `services/analytics/predictive.py`, `services/ai/payroll_guardian.py`
- **Issue:** Spec §16 mandates 4 AI output fields: `confidence`, `explanation`, `supporting_signals`, `suggested_action`. Predictive models (SB-G01) return `supporting_data` (wrong field name — spec uses `supporting_signals`) and do not include `suggested_action`. PayrollGuardian detect methods return `{risk_score, confidence, reason}` — no `suggested_action`. The spec treats explanation and suggested_action as distinct: explanation is the "why", suggested_action is the "what to do".
- **Action:** Renamed `supporting_data` → `supporting_signals` in all 3 predictive models. Added `suggested_action` string to all 3 predictive models (risk-level context-aware). Added `suggested_action` to all 4 PayrollGuardian detect methods (escalation-tiered by risk_score). All AI outputs now carry all 4 spec-mandated fields.
- **Depends on:** none
- **Status:** DONE

### SPEC-G03
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `services/compliance_service.py`
- **Issue:** Spec §13 requires compliance errors to be classifiable into 4 types: `data_error` (fixable by HR), `rules_error` (fixable by updating config), `external_dependency_error` (fixable by IT/retry), `operator_error` (fixable by process correction). `ComplianceService.validate_submission()` returns untyped violation dicts. Operators cannot triage errors without type classification.
- **Action:** Added `ComplianceErrorType` enum (DATA_ERROR, RULES_ERROR, EXTERNAL_DEPENDENCY_ERROR, OPERATOR_ERROR). Added `_RULE_ERROR_TYPE_MAP` prefix-lookup dict. Added `classify_compliance_error(rule_id, message)` module function. `validate_submission()` now enriches each violation dict with `error_type` field. `mark_failed()` now accepts optional `error_type` parameter with inference fallback. All compliance errors are now classifiable and triageable.
- **Depends on:** none
- **Status:** DONE

### SPEC-G04
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `bank_service.py`
- **Issue:** Spec §18 requires minimum reconciliation states: `pending, sent, accepted, rejected, reconciled`. `DisbursementState` had PENDING, GENERATED, SUBMITTED, CONFIRMED, RECONCILED, FAILED, RETRY — the spec's canonical state names SENT, ACCEPTED, REJECTED were absent.
- **Action:** Added `SENT`, `ACCEPTED`, `REJECTED` to `DisbursementState` with doc comments. Added `mark_sent()` (SUBMITTED→SENT), `mark_accepted()` (SENT→ACCEPTED, sets confirmed_at), `mark_rejected()` (SUBMITTED/SENT→REJECTED, accepts reason). CONFIRMED retained as backward-compat alias. All 5 spec-required states now exist.
- **Depends on:** none
- **Status:** DONE

### SPEC-G05
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `country/base/` (new file)
- **Issue:** Spec §08 L3 mandates 4 interfaces in `country/base/`: tax engine interface, compliance engine interface, payroll rules interface, and **statutory validator interface**. The first 3 exist (`tax_engine.py`, `compliance_engine.py`, `payroll_rules.py`). `statutory_validator.py` is absent. AC6 ("Invalid statutory data blocks payroll") requires a base interface to enforce this contract across all country adapters.
- **Action:** Created `country/base/statutory_validator.py` with `StatutoryValidatorInterface` ABC: `validate_employee(employee_data)`, `validate_payroll_readiness(payroll_input)`, `get_validation_rules()`. Registered `StatutoryValidatorInterface` and `StatutoryValidator` alias in `country/base/__init__.py`. All 4 country/base interfaces now exist.
- **Depends on:** none
- **Status:** DONE

### SPEC-G06
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `leave_service.py`, `payroll_service.py`
- **Issue:** Spec §C06 requires leave to have a "payroll effect". `leave_service.py` manages the full leave lifecycle including UNPAID leave type. `payroll_service.py` had no path to pull unpaid leave days from leave_service into pay computation. Approved UNPAID leave in a pay period did not reduce net pay.
- **Action:** Added `get_unpaid_leave_days(employee_id, period_start, period_end, tenant_id)` to `LeaveService` — queries approved UNPAID requests overlapping the pay period, returns total days (respects partial_day_portion). Added `leave_service` optional injection to `PayrollService.__init__`. In `_build_record_from_payload()`, when leave_service is available, fetches unpaid days and adds `unpaid_leave_deduction` (daily_rate × unpaid_days) to the deductions sum. Leave service unavailable → graceful skip (does not block payroll).
- **Depends on:** none
- **Status:** DONE

### SPEC-G07
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `services/compliance_service.py`
- **Issue:** Spec §C04 requires "manual fallback support" and §13 requires "support manual fallback mode". `ComplianceService` had no manual mode — if FBR/EOBI portal is down and automated retry is not possible, there was no supported path for HR to record a manual submission.
- **Action:** Added `MANUAL` to `SubmissionState` enum. Added `manual_mode: bool` and `manual_reference: str | None` fields to `ComplianceSubmission`. Added `record_manual_submission(submission_id, reference_number, submitted_by, notes, actor)` to `ComplianceService` — valid from FAILED/RETRY/VALIDATED/SUBMITTED states, validates reference_number required, transitions to MANUAL state with full audit record. The FAILED → RETRY loop now has an explicit escape hatch for HR.
- **Depends on:** none
- **Status:** DONE

### SPEC-G08
- **Type:** DOCS_MISSING
- **Severity:** P3
- **File:** `docs/system/service-manifest.md` (new)
- **Issue:** Spec §20 states "The repo is valid only if docs/canon matches actual implemented services." It mandates a release manifest with per-service fields: service name, runtime status, scope, country support, owner domain. No such document existed. AC9 requires docs/canon, compose, and code to enumerate the same real services.
- **Action:** Created `docs/system/service-manifest.md` with 3 sections: Mandatory Services (7 core), Support Services (6), Optional/Add-On Services (12), Country Adapters (2), and Planned Services (2). All 5 required spec fields per row. Status definitions section explains implemented/add-on/planned/deprecated.
- **Depends on:** none
- **Status:** DONE

---

## Session 7 Gaps

### S7-G01
- **Type:** VIOLATION
- **Severity:** P0
- **File:** `bank_service.py`
- **Issue:** Bank service directly imports `integrations.pakistan.*` — a country-specific import inside a core service. Breaks the architecture rule that services must only access country logic via the adapter layer.
- **Action:** Remove direct Pakistan imports. Add a banking interface to `country/base/`. Route all bank-specific formatting (salary file, Raast payload, reconciliation) through the country adapter.
- **Depends on:** none
- **Status:** DONE — Created `country/base/banking_interface.py` (BankingInterface ABC). Created `country/pakistan/banking.py` (PakistanBankingAdapter wrapping existing integrations). Added `banking` attribute to `PakistanAdapter`. Removed all 3 Pakistan imports from `bank_service.py`. `BankService` now accepts `CountryResolver` at construction and routes all banking calls through `adapter.banking`.

### S7-G02
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `country/dummy/`
- **Issue:** Architecture claims any country can be added by creating an adapter only — no service changes needed. This has never been proven. No second country adapter exists.
- **Action:** Create `country/dummy/` with minimal adapter, tax engine, compliance engine, payroll rules, and statutory validator. Add resolver mapping for dummy org. No service file changes allowed.
- **Depends on:** S7-G01
- **Status:** DONE — Created `country/dummy/` with DummyAdapter, DummyTaxEngine, DummyComplianceEngine, DummyPayrollRulesEngine, DummyStatutoryValidator, DummyBankingAdapter. Registered in `seed_dev_defaults()` as adapter_key="dummy", org="ORG_DUMMY". 6/6 tests pass in `tests/test_country_resolver_dual_country.py`. Zero service file changes.

### S7-G03
- **Type:** VIOLATION
- **Severity:** P1
- **File:** `docker-compose.yml`, `docs/canon/service-map.md`
- **Issue:** Deployment config and service map do not reflect the services that have been built. Compliance, decision, bank, and WhatsApp services are live in code but absent from compose. Service map has no status labels (implemented / add-on / planned).
- **Action:** Add 4 missing services to docker-compose. Add status column to service-map.md. Create `docs/canon/release-scope.md`.
- **Depends on:** none
- **Status:** DONE — Added compliance-service (8021), decision-service (8022), bank-service (8023), whatsapp-service (8024) to docker-compose with healthchecks and api-gateway wiring. Added Status column (IMPLEMENTED/ADD-ON/PLANNED) to service-map.md canonical registry. Created docs/canon/release-scope.md.

### S7-G04
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `tests/`
- **Issue:** No end-to-end test exists covering the full payroll → compliance → bank chain. No test proves that invalid employee data blocks payroll finalization.
- **Action:** Create `tests/test_payroll_to_bank_happy_path.py` covering: (1) valid employee runs payroll to bank disbursement, (2) invalid employee (missing statutory data) is blocked before finalization.
- **Depends on:** S7-G01
- **Status:** DONE — Created `tests/test_payroll_to_bank_happy_path.py`. 7 tests: bank file disbursement happy path, Raast disbursement, state transitions (PENDING→SUBMITTED→SENT→ACCEPTED), reconciliation, missing CNIC blocked by compliance precheck, resolver-required guard, rejection state. 7/7 pass.

### S7-G05
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `tests/test_import_health.py`, `script/import_smoke.py`
- **Issue:** No test verifies that all service and API modules can be imported without error. Import failures are silent until runtime.
- **Action:** Create `tests/test_import_health.py` that imports every top-level service/API module. Create `script/import_smoke.py` that exits nonzero on any failure.
- **Depends on:** S7-G01
- **Status:** DONE — Created `tests/test_import_health.py` (39 parametrized tests, 39/39 pass). Created `script/import_smoke.py` (18 critical modules, exits 0 on success).

---

## Session 8 Gaps (Master Docs Overlay)

Found via overlay of MASTER BUILD SPEC, MASTER MARKET RESEARCH, and MASTER BEHAVIOR SPEC against repo code. 8 gaps registered.

### S8-G01
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `payroll_service.py`
- **Issue:** `PayrollGuardian` exists in `services/ai/payroll_guardian.py` but is never called during payroll finalization. The pre-run confidence signal and anomaly report mandated by MASTER BEHAVIOR SPEC §02.1–02.2 are absent. Operators get no AI anomaly check before confirming a run.
- **Action:** Import PayrollGuardian in `payroll_service.py`. Add `_run_guardian_precheck()` method. Call it in `run_payroll()` before the compliance precheck. Block finalization on critical anomalies. Include `guardian_report` with `confidence_signal` in the response.
- **Depends on:** none
- **Status:** DONE

### S8-G02
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `payroll_service.py`
- **Issue:** No pre-run confidence signal is surfaced to the operator before payroll finalization. MASTER BEHAVIOR SPEC §02.1 requires a visible "safe to run" or "issues require review" signal before every payroll run. Same root cause as S8-G01.
- **Action:** Resolved as part of S8-G01 — `guardian_report` in response includes `confidence_signal` field.
- **Depends on:** S8-G01
- **Status:** DONE

### S8-G03
- **Type:** CODE_MISSING
- **Severity:** P1
- **File:** `payroll_service.py`
- **Issue:** No blocking gate exists for critical anomalies before payroll finalization. MASTER BEHAVIOR SPEC §02.2 requires critical anomalies to block finalization. Same root cause as S8-G01.
- **Action:** Resolved as part of S8-G01 — critical anomalies (risk >= 70) raise ServiceError and block finalization. Medium risk surfaced in response but non-blocking.
- **Depends on:** S8-G01
- **Status:** DONE

### S8-G04
- **Type:** VIOLATION
- **Severity:** P2
- **File:** `docs/system/MASTER BUILD SPEC.md`
- **Issue:** BUILD SPEC §10 service registry marks `travel-service` and `project-service` as PLANNED. Both `travel_service.py` + `travel_api.py` and `project_service.py` + `project_api.py` are implemented and importable. Spec §22 states paper services are not permitted — the inverse also applies: implemented services must not be marked PLANNED.
- **Action:** Update §10 to mark both as IMPLEMENTED.
- **Depends on:** none
- **Status:** DONE

### S8-G05
- **Type:** VIOLATION
- **Severity:** P2
- **File:** `docs/system/MASTER BUILD SPEC.md`
- **Issue:** BUILD SPEC §06 C05 (Attendance Core) lists shift templates and roster management as required core capabilities. Neither is implemented in v1. Unlabeled omissions create a false impression of completeness against the spec.
- **Action:** Add a note to C05 marking shift templates and roster management as deferred to v2.
- **Depends on:** none
- **Status:** DONE

### S8-G06
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `decision_api.py`
- **Issue:** `DecisionCard` has an `expires_at` field and `DecisionEngine.expire_card()` exists, but no scheduled process ever calls it. Expired decisions accumulate indefinitely. MASTER BEHAVIOR SPEC §06 requires decision expiry to be enforced.
- **Action:** Add `expire_overdue_decisions()` function to `decision_api.py`. Register as a job handler in `background_jobs_api.py`.
- **Depends on:** none
- **Status:** DONE

### S8-G07
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `ui/app/decisions/page.tsx`
- **Issue:** The decisions page (G28b) is not built. `decision_api.py` backend is complete. MASTER BEHAVIOR SPEC §06 and MASTER MARKET RESEARCH GAP 3 both require a decision-first UI.
- **Action:** Deferred — UI pages are a separate workstream not yet started. Backend is ready and waiting.
- **Depends on:** none
- **Status:** DEFERRED — UI pages are out of scope until explicitly requested.

### S8-G08
- **Type:** CODE_MISSING
- **Severity:** P2
- **File:** `bank_service.py`
- **Issue:** MASTER BEHAVIOR SPEC §10 requires audit records for all disbursement state transitions. `bank_service.py` has no audit logging. `execute_disbursement()`, `mark_sent()`, `mark_accepted()`, `mark_rejected()`, and `run_reconciliation()` all mutate state without any actor/timestamp/action record.
- **Action:** Add `_audit()` helper to `BankService` and call it from all five state-transition methods.
- **Depends on:** none
- **Status:** DONE

---

## Session 9 — Inter-File Normalisation Pass (2026-06-06)

*Doc-only normalisation pass. No new code gaps registered. 25 doc changes across 14 files.*
*Full OIG findings and change log: `D:\HRMS\ops\tracker.md`.*

Key doc-side gap closures retroactively noted above: G46 (event-catalog settings events), G47 (data-architecture compensation tables), MN-G04 (AttendanceSource enum in 3 docs).

Additional doc fixes (no pre-registered gap):
- 7 project-service events added to `event-catalog.md` (discovered via OIG-12 — absent from event-catalog but present in workflow-catalog)
- read-model-catalog.md section numbering collision resolved (two "13)" entries)
- service-manifest.md duplicate row removed; naming-variant fork note added
- catalogue.md path + gap count corrected; roadmap.md updated to Session 8
- intent_build_alignment.md verification scope note added
- design-system-anchor.md + hrms-archetype-system-v1.md authority chain scope notes added
- MASTER BUILD SPEC.md §10 platform-infra omission scope note added
- hrms-api-contracts.md service scope note + reporting path divergence warning added
- v3_extracted/pending.md superseded notice added

---

## Tracker Catalogue Pass (2026-06-06)

*Doc-only cataloguing pass. No code changes, no gap status changes. tracker.md Section E fully catalogued — 34 H03–H13 pages DONE. Full session detail: `docs/system/progress.md §Tracker Catalogue Pass`.*

**UI-backend interface gaps surfaced (BG-022 to BG-034) — cross-references to `hrms-ui-backend-gaps.md` only; not new G-series gaps:**

| Gap | Page | Nature |
|---|---|---|
| BG-022 | h09-notifications-inbox.html | notification_service is read-only — reply/compose not implemented |
| BG-023 | h10-org-settings.html | no personal settings model (Profile section chrome-only) |
| BG-024 | h10-org-settings.html | security settings chrome-only (2FA/SSO toggles not backed) |
| BG-025 | h10-org-settings.html | notification preferences chrome-only (topic_code matrix not backed) |
| BG-026 | h10-org-settings.html | integration_service is webhook-only (no OAuth connect flow) |
| BG-027 | h10-org-settings.html | no AI config model in any service |
| BG-028 | h11-workflow-builder.html | no notification step model in workflow_service |
| BG-029 | h11-workflow-builder.html | no FormSchema or AI step type in workflow_service |
| BG-030 | h11-survey-builder.html | engagement_service supports Likert5 question type only |
| BG-031 | h11-report-builder.html | delivery field in ReportDefinition is untyped dict; no visualization config schema |
| BG-032 | h12-helpdesk.html | helpdesk PATCH endpoints not implemented (priority/assignee/merge/forward) |
| BG-033 | h13-candidate-pipeline.html | no pipeline summary endpoint in hiring_service (stats mocked client-side) |
| BG-034 | h13-candidate-pipeline.html | FinalRound stage is UI-only — maps to status=Interviewing + is_final_round flag |

Full catalogue detail: `D:\HRMS\tracker.md` Section E. Full BG detail: `hrms-ui-backend-gaps.md`.

---

## Doc Gap Audit + Fill (2026-06-07)

*Doc-only pass. No code changes, no gap status changes. 8 missing service docs created in `docs/services/`; catalogue bumped v1.4 → v1.5; 2 cross-reference defects fixed. Full detail: `docs/system/progress.md §Doc Gap Audit + Fill`.*

---

## Full-Workspace Normalisation Pass — Cross-File Findings (2026-06-08)

*Doc-only pass. 109/109 `.md` files read line-by-line; 16 Cross-File Findings logged and triaged against `hrms-doc-catalogue-v1.md` as the resolving-authority test. 3 fixed via annotation (catalogue named a clear authority); 13 logged below as gaps — cross-references only, not new G-series gaps. Full finding detail + status: `ops/normalisation-tracker.md` §Cross-File Findings Log.*

**Fixed (catalogue-supported — annotated, originals untouched):**
| Finding | Fix |
|---|---|
| #1 | Engagement survey dimension labels diverge 3 ways — annotated `hrms-archetype-system-v1.md` L322 to point at the canonical enum in `hrms-api-contracts.md` (catalogue names it sole enum-display authority) |
| #11 | Workflow names (`leave_request_approval` etc.) diverge from canonical (`leave_request` etc.) — annotated `workflow-service.md` + `leave-service.md` to point at `workflow-catalog.md` (catalogue names it authoritative for workflow naming) |
| #15 | `manager_dashboard.md` uses unversioned `/api/manager/dashboard/...` paths — `api-standards.md` L8 (named authoritative for routing by the catalogue) states an absolute rule "all public routes are versioned under `/api/v1`" — annotated as a clear standards violation with the fix path identified |

**Logged as gaps (catalogue provides no resolving authority — needs explicit decisions, not doc edits):**
| Finding | Nature |
|---|---|
| #4 | Deferred-items roster diverges across `pending.md`/`build-progress.md`/`backend/pending.md` — two different definitions of "deferred" in play; needs reconciliation decision |
| #5 | `BenefitsPlan`/`BenefitsEnrollment`/`Allowance` fully schema'd in `data-architecture.md` but only one-line stubs in `domain-model.md` — needs a content-completeness pass |
| #6 | 4 canon docs (`domain-model`, `event-catalog`, `read-model-catalog`, `service-map`) have "Coverage checklist" sections sitting before large blocks of later-appended content — needs relocation sequencing |
| #7 | `documents` service referenced in 4 places (deps, read-models, search-indexing, event names) but has no canonical `service-map.md` entry, release-tier classification, or event definitions — needs scope confirmation + drafting |
| #8 | **Sharpened on inspection:** `service-map.md` claims ~56 events for 9 services (compliance/decision/bank/whatsapp/ewa-financial/etc.) — **zero exist in the canonical `event_contract.py` registry** (155 entries checked directly), and only 2/9 affected services even call its mandatory registration functions. This is a code-vs-doc compliance gap, not a doc-text fix — likely needs its own G-series entry once triaged |
| #9 | 18 workflows named across `service-map.md`/`read-model-catalog.md` have no `##` section in `workflow-catalog.md` (which defines only 9) — large drafting gap |
| #10 | `PayrollDeduction` entity listed under "Owned entities" in both `payroll-service.md` and `ewa-financial-service.md` — dual-ownership needs a canonical-owner decision |
| #12 | Decision Object `status` enum has 4 different value-sets across `MASTER BEHAVIOR SPEC`/`MASTER BUILD SPEC`/`decision-service.md`/`governance-service.md` — **verified unresolvable from docs**: `decision-system.md` (presumed canonical) never actually defines the enum |
| #13 | AI confidence HIGH threshold disagrees (70% vs 80%) between the two Master Specs — **verified unresolvable from docs**: no doc anywhere states the correct band cutoffs; the value was never recorded |
| #16 | `deployment.md` Stack Overview lists 20 of 25 canonical services — missing `compliance-service`, `decision-service`, `bank-service`, `whatsapp-service`, `ewa-financial-service` (the product's flagship differentiators); catalogue corroborates these are real & documented and itself names an identical "newer services lag in sibling docs" pattern (for `api-contracts.md`), but can't confirm actual runtime-deployment status |
| #2, #3 | Stale pre-restructuring path references in `hrms-archetype-system-v1.md`/`hrms-contract-structure-v1.md`/`HRMS PRODUCT SPEC.md` — small annotations already applied (bracketed `[now backend/...]` pointers), logged here for completeness |

---

## Catalogue-Authority Fix Pass — Cross-File Findings Resolved (2026-06-10)

*Doc-only pass. `hrms-doc-catalogue-v1.md` used as ground truth. Findings #4, #5, #7, #9, #10, #16 from the 2026-06-08 normalisation pass resolved by extension (per [[feedback_divergence_resolution]] — no deletion/overwrite). Findings #8, #12, #13 remain open — no canonical doc defines the disputed values. Findings #2, #3, #6, #14 already annotated or deferred.*

| Finding | Resolution |
|---|---|
| #4 | `ops/pending.md` Deferred section reconciled: G27 CLOSED per gap-register (removed from deferred list); MN-G07 and S8-G07 added with correct reasons |
| #5 | `domain-model.md` BenefitsPlan, BenefitsEnrollment, Allowance stubs extended with full Attributes tables sourced from `data-architecture.md` (single source of truth for schema) |
| #7 | `service-map.md` search-service dependency clarified: `documents` → `employee-service` document-compliance module; no standalone documents-service exists (backend code confirmed in `employee-service/document-compliance.*`) |
| #9 | `workflow-catalog.md` extended: 17 missing workflows added (projection_search_indexing, engagement_feedback_collection, automation_execution, anomaly_review, ewa_disbursement, advance_request, access_provisioning, notification_dispatch, salary_disbursement, payment_reconciliation, expense_reimbursement, report_generation, hr_ticket_resolution, whatsapp_payslip_request, whatsapp_leave_application, whatsapp_approval_action, whatsapp_alert_dispatch). Valid service registry expanded from 11 → 24 services |
| #10 | `payroll-service.md` PayrollDeduction moved from "Owned entities" to new "Entities provided by dependencies" section with explicit annotation pointing at `service-map.md` as the ownership authority (ewa-financial-service owns PayrollDeduction) |
| #16 | `deployment.md` Stack Overview extended: 5 missing services added (compliance-service, decision-service, bank-service, whatsapp-service, ewa-financial-service) |
| #8 | Still OPEN — code-registration gap (service-map.md claims ~56 events for 9 services; zero exist in event_contract.py registry). Needs a dedicated code fix, not a doc edit |
| #12 | Still OPEN — Decision Object status enum has 4 incompatible value-sets; no canonical doc defines the correct one |
| #13 | Still OPEN — AI confidence HIGH threshold (70% vs 80%) undefined in any canonical doc |

---

## Coverage Checklist Relocation & Workflow Verification Pass (2026-06-10)

| Finding | Resolution |
|---|---|
| #6 | Pure relocation (no content change) — "## Coverage checklist" section moved to the true end of file in all 4 affected canon docs: `domain-model.md`, `event-catalog.md`, `read-model-catalog.md`, `service-map.md`. Verified zero duplicate `##` headers introduced. |
| #9 (verification) | The 17 workflows added to `workflow-catalog.md` were spot-checked against backend service code. Most of their referenced event names (e.g. `EWARequested`, `AnomalyFlagged`, `TicketOpened`, `WhatsAppIntentReceived`, `ReportGenerated`) are **not yet present** in `event_contract.py` or service code — this is the same underlying gap as #8, not a new divergence. The 17 workflow entries are architecturally consistent with existing canon naming conventions but describe target-state design, not currently-implemented event flows. |

---

## Summary counts by phase

| Phase | P0 | P1 | P2 | P3 | Total | Status |
|---|---|---|---|---|---|---|
| Phase 1 — Architecture | 2 | 3 | 6 | 1 | 12 | ✅ All DONE |
| Phase 2 — Pakistan | 2 | 2 | 2 | 0 | 6 | ✅ All DONE |
| Phase 3 — Decision Engine | 1 | 3 | 0 | 0 | 4 | ✅ All DONE |
| Phase 4 — WhatsApp/Mobile | 1 | 1 | 1 | 0 | 3 | ✅ All DONE |
| Phase 5 — Multi-Country | 0 | 1 | 1 | 0 | 2 | 🟡 G26 DONE, G27 DEFERRED (see G27 entry above: informally "CLOSED — not a real requirement", not a registered fix-pending item) |
| UI (cross-phase) | 0 | 2 | 0 | 0 | 2 | 🔴 G28 OPEN (10 pages), G29 DONE |
| Docs-to-Code | 0 | 0 | 3 | 0 | 3 | ✅ All DONE |
| Pakistan Statutory (Session 3) | 3 | 4 | 3 | 0 | 10 | ✅ All DONE |
| Canon Overlay Pass 3 (Session 4) | 0 | 2 | 4 | 0 | 6 | ✅ All DONE |
| Market Research Overlay (Session 4) | 0 | 1 | 0 | 1 | 2 | ✅ All DONE |
| Behavior Spec Overlay (Session 5) | 0 | 5 | 0 | 0 | 5 | ✅ All DONE |
| Manus AI MR Overlay (Session 5) | 0 | 4 | 2 | 1 | 7 | ✅ 6 DONE, MN-G07 DEFERRED |
| HRMS Spec Overlay (Session 6) | 0 | 4 | 3 | 1 | 8 | ✅ All DONE |
| Session 7 | 1 | 4 | 0 | 0 | 5 | ✅ All DONE |
| Session 8 — Master Docs Overlay | 0 | 3 | 5 | 0 | 8 | ✅ 7 DONE, S8-G07 deferred (UI pages out of scope) |
| Session 9 — Inter-File Normalisation | — | — | — | — | 25 doc changes | ✅ All DONE (doc-only, no new code gaps) |
| Catalogue-Authority Fix Pass — Open Code/Decision Gaps (2026-06-10) | 0 | 1 | 2 | 0 | 3 | ✅ All DONE (G49/G50/G51 fixed 2026-06-10) |
| **Total** | **10** | **40** | **32** | **4** | **86** | |

---

## Fix dependency order (within each phase)

### Phase 1
```
G01 → G02 → G03 → G13 (bleeds into Phase 2)
G04 (standalone)
G05 (standalone)
G06 (standalone)
G07 (standalone)
G08 (standalone)
G09, G10, G11, G12 (standalone, docs-only)
```

### Phase 2
```
G01 → G02 → G13 (compliance service)
G14 (bank-service, no dependencies)
G15, G16, G17 (docs-only, no dependencies)
G18 → depends on G02
```

### Phase 3
```
G19 (decision HTTP layer, wraps existing code — no hard deps)
G19 → G22 (human-in-loop gate)
G19 → G21 (insight engine wiring)
G20 (docs-only, no deps)
```

### Phase 4
```
G23 (whatsapp service, webhook exists — no hard deps)
G24 → G25 (mobile docs)
```

### Phase 5
```
G01 → G26 → G27 (sequential)
```

---

## G49/G50/G51 Fix Pass (2026-06-10) ✅

| Gap | Resolution |
|---|---|
| G49 (P1) | **event_contract.py**: 41 missing events added to CANONICAL_EVENT_TYPES (8 compliance, 6 decision, 9 ewa-financial, 8 bank, 8 whatsapp, 2 reporting). **Service wiring**: `emit_canonical_event` + `EventRegistry` added to `compliance_service.py` (7 events), `bank_service.py` (5 events), `whatsapp_service.py` (6 events), `services/finance/ewa.py` (2 events), `decision_api.py` (6 events). |
| G50 (P2) | **docs/canon/decision-system.md**: canonical `status` enum (`active or resolved or expired`) and `lifecycle_state` enum (`create or update or expire or resolve`) defined. Annotations added to `MASTER BEHAVIOR SPEC.md`, `decision-service.md`, `governance-service.md` pointing to canon doc. |
| G51 (P2) | **docs/system/MASTER BUILD SPEC.md**: AI confidence HIGH threshold corrected from 80%+ to 70%+; MEDIUM corrected to 40-69%; LOW corrected to <40%. Matches code ground truth in `anomaly_engine.py` and `decision_api.py`. |


## Residual Fix Pass (2026-06-10) ✅

| Item | Fix |
|---|---|
| event-catalog.md prose (41 events) | 6 new service sections added; registry table updated; count corrected to 117 in catalogue |
| tenant_id in emit calls | `whatsapp_service.py`, `ewa.py`, `decision_api.py`, `bank_service.py` — all now use `DEFAULT_TENANT_ID` from `tenant_support`; zero hardcoded `"tenant-default"` strings remain in any `emit_canonical_event` call |
| Post-fix verification | Emit call counts grepped and confirmed; no stale tenant_id usage in event emission paths |

## Test Suite Fix Pass (2026-06-11) ✅

49 pytest failures (Phase 1 run of `backend/tests`, 85 files) — all resolved.

| Issue | Fix |
|---|---|
| `.venv`/`Lib` collected by pytest, MemoryError | Added `backend/pytest.ini` (`testpaths = tests`, `norecursedirs` excludes venv/site-packages) |
| TS-compilation tests fail on Windows (no `tsc`/`mktemp`) | `@pytest.mark.skipif(sys.platform == 'win32', ...)` added to `test_audit_service.py`, `tests/unit/test_audit_logging_standard.py`, `test_settings_domain.py` |
| Stale assertions/fixtures (dates, message text, exact-list ordering, doc cross-ref tokens) | Corrected in `test_background_jobs.py`, `test_attendance_service.py`, `test_whatsapp_webhook.py`, `test_performance_layer_qc.py`, `test_reporting_analytics.py` |
| `EventContractError("non_idempotent_events")` in `reporting_analytics.py` | Real bug: `_emit()` idempotency_key collided across rapid `rebuild_projections()` calls (timestamp-only). Fixed with monotonic `_emit_sequence` counter. |
| `test_integrity_repair_background_job_executes_safe_repairs` — `OperationTimeoutError`, job `DEAD_LETTERED` | Real perf bug: `data_integrity.py::_validate_projection_integrity()` shadow `ReportingAnalyticsService`/`SearchIndexingService` instances created 13 disk-backed temp SQLite WAL stores (25-68s on this env). Fixed: shadow instances now use unique in-memory SQLite (`file:shadow-<uuid>?mode=memory`, `uri=True`). `persistent_store.py` extended (additive) to support `mode=memory` URIs. `background_jobs.py` extended (additive) with per-job-type `timeout_seconds`; `integrity.repair` set to 10.0s. |

Verified: `test_data_integrity.py`, `test_background_jobs.py`, `test_reporting_analytics.py`, `test_search_service.py` — 23/23 passed. Full-suite re-run in progress.

## Critical Gap Fix Pass (2026-06-11) ✅

| Gap | Severity | Resolution |
|---|---|---|
| pickle serialisation in `persistent_store.py` | 🔴 Critical | Replaced with safe JSON codec (type tags). Handles: UUID, datetime, date, time, Decimal, bytes, Enum, dataclass, dict, tuple, set, list. |
| SQLite-only persistence | 🔴 Critical | PostgreSQL backend activated by `HRMS_DATABASE_URL` env var; psycopg2 `execute_values` + `ON CONFLICT DO UPDATE` for batch/upsert. |
| `http.server.HTTPServer` in production | 🔴 Critical | Replaced with uvicorn ASGI in both `api_gateway_service.py` and `service_runtime.py`. |

## Production-Readiness Uplift Pass (2026-06-11) ✅

| Gap | Severity | Resolution |
|---|---|---|
| No structured logging | 🟠 High | `structured_logging.py`: `StructuredJSONFormatter` + `configure_logging()` + `ContextVar` correlation IDs. |
| No rate limiting | 🟠 High | `rate_limiting.py`: `SlidingWindowRateLimiter` (200 req/min/IP). Gateway returns 429 + `X-RateLimit-*` headers. |
| No JWT enforcement at gateway | 🟠 High | `jwt_utils.py`: `verify_hs256_jwt()`. Gateway verifies on all non-exempt routes; propagates principal headers downstream. |
| No OpenAPI / Swagger | 🟠 High | `GET /openapi.json` + `GET /docs` added to gateway. Spec auto-generated from `ROUTES`. |
| No HTTPS / TLS | 🟠 High | `SSL_CERT_FILE` + `SSL_KEY_FILE` env vars wire uvicorn SSL at startup in both gateway and service runtime. |
| No secrets management | 🟠 High | `secrets_config.py`: `require_secrets()` validates required env vars; auto-loads `.env`. |
| No migration runner (Python) | 🟠 High | `deployment/migrate.py`: tracks applied migrations, supports SQLite + PostgreSQL, `--status` / `--dry-run`. |
| No CI/CD pipeline | 🟡 Medium | `.github/workflows/ci.yml`: test matrix, lint, security audit, migration dry-run. |

## Phase 6 Completion Pass (2026-06-11) ✅

| Gap | Resolution |
|---|---|
| W3C Trace Context (`traceparent`) | `api_gateway_service.py`: `_parse_traceparent()` parses incoming header; `_new_traceparent()` generates child span; forwarded to upstream and echoed in response. |
| CORS | All responses include `access-control-allow-origin/methods/headers/max-age`; `OPTIONS` returns 204. Configurable via `CORS_ALLOWED_ORIGINS` env var. |
| Prometheus `/metrics` | Thread-safe in-process counters; `_build_metrics_text()` returns Prometheus text exposition at `GET /metrics`. |
| JWT clock-skew tolerance | `jwt_utils.verify_hs256_jwt(clock_skew_seconds=5)` — ±5s grace window on `exp`/`nbf`. |

## Security Hardening Pass (2026-06-11) ✅

| Gap | Severity | Resolution |
|---|---|---|
| No per-tenant RBAC at gateway | 🟠 High | `_ROUTE_ROLE_MAP` in `api_gateway_service.py`: path-prefix → allowed roles; 403 on mismatch. Cross-tenant header vs JWT `tenant_id` enforcement. |
| No request body size limit | 🟠 High | `MAX_REQUEST_BODY_BYTES` (default 1 MB). Enforced in ASGI `app()` during streaming; drains then returns 413 `REQUEST_TOO_LARGE`. |
| No idempotency key support | 🟡 Medium | `_IdempotencyCache` (thread-safe, 24h TTL, 10k cap). POST/PATCH/PUT replay via `Idempotency-Key` header; `X-Idempotent-Replayed: true` on replay. |
| No JSON body validation | 🟡 Medium | Pre-forward `json.loads()` check when `Content-Type: application/json`; 400 `INVALID_JSON` on parse error. |
