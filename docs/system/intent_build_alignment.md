# Intent ↔ Build ↔ Runtime Alignment (Final Convergence Snapshot)

Date: 2026-03-31

## Objective

Capture the final, evidence-backed alignment state across intent, build artifacts, runtime handlers, gateway routing, and executable test coverage.

## Validation scope

This convergence pass re-audits and revalidates:

1. Service topology declarations and runtime handler bootability.
2. Gateway public route inventory and upstream translation behavior.
3. Runtime executability for each declared public gateway route.
4. Canon + documentation consistency after stale alias/mapping cleanup.
5. Regression and QC/RE-QC gates.

## Convergence changes applied

- Removed stale singular gateway aliases for project/workflow/integration/automation surfaces.
- Removed dead `jobs` gateway mapping that targeted the gateway itself and was not a valid executable public domain route.
- Updated compatibility/route tests to enforce canonical plural route policy and reject removed stale aliases.
- Expanded end-to-end alignment test coverage so every currently declared public gateway route is translated and executed against a real runtime handler.

## Verified evidence executed on 2026-03-31

- `pytest -q` completed successfully: `281 passed`, `70 subtests passed`.
- `python deployment/qc_validate.py` returned `QC score: 11/11`.
- RE-QC checks passed:
  - `python deployment/re_qc_validate_master_certification.py` (`5/5`)
  - `python deployment/re_qc_validate_addon_convergence.py` (`5/5`)
  - `python deployment/re_qc_validate_data_integrity.py` (`6/6`)

## Status by alignment layer

| Layer | Current status | Evidence basis | Interpretation |
| --- | --- | --- | --- |
| Service topology completeness | **Complete** | Runtime bootability test validates each declared domain service exposes executable runtime handlers. | Every declared domain service is runnable in the service runtime model. |
| Gateway route inventory | **Complete** | Route inventory now contains canonical executable public domains only (stale aliases/mapping removed). | Public route registry is canonical and non-ambiguous. |
| Gateway-to-runtime executability | **Complete** | End-to-end alignment test executes all declared public gateway routes through translation + runtime handler matching. | Every declared public route is executable through gateway forwarding logic. |
| Regression / quality gates | **Complete** | Full pytest and QC/RE-QC gates pass. | Alignment is preserved under repository-wide verification. |

## Alignment decision

**Status: FULLY ALIGNED (verified)**

This declaration is made only after explicit convergence verification across all three required dimensions:

- gateway route declarations
- runtime service handler executability
- service topology/runability

All are now verified and mutually consistent in this snapshot.

---

## Country-layer alignment update (2026-04-01)

- Implemented a country abstraction layer aligned to `docs/canon/country-layer.md` with explicit base interfaces for:
  - `TaxEngine.calculate_tax(input)`
  - `ComplianceEngine.validate_payroll(input)`
  - `ComplianceEngine.generate_reports(input)`
  - `PayrollRulesEngine.apply_rules(input)`
- Added Pakistan country adapter implementations under `country/pakistan/` and wired payroll execution through country-resolved adapter engines.
- Added `core/country_resolver.py` with org→country→adapter resolution and explicit error contracts:
  - `ORG_COUNTRY_NOT_FOUND`
  - `COUNTRY_ADAPTER_NOT_REGISTERED`
- Refactored payroll core flow so tax calculation, payroll-rule application, and compliance report generation route through the country adapter abstraction boundary rather than hardcoded core logic.

## WhatsApp integration alignment update (2026-04-01)

- Added `integrations/whatsapp/webhook.py` with:
  - `receive_message(payload)` to validate inbound webhook payloads and emit outbound provider-ready responses.
  - `parse_intent(message_text)` to map supported commands to documented intents.
- Command coverage is aligned to `docs/specs/integrations/whatsapp.md` command set for:
  - `payslip` → `payslip.get`
  - `leave` → `leave.apply`
  - `approval` → `approval.pending`
- Added focused webhook + intent tests to verify command parsing, response schema, and invalid-command help behavior.

