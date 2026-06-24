# Meridian HCM — Design Pattern Register
## Version: 1.6 | Date: 2026-03-29
## Source: design-language.html · seed pages p1–p13
## Rule: Every visual decision traces to a pattern here. New patterns added before building.

---

## FOUNDATIONS

### P-01 · Chrome — Icon Sidebar
**Source:** All seed pages
```
Width:          54px (collapsed) · 216px (expanded)
Background:     white (#FFFFFF)
Border:         1px right #E4E7EC
Logo mark:      34×34px · border-radius 9px · teal background
Nav icons:      36×36px · border-radius 8px
Active state:   background #EDFAF8 · color teal #0A8F84
Hover state:    background #F5F7FA · color #374151
Avatar:         32×32px · bottom of sidebar · teal gradient
```

### P-02 · Chrome — Topbar
**Source:** All seed pages
```
Height:         52px
Background:     white (#FFFFFF)
Border:         1px bottom #E4E7EC
Left:           breadcrumb (font-size 13px · color #64748B)
Right:          action buttons · avatar (30px teal gradient)
Breadcrumb sep: › colour #E4E7EC
Current crumb:  color #0F1623 · font-weight 600
```

### P-03 · Chrome — Page Background
**Source:** All seed pages
```
Canvas:         #F5F7FA
Cards/panels:   #FFFFFF with border 1px #E4E7EC
Inner surfaces: #F1F4F8 (table headers, input backgrounds)
```

### P-31 · Global Zoom
**Source:** Product requirement — all surfaces
```
Rule:     html { zoom: 1.1 }
Applies:  Every HTML page in the HRMS suite without exception
Position: Immediately after the CSS reset (*,*::before,*::after) and before html,body {}
Rationale: Default render size is 110% — all layouts are designed and tested at this level
```

