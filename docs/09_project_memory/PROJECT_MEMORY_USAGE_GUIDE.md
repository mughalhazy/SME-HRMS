# PROJECT MEMORY USAGE GUIDE

Layer: Project Memory
Status: Active
Created: 2026-06-18
Audience: All future AI sessions; human contributors

---

## PURPOSE

This guide explains how to use the Project Memory Layer at `docs/09_project_memory/`.

The memory layer is the institutional record of this project. It records every item that was investigated, resolved, deferred, or excluded — so that future AI sessions and human contributors do not rediscover what has already been settled.

---

## AI SESSION LOADING RULES

**Every AI session that works on this project MUST:**

1. Load `docs/09_project_memory/FINAL_CLASSIFIED_REGISTER.md` before:
   - Auditing the codebase
   - Running gap analysis
   - Starting frontend implementation
   - Adding backend features
   - Modifying APIs or routes
   - Reviewing governance documents

2. Load the relevant detail register before working in that area:
   - `AUTO_CLOSED_REGISTER.md` — if investigating already-confirmed items
   - `SAFE_DEFAULT_REGISTER.md` — if verifying defaults or assumptions
   - `OWNER_DECISION_REGISTER.md` — if asking about product/business decisions
   - `EXTERNAL_DEPENDENCY_REGISTER.md` — if checking integration readiness
   - `OUT_OF_SCOPE_REGISTER.md` — if scoping work or checking feature inclusion

3. **Do not re-derive what is already recorded.**

---

## MEMORY LAYER STRUCTURE

```
docs/09_project_memory/
├── FINAL_CLASSIFIED_REGISTER.md    ← Load this first — master index of all 152 items
├── AUTO_CLOSED_REGISTER.md         ← 86 items confirmed from repository evidence
├── SAFE_DEFAULT_REGISTER.md        ← 34 items resolved via safe deterministic defaults
├── OWNER_DECISION_REGISTER.md      ← 3 items requiring owner product/business decisions
├── EXTERNAL_DEPENDENCY_REGISTER.md ← 5 items requiring external provisioning
├── OUT_OF_SCOPE_REGISTER.md        ← 24+ items intentionally excluded from Phase 4
├── PROJECT_MEMORY_USAGE_GUIDE.md   ← This file
└── PROJECT_MEMORY_GOVERNANCE.md    ← Classification rules and reopen governance
```

---

## ITEM COUNTS (AS OF 2026-06-20)

| Class | Count | Register |
|-------|-------|---------|
| AUTO-CLOSED | 86 | AUTO_CLOSED_REGISTER.md |
| SAFE-DEFAULT | 34 | SAFE_DEFAULT_REGISTER.md |
| OWNER-DECISION | 3 | OWNER_DECISION_REGISTER.md |
| EXTERNAL-DEPENDENCY | 5 | EXTERNAL_DEPENDENCY_REGISTER.md |
| OUT-OF-SCOPE | 24+ | OUT_OF_SCOPE_REGISTER.md |
| **TOTAL** | **152+** | FINAL_CLASSIFIED_REGISTER.md |

*+2 AUTO-CLOSED added 2026-06-20: AC-085 (Phase 3.5 L0 FROZEN verdict), AC-086 (L0 output pack created)*

---

## FUTURE WORKFLOW — WHEN A GAP IS FOUND

### STEP 1: Check the memory layer first

Before treating any finding as a new gap, search the memory layer:

1. Search `FINAL_CLASSIFIED_REGISTER.md` by title and topic
2. Search the relevant detail register
3. Determine whether the item already exists

### STEP 2: If the item already exists

- Do not create a duplicate
- Update the existing entry if:
  - Status has changed (e.g., OPEN → RESOLVED)
  - Evidence has changed
  - Architecture has changed
- Record the update date and reason

### STEP 3: If the item is genuinely new

1. Classify it using the classification rules in `PROJECT_MEMORY_GOVERNANCE.md`
2. Create a new entry in the appropriate detail register
3. Add it to the FINAL_CLASSIFIED_REGISTER.md master index
4. Assign the next available ID in the series (AC-087+, SD-035+, OD-004+, ED-006+, OS-029+)

---

## IMPLEMENTATION GUIDE — PHASE 4 FRONTEND

When implementing a frontend screen or feature:

1. **Check FINAL_CLASSIFIED_REGISTER.md** — is this feature in scope?
2. **Check OUT_OF_SCOPE_REGISTER.md** — is this feature excluded?
3. **Check AUTO_CLOSED_REGISTER.md** — are the routes and APIs confirmed?
4. **Check SAFE_DEFAULT_REGISTER.md** — are there defaults to observe?
5. **Observe Phase 4 conditions:**
   - C-001: Routes 22–25 return `{status, data, service}` envelope (no `meta`)
   - C-002: Settings service is in-memory stub; do not cache aggressively
   - C-003: Frontend stays at `backend/ui/` through Phase 4
   - C-004: `/api/v1/roles` and `/api/v1/org` are served by employee-service

---

## INTEGRATION READINESS QUICK REFERENCE

