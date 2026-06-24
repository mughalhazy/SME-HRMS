# MASTER BEHAVIOR SPECIFICATION
## AURA HRMS — Unified System Behavior: Runtime Rules, Market Grounding, and Audit Canon
### v1.0 — Merged from MARKET-VALIDATED BEHAVIOR SPEC v1.0 + HRMS SYSTEM BEHAVIOR SPEC

---

## Purpose

This document is the single authoritative reference for system behavior in AURA HRMS.

It answers three questions for every major system behavior:
- **WHAT** the system must do (runtime rules, step flows, states)
- **HOW** it must do it (constraints, guards, classification rules)
- **WHY** it must do it this way (Pakistan market evidence, validated pain points)

**Sources merged:**
- `MARKET-VALIDATED BEHAVIOR SPEC v1.0` — behavior grounded in market research, gap closure, and competitive differentiation
- `HRMS SYSTEM BEHAVIOR SPEC` — runtime step flows, audit canon, security rules, system defaults

**Does not replace:** `MASTER BUILD SPEC.md` (architecture contracts, acceptance criteria, full schema definitions).

**Primary mode of operation:** PREVENTION > DETECTION > CORRECTION

The market validates this order. Buyers pay for systems that prevent errors, not systems that detect them after payroll has run.

---

## 01. Core Behavior Philosophy

### Runtime Rules (B1–B6)

| Code | Rule |
|---|---|
| B1 | System must prioritize correctness over speed |
| B2 | System must block invalid actions — never allow and fix later |
| B3 | System must explain every critical decision |
| B4 | System must surface actions, not raw data |
| B5 | System must reduce user anxiety, especially in payroll and compliance |
| B6 | System must default to safe outcomes |

### Market Grounding

| Behavior Principle | Market Evidence |
|---|---|
| Block invalid actions — never allow and fix later | P1: payroll errors are the #1 buyer complaint; corrections cause real financial and legal damage |
| Explain every critical decision | P4: lack of trust in system outputs is endemic; unexplained outputs are immediately overridden manually |
| Surface actions, not raw data | P6: manager blindness — managers receive only reports; they need prompts, not dashboards |
| Reduce compliance anxiety visibly | P2: compliance confusion is the #2 pain point; operators need to see compliance status without digging |
| Support low-bandwidth and mobile-first | P5: employees in Pakistan access everything via WhatsApp and mobile; desktop-only is a non-starter |
| Manual fallback must always exist | P7: government portals fail regularly; vendors without manual fallback lose customer trust instantly |
| Trust must be earned through correctness | GAP 6: no current system guarantees correctness — this is the single largest whitespace in the market |

---

## 02. Trust-First Behaviors

Market evidence: Customer trust is the single most cited buying criterion in Pakistan. P4 (lack of trust) is the fourth validated pain point. No current vendor has solved it.

### 2.1 Pre-Run Confidence Signal
Before every payroll run, the system must surface:
- Number of employees with incomplete statutory data
- Number of anomalies detected by the Payroll Guardian
- Compliance readiness status (ready / issues found)
- A single "safe to run" or "issues require review" signal

**Why:** Buyers want to know the system caught problems before they had to. Confidence comes from visible prevention, not invisible processing.

### 2.2 Anomaly Report Before Finalization
Every payroll run must be preceded by an AI-generated anomaly report covering:
- Salary spikes vs previous period
- Overtime outside configured thresholds
- Missing or under-computed tax deductions
- Employees flagged as potential ghost employees

The operator must acknowledge this report before finalization proceeds.

**Why:** Customer sentiment data shows "AI features seen as marketing fluff." The antidote is AI that visibly catches real problems before money moves — not AI that summarizes after the fact.

### 2.3 Reproducibility on Demand
Any payroll run must be reproducible from its audit record with identical outputs given identical inputs.

**Why:** Auditors and finance teams regularly re-verify payroll months later. A system that cannot reproduce its own outputs cannot be trusted.

