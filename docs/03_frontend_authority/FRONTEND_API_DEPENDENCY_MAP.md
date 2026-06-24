# FRONTEND API DEPENDENCY MAP

Status: Complete
Created: 2026-06-17
Phase: 3 — Frontend Authority Capture
Source: API_CONTRACT.md §4 (25 confirmed gateway routes), archetype-system-v1.md, SCREEN_CATALOG, ROUTE_CATALOG

---

## PURPOSE

Maps every confirmed API endpoint to its frontend consumer(s). No orphan APIs. No orphan UI elements. Every screen that calls an API is listed here, and every API that has a frontend consumer is identified.

**All API calls go through the gateway at `localhost:8000`.** Never call services directly.

---

## RESPONSE ENVELOPE HANDLING

| Pattern | Services | Envelope | Frontend Must |
|---------|----------|----------|---------------|
| Standard | 21 services | `{status, data, meta, error}` | Use `data` and `meta.pagination` normally |
| Non-standard | compliance, decision, banking, whatsapp | `{status, data, service}` | Handle missing `meta`; do not assume pagination; handle `service` identifier field |

The frontend API client must normalize both envelope shapes or all consumers of these 4 services must explicitly handle the difference.

---

## SERVICE 1: employee-service (`/api/v1/employees`, `/api/v1/departments`, `/api/v1/roles`)

Note: `/api/v1/roles` and `/api/v1/departments` are also served by employee-service — no separate gateway prefixes.

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/employees` | GET | Employees list, Dashboard widgets, Global search | H02-01, H01-01, H08-01 | Supports `?dept=`, `?status=`, `?search=`, `?page=`, `?limit=` |
| `/api/v1/employees/{id}` | GET | Employee profile | H03-01, H04-02 | Includes nested role, dept, grade band |
| `/api/v1/employees` | POST | Add employee form | H04-01 | Creates employee; status defaults to `active` |
| `/api/v1/employees/{id}` | PATCH | Edit employee form | H04-02 | Partial update |
| `/api/v1/employees/summary` | GET | HR Manager Dashboard KPI | H01-01 | Returns total_count, active_count, new_this_month |
| `/api/v1/employees/{id}/salary` | POST | Salary revision form | H04-09 | Creates SalaryRevision record |
| `/api/v1/departments` | GET | Departments list, Create employee (dept dropdown), Reporting filter | H02-02, H04-01, H04-03, H04-05 | Full department tree |
| `/api/v1/departments/{id}` | GET | Department detail | H03-02 | Includes employee list |
| `/api/v1/departments` | POST | Create department form | H04-03 | — |
| `/api/v1/departments/{id}` | PATCH | Edit department | H03-02 (edit action) | — |
| `/api/v1/roles` | GET | Roles list, Create employee (role dropdown), Create role | H02-03, H04-01, H04-04 | — |
| `/api/v1/roles/{id}` | GET | Role detail | H03-03 | — |
| `/api/v1/roles` | POST | Create role form | H04-04 | — |
| `/api/v1/roles/{id}` | PATCH | Edit role | H03-03 (edit action) | — |

---

## SERVICE 2: auth-service (`/api/v1/auth`)

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/auth/login` | POST | Login form | `/login` custom | Body: `{email, password, tenant_id}`; Returns JWT |
| `/api/v1/auth/logout` | POST | Logout button (topbar user menu) | All screens (topbar) | Invalidates refresh token |
| `/api/v1/auth/refresh` | POST | Auth interceptor (silent refresh) | Programmatic — all screens | Called automatically before token expiry |
| `/api/v1/auth/me` | GET | Auth context initialization | App init (all screens) | Returns current user claims; used to hydrate auth state |

---

## SERVICE 3: attendance-service (`/api/v1/attendance`)

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/attendance` | GET | Attendance list, Dashboard widgets | H02-09, H01-01, H01-02 | `?employee=`, `?from=`, `?to=`, `?status=`, `?me=true`, `?timeline=true` |
| `/api/v1/attendance/summary` | GET | Dashboard KPI, Attendance summary report | H01-01, H01-02, H07-03 | Returns daily/weekly/monthly aggregates |
| `/api/v1/attendance/summary?today=true` | GET | Dashboard "Attendance Rate Today" | H01-01 | — |

---

## SERVICE 4: leave-service (`/api/v1/leave`)

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/leave` | GET | Leave requests list, calendar, dashboard | H02-05, H06-01, H01-01, H01-02 | `?status=`, `?employee=`, `?type=`, `?from=`, `?to=`, `?me=true`, `?calendar=true`, `?all=true`, `?today=true` |
| `/api/v1/leave/{id}` | GET | Leave request detail, Approval inbox detail | H03-05, H05-01 | — |
| `/api/v1/leave` | POST | Raise leave request form | H04-06 | — |
| `/api/v1/leave/{id}` | PATCH | Approval inbox approve/reject | H05-01, H03-05 | — |
| `/api/v1/leave/balance` | GET | Employee dashboard KPI, Leave request form (show balance) | H01-02, H04-06, H03-01 Leave tab | `?employee_id=` |

