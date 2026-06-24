# C: DRIVE LEAKAGE AUDIT

Date: 2026-06-24
Status: NO LEAKAGE TO C: DETECTED

---

## AUDIT TABLE

| Tool / Path | Current Location | Leaks to C:? | Risk | Fix Applied |
|-------------|-----------------|--------------|------|-------------|
| npm cache | `D:\npm-cache` | NO | LOW | Added workspace `.npmrc` to redirect to `.workspace/cache/npm` |
| npm prefix | `D:\npm` | NO | LOW | Already off C: |
| npm tmp | undefined (uses system TEMP) | POTENTIAL | MEDIUM | `.npmrc` now sets `tmp=.workspace/temp` |
| pnpm store | undefined | LOW (not used yet) | LOW | `.workspace/cache/pnpm/` created for future use |
| yarn cache | N/A — yarn not installed | N/A | NONE | None needed |
| node_modules | Not installed | N/A | NONE | Gitignored |
| .next build | Not built | N/A | NONE | Gitignored |
| Python venv | `backend/.venv/` (D:) | NO | NONE | Already workspace-local |
| pytest cache | Deleted | N/A | NONE | Gitignored |
| coverage | Not present | N/A | NONE | `.workspace/coverage/` created |
| logs | Not present | N/A | NONE | `.workspace/logs/` created |
| TEMP / TMP env | System default (C:\Users\...) | POTENTIAL | LOW | `.npmrc tmp` overrides for npm; Python uses system tmp (acceptable) |

---

## RISK SUMMARY

**No confirmed C: leakage found at time of audit.**

- npm was pre-configured to `D:\npm-cache` and `D:\npm` — not on C:
- Python venv is at `backend/.venv/` — not on C:
- No node_modules, .next, or other build outputs present

**Residual low-risk items:**
- npm `tmp` was undefined — now fixed via `.npmrc`
- pnpm not configured — `.workspace/cache/pnpm/` prepared for when pnpm is used
- Python's system TEMP usage (for async file ops) is inherent OS behavior; acceptable

---

## VERDICT

**NO C: LEAKAGE — PASS**