### 2.4 Confidence Score on Every AI Output
Every AI-generated output (anomaly flag, attrition risk, compliance risk) must display:
- Confidence score and tier (HIGH / MEDIUM / LOW)
- Plain-language explanation
- Supporting signals that drove the output

**Why:** UX design principle from market research — "use confidence scores for AI-generated payroll audits." This is the difference between trusted AI and marketing theater.

---

## 03. Payroll Behavior

Market evidence: P1 (payroll errors) is the most damaging pain point. Pakistan tax slabs change with each Finance Act. Gratuity, PF, bonus taxation, and arrears are all high-error areas.

### Runtime Flow — Payroll Run

**STEP 1 — Pre-flight validation**

System validates:
- Employee data completeness
- CNIC validity (must be 13-digit numeric)
- Tax configuration
- Attendance consistency
- Compliance readiness

If any fails:
- Block payroll
- Return: error type, affected employees, exact fix instructions

**STEP 2 — Calculation**

System calculates:
- Gross salary
- Deductions (leave, loans, advances)
- Tax via country adapter (Pakistan: current FBR slab + filer/non-filer status)
- Net salary

**STEP 3 — Anomaly check**

System runs Payroll Guardian checks:
- Salary spikes vs previous period
- Missing deductions
- Abnormal overtime
- Potential ghost employees

If anomaly detected:
- Generate decision object
- Require operator approval if high risk (see §06 Decision and AI Behavior)

**STEP 4 — Output generation**

System generates:
- Payslips (including tax computation breakdown, leave deduction detail)
- Payroll summary
- Compliance outputs

**STEP 5 — Downstream trigger**

System triggers:
- Compliance workflow (§04)
- Bank disbursement (§08)

**Rules:**
- Payroll cannot finalize if compliance validation fails
- Payroll cannot proceed if any STEP 1 check fails — no partial runs
- Payroll must produce an immutable audit record (see §10)
- Payroll must be reproducible from its audit record

### 3.1 Statutory Completeness Gate
Payroll must refuse to proceed if any employee in the batch has:
- Missing or invalid CNIC (not 13-digit numeric)
- Missing bank details when disbursement mode requires bank transfer
- Missing EOBI number for EOBI-enrolled employees
- Missing province assignment (required for social security routing)

The system must return a specific list of affected employees and the exact field missing — not a generic error.

**Why:** Buyers need to fix specific data, not search for it. "3 employees have missing EOBI numbers" is actionable. "Validation failed" is not.

### 3.2 Tax Computation Transparency
For every payroll record the system must show:
- Gross taxable income
- Exempt allowances applied (before tax base)
- Tax slab applied and fiscal year
- Filer / non-filer status and surcharge if applicable
- Final tax deducted

**Why:** FBR enforcement has intensified. HR officers need to verify tax computation line by line, not trust a black-box result.

### 3.3 Leave Effect Visible in Payslip
When unpaid leave reduces net pay, the payslip must show:
- Number of unpaid leave days
- Daily rate applied
- Deduction amount

**Why:** Attendance vs payroll mismatch (P3) is a top source of employee disputes. Showing the calculation explicitly eliminates the dispute before it starts.

### 3.4 Payroll Cannot Silently Skip
If any component (tax engine, leave deduction, anomaly check) fails:
- System must block finalization
- Error must name the failing component and reason
- Partial payroll runs are not permitted

**Why:** Silent failures are the primary cause of payroll errors that go undetected until audit. The market has zero tolerance for this — it is the core trust failure of legacy systems.

---

## 04. Compliance Behavior

Market evidence: P2 (compliance confusion) is validated across all segments. GAP 1 (Compliance Autopilot) is the largest unmet need — no system fully automates the FBR/EOBI/PESSI lifecycle.

### Runtime Flow — Compliance Run

**STEP 1 — Statutory data validation**

Validate:
- CNIC
- Salary data
- Contribution eligibility (EOBI, PESSI/SESSI per province)

