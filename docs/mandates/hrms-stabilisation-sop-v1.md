# Meridian HCM — Stabilisation Pass SOP
## Version: 2.0 | Date: 2026-03-30
## Status: PASSES 1–13 COMPLETE · ALL 13 ARCHETYPES SEALED

---

## PURPOSE

A single controlled sweep that reconciles visual and token inconsistencies across all built pages after a phase completes. Not a redesign. Alignment only.

---

## WHAT IT IS NOT

```
NOT a redesign          → no new components or patterns
NOT a feature pass      → no new columns, filters, or actions
NOT a regression fix    → regressions are fixed immediately during build
NOT optional            → required before moving to next archetype phase
NOT continuous          → runs once per phase, not after every page
```

---

## WHEN TO TRIGGER

```
All pages in a phase are built and sealed
AND py -X utf8 hrms-audit-v1.py → all tracked files clean
AND no open regressions
```

---

## STABILISATION PROCEDURE

```
Step 1  Audit baseline → must be fully clean
Step 2  Inventory all known items for this phase
Step 3  File by file — one at a time:
          change → audit → seal → next file
Step 4  Cross-page visual review (open all pages side by side)
Step 5  py -X utf8 hrms-audit-v1.py --contracts (contract checks)
Step 6  Final audit + seal
Step 7  Mark all items RESOLVED · increment version · log date
```

---

## REGRESSION vs STABILISATION

```
REGRESSION (fix immediately during build):
  - Page does not render
  - Wrong data displayed
  - Interaction broken
  - Layout broken at normal viewport
  - Scroll container not scrolling (flex scroll bug — see P-32)

STABILISATION (defer to pass):
  - Minor token mismatch (wrong shade)
  - Font weight 1 step off
  - Padding 2px inconsistency
  - Column proportions slightly uneven
```

When uncertain: if the page is functional and the user can complete their workflow — defer.

---

## KNOWN ITEMS

```
ITEM FORMAT:
  ITEM N — [title]
  Affected pages: [list]
  Current value:  [what it is]
  Target value:   [what it should be]
  Design ref:     [pattern or token]
  Fix:            [one line]
```

### H06 Pass Items — RESOLVED 2026-03-24

```
ITEM 1 — Chip padding off P-07 spec
  Affected pages: h06-attendance-timeline · h06-shift-roster
  Current value:  .chip { padding: 2px 7px }
  Target value:   padding: 2px 8px
  Design ref:     P-07 · Chip Colours (horizontal padding 8px)
  Fix:            Updated .chip rule in both pages
  Status:         ✅ RESOLVED

ITEM 2 — Table row hover missing transition
  Affected pages: h06-attendance-timeline · h06-shift-roster
  Current value:  tbody tr:hover td { background: var(--t6) } — no transition property
  Target value:   transition: background .12s on tbody tr:hover td and tbody tr td.td-emp
  Design ref:     P-11 · Tables (body row: hover bg · transition 120ms) · P-27 --dur-micro: 120ms
  Fix:            Added transition:background .12s to tbody tr:hover td and tbody tr td.td-emp
  Status:         ✅ RESOLVED
```

---

### H05 Pass Items — RESOLVED 2026-03-23

```
ITEM 1 — Inline chip in dp-sub overrides P-07 spec
  Affected pages: h05-approval-inbox
  Current value:  style="font-size:10px;padding:1px 7px" on .chip.cr
  Target value:   No inline override — .chip class defaults (font-size:11px · padding:2px 8px)
  Design ref:     P-07 · Chip Colours
  Fix:            Removed inline style attribute
  Status:         ✅ RESOLVED

ITEM 2 — Card quick-action buttons off P-08 small spec
  Affected pages: h05-approval-inbox
  Current value:  .ab { font-size:11.5px · padding:5px 11px }
  Target value:   font-size:12px · padding:4px 10px
  Design ref:     P-08 · Buttons (Small variant)
  Fix:            Updated .ab rule
  Status:         ✅ RESOLVED

ITEM 3 — Approval card hover transition off P-27 micro token
  Affected pages: h05-approval-inbox
  Current value:  .appr { transition:background .09s }
  Target value:   transition:background .12s
  Design ref:     P-27 · Motion Tokens (--dur-micro: 120ms · row/card hover)
  Fix:            Changed .09s → .12s in .appr rule
  Status:         ✅ RESOLVED
```

