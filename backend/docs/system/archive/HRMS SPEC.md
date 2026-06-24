> **SUPERSEDED** — This document is an archived draft. Canonical authority: `docs/system/MASTER BUILD SPEC.md`
> Do not edit. Retained for historical reference only.

TITLE:  
COUNTRY-AGNOSTIC, CORE-CENTRIC, CAPABILITY-DRIVEN, MODULAR HRMS SPEC

VERSION:  
v1.0

PURPOSE:  
Define the product, architecture, behavior, and capability boundaries for a modular HRMS that:  
\- is country-agnostic by design  
\- is Pakistan-ready first  
\- is core-centric (payroll/compliance/attendance first)  
\- is capability-driven, not CRUD-driven  
\- supports modular expansion without architectural drift

\================================================================  
01\. PRODUCT THESIS  
\================================================================

This system is NOT a generic HRMS.

It is:  
→ a workforce operations platform  
→ a payroll/compliance trust system  
→ a decision-support system for HR, finance, managers, and employees

PRIMARY VALUE:  
1\. payroll accuracy  
2\. compliance correctness  
3\. attendance/payroll integrity  
4\. manager actionability  
5\. employee accessibility  
6\. extensibility across countries

POSITIONING:  
“Country-Agnostic Workforce OS with Pakistan Compliance Core”

\================================================================  
02\. PRODUCT PRINCIPLES  
\================================================================

P1. Core before edge  
\- payroll, compliance, attendance, employee data are core  
\- helpdesk, engagement, advanced AI, and extras are secondary

P2. Capability before module  
\- system must be designed around outcomes:  
  payroll run, compliance validation, salary disbursement, anomaly review  
\- not around static menu sections

P3. Country isolation  
\- country rules must live only in country layer  
\- service layer must never hardcode jurisdiction logic

P4. Explainability over automation theater  
\- AI must explain decisions  
\- no black-box critical actions

P5. Safe defaults  
\- system blocks invalid critical actions  
\- must not allow broken payroll/compliance states to proceed

P6. Modular growth  
\- optional capabilities can be added without touching core orchestration  
\- service boundaries must remain clean

\================================================================  
03\. TARGET USERS  
\================================================================

PRIMARY USERS:  
\- HR Admin  
\- Payroll Officer  
\- Compliance Officer  
\- Finance Admin  
\- Line Manager  
\- Employee

SECONDARY USERS:  
\- Auditor  
\- Operations Admin  
\- Country/Entity Admin

\================================================================  
04\. CORE PROBLEMS TO SOLVE  
\================================================================

GLOBAL / CROSS-COUNTRY:  
\- fragmented HR operations  
\- weak payroll-attendance integration  
\- lack of trustworthy automation  
\- dashboards without actionability  
\- weak employee access channels

PAKISTAN-SPECIFIC:  
\- FBR / EOBI / PESSI / SESSI fragmentation  
\- payroll error anxiety  
\- attendance mismatch and overtime disputes  
\- bank / salary disbursement friction  
\- poor mobile / WhatsApp accessibility  
\- low trust in existing systems

\================================================================  
05\. SYSTEM SHAPE  
\================================================================

SYSTEM TYPE:  
Modular monolith OR service-oriented modular platform

MANDATORY ARCHITECTURE STYLE:  
\- capability-driven  
\- domain-oriented  
\- country-agnostic orchestration  
\- country-specific rule injection via adapters  
\- explicit state transitions  
\- auditable operations

\================================================================  
06\. CORE CAPABILITIES (REQUIRED)  
\================================================================

C01. EMPLOYEE CORE  
\- employee master profile  
\- organization assignment  
\- legal entity assignment  
\- location and province/state assignment  
\- role / grade / department  
\- statutory identifiers  
\- bank details  
\- document store

C02. ORGANIZATION CORE  
\- organization  
\- legal entities  
\- business units  
\- locations  
\- cost centers  
\- reporting lines

C03. PAYROLL CORE  
\- salary structures  
\- allowances  
\- deductions  
\- tax computation  
\- arrears  
\- bonuses  
\- loans / advances  
\- final settlement  
\- payroll cycles  
\- payroll runs  
\- payslips

C04. COMPLIANCE CORE  
\- statutory validation  
\- contribution computation  
\- government output generation  
\- submission state tracking  
\- manual fallback support  
\- audit evidence

