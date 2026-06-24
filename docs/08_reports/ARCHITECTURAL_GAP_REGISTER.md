# ARCHITECTURAL GAP REGISTER

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This register lists all gaps identified during governance documentation creation: missing architecture, workflows, domain entities, contracts, permissions, testing coverage, deployment knowledge, duplicate documentation, conflicting documentation, and unverified assumptions.

---

## 1. MISSING ARCHITECTURE DOCUMENTATION

| Gap ID | Description | Affected Area | Severity |
|--------|-------------|----------------|----------|
| GAP-A-001 | No frontend architecture document describing Next.js App Router structure, component hierarchy, or state management conventions | Frontend | Medium |
| GAP-A-002 | No deployment runbook (how to deploy, rollback, scale) | Deployment | High |
| GAP-A-003 | No documented caching strategy (none exists in code — confirmed absence, not just missing docs) | Backend | Medium |
| GAP-A-004 | No documented monitoring/observability stack (metrics endpoint mentioned but implementation undocumented) | Cross-cutting | High |
| GAP-A-005 | No disaster recovery / backup documentation | Infrastructure | High |
| GAP-A-006 | Mobile app architecture undocumented (`/backend/mobile/` exists but scope unclear) | Mobile | Medium |

---

## 2. MISSING WORKFLOWS

| Gap ID | Description | Affected Area | Severity |
|--------|-------------|----------------|----------|
| GAP-W-001 | Employee offboarding workflow not documented (only onboarding covered) | HR Lifecycle | High |
| GAP-W-002 | Shift/roster scheduling workflow — no shift-service found; unclear if attendance-service covers this | Attendance | Medium |
| GAP-W-003 | Survey distribution and response collection workflow (engagement-service) undocumented | Engagement | Low (ADD-ON) |
| GAP-W-004 | Expense reimbursement-to-bank workflow not traced (does it touch bank-service?) | Expense | Low (ADD-ON) |
| GAP-W-005 | Multi-level leave approval (more than one manager in chain) not detailed | Leave | Medium |
| GAP-W-006 | Performance review → compensation adjustment linkage not documented | Performance/Payroll | Medium |

---

## 3. MISSING DOMAIN ENTITIES / SCHEMA KNOWLEDGE

| Gap ID | Description | Affected Area | Severity |
|--------|-------------|----------------|----------|
| GAP-D-001 | `011_addon_domains.sql` not read — entities for performance, engagement, helpdesk, search, expense, integration possibly underspecified | Multiple ADD-ON services | Medium |
| GAP-D-002 | `012_compensation_domain.sql` — compensation entities beyond PayrollRecord not fully cataloged | Payroll | Medium |
| GAP-D-003 | `013_travel_domain.sql` — Travel entities exist in schema but service is PLANNED/not implemented | Travel | Low |
| GAP-D-004 | Decision Card entity structure not fully documented (decision-service) | Decision Intelligence | Medium |
| GAP-D-005 | Helpdesk entities (Ticket, SLA, KnowledgeBase article) not documented | Helpdesk | Low (ADD-ON) |
| GAP-D-006 | Search-service projection entities/read models not documented | Search | Low (ADD-ON) |

---

## 4. MISSING CONTRACTS

| Gap ID | Description | Affected Area | Severity |
|--------|-------------|----------------|----------|
| GAP-C-001 | engagement-service API prefix not present in gateway route table — unclear if `/api/v1/engagement` exists | Engagement | Medium |
| GAP-C-002 | Exact endpoint signatures for performance-service (`/api/v1/performance/*`) not verified beyond prefix | Performance | Medium |
| GAP-C-003 | Exact endpoint for payroll run initiation (`POST /api/v1/payroll/run` assumed but not verified) | Payroll | High |
| GAP-C-004 | Decision Card resolution endpoint not verified | Decision Intelligence | Low |
| GAP-C-005 | Compliance submission endpoints (FBR/EOBI/PESSI) not enumerated beyond adapter file names | Compliance | Medium |
| GAP-C-006 | WhatsApp service API contract (identity mapping, message routing endpoints) not documented | WhatsApp | Medium |

---

## 5. MISSING PERMISSIONS DOCUMENTATION

| Gap ID | Description | Affected Area | Severity |
|--------|-------------|----------------|----------|
| GAP-P-001 | Full capability matrix (40+ capabilities) exists in `/backend/docs/canon/capability-matrix.md` but not cross-referenced into stitching contract per-endpoint | Cross-cutting | Medium |
| GAP-P-002 | Service role scope-enforcement for ADD-ON services (performance, engagement, helpdesk, search, expense, integration) not verified | ADD-ON services | Medium |
| GAP-P-003 | "Service" role usage — which services call which other services with Service-scoped tokens — not mapped | Cross-cutting | Medium |

