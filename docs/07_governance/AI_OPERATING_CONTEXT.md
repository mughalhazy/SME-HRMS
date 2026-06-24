# AI OPERATING CONTEXT

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-17
Owner: Human

---

## PURPOSE

This document is the first document any AI session should read before working on this project. It provides the authoritative operating context so that AI sessions can make correct decisions without reverse-engineering the source code.

**A new AI session reading only this document should be able to answer:**
- What does this SaaS do?
- Who are the users?
- What are the primary workflows?
- What are the core domain entities?
- What architectural decisions are already made?
- What areas are frozen?
- What areas require approval before modification?

---

## CURRENT_PHASE

**Phase:** Phase 4 — Frontend Implementation (AUTHORIZED)

**What This Means:**
- Phase 2 (Backend Authority Capture): COMPLETE — all 19 gaps resolved
- Phase 3 (Frontend Authority Capture): COMPLETE — 12 authority documents, 55 components, 55 routes
- Phase 3.25 (Autonomous Gap Elimination): COMPLETE — 93+ TBDs eliminated; REPOSITORY FULLY DETERMINED
- Mandate 2 (Comprehensive Gap Closure): COMPLETE — 116 items classified
- OWNER-REQUIRED Compression: COMPLETE — reduced to 5 genuine credential items (2026-06-18)
- Phase 4 frontend implementation is AUTHORIZED and UNBLOCKED

**Active Work Constraints:**
- Documentation updates: AUTONOMOUS
- Test additions: AUTONOMOUS
- Repository hygiene (archive maintenance, documentation relocation, .gitignore improvements, report generation): SAFE_REPOSITORY_HYGIENE — see `SAFE_REPOSITORY_HYGIENE_POLICY.md`
- Frontend implementation (`backend/ui/`): AUTHORIZED per Phase 4 clearance
- Bug fixes in existing services: REQUIRES APPROVAL
- New features: PROHIBITED without human authorization

**Phase 4 Conditions (must be observed during implementation):**
- C-001: compliance, decisions, banking, whatsapp use `{status, data, service}` envelope (no `meta`)
- C-002: Settings-service is in-memory stub; do not cache aggressively
- C-003: Frontend stays at `backend/ui/` through Phase 4
- C-004: `/api/v1/roles` and `/api/v1/org` are served by employee-service (no separate prefix)

**Final classified register:** `docs/08_reports/FINAL_CLASSIFIED_REGISTER.md`
**OWNER-REQUIRED items (5):** FBR / EOBI / PESSI credentials, Raast credentials, WhatsApp Business API account — none block frontend implementation.

---

## SYSTEM_IDENTITY

**Product:** Meridian HCM — Multi-tenant SaaS HR Management System
**Target Market:** SME enterprises, Pakistan launch
**Architecture:** 24 Python microservices + API Gateway + Next.js 15 frontend
**Database:** Single PostgreSQL 16 (logically partitioned by tenant_id)
**Backend Stack:** Python 3.12, Uvicorn (ASGI), custom HTTP handler (no FastAPI/Flask)
**Frontend Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS, TanStack React Query

---

## GLOSSARY

Cross-cutting terms used across governance documents without a prior formal definition:

