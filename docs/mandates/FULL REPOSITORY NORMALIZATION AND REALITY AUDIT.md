FULL REPOSITORY NORMALIZATION AND REALITY AUDIT

OBJECTIVE

Audit and normalize the entire repository before Frontend Authority Capture begins.

This is not only a documentation audit.

This is a full repository reality audit and restructuring plan.

The goal is to ensure the repository is clean, understandable, correctly organized, and aligned with the governance framework.

---

CORE RULE

The whole repository must be inventoried.

Do not only review docs/.

Do not only review backend/.

Do not cherry-pick folders.

Do not skim.

Every root folder and every meaningful subfolder must be accounted for.

Repository reality beats documentation.

---

SCOPE

Review the entire repository, including but not limited to:

Root files

docs/

backend/

frontend/

src/

tests/

scripts/

tools/

config/

configs/

infra/

docker/

.github/

migrations/

prisma/

database/

generated/

reports/

registers/

archives/

templates/

assets/

public/

build files

package files

environment examples

CI/CD files

deployment files

legacy folders

temporary folders

generated artifacts

---

EXECUTION RULES

1. Inventory the full repository tree.
2. Classify every root folder.
3. Classify every meaningful subfolder.
4. Classify every important file type.
5. Identify active folders.
6. Identify authority folders.
7. Identify source-code folders.
8. Identify test folders.
9. Identify scripts/tooling folders.
10. Identify config/infrastructure folders.
11. Identify generated-output folders.
12. Identify legacy folders.
13. Identify duplicate-purpose folders.
14. Identify misplaced files.
15. Identify obsolete files.
16. Identify temporary or build-output files that should not be tracked.
17. Identify documentation that is stored outside the docs framework.
18. Identify source files stored in documentation/report folders.
19. Identify reports stored in authority folders.
20. Identify root-level clutter.
21. Do not delete anything without explicit approval.
22. Do not modify application code.
23. Do not begin frontend work.

---

REQUIRED INVENTORY

Create a repository inventory showing:

Folder path

Purpose

File count

Important file types

Classification

Reviewed status

Recommended action

Classifications:

Active Source

Authority Documentation

Supporting Documentation

Generated Report

Test Asset

Script / Tooling

Configuration

Infrastructure

Migration / Database

Build Output

Temporary Artifact

Legacy

Archive

Unknown

Misplaced

Duplicate Purpose

---

NORMALIZATION TARGET

Propose a clean repository structure.

Do not over-engineer.

Keep it practical.

Every folder must have one clear purpose.

Every file type must have one logical home.

Every generated artifact must either be ignored, archived, or placed in a reports/output folder.

Every authority document must live under the docs framework.

Every legacy artifact must be archived or classified.

---

DOCUMENTATION NORMALIZATION

Verify:

All authority docs are in correct folders.

All reports are in reports folders.

All decision records are in decisions folders.

All governance docs are in governance folders.

All backend docs are in backend docs folders.

All legacy docs are archived or cross-referenced.

No docs outside the docs framework compete with active authority docs.

---

CODEBASE NORMALIZATION

Verify:

Source code is in expected source folders.

Backend code is not mixed with generated reports.

Frontend code or placeholders are not mixed with backend authority docs.

Scripts are grouped logically.

Tests are discoverable.

Config files are not duplicated unnecessarily.

Database/migration files are discoverable.

Generated files are not mixed with source authority.

---

ROOT LEVEL REVIEW

Review all root-level files and folders.

Identify:

Files that should remain at root

Files that should move under docs/

Files that should move under scripts/

Files that should move under config/

Files that should move under archive/

Files that should be ignored

Files needing owner review

---

REQUIRED OUTPUTS

Create:

REPOSITORY_TREE_INVENTORY.md

REPOSITORY_CLASSIFICATION_MATRIX.md

REPOSITORY_NORMALIZATION_REPORT.md

ROOT_LEVEL_CLEANUP_PLAN.md

DOCUMENTATION_PLACEMENT_AUDIT.md

CODEBASE_PLACEMENT_AUDIT.md

GENERATED_ARTIFACT_REGISTER.md

LEGACY_AND_ARCHIVE_PLAN.md

REPOSITORY_RESTRUCTURING_PLAN.md

---

EXECUTION MODE

This phase should first produce the audit and restructuring plan.

If all moves are safe documentation/report/archive moves, execute them.

If a move affects application code, imports, build paths, tests, deployment, CI/CD, or runtime behavior, do not execute it.

Instead, list it under:

REQUIRES_OWNER_APPROVAL

---

SUCCESS CRITERIA

The audit is successful only if:

Every root folder is accounted for.

Every major subfolder is accounted for.

Every major file type is accounted for.

docs/ is normalized.

backend/source structure is understood.

scripts/tooling are classified.

tests are classified.

configs/infra are classified.

generated artifacts are classified.

legacy folders are classified.

root-level clutter is identified.

duplicate folder purposes are identified.

misplaced documents/files are identified.

No frontend authority capture begins before repository reality is understood.

Stop after audit, safe restructuring, and reporting.

Do not begin Phase 3.
