# PROJECT CHARTER

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-15
Owner: Human

---

## 1. PROJECT IDENTITY

**Product Name:** Meridian HCM (Human Capital Management)
**Working Name:** HRMS SaaS
**Repository Root:** `/` (monorepo)
**Evidence:** `/ops/HRMS PRODUCT SPEC.md`, `/backend/README.md`, `/design/hrms-doc-catalogue-v1.md`

**Naming Note:** "Meridian HCM" is the product/brand name; "HRMS" is used throughout the codebase, file paths, directory names, and contracts as the internal project identifier (e.g., `/backend`, `hrms-h*.json` contracts). Both terms refer to the same system — "HRMS" should be assumed when searching the repository for file/directory names, while "Meridian HCM" is the externally-facing product name.

---

## 2. PURPOSE

Meridian HCM is a multi-tenant SaaS Human Resource Management System targeting small-to-medium enterprises (SMEs). It provides a complete workforce management platform covering the full employee lifecycle from recruitment through offboarding, with Pakistan-specific statutory compliance built-in.

**Evidence Source:** `/ops/HRMS PRODUCT SPEC.md`, `/backend/docs/canon/release-scope.md`

---

## 3. TARGET USERS

| Role | Description | Primary Access Surface |
|------|-------------|----------------------|
| Admin | Tenant super-user, full HR access | All modules |
| Manager | Department-scoped HR operations | Employee mgmt, attendance, leave, performance |
| Employee | Self-service HR operations | Own attendance, leave, payslips, profile |
| PayrollAdmin | Payroll processing and disbursement | Payroll, banking, compliance |
| Recruiter | Hiring pipeline management | Job postings, candidates, interviews |
| Service | Machine principal (inter-service) | API-to-API only |

**Evidence Source:** `/backend/docs/canon/security-model.md`, `/backend/api-gateway/routes.py`

---

## 4. PRIMARY MARKET

- **Geography:** Pakistan (initial launch)
- **Compliance Focus:** FBR (Federal Board of Revenue), EOBI (Employee Old-age Benefits Institution), PESSI, Raast payment network
- **Segment:** SME (small-to-medium enterprises)

**Evidence Source:** `/backend/country/pakistan/`, `/backend/integrations/pakistan/`, `/backend/docs/canon/country-layer.md`

---

## 5. CORE CAPABILITIES (VERIFIED IMPLEMENTED)

These capabilities exist in working code confirmed by service directories and migration files. Each maps 1:1 to a feature entry in `FEATURE_SCOPE.md` via the F-XXX identifier shown:

1. **F-001 Workforce Management** — Employee records, org hierarchy (departments, business units, legal entities, locations, cost centers, grade bands, job positions)
2. **F-002 Attendance Management** — Attendance capture, validation, period closure, policy enforcement
3. **F-003 Leave Management** — Leave request submission, approval workflow, policy application
4. **F-004 Payroll Processing** — Payroll calculation, disbursement, period management, Pakistan tax engine
5. **F-005 Recruitment** — Job postings, candidate pipeline, interview scheduling, hire handoff
6. **F-006 Authentication & Authorization** — JWT-based auth, role-based access, session management, refresh token rotation
7. **F-007 Workflow Engine** — Centralized approval workflow orchestration
8. **F-008 Audit Logging** — Immutable mutation audit trail
9. **F-009 Notification System** — Multi-channel notifications (templates, delivery, preferences)
10. **F-010 Settings & Policy** — HR policy configuration (attendance rules, leave policies, payroll settings)
11. **F-011 Compliance** — Pakistan statutory compliance (FBR, EOBI, PESSI submissions). Gateway route unconfirmed — see `FEATURE_SCOPE.md` F-011
12. **F-012 Reporting & Analytics** — Reports, dashboards, predictive analytics
13. **F-013 Automation** — Event-triggered, scheduled, threshold-triggered automation rules
14. **F-014 Decision Intelligence** — Anomaly detection, Decision Cards, risk scoring. Gateway route unconfirmed — see `FEATURE_SCOPE.md` F-014
15. **F-015 Banking Integration** — Salary disbursement, Raast payments, bank reconciliation. Gateway route unconfirmed — see `FEATURE_SCOPE.md` F-015
16. **F-016 WhatsApp Channel** — WhatsApp as HR operations access channel. Gateway route unconfirmed — see `FEATURE_SCOPE.md` F-016

