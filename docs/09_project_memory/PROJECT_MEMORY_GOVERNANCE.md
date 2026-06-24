# PROJECT MEMORY GOVERNANCE

Layer: Project Memory
Status: Active
Created: 2026-06-18
Audience: All future AI sessions; human contributors; project governance

---

## PURPOSE

This document defines the rules governing the Project Memory Layer. It specifies:
- Classification rules for each item class
- How to add new entries
- Reopen criteria
- Authority hierarchy
- Project completion definition

---

## CLASSIFICATION RULES

### AUTO-CLOSED

**Only if ALL of the following are true:**
- Directly proven from repository source code, OR
- Directly proven from authority documentation (`docs/00_authority/` or `backend/docs/canon/`), OR
- Directly proven from existing contracts (`docs/03_fullstack_contracts/`)

**Disqualified if:**
- Requires any assumption
- Requires any inference that cannot be verified from a specific file and line number
- Evidence source is a comment, not code

**Evidence requirement:** Specific file path + line number OR authority document section.

**Examples:**
- Route confirmed at `routes.py` line 52 → AUTO-CLOSED
- Enum value confirmed at `helpdesk_service.py` line 127 → AUTO-CLOSED
- Permission matrix confirmed at `security-model.md` lines 16–48 → AUTO-CLOSED

---

### SAFE-DEFAULT

**Only if ALL of the following are true:**
- One path is overwhelmingly supported by available evidence
- Implementation can proceed safely with this default
- No commercial risk introduced
- No legal or compliance risk introduced
- Default can be reversed if wrong, without data loss

**Disqualified if:**
- Evidence strongly supports multiple competing paths
- Commercial or legal consequence of being wrong is material
- Credentials are needed (those are EXTERNAL-DEPENDENCY)

**Examples:**
- TypeScript files with zero Python callers → archived (SAFE-DEFAULT)
- In-memory rate limiter → acceptable for single-replica Docker Compose (SAFE-DEFAULT)
- OpenAPI contact email fix → cosmetic (SAFE-DEFAULT)

---

### OWNER-DECISION

**Only if ALL of the following are true:**
- Repository cannot answer the question
- Architecture cannot answer the question
- Documentation cannot answer the question
- The decision affects product behaviour, strategy, or legal posture

**Disqualified if:**
- Can be resolved by reading the codebase
- Can be resolved by reading authority documents
- Is a credentials/onboarding matter (those are EXTERNAL-DEPENDENCY)
- Is a deferred feature (that is OUT-OF-SCOPE)

**Examples:**
- Commercial launch date → OWNER-DECISION
- Scaling strategy (single vs. multi-replica) → OWNER-DECISION
- Data residency policy for multi-country expansion → OWNER-DECISION

**NOT examples:**
- Which framework to use (code already decided, FD-004) → AUTO-CLOSED
- What database (already decided, FD-005) → AUTO-CLOSED

---

### EXTERNAL-DEPENDENCY

**Only if ALL of the following are true:**
- Requires credentials not held by the development team
- Requires vendor account/registration/onboarding external to the codebase
- Cannot be implemented without external approval or issuance

**Disqualified if:**
- Implementation code does not yet exist (that is OUT-OF-SCOPE until code exists)
- Is a product strategy question (that is OWNER-DECISION)

**Examples:**
- FBR API key (statutory government registration) → EXTERNAL-DEPENDENCY
- Raast credentials (bank partner onboarding) → EXTERNAL-DEPENDENCY
- WhatsApp Business API account (Meta approval) → EXTERNAL-DEPENDENCY

**NOT examples:**
- QuickBooks credentials (no code exists yet) → OUT-OF-SCOPE until implementation is built

---

### OUT-OF-SCOPE

**Only if ANY of the following are true:**
- Intentionally deferred to a future phase by the owner or governance
- Feature status is PLANNED or ADD-ON in `FEATURE_SCOPE.md`
- Regional expansion not yet authorized
- Optional capability not included in current scope
- Hardware integration not yet started

**NOT applicable if:**
- Item can be closed from evidence (use AUTO-CLOSED)
- Item was a bug or documentation error (fix it; do not defer it)

---

## ENTRY REQUIREMENTS

Every register entry MUST contain these 20 fields:

```
Item ID:          [AC/SD/OD/ED/OS]-[number]
Title:            Short descriptive name
Classification:   AUTO-CLOSED | SAFE-DEFAULT | OWNER-DECISION | EXTERNAL-DEPENDENCY | OUT-OF-SCOPE
Current Status:   Closed | OPEN | Deferred | Executed | Resolved
Original Source:  Document/item ID where this was first raised
Evidence Source:  Specific file path + line number OR authority document section
Resolution Source: What resolved it (e.g., "Phase 2.8 TR-001", "Mandate 2 SAFE-DEFAULT")
Resolution Date:  YYYY-MM-DD or "NOT YET RESOLVED"
Resolved By:      Who/what resolved it (or "N/A — requires human action")
Decision Summary: One paragraph describing the conclusion
Detailed Explanation: Full context, code evidence, decision rationale
Affected Components: List of services, files, or modules
Affected Routes:  List of API routes or "None"
Affected APIs:    List of API endpoints or "None"
Affected Workflows: WF-XXX references or "None"
Affected Roles:   Roles affected or "None"
Owner Required:   YES / NO
External Dependency: YES / NO
Future Impact:    NONE | LOW | MEDIUM | HIGH
Reopen Criteria:  What would cause this to be reopened
Related Documents: Relevant file paths
Related Register Entries: IDs of related items in any register
```