| Term | Definition |
|------|-----------|
| **Decision Card** | A runtime/in-memory advisory object produced by decision-service (`services/decision_engine.py`, `class DecisionCard`). Fields: `trigger`, `impact`, `confidence`, `recommended_action`, `reversibility`, `expires_at`, `source_domain`, `severity` (critical/notify/passive — `DecisionSeverity` enum), `resolved_at`, `actor`, `status` (default "active"), `lifecycle_state` (default "create"), `override_tracking`, `created_at`, `updated_at`, `audit_history`. It is **not** a database table — no `decision_cards` table exists in any migration file. Decision Cards are advisory: `severity=critical` drives blocking/mandatory-approval behavior, `notify` requires visible non-blocking action, `passive` is logged only. See `DOMAIN_MODEL.md` "DECISION CARD" entry. |
| **Read Model / Projection** | A denormalized, query-optimized data view derived from primary tables and/or domain events, used by reporting-analytics-service and search-service to serve read traffic without querying source-of-truth tables directly. Catalogued in `/backend/docs/canon/read-model-catalog.md` (not yet cross-referenced into governance docs — tracked as a documentation gap). |
| **Capability** | A named permission grant (e.g., `payroll.run`, `employee.write`) that, combined with a matching **Scope**, authorizes an action. The full capability matrix (40+ capabilities) is enumerated in `/backend/docs/canon/capability-matrix.md` — that file is the canonical source; this document only references the concept. |
| **Scope** (`scope_type`) | The boundary within which a Capability applies, stored on `role_bindings.scope_type` (see `DOMAIN_MODEL.md` ROLE BINDING). Five values: `Global` (tenant-wide), `Department` (limited to a department subtree), `Employee` (limited to a single employee record — typically self), `Requisition` (limited to a specific hiring requisition/job posting), `Service` (machine-to-machine, inter-service calls). Per FD-008, authorization requires **both** a Capability grant **and** a matching Scope — neither is sufficient alone. |

---

## FROZEN_DECISIONS

**Derivation Note:** This table is a fast-reference summary derived from `ADR-001_PROJECT_FOUNDATION.md` §3 (Core Technology Choices) and §7 (Architectural Principles). Any future ADR that supersedes or amends one of these decisions must update both `ADR-001` (or add a new ADR marked as superseding it) **and** this table in the same change, so this list never presents a stale "frozen" status.

These decisions are made, implemented, and not open for reconsideration without a new ADR:

| # | Decision | Rationale | Evidence |
|---|----------|-----------|----------|
| FD-001 | JWT (HS256) for authentication | Security standard for stateless auth | `/backend/docker/api_gateway_service.py` |
| FD-002 | Multi-tenant via row-level `tenant_id` | Single DB, per-tenant isolation | All migration files |
| FD-003 | API Gateway as single entry point | Centralized auth, rate limiting, routing | `docker-compose.yml`, `api_gateway_service.py` |
| FD-004 | Custom ASGI handler (no FastAPI/Flask) | Minimal dependencies, performance | `/backend/docker/service_runtime.py` |
| FD-005 | PostgreSQL 16 as single database | Shared DB with logical per-service partition | `docker-compose.yml` |
| FD-006 | Outbox pattern for cross-service events | Avoid dual-write problem | `/backend/event_outbox.py` |
| FD-007 | Country-specific logic isolated in `/backend/country/[country]/` | Core services must remain country-agnostic | `/backend/country/` structure |
| FD-008 | Deny-by-default authorization | Security-first; both capability + scope required | `/backend/docs/canon/security-model.md` |
| FD-009 | All mutations produce AuditRecord | Compliance and traceability requirement | `/backend/docs/canon/service-map.md` |
| FD-010 | `/api/v1/` API versioning prefix | API stability contract | All route definitions |
| FD-011 | Standard response envelope `{status, data, meta, error}` | Consistent client contract | `/backend/api_contract.py` |
| FD-012 | React Query for frontend data fetching | No Redux/Zustand; server-state management | `/backend/ui/package.json` |
| FD-013 | Docker Compose deployment (current) | Development and initial deployment target | `docker-compose.yml` |

---

## KNOWN_CONSTRAINTS

### Technical Constraints
- **No direct DB cross-service queries** — Services communicate only via HTTP API calls
- **No country logic in core services** — All jurisdiction-specific code lives in `/backend/country/[country]/`
- **No framework dependency** — Backend uses custom ASGI; do not introduce FastAPI/Flask/Django
- **Single PostgreSQL instance** — All 24 services share one DB; no per-service databases
- **Outbox required for events** — Cannot write events directly; must use `event_outbox.py`
- **Rate limit: 200 req/min per IP** — Enforced at API Gateway; performance tests must account for this
- **Idempotency-Key required** — All state-changing operations must handle idempotency

