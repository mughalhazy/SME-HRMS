# CONTRACT VERSION REGISTRY

Status: Draft
Authority Level: Medium
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This document is the authoritative register of all API versions and frontend page-archetype contracts in the system. It enables consumers (frontend, integrators, AI sessions) to answer: which API version is current, which contracts exist for which domain, and what each contract covers.

**Evidence Sources:**
- `/backend/api-gateway/routes.py` — API_VERSION_PREFIX, ROUTES tuple
- `/contracts/hrms-h*.json` — frontend page-archetype contracts
- `docs/07_governance/AI_OPERATING_CONTEXT.md` FD-010 — `/api/v1/` versioning frozen decision
- `docs/07_governance/AI_OPERATING_CONTEXT.md` OAQ-010 — API v2 timeline is an open question (Human decides)

---

## API VERSION STATUS

| Version | Status | Since | Notes |
|---------|--------|-------|-------|
| `/api/v1/` | **Active — all 21 gateway routes** | FD-010 (frozen) | Only version in production; defined via `API_VERSION_PREFIX = "/api/v1"` in `routes.py` |
| `/api/v2/` | **Not yet planned** | — | OAQ-010: introduction timeline is an open architectural question; Human decides |

The gateway also accepts **legacy bare-prefix paths** (e.g. `/employees` without the `/api/v1` prefix) via `is_legacy_route()` in `routes.py`, but the canonical and recommended form is `/api/v1/{prefix}`.

---

## GATEWAY ROUTE REGISTRY (v1)

All 21 confirmed routes sourced from `/backend/api-gateway/routes.py` ROUTES tuple and `/backend/deployment/config/gateway-routes.json`:

| # | Route Name | Full Prefix | Upstream Service | F-ID | Status |
|---|-----------|------------|-----------------|------|--------|
| 1 | employees | `/api/v1/employees` | employee-service | F-001 | CONFIRMED |
| 2 | departments | `/api/v1/departments` | employee-service | F-001 | CONFIRMED |
| 3 | performance | `/api/v1/performance` | performance-service | F-017 | CONFIRMED, ADD-ON |
| 4 | attendance | `/api/v1/attendance` | attendance-service | F-002 | CONFIRMED |
| 5 | leave | `/api/v1/leave` | leave-service | F-003 | CONFIRMED |
| 6 | travel | `/api/v1/travel` | travel-service | F-023 | CONFIRMED route; service PLANNED |
| 7 | projects | `/api/v1/projects` | project-service | F-024 | CONFIRMED route; service PLANNED |
| 8 | payroll | `/api/v1/payroll` | payroll-service | F-004 | CONFIRMED |
| 9 | hiring | `/api/v1/hiring` | hiring-service | F-005 | CONFIRMED |
| 10 | auth | `/api/v1/auth` | auth-service | F-006 | CONFIRMED (exempt from JWT) |
| 11 | workflows | `/api/v1/workflows` | workflow-service | F-007 | CONFIRMED |
| 12 | audit | `/api/v1/audit` | audit-service | F-008 | CONFIRMED |
| 13 | notifications | `/api/v1/notifications` | notification-service | F-009 | CONFIRMED |
| 14 | engagement | `/api/v1/engagement` | engagement-service | F-018 | CONFIRMED, ADD-ON |
| 15 | helpdesk | `/api/v1/helpdesk` | helpdesk-service | F-019 | CONFIRMED, ADD-ON |
| 16 | reporting | `/api/v1/reporting` | reporting-analytics-service | F-012 | CONFIRMED |
| 17 | search | `/api/v1/search` | search-service | F-020 | CONFIRMED, ADD-ON |
| 18 | expense | `/api/v1/expense` | expense-service | F-021 | CONFIRMED, ADD-ON |
| 19 | integrations | `/api/v1/integrations` | integration-service | F-022 | CONFIRMED, ADD-ON |
| 20 | automations | `/api/v1/automations` | automation-service | F-013 | CONFIRMED |
| 21 | settings | `/api/v1/settings` | settings-service | F-010 | CONFIRMED |

**RESOLVED (2026-06-17 — Phase 2.8 TR-003 to TR-006):** All 4 were confirmed in `routes.py` lines 52–55 and `gateway-routes.json` lines 25–28. Non-standard envelope `{status, data, service}`.