| Integration | Status | Register Entry |
|-------------|--------|---------------|
| FBR (tax) | OPEN — credentials needed | ED-001 |
| EOBI (pension) | OPEN — credentials needed | ED-002 |
| PESSI/SESSI (social security) | OPEN — credentials needed | ED-003 |
| Raast (payments) | OPEN — bank onboarding needed | ED-004 |
| WhatsApp Business API | OPEN — Meta approval needed | ED-005 |

**None of the above block Phase 4 frontend implementation.** They block production launch of their respective features.

---

## OWNER DECISION QUICK REFERENCE

| Decision | Status | Register Entry |
|----------|--------|---------------|
| Commercial launch date | OPEN | OD-001 |
| Scaling strategy (Docker Compose → Kubernetes?) | OPEN | OD-002 |
| Data residency for multi-country expansion | OPEN | OD-003 |

**OD-001 governs the urgency of all external dependency provisioning.**

---

## OUT-OF-SCOPE QUICK REFERENCE — PHASE 4

Do not build any of the following during Phase 4:

| Feature | Register Entry |
|---------|---------------|
| Frontend relocation to `/frontend/` | OS-001 |
| CI/CD activation | OS-002/003/004 |
| QuickBooks integration | OS-005 |
| SAP integration | OS-006 |
| OKR screen (G-001) | OS-007 |
| LMS screen (G-002) | OS-008 |
| Expense analytics screen (G-003) | OS-009 |
| Project tracking screen (G-004) | OS-010 |
| Asset management screen (G-005) | OS-011 |
| Expense claim submission/approval screens (G-010/G-011) | OS-012/013 |
| Asset tracking screen (G-012) | OS-014 |
| Biometric enrollment screen (G-013) | OS-015 |
| Shift scheduling screen (G-014) | OS-016 |
| Succession planning screen (G-015) | OS-017 |
| Engagement surveys screen (G-016) | OS-018 |
| Benefits enrollment screen (G-017) | OS-019 |
| Document management screen (G-018) | OS-020 |
| WhatsApp management screen | OS-021 |
| Banking management screen | OS-022 |
| Travel management screens (F-023) | OS-023 |
| Project tracker screens (F-024) | OS-024 |
| Expense claim workflow (WF-005) | OS-025 |
| Biometric hardware integration | OS-027 |
| Multi-country modules | OS-028 |

---

## MEMORY LAYER AUTHORITY POSITION

The memory layer is NOT an authority document. It is a historical and contextual record.

**Authority hierarchy (highest to lowest):**
1. Repository source code (always current)
2. `docs/00_authority/` documents (PROJECT_CHARTER, FEATURE_SCOPE, DOMAIN_MODEL, PRODUCT_WORKFLOWS, FULLSTACK_STITCHING_CONTRACT)
3. `backend/docs/canon/` documents (security-model, api-standards, service-map, event-catalog)
4. `docs/07_governance/` documents (AI_OPERATING_CONTEXT, governance policies)
5. `docs/09_project_memory/` registers ← historical record, not current source of truth

If a memory layer entry conflicts with the current state of authority documents or source code, trust the current state and update the memory layer entry.

---

## WHEN TO UPDATE THE MEMORY LAYER

| Event | Action |
|-------|--------|
| Gap found and auto-closed from repository evidence | Add AC-XXX to AUTO_CLOSED_REGISTER.md + FINAL_CLASSIFIED_REGISTER.md |
| Safe default adopted | Add SD-XXX to SAFE_DEFAULT_REGISTER.md + FINAL_CLASSIFIED_REGISTER.md |
| Owner makes a product decision | Update OD-XXX in OWNER_DECISION_REGISTER.md as RESOLVED |
| External credentials provisioned | Update ED-XXX in EXTERNAL_DEPENDENCY_REGISTER.md as RESOLVED |
| Out-of-scope feature is activated | Move OS-XXX to appropriate active register; create new entries |
| Architecture changes | Update affected AC/SD entries; reopen if criteria met |

---

## DO NOT REDISCOVER

These items were fully investigated and resolved. If they appear to be gaps in a future session, check the memory layer before treating them as new:

- Gateway routes 1–25: fully confirmed (AC-001 to AC-006)
- EWA architecture: in-process within payroll-service (AC-004)
- 60 TypeScript files: confirmed dead, archived (SD-001 to SD-003)
- Settings handler: in-memory stub — by design (AC-008, C-002)
- CircuitBreaker: confirmed in `resilience.py` (AC-009)
- OutboxManager: confirmed in `outbox_system.py` (AC-011)
- Helpdesk enums: Priority/Status confirmed in `helpdesk_service.py` (AC-007)
- Role system: 5 roles × 31 capabilities confirmed (AC-013 to AC-018)
- Frontend location: `backend/ui/` (AC-040, C-003)
- Roles endpoint: served by employee-service (C-004, AC-014)
- L0 FROZEN verdict: 13 Phase 3 authority docs reviewed; 0 blocking gaps; Phase 4 cleared (AC-085)
- L0 output pack: 4 frozen files in `docs/03_frontend_authority/` — do not re-freeze (AC-086)