---

### H04 Pass Items — RESOLVED 2026-03-23

```
ITEM 1 — .form-main top padding off spec
  Affected pages: h04-add-employee
  Current value:  padding: 24px 26px 32px
  Target value:   padding: 22px 26px 32px
  Design ref:     H04 archetype standard (all 8 other pages)
  Fix:            Updated .form-main rule
  Status:         ✅ RESOLVED

ITEM 2 — .form-footer vertical padding off spec
  Affected pages: h04-add-employee
  Current value:  padding: 12px 24px
  Target value:   padding: 13px 24px
  Design ref:     H04 archetype standard (all 8 other pages)
  Fix:            Updated .form-footer rule
  Status:         ✅ RESOLVED

ITEM 3 — .ais-chip horizontal padding 1px off spec
  Affected pages: h04-add-employee
  Current value:  padding: 2px 7px
  Target value:   padding: 2px 8px
  Design ref:     P-07 · Chip spec (horizontal padding 8px)
  Fix:            Updated .ais-chip rule
  Status:         ✅ RESOLVED

ITEM 4 — Inline revision history chips off P-07 spec
  Affected pages: h04-salary-revision
  Current value:  padding:1px 7px · no text-transform · no letter-spacing
  Target value:   padding:2px 8px · text-transform:uppercase · letter-spacing:.04em
  Design ref:     P-07 · Chip Colours (status chip spec)
  Fix:            Updated 3 inline span styles in revision history table
  Status:         ✅ RESOLVED
```

---

### H03 Pass Items — RESOLVED 2026-03-23

```
ITEM 1 — .ph-row margin-bottom off spec
  Affected pages: h03-performance-review-detail
  Current value:  margin-bottom: 14px
  Target value:   margin-bottom: 18px
  Design ref:     H03 archetype standard (all 7 other pages)
  Fix:            Updated .ph-row rule
  Status:         ✅ RESOLVED

ITEM 2 — Breadcrumb separator HTML entity vs literal character
  Affected pages: h03-role-detail · h03-job-posting-detail
  Current value:  &rsaquo; (HTML entity)
  Target value:   › (literal Unicode — matches all other H03 pages)
  Design ref:     Source consistency · same render · markup alignment
  Fix:            replace_all &rsaquo; → › in both files
  Status:         ✅ RESOLVED
```

---

### H01 Pass Items — RESOLVED 2026-03-22

```
ITEM 1 — Chip border-radius off spec
  Affected pages: all 4 H01 pages
  Current value:  border-radius: 3px
  Target value:   border-radius: 99px
  Design ref:     P-07 · Chip Colours
  Fix:            Updated .chip rule in all 4 pages
  Status:         ✅ RESOLVED

ITEM 2 — Chip padding off spec
  Affected pages: all 4 H01 pages
  Current value:  padding: 2px 7px
  Target value:   padding: 2px 8px
  Design ref:     P-07 · Chip Colours
  Fix:            Updated .chip rule in all 4 pages
  Status:         ✅ RESOLVED

ITEM 3 — Chip missing uppercase + letter-spacing
  Affected pages: all 4 H01 pages
  Current value:  no text-transform, no letter-spacing
  Target value:   text-transform: uppercase · letter-spacing: 0.04em
  Design ref:     P-07 · Chip Colours
  Fix:            Added to .chip rule in all 4 pages
  Status:         ✅ RESOLVED
```

---

## PASS LOG

