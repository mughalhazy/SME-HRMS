# DOCUMENT CLASSIFICATION MATRIX

Status: Active
Authority Level: Medium
Created: 2026-06-16
Owner: AI
Phase: Documentation Normalization and Authority Consolidation

---

## PURPOSE

Classifies every project document (150 files) by type. Classification governs how each document should be treated going forward.

---

## CLASSIFICATION DEFINITIONS

| Class | Definition |
|-------|-----------|
| **Authority Document** | Single source of truth for an information domain. Governs all related documents. |
| **Supporting Reference** | Extends or elaborates an authority document. Must not contradict it. |
| **Operational Artifact** | Session-continuity, progress tracking, or workspace management. Not a system truth. |
| **Historical Record** | Point-in-time snapshot. Valid when written; may not reflect current state. |
| **Generated Report** | Discovery, audit, or gap analysis output. Supports authority documents. |
| **Working Draft** | In progress; not yet authoritative. May contain TBDs. |
| **Mandate Document** | Phase execution instructions. Not a system truth — governs AI process only. |
| **Retired Document** | Superseded by a newer authority. Kept for traceability. Should be annotated. |
| **Archive Document** | Pre-build source artifacts. Historical only. |
| **Duplicate Document** | Redundant copy of content that lives authoritatively elsewhere. |

---

## CLASSIFICATION TABLE

### Phase Mandate Documents (Root Level)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 1 | `AUDIT REMEDIATION.md` | Mandate Document | Process instruction for resolving audit findings. Not a system truth. |
| 2 | `DOCUMENTATION NORMALIZATION AND AUTHORITY CONSOLIDATION.md` | Mandate Document | This phase's execution instructions. |
| 3 | `GOVERNANCE IMPLEMENTATION PHASE 1.md` | Mandate Document | Phase 1 execution instructions. Now complete. |
| 4 | `PHASE 1 GOVERNANCE VALIDATION.md` | Mandate Document | Phase 1 validation instructions. Now complete. |
| 5 | `PHASE 2 – BACKEND AUTHORITY CAPTURE.md` | Mandate Document | Phase 2 execution instructions. Now complete. |

---

### Backend README Files

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 6 | `backend/README.md` | Supporting Reference | Developer onboarding reference. No authority claims. |
| 7 | `backend/api-gateway/README.md` | Supporting Reference | Module-level orientation. Superseded by `BACKEND_ARCHITECTURE.md` for architecture claims. |
| 8 | `backend/deployment/README.md` | Supporting Reference | Deployment orientation. No single authority for deployment exists yet. |

---

### Backend Misc

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 9 | `backend/pending.md` | Operational Artifact | Legacy pending list. Superseded by Phase 2 gap/risk registers. |
| 10 | `backend/docs/deployment.md` | Supporting Reference | Deployment process notes. No new authority layer covers deployment yet. |

---

