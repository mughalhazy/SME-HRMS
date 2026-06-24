# ROOT LEVEL CLEANUP PLAN

Status: Active
Created: 2026-06-16
Phase: Full Repository Normalization and Reality Audit

---

## PURPOSE

Documents the current root-level files and folders, identifies what should remain at root, and specifies where each displaced file should move.

---

## PRINCIPLE

Root-level files should be limited to:
- Standard project entry points (README.md, LICENSE, .gitignore)
- Build/tooling manifests (package.json, Makefile, docker-compose if at project level)
- CI/CD configuration (must be at `.github/`)
- Nothing else

Session execution prompts, documentation, mandate files, and Windows shortcuts do not belong at root.

---

## CURRENT ROOT CONTENTS

### Folders (7)

| Folder | Should Stay at Root? | Reason |
|--------|---------------------|--------|
| `.claude/` | YES | Tool-managed; required at root |
| `.github/` | YES | GitHub Actions requires this location |
| `backend/` | YES | Primary source tree |
| `contracts/` | YES | UI contract specifications — project-level asset |
| `design/` | CONDITIONAL | Should eventually move into docs/ during Frontend Authority Capture |
| `docs/` | YES | Authority documentation framework |
| `frontend/` | CONDITIONAL | HTML wireframes archive — low-impact, but consider renaming to `frontend-wireframes/` for clarity |
| `ops/` | YES | Operational session artifacts (active: ops/pending.md) |

### Files (7)

| File | Stays at Root | Move To | Action |
|------|--------------|---------|--------|
| `(C) Phoenix LiteOS.lnk` | NO | Delete | REQUIRES_OWNER_APPROVAL — Windows shortcut file, unrelated to project |
| `GOVERNANCE IMPLEMENTATION PHASE 1.md` | NO | `docs/mandates/` | Safe documentation move |
| `PHASE 1 GOVERNANCE VALIDATION.md` | NO | `docs/mandates/` | Safe documentation move |
| `AUDIT REMEDIATION.md` | NO | `docs/mandates/` | Safe documentation move |
| `PHASE 2 – BACKEND AUTHORITY CAPTURE.md` | NO | `docs/mandates/` | Safe documentation move |
| `DOCUMENTATION NORMALIZATION AND AUTHORITY CONSOLIDATION.md` | NO | `docs/mandates/` | Safe documentation move |
| `FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md` | NO | `docs/mandates/` | Safe documentation move (after completion) |

---

## MISSING ROOT FILES

These standard root files are expected but not found at root level:

| File | Expected | Current Location | Recommendation |
|------|----------|-----------------|----------------|
| `README.md` | YES | Not at root (exists at `backend/README.md` and `backend/deployment/README.md`) | Create root README.md pointing to backend/README.md |
| `.gitignore` | YES | Only `backend/.gitignore` exists | Create root `.gitignore` (exclude `.claude/`, `.venv/` etc.) |
| `LICENSE` | OPTIONAL | Not present | Owner decision |

---

## PROPOSED CLEAN ROOT

After cleanup:

```
/
├── .claude/              ← tool memory (unchanged)
├── .github/              ← CI/CD (unchanged)
├── backend/              ← source tree (unchanged)
├── contracts/            ← UI contracts (unchanged)
├── design/               ← design docs (until Frontend Authority Capture consolidates)
├── docs/                 ← authority framework (unchanged)
├── frontend/             ← HTML wireframe archive (keep or rename)
├── ops/                  ← session ops artifacts (unchanged)
├── README.md             ← NEW — root project entry point
└── .gitignore            ← NEW — root gitignore
```

---

## SAFE MOVES (can execute immediately)

### Create `docs/mandates/` and move 6 root mandate files

These are pure documentation moves — no code, no imports, no build paths affected.

| Source | Destination |
|--------|------------|
| `GOVERNANCE IMPLEMENTATION PHASE 1.md` | `docs/mandates/GOVERNANCE_IMPLEMENTATION_PHASE_1.md` |
| `PHASE 1 GOVERNANCE VALIDATION.md` | `docs/mandates/PHASE_1_GOVERNANCE_VALIDATION.md` |
| `AUDIT REMEDIATION.md` | `docs/mandates/AUDIT_REMEDIATION.md` |
| `PHASE 2 – BACKEND AUTHORITY CAPTURE.md` | `docs/mandates/PHASE_2_BACKEND_AUTHORITY_CAPTURE.md` |
| `DOCUMENTATION NORMALIZATION AND AUTHORITY CONSOLIDATION.md` | `docs/mandates/DOCUMENTATION_NORMALIZATION_AND_AUTHORITY_CONSOLIDATION.md` |
| `FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md` | `docs/mandates/FULL_REPOSITORY_NORMALIZATION_AND_REALITY_AUDIT.md` |

**Status: SAFE TO EXECUTE** — these are documentation-only moves, no code references these files.

---

## REQUIRES_OWNER_APPROVAL

| Item | Issue | Why Owner Must Decide |
|------|-------|----------------------|
| `(C) Phoenix LiteOS.lnk` | Windows shortcut at project root | Deletion is irreversible; may be intentional (linked tool?) |
| `design/` rename/move | Contains active authority docs referenced in design sessions | Timing: should move during Frontend Authority Capture, not now |
| `frontend/` rename | HTML wireframes archive | Renaming to `frontend-wireframes/` clarifies purpose but is cosmetic |
