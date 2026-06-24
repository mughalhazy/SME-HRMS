# GIT STATUS NORMALIZATION REPORT

Date: 2026-06-24
Status: NORMALIZED

---

## BEFORE NORMALIZATION

State: No git repository. All 816 tracked files were untracked.

---

## CLASSIFICATION OF ALL TRACKED FILES

| Class | Count | Examples |
|-------|-------|---------|
| SOURCE | ~350 | `backend/*.py`, `backend/services/**/*.py` |
| CONFIG | ~20 | `backend/docker-compose.yml`, `backend/Dockerfile*`, `backend/pytest.ini`, `backend/requirements.txt` |
| DOCS | ~200 | `docs/**/*.md`, `backend/docs/**/*.md`, `ops/*.md` |
| TESTS | ~90 | `backend/tests/**/*.py`, `backend/conftest.py` |
| SCRIPTS | ~10 | `backend/start.sh`, `backend/script/*.py`, `backend/deployment/*.py` |
| REPORTS | ~50 | `docs/08_reports/*.md` |
| CONTRACTS | ~47 | `contracts/*.json` |
| WIREFRAMES | ~62 | `frontend/pages/*.html`, `frontend/seeds/*.html` |
| MIGRATIONS | ~15 | `backend/deployment/migrations/*.sql` |
| FRONTEND_SOURCE | ~80 | `backend/ui/app/**/*.tsx`, `backend/ui/components/**/*.tsx` |
| LOCKFILES | 1 | `backend/ui/package-lock.json` |

---

## ITEMS EXCLUDED FROM TRACKING (GITIGNORED)

| Item | Size | Reason |
|------|------|--------|
| `backend/.venv/` | 37.41 MB | Python virtual environment |
| `.workspace/` | <0.1 MB | Workspace-local cache/temp (created this session) |
| `.claude/` | <0.1 MB | Claude Code local tooling |
| Source `__pycache__/` | Cleaned | Python bytecode (cleaned prior run) |
| `backend/Lib/` | Cleaned | Leaked venv (cleaned prior run) |
| `backend/Scripts/` | Cleaned | Leaked venv executables (cleaned prior run) |

---

## GIT NOISE REMOVED

| Issue | Resolution |
|-------|-----------|
| No .gitattributes | Created — LF enforced for Linux/CI |
| CRLF warnings on Windows | Fixed by `.gitattributes eol=lf` |
| `.claude/` unprotected | Added to `.gitignore` |
| `safe.directory` not set | `git config --global --add safe.directory` run |

---

## BRANCH NORMALIZATION

| Branch | State |
|--------|-------|
| `main` | Created — baseline commit `887cde4` |
| `develop` | Created — matches CI config |

---

## WORKING TREE AFTER BASELINE COMMIT

Working tree is clean except for reports created AFTER the baseline commit was staged. These are staged and committed in the follow-up report commit.

---

## VERDICT: NORMALIZED
