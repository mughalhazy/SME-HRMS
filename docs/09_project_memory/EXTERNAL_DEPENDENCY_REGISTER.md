# EXTERNAL DEPENDENCY REGISTER

Layer: Project Memory
Status: Active
Created: 2026-06-18
Rule: Items in this register require external provisioning — credentials, accounts, registrations, or vendor approvals. They CANNOT be resolved from repository evidence. They DO NOT block frontend implementation (Phase 4) unless the feature is in the active sprint.

---

## Classification Criteria

An item qualifies as EXTERNAL-DEPENDENCY only if:
- Requires credentials not held by the development team
- Requires vendor account creation/approval
- Requires statutory registration with a government body
- Requires bank/payment processor onboarding

---

## §1 — FBR INTEGRATION CREDENTIALS (ED-001)

**Item ID:** ED-001
**Title:** FBR (Federal Board of Revenue) API Credentials and Registration
**Classification:** EXTERNAL-DEPENDENCY
**Current Status:** OPEN — awaiting owner provisioning
**Original Source:** INTEGRATION_CATALOG.md §FBR; Mandate 2 OWNER-REQUIRED compression
**Evidence Source:** `backend/country/pakistan/fbr.py` (implementation exists — calls FBR API); `backend/integrations/pakistan/fbr_client.py` (client configured); `docker-compose.yml` env var `FBR_API_KEY` expected
**Resolution Source:** N/A — not resolvable from repository
**Resolution Date:** NOT YET RESOLVED
**Resolved By:** N/A — requires human action
**Decision Summary:** FBR statutory tax reporting integration requires an organization-specific API key from the Federal Board of Revenue. Owner must register the organization with FBR, complete the e-Filing portal enrollment, and obtain API credentials.
**Detailed Explanation:** The implementation code (`fbr.py`, `fbr_client.py`) is complete and awaits credentials. The `FBR_API_KEY` environment variable must be populated in the production `.env` file. FBR registration is a statutory requirement for payroll compliance in Pakistan — it cannot be bypassed or mocked in production. In development/testing: mock mode is acceptable with a placeholder key.
**Affected Components:** `backend/country/pakistan/fbr.py`; `backend/integrations/pakistan/fbr_client.py`; payroll-service tax calculation
**Affected Routes:** `/api/v1/compliance` (gateway route 22); `/api/v1/payroll`
**Affected APIs:** FBR e-Filing API; compliance reports endpoint
**Affected Workflows:** WF-003 (Payroll Run — tax calculation); WF-007 (Compliance Reporting)
**Affected Roles:** PayrollAdmin, Admin
**Owner Required:** YES — statutory registration
**External Dependency:** YES — FBR government portal
**Future Impact:** HIGH — payroll tax computation and e-filing will not function in production without this credential
**Reopen Criteria:** N/A — this item IS open; closes when credentials are provisioned and `FBR_API_KEY` is set in production `.env`
**Related Documents:** `docs/01_backend/INTEGRATION_CATALOG.md` §FBR; `backend/country/pakistan/fbr.py`
**Related Register Entries:** OD-001 (launch timeline governs provisioning urgency)

---

## §2 — EOBI INTEGRATION CREDENTIALS (ED-002)

