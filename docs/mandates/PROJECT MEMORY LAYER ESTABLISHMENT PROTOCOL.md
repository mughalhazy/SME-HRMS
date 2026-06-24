PROJECT MEMORY LAYER ESTABLISHMENT PROTOCOL

OBJECTIVE

Create a permanent Project Memory Layer that survives all future phases, audits, redesigns, frontend work, backend work, deployment work, and AI sessions.

The purpose is to ensure that decisions, resolutions, classifications, defaults, exclusions, and external dependencies never need to be rediscovered.

This layer becomes the institutional memory of the project.

---

PHASE M1 — CREATE MEMORY LAYER

Create:

docs/09_project_memory/

FINAL_CLASSIFIED_REGISTER.md

AUTO_CLOSED_REGISTER.md

SAFE_DEFAULT_REGISTER.md

OWNER_DECISION_REGISTER.md

EXTERNAL_DEPENDENCY_REGISTER.md

OUT_OF_SCOPE_REGISTER.md

PROJECT_MEMORY_USAGE_GUIDE.md

PROJECT_MEMORY_GOVERNANCE.md

---

REGISTER PURPOSES

FINAL_CLASSIFIED_REGISTER.md

Master index of every classified item.

Contains:

- Item ID
- Title
- Classification
- Status
- Evidence Source
- Resolution Source
- Current State
- Register Link

Purpose:

Single entry point for future AI sessions.

---

AUTO_CLOSED_REGISTER.md

Contains items resolved directly from:

- source code
- architecture
- contracts
- authority docs
- repository evidence

Examples:

- route confirmations
- workflow confirmations
- permission confirmations
- schema confirmations
- API confirmations

Purpose:

Prevent rediscovery of already-proven facts.

---

SAFE_DEFAULT_REGISTER.md

Contains items resolved through safe deterministic defaults.

Examples:

- default VAT handling
- default pagination
- default sort order
- default retention periods
- default timeout values

Purpose:

Track assumptions that were accepted because evidence strongly supported one path.

---

OWNER_DECISION_REGISTER.md

Contains genuine product/business decisions.

Examples:

- Stripe vs Paddle
- SaaS branding
- pricing strategy
- multi-tenant strategy
- regional launch priorities

Purpose:

Track owner-owned decisions.

---

EXTERNAL_DEPENDENCY_REGISTER.md

Contains items requiring external provisioning.

Examples:

- JazzCash credentials
- Easypaisa credentials
- SMTP credentials
- OAuth credentials
- FBR registration
- merchant onboarding
- domain ownership

Purpose:

Prevent external onboarding tasks from appearing as software gaps.

---

OUT_OF_SCOPE_REGISTER.md

Contains:

- deferred features
- future phases
- regional expansions
- optional integrations
- launch exclusions

Examples:

- UAE tax module
- advanced AI search
- mobile native application
- hardware integrations

Purpose:

Maintain scope discipline.

---

REQUIRED FIELDS FOR EVERY ENTRY

Every register entry must contain:

Item ID:

Title:

Classification:

Current Status:

Original Source:

Evidence Source:

Resolution Source:

Resolution Date:

Resolved By:

Decision Summary:

Detailed Explanation:

Affected Components:

Affected Routes:

Affected APIs:

Affected Workflows:

Affected Roles:

Owner Required:
YES / NO

External Dependency:
YES / NO

Future Impact:
NONE / LOW / MEDIUM / HIGH

Reopen Criteria:

Related Documents:

Related Register Entries:

---

CLASSIFICATION RULES

AUTO_CLOSED

Only if:

- directly proven from repository evidence
- directly proven from authority documentation
- directly proven from contracts

No assumptions allowed.

---

SAFE_DEFAULT

Only if:

- one path is overwhelmingly supported
- implementation can proceed safely
- no commercial/legal risk introduced

---

OWNER_DECISION

Only if:

- repository cannot answer
- architecture cannot answer
- documentation cannot answer
- decision affects product behaviour

---

EXTERNAL_DEPENDENCY

Only if:

- requires credentials
- requires onboarding
- requires registration
- requires vendor approval
- requires external ownership

---

OUT_OF_SCOPE

Only if:

- intentionally deferred
- future phase
- regional expansion
- optional capability

---

AI MEMORY USAGE RULE

Every future AI session must load:

FINAL_CLASSIFIED_REGISTER.md

before:

- auditing
- redesigning
- frontend work
- backend work
- deployment work
- gap analysis

This becomes the first memory source after authority documents.

---

FUTURE WORKFLOW

Whenever a gap is found:

STEP 1
Check all memory registers.

STEP 2
Determine whether the item already exists.

STEP 3
If it exists:

- update status
- update evidence
- update resolution

Do not create duplicates.

STEP 4
If new:

- classify
- create entry
- add to Final Classified Register

---

REOPEN GOVERNANCE

Items may only be reopened when:

- evidence changed
- implementation changed
- architecture changed
- owner explicitly reverses decision
- external dependency becomes available

Otherwise:

resolved items remain resolved.

---

PROJECT COMPLETION RULE

Project completion does NOT require:

- EXTERNAL_DEPENDENCY items complete
- OUT_OF_SCOPE items complete

Project completion DOES require:

- AUTO_CLOSED reviewed
- SAFE_DEFAULT reviewed
- OWNER_DECISION resolved

External dependencies remain tracked but do not block development unless explicitly required.

---

SUCCESS CRITERIA

At completion:

1. Every classified item exists in exactly one register.
2. No decision must be rediscovered.
3. No resolved item disappears from project memory.
4. Future AI sessions can reconstruct project history from the memory layer alone.
5. Authority layer remains source of truth.
6. Memory layer becomes source of historical context.