## Pakistan integration alignment update (2026-04-01)

- Added `integrations/pakistan/` adapters aligned to `docs/specs/country/pakistan/compliance.md` submission shapes:
  - `fbr_adapter.submit_annexure_c(payload)` validates Annexure-C schema fields/constraints and simulates API submission.
  - `eobi_adapter.submit_pr01(payload)` validates PR-01 payload envelope and simulates submission.
  - `pessi_adapter.submit_contribution_return(payload)` validates PESSI/SESSI contribution return envelope and simulates submission.
- Added payroll disbursement exports for downstream payment execution:
  - `bank_salary.generate_salary_bank_csv(payload)` for CSV.
  - `bank_salary.generate_salary_bank_excel_rows(payload)` for Excel-friendly row structure.
  - `raast_payment.build_raast_payment_export(payload)` for Raast batch transaction export.
- Added accounting integration contract and stubs under `integrations/accounting/base.py`:
  - `AccountingAdapter` interface.
  - `QuickBooksAdapter` and `SAPAdapter` stub implementations.
- Added biometric ingestion adapter `integrations/biometric/device_adapter.py` to normalize device logs for attendance workflows.
- Added integration tests to verify adapter callability, simulated submissions, and compliance-payload compatibility generated from `PakistanComplianceService.generate_reports`.

## HR Copilot decision alignment update (2026-04-01)

- Added `services/ai/hr_copilot.py` to answer canonical HR assistant prompts:
  - `salary breakdown`
  - `leave balance`
  - `tax explanation`
- Enforced role-based access controls for query execution (`Admin`, `HR`, `Payroll`, `Manager`) and explicit denial for unauthorized roles.
- Ensured explainability by returning a dual-output contract for each query:
  - `answer`: direct response value for the requested HR question.
  - `explanation`: traceable calculation/policy rationale grounded in source data.
- Implemented responses that combine payroll and compliance datasets so outcomes are both financially and policy aligned.
- Added focused tests validating answer correctness, explanation presence, and unauthorized access denial.

## Predictive analytics alignment update (2026-04-01)

- Added `services/analytics/predictive.py` with three predictive models aligned to decision-system confidence requirements:
  - `predict_attrition_risk(...)`
  - `predict_workforce_forecast(...)`
  - `predict_compliance_risk(...)`
- Enforced output contract for all predictive models with both:
  - `prediction`
  - `confidence`
- Added focused tests validating that all three models generate predictions and always include confidence, plus input validation coverage.

## Pakistan real-integration alignment update (2026-04-01, productionization pass)

- Replaced simulated Pakistan compliance adapter submissions with config-driven HTTP integrations:
  - `integrations/pakistan/fbr_adapter.py`
  - `integrations/pakistan/eobi_adapter.py`
  - `integrations/pakistan/pessi_adapter.py`
- Added shared HTTP transport `integrations/http_client.py` with:
  - timeout controls
  - retry policy (attempts + backoff + retryable status codes)
  - provider error normalization (`IntegrationHTTPError`)
- Enforced strict payload validation against Pakistan compliance document shapes:
  - Annexure-C validation in FBR adapter
  - PR-01 envelope validation in EOBI adapter
  - contribution return envelope validation in PESSI adapter
- Implemented request-signing support for FBR (`X-Signature`) when signing secret is configured.
- Implemented response validation + mapped error contracts in all adapters.
- Upgraded accounting connectors:
  - QuickBooks: real API client flow to create journal entries via configurable realm endpoint.
  - SAP: structured connector interface (`SAPConnectorConfig` + executable adapter contract) with real transport path.
- Finalized payment exports for production readiness:
  - bank salary CSV/Excel generators now validate required fields and PK IBAN + amount rules.
  - Raast export now validates payment rows and emits normalized amounts.
- Implemented biometric ingestion adapter mapping for real device payload variants (`emp_code`, `event_code`, `event_time`, `terminal_id`) in addition to canonical format.
- Extended integration tests to cover success/failure scenarios and mockable HTTP client behavior across Pakistan adapters and accounting connectors.