**Item ID:** ED-002
**Title:** EOBI (Employees' Old-Age Benefits Institution) API Credentials
**Classification:** EXTERNAL-DEPENDENCY
**Current Status:** OPEN — awaiting owner provisioning
**Original Source:** INTEGRATION_CATALOG.md §EOBI; Mandate 2 OWNER-REQUIRED compression
**Evidence Source:** `backend/country/pakistan/eobi.py` (implementation exists); `docker-compose.yml` env var `EOBI_API_KEY` expected
**Resolution Source:** N/A — not resolvable from repository
**Resolution Date:** NOT YET RESOLVED
**Resolved By:** N/A — requires human action
**Decision Summary:** EOBI statutory compliance (employer contribution reporting) requires organization-specific credentials from EOBI. Owner must register each client organization with EOBI and obtain API credentials.
**Detailed Explanation:** EOBI contributions are mandatory for employers with 5+ employees in Pakistan. The implementation code (`eobi.py`) is complete. The `EOBI_API_KEY` environment variable must be set per organization (multi-tenant consideration: each tenant may need separate credentials or a shared integration key depending on EOBI's multi-employer API model). In development/testing: mock mode acceptable.
**Affected Components:** `backend/country/pakistan/eobi.py`; payroll-service; compliance-service
**Affected Routes:** `/api/v1/compliance` (gateway route 22)
**Affected APIs:** EOBI API; compliance reports endpoint
**Affected Workflows:** WF-003 (Payroll Run — EOBI deduction); WF-007 (Compliance Reporting)
**Affected Roles:** PayrollAdmin, Admin
**Owner Required:** YES — statutory registration per organization
**External Dependency:** YES — EOBI government portal
**Future Impact:** HIGH — EOBI contribution calculation and reporting will not be production-valid without credentials
**Reopen Criteria:** N/A — this item IS open; closes when credentials are provisioned
**Related Documents:** `docs/01_backend/INTEGRATION_CATALOG.md` §EOBI; `backend/country/pakistan/eobi.py`
**Related Register Entries:** OD-001 (launch timeline); ED-001 (FBR — co-requisite for payroll compliance)

---

## §3 — PESSI / SESSI CREDENTIALS (ED-003)

**Item ID:** ED-003
**Title:** PESSI / SESSI (Provincial Social Security Institutions) API Credentials
**Classification:** EXTERNAL-DEPENDENCY
**Current Status:** OPEN — awaiting owner provisioning
**Original Source:** INTEGRATION_CATALOG.md §PESSI; Mandate 2 OWNER-REQUIRED compression
**Evidence Source:** `backend/country/pakistan/pessi.py` or equivalent; compliance-service references; `docker-compose.yml` env var `PESSI_API_KEY` expected
**Resolution Source:** N/A — not resolvable from repository
**Resolution Date:** NOT YET RESOLVED
**Resolved By:** N/A — requires human action
**Decision Summary:** Provincial social security (PESSI for Punjab, SESSI for Sindh, BESSI for Balochistan, KPESSI for KPK) requires province-specific employer registration. Owner must determine which provinces' clients they will serve initially and register accordingly.
**Detailed Explanation:** Social security contribution is province-specific in Pakistan. The architecture correctly isolates this in `/backend/country/pakistan/` per FD-007. The owner must decide: (1) which province(s) to launch in first, (2) register with the appropriate institution(s), (3) obtain API credentials (where available — SESSI/PESSI APIs have varying availability). Some provinces may require manual file submission rather than API integration. The implementer should verify API availability with each institution.
**Affected Components:** `backend/country/pakistan/` (provincial compliance logic); compliance-service
**Affected Routes:** `/api/v1/compliance` (gateway route 22)
**Affected APIs:** PESSI/SESSI API (province-dependent)
**Affected Workflows:** WF-003 (Payroll Run — social security deduction); WF-007 (Compliance Reporting)
**Affected Roles:** PayrollAdmin, Admin
**Owner Required:** YES — statutory registration, province selection
**External Dependency:** YES — provincial social security portals
**Future Impact:** HIGH — social security deductions and reporting require provincial registration
**Reopen Criteria:** N/A — this item IS open; closes when credentials are provisioned per province
**Related Documents:** `docs/01_backend/INTEGRATION_CATALOG.md` §PESSI; `backend/country/pakistan/`
**Related Register Entries:** OD-001 (launch timeline); ED-001 (FBR); ED-002 (EOBI)

---

## §4 — RAAST PAYMENT CREDENTIALS (ED-004)

**Item ID:** ED-004
**Title:** Raast (SBP Instant Payment) Credentials and Bank Partner Onboarding
**Classification:** EXTERNAL-DEPENDENCY
**Current Status:** OPEN — awaiting owner provisioning
**Original Source:** INTEGRATION_CATALOG.md §Raast; Mandate 2 OWNER-REQUIRED compression
**Evidence Source:** `backend/banking_api.py` (Raast endpoint call); `backend/country/pakistan/raast_payment.py` (payload construction); `docker-compose.yml` env var `RAAST_API_KEY` / `RAAST_BANK_CODE` expected; EWA architecture uses Raast for payouts
**Resolution Source:** N/A — not resolvable from repository
**Resolution Date:** NOT YET RESOLVED
**Resolved By:** N/A — requires human action
**Decision Summary:** Raast instant payment integration requires onboarding through a participating bank (Raast is an SBP infrastructure; access is via a member bank's API). Owner must select a bank partner, complete onboarding, and obtain Raast API credentials.
**Detailed Explanation:** Raast is the State Bank of Pakistan's instant payment infrastructure. Direct SBP API access is only available via member banks (e.g., HBL, UBL, MCB, Meezan). The owner must: (1) select a bank partner, (2) open a corporate account if not already held, (3) complete the bank's business onboarding for Raast bulk disbursement, (4) obtain API credentials specific to that bank's Raast gateway. The implementation code (`banking_api.py`, `raast_payment.py`) is complete and awaits credentials. EWA (Earned Wage Access) payouts also route through this integration (`FinancialWellnessService` in `ewa.py`).
**Affected Components:** `backend/banking_api.py`; `backend/country/pakistan/raast_payment.py`; `backend/services/finance/ewa.py`; bank-service
**Affected Routes:** `/api/v1/banking` (gateway route 24)
**Affected APIs:** Raast disbursement API (via bank partner gateway)
**Affected Workflows:** WF-003 (Payroll Run — disbursement step); WF-006 (EWA requests)
**Affected Roles:** PayrollAdmin, Admin
**Owner Required:** YES — bank partner selection, corporate account, onboarding
**External Dependency:** YES — bank partner; SBP Raast infrastructure
**Future Impact:** HIGH — payroll disbursement and EWA payouts will not function in production without credentials
**Reopen Criteria:** N/A — this item IS open; closes when bank partner onboarding is complete and credentials are set
**Related Documents:** `docs/01_backend/INTEGRATION_CATALOG.md` §Raast; `backend/banking_api.py`; `backend/services/finance/ewa.py`
**Related Register Entries:** OD-001 (launch timeline); SD-034 (Raast protocol default)

---

## §5 — WHATSAPP BUSINESS API ACCOUNT (ED-005)

**Item ID:** ED-005
**Title:** WhatsApp Business API Account and Meta Business Manager Approval
**Classification:** EXTERNAL-DEPENDENCY
**Current Status:** OPEN — awaiting owner provisioning
**Original Source:** INTEGRATION_CATALOG.md §WhatsApp; Mandate 2 OWNER-REQUIRED compression; TR-006 (gateway route 25 confirmed)
**Evidence Source:** `backend/api-gateway/routes.py` line 55 (route 25: `/api/v1/whatsapp` → whatsapp-service confirmed); `backend/docs/canon/service-map.md` (notification-service → whatsapp); docker-compose.yml env var `WHATSAPP_API_TOKEN` / `WHATSAPP_PHONE_NUMBER_ID` expected
**Resolution Source:** N/A — not resolvable from repository
**Resolution Date:** NOT YET RESOLVED
**Resolved By:** N/A — requires human action
**Decision Summary:** WhatsApp Business API requires a Meta Business Manager account, business verification, and approval of a WhatsApp Business Account (WABA). Owner must create the business account, submit for Meta's business verification, and obtain a phone number ID and API token.
**Detailed Explanation:** WhatsApp notification delivery (leave approvals, payslip distribution, workflow notifications) routes through gateway route 25 (`/api/v1/whatsapp`) per TR-006. The whatsapp-service uses the Meta Cloud API (WhatsApp Business Platform). Owner must: (1) create or use existing Meta Business Manager account, (2) add a WhatsApp Business Account, (3) complete business verification (may take 5–15 business days), (4) register a dedicated phone number for the business, (5) obtain `WHATSAPP_PHONE_NUMBER_ID` and a permanent API token. Alternatively, a third-party WhatsApp BSP (Business Solution Provider) can be used — this also requires vendor account creation. Implementation code exists and awaits credentials.
**Affected Components:** whatsapp-service; notification-service; `backend/api-gateway/routes.py` route 25
**Affected Routes:** `/api/v1/whatsapp` (gateway route 25 — C-001 applies: returns `{status, data, service}` envelope)
**Affected APIs:** Meta WhatsApp Cloud API; whatsapp-service endpoint
**Affected Workflows:** All notification-driven workflows (leave approvals, payroll notifications, onboarding)
**Affected Roles:** All roles (notification recipients)
**Owner Required:** YES — Meta Business Manager account creation, business verification
**External Dependency:** YES — Meta Business Manager; Meta review process
**Future Impact:** HIGH — WhatsApp notifications will not function in production without account approval
**Reopen Criteria:** N/A — this item IS open; closes when Meta WABA approval is complete and `WHATSAPP_API_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID` are set in production `.env`
**Related Documents:** `docs/01_backend/INTEGRATION_CATALOG.md` §WhatsApp; `backend/api-gateway/routes.py` line 55; `docs/03_fullstack_contracts/CONTRACT_VERSION_REGISTRY.md` (TR-006)
**Related Register Entries:** OD-001 (launch timeline governs urgency); C-001 (non-standard envelope for route 25)