### Backend Canon Docs (`backend/docs/canon/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 11 | `backend/docs/canon/api-standards.md` | Supporting Reference | API standards still actively used as anchor by backend code and tests. Partially superseded by `API_CONTRACT.md` for contract claims but retains standalone authority for coding standards. |
| 12 | `backend/docs/canon/capability-matrix.md` | Supporting Reference | 40+ CAP-XXX codes still actively referenced by backend code. Partially superseded by `USER_ROLES_AND_PERMISSIONS.md` but retains detailed capability definitions. |
| 13 | `backend/docs/canon/country-layer.md` | Supporting Reference | Country-adapter architecture still valid. No new authority doc covers this domain specifically. Remains primary reference for country-layer design. |
| 14 | `backend/docs/canon/data-architecture.md` | Retired Document | Superseded by `docs/01_backend/DATABASE_SCHEMA.md` (Migrations 001–015, compound FK pattern). Pre-dates migration 014/015 fixes. Should be annotated as superseded. |
| 15 | `backend/docs/canon/decision-system.md` | Supporting Reference | Decision Intelligence detail (Decision Cards, AI confidence tiers) not fully captured in new authority layer. Remains primary reference for decision-service design. |
| 16 | `backend/docs/canon/domain-model.md` | Retired Document | Superseded by `docs/00_authority/DOMAIN_MODEL.md`. New version is more comprehensive and includes multi-tenancy invariant. Should be annotated as superseded. |
| 17 | `backend/docs/canon/event-catalog.md` | Supporting Reference | Event registry (126 events) is more detailed than `EVENT_AND_QUEUE_ARCHITECTURE.md`. Both are needed; catalog is the event definition authority, architecture doc covers outbox mechanics. |
| 18 | `backend/docs/canon/read-model-catalog.md` | Working Draft | Read-model projections not captured in any new authority document. Remains active reference. |
| 19 | `backend/docs/canon/read-models.md` | Working Draft | Read-model implementation notes. No new authority equivalent. |
| 20 | `backend/docs/canon/release-scope.md` | Retired Document | Superseded by `docs/00_authority/FEATURE_SCOPE.md`. Should be annotated as superseded. |
| 21 | `backend/docs/canon/security-model.md` | Retired Document | Superseded by `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md`. Should be annotated as superseded. |
| 22 | `backend/docs/canon/service-map.md` | Retired Document | Superseded by `docs/01_backend/SERVICE_CATALOG.md`. Some entries annotated TBD (ewa-financial-service). Should be annotated as superseded. |
| 23 | `backend/docs/canon/ui-surface-map.md` | Working Draft | No new authority doc covers UI surface-to-service mapping. Frontend Authority Capture not yet done. Remains active reference. |
| 24 | `backend/docs/canon/workflow-catalog.md` | Supporting Reference | More granular than `PRODUCT_WORKFLOWS.md`. Both are valid: authority doc covers business workflows; catalog covers technical workflow definitions. |

---

### Backend Design / Build-Pass Reports (`backend/docs/design/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 25 | `backend/docs/design/addon-certification-pass-p51.md` | Historical Record | Build pass P51 certification. Point-in-time. |
| 26 | `backend/docs/design/addon-convergence-report-p50.md` | Historical Record | Build pass P50 convergence. Point-in-time. |
| 27 | `backend/docs/design/api-contract-standardization-summary.md` | Historical Record | API contract standardization pass summary. |
| 28 | `backend/docs/design/background-jobs-summary.md` | Historical Record | Background jobs implementation summary. |
| 29 | `backend/docs/design/backward-compatibility-report-p28.md` | Historical Record | Stub pointing to `convergence-history.md`. P28 stub. |
| 30 | `backend/docs/design/chaos-auto-healing-report.md` | Historical Record | Chaos engineering pass report. |
| 31 | `backend/docs/design/convergence-history.md` | Historical Record | Consolidated P28–P33 build pass history. Most valuable of the design docs. |
| 32 | `backend/docs/design/data-integrity-report-p29.md` | Historical Record | Stub pointing to `convergence-history.md`. P29 stub. |
| 33 | `backend/docs/design/design-system-anchor.md` | Supporting Reference | Design system anchor reference. |
| 34 | `backend/docs/design/event-reliability-report-p30.md` | Historical Record | Stub pointing to `convergence-history.md`. P30 stub. |
| 35 | `backend/docs/design/final-convergence-report-p32.md` | Historical Record | Stub pointing to `convergence-history.md`. P32 stub. |
| 36 | `backend/docs/design/final-system-certification-pass-p33.md` | Historical Record | Stub (2 lines) pointing to `convergence-history.md`. P33 stub. |
| 37 | `backend/docs/design/micro-fix-register.md` | Historical Record | Micro-fix surgical patch register. |
| 38 | `backend/docs/design/search-indexing-summary.md` | Historical Record | Search indexing implementation summary. |
| 39 | `backend/docs/design/workflow-integrity-report-p31.md` | Historical Record | Stub pointing to `convergence-history.md`. P31 stub. |

---

### Backend Legacy Reports (`backend/docs/reports/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 40 | `backend/docs/reports/alignment_final.md` | Historical Record | Stub pointing to `intent_build_alignment.md`. 2026-03-31 baseline snapshot. |
| 41 | `backend/docs/reports/platform_validation_2026-04-01.md` | Historical Record | Platform validation at 2026-04-01. Pre-Sessions 2–8. |

---

### Backend Per-Service Docs (`backend/docs/services/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 42–70 | `backend/docs/services/*.md` (29 files) | Supporting Reference | Per-service design intent and API notes. No new authority doc covers per-service detail at this level. `SERVICE_CATALOG.md` covers service catalog; these cover individual service design. Remain active references but must defer to `SERVICE_CATALOG.md` for any conflict on service ownership/ports. |