## Mobile experience alignment update (2026-04-01)

- Added a dedicated mobile contract layer under `mobile/` with API-driven screen endpoints for:
  - dashboard (decision cards only)
  - payslip view
  - leave apply
  - alerts
- Enforced decision-first UX for mobile payloads by returning action cards first and excluding non-action/report-heavy fields.
- Enforced low-bandwidth constraints with compact JSON serialization + gzip/base64 wire payload encoding metadata (`raw_size_bytes`, `compressed_size_bytes`).
- Added pagination-first response envelopes (cursor/next cursor/limit/count) and strict minimal-field projections to avoid heavy data responses.
- Implemented `services/mobile_gateway.py` as an aggregator over payroll, attendance, decisions, and notifications with:
  - lightweight endpoint-specific payload shaping
  - basic in-memory cache keyed by endpoint/page/page-size/signature
  - fallback responses when no actionable data exists
- Added focused tests for endpoint functionality, payload-size minimization/compression, decision-first rendering, and fallback/cache behavior.

## Experience/product-tier alignment update (2026-04-01)

- Added `services/product/experience.py` as the product-domain home for experience-mode and tier feature policy.
- Standardized tier identifiers to `SMB`, `MID`, and `ENTERPRISE` and enforced monotonic feature mapping.
- Updated SME Lite gating so only `payroll`, `compliance`, and `attendance` remain enabled in Lite mode.
- Kept Payroll-as-a-Service managed mode + admin override flow with SMB-deny and MID/ENTERPRISE allow policy.
- Added `services/finance/ewa.py` financial-wellness API contracts:
  - `loan_request(...)`
  - `salary_advance(...)`
- Expanded experience-layer tests to validate feature gating, tier restrictions, PaaS mode behavior, and callable financial-wellness APIs.

## Experience workflow productionization update (2026-04-01, workflow execution pass)

- Converted experience-layer runtime from mode-only flag resolution to executable workflow gating:
  - Added `services/product/tier_enforcer.py` with strict `SMB` / `MID` / `ENTERPRISE` enforcement contracts.
  - Added runtime middleware guard `services/product/middleware.py` to block advanced workflows at execution time.
- Enforced SME Lite as a restricted workflow profile:
  - Only `payroll`, `compliance`, and `attendance` workflows are executable in Lite mode.
  - Advanced workflows are denied by runtime middleware even if requested by caller payload.
- Added Payroll-as-a-Service managed flow execution in `services/payroll/paas.py`:
  - Managed payroll run workflow supports external operator mode.
  - Admin override path enforces tier gating (`MID`+ only) and reason capture.
  - Managed-flow audit entries are captured for both run and override operations.
- Exposed PaaS API handlers in `payroll_api.py`:
  - `post_paas_run_payroll(...)` for `POST /paas/run-payroll`
  - `post_paas_override(...)` for `POST /paas/override`
- Upgraded financial wellness from placeholder-only response contracts to executable EWA workflow in `services/finance/ewa.py`:
  - Salary advance request flow (`request_salary_advance`)
  - Approval workflow (`approve_salary_advance`)
  - Payroll deduction integration (`payroll_deduction_for_employee`)
- Integrated EWA deductions into payroll runtime computation in `payroll_service.py` so approved advances are deducted automatically during payroll record construction.

## Pakistan + Integration production hardening alignment update (2026-04-01, QC uplift)

- Added centralized integration runtime config layer: `config/integrations.py`.
  - Supports endpoint + credential loading.
  - Supports environment switching via `INTEGRATION_ENV` (`sandbox`/`live`).
- Upgraded Pakistan statutory adapters with production-grade submission handling:
  - `integrations/pakistan/fbr_adapter.py`
  - `integrations/pakistan/eobi_adapter.py`
  - `integrations/pakistan/pessi_adapter.py`
  - Added auth headers, configurable retries/timeouts, structured failure mapping.
