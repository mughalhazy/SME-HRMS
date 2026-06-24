# Meridian HCM — Doc Catalogue
## Version: 2.1 | Date: 2026-06-11 (Test Suite Fix Pass — 49 pytest failures in backend/tests resolved: pytest.ini added, win32 skipif on tsc/mktemp tests, stale assertions corrected, real bugs fixed in reporting_analytics.py event idempotency and data_integrity.py shadow-validator perf via in-memory SQLite)
## Version: 2.0 | Date: 2026-06-10 (G49/G50/G51 fix pass — 41 events added to event_contract.py + 5 services wired; Decision Card status enum canonicalised in decision-system.md; AI confidence tiers corrected in MASTER BUILD SPEC; annotations added to 3 divergent docs)
## Single reference for all system docs — what each file is, when to use it

---

## UPLOAD PRIORITY

```
ALWAYS    → load every session
PHASE     → load when that archetype phase starts
ON-DEMAND → load only when modifying that file
```

---

## CATEGORY 1 — AUTHORITY

### `design-language.html`
Meridian HCM design system · Inter + JetBrains Mono · teal #0A8F84 · 6 principles · all tokens · all components · motion · 6 layout patterns · AI rules · voice & tone
**When:** Every session · before building anything
**Upload:** ALWAYS

### `backend/` (repo)
Full backend repo · all service files · models · APIs · SQL
**When:** Every session · read relevant service for each page
**Upload:** ALWAYS

---

## CATEGORY 2 — ENFORCEMENT

### `hrms-audit-v1.py`
Audit script · file hash integrity · mirror sync · 6 contract checks · --rebuild for path portability
**When:** Every session · run before and after every single change
**Upload:** ALWAYS

### `hrms-audit-manifest-v1.json`
Sealed file hashes · required by audit script
**When:** Every session
**Upload:** ALWAYS

### `hrms-build-protocol-sop-v1.md`
9-step build protocol · audit commands · hierarchy of authority · violation procedure
**When:** Every session
**Upload:** ALWAYS

---

## CATEGORY 3 — REGISTERS

### `hrms-ui-backend-gaps.md`
Gap register · all Backend/UI/Contract/Design gaps · format · change log
**When:** Every session · read before building · update when new gaps found
**Upload:** ALWAYS

### `hrms-design-register-v1.md`
Pattern register P-01 to P-33 · chrome · typography · colour · components · layout patterns · motion · flex scroll rule · fixed-layout wide table
**When:** Every session · reference for solved visual problems
**Upload:** ALWAYS

---

## CATEGORY 4 — SYSTEM ARCHITECTURE

### `hrms-archetype-system-v1.md`
All 13 archetypes · every page mapped · services · build status · leads-to · dependency map
**When:** Every session · confirms what to build next
**Upload:** ALWAYS

### `hrms-contract-structure-v1.md`
File hierarchy · 3 file types · 7 isolation rules · full DSL format · audit scope · phase handoff model
**When:** Every session · required before any contract or schema work
**Upload:** ALWAYS

---

## CATEGORY 5 — SOPs

### `hrms-stabilisation-sop-v1.md`
Stabilisation pass procedure · trigger · regression vs stabilisation guide · pass log
**When:** Every session (to know what NOT to fix mid-build)
**Upload:** ALWAYS

---

## CATEGORY 6 — CONTRACTS & SCHEMAS

### `hrms-api-contracts.md`
All enum display logic · chip colours · service map · never duplicated in page contracts
**When:** Before any page that uses status chips or enum display
**Upload:** ALWAYS

### `hrms-schema-template.json`
Slot contracts for all 13 archetypes · required/optional flags · density values
**Upload:** PHASE (load when writing contracts)

### `hrms-h[N]-[page]-contract.json`
Per-page data contracts · one per page
**Upload:** PHASE (relevant archetype phase)

---

## CATEGORY 7 — SEED PAGES

One per archetype · layout anchor · visual reference · NOT modified during build.
**Location:** `frontend/seeds/` folder
**Upload:** PHASE — load the seed page for the archetype currently being built

### `p1-dashboard.html` — H01 Command Center seed
**Archetype:** H01 — HR Manager Dashboard (Command Center)
**Description:** Full-width 216px sidebar (only H01 uses this width) with logo-mark teal div, nav sections (Overview/Workforce/Compensation/Talent). Topbar 52px: title, 208px search box, bell, help, Export + Add Employee buttons, avatar. AI bar: `<div class="ai-bar" id="ai-bar">` teal bg, confidence chip, Review + Dismiss buttons, ✕ close — always dismissable. KPI strip: `grid-template-columns:repeat(5,1fr)` with `.kpi.warn{background:var(--al)}`. Main grid: `.g3{grid-template-columns:1.7fr 1fr}` left-heavy. Dept bars: horizontal progress bars animated on load. Attendance donut: inline SVG circles. Action items: 2px left border by severity (red=Critical, amber=Warning, blue=Info). Recent Hires table + Recent Activity feed JS-rendered. Stagger animations: `.a1{animation:fu .28s}` / `.a2{…0.06s}` / `.a3{…0.12s}`. User: Alex Wang, HR Administrator.
**When:** Before building any H01 dashboard page. Defines full sidebar pattern and AI bar placement.
**Upload:** PHASE (H01)