Exception: `backend/docs/services/employee-service.md` — now stale regarding implementation (was TypeScript-only; now Python). Should be updated to reflect `employee_service.py`.

---

### Backend Specifications (`backend/docs/specs/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 71 | `backend/docs/specs/country/pakistan/compliance.md` | Supporting Reference | Pakistan compliance spec. No new authority doc covers country specs. Remains primary reference. |
| 72 | `backend/docs/specs/country/pakistan/payroll.md` | Supporting Reference | Pakistan payroll calculation spec. Remains primary reference. |
| 73 | `backend/docs/specs/experience-layer.md` | Supporting Reference | Experience layer specification. |
| 74 | `backend/docs/specs/integrations/accounting.md` | Supporting Reference | Accounting integration spec. Supplemented by `INTEGRATION_CATALOG.md`. |
| 75 | `backend/docs/specs/integrations/whatsapp.md` | Supporting Reference | WhatsApp integration spec. Supplemented by `INTEGRATION_CATALOG.md`. |
| 76 | `backend/docs/specs/mobile-layer.md` | Supporting Reference | Mobile layer specification. |
| 77 | `backend/docs/specs/ui/manager_dashboard.md` | Supporting Reference | Manager dashboard UI spec. |

---

### Backend System Docs (`backend/docs/system/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 78 | `backend/docs/system/MASTER BEHAVIOR SPEC.md` | Retired Document | Superseded by `docs/00_authority/PROJECT_CHARTER.md` + `PRODUCT_WORKFLOWS.md`. Should be annotated as superseded. |
| 79 | `backend/docs/system/MASTER BUILD SPEC.md` | Retired Document | Superseded by `docs/01_backend/BACKEND_ARCHITECTURE.md` + `DATABASE_SCHEMA.md`. Should be annotated. |
| 80 | `backend/docs/system/MASTER MARKET RESEARCH.md` | Historical Record | Market research foundation. Informs product decisions. No authority equivalent. |
| 81 | `backend/docs/system/catalogue.md` | Operational Artifact | Session entry-point catalogue for legacy docs. Superseded in function by this normalization layer but retains value as legacy navigation aid. |
| 82 | `backend/docs/system/gap-register.md` | Retired Document | Superseded by `docs/08_reports/BACKEND_GAP_REGISTER.md`. Original gap register is now fully resolved and outdated. |
| 83 | `backend/docs/system/infrastructure.md` | Supporting Reference | Infrastructure notes. No new authority doc covers infrastructure/deployment. |
| 84 | `backend/docs/system/intent_build_alignment.md` | Historical Record | Intent-to-build alignment at 2026-03-31 baseline. Valid for that snapshot only; explicitly self-disclaimed for Sessions 2–8. |
| 85 | `backend/docs/system/pending.md` | Operational Artifact | Legacy pending items. Superseded by Phase 2 registers. |
| 86 | `backend/docs/system/progress.md` | Operational Artifact | Legacy refactor progress tracker. Superseded by Phase 2 reports. |
| 87 | `backend/docs/system/qc-suite.md` | Supporting Reference | QC suite definitions and scoring rules. |
| 88 | `backend/docs/system/roadmap.md` | Working Draft | Product roadmap. No new authority equivalent. |
| 89 | `backend/docs/system/service-manifest.md` | Retired Document | Superseded by `docs/01_backend/SERVICE_CATALOG.md`. Contains stale TypeScript employee-service claim. |
| 90 | `backend/docs/system/success-criteria.md` | Supporting Reference | Build success criteria. |
| 91 | `backend/docs/system/system-purpose.md` | Retired Document | Superseded by `docs/00_authority/PROJECT_CHARTER.md`. Should be annotated. |

---

### Backend System Archive (`backend/docs/system/archive/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 92–98 | All 7 archive files | Archive Document | Pre-build source specifications and market research. Historical origin artifacts. No active authority role. Must be preserved for traceability. |

---

