# FRONTEND GAP REGISTER

Status: Complete
Created: 2026-06-17
Last Reviewed: 2026-06-18
Phase: 3 — Frontend Authority Capture
Source: All Phase 3 authority documents, API_CONTRACT.md, DOMAIN_MODEL.md, archetype-system-v1.md
Final Classification: See `docs/08_reports/FINAL_CLASSIFIED_REGISTER.md` §7 — all 43 gaps classified AUTO-CLOSED or OUT-OF-SCOPE. 0 gaps block Phase 4.

---

## PURPOSE

Registers every gap between confirmed backend reality and complete frontend traceability. A gap is any area where:
- A backend capability exists but has no confirmed frontend consumer
- A frontend screen exists (wireframe) but has no confirmed backend API
- A workflow step has no confirmed UI representation
- A domain entity has no UI representation at a key lifecycle point

**Gaps are informational — they do not block Phase 3 completion. They are inputs for the implementation backlog.**

Gap classification:
- **KNOWN GAP:** Gap is known and accepted; implementation path is clear
- **IMPLEMENTATION DETAIL:** Gap is resolved in implementation; frontend implementer decides
- **OUT OF SCOPE:** Gap is intentionally excluded from current scope
- **ADD-ON:** Gap is in ADD-ON features; deferred
- **PLANNED:** Gap is in PLANNED features; future

---

## GAP CATEGORY 1: SCREENS WITH NO BACKEND API (OUT OF SCOPE / PLANNED)

| ID | Screen | Wireframe | Status | Reason |
|----|--------|-----------|--------|--------|
| G-001 | Shift Roster | `h06-shift-roster.html` | OUT OF SCOPE | Shift/roster scheduling confirmed out of scope. No backend service. No Phase 3 route. |
| G-002 | Documents List | `h02-documents.html` | OUT OF SCOPE | Document management confirmed out of scope. No backend service. No Phase 3 route. |
| G-003 | Travel Requests List | `h02-travel-requests.html` | PLANNED (F-023) | Travel Management is PLANNED. Service scaffolded only. No Phase 3 route. |
| G-004 | Raise Travel Request | `h04-raise-travel-request.html` | PLANNED (F-023) | Same as G-003. |
| G-005 | Project Management screens | (not in archetype system) | PLANNED (F-024) | Project Management is PLANNED. No wireframes. No backend. No Phase 3 scope. |

---

## GAP CATEGORY 2: ADD-ON SCREENS (DEFERRED — NOT BLOCKING)

| ID | Screen | Wireframe | Feature | Implementation Status |
|----|--------|-----------|---------|----------------------|
| G-010 | Performance Reviews List | `h02-performance-reviews.html` | F-017 | ADD-ON — performance-service exists; routes deferred |
| G-011 | Performance Review Detail | `h03-performance-review-detail.html` | F-017 | ADD-ON |
| G-012 | Expense Claims List | `h02-expense-claims.html` | F-021 | ADD-ON — expense-service exists; routes deferred |
| G-013 | Expense Claim Detail | `h03-expense-claim-detail.html` | F-021 | ADD-ON |
| G-014 | Raise Expense Claim | `h04-raise-expense-claim.html` | F-021 | ADD-ON |
| G-015 | Engagement Results | `h07-engagement-results.html` | F-018 | ADD-ON — engagement-service exists; routes deferred |
| G-016 | Survey Builder | `h11-survey-builder.html` | F-018 | ADD-ON |
| G-017 | Helpdesk | `h12-helpdesk.html` | F-019 | ADD-ON — helpdesk-service exists; routes deferred |
| G-018 | Performance Dashboard | (no separate H01 variant) | F-017 | ADD-ON — performance tab on HR Manager Dashboard; deferred |

---

## GAP CATEGORY 3: SETTINGS — CHROME-ONLY SECTIONS

Settings page (H10) has 5 backend-persistent sections and 5 chrome-only sections. The chrome-only sections have no backend persistence in Phase 3.

