# BLOAT CLEANUP REPORT

Date: 2026-06-24
Status: COMPLETE
Total Reclaimed: 28.44 MB

---

## DELETED ITEMS (CONFIRMED)

### 1. Leaked Partial Venv — `backend/Lib/` (22.96 MB)

**What it was:** A `site-packages` tree at `backend/Lib/site-packages/` — a partial virtual environment installed directly into the `backend/` directory root instead of into `backend/.venv/`. It contained pip, pytest, pygments, and their transitive pycache artifacts. It had a sibling `backend/Scripts/` with venv executables.

**Why deleted:** Completely redundant with `backend/.venv/` which is the proper, complete virtual environment. `backend/.venv/` contains all the same packages plus more, with a valid `pyvenv.cfg`. The `backend/Lib/` tree had no `pyvenv.cfg` — confirming it was a leak from a direct `pip install` into the wrong location.

**Impact:** None — `backend/.venv/` remains intact and functional.

---

### 2. Leaked Venv Executables — `backend/Scripts/` (0.52 MB)

**What it was:** `pip3.14.exe`, `pip3.exe`, `py.test.exe`, `pygmentize.exe`, `pytest.exe` at `backend/Scripts/` — the executable half of the leaked partial venv.

**Why deleted:** Same reason as `backend/Lib/` — sibling artifacts from the same leaked install. The proper executables exist in `backend/.venv/Scripts/`.

**Impact:** None.

---

### 3. Test Cache — `backend/.pytest_cache/` (0.04 MB)

**What it was:** pytest's cache directory, generated on last test run.

**Why deleted:** Pure generated artifact. Regenerated automatically on next `pytest` invocation.

**Impact:** None — first `pytest` run will be marginally slower (cold cache).

---

### 4. Source Code `__pycache__/` — 34 directories (4.92 MB)

**What they were:** Python bytecode cache directories generated inside source code directories when the application was run. Located in:

- `backend/__pycache__/` (2.70 MB — root-level imports)
- `backend/api/__pycache__/`
- `backend/api-gateway/__pycache__/`
- `backend/attendance_service/__pycache__/`
- `backend/audit_service/__pycache__/`
- `backend/config/__pycache__/`
- `backend/core/__pycache__/`
- `backend/country/**/__pycache__/`
- `backend/docker/__pycache__/`
- `backend/integrations/**/__pycache__/`
- `backend/mobile/**/__pycache__/`
- `backend/services/**/__pycache__/`
- `backend/tests/**/__pycache__/` (1.25 MB)

**Why deleted:** Pure generated artifacts. Python regenerates these on next import. Already gitignored via `__pycache__/` and `*.py[cod]` in `.gitignore`.

**Impact:** None — regenerated automatically on next `python` or `pytest` invocation.

---

## NOT DELETED (KEPT)

| Item | Size | Reason Kept |
|------|------|-------------|
| `backend/.venv/` | 37.41 MB | Proper virtual environment — required |
| `backend/.venv/Lib/site-packages/__pycache__/` | ~8 MB (inside .venv) | Part of venv — gitignored with `.venv/` |
| All source `.py` files | N/A | Required source code |
| All migration files | N/A | Required source code |
| All test files | N/A | Required tests |
| All config files | N/A | Required configs |
| All docs | N/A | Required documentation |

---

## SUMMARY TABLE

| Category | Count | Size | Action |
|----------|-------|------|--------|
| Leaked partial venv (Lib + Scripts) | 2 dirs | 23.48 MB | DELETED |
| pytest cache | 1 dir | 0.04 MB | DELETED |
| Source `__pycache__/` | 34 dirs | 4.92 MB | DELETED |
| **TOTAL RECLAIMED** | **37 dirs** | **28.44 MB** | |
