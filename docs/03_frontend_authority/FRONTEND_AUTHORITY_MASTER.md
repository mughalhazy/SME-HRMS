# FRONTEND AUTHORITY MASTER

Status: Complete
Created: 2026-06-17
Phase: 3 — Frontend Authority Capture
Mandate: `# PHASE 3 — FRONTEND AUTHORITY CAPTURE.md`

---

## PURPOSE

This document is the governing index for all Phase 3 Frontend Authority outputs. Every frontend element defined in this phase is derived exclusively from verified backend reality, confirmed API contracts, resolved architectural decisions, and product authority documents. No frontend functionality is invented here.

**Principle:** If it is not in a backend service, a confirmed gateway route, a defined workflow, a confirmed role, or an authorized product decision, it does not appear in the frontend authority model.

---

## SOURCE AUTHORITY DOCUMENTS

All frontend authority derives from these verified sources:

| Source | Path | What It Provides |
|--------|------|-----------------|
| PROJECT_CHARTER | `docs/00_authority/PROJECT_CHARTER.md` | User types, product identity, constraints |
| FEATURE_SCOPE | `docs/00_authority/FEATURE_SCOPE.md` | 16 IMPLEMENTED + 6 ADD-ON + 2 PLANNED features |
| DOMAIN_MODEL | `docs/00_authority/DOMAIN_MODEL.md` | All entities, fields, lifecycles |
| PRODUCT_WORKFLOWS | `docs/00_authority/PRODUCT_WORKFLOWS.md` | WF-001 through WF-008 |
| FULLSTACK_STITCHING_CONTRACT | `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md` | T-001 to T-015 traces |
| API_CONTRACT | `docs/01_backend/API_CONTRACT.md` | 25 gateway routes, endpoint catalogue, auth contract |
| Security Model | `backend/docs/canon/security-model.md` | 30 capabilities, 6 roles, scope model |
| Archetype System | `design/hrms-archetype-system-v1.md` | H01–H13, 48 pages, layout + slots |
| PRODUCT_DECISION_REGISTER | `docs/08_reports/PRODUCT_DECISION_REGISTER.md` | 21 confirmed routes, all decisions STABLE |
| RESIDUAL_DECISION_COLLAPSE_REPORT | `docs/08_reports/RESIDUAL_DECISION_COLLAPSE_REPORT.md` | All prior TBDs collapsed |
| POST_COLLAPSE_FRONTEND_READINESS | `docs/08_reports/POST_COLLAPSE_FRONTEND_READINESS.md` | GO issued, all gates passed |

---

## FRONTEND APPLICATION LOCATION

**Path:** `backend/ui/`
**Framework:** Next.js 15, App Router, TypeScript, Tailwind CSS, TanStack React Query
**API Base URL (dev):** `http://localhost:8000`
**Port (dev):** 3000
**Condition C-003:** Frontend lives at `backend/ui/` by authorized decision (Phase 2.95 OCR-001). Relocation to repo-root `frontend/` is post-Phase 3.

---

## SCOPE OF THIS PHASE

**Phase 3 builds authority for:**
- 16 IMPLEMENTED core features (F-001 through F-016)
- 6 ADD-ON features (F-017 through F-022) — authority defined but implementation deferred
- Full navigation, permission, workflow, screen, and API dependency model

**Phase 3 does NOT cover:**
- F-023 Travel Management (PLANNED — service scaffolded only)
- F-024 Project Management (PLANNED — service scaffolded only)
- Document Management (confirmed OUT OF SCOPE)
- LMS (confirmed OUT OF SCOPE)
- Native mobile app (FUTURE SCOPE)
- Shift/Roster scheduling (confirmed OUT OF SCOPE)
- Any new functionality not present in backend

---

## KEY FACTS FOR FRONTEND IMPLEMENTATION

