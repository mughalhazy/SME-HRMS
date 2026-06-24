# ADR-001: PROJECT FOUNDATION

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-15
Owner: Human

---

## METADATA

- **ADR Number:** 001
- **Title:** Project Foundation — Architecture, Technology, and Constraint Decisions
- **Status:** Active (decisions implemented and in production code)
- **Date:** Inferred from codebase; precise date TBD – REQUIRES VERIFICATION
- **Deciders:** TBD – REQUIRES VERIFICATION (human project owner)
- **Evidence Base:** Actual codebase structure, migration files, configuration files

---

## 1. PROJECT PURPOSE

Meridian HCM is a multi-tenant SaaS HR Management System built for SME enterprises with an initial focus on the Pakistan market. The system covers the full HR lifecycle: recruitment, workforce management, attendance, leave, payroll, compliance, performance, and employee engagement.

**Primary evidence:** `/ops/HRMS PRODUCT SPEC.md`, `docker-compose.yml` service inventory, `/backend/docs/canon/release-scope.md`

---

## 2. CURRENT ARCHITECTURE

### Overall Architecture

**Pattern:** Microservices with shared database
**Decomposition:** Domain-driven (one service per HR domain)
**Entry Point:** Single API Gateway proxying all client requests to internal services
**Deployment:** Docker Compose with 24 services + PostgreSQL + Next.js frontend

### Service Topology

```
[Browser / WhatsApp Client]
         │
         ▼
   [API Gateway :8000]
   ├── JWT Validation
   ├── Rate Limiting (200 req/min/IP)
   ├── Route Resolution
   └── CORS
         │
         ├── /api/v1/employees    → employee-service :8001     [CONFIRMED]
         ├── /api/v1/departments  → employee-service :8001     [CONFIRMED]
         ├── /api/v1/attendance   → attendance-service :8002    [CONFIRMED]
         ├── /api/v1/leave        → leave-service :8003         [CONFIRMED]
         ├── /api/v1/payroll      → payroll-service :8004       [CONFIRMED]
         ├── /api/v1/hiring       → hiring-service :8005        [CONFIRMED]
         ├── /api/v1/auth         → auth-service :8006          [CONFIRMED]
         ├── /api/v1/notifications→ notification-service :8007  [CONFIRMED]
         ├── /api/v1/audit        → audit-service :8008         [CONFIRMED]
         ├── /api/v1/workflows    → workflow-service :8009      [CONFIRMED]
         ├── /api/v1/performance  → performance-service :8010   [CONFIRMED, ADD-ON]
         ├── /api/v1/engagement   → engagement-service :8011    [CONFIRMED, ADD-ON]
         ├── /api/v1/helpdesk     → helpdesk-service :8012      [CONFIRMED, ADD-ON]
         ├── /api/v1/reporting    → reporting-analytics-service :8013 [CONFIRMED]
         ├── /api/v1/search       → search-service :8014        [CONFIRMED, ADD-ON]
         ├── /api/v1/expense      → expense-service :8015       [CONFIRMED, ADD-ON]
         ├── /api/v1/integrations → integration-service :8016   [CONFIRMED, ADD-ON]
         ├── /api/v1/automations  → automation-service :8017    [CONFIRMED]
         ├── /api/v1/travel       → travel-service :8018        [CONFIRMED route; service implementation status PLANNED — see FEATURE_SCOPE F-023]
         ├── /api/v1/projects     → project-service :8019       [CONFIRMED route; service implementation status PLANNED — see FEATURE_SCOPE F-024]
         └── /api/v1/settings     → settings-service :8020      [CONFIRMED]

   UNCONFIRMED — services exist as containers (docker-compose.yml ports 8021-8024)
   and have implementation files, but NO path prefix for them appears in the
   gateway ROUTES table (`/backend/api-gateway/routes.py`,
   `/backend/deployment/config/gateway-routes.json`). Client-facing access via
   `/api/v1/{prefix}` through the API Gateway is NOT CONFIRMED for these services:
         ├── compliance-service :8021  — TBD – REQUIRES VERIFICATION (no `/api/v1/compliance` gateway route found)
         ├── decision-service :8022    — TBD – REQUIRES VERIFICATION (no `/api/v1/decisions` gateway route found)
         ├── bank-service :8023        — TBD – REQUIRES VERIFICATION (no `/api/v1/banking` gateway route found)
         └── whatsapp-service :8024    — TBD – REQUIRES VERIFICATION (no `/api/v1/whatsapp` gateway route found)

[Next.js Frontend :3000]
   ├── Next.js 15 App Router
   ├── React 19 + TypeScript
   ├── TanStack React Query
   └── Tailwind CSS 4
```

