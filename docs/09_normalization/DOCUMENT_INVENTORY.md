# DOCUMENT INVENTORY

Status: Active
Authority Level: Medium
Created: 2026-06-16
Owner: AI
Phase: Documentation Normalization and Authority Consolidation

---

## PURPOSE

Complete inventory of all project documentation (150 files). Excludes venv/library files (`backend/.venv/`, `backend/Lib/`). Every file is listed with path, category, and brief description.

---

## INVENTORY COUNT SUMMARY

| Layer | Count |
|-------|-------|
| Phase mandate documents (root-level) | 5 |
| Backend README files | 3 |
| Backend canon docs (`backend/docs/canon/`) | 14 |
| Backend design/build-pass reports (`backend/docs/design/`) | 15 |
| Backend legacy reports (`backend/docs/reports/`) | 2 |
| Backend per-service docs (`backend/docs/services/`) | 29 |
| Backend specifications (`backend/docs/specs/`) | 7 |
| Backend system/ops docs (`backend/docs/system/`) | 13 |
| Backend system archive (`backend/docs/system/archive/`) | 7 |
| Backend misc | 2 |
| Design UI docs (`design/`) | 9 |
| Governance authority docs (`docs/00_authority/`) | 5 |
| Backend authority docs (`docs/01_backend/`) | 8 |
| Fullstack contracts (`docs/03_fullstack_contracts/`) | 5 |
| Decision records (`docs/06_decisions/`) | 1 |
| Governance ops (`docs/07_governance/`) | 2 |
| Reports and registers (`docs/08_reports/`) | 14 |
| Ops workspace docs (`ops/`) | 8 |
| **Total** | **150** |

---

## SECTION 1 — PHASE MANDATE DOCUMENTS (Root Level)

| # | Path | Description |
|---|------|-------------|
| 1 | `AUDIT REMEDIATION.md` | Process mandate: review most recent audit report and resolve all findings |
| 2 | `DOCUMENTATION NORMALIZATION AND AUTHORITY CONSOLIDATION.md` | This phase's mandate: normalize all docs before Frontend Capture begins |
| 3 | `GOVERNANCE IMPLEMENTATION PHASE 1.md` | Phase 1 mandate: establish governance foundation |
| 4 | `PHASE 1 GOVERNANCE VALIDATION.md` | Phase 1 validation mandate: audit consistency of Phase 1 documents |
| 5 | `PHASE 2 – BACKEND AUTHORITY CAPTURE.md` | Phase 2 mandate: capture backend authority as verified documentation |

---

## SECTION 2 — BACKEND README FILES

| # | Path | Description |
|---|------|-------------|
| 6 | `backend/README.md` | Backend repository overview |
| 7 | `backend/api-gateway/README.md` | API Gateway module documentation |
| 8 | `backend/deployment/README.md` | Deployment configuration documentation |

---

## SECTION 3 — BACKEND MISC

| # | Path | Description |
|---|------|-------------|
| 9 | `backend/pending.md` | Legacy pending work items for backend |
| 10 | `backend/docs/deployment.md` | Deployment process notes |

---

## SECTION 4 — BACKEND CANON DOCS (`backend/docs/canon/`)

Original canonical documentation layer established during backend build.

| # | Path | Description |
|---|------|-------------|
| 11 | `backend/docs/canon/api-standards.md` | API design standards — versioning, naming, response shape, pagination |
| 12 | `backend/docs/canon/capability-matrix.md` | 40+ capability codes (CAP-XXX) mapped to services, roles, and scopes |
| 13 | `backend/docs/canon/country-layer.md` | Country-adapter architecture, CountryResolver, adapter pattern |
| 14 | `backend/docs/canon/data-architecture.md` | DB schema overview, entity column definitions (pre-migration-014/015) |
| 15 | `backend/docs/canon/decision-system.md` | Decision Intelligence system — Decision Cards, anomaly engine, AI confidence tiers |
| 16 | `backend/docs/canon/domain-model.md` | Original domain entity model (predates `docs/00_authority/DOMAIN_MODEL.md`) |
| 17 | `backend/docs/canon/event-catalog.md` | Canonical event registry — 126 events with producer, entity, and trigger |
| 18 | `backend/docs/canon/read-model-catalog.md` | Read-model projection catalog |
| 19 | `backend/docs/canon/read-models.md` | Read-model implementation notes |
| 20 | `backend/docs/canon/release-scope.md` | Original feature scope definition (predates `docs/00_authority/FEATURE_SCOPE.md`) |
| 21 | `backend/docs/canon/security-model.md` | Security model — JWT, RBAC, tenant isolation (predates AUTH_AND_TENANCY_CONTRACT) |
| 22 | `backend/docs/canon/service-map.md` | Service topology with stale refs annotated TBD (partially superseded) |
| 23 | `backend/docs/canon/ui-surface-map.md` | UI surface-to-service mapping (frontend scope, not yet captured in new authority layer) |
| 24 | `backend/docs/canon/workflow-catalog.md` | Detailed workflow definitions (more granular than `PRODUCT_WORKFLOWS.md`) |

