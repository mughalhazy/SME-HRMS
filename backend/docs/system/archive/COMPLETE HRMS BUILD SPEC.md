> **SUPERSEDED** — This document is an archived draft. Canonical authority: `docs/system/MASTER BUILD SPEC.md`
> Do not edit. Retained for historical reference only.

SYSTEM NAME:  
AURA HRMS — Pakistan Compliance OS \+ AI Workforce Decision System

VERSION:  
v1.0 — Foundational Architecture

\============================================================  
01\. SYSTEM VISION  
\============================================================

PURPOSE:  
Build a Pakistan-first, AI-native HRMS that:  
\- eliminates payroll errors  
\- automates compliance  
\- surfaces decisions (not dashboards)  
\- scales to multi-country architecture

POSITIONING:  
“Pakistan Compliance OS with AI Decision Intelligence”

CORE PRINCIPLE:  
Trust \> Accuracy \> Compliance \> Intelligence \> UX

\============================================================  
02\. DESIGN PRINCIPLES  
\============================================================

P1 — Compliance is the core product (not a feature)  
P2 — Payroll must be zero-error  
P3 — Decisions \> dashboards  
P4 — AI must be explainable  
P5 — Mobile \+ WhatsApp first  
P6 — Country logic must be isolated  
P7 — Single source of truth for statutory rules

\============================================================  
03\. SYSTEM ARCHITECTURE  
\============================================================

LAYER 1 — DATA LAYER  
\- Employees  
\- Organizations  
\- Legal Entities  
\- Locations (with country \+ province)  
\- Payroll Records  
\- Attendance Logs  
\- Compliance Records  
\- Audit Logs (immutable)

\---

LAYER 2 — DOMAIN LAYER

Core Domains:  
\- Payroll  
\- Compliance  
\- Attendance  
\- Leave  
\- Performance  
\- Recruitment  
\- Finance (EWA)

Each domain:  
\- owns logic  
\- exposes interfaces  
\- NO country-specific hardcoding

\---

LAYER 3 — COUNTRY ABSTRACTION LAYER

country/base/  
  \- TaxEngineInterface  
  \- ComplianceEngineInterface  
  \- PayrollRulesInterface

country/pakistan/  
  \- PakistanTaxEngine  
  \- PakistanComplianceEngine  
  \- PakistanPayrollRules

RULE:  
ALL statutory logic MUST live here

\---

LAYER 4 — SERVICE LAYER

Services:  
\- PayrollService (orchestrator only)  
\- ComplianceService (orchestrator only)  
\- AttendanceService  
\- DecisionEngine  
\- MobileGateway  
\- WhatsAppService

RULE:  
Services DO NOT contain country logic

\---

LAYER 5 — INTEGRATION LAYER

Pakistan:  
\- FBR Adapter  
\- EOBI Adapter  
\- PESSI/SESSI Adapter  
\- Bank Adapter  
\- Raast Adapter  
\- WhatsApp API

\---

LAYER 6 — EXPERIENCE LAYER

Interfaces:  
\- HR Admin Console  
\- Manager Dashboard (decision-first)  
\- Employee Portal  
\- Mobile App  
\- WhatsApp Interface

\============================================================  
04\. CORE MODULES (DETAILED)  
\============================================================

\[MODULE 1\] CORE HR  
\- Employee profile  
\- Org structure  
\- Role permissions  
\- Document management

\---

\[MODULE 2\] PAYROLL ENGINE (CRITICAL)

Features:  
\- salary structures  
\- tax calculation (Pakistan slabs)  
\- gratuity / PF  
\- loan deduction  
\- arrears & bonuses  
\- final settlement

RULE:  
PayrollService calls:  
→ country\_adapter.tax\_engine()

\---

\[MODULE 3\] COMPLIANCE ENGINE

Features:  
\- FBR Annexure-C  
\- EOBI PR-01  
\- PESSI / SESSI returns  
\- compliance validation BEFORE payroll

SUBSYSTEM:  
Compliance Autopilot

States:  
DRAFT → VALIDATED → SUBMITTED → ACKNOWLEDGED → FAILED

\---

\[MODULE 4\] ATTENDANCE ENGINE

Features:  
\- biometric sync  
\- GPS check-in  
\- face recognition  
\- shift management  
\- overtime rules

ADVANCED:  
\- grace period  
\- late penalty ladder  
\- exception workflows

