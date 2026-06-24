# FRONTEND IMPACT ANALYSIS

Status: Complete
Created: 2026-06-17
Phase: 2.95 — Residual Decision Collapse

---

## PURPOSE

For each residual decision and collapsed TBD item, analyzes the specific impact on frontend dimensions: Navigation, Menus, Screens, Dashboards, Permissions, Workflows, Forms, Components, User Journeys, and Role Experiences.

This document answers the mandate's FRONTEND READINESS TEST: "Can any remaining unresolved decision alter any of these dimensions?"

---

## ANALYSIS FORMAT

For each decision:
- **Decision:** What was being decided
- **Collapse Outcome:** How it was resolved
- **Navigation Impact:** Does it change what routes/items exist?
- **Menu Impact:** Does it change sidebar/header nav composition?
- **Screen Impact:** Does it add, remove, or alter screens?
- **Dashboard Impact:** Does it change dashboard widgets or composition?
- **Permission Impact:** Does it change role-based visibility?
- **Workflow Impact:** Does it change multi-step flows?
- **Form Impact:** Does it change form fields, validation, or submission?
- **Component Impact:** Does it require new or changed UI components?
- **User Journey Impact:** Does it change end-to-end task flows?
- **Role Experience Impact:** Does it change what a specific role sees or can do?

---

## ROD-001: Frontend App Location

**Decision:** Should `backend/ui/` be relocated to repo root `frontend/`?
**Collapse Outcome:** OWNER_CONFIRMATION_ONLY — Stay in `backend/ui/` through Phase 3.

| Dimension | Impact |
|-----------|--------|
| Navigation | **ZERO** — File system location has no effect on Next.js routes |
| Menus | **ZERO** |
| Screens | **ZERO** — All screens render identically regardless of code directory |
| Dashboards | **ZERO** |
| Permissions | **ZERO** |
| Workflows | **ZERO** |
| Forms | **ZERO** |
| Components | **ZERO** |
| User Journeys | **ZERO** |
| Role Experiences | **ZERO** |

**Frontend Impact Score: ZERO**
This decision is purely structural (where code lives in the repo). No user-visible aspect is affected by whether the Next.js app is at `backend/ui/` or `frontend/`.

---

## ROD-002: TypeScript Dead Code Archiving

**Decision:** Archive 60 dead TypeScript files.
**Collapse Outcome:** RESOLVED — SAFE_REPOSITORY_HYGIENE authorized.

| Dimension | Impact |
|-----------|--------|
| Navigation | **ZERO** — Dead files are not imported or executed |
| Menus | **ZERO** |
| Screens | **ZERO** |
| Dashboards | **ZERO** |
| Permissions | **ZERO** |
| Workflows | **ZERO** |
| Forms | **ZERO** |
| Components | **ZERO** |
| User Journeys | **ZERO** |
| Role Experiences | **ZERO** |

**Frontend Impact Score: ZERO**

---

## ROD-003: Deploy Validation CI Migration

**Decision:** Migrate `deploy.yml` to root CI as integration test.
**Collapse Outcome:** OWNER_CONFIRMATION_ONLY — Migrate as `workflow_dispatch`.

| Dimension | Impact |
|-----------|--------|
| Navigation | **ZERO** |
| Menus | **ZERO** |
| Screens | **ZERO** |
| Dashboards | **ZERO** |
| Permissions | **ZERO** |
| Workflows | **ZERO** |
| Forms | **ZERO** |
| Components | **ZERO** |
| User Journeys | **ZERO** |
| Role Experiences | **ZERO** |

**Frontend Impact Score: ZERO**
CI/CD infrastructure decisions have no user-visible frontend impact.

---

## ROD-004: Docker Build + Test CI Migration

**Decision:** Archive dead CI workflow files; optionally migrate unique steps to root CI.
**Collapse Outcome:** RESOLVED (archive) / OWNER_CONFIRMATION_ONLY (activation).

| Dimension | Impact |
|-----------|--------|
| All dimensions | **ZERO** |

**Frontend Impact Score: ZERO**

---

## Compliance/Decision/Banking/WhatsApp — Gateway Route Confirmation

**Decision:** Were routes confirmed for these 4 services?
**Collapse Outcome:** RESOLVED — All 4 routes confirmed (routes 22–25 in `routes.py`).

