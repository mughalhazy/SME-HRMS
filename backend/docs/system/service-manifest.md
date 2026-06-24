# Service Manifest

Per **SPEC §10 + §20**: all services must be enumerated with runtime status, scope, country support, and owner domain.

> **Rule:** A service marked `implemented` must have a real code file, a docker-compose entry or runnable entrypoint, and at minimum one test or QC script covering it. `planned` services must be clearly labelled and not over-claimed in the README.

---

## Mandatory Services (Core)

| Service | Runtime Status | Code File | Scope | Country Support | Owner Domain |
|---|---|---|---|---|---|
| employee-service | implemented | `services/employee-service/` (TypeScript) | core | country-agnostic | Employee Core (C01) |
| payroll-service | implemented | `payroll_service.py` | core | country-agnostic via adapter | Payroll Core (C03) |
| compliance-service | implemented | `services/compliance_service.py` + `compliance_api.py` | core | country-agnostic via adapter | Compliance Core (C04) |
| attendance-service | implemented | `attendance_service/service.py` | core | country-agnostic | Attendance Core (C05) |
| bank-service | implemented | `bank_service.py` + `banking_api.py` | core | country-agnostic | Disbursement Core (C07) |
| decision-service | implemented | `services/decision_engine.py` + `decision_api.py` | core | country-agnostic | Decision Core (C08) |
| employee-access-service | implemented | `services/mobile_gateway.py` + `whatsapp_service.py` | core | country-agnostic | Employee Access Core (C09) |

---

## Support Services

| Service | Runtime Status | Code File | Scope | Country Support | Owner Domain |
|---|---|---|---|---|---|
| automation-service | implemented | `supervisor_engine.py` + `automation_api.py` | support | country-agnostic | Automation / Supervisor |
| notification-service | implemented | `notification_service.py` | support | country-agnostic | Notifications |
| audit-service | implemented | `audit_service/service.py` | support | country-agnostic | Audit (Security Canon §19) |
| auth-service | implemented | `services/auth-service/service.py` (Python) | support | country-agnostic | Auth / RBAC |
| outbox-system | implemented | `outbox_system.py` | support | country-agnostic | At-least-once delivery |
| error-registry | implemented | `error_registry.py` | support | country-agnostic | Error classification (SB-G03) |
| workflow-service | implemented | `workflow_service.py` (per `docs/services/workflow-service.md`) | support | country-agnostic | Centralized Approval Orchestration |

---

## Optional / Add-On Services

| Service | Runtime Status | Code File | Scope | Country Support | Owner Domain |
|---|---|---|---|---|---|
| helpdesk-service | implemented | `helpdesk_api.py` | add-on (A01) | country-agnostic | HR Service Delivery |
| expense-service | implemented | `expense_api.py` | add-on (A02) | country-agnostic | Expenses |
| ewa-financial-service | implemented | `services/finance/ewa.py` | add-on (A03) | country-agnostic | Financial Wellness |
| performance-service | implemented | `services/performance/` | add-on (A04) | country-agnostic | Performance |
| hiring-service | implemented | `hiring_service.py` | add-on (A05) | country-agnostic | Recruitment |
| engagement-service | implemented | `services/engagement/` + `engagement_api.py` | add-on (A06) | country-agnostic | Engagement |
| analytics-service | implemented | `services/analytics/predictive.py` + `reporting_analytics_api.py` | add-on (A07) | country-agnostic | Predictive Insights |
| whatsapp-access-service | implemented | `whatsapp_service.py` + `whatsapp_api.py` | add-on | country-agnostic | WhatsApp Channel (SPEC §17) |

> **Naming note (OIG-2/OIG-9):** `analytics-service` is the name used in this manifest (SPEC §20 compliance artifact). The canonical names used in `docs/canon/service-map.md` and `MASTER BUILD SPEC.md §10` are `reporting-analytics-service` (for analytics) and `whatsapp-service` (for WhatsApp channel). `employee-access-service` in the Mandatory Core table above maps to `mobile_gateway.py` + `whatsapp_service.py` and has no equivalent in service-map.md. These naming variants reflect the session-6 artifact state. Service-map.md is the canonical service inventory.
| leave-service | implemented | `leave_service.py` | core | country-agnostic | Leave Core (C06) |
| cost-planning-service | implemented | `services/cost_planning_service.py` | add-on | country-agnostic | Cost Planning |
| governance-service | implemented | `services/governance/service.py` | support | country-agnostic | Human-in-loop Gates |
| experience-layer | implemented | `services/product/experience.py` | add-on | country-agnostic | PaaS / Tier gating |
| integration-service | implemented | `integration_service.py` + `integration_api.py` | add-on | country-agnostic | Outbound Webhooks / Connector Dispatch |
| search-service | implemented | `search_service.py` + `search_api.py` | add-on | country-agnostic | Cross-Domain Search |
| settings-service | implemented | `services/settings-service/` (per `docs/services/settings-service.md`) | add-on | country-agnostic | HR Policy Configuration |

> **B-category fix (2026-06-13):** `integration-service`, `search-service`, and `settings-service` each have a full entry in `docs/services/*.md` and `docs/canon/service-map.md` but were absent from this manifest — added above (extension, mirroring existing row format). `workflow-service` added to Support Services below; `travel-service` and `project-service` added to Planned Services below with a status-divergence note (see those sections).

---

## Country Adapters

| Adapter | Runtime Status | Code Path | Scope | Country | Owner Domain |
|---|---|---|---|---|---|
| Pakistan adapter | implemented | `country/pakistan/` | core | Pakistan (PK) | SPEC §11 |
| Dummy adapter | implemented | `country/dummy/` | architecture proof | — | S7-G02 — proves any country plugs in without service changes |

---

## Planned Services (not yet built)

| Service | Status | Blocks | Notes |
|---|---|---|---|
| Export sector compliance | planned | MN-G07 | Needs SA8000/WRAP/BSCI domain research |
| travel-service | planned per `canon/release-scope.md` | — | **NOTE (B-category, 2026-06-13):** `docs/services/travel-service.md` describes `travel_service.py` + `travel_api.py` as "fully implemented and importable (per gap S8-G04; BUILD SPEC §10 corrected)" — a status divergence vs. this manifest/`release-scope.md`'s "Planned — No runtime code." Not resolved here per [[feedback_divergence_resolution]]; flagged for a future canon-vs-code verification pass. |
| project-service | planned per `canon/release-scope.md` | — | Has a full entry in `docs/services/project-service.md` and `docs/canon/service-map.md` (10 endpoints, `/api/v1/projects`); release-scope.md lists it as "Domain build — staffing, allocation" with no runtime code. Added here for manifest completeness (B-category, 2026-06-13). |

---

## Service Status Definitions

Per SPEC §10:
- `implemented` — code exists, runnable, has at minimum one test or QC check
- `add-on` — optional capability, plugs into core without changing core behavior
- `planned` — designed/documented but not yet implemented
- `deprecated` — removed or being phased out (none currently)

---

*Last updated: 2026-04-13 (Session 6 — HRMS SPEC.md overlay, SPEC-G08)*