| Fact | Value |
|------|-------|
| API gateway port (dev) | 8000 |
| Frontend port (dev) | 3000 |
| Authentication | JWT HS256, Bearer token |
| Auth-exempt routes | `/api/v1/auth/*`, `/health`, `/ready`, `/metrics` |
| JWT claims forwarded | X-User-Id, X-User-Role, X-Tenant-Id |
| Standard response envelope | `{status, data, meta, error}` — 21 services |
| Non-standard envelope | `{status, data, service}` — 4 services: compliance, decision, banking, whatsapp |
| Rate limit | 200 req/min per IP |
| Roles | Admin, PayrollAdmin, Manager, Recruiter, Employee |
| RBAC-restricted routes | payroll (Admin/PayrollAdmin/Manager), audit (Admin), hiring (Admin/Manager/Recruiter), reporting (Admin/Manager) |
| UI archetypes | H01–H13 (13 archetypes, 48 pages) |
| Wireframes location | `frontend/pages/` and `frontend/seeds/` |
| Total gateway routes | 25 confirmed |

---

## FRONTEND AUTHORITY DOCUMENT INDEX

| Document | Description |
|----------|-------------|
| [FRONTEND_ROUTE_CATALOG.md](FRONTEND_ROUTE_CATALOG.md) | All frontend routes with roles, APIs, actions, blocking conditions |
| [FRONTEND_SCREEN_CATALOG.md](FRONTEND_SCREEN_CATALOG.md) | All 48 screens — purpose, permissions, API dependencies, states |
| [FRONTEND_DASHBOARD_CATALOG.md](FRONTEND_DASHBOARD_CATALOG.md) | 4 dashboard variants by role — widgets, KPIs, data sources |
| [FRONTEND_NAVIGATION_MODEL.md](FRONTEND_NAVIGATION_MODEL.md) | Role-based navigation structure and sidebar composition |
| [FRONTEND_ROLE_EXPERIENCE_MATRIX.md](FRONTEND_ROLE_EXPERIENCE_MATRIX.md) | Per-role experience: screens, actions, journeys |
| [FRONTEND_PERMISSION_MATRIX.md](FRONTEND_PERMISSION_MATRIX.md) | All 30 capabilities mapped to UI visibility and behavior |
| [FRONTEND_WORKFLOW_TO_SCREEN_MAP.md](FRONTEND_WORKFLOW_TO_SCREEN_MAP.md) | WF-001 to WF-008 mapped to UI screens and actions |
| [FRONTEND_API_DEPENDENCY_MAP.md](FRONTEND_API_DEPENDENCY_MAP.md) | Every API endpoint mapped to its UI consumer |
| [FRONTEND_COMPONENT_INVENTORY.md](FRONTEND_COMPONENT_INVENTORY.md) | Required UI components derived from archetype system |
| [FRONTEND_GAP_REGISTER.md](FRONTEND_GAP_REGISTER.md) | Gaps between backend reality and complete frontend traceability |
| [FRONTEND_AUTHORITY_READINESS_REPORT.md](FRONTEND_AUTHORITY_READINESS_REPORT.md) | Final readiness assessment and Phase 3 sign-off |

---

## ARCHITECTURAL DECISIONS CARRIED INTO PHASE 3

| Decision | Impact on Frontend |
|---------|-------------------|
| API Gateway as single entry point | ALL API calls go through `localhost:8000` — never direct to services |
| JWT HS256, Bearer token | Auth header on every non-exempt request; store token in httpOnly cookie or memory |
| Non-standard envelope (4 services) | Compliance, decision, banking, whatsapp response handler must check for missing `meta` |
| Settings non-persistence | Settings component must not cache; treat as volatile |
| Employee service serves roles and departments | `/api/v1/roles` and `/api/v1/departments` go to employee-service via gateway |
| Banking/WhatsApp are backend integrations | No standalone frontend banking or WhatsApp screens; interactions surface through payroll and notifications |
| Decision Cards are in-memory | `/decisions` list may be empty between service restarts in dev |
| Workflow status uses lowercase | `pending`, `completed`, `approved`, `rejected` — NOT PascalCase |
| `tenant_id` in JWT | Extract from JWT, propagate as X-Tenant-Id; never hardcode or allow cross-tenant data |

---

## PHASE STATUS

This document and all child documents in `docs/03_frontend_authority/` constitute the complete Phase 3 output.

**Phase 3 completes the pre-implementation authority model. Frontend implementation (Phase 4) may begin after owner review of Phase 3 outputs.**