**Evidence:** `docker-compose.yml`, `/backend/api-gateway/routes.py`, `/backend/deployment/config/gateway-routes.json`, `/backend/ui/`. The gateway ROUTES table contains exactly 21 confirmed path-prefix entries (verified by direct read of `routes.py` and `gateway-routes.json`, which agree). `compliance-service`, `decision-service`, `bank-service`, and `whatsapp-service` are deployed (docker-compose.yml lines 303-352) and have backend implementation files (`compliance_service.py`, `decision_api.py` / `decision_engine.py`, `bank_service.py`, `whatsapp_service.py` / `whatsapp_api.py`), but their client-facing routing path is unconfirmed — they may be reached via a mechanism other than the gateway ROUTES table, or may not yet be exposed to clients. This does not imply the services are non-functional; only that the API Gateway routing claim could not be verified from `routes.py`/`gateway-routes.json`.

### Data Architecture

**Pattern:** Shared PostgreSQL database with logical tenant isolation
- Single PostgreSQL 16 instance shared by all 24 services
- No per-service databases; no cross-service direct DB queries
- Tenant isolation via `(tenant_id, entity_id)` unique constraints on every table
- Cross-service communication via HTTP API calls only

**Evidence:** `docker-compose.yml` (postgres:16-alpine), migration files

### Event Architecture

**Pattern:** Outbox-based event publication
- All domain events written to `service_outbox` table atomically with triggering mutation
- Outbox processor publishes events asynchronously
- 143 domain events cataloged in `/backend/docs/canon/event-catalog.md`
- No external message broker (RabbitMQ, Kafka) — in-process event processing

**Evidence:** `/backend/event_outbox.py`, `/backend/outbox_system.py`, `007_event_outbox.sql`

---

## 3. CORE TECHNOLOGY CHOICES

### Backend

| Choice | Decision | Alternatives Considered | Reason |
|--------|----------|------------------------|--------|
| Language | Python 3.12 | — | TBD – REQUIRES VERIFICATION |
| HTTP Server | Uvicorn (ASGI) | — | TBD – REQUIRES VERIFICATION |
| Web Framework | None (custom ASGI handler) | FastAPI, Flask, Django | Minimal dependencies, performance control |
| Database | PostgreSQL 16 | — | TBD – REQUIRES VERIFICATION |
| ORM | None (raw SQL via psycopg2) | SQLAlchemy, Django ORM | Explicit control over queries |
| Authentication | JWT (HS256) | OAuth2, session-based | Stateless, suitable for microservices |
| Migrations | Raw SQL files + custom runner | Alembic, Flyway | Direct control, no ORM dependency |
| Testing | pytest | — | Python standard |
| Linting | ruff | flake8, pylint | Speed, modern Python rules |
| Security Scanning | pip-audit | safety, bandit | Dependency vulnerability detection |

**Evidence:** `requirements.txt`, `/backend/docker/service_runtime.py`, `ci.yml`

### Frontend

| Choice | Decision | Alternatives Considered | Reason |
|--------|----------|------------------------|--------|
| Framework | Next.js 15 (App Router) | React SPA, Remix | SSR capabilities, App Router routing |
| Language | TypeScript 5.8 | JavaScript | Type safety |
| Styling | Tailwind CSS 4 | CSS Modules, Styled Components | Utility-first, design system tokens |
| State (server) | TanStack React Query 5 | Redux, SWR | Server-state management |
| State (client) | React Context + useState | Redux, Zustand | Sufficient for current scope |
| Icons | Lucide React | Heroicons, FontAwesome | TBD – REQUIRES VERIFICATION |

**Evidence:** `/backend/ui/package.json`, `/backend/ui/next.config.ts`

### Infrastructure

| Choice | Decision | Reason |
|--------|----------|--------|
| Containerization | Docker | Industry standard, reproducible environments |
| Orchestration (current) | Docker Compose | Simplicity for initial deployment |
| CI/CD | GitHub Actions | TBD – REQUIRES VERIFICATION (code hosting) |
| Python matrix | 3.11, 3.12 | Compatibility testing |

**Evidence:** `docker-compose.yml`, `.github/workflows/ci.yml`

---

## 4. KNOWN CONSTRAINTS

### Technical
- No external message broker; in-process background jobs only (constraint on throughput)
- No caching layer (Redis/Memcached not present in codebase)
- No dedicated search index (search-service uses DB projections, not Elasticsearch/Algolia)
- Single PostgreSQL instance is a vertical scaling constraint
- Custom ASGI handler means no FastAPI ecosystem benefits (Pydantic, automatic OpenAPI)