### `p2-list.html` — H02 Data Directory seed
**Archetype:** H02 — Employee Directory (Data Directory)
**Description:** Slim sidebar 54px (icon-only, no labels — used by H02–H13). Stats strip: `grid-template-columns:repeat(5,1fr)` (Total 342, Active 318, On Leave 18, New This Month 14, Avg Tenure 3.2y). Toolbar: filter tab row (All/Active/On Leave/Onboarding with counts) + search + 3 selects. Bulk action bar: `.bulk-bar{display:none}` → `.bulk-bar.show{display:flex}` blue bg (#EFF6FF) appears on row select. Table 10 cols: checkbox, Employee (avatar+name+ID), Dept, Role, Joined↓, Location, Manager, Status, Salary, Actions. Row hover actions: View/Edit/Message at `opacity:0→1`. Footer pagination (1–12 of 342). JS: `Set()` for selection, `toggleAll()`, `clearSel()`, bulk count update.
**When:** Before building any H02 list/directory page. Defines slim sidebar pattern, bulk action bar, table row hover actions.
**Upload:** PHASE (H02)

### `p3-profile.html` — H03 Detail View seed
**Archetype:** H03 — Employee Profile (Detail View)
**Description:** Topbar: breadcrumb `Employees › James Okafor` + Edit Profile/Export/Message buttons. Profile header: 66px avatar gradient (#4F46E5→#7C3AED), name 20px, role, chip row (status/location/manager/join date/EMP ID). Tab nav: Overview/Compensation/Attendance/Documents/History with border-bottom underline style. Overview tab: `grid-template-columns:1fr 292px` — left: AI risk alert + personal details (2-col field grid) + onboarding progress bars; right: leave balance 2×2 grid + at-a-glance + employment timeline. AI risk: `.risk{background:var(--al)}` amber box, pulsing dot `@keyframes pulse`, 78% confidence bar, Schedule Check-in + View Full Analysis CTAs. Leave balance: Annual(18/25d)/Sick(10/10d)/Carry Over(3/5d)/Unpaid(0/—) in 2×2 grid. Employment timeline: `.tl-item` dot + connecting line. Compensation tab: single col, base salary in teal mono large. Documents tab: emoji icons + missing doc warning. JS: `switchTab()` shows/hides `.tab-panel` divs.
**When:** Before building any H03 detail/profile page. Defines tab nav pattern, AI risk component, and right-rail layout.
**Upload:** PHASE (H03)

### `p4-form.html` — H04 Form+Config seed
**Archetype:** H04 — Add Employee (5-step wizard)
**Description:** Step header: `.steps-row` with done (✓ green circle) / active (teal circle) / pending (grey) states. 5 steps: Personal Info (done) → Employment (active, default) → Compensation → Access & Roles → Review. Layout: `.form-wrap{grid-template-columns:1fr 304px}` — main form + right rail. Form sections: `.fg{grid-template-columns:1fr 1fr}` and `.fg3{grid-template-columns:1fr 1fr 1fr}`. Radio pills: `.ropt` with `.rdot2` custom radio dot. Employment type: Hybrid/On-site/Remote and FT-Permanent/FT-Fixed/PT/Contractor. Step 4 Access: 5 system rows (GitHub/AWS/Jira/Slack/HCM) each with access-level select. Step 5 Review: 2×2 summary cards + green "All required fields complete" banner. Rail: live-updating Summary, AI Suggestions (Smart Fill chips `.ais-chip`), Checklist. Footer: step N of 5, progress %, Back + Save & Exit + Next (step 5 Next turns green). JS: `goStep(n)` updates header, checklist, footer, rail.
**When:** Before building any H04 create/edit form page. Defines wizard step header, form grid patterns, and right-rail summary.
**Upload:** PHASE (H04)

### `p5-workflow.html` — H05 Approval Workflow seed
**Archetype:** H05 — Approval Workflow (two-panel inbox)
**Description:** Topbar: "Approval Workflows · 9 pending · 3 overdue · 2 SLA breached" + Filter + Approve All Eligible. Layout: `.wf-body{grid-template-columns:380px 1fr}`. Left panel: filter tabs (All 9/Leave 4/Payroll 3/Contracts 2), urgency-sorted approval cards. Card: avatar, name, type, SLA chip (overdue=red / due soon=amber / ok=green), dept chip, inline Approve/Reject/Delegate buttons. SLA text classes: `.sla-over{color:var(--red)}` / `.sla-warn{color:var(--amber)}` / `.sla-ok{color:var(--t4)}`. Right detail panel: request details table, optional policy/leave-balance box, impact assessment, AI assessment box `.ai-box{background:var(--tl)}` teal, approval history, comment textarea, full-width Approve then Reject+Delegate row. 6 mock approvals: Tom Nakamura (annual leave SLA breached), Eva Fischer (payroll anomaly AI 91%), Laila Osei (contract renewal), Marcus Hill (OT 48h), Amara Kofi (sick 2d), James Okafor (equipment). JS: `renderDetail(key)` populates right panel, `selCard()` highlights selection.
**When:** Before building any H05 approval workflow page. Defines two-panel inbox, SLA chip logic, AI assessment placement.
**Upload:** PHASE (H05)

### `p6-calendar.html` — H06 Calendar seed
**Archetype:** H06 — Leave Calendar (Calendar)
**Description:** Layout: slim sidebar + [cal-sidebar 220px + cal-main]. Topbar: "HR Calendar" + month nav (< March 2026 >) + Today + Add Event + Export. Second toolbar: view toggle (Month/Week/Day/Timeline) + filter pills (Leave/Payroll/Hiring/Reviews/Holidays toggle via `.off` class) + dept+employee selects. Cal sidebar 220px: mini calendar (7-col grid, today=teal circle, has-ev=dot indicator), legend (5 types with counts), upcoming events list. Main grid: `grid-template-columns:repeat(7,1fr)`, `grid-auto-rows:1fr`, min-height 112px per cell. Today: `.day-cell.today{background:var(--tl)}`. Events: up to 3 visible + "+N more" link, fixed-position hover tooltip. Event CSS: `.ev-leave{background:var(--gl)}` / `.ev-payroll{background:var(--al)}` / `.ev-hire{background:var(--bl)}` / `.ev-review{background:var(--vl)}` / `.ev-holiday{background:var(--t5)}`. JS: `EVENTS` keyed by day, `renderCal()`, `renderMiniCal()`, `changeMonth()`, `toggleFilter()`, tooltip show/hide.
**When:** Before building any H06 calendar page. Defines mini-cal sidebar, event type color classes, tooltip pattern.
**Upload:** PHASE (H06)

### `p7-analytics.html` — H07 Analytics+Evaluation seed
**Archetype:** H07 — HR Analytics (Analytics + Evaluation)
**Description:** Report nav tabs: Workforce/Payroll/Attendance+Leave/Recruiting/Performance/Saved Reports. Filter bar: Period/Department/Location + Reset/Apply. 4-col KPI grid (Headcount 342, Attrition 5.8%, Avg Tenure 3.2y, Time-to-Hire 34d). `.charts-row{grid-template-columns:2fr 1fr}`: grouped bar chart (3 months × 5 depts, JS-built) + workforce donut (inline SVG). `.charts-row-3{grid-template-columns:1fr 1fr 1fr}`: Attrition by dept (ibar sparklines) + Headcount Growth (SVG polyline with area fill `rgba(10,143,132,.08)`) + Hiring Funnel (horizontal bars). Dept breakdown table with inline bar: `.ibar-wrap{display:flex}` / `.ibar-track{flex:1;height:5px}` / `.ibar-fill{height:100%}`. All charts are JS-built from data arrays — no static HTML charts.
**When:** Before building any H07 analytics page. Defines chart layout patterns, inline bar component, and SVG chart approach.
**Upload:** PHASE (H07)

### `p8-search.html` — H08 Global Search seed
**Archetype:** H08 — People Search (Global Search)
**Description:** Hero search: large input (font-size:15px) + ⌘K shortcut chip + active filter chips (pill-style, fc-on/fc-off toggle). Layout: `.search-body{grid-template-columns:228px 1fr}`. Facet sidebar 228px: Dept (colored dots), Status, Location, Job Level, Salary Range (range slider $80K–$250K+), Skills. Results area: sticky results header (count + sort + list/grid toggle), result items: 42px avatar, name+role with `.hl{background:#FEF9C3}` highlight, meta, skill tags, salary+dept, hover actions. JS: `toggleChip()`, `clearAll()`, `toggleFacet()`, `updateCount()`, `doSearch()`.
**When:** Before building any H08 search page. Defines hero search, facet sidebar, highlight style, and chip toggle pattern.
**Upload:** PHASE (H08)

### `p9-inbox.html` — H09 Notifications Inbox seed
**Archetype:** H09 — Notifications Inbox (three-panel)
**Description:** Three-panel layout: `.inbox-body{grid-template-columns:200px 340px 1fr}`. Nav panel 200px: search, folder sections — All Messages(12 red), Approvals(5 amber), AI Alerts(3 red), Email(4 red), Leave Requests(4 amber), Starred(7 grey), Sent, Archive — with `.nav-badge` colored chips. Message list 340px: sticky header, 8 message rows with unread indicator (3px teal left bar via `.msg.unread`), avatar, from, time, subject, preview, chip tags. Detail panel: full thread view — message body, `.thread-item` rows with avatar, `reply-area` at bottom (Reply/Reply All/Forward tabs, textarea, action buttons). Topbar: "Inbox" + red unread count badge (12) + Compose. JS: `messages{}` keyed by sender, `selMsg()` populates detail panel, `setReplyTab()` toggles tabs.
**When:** Before building any H09 inbox/notification page. Defines three-panel layout, unread indicator, thread view, and reply area pattern.
**Upload:** PHASE (H09)

### `p10-settings.html` — H10 Org Settings seed
**Archetype:** H10 — Organisation Settings (two-panel nav)
**Description:** Layout: `.settings-body{grid-template-columns:232px 1fr}`. Settings nav 232px: Account section (Profile, Security, Notifications [3 red badge]), Organisation section (Company Details, Leave Policies, Payroll Config [! amber badge], Roles & Permissions), System section (Integrations [6 green badge], AI & Automation, Audit Log, Data & Retention). Active panel: Profile by default. Toggle switches: `.toggle{width:38px;height:21px}` / `.toggle.on{background:var(--teal)}` — click toggles `.on` class. Notification Matrix: table 8 events × 4 channels (In-app/Email/Slack/SMS) with checkboxes. Integrations: 8 cards (Slack/Google Workspace/GitHub/Jira/Stripe/Looker connected; Okta/AWS not connected). AI panel: 6 feature toggles + 3 confidence threshold selects. Danger zone (shared block): Export All Data/Reset Settings/Revoke Access. JS: `setSection(el, key)` switches panels and shows danger zone conditionally for profile/security/company/data only.
**When:** Before building any H10 settings page. Defines settings nav pattern, toggle component, notification matrix, integration card, and danger zone.
**Upload:** PHASE (H10)

### `p11-builder.html` — H11 Builder seed
**Archetype:** H11 — Workflow Builder (Builder)
**Description:** Three-panel layout: `.builder{grid-template-columns:248px 1fr 272px}`. Topbar: brand name + `tb-brand-badge` version chip + workflow name + auto-saved status dot + Undo/Redo/Version History/Preview/Test Flow/Publish. Palette 248px: search + 4 sections (Form Fields: Text Input/Text Area/Date Picker/Dropdown/Radio Group/Checkbox/File Upload/Rating; Workflow Logic: Approval/Condition/SLA Timer/AI Action; Notifications: Email/Slack/Webhook/SMS; Layout: Section/Divider/Info Box/Calc Field) — `.pal-comp{cursor:grab}` drag components. Canvas center: Form/Flow/Preview view toggle, zoom ±10% (50–200%), Grid/Fit buttons. Canvas frame: 5 sections (Leave Details / Condition routing / Notification action / SLA+Escalation / AI Pre-check) + `.drop-zone` dashed. Section control overlays: ↑↓ move, ⊕ duplicate, ✕ delete — appear on hover. Properties panel 272px: Section Settings, Accent Color (6 swatches), Field Order (drag-list), Visibility Rules, Validation. Footer: "All changes saved" + "5 sections · 7 fields · 3 conditions". JS: `selSection()`, `zoom(delta)`, `setVS()`, swatch clicks.
**When:** Before building any H11 builder page. Defines three-panel builder layout, drag palette, canvas sections, and properties panel.
**Upload:** PHASE (H11)

### `p12-support.html` — H12 Helpdesk/Support seed
**Archetype:** H12 — Helpdesk (Support & Tickets)
**Description:** Layout: `.support-body{grid-template-columns:340px 1fr}`. Stats strip 5 cols: Open(7, 3 urgent)/In Progress(4, 2 near SLA)/Pending(2)/Resolved This Week(9)/Avg Resolution Time(1.4d). Ticket list 340px: filter tabs (Open/In Progress/Resolved), search, 7 ticket cards (TKT-0142 to TKT-0148) — `.tkt.sel{border-left:2px solid var(--teal)}`. Detail panel: `.td-body{grid-template-columns:1fr 280px}` — main thread + 280px rail. Thread: `.thread-msg` conversation items, `.system-msg` AI notes (grey bg), `.internal-note{background:#FFFBEB;border:1px solid #FCD34D}` HR-admin-only yellow notes, `.system-msg` status change events. Rail: Ticket Details meta, Status/Priority inline selects, Assignee, Reporter, Related Tickets, Activity Log timeline. Reply area: Reply to Reporter/Internal Note/Forward tabs (internal note turns textarea yellow). JS: `selTkt()` from `ticketData{}`, `setTab()`, `setRTab()` (internal = yellow textarea).
**When:** Before building any H12 helpdesk/support page. Defines ticket list + detail two-panel, internal note pattern, system message style.
**Upload:** PHASE (H12)

### `p13-pipeline.html` — H13 Candidate Pipeline seed
**Archetype:** H13 — Candidate Pipeline (Kanban Board + Slide Panel)
**Description:** Kanban board: `board-wrap` scrollable flex row, 5 columns 268px each (Applied/Screening/Interview/Final Round/Offer Sent). Stage colors via `.stage-{id} .col-head{border-top:3px solid …}`. Stats strip: Total Candidates(247)/Avg TTH(34d)/Offer Accept Rate(84%)/Interviews This Week(14)/SLA at Risk(2). Sub-toolbar: role filter tabs + search + filter + sort + AI match filter + Board/List toggle. Candidate card: avatar, name+role, star toggle, AI match bar (teal ≥85% / blue2 ≥70% / amber <70%), chip row + source tag + days-in-stage badge (`.days-ok` grey / `.days-warn` amber / `.days-over` red pulse animation). Interviewer avatar stack: overlapping `-5px margin-left`. Hover actions: `.cc-acts{opacity:0→1}` — Move + Reject buttons. `.ccard.urgent{border-left:3px solid var(--red2)}` / `.ccard.sla-warn{border-left:3px solid var(--amber2)}`. Slide panel 480px: fixed right, `transform:translateX(100%)→0`, `.overlay` backdrop. Panel: large avatar + chips, AI match big score (28px mono teal, progress bar, signal list ✅⚠️❌), Application Details, Interviewer Feedback (stars + verdict chip), Timeline, action buttons. JS: `STAGES[]`, `CANDIDATES[]` (10 records), `renderBoard()`, `renderCard()`, `openPanel(id)`, `closePanel()`, `setTP()`, `setBoard()`.
**When:** Before building any H13 pipeline page. Defines kanban board layout, AI match bar, days-in-stage badge, and slide panel pattern.
**Upload:** PHASE (H13)

---

## CATEGORY 8 — HANDOFF

### `hrms-claude-code-prompt-v1.md`
Full Claude Code session prompt · anchor files · rules · build queue · service names
**When:** Start of every Claude Code session — paste as opening prompt
**Upload:** ALWAYS

---

## RECOMMENDED UPLOAD SET

### Every session (14 files)
```
design-language.html
backend/
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

### Per phase (add to always set)
```
Relevant seed page (e.g. p4-form.html for H04 phase)
hrms-schema-template.json (when writing contracts)
Relevant page contracts from current + prior phases
```

### Per-archetype sets (add to always set)
Every archetype phase: `frontend/seeds/p[N]-[name].html` + `hrms-schema-template.json` + any extra contracts below.

| Archetype | Seed page | Extra contracts |
|---|---|---|
| H04 | p4-form.html | hrms-h03-*-contract.json (all 8 — context for linked detail pages) |
| H05 | p5-workflow.html | hrms-h03-*-contract.json (H05 links to H03 for full record view) |
| H06 | p6-calendar.html | — |
| H07 | p7-analytics.html | — |
| H08 | p8-search.html | — |
| H09 | p9-inbox.html | — |
| H10 | p10-settings.html | — |
| H11 | p11-builder.html | hrms-h11-workflow-builder-contract.json + hrms-h11-survey-builder-contract.json |
| H12 | p12-support.html | — |
| H13 | p13-pipeline.html | — |

---

## CATEGORY 9 — BACKEND CANON DOCS
**Location:** `backend/docs/canon/`
Ground-truth architectural contracts for the backend repo. These define entities, services, events, APIs, and data shapes that the UI pages consume.

### `domain-model.md`
**Purpose:** Canonical entity definitions for every HRMS domain object with attributes, types, relationships, and lifecycle states.
**Description:** Covers 30+ entities across all services — Employee, Department, Role, LeaveRequest, PayrollRecord, Candidate, Interview, AttendanceRecord, Survey, UserAccount, WebhookEndpoint, and more. Each entry includes owning service, field table (name/type/required/notes), relationships, and valid status transitions. The ground truth for all field names and data shapes used in page contracts and mock data.
**When:** Before building any page — confirms exact field names, types, and enum values for that service's entities.
**Upload:** ON-DEMAND (load for the service being built)

### `service-map.md`
**Purpose:** Canonical bounded-service registry listing all 24 services with responsibilities, owned entities, APIs, dependencies, events, and read models.
**Description:** 23 services listed with status (IMPLEMENTED / ADD-ON / PLANNED). For each: responsibilities, owned entities, canonical API endpoints, upstream/downstream dependencies, published events, subscribed events, and read models produced. Authoritative reference for service boundaries and inter-service contracts. Supersedes the partial service map in `hrms-api-contracts.md` — includes compliance-service, decision-service, bank-service, whatsapp-service, ewa-financial-service, automation-service, and project-service which are absent from the UI-side service map.
**When:** Before any page that touches a service not fully described in `hrms-api-contracts.md`; when verifying endpoints or event dependencies.
**Upload:** ON-DEMAND

### `api-standards.md`
**Purpose:** Canonical Service Contract Standard (SCS) — request/response envelope format, HTTP status codes, pagination, filtering, sorting, and auth requirements all services must conform to.
**Description:** Defines: base path `/api/v1`, request envelope (`request_id`, `tenant_id`, `actor`), response envelope (`status`/`data`/`meta`/`error`), status code semantics (200/201/202/204/400/401/403/404/409/422/429/500/502/503/504), cursor pagination, filtering and sorting conventions, QC checks, and versioning rules. All mock API contracts in page contracts must conform to this envelope shape.
**When:** When writing or reviewing API contracts; when constructing mock response shapes for page contracts.
**Upload:** ON-DEMAND

### `workflow-catalog.md`
**Purpose:** Deterministic HR workflow definitions mapping each workflow to services, entities, state transitions, steps, and events.
**Description:** 26 workflows as of 2026-06-10 (extended from 9 during catalogue-authority fix pass — 17 service-referenced workflows were missing entries). Original 9: `employee_onboarding`, `attendance_tracking`, `leave_request`, `payroll_processing`, `project_resource_allocation`, `settings_administration`, `candidate_hiring`, `performance_management`, `travel_request`. Added 17: `projection_search_indexing`, `engagement_feedback_collection`, `automation_execution`, `anomaly_review`, `ewa_disbursement`, `advance_request`, `access_provisioning`, `notification_dispatch`, `salary_disbursement`, `payment_reconciliation`, `expense_reimbursement`, `report_generation`, `hr_ticket_resolution`, `whatsapp_payslip_request`, `whatsapp_leave_application`, `whatsapp_approval_action`, `whatsapp_alert_dispatch`. Each entry specifies owning/participating services, referenced entities, trigger conditions, state machine transitions, events consumed/published, and numbered workflow steps. Valid service registry expanded from 11 to 24. Authoritative for approval routing and workflow step sequencing shown in H05 pages.
**When:** Before building H05 Approval Inbox pages; when mapping workflow states to UI states.
**Upload:** ON-DEMAND

### `event-catalog.md`
**Purpose:** Registry of every canonical domain event emitted across HRMS services with aggregate, state transition, minimum payload, and consumer list.
**Description:** 117 documented events across all services (76 original + 41 added G49 fix 2026-06-10): employee lifecycle, attendance, leave, payroll, hiring, auth, notifications, travel, engagement, learning, helpdesk, workforce intelligence, cost planning, settings, project, plus compliance (8), decision (6), ewa-financial (9), bank (8), whatsapp (8), reporting (2). Each entry defines the aggregate entity, the state transition that triggers it, minimum payload fields, and downstream consumers. All events follow PastTense naming. Events are immutable; corrections emit new events.
**When:** When auditing which notifications or side effects should fire from a given UI action; when diagnosing missing downstream updates.
**Upload:** ON-DEMAND

### `data-architecture.md`
**Purpose:** Relational database schema for all HRMS tables — columns, types, nullability, indexes, and foreign key constraints.
**Description:** Full SQL-level table definitions for: departments, business_units, legal_entities, locations, cost_centers, grade_bands, job_positions, roles, employees, performance tables (review_cycles, goals, feedback, calibrations, pip_plans, pip_milestones), engagement tables (surveys, questions, responses, answers, aggregates), attendance_records, leave_requests, payroll_records, hiring tables (job_postings, candidates, interviews), access-control tables (user_accounts, role_bindings, permission_policies, sessions, refresh_tokens), notification tables (templates, messages, delivery_attempts, preferences), integration tables (event_outbox), compensation domain tables (compensation_bands, salary_revisions, benefits_plans, benefits_enrollments, allowances — added 2026-06-06), travel tables (travel_requests, travel_itinerary_segments). Includes referential graph summary with compensation and travel FK references, and implementation notes (ON UPDATE CASCADE, ON DELETE RESTRICT). attendance_records.source enum extended to 6 values (GEO_FENCE, FACE_RECOGNITION, MOBILE added MN-G04).
**When:** When verifying exact column names, types, or constraints for mock data; when checking if a field exists at the DB level vs. only in the service layer.
**Upload:** ON-DEMAND

### `read-model-catalog.md`
**Purpose:** 25 query-optimised projection definitions — fields, source services/entities, grain, and primary consumers for every read model in the system.
**Description:** Covers: employee_directory_view, organization_structure_view, attendance_dashboard_view, leave_requests_view, payroll_summary_view, job_posting_directory_view, candidate_pipeline_view, performance_review_view, engagement_survey_view, settings_configuration_view, access_control_view, notification_delivery_view, integration_delivery_view, document_library_view, global_search_view, compliance_status_view, decision_cards_view, financial_wellness_view, disbursement_status_view, analytics_dashboard_view, whatsapp_session_view, expense_claims_view, helpdesk_tickets_view, helpdesk_sla_view, automation_execution_view. Each entry lists fields, source services, and UI consumers.
**When:** When building analytics or dashboard pages that need exact field names from read models; when verifying what data is available without a direct API call.
**Upload:** ON-DEMAND

### `security-model.md`
**Purpose:** Authentication, authorization scope, capability-to-role matrix, and data-protection rules for all 6 security principals.
**Description:** Defines 6 principals: Admin, Manager, Employee, Recruiter, PayrollAdmin, Service. Capability-to-role matrix (30+ CAP-IDs × 6 roles). Module permission coverage table. Scope dimensions (Global/Department/Employee/Requisition/Service). Enforcement rules (deny-by-default, scope filters mandatory in handlers). Authentication controls (short-lived tokens, MFA, session revocation). Data protection controls (encryption at rest, TLS, field-level filtering for salary/review/security data). Audit requirements.
**When:** When implementing authorization-aware UI (disabled buttons, hidden sections based on role); when verifying which roles can perform a given action.
**Upload:** ON-DEMAND

### `capability-matrix.md`
**Purpose:** Capability registry cross-referencing CAP-IDs to service owners, primary entities, read models, and API endpoint categories.
**Description:** 31 capabilities (CAP-EMP through CAP-AUT-003) in a table with: capability name, service owner, primary entities, primary read model(s), and API endpoint category. Useful for quickly mapping a UI feature to its backing capability ID, owning service, and data sources. Complementary to `security-model.md`.
**When:** When determining which service owns a given UI capability and what read model to use.
**Upload:** ON-DEMAND

### `ui-surface-map.md`
**Purpose:** Maps all UI surfaces to read models, capability IDs, owning services, and domain entities — the bridge between frontend page names and backend data contracts.
**Description:** 22 named UI surfaces (dashboard, employee_list, employee_profile, attendance_dashboard, leave_requests, payroll_dashboard, job_postings, candidate_pipeline, performance_reviews, departments, roles, settings, compliance_dashboard, decision_center, financial_wellness, banking_disbursement, analytics_reports, whatsapp_admin, expense_claims, engagement_surveys, helpdesk, automations_admin). Each entry maps to read model(s), capability ID(s), primary service owner, and domain entities. Notes on `decision_center` as AI Payroll Guardian surface and WhatsApp as parallel access channel.
**When:** When starting work on any new UI surface — confirms the read model and capability stack before opening service docs.
**Upload:** ON-DEMAND

### `country-layer.md`
**Purpose:** Country abstraction layer specification — interfaces, adapter pattern, resolver, and step-by-step data flow for plugging in country-specific payroll/compliance logic.
**Description:** Defines 3 interfaces: `TaxEngineInterface.calculate_tax()`, `ComplianceEngineInterface.validate_payroll()` / `generate_reports()`, `PayrollRulesInterface.apply_rules()`. Adapter pattern (one adapter per country). Resolver (org → country → adapter). 12-step data flow from payroll run request to persisted output. Pakistan example flow. QC test scenarios (interface conformance, resolver, determinism, validation gate, end-to-end). Rule: no `if country ==` in any service — all country logic isolated in adapters.
**When:** When building compliance or payroll pages that mention country-specific logic; when trying to understand how Pakistan-specific tax rules are applied.
**Upload:** ON-DEMAND

### `decision-system.md`
**Purpose:** AI Payroll Guardian specification — 4 anomaly types, dual scoring model, Decision Card schema, and lifecycle.
**Description:** 4 anomaly types: salary_spike, overtime_anomaly, missing_deductions, ghost_employee. Dual scoring: risk score (0–100) + confidence (%); 3 risk bands (Low/Medium/High). "Why flagged" format (machine + human readable). Decision Card schema (trigger/impact/confidence/recommended_action/reversibility/expires_at). 3-state lifecycle (Create → Update → Expire). 5 test scenarios. Human-in-loop gate: High-risk cards block payroll approval. Rule: AI output never uses red colour — teal only for AI surfaces.
**When:** When building H01 dashboard AI bars, H07 analytics anomaly sections, or any Decision Card UI surface; aligns P-12 AI component rules to backend data.
**Upload:** ON-DEMAND

### `release-scope.md`
**Purpose:** Definitive list of which services are in Core release, Add-On, or Planned — with ports and country adapter status.
**Description:** Core (13 services, all with ports): employee-service (8001), attendance-service (8002), leave-service (8003), payroll-service (8004), hiring-service (8005), auth-service (8006), notification-service (8007), compliance-service (8021), decision-service (8022), bank-service (8023), whatsapp-service (8024), reporting-analytics-service (8013), automation-service (8017). Add-On (8 services): helpdesk, expense, ewa-financial, performance, engagement, integration, settings, search. Planned (2): travel-service, project-service. Country adapters: Pakistan (PK) implemented; UAE (AE) planned; Dummy (XX) for testing.
**When:** When determining whether a service's features should be chrome-only (Add-On/Planned) vs. wired to real endpoints (Core).
**Upload:** ON-DEMAND

### `read-models.md`
**Purpose:** Pointer-only stub — redirects to `read-model-catalog.md` as the canonical source.
**Description:** 3-line file. States that all read model contracts are in `docs/canon/read-model-catalog.md`. Search/indexing extensions (document_library_view, global_search_view) merged into that catalog. No standalone content.
**When:** Do not load — use `read-model-catalog.md` directly.
**Upload:** N/A (pointer only)

---

## CATEGORY 10 — BACKEND SERVICE DOCS
**Location:** `backend/docs/services/`
Per-service implementation documentation: scope, full HTTP surface, authorization capabilities, owned entities, domain rules, events, and read models. Richer than the service-map entries — includes domain rules, lifecycle states, and implementation notes.

### `employee-service.md`
**Purpose:** Full spec for employee-service — the authoritative workforce master data and org structure service.
**Description:** Scope (employee lifecycle + org reference data), HTTP surface (13 endpoints: employees, departments, roles, org entities), authorization capabilities (CAP-EMP-001/002), owned entities (Employee + 8 org entities), supported workflows, all published/subscribed events, read models (employee_directory_view, organization_structure_view). Notes on dynamic schema support and multi-entity hierarchy.
**When:** Before building H02 Employees/Departments/Roles, H03 Employee Profile/Department Detail/Role Detail, H04 Add/Edit Employee.
**Upload:** ON-DEMAND

### `leave-service.md`
**Purpose:** Full spec for leave-service — leave lifecycle, policy validation, and payroll linkage.
**Description:** Scope, HTTP surface (10 endpoints including `GET /api/v1/leave/balances/{employee_id}` and `GET /api/v1/leave/calendar?department_id=&month=` — NOTE: these 2 endpoints are NOT in hrms-api-contracts.md), leave types (Annual/Sick/Unpaid/Casual/Maternity/Custom), domain rules (workflow routing, overlap validation, policy constraints, payroll injection). Authorization, events, read models.
**When:** Before building H02 Leave Requests, H03 Leave Request Detail, H04 Raise Leave Request, H06 Leave Calendar. Reveals extra endpoints (balances, calendar) missing from UI contracts.
**Upload:** ON-DEMAND

### `payroll-service.md`
**Purpose:** Full spec for payroll-service — zero-error payroll calculation, country abstraction rule, and compliance gate requirement.
**Description:** Scope (DRAFT→PROCESSED→PAID→CANCELLED lifecycle), HTTP surface (8 endpoints), calculation inputs (base salary, allowances, deductions, attendance, leave, country rules, tax), country abstraction rule diagram (PayrollService → CountryResolver → CountryAdapter → apply_rules() → calculate_tax()), compliance gate (blocks finalization if compliance not validated), authorization, events, read models.
**When:** Before building H02 Payroll Records, H03 Payroll Record Detail, H07 Payroll Reports. Clarifies that PayrollService never computes tax directly — country adapter does.
**Upload:** ON-DEMAND

### `hiring-service.md`
**Purpose:** Full spec for hiring-service — job posting lifecycle, candidate pipeline, interview management, and hire handoff.
**Description:** Scope, HTTP surface (17 endpoints including `GET /api/v1/hiring/candidate-pipeline?pipeline_stage=` not in hrms-api-contracts), domain rules (stage transitions, Google Calendar sync metadata, LinkedIn import, hire-only-from-Offered rule), events (12 events including CandidateStageTransitionRecorded not in event-catalog), implementation note (in-memory reference implementation).
**When:** Before building H02 Job Postings, H03 Job Posting Detail, H04 Create Job Posting, H13 Candidate Pipeline. Reveals extra pipeline endpoint.
**Upload:** ON-DEMAND

### `auth-service.md`
**Purpose:** Full spec for auth-service — identity, sessions, role bindings, token lifecycle, and RBAC enforcement.
**Description:** Scope, HTTP surface (16 endpoints: login/refresh/logout/me, user management, session revocation, role bindings, policies, access query), 6 security principals with descriptions, authorization capabilities (CAP-AUT-001), owned entities (UserAccount/RoleBinding/PermissionPolicy/Session/RefreshToken), workflows, events (7 published), subscribed events, read models.
**When:** Before building H10 Organisation Settings (Roles & Permissions section); when adding user provisioning to H04 Add Employee (Step 5 — Access & Roles, BG-007).
**Upload:** ON-DEMAND

### `workflow-service.md`
**Purpose:** Centralized workflow orchestration service — inline approval paths wired into leave, payroll, and hiring services.
**Description:** Documents 3 inline approval integrations: leave-service.submit_request → leave_request_approval workflow, payroll-service.mark_paid → payroll_disbursement_approval workflow, hiring-service.mark_candidate_hired → candidate_hiring_approval workflow. API surface (6 endpoints: get instance, get inbox, approve, reject, delegate, escalate). Integration rules (domain services initiate but don't own approval state; transitions emit events + audit + notifications; tenant matching enforced).
**When:** Before building H05 Approval Inbox; when understanding how approval state flows from H03 detail pages back to the workflow engine.
**Upload:** ON-DEMAND

### `performance-service.md`
**Purpose:** Full spec for performance-service — review cycles, OKRs/goals, 360 feedback, calibration sessions, and PIP management.
**Description:** Scope, HTTP surface (20 endpoints across review-cycles/goals/feedback/calibrations/pips), authorization capabilities (CAP-PRF-001), owned entities (ReviewCycle/Goal/Feedback/CalibrationSession/PipPlan), all published events (15 events), subscribed events, read models (performance_review_view, employee_profile_view). Notes on workflow-service integration for all approval routing.
**When:** Before building H03 Performance Review Detail, H07 HR Analytics (Performance tab stub BG-019).
**Upload:** ON-DEMAND

### `attendance-service.md`
**Purpose:** Full spec for attendance-service — multi-source capture, shift management, overtime engine, and period closure.
**Description:** Scope, HTTP surface (10 endpoints including exceptions endpoints not in hrms-api-contracts), capture sources (biometric/GPS/face recognition/manual), advanced features (grace period, late penalty ladder, missing punch resolution, multi-shift templates, overtime engine), authorization capabilities (CAP-ATT-001/002), owned entities (AttendanceRecord/AttendancePeriod/AttendanceException/ShiftTemplate), events, read models. Notes on biometric adapter integration.
**When:** Before building H02 Attendance Records, H06 Attendance Timeline/Shift Roster. Reveals exceptions endpoints and ShiftTemplate entity not in hrms-api-contracts.
**Upload:** ON-DEMAND

### `notification-service.md`
**Purpose:** Full spec for notification-service — 4 channels, template management, delivery tracking, and subject preferences.
**Description:** Scope, HTTP surface (9 endpoints), channels (Email/SMS/Push/WhatsApp via whatsapp-service outbound), authorization capabilities (CAP-NOT-001/002), owned entities, events (4 published including AnomalyDetected subscription from decision-service and ComplianceSubmissionFailed subscription — neither in current hrms-archetype-system), read models (notification_delivery_view). Notes on channel routing via preference rules.
**When:** Before building H09 Notifications Inbox; when auditing which notification events map to which inbox topics.
**Upload:** ON-DEMAND

### `engagement-service.md`
**Purpose:** Full spec for engagement-service — surveys, pulse campaigns, D1-D5 dimension scoring, and response aggregation.
**Description:** Scope, HTTP surface (8 endpoints), authorization (Admin full / Manager dept-level aggregates / Employee submit-only), owned entities, workflows (engagement_feedback_collection), events (5 published), subscribed events, read models (engagement_survey_view). Notes on anonymity and department scoping.
**When:** Before building H07 Engagement Results, H11 Survey Builder.
**Upload:** ON-DEMAND

### `expense-service.md`
**Purpose:** Full spec for expense-service — reimbursement claims, receipts, policy limits, and accounting export. Distinct from ewa-financial-service.
**Description:** Scope (accounting-facing reimbursements, NOT payroll-linked), HTTP surface (11 endpoints), lifecycle (DRAFT→SUBMITTED→APPROVED→REIMBURSED + REJECTED), domain rules (receipt required before submission, category limits, accounting export not payroll injection), authorization capabilities (CAP-EXP-001/002/003 — 3 capabilities vs 1 in capability-matrix), owned entities, events (4 published), read models (expense_claims_view).
**When:** Before building H02 Expense Claims, H03 Expense Claim Detail, H04 Raise Expense Claim, H05 Approval Inbox (expense cards).
**Upload:** ON-DEMAND

### `settings-service.md`
**Purpose:** Full spec for settings-service — attendance rules, leave policies, and payroll settings with domain validation rules.
**Description:** Scope, owned entities (AttendanceRule/LeavePolicy/PayrollSettings), canonical APIs (6 endpoints), domain rules (unique codes, one active policy per leave_type, carry-forward ≤ entitlement, approval-stage requirements), authorization, events (4 published), read models (settings_configuration_view).
**When:** Before building H10 Organisation Settings; when checking settings validation rules.
**Upload:** ON-DEMAND

### `reporting-analytics-service.md`
**Purpose:** Full spec for reporting-analytics-service — 4 report tiers (operational/compliance/predictive/anomaly) with 9 endpoints.
**Description:** Scope (read-only consumer of all domain read models; feeds decision-service), HTTP surface (9 endpoints: reports, headcount, payroll-summary, attendance-trends, compliance-status, turnover, anomalies, schedule), 4 report tiers with content details (operational: headcount/attendance/leave/payroll; compliance: FBR/EOBI/PESSI; predictive: attrition/cost/overtime/leave-liability; anomaly: salary/overtime/deductions/ghost), authorization (CAP-RPT-001/002/003 — 3 capabilities vs 2 in capability-matrix), owned entities, events, read models.
**When:** Before building H07 Analytics pages; clarifies which report tier feeds which tab.
**Upload:** ON-DEMAND

### `helpdesk-service.md`
**Purpose:** Full spec for helpdesk-service — HR ticket management, SLA tracking, knowledge base, and ticket routing.
**Description:** Scope (HR query management; does NOT mutate payroll/compliance/attendance data), HTTP surface (13 endpoints including knowledge base and SLA report endpoints not in capability-matrix), ticket lifecycle (OPEN→ASSIGNED→IN_PROGRESS→RESOLVED→CLOSED + PENDING_EMPLOYEE + REOPENED branches), 7 ticket categories, domain rules (SLA timer pauses on PENDING_EMPLOYEE, resolution note required, configurable reopen window), authorization capabilities (CAP-HLP-001 to 004 — 4 capabilities vs 2 in capability-matrix), owned entities (HelpDeskTicket/TicketComment/TicketCategory/KnowledgeBaseArticle), events (7 published including SLABreached), read models.
**When:** Before building H12 Helpdesk. Reveals richer ticket lifecycle and knowledge base functionality.
**Upload:** ON-DEMAND

### `bank-service.md`
**Purpose:** Full spec for bank-service — salary disbursement file generation, Raast payout, payment tracking, and reconciliation.
**Description:** Scope (integration/access layer bridge between payroll/EWA and banking channels), HTTP surface (11 endpoints), disbursement lifecycle (PENDING→GENERATED→SUBMITTED→CONFIRMED→RECONCILED + FAILED→RETRY), domain rules (disbursement only after PayrollPaid event, CNIC match for Raast, reconciliation exceptions, audit on account changes), authorization (CAP-BNK-001/002/003 — 3 capabilities), owned entities (DisbursementBatch/PaymentRecord/ReconciliationReport/EmployeeBankAccount), events, read models.
**When:** When auditing payroll disbursement gaps (BG-related) or building banking admin surfaces not currently in the UI.
**Upload:** ON-DEMAND

### `compliance-service.md`
**Purpose:** Full spec for compliance-service — Pakistan statutory lifecycle (FBR/EOBI/PESSI), country-agnostic validation gate, and audit trail.
**Description:** Scope (DRAFT→VALIDATED→SUBMITTED→ACK→FAILED→RETRY lifecycle), HTTP surface (9 endpoints), submission lifecycle states with definitions, domain rules (validation MUST run before payroll finalization, report generation only after VALIDATED state, all transitions immutable, scoped to org+legal_entity+period+type), authorization (CAP-COM-001/002/003 — 3 capabilities), owned entities, events (8 published including ComplianceRetryQueued), read models (compliance_status_view).
**When:** When auditing compliance-related gaps or understanding the payroll compliance gate (BG related); not currently in the Meridian UI but back-end is fully implemented.
**Upload:** ON-DEMAND

### `decision-service.md`
**Purpose:** Full spec for decision-service — AI guardian, 4 anomaly types, Decision Card lifecycle, and human-in-loop gate enforcement.
**Description:** Scope (cross-domain intelligence; NOT a sub-module of payroll), HTTP surface (7 endpoints), full Decision Card schema (15 fields), 4 anomaly types with detection logic, 3 risk routing tiers, human-in-loop gates (High-risk cards block payroll; override requires reason), authorization (CAP-DEC-001/002), owned entities (DecisionCard/AnomalyRecord/DecisionAuditEntry), events (6 published), read models (decision_cards_view + enriches manager_dashboard_view).
**When:** When building AI bar components in dashboards; when auditing how the P-12 AI component maps to backend Decision Card data.
**Upload:** ON-DEMAND

### `automation-service.md`
**Purpose:** Full spec for automation-service — event/schedule/threshold-triggered rule engine with cross-service action dispatch.
**Description:** Scope (infrastructure layer, NOT business domain), HTTP surface (10 endpoints), full automation rule schema (trigger types/conditions/actions in YAML), 3 trigger types (event-triggered/schedule-triggered/threshold-triggered) with use cases, authorization (CAP-AUT-002/003), owned entities (AutomationRule/AutomationExecution/AutomationExecutionLog), events (4 published), read models (automation_execution_view). Sub-module SupervisorEngine documented here.
**When:** When understanding background automation architecture; when auditing how scheduled payroll runs or SLA breach escalations are triggered.
**Upload:** ON-DEMAND

### `ewa-financial-service.md`
**Purpose:** Full spec for ewa-financial-service — earned wage access and salary advances with payroll deduction injection.
**Description:** Scope (payroll-linked financial services; distinct from expense-service accounting claims), HTTP surface (8 endpoints), domain rules (EWA cap % of accrued wages, one advance per employee, threshold-based approval, bank-service routing for Raast/transfer, full audit trail), authorization (CAP-EWA-001/002/003 — 3 capabilities), owned entities (EWARequest/SalaryAdvance/RepaymentSchedule/PayrollDeduction), events (8 published), read models (financial_wellness_view).
**When:** When auditing financial wellness features not in the current UI build; provides clarity on EWA vs. expense boundary.
**Upload:** ON-DEMAND

### `whatsapp-service.md`
**Purpose:** Full spec for whatsapp-service — first-class WhatsApp HRMS interface with identity mapping, session management, and 4 workflow capabilities.
**Description:** Scope (standalone integration/access layer; not a notification bolt-on), HTTP surface (8 endpoints), 4 capabilities (payslip/leave/approvals/alerts), identity + security model (one phone per employee, OTP verification, expiring payslip links, RBAC via session role context), interaction model (free-text/shortcuts/buttons/multi-step), authorization (CAP-WA-001/002/003), owned entities (WhatsAppIdentityMap/WhatsAppSession/WhatsAppConversationEvent), events, read models.
**When:** When building WhatsApp admin surfaces; when auditing notification_service integration with WhatsApp channel.
**Upload:** ON-DEMAND

### `project-service.md`
**Purpose:** Full spec for project-service (IMPLEMENTED — was marked PLANNED, corrected per S8-G04) — project staffing, allocation governance, and allocation ledger.
**Description:** Scope (staffing assignments without duplicating payroll; allocation ledger for audit/reporting; optional workflow-service routing for approvals), HTTP surface (10 endpoints), domain rules (100% allocation cap per employee across active assignments, append-only ledger, tenant-scoped optional approvals), events (7 published). NOTE: project_service.py + project_api.py ARE implemented — MASTER BUILD SPEC §10 was corrected in S8-G04 to mark both travel-service and project-service as IMPLEMENTED.
**When:** When checking whether project-service is available for G28 UI pages (G28j projects/page.tsx — backend is ready).
**Upload:** ON-DEMAND

### `travel-service.md`
**Purpose:** Full spec for travel-service (IMPLEMENTED — was marked PLANNED, corrected per S8-G04) — employee travel request lifecycle from draft through approval, booking, and completion.
**Description:** Scope (add-on; reuses employee-service snapshots; approval via workflow-service; full audit + event emission at every transition). Lifecycle: Draft → Submitted → Approved/Rejected → Booked → Completed, with Cancelled possible from any non-terminal state. HTTP surface (9 endpoints). Owned entities: TravelRequest (purpose/trip_type/origin+destination/dates/estimated_cost/currency/status/workflow_id/itinerary_segments), TravelItinerarySegment, EmployeeSnapshot cache. Events published: 7 (Created/Submitted/Approved/Rejected/ItineraryUpdated/Cancelled/Completed). Events subscribed: EmployeeCreated/Updated/StatusChanged. Read model: travel_requests_view. Dependencies: employee-service/workflow-service/audit-service/notification-service/outbox-system.
**When:** When building the travel UI page; when tracing travel approval workflows through workflow-service.
**Upload:** ON-DEMAND

### `integration-service.md`
**Purpose:** Full spec for integration-service — centralized outbound webhook dispatch with payload signing, per-attempt delivery tracking, and failure replay.
**Description:** Scope (add-on; domain services free of partner logic; webhook-only — OAuth connect flows are BG-026 chrome). HTTP surface (6 endpoints: POST/PATCH/DELETE webhooks, GET list, GET delivery attempts, POST replay). Owned entities: WebhookEndpoint (target_url/subscribed_events/status/HMAC-sealed secret/signature config/retry backoff/delivery counters), WebhookDelivery (attempt_count/last_http_status/dead_lettered_at), WebhookDeliveryAttempt (full request+response log incl. duration_ms). _SecretSealer: XOR stream cipher + HMAC-SHA256 MAC over HRMS_WEBHOOK_MASTER_KEY. Fan-out flow: consume_event → match subscriptions → create WebhookDelivery → background job → dispatch + sign → retry → dead-letter. Read model: integration_delivery_view. Dependencies: audit-service/background-jobs/outbox-system/event_contract/resilience.
**When:** When building the integrations settings UI; when debugging failed webhook deliveries; when auditing outbound event fan-out.
**Upload:** ON-DEMAND

### `search-service.md`
**Purpose:** Full spec for search-service — projection-backed cross-domain search over employees, candidates, documents, and payroll without touching transactional stores.
**Description:** Scope (add-on; event-driven reindex via background-jobs; tenant-safe via assert_tenant_access). HTTP surface (4 endpoints: universal search + employee/candidate/document shortcuts). Indexed read models: employee_directory_view / organization_structure_view / candidate_pipeline_view / document_library_view / payroll_summary_view → global_search_view. SearchDocument schema (document_id/source_view/source_key/domain/entity_type/display_name/search_blob/keywords/facets). Scoring: term-match _score_row() + sort + CachedSearchResult TTL cache. Indexing: consume_event → reindex background job → ingest_read_model → _replace_index_docs. rebuild_index() for full re-projection. Events subscribed: 16 (Employee/Department/Role/Candidate/Document/Payroll events). Read models produced: global_search_view + SearchProjectionState. health_snapshot() + get_projection_state() for ops monitoring.
**When:** When building search UI pages; when debugging missing search results after bulk imports; when checking indexing lag via projection state.
**Upload:** ON-DEMAND

### `audit-service.md`
**Purpose:** Full spec for audit-service — append-only JSONL audit trail with cursor-paginated query API, consumed by every domain service that mutates sensitive data.
**Description:** Scope (support; write-once ledger; hard requirement per MASTER BUILD SPEC §19; depended on by 10+ services). Storage: append-only JSONL file at HRMS_AUDIT_LOG_PATH (default tempdir/sme-hrms/audit-records.jsonl); thread-safe RLock; records never updated or deleted. AuditRecord schema: audit_id/tenant_id/actor{id/type/role/department_id}/action/entity/entity_id/before/after/timestamp/trace_id/source. emit_audit_record() module helper used by all domain services (auto-injects source.service name). HTTP surface: GET /api/v1/audit/records with 8 filter params + cursor pagination (base64url-encoded offset, limit 1–100). _normalize_mapping() handles arbitrary Python objects (dataclasses/Enums/datetime/Decimal/Path/to_dict). No events published or subscribed.
**When:** When tracing a specific mutation in payroll, compliance, or disbursement; when auditing actor actions for compliance review; when understanding how domain services wire into the audit trail.
**Upload:** ON-DEMAND

### `outbox-system.md`
**Purpose:** Full spec for the dual-component outbox infrastructure — at-least-once event delivery with idempotent consumer guards, dead-letter handling, and observability tracing.
**Description:** Two components: (1) OutboxManager (outbox_system.py) — full-featured per-service outbox with EventRegistry contract validation, IdempotencyStore deduplication (consume_once()), DeadLetterQueue overflow, PersistentKVStore (3 namespaces: outbox_records/processed_events/dispatch_log), Observability tracing; used by automation/integration/leave/payroll/attendance/auth/hiring. (2) EventOutbox (event_outbox.py) — lighter lower-level outbox without EventRegistry validation; used by background_jobs/expense/project. OutboxRecord schema: outbox_id/event_id/event_type/tenant_id/status(pending|dispatched|failed)/payload/attempt_count/last_error. dispatch_pending() with run_with_retry (3 attempts, 0.01s base delay, 0.5s timeout). transaction() helper for atomic domain-mutation + enqueue. No HTTP surface — imported directly.
**When:** When debugging event delivery failures; when understanding at-least-once delivery guarantees; when choosing OutboxManager vs EventOutbox for a new service.
**Upload:** ON-DEMAND

### `error-registry.md`
**Purpose:** Full spec for the central error-code catalogue — maps 22 system error codes to type, severity, resolution steps, and retryability.
**Description:** Scope (support module; no HTTP surface; imported by domain services and api_contract.py). Functions: get_error_descriptor(code) → dict|None; register_error() for runtime extension by country adapters; update_error() for field-level amendment. Descriptor schema: type(validation|system|external_dependency) / severity(critical|high|medium|low) / resolution_steps(ordered human-readable operator instructions) / retryable(bool). 22 pre-registered codes across 6 domains: Payroll (6: EMPLOYEE_DATA_INCOMPLETE/CNIC_INVALID/TAX_CONFIG_MISSING/ATTENDANCE_INCONSISTENCY/COMPLIANCE_GATE_FAILED/DUPLICATE_RUN), Compliance (3), Attendance (4), Bank/Disbursement (2), WhatsApp (2), General (5: VALIDATION_ERROR/FORBIDDEN/NOT_FOUND/EMPLOYEE_NOT_FOUND/SYSTEM_ERROR). Resolution steps written for HR operators (reference UI nav paths, not code).
**When:** When surfacing error codes in operator-facing UI; when a country adapter needs to register jurisdiction-specific error codes; when tracing what resolution guidance an operator sees for a specific error.
**Upload:** ON-DEMAND

### `experience-layer-service.md`
**Purpose:** Full spec for the experience-layer service — tenant tier and feature-flag resolver controlling which capabilities are active for SMB / MID / ENTERPRISE tenants.
**Description:** Scope (add-on; no HTTP surface; services/product/experience.py 102 lines; services/experience_layer_service.py is 3-line re-export stub). ExperienceLayerService: resolve_feature_flags(tier, sme_lite_mode, payroll_managed_mode, admin_override_controls) → dict[str, bool]. Tier feature matrix: SMB (payroll/compliance/attendance), MID (+performance/recruitment/analytics), ENTERPRISE (+governance/advanced_compliance/workflows). sme_lite_mode restricts any tier to {payroll, compliance, attendance}. payroll_admin_override_controls requires tier in {MID, ENTERPRISE} AND payroll_managed_mode AND admin_override_controls. FinancialWellnessHook: frozen dataclass (provider/endpoint/method/integration_mode) for loan_api_hook() and ewa_api_hook(). Related: services/product/middleware.py + tier_enforcer.py. Companion spec: docs/specs/experience-layer.md (UX principles).
**When:** When implementing tier-gated UI features; when understanding PaaS mode controls; when wiring financial-wellness EWA/loan integration hooks.
**Upload:** ON-DEMAND

### `governance-service.md`
**Purpose:** Full spec for the governance-service — human-in-the-loop gate enforcement for payroll, compliance, anomaly override, and decision card lifecycle.
**Description:** Scope (support; no HTTP surface; services/governance/service.py 97 lines; ENTERPRISE-tier gated per ExperienceLayerService). GovernanceService: create_payroll_approval() → pending approval dict; review_payroll_approval(decision: approved|rejected) — guards status==pending; submit_compliance(approval) — guards status==approved; override_anomaly(reason required) — mutates anomaly dict with override fields; update_decision(lifecycle_state != expire) / expire_decision() — decision card terminal state. GovernanceError (ValueError subclass) for all policy violations. In-memory audit_trail: list[GovernanceAction{user/action/timestamp/reason}]. No persistence — callers must call emit_audit_record() separately for durable audit trail. Aligned to docs/canon/decision-system.md.
**When:** When implementing payroll finalization gates; when tracing anomaly override approval chains; when auditing decision card lifecycle mutations.
**Upload:** ON-DEMAND

---

## CATEGORY 11 — BACKEND SYSTEM DOCS
**Location:** `backend/docs/system/`
Ops-level documentation for the AURA HRMS build: purpose, success gates, roadmap, gap tracking, infrastructure, and certification record.

### `catalogue.md`
**Purpose:** Session entry point for the AURA HRMS backend build — maps all 12 system docs, their purpose, when to read, relationships, and session-start checklist.
**Description:** Documents 12 system docs with purpose, when to read, key content, and feed-into relationships. Includes document relationship diagram. Session start checklist (6 steps: pending → progress → gap-register → roadmap → success-criteria → qc-suite). Build protocol reminders (workspace path, gap rules, no scope creep, country rule, event rule, QC rule, doc rule). The backend equivalent of the UI `hrms-doc-catalogue-v1.md`.
**When:** Start of any backend session or when onboarding to the backend codebase.
**Upload:** ON-DEMAND

### `system-purpose.md`
**Purpose:** AURA HRMS identity, 7 design principles (P1-P7), 6-layer architecture, and strategic product model.
**Description:** System identity: "TRUST INFRASTRUCTURE for workforce operations." Core purpose: payroll accuracy, Pakistan compliance automation, decision-driven HR, multi-country expansion. 7 principles: P1 Compliance is the product / P2 Payroll must never break / P3 Decisions > Dashboards / P4 AI explainable and reversible / P5 Country logic isolated / P6 Mobile-first / P7 WhatsApp is a real access channel. 6-layer architecture diagram. 5-layer strategic product model. "What it is NOT" list.
**When:** When validating whether a feature belongs in the core system; when aligning UI decisions with backend principles.
**Upload:** ON-DEMAND

### `success-criteria.md`
**Purpose:** Binary completion gates S1-S18 across 4 tiers — the system is done when all are met.
**Description:** Tier 1 non-negotiable (S1-S5: zero payroll errors, compliance automated, compliance validates before payroll, country abstraction enforced, full audit trail). Tier 2 core product (S6-S10: decision cards, explainable AI, human-in-loop, WhatsApp functional, manager WhatsApp approvals). Tier 3 architecture (S11-S14: new country = adapter only, multi-entity, API-first, independent deploy). Tier 4 quality gates (S15-S18: pytest 0 failures, QC 11/11, RE-QC all green, intent/build aligned). Phase gate definitions. Known partial: S3 (compliance gate not fully wired into mark_paid).
**When:** When assessing whether a backend feature is complete or a gap; when deciding if a UI chrome flag is permanent or temporary.
**Upload:** ON-DEMAND

### `roadmap.md`
**Purpose:** 5 sequential build phases with deliverables and current completion status.
**Description:** Phase 1 (Architecture): country abstraction, service map, API standards, event/read-model catalogs — ✅ Complete. Phase 2 (Pakistan Payroll/Compliance): tax engine, FBR/EOBI/PESSI, bank disbursement, Raast — ✅ Complete (S3 partial G22 deferred). Phase 3 (Decision Engine/AI Guardian): anomaly detection, Decision Cards, human-in-loop — ✅ Complete. Phase 4 (WhatsApp + Mobile): WhatsApp service, mobile gateway, approval actions — ✅ Complete. Phase 5 (Multi-Country): Pakistan adapter + DummyAdapter proving architecture — ✅ Complete. All 5 phases complete as of Session 8 (2026-04-14). Sessions 6–8 outcomes (SPEC-G, S7-G, S8-G gaps) reflected in Phase 1 status section (updated 2026-06-06). Execution constraints (sequential dependency rules).
**When:** When understanding why a backend service exists or what build phase introduced it.
**Upload:** ON-DEMAND

### `progress.md`
**Purpose:** Single scoreboard for all registered backend gaps (G01-G48+) and session-by-session completion status.
**Description:** Overall status table (14 phases/groups, all complete through Session 8 except UI G28a-G28j still open). Per-phase gap tables with G-numbers, severity (P0-P3), title, and DONE/OPEN/DEFERRED status. Architecture principles enforced at every fix. Last updated: 2026-04-14 (Session 8). 10 UI pages (G28a-G28j) are the only remaining open items.
**When:** When picking up backend work mid-session; when checking whether a specific gap has been addressed.
**Upload:** ON-DEMAND

### `gap-register.md`
**Purpose:** Full detail record for every backend gap (83 total across 15 gap phases): type, severity, file, issue, action, dependencies, and final status.
**Description:** 83 total gaps across 8 sessions. Gap types: CODE_MISSING, DOCS_MISSING, VIOLATION, DUPLICATION, STUB. Severity P0-P3. Phases: G01-G12 (Phase 1 architecture), G13-G22 (Phase 2 Pakistan payroll/compliance), G19-G22 (Phase 3 decision engine), G23-G25 (Phase 4 WhatsApp/mobile), G26-G27 (Phase 5 multi-country), G28-G29 (UI), G30-G32 (docs-to-code), G33-G42 (Pakistan statutory Session 3), G43-G48 (Canon Overlay Pass 3 Session 4), MR-G01/G02 (Market Research overlay), SB-G01-SB-G05 (Behavior Spec Session 5), MN-G01-MN-G07 (Manus AI MR Session 5), SPEC-G01-SPEC-G08 (HRMS Spec Session 6), S7-G01-S7-G05 (Session 7 final integrity), S8-G01-S8-G08 (Session 8 master docs overlay). Summary: 79 DONE, 3 DEFERRED (G27 UAE adapter, MN-G07 export sector, S8-G07 decisions UI), 10 OPEN (G28a-G28j UI pages). Never fix a gap without registering it here first.
**When:** When investigating why a specific piece of backend code was written a certain way; when planning fixes for known architectural violations.
**Upload:** ON-DEMAND

### `pending.md`
**Purpose:** Active work tracker — what is blocking certification, what is deferred, what is open. The "what to do next" doc.
**Description:** 3 blocking items: full QC suite not run since Session 4 (new Sessions 5-8 code unverified), 10 UI pages G28a-G28j open (backends ready), G22 check_payroll_gate() not wired into mark_paid() (deferred). UI page list: compliance, decisions, financial-wellness, banking, analytics, helpdesk, automations, whatsapp-admin, projects, mobile-dashboard. Also covers deferred items and Pakistan statutory gaps G33-G42 (all now DONE per progress.md). Last updated 2026-04-14 (Session 8).
**When:** At the start of any backend session — identifies the highest-priority remaining work.
**Upload:** ON-DEMAND

### `infrastructure.md`
**Purpose:** Documents 6 platform-level infrastructure modules that underpin all business services but have no HTTP surface.
**Description:** chaos_engine.py (497 lines — fault injection, gated by env flag, never in production), resilience.py (672 lines — CircuitBreaker/RetryPolicy/Bulkhead/trace ID), outbox_system.py (OutboxManager — at-least-once event delivery, all canonical events dispatched here), background_jobs.py (cron + deferred job scheduler), persistent_store.py (thin persistence abstraction), supervisor_engine.py (749 lines — infrastructure incident supervisor). Dependency direction diagram. 3 rules: no cross-DB calls, all external calls via resilience.py, all events via outbox_system.py.
**When:** When touching event delivery, background jobs, or resilience code; when debugging why an event was/wasn't delivered.
**Upload:** ON-DEMAND

### `intent_build_alignment.md`
**Purpose:** Final certification record — verified evidence of alignment between intent, build artifacts, runtime handlers, and test coverage.
**Description:** Last QC-verified: 2026-03-31 (pre-sessions 2-8). pytest 281 passed, QC 11/11, RE-QC all green (5/5, 5/5, 6/6). Has 8 update sections covering: country-layer (2026-04-01), WhatsApp integration (2026-04-01), Pakistan real-integration hardening (2026-04-01), mobile product layer (2026-04-01), experience-tier alignment (2026-04-01), P3 orchestration cleanup (2026-04-01), Session 2 (2026-04-12, all G01-G29 done), Session 3 spec alignment + Pakistan statutory (2026-04-12), Session 4 Canon Overlay Pass 3 (2026-04-12), Session 5 Behavior Spec overlay. CRITICAL: 50+ new files added in Sessions 2-8. Full QC suite (pytest + QC 11/11 + RE-QC) has NOT been re-run since 2026-03-31. Tier 5 coverage gaps exist for 15+ new methods/endpoints from Sessions 2/3/5/6. Alignment is PENDING re-certification — do not treat as currently certified.
**When:** When assessing backend certification status; when determining if a new QC run is needed before shipping.
**Upload:** ON-DEMAND
### `MASTER MARKET RESEARCH.md`
**Purpose:** Authoritative Pakistan HRMS market intelligence — 21 sections covering competitor analysis, 7 validated customer pain points, 7 market gaps, and strategic product positioning.
**Description:** 21 sections. Covers: global HRMS landscape (Enterprise/Mid-Market/Payroll-First/New AI-Led), Pakistan market (SMB/Mid-Market/Enterprise segmentation), 5 regulatory systems (FBR/EOBI/PESSI/SESSI + provincial variations), 6-vendor competitor analysis with per-vendor SWOT (PayPeople/Sidat Hyder/Resourceinn/Decibel/WebHR/SAP), 7 customer pain points (P1 payroll errors, P2 compliance confusion, P3 attendance/payroll mismatch, P4 lack of trust, P5 poor employee access, P6 manager blindness, P7 support reliability), 4 regional insights (Karachi/Lahore/Islamabad/Industrial Punjab), 7 market gaps (Compliance Autopilot, AI Payroll Auditor, Decision-First UX, Pakistan-Native Design, WhatsApp HR Layer, Trust Infrastructure, Compliance-First for Startups), 5 strategic opportunities (Compliance Autopilot, PaaS, Export Sector, Financial Wellness, WhatsApp-Native), product innovation priorities (Must Build / Should Build / Do Not Build Early), 5-layer strategic product model, "Winning in 2026" framework, capability benchmark (must-have vs differentiators). Supersedes both source archive docs.
**When:** When validating product decisions against market reality; when understanding why certain features (compliance, WhatsApp, Decision Cards) are prioritized; when assessing competitive positioning.
**Upload:** ON-DEMAND

### `MASTER BEHAVIOR SPEC.md`
**Purpose:** Authoritative unified behavior specification — runtime rules, market-grounded WHY statements, payroll/compliance/decision/WhatsApp step flows, and audit canon.
**Description:** Merged from MARKET-VALIDATED BEHAVIOR SPEC v1.0 + HRMS SYSTEM BEHAVIOR SPEC. Covers: 6 core runtime rules (B1-B6), trust-first behaviors (pre-run confidence signal, anomaly report, reproducibility), payroll 5-step runtime flow with guards, compliance 4-step flow with full state machine (including MANUAL state), Decision Card 15-field schema, AI output canonical format (supporting_signals not supporting_data), WhatsApp/bank/disbursement/error behaviors, audit record fields, security behavior (RBAC, no plaintext, no log-leaking), system defaults (safe > risky, explicit > implicit), market gap closure map (GAP 1-7 → system behaviors), competitive differentiation. Does NOT replace MASTER BUILD SPEC.
**When:** When implementing domain service behavior or reviewing any backend behavior against product intent.
**Upload:** ON-DEMAND

---

## CATEGORY 12 — BACKEND SPECS
**Location:** `backend/docs/specs/`
Feature-level specifications: experience principles, mobile constraints, country-specific payroll/compliance requirements, and integration adapters.

### `experience-layer.md`
**Purpose:** Decision-first UX principles, API interaction model, mobile constraints, tier logic (SMB/MID/ENTERPRISE), SME Lite mode, and PaaS mode.
**Description:** 4 principles (Show actions / Show what needs fixing / Show why / Show confidence). Decision-first UI rule (no report-heavy dashboards). API model (intent-driven request → decision payload with rationale → actions first). Mobile constraints (low bandwidth, minimal payload). Tier definitions: SMB (payroll+compliance+attendance), MID (SMB + performance+recruiting+analytics), ENTERPRISE (MID + governance+advanced compliance+workflows). Tier gating is deterministic/monotonic (SMB ⊆ MID ⊆ ENTERPRISE). SME Lite mode (only payroll/compliance/attendance; hides all other modules regardless of tier). PaaS mode (managed payroll — admin override only for MID/ENTERPRISE; disabled for SMB). Financial wellness API contracts (POST /loan, POST /ewa). Implementation: services/product/experience.py, tier_enforcer.py, middleware.py, services/payroll/paas.py.
**When:** When designing any new UI surface — confirms the decision-first principle and mobile payload constraints; when implementing tier gating.
**Upload:** ON-DEMAND

### `mobile-layer.md`
**Purpose:** Mobile gateway layer spec — compact action-oriented responses for low-bandwidth mobile clients.
**Description:** Scope (optimization layer, not a separate service; does not replace domain APIs), implementation files (MobileGatewayService in services/mobile_gateway.py, 211 lines; mobile/contracts.py), 4 API endpoints (/api/v1/mobile/dashboard, /mobile/employee/{id}, /mobile/payslip/{id}, /mobile/action), card-based response model (type: decision|alert|task; severity: critical|high|medium|low; title/why/action/due_at), sort order (critical→high→medium→low then due_at).
**When:** When building any mobile-first UI surface; when understanding how compact payloads differ from full API responses.
**Upload:** ON-DEMAND

### `specs/country/pakistan/compliance.md`
**Purpose:** Pakistan statutory compliance spec — FBR Annexure-C schema, exact tax slabs, EOBI formula, PESSI/SESSI formula, validation rules, and QC test scenarios.
**Description:** FBR Annexure-C complete YAML schema (employer NTN/name/address + per-employee: CNIC/filer status/annual taxable income/tax slab code/monthly tax/exemptions list). Tax slabs: 6 slabs for 2024/2025/2026 (0% to PKR 600K, 5% up to 1.2M, 15% up to 2.2M, 25% up to 3.2M, 30% up to 4.1M, 35% above). Profile-based withholding override via metadata.rate. EOBI formula: insurable_wage = min(max(basic, eobi_min_wage), eobi_max_wage); employee=1%, employer=5%. PESSI/SESSI formula: province-aware, employer 6% + employee 1%, wage_cap PKR 18,000. 5 validation rules (missing tax, incorrect slab, invalid CNIC, negative salary, non-numeric amounts). Input/output schemas. 2 test scenarios. QC 10/10 PASS.
**When:** When auditing H07 Compliance Reports content; when implementing Pakistan statutory calculations; exact formulas for EOBI/PESSI math.
**Upload:** ON-DEMAND

### `specs/country/pakistan/payroll.md`
**Purpose:** Pakistan payroll computation spec — salary structure, exact calculation formulas, tax slabs, 10 test scenarios, and final settlement rules.
**Description:** Salary structure (basic + allowances: HRA/conveyance/medical/utility/shift; deductions: income tax/PF/loans/absence penalties). Calculation formulas: Gross = Basic + Allowances + Bonuses/Arrears; Taxable Income = Gross - Non-Taxable Allowances - Exemptions; Net = Gross - Total Deductions; Total Deductions = Tax + PF + Loan Recovery + Others. Gratuity (accrual-based, prorated), Provident Fund (employee + employer %, with ledger), Loans/Advances (installment recovery, deferment), Arrears/Bonuses (taxable status tagging). Final Settlement (F&F): leave encashment, pending deduction recovery, net payable/recoverable output. 3 payroll frequencies (Monthly/Weekly/Daily). Prorated salary formula. 10 test scenarios. QC 10/10 PASS.
**When:** When auditing payroll calculation details; when implementing salary computation; reference for F&F logic.
**Upload:** ON-DEMAND

### `specs/integrations/whatsapp.md`
**Purpose:** WhatsApp HR layer spec — 4 capabilities, 3 interaction modes, full step-by-step flows, webhook/response schemas, OTP/RBAC security model, error handling, and 15 QC test scenarios.
**Description:** 6 sections. §1 Capabilities: Payslip (current/past, secure expiring link, PDF), Leave (balances/apply with overlap/holiday validation, tracking ID), Approvals (manager list+decide with OTP step-up, audit confirmation), Alerts (priority tags, quiet hours bypass for high-priority, deep links). §2 Interaction model: 3 modes (natural language/shortcuts/buttons), step-by-step session with context retention, 15-min timeout, cancel keyword. §2.4 Security: identity mapping table (wa_identity_map), one-phone-per-employee enforced, OTP policy (6 digits, 3 retries, 5-min validity, hard lock), RBAC by intent (payslip=employee+, leave=self, approval=manager/hr_admin, alert=system/hr_admin). §3 4 flows with step-by-step detail and edge cases. §4 Full webhook schema (event_id/timestamp/channel/message/security/otp fields) + response schema (correlation_id/to/type/text/interactive/attachments/meta). §5 Error handling: IDENTITY_NOT_MAPPED, OTP_REQUIRED/FAILED/LOCKED, FORBIDDEN, structured error envelope with recoverable + next_step. §6 15 QC test scenarios (functional + resilience including idempotency, rate limiting, OTP flows). QC 14/14 checks PASS.
**When:** When implementing WhatsApp service; when auditing security model for WhatsApp access; much richer than the service doc.
**Upload:** ON-DEMAND

### `specs/integrations/accounting.md`
**Purpose:** Accounting integration spec — QuickBooks and SAP journal export adapters, payload schema, and one-way sync model.
**Description:** Scope (one-way: HRMS payroll → accounting; triggered after PayrollPaid; no read-back). Implementation (integrations/accounting/base.py, 108 lines). QuickBooksAdapter (OAuth Bearer, /v3/company/{realm_id}/journalentry, config structure, return shape). SAPAdapter (OData ZPAYROLL_JOURNAL_SRV, config from SAPConnectorConfig.from_env()). Journal entry payload schema (lines with account_code/description/debit/credit, totals, period, employee array). Config loading patterns.
**When:** When auditing accounting integration gaps or when extending the H10 Integrations page beyond webhooks.
**Upload:** ON-DEMAND

### `specs/ui/manager_dashboard.md`
**Purpose:** Manager dashboard decision-first UX specification — 7 data blocks, each surfacing only actionable exceptions.
**Description:** Principle (decision-first, no decorative charts, urgency-ordered content). 7 data blocks: Attendance Alerts (late/absent/missing records + actions), Overtime Anomalies (threshold/spike/unapproved + actions), Compliance Status (validation failures/filing deadlines/violations), Payroll Anomalies (AI guardian flags/ghost employees — acknowledge/override/dismiss), Leave Requests (pending approvals + policy conflicts), Performance Pipeline (overdue PIPs/calibrations + actions), Decision Cards (highest-priority open cards). UX rules (max 5 items per block, age badges, severity-ordered). Empty states per block. Data sources list.
**When:** When building or auditing H01 HR Manager Dashboard; confirms decision-first content hierarchy and which backend endpoints each block uses.
**Upload:** ON-DEMAND

---

## CATEGORY 13 — DESIGN REPORTS
**Location:** `backend/docs/design/`
Build convergence passes, QC validations, and UI design anchors from the backend build process.

### `design-system-anchor.md`
**Purpose:** HRMS UI design system anchor — 19 sections covering visual rules, typography, spacing, color, components, layout, and 5 page archetypes. Supersedes all page-level design decisions.
**Description:** 19 sections: Design Principles (7 rules), Global Visual Rules (12-column layout, approved patterns only), Color System (intent map: primary blue/neutral/green/amber/red/gray), Typography (5-level hierarchy: page title/section/card/body/meta), Spacing (approved scale: 4/8/12/16/20/24/32), Border Radius+Surfaces, Shadow+Border, Grid+Layout (page frame: header/summary/primary workspace/secondary/supporting), Component Rules (cards/buttons/inputs/badges/metrics/panels), Data Display Rules (structured lists preferred over tables), Row Structure, Hierarchy Rules (L1 identity+primary/L2 main workflow/L3 supporting context), Page Polish (fix alignment→spacing→hierarchy→remove clutter), Responsiveness (desktop-first), Page Consistency, Codex Execution Rules, QC Checklist, Final Lock, Page Archetype Rules. Page archetypes: COMMAND CENTER (Dashboard), DATA DIRECTORY (Employees), ANALYTICS/EVALUATION (Performance), PIPELINE (Hiring), FORM/CONFIG (Settings) — each with mandatory structural rules. Status: LOCKED. Note: backend-side UI spec, distinct from Meridian `design-language.html`.
**When:** When building the 10 remaining UI pages (G28a-G28j) in the Next.js app.
**Upload:** ON-DEMAND

### `micro-fix-register.md`
**Purpose:** Registry of repeatable UI fixes converted to system rules — 2 fixes currently registered. All future UI prompts must anchor to this file.
**Description:** Captures UI fixes that recur across pages and converts them into enforced system rules. Format: FIX-NNN with PROBLEM/ROOT CAUSE/FIX/RULE/APPLIES TO. Currently 2 fixes: FIX-001 (nav overflow + dropdown: no tab may disappear without accessible alternative — "More" dropdown + priority ordering), FIX-002 (KPI card misalignment: grid system + equal height + standardized padding enforced). Extension rule: append only, never modify past fixes. QC 5/5. All UI prompts must include ANCHOR references to both design-system-anchor.md and micro-fix-register.md.
**When:** When building or polishing any of the 10 remaining UI pages (G28a-G28j).
**Upload:** ON-DEMAND

### `convergence-history.md`
**Purpose:** Consolidated record of sequential build convergence passes P28-P33 — backward compat, data integrity, event reliability, workflow integrity, final convergence, and system certification.
**Description:** P28 (Backward Compatibility: gateway path drift, list response shape drift, event naming drift — aliases added, regression tests locked), P29 (Data Integrity: DataIntegrityValidator across 8 domains), P30 (Event Consistency: replay safety), P31 (Workflow Integrity), P32 (Final Convergence: stale alias removal, end-to-end route coverage), P33 (Final System Certification: all QC gates green, 281 pytest passed, QC 11/11, RE-QC all green). Individual report files P28-P33 are pointers to this doc.
**When:** When understanding why gateway routes or response shapes are structured a certain way; when diagnosing backward compatibility issues.
**Upload:** ON-DEMAND

### `api-contract-standardization-summary.md`
**Purpose:** Summary of D1 Service Contract Standard adoption — shared envelope helpers, newly wrapped endpoints, payload normalization.
**Description:** Shared utilities in api_contract.py (envelope helpers, pagination helpers, compatibility list payload builders). Newly wrapped endpoints: payroll_api.py (5 endpoints), leave_api.py, employee API, notification API, reporting analytics API, hiring/auth/settings APIs. Purpose: preserve existing PayrollService business methods while adapting legacy payloads (`{"data": ...}`, `page.nextCursor/hasNext`) into D1 canonical envelopes with `meta.pagination`.
**When:** When diagnosing inconsistent API response shapes; when adding new endpoints that must conform to D1 standard.
**Upload:** ON-DEMAND

### `background-jobs-summary.md`
**Purpose:** Summary of background jobs layer — workloads moved off request path and domain boundary preservation rules.
**Description:** 5 workloads now job-ready: payroll_processing (payroll.run handler), leave_request (leave.balance.recompute handler), notification_dispatch (notification.dispatch handler), event_outbox (outbox.dispatch handler), workflow escalation (workflow.escalation handler). Boundary preservation: business rules stay in domain services; job layer only schedules/retries/tracks/replays. Tenant context and trace IDs carried into every execution.
**When:** When adding new background operations; when debugging why a scheduled job didn't run.
**Upload:** ON-DEMAND

### `search-indexing-summary.md`
**Purpose:** Summary of search-service implementation — projection-backed indexing, event flow, read models extended.
**Description:** Read models extended (employee_directory_view, organization_structure_view, candidate_pipeline_view, document_library_view, payroll_summary_view, global_search_view). Event and job flow (domain events → outbox → search-service consumes → enqueues search.reindex background job → rebuilds projections → search APIs query only indexed documents). Guardrails: no transactional DB reads for search, domain services remain authoritative for writes.
**When:** When auditing H08 Global Search; when understanding why search results may lag behind operational data.
**Upload:** ON-DEMAND

### `chaos-auto-healing-report.md`
**Purpose:** Chaos testing and auto-healing validation report — extend-only harness in chaos_engine.py verified by tests.
**Description:** Scope (non-invasive fault injection via chaos_engine.py; does not change business logic; injects reversible failures; uses existing observability/retry/jobs/event-outbox/workflow/supervisor subsystems; validates graceful degradation). Scenarios covered: service downtime, cascading failures, event delivery failures, job queue saturation, workflow timeout. All failures validated with auto-recovery assertions.
**When:** When adding new infrastructure or services that need chaos-test coverage.
**Upload:** ON-DEMAND

### `addon-convergence-report-p50.md`
**Purpose:** P50 add-on convergence QC — validates add-on services against core platform canonical controls D1-D8 with 10 QC dimensions.
**Description:** Scope (convergence of add-ons with core + parity layers). 10 QC dimensions: duplication across modules, parallel logic vs. existing services, automation-to-workflow alignment, analytics-to-reporting consistency, tenant isolation guarantees, event contract conformance, API standard compliance, domain boundary respect, read-model contract alignment, security model coverage. Objective: produce single coherent system from core + add-ons.
**When:** When adding new add-on services; when validating that add-on code doesn't duplicate or conflict with core services.
**Upload:** ON-DEMAND

### `backward-compatibility-report-p28.md` / `data-integrity-report-p29.md` / `event-reliability-report-p30.md` / `workflow-integrity-report-p31.md` / `final-convergence-report-p32.md` / `final-system-certification-pass-p33.md` / `addon-certification-pass-p51.md`
**Purpose:** Pointer-only stubs — all content merged into `convergence-history.md` or `addon-convergence-report-p50.md`.
**Description:** Single-line pointer files. P28/P29/P30/P31/P32/P33 → see `convergence-history.md` (P33 = Final System Certification: all QC gates green, 281 pytest passed, QC 11/11, RE-QC all green). P51 → confirms P50 add-on convergence passed QC 10/10.
**When:** Do not load — use `convergence-history.md` and `addon-convergence-report-p50.md` directly.
**Upload:** N/A (pointers only)

---

## CATEGORY 14 — VALIDATION REPORTS
**Location:** `backend/docs/reports/`

### `platform_validation_2026-04-01.md`
**Purpose:** End-to-end platform validation report (2026-04-01) — full regression evidence, 5 mandatory scenario categories, mandatory scenario matrix, and final certification declaration.
**Description:** Date: 2026-04-01. Status: PASS. Alignment: 100%. Test files listed with coverage: tenant+gateway+runtime (test_gateway_runtime_alignment_e2e + test_gateway_tenant_context), country abstraction (test_country_resolver + test_payroll_country_adapter_integration), attendance+payroll (test_services_attendance_service + test_payroll_compensation_integration), payroll+compliance+Pakistan (test_services_payroll_service + test_document_compliance_service + test_security_compliance_lock), AI/decision (test_payroll_guardian + test_hr_copilot + test_workforce_analytics + test_governance_service), experience layers (test_manager_dashboard_api + test_employee_ui + test_dashboard_ui + test_reporting_analytics), recruitment (test_hiring_service), integrations (test_integration_service + test_api_gateway_proxy_forwarding). 5 mandatory scenarios: payroll+compliance PASS, attendance+payroll sync PASS, WhatsApp PASS, manager decision+audit PASS, recruitment→onboarding PASS. AI Payroll Guardian anomaly+confidence+explanation validated. Pakistan adapter (FBR/EOBI/PESSI/bank/Raast) validated. Architecture: country abstraction enforced, no drift. 1 auto-fix applied (Python deprecation warning in test_settings_domain.py). Final: FULL SYSTEM WORKS END-TO-END, PAKISTAN AI HRMS FULLY CONVERGED.
**When:** When assessing what was validated at end of Phase 4; reference baseline for QC re-run comparison.
**Upload:** ON-DEMAND

### `alignment_final.md`
**Purpose:** Pointer-only stub — redirects to `intent_build_alignment.md` as the authoritative alignment record.
**Description:** 4-line pointer file. States that docs/system/intent_build_alignment.md is canonical. References convergence-history.md for P28-P33 pass history. Status: ✅ Full alignment verified (gateway routes, runtime handlers, service topology mutually consistent) — as of 2026-03-31.
**When:** Do not load — use `intent_build_alignment.md` directly.
**Upload:** N/A (pointer only)

---

## CATEGORY 15 — ROOT OPS DOCS
**Location:** `D:\HRMS\ops\` (moved from project root during 2026-06-07 workspace restructuring)
Workspace-level files that sit outside both the UI docs folder and the backend repo.

### `hrms-directory-structure-v1.md`
**Purpose:** UI workspace directory structure — the canonical folder layout for the Meridian HCM UI build.
**Description:** Defines the intended layout for: hrms-audit-v1.py (root), hrms-audit-manifest-v1.json (root), docs/ (system docs), seed-pages/ (read-only archetype anchors), contracts/ (schema + page contracts), pages/ (built HTML), repo/ (unzipped SME-HRMS-main). Includes directory rules (read-only seed pages, one HTML per page, script resolves relative paths) and first-run instructions. NOTE: This intended layout predates the 2026-06-07 workspace restructuring — current actual layout is `ops/`, `frontend/pages/`, `frontend/seeds/`, `design/`, `backend/` (see doc audit findings; `repo/` and the source zip have since been removed as redundant with the extracted `backend/` working copy).
**When:** When setting up the workspace on a new machine; when auditing file placement against the defined structure.
**Upload:** ON-DEMAND

### `hrms-progress.md`
**Purpose:** Meridian HCM UI build progress log — session-by-session record of pages built, gaps logged, and stabilisation passes completed.
**Description:** Tracked in the audit manifest (sealed 2026-03-30). Contains detailed build history for all 49 pages across H01-H13, including per-session gap discovery, P-32 scroll fix application record, stabilisation pass summaries, and contract sealing confirmations. The 1,113-line detailed companion to the summary status in `hrms-archetype-system-v1.md`.
**When:** When reconstructing the exact history of when a page was built or a gap was logged; when auditing the full build timeline.
**Upload:** ON-DEMAND

### `HRMS PRODUCT SPEC.md`
**Purpose:** Root-level AURA HRMS product and architecture specification — system purpose, design principles, and 6-layer architecture in structured plain-text format.
**Description:** Formatted as structured plain-text (not Markdown headers). Covers: system purpose (zero-error payroll, Pakistan compliance, decision system, multi-country), 7 design principles (P1-P7), 6-layer architecture (data/org, domain, country abstraction, services, integrations/access, experience), capability list, Pakistan statutory requirements, non-goals. Appears to be an earlier standalone product spec; content largely superseded by `docs/system/system-purpose.md` and `docs/system/MASTER BUILD SPEC.md` in the backend repo but useful as a quick-reference summary.
**When:** When needing a compact product overview; when aligning UI design decisions with product principles.
**Upload:** ON-DEMAND

### `answers.md`
**Purpose:** Design decision log — 5 canonical architectural choices with their rationale, plus a final clean service map.
**Description:** 5 decisions: C1 expense-service vs ewa-financial-service are SEPARATE (expense=accounting/reimbursements/receipts; EWA=earned wage access/salary advances/payroll-linked), C2 helpdesk-service is ADD-ON (not core HRMS — belongs in HR service delivery, not required for payroll/compliance/core HR), C3 automation-service is INFRASTRUCTURE SERVICE not business domain (no HR logic — orchestrates workflows/triggers/scheduling), C4 decision-service is STANDALONE (cross-domain: spans payroll/attendance/compliance/performance — embedding in payroll would break architecture), C5 WhatsApp is STANDALONE ACCESS CHANNEL SERVICE not just an integration adapter (requires identity mapping/session handling/security/workflow execution). Final service map: CORE DOMAIN (payroll/compliance/attendance/employee), FINANCIAL (ewa/expense), INTELLIGENCE (decision), INFRASTRUCTURE (automation), INTEGRATION/ACCESS (whatsapp/bank/government-adapters), OPTIONAL (helpdesk).
**When:** When uncertain about whether a feature belongs in one service vs. another; when justifying service boundary decisions.
**Upload:** ON-DEMAND

### `pending.md`
**Purpose:** Root-level pending work tracker — 10 open UI pages (G28a-G28j) and 2 deferred items.
**Description:** Two sections: (1) UI Pages (G28) — 10 Next.js pages still to build, all backends implemented: `/app/compliance` (compliance_api.py), `/app/decisions` (decision_api.py), `/app/financial-wellness` (ewa.py), `/app/banking` (banking_api.py), `/app/analytics` (reporting_analytics_api.py), `/app/helpdesk` (helpdesk_api.py), `/app/automations` (automation_api.py), `/app/engagement` (engagement_api.py), `/app/whatsapp-admin` (whatsapp_api.py), `/app/expenses` (expense_api.py). (2) Deferred — G27 UAE statutory adapter (needs WPS/MOHRE/DEWS knowledge); G22 full `check_payroll_gate()` wiring into `payroll_service.py mark_paid()` (needs integration test coverage). Note: G33-G42 Pakistan statutory gaps removed from this file — all DONE as of Session 3 (2026-04-12); see `docs/system/progress.md` for confirmed status.
**When:** When checking which backend-ready UI pages still need building; when reviewing deferred items before starting a new session.
**Upload:** ON-DEMAND

### `build-progress.md`
**Purpose:** Build progress summary for the AURA HRMS backend — session history, architecture rules, repo location, and gap closure status.
**Description:** Last updated 2026-06-06 (Tracker Catalogue Pass complete). Documents: what the project is (AURA HRMS trust infrastructure), repo location (D:/HRMS/backend/), product spec anchor (D:/HRMS/HRMS PRODUCT SPEC.md), architecture rules (country-agnostic, capability-driven, country-focused). Session status: all 79 backend gaps DONE (G01–G29, G33–G42, plus Sessions 4–9 gaps). 5 country base interfaces. 3 DEFERRED (G27 UAE adapter, MN-G07 export sector, S8-G07 decisions UI). 10 OPEN (G28a–G28j UI pages). Latest addition: Tracker Catalogue Pass — 34 HTML pages catalogued in tracker.md Section E, BG-022–034 UI-backend gaps documented. For full gap-by-gap scoreboard see `docs/system/progress.md`.
**When:** When quick-referencing the repo path, product spec anchor, or overall session completion status.
**Upload:** ON-DEMAND

### `tracker.md`
**Purpose:** Full workspace read tracker + OIG Overlap Register — tracks line-by-line read status of every file in the workspace and records Session 9 inter-file normalisation findings.
**Description:** Last updated 2026-06-06. 11 sections (A–K) covering: Section A root-level ops files, Section B contracts (47 JSON files, all DONE), Section C UI docs (10 files, all DONE), Section D seed pages (13 files, all DONE), Section E built pages (48 HTML pages — H01/H02 DONE from earlier sessions, H03–H13 34 pages now DONE as of 2026-06-06 with full catalogue notes per page), Sections F–K backend docs/source files (many still PENDING — backend Python source not yet read). Also contains: OIG Overlap Register (13 groups, Session 9 inter-file normalisation findings), Action Phase table (25 doc changes across 14 files). Status values: PENDING (not yet read) / DONE (read + catalogued).
**When:** When checking whether a specific file has been catalogued; when reviewing OIG overlap findings from Session 9; when picking up the full workspace read task.
**Upload:** ON-DEMAND

### `normalisation-tracker.md`
**Purpose:** Full-workspace doc normalisation pass tracker — line-by-line read log, cross-file findings register (16 findings), and catalogue-anchored fix-pass results for the 2026-06-08 normalisation sweep.
**Description:** 230 lines. Distinct from `tracker.md` (which covers the earlier catalogue-pass read status). Covers 109 project `.md` files at no-skim depth. Contains: per-file read status (PENDING/DONE), Cross-File Findings Log (16 findings #1–#16 with pattern, proposed fix, and resolution status), and the 2026-06-08 catalogue-anchored fix pass results (fixed #1/#11/#15; deepened but still-gap #8/#16; logged as gap #4/#5/#6/#7/#9/#10/#12/#13; pre-existing annotations #2/#3/#14). Findings #8/#12/#13 subsequently registered as G49/G50/G51 in gap-register.md (2026-06-10). Finding #6 resolved (coverage checklist relocation) 2026-06-10.
**When:** When reviewing the full rationale for any 2026-06-08 normalisation finding; when auditing which cross-file issues are still open vs resolved. NOTE: G49/G50/G51 all resolved 2026-06-10 — no open code/decision gaps remain.
**Upload:** ON-DEMAND

---

## QUICK LOOKUP

```
"What layout does this archetype use?"          → hrms-archetype-system-v1.md
"What fields does this service expose?"          → backend repo
"What does this status chip look like?"          → hrms-api-contracts.md
"What spacing/colour/font to use?"              → design-language.html
"Is there a gap for this missing endpoint?"      → hrms-ui-backend-gaps.md
"How do I write a contract file?"               → hrms-contract-structure-v1.md (DSL section)
"What visual pattern solves this problem?"      → hrms-design-register-v1.md
"What is the correct build sequence?"           → hrms-build-protocol-sop-v1.md
"Can I fix this inconsistency now?"             → hrms-stabilisation-sop-v1.md (probably no)
"What pages are already built?"                 → hrms-archetype-system-v1.md (build status)
"What does this archetype look like?"           → frontend/seeds/p[N]-*.html
"What files are tracked?"                       → hrms-audit-manifest-v1.json
"Which service owns this entity?"               → backend/docs/canon/domain-model.md
"What are all the API endpoints?"               → backend/docs/canon/service-map.md
"What events does a service emit?"              → backend/docs/canon/event-catalog.md
"What read model does this UI surface use?"     → backend/docs/canon/read-model-catalog.md
"What are Pakistan tax/compliance rules?"       → backend/docs/specs/country/pakistan/
"What is the QC validation process?"            → backend/docs/system/qc-suite.md
"What is next to build/fix on the backend?"     → backend/docs/system/pending.md
"Is this backend certified?"                    → backend/docs/system/intent_build_alignment.md
```

---

## CATEGORY 16 — BUILT HTML PAGES
**Location:** `frontend/pages/`
49 production-ready single-file HTML pages implementing the Meridian HCM UI. Each page is a complete self-contained HTML/CSS/JS document. All sealed in `hrms-audit-manifest-v1.json`.

```
H01 Dashboards (4 pages):
  h01-hr-manager-dashboard.html    [30 KB]  HR Manager overview: KPIs, payroll summary, AI attrition bar, dept charts, activity feed
  h01-employee-self-service.html   [28 KB]  Employee portal: leave balance, next payslip, goals, attendance this month
  h01-payroll-admin-dashboard.html [25 KB]  Payroll admin: cycle status, anomalies, headcount cost, processing timeline
  h01-recruitment-dashboard.html   [23 KB]  Recruitment: open roles, pipeline by stage, time-to-hire, offer accept rate

H02 List/Table (11 pages):
  h02-employees.html               [20 KB]  Employee list with avatar+name+ID, department, role, status, hire date
  h02-departments.html             [14 KB]  Department list with code, head, status, employee count
  h02-roles.html                   [14 KB]  Role list with title, level, category, headcount
  h02-job-postings.html            [16 KB]  Job posting list with status, applicant count, closing date
  h02-leave-requests.html          [17 KB]  Leave request list with employee, type, dates, days, status
  h02-payroll-records.html         [16 KB]  Payroll records list with period, gross, net, status
  h02-expense-claims.html          [17 KB]  Expense claims list with employee, category, amount, status
  h02-travel-requests.html         [17 KB]  Travel requests list with destination, departure, return, status
  h02-attendance-records.html      [18 KB]  Attendance records with check-in, check-out, status, source, record state
  h02-performance-reviews.html     [16 KB]  Performance reviews list with cycle, status, reviewer, due date
  h02-documents.html               [18 KB]  Employee documents list with type, expiry, status

H03 Detail/Profile (8 pages):
  h03-employee-profile.html        [43 KB]  Employee profile: Overview/Compensation/Documents/Leave/Performance/History tabs
  h03-department-detail.html       [32 KB]  Department detail: Overview/Members/Sub-departments tabs
  h03-role-detail.html             [18 KB]  Role detail: Overview/Employees in Role tabs
  h03-job-posting-detail.html      [26 KB]  Job posting detail: Overview/Candidates/Interview Schedule tabs
  h03-leave-request-detail.html    [16 KB]  Leave request detail: request info, balance, AI assessment, approval history
  h03-payroll-record-detail.html   [13 KB]  Payroll record detail: earnings breakdown, deductions, net pay, status history
  h03-expense-claim-detail.html    [25 KB]  Expense claim detail: line items, attachments, approval history, policy compliance
  h03-performance-review-detail.html [39 KB] Review detail: Goals/Feedback/Calibration/PIP tabs

H04 Forms (9 pages):
  h04-add-employee.html            [38 KB]  6-step new employee wizard: Personal→Employment→Role→Compensation→Access→Review
  h04-edit-employee.html           [34 KB]  Edit employee form with section tabs
  h04-create-department.html       [22 KB]  Create department form
  h04-create-role.html             [20 KB]  Create role form
  h04-create-job-posting.html      [39 KB]  4-step job posting: Details→Requirements→Pipeline Template→Publish
  h04-raise-leave-request.html     [15 KB]  Leave request form (simple)
  h04-raise-expense-claim.html     [26 KB]  Expense claim form (stepped: Details→Line Items→Attachments→Submit)
  h04-raise-travel-request.html    [16 KB]  Travel request form (simple)
  h04-salary-revision.html         [19 KB]  Salary revision form with compensation band and effective date

H05 Workflow (1 page):
  h05-approval-inbox.html          [25 KB]  Split-view approval inbox: list left, detail+action bar right

H06 Calendar/Timeline (3 pages):
  h06-leave-calendar.html          [26 KB]  Team leave calendar: month/week/day views, department filter, public holidays
  h06-attendance-timeline.html     [23 KB]  Attendance roster grid: team week view, status per employee per day
  h06-shift-roster.html            [23 KB]  Shift roster grid: schedule assignments by employee and date

H07 Analytics (5 pages):
  h07-hr-analytics.html            [55 KB]  HR Analytics: Workforce/Payroll stub/Attendance/Recruiting/Performance stub/Saved tabs
  h07-payroll-reports.html         [40 KB]  Payroll Reports: Overview/Monthly Breakdown/Department Costs/Payslips/Run History tabs
  h07-attendance-summary.html      [49 KB]  Attendance Summary: Overview/Daily/Department/Anomalies/Corrections tabs
  h07-engagement-results.html      [43 KB]  Engagement Results: Survey results, D1-D5 dimensions, question analysis, responses
  h07-compliance-reports.html      [56 KB]  Compliance Reports: Overview/Documents/Expiring/Acknowledgements/Tasks tabs

H08 Search (1 page):
  h08-global-search.html           [32 KB]  Global search with facets, result cards (employee/candidate/document)

H09 Inbox (1 page):
  h09-notifications-inbox.html     [38 KB]  Notifications inbox: folders, message list, detail panel with topic routing

H10 Settings (1 page):
  h10-org-settings.html            [62 KB]  Organisation settings: Company/Leave Policies/Payroll Config/Roles & Permissions/Attendance + chrome sections

H11 Builders (3 pages):
  h11-workflow-builder.html        [53 KB]  Workflow builder: approval routing, SLA, conditions on canvas with properties panel
  h11-survey-builder.html          [48 KB]  Survey builder: Likert5 questions, D1-D5 dimensions, publish/close lifecycle
  h11-report-builder.html          [42 KB]  Report builder: 8 report types, filter config, schedule, delivery

H12 Support (1 page):
  h12-helpdesk.html                [44 KB]  Helpdesk: ticket list, detail panel with thread+rail, SLA tracker, reply area

H13 Pipeline (1 page):
  h13-candidate-pipeline.html      [48 KB]  Candidate pipeline: Kanban board (Applied/Screening/Interview/FinalRound/Offer), slide panel
```

---

## CATEGORY 17 — PAGE CONTRACTS
**Location:** `contracts/`
46 page-level data contracts plus the schema template. Each contract is a JSON DSL file defining the data layer for its corresponding built page. All conform to `hrms-contract-structure-v1.md`.

**KEY FINDINGS FROM FULL READS (all 47 contracts read):**
- H07 contracts use a different top-level structure (no `_meta` wrapper) — fields: contract/version/date/backend_service/endpoints/gaps/tab_inventory
- H08/H09/H10 use `id` at top level; H11-H13 use mixed formats
- CG-001 confirmed: h01-recruitment-dashboard uses wrong enum values ("Interviewing" and "Completed" instead of canonical Hiring.candidate.status values)
- h04-create-job-posting references `GET /api/v1/pipeline-templates` — endpoint NOT documented in service-map or any service doc
- h04-add-employee step 4 saves compensation via separate POST call (POST /api/v1/compensation/employees/:id/salary-revisions)
- h03-department-detail: `icon_colour` field is UI-only (no backend field in Department model)
- h05-approval-inbox has type-specific context panels with exact field mappings per subject_type (leave/expense/travel)
- h07-engagement-results uses path `/aggregated-results` (not `/aggregates` as in service-map.md)
- h07-compliance-reports: accent colour amber #B45309 (not teal — compliance/risk theme)
- h09-notifications-inbox has detailed topic_code_to_folder_map (14 topic codes → 8 folders)
- h10-org-settings chrome_sections: 7 total (Profile/Security/Notifications/Integrations/AI+Automation + Audit Log + Data & Retention — 2 more than previously documented)
- h11-report-builder lists 8 explicit REPORT_TYPES
- h12-helpdesk has 10 endpoints (including stats + attachments — more than the 13 in service doc)
- h13-candidate-pipeline: "Final Round" uses local `is_final_round:true` flag; no PATCH issued for interview→final transition
- WELCOME_BANNER slot in h01-employee-self-service contract (not defined in schema template)

### `hrms-schema-template.json` [21 KB]
**Purpose:** Master slot contract for all 13 archetypes — the BLOCKER file that must exist before any page contracts can be created.
**Description:** Defines slot lists (required/optional), allowed components per slot, surface density values, and page state names (loaded/skeleton/empty/error/partial) for all 13 archetypes H01–H13. NOT tracked in the audit manifest (oversight — should be added).

### H01 Dashboard Contracts [4 files, 4.6–7.4 KB each]
```
hrms-h01-hr-manager-dashboard-contract.json    [7.4 KB]  HR Manager Dashboard DSL: KPI slots, chart config, AI bar, activity feed data
hrms-h01-employee-self-service-contract.json   [4.9 KB]  Employee Self-Service DSL: leave balance, payslip, goals, attendance slots
hrms-h01-payroll-admin-dashboard-contract.json [5.1 KB]  Payroll Admin Dashboard DSL: cycle status, anomaly feed, cost KPIs
hrms-h01-recruitment-dashboard-contract.json   [4.6 KB]  Recruitment Dashboard DSL: pipeline stage charts, hiring KPIs
```

### H02 List Contracts [11 files, 3.0–4.2 KB each]
```
hrms-h02-employees-contract.json           [4.2 KB]  Employees list columns, filters, actions, empty/error states
hrms-h02-departments-contract.json         [3.2 KB]  Departments list columns, filters, actions
hrms-h02-roles-contract.json               [3.0 KB]  Roles list columns, filters
hrms-h02-job-postings-contract.json        [3.5 KB]  Job Postings list columns, filters, pipeline link
hrms-h02-leave-requests-contract.json      [3.6 KB]  Leave Requests list columns, filters, decision links
hrms-h02-payroll-records-contract.json     [3.8 KB]  Payroll Records list columns, filters
hrms-h02-expense-claims-contract.json      [3.5 KB]  Expense Claims list columns, filters
hrms-h02-travel-requests-contract.json     [3.3 KB]  Travel Requests list columns, filters
hrms-h02-attendance-records-contract.json  [3.9 KB]  Attendance Records list columns, filters, source/state enums
hrms-h02-performance-reviews-contract.json [3.5 KB]  Performance Reviews list columns, filters
hrms-h02-documents-contract.json           [3.6 KB]  Documents list columns, filters
```

### H03 Detail Contracts [8 files, 3.2–9.0 KB each]
```
hrms-h03-employee-profile-contract.json        [8.9 KB]  Employee Profile tabs, fields, compensation, leave, performance
hrms-h03-department-detail-contract.json       [3.7 KB]  Department Detail tabs, members, sub-departments
hrms-h03-role-detail-contract.json             [3.2 KB]  Role Detail tabs, employees-in-role
hrms-h03-job-posting-detail-contract.json      [4.4 KB]  Job Posting Detail tabs, candidates, interviews
hrms-h03-leave-request-detail-contract.json    [4.0 KB]  Leave Request Detail fields, approval history
hrms-h03-payroll-record-detail-contract.json   [3.2 KB]  Payroll Record Detail earnings breakdown, status history
hrms-h03-expense-claim-detail-contract.json    [4.6 KB]  Expense Claim Detail line items, attachments, approval trail
hrms-h03-performance-review-detail-contract.json [7.0 KB] Performance Review Detail goals, calibration, PIP
```

### H04 Form Contracts [9 files, 2.9–9.2 KB each]
```
hrms-h04-add-employee-contract.json        [9.0 KB]  Add Employee 6-step form fields, validation, access provisioning
hrms-h04-edit-employee-contract.json       [9.2 KB]  Edit Employee section tabs, editable fields
hrms-h04-create-department-contract.json   [3.9 KB]  Create Department form fields
hrms-h04-create-role-contract.json         [3.4 KB]  Create Role form fields
hrms-h04-create-job-posting-contract.json  [7.3 KB]  Create Job Posting 4-step form: details/requirements/pipeline/publish
hrms-h04-raise-leave-request-contract.json [3.0 KB]  Raise Leave Request form fields and validation
hrms-h04-raise-expense-claim-contract.json [2.9 KB]  Raise Expense Claim form fields and receipt attachment
hrms-h04-raise-travel-request-contract.json [3.3 KB] Raise Travel Request form fields
hrms-h04-salary-revision-contract.json    [3.9 KB]  Salary Revision form with band selection and effective date
```

### H05–H13 Contracts [14 files]
```
hrms-h05-approval-inbox-contract.json     [12.5 KB]  Approval Inbox workflow types, detail panel, action bar
hrms-h07-hr-analytics-contract.json       [9.4 KB]   HR Analytics tabs, chart data, saved reports
hrms-h07-payroll-reports-contract.json    [6.9 KB]   Payroll Reports tabs, period selectors (NOT in manifest — audit gap)
hrms-h07-attendance-summary-contract.json [8.2 KB]   Attendance Summary tabs, aggregate dimensions
hrms-h07-engagement-results-contract.json [7.2 KB]   Engagement Results D1-D5 dimensions, participation metrics
hrms-h07-compliance-reports-contract.json [7.2 KB]   Compliance Reports document/task/expiry tabs
hrms-h08-global-search-contract.json      [5.3 KB]   Global Search facets, result card fields, entity types
hrms-h09-notifications-inbox-contract.json [5.3 KB]  Notifications Inbox folders, topic_codes, message structure
hrms-h10-org-settings-contract.json       [9.2 KB]   Org Settings sections, leave policies, payroll config, roles
hrms-h11-workflow-builder-contract.json   [6.0 KB]   Workflow Builder canvas sections, palette components, chrome flags
hrms-h11-survey-builder-contract.json     [6.7 KB]   Survey Builder dimensions, question types, lifecycle actions
hrms-h11-report-builder-contract.json     [8.2 KB]   Report Builder 8 report types, schedule, delivery chrome
hrms-h12-helpdesk-contract.json           [8.5 KB]   Helpdesk ticket list, detail panel, workflow actions, chrome gaps
hrms-h13-candidate-pipeline-contract.json [8.5 KB]   Candidate Pipeline kanban stages, slide panel, stat strip
```
**Note:** No H06 contracts exist (leave-calendar, attendance-timeline, shift-roster have no contracts — audit gap BG noted).

---

## CATEGORY 18 — BACKEND PYTHON — CORE SERVICE IMPLEMENTATIONS
**Location:** `backend/` (root level .py files)
The main Python service implementations. Each file is a self-contained domain service with models, business logic, and in-memory persistence via `PersistentKVStore`. All use `outbox_system.py` for events, `resilience.py` for error handling, and `audit_service` for write auditing.

### `payroll_service.py` [114.9 KB]
**Purpose:** Core payroll service — salary computation, tax routing via country adapter, payroll lifecycle, and disbursement gate.
**Description:** Imports CountryResolver, PayrollGuardian, WorkflowService, ComplianceAutopilot. Implements PayrollService with full `DRAFT→PROCESSED→PAID→CANCELLED` lifecycle. Orchestrates: base salary + allowances + deductions + attendance/leave inputs → country_adapter.apply_rules() → country_adapter.calculate_tax() → net pay. Blocks mark_paid() if compliance gate not passed (S3). The largest single file in the repo (114.9 KB). Role enum: Admin/Manager/Employee/PayrollAdmin.
**When:** Ground truth for payroll calculation logic and field shapes used in H02/H03/H07 payroll pages.

### `leave_service.py` [73.7 KB]
**Purpose:** Leave request lifecycle management — submission, approval/rejection, balance tracking, calendar events.
**Description:** Imports NotificationService, WorkflowService, audit_service. Implements LeaveService with `DRAFT→SUBMITTED→APPROVED/REJECTED/CANCELLED` lifecycle. Enums: LeaveType (Annual/Sick/Casual/Unpaid/Other), LeaveStatus. Policy validation (overlap, entitlement, notice period). Balance tracking. Private `_balances_for_employee()` — no HTTP exposure (BG-006). Holiday calendar support. 73.7 KB.
**When:** Ground truth for leave field shapes, enum values, and balance calculation logic used in H02/H03/H04/H06 leave pages.

### `notification_service.py` [56.4 KB]
**Purpose:** Notification queuing, template rendering, multi-channel delivery, and preference management.
**Description:** Imports EventRegistry, api_contract, resilience. Implements NotificationService. Channels: Email/SMS/Push/InApp. Template rendering with variable substitution. Preference-based channel filtering. DeadLetterQueue for failed deliveries. `ingest_event()` for event-driven notifications. `CANONICAL_TOPIC_CODES` registry. 56.4 KB.
**When:** When auditing which notification events wire to which H09 inbox topics.

### `workflow_service.py` [37.4 KB]
**Purpose:** Centralized workflow engine — approval instance lifecycle, inbox management, delegation, escalation.
**Description:** Imports NotificationService, EventRegistry, workflow_contract. WorkflowService implements: `create_instance()`, `get_instance()`, `get_inbox()`, `approve_step()`, `reject_step()`, `delegate_step()`, `escalate()`. State machine: Pending→Approved/Rejected/Delegated/Escalated/Cancelled. `ensure_workflow_contract()` validation. Multi-step approval chains. 37.4 KB.
**When:** When auditing H05 Approval Inbox workflow state mapping.

### `search_service.py` [40.2 KB]
**Purpose:** Cross-domain projection-backed search — employee, candidate, and document indexing and querying.
**Description:** Imports PersistentKVStore, EventRegistry, resilience. Implements SearchIndexingService and SearchQueryService. `SearchDocument` dataclass with metadata dict. `_employee_documents()`, `_candidate_documents()`, `_document_documents()` builders. Keyword list from name+role+department. `global_search_view` projection. BG-021 noted: no salary/location/skills in search index. 40.2 KB.
**When:** Ground truth for H08 Global Search field shapes and keyword matching behavior.

### `reporting_analytics.py` [43.2 KB]
**Purpose:** Aggregation and analytics service — headcount, payroll summary, attendance trends, compliance status, anomaly signals.
**Description:** Imports EventRegistry, PersistentKVStore. `ReportingAnalyticsService` with REPORT_TYPES dict. Endpoints backed by: workforce projections, attendance_dashboard_view, payroll_summary_view. InsightEngine integration for anomaly feeds. BG-018/019: payroll and performance not integrated. AnalyticsProjection dataclass. 43.2 KB.
**When:** Ground truth for H07 analytics pages — what data is actually aggregatable vs. mocked.

### `project_service.py` [45.5 KB]
**Purpose:** Project staffing service — project lifecycle, employee allocation, 100% allocation cap enforcement, append-only ledger, and optional workflow-service approval routing.
**Description:** Imports WorkflowService, NotificationService, EventOutbox, EventRegistry, audit_service, PersistentKVStore, resilience, tenant_support, workflow_support. `ProjectService` with: `Project` (PROJECT_STATUSES: Draft/Planned/Active/OnHold/Completed/Cancelled), `ProjectAssignment` (ASSIGNMENT_STATUSES: PendingApproval/Allocated/Rejected/Released), `AllocationLedgerEntry`, `EmployeeSnapshot` cache. Domain rules: 100% allocation cap across active assignments per employee, append-only ledger for audit/reporting, tenant-scoped optional approval routing via workflow-service. Events published: 7 (ProjectCreated, ProjectStatusChanged, ProjectAssignmentRequested, ProjectAssignmentAllocated, ProjectAssignmentRejected, ProjectAssignmentReleased, ProjectAllocationUpdated). 45.5 KB.
**When:** Ground truth for project staffing logic and allocation cap enforcement used in G28j (`/app/projects`); when auditing the project-service event contract (G49 scope).

### `engagement_service.py` [32.8 KB]
**Purpose:** Employee engagement surveys — creation, question management, response capture, D1-D5 dimension aggregation.
**Description:** Imports audit_service, EventRegistry, resilience. `EngagementService` with SURVEY_STATUSES, QUESTION_KINDS (only Likert5 — BG-030), DIMENSIONS (D1-D5). AggregatedSurveyResult with participation_rate, overall_average_score, favorable_ratio, question_scores[], dimension_scores[]. `publish()` / `close()` lifecycle. 32.8 KB.
**When:** Ground truth for H07 Engagement Results and H11 Survey Builder data shapes.

### `expense_service.py` [33.3 KB]
**Purpose:** Expense claim lifecycle — draft, submission, approval, rejection, reimbursement, receipt attachment.
**Description:** Imports audit_service, EventRegistry, event_outbox. `ExpenseService` with CLAIM_STATUSES (Draft/Submitted/Approved/Rejected/Reimbursed), EXPENSE_CATEGORIES. Receipt attachment management. Category-level policy validation. Accounting export flag. 33.3 KB.
**When:** Ground truth for H02/H03/H04 expense pages.

### `integration_service.py` [31.6 KB]
**Purpose:** Outbound webhook management — endpoint registration, event fan-out delivery, retry, dead-letter, replay.
**Description:** `IntegrationService` with WebhookEndpoint, WebhookDelivery, WebhookDeliveryAttempt dataclasses. HMAC-SHA256 signing. Delivery retry with backoff. Dead-letter tracking. Event subscription fan-out. Replay capability. 31.6 KB.
**When:** When auditing H10 Integrations section (currently chrome-only BG-026).

### `travel_service.py` [29.2 KB]
**Purpose:** Travel request lifecycle — draft, submission, approval, itinerary management, cancellation, completion.
**Description:** Imports NotificationService, audit_service. `TravelService` with `DRAFT→SUBMITTED→APPROVED→BOOKED→COMPLETED` + REJECTED/CANCELLED. TravelRequest and TravelItinerarySegment (Flight/Rail/Hotel/Car/Other segments). Trip types: OneWay/RoundTrip/MultiCity. 29.2 KB.
**When:** Ground truth for H02/H03/H04 travel request pages.

### `performance_service.py` [48.1 KB]
**Purpose:** Performance management — review cycles, OKR goals, 360 feedback, calibration sessions, PIP plans.
**Description:** Imports WorkflowService, NotificationService, audit_service. `PerformanceService` with ReviewCycle, Goal, Feedback, CalibrationSession, PipPlan dataclasses. Full approval workflows for each entity. PIP milestone tracking. 48.1 KB.
**When:** Ground truth for H02/H03 performance pages and H07 Performance analytics stub.

### `helpdesk_service.py` [45.4 KB]
**Purpose:** HR helpdesk ticket management — creation, routing, SLA tracking, comments, knowledge base.
**Description:** Imports NotificationService, audit_service. `HelpdeskService` with TICKET_STATUSES (Draft/Open/InProgress/Resolved/Closed), PRIORITIES, TicketComment, KnowledgeBaseArticle. SLA timer management (pauses on PENDING_EMPLOYEE). Resolution notes required. 45.4 KB. NOTE: service exposes `PATCH /tickets/{id}` per service-map.md but hrms-ui-backend-gaps BG-032 logs this as missing.
**When:** Ground truth for H12 Helpdesk page data shapes.

### `bank_service.py` [18.4 KB]
**Purpose:** Salary disbursement and banking — bank file generation, Raast payout, payment tracking, reconciliation.
**Description:** Imports CountryResolver (via country.base.banking_interface.BankingInterface). `BankService` with DisbursementBatch, PaymentRecord, ReconciliationReport. Lifecycle: PENDING→GENERATED→SUBMITTED→CONFIRMED→RECONCILED + FAILED→RETRY. CNIC match validation for Raast. Reconciliation exception flagging. 18.4 KB.
**When:** When auditing banking disbursement flows not in current UI.

### `automation_service.py` [16.6 KB]
**Purpose:** Automation rule engine — event/schedule/threshold triggers with cross-service action dispatch.
**Description:** `AutomationService` with AutomationRule, AutomationExecution, AutomationExecutionLog. Trigger types: event_triggered, schedule_triggered, threshold_triggered. Condition evaluation. Action dispatch via api_call/event_emit/notification. 16.6 KB.
**When:** When auditing how background automations trigger payroll/SLA escalation actions.

### `whatsapp_service.py` [11.4 KB]
**Purpose:** WhatsApp identity mapping, session management, and outbound message dispatch.
**Description:** Imports PersistentKVStore. `WhatsAppService` with identity mapping (phone↔employee), OTP verification, session state machine (15min timeout), outbound send. WhatsAppIdentityMap, WhatsAppSession, WhatsAppConversationEvent dataclasses. 11.4 KB.
**When:** Ground truth for WhatsApp service identity/session layer.

### `workflow_support.py` [2.9 KB]
**Purpose:** Shared workflow helper utilities — terminal result assertion and action resolution for domain services.
**Description:** `require_terminal_workflow_result()` validates that a workflow step has reached a terminal state before a domain service applies its side effect. `resolve_workflow_action()` maps workflow outcome to domain action. Used by payroll_service, leave_service, hiring_service. 2.9 KB.
**When:** When auditing how domain services integrate with workflow-service approval gates.

### `supervisor_engine.py` [35.3 KB]
**Purpose:** Infrastructure incident supervisor — health monitoring, recovery hooks, background job supervision.
**Description:** `SupervisorEngine` monitors service health, detects incidents, executes recovery hooks, and escalates unresolvable failures. Integrates with background_jobs.py for health polling. Does not own business logic. Gated by environment for production safety. 35.3 KB. Documented in `docs/services/automation-service.md §Sub-module: SupervisorEngine`.
**When:** When debugging why a background job or service recovery didn't execute.

### `data_integrity.py` [35.7 KB]
**Purpose:** Cross-service data integrity validator — cross-domain consistency checks across 8 dimensions.
**Description:** Imports AuditService, BackgroundJobService, ReportingAnalyticsService, SearchIndexingService. `DataIntegrityValidator` with `IntegrityIssue` dataclass. Validates: employee/org integrity, leave balance consistency, payroll cycle correctness, candidate-to-employee handoff, workflow/business-state alignment, projection drift, tenant ownership, audit/event alignment. Part of Tier 4 QC suite. 35.7 KB.
**When:** When running QC validation suite (Tier 4); when debugging cross-service data inconsistencies.

### `chaos_engine.py` [24.7 KB]
**Purpose:** Fault injection and chaos testing framework — controlled failure simulation for resilience validation.
**Description:** `ChaosEngine` injects controlled failures (latency, errors, service unavailability, cascade) via `ChaosProfile` config. Tests: service downtime, cascading failures, event delivery failures, job queue saturation, workflow timeout. **NEVER active in production** — gated by environment flag. Uses supervisor/resilience/jobs/outbox subsystems. 24.7 KB.
**When:** Only in test/staging environments; when adding new services that need chaos-test coverage.

### `resilience.py` [24.1 KB]
**Purpose:** Resilience patterns library — CircuitBreaker, RetryPolicy, Bulkhead, trace IDs, DLQ.
**Description:** `CircuitBreaker` (opens after N failures, half-opens on probe). `RetryPolicy` (exponential backoff with jitter). `Bulkhead` (concurrency limits per dependency). `new_trace_id()`. `Observability` context manager. `CentralErrorLogger`. `DeadLetterQueue`. `IdempotencyStore`. Imported by all service API modules. 24.1 KB.
**When:** When debugging circuit-breaker trips or retry exhaustion; when adding new external service calls.

### `background_jobs.py` [27.4 KB]
**Purpose:** Background job scheduler and executor — cron-style and deferred jobs for domain services.
**Description:** `BackgroundJobService` with job registration, scheduling, execution, failure logging, and retry tracking. Job types: payroll.run, leave.balance.recompute, notification.dispatch, outbox.dispatch, workflow.escalation, search.reindex. Tenant context and trace IDs carried into every execution. 27.4 KB.
**When:** When debugging why a scheduled operation didn't run; when registering new background workloads.

### `outbox_system.py` [10.6 KB]
**Purpose:** Transactional outbox pattern — at-least-once event delivery via background relay.
**Description:** `OutboxManager` writes events to outbox store before acknowledging originating transaction. Background relay polls for undelivered events and dispatches to event bus. Guarantees at-least-once delivery (consumers must be idempotent). Used by every domain service for all canonical events. 10.6 KB.
**When:** When debugging missing or duplicate events; the single point of event dispatch for the entire system.

### `persistent_store.py` [6.8 KB]
**Purpose:** Thin persistence abstraction layer — common get/set/delete/list interface wrapping the underlying datastore.
**Description:** `PersistentKVStore` with generic get/set/delete/list operations. Used by all in-memory domain service implementations. Does not implement the DB driver — injected at startup. Enables service unit tests without a real database. 6.8 KB.
**When:** When adding new persistent entities to any service.

### `event_contract.py` [19.7 KB]
**Purpose:** Canonical event type registry and contract enforcement — PascalCase ↔ dot-notation mapping, envelope schema.
**Description:** `CANONICAL_EVENT_TYPES` dict mapping PascalCase event names (e.g. `EmployeeCreated`) to dot-delimited D2 event types (e.g. `employee.created`). `EventRegistry` context manager. `emit_canonical_event()`, `ensure_event_contract()`, `legacy_event_name_for()`. `EventContractError`. Source of truth for all event names used across services. 19.7 KB.
**When:** When adding new domain events — must register here before emitting.

### `error_registry.py` [10.8 KB]
**Purpose:** Central error code registry — maps every system error code to type, severity, resolution steps, and retry-safety.
**Description:** `_REGISTRY` dict mapping string error codes (e.g. `PAYROLL_EMPLOYEE_DATA_INCOMPLETE`) to descriptors with: type (validation/system/external_dependency), severity (critical/high/medium/low), resolution_steps (ordered list), retryable (bool). `get_error_descriptor()` accessor. `register_error()` for extensibility (SB-G03). 22 registered error codes. 10.8 KB.
**When:** When adding new error codes; when implementing error handling in a new service endpoint.

### `api_contract.py` [4.8 KB]
**Purpose:** Shared API envelope helpers — request context, response wrappers, and pagination builders for D1 standard compliance.
**Description:** `RequestContext` dataclass (request_id, tenant_id, actor, service). `success_response()`, `error_response()`, `pagination_payload()`, `list_payload()`. Centralizes D1 SCS envelope formatting so services don't inline it. Used by all API modules. 4.8 KB.
**When:** When adding a new endpoint — use these helpers instead of constructing envelopes manually.

### `workflow_contract.py` [11.9 KB]
**Purpose:** Workflow contract validator — ensures workflow instances, steps, and SLA durations conform to the canonical contract schema.
**Description:** `ensure_workflow_contract()` validates workflow payload against allowed statuses, step types, and ISO-8601 duration patterns. `_ALLOWED_WORKFLOW_STATUSES`, `_ALLOWED_STEP_TYPES`, `_ALLOWED_STEP_STATUSES`. Duration parsing (ISO-8601 `PTnHnMnS` and shorthand `nh nm ns`). Used by workflow_service and services that initiate workflow instances. 11.9 KB.
**When:** When adding new workflow step types or modifying the workflow schema.

### `automation_contract.py` [7.8 KB]
**Purpose:** Automation rule contract validator — validates automation trigger/condition/action schema.
**Description:** Validates AutomationRule payload: allowed trigger types (event/schedule/threshold), condition operators, action types (api_call/event_emit/notification). Schema enforcement for the automation service. 7.8 KB.
**When:** When adding new automation trigger types or action dispatchers.

### `event_outbox.py` [7.3 KB]
**Purpose:** Lightweight event outbox wrapper — convenience layer over OutboxManager for domain services.
**Description:** `EventOutbox` class wrapping `OutboxManager` with domain-service-friendly methods. Handles serialization and tenant context injection. Used by expense_service and other services that need a simpler outbox interface than the full OutboxManager. 7.3 KB.
**When:** An alternative to direct outbox_system usage; use when OutboxManager's full interface is not needed.

### `master_certification.py` [11.1 KB]
**Purpose:** Master certification QC script — validates system-wide architectural certification against P51 add-on convergence outputs.
**Description:** Uses `AddonConvergenceService`. `CertificationSnapshot` dataclass with: module_id, architecture_signature, duplicate_logic_count, extends_parity_module, automation_aligned_with_workflow, analytics_source, tenant_isolation_verified, audit_trail_present. Part of Tier 3 RE-QC suite. Called by `deployment/re_qc_validate_master_certification.py`. 11.1 KB.
**When:** Running the master certification RE-QC gate (Tier 3) after sessions.

### `addon_convergence.py` [10.3 KB]
**Purpose:** Add-on convergence validator — checks add-on modules against core platform canonical controls D1-D8.
**Description:** `AddonModule` dataclass. `AddonConvergenceService` validates: no duplication, no parallel logic, automation-to-workflow alignment, analytics-to-reporting consistency, tenant isolation. Used by master_certification.py and the P50/P51 convergence passes. 10.3 KB.
**When:** When adding new add-on services; referenced by Tier 3 RE-QC.

### `insight_engine.py` [5.6 KB]
**Purpose:** Explainable insight helper — structured insight objects with type, score, confidence, and evidence for AI surfaces.
**Description:** `ExplainableInsight` frozen dataclass (insight_type, summary, score, confidence, evidence list of (metric, value, expected) tuples). Used by reporting_analytics and decision_api to produce structured AI output conforming to the MASTER BEHAVIOR SPEC AI output format. 5.6 KB.
**When:** When building AI output surfaces in dashboards; the canonical shape for any "why" explanation.

### `tenant_support.py` [1.3 KB]
**Purpose:** Tenant isolation helpers — tenant ID normalization and access assertion.
**Description:** `DEFAULT_TENANT_ID`. `normalize_tenant_id()`. `assert_tenant_access()`. Imported by all domain services to enforce tenant scoping on every read/write operation. 1.3 KB.
**When:** When adding any new data query — all queries must pass through assert_tenant_access.

### `cost_planning_service.py` [3.3 KB]
**Purpose:** Workforce cost planning — headcount cost projections and budget modeling.
**Description:** Add-on service for projecting workforce cost based on headcount, salary bands, and benefits. Not an HTTP service — utility module consumed by analytics layer. 3.3 KB.
**When:** When auditing cost planning analytics features.

### `employee_ui.py` [5.8 KB]
**Purpose:** Employee portal UI module — employee-facing API surface for self-service actions.
**Description:** Provides employee-facing endpoints: profile view, payslip access, leave balance, leave application. Thin layer over domain services with employee-scope enforcement. 5.8 KB.
**When:** When building employee self-service page flows.

### `payroll_ui.py` [3.4 KB]
**Purpose:** Payroll admin UI module — simplified payroll admin surface for non-API-gateway scenarios.
**Description:** Thin presentation layer over payroll_service for payroll admin dashboards. 3.4 KB.
**When:** When auditing payroll admin UI capabilities separate from the full payroll API.

### `test_payroll_service.py` [16.2 KB]
**Purpose:** Root-level payroll service integration tests — standalone test file for core payroll calculation paths.
**Description:** Covers: gross/net pay calculation, tax routing via country adapter, deduction order, edge cases (zero salary, missing employee). Part of the broader test suite but lives at root alongside the main service file. 16.2 KB.
**When:** When debugging payroll calculation correctness.

---

## CATEGORY 19 — BACKEND PYTHON — API SURFACE LAYER
**Location:** `backend/` (root *_api.py files)
HTTP API modules — thin layers that parse requests, call domain services, and format D1-standard responses. Each pairs with a *_service.py file.

```
payroll_api.py         [7.5 KB]   Payroll HTTP endpoints: run, process, mark-paid, cancel, get/list records
leave_api.py           [6.9 KB]   Leave HTTP endpoints: create, submit, approve, reject, cancel, get, list
notification_api.py    [7.7 KB]   Notification HTTP endpoints: send, bulk-send, templates, preferences, delivery status
decision_api.py        [18.6 KB]  Decision service HTTP endpoints: cards, anomalies, scan, acknowledge/override/dismiss + check_payroll_gate()
compliance_api.py      [8.8 KB]   Compliance HTTP endpoints: submit, validate, generate, submit-to-authority, retry, report, audit
banking_api.py         [11.2 KB]  Banking HTTP endpoints: disbursements, execute, payments, reconcile, raast/payout, accounts
whatsapp_api.py        [7.7 KB]   WhatsApp HTTP endpoints: webhook, identity register/verify/revoke, send, conversations, sessions
automation_api.py      [3.4 KB]   Automation HTTP endpoints: create, enable/disable, delete, list, trigger, executions
engagement_api.py      [5.9 KB]   Engagement HTTP endpoints: surveys, publish/close, responses, aggregates
expense_api.py         [4.7 KB]   Expense HTTP endpoints: claims, submit, approve/reject/cancel, receipts, reports
helpdesk_api.py        [6.7 KB]   Helpdesk HTTP endpoints: tickets, assign/resolve/close/reopen, comments, categories, articles, SLA
performance_api.py     [9.7 KB]   Performance HTTP endpoints: review-cycles, goals, feedback, calibrations, PIPs
reporting_analytics_api.py [8.6 KB] Analytics HTTP endpoints: reports, headcount, payroll-summary, attendance-trends, compliance-status, turnover, anomalies, schedule
search_api.py          [4.7 KB]   Search HTTP endpoints: global search, employee/candidate/document search
project_api.py         [7.4 KB]   Project HTTP endpoints: projects, assignments, allocation, approve/reject/release
travel_api.py          [5.8 KB]   Travel HTTP endpoints: requests, submit, approve/reject, itinerary, cancel/complete
workflow_api.py        [3.8 KB]   Workflow HTTP endpoints: instance get, inbox, approve, reject, delegate, escalate
background_jobs_api.py [5.0 KB]   Background jobs HTTP endpoints: job status, manual trigger (internal only — not exposed via gateway)
integration_api.py     [4.8 KB]   Integration HTTP endpoints: webhooks register/update/delete/list, deliveries, replay
```

---

## CATEGORY 20 — BACKEND PYTHON — AI & DECISION LAYER
**Location:** `backend/services/ai/` and `services/decision_engine.py`, `services/governance/`

### `services/ai/payroll_guardian.py` [8.0 KB]
**Purpose:** AI Payroll Guardian — anomaly detection for salary spikes, overtime, missing deductions, ghost employees.
**Description:** `PayrollGuardian` class with configurable thresholds (`salary_spike_pct` default 20%, `overtime_ratio` default 1.5×, `ghost_inactivity_days` default 30). Methods: `detect_salary_spike()`, `detect_overtime_anomaly()`, `detect_missing_deductions()`, `detect_ghost_employee()`. Returns AnomalySignal dataclasses. Thresholds injectable per tenant (SB-G04).
**When:** Ground truth for anomaly detection logic shown in H01 HR Manager Dashboard AI bar and H07 analytics pages.

### `services/ai/anomaly_engine.py` [5.6 KB]
**Purpose:** Anomaly signal builder — structures evidence into the canonical AnomalySignal format with risk score and confidence.
**Description:** `AnomalySignal` frozen dataclass (anomaly_type, summary, evidence tuples, risk_score, confidence). `AnomalyEngine` aggregates signals from PayrollGuardian and other sources. `to_dict()` produces the canonical `why_flagged` JSON shape for Decision Cards.
**When:** When auditing how anomaly evidence is structured for display in Decision Card UI surfaces.

### `services/ai/hr_copilot.py` [4.2 KB]
**Purpose:** HR Q&A assistant — explainable answers to salary breakdown, leave balance, and tax questions with RBAC gating.
**Description:** `HRCopilot` with `AccessContext(actor_role)`. Supported queries: salary breakdown, leave balance, tax explanation. Role-gated (Admin/HR/Payroll/Manager). Returns structured explainable answers. RBAC enforced before any data access.
**When:** When building AI assistant features in manager dashboard or HR admin surfaces.

### `services/decision_engine.py` [11.9 KB]
**Purpose:** Decision Card engine — creates, updates, expires, and routes Decision Cards through their lifecycle.
**Description:** `DecisionSeverity` enum (critical/notify/passive). `DecisionCard` dataclass with all 15 fields from `docs/canon/decision-system.md`. `DecisionEngine` with `create_card()`, `update_card()`, `expire_card()`. Routes to `GovernanceService` for human-in-loop enforcement on critical cards.
**When:** Ground truth for Decision Card lifecycle and field shapes shown in manager dashboard and decision center UI.

### `services/governance/service.py` [3.7 KB]
**Purpose:** Human-in-loop governance service — enforces mandatory review gates for critical AI decisions.
**Description:** `GovernanceService` with `GovernanceAction` dataclass. `require_review()` blocks action execution until a governance action (acknowledge/override/dismiss) is recorded. `record_action()` logs the governance decision with actor, timestamp, and rationale. Enforces S8 success criterion.
**When:** When auditing how High-risk Decision Cards block payroll approval (S8 gate).

### `services/analytics/predictive.py` [7.3 KB]
**Purpose:** Predictive workforce analytics — attrition risk, payroll cost forecast, overtime escalation, leave liability models.
**Description:** `PredictiveAnalyticsService` aligned to `docs/canon/decision-system.md`. Methods: `predict_attrition_risk()`, `forecast_payroll_cost()`, `predict_overtime_escalation()`, `project_leave_liability()`. All return `ExplainableInsight` objects with score/confidence/evidence. `_clamp()` utility.
**When:** When auditing predictive insight data shown in H07 analytics pages.

### `services/analytics/workforce.py` [8.6 KB]
**Purpose:** Operational workforce analytics — headcount, turnover, attendance trends, hiring funnel aggregations.
**Description:** `WorkforceAnalyticsService` with methods for: headcount snapshot, turnover rate calculation, attendance trend aggregation, hiring funnel summary. Reads from read models only. Used by reporting_analytics.py.
**When:** When auditing which H07 analytics tabs are data-driven vs. mocked.

### `services/compliance_autopilot.py` [1.5 KB]
**Purpose:** Compliance autopilot stub — routes compliance validation trigger to ComplianceService.
**Description:** Thin delegation layer imported by payroll_service.py to trigger compliance validation before payroll finalization. Keeps payroll_service from directly importing compliance_service (separation of concerns). 1.5 KB.
**When:** When auditing how the compliance gate is triggered during payroll processing.

### `services/compliance_service.py` [19.2 KB]
**Purpose:** Country-agnostic compliance service — full `DRAFT→VALIDATED→SUBMITTED→ACK→FAILED→RETRY` lifecycle.
**Description:** Full compliance service implementation (G02 fix) replacing the original 3-line Pakistan-hardcoded stub. Delegates country-specific validation and report generation to `CountryResolver → ComplianceEngineInterface`. Maintains immutable submission state machine. 9 endpoints implemented.
**When:** Ground truth for compliance submission logic and state transitions.

---

## CATEGORY 21 — BACKEND PYTHON — INFRASTRUCTURE & SHARED
**Location:** `backend/` (shared utility modules)

```
background_jobs.py  [27.4 KB]  (see Category 18)
resilience.py       [24.1 KB]  (see Category 18)
outbox_system.py    [10.6 KB]  (see Category 18)
persistent_store.py [6.8 KB]   (see Category 18)
event_contract.py   [19.7 KB]  (see Category 18)
error_registry.py   [10.8 KB]  (see Category 18)
api_contract.py     [4.8 KB]   (see Category 18)
workflow_contract.py [11.9 KB] (see Category 18)
automation_contract.py [7.8 KB] (see Category 18)
tenant_support.py   [1.3 KB]   (see Category 18)
```

### `audit_service/service.py` [8.2 KB]
**Purpose:** Immutable audit log service — records every privileged write, approval, and access-change with full actor/action/entity context.
**Description:** `AuditService` with `emit_audit_record()` function imported by all domain services. Records: actor, action, affected_entities, result, timestamp, trace_id. JSON serializable with Decimal/date/Enum handling. File-backed persistence with thread lock. Per S5 success criterion.
**When:** When verifying audit trail completeness; when adding new audit-worthy operations.

### `audit_service/api.py` [1.6 KB]
**Purpose:** Audit service HTTP surface — query endpoint for audit log retrieval.
**Description:** Single endpoint: `GET /api/v1/audit?entity_id=&action_type=&actor=&limit=&cursor=`. Returns paginated audit records. Admin-only capability.
**When:** When auditing the audit trail query surface.

### `audit_service/__init__.py` [0.2 KB]
**Purpose:** Audit service package init — exports AuditService.

---

## CATEGORY 22 — BACKEND COUNTRY ADAPTERS
**Location:** `backend/country/`

### `country/base/` — Interface definitions
```
country/base/__init__.py      [0.6 KB]  Package init — exports base interfaces
country/base/tax_engine.py    [0.3 KB]  TaxEngineInterface ABC: calculate_tax(input) → {tax_amount}
country/base/compliance_engine.py [0.5 KB] ComplianceEngineInterface ABC: validate_payroll() + generate_reports()
country/base/payroll_rules.py [0.3 KB]  PayrollRulesInterface ABC: apply_rules(input) → {adjusted_gross, rule_adjustments, final_deductions}
country/base/banking_interface.py [1.2 KB] BankingInterface ABC: generate_disbursement_file() + execute_payout()
country/base/statutory_validator.py [2.2 KB] StatutoryValidator base — common validation utilities for statutory compliance checks
```

### `country/pakistan/` — Pakistan reference implementation
```
country/pakistan/__init__.py  [0.7 KB]  Package init — exports PakistanAdapter (tax + compliance + payroll rules)
country/pakistan/tax_engine.py [1.0 KB] Pakistan tax engine — FBR income tax slabs, filer/non-filer routing
country/pakistan/payroll_rules.py [4.9 KB] Pakistan payroll rules — exempt allowances, EOBI/PESSI, WPPF/WWF, min wage, overtime 2×
country/pakistan/statutory.py [28.8 KB] Pakistan statutory engine — full FBR Annexure-C, EOBI PR-01, PESSI/SESSI, gratuity, provident fund, ATL filer check, Finance Act 2023/2024 surcharge (G33-G42 all implemented)
country/pakistan/compliance_engine.py [0.5 KB] Pakistan compliance engine — delegates to statutory.py via ComplianceEngineInterface
country/pakistan/banking.py   [1.1 KB]  Pakistan banking adapter — Raast payout routing and bank file format selection
```

### `country/dummy/` — Architecture proof adapter
```
country/dummy/__init__.py     [0.9 KB]  Package init — exports DummyAdapter (all interfaces, no-op implementations)
country/dummy/tax_engine.py   [0.4 KB]  Dummy tax engine — returns 0 tax; proves new country = adapter only
country/dummy/payroll_rules.py [0.4 KB] Dummy payroll rules — pass-through; no adjustments
country/dummy/compliance_engine.py [0.5 KB] Dummy compliance engine — always validates; no report generation
country/dummy/statutory_validator.py [0.7 KB] Dummy statutory validator — no-op; confirms interface conformance
country/dummy/banking.py      [0.9 KB]  Dummy banking adapter — no-op disbursement; proves architecture
```

### `core/country_resolver.py` [4.5 KB]
**Purpose:** Country adapter resolver — maps organization ID to country code to adapter instance.
**Description:** `CountryResolver` with `register_adapter()`, `register_mapping()`, `list_mappings()`, `resolve(org_id) → adapter`. `seed_dev_defaults()` for test/dev. Error codes: `ORG_COUNTRY_NOT_FOUND`, `COUNTRY_ADAPTER_NOT_REGISTERED`. Data-driven (G01 fix — no hardcoded Pakistan default). 4.5 KB.
**When:** The single point of country resolution for all domain services — critical for the P5 architecture principle.

---

## CATEGORY 23 — BACKEND INTEGRATION ADAPTERS
**Location:** `backend/integrations/`

### `integrations/pakistan/` — Pakistan government and banking integrations
```
integrations/pakistan/__init__.py  [0 KB]    Package init
integrations/pakistan/fbr_adapter.py    [7.8 KB]  FBR Annexure-C submission adapter: HMAC signing, payload validation, submission tracking, retry
integrations/pakistan/eobi_adapter.py   [4.9 KB]  EOBI PR-01 contribution submission adapter: contribution calculation, batch submission
integrations/pakistan/pessi_adapter.py  [4.5 KB]  PESSI/SESSI returns submission adapter: province-aware routing (Punjab/Sindh/KP/Balochistan)
integrations/pakistan/raast_payment.py  [3.3 KB]  Raast instant payment adapter: mobile/IBAN validation, SBP API integration, payment tracking
integrations/pakistan/bank_salary.py    [4.5 KB]  Bank salary file generator: bank-specific file formats (Habib Bank, MCB, etc.) for batch disbursement
integrations/pakistan/atl_adapter.py    [3.9 KB]  FBR ATL (Active Taxpayer List) verification adapter: CNIC-based filer status verification with 30-day cache (G42)
integrations/pakistan/payment_reconciliation.py [3.3 KB] Payment reconciliation engine: matches bank confirmations against disbursement records, flags discrepancies
integrations/pakistan/submission_tracking.py [6.5 KB] Statutory submission tracker: records submission attempts, states (DRAFT→ACK→FAILED→RETRY), audit trail per submission
```

### `integrations/accounting/` — Accounting system integrations
```
integrations/accounting/__init__.py [0 KB]   Package init
integrations/accounting/base.py     [5.1 KB] QuickBooksAdapter + SAPAdapter: payroll journal export, OAuth/OData, normalize PayrollPaid event to journal entries
```

### `integrations/biometric/` — Biometric device integration
```
integrations/biometric/__init__.py  [0 KB]   Package init
integrations/biometric/device_adapter.py [2.0 KB] Biometric device adapter: fingerprint/card reader data ingest, normalizes raw punch records to AttendanceRecord format
```

### `integrations/whatsapp/` — WhatsApp Business API integration
```
integrations/whatsapp/__init__.py   [0 KB]   Package init
integrations/whatsapp/webhook.py    [6.9 KB] WhatsApp webhook handler: inbound payload validation, intent parsing (payslip/leave/approval), CommandRegistry, OTP/session routing
```

### `integrations/http_client.py` [2.9 KB]
**Purpose:** HTTP client utility — shared JsonHTTPClient with RetryPolicy for all external API calls.
**Description:** `JsonHTTPClient` wraps requests with retry/timeout. `RetryPolicy` configures attempt counts, backoff. `IntegrationHTTPError` for provider-side failures. Used by all Pakistan integration adapters.

### `config/integrations.py` [1.6 KB]
**Purpose:** Integration configuration loader — loads FBR/EOBI/PESSI/QuickBooks/SAP config from environment.
**Description:** `load_integrations_config()` returns structured config dict read from env vars/config files. Single injection point for all external integration credentials.

---

## CATEGORY 24 — BACKEND TYPESCRIPT — employee-service
**Location:** `backend/services/employee-service/`
The TypeScript service implementing employee lifecycle, organization structure, compensation, documents, contractors, and asset management. The primary source of truth for employee data shapes.

```
employee.model.ts         [6.5 KB]  EMPLOYMENT_TYPES, EMPLOYEE_STATUSES, CONTRACT_TYPES, DEPARTMENT_STATUSES, ROLE_STATUSES etc. — the canonical TypeScript enum definitions
employee.service.ts       [27.9 KB] EmployeeService: create, update, status-change, reporting-line, org assignment, matrix management
employee.controller.ts    [12.2 KB] HTTP controller: POST/PATCH/GET /employees endpoints with RBAC middleware
employee.repository.ts    [31.5 KB] PersistentMap-backed employee repository: tenant-scoped CRUD, filtering, cursor pagination
employee.routes.ts        [21.5 KB] Express route definitions: all /employees and /departments and /roles routes wired to controllers
employee.validation.ts    [11.8 KB] Zod schemas: CreateEmployeeInput, UpdateEmployeeInput, org assignment validation
department.model.ts       [1.0 KB]  DepartmentStatus enum, Department interface
department.service.ts     [6.3 KB]  DepartmentService: create, update, list, head assignment
department.controller.ts  [7.2 KB]  HTTP controller for /departments endpoints
department.repository.ts  [12.8 KB] PersistentMap-backed department repository
department.validation.ts  [3.2 KB]  Zod schemas for department create/update
role.model.ts             [2.3 KB]  RoleStatus, EmploymentCategory enums, Role interface
role.service.ts           [3.3 KB]  RoleService: create, update, list
role.controller.ts        [4.8 KB]  HTTP controller for /roles endpoints
role.repository.ts        [10.8 KB] PersistentMap-backed role repository
role.validation.ts        [3.4 KB]  Zod schemas for role create/update
org.model.ts              [5.3 KB]  BusinessUnit, LegalEntity, Location, CostCenter, GradeBand, JobPosition models and status enums
org.service.ts            [15.6 KB] OrgService: CRUD for all org entity types (business_unit/legal_entity/location/cost_center/grade_band/job_position)
org.controller.ts         [10.7 KB] HTTP controller for /org/{kind} routes
org.repository.ts         [18.0 KB] PersistentMap-backed org entity repository (multi-kind)
org.validation.ts         [10.4 KB] Zod schemas for each org entity kind
compensation.model.ts     [8.7 KB]  CompensationBand, SalaryRevision, BenefitsPlan, BenefitsEnrollment, Allowance models and status enums
compensation.service.ts   [24.0 KB] CompensationService: salary revision lifecycle, band management, benefits enrollment, allowance CRUD
compensation.controller.ts [14.2 KB] HTTP controller for /compensation endpoints
compensation.repository.ts [25.2 KB] PersistentMap-backed compensation repository (revision history, band lookup)
compensation.validation.ts [19.0 KB] Zod schemas for compensation create/update with effective-date and band validation
document-compliance.model.ts [4.1 KB] EmployeeDocument, PolicyAcknowledgement, ComplianceTask models and DOCUMENT_TYPES/STATUSES/TASK_TYPES/STATUSES enums
document-compliance.service.ts [20.1 KB] DocumentComplianceService: document CRUD, expiry tracking, acknowledgement, task lifecycle
document-compliance.controller.ts [10.9 KB] HTTP controller for document compliance endpoints
document-compliance.repository.ts [6.7 KB] PersistentMap-backed document compliance repository
contractor.controller.ts  [10.0 KB] HTTP controller for contractor management (IndependentContractor/Agency/StatementOfWork)
learning.model.ts         [4.1 KB]  Learning & development model: LearningEnrollment, LearningCourse
learning.service.ts       [19.6 KB] LearningService: course catalog, enrollment, completion tracking
learning.controller.ts    [11.2 KB] HTTP controller for learning endpoints
learning.repository.ts    [8.5 KB]  PersistentMap-backed learning repository
asset-management.model.ts [2.1 KB]  AssetAssignment model: asset tracking per employee
asset-management.service.ts [11.0 KB] AssetManagementService: issue, return, transfer, audit
asset-management.controller.ts [7.8 KB] HTTP controller for asset management endpoints
asset-management.repository.ts [4.9 KB] PersistentMap-backed asset management repository
rbac.middleware.ts        [12.1 KB] RBAC middleware: capability-based authorization enforcement for all employee-service routes
event-outbox.ts           [2.9 KB]  TypeScript event outbox: writes canonical employee events before acknowledging transactions
domain-seed.ts            [8.9 KB]  Domain seed data: test/dev employee, department, role, org entities
service.errors.ts         [0.1 KB]  Service error types
```

---

## CATEGORY 25 — BACKEND TYPESCRIPT — settings-service
**Location:** `backend/services/settings-service/`
```
settings.model.ts      [5.4 KB]  AttendanceRule, LeavePolicy, PayrollSettings models; PAY_SCHEDULES, LEAVE_POLICY_TYPES, ACCRUAL_FREQUENCIES, LEAVE_DEDUCTION_MODES enums — the canonical TypeScript settings model
settings.service.ts    [6.4 KB]  SettingsService: attendance rule CRUD, leave policy CRUD, payroll settings PUT
settings.controller.ts [5.8 KB]  HTTP controller for /settings endpoints
settings.repository.ts [17.2 KB] PersistentMap-backed settings repository with validation on write
settings.routes.ts     [2.7 KB]  Express route definitions for settings endpoints
settings.validation.ts [10.5 KB] Zod schemas for attendance rule, leave policy, payroll settings with cross-field validation
```

---

## CATEGORY 26 — BACKEND PYTHON — OTHER SERVICE MODULES
**Location:** `backend/services/` (subdirectory Python modules)

```
services/hiring_service/service.py [101.8 KB] Full hiring service: JobPosting, Candidate, Interview, stage transitions, Google Calendar sync, LinkedIn import, CandidateHired handoff. The largest service file.
services/hiring_service/api.py     [17.5 KB]  Hiring service HTTP API: all /hiring endpoints including candidate-pipeline, linkedin-import, mark-hired
services/hiring_service/__init__.py [1.0 KB]  Package init
services/auth-service/service.py   [42.9 KB]  Full auth service: UserAccount, RoleBinding, PermissionPolicy, Session, RefreshToken, JWT issuance, RBAC evaluation
services/auth-service/api.py       [14.0 KB]  Auth service HTTP API: login, refresh, logout, me, users, sessions, bindings, policies, access
services/auth-service/__init__.py  [0.2 KB]   Package init
services/attendance_service.py     [10.7 KB]  Attendance service layer (thin wrapper over attendance_service/ module, compute layer)
services/attendance/face_recognition.py [2.4 KB] Face recognition attendance capture: face-match biometric source adapter
services/attendance/__init__.py    [0.2 KB]   Package init
services/finance/ewa.py            [4.6 KB]   EWA and salary advance service: EWARequest, SalaryAdvance, eligibility check, repayment schedule, deduction injection
services/finance/__init__.py       [0.2 KB]   Package init
services/performance/insights.py   [4.2 KB]   Performance insights: goal completion rates, feedback sentiment, calibration stats
services/performance/__init__.py   [0.1 KB]   Package init
services/governance/service.py     [3.7 KB]   (see Category 20)
services/governance/__init__.py    [0.1 KB]   Package init
services/payroll/paas.py           [2.1 KB]   Payroll-as-a-Service mode: managed_payroll_mode, payroll_admin_override_controls, tier enforcement
services/payroll_policy_engine.py  [4.8 KB]   Payroll policy engine: policy rule evaluation, statutory threshold enforcement, per-tenant config
services/payroll_service.py        [7.6 KB]   Payroll computation service (pure math layer — gross/taxable/net/overtime — no HTTP/persistence)
services/recruitment/service.py    [7.3 KB]   CV parsing and candidate scoring utilities (NOT a duplicate of hiring_service — separate concern)
services/recruitment/__init__.py   [0.6 KB]   Package init
services/mobile_gateway.py         [7.7 KB]   MobileGatewayService: compact decision-card responses, cache layer, action dispatch for mobile clients
services/compliance_service.py     [19.2 KB]  (see Category 20)
services/compliance_autopilot.py   [1.5 KB]   (see Category 20)
services/decision_engine.py        [11.9 KB]  (see Category 20)
services/experience_layer_service.py [0.2 KB] Experience layer service stub: delegates to services/product/experience.py
services/product/experience.py     [2.8 KB]   Experience layer: SME Lite mode enforcement, PaaS mode, tier-based feature gating
services/product/tier_enforcer.py  [1.3 KB]   Tier enforcement: CORE/SME_LITE/ENTERPRISE feature flag evaluation
services/product/middleware.py     [0.4 KB]   Experience layer middleware: injects tier context into requests
services/product/__init__.py       [0.3 KB]   Package init
```

---

## CATEGORY 27 — ATTENDANCE SERVICE MODULE
**Location:** `backend/attendance_service/`
The attendance_service module (distinct from the root attendance_service.py):
```
attendance_service/service.py  [59.1 KB]  Full attendance service: record capture, shift management, overtime engine, exception resolution, period closure. Largest non-hiring service file.
attendance_service/api.py      [13.5 KB]  Attendance HTTP API: records CRUD, validate/approve, period lock, summaries, exceptions
attendance_service/models.py   [7.5 KB]   AttendanceRecord, AttendancePeriod, ShiftTemplate, AttendanceException models and enums (AttendanceStatus, RecordState, AttendanceSource, ScheduleStatus, CorrectionStatus)
attendance_service/ui.py       [4.2 KB]   Attendance UI surface: compact attendance views for employee self-service
attendance_service/__init__.py [1.1 KB]   Package init — exports AttendanceService
```

---

## CATEGORY 28 — BACKEND API GATEWAY
**Location:** `backend/api-gateway/`
```
api-gateway/routes.py          [4.4 KB]  Route registry: API_VERSION_PREFIX, Route dataclass, all /api/v1/* → upstream service mappings. Canonical route definitions aligned to service-map.md.
api-gateway/dashboard_ui.py    [5.4 KB]  Dashboard UI handler: renders HTML dashboard surface via api-gateway
api-gateway/load_control.py    [9.7 KB]  Load control: rate limiting, circuit breaker per route, load shedding under saturation
api-gateway/tenant.py          [2.5 KB]  Tenant context injection: extracts and validates tenant_id for all gateway-routed requests
api-gateway/README.md          [0.5 KB]  Route group overview (see `docs/deployment.md` for full gateway deployment context)
```

### `docs/deployment.md`
**Purpose:** Deployment architecture overview — full service roster, Docker runtime configuration, environment variables, and migration strategy for the AURA HRMS stack.
**Description:** Lists all 22 runtime services provisioned by the deployment layer (employee/attendance/leave/payroll/hiring/auth/notification/audit/workflow/performance/engagement/helpdesk/reporting-analytics/search/expense/integration/automation/travel/project/settings/api-gateway/frontend-ui) plus postgres and migrations job. Covers Docker Compose structure, environment variable requirements, and one-shot schema migration configuration.
**When:** When setting up a deployment environment; when verifying which services are containerized; when troubleshooting service startup or port conflicts.
**Upload:** ON-DEMAND

### `deployment/config/gateway-routes.json` [1.0 KB]
**Purpose:** Runtime gateway route configuration — maps domain names to service URLs and ports.
**Description:** JSON registry of 20 domain routes: employees/departments (→employee-service:8001), performance (→8010), attendance (→8002), leave (→8003), travel (→8018), projects (→8019), payroll (→8004), hiring (→8005), auth (→8006), workflows (→8009), audit (→8008), notifications (→8007), engagement (→8011), helpdesk (→8012), reporting (→8013), search (→8014), expense (→8015), integrations (→8016), automations (→8017), settings (→8020). Note: compliance/decision/banking/whatsapp routes not in this config — may route via gateway or direct.
**When:** When configuring docker-compose or verifying which service handles a given route.

### `docker/service_runtime.py` [21.2 KB]
**Purpose:** Service runtime — ASGI HTTP server implementation used by all service containers in Docker.
**Description:** Async ASGI `app` function using `asyncio.to_thread` for sync route dispatch. Implements: JSON request/response (`_build_response`), route matching (`_match`), error formatting, D1 envelope, health/ready endpoints. Structured JSON logging via `configure_logging()`. TLS activated by `SSL_CERT_FILE`/`SSL_KEY_FILE` env vars. Entry point: `uvicorn.run("service_runtime:app", ...)`. All Python services run via this runtime inside Docker containers.

### `docker/api_gateway_service.py` [~15 KB]
**Purpose:** API gateway Docker service — the runtime implementation of the gateway container.
**Description:** Async ASGI gateway. Features: route forwarding to upstream services via `urllib.request.urlopen`; circuit breaker (`resilience.CircuitBreaker`); sliding-window rate limiting (`SlidingWindowRateLimiter`, 200 req/min/IP, configurable via `GATEWAY_RATE_LIMIT`/`GATEWAY_RATE_WINDOW_SECONDS`); JWT enforcement (`verify_hs256_jwt` with ±5s clock-skew tolerance, skip auth/health/openapi/metrics routes, propagates `X-User-Id`/`X-User-Role`/`X-Tenant-Id` downstream); per-tenant RBAC (`_ROUTE_ROLE_MAP` path-prefix → allowed roles, cross-tenant `X-Tenant-Id` vs JWT `tenant_id` check, 403 on mismatch); request body size limit (`MAX_REQUEST_BODY_BYTES`, default 1 MB, enforced during ASGI streaming, 413 on overflow); idempotency key support (`_IdempotencyCache`, 24h TTL, 10k cap, LRU eviction, POST/PATCH/PUT replay with `X-Idempotent-Replayed: true`); JSON body validation (pre-forward `json.loads()` on `application/json`, 400 on parse error); W3C Trace Context (`_parse_traceparent`/`_new_traceparent`, child span forwarded to upstream, echoed in response); CORS headers on all responses (`OPTIONS` 204 preflight, configurable via `CORS_ALLOWED_ORIGINS`); Prometheus metrics at `GET /metrics` (thread-safe counters: `gateway_requests_total`, `gateway_request_duration_seconds_total`, `gateway_errors_total`); OpenAPI spec at `GET /openapi.json`; Swagger UI at `GET /docs`; structured JSON logging with `ContextVar` correlation IDs; TLS via `SSL_CERT_FILE`/`SSL_KEY_FILE`. Health at `/health`, readiness at `/ready`.

### `docker/common_service.py` [3.4 KB]
**Purpose:** Common service Docker base — shared startup and configuration loading for all service containers.

---

## CATEGORY 29 — BACKEND TESTS
**Location:** `backend/tests/`
80+ pytest test files. Last verified clean run: 281 passed (2026-03-31, pre-sessions 5-8). New code from sessions 5-8 has not been re-run (Tier 5 coverage gap register lists 15 known gaps).

```
Core domain tests:
  test_payroll_service.py             [see also root test_payroll_service.py]
  test_hiring_service.py          [26.4 KB]  Hiring lifecycle: job postings, candidates, stage transitions, interviews, hire handoff
  test_hiring_api.py              [9.4 KB]   Hiring HTTP API: endpoint contracts, request validation, response shapes
  test_leave_service.py           [11.7 KB]  Leave lifecycle: submission, approval, rejection, cancellation, overlap validation
  test_leave_api.py               [5.2 KB]   Leave HTTP API: endpoint contracts
  test_attendance_service.py      [28.8 KB]  Attendance capture, validation, period closure, exception handling
  test_payroll_api.py             [5.1 KB]   Payroll HTTP API: run, process, mark-paid endpoint contracts
  test_notification_service.py    [15.4 KB]  Notification queuing, template rendering, preference filtering, channel routing
  test_workflow_engine.py         [8.1 KB]   Workflow instance lifecycle, step approvals, delegation, escalation
  test_workflow_contract.py       [4.4 KB]   Workflow contract validation: duration parsing, step type enforcement
  test_engagement_service.py      [12.4 KB]  Survey creation, publication, response capture, D1-D5 aggregation
  test_expense_service.py         [7.5 KB]   Expense claim lifecycle, receipt attachment, policy validation
  test_integration_service.py     [9.8 KB]   Webhook registration, delivery, retry, dead-letter, replay
  test_helpdesk_service.py        [9.0 KB]   Helpdesk ticket lifecycle, SLA tracking, knowledge base
  test_helpdesk_api.py            [9.1 KB]   Helpdesk HTTP API: all endpoints
  test_reporting_analytics.py     [18.2 KB]  Analytics aggregation, report generation, anomaly signals
  test_search_service.py          [13.2 KB]  Search indexing, projection queries, entity type filtering
  test_automation_service.py      [9.1 KB]   Automation rule creation, trigger evaluation, action dispatch

Pakistan compliance tests:
  test_pakistan_compliance_service.py [5.2 KB]  Tax slab formula, FBR Annexure-C schema, EOBI/PESSI math, province routing
  test_pakistan_integrations.py   [10.7 KB]  FBR/EOBI/PESSI adapter submissions, Raast payout, bank salary file generation

Country architecture tests:
  test_country_resolver.py        [0.7 KB]   Resolver registration and adapter resolution
  test_country_resolver_dual_country.py [2.3 KB] Multi-country resolver: Pakistan + Dummy adapters simultaneously
  test_country_architecture_validation.py [4.3 KB] P5 enforcement: no country imports in core services

AI and decision tests:
  test_decision_engine.py         [4.1 KB]   Decision Card lifecycle, severity routing, expiry
  test_payroll_guardian.py        [1.7 KB]   Anomaly detection: spike/overtime/deduction/ghost thresholds
  test_anomaly_engine.py          [1.8 KB]   AnomalySignal structure and evidence formatting
  test_hr_copilot.py              [2.5 KB]   HR Q&A RBAC enforcement and answer structure
  test_governance_service.py      [3.0 KB]   Human-in-loop gate enforcement for critical decisions
  test_predictive_analytics.py    [1.7 KB]   Attrition risk, cost forecast, overtime probability models

Employee service tests:
  test_employee_service_domain.py [7.4 KB]   Employee lifecycle, org structure, reporting lines
  test_document_compliance_service.py [9.3 KB] Document CRUD, expiry tracking, compliance task lifecycle
  test_compensation_domain.py     [8.7 KB]   Salary revision, band validation, benefits enrollment
  test_contractor_management_domain.py [7.1 KB] Contractor types, contract lifecycle
  test_asset_management_service.py [9.3 KB]  Asset issue/return/transfer lifecycle
  test_learning_service.py        [10.1 KB]  Learning enrollment, completion, course catalog
  test_role_domain.py             [2.3 KB]   Role CRUD, employment category enforcement
  test_settings_domain.py         [8.7 KB]   AttendanceRule, LeavePolicy, PayrollSettings validation

Infrastructure and resilience tests:
  test_background_jobs.py         [11.2 KB]  Job scheduling, execution, failure logging, retry
  test_outbox_system.py           [3.2 KB]   At-least-once delivery, relay polling
  test_chaos_engine.py            [3.1 KB]   Fault injection scenarios, recovery assertions
  test_chaos_resilience_hardening.py [4.8 KB] Combined chaos + resilience validation
  test_failure_resilience.py      [7.9 KB]   Circuit breaker, retry, bulkhead under fault conditions
  test_supervisor_engine.py       [6.0 KB]   Infrastructure incident detection and recovery hooks
  test_audit_service.py           [14.1 KB]  Audit record emission, field completeness, immutability

Auth and security tests:
  test_auth_service.py            [13.8 KB]  Login, token issuance, session management, RBAC evaluation
  test_security_compliance_lock.py [0.6 KB]  Security compliance lock validation
  test_security_logging.py        [2.0 KB]   Sensitive field redaction in logs

Gateway and routing tests:
  test_api_gateway_routes.py      [3.5 KB]   Route registry completeness, canonical prefix enforcement
  test_api_gateway_proxy_forwarding.py [3.8 KB] End-to-end request forwarding through gateway
  test_gateway_runtime_alignment_e2e.py [7.1 KB] All declared public gateway routes executable
  test_gateway_load_control.py    [3.4 KB]   Rate limiting, circuit-breaker behavior under load
  test_gateway_tenant_context.py  [2.1 KB]   Tenant ID extraction and propagation
  test_gateway_api_standards.py   [1.8 KB]   D1 envelope conformance across all routes
  test_route_runtime_consistency.py [2.5 KB] Backward-compatibility aliases + canonical route parity

Data integrity and migration tests:
  test_data_integrity.py          [15.6 KB]  8-dimension cross-service integrity validation
  test_migration_schema.py        [8.1 KB]   SQL migration completeness and schema correctness
  test_backward_compatibility_enforcement.py [3.7 KB] Legacy route aliases, list response shape normalization

WhatsApp and mobile tests:
  test_whatsapp_webhook.py        [1.9 KB]   Inbound payload validation, intent parsing, command routing
  test_mobile_gateway.py          [4.6 KB]   Compact response format, severity ordering, action dispatch

QC and certification tests:
  test_master_certification.py    [2.6 KB]   P51 certification assertions
  test_addon_convergence.py       [4.8 KB]   P50 add-on convergence 10-dimension validation

Other domain tests:
  test_travel_domain.py           [6.6 KB]   Travel request lifecycle, itinerary segments
  test_travel_api.py              [6.3 KB]   Travel HTTP API endpoints
  test_project_service.py         [10.9 KB]  Project management, staffing assignments, allocation ledger
  test_performance_domain.py      [10.3 KB]  Review cycles, goals, feedback, calibration, PIP
  test_event_workflow_consistency.py [7.5 KB] Event-to-workflow state alignment across domains
  test_payroll_to_bank_happy_path.py [6.4 KB] End-to-end: payroll run → bank disbursement → reconciliation
  test_payroll_country_adapter_integration.py [2.7 KB] Payroll with Pakistan adapter: tax routing, rule application
  test_payroll_compensation_integration.py [1.4 KB] Payroll with compensation module: SalaryRevision input
  test_payroll_guardian.py        [1.7 KB]   (see AI tests above)
  test_experience_layer_service.py [3.9 KB]  SME Lite mode enforcement, tier gating, PaaS mode
  test_services_payroll_service.py [5.1 KB]  Pure payroll computation layer (services/payroll_service.py)
  test_services_attendance_service.py [3.4 KB] Attendance computation layer
  test_services_face_recognition_attendance.py [1.8 KB] Face recognition biometric capture
  test_recruitment_service.py     [3.4 KB]   CV parsing, candidate scoring utilities
  test_performance_insights_service.py [2.6 KB] Performance insights: goal completion, calibration stats
  test_workforce_analytics.py     [3.0 KB]   Operational workforce analytics
  test_insight_engine.py          [1.1 KB]   ExplainableInsight structure
  test_import_health.py           [1.8 KB]   All service modules importable without circular dependencies
  test_dashboard_ui.py            [3.9 KB]   Dashboard UI handler
  test_employee_portal_api.py     [2.2 KB]   Employee portal API
  test_employee_ui.py             [2.7 KB]   Employee UI surface
  test_payroll_ui.py              [1.7 KB]   Payroll UI surface
  test_attendance_ui.py           [2.8 KB]   Attendance UI surface
  test_service_runtime_employee.py [1.9 KB]  Service runtime for employee service
  test_governance_service.py      [3.0 KB]   (see AI tests above)

Unit test subdirectory (tests/unit/):
  test_attendance_api_standards.py [4.2 KB]  Attendance API D1 envelope conformance
  test_audit_logging_standard.py  [14.7 KB]  Audit field completeness across all domain operations
  test_observability_middleware_standard.py [0.7 KB] Observability middleware standard
  test_workflow_support_standard.py [1.9 KB] workflow_support.py contract standard

Deployment QC validators (deployment/):
  qc_validate.py              [3.0 KB]  Primary QC gate: 10-point deployment quality rubric (target 10/10)
  qc_validate_engagement.py   [2.9 KB]  Engagement service QC: survey/response/aggregate shape validation
  qc_validate_performance.py  [2.0 KB]  Performance service QC: review cycle/goal/PIP shape validation
  qc_validate_role_mapping.py [1.1 KB]  Role binding QC: RBAC role mapping correctness
  qc_validate_settings.py     [3.0 KB]  Settings service QC: leave policy/attendance rule/payroll settings validation
  re_qc_validate_addon_convergence.py   [1.7 KB] RE-QC: P50 add-on convergence gate (must pass 10/10)
  re_qc_validate_audit_service.py       [1.8 KB] RE-QC: audit service field completeness
  re_qc_validate_candidate_domain_integrity.py [2.0 KB] RE-QC: candidate-to-employee handoff integrity
  re_qc_validate_data_integrity.py      [1.7 KB] RE-QC: P29 data integrity gate (must pass 6/6)
  re_qc_validate_employee_domain_integrity.py [3.0 KB] RE-QC: employee domain completeness
  re_qc_validate_engagement_domain_integrity.py [1.6 KB] RE-QC: engagement domain integrity
  re_qc_validate_master_certification.py [2.2 KB] RE-QC: P51 master certification gate (must pass 5/5)
  re_qc_validate_performance_domain_integrity.py [2.2 KB] RE-QC: performance domain integrity
  re_qc_validate_role_integrity.py      [1.3 KB] RE-QC: role/RBAC integrity
  re_qc_validate_security_compliance_lock.py [6.1 KB] RE-QC: security compliance lock (sensitive field exposure, log-leaking)
  re_qc_validate_settings_domain_integrity.py [2.3 KB] RE-QC: settings domain integrity
  repair_data_integrity.py      [3.1 KB] Data integrity repair script: fixes known projection drift and tenant mismatch issues
  conftest.py (tests/)          [0.1 KB] Pytest configuration — minimal test fixtures
```

---

## CATEGORY 30 — DEPLOYMENT & CONFIGURATION
**Location:** `backend/`

### Docker and Compose
```
docker-compose.yml     [16.0 KB]  Full service topology: 22 containers (20 services + postgres + migrations). Postgres health checks, migration one-shot, all service ports.
Dockerfile             [0.2 KB]   Base Dockerfile (minimal Python image)
Dockerfile.api         [0.2 KB]   API gateway container: runs docker/api_gateway_service.py
Dockerfile.services    [0.4 KB]   Domain service containers: runs docker/service_runtime.py with service name env var
Dockerfile.ui          [0.1 KB]   Frontend UI container: serves static deployment/frontend/index.html
Dockerfile.render      [1.1 KB]   Render.com deployment variant: single-container with supervisor
start.sh               [1.8 KB]   All-in-one startup script: starts all services in-process (non-compose alternative for development)
.dockerignore          [0.1 KB]   Docker build context exclusions
```

### Deployment Config
```
deployment/config/gateway-routes.json [1.0 KB]  (see Category 28)
deployment/config/services.env        [0.9 KB]  Service environment variable defaults: DB credentials, JWT config, service URLs, tenant ID
deployment/config/postgres-init.sql  [0.1 KB]  PostgreSQL initialization: enables uuid-ossp extension
.env.example                          [0.7 KB]  Environment variable template: DB, JWT, service URLs, tenant ID, WhatsApp/FBR/Raast credentials
```

### Database Migrations (deployment/migrations/)
```
001_core_schema.sql         [4.8 KB]  Core tables: departments, business_units, legal_entities, locations, cost_centers, grade_bands, job_positions, roles, employees (with all FK constraints, indexes, CHECK constraints)
002_workflow_schema.sql     [22.1 KB] Workflow tables: workflow_definitions, workflow_instances, workflow_steps, workflow_audit_log, approval tables
003_centralized_workflow_engine.sql [3.5 KB] Centralized workflow engine tables: workflow_step_assignments, escalation tracking
004_persistence_normalization.sql [5.6 KB] Persistence normalization: tenant_id column additions, FK normalizations
005_tenant_foundation.sql   [1.4 KB]  Tenant foundation: tenant isolation constraints, row-level security setup
006_notification_service.sql [4.7 KB] Notification tables: templates, messages, delivery_attempts, notification_preferences
007_event_outbox.sql        [1.4 KB]  Event outbox table: aggregate/event/payload/trace/published_at columns
008_background_jobs_schema.sql [2.6 KB] Background jobs tables: job_definitions, job_executions, execution_log
009_audit_service.sql       [1.7 KB]  Audit log table: actor/action/affected_entities/result/trace_id with immutable append
010_engagement_service.sql  [4.3 KB]  Engagement tables: surveys, questions, responses, answers, aggregates
011_addon_domains.sql       [2.2 KB]  Add-on domain tables: expense_claims, helpdesk_tickets, travel_requests
012_compensation_domain.sql [8.6 KB]  Compensation tables: compensation_bands, salary_revisions, benefits_plans, benefits_enrollments, allowances
013_travel_domain.sql       [4.3 KB]  Travel tables: travel_requests (with tenant_id PK), travel_itinerary_segments
```

### Scripts and Frontend
```
deployment/scripts/run-migrations.sh [0.8 KB]  Migration runner: waits for postgres health, applies migrations in order
deployment/frontend/index.html       [0.4 KB]  Static frontend placeholder: served by Dockerfile.ui on port 3000
requirements.txt                      [0 KB]   Python requirements file (empty — dependencies managed via OS packages or implicit)
```

---

## CATEGORY 31 — BACKEND TYPESCRIPT — UI (Next.js)
**Location:** `backend/ui/`
A partial Next.js frontend implementation. Covers core HR modules but NOT the full 49-page Meridian HCM UI (those are in `frontend/pages/`). This is the backend repo's own React/TypeScript UI.

### App Pages (ui/app/)
```
page.tsx                     [0.1 KB]  Root page redirect
layout.tsx                   [0.7 KB]  Root layout: query provider, auth gate, app shell
loading.tsx                  [0.6 KB]  Root loading state
not-found.tsx                [1.9 KB]  404 page
globals.css                  [0.9 KB]  Global CSS: base styles, CSS variables
dashboard/page.tsx           [0.4 KB]  Dashboard page
attendance/page.tsx          [0.4 KB]  Attendance page
leave/page.tsx               [0.4 KB]  Leave management page
payroll/page.tsx             [0.3 KB]  Payroll page
performance/page.tsx         [0.4 KB]  Performance page
hiring/page.tsx              [0.3 KB]  Hiring page
notifications/page.tsx       [0.4 KB]  Notifications page
organization/page.tsx        [0.4 KB]  Organization page
settings/page.tsx            [0.3 KB]  Settings page
employees/page.tsx           [0.4 KB]  Employee list page
employees/[id]/page.tsx      [0.5 KB]  Employee detail page
employees/[id]/edit/page.tsx [0.5 KB]  Employee edit page
employees/[id]/loading.tsx   [0.5 KB]  Employee detail loading state
employees/new/page.tsx       [0.4 KB]  New employee page
employees-v2/page.tsx        [0.4 KB]  Employees v2 page
candidate-pipeline/page.tsx  [0.1 KB]  Candidate pipeline page
departments/page.tsx         [0.1 KB]  Departments page
employee-profile/page.tsx    [0.1 KB]  Employee profile page
job-postings/page.tsx        [0.1 KB]  Job postings page
leave-requests/page.tsx      [0.1 KB]  Leave requests page
login/page.tsx               [0.1 KB]  Login page
performance-reviews/page.tsx [0.1 KB]  Performance reviews page
roles/page.tsx               [0.1 KB]  Roles page
```

### UI Components (ui/components/)
```
auth/auth-gate.tsx         [1.3 KB]   Auth gate: blocks unauthenticated users
auth/auth-provider.tsx     [3.9 KB]   Auth provider: session management, token storage, login/logout
auth/login-form.tsx        [5.0 KB]   Login form: credential input, API call, error display

base/avatar.tsx            [0.8 KB]   Avatar component: initials or image
base/badge.tsx             [1.1 KB]   Badge/chip component
base/button.tsx            [2.5 KB]   Button component: primary/secondary/danger/ghost variants
base/calendar.tsx          [4.1 KB]   Calendar picker component
base/card.tsx              [1.3 KB]   Card container component
base/dialog.tsx            [3.2 KB]   Modal dialog component
base/dropdown-menu.tsx     [4.5 KB]   Dropdown menu component
base/feedback.tsx          [5.6 KB]   Toast/alert feedback component
base/form.tsx              [1.1 KB]   Form wrapper component
base/input.tsx             [1.7 KB]   Input field component
base/page.tsx              [5.5 KB]   Page layout wrapper
base/separator.tsx         [0.4 KB]   Divider separator component
base/slot.tsx              [1.1 KB]   Slot (portals/composition) component
base/switch.tsx            [1.8 KB]   Toggle switch component
base/table.tsx             [1.9 KB]   Table component
base/tabs.tsx              [2.3 KB]   Tab navigation component

dashboard/enterprise-dashboard.tsx   [16.8 KB] Enterprise dashboard: KPI cards, attendance widget, payroll status, decision-first layout
dashboard/attendance-payroll-workspace.tsx [29.1 KB] Attendance + payroll combined workspace: approval queues, anomaly alerts
dashboard/Dashboard.tsx              [0.1 KB]  Dashboard stub/re-export

employees/EmployeeList.tsx           [20.1 KB] Employee list table with filtering, sorting, avatar+name columns
employees/EmployeeDetail.tsx         [11.5 KB] Employee detail profile view
employees/employee-form.tsx          [12.4 KB] Employee create/edit form with validation
employees/EmployeesV2.tsx            [18.6 KB] Employees v2 with enhanced filtering
employees/employee-list-page.tsx     [16.1 KB] Employee list page wrapper with pagination
employees/employee-create-page.tsx   [0.6 KB]  Employee create page shell
employees/employee-edit-page.tsx     [1.2 KB]  Employee edit page shell
employees/employee-profile-page.tsx  [5.4 KB]  Employee profile page shell
employees/employee-data.ts           [6.7 KB]  Employee mock/type data
employees/people-structure-page.tsx  [7.9 KB]  People structure/org chart view

hiring/hiring-page.tsx               [6.0 KB]  Hiring page with job postings list
hiring/hiring-pipeline-board.tsx     [39.8 KB] Kanban pipeline board: drag-drop stages, candidate cards, slide panel

organization/organization-page.tsx   [16.3 KB] Organization structure page: departments, roles, reporting lines

shared/app-shell.tsx                 [9.3 KB]  Shared app shell: sidebar navigation, topbar, content area
shared/query-provider.tsx            [0.5 KB]  React Query provider wrapper
hrms/shell/app-shell.tsx             [0.1 KB]  HRMS app shell stub
layout/app-shell.tsx                 [0.1 KB]  Layout app shell stub

surfaces/Attendance.tsx              [24.7 KB] Attendance surface: records table, shift view, corrections
surfaces/Departments.tsx             [11.7 KB] Departments surface: list, create, edit
surfaces/LeaveManagement.tsx         [16.0 KB] Leave management surface: requests, balance, calendar
surfaces/Payroll.tsx                 [16.8 KB] Payroll surface: records, run status, payslips
surfaces/Settings.tsx                [10.2 KB] Settings surface: policies, rules, payroll config
surfaces/job-postings-page.tsx       [5.3 KB]  Job postings surface
surfaces/leave-requests-page.tsx     [5.7 KB]  Leave requests surface
surfaces/notifications-page.tsx      [9.8 KB]  Notifications surface
surfaces/performance-reviews-page.tsx [11.3 KB] Performance reviews surface
surfaces/employee-profile-workspace.tsx [6.9 KB] Employee profile workspace
```

### UI Library (ui/lib/)
```
api/client.ts              [3.4 KB]  HTTP API client: fetch wrapper with auth headers, error handling, base URL config
api/hrms.ts                [11.0 KB] HRMS API module: typed functions for all service endpoints
api/mock/index.ts          [6.9 KB]  Mock API router: intercepts requests and returns mock data in dev
api/mock/shared.ts         [26.0 KB] Shared mock data: employees, departments, payroll records, leave requests
api/mock/employees.mock.ts [3.4 KB]  Employee mock data
api/mock/attendance.mock.ts [2.3 KB] Attendance mock data
api/mock/hiring.mock.ts    [5.4 KB]  Hiring pipeline mock data
api/mock/leave.mock.ts     [1.4 KB]  Leave request mock data
api/mock/payroll.mock.ts   [2.5 KB]  Payroll record mock data
api/mock/notifications.mock.ts [4.4 KB] Notification mock data
api/mock/dashboard.mock.ts [1.6 KB]  Dashboard KPI mock data
api/mock/auth.mock.ts      [5.1 KB]  Auth session mock data
auth/api.ts                [1.5 KB]  Auth API calls: login, logout, refresh
auth/session.ts            [2.1 KB]  Session management: token storage, expiry, auto-refresh
employees/api.ts           [4.0 KB]  Employee API functions: CRUD, filtering, pagination
employees/types.ts         [1.8 KB]  TypeScript types for employee data
employees/validation.ts    [2.0 KB]  Client-side employee validation rules
hooks/use-health.ts        [0.3 KB]  React hook for service health check
navigation.ts              [5.6 KB]  Navigation routes and link helpers
utils.ts                   [0.7 KB]  Shared utility functions (className merging, etc.)
styles/theme.css           [0.7 KB]  CSS theme variables
```

### UI Config
```
ui/next.config.ts          [0.1 KB]  Next.js config: API proxy rules
ui/next-env.d.ts           [0.3 KB]  Next.js TypeScript environment declarations
ui/package.json            [0.6 KB]  Dependencies: Next.js, React, Tailwind, shadcn/ui, react-query
ui/package-lock.json       [54.8 KB] Locked dependency tree (generated — do not edit)
ui/tsconfig.json           [0.6 KB]  TypeScript config: strict mode, path aliases
ui/postcss.config.mjs      [0.1 KB]  PostCSS config for Tailwind
ui/.env.example            [0.1 KB]  UI env template: NEXT_PUBLIC_API_URL
ui/layout.tsx              [0.1 KB]  Root layout alias
```

---

## CATEGORY 32 — BACKEND TYPESCRIPT — SHARED INFRASTRUCTURE (TypeScript)
**Location:** `backend/`
TypeScript-based middleware and utilities (distinct from Python infrastructure layer).

```
middleware/audit.ts            [3.0 KB]  Express audit middleware: logs request/response with actor, action, trace ID
middleware/audit-store.ts      [0.7 KB]  Audit store: writes audit records to persistent storage
middleware/circuit-breaker.ts  [1.1 KB]  TypeScript circuit breaker: wraps outbound calls with open/half-open/closed state
middleware/error-handler.ts    [1.6 KB]  Global error handler middleware: maps domain errors to D1 error responses
middleware/logger.ts           [7.6 KB]  Structured logger middleware: JSON logging with log level, trace ID, service context
middleware/rate-limit.ts       [5.9 KB]  Rate limiting middleware: sliding window rate limit per tenant/IP
middleware/request-id.ts       [1.5 KB]  Request ID middleware: generates/propagates X-Request-Id header
middleware/retry.ts            [1.0 KB]  Retry middleware: exponential backoff for transient failures
middleware/tenant-context.ts   [1.5 KB]  Tenant context middleware: extracts and validates tenant_id from request
middleware/throttle.ts         [3.0 KB]  Throttle middleware: request rate control per endpoint
middleware/validation.ts       [3.2 KB]  Zod validation middleware: parses and validates request body/query schemas

db/optimization.ts             [3.9 KB]  Database optimization helpers: query batching, index hints, connection pooling
db/persistent-map.ts           [2.4 KB]  PersistentMap TypeScript implementation: get/set/delete/list with tenant scoping

cache/cache.service.ts         [1.9 KB]  Cache service: in-memory cache with TTL and LRU eviction

metrics/metrics.ts             [4.9 KB]  Metrics collection: request counts, latency histograms, error rates (Prometheus-compatible)

health/health.controller.ts    [0.9 KB]  Health check controller: /health and /ready endpoints

utils/idempotency.ts           [1.0 KB]  Idempotency key utility: deduplication for write operations
```

---

## CATEGORY 33 — BACKEND — API LAYER (root api/ and api-gateway/)
```
api/__init__.py             [0 KB]    API package init
api/employee_portal.py      [4.5 KB]  Employee portal API: compact endpoints for employee self-service (leave balance, payslip, profile)
api/manager_dashboard.py    [8.9 KB]  Manager dashboard API: decision-first data aggregation endpoint (Decision Cards, anomalies, pending approvals, attendance alerts)
api/workforce.py            [3.1 KB]  Workforce API: workforce summary stats endpoint (headcount, active count, turnover)
```

---

## CATEGORY 34 — MOBILE AND PRODUCT LAYER
```
mobile/__init__.py          [0.2 KB]  Mobile package init
mobile/contracts.py         [1.7 KB]  Mobile API contracts: build_mobile_response() card builder, MobileCard dataclass
mobile/session.py           [2.6 KB]  Mobile session management: session state, device registration
mobile/app/__init__.py      [0.1 KB]  Mobile app package init
mobile/app/product.py       [3.4 KB]  Mobile product module: feature availability per tier in mobile context
```

---

## CATEGORY 35 — WORKSPACE ROOT FILES
**Location:** `D:\HRMS\` (project root)

### `V3.zip` [903.5 KB] — REMOVED 2026-06-07
**Purpose:** Source archive of the SME-HRMS-main backend repo.
**Description:** Original zip from which the backend working copy was unzipped (originally to `v3_extracted/SME-HRMS-main/`, since renamed to `backend/`). Deleted during the 2026-06-07 workspace restructuring as redundant with the extracted working copy, which is the source of record going forward.
**When:** N/A — file no longer present.

### `.claude/settings.local.json` [0.6 KB]
**Purpose:** Claude Code local project settings — tool permissions and hook configurations.
**Description:** Project-level `.claude/settings.json` overrides for this workspace. Contains allowed tool permissions and any configured hooks. Do not commit sensitive values.
**When:** When adjusting Claude Code permissions for this workspace (use `/update-config` skill).

---

## CATEGORY 36 — BACKEND SYSTEM DOCS (missed from Category 11)

### `docs/system/qc-suite.md` [15.9 KB]
**Purpose:** Standard QC validation process — when to run, all 5 tier commands with exact scripts, full test file index (80+ tests), and Tier 5 coverage gap register (15 known uncovered areas from sessions 2/3/5/6).
**Description:** Run trigger table (gap closed, new file added, major session complete, before final alignment — each requires different tiers). 5-tier suite: Tier 1 `pytest -q` (target 0 failures, last verified 281 passed 2026-03-31, pre-session 2), Tier 2 `deployment/qc_validate.py` (10-point infrastructure rubric, target 11/11), Tier 3 RE-QC: master_certification (5/5), addon_convergence (5/5), data_integrity (6/6), Tier 4 twelve domain integrity validators (security_compliance_lock, audit_service, employee_domain_integrity, candidate_domain_integrity, engagement_domain_integrity, performance_domain_integrity, role_integrity, settings_domain_integrity, qc_validate_engagement, qc_validate_performance, qc_validate_role_mapping, qc_validate_settings), Tier 5 Coverage Gap Register — 15 known gaps: compliance_api.py (no test), bank_service/banking_api (no test), decision_api.py (no test), whatsapp_service/api (no test), atl_adapter.py (no test), G33-G42 new statutory methods not yet tested, SB-G01-SB-G05 new capabilities not yet asserted, SPEC-G01/G02 renamed fields not yet tested, MN-G01-G06 new methods not yet tested. Full test-file-to-coverage index.
**When:** Before any final alignment pass; when adding new code that needs a test; when determining if a full QC run is needed before updating intent_build_alignment.md.
**Upload:** ON-DEMAND

### `docs/system/MASTER BUILD SPEC.md` [27.0 KB]
**Purpose:** Authoritative product and architecture specification — 22 sections covering product thesis, 6-layer architecture, 9 core capabilities, 7 add-on capabilities, full Pakistan statutory coverage, and behavior contracts.
**Description:** v2.0, merged from Complete Build Spec v1.0 + HRMS Spec v1.0. Key sections: §01 product thesis (Trust>Accuracy>Compliance>Intelligence>UX), §02 7 design principles, §03 target users (6 primary + 3 secondary), §04 core problems (global + Pakistan-specific), §05 6-layer architecture (Data/Domain/Country Abstraction/Service-Orchestration/Integration/Experience), §06 core capabilities C01-C09 (employee/org/payroll/compliance/attendance/leave/disbursement/decision/employee-access), §07 add-on A01-A07 (helpdesk/expenses/EWA/performance/recruitment/engagement/advanced AI), §08 country-agnostic rules R1-R6, §09 country resolution model (legal entity > org config > location > explicit override), §10 service registry — MANDATORY (7 IMPLEMENTED: employee/payroll/compliance/attendance/bank/decision/whatsapp), SUPPORT (automation/notification/reporting-analytics/audit), ADD-ON (8), IMPLEMENTED (travel-service + project-service — corrected from PLANNED per S8-G04), §11 Pakistan country profile (20 statutory requirements), §12 payroll behavior contract (10-step run sequence), §13 compliance behavior contract (7 states: DRAFT→VALIDATED→SUBMITTED→ACKNOWLEDGED→FAILED→RETRY→MANUAL + 4 error types), §14 attendance contract, §15 decision system canon (15-field Decision Object, 3 severity levels), §16 AI/insight behavior (4 mandatory output fields), §17 WhatsApp must-be treated as standalone access-channel service, §18 disbursement states (PENDING→GENERATED→SUBMITTED→SENT→ACCEPTED→RECONCILED), §19 audit requirements, §20 service registry rule (no paper services), §21 acceptance criteria AC1-AC10 + PK1-PK8. 5 country/base interfaces now: TaxEngine + ComplianceEngine + PayrollRules + StatutoryValidator + Banking. Supersedes both archive build spec files.
**When:** The definitive backend spec — consult when validating any architectural or capability decision; when implementing new behavior contracts.
**Upload:** ON-DEMAND

### `docs/system/service-manifest.md` [4.8 KB]
**Purpose:** Service manifest — all services with runtime status, code file paths, scope, country support, and owner domain.
**Description:** Per SPEC §10+§20. 3 service tiers: Mandatory Core (7 services: employee/payroll/compliance/attendance/bank/decision/employee-access), Support (6 services: automation/notification/audit/auth/outbox/error-registry), Optional Add-On (12 services: helpdesk/expense/ewa/performance/hiring/engagement/analytics/whatsapp/leave/cost-planning/governance/experience-layer). Country adapters (Pakistan + Dummy). Planned services (export sector compliance MN-G07 deferred). Rule: `implemented` must have code + test + docker entry. Last updated 2026-04-13 (Session 6).
**When:** The most current and granular service registry — maps capability codes (C01-C09, A01-A07) to exact code files.
**Upload:** ON-DEMAND

### `docs/system/archive/` — Archived superseded specifications
```
archive/COMPLETE HRMS BUILD SPEC.md    [8.0 KB]  v1.0 build spec — superseded by MASTER BUILD SPEC.md
archive/HRMS SPEC.md                   [17.9 KB] Country-agnostic modular HRMS spec — superseded by MASTER BUILD SPEC.md
archive/HRMS Repo Surgical Upgrade Spec.md [13.5 KB] Surgical upgrade targeting 100% in all areas — historical reference for session 1-3 gap work
archive/HRMS SYSTEM BEHAVIOR SPEC.md  [6.2 KB]  Original system behavior spec — superseded by MASTER BEHAVIOR SPEC.md
archive/MARKET-VALIDATED BEHAVIOR SPEC.md [23.8 KB] Market-validated behavior spec — superseded by MASTER BEHAVIOR SPEC.md
archive/Pakistan_HRMS_Market_Research_Report_(2024–2026) MANUS AI.md [13.3 KB] Original Manus AI market research — superseded by MASTER MARKET RESEARCH.md
archive/RMS MARKET RESEARCH--CHAT GPT.md [6.7 KB] Original ChatGPT market research — superseded by MASTER MARKET RESEARCH.md
```
**Purpose:** All archive files are superseded source documents. Their content has been merged into the MASTER * series. Do not consult these directly — use the MASTER versions.
**When:** Historical reference only; never load in active sessions.
**Upload:** N/A

---

## CATEGORY 37 — REPOSITORY README FILES
Root-level and directory-level README files in the backend repo. Brief orientation documents — use the canonical docs/canon and docs/system files for authoritative detail.

### `backend/README.md` [3.5 KB]
**Purpose:** Top-level repo orientation — 21 service ports, canonical gateway routes, key files, and local run instructions.
**Description:** 88 lines. Lists all 21 standalone services with ports: employee-service (8001), attendance (8002), leave (8003), payroll (8004), hiring (8005), auth (8006), notification (8007), audit (8008), workflow (8009), performance (8010), engagement (8011), helpdesk (8012), reporting (8013), search (8014), expense (8015), integration (8016), automation (8017), travel (8018), project (8019), settings (8020), api-gateway (8000), frontend-ui (3000). NOTE: `background_jobs.py` is an INTERNAL MODULE — not a separate docker-compose service. Canonical gateway routes added by the repo: `/api/v1/projects`, `/api/v1/integrations`, `/api/v1/automations`, `/api/v1/workflows`. Key root files: `docker-compose.yml`, `Dockerfile.services`, `Dockerfile.api`, `Dockerfile.ui`, `start.sh`, `.env.example`. Local run: `docker compose up -d --build`. Health check: `curl http://localhost:8000/ready`.
**When:** When confirming service port assignments; when setting up the repo for the first time.
**Upload:** ON-DEMAND

### `backend/api-gateway/README.md` [0.5 KB]
**Purpose:** API gateway directory orientation — route group summary and pointer to routes.py.
**Description:** 16 lines. All routes under `/api/v1`. Route groups: employees/departments → employee-service, attendance → attendance-service, leave → leave-service, payroll → payroll-service, hiring → hiring-service. Route registry is in `api-gateway/routes.py`. Use `docs/canon/api-standards.md` and `api-gateway/routes.py` for authoritative routing detail.
**When:** Orientation only — use `api-gateway/routes.py` for actual route definitions.
**Upload:** N/A (pointer)

### `backend/deployment/README.md` [0.6 KB]
**Purpose:** Deployment directory orientation — lists what each deployment/ subdirectory contains and key QC script locations.
**Description:** 18 lines. Directory map: `config/` — env + gateway/postgres bootstrap configuration; `migrations/` — SQL migrations for canonical HRMS entities; `scripts/run-migrations.sh` — migration runner executed by compose; `frontend/` — static UI artifact for `Dockerfile.ui`; `qc_validate.py` — automated QC scoring (target 10/10). Also notes: `re_qc_validate_addon_convergence.py` (P50 gate, must pass 10/10) and `re_qc_validate_master_certification.py` (P51 gate, must pass 10/10). Compose runtime note: `docker-compose.yml` starts Postgres, runs one-shot migrations, then starts all domain services before api-gateway.
**When:** Orientation only — use `docs/system/qc-suite.md` for full QC process detail.
**Upload:** N/A (pointer)

---

## Catalogue Update — Production-Readiness Pass (2026-06-11)

### New backend modules

| File | Purpose |
|---|---|
| `backend/structured_logging.py` | `StructuredJSONFormatter` + `configure_logging()` + `ContextVar` correlation-ID propagation. |
| `backend/rate_limiting.py` | `SlidingWindowRateLimiter` — thread-safe per-key sliding window; used by API gateway. |
| `backend/jwt_utils.py` | `verify_hs256_jwt()` — stateless HS256 token verification shared between gateway and services. |
| `backend/secrets_config.py` | `require_secrets()` — validates required env vars at startup; auto-loads `.env` via python-dotenv. |
| `backend/deployment/migrate.py` | Python migration runner; tracks applied SQL files in `schema_migrations` table; supports SQLite + PostgreSQL. |
| `backend/.github/workflows/ci.yml` | GitHub Actions CI: test matrix (3.11/3.12), ruff lint, pip-audit security scan, migration dry-run. |

### Modified backend files (additive)

| File | Change |
|---|---|
| `backend/persistent_store.py` | pickle replaced with JSON type-tag codec; PostgreSQL backend added. |
| `backend/docker/api_gateway_service.py` | uvicorn ASGI; structured logging; rate limiting; JWT enforcement; OpenAPI endpoint; TLS. |
| `backend/docker/service_runtime.py` | uvicorn ASGI; structured logging; TLS. |

## Catalogue Update — Phase 6 Completion (2026-06-11)

### Modified: `docker/api_gateway_service.py`
W3C Trace Context (`_parse_traceparent`/`_new_traceparent`), CORS headers + `OPTIONS` preflight, `GET /metrics` Prometheus endpoint, JWT clock-skew tolerance (±5s).

### Modified: `backend/jwt_utils.py`
`verify_hs256_jwt` now accepts `clock_skew_seconds` parameter (default 5).

### Docs alignment fixes
- `hrms-doc-catalogue-v1.md`: `service_runtime.py` and `api_gateway_service.py` entries rewritten (removed stale `BaseHTTPRequestHandler` description).
- `infrastructure.md`: `persistent_store.py` entry updated; new entries for `structured_logging.py`, `rate_limiting.py`, `jwt_utils.py`, `secrets_config.py`.
- `service-manifest.md`: `auth-service` language corrected from `(TypeScript)` to `(Python)`.
- `success-criteria.md`: Tier 5 added (S19–S31, all ✅).
- `roadmap.md`: Phase 6 added with all items ✅.

## Catalogue Update — Security Hardening Pass (2026-06-11)

### Modified: `docker/api_gateway_service.py`
Four new features added (all inline in gateway, no new files):
- **Per-tenant RBAC**: `_ROUTE_ROLE_MAP` dict + cross-tenant `X-Tenant-Id` vs JWT `tenant_id` check after JWT verification; 403 on role or tenant mismatch.
- **Body size limit**: `MAX_REQUEST_BODY_BYTES` constant (default 1 MB, `MAX_REQUEST_BODY_BYTES` env var); enforced during ASGI streaming body read; 413 `REQUEST_TOO_LARGE` before body fully loaded.
- **Idempotency cache**: `_IdempotencyCache` class (thread-safe `RLock`, 24h TTL, 10k LRU cap); `Idempotency-Key` header on POST/PATCH/PUT replays cached response with `X-Idempotent-Replayed: true`.
- **JSON body validation**: pre-forward `json.loads(body)` when `Content-Type: application/json`; 400 `INVALID_JSON` on `json.JSONDecodeError`.

Inline entry updated above to reflect all current capabilities.

### Docs updated
- `success-criteria.md`: S32–S35 added (per-tenant RBAC, body size limit, idempotency, JSON validation — all ✅).
- `roadmap.md`: Phase 6 extended with 4 new ✅ items.
- `backend/docs/system/progress.md`: Security Hardening Pass section appended.
- `backend/docs/system/gap-register.md`: Security Hardening Pass section appended.
- `ops/build-progress.md`: Security Hardening Pass section appended.