### Authorization Constraints
- JWT must be validated at API Gateway for all non-exempt routes
- Exempt routes: `/health`, `/ready`, `/metrics`, `/api/v1/auth/*`
- Scope enforcement must be done in each service — gateway only checks role, not scope
- `tenant_id` must be extracted from JWT payload and propagated through request context
- Salary data must be filtered from responses for non-PayrollAdmin/Admin roles

### Data Constraints
- All primary tables must have `tenant_id` column (VARCHAR 80)
- All primary tables must have unique constraint: `(tenant_id, [entity]_id)`
- All foreign keys must reference `(tenant_id, entity_id)` — not just `entity_id`
- Audit records are IMMUTABLE — no update or delete operations permitted

---

## ACTIVE_AUTHORITY_DOCS

Read these documents before working on the relevant area. They take precedence over code comments and inline documentation.

| Document | Path | Purpose | When to Read |
|----------|------|---------|--------------|
| PROJECT_CHARTER | `docs/00_authority/PROJECT_CHARTER.md` | Project identity, scope, constraints | First document for any new session |
| FEATURE_SCOPE | `docs/00_authority/FEATURE_SCOPE.md` | Feature status register | Before adding/modifying features |
| DOMAIN_MODEL | `docs/00_authority/DOMAIN_MODEL.md` | Entity definitions, relationships, lifecycles | Before touching any data model |
| PRODUCT_WORKFLOWS | `docs/00_authority/PRODUCT_WORKFLOWS.md` | End-to-end user workflows | Before modifying multi-service flows |
| FULLSTACK_STITCHING_CONTRACT | `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md` | Feature-to-code traceability | Before modifying any API or UI |
| DECISION_ESCALATION_MATRIX | `docs/07_governance/DECISION_ESCALATION_MATRIX.md` | What requires approval (4 tiers incl. SAFE_REPOSITORY_HYGIENE) | Before ANY code change |
| SAFE_REPOSITORY_HYGIENE_POLICY | `docs/07_governance/SAFE_REPOSITORY_HYGIENE_POLICY.md` | Policy for TIER 1.5 — low-risk repository maintenance | Before any structural/archival action |
| REPOSITORY_HYGIENE_EXECUTION_GUIDELINES | `docs/07_governance/REPOSITORY_HYGIENE_EXECUTION_GUIDELINES.md` | Step-by-step execution for hygiene actions | When executing SAFE_REPOSITORY_HYGIENE tier actions |
| ADR-001 | `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` | Foundation decisions | For architectural context |
| Domain Model (Canon) | `/backend/docs/canon/domain-model.md` | Authoritative domain entities | For implementation detail |
| Security Model (Canon) | `/backend/docs/canon/security-model.md` | Auth, roles, capabilities | Before auth/permission changes |
| API Standards (Canon) | `/backend/docs/canon/api-standards.md` | Request/response format | Before adding endpoints |
| Event Catalog (Canon) | `/backend/docs/canon/event-catalog.md` | All 143 domain events | Before adding/modifying events |

---

## PROTECTED_AREAS

These areas require explicit human approval before any modification:

### CRITICAL (Do not touch without written approval)
- `/backend/docker/api_gateway_service.py` — Core routing, JWT validation, rate limiting
- `/backend/deployment/migrations/*.sql` — Database schema migrations (irreversible)
- `/backend/docs/canon/security-model.md` — Security policy definitions
- `/backend/country/pakistan/` — Statutory compliance logic (FBR, EOBI, PESSI)
- `/backend/integrations/pakistan/` — Payment and regulatory integrations

