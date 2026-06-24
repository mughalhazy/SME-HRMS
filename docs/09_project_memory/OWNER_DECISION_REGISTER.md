# OWNER-DECISION REGISTER

Layer: Project Memory
Status: Active
Created: 2026-06-18
Rule: Items in this register can only be resolved by the owner. Do not synthesize answers from repository evidence. Do not apply safe defaults. Await owner decision.

---

## Classification Criteria

An item qualifies as OWNER-DECISION only if:
- Repository cannot answer
- Architecture cannot answer
- Documentation cannot answer
- Decision affects product behaviour
- No credential provisioning is required (those go to EXTERNAL_DEPENDENCY_REGISTER.md)

---

## §1 — COMMERCIAL LAUNCH DATE (OD-001)

**Item ID:** OD-001
**Title:** Commercial Launch Date and Go-Live Timeline
**Classification:** OWNER-DECISION
**Current Status:** OPEN — awaiting owner decision
**Original Source:** Phase 3 gap analysis; governance capture
**Evidence Source:** FEATURE_SCOPE.md (lists LIVE/PLANNED/ADD-ON statuses but no launch date); PROJECT_CHARTER.md (no date specified); no deployment configuration sets a launch date
**Resolution Source:** N/A — not resolvable from repository
**Resolution Date:** NOT YET RESOLVED
**Resolved By:** N/A
**Decision Summary:** The owner must decide when to launch commercially. This determines sprint planning, beta testing period, external onboarding lead times for ED-001 through ED-005.
**Detailed Explanation:** Repository contains no launch date. FEATURE_SCOPE.md specifies LIVE/PLANNED/ADD-ON classifications but these are feature-completeness categories, not launch dates. A commercial launch date is required to: (1) plan external credential provisioning timeline (FBR registration can take weeks; Raast onboarding varies by bank partner), (2) set a hard deadline for LIVE features, (3) schedule beta/staging environment setup, (4) coordinate QA sign-off.
**Affected Components:** All LIVE features; all external integrations (ED-001 to ED-005)
**Affected Routes:** All production routes
**Affected APIs:** All
**Affected Workflows:** All 7 primary workflows
**Affected Roles:** All roles
**Owner Required:** YES — product/business decision
**External Dependency:** NO (but OD-001 governs timeline for ED-001 to ED-005 provisioning)
**Future Impact:** HIGH — all Phase 4 sprint planning depends on this
**Reopen Criteria:** N/A — this item IS open; closes when owner specifies a launch date
**Related Documents:** `docs/00_authority/FEATURE_SCOPE.md`; `docs/00_authority/PROJECT_CHARTER.md`
**Related Register Entries:** ED-001 (FBR); ED-002 (EOBI); ED-003 (PESSI); ED-004 (Raast); ED-005 (WhatsApp)

---

## §2 — SCALING STRATEGY (OD-002)

**Item ID:** OD-002
**Title:** Scaling Strategy Beyond Docker Compose (Multi-Replica / Kubernetes)
**Classification:** OWNER-DECISION
**Current Status:** OPEN — awaiting owner decision
**Original Source:** OAQ-001 (AI_OPERATING_CONTEXT.md); Mandate 2 OWNER-REQUIRED compression
**Evidence Source:** `backend/docker-compose.yml` (single-replica Docker Compose deployment confirmed); no Kubernetes or Helm configuration found; no container registry configured
**Resolution Source:** N/A — not resolvable from repository
**Resolution Date:** NOT YET RESOLVED
**Resolved By:** N/A
**Decision Summary:** Owner must decide the scaling strategy. Current infrastructure: single Docker Compose. Options include: (1) remain on Docker Compose with vertical scaling, (2) migrate to Kubernetes, (3) deploy to managed container service (ECS, Cloud Run). This decision affects rate-limiter state sharing (SD-033), session storage, and the need for a Redis cache layer.
**Detailed Explanation:** Rate limiter at `backend/docker/rate_limiting.py` uses an in-process dict (`_buckets`). In multi-replica deployment, each replica has independent state — per-instance rate limiting, not per-user across all replicas. If multi-replica is required, rate limiter must be migrated to Redis or equivalent shared state. Similarly, settings service in-memory stub (C-002) would behave inconsistently across replicas. No Kubernetes YAML, no Helm chart, no cloud provider configuration exists in the repository.
**Affected Components:** API Gateway (rate limiting); settings-service; all stateful in-process components
**Affected Routes:** All routes (rate limiting)
**Affected APIs:** All
**Affected Workflows:** None directly
**Affected Roles:** All roles
**Owner Required:** YES — infrastructure/product strategy decision
**External Dependency:** NO (but scaling may require cloud provider contracts)
**Future Impact:** HIGH — if multi-replica, SD-033 must be reopened and rate limiter redesigned
**Reopen Criteria:** N/A — this item IS open; closes when owner specifies scaling strategy
**Related Documents:** `docs/07_governance/AI_OPERATING_CONTEXT.md` §OPEN_ARCHITECTURAL_QUESTIONS OAQ-001; `backend/docker-compose.yml`; `backend/docker/rate_limiting.py`
**Related Register Entries:** SD-033 (rate limiter default); SD-005 (CI workflows archived — CI activation is part of scaling strategy)

---

## §3 — DATA RESIDENCY BEYOND PAKISTAN (OD-003)

**Item ID:** OD-003
**Title:** Data Residency Requirements for Regions Beyond Pakistan
**Classification:** OWNER-DECISION
**Current Status:** OPEN — awaiting owner decision
**Original Source:** OAQ-005 (AI_OPERATING_CONTEXT.md); Mandate 2 OWNER-REQUIRED compression
**Evidence Source:** `backend/country/pakistan/` (country-specific logic isolated per FD-007); no other country directory exists; FEATURE_SCOPE.md lists Pakistan as initial launch target
**Resolution Source:** N/A — not resolvable from repository
**Resolution Date:** NOT YET RESOLVED
**Resolved By:** N/A
**Decision Summary:** Owner must decide whether multi-country expansion requires data residency guarantees. Current architecture (FD-007) correctly isolates country-specific logic in `/backend/country/[country]/`, but data residency (physical server location, cross-border data transfer rules) is a legal/compliance decision, not an architectural one.
**Detailed Explanation:** For Pakistan launch: data residency is not legislatively mandated in the current framework for HRMS software. However, if expansion to UAE, Saudi Arabia, India, or other markets occurs, local data residency laws may apply (India: Personal Data Protection Bill; UAE: PDPL; etc.). Architecture supports country expansion (FD-007) but database remains single PostgreSQL instance — physical location of that instance is a deployment/legal decision. Owner must specify: (1) single-region or multi-region deployment, (2) data sovereignty requirements per market, (3) timeline for multi-country expansion (OAQ-005).
**Affected Components:** PostgreSQL deployment; backup/DR configuration; `backend/country/` architecture
**Affected Routes:** None (infrastructure decision)
**Affected APIs:** None
**Affected Workflows:** None directly
**Affected Roles:** None directly
**Owner Required:** YES — legal/compliance/product decision
**External Dependency:** Possibly — cloud provider regions; local DPO registration
**Future Impact:** HIGH — if multi-country expansion proceeds, architecture and infrastructure must change
**Reopen Criteria:** N/A — this item IS open; closes when owner specifies data residency policy
**Related Documents:** `docs/07_governance/AI_OPERATING_CONTEXT.md` §OPEN_ARCHITECTURAL_QUESTIONS OAQ-005; `backend/country/pakistan/`; `docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md` FD-007
**Related Register Entries:** OS-023 (multi-country OUT-OF-SCOPE for Phase 4)
