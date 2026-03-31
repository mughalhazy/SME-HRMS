# Intent ↔ Build Alignment (P1–P51)

This document aligns prompt intent (P1–P51) to the current repository implementation surfaces (modules, APIs, DB schema, tests, docs) and classifies each prompt as **COMPLETE**, **PARTIAL**, **MISSING**, or **ORPHAN**.

## Classification rules used

- **COMPLETE**: module + API + DB (or explicitly stateless design) + tests + docs are all present and wired.
- **PARTIAL**: implementation exists but one or more of API exposure, gateway wiring, deployment wiring, DB migration, tests, or docs is missing/incomplete.
- **MISSING**: prompt intent not found in codebase artifacts.
- **ORPHAN**: code/build artifact exists but no clear prompt-intent mapping in P1–P51 evidence set.

## A) Alignment Matrix

| Prompt | Module / Service | API endpoint(s) | DB model / migration | Test coverage | Status |
|---|---|---|---|---|---|
| P1 | employee domain foundation (`employee` logic spread across domain tests and APIs) | `/api/v1/employees`, `/api/v1/departments` | `001_core_schema.sql` (`employees`, `departments`) | `tests/test_employee_service_domain.py`, `tests/test_employee_ui.py` | COMPLETE |
| P2 | role/organization model (`roles`) | `/api/v1/roles` (via employee-service route family) | `001_core_schema.sql` (`roles`) | `tests/test_role_domain.py` | COMPLETE |
| P3 | attendance service (`attendance_service/*`) | `/api/v1/attendance/*` | `002_workflow_schema.sql` (`attendance_records`) + `004_persistence_normalization.sql` ext | `tests/test_attendance_service.py`, `tests/test_attendance_ui.py` | COMPLETE |
| P4 | leave service (`leave_service.py`, `leave_api.py`) | `/api/v1/leave/requests*` | `002_workflow_schema.sql` (`leave_requests`) | `tests/test_leave_service.py`, `tests/test_leave_api.py` | COMPLETE |
| P5 | payroll service (`payroll_service.py`, `payroll_api.py`) | `/api/v1/payroll/*` | `002_workflow_schema.sql` (`payroll_records`) | `tests/test_payroll_api.py`, `tests/test_payroll_ui.py`, `test_payroll_service.py` | COMPLETE |
| P6 | hiring foundation (`hiring-service` module set) | `/api/v1/hiring/*` | `002_workflow_schema.sql` (`job_postings`, `candidates`, `candidate_stage_transitions`) | `tests/test_hiring_service.py`, `tests/test_hiring_api.py` | COMPLETE |
| P7 | centralized workflow engine (`workflow_service.py`, `workflow_api.py`) | `/api/v1/workflows/*` | `003_centralized_workflow_engine.sql` | `tests/test_workflow_engine.py`, `tests/test_workflow_contract.py` | PARTIAL (not deployed in compose) |
| P8 | API contract normalization (`api_contract.py`) | shared envelope for `/api/v1/*` | N/A (contract layer) | gateway + API tests using envelope assertions | COMPLETE |
| P9 | event contract normalization (`event_contract.py`) | event payload contract (D2) | `007_event_outbox.sql` / outbox persistence linkage | `tests/test_outbox_system.py`, `tests/test_backward_compatibility_enforcement.py` | COMPLETE |
| P10 | workflow payload contract (`workflow_contract.py`) | workflow request/response contract | `003_centralized_workflow_engine.sql` | `tests/test_workflow_contract.py` | COMPLETE |
| P11 | tenant foundation (`tenant_support.py`, gateway tenant middleware) | tenant-scoped `/api/v1/*` | `005_tenant_foundation.sql` | `tests/test_gateway_tenant_context.py`, `tests/test_security_compliance_lock.py` | COMPLETE |
| P12 | audit service (`audit_service/*`) | `/api/v1/audit/*` | `009_audit_service.sql` (`audit_records`) | `tests/test_audit_service.py`, `tests/test_security_logging.py` | PARTIAL (service not deployed in compose) |
| P13 | auth service (`auth` models in migrations + service API surface) | `/api/v1/auth/*` | `004_persistence_normalization.sql` (`user_accounts`, `role_bindings`, `permission_policies`, `sessions`, `refresh_tokens`) | `tests/test_auth_service.py` | COMPLETE |
| P14 | notification service (`notification_service.py`, `notification_api.py`) | `/api/v1/notifications/*` | `006_notification_service.sql` | `tests/test_notification_service.py` | COMPLETE |
| P15 | background job system (`background_jobs.py`, `background_jobs_api.py`) | `/api/v1/jobs/*` (gateway-local job route) | `008_background_jobs_schema.sql` (`background_jobs`, failures) | `tests/test_background_jobs.py`, `tests/test_gateway_load_control.py` | PARTIAL (compose wiring is indirect/in-process) |
| P16 | outbox system (`outbox_system.py`, `event_outbox.py`) | internal dispatch APIs/events | `007_event_outbox.sql` + `008_background_jobs_schema.sql` (`event_outbox`) | `tests/test_outbox_system.py` | COMPLETE |
| P17 | supervisor / healing (`supervisor_engine.py`) | internal control-plane hooks | N/A (state from workflows/jobs/outbox) | `tests/test_supervisor_engine.py`, `tests/test_failure_resilience.py` | COMPLETE |
| P18 | resilience hardening (`resilience.py`, chaos modules) | middleware/gateway controls | N/A | `tests/test_failure_resilience.py`, `tests/test_chaos_engine.py`, `tests/test_chaos_resilience_hardening.py` | COMPLETE |
| P19 | gateway load control (`api-gateway/load_control.py`) | gateway throttling for `/api/v1/*` | N/A | `tests/test_gateway_load_control.py` | COMPLETE |
| P20 | gateway route registry (`api-gateway/routes.py`) | canonical + legacy route resolution | N/A | `tests/test_api_gateway_routes.py`, `tests/test_backward_compatibility_enforcement.py` | COMPLETE |
| P21 | integration service (`integration_service.py`, `integration_api.py`) | `/api/v1/integrations/*` | **No dedicated migration file found for integration tables** | `tests/test_integration_service.py` | PARTIAL |
| P22 | search service (`search_service.py`, `search_api.py`) | `/api/v1/search*` (service-local) | **No search schema migration found** | `tests/test_search_service.py` | PARTIAL |
| P23 | reporting analytics (`reporting_analytics.py`, API) | `/api/v1/reporting/*` | projection/read-model only; no dedicated migration | `tests/test_reporting_analytics.py` | PARTIAL |
| P24 | performance service (`performance_service.py`, `performance_api.py`) | `/api/v1/performance/*` | **No performance migration in `deployment/migrations`** | `tests/test_performance_domain.py`, `tests/test_performance_layer_qc.py` | PARTIAL |
| P25 | engagement service (`engagement_service.py`, `engagement_api.py`) | `/api/v1/engagement/*` | `010_engagement_service.sql` | `tests/test_engagement_service.py` | PARTIAL (not in gateway route registry) |
| P26 | payroll-attendance-leave integration slice | `/api/v1/payroll/run` etc | relies on `002_workflow_schema.sql` entities | `tests/test_payroll_compensation_integration.py` | COMPLETE |
| P27 | QC baseline automation (`deployment/qc_validate*.py`) | N/A | validates migrations and deployment artifacts | `tests/test_data_integrity.py`, domain RE-QC tests | COMPLETE |
| P28 | backward compatibility pass | gateway aliases + payload compatibility | N/A (compatibility layer) | `tests/test_backward_compatibility_enforcement.py` | COMPLETE |
| P29 | data integrity pass | cross-domain integrity validators | migration coverage assertions | `tests/test_data_integrity.py`, `deployment/re_qc_validate_data_integrity.py` | COMPLETE |
| P30 | event reliability pass | outbox/replay stability | outbox tables (`007_event_outbox.sql`, `008_background_jobs_schema.sql`) | `tests/test_outbox_system.py`, resilience tests | COMPLETE |
| P31 | workflow integrity pass | centralized workflow transitions | workflow migrations (`003_centralized_workflow_engine.sql`) | `tests/test_workflow_engine.py` | COMPLETE |
| P32 | final convergence pass | supervisor/workflow/QC validator alignment | N/A | `tests/test_supervisor_engine.py`, QC scripts | COMPLETE |
| P33 | final certification pass | release-gate certification | N/A | `tests/test_master_certification.py` + full pytest/QC evidence docs | COMPLETE |
| P34 | project management domain (`project_service.py`) | project API not gateway-registered | **No migration found** | `tests/test_project_service.py` | PARTIAL |
| P35 | expense management (`expense_service.py`, `expense_api.py`) | expense endpoints service-local | **No migration found** | `tests/test_expense_service.py` | PARTIAL |
| P36 | helpdesk domain (`helpdesk_service.py`, `helpdesk_api.py`) | helpdesk endpoints service-local | **No migration found** | `tests/test_helpdesk_service.py`, `tests/test_helpdesk_api.py` | PARTIAL |
| P37 | travel domain (`travel_service.py`, `travel_api.py`) | `/api/v1/travel/*` | **No travel migration in current migrations directory** | `tests/test_travel_domain.py`, `tests/test_travel_api.py` | PARTIAL |
| P38 | automation domain (`automation_service.py`, `automation_api.py`) | `/api/v1/automations/*` | **No migration found** | `tests/test_automation_service.py` | PARTIAL |
| P39 | asset management extension | API/module inferred from tests only | **No module/migration found** | `tests/test_asset_management_service.py` | MISSING |
| P40 | learning extension | API/module inferred from tests only | **No module/migration found** | `tests/test_learning_service.py` | MISSING |
| P41 | document compliance extension | API/module inferred from tests only | **No module/migration found** | `tests/test_document_compliance_service.py` | MISSING |
| P42 | contractor management extension | API/module inferred from tests only | **No module/migration found** | `tests/test_contractor_management_domain.py` | MISSING |
| P43 | compensation extension | API/module inferred from tests only | **No module/migration found** | `tests/test_compensation_domain.py` | MISSING |
| P44 | settings-service implementation (`services/settings-service/*.ts`) | canonical `/api/v1/settings*` in docs; gateway route absent | **No explicit SQL migration for settings tables** | `tests/test_settings_domain.py`, `deployment/qc_validate_settings.py` | PARTIAL |
| P45 | dashboard UI expansion (`api-gateway/dashboard_ui.py`, ui pages) | UI/aggregated dashboard endpoints | N/A | `tests/test_dashboard_ui.py` | PARTIAL |
| P46 | employee/payroll UI hardening (`employee_ui.py`, `payroll_ui.py`) | UI-facing APIs | N/A | `tests/test_employee_ui.py`, `tests/test_payroll_ui.py` | PARTIAL |
| P47 | middleware hardening (`middleware/*.ts`) | request id, validation, rate limits, audit hooks | N/A | indirect via gateway/security tests | PARTIAL (TS middleware not clearly wired in Python gateway) |
| P48 | security compliance lock | tenant + audit + auth enforcement | tenant/auth/audit migrations | `tests/test_security_compliance_lock.py`, `tests/test_security_logging.py` | COMPLETE |
| P49 | add-on pre-convergence bundle (cross-domain) | mixed endpoints across add-ons | mixed/no unified migration set | `tests/test_addon_convergence.py` | PARTIAL |
| P50 | add-on convergence QC (`addon_convergence.py`) | convergence gate | N/A | `tests/test_addon_convergence.py`, `deployment/re_qc_validate_addon_convergence.py` | COMPLETE |
| P51 | master certification QC (`master_certification.py`) | certification gate | N/A | `tests/test_master_certification.py`, `deployment/re_qc_validate_master_certification.py` | COMPLETE |

