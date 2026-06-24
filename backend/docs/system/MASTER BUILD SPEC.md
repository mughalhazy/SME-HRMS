SYSTEM NAME:
AURA HRMS — Pakistan Compliance OS + AI Workforce Decision System

VERSION:
v2.0 — Master Build Spec (merged from Complete Build Spec v1.0 + HRMS Spec v1.0)

PURPOSE:
Build a Pakistan-first, country-agnostic, AI-native HRMS that:
- eliminates payroll errors
- automates compliance
- surfaces decisions instead of dashboards
- scales to multi-country without architectural drift

POSITIONING:
"Country-Agnostic Workforce OS with Pakistan Compliance Core and AI Decision Intelligence"

CORE PRINCIPLE:
Trust > Accuracy > Compliance > Intelligence > UX

================================================================
01. PRODUCT THESIS
================================================================

This system is NOT a generic HRMS.

It is:
→ a workforce operations platform
→ a payroll/compliance trust system
→ a decision-support system for HR, finance, managers, and employees

PRIMARY VALUE:
1. payroll accuracy
2. compliance correctness
3. attendance/payroll integrity
4. manager actionability
5. employee accessibility
6. extensibility across countries

================================================================
02. PRODUCT PRINCIPLES
================================================================

P1. Core before edge
    - payroll, compliance, attendance, employee data are the core product
    - helpdesk, engagement, advanced AI, and extras are secondary

P2. Capability before module
    - design around outcomes: payroll run, compliance validation, salary disbursement, anomaly review
    - not around static menu sections or CRUD screens

P3. Country isolation
    - country rules must live only in the country layer
    - service orchestration must never hardcode jurisdiction logic

P4. Explainability over automation theater
    - AI must explain its decisions with supporting signals and suggested actions
    - no black-box critical actions

P5. Safe defaults
    - system blocks invalid critical actions
    - broken payroll/compliance states must not be allowed to proceed silently

P6. Mobile + WhatsApp first
    - employees must be reachable via WhatsApp and mobile without requiring desktop access

P7. Modular growth
    - optional capabilities can be added without touching core orchestration
    - service boundaries must remain clean

================================================================
03. TARGET USERS
================================================================

PRIMARY:
- HR Admin
- Payroll Officer
- Compliance Officer
- Finance Admin
- Line Manager
- Employee

SECONDARY:
- Auditor
- Operations Admin
- Country / Entity Admin

================================================================
04. CORE PROBLEMS TO SOLVE
================================================================

GLOBAL / CROSS-COUNTRY:
- fragmented HR operations across entities
- weak payroll-attendance integration
- lack of trustworthy automation
- dashboards without actionability
- weak employee access channels

PAKISTAN-SPECIFIC:
- FBR / EOBI / PESSI / SESSI fragmentation
- payroll error anxiety and audit risk
- attendance mismatch and overtime disputes
- bank / salary disbursement friction
- poor mobile / WhatsApp accessibility
- low trust in existing HR systems

================================================================
05. SYSTEM ARCHITECTURE
================================================================

The system is organized into six layers. Country-specific logic is confined
entirely to Layer 3. Layers 4 and above contain no country references.

---

LAYER 1 — DATA LAYER

- Employees
- Organizations
- Legal Entities
- Locations (with country + province)
- Payroll Records
- Attendance Logs
- Compliance Records
- Audit Logs (immutable)

---

LAYER 2 — DOMAIN LOGIC LAYER

Core domains (each owns its logic and exposes interfaces):
- Payroll
- Compliance
- Attendance
- Leave
- Decision
- Employee Access

Rule: No domain may hardcode country-specific rules.

---

LAYER 3 — COUNTRY ABSTRACTION LAYER

country/base/
  - TaxEngineInterface
  - ComplianceEngineInterface
  - PayrollRulesInterface
  - StatutoryValidatorInterface
  - BankingInterface

country/{country}/
  - adapter (entry point — instantiates all engines)
  - tax_engine
  - compliance_engine
  - payroll_rules
  - statutory_validator
  - banking

Rule: ALL statutory logic, tax computation, and bank-format generation must
live exclusively in this layer. Services never import from country/{country}/ directly.