---

## SERVICE 5: payroll-service (`/api/v1/payroll`)

Gateway-enforced: Admin, PayrollAdmin, Manager only. Employee can access own payslip by ID.

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/payroll` | GET | Payroll list, Dashboard widgets | H02-06, H01-01, H01-03 | `?period=`, `?status=`, `?employee=` |
| `/api/v1/payroll/{id}` | GET | Payroll record detail, Employee payslip | H03-06, H01-02 (own latest) | Employee sees own only |
| `/api/v1/payroll/run` | POST | Payroll run form | H04 (payroll run trigger) | Body: `{period, validate_only?}` |
| `/api/v1/payroll/status?period=current` | GET | Payroll Admin dashboard KPI | H01-03 | Returns current period run status |
| `/api/v1/payroll/summary` | GET | Payroll Admin dashboard | H01-03 | Returns cost totals, employee count |
| `/api/v1/payroll/summary?period=current` | GET | Dashboard KPI | H01-03 | — |
| `/api/v1/payroll?me=true&latest=true` | GET | Employee self-service dashboard | H01-02 | Returns most recent own payslip summary |
| `/api/v1/payroll/{id}/disburse` | POST | Payroll detail "Trigger Disbursement" | H03-06 | CAP-BNK-002 required |

---

## SERVICE 6: hiring-service (`/api/v1/hiring`)

Gateway-enforced: Admin, Manager, Recruiter only.

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/hiring/postings` | GET | Job postings list, Dashboard | H02-04, H01-04 | `?status=`, `?dept=`, `?search=` |
| `/api/v1/hiring/postings/{id}` | GET | Job posting detail | H03-04 | — |
| `/api/v1/hiring/postings` | POST | Create job posting form | H04-05 | 4-step form |
| `/api/v1/hiring/postings/{id}` | PATCH | Edit/close job posting | H03-04 | — |
| `/api/v1/hiring/candidates` | GET | Candidate pipeline, Dashboard | H13-01, H01-04 | `?posting_id=`, `?stage=`, `?status=` |
| `/api/v1/hiring/candidates/{id}` | GET | Candidate detail slide-over | H13 slide-over | — |
| `/api/v1/hiring/candidates/{id}` | PATCH | Stage advancement, hire/reject | H13-01, H13 slide-over | Body: `{stage: "Screening"|"Interviewing"|"Offered"|"Hired"|"Rejected"}` |
| `/api/v1/hiring/pipeline` | GET | Candidate pipeline board init | H13-01 | Returns staged groupings |
| `/api/v1/hiring/pipeline/summary` | GET | Recruitment Dashboard funnel | H01-04 | Per-stage counts for funnel chart |
| `/api/v1/hiring/summary` | GET | Hiring dashboard KPI row | H01-04 | Open positions, active candidates, this-week interviews |
| `/api/v1/hiring/interviews` | GET | Dashboard "interviews this week" | H01-04 | `?this_week=true` |
| `/api/v1/hiring/interviews` | POST | Schedule interview (candidate detail) | H13 slide-over | Body: `{candidate_id, date, type, interviewers}` |

---

## SERVICE 7: workflow-service (`/api/v1/workflows`)

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/workflows` | GET | Approval inbox, Dashboard pending count | H05-01, H01-01 | `?status=pending`, `?type=leave_approval|ewa_approval|expense_approval` |
| `/api/v1/workflows/{id}/steps/{step_id}` | PUT | Approval inbox action | H05-01 | Body: `{action: "approve"|"reject", reason?: "..."}` |
| `/api/v1/workflows/definitions` | GET | Workflow builder | H11-01 | — |
| `/api/v1/workflows/definitions` | POST | Workflow builder save | H11-01 | — |

---

## SERVICE 8: settings-service (`/api/v1/settings`)

Note: In-memory dict stub in dev — volatile. Frontend must not cache.

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/settings` | GET | Settings page, Leave request (types), Add employee (grade bands), Attendance rules | H10-01, H04-06, H04-01, H02-09 | Returns all settings as flat object |
| `/api/v1/settings` | PUT | Settings form save | H10-01 | Full replacement — not PATCH |

---