## B) Gap Report

### Missing builds

1. **Prompt-intended domains with tests but no build modules/migrations**
   - P39 Asset Management
   - P40 Learning
   - P41 Document Compliance
   - P42 Contractor Management
   - P43 Compensation

2. **Prompt artifacts inferred by tests only**
   - These prompts have strong test intent but no corresponding runtime service module in repo root or `services/` except settings.

### Incomplete builds

1. **Implemented but not fully exposed/wired**
   - P25 Engagement is implemented + migrated, but not present in API gateway route registry.
   - P44 Settings has TS service implementation + docs/tests but no gateway route wiring and no explicit SQL migration.
   - P24 Performance is implemented and tested, but no dedicated schema migration in `deployment/migrations`.

2. **Implemented but deployment coverage gaps**
   - P7 Workflow and P12 Audit are route-addressable in gateway map, but service deployment list in `docker-compose.yml`/`docs/deployment.md` omits these services.
   - P21/P22/P23/P34/P35/P36/P37/P38 exist as modules/tests but are not declared in compose runtime.

3. **Doc/build divergence**
   - Canonical service map includes settings/integration/travel as first-class services, but deployment docs list only a subset.
   - `docs/services/*` coverage exists for hiring/project/settings/workflow only; many active modules have no service-level docs.