**STEP 2 — Output generation**

Generate:
- FBR Annexure-C file
- EOBI PR-01 report
- PESSI C-1 / SESSI C-1 report per province

**STEP 3 — State assignment and submission**

State machine:
```
DRAFT → VALIDATED → SUBMITTED → ACKNOWLEDGED
                             ↓
                           FAILED → RETRY → MANUAL
```

MANUAL state: operator has recorded manual submission with reference number and notes. This is a terminal success state, not a failure state.

**STEP 4 — Error handling**

If submission fails, classify error:
- `data_error` — missing or invalid employee data (operator can fix)
- `rules_error` — contribution rule or rate mismatch (HR / config fix required)
- `external_dependency_error` — portal unavailable or rejected by external system (retry or manual fallback)
- `operator_error` — incorrect action taken by operator (guided correction)

Provide for each:
- Correction steps
- Who can fix it
- Retry or manual fallback option

**Rules:**
- Compliance must run before payroll finalization — this gate is mandatory and cannot be bypassed
- All submissions must be logged with actor, timestamp, state, and outcome
- System must always offer manual fallback when automated submission fails

### 4.1 Compliance Runs Before Payroll — Always
Compliance validation is not optional and cannot be bypassed. The operator cannot finalize payroll without compliance clearing the batch.

**Why:** The compliance-payroll gate is the product's core trust promise. Bypassing it would make the system indistinguishable from legacy vendors.

### 4.2 Autopilot Mode with Human Escalation
The system must attempt automated compliance in this order:
1. Validate statutory data automatically
2. Generate required outputs (FBR Annexure-C, EOBI PR-01, PESSI/SESSI C-1)
3. Attempt portal submission where API is available
4. On failure — classify the error, explain it, and offer retry or manual fallback

**Why:** GAP 1 is "no system fully automates the filing lifecycle." The autopilot pattern — automated by default, human-escalated on failure — is the behavior that closes this gap.

### 4.3 Province-Aware Routing is Silent and Automatic
The system must route social security contributions to the correct body based on employee province without operator intervention:
- Punjab → PESSI
- Sindh → SESSI
- Others → configurable / extensible

**Why:** Provincial fragmentation is one of the most cited compliance pain points. Operators should not have to know which province maps to which body — the system must know.

### 4.4 Manual Fallback is a First-Class Feature
When automated submission fails and retry is exhausted, the system must:
- Offer a manual submission recording path
- Accept a reference number from the operator
- Record the manual submission with actor, timestamp, and notes
- Transition the submission to MANUAL state (not FAILED)

**Why:** P7 (support reliability) — government portals are unreliable. Operators need a documented escape hatch, not a dead end. A FAILED state with no path forward destroys trust.

### 4.5 Error Messages Must Be Actionable
Every compliance error must include:
- Error type (data / rules / external / operator)
- Affected employee(s) or field(s)
- Exact correction step required
- Who can fix it (HR / IT / operator / retry)

**Why:** P2 — compliance confusion is driven by opaque error messages. "EOBI submission failed" is useless. "Employee EMP-042 missing EOBI number — update in employee profile" is actionable.

---

## 05. Attendance Behavior

Market evidence: P3 (attendance vs payroll mismatch) is validated as a top dispute source, especially in industrial Punjab (Faisalabad/Sialkot) where shift-based manufacturing is dominant.

### Runtime Processing

When attendance data is processed:
- Validate timestamps
- Detect missing punches
- Apply shift rules
- Calculate overtime

If inconsistency detected:
- Flag employee with specific dates and shifts affected
- Create resolution task
- Show estimated payroll impact of each gap

**Rules:**
- Attendance must reconcile with payroll before finalization
- Unresolved missing punches must block payroll if critical
- Resolution or explicit operator acknowledgment required before proceeding

### 5.1 Biometric and GPS Data are First-Class Sources
The system must treat biometric sync, GPS check-in, face recognition, and mobile attendance as equivalent valid sources — not as integrations that need manual review to count.

