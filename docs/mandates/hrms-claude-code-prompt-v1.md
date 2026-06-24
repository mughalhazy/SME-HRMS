# HRMS — Claude Code Continuation Prompt
## Version: 2.4 | Date: 2026-03-30

---

## BEFORE YOU START

You are building the Meridian HCM UI.
48 pages built and sealed (H01–H13 complete). H01–H13 stabilisation passes complete.
ALL 13 ARCHETYPES COMPLETE — H01 through H13 built, sealed, and audited.
P-32 scroll fix applied to all 48 built pages — all clean and sealed.
Your job is execution — anchored strictly to repo + design language + seed pages.

Read `hrms-doc-catalogue-v1.md` first. Use its Quick Lookup whenever unsure which file to consult.

---

## STEP 0 — SESSION START (mandatory)

```
1. Confirm all uploaded files are readable
2. py -X utf8 hrms-audit-v1.py              → must be clean
3. py -X utf8 hrms-audit-v1.py --contracts  → note all blockers
4. Read hrms-archetype-system-v1.md  → confirm build status
5. Read hrms-ui-backend-gaps.md      → confirm gap count + last entries
6. State what you will build next · wait for confirmation
```

---

## ANCHOR FILES — upload ALL before starting

### ALWAYS (every session)
```
design-language.html
hrms-audit-v1.py
hrms-audit-manifest-v1.json
hrms-build-protocol-sop-v1.md
hrms-stabilisation-sop-v1.md
hrms-ui-backend-gaps.md
hrms-design-register-v1.md
hrms-archetype-system-v1.md
hrms-contract-structure-v1.md
hrms-api-contracts.md
hrms-doc-catalogue-v1.md
hrms-claude-code-prompt-v1.md
hrms-progress.md
```

### PER PHASE (add to always set)
```
Seed page for current archetype (e.g. p1-dashboard.html for H01)
hrms-schema-template.json (once built)
```

---

## NON-NEGOTIABLE RULES

```
1. Anchor to repo + design-language.html + seed pages ONLY
2. Run audit after EVERY single change — never batch, never skip
3. Never invent fields, services, or patterns outside those sources
4. Never drop repo-valid fields to satisfy a prompt
5. Mock data must use real enum values from hrms-api-contracts.md
6. Log new gaps BEFORE building — never after
7. Run --contracts before any contract or schema work
8. Seed pages are READ-ONLY — never modify them
```

---

## BUILD PROTOCOL (9 steps)

```
1. py -X utf8 hrms-audit-v1.py              → clean baseline
2. Read repo service files                    → models · API · routes
3. Read design-language.html                  → tokens · components · patterns
4. Read seed page for this archetype          → layout · density · visual reference
5. Read design register                       → applicable patterns
6. Log new gaps → audit → seal                → before writing a single line
7. Build
8. py -X utf8 hrms-audit-v1.py              → only expected file drifted
9. py -X utf8 hrms-audit-v1.py --sync + deliver
```

Single change = single audit. No exceptions.

---

## HIERARCHY OF AUTHORITY

```
1. Repo (service files · models · SQL)   → data shape
2. design-language.html                   → presentation
3. Seed pages (p1–p13)                   → archetype layout
4. hrms-design-register-v1.md            → solved visual problems
5. Gap register                           → what is deferred
6. Prompt / instruction                   → additive only
```

---

## DESIGN LANGUAGE (from design-language.html)

### Tokens
```
--teal:  #0A8F84   Primary · active · AI informational
--grn:   #15803D   Success · Active · Approved
--amber: #B45309   Warning · Pending · Draft
--red:   #B91C1C   Error · Rejected (NEVER for AI)
--blue:  #1D4ED8   Info · Processing
--t1:    #0F1623   Primary text
--t3:    #64748B   Labels · meta
--bd:    #E4E7EC   Standard border
--bg:    #F5F7FA   Canvas
--w:     #FFFFFF   Cards · panels
--r:     8px       Standard radius
--r2:    11px      Card radius
Font:    Inter (UI) · JetBrains Mono (numbers · codes)
```

### Chrome
```
Sidebar:  54px icon-only · white · border-right 1px #E4E7EC
Topbar:   52px · white · border-bottom 1px #E4E7EC
Canvas:   #F5F7FA scrollable below topbar
```