---

LAYER 4 — SERVICE / ORCHESTRATION LAYER

Services (orchestrators only — no country logic):
- PayrollService
- ComplianceService
- AttendanceService
- BankService
- DecisionService
- WhatsAppService
- EmployeeAccessService

Rule: Services resolve country via CountryResolver only.
      They call adapter.tax_engine, adapter.compliance_engine, adapter.banking etc.
      No service contains "PK", "pakistan", or any country-specific literal.

---

LAYER 5 — INTEGRATION LAYER

Pakistan:
- FBR Adapter
- EOBI Adapter
- PESSI / SESSI Adapter
- Bank Salary Adapter
- Raast Adapter
- WhatsApp API

Other countries:
- Add integration adapters here only, no service changes required.

---

LAYER 6 — EXPERIENCE LAYER

Interfaces:
- HR Admin Console
- Manager Dashboard (decision-first)
- Employee Portal
- Mobile App / Mobile Web
- WhatsApp Interface

================================================================
06. CORE CAPABILITIES (REQUIRED)
================================================================

C01. EMPLOYEE CORE
- employee master profile
- organization assignment
- legal entity assignment
- location and province/state assignment
- role / grade / department
- statutory identifiers (CNIC, EOBI number, social security number)
- bank details
- document store

C02. ORGANIZATION CORE
- organization
- legal entities
- business units
- locations
- cost centers
- reporting lines

C03. PAYROLL CORE
- salary structures
- allowances
- deductions
- tax computation (country-adapter driven)
- gratuity and provident fund (country-specific)
- arrears
- bonuses
- loans and advances
- final settlement
- payroll cycles
- payroll runs
- payslips
- leave-to-payroll effect (unpaid leave reduces net pay)

C04. COMPLIANCE CORE
- statutory validation before payroll finalization
- contribution computation
- government output generation (FBR, EOBI, PESSI, etc.)
- submission state tracking
- manual fallback support when automation fails
- audit evidence preservation

C05. ATTENDANCE CORE
- clock events ingestion
- biometric sync
- GPS / mobile attendance
- face recognition
- overtime rules
- grace period and late penalty logic
- missing punch detection and resolution
- payroll-ready attendance summary
- shift templates and rosters *(deferred to v2 — foundation in place, full roster management not yet built)*

C06. LEAVE CORE
- policy definitions
- accrual and balance tracking
- leave requests and approvals
- payroll effect (approved unpaid leave reduces net pay)

C07. DISBURSEMENT CORE
- bank-specific salary file generation
- Raast / instant payment payload generation
- payout batching and status tracking
- reconciliation with state transitions
- failure and retry handling

C08. DECISION CORE
- anomaly detection intake from payroll, attendance, compliance
- decision object creation with full schema
- approvals / overrides by authorized actors
- full auditability
- expiration / SLA handling per decision card

C09. EMPLOYEE ACCESS CORE
- employee self-service
- mobile-optimized interaction
- payslip access
- leave request and status
- alerts and notifications
- WhatsApp access channel

================================================================
07. OPTIONAL / ADD-ON CAPABILITIES
================================================================

A01. HELPDESK / HR SERVICE DELIVERY
- employee query tickets
- SLA routing and tracking
- knowledge base

A02. EXPENSES
- reimbursement claims
- receipt capture
- approval chains
- accounting export

A03. EWA / FINANCIAL WELLNESS
- earned wage access
- salary advance
- deduction-backed repayment via payroll

A04. PERFORMANCE MANAGEMENT
- goals and OKRs
- 360-degree feedback
- review cycles
- calibration

A05. RECRUITMENT
- job postings
- candidate management
- interview workflows
- hire-to-employee handoff

A06. ENGAGEMENT
- surveys
- sentiment tracking
- pulse checks

A07. ADVANCED AI INSIGHTS
- attrition risk modeling
- burnout trend detection
- workforce pattern intelligence

Rule: Optional capabilities must plug into core without changing core
behavior contracts or service interfaces.

================================================================
08. COUNTRY-AGNOSTIC ARCHITECTURE RULES
================================================================

