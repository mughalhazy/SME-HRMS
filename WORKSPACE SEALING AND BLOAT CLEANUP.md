# WORKSPACE SEALING AND BLOAT CLEANUP

OBJECTIVE

Seal the workspace/repository so npm, dependencies, cache, temp files, runtime files, build outputs, logs, test artifacts, and generated bloat do not leak into C:.

Also clean the repository so only required source, configuration, documentation, tests, scripts, and approved artifacts remain.

This phase is repository hygiene and sealing only.

Do not change application logic.

Do not change APIs.

Do not change database schemas.

Do not change architecture.

---

CORE RULES

1. Keep the workspace self-contained.
2. No npm/cache/temp/build/runtime leakage into C:.
3. No unnecessary generated artifacts committed or left in active workspace.
4. No deleting source code.
5. No deleting required configs.
6. No deleting required docs.
7. No deleting required tests.
8. If uncertain, move to archive/quarantine instead of deleting.

---

PART A — DISCOVERY

Audit the full workspace for:

- node_modules
- .next
- dist
- build
- coverage
- .turbo
- .vite
- .cache
- .parcel-cache
- logs
- tmp
- temp
- runtime outputs
- test outputs
- screenshots
- generated reports
- compiled artifacts
- Python __pycache__
- .pyc files
- virtual environments
- lock/temp files
- duplicate dependency folders
- local build artifacts
- package manager caches
- npm/pnpm/yarn cache paths
- environment-generated files

Also inspect:

- package.json scripts
- npm config
- pnpm config
- yarn config
- vite/next configs
- test configs
- build configs
- env examples
- CI configs
- runtime scripts
- start scripts

---

PART B — C: LEAKAGE AUDIT

Verify whether any process writes or is configured to write to C:.

Check:

- npm cache path
- pnpm store path
- yarn cache path
- node temp path
- build output paths
- test output paths
- coverage paths
- runtime output paths
- log paths
- dependency install paths
- script-created paths
- environment variables
- TEMP / TMP usage
- tool-specific cache paths

Create a table:

Path / Tool / Current Location / Risk / Required Fix

---

PART C — SEALING PLAN

Create local workspace paths for:

- npm cache
- pnpm store
- yarn cache
- temp
- build output
- runtime output
- logs
- test output
- coverage
- artifacts

Use workspace-local folders only.

Example pattern:

.workspace/
  cache/
  temp/
  logs/
  runtime/
  test-output/
  coverage/
  artifacts/

Do not use C:.

---

PART D — SAFE CLEANUP

Remove or quarantine generated bloat only.

Clean:

- build outputs
- runtime outputs
- test outputs
- coverage outputs
- logs
- temp folders
- stale screenshots
- stale generated reports
- obsolete compiled artifacts
- __pycache__
- .pyc
- duplicate caches
- abandoned output folders

Do not remove source, configs, docs, tests, migrations, package manifests, lockfiles, or required scripts.

If uncertain, move to:

archive/quarantine_cleanup/

with a manifest.

---

PART E — CONFIG UPDATES

Update safe configuration only where needed to keep outputs workspace-local.

Possible safe updates:

- .npmrc
- .yarnrc
- .pnpm-store config
- package scripts output paths
- test output paths
- coverage output paths
- runtime log paths
- temp/cache env wrappers
- .gitignore

Do not alter application behavior.

---

PART F — GITIGNORE / TRACKING CLEANUP

Update .gitignore to exclude:

- node_modules
- build outputs
- runtime outputs
- logs
- temp
- cache
- coverage
- test artifacts
- .pyc
- __pycache__
- local env files
- generated bloat

Do not ignore required source/config/docs.

---

PART G — VALIDATION

Validate:

1. Repository builds or scripts still discoverable.
2. Required source files remain.
3. Required docs remain.
4. Required configs remain.
5. Required tests remain.
6. No broken references caused by cleanup.
7. No C: paths remain in npm/cache/build/runtime/test settings.
8. Cleanup did not remove required files.
9. Workspace remains self-contained.

Use evidence, not claims.

---

REQUIRED OUTPUTS

Create:

WORKSPACE_SEALING_REPORT.md

C_DRIVE_LEAKAGE_AUDIT.md

BLOAT_CLEANUP_REPORT.md

CLEANUP_QUARANTINE_MANIFEST.md

GITIGNORE_UPDATE_REPORT.md

POST_CLEANUP_VALIDATION_REPORT.md

SEALED_WORKSPACE_FINAL_STATUS.md

---

FINAL STATUS MUST INCLUDE

- Files/folders removed
- Files/folders quarantined
- Configs updated
- .gitignore changes
- C: leakage risks found
- C: leakage risks fixed
- Remaining risks
- Validation commands run
- Final verdict

Final verdict must be one of:

SEALED_PASS

SEALED_PASS_WITH_FINDINGS

PARTIAL

FAIL

---

SUCCESS CRITERIA

Workspace is lean.

Generated bloat removed or quarantined.

Runtime/build/test/cache outputs are workspace-local.

No known npm/dependency/cache/temp/build/runtime leakage to C:.

No required project files removed.

No application behavior changed.

Stop after sealing, cleanup, and validation.