**Why:** The market is rapidly moving from biometric-only to geo-fencing and face recognition. Vendors that treat these as secondary data sources create the very mismatch employees dispute.

### 5.2 Missing Punches Surface Before Payroll
Missing punch detection must run before the payroll gate, not after. The system must:
- Flag employees with unresolved missing punches
- Show the exact dates and shifts affected
- Present the estimated payroll impact of each gap
- Allow the operator to resolve or escalate before proceeding

**Why:** Discovering missing punches after payroll has run causes retrospective corrections, which are the top source of employee distrust.

### 5.3 Overtime Disputes Must Be Pre-empted
For every overtime claim, the system must show:
- Raw attendance records supporting the claim
- Shift rule applied
- Hours computed
- Any threshold exceeded

**Why:** Overtime disputes are the #1 attendance grievance in industrial settings. Showing the calculation explicitly before payroll runs eliminates the dispute at source.

### 5.4 Shift-Based Workforce *(Target — v1 Foundation Only)*
Shift templates, roster management, and multi-shift attendance are first-class design targets. The current v1 implementation provides the attendance data model and rules engine foundation. Full shift template management and piece-rate payroll calculation are planned capabilities for a future roadmap increment — they are not implemented in v1.

**Why:** Faisalabad and Sialkot (industrial Punjab) represent a major market segment. Systems that cannot handle factory-floor shift patterns lose this segment entirely.

---

## 06. Decision and AI Behavior

Market evidence: P6 (manager blindness). GAP 2 (AI Payroll Auditor — no explainable anomaly detection exists). GAP 3 (Decision-First UX — dashboards dominate, decisions missing). Top negative theme: "AI features seen as marketing fluff."

### Decision Object — Full Schema

Every decision created by the system must conform to this schema:

```
{
  id,                  // unique identifier
  source_domain,       // which domain created this (payroll, compliance, attendance, etc.)
  trigger,             // what caused the decision
  impact_scope,        // who/what is affected
  severity,            // critical | notify | passive
  confidence,          // 0.0–1.0
  explanation,         // plain-language reason
  supporting_signals,  // specific data points that triggered the flag
  suggested_action,    // what the operator should do
  recommended_action,  // system's preferred resolution
  reversibility,       // reversible | irreversible | conditional
  expires_at,          // when the decision expires
  status,              // open | approved | rejected | expired | auto_resolved
                       // NOTE (G50): canonical status values from decision_engine.py are
                       // active | resolved | expired — see docs/canon/decision-system.md
  created_at,
  resolved_at,
  actor                // who resolved it (null if unresolved)
}
```

**Severity behavior:**
- `critical` — block further processing, require explicit operator approval
- `notify` — non-blocking, surface to relevant actor with suggested action
- `passive` — logged only, no action required

### AI Output Format — Canonical

Every AI-generated output must include:

```
{
  prediction,          // what the AI detected or predicted
  confidence,          // numeric score 0.0–1.0
  explanation,         // plain-language explanation
  supporting_signals,  // the specific signals that drove the output (not raw data)
  suggested_action     // what the system recommends doing
}
```

Note: The field `supporting_data` (used in older internal documentation) is **deprecated**. The canonical fields are `supporting_signals` and `suggested_action`.

### AI Must

- Explain all outputs in plain language
- Provide a confidence score with tier (HIGH ≥ 0.7, MEDIUM 0.5–0.69, LOW < 0.5)
- Never present LOW confidence outputs as requiring action — label them informational only
- Never auto-approve high-risk actions
- Never override compliance rules
- Never act without traceability (every AI action produces an audit record)

### 6.1 Decisions Reach Managers Proactively
Decision cards must be delivered to the relevant manager or HR officer without requiring them to log in and search. Critical decisions must generate a notification via the operator's configured channel.