### P-32 · Scroll Container — Flex min-height + Zoom Clipping Fix
**Source:** Discovered 2026-03-23 — H03 scroll bug · Generalised to H01/H02 2026-03-23
```
Two compounding problems:

PROBLEM 1 — flex min-height:auto
  Without min-height:0 a flex child's implicit minimum size equals its content
  height — overflow-y:auto never activates. Parent overflow:hidden silently clips
  the bottom instead of showing a scrollbar.

PROBLEM 2 — html{zoom:1.1} scroll gap
  With zoom:1.1 the scroll container's CSS clientHeight is ~10vh larger than the
  physical viewport. Max scroll position is reached before the last ~10% of content
  is physically visible. Fix: padding-bottom:12vh on the scroll content element.

H03 / detail pages (sticky header + tab content):
  .page        { flex:1; overflow-y:auto; min-height:0 }
  .prof-head   { position:sticky; top:0; z-index:10 }
  .tab-scroll  { display:block; padding-bottom:12vh }        ← plain wrapper, not scroll container
  .tab-panels  { display:block }                             ← only if intermediate flex layer present
  .tab-panel.on{ display:block }                             ← only if intermediate flex layer present
  JS (tab switch): document.querySelector('.page').scrollTop = 0

H01 / dashboard pages (direct padding on page):
  .page        { flex:1; overflow-y:auto; min-height:0; padding:24px 24px 12vh }

H02 / list pages (table wrapper is the scroll container):
  .table-wrap  { flex:1; overflow-y:auto; min-height:0; padding-bottom:12vh }

H04 / form pages (side-by-side rail + main):
  .form-main   { overflow-y:auto; min-height:0 }
  .form-rail   { overflow-y:auto; min-height:0 }
  (zoom gap handled by natural whitespace below last field — no extra padding needed)

H05 / workflow split pages (list-col + detail-col):
  .list-col    { overflow-y:auto; min-height:0; padding-bottom:12vh }
  .detail-col  { display:flex; flex-direction:column; overflow:hidden; min-height:0 }
  .dp-sects    { flex:1; overflow-y:auto; min-height:0; padding-bottom:12vh }
  .dp-actions  { flex-shrink:0 }          ← always visible; detail-col clips, not dp-actions
  Note: detail-col uses overflow:hidden (not auto) so the action bar at the bottom
  is never scrolled away — only dp-sects scrolls.

H06 / calendar pages (cal-sidebar + cal-main + cal-grid):
  .cal-area    { flex:1; overflow:hidden; min-height:0 }
  .cal-sidebar { overflow-y:auto; min-height:0 }
  .cal-main    { flex:1; display:flex; flex-direction:column; overflow:hidden; min-height:0 }
  .cal-grid    { flex:1; overflow-y:auto; min-height:0; padding-bottom:12vh }
  Note: cal-main uses overflow:hidden so cal-grid scrolls inside it. day-hdrs is flex-shrink:0.

H06 / roster pages (attendance timeline + shift roster):
  .roster-wrap { overflow:auto; min-height:0; padding-bottom:12vh }
  Note: overflow:auto not overflow-y:auto — both axes required for horizontal scroll across
  many day-columns at zoom:1.1. First employee column uses position:sticky;left:0 to stay
  pinned while the day columns scroll horizontally.

H10 / settings pages (sidebar nav + scrollable content in a 2-col grid):
  .settings-body    { flex:1; overflow:hidden; display:grid; grid-template-columns:232px 1fr; min-height:0 }
  .settings-nav     { overflow-y:auto; min-height:0; padding:12px 10px 12vh }
  .settings-content { overflow-y:auto; min-height:0; padding:26px 30px 12vh }
  Note: both panels independently scrollable. setSection() JS swaps section visibility
  within settings-content; scrollTop not reset (sections stay at top on first load).

H11 / builder pages (3-panel grid: palette + canvas-wrap + props):
  .builder     { flex:1; overflow:hidden; display:grid; grid-template-columns:248px 1fr 272px; min-height:0 }
  .palette     { display:flex; flex-direction:column; overflow:hidden; min-height:0 }
  .pal-body    { flex:1; overflow-y:auto; min-height:0; padding:10px 10px 12vh }
  .canvas-wrap { display:flex; flex-direction:column; overflow:hidden; min-height:0 }
  .canvas-area { flex:1; overflow:auto; min-height:0; padding:24px 24px 12vh }
  .props       { display:flex; flex-direction:column; overflow:hidden; min-height:0 }
  .props-body  { flex:1; overflow-y:auto; min-height:0; padding-bottom:12vh }
  Note: canvas-area uses overflow:auto (both axes) for zoom-level pan. All three panels
  require min-height:0 + 12vh. canvas-area and props-body were missing 12vh at first build
  of Workflow Builder — caught in Pass 11 and fixed. Apply all three from build time on
  future builder pages (Report Builder · any new H11 variant).

H07 / analytics pages (tab-nav layout — report-nav + filter-bar + scrollable content):
  .page    { flex:1; overflow-y:auto; min-height:0 }
  .content { padding:22px 22px 12vh }
  Note: .page is the scroll container. .content carries the 12vh zoom-gap padding. Tab switch
  JS resets document.querySelector('.page').scrollTop = 0 on each tab change.

Applied:
  H07 HR Analytics                — 2026-03-28 (build time · page/content pattern)
  H07 Payroll Reports             — 2026-03-28 (build time · page/content pattern)
  H07 Attendance Summary          — 2026-03-28 (build time · page/content pattern)
  H07 Engagement Results          — 2026-03-28 (build time · page/content pattern)
  H07 Compliance Reports          — 2026-03-29 (build time · page/content pattern)
  H08 Global Search               — 2026-03-29 (build time · search-body grid · facets + results-area both min-height:0 + padding-bottom:12vh)
  H09 Notifications Inbox         — 2026-03-29 (build time · inbox-body 3-col grid · nav-items + msg-list + detail-body all min-height:0 + padding-bottom:12vh)
  H10 Organisation Settings       — 2026-03-29 (build time · settings-body grid · settings-nav + settings-content both overflow-y:auto min-height:0 + padding-bottom:12vh ×2)
  H11 Workflow Builder            — 2026-03-29 (stab pass · canvas-area + props-body padding-bottom:12vh missing at build; fixed in Pass 11 · see H11 pattern below)
  H11 Survey Builder              — 2026-03-29 (build time · same 3-panel pattern; all 12vh applied correctly from outset)
  H06 leave calendar              — 2026-03-24 (build time · cal-area/cal-main/cal-grid pattern)
  H06 attendance timeline         — 2026-03-24 (build time · roster-wrap pattern)
  H06 shift roster                — 2026-03-24 (build time · roster-wrap pattern)
  H05 approval inbox              — 2026-03-23 (build time · list-col/detail-col/dp-sects pattern)
  H04 form-main + form-rail       — 2026-03-23 (build time)
  H03 all 8 detail pages          — 2026-03-23 (regression fix)
  H01 all 4 dashboard pages       — 2026-03-23 (regression fix)
  H02 all 11 list pages           — 2026-03-23 (regression fix)
```

