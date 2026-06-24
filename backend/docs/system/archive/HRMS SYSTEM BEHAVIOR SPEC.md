> **SUPERSEDED** — This document is an archived draft. Canonical authority: `docs/system/MASTER BEHAVIOR SPEC.md`
> Do not edit. Retained for historical reference only.

TITLE:  
HRMS SYSTEM BEHAVIOR SPEC — PAKISTAN-FIRST \+ AI DECISION SYSTEM

\============================================================  
01\. CORE BEHAVIOR PHILOSOPHY  
\============================================================

B1: System must prioritize correctness over speed  
B2: System must block invalid actions (not allow and fix later)  
B3: System must explain every critical decision  
B4: System must surface actions, not raw data  
B5: System must reduce user anxiety (especially payroll/compliance)  
B6: System must default to safe outcomes

PRIMARY BEHAVIOR MODE:  
→ PREVENTION \> DETECTION \> CORRECTION

\============================================================  
02\. PAYROLL BEHAVIOR  
\============================================================

WHEN payroll is initiated:

STEP 1:  
System validates:  
\- employee data completeness  
\- CNIC validity  
\- tax configuration  
\- attendance consistency  
\- compliance readiness

IF ANY FAILS:  
→ BLOCK payroll  
→ return:  
  \- error type  
  \- affected employees  
  \- fix instructions

\---

STEP 2:  
System calculates:  
\- gross salary  
\- deductions  
\- tax (via country adapter)  
\- net salary

\---

STEP 3:  
System runs anomaly checks:  
\- salary spikes  
\- missing deductions  
\- abnormal overtime

IF anomaly detected:  
→ generate decision object  
→ require approval if high risk

\---

STEP 4:  
System generates:  
\- payslips  
\- payroll summary  
\- compliance outputs

\---

STEP 5:  
System triggers:  
→ compliance workflow  
→ bank disbursement

\---

RULES:

\- payroll cannot finalize if compliance validation fails  
\- payroll must produce audit record  
\- payroll must be reproducible

\============================================================  
03\. COMPLIANCE BEHAVIOR  
\============================================================

WHEN compliance is triggered:

STEP 1:  
Validate statutory data:  
\- CNIC  
\- salary data  
\- contribution eligibility

\---

STEP 2:  
Generate outputs:  
\- FBR file  
\- EOBI report  
\- PESSI/SESSI report

\---

STEP 3:  
Assign state:

DRAFT → VALIDATED → SUBMITTED → ACKNOWLEDGED → FAILED → RETRY

\---

STEP 4:  
Handle errors:

IF submission fails:  
→ classify error:  
  \- data issue  
  \- system issue  
  \- external (portal)

→ provide:  
  \- correction steps  
  \- retry option

\---

RULES:

\- compliance must run before payroll finalization  
\- all submissions must be logged  
\- system must support manual fallback

\============================================================  
04\. ATTENDANCE BEHAVIOR  
\============================================================

WHEN attendance data is processed:

\- validate timestamps  
\- detect missing punches  
\- apply shift rules  
\- calculate overtime

\---

IF inconsistency:  
→ flag employee  
→ create resolution task

\---

RULES:

\- attendance must reconcile with payroll  
\- unresolved issues must block payroll if critical

\============================================================  
05\. DECISION SYSTEM BEHAVIOR  
\============================================================

WHEN system detects anomaly or issue:

CREATE DECISION OBJECT:

{  
  trigger,  
  impact,  
  confidence,  
  explanation,  
  recommended\_action,  
  reversibility,  
  expires\_at  
}

\---

BEHAVIOR:

\- high-risk → require approval  
\- medium-risk → suggest action  
\- low-risk → auto-resolve (if safe)

\---

RULES:

\- every decision must be explainable  
\- every decision must be auditable  
\- no silent system actions

\============================================================  
06\. AI BEHAVIOR  
\============================================================

AI MUST:

\- explain outputs  
\- provide confidence score  
\- avoid black-box decisions

AI MUST NOT:

\- auto-approve high-risk actions  
\- override compliance rules  
\- act without traceability

\---

AI OUTPUT FORMAT:

{  
  prediction,  
  confidence,  
  explanation,  
  supporting\_data  
}

\============================================================  
07\. WHATSAPP / MOBILE BEHAVIOR  
\============================================================

WHEN user interacts via WhatsApp:

\- identify user via phone mapping  
\- authenticate (OTP if required)  
\- route to correct function

\---

SUPPORTED ACTIONS:

\- view payslip  
\- apply leave  
\- receive alerts  
\- approve actions

\---

RULES:

\- no sensitive data without authentication  
\- responses must be concise  
\- support low-bandwidth usage

\============================================================  
08\. ERROR HANDLING BEHAVIOR  
\============================================================

ALL ERRORS MUST:

\- be classified  
\- include explanation  
\- include resolution steps

\---

ERROR TYPES:

\- validation error  
\- system error  
\- external dependency error

\---

RULES:

\- no generic errors  
\- no silent failures

\============================================================  
09\. AUDIT BEHAVIOR  
\============================================================

SYSTEM MUST LOG:

\- payroll runs  
\- compliance submissions  
\- decision actions  
\- user overrides

\---

AUDIT RECORD MUST INCLUDE:

\- timestamp  
\- actor  
\- action  
\- affected entities  
\- result

\============================================================  
10\. SECURITY BEHAVIOR  
\============================================================

\- enforce role-based access  
\- protect sensitive data  
\- log all critical actions

\---

RULES:

\- no unauthorized data access  
\- no plaintext sensitive storage

\============================================================  
11\. USER EXPERIENCE BEHAVIOR  
\============================================================

SYSTEM SHOULD:

\- show what needs action  
\- show why it matters  
\- show how to fix

SYSTEM SHOULD NOT:

\- overwhelm with data  
\- hide critical issues  
\- rely on dashboards alone

\============================================================  
12\. SYSTEM DEFAULTS  
\============================================================

DEFAULT BEHAVIOR:

\- safe over risky  
\- explicit over implicit  
\- guided over manual

\============================================================  
END OF BEHAVIOR SPEC  
\============================================================