R1. No service may import any country-specific module directly.
R2. All country logic is resolved via:
      adapter = country_resolver.get_adapter(org_id)
R3. All statutory rules live only in country/{country}/
R4. Adding a new country requires only a new adapter — no service changes.
R5. No hardcoded "PK", "pakistan", or country literals in service logic.
R6. Core orchestration must remain identical across all countries.

ENFORCEMENT:
- grep of service files must return zero country-specific imports or literals
- a second dummy country adapter must exist as architecture proof
- tests must verify payroll service works identically with any adapter

================================================================
09. COUNTRY RESOLUTION MODEL
================================================================

Resolution source priority (highest to lowest):
1. legal entity
2. organization config
3. location / employment assignment
4. explicit runtime override (admin / system only)

Required method:
    adapter = country_resolver.get_adapter(org_id or legal_entity_id)

Resolver must:
- be config/data-driven
- not contain business logic
- not seed production assumptions in code
- support runtime registration of new adapters and org mappings

================================================================
10. CORE SERVICES REGISTRY
================================================================

NOTE: This registry covers services explicitly built as part of this project and classified by capability tier.
Four fully-implemented services are omitted here because they are treated as assumed platform infrastructure:
leave-service, hiring-service, auth-service, workflow-service. All four are fully implemented and documented
in docs/canon/service-map.md, which is the authoritative complete service inventory.

MANDATORY CORE SERVICES:
- employee-service       → IMPLEMENTED
- payroll-service        → IMPLEMENTED
- compliance-service     → IMPLEMENTED
- attendance-service     → IMPLEMENTED
- bank-service           → IMPLEMENTED
- decision-service       → IMPLEMENTED
- whatsapp-service       → IMPLEMENTED

SUPPORT SERVICES:
- automation-service             → IMPLEMENTED
- notification-service           → IMPLEMENTED
- reporting-analytics-service    → IMPLEMENTED
- audit-service                  → IMPLEMENTED

OPTIONAL / ADD-ON SERVICES:
- helpdesk-service        → ADD-ON
- expense-service         → ADD-ON
- ewa-financial-service   → ADD-ON
- performance-service     → ADD-ON
- engagement-service      → ADD-ON
- search-service          → ADD-ON
- integration-service     → ADD-ON
- settings-service        → ADD-ON

IMPLEMENTED (previously marked PLANNED — code exists):
- travel-service          → IMPLEMENTED (travel_service.py + travel_api.py)
- project-service         → IMPLEMENTED (project_service.py + project_api.py)

Rule: Every documented service must be marked exactly as one of:
      implemented / add-on / planned / deprecated.
      Paper services (documented but not runnable) are not permitted.

================================================================
11. PAKISTAN COUNTRY PROFILE (REQUIRED FIRST-CLASS SUPPORT)
================================================================

MUST SUPPORT:
- Pakistan income tax computation (Finance Act slabs, multi-year)
- Filer / non-filer surcharge (Finance Act 2023/2024)
- Exempt allowance exclusion before tax computation
- FBR Annexure-C output generation
- EOBI eligibility check and PR-01 contribution generation
- PESSI (Punjab) and SESSI (Sindh) branching and contribution math
- WPPF (Workers Profit Participation Fund)
- WWF (Workers Welfare Fund)
- Gratuity calculation
- Provident Fund calculation and rate updates
- Arrears taxation via separate computation path
- Bonus income taxation
- Province-aware compliance routing (Punjab → PESSI, Sindh → SESSI, extensible)
- CNIC validation (13-digit, numeric)
- Bank salary file generation (bank-specific formats)
- Raast instant payment payload generation
- Statutory completeness validation before payroll finalization
- ATL / FBR filer status verification
- Tax slab update mechanism for each Finance Act year

PAYROLL BLOCK CONDITIONS (Pakistan):
- invalid or missing CNIC
- missing bank details when disbursement mode requires bank
- missing statutory identifiers required by policy
- unresolved critical attendance issues
- invalid province / entity mapping
- compliance validation failure

================================================================
12. PAYROLL BEHAVIOR CONTRACT
================================================================