---

## TYPOGRAPHY

### P-04 · Type Scale
**Source:** design-language.html
```
Page title:     17–20px · font-weight 700 · letter-spacing -0.02em · color #0F1623
Section title:  15px · font-weight 600 · color #374151
Body:           13–14px · font-weight 400 · color #374151
Meta/label:     12px · font-weight 500 · color #64748B
Caption:        11px · font-weight 500 · color #94A3B8
Chip label:     11px · font-weight 600 · uppercase · letter-spacing 0.04em
Table header:   11px · font-weight 600 · uppercase · letter-spacing 0.06em · color #94A3B8
```

### P-05 · Monospace Numbers
**Source:** design-language.html
```
Font:      JetBrains Mono
Use for:   KPI numbers · salary figures · employee IDs · codes · dates in tables
Size:      Inherits from context
Weight:    500 or 600
```

---

## COLOUR

### P-06 · Semantic Colour Tokens
**Source:** design-language.html
```
--teal:   #0A8F84  Primary action · active nav · AI informational
--grn:    #15803D  Success · Active · Approved · Paid
--amber:  #B45309  Warning · Pending · Draft · Late
--red:    #B91C1C  Error · Terminated · Rejected · Urgent (NEVER for AI)
--blue:   #1D4ED8  Info · OnLeave · Processing · Interviewing
--violet: #5B21B6  Special states · Highlights
--t1:     #0F1623  Primary text
--t2:     #374151  Secondary text
--t3:     #64748B  Tertiary text / labels
--t4:     #94A3B8  Placeholder / disabled
--bd:     #E4E7EC  Standard border
--bd2:    #CBD5E1  Stronger border / divider
```

### P-07 · Chip Colours
**Source:** design-language.html · p2-list.html
```
Active/Approved/Paid/Present:   bg #DCFCE7 · text #15803D · border implicit
Pending/Draft/Warning/Late:     bg #FEF3C7 · text #B45309
Rejected/Terminated/Failed:     bg #FEE2E2 · text #B91C1C
OnLeave/Processing/Interviewing:bg #DBEAFE · text #1D4ED8
Teal/Reimbursed:                bg #EDFAF8 · text #0A8F84
Inactive/Archived/Cancelled:    bg #F1F4F8 · text #64748B

Chip anatomy:
  padding: 2px 8px
  border-radius: 99px
  font-size: 11px · font-weight 600 · uppercase · letter-spacing 0.04em
```

---

## COMPONENTS

### P-08 · Buttons
**Source:** design-language.html · all seed pages
```
Primary:   bg teal #0A8F84 · text white · hover #0C9E92
           padding 6px 13px · border-radius 8px · font-weight 600
Secondary: bg white · border 1px #E4E7EC · text #374151 · hover bg #F5F7FA
Danger:    bg #FEE2E2 · text #B91C1C · border implicit
Ghost:     bg transparent · no border · text #374151
Small:     padding 4px 10px · font-size 12px

Rule: ONE primary button per toolbar. Never primary for destructive actions.
Rule: Lead with verb — "Add Employee" not "Employee Add"
```

### P-09 · Form Fields
**Source:** p4-form.html · design-language.html
```
Input:       padding 8px 11px · border 1px #E4E7EC · border-radius 8px · font-size 13px
             focus: border-color teal · transition 140ms
Label:       font-size 12px · font-weight 500 · color #64748B · margin-bottom 4px
             Always ABOVE field. Never inside (placeholder ≠ label).
Required:    default — mark optional with "(optional)" not required with "*"
Validate:    on blur, not on keystroke
Error state: border-color red · error text below field · font-size 12px · color red
```

### P-10 · Cards
**Source:** design-language.html · p1-dashboard.html
```
Standard card:
  background: white · border: 1px #E4E7EC · border-radius 11px
  Card head:  title + optional subtitle + right-aligned link/action
  Card body:  padding 16px 18px on all sides
  
KPI card:
  Same as standard · monospace number (22px · font-weight 600)
  Label: 10px · uppercase · letter-spacing 0.08em · color #94A3B8
  Trend badge below number
  Warning state: bg #FEF3C7 · border #FCD34D
  
Hover: translateY(-1px) + box-shadow · 140ms ease
```