### Key patterns (design register)
```
P-07  Chip colours — green/amber/red/blue/teal/grey per status
P-08  Buttons — teal primary · one per toolbar · verb-first labels
P-09  Form fields — label above · validate on blur · optional not required
P-11  Tables — 40px rows · sticky header · avatar+name+ID first col
P-12  AI component — teal bar · confidence score · dismissable · never red
P-27  Motion — 120ms micro · 280ms page entry · 800ms bar fill
P-28  Confirmation — destructive always confirm · red button
P-29  Empty state — icon + headline + body + single CTA
P-30  Skeleton — shimmer · mirrors loaded layout · table headers stay real
P-31  Global zoom — html{zoom:1.1} on every page without exception
P-32  Scroll fix — min-height:0 on flex scroll containers + padding-bottom:12vh
      for zoom compensation (see design register for per-archetype patterns)
P-33  Fixed-layout wide table — table-layout:fixed + <colgroup> % widths + font-size:12px
      for 8+ column tables that must fit in-page without horizontal scroll
```

---

## CONTRACT SYSTEM

### File types
```
hrms-api-contracts.md        → enums + service map (SHARED — never duplicated)
hrms-schema-template.json    → slot contracts all 13 archetypes (BLOCKER until created)
hrms-h[N]-[page]-contract.json → data + config per page
```

### DSL rules
```
Source notation:  "{service} › {Model}.{field_path}"
Enum refs:        "ref:api-contracts#EnumName"
Column widths:    sum(width_pct) = 100 ±1
dsl_version:      "1.0" in every renderer_schema
Required fields:  id · version · last_updated · archetype_ref · seed_page_ref
```

---

## GAP REGISTER

```
File:    hrms-ui-backend-gaps.md
Current: 36 gaps — BG-001–034 · CG-001 open · UG-001 resolved · UG-002 open
         Last: BG-034 (no FinalRound stage in CANONICAL_PIPELINE_STAGES — H13 Final Round column UI-only)
Rule:    Log BEFORE building. Fix at source layer only.
Format:  Title · Urgency · Surface · Discovered · Workaround · Solution
```

---

## ARCHETYPES (13 total · ALL COMPLETE ✅)

```
H01  Dashboard           → p1-dashboard.html  · HR Manager · Employee · Payroll · Recruitment      ✅
H02  List / Table        → p2-list.html       · Employees · Depts · Roles · Leave · Payroll · Expenses... ✅
H03  Detail / Profile    → p3-profile.html    · Employee Profile · Job · Leave Detail · Review...   ✅
H04  Create / Edit Form  → p4-form.html       · Add Employee · Raise Leave · Expense Claim...       ✅
H05  Workflow / Approval → p5-workflow.html   · Approval Inbox                                      ✅
H06  Calendar / Timeline → p6-calendar.html  · Leave Calendar · Attendance · Roster                 ✅
H07  Analytics / Reports → p7-analytics.html · HR Analytics · Payroll · Engagement...               ✅
H08  Search / Discovery  → p8-search.html    · Global Search                                        ✅
H09  Inbox / Feed        → p9-inbox.html     · Notifications                                        ✅
H10  Settings            → p10-settings.html · Org Settings · Integrations                          ✅
H11  Builder             → p11-builder.html  · Workflow · Survey · Report Builders                  ✅
H12  Support / Ticket    → p12-support.html  · Helpdesk                                             ✅
H13  Candidate Pipeline  → p13-pipeline.html · Hiring Kanban                                        ✅
```

---

## IMMEDIATE NEXT TASKS

```
ALL 13 ARCHETYPES COMPLETE — H01 through H13 built, sealed, audited, stab-passed.
104/104 audit clean · 36 gaps logged · 48 pages sealed.

Next session work (if any):
1. py -X utf8 hrms-audit-v1.py              → confirm 104/104 clean
2. py -X utf8 hrms-audit-v1.py --contracts  → confirm no blockers
3. Resolve UG-002 (H12 textarea scroll under zoom:1.1)
   Fix path: JS auto-resize (scrollHeight) on textarea input event
4. Any additional pages or archetypes as directed
```

Note: Python must be invoked as `py -X utf8` on this machine (Windows, Python 3.14).

---

## SERVICE NAMES (repo-accurate)

```
TypeScript: employee-service · settings-service
Python:     auth-service · hiring_service · leave_service · payroll_service
            performance_service · attendance_service · expense_service
            travel_service · helpdesk_service · engagement_service
            workflow_service · reporting_analytics · search_service
            notification_service · integration_service
```