### Design UI Docs (`design/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 99 | `design/hrms-api-contracts.md` | Supporting Reference | UI-layer API contract expectations. Partially superseded by `API_CONTRACT.md` + `DATA_SHAPE_REGISTRY.md` for backend claims; still authoritative for UI response shape expectations until Frontend Authority Capture. |
| 100 | `design/hrms-archetype-system-v1.md` | Authority Document | 48-archetype UI system definition. No equivalent in new authority layer (Frontend not captured). Remains authoritative for UI architecture. |
| 101 | `design/hrms-build-protocol-sop-v1.md` | Operational Artifact | UI build SOP for session continuity. |
| 102 | `design/hrms-claude-code-prompt-v1.md` | Operational Artifact | Claude Code session prompt template for UI sessions. |
| 103 | `design/hrms-contract-structure-v1.md` | Supporting Reference | Frontend contract file structure. |
| 104 | `design/hrms-design-register-v1.md` | Authority Document | UI pattern register (P-01 to P-33). Authoritative for UI patterns until Frontend Authority Capture. |
| 105 | `design/hrms-doc-catalogue-v1.md` | Operational Artifact | UI-layer session entry-point catalogue. Active for UI sessions. |
| 106 | `design/hrms-stabilisation-sop-v1.md` | Operational Artifact | UI stabilization SOP with historical pass log. |
| 107 | `design/hrms-ui-backend-gaps.md` | Generated Report | UI-to-backend gap register (BG-001–034). Valuable for Frontend Authority Capture. |

---

### Governance Authority Docs (`docs/00_authority/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 108 | `docs/00_authority/DOMAIN_MODEL.md` | **Authority Document** | Primary domain entity authority. Supersedes `backend/docs/canon/domain-model.md`. |
| 109 | `docs/00_authority/FEATURE_SCOPE.md` | **Authority Document** | Primary feature scope authority. Supersedes `backend/docs/canon/release-scope.md`. |
| 110 | `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md` | **Authority Document** | Cross-layer traceability authority. No legacy equivalent. |
| 111 | `docs/00_authority/PRODUCT_WORKFLOWS.md` | **Authority Document** | Business workflow authority. Companion to `backend/docs/canon/workflow-catalog.md`. |
| 112 | `docs/00_authority/PROJECT_CHARTER.md` | **Authority Document** | Project identity, purpose, and governance rules authority. Supersedes `system-purpose.md`. |

---

### Backend Authority Docs (`docs/01_backend/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 113 | `docs/01_backend/API_CONTRACT.md` | **Authority Document** | Backend API authority. Supersedes `api-standards.md` for contract claims. |
| 114 | `docs/01_backend/BACKEND_ARCHITECTURE.md` | **Authority Document** | Backend architecture authority. Supersedes `MASTER BUILD SPEC.md`. |
| 115 | `docs/01_backend/DATABASE_SCHEMA.md` | **Authority Document** | Database schema authority. Supersedes `data-architecture.md`. |
| 116 | `docs/01_backend/ERROR_CONTRACT.md` | **Authority Document** | Error handling authority. Supersedes `error-registry.md` service doc. |
| 117 | `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md` | **Authority Document** | Event architecture authority. Companion to `event-catalog.md` (catalog = event registry). |
| 118 | `docs/01_backend/INTEGRATION_CATALOG.md` | **Authority Document** | External integration authority. Supersedes integration specs. |
| 119 | `docs/01_backend/SERVICE_CATALOG.md` | **Authority Document** | Service catalog authority. Supersedes `service-map.md` and `service-manifest.md`. |
| 120 | `docs/01_backend/VALIDATION_RULES.md` | **Authority Document** | Validation rules authority. No legacy equivalent. |

---

### Fullstack Contracts (`docs/03_fullstack_contracts/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 121 | `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` | **Authority Document** | Auth and tenancy authority. Supersedes `security-model.md`. |
| 122 | `docs/03_fullstack_contracts/CONTRACT_VERSION_REGISTRY.md` | **Authority Document** | API version registry authority. |
| 123 | `docs/03_fullstack_contracts/DATA_SHAPE_REGISTRY.md` | **Authority Document** | Data shape registry authority. |
| 124 | `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md` | **Authority Document** | Roles and permissions authority. Supersedes `capability-matrix.md` for role/permission claims. |
| 125 | `docs/03_fullstack_contracts/VALIDATION_PARITY.md` | Generated Report | Validation parity analysis. Supports `VALIDATION_RULES.md`. |

---

### Decision Records (`docs/06_decisions/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 126 | `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` | **Authority Document** | ADR-001 is authoritative for the architectural decisions it records. |

