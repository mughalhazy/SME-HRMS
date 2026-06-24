# Meridian HCM — Build Protocol SOP
## Version: 1.2 | Date: 2026-03-24
## Status: LOCKED

---

## PURPOSE

Mandatory sequence governing every change to the Meridian HCM UI system.
Ensures every page is repo-anchored, audit-trailed, and gap-registered before delivery.

---

## WHEN TO USE

Every time any of the following occurs:
- Building a new page (HTML · contract · schema)
- Modifying an existing page
- Adding or updating gap register entries
- Adding or updating design register entries
- Adding or updating contract or schema files

---

## THE 9-STEP PROTOCOL

```
Step 1  AUDIT BASELINE
        py -X utf8 hrms-audit-v1.py
        Must be clean before proceeding.
        If drifted: investigate. Do not proceed until resolved.

Step 2  READ REPO
        Read service files for this page:
        models · schemas/service · routes/api · SQL (if present)
        Ground truth for all data decisions.

Step 3  READ DESIGN LANGUAGE
        Read design-language.html and the seed page for this archetype.
        Confirm: layout · density · colour · component rules · patterns.
        This is a READ — open both files, find the relevant sections.

Step 4  READ DESIGN REGISTER
        Read hrms-design-register-v1.md.
        Identify patterns that apply to this page.

Step 5  READ GAP REGISTER
        Read hrms-ui-backend-gaps.md.
        Note existing gaps affecting this page.

Step 6  LOG NEW GAPS
        Before writing any code:
        Log every new gap discovered in steps 2–5.
        Then: py -X utf8 hrms-audit-v1.py → seal gap register before proceeding.

Step 7  BUILD
        Write the HTML / contract / schema file.
        Mock data must conform to real API shape.
        Mock data must use real enum values from hrms-api-contracts.md.
        No invented fields.
        P-32 scroll rule — apply the correct pattern for the archetype being built:
          H01 .page        → flex:1; overflow-y:auto; min-height:0; padding:24px 24px 12vh
          H02 .table-wrap  → flex:1; overflow-y:auto; min-height:0; padding-bottom:12vh
          H03 .page        → flex:1; overflow-y:auto; min-height:0
              .prof-head   → position:sticky; top:0; z-index:10
              .tab-scroll  → display:block; padding-bottom:12vh (or 22px 26px 12vh if padded)
          H04 .form-main   → overflow-y:auto; min-height:0
              .form-rail   → overflow-y:auto; min-height:0
          H05 .list-col    → overflow-y:auto; min-height:0; padding-bottom:12vh
              .detail-col  → display:flex; flex-direction:column; overflow:hidden; min-height:0
              .dp-sects    → flex:1; overflow-y:auto; min-height:0; padding-bottom:12vh
              .dp-actions  → flex-shrink:0  (action bar always visible — never scrolled away)
          H06 .cal-area    → flex:1; overflow:hidden; min-height:0
              .cal-sidebar → overflow-y:auto; min-height:0
              .cal-main    → flex:1; display:flex; flex-direction:column; overflow:hidden; min-height:0
              .cal-grid    → flex:1; overflow-y:auto; min-height:0; padding-bottom:12vh
              roster pages → .roster-wrap: overflow:auto; min-height:0; padding-bottom:12vh
                             (overflow:auto not overflow-y:auto — both axes needed for sticky col)
          Without min-height:0: overflow-y:auto silently fails in flex containers.
          Without padding-bottom:12vh: html{zoom:1.1} clips the last ~10% of content.

Step 8  POST-BUILD AUDIT
        py -X utf8 hrms-audit-v1.py
        Only the file just built should appear as drifted.
        If unexpected files drifted: STOP — investigate before sealing.

Step 9  SEAL + DELIVER
        py -X utf8 hrms-audit-v1.py --sync
        Then deliver (present_files or equivalent).
```

---

## SINGLE CHANGE = SINGLE AUDIT

```
CORRECT:
  change 1 → audit → seal
  change 2 → audit → seal

WRONG:
  change 1, change 2, change 3 → audit → seal
```

---

## AUDIT COMMANDS

```
py -X utf8 hrms-audit-v1.py              → full audit (before and after every change)
py -X utf8 hrms-audit-v1.py --sync       → seal after approved changes
py -X utf8 hrms-audit-v1.py --contracts  → contract-layer checks (before contract work)
py -X utf8 hrms-audit-v1.py --add <p>    → register new file
py -X utf8 hrms-audit-v1.py --check <n>  → single file status
py -X utf8 hrms-audit-v1.py --rebuild    → convert absolute paths to relative (first run on new machine)
```

---

## HIERARCHY OF AUTHORITY

```
1. Repo (service files · models · SQL)   → ground truth for data
2. design-language.html                   → ground truth for presentation
3. Seed pages (p1–p13)                   → ground truth for archetype layout
4. hrms-design-register-v1.md            → ground truth for solved visual problems
5. Gap register                           → ground truth for what is deferred
6. Prompt / instruction                   → additive only — never overrides 1–5
```

A prompt that conflicts with the repo is declined.
A prompt that conflicts with the design language is flagged.

---

## PROTOCOL VIOLATIONS

If a step was skipped:
```
Do not continue.
Run py -X utf8 hrms-audit-v1.py immediately.
If clean: log the skip, proceed from the missed step.
If drifted: restore from manifest before proceeding.
```

---

## SESSION END CHECKLIST

```
□ py -X utf8 hrms-audit-v1.py → all expected files clean
□ Gap register updated with all new gaps this session
□ Design register updated with all new patterns this session
□ No open regressions in any page
```
