SUPERSEDED: This document is the original product brief. The canonical authority is:
  - Architecture + implementation: v3_extracted/SME-HRMS-main/docs/system/MASTER BUILD SPEC.md  [now backend/docs/system/MASTER BUILD SPEC.md, restructured 2026-06-07]
  - Behavior + compliance rules:   v3_extracted/SME-HRMS-main/docs/system/MASTER BEHAVIOR SPEC.md  [now backend/docs/system/MASTER BEHAVIOR SPEC.md, restructured 2026-06-07]
  - System purpose + principles:   v3_extracted/SME-HRMS-main/docs/system/system-purpose.md  [now backend/docs/system/system-purpose.md, restructured 2026-06-07]
This file is kept as a reference for original intent. Do not edit.
NOTE (normalisation pass, 2026-06-08): the bracketed path updates above extend this banner — itself a previously-sanctioned edit per tracker.md's 2026-06-05 normalisation log (L1039) — without altering the spec content below, which remains frozen per "Do not edit." See Cross-File Finding #3 in ops/normalisation-tracker.md.

============================================================

SYSTEM NAME:
AURA HRMS — Pakistan Compliance OS + AI Workforce Decision System

============================================================
01. SYSTEM PURPOSE
============================================================

Build a system that:

- Guarantees payroll accuracy (0-error target)
- Automates Pakistan compliance (FBR, EOBI, PESSI/SESSI)
- Converts HR from data-entry → decision system
- Supports multi-country WITHOUT changing services

CORE TRUTH:
This is NOT an HR tool.
This is a TRUST INFRASTRUCTURE for workforce operations.

============================================================
02. CORE DESIGN PRINCIPLES
============================================================

P1: Compliance is the product
P2: Payroll must never break
P3: Decisions > dashboards
P4: AI must be explainable and reversible
P5: Country logic must be isolated
P6: System must work on mobile-first environments
P7: WhatsApp is an extension layer, not a feature

============================================================
03. SYSTEM ARCHITECTURE (CANON)
============================================================

LAYER 1 — DATA
- employees
- organizations
- legal_entities
- locations (country + province aware)
- payroll_records
- attendance_logs
- compliance_records
- audit_logs (immutable)

---

LAYER 2 — DOMAIN
- payroll
- compliance
- attendance
- leave
- performance
- recruitment
- finance (EWA)

Each domain:
→ owns business logic
→ exposes interfaces

---

LAYER 3 — COUNTRY ABSTRACTION

country/base/
  - tax_engine_interface
  - compliance_engine_interface
  - payroll_rules_interface

country/pakistan/
  - adapter
  - tax_engine
  - compliance_engine
  - payroll_rules

RULE:
ALL statutory logic lives here ONLY

---

LAYER 4 — SERVICES

services/
  - payroll_service
  - compliance_service
  - attendance_service
  - decision_engine
  - insight_engine

RULE:
- orchestration ONLY
- NO country logic

---

LAYER 5 — INTEGRATIONS

- FBR adapter
- EOBI adapter
- PESSI/SESSI adapter
- bank adapters
- Raast adapter
- WhatsApp API

---

LAYER 6 — EXPERIENCE

- HR admin console
- Manager dashboard (decision-first)
- Employee portal
- Mobile layer (low bandwidth)
- WhatsApp interface

============================================================
04. CORE CAPABILITIES (FULL SYSTEM)
============================================================

[CAPABILITY 1] CORE HR
- employee profiles (dynamic schema)
- org hierarchy (multi-entity)
- document management
- role-based access

---

[CAPABILITY 2] PAYROLL ENGINE (CRITICAL)

- salary structures
- allowances/deductions
- tax calculation (Pakistan slabs)
- gratuity / PF
- loans & advances
- arrears & bonuses
- final settlement

RULE:
PayrollService MUST call:
→ country_adapter.tax_engine

---

[CAPABILITY 3] COMPLIANCE ENGINE (CORE)

Outputs:
- FBR Annexure-C
- EOBI PR-01
- PESSI / SESSI returns

Features:
- validation BEFORE payroll
- submission lifecycle
- audit logs