## SERVICE 9: notification-service (`/api/v1/notifications`)

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/notifications` | GET | Notifications inbox, Topbar bell badge, Dashboard preview | H09-01, topbar, H01-02 | `?me=true`, `?unread=true`, `?folder=`, `?limit=` |
| `/api/v1/notifications/{id}/read` | PATCH | Notification item "Mark read" | H09-01, topbar notification click | — |
| `/api/v1/notifications` | POST | Admin broadcast (if supported) | H10-01 or admin action | CAP-NOT-002 |

---

## SERVICE 10: reporting-analytics-service (`/api/v1/reporting`)

Gateway-enforced: Admin, Manager only.

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/reporting/dashboards` | GET | HR Analytics page, HR Dashboard widgets | H07-01, H01-01 | `?widget=headcount|attrition|...` |
| `/api/v1/reporting/payroll` | GET | Payroll reports tab | H07-02 | `?widget=cost_trend|dept_cost` |
| `/api/v1/reporting/attendance` | GET | Attendance summary tab | H07-03 | — |
| `/api/v1/reporting/hiring` | GET | Recruitment dashboard charts | H01-04 | `?widget=days_to_hire` |
| `/api/v1/reporting/custom` | POST | Report builder | H11-03 | Body: `{dimensions, filters, schedule}` |

---

## SERVICE 11: compliance-service (`/api/v1/compliance`)

**Non-standard envelope: `{status, data, service}` — no `meta` field.**

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/compliance` | GET | Compliance reports page, Dashboard (upcoming deadlines) | H07-05, H01-03 | `?upcoming=true`, `?period=` |
| `/api/v1/compliance/generate` | POST | Compliance generate button | H07-05 | Body: `{period, type}` |
| `/api/v1/compliance/{id}/export` | GET | Compliance report download | H07-05 | Returns file download |

---

## SERVICE 12: decision-engine-service (`/api/v1/decisions`)

**Non-standard envelope: `{status, data, service}` — no `meta` field.**
**In-memory only — DecisionCard entities are not persisted. List may be empty after service restart.**

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/decisions` | GET | Decision cards page, Payroll dashboard | `/decisions`, H01-03 | `?scope=payroll|dept|global`, `?severity=critical|notify|passive` |
| `/api/v1/decisions/{id}/resolve` | POST | Decision card "Mark Resolved" button | `/decisions` | CAP-DEC-002 (Admin only) |

---

## SERVICE 13: banking-service (`/api/v1/banking`)

**Non-standard envelope: `{status, data, service}` — no `meta` field.**
No standalone frontend banking screen. Banking surfaces through payroll detail.

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/banking/disburse` | POST | Payroll detail "Trigger Disbursement" | H03-06 | CAP-BNK-002; triggered via payroll-service which calls banking-service internally. Frontend calls `/api/v1/payroll/{id}/disburse`. |
| `/api/v1/banking/status/{payroll_id}` | GET | Payroll detail disbursement status | H03-06 | CAP-BNK-001 |

---

## SERVICE 14: whatsapp-service (`/api/v1/whatsapp`)

**Non-standard envelope: `{status, data, service}` — no `meta` field.**
No standalone frontend WhatsApp screen. WhatsApp is a backend notification integration.

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/whatsapp/config` | GET / PUT | Settings → Integrations section (chrome-only in Phase 3) | H10-01 | CAP-WA-001; Admin only; chrome-only — no backend persistence for Integrations tab yet |

---

## SERVICE 15: search-service (`/api/v1/search`)

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/search` | GET | Global search page | H08-01 | `?q=`, `?type=employee|candidate|document` |

---

## SERVICE 16: ewa-service (`/api/v1/ewa`)

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/ewa/request` | POST | EWA request form | `/employees/[id]/ewa` | CAP-EWA-001 (Employee own) |
| `/api/v1/ewa` | GET | Approval inbox (EWA type) | H05-01 | `?status=pending`; CAP-EWA-002 (Manager/PA/Admin) |
| `/api/v1/ewa/{id}` | PATCH | Approval inbox approve/reject | H05-01 | Action via workflow-service step |

---

## SERVICE 17: audit-service (`/api/v1/audit`)

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/audit` | GET | Audit log list | `/audit` H02 | `?user=`, `?action=`, `?entity=`, `?from=`, `?to=`; Admin only; AuditRecord = PROHIBITED from modification |
| `/api/v1/audit/{id}` | GET | Audit log detail (inline expand) | `/audit` inline | Read-only |
| `/api/v1/audit?export=csv` | GET | Audit log export | `/audit` | Download CSV |

---

## SERVICE 18: performance-service (`/api/v1/performance`)

**ADD-ON — F-017. Implementation deferred.**

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/performance/reviews` | GET | Performance reviews list | `/performance/reviews` ADD-ON | Deferred |
| `/api/v1/performance/reviews/{id}` | GET | Performance review detail | `/performance/reviews/[id]` ADD-ON | Deferred |
| `/api/v1/performance/summary` | GET | Performance dashboard | `/performance` ADD-ON | Deferred |