WHEN a payroll run starts:
1. resolve adapter via CountryResolver
2. validate employee eligibility and statutory completeness
3. validate attendance integrity for the pay period
4. compute pay components (base, allowances, deductions, overtime)
5. apply leave effect (unpaid leave days reduce net pay)
6. compute country tax and statutory outputs via adapter
7. run anomaly checks (Payroll Guardian)
8. produce payroll result set
9. block or continue based on decision thresholds
10. generate payslips and downstream outputs
11. create immutable audit record

PAYROLL MUST:
- be reproducible given the same inputs
- be auditable with full actor/timestamp/state trail
- be blockable at the precheck gate
- expose failure reasons clearly to the operator

PAYROLL MUST NOT:
- silently skip statutory issues
- finalize with critical unresolved data gaps
- contain country-specific rules in orchestration code

================================================================
13. COMPLIANCE BEHAVIOR CONTRACT
================================================================

COMPLIANCE MUST:
- validate statutory readiness before payroll finalization
- generate required output artifacts per jurisdiction
- support submission state transitions
- support manual fallback mode when automated submission fails
- classify errors by type to enable operator triage
- preserve evidence linked to payroll run and legal entity

SUBMISSION STATES:
  DRAFT → VALIDATED → SUBMITTED → ACKNOWLEDGED → FAILED → RETRY → MANUAL

State descriptions:
- DRAFT        — submission record created, not yet validated
- VALIDATED    — statutory validation passed
- SUBMITTED    — sent to government portal/system
- ACKNOWLEDGED — portal confirmed receipt
- FAILED       — submission failed with error
- RETRY        — queued for retry after failure
- MANUAL       — operator recorded manual submission (escape hatch when portal is unavailable)

ERROR TYPES (for operator triage):
- data_error               — missing or invalid employee data, fixable by HR
- rules_error              — statutory constraint violated, fixable by data/config update
- external_dependency_error — government portal unavailable, fixable by retry or manual
- operator_error           — process error (duplicate, wrong period), fixable by operator

COMPLIANCE OUTPUTS MUST BE:
- explainable (violations listed with rule_id and description)
- reproducible
- linked to a specific payroll run, legal entity, and period

================================================================
14. ATTENDANCE BEHAVIOR CONTRACT
================================================================

ATTENDANCE MUST:
- ingest raw clock events (biometric, GPS, mobile, face recognition)
- resolve shift templates for each attendance record
- identify missing punches and flag for resolution
- compute overtime per configured rules
- compute lateness and apply penalty rules
- produce payroll-ready attendance summary per employee per period

ATTENDANCE CRITICAL RULE:
If an attendance inconsistency materially affects payroll:
→ system must block payroll finalization OR generate a mandatory decision review card.

================================================================
15. DECISION SYSTEM CANON
================================================================

PURPOSE:
Convert anomalies, conflicts, and approval requirements across all domains
into a consistent, actionable decision workflow.

DECISION OBJECT SCHEMA:
- id
- source_domain      (payroll / attendance / compliance / finance)
- trigger            (what caused this decision to be created)
- impact_scope
- severity           (passive / notify / critical)
- confidence         (0.0 – 1.0)
- explanation        (plain language reason)
- supporting_signals (data points that drove the decision)
- suggested_action   (recommended next step for the actor)
- recommended_action (system recommendation)
- reversibility      (reversible / irreversible / partially-reversible)
- expires_at
- status             (active / resolved / expired / overridden)
                     # NOTE (Group C fix, 2026-06-13): canonical status enum is
                     # active | resolved | expired — see docs/canon/decision-system.md.
                     # `overridden` here maps to `resolved` with an override flag
                     # (see decision-system.md / decision-service.md mapping notes).
- created_at
- resolved_at
- actor              (who resolved, if resolved)

SEVERITY LEVELS AND BEHAVIOR:
- critical → block the triggering action; mandatory human approval required
- notify   → visible action required; non-blocking unless escalated
- passive  → logged and surfaced in stream; no immediate action required

AI CONFIDENCE TIERS:
- HIGH    (70%+)  — high confidence, system recommendation is reliable
- MEDIUM  (40-69%) — moderate confidence, human review recommended
- LOW     (<40%)  — low confidence, treat as informational only