| Service | Port | Path Prefix | Status |
|---------|------|------------|--------|
| compliance-service | 8021 | `/api/v1/compliance` | CONFIRMED — gateway route 22 (TR-003) |
| decision-service | 8022 | `/api/v1/decisions` | CONFIRMED — gateway route 23 (TR-004) |
| bank-service | 8023 | `/api/v1/banking` | CONFIRMED — gateway route 24 (TR-005) |
| whatsapp-service | 8024 | `/api/v1/whatsapp` | CONFIRMED — gateway route 25 (TR-006) |

See `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` §2 for full rationale.

---

## FRONTEND CONTRACT REGISTRY

Contracts are stored in `/contracts/hrms-h*.json`. Each file encodes a page-archetype contract: data requirements, API dependencies, form fields, and UI layout for a specific screen type.

### Archetype Key

| Archetype | Type | Pattern |
|-----------|------|---------|
| H01 | Dashboard (role-specific views) | Summary metrics, KPIs, quick actions |
| H02 | List / Data Table | Paginated entity lists with filters |
| H03 | Detail / Profile | Single-entity detail view |
| H04 | Create / Edit Form | Data entry forms |
| H05 | Approval Inbox | Pending workflow actions |
| H07 | Reports / Analytics | Aggregated/filtered reporting views |
| H08 | Global Search | Cross-domain search interface |
| H09 | Notifications Inbox | Notification list and read management |
| H10 | Settings / Configuration | HR policy configuration screens |
| H11 | Builder / Wizard | Multi-step creation wizards |
| H12 | Helpdesk | Ticket management interface |
| H13 | Pipeline | Kanban/stage-based workflow UI |

### Contract File Index

