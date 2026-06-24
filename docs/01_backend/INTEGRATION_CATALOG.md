# INTEGRATION CATALOG

Status: Draft
Authority Level: Medium
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

Catalog of external/third-party integrations found under `D:\SaaS\HRMS\backend\integrations\`, `D:\SaaS\HRMS\backend\config\integrations.py`, and `D:\SaaS\HRMS\backend\country\pakistan\`. For each integration: name, purpose, owning service, source files, protocol, auth mechanism, and TBD markers for unverifiable details (sandbox vs. production credentials, rate limits, exact endpoint URLs).

**Evidence sources:** `backend/integrations/**`, `backend/config/integrations.py`, `backend/country/pakistan/**`, `backend/docs/canon/country-layer.md`, `backend/docs/canon/service-map.md`.

---

## 1. FBR (Federal Board of Revenue) — Annexure-C / Active Taxpayer List (ATL)

- **Purpose:** (a) Submit Annexure-C income-tax withholding statements; (b) verify employee "filer" status against FBR's public Active Taxpayer List (ATL) before payroll tax calculation.
- **Owning service:** `compliance-service` (submission), `payroll-service` (ATL filer-status check during payroll record construction).
- **Source files:**
  - `backend\integrations\pakistan\fbr_adapter.py` — validates/builds Annexure-C payloads (`_validate_annexure_c_payload`, required keys: `tax_year`, `period`, `employer`, `totals`, `employees`; employer requires `ntn`, `name`, `address`, `withholding_agent_cnic_ntn`; per-employee requires `cnic`, `tax_slab_code`, `annual_tax`, `monthly_tax_deducted`, `exemptions`, etc.)
  - `backend\integrations\pakistan\atl_adapter.py` — `verify_filer_status()`; ATL endpoint default `https://atl.fbr.gov.pk/atl/online/ATL.aspx` (public lookup), 30-day cache TTL (`_CACHE_TTL_DAYS`, in-process dict `_atl_cache`), configurable via `FBR_ATL_ENDPOINT` / `config/integrations.py` key `fbr_atl`.
  - `backend\integrations\pakistan\submission_tracking.py` — generic submission lifecycle tracker (`SubmissionTracker`, `SubmissionRecord`), lifecycle states `DRAFT → VALIDATED → SUBMITTED → ACKNOWLEDGED → FAILED → RETRY` (`LIFECYCLE_STATES`, `_ALLOWED_TRANSITIONS`).
  - `backend\config\integrations.py` — `IntegrationsConfig.fbr` loaded from env vars `PAKISTAN_FBR_{SANDBOX|LIVE}_BASE_URL`, `PAKISTAN_FBR_BASE_URL`, `PAKISTAN_FBR_AUTH_TOKEN`, `PAKISTAN_FBR_TIMEOUT_SECONDS`, `PAKISTAN_FBR_RETRY_ATTEMPTS`.
- **Protocol:** REST (JSON POST), via shared `JsonHTTPClient` (`backend/integrations/http_client.py`) with `RetryPolicy` (default 3 attempts, 0.5s backoff, retries on 408/429/500/502/503/504). ATL lookup is a GET-style public web lookup (TBD – REQUIRES VERIFICATION whether implemented as scrape vs. API; only the endpoint URL and cache behavior were confirmed).
- **Auth mechanism:** Bearer-style `auth_token` from `PAKISTAN_FBR_AUTH_TOKEN` env var, passed via `IntegrationRuntimeConfig.auth_token`. Exact header name/scheme for FBR submission: TBD – REQUIRES VERIFICATION (not shown in the portion of `fbr_adapter.py` read).
- **Environment selection:** `config/integrations.py` `_env_name()` reads `INTEGRATION_ENV` (default `"sandbox"`; only `"live"` switches to live). Both sandbox and live base-URL env vars are supported (`PAKISTAN_FBR_SANDBOX_BASE_URL` / `PAKISTAN_FBR_LIVE_BASE_URL`).
- **TBD:** Production vs. sandbox credential values, exact FBR Annexure-C submission endpoint URL, rate limits — all TBD – REQUIRES VERIFICATION (not present in repo; expected to be deployment-time secrets).

---

## 2. EOBI (Employees' Old-Age Benefits Institution) — PR-01 Submission

- **Purpose:** Submit PR-01 statutory contribution returns to EOBI.
- **Owning service:** `compliance-service`.
- **Source files:**
  - `backend\integrations\pakistan\eobi_adapter.py` — `_validate_pr01_payload()`; required top-level keys `submission_format` (must equal `"PR-01"`), `period` (with `month`/`year`), `employer` (with `registration_number`), `employees` (non-empty array). Uses `DEFAULT_SUBMISSION_TRACKER` / `SubmissionTracker` from `submission_tracking.py`.
  - `backend\config\integrations.py` — `IntegrationsConfig.eobi`, env vars `PAKISTAN_EOBI_{SANDBOX|LIVE}_BASE_URL`, `PAKISTAN_EOBI_BASE_URL`, `PAKISTAN_EOBI_AUTH_TOKEN`, `PAKISTAN_EOBI_TIMEOUT_SECONDS`, `PAKISTAN_EOBI_RETRY_ATTEMPTS`.
- **Protocol:** REST (JSON POST) via `JsonHTTPClient` + `RetryPolicy` (same shared client as FBR).
- **Auth mechanism:** Token-based via `PAKISTAN_EOBI_AUTH_TOKEN` — exact scheme TBD – REQUIRES VERIFICATION.
- **Submission lifecycle:** Tracked via shared `SubmissionTracker` (`DRAFT → VALIDATED → SUBMITTED → ACKNOWLEDGED → FAILED → RETRY`), consistent with `docs/canon/service-map.md` compliance-service lifecycle description.
- **TBD:** Exact EOBI endpoint URL, production credentials, rate limits.

---

## 3. PESSI / SESSI (Provincial / Sindh Employees Social Security Institution) — C-1 Contribution Return

- **Purpose:** Submit C-1 social security contribution returns.
- **Owning service:** `compliance-service`.
- **Source files:**
  - `backend\integrations\pakistan\pessi_adapter.py` — `submit_contribution_return()`; required top-level keys `period`, `establishment` (with `registration_number`), `employees` (array). Generates `submission_id` as `pessi_<uuid12hex>`, registers as `"PESSI_SESSI"` / `"C-1"` via `DEFAULT_SUBMISSION_TRACKER.create_pending(...)`.
  - `backend\config\integrations.py` — `IntegrationsConfig.pessi`, env vars `PAKISTAN_PESSI_{SANDBOX|LIVE}_BASE_URL`, `PAKISTAN_PESSI_BASE_URL`, `PAKISTAN_PESSI_AUTH_TOKEN`, `PAKISTAN_PESSI_TIMEOUT_SECONDS`, `PAKISTAN_PESSI_RETRY_ATTEMPTS`.
- **Protocol:** REST (JSON POST) via `JsonHTTPClient` + `RetryPolicy`.
- **Auth mechanism:** Token-based via `PAKISTAN_PESSI_AUTH_TOKEN` — exact scheme TBD – REQUIRES VERIFICATION.
- **TBD:** Exact PESSI/SESSI endpoint URL, production credentials, rate limits, whether PESSI and SESSI (which are separate provincial institutions per common Pakistan compliance practice) are handled by the same adapter or require separate config — only one adapter file (`pessi_adapter.py`) was found.

---

## 4. Raast (Pakistan Instant Payment System)

- **Purpose:** Execute Raast instant payment payouts for salary and EWA/advance disbursements.
- **Owning service:** `bank-service`.
- **Source files:**
  - `backend\integrations\pakistan\raast_payment.py` — `build_raast_payment_export()`; validates `transaction_id`, `debtor_iban` (must start with `"PK"`), `creditor_iban` (must start with `"PK"`) OR `creditor_mobile` (valid 11/12-digit mobile number per `_is_valid_mobile`), `amount` (> 0, Decimal). `_validate_batch_total()` cross-checks transaction sum against `payroll_total`. Output includes `batch_id` (default `raast-<unix-timestamp>`), `currency` (default `"PKR"`).
  - `backend\country\pakistan\banking.py` — country-layer `BankingInterface` implementation; `BankService` is documented to accept `CountryResolver` at construction and route all banking calls through `adapter.banking` (`backend/docs/canon/country-layer.md` §2.5). Not independently read in full this pass — TBD – REQUIRES VERIFICATION for exact method bodies.
- **Protocol:** TBD – REQUIRES VERIFICATION. `raast_payment.py` (lines 1-50 read) only shows payload construction/validation logic — no HTTP call to a Raast API endpoint was observed in the read portion. Whether this produces a file export (batch) for manual/separate submission, or calls a live Raast API, is TBD – REQUIRES VERIFICATION.
- **Auth mechanism:** TBD – REQUIRES VERIFICATION (no Raast-specific config block found in `config/integrations.py`, which only defines `fbr`, `eobi`, `pessi`, `quickbooks`, `sap`).
- **Validation rules confirmed:** IBAN must be Pakistani (`PK` prefix); mobile numbers must be 11 or 12 digits; transaction amounts must be positive and reconcile to `payroll_total`.

---

## 5. Bank Salary Disbursement Files (Standard / HBL Bulk / Meezan Bulk)

- **Purpose:** Generate bank-format salary disbursement export files (CSV/Excel rows) for standard bank upload, HBL bulk format, and Meezan bulk format.
- **Owning service:** `bank-service`.
- **Source files:**
  - `backend\integrations\pakistan\bank_salary.py` — `_BANK_HEADERS` dict defines column layouts for 3 formats:
    - `"standard"`: `employee_id, employee_name, bank_account, iban, net_salary, currency, payment_reference`
    - `"hbl_bulk"`: `employee_id, employee_name, iban, amount, currency, narration, payment_reference`
    - `"meezan_bulk"`: `employee_id, employee_name, account_or_iban, amount, currency, payment_reference`
  - `_validate_employee()` — requires `employee_id`, `full_name`, and either a `PK`-prefixed `iban` or non-empty `bank_account`; `net_salary` must be a positive Decimal.
- **Protocol:** File generation (CSV via `csv`/`io` modules — no network call). This is an **export/file-based** integration, not an API call.
- **Auth mechanism:** N/A (file generation only — files are presumably uploaded to bank portals out-of-band).
- **TBD:** Whether/how generated files are transmitted to HBL/Meezan (manual upload vs. automated SFTP/API) — TBD – REQUIRES VERIFICATION.

---

## 6. Payment Reconciliation (Generic)

- **Purpose:** Match payment confirmations against payroll records; produce reconciliation summary (matched, mismatches, missing payments, failures, unmatched payments).
- **Owning service:** `bank-service`.
- **Source files:**
  - `backend\integrations\pakistan\payment_reconciliation.py` — `reconcile_payroll_payments()`; `SUCCESS_STATES = {"success", "posted", "paid", "settled"}`, `FAILURE_STATES = {"failed", "reversed", "rejected", "timeout"}`. Compares `payroll` rows (by `employee_id`, expected amount from `payout`/`net_salary`) against `payments` rows.
- **Protocol:** In-process data reconciliation (no external network call) — operates on payloads already retrieved from elsewhere (likely bank statement imports or Raast confirmation callbacks).
- **Auth mechanism:** N/A.
- **TBD:** Source of the `payments` payload (manual upload, bank API pull, Raast webhook) — TBD – REQUIRES VERIFICATION.

---

## 7. WhatsApp Business API (Inbound Webhook + Command Dispatch)

- **Purpose:** WhatsApp access channel — receive inbound messages, parse intents via keyword commands, dispatch to domain services (payslip retrieval, leave application, approval actions, attendance status).
- **Owning service:** `whatsapp-service`.
- **Source files:**
  - `backend\integrations\whatsapp\webhook.py` — `CommandRegistry` class; module-level `_command_registry` pre-loaded with 4 core commands: `payslip → payslip.get`, `leave → leave.apply`, `approval → approval.pending`, `attendance → attendance.status`.
  - `backend\whatsapp_service.py`, `backend\whatsapp_api.py` — service-level implementation (not read in full this pass).
- **Protocol:** Webhook (inbound) — WhatsApp Business API delivers messages to a webhook endpoint exposed by `whatsapp-service`. Outbound message sending protocol: TBD – REQUIRES VERIFICATION (not confirmed in the read portion; `docs/canon/service-map.md` lists "WhatsApp Business API provider" as an external dependency and `notification-service` as providing "shared outbound channel").
- **Auth mechanism:** TBD – REQUIRES VERIFICATION (no WhatsApp-specific entry in `config/integrations.py`; webhook signature verification, if any, not confirmed in the 50-line read of `webhook.py`).
- **Identity/session model:** Per `docs/canon/service-map.md`, `whatsapp-service` owns `WhatsAppIdentityMap` (phone↔employee mapping with OTP verification via `auth-service`), `WhatsAppSession` (session-bound RBAC), `WhatsAppConversationEvent` (audit/analytics log).
- **Gateway exposure:** `/api/v1/whatsapp` is **CONFIRMED** as gateway route 25 (`routes.py` line 55, `gateway-routes.json` line 28 — Phase 2.8 TR-006). Non-standard response envelope: `{status, data, service}`. Inbound webhook delivery may also occur out-of-band from the API Gateway.

---

## 8. Biometric Device Adapter (Attendance)

- **Purpose:** Ingest attendance punch logs from biometric devices (check-in/check-out/break events) and normalize to a canonical event format.
- **Owning service:** `attendance-service` (consumer of normalized logs — exact integration point TBD – REQUIRES VERIFICATION).
- **Source files:**
  - `backend\integrations\biometric\device_adapter.py` — `_EVENT_MAP` normalizes raw event codes (`IN`/`OUT`/`BREAK_IN`/`BREAK_OUT`/`0`/`1`/etc.) to canonical types (`check_in`, `check_out`, `break_start`, `break_end`). `_normalize_log()` extracts `employee_id`, `event_type`, `timestamp` (ISO-8601 validated), `device_id` from flexible field-path candidates (e.g., `employee_id`, `emp_code`, `employee.code`, `user_id`). `ingest_device_logs()` returns `{status, accepted_logs, rejected_logs, logs}`.
- **Protocol:** Batch ingestion of a `logs` array (format-agnostic across device vendors via flexible field extraction) — no specific vendor API confirmed. Source `"biometric_device"` tag applied to all normalized logs.
- **Auth mechanism:** N/A / TBD – REQUIRES VERIFICATION (no config entry found; likely device-side push or file/batch upload).
- **TBD:** Specific device vendor(s) supported, transport mechanism (HTTP push from device, file import, polling) — TBD – REQUIRES VERIFICATION.

---

## 9. Accounting Export — QuickBooks

- **Purpose:** Export approved payroll journal entries / expense claims to QuickBooks Online.
- **Owning service:** `expense-service` (claims export) and/or `payroll-service`/`compliance-service` (payroll journal export) — exact owning service for the journal export call TBD – REQUIRES VERIFICATION (the adapter is generic; `docs/canon/service-map.md` describes `expense-service` as exporting "approved claims to accounting systems").
- **Source files:**
  - `backend\integrations\accounting\base.py` — `AccountingAdapter` ABC with abstract `export_payroll_journal(payload)`. `QuickBooksAdapter(AccountingAdapter)`:
    - Endpoint: `{base_url}/v3/company/{realm_id}/journalentry`
    - Config: `realm_id` from `cfg` or `QUICKBOOKS_REALM_ID` env var; `access_token` from `cfg` or `shared.auth_token`.
    - Payload: `{"Line": journal_entries, "PrivateNote": memo}`.
    - Response handling: expects `body["JournalEntry"]["Id"]`; returns `{"provider": "QuickBooks", "status": "success"|"failure", "journal_entry_id", "sync_token", ...}`.
  - `backend\config\integrations.py` — `IntegrationsConfig.quickbooks`, env vars `QUICKBOOKS_{SANDBOX|LIVE}_BASE_URL`, `QUICKBOOKS_BASE_URL`, `QUICKBOOKS_AUTH_TOKEN`, `QUICKBOOKS_TIMEOUT_SECONDS`, `QUICKBOOKS_RETRY_ATTEMPTS`, plus `QUICKBOOKS_REALM_ID`.
- **Protocol:** REST (JSON POST), QuickBooks Online API v3, via `JsonHTTPClient` + `RetryPolicy`.
- **Auth mechanism:** OAuth2 Bearer token (`Authorization: Bearer {access_token}`) — token itself sourced from `QUICKBOOKS_AUTH_TOKEN`; OAuth2 flow/refresh mechanism TBD – REQUIRES VERIFICATION (only static token usage confirmed).

---

## 10. Accounting Export — SAP

- **Purpose:** Export payroll journal entries to SAP (likely via a SAP connector/middleware).
- **Owning service:** TBD – REQUIRES VERIFICATION (same ambiguity as QuickBooks above).
- **Source files:**
  - `backend\integrations\accounting\base.py` — `SAPConnectorConfig` dataclass: `base_url`, `company_code` (from `SAP_COMPANY_CODE` env var), `auth_token`, `timeout_seconds`, `retry_attempts`. `from_env()` loads from `load_integrations_config().sap`. A corresponding `SAPAdapter`/`export_payroll_journal` implementation was not confirmed in the 40-line read — TBD – REQUIRES VERIFICATION whether a full SAP adapter class exists beyond the config dataclass.
  - `backend\config\integrations.py` — `IntegrationsConfig.sap`, env vars `SAP_{SANDBOX|LIVE}_BASE_URL`, `SAP_BASE_URL`, `SAP_AUTH_TOKEN`, `SAP_TIMEOUT_SECONDS`, `SAP_RETRY_ATTEMPTS`.
- **Protocol:** TBD – REQUIRES VERIFICATION (config dataclass present; REST assumed by convention with QuickBooks, but no confirmed request-building code read).
- **Auth mechanism:** Token-based (`auth_token` from `SAP_AUTH_TOKEN`) — exact scheme TBD – REQUIRES VERIFICATION.

---

## 11. Shared HTTP Client Infrastructure

- **Purpose:** Common HTTP client used by all integration adapters above (FBR, EOBI, PESSI, QuickBooks, SAP).
- **Source files:**
  - `backend\integrations\http_client.py` — `JsonHTTPClient` (uses Python stdlib `urllib.request`, no `requests`/`httpx` dependency — consistent with ADR-001's "minimal dependencies" principle); `RetryPolicy` (`attempts=3`, `backoff_seconds=0.5`, `retry_on_statuses=(408, 429, 500, 502, 503, 504)`); `IntegrationHTTPError` exception with `status_code`, `code`, `message`, `details`.
  - `backend\config\integrations.py` — `load_integrations_config()` returns `IntegrationsConfig(fbr, eobi, pessi, quickbooks, sap)`. Environment selection via `INTEGRATION_ENV` (default `"sandbox"`).
- **Protocol:** REST/JSON over HTTP(S), `POST` only (`post_json` is the only method observed in the 50-line read — GET support TBD – REQUIRES VERIFICATION).
- **Auth mechanism:** Per-integration bearer/token headers, constructed by each adapter individually (not centralized in `JsonHTTPClient`).

---

## SUMMARY TABLE

| # | Integration | Owning Service | Protocol | Auth | Config Source |
|---|---|---|---|---|---|
| 1 | FBR Annexure-C / ATL | compliance-service, payroll-service | REST (POST) + public lookup | Token (`PAKISTAN_FBR_AUTH_TOKEN`) | `config/integrations.py` (`fbr`), `fbr_adapter.py`, `atl_adapter.py` |
| 2 | EOBI PR-01 | compliance-service | REST (POST) | Token (`PAKISTAN_EOBI_AUTH_TOKEN`) | `config/integrations.py` (`eobi`), `eobi_adapter.py` |
| 3 | PESSI/SESSI C-1 | compliance-service | REST (POST) | Token (`PAKISTAN_PESSI_AUTH_TOKEN`) | `config/integrations.py` (`pessi`), `pessi_adapter.py` |
| 4 | Raast instant payments | bank-service | TBD – REQUIRES VERIFICATION | TBD – REQUIRES VERIFICATION | `raast_payment.py`, `country/pakistan/banking.py` |
| 5 | Bank salary export (HBL/Meezan/standard) | bank-service | File export (CSV) | N/A | `bank_salary.py` |
| 6 | Payment reconciliation | bank-service | In-process | N/A | `payment_reconciliation.py` |
| 7 | WhatsApp Business API | whatsapp-service | Webhook (inbound) + outbound via notification-service | Auth mechanism TBD – deployment secret | `integrations/whatsapp/webhook.py` |
| 8 | Biometric device ingestion | attendance-service (TBD) | Batch ingest | TBD – REQUIRES VERIFICATION | `integrations/biometric/device_adapter.py` |
| 9 | QuickBooks accounting export | expense-service (TBD) | REST (POST), OAuth2 Bearer | `QUICKBOOKS_AUTH_TOKEN` | `config/integrations.py` (`quickbooks`), `integrations/accounting/base.py` |
| 10 | SAP accounting export | TBD – REQUIRES VERIFICATION | TBD – REQUIRES VERIFICATION | `SAP_AUTH_TOKEN` | `config/integrations.py` (`sap`), `integrations/accounting/base.py` |
| 11 | Shared HTTP client | all of the above | REST/JSON (POST), stdlib `urllib` | per-adapter | `integrations/http_client.py` |

**Global TBD:** All sandbox vs. production credential values are environment-injected (`*_AUTH_TOKEN`, `*_SANDBOX_BASE_URL`, `*_LIVE_BASE_URL`) and not present in the repository — TBD – REQUIRES VERIFICATION for any specific deployment. No explicit rate-limit handling beyond `RetryPolicy.retry_on_statuses` (which includes `429`) was found for any integration — per-provider rate limits are TBD – REQUIRES VERIFICATION.