---

## REOPEN GOVERNANCE

Items may ONLY be reopened when one of the following is true:

| Trigger | Applies To |
|---------|-----------|
| Evidence changed (code was modified, new file found) | AUTO-CLOSED items |
| Implementation proved the default wrong | SAFE-DEFAULT items |
| Architecture changed (new service, new route, restructure) | AUTO-CLOSED, SAFE-DEFAULT |
| Owner explicitly reverses a decision | OWNER-DECISION items |
| External dependency becomes available | EXTERNAL-DEPENDENCY items |
| Deferred feature is activated by owner | OUT-OF-SCOPE items |

**Otherwise:** Resolved items remain resolved. Do not reopen based on:
- A different AI session disagreeing with the resolution
- Theoretical alternative interpretations
- Uncertainty without new evidence

---

## DUPLICATE PREVENTION

Before creating any new memory entry:

1. Search FINAL_CLASSIFIED_REGISTER.md for the topic
2. Search the relevant detail register for title matches
3. If a match exists, UPDATE the existing entry, do not create a duplicate
4. If unsure whether something is a duplicate, it is a duplicate until proven otherwise

---

## ID ASSIGNMENT RULES

IDs are assigned sequentially within each class:

| Class | Prefix | Next Available ID |
|-------|--------|------------------|
| AUTO-CLOSED | AC- | AC-087 |
| SAFE-DEFAULT | SD- | SD-035 |
| OWNER-DECISION | OD- | OD-004 |
| EXTERNAL-DEPENDENCY | ED- | ED-006 |
| OUT-OF-SCOPE | OS- | OS-029 |

IDs are NEVER reused. When an item is reclassified, it gets a new ID in the new class; the old ID is marked as "Reclassified to [new ID]".

---

## AUTHORITY HIERARCHY (ENFORCED)

The memory layer is subordinate to all other authority sources. In case of conflict:

```
1. Repository source code          ← HIGHEST — always current
2. docs/00_authority/              ← PROJECT_CHARTER, FEATURE_SCOPE, DOMAIN_MODEL,
                                      PRODUCT_WORKFLOWS, FULLSTACK_STITCHING_CONTRACT
3. backend/docs/canon/             ← security-model, api-standards, service-map,
                                      event-catalog, capability-matrix
4. docs/07_governance/             ← AI_OPERATING_CONTEXT, governance policies
5. docs/09_project_memory/         ← HISTORICAL RECORD (subordinate to all above)
```

**If memory layer conflicts with items 1–4:** Trust items 1–4. Update the memory layer entry. Do not act on stale memory.

---

## AI MEMORY USAGE RULES

1. **Load FINAL_CLASSIFIED_REGISTER.md before any audit, gap analysis, or implementation work.**
2. **Do not re-derive what is recorded.** If an item is in the memory layer, treat it as resolved unless a reopen trigger applies.
3. **Do not produce duplicate gap findings.** If a gap is raised that matches an existing memory entry, cite the existing entry and explain its resolution.
4. **Do not treat EXTERNAL-DEPENDENCY items as software gaps.** They are provisioning tasks, not implementation tasks.
5. **Do not treat OUT-OF-SCOPE items as missing features.** They are intentionally excluded.
6. **Verify before acting on memory.** If a memory entry names a file path or function, confirm it still exists before recommending action.

---

## PROJECT COMPLETION DEFINITION

Per the protocol:

**Project completion does NOT require:**
- EXTERNAL-DEPENDENCY items resolved (ED-001 to ED-005)
- OUT-OF-SCOPE items implemented

**Project completion DOES require:**
- All AUTO-CLOSED items: reviewed ✓ (86 items — COMPLETE)
- All SAFE-DEFAULT items: reviewed ✓ (34 items — COMPLETE)
- All OWNER-DECISION items: resolved (3 items — OPEN: OD-001, OD-002, OD-003)

External dependencies remain tracked but do not block development unless the specific feature is in the active sprint.

---

## GOVERNANCE OWNERSHIP

| Responsibility | Owner |
|---------------|-------|
| Memory layer content accuracy | AI sessions + human review |
| Classification decisions | AI sessions (AUTO-CLOSED, SAFE-DEFAULT); Human (OWNER-DECISION, EXTERNAL-DEPENDENCY) |
| Reopen authorization | Human only |
| OUT-OF-SCOPE activation | Human only |
| Memory layer structural changes | Human only |

---

## MEMORY LAYER STALENESS POLICY

Memory entries older than 6 months should be verified against current repository state before being acted upon:
- AUTO-CLOSED: re-verify the specific file and line number still exist and match
- SAFE-DEFAULT: re-verify the default is still appropriate given current architecture
- OWNER-DECISION: re-verify no decision has been made since the entry was created
- EXTERNAL-DEPENDENCY: re-verify credentials have not already been provisioned
- OUT-OF-SCOPE: re-verify feature has not been activated

This policy applies from: 2026-12-18 (6 months after creation date 2026-06-18).

---

## CHANGE LOG

| Date | Change | Author |
|------|--------|--------|
| 2026-06-18 | Memory layer established — 150+ items across 5 registers | AI session (Mandate 2 + Memory Layer Protocol) |
| 2026-06-20 | Phase 3.5 L0 FROZEN completed — +2 AUTO-CLOSED (AC-085, AC-086); FINAL_CLASSIFIED_REGISTER updated to 152 total items; next AC ID: AC-087 | AI session (Phase 3.5 + Memory Layer Re-run) |