**Why:** P6 — managers are blind because information is buried in dashboards. Proactive delivery of decisions is the behavior that closes this gap.

### 6.2 Every Decision Card Must Be Self-Contained
A decision card must contain everything needed to act on it without clicking elsewhere:
- What happened (trigger)
- Why it matters (impact and severity)
- What confidence the system has (score + tier)
- Why the system thinks this (explanation + supporting signals)
- What to do next (suggested action)
- Whether the action can be reversed (reversibility)
- When it expires

**Why:** GAP 3 — current systems require managers to interpret raw data. A self-contained decision card makes the system the analyst, not the manager.

### 6.3 AI Must Not Create New Anxiety
AI outputs that are unexplained create more anxiety than they resolve — especially for payroll officers already under compliance pressure. Every AI flag must include:
- A plain-language reason why it was flagged
- The specific data point(s) that triggered it
- Whether it is blocking or advisory

**Why:** "AI features are sometimes seen as marketing fluff with limited practical utility" — this is the top AI-related negative sentiment. Explainability is not a nice-to-have; it is what separates trusted AI from anxiety-inducing black boxes.

### 6.4 Low-Confidence Outputs Must Be Clearly Marked
Outputs with confidence below 0.5 (LOW tier) must be explicitly labeled as informational only. The system must not present low-confidence signals as requiring action.

**Why:** If managers act on low-confidence signals and the signal was wrong, trust in the entire AI layer collapses. Better to under-claim than to over-promise.

---

## 07. WhatsApp and Mobile Behavior

Market evidence: P5 (poor employee access). GAP 5 (WhatsApp HR layer — almost no system uses messaging effectively). "Ignoring WhatsApp culture" is the top mistake current vendors make. 70–80% of the workforce uses WhatsApp as their primary communication channel.

### Runtime Flow — WhatsApp Interaction

When user interacts via WhatsApp:
1. Identify user via phone number mapping
2. Authenticate (OTP or PIN if sensitive action)
3. Route to correct domain function (same services as web portal — no independent logic)
4. Return response in under 3 message exchanges for common tasks

### Supported Actions

- View payslip (current and historical)
- Apply for leave and check status
- View attendance status
- Receive compliance and payroll alerts
- Approve actions (for managers)

**Rules:**
- No sensitive data without authentication
- Responses must be concise — text-first, no image-only responses
- Full low-bandwidth support (completable on basic smartphone over mobile data)
- WhatsApp routes to the same domain services as the web portal — no independent data or logic

### 7.1 WhatsApp is Not a Demo Feature
WhatsApp access must support the complete employee self-service loop — payslip, leave, attendance, alerts, approvals.

**Why:** A WhatsApp integration that only shows payslips is not meaningfully different from an email. Employees will stop using it within weeks. Full loop support makes it sticky.

### 7.2 Responses Must Work on Low Bandwidth
Every WhatsApp response must:
- Be completable in under 3 message exchanges for common tasks
- Contain no large attachments unless explicitly requested
- Use text-first formatting (no image-only responses)

**Why:** Factory floor and field workers in Pakistan often use basic smartphones on mobile data. A WhatsApp HR bot that requires fast internet defeats its own purpose.

### 7.3 Sensitive Actions Require Verification
Any WhatsApp action that involves personal data (payslip) or financial action (leave with pay impact) must require OTP or PIN verification before responding.

**Why:** Phone numbers are shared in some contexts. A payslip sent to the wrong person is a data breach. Trust requires that sensitive data is protected even on the most accessible channel.

### 7.4 WhatsApp Must Not Replace Core Logic
WhatsApp is an access channel only. It routes to the same domain services as the web portal. It does not contain independent logic, independent data stores, or independent validation rules.

**Why:** The vendor mistake of treating WhatsApp as a separate product leads to inconsistent behavior — leave approved on WhatsApp but not reflected in payroll. This destroys trust faster than having no WhatsApp at all.

---

## 08. Bank and Disbursement Behavior