---

## SECTION 5 — BACKEND DESIGN / BUILD-PASS REPORTS (`backend/docs/design/`)

Historical convergence pass documentation from Sessions P28–P51.

| # | Path | Description |
|---|------|-------------|
| 25 | `backend/docs/design/addon-certification-pass-p51.md` | Add-on service certification pass P51 |
| 26 | `backend/docs/design/addon-convergence-report-p50.md` | Add-on service convergence report P50 |
| 27 | `backend/docs/design/api-contract-standardization-summary.md` | API contract standardization summary |
| 28 | `backend/docs/design/background-jobs-summary.md` | Background jobs implementation summary |
| 29 | `backend/docs/design/backward-compatibility-report-p28.md` | Stub pointing to `convergence-history.md` P28 section |
| 30 | `backend/docs/design/chaos-auto-healing-report.md` | Chaos/auto-healing implementation report |
| 31 | `backend/docs/design/convergence-history.md` | Consolidated record of P28–P33 convergence passes |
| 32 | `backend/docs/design/data-integrity-report-p29.md` | Stub pointing to `convergence-history.md` P29 section |
| 33 | `backend/docs/design/design-system-anchor.md` | Design system anchor reference |
| 34 | `backend/docs/design/event-reliability-report-p30.md` | Stub pointing to `convergence-history.md` P30 section |
| 35 | `backend/docs/design/final-convergence-report-p32.md` | Stub pointing to `convergence-history.md` P32 section |
| 36 | `backend/docs/design/final-system-certification-pass-p33.md` | Stub pointing to `convergence-history.md` P33 section |
| 37 | `backend/docs/design/micro-fix-register.md` | Micro-fix register for surgical patch operations |
| 38 | `backend/docs/design/search-indexing-summary.md` | Search service indexing summary |
| 39 | `backend/docs/design/workflow-integrity-report-p31.md` | Stub pointing to `convergence-history.md` P31 section |

---

## SECTION 6 — BACKEND LEGACY REPORTS (`backend/docs/reports/`)

| # | Path | Description |
|---|------|-------------|
| 40 | `backend/docs/reports/alignment_final.md` | Stub pointing to `intent_build_alignment.md` — alignment state as of 2026-03-31 |
| 41 | `backend/docs/reports/platform_validation_2026-04-01.md` | Platform validation report as of 2026-04-01 |

---

## SECTION 7 — BACKEND PER-SERVICE DOCS (`backend/docs/services/`)

One documentation file per service/module.

