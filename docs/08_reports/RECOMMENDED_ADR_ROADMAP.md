# RECOMMENDED ADR ROADMAP

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This roadmap recommends future Architecture Decision Records (ADRs) based on open architectural questions (`AI_OPERATING_CONTEXT.md` → OPEN_ARCHITECTURAL_QUESTIONS) and gaps identified in `ARCHITECTURAL_GAP_REGISTER.md`. Each entry includes the question to be resolved, why it matters, and suggested priority.

ADRs should be created in `docs/06_decisions/` following the format of `ADR-001_PROJECT_FOUNDATION.md`.

---

## ROADMAP

### ADR-002: Scaling Strategy (Docker Compose → Production Orchestration)

- **Resolves:** OAQ-001, GAP-DEP-001
- **Question:** Should the system move from Docker Compose to Kubernetes, a managed container service (ECS, Cloud Run), or remain on Compose with a different host?
- **Why It Matters:** Docker Compose lacks built-in HA, auto-scaling, and rolling deployments. As tenant count grows, this becomes the primary infrastructure bottleneck.
- **Priority:** High
- **Trigger:** Before onboarding production tenants beyond pilot scale

---

### ADR-003: Secrets Management Strategy

- **Resolves:** GAP-DEP-003
- **Question:** How are JWT_SECRET, database credentials, and third-party API keys (FBR, EOBI, Raast, WhatsApp) managed and rotated in production?
- **Why It Matters:** Current `.env`-based approach (visible in `docker-compose.yml`) is unsuitable for production; security-critical given financial and compliance integrations.
- **Priority:** High
- **Trigger:** Before any production deployment

---

### ADR-004: Caching Layer Introduction

- **Resolves:** OAQ-002, GAP-A-003
- **Question:** Should Redis (or similar) be introduced for session caching, rate-limit state, idempotency cache, and frequently-read projections?
- **Why It Matters:** Current rate-limiting and idempotency caches are in-process (per-instance), which breaks correctness when scaling to multiple gateway instances.
- **Priority:** High (becomes blocking once ADR-002 introduces multi-instance gateway)
- **Trigger:** Before horizontal scaling of API Gateway

---

### ADR-005: Asynchronous Processing Strategy (Message Queue)

- **Resolves:** OAQ-003, R-002 (event loss risk)
- **Question:** Should RabbitMQ, Kafka, or a managed queue (SQS) replace or augment the in-process outbox/background job system?
- **Why It Matters:** In-process processing risks event loss on crash; 143 cataloged domain events depend on reliable delivery for cross-service consistency (e.g., payroll → compliance → bank).
- **Priority:** Medium-High
- **Trigger:** Before payroll/compliance volume reaches a scale where event loss has material financial impact

---

### ADR-006: API Versioning and v2 Strategy

- **Resolves:** OAQ-010
- **Question:** What is the policy for introducing breaking API changes — new version prefix (`/api/v2/`), header-based versioning, or deprecation windows?
- **Why It Matters:** `FULLSTACK_STITCHING_CONTRACT.md` shows tight coupling between frontend and `/api/v1/` contracts; any breaking change today has no defined migration path.
- **Priority:** Medium
- **Trigger:** Before the first breaking API change is needed

---

### ADR-007: Multi-Country Expansion Architecture

- **Resolves:** OAQ-005
- **Question:** How does the country layer (`/backend/country/[country]/`) scale to support a second country (e.g., UAE, India)? What's shared vs. duplicated?
- **Why It Matters:** Currently Pakistan-only. The existence of `/backend/country/base/` suggests a resolver pattern was anticipated, but it's unproven with only one implementation.
- **Priority:** Medium
- **Trigger:** Before sales/product commits to a second country market

---

### ADR-008: Mobile Application Architecture

- **Resolves:** OAQ-004, GAP-A-006
- **Question:** What is the scope and architecture of the mobile app referenced in `/backend/mobile/`? Native, React Native, PWA?
- **Why It Matters:** Affects API contract design (mobile-specific endpoints?), auth token lifetime, and offline-sync requirements.
- **Priority:** Medium
- **Trigger:** Before mobile development begins

---

### ADR-009: Observability and Monitoring Stack

- **Resolves:** OAQ-007, GAP-A-004
- **Question:** What APM/tracing/metrics stack will be used (Prometheus + Grafana, Datadog, OpenTelemetry)? How does `/metrics` get implemented and consumed?
- **Why It Matters:** With 24 services and a circuit breaker pattern already in place, distributed tracing is essential for diagnosing cross-service issues. Currently no visibility beyond logs.
- **Priority:** High
- **Trigger:** Before production launch (operational blindness risk)

---

### ADR-010: Database Backup and Disaster Recovery

- **Resolves:** GAP-DEP-004
- **Question:** What is the backup frequency, retention policy, and restore procedure for the single PostgreSQL instance holding all tenant data?
- **Why It Matters:** A single DB instance is a single point of failure for all 24 services and all tenants. Payroll and compliance data loss would have legal/financial consequences.
- **Priority:** Critical
- **Trigger:** Before any tenant with real payroll data goes live

---

### ADR-011: Frontend Testing Strategy

- **Resolves:** GAP-T-003
- **Question:** What testing framework (Jest, Vitest, Playwright, Cypress) will be adopted for the Next.js frontend, and what is the minimum coverage bar?
- **Why It Matters:** No frontend test suite currently exists; UI regressions (especially in approval flows, payroll display) carry compliance and trust risk.
- **Priority:** Medium
- **Trigger:** Before next major frontend feature push

---

### ADR-012: Feature Flag and Tenant Configuration Strategy

- **Resolves:** OAQ-009
- **Question:** How are `tenant_configs.feature_flags` (JSONB) managed — admin UI, config file, dedicated feature-flag service?
- **Why It Matters:** ADD-ON features (performance, engagement, helpdesk, search, expense, integration) need a clear enablement mechanism per tenant.
- **Priority:** Medium
- **Trigger:** Before ADD-ON features are sold as upsells

---

### ADR-013: Audit Log Immutability Enforcement Mechanism

- **Resolves:** GAP-U-004
- **Question:** Is audit_records immutability enforced at the database level (REVOKE UPDATE/DELETE, triggers) or only by application convention?
- **Why It Matters:** Application-only enforcement is insufficient for compliance; database-level guarantees are needed if audit logs are used as legal evidence.
- **Priority:** High
- **Trigger:** Before relying on audit logs for compliance attestation

---

## SEQUENCING RECOMMENDATION

**Before any production tenant onboarding (Critical path):**
1. ADR-010 (Disaster Recovery)
2. ADR-003 (Secrets Management)
3. ADR-013 (Audit Immutability)
4. ADR-009 (Observability)

**Before scaling beyond pilot (High path):**
5. ADR-002 (Scaling Strategy)
6. ADR-004 (Caching Layer)
7. ADR-005 (Message Queue)

**Before next major product expansion (Medium path):**
8. ADR-007 (Multi-Country)
9. ADR-008 (Mobile)
10. ADR-006 (API v2)
11. ADR-012 (Feature Flags)
12. ADR-011 (Frontend Testing)
