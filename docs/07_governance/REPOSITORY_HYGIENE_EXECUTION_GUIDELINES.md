# REPOSITORY HYGIENE EXECUTION GUIDELINES

Status: Active
Authority Level: Governance
Created: 2026-06-17
Owner: Human (ratified)
Policy: `SAFE_REPOSITORY_HYGIENE_POLICY.md`

---

## PURPOSE

Step-by-step execution guidance for performing `SAFE_REPOSITORY_HYGIENE` tier actions. These guidelines ensure consistent, documented execution without requiring owner approval.

Read `SAFE_REPOSITORY_HYGIENE_POLICY.md` before using this document to confirm an action qualifies for this tier.

---

## GENERAL EXECUTION RULES

1. **Verify qualification first.** Before executing, apply the disqualifying factors checklist from `SAFE_REPOSITORY_HYGIENE_POLICY.md`. If any factor applies, escalate to `REQUIRES_APPROVAL`.

2. **State before acting.** Output one sentence describing the action before using any file-system tool.

3. **Verify the source.** Confirm the file or directory to be moved/updated actually exists at the expected path before proceeding.

4. **Execute precisely.** Do not modify file contents during a hygiene move unless the modification is itself a hygiene action (e.g., updating a `Status:` field in a report header).

5. **Create destination directories first.** Verify or create the destination directory before moving files.

6. **Record every action.** After completion, add an entry to the relevant register (classification matrix, inventory, or phase report).

7. **Do not chain unrelated hygiene actions in a single session** unless the session plan explicitly covers them. Scope each hygiene pass clearly.

---

## ACTION TYPE GUIDELINES

### Archive Maintenance — Moving Dead Code

**When to use:** Source files (TypeScript, Python stubs, unused scripts) confirmed as dead by grep — zero import callers, superseded by active implementation.

**Step-by-step:**

1. Confirm dead status: grep for the file name, module name, or class/function names across the active codebase
2. Confirm the archive destination directory (e.g., `backend/docs/system/archive/<subdirectory>/`)
3. Create the destination directory if it does not exist
4. Move the files using available file tools (Read → Write at destination; confirm source removal is authorized under SAFE_REPOSITORY_HYGIENE — moving within the repo, not deleting)
5. Update the inventory register or classification matrix to record the completed action
6. Note: If the archive operation involves more than ~20 files, create a brief execution log entry in `docs/08_reports/` documenting what was moved, from where, and to where

**Example — TypeScript employee-service archiving (43 files):**
```
Source: backend/services/employee-service/*.ts
Destination: backend/docs/system/archive/typescript-employee-service/
Evidence of dead status: zero Python imports of TypeScript modules (confirmed by grep)
Authorized by: APPROVAL_RECLASSIFICATION_REPORT.md (OA-004)
```

---

### Documentation Relocation

**When to use:** Moving `.md` files to a more appropriate location within `docs/`. Relocating reports from an ad-hoc location to `docs/08_reports/`. Moving mandate files to `docs/mandates/`.

**Step-by-step:**

1. Read the file to confirm its content and current location
2. Confirm the destination directory exists (or create it under `docs/`)
3. Write the file at the new path (content unchanged)
4. Verify the old location is no longer needed — if the old file should be removed, note that file removal outside `docs/` requires `REQUIRES_APPROVAL`; inside `docs/` is safe
5. Update any cross-references in other documents that pointed to the old path
6. Update the `MEMORY.md` or inventory register if the document was tracked there

---

### Root-Level Cleanup

**When to use:** Removing OS artifacts, `.lnk` files, temp files, or non-project files from the repository root.

**Step-by-step:**

1. List the root directory contents
2. Identify files that are OS-generated (`.lnk`, `.DS_Store`, `Thumbs.db`) or clearly non-project
3. Confirm no other file in the repository references or imports the target
4. Delete OS artifacts (OS artifacts inside `docs/` or root are safe to delete under SAFE_REPOSITORY_HYGIENE)
5. Add the artifact pattern to `.gitignore` so it is not re-committed
6. Record the action in the relevant report

---

### .gitignore Improvements

**When to use:** Adding new ignore patterns. Reorganizing `.gitignore` with section headers. Never removing patterns.

**Step-by-step:**

1. Read the current `.gitignore`
2. Identify the new pattern to add
3. Verify the pattern does not accidentally ignore tracked files (run `git check-ignore -v <path>` mentally — does this pattern match anything currently tracked?)
4. Add the pattern to the appropriate section; if no section exists, create one with a comment header
5. No approval needed unless the pattern would remove a currently tracked file from git (that would be a `REQUIRES_APPROVAL` change)

---

### Documentation Normalization

**When to use:** Fixing broken cross-references. Correcting metadata (Status field, Last Reviewed date, phase identifier). Adding missing headers.

**Step-by-step:**

1. Read the document
2. Identify the specific normalization needed (broken link, stale date, wrong status)
3. Apply the edit using the Edit tool (targeted replacement, not full rewrite)
4. Verify the replacement did not accidentally remove content
5. No register entry needed for minor metadata fixes; add a note in the session summary report