---

## 6. MISSING TESTING COVERAGE KNOWLEDGE

| Gap ID | Description | Affected Area | Severity |
|--------|-------------|----------------|----------|
| GAP-T-001 | No consolidated test coverage report (% coverage by service) | Cross-cutting | Medium |
| GAP-T-002 | Helpdesk, integration-service, whatsapp-service, travel-service, project-service have no identified test files | Multiple services | Medium |
| GAP-T-003 | Frontend has no identified test suite (no Jest/Playwright/Cypress config found) | Frontend | High |
| GAP-T-004 | E2E test coverage across service boundaries not documented | Cross-cutting | Medium |

---

## 7. MISSING DEPLOYMENT KNOWLEDGE

| Gap ID | Description | Affected Area | Severity |
|--------|-------------|----------------|----------|
| GAP-DEP-001 | Production deployment target unknown (Docker Compose appears dev-oriented) | Infrastructure | High |
| GAP-DEP-002 | Dockerfile.ui / NGINX configuration for frontend not examined | Frontend Deployment | Medium |
| GAP-DEP-003 | Secrets management strategy (JWT_SECRET, DB password) for production not documented | Security/Deployment | High |
| GAP-DEP-004 | Backup/restore procedure for PostgreSQL not documented | Database | High |
| GAP-DEP-005 | Zero-downtime migration strategy not documented | Database | Medium |

---

## 8. DUPLICATE DOCUMENTATION

| Gap ID | Description | Files Involved | Severity |
|--------|-------------|-----------------|----------|
| GAP-DUP-001 | Multiple progress-tracking files in `/ops/` with overlapping purpose (`build-progress.md`, `hrms-progress.md`, `tracker.md`, `normalisation-tracker.md`) | `/ops/*.md` | Low |
| GAP-DUP-002 | Domain model exists in both `/backend/docs/canon/domain-model.md` and now `docs/00_authority/DOMAIN_MODEL.md` — the latter is a governance-layer summary; canon doc remains implementation-detail source of truth | `/backend/docs/canon/domain-model.md`, `docs/00_authority/DOMAIN_MODEL.md` | Low (intentional layering, but must stay in sync) |

---

## 9. CONFLICTING DOCUMENTATION

| Gap ID | Description | Files Involved | Severity |
|--------|-------------|-----------------|----------|
| GAP-CONF-001 | None identified during this review. A full conflict-detection pass would require reading all 47 entries in `/design/hrms-doc-catalogue-v1.md` against canon docs — not performed due to scope. | TBD – REQUIRES VERIFICATION | TBD |

---

## 10. UNVERIFIED ASSUMPTIONS

| Gap ID | Assumption | Where Used | Severity |
|--------|-----------|------------|----------|
| GAP-U-001 | Payroll run is triggered via `POST /api/v1/payroll/run` | `FULLSTACK_STITCHING_CONTRACT.md` T-006 | High |
| GAP-U-002 | Employee status auto-transitions to OnLeave during approved leave | `PRODUCT_WORKFLOWS.md` WF-002 | Medium |
| GAP-U-003 | API Gateway exempts only `/health`, `/ready`, `/metrics`, `/api/v1/auth/*` from JWT — full exemption list not verified beyond initial grep | `AI_OPERATING_CONTEXT.md` | High |
| GAP-U-004 | Audit records table has no soft-delete or update mechanism (assumed fully immutable) | `DECISION_ESCALATION_MATRIX.md`, `DOMAIN_MODEL.md` | High |
| GAP-U-005 | Frontend `/backend/ui` is the sole UI; `/frontend` directory (HTML seeds) is not in active use | `PROJECT_CHARTER.md` | Medium |
| GAP-U-006 | Decision Cards are advisory-only (no automatic enforcement actions) | `FULLSTACK_STITCHING_CONTRACT.md` T-012 | Low |

---

## PRIORITIZED REMEDIATION ORDER

1. **GAP-U-003** — Verify full JWT exemption list (security-critical)
2. **GAP-U-004** — Verify audit_records immutability enforcement (compliance-critical)
3. **GAP-C-003** — Verify payroll run endpoint (core business workflow)
4. **GAP-DEP-001, GAP-DEP-003** — Production deployment and secrets strategy (cannot go to production without this)
5. **GAP-T-003** — Frontend test coverage (quality risk)
6. **GAP-A-001, GAP-A-002** — Frontend architecture and deployment runbook docs (Phase 2 candidates)
7. Remaining gaps — address opportunistically during Phase 2+ work