| # | Path | Description |
|---|------|-------------|
| 42 | `backend/docs/services/attendance-service.md` | Attendance service documentation |
| 43 | `backend/docs/services/audit-service.md` | Audit service documentation |
| 44 | `backend/docs/services/auth-service.md` | Auth service documentation |
| 45 | `backend/docs/services/automation-service.md` | Automation service documentation |
| 46 | `backend/docs/services/bank-service.md` | Bank/disbursement service documentation |
| 47 | `backend/docs/services/compliance-service.md` | Compliance service documentation |
| 48 | `backend/docs/services/decision-service.md` | Decision intelligence service documentation |
| 49 | `backend/docs/services/employee-service.md` | Employee service documentation |
| 50 | `backend/docs/services/engagement-service.md` | Engagement/survey service documentation |
| 51 | `backend/docs/services/error-registry.md` | Error code registry documentation |
| 52 | `backend/docs/services/ewa-financial-service.md` | EWA financial service documentation |
| 53 | `backend/docs/services/expense-service.md` | Expense service documentation |
| 54 | `backend/docs/services/experience-layer-service.md` | Experience layer service documentation |
| 55 | `backend/docs/services/governance-service.md` | Governance service documentation |
| 56 | `backend/docs/services/helpdesk-service.md` | Helpdesk service documentation |
| 57 | `backend/docs/services/hiring-service.md` | Hiring/recruitment service documentation |
| 58 | `backend/docs/services/integration-service.md` | Integration hub service documentation |
| 59 | `backend/docs/services/leave-service.md` | Leave management service documentation |
| 60 | `backend/docs/services/notification-service.md` | Notification service documentation |
| 61 | `backend/docs/services/outbox-system.md` | Outbox/event system documentation |
| 62 | `backend/docs/services/payroll-service.md` | Payroll service documentation |
| 63 | `backend/docs/services/performance-service.md` | Performance management service documentation |
| 64 | `backend/docs/services/project-service.md` | Project management service documentation |
| 65 | `backend/docs/services/reporting-analytics-service.md` | Reporting and analytics service documentation |
| 66 | `backend/docs/services/search-service.md` | Search service documentation |
| 67 | `backend/docs/services/settings-service.md` | Settings and HR policy service documentation |
| 68 | `backend/docs/services/travel-service.md` | Travel management service documentation |
| 69 | `backend/docs/services/whatsapp-service.md` | WhatsApp channel service documentation |
| 70 | `backend/docs/services/workflow-service.md` | Workflow engine service documentation |

---

## SECTION 8 — BACKEND SPECIFICATIONS (`backend/docs/specs/`)

| # | Path | Description |
|---|------|-------------|
| 71 | `backend/docs/specs/country/pakistan/compliance.md` | Pakistan statutory compliance specification (FBR, EOBI, PESSI) |
| 72 | `backend/docs/specs/country/pakistan/payroll.md` | Pakistan payroll calculation specification |
| 73 | `backend/docs/specs/experience-layer.md` | Experience layer (mobile gateway) specification |
| 74 | `backend/docs/specs/integrations/accounting.md` | Accounting integration specification |
| 75 | `backend/docs/specs/integrations/whatsapp.md` | WhatsApp integration specification |
| 76 | `backend/docs/specs/mobile-layer.md` | Mobile layer specification |
| 77 | `backend/docs/specs/ui/manager_dashboard.md` | Manager dashboard UI specification |

---

## SECTION 9 — BACKEND SYSTEM DOCS (`backend/docs/system/`)

Original session-continuity and operational documentation.

| # | Path | Description |
|---|------|-------------|
| 78 | `backend/docs/system/MASTER BEHAVIOR SPEC.md` | Master behavior specification (merged canonical) |
| 79 | `backend/docs/system/MASTER BUILD SPEC.md` | Master build specification v2.0 |
| 80 | `backend/docs/system/MASTER MARKET RESEARCH.md` | Master market research document |
| 81 | `backend/docs/system/catalogue.md` | Session entry-point catalogue for backend ops docs |
| 82 | `backend/docs/system/gap-register.md` | Original gap register (pre-BACKEND_GAP_REGISTER.md) |
| 83 | `backend/docs/system/infrastructure.md` | Infrastructure documentation |
| 84 | `backend/docs/system/intent_build_alignment.md` | Intent-to-build alignment snapshot (2026-03-31 baseline) |
| 85 | `backend/docs/system/pending.md` | Pending items list (legacy) |
| 86 | `backend/docs/system/progress.md` | Refactor progress tracker (legacy) |
| 87 | `backend/docs/system/qc-suite.md` | QC suite documentation |
| 88 | `backend/docs/system/roadmap.md` | Product roadmap |
| 89 | `backend/docs/system/service-manifest.md` | Service manifest with runtime status |
| 90 | `backend/docs/system/success-criteria.md` | Success criteria documentation |
| 91 | `backend/docs/system/system-purpose.md` | System identity and 7 design principles |

---

## SECTION 10 — BACKEND SYSTEM ARCHIVE (`backend/docs/system/archive/`)

Pre-build original source specification files.

