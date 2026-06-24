# AUTHORITY MAPPING MATRIX

Status: Active
Authority Level: Medium
Created: 2026-06-16
Owner: AI
Phase: Documentation Normalization and Authority Consolidation

---

## PURPOSE

For every information domain, this matrix establishes exactly one authoritative document and classifies all other documents as supporting, legacy, or retired relative to that domain.

---

## DOMAIN MAP

### D-001: Project Identity and Purpose

**Authority:** `docs/00_authority/PROJECT_CHARTER.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/00_authority/PROJECT_CHARTER.md` | **AUTHORITY** | Meridian HCM identity, 7 design principles, F-XXX feature IDs, governance rules |
| `backend/docs/system/system-purpose.md` | RETIRED | Superseded. Contains the same 7 principles. Charter is more complete. |
| `backend/docs/system/MASTER BUILD SPEC.md` | RETIRED | Superseded. System identity section subsumed by Charter. |
| `backend/docs/system/MASTER BEHAVIOR SPEC.md` | RETIRED | Superseded. Behavior principles now in Charter and PRODUCT_WORKFLOWS.md. |
| `ops/HRMS PRODUCT SPEC.md` | RETIRED | Self-labeled superseded. Original intent document. |
| `ops/build-progress.md` (§ "What This Project Is") | SUPPORTING | Useful summary for session continuity; not authoritative. |
| `backend/docs/system/archive/HRMS SPEC.md` | ARCHIVE | Pre-build origin artifact. |
| `backend/docs/system/archive/COMPLETE HRMS BUILD SPEC.md` | ARCHIVE | Pre-build origin artifact. |

---

### D-002: Feature Scope

**Authority:** `docs/00_authority/FEATURE_SCOPE.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/00_authority/FEATURE_SCOPE.md` | **AUTHORITY** | 24 features (F-001–F-024), status (IMPLEMENTED/ADD-ON/PLANNED), OUT OF SCOPE list |
| `backend/docs/canon/release-scope.md` | RETIRED | Superseded. Predates F-XXX ID system and current feature count. |
| `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` | SUPPORTING | ADR-001 references scope decisions; scope authority remains with FEATURE_SCOPE.md. |
| `ops/answers.md` | SUPPORTING | C1–C5 decisions shaped scope. Historical reference only; not authoritative. |
| `backend/docs/system/success-criteria.md` | SUPPORTING | Success criteria derived from scope; not authoritative for scope itself. |

---

### D-003: Domain Model and Entities

**Authority:** `docs/00_authority/DOMAIN_MODEL.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/00_authority/DOMAIN_MODEL.md` | **AUTHORITY** | 57+ entities, multi-tenancy invariant, compound FK pattern, CHECK constraint values |
| `backend/docs/canon/domain-model.md` | RETIRED | Superseded. New version is more complete and includes corrections from Phase 2. |
| `backend/docs/canon/data-architecture.md` | RETIRED | Superseded by both DOMAIN_MODEL.md (entity definitions) and DATABASE_SCHEMA.md (schema). |
| `backend/docs/services/*.md` (entity sections) | SUPPORTING | Service-level entity detail; must defer to DOMAIN_MODEL.md on entity definitions. |

---

### D-004: Product Workflows

**Authority:** `docs/00_authority/PRODUCT_WORKFLOWS.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/00_authority/PRODUCT_WORKFLOWS.md` | **AUTHORITY** | 9 core business workflows with triggers, actors, steps, outcomes |
| `backend/docs/canon/workflow-catalog.md` | SUPPORTING | Technical workflow catalog with detailed step definitions, SLAs, escalations. More granular than PRODUCT_WORKFLOWS.md. Complementary — not competing. Both should be consulted. |
| `backend/docs/system/MASTER BEHAVIOR SPEC.md` | RETIRED | Workflow behavior content superseded by PRODUCT_WORKFLOWS.md. |

---

### D-005: Backend Architecture