### Overbuilt / unmapped components (ORPHAN)

1. **Middleware TS layer (`middleware/*.ts`)**
   - Rich middleware implementation exists, but primary gateway runtime in this repo is Python-based; wiring path is unclear.
2. **Settings TS service (`services/settings-service/*`)**
   - Strong implementation footprint in TS, but deployment path in compose is absent and gateway lacks route registration.

## C) System Risks

### Deployment gaps

- **High risk**: service-map/gateway references exceed deployed services, creating environment-specific 404/502 drift.
- **High risk**: workflow/audit/integration/travel/performance and add-on domains may pass unit tests yet fail in integrated compose runtime.

### Gateway mismatches

- **High risk**: `/api/v1/engagement` and `/api/v1/settings` are canonical capabilities but absent from `api-gateway/routes.py`.
- **Medium risk**: route registry includes upstream names without corresponding compose services, causing unresolved upstream targets.

### Migration risks

- **High risk**: several domain modules (performance/travel/integration/add-ons) have no explicit schema migration coverage.
- **Medium risk**: mixed persistence style (SQL-backed + in-memory/implicit stores) can produce non-deterministic behavior across environments.

## D) Priority Fix List (ordered to reach 100% alignment)

1. **Create/confirm authoritative prompt-to-capability manifest for P1–P51** (single source of truth linking prompt intent to modules/APIs/tests/docs).
2. **Close gateway exposure gaps**: add canonical route entries for engagement and settings (and any additional implemented domains).
3. **Close deployment gaps**: align `docker-compose.yml` and `docs/deployment.md` with gateway/service-map reality (or prune unused gateway routes).
4. **Close schema gaps**: add migrations for performance, integration, travel, settings, and add-on domains where persistent state is expected.
5. **Reconcile test-only prompts P39–P43**: either implement missing services or formally de-scope/remove tests and prompts from active scope.
6. **Resolve TS/Python runtime split**: explicitly declare whether middleware/settings TS stack is production path; wire or retire orphan code.
7. **Expand service docs coverage** so every deployed service has a matching `docs/services/*` page and endpoint inventory.
8. **Add alignment CI gate** that verifies prompt manifest ↔ routes ↔ compose services ↔ migrations ↔ tests are all in sync.
9. **Run full regression + RE-QC after alignment changes** and publish evidence in this document as an update appendix.

## V1 ↔ V2 Continuity Findings

### Features present in V1 but degraded in V2

- Legacy compatibility requirements remain documented (legacy route aliases, list alias shape, event-name mapping), but growth in new domains has outpaced uniform gateway/deployment wiring.
- Early canonical guarantees (single deployed service map) appear degraded by partial add-on domain introduction.

### Features extended in V2 but not fully wired

- Add-on domain wave (project/expense/helpdesk/travel/automation/settings and test-only domains) shows significant implementation extension but inconsistent migration, gateway, and deployment completion.
- Canonical docs evolved to include broader service map, but runtime deployment list did not keep pace.

---

**Current overall alignment score (qualitative):** **PARTIAL**.

The core P1–P33 backbone is largely coherent and evidenced, while P34–P49 add-on expansion introduces most of the present alignment debt.