Rules:
- Decision service must be cross-domain.
- It must NOT be embedded only inside payroll.
- All decisions must have a "Why" explanation and audit trail.
- Human-in-loop is required for: payroll approval, compliance submission, anomaly override.

================================================================
16. AI / INSIGHT BEHAVIOR
================================================================

AI IS ALLOWED TO:
- flag anomalies and classify patterns
- produce confidence scores
- produce plain-language explanations
- provide supporting signals
- suggest next actions

AI IS NOT ALLOWED TO:
- override compliance rules
- auto-approve high-risk financial actions
- make non-auditable critical decisions

MANDATORY AI OUTPUT FIELDS (all AI-generated outputs must include):
- confidence
- explanation
- supporting_signals
- suggested_action

PAYROLL GUARDIAN detects:
- salary anomalies / spikes
- overtime spikes
- missing or under-computed tax deductions
- ghost employee indicators

================================================================
17. EMPLOYEE ACCESS / WHATSAPP / MOBILE
================================================================

EMPLOYEE ACCESS CHANNELS:
- web portal
- mobile web / app
- WhatsApp access channel

WHATSAPP MUST BE TREATED AS:
- a standalone access-channel service
- not merely a webhook snippet
- not a replacement for core logic

WHATSAPP RESPONSIBILITIES:
- user-to-employee phone mapping
- OTP verification for sensitive actions
- request routing to domain services
- safe response formatting
- audit trail for all sensitive actions

SUPPORTED EMPLOYEE ACTIONS:
- view payslip
- request leave
- receive attendance alerts
- view compliance / payroll status

SUPPORTED MANAGER ACTIONS:
- approve simple actions
- receive team alerts
- review pending decision cards

================================================================
18. BANK / DISBURSEMENT BEHAVIOR
================================================================

BANK SERVICE MUST:
- accept approved payroll run output
- generate bank-specific salary files (CSV / Excel per bank format)
- generate Raast-compatible payment payloads where configured
- track payout status per employee per period
- support full reconciliation state lifecycle
- route all bank-format generation through the country banking adapter

DISBURSEMENT STATES:
  PENDING → GENERATED → SUBMITTED → SENT → ACCEPTED / REJECTED → RECONCILED / FAILED → RETRY

State descriptions:
- PENDING      — disbursement batch created
- GENERATED    — salary file generated
- SUBMITTED    — file sent to bank system
- SENT         — bank acknowledged receipt
- ACCEPTED     — bank confirmed all credits processed
- REJECTED     — bank rejected the file
- RECONCILED   — all payments matched against payroll records
- FAILED       — unrecoverable failure
- RETRY        — queued for retry

Rule: Bank service must never import country-specific banking modules directly.
      All bank-format generation is delegated via BankingInterface through the country adapter.

================================================================
19. UX SYSTEM
================================================================

PRINCIPLES:
- decision-first UI (decisions and alerts before reports)
- confidence always visible alongside AI outputs
- compliance status always prioritized in manager views

CORE UI COMPONENTS:
- Decision Cards (primary action surface)
- Agent Cards (AI output display)
- Confidence Module (score + tier + explanation)

ANTI-PATTERNS (never build these):
- dashboard overload with no actionable path
- hidden compliance status behind nested menus
- generic AI outputs without explanation or context
- approval flows that bypass audit trail

================================================================
20. SECURITY / AUDIT CANON
================================================================

MANDATORY:
- RBAC (role-based access control)
- entity-scoped access (tenant isolation)
- immutable audit events for all critical operations
- sensitive data protection and field-level redaction where required
- actor + timestamp + action + outcome on all critical changes

CRITICAL AUDIT EVENTS (must be captured):
- payroll run creation and finalization
- compliance validation and submission
- bank payout generation
- decision approval / rejection / override
- employee-sensitive action via any access channel
- statutory data changes (CNIC, bank details, EOBI number)

================================================================
21. SCALABILITY
================================================================

- multi-entity support (separate legal entities per org)
- multi-country support (adapter-per-country, no service changes)
- modular services (add-ons deployable independently)
- API-first design (all capabilities accessible via REST API)
- event-driven inter-service communication where appropriate