C05. ATTENDANCE CORE  
\- clock events  
\- biometric ingestion  
\- GPS/mobile attendance  
\- shift templates  
\- rosters  
\- overtime  
\- grace periods  
\- late penalty logic  
\- missing punch resolution

C06. LEAVE CORE  
\- policy definitions  
\- accrual / balance  
\- leave requests  
\- approvals  
\- payroll effect

C07. DISBURSEMENT CORE  
\- bank salary file generation  
\- payout batching  
\- payout tracking  
\- reconciliation states  
\- Raast / instant payment path where applicable

C08. DECISION CORE  
\- anomaly detection intake  
\- decision object creation  
\- approvals / overrides  
\- auditability  
\- expiration / SLA handling

C09. EMPLOYEE ACCESS CORE  
\- employee self-service  
\- mobile optimized interaction  
\- payslip access  
\- leave access  
\- alerts  
\- status views

\================================================================  
07\. OPTIONAL / ADD-ON CAPABILITIES  
\================================================================

A01. HELPDESK / HR SERVICE DELIVERY  
\- ticketing  
\- employee issue handling  
\- SLA routing

A02. EXPENSES  
\- reimbursements  
\- receipts  
\- approval chains

A03. EWA / FINANCIAL WELLNESS  
\- salary advance  
\- earned wage access  
\- deduction-backed repayment

A04. PERFORMANCE  
\- goals  
\- OKRs  
\- reviews  
\- 360 feedback

A05. RECRUITMENT  
\- jobs  
\- candidates  
\- interview workflows  
\- onboarding

A06. ENGAGEMENT  
\- surveys  
\- sentiment  
\- pulse checks

A07. ADVANCED AI INSIGHTS  
\- attrition risk  
\- burnout trends  
\- workforce pattern intelligence

RULE:  
Optional capabilities must plug into the core without changing core behavior contracts.

\================================================================  
08\. COUNTRY-AGNOSTIC ARCHITECTURE CANON  
\================================================================

MANDATORY LAYERS:

L1. DOMAIN DATA LAYER  
\- entities  
\- repositories  
\- state storage

L2. DOMAIN LOGIC LAYER  
\- payroll domain logic  
\- attendance domain logic  
\- leave domain logic  
\- decision domain logic

L3. COUNTRY ABSTRACTION LAYER  
country/base/  
  \- tax engine interface  
  \- compliance engine interface  
  \- payroll rules interface  
  \- statutory validator interface

country/{country}/  
  \- adapter  
  \- tax engine  
  \- compliance engine  
  \- payroll rules  
  \- validators

L4. SERVICE / ORCHESTRATION LAYER  
\- payroll service  
\- compliance service  
\- attendance service  
\- decision service  
\- bank service  
\- employee access service

L5. INTERFACE / API LAYER  
\- REST / internal APIs  
\- events  
\- webhooks  
\- admin endpoints

CRITICAL RULES:  
R1. Services must never import country-specific modules directly  
R2. Services must resolve country via resolver  
R3. All statutory logic must live in country/{country}/  
R4. Adding a new country must require only new country adapter implementation  
R5. No hardcoded "PK", "pakistan", or country literals in service logic  
R6. Core orchestration must remain identical across countries

\================================================================  
09\. COUNTRY RESOLUTION MODEL  
\================================================================

Country resolution source priority:  
1\. legal entity  
2\. organization config  
3\. location / employment assignment  
4\. explicit runtime override (admin/system only)

REQUIRED METHOD:  
adapter \= country\_resolver.get\_adapter(org\_id or legal\_entity\_id)

RESOLVER MUST:  
\- be config/data driven  
\- not contain business logic  
\- not seed production assumptions in code

\================================================================  
10\. CORE SERVICES (CANON)  
\================================================================

MANDATORY SERVICES:  
\- employee-service  
\- payroll-service  
\- compliance-service  
\- attendance-service  
\- bank-service  
\- decision-service  
\- employee-access-service

SUPPORT SERVICES:  
\- automation-service  
\- notification-service  
\- audit-service

OPTIONAL SERVICES:  
\- helpdesk-service  
\- expense-service  
\- ewa-financial-service  
\- performance-service  
\- recruitment-service

RULE:  
If documented as a service, it must be marked as exactly one of:  
\- implemented  
\- add-on  
\- planned  
\- deprecated

