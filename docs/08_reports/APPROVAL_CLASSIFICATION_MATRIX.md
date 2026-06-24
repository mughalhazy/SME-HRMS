# APPROVAL CLASSIFICATION MATRIX

Status: Complete
Created: 2026-06-16
Phase: Repository Determinability Review, Approval Elimination, and Pre-Frontend Go/No-Go

---

## PURPOSE

Classification matrix for every open item reviewed during this phase. Uses the mandate's classification taxonomy.

---

## CLASSIFICATION TAXONOMY

| Classification | Definition |
|---|---|
| Resolved By Evidence | Repository evidence conclusively determined the answer; item closed |
| Repository Hygiene | Safe structural cleanup; executed or queued for execution |
| Documentation Correction | Doc text corrected to match code reality |
| Authority Correction | Authority document updated with new confirmed facts |
| Configuration Clarification | Config file clarified without behavior change |
| Repository Determinable | Evidence determines the answer; execution deferred to owner |
| Owner Decision Required | Evidence exhausted; business/policy intent required |
| Security Policy Decision | Security model choice required |
| Product Policy Decision | Product behavior choice required |
| Architecture Decision | Architecture direction required |
| Runtime Decision | Runtime behavior choice required |
| Deployment Decision | Deployment strategy choice required |

---

## MATRIX

| ID | Item | Classification | Status |
|---|---|---|---|
| OA-001 | Dead function `_employee_domain_departments()` | Repository Hygiene | EXECUTED — deleted |
| OA-002 | OpenAPI title "Aura HRMS API" | Documentation Correction | EXECUTED — updated |
| OA-003 | Frontend at `backend/ui/` | Architecture Decision + Deployment Decision | OWNER DECISION |
| OA-004 | TS employee-service 43 files | Repository Determinable | DEFERRED — owner to execute |
| OA-005 | TS settings-service 6 files | Repository Determinable | DEFERRED — owner to execute |
| OA-006 | TS middleware 11 files | Repository Determinable | DEFERRED — owner to execute |
| OA-007 (build.yml) | Docker image build jobs | Repository Hygiene | DEFERRED — owner to migrate to root CI |
| OA-007 (deploy.yml) | Deploy validation workflow | Deployment Decision | OWNER DECISION |
| OA-007 (test.yml) | Unittest + compose config | Repository Hygiene | DEFERRED — merge unique steps to root CI |
| OA-008 | `attendance_service` naming conflict | Resolved By Evidence (no conflict) | CLOSED |
| OA-009 | `(C) Phoenix LiteOS.lnk` | Repository Hygiene | EXECUTED — deleted |
| OA-010 | Root .gitignore + README | Repository Hygiene | EXECUTED — created |
| TO-001 | /health /ready registration | Resolved By Evidence | CLOSED — documented |
| TO-002 | CircuitBreaker domain usage | Resolved By Evidence | CLOSED — documented |
| TO-003 | outbox_system.py purpose | Resolved By Evidence | CLOSED — documented |
| TO-004 | 007_event_outbox.sql path | Resolved By Evidence | CLOSED — documented |
| TO-005 | Cross-service dependency map | Resolved By Evidence (partial) | PARTIAL — non-blocking |
| UC-001 | outbox_system.py | Resolved By Evidence | CLOSED (same as TO-003) |
| UC-002 | Migration file path | Resolved By Evidence | CLOSED (same as TO-004) |
| UC-003 | CircuitBreaker | Resolved By Evidence | CLOSED (same as TO-002) |
| UC-004 | /health /ready | Resolved By Evidence | CLOSED (same as TO-001) |
| UC-005 | Cross-service deps | Resolved By Evidence (partial) | PARTIAL (same as TO-005) |
| UC-006 | employee_api.py endpoints | Resolved By Evidence | CLOSED — 14 routes documented |
| UC-007 | TS test references | Resolved By Reclassification | CLOSED — no cross-lang import |
| ARG-003 | Country resolver bootstrap | Authority Correction | EXECUTED — §12.4 corrected |
| NF-001 | ARG-003 doc error | Documentation Correction | EXECUTED |
| NF-002 | Two outbox implementations | Authority Correction | EXECUTED — §11 updated |
| NF-003 | Face recognition attendance | Resolved By Evidence | NOTED — Phase 3 awareness |
| NF-004 | event_contract.py undocumented | Authority Correction (future) | NON-BLOCKING |

---

## CLASSIFICATION COUNTS

| Classification | Count |
|---|---|
| Resolved By Evidence | 8 |
| Repository Hygiene (executed) | 5 |
| Documentation Correction (executed) | 2 |
| Authority Correction (executed) | 3 |
| Repository Determinable (deferred to owner) | 4 |
| Architecture + Deployment Decision | 1 |
| Deployment Decision | 1 |
| Partial resolution | 2 |
| **Total** | **26** |