Market evidence: Bank/salary disbursement friction is a cited pain point. Raast instant payments are a strategic opportunity. Bank-specific file format errors are a top support issue.

### Disbursement State Machine

```
PENDING → GENERATED → SUBMITTED → SENT → ACCEPTED → RECONCILED
                                       ↓
                                    REJECTED → RETRY
                                             → FAILED (if exhausted)
```

### 8.1 Salary File Format is the Bank's Format, Not a Generic CSV
The system must generate bank-specific salary files per the format each bank requires. Generic CSV output that requires manual reformatting is a support burden and a source of disbursement failures.

**Why:** Every manual reformatting step is a failure point and a support ticket.

### 8.2 Raast Path is Real, Not a Placeholder
Where Raast is configured, the system must generate a valid Raast-format payment batch — not a stub or a note. Raast disbursement is a real competitive advantage in the Pakistan market for instant salary crediting.

**Why:** Raast is the payment rail that makes instant salary crediting possible — a genuine competitive differentiator for attracting modern employers.

### 8.3 Disbursement Failures Must Have a Recovery Path
When a salary file is rejected by the bank, the system must:
- Record the rejection with reason
- Transition to REJECTED state (not silently fail)
- Present the operator with correction steps
- Allow resubmission without recreating the entire batch

**Why:** A rejected salary file on payday is a crisis. The system's behavior in that moment determines whether the operator trusts it or abandons it.

---

## 09. Error and Recovery Behavior

Market evidence: P7 (support reliability) — local vendors praised for responsive localized help. Global vendors criticized for leaving operators stranded on portal issues.

### Error Classification — System-Wide

All system errors must be classified into one of these types:

| Type | Description | Who can fix |
|---|---|---|
| Validation error | Data does not meet required format or rules | Operator / HR |
| System error | Internal processing failure | IT / retry |
| External dependency error | External portal, API, or service unavailable | Retry or manual fallback |

For compliance service specifically, the canonical 4-type classification applies (see §04): `data_error`, `rules_error`, `external_dependency_error`, `operator_error`.

**Rules:**
- No generic errors
- No silent failures
- Every error must include: what failed, why it failed, who can fix it, what to do right now

### 9.1 Every Error Tells the Operator What to Do Next
No error in the system should leave the operator at a dead end. Every error must include:
- What failed (component and context)
- Why it failed (root cause in plain language)
- Who can fix it (HR / IT / operator / external)
- What to do right now (specific next step)

**Why:** Operators under payroll pressure need resolution paths, not error codes. This is the behavior that replaces the need for a support call.

### 9.2 External Portal Failures Do Not Block the Operator
When FBR, EOBI, or SESSI portals are unavailable:
- System continues to generate and store the correct output artifacts
- System transitions to MANUAL state with clear recording path
- System notifies the operator with the exact reference data needed for manual submission

**Why:** Government portal reliability in Pakistan is inconsistent. A system that blocks the entire compliance workflow when a portal is down is unusable in the real world. The manual fallback is not a fallback — it is a production requirement.

---

## 10. Audit Behavior

Every significant system action must produce an immutable audit record. This is the mechanism that enables reproducibility (§02.3), compliance accountability (§04), and decision traceability (§06).

### What Must Be Logged

- All payroll runs (initiation, each step result, finalization or failure)
- All compliance submissions (each state transition, actor, outcome)
- All decision object actions (creation, approval, rejection, expiry, auto-resolution)
- All user overrides of system-generated values
- All WhatsApp actions involving sensitive data or approvals
- All bank disbursement state transitions

### Audit Record Fields

Every audit record must include:

| Field | Description |
|---|---|
| timestamp | ISO 8601 datetime, server time |
| actor | user ID and role who triggered the action |
| action | what was done (specific — not "updated") |
| affected_entities | which employees, batches, or records were affected |
| result | outcome (success / failure / partial) and relevant output reference |

### Audit Rules