- Added submission lifecycle tracking with payload persistence:
  - `integrations/pakistan/submission_tracking.py`
  - Status progression: `pending` → `submitted` / `failed`.
  - Request/response payloads persisted in tracker records.
- Enforced schema alignment for statutory submission formats:
  - Annexure-C validation maintained in FBR adapter.
  - PR-01 format contract enforced (`submission_format = PR-01`) and wired from compliance report generation.
- Strengthened accounting connectors:
  - QuickBooks connector uses real API POST path with config-driven endpoint/auth/retry/timeout.
  - SAP adapter remains structured connector and now resolves runtime transport settings through config layer.
- Finalized payment export validation hardening:
  - Salary bank export requires non-empty employees and validates IBAN/amount constraints.
  - Raast export requires non-empty payment set and strict amount/identifier validation.
- Expanded biometric normalization support for multiple vendor schemas:
  - Supports canonical, vendor flat, and nested device payload forms.

## Mobile product-layer execution alignment update (2026-04-01, real mobile app pass)

- Added executable mobile product layer package under `mobile/app/`:
  - `mobile/app/product.py` introduces `MobileAppService` with authenticated mobile flows.
  - `mobile/app/__init__.py` exports mobile product service entrypoint.
- Added token-based lightweight session auth under `mobile/session.py`:
  - stateless signed bearer tokens via `issue_token(...)`.
  - lightweight validation via `validate_token(...)` with explicit `TOKEN_INVALID` handling path.
- Hardened mobile contract enforcement in `mobile/contracts.py`:
  - mobile responses now explicitly mark `decision_cards_only` and `minimal_payload` contract flags.
  - compressed wire payload remains mandatory (`gzip+base64`) with size metadata.
- Upgraded `services/mobile_gateway.py` so all mobile flows return decision-card structures only:
  - dashboard, payslip, leave apply, and alerts now emit action-first decision cards.
  - payload trimming and compact card shaping preserved.
  - in-memory cache + fallback cards remain active for low-latency mobile behavior.
- Extended mobile tests in `tests/test_mobile_gateway.py` to validate:
  - decision-card-only contract on all flows.
  - low-bandwidth/compression behavior.
  - token-auth success/failure handling in mobile product layer.

## Country-agnostic statutory isolation refactor update (2026-04-01, leakage-removal pass)

- Removed hardcoded organization/country literals from service orchestration paths and standardized country routing through `country_resolver.get_adapter(organization_id)`.
- Refactored service-layer country coupling to be adapter-driven:
  - `payroll_service.py` now resolves adapter via resolver in both record construction and batch compliance execution.
  - `services/payroll_service.py` now orchestrates tax/compliance calls via resolver-selected adapter instead of direct Pakistan engine imports.
- Enforced interface naming alignment in `country/base` with explicit interfaces:
  - `TaxEngineInterface`
  - `ComplianceEngineInterface`
  - `PayrollRulesInterface`
- Consolidated Pakistan statutory logic under `country/pakistan/` by moving tax/report/compliance formulas to `country/pakistan/statutory.py` and turning `services/compliance_service.py` into a compatibility export only.
- Updated country-layer canon doc to reflect interface names and organization/legal-entity/config resolver path, removing stale hardcoded org examples from resolver/test flow references.
- Updated/expanded tests to validate adapter resolution API (`get_adapter`) and adapter-routed payroll behavior without hardcoded org/country constants in service orchestration.

## Pakistan payroll orchestration cleanup update (2026-04-01, P3)

- Refactored `services/payroll_service.py` to keep payroll as orchestration-only:
  - policy math delegated to `services/payroll_policy_engine.py`
  - tax delegated exclusively through `adapter.tax_engine.calculate_tax(...)`
  - compliance delegated exclusively through `adapter.compliance_engine.validate_payroll(...)`
- Added `services/payroll_policy_engine.py` as the shared policy execution layer for:
  - overtime tiered computation
  - penalty computation
  - shift-rule adjustments
- Updated payroll outputs to include explicit policy contributions (`shift_pay`, `penalties`) and confirmed no duplicated policy/tax/compliance logic paths.