**Evidence Source:** `/backend/docs/canon/release-scope.md`, service directories, `docker-compose.yml`. See `FEATURE_SCOPE.md` for the authoritative per-feature status, service, port, and API prefix detail.

---

## 6. ADD-ON CAPABILITIES (CODE EXISTS, STATUS: ADD-ON)

Each maps 1:1 to a feature entry in `FEATURE_SCOPE.md` via the F-XXX identifier shown:

1. **F-017 Performance Management** — Review cycles, goals, feedback, calibration, PIPs
2. **F-018 Employee Engagement** — Surveys, sentiment analysis, aggregated results
3. **F-019 Helpdesk** — HR service tickets, SLAs, knowledge base
4. **F-020 Cross-Domain Search** — Cross-domain projection-backed search
5. **F-021 Expense Management** — Expense claims, receipts, approval, accounting export
6. **F-022 Integration Hub** — Outbound webhooks, connector dispatch, replay

**Evidence Source:** `/backend/docs/canon/release-scope.md`. See `FEATURE_SCOPE.md` for the authoritative per-feature status, service, port, and API prefix detail.

---

## 7. PLANNED CAPABILITIES (NOT YET IMPLEMENTED)

Each maps 1:1 to a feature entry in `FEATURE_SCOPE.md` via the F-XXX identifier shown:

1. **F-023 Travel Management** — Travel requests, itineraries, approvals
2. **F-024 Project Management** — Project planning, staffing, resource allocation

**Evidence Source:** `/backend/docs/canon/release-scope.md`, service directories show `travel-service` (port 8018) and `project-service` (port 8019) with PLANNED status. Note: the API Gateway ROUTES table includes `/api/v1/travel` and `/api/v1/projects` prefixes (routing is confirmed), but the underlying service implementations remain PLANNED per `FEATURE_SCOPE.md` F-023/F-024.

---

## 8. DEPLOYMENT MODEL

- **Architecture:** 24 containerized microservices + API Gateway + Next.js frontend
- **Database:** Single PostgreSQL 16 instance (logically partitioned by service/tenant)
- **Orchestration:** Docker Compose (development/initial deployment)
- **Port Exposure:** API Gateway (8000), Frontend (3000)
- **Multi-tenancy:** Row-level tenant isolation via `tenant_id` on all core tables

**Evidence Source:** `docker-compose.yml`, `/backend/deployment/`

---

## 9. AUTHORITATIVE CONSTRAINTS

1. All API calls route through the API Gateway (port 8000) — no direct service access from frontend
2. All tables enforce `(tenant_id, entity_id)` unique constraints for tenant isolation
3. Authentication is JWT (HS256) — enforced at gateway, exempt only for `/api/v1/auth/*`, `/health`, `/ready`, `/metrics`
4. All mutations must produce an audit record in audit-service
5. Country-specific compliance logic is isolated in `/backend/country/[country]/` — no country logic in core services
6. Outbox pattern governs all cross-service events — no direct DB writes across service boundaries

**Evidence Source:** `/backend/docker/api_gateway_service.py`, `/backend/deployment/migrations/004_persistence_normalization.sql`, `/backend/docs/canon/security-model.md`

---

## 10. OPEN QUESTIONS (TBD – REQUIRES VERIFICATION)

- [ ] Official product launch date or timeline
- [ ] Confirmed paying customer count or beta status
- [ ] Scaling strategy beyond Docker Compose (Kubernetes, managed cloud, etc.)
- [ ] Mobile application scope and delivery timeline
- [ ] SLA commitments to tenants
- [ ] Data residency requirements beyond Pakistan