\================================================================  
11\. PAKISTAN COUNTRY PROFILE (REQUIRED FIRST-CLASS SUPPORT)  
\================================================================

MUST SUPPORT:  
\- Pakistan tax computation  
\- FBR output generation  
\- EOBI eligibility and output generation  
\- PESSI / SESSI branching  
\- province-aware compliance handling  
\- CNIC validation  
\- bank salary output  
\- Raast payout option / placeholder path  
\- statutory completeness validation before payroll finalization

PAKISTAN PAYROLL BLOCK CONDITIONS:  
\- invalid or missing CNIC  
\- missing bank details when payout mode requires bank  
\- missing statutory identifiers required by policy  
\- unresolved attendance critical issues  
\- invalid province/entity mapping  
\- compliance validation failure

\================================================================  
12\. PAYROLL BEHAVIOR CONTRACT  
\================================================================

WHEN payroll run starts:  
1\. resolve adapter  
2\. validate employee eligibility and completeness  
3\. validate attendance integrity  
4\. compute pay components  
5\. compute country tax and statutory outputs  
6\. run anomaly checks  
7\. produce payroll result set  
8\. block or continue based on decision thresholds  
9\. generate payslips and downstream outputs  
10\. create audit record

PAYROLL MUST:  
\- be reproducible  
\- be auditable  
\- be blockable  
\- expose failure reasons clearly

PAYROLL MUST NOT:  
\- silently skip statutory issues  
\- finalize with critical unresolved data issues  
\- contain country-specific rules in orchestration code

\================================================================  
13\. COMPLIANCE BEHAVIOR CONTRACT  
\================================================================

COMPLIANCE MUST:  
\- validate statutory readiness before payroll finalization  
\- generate required output artifacts  
\- support submission state transitions  
\- support manual fallback mode  
\- preserve evidence

SUBMISSION STATES:  
\- DRAFT  
\- VALIDATED  
\- SUBMITTED  
\- ACKNOWLEDGED  
\- FAILED  
\- RETRY

ERROR TYPES:  
\- data\_error  
\- rules\_error  
\- external\_dependency\_error  
\- operator\_error

COMPLIANCE OUTPUTS MUST BE:  
\- explainable  
\- reproducible  
\- linked to payroll run and entity

\================================================================  
14\. ATTENDANCE BEHAVIOR CONTRACT  
\================================================================

ATTENDANCE MUST:  
\- ingest raw events  
\- resolve shifts  
\- identify missing punches  
\- compute overtime  
\- compute lateness  
\- produce payroll-ready attendance summary

ATTENDANCE CRITICAL RULE:  
If attendance inconsistency materially affects payroll:  
→ system must block payroll finalization or generate mandatory decision review

\================================================================  
15\. DECISION SYSTEM CANON  
\================================================================

PURPOSE:  
Convert anomalies, conflicts, and approvals into a consistent decision workflow.

DECISION OBJECT SCHEMA:  
\- id  
\- source\_domain  
\- trigger  
\- impact\_scope  
\- severity  
\- confidence  
\- explanation  
\- recommended\_action  
\- reversibility  
\- expires\_at  
\- status  
\- created\_at  
\- resolved\_at  
\- actor

SEVERITY LEVELS:  
\- passive  
\- notify  
\- critical

BEHAVIOR:  
\- critical → block / mandatory approval  
\- notify → visible action required, non-blocking unless escalated  
\- passive → logged / surfaced in stream

RULE:  
Decision service must be cross-domain.  
It must NOT be embedded only inside payroll.

\================================================================  
16\. AI / INSIGHT BEHAVIOR  
\================================================================

AI IS ALLOWED TO:  
\- flag anomalies  
\- classify patterns  
\- produce confidence  
\- produce explanation  
\- suggest actions

AI IS NOT ALLOWED TO:  
\- override compliance rules  
\- auto-approve high-risk financial actions  
\- make non-auditable critical decisions

MANDATORY AI OUTPUT FIELDS:  
\- confidence  
\- explanation  
\- supporting\_signals  
\- suggested\_action

\================================================================  
17\. EMPLOYEE ACCESS / WHATSAPP / MOBILE  
\================================================================

EMPLOYEE ACCESS CHANNELS:  
\- web portal  
\- mobile web/app  
\- WhatsApp access channel