| # | Path | Description |
|---|------|-------------|
| 92 | `backend/docs/system/archive/COMPLETE HRMS BUILD SPEC.md` | First-generation complete build spec |
| 93 | `backend/docs/system/archive/HRMS Repo Surgical Upgrade Spec.md` | Repo surgical upgrade specification |
| 94 | `backend/docs/system/archive/HRMS SPEC.md` | Original HRMS specification |
| 95 | `backend/docs/system/archive/HRMS SYSTEM BEHAVIOR SPEC.md` | Original system behavior spec |
| 96 | `backend/docs/system/archive/MARKET-VALIDATED BEHAVIOR SPEC.md` | Market-validated behavior specification |
| 97 | `backend/docs/system/archive/Pakistan_HRMS_Market_Research_Report_(2024–2026) MANUS AI.md` | Pakistan HRMS market research (Manus AI) |
| 98 | `backend/docs/system/archive/RMS MARKET RESEARCH--CHAT GPT.md` | HRMS market research (ChatGPT) |

---

## SECTION 11 — DESIGN UI DOCS (`design/`)

UI design-layer documentation for Meridian HCM frontend (48 archetypes).

| # | Path | Description |
|---|------|-------------|
| 99 | `design/hrms-api-contracts.md` | UI-layer API contracts — frontend response shape expectations |
| 100 | `design/hrms-archetype-system-v1.md` | 48-archetype UI system definition |
| 101 | `design/hrms-build-protocol-sop-v1.md` | UI build protocol standard operating procedure |
| 102 | `design/hrms-claude-code-prompt-v1.md` | Claude Code session prompt template for UI builds |
| 103 | `design/hrms-contract-structure-v1.md` | Frontend contract file structure and naming |
| 104 | `design/hrms-design-register-v1.md` | UI pattern register (P-01 to P-33 patterns) |
| 105 | `design/hrms-doc-catalogue-v1.md` | Meridian HCM doc catalogue (UI-layer equivalent of `catalogue.md`) |
| 106 | `design/hrms-stabilisation-sop-v1.md` | UI stabilization SOP with pass history |
| 107 | `design/hrms-ui-backend-gaps.md` | UI-to-backend gap register (BG-001–BG-034, CG-001, UG-001–002) |

---

## SECTION 12 — GOVERNANCE AUTHORITY DOCS (`docs/00_authority/`)

Phase 1 primary authority documents.

| # | Path | Description |
|---|------|-------------|
| 108 | `docs/00_authority/DOMAIN_MODEL.md` | Authoritative domain entity model — 57+ entities, multi-tenancy invariant |
| 109 | `docs/00_authority/FEATURE_SCOPE.md` | Authoritative feature scope — 24 features, IN/OUT of scope |
| 110 | `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md` | Fullstack traceability — 15 journeys, Phase 2 backend evidence layer |
| 111 | `docs/00_authority/PRODUCT_WORKFLOWS.md` | Product workflow definitions — 9 core workflows |
| 112 | `docs/00_authority/PROJECT_CHARTER.md` | Project charter — purpose, principles, governance rules |

---

## SECTION 13 — BACKEND AUTHORITY DOCS (`docs/01_backend/`)

Phase 2 backend authority documents.

| # | Path | Description |
|---|------|-------------|
| 113 | `docs/01_backend/API_CONTRACT.md` | Authoritative API contract — 21 routes, 164 endpoints, response envelope |
| 114 | `docs/01_backend/BACKEND_ARCHITECTURE.md` | Authoritative backend architecture — runtime, gateway, resilience, country layer |
| 115 | `docs/01_backend/DATABASE_SCHEMA.md` | Authoritative database schema — 58 tables, all migrations 001–015 |
| 116 | `docs/01_backend/ERROR_CONTRACT.md` | Authoritative error contract — codes, envelope, HTTP status mapping |
| 117 | `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md` | Authoritative event architecture — outbox pattern, 126 events |
| 118 | `docs/01_backend/INTEGRATION_CATALOG.md` | Authoritative integration catalog — all external integrations |
| 119 | `docs/01_backend/SERVICE_CATALOG.md` | Authoritative service catalog — 24 services, ports, owned entities |
| 120 | `docs/01_backend/VALIDATION_RULES.md` | Authoritative validation rules — DB-level and application-level |

---

## SECTION 14 — FULLSTACK CONTRACTS (`docs/03_fullstack_contracts/`)