---

## SERVICE 19: automations-service (`/api/v1/automations`)

| Endpoint | Method | Frontend Consumer(s) | Screen(s) | Notes |
|----------|--------|----------------------|-----------|-------|
| `/api/v1/automations` | GET | Automations list | `/automations` | Admin only; CAP-AUT-002 |
| `/api/v1/automations` | POST | Create automation rule | `/automations` | — |
| `/api/v1/automations/{id}` | PATCH | Edit/enable/disable rule | `/automations` | — |

---

## SERVICE 20: integration-service (`/api/v1/integrations`)

Settings → Integrations section is chrome-only in Phase 3 (no backend persistence for Integrations tab). Integration-service is present in system but has no confirmed frontend endpoints for Phase 3 core screens.

---

## SERVICE 21: helpdesk-service (`/api/v1/helpdesk`)

**ADD-ON — F-019. Implementation deferred.**

---

## SERVICE 22–25: (engagement, expense, travel — ADD-ON/PLANNED)

ADD-ON and PLANNED services have no Phase 3 core frontend API calls. Their endpoints are noted in the ADD-ON screen entries of FRONTEND_SCREEN_CATALOG.md.

---

## API CONSUMER COMPLETENESS CHECK

| Gateway Route | Service | Phase 3 Frontend Consumer | Status |
|--------------|---------|--------------------------|--------|
| `/api/v1/employees` | employee-service | ✅ H02-01, H03-01, H04-01/02/03, H01-01 | Covered |
| `/api/v1/departments` | employee-service | ✅ H02-02, H03-02, H04-01/03/05 | Covered |
| `/api/v1/roles` | employee-service | ✅ H02-03, H03-03, H04-01/04 | Covered |
| `/api/v1/auth` | auth-service | ✅ Login, logout, token refresh, auth init | Covered |
| `/api/v1/attendance` | attendance-service | ✅ H02-09, H06-02, H01-01/02, H07-03 | Covered |
| `/api/v1/leave` | leave-service | ✅ H02-05, H03-05, H04-06, H05-01, H06-01, H01-01/02 | Covered |
| `/api/v1/payroll` | payroll-service | ✅ H02-06, H03-06, H01-02/03, payroll run | Covered |
| `/api/v1/hiring` | hiring-service | ✅ H02-04, H03-04, H04-05, H13-01, H01-04 | Covered |
| `/api/v1/workflows` | workflow-service | ✅ H05-01, H11-01, H01-01 | Covered |
| `/api/v1/settings` | settings-service | ✅ H10-01, H04-06, H04-01 | Covered |
| `/api/v1/notifications` | notification-service | ✅ H09-01, topbar, H01-02 | Covered |
| `/api/v1/reporting` | reporting-analytics | ✅ H07-01/02/03, H01-01/03/04, H11-03 | Covered |
| `/api/v1/compliance` | compliance-service | ✅ H07-05, H01-03 | Covered (non-standard envelope) |
| `/api/v1/decisions` | decision-engine | ✅ `/decisions`, H01-03 | Covered (non-standard envelope) |
| `/api/v1/banking` | banking-service | ✅ H03-06 (via payroll-service proxy) | Covered (non-standard envelope) |
| `/api/v1/whatsapp` | whatsapp-service | ✅ H10-01 settings (chrome-only) | Covered (non-standard envelope) |
| `/api/v1/search` | search-service | ✅ H08-01 | Covered |
| `/api/v1/ewa` | ewa-service | ✅ Employee EWA form, H05-01 | Covered |
| `/api/v1/audit` | audit-service | ✅ `/audit` H02 | Covered |
| `/api/v1/automations` | automations-service | ✅ `/automations` | Covered |
| `/api/v1/performance` | performance-service | ADD-ON deferred | Deferred |
| `/api/v1/engagement` | engagement-service | ADD-ON deferred | Deferred |
| `/api/v1/expenses` | expense-service | ADD-ON deferred | Deferred |
| `/api/v1/helpdesk` | helpdesk-service | ADD-ON deferred | Deferred |
| `/api/v1/integrations` | integration-service | Chrome-only in Phase 3 | Deferred (Phase 4+) |

**All 25 gateway routes accounted for.** 20 with Phase 3 core consumers. 4 ADD-ON deferred. 1 chrome-only (integrations).