WHATSAPP MUST BE TREATED AS:  
\- a standalone access-channel service  
\- not merely a webhook snippet  
\- not a replacement for core logic

WHATSAPP RESPONSIBILITIES:  
\- user mapping  
\- authentication / OTP if needed  
\- request routing  
\- safe response formatting  
\- audit trail for sensitive actions

SUPPORTED EMPLOYEE ACTIONS:  
\- view payslip  
\- request leave  
\- receive alerts  
\- view attendance status

SUPPORTED MANAGER ACTIONS:  
\- approve simple actions  
\- receive team alerts  
\- review pending items

\================================================================  
18\. BANK / DISBURSEMENT BEHAVIOR  
\================================================================

BANK SERVICE MUST:  
\- accept approved payroll run output  
\- generate bank-specific salary outputs  
\- generate Raast-compatible payloads where configured  
\- track payout status  
\- support reconciliation states

MINIMUM RECONCILIATION STATES:  
\- pending  
\- sent  
\- accepted  
\- rejected  
\- reconciled

\================================================================  
19\. SECURITY / AUDIT CANON  
\================================================================

MANDATORY:  
\- RBAC  
\- entity-scoped access  
\- immutable audit events for critical operations  
\- sensitive data protection  
\- actor \+ timestamp \+ action \+ outcome on all critical changes

CRITICAL AUDIT EVENTS:  
\- payroll run creation/finalization  
\- compliance validation/submission  
\- bank payout generation  
\- decision approval/rejection/override  
\- employee-sensitive action via access channels

\================================================================  
20\. DOCS / CODE / DEPLOYMENT ALIGNMENT RULE  
\================================================================

The repo is valid only if:  
\- docs/canon matches actual implemented services  
\- docker-compose/runtime matches actual startable services  
\- README does not over-claim  
\- planned/add-on services are clearly marked

MANDATORY RELEASE MANIFEST FIELDS:  
\- service name  
\- runtime status  
\- scope (core/add-on/planned)  
\- country support  
\- owner domain

\================================================================  
21\. ACCEPTANCE CRITERIA FOR “ARCHITECTURALLY CORRECT”  
\================================================================

The system is architecturally correct only when ALL are true:

AC1. No country-specific imports exist inside services  
AC2. Resolver selects adapter via config/data  
AC3. Pakistan adapter runs without special-casing service code  
AC4. A second dummy country adapter can be added without touching services  
AC5. Payroll \-\> compliance \-\> bank happy path works  
AC6. Invalid statutory data blocks payroll  
AC7. Decision service exists as cross-domain service  
AC8. WhatsApp exists as access-channel service, not only integration note  
AC9. docs/canon, compose, and code enumerate the same real services  
AC10. import-health and test collection pass

\================================================================  
22\. ACCEPTANCE CRITERIA FOR “PAKISTAN READY”  
\================================================================

The system is Pakistan-ready only when ALL are true:

PK1. Pakistan tax calculation is executable and tested  
PK2. FBR output generation is executable and tested  
PK3. EOBI output generation is executable and tested  
PK4. PESSI / SESSI branching is executable and tested  
PK5. CNIC/statutory validation blocks invalid payroll  
PK6. bank/Raast path is runnable  
PK7. attendance/payroll conflict handling is active  
PK8. audit trail exists for payroll/compliance/disbursement

\================================================================  
23\. DELIVERY PRIORITY  
\================================================================

PRIORITY 1 — CORE CORRECTNESS  
\- employee core  
\- payroll core  
\- compliance core  
\- attendance core  
\- bank core  
\- audit core

PRIORITY 2 — CONTROL \+ ACTION  
\- decision core  
\- employee access core  
\- manager decision flows

PRIORITY 3 — EXPANSION  
\- WhatsApp service  
\- optional add-ons  
\- second country adapter  
\- advanced AI

\================================================================  
24\. NON-GOALS  
\================================================================

This spec does NOT require:  
\- overbuilt UI design  
\- engagement gimmicks  
\- fake AI chat surfaces  
\- broad feature sprawl before core correctness  
\- country expansion before country isolation works

\================================================================  
25\. ONE-LINE SUMMARY  
\================================================================

Build a modular HRMS where:  
\- payroll/compliance/attendance are the core  
\- countries plug in through adapters  
\- decisions are first-class  
\- Pakistan is fully supported first  
\- expansion never contaminates core orchestration

END