---

### Report Generation

**When to use:** Creating new output reports under `docs/08_reports/`.

**Step-by-step:**

1. Confirm the report does not already exist (check `docs/08_reports/` for an existing file with the same name or purpose)
2. Define the report content from session evidence
3. Write the report using standard header format:
   ```
   Status: Complete | Active | Draft
   Created: YYYY-MM-DD
   Phase: <phase name>
   ```
4. Add a pointer to the report in `MEMORY.md` if it is a long-lived governance artifact

---

### Folder Restructuring (safe subset)

**When to use:** Creating new organizational subdirectories under `docs/` or archive locations. Renaming `docs/` subdirectories where no build tool references the path.

**Step-by-step:**

1. Verify the rename does not affect any import path, build configuration, or external reference
2. Check `docker-compose.yml`, `package.json`, and `.github/workflows/ci.yml` for references to the path — if any exist, escalate to `REQUIRES_APPROVAL`
3. Create the new directory
4. Move files into it (each file: Read → Write at new path)
5. Update all internal cross-reference links that pointed to the old path
6. Record the restructuring in the relevant inventory register

---

### Archiving Dead CI Workflow Files

**When to use:** Moving never-executing workflow files from `backend/.github/workflows/` (which GitHub ignores) to an archive location for reference.

**Scope:** File-level move only. NO modification of YAML content. NO activation in root `.github/workflows/`.

**Step-by-step:**

1. Confirm the workflow is in `backend/.github/workflows/` (not executed by GitHub — GitHub only reads root `.github/workflows/`)
2. Read the file and confirm it is not already being executed elsewhere
3. Create destination directory: `docs/archive/ci-legacy/`
4. Write the file at the archive path (content unchanged)
5. The original in `backend/.github/workflows/` may be left in place or removed — removing it is SAFE_REPOSITORY_HYGIENE since it was never executed; leaving it is harmless
6. Record in the classification matrix: status updated to `ARCHIVED`
7. DO NOT modify the YAML content, DO NOT move to root `.github/workflows/` — those actions are `REQUIRES_APPROVAL`

---

## POST-EXECUTION CHECKLIST

After completing any SAFE_REPOSITORY_HYGIENE action:

- [ ] Source files confirmed at expected path before action
- [ ] Destination exists or was created
- [ ] Action executed without modifying file content (unless the content change was itself a hygiene action)
- [ ] No docker-compose.yml was touched
- [ ] No active CI workflow YAML was modified
- [ ] No active Python module was moved
- [ ] Relevant register or matrix updated
- [ ] Phase report includes the completed action

---

## ACTIONS THAT LOOK LIKE HYGIENE BUT ARE NOT

These commonly arise during hygiene passes and must be escalated:

| Action | Why it is NOT SAFE_REPOSITORY_HYGIENE |
|--------|---------------------------------------|
| Renaming `backend/services/employee-service/` directory | The Python `employee-service` package may be imported by path-sensitive tooling |
| Moving `backend/ui/` to `frontend/` | Requires docker-compose.yml update (REQUIRES_APPROVAL) + hidden import risks |
| Deleting `backend/.github/workflows/deploy.yml` (not archiving) | Deletion of non-doc files is REQUIRES_APPROVAL without explicit authorization |
| Adding `docker compose config` step to root `ci.yml` | Modifying active CI pipeline — REQUIRES_APPROVAL |
| Moving `backend/api-gateway/routes.py` to a new location | Active module with callers — REQUIRES_APPROVAL |
| Editing `.env.example` to add new variables | Application configuration change — REQUIRES_APPROVAL (dependency/env change) |
| Removing `__pycache__/` directories | These are auto-generated and typically gitignored already; verify via `.gitignore` before touching |

---

## REGISTER MAINTENANCE AFTER HYGIENE EXECUTION

When a SAFE_REPOSITORY_HYGIENE action completes that was previously tracked as an open item:

1. In `APPROVAL_CLASSIFICATION_MATRIX.md`: update the row's Status from `DEFERRED` to `EXECUTED — [date]`
2. In `RESIDUAL_OWNER_DECISION_REGISTER.md`: if the item was a ROD, add a closing note: "Sub-item A archived YYYY-MM-DD"
3. In `APPROVAL_RECLASSIFICATION_REPORT.md`: update the Execution Target row to `COMPLETE — [date]`
4. In session summary: note the completion for the owner's awareness

---

## RELATIONSHIP TO OTHER GOVERNANCE DOCUMENTS

| Document | Relationship |
|----------|-------------|
| `SAFE_REPOSITORY_HYGIENE_POLICY.md` | Defines the tier; qualification criteria |
| `DECISION_ESCALATION_MATRIX.md` | Parent governance document; this tier is TIER 1.5 |
| `APPROVAL_RECLASSIFICATION_REPORT.md` | Lists all items reclassified to this tier |
| `APPROVAL_CLASSIFICATION_MATRIX.md` | Register to update after execution |
| `RESIDUAL_OWNER_DECISION_REGISTER.md` | Items that were partially reclassified; archive sub-items now authorized |