### P-11 · Tables
**Source:** p2-list.html · design-language.html
```
Row height:     40px (single-line, no wrapping)
Header:         bg #F1F4F8 · sticky · font-size 11px · uppercase · color #94A3B8
Body row:       hover bg #F5F7FA · transition 120ms
First column:   name + ID stacked · avatar left of name
Borders:        1px #E4E7EC bottom per row · no vertical borders
Checkbox:       16×16px · left of row for bulk selection
Actions:        icon buttons right · appear on row hover
Scrollbar:      4px wide · #CBD5E1 thumb
```

### P-12 · AI Component
**Source:** design-language.html · p1-dashboard.html · p5-workflow.html
```
Bar:        teal background · confidence score + label · pulsing dot (2s infinite)
Card:       teal left border · "AI Assessment" label · reasoning text · confidence %
Rules:
  Teal = informational AI (dashboard, suggestions)
  Amber = actionable warning (attrition risk, anomaly)
  NEVER red for AI — red is reserved for system errors
  Always dismissable
  Always shows confidence score — never absolutes
  Pulsing dot = live/active · Static dot = completed
```

### P-13 · Progress Bar
**Source:** design-language.html
```
Height:         5px (inline in tables) · 8px (standalone)
Background:     #F1F4F8
Fill:           colour varies by context (teal = default · green = complete)
Border-radius:  99px
Animation:      width 0 → value · 800–900ms · cubic-bezier(.25,.8,.25,1)
                Triggered after page paint, not on load
```

---

## LAYOUT PATTERNS

### P-14 · Dashboard Layout
**Source:** p1-dashboard.html · design-language.html (layouts section)
```
Slots:    KPI row (5 cols) · Chart primary (2/3 width) · Chart secondary (1/3) · Activity feed
KPI row:  5 equal-width cards · gap 12px
Charts:   grid-template-columns: 2fr 1fr · gap 16px
Activity: right column · avatar + text + timestamp
```

### P-15 · List / Table Layout
**Source:** p2-list.html
```
Filter bar: search (left, flex-1) · select filters · date range (right)
            background white · border-bottom 1px · padding 12px 16px
Table:      full width · sticky header · horizontal scroll for overflow
Pagination: below table · left: per-page selector · right: page controls
```

### P-16 · Detail / Profile Layout
**Source:** p3-profile.html
```
Profile header: avatar (48px) + name + role + status chip + action buttons
Tab nav:        below header · underline style · active = teal underline
Tab content:    scrollable · grid layout per tab
Action rail:    right side or top-right of header
```

### P-17 · Form Layout
**Source:** p4-form.html
```
Step header:    title + subtitle + step progress strip (dots or numbered)
Form body:      max-width 680px · centred · sections with dividers
Section:        section title (13px 600) + fields in 1 or 2-column grid
Footer:         sticky · white · border-top · Back (left) + Save/Next (right)
```

### P-18 · Workflow Split Layout
**Source:** p5-workflow.html
```
Left panel:  340px · approval list · filter tabs above list
Right panel: flex-1 · detail + action bar at bottom
Action bar:  Approve (teal full-width) · Reject + Delegate (50/50 below)
Comment:     textarea above action bar · optional
```

### P-19 · Calendar Layout
**Source:** p6-calendar.html
```
Mini-cal sidebar: ~100px · compact month view · week day labels
Filter strip:     horizontal below topbar · toggle chips per category
Main grid:        7-column · month view default · day cell has date + event chips
Event chips:      colour per type · truncated label · tooltip on hover
View toggle:      Month / Week / Day (top right)
```

### P-20 · Analytics Layout
**Source:** p7-analytics.html
```
Tab nav:     Workforce · Payroll · Attendance & Leave · Recruiting · Performance · Saved
Filter bar:  Period selector · department filter · export actions (right)
Chart grid:  responsive · charts stack at smaller widths
Export bar:  Export PDF · Schedule Report · New Report (top right of topbar)
```

### P-21 · Search Layout
**Source:** p8-search.html
```
Search bar:    full-width top · highlighted query terms in results
Facet panel:   left ~220px · collapsible sections · checkbox per facet value
Result list:   flex-1 · result card = avatar + name + role + dept + skills tags + salary + actions
View toggle:   List / Grid (top right)
Result count:  below search bar · "N results"
```

