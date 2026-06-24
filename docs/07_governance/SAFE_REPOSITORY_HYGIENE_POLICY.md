# SAFE REPOSITORY HYGIENE POLICY

Status: Active
Authority Level: Governance
Created: 2026-06-17
Owner: Human (ratified)
Supersedes: Nothing — introduces new execution tier

---

## PURPOSE

This document defines the `SAFE_REPOSITORY_HYGIENE` execution tier: a middle category between `AUTONOMOUS` and `REQUIRES_APPROVAL` that governs low-risk repository maintenance activities. It was introduced to reduce unnecessary owner escalations for structural and organizational work while preserving approval controls for all changes that affect architecture, runtime, infrastructure, database, security, or application functionality.

Cross-reference: `DECISION_ESCALATION_MATRIX.md` (TIER 1.5), `REPOSITORY_HYGIENE_EXECUTION_GUIDELINES.md`

---

## PROBLEM THIS SOLVES

Prior to this policy, repository audit and normalization phases generated excessive `REQUIRES_APPROVAL` items for activities that carry no operational risk — moving dead code to archive directories, relocating report files, improving `.gitignore` patterns, updating document cross-references. These items accumulated in owner decision registers, blocking routine hygiene work that any session could safely execute.

Owner approval must remain focused on:
- Architecture and infrastructure decisions
- Runtime behavior changes
- Security and permission changes
- API and database changes
- Deployment behavior changes

Owner approval must not be required for routine repository maintenance.

---

## TIER DEFINITION

An action qualifies as `SAFE_REPOSITORY_HYGIENE` if it satisfies ALL of the following:

### Negative criteria (none of these may apply)
1. Does not modify business logic
2. Does not modify any API or API contract
3. Does not modify database structures or migration files
4. Does not modify runtime behavior
5. Does not modify infrastructure configuration (docker-compose.yml, Dockerfiles, nginx config)
6. Does not modify deployment behavior
7. Does not modify security boundaries
8. Does not modify permissions or authorization logic
9. Does not modify authentication mechanisms
10. Does not modify any application functionality
11. Does not delete files outside `docs/` or `ops/`
12. Does not activate a currently inactive workflow or service

### Positive criteria (at least one must apply)
The action must improve at least one of:
- Repository organization and discoverability
- Documentation quality or accuracy
- Archive structure and maintainability
- Governance records and traceability
- Code hygiene (removing confirmed-dead artifacts)

---

## QUALIFYING ACTION TYPES

### Documentation Relocation
Moving `.md` files between subdirectories within `docs/`. Relocating reports to `docs/08_reports/`. Relocating mandate files to `docs/mandates/`. Moving authority documents between `docs/` subdirectories.

### Documentation Normalization
Fixing broken cross-references between documents. Updating authority document pointers. Adding or correcting metadata (status fields, dates, reviewer, phase). Updating stale report statuses (e.g., marking `Status: Complete`).

### Archive Maintenance
Moving confirmed-dead source files (TypeScript stubs, superseded Python files, unused scripts) to archive directories such as `backend/docs/system/archive/` or `docs/archive/`. "Confirmed-dead" means: no active import, no active caller confirmed by grep, superseded by a replacement implementation.

Note: Archiving (move to archive directory) qualifies. Deletion of files outside `docs/` or `ops/` does NOT qualify — use `REQUIRES_APPROVAL` for deletion.

### Folder Restructuring (safe subset)
Creating new organizational subdirectories under `docs/`, `backend/docs/`, or archive roots. Renaming `docs/` subdirectories where no build tool, import, or external reference resolves against the path.

### Report Generation
Creating new report files under `docs/08_reports/`. Generating classification matrices, inventory registers, audit reports, decision registers.

### Report Consolidation
Merging stale report fragments into a single authoritative report. Marking superseded fragments with status `Superseded by [new report]`.

### Generated Artifact Cleanup
Removing auto-generated files (`.pyc`, `__pycache__`, build artifacts, lock artifacts) that do not belong in version control. Removing auto-generated log files committed by mistake.

### Temporary Artifact Cleanup
Removing OS-generated files (`.lnk`, `.DS_Store`, `Thumbs.db`) accidentally committed. Removing scratch or temp files from the repository root.

### Root-Level Cleanup
Removing non-project files from the repository root. Organizing the root directory into clearly named subdirectories. Creating `README.md` at the root if absent.

### .gitignore Improvements
Adding new ignore patterns to `.gitignore` (additive). Reorganizing `.gitignore` with section comments. Never removing existing tracked patterns — that requires `REQUIRES_APPROVAL`.

### Governance Metadata Updates
Updating `Last Reviewed` dates. Updating `Status` fields. Adding cross-references between governance documents. Creating new governance registers or classification matrices.

### Classification Matrix Updates
Classifying newly discovered items in existing registers. Updating open item registers after resolution. Adding new rows; changing status of resolved rows.

### Inventory Updates
Adding discovered files or directories to inventory registers. Correcting inventory entries that reference wrong file paths. Updating item counts.

---

## DISQUALIFYING FACTORS

If any of the following apply, the action is NOT `SAFE_REPOSITORY_HYGIENE`:

| Factor | Required Tier | Reason |
|--------|--------------|--------|
| Modifies `docker-compose.yml` content | REQUIRES_APPROVAL | Infrastructure change |
| Modifies any `.github/workflows/` YAML content | REQUIRES_APPROVAL | CI/CD pipeline change |
| Activates an inactive CI workflow by adding it to root `.github/workflows/` | REQUIRES_APPROVAL | Deployment behavior change |
| Moves a Python file with active import callers | REQUIRES_APPROVAL | Production code movement |
| Renames a module, class, or function | REQUIRES_APPROVAL | Refactor with import risk |
| Deletes a file outside `docs/` or `ops/` | REQUIRES_APPROVAL | Irreversible outside safe zone |
| Moves the Next.js frontend app directory (`backend/ui/`) | REQUIRES_APPROVAL | Build path dependencies + docker-compose update required |
| Creates, modifies, or deletes database migrations | REQUIRES_APPROVAL | Schema change |
| Modifies `/backend/country/pakistan/` | REQUIRES_APPROVAL | Statutory compliance |
| Modifies `/backend/integrations/pakistan/` | REQUIRES_APPROVAL | Payment adapter |
| Modifies `/backend/docs/canon/security-model.md` | REQUIRES_APPROVAL | Security policy |
| Removes existing patterns from `.gitignore` | REQUIRES_APPROVAL | Could expose committed files |
| Moves files between separate git repositories | REQUIRES_APPROVAL | Cross-repo structural change |

---

## ESCALATION PROCEDURE

`SAFE_REPOSITORY_HYGIENE` actions do NOT require pausing for owner confirmation before execution. The procedure is:

1. **State the action** — one sentence before executing, describing what will happen and why
2. **Execute** — perform the action using available tools
3. **Record** — document the completed action in the appropriate register or report
4. **Report** — include in the phase summary delivered to the owner

If uncertain whether an action qualifies, apply the disqualifying factors checklist above. If any factor applies, escalate to `REQUIRES_APPROVAL` following the standard escalation procedure in `DECISION_ESCALATION_MATRIX.md`.

---

## EXAMPLES

| Action | Tier | Rationale |
|--------|------|-----------|
| Move 43 dead TypeScript files to `backend/docs/system/archive/typescript-employee-service/` | SAFE_REPOSITORY_HYGIENE | Confirmed dead code (zero callers), archive move, fully reversible |
| Move 6 dead TypeScript files to `backend/docs/system/archive/typescript-settings-service/` | SAFE_REPOSITORY_HYGIENE | Same rationale |
| Move 11 dead TypeScript middleware files to `backend/docs/system/archive/typescript-middleware/` | SAFE_REPOSITORY_HYGIENE | Same rationale |
| Add `*.lnk` and `Thumbs.db` to root `.gitignore` | SAFE_REPOSITORY_HYGIENE | Additive `.gitignore` pattern, no behavior change |
| Create `docs/08_reports/APPROVAL_RECLASSIFICATION_REPORT.md` | SAFE_REPOSITORY_HYGIENE | Report generation, docs-only |
| Copy `backend/.github/workflows/build.yml` to `docs/archive/ci-old/` as reference (not activating) | SAFE_REPOSITORY_HYGIENE | File archived as reference, not executed |
| Move `backend/.github/workflows/build.yml` to root `.github/workflows/` and modify Dockerfile paths | REQUIRES_APPROVAL | CI/CD content modification + activation |
| Move `backend/ui/` to `frontend/` + update docker-compose.yml | REQUIRES_APPROVAL | Infrastructure change (docker-compose.yml) + hidden import path risks |
| Add compose validation step to root `.github/workflows/ci.yml` | REQUIRES_APPROVAL | Modifying active CI pipeline content |
| Rename `docs/10_repo_audit/` → `docs/10_repository/` | SAFE_REPOSITORY_HYGIENE | Folder rename in docs/, no build tool references |
| Delete `backend/services/employee-service/` TypeScript directory entirely | REQUIRES_APPROVAL | File deletion outside docs/ — archive instead |
| Update `Last Reviewed: 2026-06-15` → `Last Reviewed: 2026-06-17` in a governance doc | SAFE_REPOSITORY_HYGIENE | Metadata update |
| Fix broken cross-reference link in `AI_OPERATING_CONTEXT.md` | SAFE_REPOSITORY_HYGIENE | Documentation normalization |

---

## RELATIONSHIP TO OTHER GOVERNANCE DOCUMENTS

| Document | Relationship |
|----------|-------------|
| `DECISION_ESCALATION_MATRIX.md` | Parent — SAFE_REPOSITORY_HYGIENE appears as TIER 1.5 |
| `AI_OPERATING_CONTEXT.md` | References this policy in ACTIVE_AUTHORITY_DOCS table |
| `REPOSITORY_HYGIENE_EXECUTION_GUIDELINES.md` | Companion — step-by-step execution guidance for this tier |
| `RESIDUAL_OWNER_DECISION_REGISTER.md` | Items reclassified from that register under this policy |
| `APPROVAL_RECLASSIFICATION_REPORT.md` | Records the initial reclassification pass |