- Audit records are immutable — they cannot be edited or deleted by any role
- All audit records must be queryable by actor, date range, action type, and affected entity
- Payroll audit records must contain sufficient data to reproduce the run
- Any user override must include a reason field (mandatory)

---

## 11. Security Behavior

### Access Control

- Enforce role-based access control (RBAC) across all system actions
- No user may access data outside their assigned organization, entity, or role scope
- No unauthorized data access — principle of least privilege applies

### Data Protection

- No sensitive data stored in plaintext (CNICs, bank account numbers, salaries, tax details)
- No sensitive data in logs — log references and IDs, not values
- All critical actions logged to the audit trail (§10)

### Rules

- Role boundaries are enforced at the service layer, not just the UI
- WhatsApp interactions involving sensitive data require authentication before any data is returned (§07.3)
- Compliance outputs (FBR, EOBI files) are accessible only to authorized HR and finance roles

---

## 12. UX Behavior Mandates

Market evidence: "UI clutter" and "over-complicating the UI" are top negative themes. "Anti-pattern: hiding compliance settings behind deep menus." Designing for admin power users while ignoring average employees is the #2 vendor mistake.

### System Should

- Show what needs action (decision cards, not reports)
- Show why it matters (severity and impact, not raw data)
- Show how to fix (resolution steps, not just error codes)

### System Should Not

- Overwhelm with data
- Hide critical issues behind navigation
- Rely on dashboards alone for operator visibility

### 12.1 Compliance Status is Always Visible
Compliance status for the current payroll period must be visible on the primary HR dashboard without any navigation. It must not be buried in a submenu.

**Why:** Compliance anxiety is the core emotional driver of buying decisions. If the system makes compliance invisible in the UI, it fails its core promise.

### 12.2 Actions Always Have a Next Step
Every screen that shows a problem must also show a resolution path. The system must not display issues without also displaying what to do about them.

**Why:** "Dashboard overload with no actionable path" is explicitly identified as the anti-pattern to avoid. Action-first UX is the direct response to P6 (manager blindness).

### 12.3 Employee-Facing Screens Must Be Simple
Employee-facing interfaces (payslip, leave, attendance) must be completable by a non-technical user in under 30 seconds for the most common tasks. No employee should need training to view their own payslip.

**Why:** "Designing for power users while ignoring the average employee" is the top UX mistake in the market. The WhatsApp and mobile channels exist precisely because the web portal fails this standard for most employees.

### 12.4 AI Confidence Must Be Visible, Not Hidden
Confidence scores and AI explanations must be shown next to AI-generated outputs — not accessible only via a "Details" click. If the operator cannot see why the system flagged something, they will not trust the flag.

**Why:** "Use confidence scores for AI-generated payroll audits" — this is the market-validated design principle. Hiding confidence scores defeats the trust-building purpose of showing them.

---

## 13. System Defaults

When any behavior can go one of two ways and the spec does not explicitly prescribe, the system must default to:

| Default | Over |
|---|---|
| Safe | Risky |
| Explicit | Implicit |
| Guided | Manual |

**Application:**
- When a tax slab is ambiguous — apply the more conservative rate, flag for review
- When a compliance state is uncertain — stay in VALIDATED, do not auto-advance to SUBMITTED
- When an AI confidence score is borderline — label LOW, not MEDIUM
- When a user attempts an action without required data — block with explanation, not silent skip

---

## 14. Multi-Entity and Regional Behavior

Market evidence: Karachi — enterprise and multi-entity. Industrial Punjab — shift-based and attendance-heavy. Islamabad — secure cloud hosting. These are distinct use cases, not variations of the same use case.

### 14.1 Multi-Entity is a Core Scenario
Running payroll across multiple legal entities with different compliance obligations in the same run must be a supported first-class operation — not a workaround.

**Why:** Karachi-based organizations are predominantly multi-entity. A system that requires separate logins or separate runs per entity loses the enterprise segment.