### P-22 · Inbox Layout
**Source:** p9-inbox.html
```
Folder nav:    left ~200px · sections with unread counts
Message list:  centre · sender + subject + preview + timestamp
Detail panel:  right · full message + reply input + actions
Compose:       button top of folder nav
```

### P-23 · Settings Layout
**Source:** p10-settings.html
```
Settings nav:  left ~220px · grouped sections (Account · Organisation)
Content:       flex-1 · section heading + form fields or config panels
Save bar:      sticky bottom · appears when unsaved changes exist
```

### P-24 · Builder Layout
**Source:** p11-builder.html
```
Builder topbar: Undo/Redo · Version History · Preview · Test · Publish
Palette:        left 240px · searchable component list · drag to canvas
Canvas:         flex-1 · zoom controls · grid snap
Properties:     right 280px · context-sensitive to selected section
Footer:         status dot + "All changes saved" · section/field count
```

### P-25 · Support / Ticket Layout
**Source:** p12-support.html
```
Status strip:   Open · In Progress · Pending · Resolved · with urgency counts
Ticket list:    left ~360px · priority indicator + title + SLA + status
Detail panel:   right · description + attachments + comments + actions
New ticket:     button in topbar
```

### P-26 · Pipeline / Kanban Layout
**Source:** p13-pipeline.html
```
KPI strip:     Total Candidates · Open Roles · Avg Time-to-Hire · Offer Accept Rate
Board:         horizontal scroll · one column per stage
Column:        stage label + count · candidate cards below
Card:          avatar + name + role + days-in-stage + quick actions
Detail drawer: slides in from right on card click
```

---

## MOTION

### P-27 · Motion Tokens
**Source:** design-language.html
```
--dur-micro:  120ms  Button hover · tab switch · chip click
--dur-sm:     200ms  Toggle · focus border · swatch
--dur-md:     280ms  Page section entry (translateY 7px → 0 · opacity 0 → 1)
--dur-lg:     800ms  Progress bar fill · bar chart animation
Stagger:      +60ms per element (KPI cards · list rows on load)
AI pulse:     2s infinite box-shadow pulse
Hover lift:   translateY(-1px) + box-shadow · 140ms
Slide panel:  220ms ease-out (detail panels from right)
```

---

## INTERACTION

### P-28 · Confirmation Pattern
**Source:** design-language.html
```
Destructive actions always confirm.
Modal must: name the specific entity · state if irreversible
Confirm button: red (only place red appears on a button)
```

### P-29 · Empty State
**Source:** design-language.html
```
Icon:     relevant emoji or illustration
Headline: "No [entity] yet." or "No results found."
Body:     one line explaining what to do
CTA:      single primary action
```

### P-30 · Skeleton Loading
**Source:** design-language.html
```
Shimmer: linear-gradient animation · 1400ms
Shapes:  text-line · heading · avatar · table-row · chip · kpi-number
Rule:    skeleton must mirror the loaded layout exactly
         table column headers stay real — only rows skeleton
```

---

### P-33 · Fixed-Layout Wide Table
**Source:** Discovered 2026-03-28 — H07 Attendance Summary Corrections table (9-column truncation fix)
```
Problem:
  A table with many columns and verbose headers overflows its container (.twrap{overflow:hidden}),
  clipping the rightmost columns. Horizontal scroll (.twrap{overflow-x:auto}) was rejected —
  all content must remain visible in-page without scrolling.

Solution — table-layout:fixed + <colgroup> percentages:
  <div class="twrap">
    <table style="table-layout:fixed;width:100%;font-size:12px">
      <colgroup>
        <col style="width:XX%">  <!-- one per column, all widths must sum to 100% -->
        ...
      </colgroup>
      ...
    </table>
  </div>

Rules:
  table-layout:fixed  — browser honours the <colgroup> widths; cell content wraps or truncates
  width:100%          — table fills the container
  font-size:12px      — reduce from default 13px to recover horizontal space
  Headers             — shorten verbose labels: "Correction ID"→"Corr. ID" · "Requested Check-in"→"Check-in"
  Cell padding        — reduce from 10–11px to 8–9px vertical to recover space
  No min-width        — never set min-width on a fixed-layout table (defeats the fix)

When to apply:
  Any table with 8+ columns that must fit the full viewport without a horizontal scrollbar.
  Preferred over overflow-x:auto when the design requires all columns visible at once.

Applied:
  H07 Attendance Summary — Corrections tab (9-col table) — 2026-03-28
```