| ID | Settings Section | Status | Path to Resolution |
|----|-----------------|--------|-------------------|
| G-020 | Profile settings | KNOWN GAP | No `/api/v1/auth/profile` endpoint confirmed for profile editing. Future scope. |
| G-021 | Security settings | KNOWN GAP | Token/session management (CAP-AUT-003) exists in auth-service but no frontend settings UI defined. Future scope. |
| G-022 | Notifications preferences | KNOWN GAP | No `/api/v1/notifications/preferences` endpoint. Chrome renders UI but no persistence. |
| G-023 | Integrations (incl. WhatsApp config) | KNOWN GAP | Integration-service present but no confirmed frontend endpoints for integration config. `/api/v1/whatsapp/config` confirmed but Settings Integrations tab is chrome-only. |
| G-024 | AI & Automation preferences | KNOWN GAP | No confirmed API for AI preference settings. Chrome-only. Future scope. |

---

## GAP CATEGORY 4: ENTITY LIFECYCLE STATES WITH LIMITED UI COVERAGE

Some entity lifecycle states exist in the domain model but have limited or no frontend UI representation.

| ID | Entity | State | UI Coverage | Gap |
|----|--------|-------|-------------|-----|
| G-030 | Employee | `draft` | StatusBadge shows "Draft"; Add Employee form creates active by default | No dedicated "draft employee" workflow or draft review screen — IMPLEMENTATION DETAIL |
| G-031 | Employee | `suspended` | StatusBadge shows "Suspended" | No "Suspend Employee" action defined in frontend — KNOWN GAP; Admin can PATCH via edit |
| G-032 | Employee | `terminated` | StatusBadge shows "Terminated" | No "Terminate Employee" action screen defined — KNOWN GAP; Admin can PATCH via edit form |
| G-033 | WorkflowInstance | `in_progress` intermediate steps | Approval inbox shows `pending` items | Multi-step workflows with intermediate states may show partial information — IMPLEMENTATION DETAIL |
| G-034 | ReviewCycle (ADD-ON) | All states | No UI representation in Phase 3 | ADD-ON — F-017 deferred |
| G-035 | Goal / Feedback / CalibrationSession | All states | No UI | ADD-ON — F-017 deferred |
| G-036 | Survey entities | All states | No UI | ADD-ON — F-018 deferred |
| G-037 | Compensation entities (CompensationBand, BenefitsPlan, BenefitsEnrollment, Allowance) | All states | Partial — salary revision H04 covers SalaryRevision; CompensationBand visible in employee profile Compensation tab | No dedicated compensation management screen — KNOWN GAP; compensation management is Admin-only; implementer can surface through employee profile |
| G-038 | JobPosition (Requisition scope) | All states | No dedicated screen — job postings cover open positions | No separate org chart of all defined positions vs. filled positions — KNOWN GAP; low priority |

---

## GAP CATEGORY 5: API ENDPOINTS WITH UNCERTAIN FRONTEND MAPPING

These API patterns are mentioned in the API contract but their exact frontend consumer is not yet pinned.

| ID | Endpoint | Uncertainty | Resolution |
|----|----------|-------------|------------|
| G-040 | `GET /api/v1/employees/summary` | Whether this is a distinct endpoint or inferred from the employees list | IMPLEMENTATION DETAIL — implement as part of dashboard data loading; if endpoint doesn't exist, derive from `/api/v1/employees` count response |
| G-041 | `GET /api/v1/hiring/summary` | Whether this is a distinct endpoint or constructed from multiple calls | IMPLEMENTATION DETAIL — implement recruitment dashboard; if no single summary endpoint, compose from separate calls (postings count, candidates count, interviews this week) |
| G-042 | `GET /api/v1/payroll/status?period=current` | Whether status is a distinct sub-endpoint | IMPLEMENTATION DETAIL — if not available as sub-endpoint, derive from `GET /api/v1/payroll?period=current&limit=1` |
| G-043 | `DELETE /api/v1/notifications/{id}` | Whether delete is supported | IMPLEMENTATION DETAIL — implement with soft-delete/archive as fallback if hard delete not supported |
| G-044 | `GET /api/v1/audit/{id}` | Whether individual audit records are fetchable by ID | IMPLEMENTATION DETAIL — if not supported, expand-in-place from list response data |