================================================================
22. DOCS / CODE / DEPLOYMENT ALIGNMENT RULE
================================================================

The repo is valid only if ALL are true:
- docs/canon matches actual implemented services
- docker-compose / runtime matches actual startable services
- README does not over-claim capabilities not yet implemented
- planned and add-on services are explicitly marked as such

MANDATORY RELEASE MANIFEST FIELDS (per service):
- service name
- runtime status (implemented / add-on / planned / deprecated)
- scope (core / support / optional)
- country support
- owner domain

================================================================
23. ROADMAP
================================================================

PHASE 1 — ARCHITECTURE FOUNDATION
- country resolver (data-driven, no hardcoding)
- country/base interfaces
- Pakistan adapter as reference implementation
- service layer country-agnostic rewrite

PHASE 2 — PAKISTAN CORE
- compliance hardening (FBR, EOBI, PESSI/SESSI)
- payroll engine upgrade (all statutory items)
- bank / Raast path

PHASE 3 — DIFFERENTIATION
- AI Payroll Guardian
- Decision Engine (cross-domain)
- WhatsApp HR access channel

PHASE 4 — GLOBAL SCALE
- second country adapter (architecture proof) ✅ DONE — DummyAdapter in country/dummy/
- additional country adapters added on demand as new markets require — no service changes needed

================================================================
24. ACCEPTANCE CRITERIA — ARCHITECTURALLY CORRECT
================================================================

The system is architecturally correct only when ALL are true:

AC1.  No country-specific imports exist inside services
AC2.  Resolver selects adapter via config/data, not hardcoded defaults
AC3.  Pakistan adapter runs without special-casing in service code
AC4.  A second dummy country adapter can be added without touching services
AC5.  Payroll → compliance → bank happy path works end-to-end
AC6.  Invalid statutory data blocks payroll finalization
AC7.  Decision service exists as a standalone cross-domain service
AC8.  WhatsApp exists as an access-channel service, not only an integration note
AC9.  docs/canon, docker-compose, and code enumerate the same real services
AC10. Import-health and test collection pass without error

================================================================
25. ACCEPTANCE CRITERIA — PAKISTAN READY
================================================================

The system is Pakistan-ready only when ALL are true:

PK1.  Pakistan tax calculation is executable and tested
PK2.  FBR output generation is executable and tested
PK3.  EOBI output generation is executable and tested
PK4.  PESSI / SESSI province branching is executable and tested
PK5.  CNIC and statutory validation blocks invalid payroll
PK6.  Bank / Raast disbursement path is runnable
PK7.  Attendance / payroll conflict handling is active
PK8.  Audit trail exists for payroll / compliance / disbursement operations

================================================================
26. DELIVERY PRIORITY
================================================================

PRIORITY 1 — CORE CORRECTNESS
- employee core
- payroll core
- compliance core
- attendance core
- bank core
- audit core

PRIORITY 2 — CONTROL + ACTION
- decision service (cross-domain)
- employee access core
- manager decision flows

PRIORITY 3 — EXPANSION
- WhatsApp service
- optional add-ons
- second country adapter
- advanced AI insights

================================================================
27. NON-GOALS
================================================================

This spec does NOT require:
- overbuilt UI design before core logic is correct
- engagement gimmicks or gamification
- fake AI chat surfaces
- broad feature sprawl before core correctness is achieved
- country expansion before country isolation is proven to work

================================================================
28. SUCCESS CRITERIA
================================================================

The system succeeds when:
- payroll runs produce zero statutory errors
- compliance submissions are fully automated with manual fallback
- decisions replace dashboard-browsing for HR and manager workflows
- AI outputs are trusted because they are explainable
- mobile and WhatsApp adoption is measurable
- a new country can be added by one engineer in one day (adapter only)

================================================================
ONE-LINE SUMMARY
================================================================

Build a modular HRMS where payroll/compliance/attendance are the core,
countries plug in through adapters, decisions are first-class,
Pakistan is fully supported first, and expansion never contaminates
core orchestration.

================================================================
END OF MASTER BUILD SPEC
================================================================