| Contract File | Archetype | Domain | Key API Prefix(es) |
|--------------|-----------|--------|-------------------|
| `hrms-h01-employee-self-service-contract.json` | H01 Dashboard | Self-Service | `/api/v1/employees`, `/api/v1/attendance`, `/api/v1/leave` |
| `hrms-h01-hr-manager-dashboard-contract.json` | H01 Dashboard | Manager | `/api/v1/employees`, `/api/v1/attendance`, `/api/v1/leave`, `/api/v1/workflows` |
| `hrms-h01-payroll-admin-dashboard-contract.json` | H01 Dashboard | Payroll | `/api/v1/payroll` |
| `hrms-h01-recruitment-dashboard-contract.json` | H01 Dashboard | Recruitment | `/api/v1/hiring` |
| `hrms-h02-attendance-records-contract.json` | H02 List | Attendance | `/api/v1/attendance` |
| `hrms-h02-departments-contract.json` | H02 List | Org Structure | `/api/v1/departments` |
| `hrms-h02-documents-contract.json` | H02 List | Documents | TBD – REQUIRES VERIFICATION (no `/api/v1/documents` gateway route) |
| `hrms-h02-employees-contract.json` | H02 List | Workforce | `/api/v1/employees` |
| `hrms-h02-expense-claims-contract.json` | H02 List | Expense | `/api/v1/expense` |
| `hrms-h02-job-postings-contract.json` | H02 List | Hiring | `/api/v1/hiring` |
| `hrms-h02-leave-requests-contract.json` | H02 List | Leave | `/api/v1/leave` |
| `hrms-h02-payroll-records-contract.json` | H02 List | Payroll | `/api/v1/payroll` |
| `hrms-h02-performance-reviews-contract.json` | H02 List | Performance | `/api/v1/performance` |
| `hrms-h02-roles-contract.json` | H02 List | Auth/Roles | `/api/v1/employees` — roles served by employee-service (C-004; employee_api.py `get_roles`) |
| `hrms-h02-travel-requests-contract.json` | H02 List | Travel | `/api/v1/travel` |
| `hrms-h03-department-detail-contract.json` | H03 Detail | Org Structure | `/api/v1/departments` |
| `hrms-h03-employee-profile-contract.json` | H03 Detail | Workforce | `/api/v1/employees` |
| `hrms-h03-expense-claim-detail-contract.json` | H03 Detail | Expense | `/api/v1/expense` |
| `hrms-h03-job-posting-detail-contract.json` | H03 Detail | Hiring | `/api/v1/hiring` |
| `hrms-h03-leave-request-detail-contract.json` | H03 Detail | Leave | `/api/v1/leave` |
| `hrms-h03-payroll-record-detail-contract.json` | H03 Detail | Payroll | `/api/v1/payroll` |
| `hrms-h03-performance-review-detail-contract.json` | H03 Detail | Performance | `/api/v1/performance` |
| `hrms-h03-role-detail-contract.json` | H03 Detail | Auth/Roles | `/api/v1/employees` — roles served by employee-service (C-004) |
| `hrms-h04-add-employee-contract.json` | H04 Form | Workforce | `/api/v1/employees`, `/api/v1/departments` |
| `hrms-h04-create-department-contract.json` | H04 Form | Org Structure | `/api/v1/departments` |
| `hrms-h04-create-job-posting-contract.json` | H04 Form | Hiring | `/api/v1/hiring` |
| `hrms-h04-create-role-contract.json` | H04 Form | Auth/Roles | `/api/v1/employees` — roles served by employee-service (C-004; employee_api.py `post_roles`) |
| `hrms-h04-edit-employee-contract.json` | H04 Form | Workforce | `/api/v1/employees` |
| `hrms-h04-raise-expense-claim-contract.json` | H04 Form | Expense | `/api/v1/expense` |
| `hrms-h04-raise-leave-request-contract.json` | H04 Form | Leave | `/api/v1/leave` |
| `hrms-h04-raise-travel-request-contract.json` | H04 Form | Travel | `/api/v1/travel` |
| `hrms-h04-salary-revision-contract.json` | H04 Form | Compensation | `/api/v1/payroll` (TBD – REQUIRES VERIFICATION exact sub-path) |
| `hrms-h05-approval-inbox-contract.json` | H05 Approval | Workflow | `/api/v1/workflows` |
| `hrms-h07-attendance-summary-contract.json` | H07 Report | Attendance | `/api/v1/reporting`, `/api/v1/attendance` |
| `hrms-h07-compliance-reports-contract.json` | H07 Report | Compliance | `/api/v1/reporting`, `/api/v1/compliance` (gateway route 22 — CONFIRMED, TR-003) |
| `hrms-h07-engagement-results-contract.json` | H07 Report | Engagement | `/api/v1/engagement`, `/api/v1/reporting` |
| `hrms-h07-hr-analytics-contract.json` | H07 Report | Analytics | `/api/v1/reporting` |
| `hrms-h07-payroll-reports-contract.json` | H07 Report | Payroll | `/api/v1/payroll`, `/api/v1/reporting` |
| `hrms-h08-global-search-contract.json` | H08 Search | Cross-Domain | `/api/v1/search` |
| `hrms-h09-notifications-inbox-contract.json` | H09 Notifications | Notifications | `/api/v1/notifications` |
| `hrms-h10-org-settings-contract.json` | H10 Settings | Settings | `/api/v1/settings` |
| `hrms-h11-report-builder-contract.json` | H11 Builder | Reporting | `/api/v1/reporting` |
| `hrms-h11-survey-builder-contract.json` | H11 Builder | Engagement | `/api/v1/engagement` |
| `hrms-h11-workflow-builder-contract.json` | H11 Builder | Workflow | `/api/v1/workflows` |
| `hrms-h12-helpdesk-contract.json` | H12 Helpdesk | Helpdesk | `/api/v1/helpdesk` |
| `hrms-h13-candidate-pipeline-contract.json` | H13 Pipeline | Hiring | `/api/v1/hiring` |
| `hrms-schema-template.json` | Template | — | Contract schema template, not a page contract |

---

## CONTRACT GOVERNANCE NOTES

- **Breaking change definition:** Per `AI_OPERATING_CONTEXT.md` CONTRACT_COMPATIBILITY_POLICY: any change to an existing endpoint's method, path, required parameters, or response shape is a breaking change requiring a new version or explicit deprecation.
- **Non-breaking changes:** Adding optional query parameters, adding fields to response `data`, adding new endpoints.
- **Version change protocol:** Any v2 introduction must update this registry, add an ADR entry in `docs/06_decisions/`, and update `AI_OPERATING_CONTEXT.md` FD-010 (or supersede it with a new FD). Per OAQ-010, the Human decides v2 timing.
- **`hrms-h02-documents-contract.json` gap:** This contract exists but there is no `/api/v1/documents` gateway route in the ROUTES table — see `docs/08_reports/BACKEND_GAP_REGISTER.md`.