---

## GAP CATEGORY 6: RBAC EDGE CASES

| ID | Gap | Classification | Resolution |
|----|-----|----------------|------------|
| G-050 | Manager can view own payslip but `/payroll` gateway route is restricted to Admin/PayrollAdmin/Manager — Manager CAN access but gets dept-filtered data | KNOWN GAP — navigation clearly shows `/payroll` for Manager; API scope enforcement handles filtering | IMPLEMENTATION DETAIL — verify API returns correct scoped data |
| G-051 | Employee navigating to `/payroll/[id]` for own payslip — no nav link in sidebar for Employee | KNOWN GAP — Employee reaches payslip from Dashboard widget "View Payslip" link and from own Employee Profile Compensation tab | IMPLEMENTATION DETAIL — no `/payroll` nav item for Employee; deep-link from dashboard only |
| G-052 | Recruiter's own leave — Recruiter can raise leave (`/leave/new`) but has no `/leave/requests` team view | KNOWN GAP — documented in ROLE_EXPERIENCE_MATRIX; Recruiter uses `/leave` (own calendar only) | No gap in authority; implementation is clear |
| G-053 | CAP-C-002 (Compliance management) vs CAP-COM-001 (view compliance) — Admin can manage, PayrollAdmin read-only | IMPLEMENTATION DETAIL — compliance screen must render different actions based on role claim |

---

## GAP CATEGORY 7: WHATSAPP / BANKING FRONTEND SCOPE

| ID | Gap | Classification |
|----|-----|----------------|
| G-060 | No standalone WhatsApp screen — WhatsApp is backend integration | OUT OF SCOPE by design. No gap in frontend authority. |
| G-061 | Banking disbursement surfaced via payroll detail only — no standalone banking screen | OUT OF SCOPE by design. No gap in frontend authority. |
| G-062 | Banking service non-standard envelope | KNOWN GAP — frontend must handle `{status, data, service}` for any banking API calls. Covered in FRONTEND_API_DEPENDENCY_MAP. |

---

## GAP CATEGORY 8: DOCUMENTATION DRIFT IN SOURCE DOCS

These are documentation drift items identified during Phase 3 authority capture that exist in source docs but do not affect frontend authority.

| ID | Stale Item | In Document | Phase Resolved | Frontend Impact |
|----|-----------|-------------|----------------|-----------------|
| G-070 | "Gateway route unconfirmed" notes for F-011/014/015/016 | PROJECT_CHARTER §5 | Phase 2.8 — routes 22–25 confirmed | Zero — routes are confirmed; charter note is stale |
| G-071 | "TBD – REQUIRES VERIFICATION" markers on compliance/decision/banking/whatsapp | FEATURE_SCOPE.md | Phase 2.95 collapse | Zero — routes confirmed; markers stale |
| G-072 | Missing gateway routes in FULLSTACK_STITCHING_CONTRACT known gaps table | FULLSTACK_STITCHING_CONTRACT | Phase 2.95 collapse | Zero — traces T-001 to T-015 are authoritative; known gaps table is stale |

---

## GAP SUMMARY

| Category | Gap Count | Blocking Phase 3? |
|----------|-----------|-------------------|
| Screens with no backend (Out of Scope/Planned) | 5 | No |
| ADD-ON screens (deferred) | 9 | No |
| Chrome-only settings sections | 5 | No |
| Entity lifecycle gaps | 9 | No |
| API endpoint uncertainty | 5 | No |
| RBAC edge cases | 4 | No |
| WhatsApp/Banking scope clarity | 3 | No |
| Documentation drift | 3 | No |
| **Total gaps registered** | **43** | **0 blocking** |

**All 43 gaps are non-blocking.** Phase 3 authority is complete. Implementation may proceed.