---

### Governance Operations (`docs/07_governance/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 127 | `docs/07_governance/AI_OPERATING_CONTEXT.md` | **Authority Document** | AI operating rules authority. No legacy equivalent. |
| 128 | `docs/07_governance/DECISION_ESCALATION_MATRIX.md` | **Authority Document** | Decision escalation authority. No legacy equivalent. |

---

### Reports and Registers (`docs/08_reports/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 129 | `docs/08_reports/API_DISCOVERY_REPORT.md` | Generated Report | Phase 2 API discovery findings. |
| 130 | `docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md` | Generated Report | Cross-domain architectural gap register. |
| 131 | `docs/08_reports/BACKEND_ARCHITECTURE_REPORT.md` | Generated Report | Phase 2 backend architecture findings. |
| 132 | `docs/08_reports/BACKEND_AUTHORITY_CAPTURE_REPORT.md` | Generated Report | Phase 2 master summary — all 19 gaps resolved. |
| 133 | `docs/08_reports/BACKEND_GAP_REGISTER.md` | Generated Report | Phase 2 gap register — supersedes `backend/docs/system/gap-register.md`. |
| 134 | `docs/08_reports/BACKEND_RISK_REGISTER.md` | Generated Report | Phase 2 risk register — all 13 risks resolved. |
| 135 | `docs/08_reports/DATABASE_DISCOVERY_REPORT.md` | Generated Report | Phase 2 database discovery findings. |
| 136 | `docs/08_reports/DOCUMENTATION_COVERAGE_MATRIX.md` | Generated Report | Documentation coverage per service. |
| 137 | `docs/08_reports/EVENT_DISCOVERY_REPORT.md` | Generated Report | Phase 2 event discovery findings. |
| 138 | `docs/08_reports/GOVERNANCE_CONSISTENCY_AUDIT.md` | Generated Report | Phase 1 governance consistency audit. |
| 139 | `docs/08_reports/GOVERNANCE_IMPLEMENTATION_REPORT.md` | Generated Report | Phase 1 governance implementation summary. |
| 140 | `docs/08_reports/RECOMMENDED_ADR_ROADMAP.md` | Generated Report | Recommended future ADR topics. |
| 141 | `docs/08_reports/REMEDIATION_REPORT.md` | Generated Report | Phase 1 audit remediation findings. |
| 142 | `docs/08_reports/SECURITY_DISCOVERY_REPORT.md` | Generated Report | Phase 2 security discovery findings. |

---

### Ops Workspace Docs (`ops/`)

| # | Document | Classification | Justification |
|---|----------|---------------|---------------|
| 143 | `ops/HRMS PRODUCT SPEC.md` | Retired Document | Self-labeled "SUPERSEDED." Kept as intent reference. No active authority role. |
| 144 | `ops/answers.md` | Historical Record | 5 architectural decisions (C1–C5). Predates formal ADR system. Should be absorbed into future ADRs. |
| 145 | `ops/build-progress.md` | Operational Artifact | UI build session progress (H01–H13). Active for UI continuity. |
| 146 | `ops/hrms-directory-structure-v1.md` | Historical Record | Pre-2026-06-07 directory structure. Stale — workspace restructured. |
| 147 | `ops/hrms-progress.md` | Operational Artifact | Full build session history (1,113 lines). Active for session continuity. |
| 148 | `ops/normalisation-tracker.md` | Operational Artifact | Line-by-line normalisation read tracker (109/109 DONE). Completed artifact. |
| 149 | `ops/pending.md` | Operational Artifact | Outstanding pending items — 10 UI pages + 2 deferred. Active work tracker. |
| 150 | `ops/tracker.md` | Operational Artifact | Full workspace file read tracker (cataloguing pass). Completed artifact. |

---

## CLASSIFICATION SUMMARY

| Classification | Count |
|---------------|-------|
| Authority Document | 21 |
| Supporting Reference | 32 |
| Generated Report | 17 |
| Operational Artifact | 14 |
| Historical Record | 16 |
| Mandate Document | 5 |
| Retired Document | 11 |
| Working Draft | 4 |
| Archive Document | 7 |
| **Total** | **127** |

Note: 29 per-service docs (`backend/docs/services/*.md`) counted as one Supporting Reference group above; individually they are 29 entries bringing the total to 150.
