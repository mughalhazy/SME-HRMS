# LOCAL-TO-GITHUB EXACT MIRROR BASELINE

OBJECTIVE

Make the GitHub repository match the local sealed SaaS repository exactly before frontend work begins.

Local repository is the source of truth.

GitHub must become an exact mirror of local repository contents, structure, branch, and commit state.

This phase intentionally removes ambiguity from previous GitHub commits/history.

---

CORE RULE

LOCAL WINS.

Remote GitHub must match local.

Do not merge remote noise into local.

Do not preserve old GitHub commits if they are not part of the approved local sealed baseline.

---

SAFETY RULES

Before any destructive remote update:

1. Confirm current directory is the correct SaaS repository root.
2. Confirm GitHub remote belongs to this exact SaaS project.
3. Confirm repository is private.
4. Confirm local repo has no secrets staged/tracked.
5. Confirm local repo has no build/cache/runtime/bloat tracked.
6. Confirm local sealed baseline is committed.
7. Create a local safety tag before remote overwrite.

If any of these cannot be verified, fix automatically where safe.

Only stop if the remote identity is uncertain or secret exposure is detected.

---

PART A — VERIFY LOCAL SOURCE OF TRUTH

Run:

git status --short
git branch --show-current
git log --oneline --decorate -5
git remote -v

Verify:

- correct repo root
- correct project files
- clean/sealed workspace
- current branch intended for GitHub
- local baseline commit exists

If working tree is dirty:

- classify changes
- stage valid source/docs/config/test/report changes
- exclude bloat/secrets/cache
- commit with:

chore: finalize sealed local baseline before remote mirror

---

PART B — SECRET AND BLOAT FINAL CHECK

Run a final scan for:

- .env
- .env.*
- credentials
- tokens
- private keys
- node_modules
- build outputs
- dist
- coverage
- runtime outputs
- logs
- cache
- temp
- test-output
- __pycache__
- *.pyc

If found tracked:

- untrack safe generated files
- update .gitignore
- commit cleanup

Do not push secrets.

---

PART C — CREATE SAFETY TAG

Create a local tag:

pre-frontend-local-baseline

If tag exists, create timestamped tag:

pre-frontend-local-baseline-YYYYMMDD-HHMM

This tag records the approved local baseline before remote overwrite.

---

PART D — VERIFY REMOTE IDENTITY

Fetch remote metadata:

git remote -v
git ls-remote --heads origin

Confirm:

- remote URL is correct
- repo name matches this SaaS project
- repo is intended target
- branch target is correct

If remote is wrong:

- correct remote if correct URL is known
- otherwise stop and request correct URL

---

PART E — REMOTE MIRROR OPERATION

Make GitHub branch exactly match local branch.

Use safer force-with-lease, not blind force:

git push --force-with-lease origin HEAD:main

If project uses another branch name, push to that branch instead.

Do not push multiple branches unless explicitly required.

Do not push tags unless required.

---

PART F — POST-PUSH VERIFICATION

After push:

git fetch origin

Verify:

- local HEAD equals origin/main
- no remote divergence
- remote branch points to same commit
- GitHub contains same tracked file set as local

Run:

git rev-parse HEAD
git rev-parse origin/main
git diff --stat HEAD origin/main
git diff --name-status HEAD origin/main

Expected:

- same commit hash
- empty diff
- no file differences

---

PART G — FINAL REPORT

Create:

GITHUB_EXACT_MIRROR_BASELINE_REPORT.md

Include:

- repository root
- branch
- remote URL
- local commit hash
- remote commit hash
- safety tag
- files tracked count
- ignored bloat summary
- secret scan result
- diff result
- final verdict

Final verdict must be:

EXACT_MIRROR_CONFIRMED

or

ESCALATION_REQUIRED

---

SUCCESS CRITERIA

- Local repository is source of truth.
- GitHub main branch exactly matches local HEAD.
- Previous GitHub noise/history removed from active branch.
- No secrets pushed.
- No bloat pushed.
- No cache/runtime/build artifacts pushed.
- Local and GitHub are identical before frontend begins.