**Authority:** `docs/01_backend/BACKEND_ARCHITECTURE.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/01_backend/BACKEND_ARCHITECTURE.md` | **AUTHORITY** | 24 microservices, ASGI runtime, gateway, resilience, country layer, observability |
| `backend/docs/system/MASTER BUILD SPEC.md` | RETIRED | Superseded. Architecture content now in BACKEND_ARCHITECTURE.md. |
| `backend/docs/system/intent_build_alignment.md` | HISTORICAL | 2026-03-31 baseline snapshot. Self-disclaimed for Sessions 2–8. Not authoritative for current state. |
| `backend/docs/reports/alignment_final.md` | HISTORICAL | Stub pointing to intent_build_alignment.md. |
| `backend/docs/design/convergence-history.md` | HISTORICAL | P28–P33 build pass decisions. Valuable context; not authoritative for current state. |
| `backend/README.md` | SUPPORTING | Developer orientation; defers to BACKEND_ARCHITECTURE.md for architecture claims. |

---

### D-006: Database Schema

**Authority:** `docs/01_backend/DATABASE_SCHEMA.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/01_backend/DATABASE_SCHEMA.md` | **AUTHORITY** | 58 tables, migrations 001–015, all columns/PKs/FKs/CHECK constraints |
| `backend/docs/canon/data-architecture.md` | RETIRED | Superseded. Pre-dates migration 014/015 compound FK corrections. |
| `docs/08_reports/DATABASE_DISCOVERY_REPORT.md` | SUPPORTING | Discovery findings; defers to DATABASE_SCHEMA.md for current truth. |

---

### D-007: API Contract and Standards

**Authority (Contract):** `docs/01_backend/API_CONTRACT.md`
**Authority (Standards):** `backend/docs/canon/api-standards.md` *(retained for coding standards)*

| Document | Role | Notes |
|----------|------|-------|
| `docs/01_backend/API_CONTRACT.md` | **AUTHORITY** | 21 gateway routes, 164 endpoints, response envelope, standard patterns |
| `backend/docs/canon/api-standards.md` | SUPPORTING | Retained as authority for API coding standards (versioning rules, naming conventions) referenced by tests and code. Not superseded for standards; superseded for route/endpoint claims. |
| `design/hrms-api-contracts.md` | SUPPORTING | UI-layer expected response shapes. Supplemented by DATA_SHAPE_REGISTRY.md. Remains relevant for Frontend Authority Capture. |
| `docs/08_reports/API_DISCOVERY_REPORT.md` | SUPPORTING | Discovery findings. |
| `docs/03_fullstack_contracts/CONTRACT_VERSION_REGISTRY.md` | SUPPORTING | Version registry; defers to API_CONTRACT.md for route/endpoint content. |

---

### D-008: Service Catalog

**Authority:** `docs/01_backend/SERVICE_CATALOG.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/01_backend/SERVICE_CATALOG.md` | **AUTHORITY** | 24 services, ports, owned entities, dependencies, gateway route status |
| `backend/docs/canon/service-map.md` | RETIRED | Superseded. TBD annotations added for stale entries (ewa-financial-service). |
| `backend/docs/system/service-manifest.md` | RETIRED | Superseded. Contains stale employee-service TypeScript claim (now Python). |
| `backend/docs/services/*.md` (29 files) | SUPPORTING | Per-service design detail. Not superseded — SERVICE_CATALOG.md covers topology; service docs cover design intent. Must defer on service ownership/ports. |

---

### D-009: Events and Outbox Architecture

**Authority (Architecture):** `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md`
**Authority (Event Registry):** `backend/docs/canon/event-catalog.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md` | **AUTHORITY** | Outbox pattern, dual implementation, background jobs, event-triggered automation |
| `backend/docs/canon/event-catalog.md` | **AUTHORITY** | 126-event registry with event names, producers, entities, triggers. EVENT_AND_QUEUE_ARCHITECTURE.md covers mechanics; event-catalog.md covers the event registry itself. Both authoritative for their sub-domain. |
| `docs/08_reports/EVENT_DISCOVERY_REPORT.md` | SUPPORTING | Discovery findings; defers to above authorities. |
| `backend/docs/services/outbox-system.md` | SUPPORTING | Outbox system implementation notes. |

---

### D-010: Error Handling Contract

**Authority:** `docs/01_backend/ERROR_CONTRACT.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/01_backend/ERROR_CONTRACT.md` | **AUTHORITY** | Error envelope shape, error codes, HTTP status conventions |
| `backend/docs/services/error-registry.md` | SUPPORTING | Detailed error code registry; complements ERROR_CONTRACT.md. Should be cross-referenced. |

---

### D-011: Validation Rules

