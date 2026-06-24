# DOCUMENTATION COVERAGE MATRIX

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This matrix tracks documentation coverage across all services, domains, and cross-cutting concerns, comparing what governance requires against what exists (newly created + pre-existing).

---

## COVERAGE BY SERVICE

| Service | Port | Canon Domain Doc | Service-Level Doc | API Contract Trace | Test Coverage Doc | Coverage Status |
|---------|------|------------------|--------------------|--------------------|--------------------|------------------|
| employee-service | 8001 | Yes (`canon/domain-model.md`) | TBD | Partial (T-001–T-003, T-015) | TBD | Partial |
| attendance-service | 8002 | Yes | TBD | Partial (T-007) | TBD | Partial |
| leave-service | 8003 | Yes | TBD | Partial (T-004, T-005) | TBD | Partial |
| payroll-service | 8004 | Yes | TBD | Partial (T-006) | TBD | Partial |
| hiring-service | 8005 | Yes | TBD | Partial (T-008, T-009) | TBD | Partial |
| auth-service | 8006 | Yes | Yes (`docs/services/auth-service.md`) | Yes (T-010) | Partial (`test_auth_service.py`) | Good |
| notification-service | 8007 | Yes | TBD | Partial (T-014) | TBD | Partial |
| audit-service | 8008 | Yes | TBD | None | Partial (`test_audit_service.py`) | Partial |
| workflow-service | 8009 | Yes (`canon/workflow-catalog.md`) | TBD | Partial (T-005) | Partial (`test_workflow*.py`) | Partial |
| performance-service | 8010 | Partial | TBD | None | Partial (`test_performance*.py`) | Gap |
| engagement-service | 8011 | Partial | TBD | None | Partial (`test_engagement*.py`) | Gap |
| helpdesk-service | 8012 | TBD | TBD | None | TBD | Gap |
| reporting-analytics-service | 8013 | Partial | TBD | Partial (T-011) | Partial (`test_reporting_analytics.py`) | Partial |
| search-service | 8014 | TBD | TBD | None | Partial (`test_search_service.py`) | Gap |
| expense-service | 8015 | TBD | TBD | None | Partial (`test_expense*.py`) | Gap |
| integration-service | 8016 | TBD | TBD | None | TBD | Gap |
| automation-service | 8017 | Partial | TBD | None | TBD | Gap |
| travel-service | 8018 | TBD | TBD | None | TBD | Gap (PLANNED) |
| project-service | 8019 | TBD | TBD | None | TBD | Gap (PLANNED) |
| settings-service | 8020 | Partial | TBD | Partial (T-013) | TBD | Partial |
| compliance-service | 8021 | Yes (`canon/country-layer.md`) | TBD | Partial (WF-007) | Partial (`test_country_*.py`) | Partial |
| decision-service | 8022 | Yes (`canon/decision-system.md`) | TBD | Partial (T-012) | Partial (`test_decision*.py`) | Partial |
| bank-service | 8023 | Partial | TBD | None | Partial (`test_*_integration.py`) | Gap |
| whatsapp-service | 8024 | TBD | TBD | None | TBD | Gap |
| API Gateway | 8000 | Yes | Yes (`api-gateway/README.md`) | N/A (cross-cutting) | Yes (`test_api_gateway*.py`) | Good |

---

## COVERAGE BY CROSS-CUTTING CONCERN

| Concern | Existing Docs | New Governance Docs | Status |
|---------|---------------|---------------------|--------|
| Domain Model | `/backend/docs/canon/domain-model.md` | `docs/00_authority/DOMAIN_MODEL.md` | Good |
| Security/Auth | `/backend/docs/canon/security-model.md`, `capability-matrix.md` | `docs/07_governance/DECISION_ESCALATION_MATRIX.md` | Good |
| API Standards | `/backend/docs/canon/api-standards.md` | `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md` | Good |
| Event Catalog | `/backend/docs/canon/event-catalog.md` (143 events) | Referenced in `DOMAIN_MODEL.md` | Good |
| Workflow Catalog | `/backend/docs/canon/workflow-catalog.md` | `docs/00_authority/PRODUCT_WORKFLOWS.md` | Good |
| Data Architecture | `/backend/docs/canon/data-architecture.md` | Referenced in `ADR-001` | Good |
| Read Models | `/backend/docs/canon/read-model-catalog.md` | Not yet cross-referenced | Partial |
| Release Scope | `/backend/docs/canon/release-scope.md` | `docs/00_authority/FEATURE_SCOPE.md` | Good |
| Country Layer | `/backend/docs/canon/country-layer.md` | Referenced in `PROJECT_CHARTER.md`, `ADR-001` | Good |
| Deployment | `docker-compose.yml`, `/backend/deployment/README.md` | Not yet created (`05_deployment/`) | Gap |
| Frontend Architecture | None found | Not yet created (`02_frontend/`) | Gap |
| Testing Strategy | Implicit via test files; `.github/workflows/ci.yml` | Not yet created (`04_testing/`) | Gap |
| Governance/AI Operating Context | None pre-existing | `docs/07_governance/AI_OPERATING_CONTEXT.md` | Good (new) |
| ADRs | None pre-existing | `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` | Good (new) |

---

## PHASE 1 REQUIRED DOCUMENT STATUS

| Required Document | Path | Status |
|--------------------|------|--------|
| PROJECT_CHARTER.md | `docs/00_authority/` | CREATED |
| FEATURE_SCOPE.md | `docs/00_authority/` | CREATED |
| DOMAIN_MODEL.md | `docs/00_authority/` | CREATED |
| PRODUCT_WORKFLOWS.md | `docs/00_authority/` | CREATED |
| FULLSTACK_STITCHING_CONTRACT.md | `docs/00_authority/` | CREATED |
| AI_OPERATING_CONTEXT.md | `docs/07_governance/` | CREATED |
| DECISION_ESCALATION_MATRIX.md | `docs/07_governance/` | CREATED |
| ADR-001_PROJECT_FOUNDATION.md | `docs/06_decisions/` | CREATED |
| GOVERNANCE_IMPLEMENTATION_REPORT.md | `docs/08_reports/` | CREATED |
| DOCUMENTATION_COVERAGE_MATRIX.md | `docs/08_reports/` | CREATED (this document) |
| ARCHITECTURAL_GAP_REGISTER.md | `docs/08_reports/` | CREATED |
| RECOMMENDED_ADR_ROADMAP.md | `docs/08_reports/` | CREATED |

---

## EMPTY DIRECTORY STATUS (Created, Awaiting Phase 2+ Content)

| Directory | Purpose | Content Status |
|-----------|---------|-----------------|
| `docs/01_backend/` | Per-service backend documentation | Empty — populate in future phase |
| `docs/02_frontend/` | Frontend architecture documentation | Empty — populate in future phase |
| `docs/03_fullstack_contracts/` | Detailed per-feature contracts (beyond stitching summary) | Empty — populate in future phase |
| `docs/04_testing/` | Testing strategy and coverage reports | Empty — populate in future phase |
| `docs/05_deployment/` | Deployment runbooks, environment configs | Empty — populate in future phase |

These directories were created per the required structure but intentionally left without placeholder documents, since placeholder text does not count as completed documentation per the success criteria.