| Dimension | Impact | Detail |
|-----------|--------|--------|
| Navigation | **POSITIVE — ROUTES NOW CONFIRMED** | `/compliance`, `/decisions`, `/banking` (backend-only), `/whatsapp` (messaging channel) are all reachable |
| Menus | **POSITIVE** | `/compliance` and `/decisions` should appear in navigation for appropriate roles |
| Screens | **POSITIVE** | Decision Intelligence screen (`/decisions`), Compliance screen (`/compliance`) are buildable |
| Dashboards | **POSITIVE** | Decision Cards widget on dashboard can call `/api/v1/decisions` |
| Permissions | **CONFIRMED** | These routes use gateway JWT auth; service-level RBAC applies |
| Workflows | **CONFIRMED** | WF-007 (compliance reporting) confirmed end-to-end |
| Forms | **MINIMAL** | Compliance form fields discoverable in Phase 3 |
| Components | **MINIMAL** | Decision Card list component needed |
| User Journeys | **POSITIVE** | Compliance officer journey (generate + submit) confirmed |
| Role Experiences | **POSITIVE** | Admin sees compliance reports; Admin/Manager see decision cards |

**Frontend Impact Score: POSITIVE CONFIRMATION — previously uncertain screens are now confirmed buildable.**

Note: `/api/v1/banking` (bank-service) serves disbursement integration; it is called internally by payroll-service, not directly from a standalone banking screen. The `/banking` gateway route exists but the frontend interaction is through the `/payroll` workflow. No standalone `/banking` navigation screen is required.

`/api/v1/whatsapp` serves the WhatsApp messaging channel — it is a messaging integration, not a management screen. No standalone `/whatsapp` navigation screen is required for Phase 3.

---

## F-007 (Workflow) — Approval Inbox Route: `/approvals`

**Decision:** What UI route for the workflow approval inbox?
**Collapse Outcome:** RESOLVED — `/approvals`

| Dimension | Impact |
|-----------|--------|
| Navigation | **DEFINED** — `/approvals` route added to navigation for Manager + Admin |
| Menus | **DEFINED** — "Approvals" sidebar item for Manager and Admin roles |
| Screens | **DEFINED** — H05 approval inbox archetype screen at `/approvals` |
| Dashboards | **MINIMAL** — Pending approvals count widget on dashboard |
| Permissions | **DEFINED** — Visible to: Manager, Admin |
| Workflows | **CENTRAL** — This is where WF-002/003/004 approval steps are actioned |
| Forms | **DEFINED** — Approve/Reject form with optional reason field |
| Components | **DEFINED** — ApprovalCard component; status badge; action buttons |
| User Journeys | **CRITICAL** — Manager leave approval journey flows through this screen |
| Role Experiences | **Manager** — Central to Manager role experience. Employee role does NOT see this screen. |

**Frontend Impact Score: HIGH — This route decision was the key missing piece in the approval workflow UX. Now resolved.**

---

## F-008 (Audit) — Audit Log Viewer Route: `/audit`

**Decision:** What UI route for the audit log viewer?
**Collapse Outcome:** RESOLVED — `/audit`

| Dimension | Impact |
|-----------|--------|
| Navigation | **DEFINED** — `/audit` route; Admin-only visibility |
| Menus | **DEFINED** — "Audit Log" sidebar item, Admin role only |
| Screens | **DEFINED** — Audit log list view (H02 archetype); filter by entity, actor, date range |
| Dashboards | **MINIMAL** — No dashboard widget needed (audit is on-demand) |
| Permissions | **DEFINED** — Admin only (matches gateway RBAC on `/api/v1/audit`) |
| Workflows | **NONE** — Audit is read-only; no workflow |
| Forms | **MINIMAL** — Filter form only (date range, entity type) |
| Components | **DEFINED** — AuditRecordRow component; timestamp + actor + action + entity display |
| User Journeys | **DEFINED** — Admin investigates mutation history |
| Role Experiences | **Admin only** — No other role sees this screen |

**Frontend Impact Score: DEFINED — Audit screen is a clean read-only list; no complex UX decisions.**

---

## F-011 (Compliance) — Compliance Screen Route: `/compliance`

**Decision:** What UI route for compliance submission management?
**Collapse Outcome:** RESOLVED — `/compliance`