**Authority:** `docs/01_backend/VALIDATION_RULES.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/01_backend/VALIDATION_RULES.md` | **AUTHORITY** | DB-level CHECK constraints, application-layer validation per entity |
| `docs/03_fullstack_contracts/VALIDATION_PARITY.md` | SUPPORTING | Frontend vs. backend comparison. Defers to VALIDATION_RULES.md for backend rules. |
| `design/hrms-ui-backend-gaps.md` (BG-XXX validation gaps) | SUPPORTING | Validation gap register; defers to VALIDATION_RULES.md for current rules. |

---

### D-012: External Integrations

**Authority:** `docs/01_backend/INTEGRATION_CATALOG.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/01_backend/INTEGRATION_CATALOG.md` | **AUTHORITY** | All external integrations — FBR, EOBI, ATL, Raast, bank salary, biometric, WhatsApp, accounting |
| `backend/docs/specs/integrations/accounting.md` | SUPPORTING | Accounting integration detail. Defers to INTEGRATION_CATALOG.md for catalog claims. |
| `backend/docs/specs/integrations/whatsapp.md` | SUPPORTING | WhatsApp integration detail. Defers to INTEGRATION_CATALOG.md for catalog claims. |
| `backend/docs/specs/country/pakistan/compliance.md` | SUPPORTING | Pakistan compliance integration detail. Remains primary for Pakistan-specific implementation. |
| `backend/docs/specs/country/pakistan/payroll.md` | SUPPORTING | Pakistan payroll calculation detail. Remains primary for Pakistan-specific implementation. |

---

### D-013: Authentication and Tenancy

**Authority:** `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` | **AUTHORITY** | JWT HS256, token lifecycle, tenant_id propagation, session/refresh, exempt routes |
| `backend/docs/canon/security-model.md` | RETIRED | Superseded. Content absorbed into AUTH_AND_TENANCY_CONTRACT.md and SECURITY_DISCOVERY_REPORT.md. |
| `docs/08_reports/SECURITY_DISCOVERY_REPORT.md` | SUPPORTING | Discovery findings. Defers to AUTH_AND_TENANCY_CONTRACT.md for current auth model. |

---

### D-014: Roles, Permissions, and Capabilities

**Authority:** `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md` | **AUTHORITY** | 6 roles, capability matrix, 5 scope types, deny-by-default RBAC |
| `backend/docs/canon/capability-matrix.md` | SUPPORTING | Retained for detailed CAP-XXX codes actively referenced by code and tests. Superseded for role/permission claims but CAP-XXX code definitions remain uniquely here. |

---

### D-015: Data Shapes and API Response Formats

**Authority:** `docs/03_fullstack_contracts/DATA_SHAPE_REGISTRY.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/03_fullstack_contracts/DATA_SHAPE_REGISTRY.md` | **AUTHORITY** | API data shapes per major entity, snake_case conventions |
| `design/hrms-api-contracts.md` | SUPPORTING | UI-layer response expectations. Predates DATA_SHAPE_REGISTRY.md. Relevant for Frontend Authority Capture. |

---

### D-016: Country Layer Architecture

**Authority:** `backend/docs/canon/country-layer.md` *(no new authority doc yet)*

| Document | Role | Notes |
|----------|------|-------|
| `backend/docs/canon/country-layer.md` | **AUTHORITY** | Country-adapter pattern, CountryResolver, adapter interface. No new authority doc covers this domain. Remains primary authority until Backend Architecture Coverage is expanded. |
| `docs/01_backend/BACKEND_ARCHITECTURE.md` (§12) | SUPPORTING | Country layer section in BACKEND_ARCHITECTURE.md supplements but does not supersede country-layer.md. |
| `backend/docs/specs/country/pakistan/compliance.md` | SUPPORTING | Pakistan-specific country adapter implementation. |
| `backend/docs/specs/country/pakistan/payroll.md` | SUPPORTING | Pakistan-specific payroll adapter. |

---

### D-017: AI Governance

**Authority:** `docs/07_governance/AI_OPERATING_CONTEXT.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/07_governance/AI_OPERATING_CONTEXT.md` | **AUTHORITY** | AI operating rules, protected areas, FD-XXX constraints, escalation rules |
| `docs/07_governance/DECISION_ESCALATION_MATRIX.md` | SUPPORTING | Escalation matrix; companion to AI_OPERATING_CONTEXT.md. |

---

