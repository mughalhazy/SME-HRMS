# Meridian HCM — Contract & Schema File Structure
## Version: 1.0 | Date: 2026-03-22

> NOTE (2026-06-09 stale-ref pass): path examples updated to current layout — `seed-pages/` → `frontend/seeds/`, `hrms-repo/SME-HRMS-main/services/` → `backend/services/`. See Cross-File Finding #2 in `ops/normalisation-tracker.md`.

---

## PRINCIPLE

```
Define once → reference everywhere
Never duplicate → only point to source
Archetype owns its schema → page owns its config
```

---

## FILE HIERARCHY

```
/hrms/docs/
├── SHARED
│   ├── hrms-api-contracts.md          ← enums + service map (never duplicated)
│   └── design-language.html           ← visual + interaction authority
│
├── SYSTEM SCHEMA
│   └── hrms-schema-template.json      ← archetype slot contracts (all 13)
│
└── PAGE CONTRACTS
    ├── hrms-h01-dashboard-contract.json
    ├── hrms-h02-employees-contract.json
    └── hrms-h[N]-[page]-contract.json
```

---

## FILE TYPES

### 1. `hrms-api-contracts.md` — SHARED
One file. Never duplicated. Contains all enum display logic + service map.
Rule: If an enum exists here, no page contract may redefine it. Reference only.
Enum registry trigger: if file exceeds 800 lines → extract enums into `hrms-enum-registry.md`.

### 2. `hrms-schema-template.json` — SYSTEM SCHEMA
One file. Defines slot contracts for ALL 13 archetypes.

**BLOCKER RULE:** No page contract may be created until this file exists and is tracked in the audit manifest.

Contains per archetype:
- Slot list with required/optional flags
- Allowed components per slot
- Surface density values
- Page state names (loaded · skeleton · empty · error · partial)

**Forbidden in schema template:** `source` · `service` · `endpoint` · `enum_ref` · `gap`
These belong in page contracts only. Their presence = audit BLOCKER.

### 3. `hrms-h[N]-[page]-contract.json` — PAGE CONTRACT
One per page. Contains data + configuration only. Never layout.

**Mandatory fields:**
```json
{
  "_meta": {
    "id":            "h02-employees",
    "archetype":     "H02 List/Table",
    "page":          "Employees",
    "surface":       "admin",
    "version":       "1.0",
    "last_updated":  "2026-03-22",
    "archetype_ref": "hrms-schema-template.json",
    "seed_page_ref": "frontend/seeds/p2-list.html"
  }
}
```

Rule: `archetype_ref` must resolve to a file that exists on disk — audit checks this.
Rule: `seed_page_ref` links to the design anchor for this archetype.
Rule: Column widths must sum to 100 ±1.

---

## ISOLATION RULES

```
1. ENUM ISOLATION
   Enums live in hrms-api-contracts.md ONLY.
   Page contracts reference: "enum_ref": "ref:api-contracts#EmployeeStatus"
   Never copy-paste enum values into contracts.

2. LAYOUT ISOLATION
   Layout lives in hrms-schema-template.json ONLY.
   Page contracts reference: "archetype_ref": "hrms-schema-template.json"
   Never describe layout in page contracts.

3. GAP ISOLATION
   Gaps live in hrms-ui-backend-gaps.md ONLY.
   Page contracts reference by ID: "gaps": ["BG-001", "BG-002"]

4. MOCK DATA ISOLATION
   Mock data defined in page contracts ONLY.
   Must conform to real API shape.
   Must use real enum values from hrms-api-contracts.md.
   Must NOT introduce fields not in the repo response.

5. SERVICE NAMING
   All service names must match repo directory names exactly.
   Check: ls backend/services/ and root-level *.py files
   No aliasing · no shorthand · no abbreviation.

6. CROSS-ARCHETYPE ISOLATION
   H02 contracts never import H03 contracts.
   Exception: H03 may reference its parent H02 as "parent_list_ref" for breadcrumb only.

7. SURFACE ISOLATION
   Admin and Employee Self-Service variants of the same resource = separate contracts.
```

---

## DSL FORMAT REFERENCE

### Top-level structure
```json
{
  "_meta": {
    "id":            "h02-employees",
    "archetype":     "H02 List/Table",
    "page":          "Employees",
    "surface":       "admin",
    "version":       "1.0",
    "last_updated":  "2026-03-22",
    "archetype_ref": "hrms-schema-template.json",
    "seed_page_ref": "frontend/seeds/p2-list.html"
  },
  "workflow":        { ... },
  "api_contract":    { ... },
  "renderer_schema": { ... }
}
```