### HIGH (Require architectural review before modification)
- `/backend/api-gateway/routes.py` — Route table (all services depend on it)
- `/backend/docker/service_runtime.py` — Core ASGI handler (all services use it)
- `/backend/api_contract.py` — Response envelope standard
- `/backend/resilience.py` — Circuit breaker (cross-cutting reliability)
- `/backend/event_outbox.py` — Event publication (data consistency depends on this)
- Any file in `/backend/docs/canon/` — Canonical documentation

---

## DO_NOT_MODIFY_AREAS

These areas must never be modified by an AI session without explicit user instruction:

1. **Audit records** — Never add DELETE or UPDATE operations to `audit_records` table
2. **Tenant isolation constraints** — Never remove `tenant_id` from any table or relax unique constraints
3. **JWT secret handling** — Never log, expose, or weaken JWT_SECRET handling
4. **Password hashing** — Never bypass or weaken password_hash verification
5. **Rate limiting** — Never disable or circumvent API Gateway rate limits
6. **Migration files** — Never modify an already-applied migration; always create new ones

---

## OPEN_ARCHITECTURAL_QUESTIONS

These questions are unresolved and should not be assumed answered:

| # | Question | Impact | Who Decides |
|---|----------|--------|-------------|
| OAQ-001 | Scaling strategy beyond Docker Compose (Kubernetes?) | Infrastructure, deployment pipeline | Human |
| OAQ-002 | Caching layer introduction (Redis?) | Performance, session storage | Human |
| OAQ-003 | Message queue vs. in-process background jobs (RabbitMQ/Kafka?) | Reliability, throughput | Human |
| OAQ-004 | Mobile application scope and architecture | Product roadmap | Human |
| OAQ-005 | Multi-country expansion plan (India, UAE, etc.) | Country layer architecture | Human |
| OAQ-006 | SLA and uptime guarantees | Infrastructure, monitoring | Human |
| OAQ-007 | APM / distributed tracing implementation | Observability | Human |
| OAQ-008 | Database backup and disaster recovery strategy | Data safety | Human |
| OAQ-009 | A/B testing and feature flag service | Product experimentation | Human |
| OAQ-010 | API v2 introduction timeline and migration strategy | API stability | Human |

---

## REQUIRED_VALIDATIONS

Before claiming any work is complete, verify:

### For backend changes:
```bash
# Run test suite
python -m pytest -p no:cacheprovider -q --tb=short

# Run linter
ruff check . --select E,F,W --ignore E501 --exclude .venv

# Run security scan
pip-audit -r requirements.txt

# Migration dry-run (if schema changes)
python deployment/migrate.py --dry-run
```

### For any change:
```bash
# API Gateway health
curl http://localhost:8000/ready
curl http://localhost:8000/health

# Service health (replace with relevant port)
curl http://localhost:800X/health

# Frontend health
curl http://localhost:3000/
```

**Evidence Source:** `.github/workflows/ci.yml`

---

## DOCUMENT_FRESHNESS_POLICY

| Document Type | Review Trigger | Reviewer |
|--------------|----------------|---------|
| Authority documents (`00_authority/`) | Any schema or API change | Human Owner |
| Governance documents (`07_governance/`) | Any new architectural decision | Shared |
| ADRs (`06_decisions/`) | Any frozen decision reversal | Human Owner |
| Reports (`08_reports/`) | After major implementation sprints | AI-assisted, Human-approved |
| Stale threshold | 90 days without review | Flag for re-review |

---

## CONTRACT_COMPATIBILITY_POLICY

When making any API change:

1. **Check `FULLSTACK_STITCHING_CONTRACT.md`** — Does this change break a documented trace?
2. **Check `contracts/hrms-h*.json`** — Does this change break a page archetype contract?
3. **Check frontend consumers** — Does `/backend/ui/lib/api/` call this endpoint?
4. **Check test coverage** — Does a test assert on this behavior?

**Breaking change definition:** Any change to an existing endpoint's method, path, required parameters, or response shape is a breaking change requiring a new version or explicit deprecation.

**Non-breaking changes:** Adding optional query parameters, adding fields to response `data`, adding new endpoints.