### D-018: Architectural Decision Records

**Authority:** `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` (for ADR-001 decisions)

| Document | Role | Notes |
|----------|------|-------|
| `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` | **AUTHORITY** | Foundation decisions — tech stack, architecture, deployment choices |
| `ops/answers.md` | HISTORICAL | C1–C5 pre-formal ADR decisions. Should migrate to formal ADRs (ADR-002 onward). |
| `docs/08_reports/RECOMMENDED_ADR_ROADMAP.md` | SUPPORTING | Recommended future ADR topics. |

---

### D-019: Cross-Layer Fullstack Traceability

**Authority:** `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md` | **AUTHORITY** | 15 user journeys, backend evidence layer, fullstack traceability |
| `design/hrms-ui-backend-gaps.md` | SUPPORTING | UI-to-backend gap analysis. Complements stitching contract. |
| `docs/08_reports/DOCUMENTATION_COVERAGE_MATRIX.md` | SUPPORTING | Coverage view by service. |

---

### D-020: Decision Intelligence System

**Authority:** `backend/docs/canon/decision-system.md` *(no new authority doc yet)*

| Document | Role | Notes |
|----------|------|-------|
| `backend/docs/canon/decision-system.md` | **AUTHORITY** | Decision Cards, anomaly engine, AI confidence tiers, DecisionCardStatus enum |
| `backend/docs/services/decision-service.md` | SUPPORTING | Decision service implementation detail. |

---

### D-021: Read Models

**Authority:** `backend/docs/canon/read-model-catalog.md` *(no new authority doc yet)*

| Document | Role | Notes |
|----------|------|-------|
| `backend/docs/canon/read-model-catalog.md` | **AUTHORITY** | Read-model projection catalog. No new authority equivalent. |
| `backend/docs/canon/read-models.md` | SUPPORTING | Read-model implementation notes. |

---

### D-022: UI Architecture

**Authority:** `design/hrms-archetype-system-v1.md` *(no governance-layer doc yet)*

| Document | Role | Notes |
|----------|------|-------|
| `design/hrms-archetype-system-v1.md` | **AUTHORITY** | 48-archetype UI system. Frontend Authority Capture not done. This is the current UI architecture authority. |
| `design/hrms-design-register-v1.md` | **AUTHORITY** | P-01 to P-33 UI patterns. Co-authority with archetype system for UI layer. |
| `backend/docs/canon/ui-surface-map.md` | SUPPORTING | UI surface-to-service mapping. Complements archetype system. |
| `design/hrms-doc-catalogue-v1.md` | SUPPORTING | UI-layer doc catalogue for session navigation. |
| `backend/docs/specs/ui/manager_dashboard.md` | SUPPORTING | Specific UI surface specification. |

---

### D-023: Gap Management

**Authority:** `docs/08_reports/BACKEND_GAP_REGISTER.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/08_reports/BACKEND_GAP_REGISTER.md` | **AUTHORITY** | Backend gap register — all 19 gaps, final statuses (all resolved) |
| `backend/docs/system/gap-register.md` | RETIRED | Superseded. Original gap register G01–Gxx, now outdated. |
| `docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md` | SUPPORTING | Cross-domain architectural gaps (GAP-A-001 through GAP-T-xxx). Addresses different scope than BACKEND_GAP_REGISTER.md — covers frontend, deployment, testing gaps too. |
| `design/hrms-ui-backend-gaps.md` | SUPPORTING | UI-to-backend gaps (BG-001–034). Relevant for Frontend Authority Capture. |
| `backend/docs/design/micro-fix-register.md` | HISTORICAL | Micro-fix register from build passes. Completed. |

---

### D-024: Risk Management

**Authority:** `docs/08_reports/BACKEND_RISK_REGISTER.md`

| Document | Role | Notes |
|----------|------|-------|
| `docs/08_reports/BACKEND_RISK_REGISTER.md` | **AUTHORITY** | Backend risk register — all 13 risks, all resolved. |

---

### D-025: Infrastructure and Deployment

**Authority:** None established *(gap — no authoritative deployment doc)*

| Document | Role | Notes |
|----------|------|-------|
| `backend/docs/deployment.md` | SUPPORTING | Deployment process notes. |
| `backend/deployment/README.md` | SUPPORTING | Deployment configuration overview. |
| `backend/docs/system/infrastructure.md` | SUPPORTING | Infrastructure notes. |
| `docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md` (GAP-A-002) | REFERENCE | Deployment runbook absence flagged as a gap. |