### Renderer schema structure
```json
"renderer_schema": {
  "dsl_version": "1.0",
  "archetype":   "list_table",
  "surface":     "admin",
  "page_title":  "Employees",
  "page_states": ["loaded", "skeleton", "empty", "error", "partial"],
  "chrome": {
    "nav_active": "Employees",
    "topbar": {
      "breadcrumb": ["Employees"],
      "primary_action": { "label": "Add Employee", "variant": "primary" }
    }
  },
  "slots": { ... },
  "empty_state":   { ... },
  "error_state":   { ... },
  "partial_state": { ... }
}
```

### Slot DSL shape
```json
"SLOT_NAME": {
  "component": "ComponentName",
  "required":  true,
  "condition": "optional — when this slot renders"
}
```

**Slot contract validation rule:** Every page contract must implement all required slots from its schema template. Missing required slot = audit warning.

### Data table column shape
```json
{
  "id":        "status",
  "type":      "status_chip",
  "label":     "Status",
  "source":    "employee-service › Employee.status",
  "enum_ref":  "ref:api-contracts#EmployeeStatus",
  "width_pct": 10
}
```

**Column type vocabulary (from design-language.html):**
```
entity       → avatar + name + ID, font-weight 600
text         → string, color #374151
meta         → secondary string, color #64748B
status_chip  → chip component, enum_ref required
date         → formatted date, monospace
number       → right-aligned, monospace
progress_bar → 5px bar + percentage
actions      → icon buttons, appear on hover
```

**Column width rule:** sum(columns[].width_pct) must equal 100 ±1. Audit checks this.

### Source field notation
```
Format: "{service} › {Model}.{field_path}"

Valid:
  "employee-service › Employee.status"
  "leave_service › LeaveRequest.total_days"
  "derived › count(status='Active')"
  "ref:api-contracts#EmployeeStatus"

Invalid (free text not allowed):
  "comes from the employee service"
  "the status field"
```

### API contract structure
```json
"api_contract": {
  "primary_source": {
    "service":  "employee-service",
    "endpoint": "GET /api/v1/employees",
    "params":   { "tenant_id": "required" },
    "response_fields": {
      "employee_id":   "Employee.employee_id",
      "status":        "Employee.status — ref:api-contracts#EmployeeStatus"
    }
  },
  "row_actions":  [ { "label": "View", "route": "/employees/{employee_id}" } ],
  "bulk_actions": [ { "label": "Suspend", "requires_confirm": true } ]
}
```

**Action route rule:** Dynamic params use `{param}` syntax. Param must exist in response_fields.

### Page states
```json
"empty_state": {
  "icon":     "👥",
  "headline": "No employees yet.",
  "body":     "Add your first employee to get started.",
  "cta":      { "label": "Add Employee", "route": "/employees/new" }
},
"error_state": {
  "message": "Couldn't load employees.",
  "detail":  "employee-service may be unavailable.",
  "action":  "retry"
}
```

---

## AUDIT CHECKS (python hrms-audit.py --contracts)

```
1. SCHEMA TEMPLATE EXISTS   hrms-schema-template.json must exist (BLOCKER)
2. SCHEMA REFERENCE         every contract must have "archetype_ref" field
3. SCHEMA FILE EXISTS       archetype_ref must resolve to file on disk (BLOCKER)
4. GAP ID VALIDITY          every BG-xxx must exist in gap register
5. CONTRACT VERSIONING      every contract must have "version" + "last_updated"
6. COLUMN WIDTH SUM         sum(width_pct) must be 99–101
```

---

## PHASE HANDOFF — what to upload per phase

### Phase 1 — H01 Dashboards
```
hrms-api-contracts.md
hrms-schema-template.json (after creation)
design-language.html
frontend/seeds/p1-dashboard.html
```

### Phase 2 — H02 Lists
```
+ frontend/seeds/p2-list.html
+ hrms-h01-*-contract.json (reference)
```

### Phase 3 — H03 Detail + H04 Forms
```
+ frontend/seeds/p3-profile.html · p4-form.html
```

### Subsequent phases
Add seed page for each new archetype. Previous contracts for breadcrumb/parent_list_ref only.