| Dimension | Impact |
|-----------|--------|
| Navigation | **DEFINED** — `/compliance` route; Admin + PayrollAdmin |
| Menus | **DEFINED** — "Compliance" sidebar item for Admin and PayrollAdmin |
| Screens | **DEFINED** — Report generation screen; filing status list |
| Dashboards | **MINIMAL** — Filing status indicator on Admin dashboard |
| Permissions | **DEFINED** — Admin, PayrollAdmin |
| Workflows | **DEFINED** — WF-007: generate → review → submit |
| Forms | **DEFINED** — Period selector, report type selector (FBR/EOBI/PESSI), submit trigger |
| Components | **DEFINED** — ComplianceReportCard; filing status badge; submission confirmation |
| User Journeys | **DEFINED** — PayrollAdmin generates and submits compliance report post-payroll |
| Role Experiences | **PayrollAdmin** — This is a core PayrollAdmin workflow post-payroll-run |

**Frontend Impact Score: DEFINED — Compliance screen is a high-value screen for the PayrollAdmin role.**

---

## F-013 (Automation) — Automation Rules Route: `/automations`

**Decision:** What UI route for automation engine management?
**Collapse Outcome:** RESOLVED — `/automations`

| Dimension | Impact |
|-----------|--------|
| Navigation | **DEFINED** — `/automations` route; Admin |
| Menus | **DEFINED** — "Automations" sidebar item |
| Screens | **DEFINED** — Rule list view; rule detail/edit |
| Dashboards | **MINIMAL** — Active automation count; no critical widget |
| Permissions | **MINIMAL** — No gateway RBAC restriction; Admin by convention |
| Workflows | **DEFINED** — View/edit event-triggered automation rules |
| Forms | **DEFINED** — Rule configuration form (trigger event, action, threshold) |
| Components | **DEFINED** — AutomationRuleCard; trigger/action display |
| User Journeys | **DEFINED** — Admin configures automated thresholds (e.g., attendance alerts) |
| Role Experiences | **Admin** — Power-user configuration screen |

**Frontend Impact Score: DEFINED — Standard CRUD list + detail pattern.**

---

## Shift/Roster Scheduling — Confirmed Out of Scope

**Decision:** Is shift/roster scheduling in scope?
**Collapse Outcome:** RESOLVED — OUT OF SCOPE.

| Dimension | Impact |
|-----------|--------|
| Navigation | **ZERO** — No `/roster` or `/shifts` route needed |
| All others | **ZERO** |

---

## WF-001/002/003 Implementation TBDs — Collapsed

**Decision:** Multiple TBD details in core workflows (document collection step, calendar update, payroll approval step).
**Collapse Outcome:** RESOLVED as implementation details.

| Workflow TBD | UX Impact |
|-------------|----------|
| WF-001 document collection step | Add document upload step in onboarding form. Implementation detail, not product scope. No navigation change. |
| WF-002 calendar update | Attendance display shows Leave status; implementation follows existing attendance pattern. No screen change. |
| WF-003 payroll approval optional | Default: no mandatory workflow approval step. PayrollAdmin reviews + initiates disbursement in one flow. No additional approval screen. |

**Frontend Impact: ZERO scope impact. Standard patterns apply.**

---

## FRONTEND READINESS TEST — FINAL EVALUATION

The mandate requires answering for each dimension: "Can any remaining unresolved decision materially alter this?"

| Dimension | Open Decisions Remaining | Verdict |
|-----------|------------------------|---------|
| Navigation | ZERO — all routes defined or collapsed | **CLEAR** |
| Menus | ZERO — role-based visibility fully defined | **CLEAR** |
| Screens | ZERO — all screens accounted for (21 routes defined) | **CLEAR** |
| Dashboards | ZERO — widget composition stable | **CLEAR** |
| Permissions | ZERO — 5 roles + 4 RBAC restrictions confirmed from code | **CLEAR** |
| Workflows | ZERO — WF-001 to WF-004, WF-007, WF-008 stable | **CLEAR** |
| Forms | ZERO — standard patterns; field details discoverable in Phase 3 | **CLEAR** |
| Components | ZERO — component patterns defined by archetypes | **CLEAR** |
| User Journeys | ZERO — all core journeys confirmed | **CLEAR** |
| Role Experiences | ZERO — per-role visibility fully defined | **CLEAR** |
| Product Scope | ZERO — 16 IMPLEMENTED, 6 ADD-ON, 2 PLANNED; out-of-scope confirmed | **CLEAR** |

**All 11 dimensions: CLEAR**

**FRONTEND READINESS TEST RESULT: PASS — All dimensions clear of unresolved decisions.**