```
PASS 1 — H01 Dashboards
  Status:    ✅ COMPLETE — 2026-03-22 · scroll regression fix applied 2026-03-23
  Trigger:   All 4 H01 dashboard pages built and sealed
  Items:     3 items identified · 3 resolved · 0 deferred
  Regression fix: P-32 scroll fix applied to all 4 pages — .page min-height:0 + padding:24px 24px 12vh

PASS 2 — H02 Lists
  Status:    ✅ COMPLETE — 2026-03-22 · scroll regression fix applied 2026-03-23
  Trigger:   All 11 H02 list pages built and sealed
  Items:     0 stabilisation items — all pages built with correct P-07 chip spec and P-31 zoom from the outset
  Regression fix: P-32 scroll fix applied to all 11 pages — .table-wrap min-height:0 + padding-bottom:12vh

PASS 3 — H03 Detail pages (partial — H03 only)
  Status:    ✅ COMPLETE — 2026-03-23
  Trigger:   All 8 H03 detail pages built and sealed
  Items:     2 items identified · 2 resolved · 0 deferred
  Pre-known: P-32 full scroll fix applied to all H03 pages as regression fix — page-level
             overflow-y:auto, sticky .prof-head, .tab-scroll display:block + padding-bottom:12vh

PASS 4 — H04 Create / Edit Form pages
  Status:    ✅ COMPLETE — 2026-03-23
  Trigger:   All 9 H04 form pages complete ✅ · audit clean 74/74 ✅
  Items:     4 items identified · 4 resolved · 0 deferred
  Pre-known: P-32 (min-height:0) applied to form-main and form-rail on all pages from build time

PASS 5 — H05 Workflow / Approval
  Status:    ✅ COMPLETE — 2026-03-23
  Trigger:   Approval Inbox built and sealed ✅ · audit clean 76/76 ✅
  Items:     3 items identified · 3 resolved · 0 deferred
  Pre-known: P-32 H05 split-view pattern applied at build time — list-col overflow-y:auto +
             detail-col overflow:hidden + dp-sects overflow-y:auto + dp-actions flex-shrink:0

PASS 6 — H06 Calendar / Roster pages
  Status:    ✅ COMPLETE — 2026-03-24
  Trigger:   All 3 H06 pages built and sealed ✅ · audit clean 78/78 ✅
  Items:     2 items identified · 2 resolved · 0 deferred
  ITEM 1:    Chip padding off P-07 spec in h06-attendance-timeline + h06-shift-roster
             `.chip{padding:2px 7px}` → `padding:2px 8px` — P-07: padding 2px 8px
  ITEM 2:    Table row hover missing transition in h06-attendance-timeline + h06-shift-roster
             Added `transition:background .12s` to `tbody tr:hover td` and `tbody tr td.td-emp`
             P-11: body row hover bg · transition 120ms
  Pre-known: P-32 H06 calendar pattern applied at build time — cal-area overflow:hidden +
             cal-sidebar overflow-y:auto + cal-main overflow:hidden + cal-grid overflow-y:auto +
             roster-wrap overflow:auto (both axes for sticky-col + horizontal scroll)

PASS 7 — H07 Analytics / Reports pages
  Status:    ✅ COMPLETE — 2026-03-29
  Trigger:   All 5 H07 pages built and sealed ✅ · audit clean 88/88 ✅
  Items:     0 items identified · 0 resolved · 0 deferred
  Scan:      P-07 chip spec identical across all 5 pages ✅
             P-11 tbody tr td transition:background .12s ✅
             P-31 html{zoom:1.1} ✅
             P-32 overflow-y:auto;min-height:0 + padding-bottom:12vh ✅
             P-32 scrollTop=0 on tab switch ✅
             No inline chip overrides ✅
             class="sb-ico on" present on all pages ✅
  Pre-known: All H07 pages built with correct specs from the outset — P-33 fixed-layout wide table
             applied during build on h07-attendance-summary and h07-compliance-reports;
             KPI sparklines added to h07-compliance-reports during build session

PASS 8 — H08 Search / Discovery pages
  Status:    ✅ COMPLETE — 2026-03-29
  Trigger:   h08-global-search built and sealed ✅ · audit clean 90/90 ✅
  Items:     0 items identified · 0 resolved · 0 deferred
  Scan:      P-07 chip spec ✅ · P-11 transition:background .12s ✅
             P-31 zoom:1.1 ✅ · P-32 min-height:0 ×4 + padding-bottom:12vh ×2 ✅
             class="sb-ico on" ✅ · no inline chip overrides ✅
  Pre-known: P-32 H08 search pattern applied at build time — search-body grid overflow:hidden +
             facets min-height:0 + results-area min-height:0; both containers padding-bottom:12vh

PASS 9 — H09 Notifications Inbox
  Status:    ✅ COMPLETE — 2026-03-29
  Trigger:   h09-notifications-inbox built and sealed ✅ · audit clean 92/92 ✅
  Items:     0 items identified · 0 resolved · 0 deferred
  Scan:      P-07 chip spec (all 8 classes: cg/ca/cr/cb/ct/cv/cn) ✅
             P-12 AI bar (teal · confidence score · dismissable · never red) ✅
             P-31 html{zoom:1.1} ✅
             P-32 inbox-body grid overflow:hidden + msg-list overflow-y:auto min-height:0 +
                  detail-body overflow-y:auto min-height:0 · padding-bottom:12vh ×2 ✅
             No sb-ico href/onclick — chrome only ✅ · no inline chip overrides ✅
  Regression fix: reply-area moved inside detail-body scroll container (P-32 zoom clip fix)

PASS 10 — H10 Organisation Settings
  Status:    ✅ COMPLETE — 2026-03-29
  Trigger:   h10-org-settings built and sealed ✅ · audit clean 94/94 ✅
  Items:     0 items identified · 0 resolved · 0 deferred
  Scan:      P-07 chip spec (status/leave-type/category chips) ✅
             P-11 40px rows · transition:background .12s · sticky thead ✅
             P-31 html{zoom:1.1} ✅
             P-32 settings-body grid min-height:0 + settings-nav overflow-y:auto min-height:0
                  + settings-content overflow-y:auto min-height:0 · padding-bottom:12vh ×2 ✅
             class="sb-ico on" ✅ · no sb-ico href/onclick ✅ · no inline chip overrides ✅
  Pre-known: Chrome sections (Profile/Security/Notifications/Integrations/AI) carry chrome-notice
             banners citing BG-023–027 — not stabilisation items, by design

PASS 11 — H11 Workflow Builder
  Status:    ✅ COMPLETE — 2026-03-29
  Trigger:   h11-workflow-builder built and sealed ✅ · audit clean 96/96 ✅
  Items:     2 items identified · 2 resolved · 0 deferred
  ITEM 1:    .props-body missing padding-bottom:12vh
             `.props-body{flex:1;overflow-y:auto;min-height:0}` → added `padding-bottom:12vh`
             P-32: all scroll containers must have padding-bottom:12vh for zoom compensation
  ITEM 2:    .canvas-area missing padding-bottom:12vh
             `.canvas-area{…;padding:24px}` → `padding:24px 24px 12vh`
             P-32: zoom compensation required on all overflow:auto scroll containers
  Scan:      P-07 chip spec (ca/ct classes on canvas section badges) ✅
             P-31 html{zoom:1.1} line 9 ✅
             P-32 builder grid min-height:0 + palette overflow:hidden min-height:0 +
                  pal-body overflow-y:auto min-height:0 padding-bottom:12vh ✅
                  canvas-wrap overflow:hidden min-height:0 +
                  canvas-area overflow:auto min-height:0 padding-bottom:12vh ✅ (fixed)
                  props overflow:hidden min-height:0 +
                  props-body overflow-y:auto min-height:0 padding-bottom:12vh ✅ (fixed)
             class="sb-ico on" on builder/pencil icon ✅ · no sb-ico href/onclick ✅
             No inline chip overrides ✅
  Pre-known: Chrome palette sections (Form Fields · Notifications) and canvas sections
             (s1 Leave Details · s3 Auto Notification · s5 AI Pre-check) carry pal-comp-chrome
             class or chrome-notice banners citing BG-028/029 — by design

PASS 11b — H11 Survey Builder
  Status:    ✅ COMPLETE — 2026-03-29
  Trigger:   h11-survey-builder built and sealed ✅ · audit clean 98/98 ✅
  Items:     0 items identified · 0 resolved · 0 deferred
  Scan:      P-07 chip spec (ca/ct/cg/cb classes on canvas section badges + topbar status chip) ✅
             P-31 html{zoom:1.1} line 9 ✅
             P-32 builder grid min-height:0 + palette overflow:hidden min-height:0 +
                  pal-body overflow-y:auto min-height:0 padding-bottom:12vh ✅
                  canvas-wrap overflow:hidden min-height:0 +
                  canvas-area overflow:auto min-height:0 padding:24px 24px 12vh ✅
                  props overflow:hidden min-height:0 +
                  props-body overflow-y:auto min-height:0 padding-bottom:12vh ✅
             class="sb-ico on" on builder/pencil icon ✅ · no sb-ico href/onclick ✅
             No inline chip overrides ✅
  Pre-known: Chrome palette items (Short Text · Long Text · Rating Stars · Multi-choice · NPS ·
             Page Break · Anonymity · Response Window · Reminder Schedule) carry pal-comp-chrome
             class citing BG-030 — by design

PASS 11c — H11 Report Builder
  Status:    ✅ COMPLETE — 2026-03-30
  Trigger:   h11-report-builder built and sealed ✅ · audit clean 100/100 ✅
  Items:     0 items identified · 0 resolved · 0 deferred
  Scan:      P-07 chip spec (chip-green/amber/teal/blue/grey classes, correct padding/radius) ✅
             P-31 html{zoom:1.1} line 6 ✅
             P-32 builder grid min-height:0 + palette overflow:hidden +
                  pal-body overflow-y:auto min-height:0 padding:10px 10px 12vh ✅
                  canvas-area overflow:auto min-height:0 padding:24px 24px 12vh ✅
                  props-body overflow-y:auto min-height:0 padding-bottom:12vh ✅
             class="sb-ico on" on builder/pencil icon ✅ · no sb-ico href/onclick ✅
             No inline chip overrides ✅
  Pre-known: Chrome palette items (Visualization Config · Delivery Destination) carry
             pal-comp-chrome class citing BG-031. Canvas s3 Delivery card is chrome-card
             with disabled inputs — by design.

PASS 12 — H12 Helpdesk
  Status:    ✅ COMPLETE — 2026-03-30
  Trigger:   h12-helpdesk built and sealed ✅ · audit clean 102/102 ✅
  Items:     0 items identified · 0 resolved · 0 deferred
  Scan:      P-07 chip spec (chip-red/amber/blue/grey/green classes) ✅
             P-31 html{zoom:1.1} line 8 ✅
             P-32 support-body grid min-height:0 ✅
                  ticket-list flex-column overflow:hidden min-height:0 ✅
                  tl-scroll overflow-y:auto flex:1 min-height:0 ✅
                  ticket-detail overflow:hidden min-height:0 ✅
                  td-body display:grid min-height:0 ✅
                  td-main + td-rail overflow-y:auto min-height:0 padding-bottom:12vh ✅
                  reply-area flex-shrink:0 (outside scroll) ✅
             class="sb-ico on" on Helpdesk icon ✅ · no sb-ico href/onclick ✅
             No inline chip overrides ✅
  Pre-known: Chrome items (Priority select · Reassign · Merge · Forward) carry
             disabled/title tooltip citing BG-032 — by design.

PASS 13 — H13 Candidate Pipeline
  Status:    ✅ COMPLETE — 2026-03-30
  Trigger:   h13-candidate-pipeline built and sealed ✅ · audit clean 104/104 ✅
  Items:     0 items identified · 0 resolved · 0 deferred
  Scan:      P-07 chip spec (cg/ca/cr/cb/cv/ct/cn classes per status) ✅
             P-31 html{zoom:1.1} line 10 ✅
             P-32 board-wrap overflow-x:auto + padding-bottom:12vh ✅
                  col display:flex flex-direction:column + col-body overflow-y:auto flex:1 ✅
                  sp-body overflow-y:auto min-height:0 (slide panel) ✅
             class="sb-ico on" on correct nav icon ✅ · no sb-ico href/onclick ✅
             No inline chip overrides ✅
             P-27 transition:120ms on cards (transform/box-shadow/border-color) ✅
             P-12 AI match bar: teal colour token · confidence score · never red ✅
  Pre-known: BG-033 stat strip (Avg Time-to-Hire · Offer Accept Rate · Interviews This Week)
             mocked client-side — no summary endpoint.
             BG-034 "Final Round" kanban column is UI-only; no backend stage equivalent.
             Chrome items (stat mocks, Final Round column) documented in contract.
```