**Action Required:** No authoritative deployment document exists. GAP-A-002 is open. Deployment Authority Capture is a future phase.

---

### D-026: Testing and QA

**Authority:** None established *(gap)*

| Document | Role | Notes |
|----------|------|-------|
| `backend/docs/system/qc-suite.md` | SUPPORTING | QC suite definitions and scoring. |
| `docs/08_reports/DOCUMENTATION_COVERAGE_MATRIX.md` | SUPPORTING | Coverage view. |

**Action Required:** No authoritative testing document exists. Testing Authority Capture is a future phase.

---

### D-027: Market Context and Product Positioning

**Authority:** `backend/docs/system/MASTER MARKET RESEARCH.md`

| Document | Role | Notes |
|----------|------|-------|
| `backend/docs/system/MASTER MARKET RESEARCH.md` | **AUTHORITY** | Consolidated market research. |
| `backend/docs/system/archive/Pakistan_HRMS_Market_Research_Report_(2024–2026) MANUS AI.md` | ARCHIVE | Source research artifact. |
| `backend/docs/system/archive/RMS MARKET RESEARCH--CHAT GPT.md` | ARCHIVE | Source research artifact. |

---

## DOMAIN AUTHORITY SUMMARY

| Domain ID | Domain | Authority Document | Status |
|-----------|--------|-------------------|--------|
| D-001 | Project Identity | `docs/00_authority/PROJECT_CHARTER.md` | Established |
| D-002 | Feature Scope | `docs/00_authority/FEATURE_SCOPE.md` | Established |
| D-003 | Domain Model | `docs/00_authority/DOMAIN_MODEL.md` | Established |
| D-004 | Product Workflows | `docs/00_authority/PRODUCT_WORKFLOWS.md` | Established |
| D-005 | Backend Architecture | `docs/01_backend/BACKEND_ARCHITECTURE.md` | Established |
| D-006 | Database Schema | `docs/01_backend/DATABASE_SCHEMA.md` | Established |
| D-007 | API Contract | `docs/01_backend/API_CONTRACT.md` | Established |
| D-007b | API Standards | `backend/docs/canon/api-standards.md` | Retained (active code anchor) |
| D-008 | Service Catalog | `docs/01_backend/SERVICE_CATALOG.md` | Established |
| D-009a | Event Architecture | `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md` | Established |
| D-009b | Event Registry | `backend/docs/canon/event-catalog.md` | Retained (no new equivalent) |
| D-010 | Error Contract | `docs/01_backend/ERROR_CONTRACT.md` | Established |
| D-011 | Validation Rules | `docs/01_backend/VALIDATION_RULES.md` | Established |
| D-012 | External Integrations | `docs/01_backend/INTEGRATION_CATALOG.md` | Established |
| D-013 | Auth and Tenancy | `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` | Established |
| D-014 | Roles and Permissions | `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md` | Established |
| D-015 | Data Shapes | `docs/03_fullstack_contracts/DATA_SHAPE_REGISTRY.md` | Established |
| D-016 | Country Layer | `backend/docs/canon/country-layer.md` | **Gap — no new authority** |
| D-017 | AI Governance | `docs/07_governance/AI_OPERATING_CONTEXT.md` | Established |
| D-018 | ADRs | `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` | Partially established |
| D-019 | Fullstack Traceability | `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md` | Established |
| D-020 | Decision Intelligence | `backend/docs/canon/decision-system.md` | **Gap — no new authority** |
| D-021 | Read Models | `backend/docs/canon/read-model-catalog.md` | **Gap — no new authority** |
| D-022 | UI Architecture | `design/hrms-archetype-system-v1.md` | **Gap — Frontend Capture pending** |
| D-023 | Gap Management | `docs/08_reports/BACKEND_GAP_REGISTER.md` | Established (backend scope) |
| D-024 | Risk Management | `docs/08_reports/BACKEND_RISK_REGISTER.md` | Established (backend scope) |
| D-025 | Deployment | None | **Gap — Deployment Capture pending** |
| D-026 | Testing and QA | None | **Gap — Testing Capture pending** |
| D-027 | Market Context | `backend/docs/system/MASTER MARKET RESEARCH.md` | Established |