### Regulatory & Compliance
- Pakistan-first: FBR, EOBI, PESSI statutory compliance required
- Tax calculations must conform to Pakistani income tax slabs
- Salary disbursement must support Raast (Pakistan instant payment) protocol
- Audit logs must be retained and immutable (regulatory requirement inferred)

### Business
- SME focus: complexity and cost must be appropriate for SME budgets
- Multi-tenancy: all tenants share infrastructure (no dedicated per-tenant resources)
- Pakistan market: WhatsApp as access channel is specifically required (many SME HR ops via WhatsApp)

---

## 5. MAJOR ASSUMPTIONS

| # | Assumption | Status | Impact if Wrong |
|---|-----------|--------|----------------|
| A-001 | Docker Compose is sufficient for initial deployment scale | TBD – REQUIRES VERIFICATION | Need Kubernetes/cloud orchestration sooner |
| A-002 | Single PostgreSQL handles expected tenant/data volume | TBD – REQUIRES VERIFICATION | Need sharding or read replicas |
| A-003 | In-process background jobs handle async workload | TBD – REQUIRES VERIFICATION | Need RabbitMQ/Kafka for reliability |
| A-004 | Pakistan-first compliance is sufficient for launch | Assumed | Expansion requires new country layers |
| A-005 | WhatsApp API access is stable for business use | TBD – REQUIRES VERIFICATION | WhatsApp channel (F-016) fails |
| A-006 | Custom ASGI handler performance is sufficient | TBD – REQUIRES VERIFICATION | May need FastAPI's async optimization |
| A-007 | Tailwind CSS 4 + bespoke components is sufficient for UI needs | Assumed | May need component library |

---

## 6. KNOWN RISKS

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| R-001 | Single DB becomes bottleneck under load | Medium | High | Circuit breaker in place; migration plan TBD |
| R-002 | In-process event processing loses events on crash | Medium | High | Outbox pattern mitigates but no dead-letter queue |
| R-003 | Custom ASGI handler has undiscovered bugs | Low | High | 92+ test files; chaos engine tests resilience |
| R-004 | Pakistan compliance rules change (tax slabs, EOBI rates) | High | High | Country layer isolated; rules updateable without core changes |
| R-005 | JWT secret compromise | Low | Critical | HS256 with environment-injected secret; rotate on breach |
| R-006 | Tenant data leakage via SQL injection or query error | Low | Critical | Row-level tenant_id filters; psycopg2 parameterized queries |
| R-007 | WhatsApp API deprecation or policy change | Medium | Medium | F-016 is isolated service; can disable without core impact |
| R-008 | Docker Compose not suitable for HA production | Medium | High | OAQ-001 open (Kubernetes consideration) |

---

## 7. ARCHITECTURAL PRINCIPLES

These principles are inferred from the actual architecture and must be preserved:

1. **Tenant First** — Every data operation must include tenant_id; isolation is non-negotiable
2. **Audit Everything** — Every state mutation produces an immutable audit record
3. **Gateway as Sheriff** — All client traffic routes through API Gateway; services trust the gateway's JWT validation
4. **Country Layer Isolation** — Core services are country-agnostic; jurisdiction logic lives in `/backend/country/[country]/`
5. **Outbox for Events** — No dual-write; events are published atomically with mutations via outbox
6. **Deny by Default** — Authorization requires explicit capability grant + matching scope
7. **Standard Contracts** — All responses use `{status, data, meta, error}` envelope
8. **Minimal Dependencies** — Backend uses minimal packages; no ORM, no web framework
9. **Services Communicate via HTTP** — No direct DB access across service boundaries
10. **Test Coverage Required** — 92+ test files; new features require tests before shipping

---

## 8. DECISIONS SUPERSEDED BY THIS ADR

None — this is the foundation ADR. All subsequent ADRs reference this document.

---

## 9. FUTURE ADR CANDIDATES

See `docs/08_reports/RECOMMENDED_ADR_ROADMAP.md` for the full roadmap.

Priority candidates:
- ADR-002: Scaling Strategy (Docker Compose → Kubernetes)
- ADR-003: Caching Layer Introduction (Redis)
- ADR-004: Message Queue Decision (in-process vs. RabbitMQ/Kafka)
- ADR-005: API v2 Strategy
- ADR-006: Mobile Application Architecture
- ADR-007: Multi-Country Expansion Strategy