STATES:
DRAFT → VALIDATED → SUBMITTED → ACK → FAILED → RETRY

---

[CAPABILITY 4] ATTENDANCE ENGINE

- biometric integration
- GPS check-in
- face recognition
- shift management
- overtime engine

ADVANCED:
- grace periods
- late penalty ladder
- missing punch resolution
- multi-shift templates

---

[CAPABILITY 5] LEAVE MANAGEMENT

- leave policies
- approval workflows
- payroll linkage

---

[CAPABILITY 6] PERFORMANCE MANAGEMENT

- OKRs
- 360 feedback
- performance cycles

---

[CAPABILITY 7] RECRUITMENT

- job posting
- CV parsing
- candidate scoring
- interview workflows

---

[CAPABILITY 8] FINANCIAL (EWA)

- earned wage access
- salary advances
- payroll deduction repayment

---

[CAPABILITY 9] BANKING + DISBURSEMENT

- bank-specific salary files
- Raast payouts
- payment tracking
- reconciliation engine

---

[CAPABILITY 10] REPORTING → INTELLIGENCE

- operational reports
- compliance reports
- predictive insights
- anomaly signals

============================================================
05. AI + DECISION SYSTEM (DIFFERENTIATOR)
============================================================

[AI PAYROLL GUARDIAN]

Detect:
- salary anomalies
- overtime spikes
- missing deductions
- ghost employees

Output:
- risk_score
- confidence
- explanation
- anomaly_type

---

[DECISION ENGINE]

Decision Object:
- trigger
- impact
- confidence
- recommended_action
- reversibility
- expires_at

Render:
→ Decision Cards

---

[CONFIDENCE SYSTEM]

- HIGH (80%+)
- MEDIUM (50–79%)
- LOW (<50%)

MANDATORY:
- explanation
- audit trail

---

[HUMAN-IN-LOOP]

Required for:
- payroll approval
- compliance submission
- anomaly override

============================================================
06. WHATSAPP HR LAYER
============================================================

FUNCTIONS:
- payslip retrieval
- leave application
- attendance alerts
- approval actions
- payroll notifications

SYSTEM REQUIREMENTS:
- phone ↔ employee mapping
- OTP verification
- secure message handling

RULE:
WhatsApp = extension of HRMS

============================================================
07. COUNTRY-AGNOSTIC RULES (MANDATORY)
============================================================

R1: NO hardcoded country in services
R2: Resolver is ONLY entry point
R3: ALL country logic in:
    country/{country}/
R4: Services NEVER import country modules
R5: Adding new country:
    → adapter only
    → no service changes

============================================================
08. PAKISTAN-SPECIFIC REQUIREMENTS
============================================================

MUST SUPPORT:

- FBR tax compliance
- EOBI contributions
- PESSI / SESSI variations
- CNIC validation
- multi-province rules

CRITICAL:
Compliance must be:
- validated BEFORE payroll
- auditable AFTER submission

============================================================
09. UX / SYSTEM BEHAVIOR RULES
============================================================

DO:
- show actions (not data)
- show what needs fixing
- show why
- show confidence

DO NOT:
- overload dashboards
- hide compliance logic
- show raw data without decisions

============================================================
10. SECURITY + AUDIT
============================================================

- role-based access control
- immutable audit logs
- compliance traceability
- sensitive data encryption

============================================================
11. SCALABILITY
============================================================

- multi-entity support
- multi-country expansion
- modular services
- API-first architecture

============================================================
12. ROADMAP (EXECUTION ORDER)
============================================================

PHASE 1:
- architecture cleanup
- country abstraction enforcement

PHASE 2:
- Pakistan payroll + compliance hardening

PHASE 3:
- decision engine + AI guardian

PHASE 4:
- WhatsApp + mobile expansion

PHASE 5:
- multi-country rollout

============================================================
13. SUCCESS CRITERIA
============================================================

SYSTEM IS COMPLETE WHEN:

- payroll errors ≈ 0
- compliance fully automated
- decisions replace dashboards
- AI outputs are explainable
- WhatsApp fully usable
- country abstraction works cleanly

============================================================
END OF SPEC
============================================================