\---

\[MODULE 5\] LEAVE MANAGEMENT  
\- leave policies  
\- approval flows  
\- payroll linkage

\---

\[MODULE 6\] PERFORMANCE MANAGEMENT  
\- OKRs  
\- 360 feedback  
\- review cycles

\---

\[MODULE 7\] RECRUITMENT  
\- job postings  
\- AI CV parsing  
\- candidate scoring

\---

\[MODULE 8\] FINANCE (EWA)  
\- earned wage access  
\- salary advance  
\- repayment via payroll

\---

\[MODULE 9\] REPORTING → INTELLIGENCE  
\- operational reports  
\- predictive insights  
\- anomaly detection outputs

\============================================================  
05\. AI \+ DECISION SYSTEM (CORE DIFFERENTIATOR)  
\============================================================

\[AI PAYROLL GUARDIAN\]

Detect:  
\- salary anomalies  
\- overtime spikes  
\- missing deductions  
\- ghost employees

Output:  
\- risk score  
\- confidence %  
\- explanation

\---

\[DECISION ENGINE\]

Replace dashboards with:

Decision Object:  
\- trigger  
\- impact  
\- confidence  
\- recommended action  
\- reversibility  
\- expires\_at

Render:  
→ Decision Cards

\---

\[CONFIDENCE SYSTEM\]

Levels:  
\- HIGH (80%+)  
\- MEDIUM (50–79%)  
\- LOW (\<50%)

REQUIRED:  
\- “Why” explanation  
\- audit trail

\---

\[HUMAN-IN-LOOP\]

Required for:  
\- payroll approval  
\- compliance submission  
\- anomaly override

\============================================================  
06\. WHATSAPP HR LAYER (CRITICAL)  
\============================================================

Features:  
\- payslip retrieval  
\- leave application  
\- approval actions  
\- attendance alerts

SYSTEM:  
\- phone ↔ employee mapping  
\- OTP verification  
\- secure messaging

RULE:  
WhatsApp is an extension, not replacement

\============================================================  
07\. COUNTRY-AGNOSTIC RULES (MANDATORY)  
\============================================================

RULE 1:  
NO hardcoded country codes in services

RULE 2:  
All country logic resolved via:  
→ country\_resolver(org\_id)

RULE 3:  
Single source of truth:  
→ country/{country}/

RULE 4:  
Adding new country requires:  
\- new adapter only  
\- NO service change

\============================================================  
08\. COMPLIANCE HARDENING (PAKISTAN)  
\============================================================

REQUIRED:

\- submission lifecycle engine  
\- retry logic  
\- error mapping  
\- audit logs  
\- manual fallback export

ADD:  
\- province-specific rules

\============================================================  
09\. BANKING \+ PAYMENTS  
\============================================================

\- bank-specific file formats  
\- Raast integration  
\- payment tracking  
\- failure recovery

\============================================================  
10\. UX SYSTEM (AURA-ALIGNED)  
\============================================================

PRINCIPLES:

\- decision-first UI  
\- confidence visible  
\- compliance prioritized

COMPONENTS:

\- Decision Cards  
\- Agent Cards  
\- Confidence Module

ANTI-PATTERNS:

\- dashboard overload  
\- hidden compliance  
\- generic AI outputs

\============================================================  
11\. SECURITY \+ AUDIT  
\============================================================

\- role-based access  
\- audit logs (immutable)  
\- compliance traceability  
\- encryption for sensitive data

\============================================================  
12\. SCALABILITY  
\============================================================

\- multi-entity support  
\- multi-country support  
\- modular services  
\- API-first design

\============================================================  
13\. ROADMAP  
\============================================================

PHASE 1 — ARCHITECTURE FIX  
\- remove hardcoding  
\- unify country layer

PHASE 2 — PAKISTAN CORE  
\- compliance hardening  
\- payroll engine upgrade

PHASE 3 — DIFFERENTIATION  
\- AI payroll guardian  
\- WhatsApp HR

PHASE 4 — GLOBAL SCALE  
\- second country adapter

\============================================================  
14\. SUCCESS CRITERIA  
\============================================================

\- zero payroll errors  
\- full compliance automation  
\- decisions replace reports  
\- AI is trusted and explainable  
\- mobile \+ WhatsApp adoption  
\- country abstraction works

\============================================================  
END OF SPEC  
\============================================================