| # | Path | Description |
|---|------|-------------|
| 121 | `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` | Auth/tenancy — JWT model, token lifecycle, tenant isolation |
| 122 | `docs/03_fullstack_contracts/CONTRACT_VERSION_REGISTRY.md` | API version registry — 21 routes, 47 frontend contracts indexed |
| 123 | `docs/03_fullstack_contracts/DATA_SHAPE_REGISTRY.md` | API data shapes per entity — snake_case DB vs. API fields |
| 124 | `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md` | 6 roles, capability matrix, 5 scope types, deny-by-default |
| 125 | `docs/03_fullstack_contracts/VALIDATION_PARITY.md` | Frontend vs. backend validation coverage comparison |

---

## SECTION 15 — DECISION RECORDS (`docs/06_decisions/`)

| # | Path | Description |
|---|------|-------------|
| 126 | `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` | ADR-001: Project foundation, tech stack, architecture choices |

---

## SECTION 16 — GOVERNANCE OPERATIONS (`docs/07_governance/`)

| # | Path | Description |
|---|------|-------------|
| 127 | `docs/07_governance/AI_OPERATING_CONTEXT.md` | AI operating context — protected areas, escalation rules, FD-XXX constraints |
| 128 | `docs/07_governance/DECISION_ESCALATION_MATRIX.md` | Decision escalation matrix — what AI can/cannot decide |

---

## SECTION 17 — REPORTS AND REGISTERS (`docs/08_reports/`)

| # | Path | Description |
|---|------|-------------|
| 129 | `docs/08_reports/API_DISCOVERY_REPORT.md` | API discovery findings — 164 endpoints, 3 gaps |
| 130 | `docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md` | Architectural gaps across all domains |
| 131 | `docs/08_reports/BACKEND_ARCHITECTURE_REPORT.md` | Backend architecture findings — 7 findings |
| 132 | `docs/08_reports/BACKEND_AUTHORITY_CAPTURE_REPORT.md` | Phase 2 master summary — 19/19 gaps resolved |
| 133 | `docs/08_reports/BACKEND_GAP_REGISTER.md` | Backend gap register — all 19 gaps, final statuses |
| 134 | `docs/08_reports/BACKEND_RISK_REGISTER.md` | Backend risk register — all 13 risks, all resolved |
| 135 | `docs/08_reports/DATABASE_DISCOVERY_REPORT.md` | Database discovery — 58 tables, schema findings |
| 136 | `docs/08_reports/DOCUMENTATION_COVERAGE_MATRIX.md` | Documentation coverage per service |
| 137 | `docs/08_reports/EVENT_DISCOVERY_REPORT.md` | Event discovery — dual outbox, 8 findings |
| 138 | `docs/08_reports/GOVERNANCE_CONSISTENCY_AUDIT.md` | Phase 1 governance consistency audit — findings |
| 139 | `docs/08_reports/GOVERNANCE_IMPLEMENTATION_REPORT.md` | Phase 1 governance implementation summary |
| 140 | `docs/08_reports/RECOMMENDED_ADR_ROADMAP.md` | Recommended future ADR topics |
| 141 | `docs/08_reports/REMEDIATION_REPORT.md` | Remediation report — consistency audit findings resolved |
| 142 | `docs/08_reports/SECURITY_DISCOVERY_REPORT.md` | Security discovery — auth model, 4 bypass services |

---

## SECTION 18 — OPS WORKSPACE DOCS (`ops/`)

Workspace operational continuity artifacts from UI build sessions.

| # | Path | Description |
|---|------|-------------|
| 143 | `ops/HRMS PRODUCT SPEC.md` | Product spec (SUPERSEDED — header says "do not edit", kept as reference) |
| 144 | `ops/answers.md` | 5 architectural decisions (C1–C5) + final service map |
| 145 | `ops/build-progress.md` | Build progress continuity (H01–H13 archetypes, Sessions 1–26+) |
| 146 | `ops/hrms-directory-structure-v1.md` | Directory structure reference (pre-2026-06-07 restructure) |
| 147 | `ops/hrms-progress.md` | Full build session history (1,113 lines, Session 1–9+) |
| 148 | `ops/normalisation-tracker.md` | Line-by-line normalisation read tracker (109/109 DONE) |
| 149 | `ops/pending.md` | Outstanding pending items — 10 UI pages + 2 deferred items |
| 150 | `ops/tracker.md` | Full workspace read tracker (file-by-file cataloguing pass) |