### 14.2 Province Determines Compliance Routing Automatically
When an organization has employees in multiple provinces, the system must apply the correct provincial social security rules per employee automatically — not per organization setting.

**Why:** A Lahore-headquartered company with Karachi employees needs PESSI for some and SESSI for others. Getting this wrong is a compliance failure, not a configuration issue.

### 14.3 High-Volume Payroll *(Target Behavior — Not Yet Load-Tested)*
Payroll runs for organizations with 500+ employees are a target capability. The system must be designed to process large batches without UI timeouts or partial failures, and without requiring the operator to be present throughout. Load testing at this scale has not yet been performed — this is an architectural target, not a verified benchmark.

**Why:** Karachi enterprise use case. Large-scale payroll runs on deadline (typically 25th–28th of each month) are the highest-stress moment in the operator's month.

---

## 15. Market Gap Closure Map

This table shows which system behavior directly closes each validated market gap.

| Market Gap | System Behavior That Closes It |
|---|---|
| GAP 1 — No Compliance Autopilot | §04 Compliance Behavior: autopilot mode, province-aware routing, manual fallback |
| GAP 2 — No AI Payroll Auditor | §02 Trust: pre-run anomaly report; §06 Decision/AI: self-contained decision cards |
| GAP 3 — No Decision-First UX | §06.1 Proactive decision delivery; §12.2 Actions always have a next step |
| GAP 4 — Not Pakistan-Native | §04 Province routing; §03 Tax transparency; §08 Bank/Raast formats |
| GAP 5 — No WhatsApp HR Layer | §07 WhatsApp full-loop behavior; low-bandwidth first; OTP verification |
| GAP 6 — No Trust Infrastructure | §02 Trust-first behaviors; §02.3 Reproducibility; §02.4 Confidence scores |
| GAP 7 — No Compliance Tool for Startups | §04.1 Compliance always before payroll; minimal onboarding path for small teams |

---

## 16. Competitive Differentiation Behaviors

These are the specific behaviors that differentiate AURA HRMS from every current Pakistan vendor.

| Competitor Weakness | AURA HRMS Behavior |
|---|---|
| Sidat Hyder — technical debt, slow to change | Adapter-only country architecture; new rules deployable without service changes |
| PayPeople — limited industrial/manufacturing depth | Shift-based attendance as first-class design target (v1 foundation, v2 full implementation) |
| Resourceinn — UI cluttered, limited global presence | Action-first UX; compliance always visible; no training required for employee tasks |
| WebHR — weak compliance depth | Full statutory lifecycle: FBR, EOBI, PESSI/SESSI automated with manual fallback |
| All vendors — AI as marketing fluff | AI outputs require confidence score, explanation, and supporting signals — always |
| All vendors — WhatsApp as demo | WhatsApp full-loop: payslip, leave, attendance, approvals — on low bandwidth |
| All vendors — compliance hidden | Compliance status is the first visible element, not a sub-menu |

---

## 17. Success Signal — What "Working" Looks Like in Market Terms

The system is working when:

- An HR officer runs payroll and sees a pre-run report showing zero anomalies — they click confirm with confidence, not anxiety
- A compliance officer sees "PESSI submitted — ACKNOWLEDGED" without having manually checked the portal
- A factory floor manager receives a WhatsApp message: "Team attendance issue: 3 employees have unresolved missing punches for this period" — and can action it from their phone
- A payroll dispute is resolved by showing the employee the exact calculation — unpaid leave days, daily rate, deduction — in their payslip
- An FBR portal outage does not stop payroll month-end — the operator records manual submission and continues
- A new country is added by one engineer in one day — no existing service is touched
- An AI flag is reviewed by a payroll officer who can see exactly why it was raised and acts on it — rather than overriding it because they cannot verify it

---

*Merged from MARKET-VALIDATED BEHAVIOR SPEC v1.0 (Session 7) and HRMS SYSTEM BEHAVIOR SPEC. Produced Session 7. Predecessor files archived.*
