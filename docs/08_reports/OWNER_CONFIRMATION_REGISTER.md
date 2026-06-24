# OWNER CONFIRMATION REGISTER

Status: Active — Awaiting Owner Confirmation
Created: 2026-06-17
Phase: 2.95 — Residual Decision Collapse

---

## PURPOSE

Registers all items classified as `OWNER_CONFIRMATION_ONLY` — decisions where a recommended path exists, implementation may proceed, and the owner need only confirm (or object) rather than actively decide.

**Mechanism:** Each entry has a Recommended Default. Execution proceeds on the Recommended Default unless the owner explicitly selects a different option. Silence = confirmation of the default.

---

## OCR-001: Frontend App Location Through Phase 3

**Source:** ROD-001 (Residual Owner Decision Register)
**Original Classification:** Architecture Decision + Deployment Decision

**Recommended Default:**
Leave the Next.js frontend app at `backend/ui/` through the entirety of Phase 3 (Frontend Authority Capture). All Phase 3 work references `backend/ui/` as the authoritative frontend location.

After Phase 3 is complete and the frontend builds cleanly from `backend/ui/`, schedule a post-Phase 3 relocation sprint that:
1. Runs `next build` from the new `frontend/` location to verify no broken imports
2. Updates `backend/docker-compose.yml` build context for `frontend-ui` service
3. Renames existing `frontend/` (wireframes) to `frontend-wireframes/`

**Rationale:** Phase 3 frontend work has zero dependency on the file system location of the Next.js app. Relocating mid-audit adds execution risk (hidden import paths) with no UX benefit. Deferring to post-Phase 3 allows the build to validate the move safely.

**Why OWNER_CONFIRMATION_ONLY and not RESOLVED:**
The post-Phase 3 relocation will require a docker-compose.yml update (REQUIRES_APPROVAL). The owner should formally note awareness that the structural anomaly persists until then.

**Actions blocked if owner does not confirm:** None. Phase 3 proceeds from `backend/ui/` regardless.

**Owner response options:**
- Confirm default (silence or "confirmed") → Phase 3 proceeds from `backend/ui/`; relocation scheduled post-Phase 3
- Redirect: "Relocate before Phase 3" → Owner to authorize docker-compose.yml update; Phase 3 holds until build validates

---

## OCR-002: Deploy Validation CI Migration

**Source:** ROD-003 (Residual Owner Decision Register)
**Original Classification:** Deployment Decision

**Recommended Default:**
Migrate `backend/.github/workflows/deploy.yml` to `root/.github/workflows/integration.yml` as a `workflow_dispatch`-only trigger (manually triggered, not on every push). The integration test runs:
1. `docker compose up -d --build`
2. Health check: `curl http://localhost:8000/ready`
3. Frontend check: `curl http://localhost:3000/`
4. `docker compose down -v`

Promote to PR trigger once the workflow runs cleanly once on a manually triggered run.

**Requires owner to confirm:**
- GitHub runner type: GitHub-hosted runners with Docker support are available on paid plans; or a self-hosted runner must be registered
- Database seeding: The workflow requires `DATABASE_URL` and service env vars; owner must confirm how `.env` is generated in CI (secrets vault, default test values, etc.)
- Registry target: `build-push-action@v6` requires a registry; for integration-only, `docker compose build` without push is simpler

**Why OWNER_CONFIRMATION_ONLY:**
The recommended path is clear. The blocker is infrastructure choices (runner capabilities, env secret management) that the owner must confirm before the CI file can be written correctly.

**Actions blocked if owner does not confirm:** Only the CI migration itself is blocked. Phase 3 frontend work is not blocked.

**Owner response options:**
- Confirm default (silence or "confirmed") → Proceed with migration once runner + secrets strategy is confirmed
- Redirect: "Delete deploy.yml instead" → Option B: remove the file; simpler but loses the integration test pattern
- Redirect: "Leave as-is" → Option C: no CI migration; permanent status quo

---

## OCR-003: Docker Build + Test CI Step Activation

**Source:** ROD-004 (Residual Owner Decision Register, Sub-item B)
**Original Classification:** Repository Hygiene — DEFERRED

**Note:** Sub-item A (archiving `build.yml` and `test.yml` as reference files in `docs/archive/ci-legacy/`) is SAFE_REPOSITORY_HYGIENE and does not require confirmation. Only Sub-item B (activating steps in root CI) is registered here.

**Recommended Default:**
Add a `docker compose config` validation step to the existing root `.github/workflows/ci.yml` lint or test job:
```yaml
- name: Validate docker-compose config
  run: docker compose config > /tmp/compose.rendered.yaml
```

This provides a cheap, zero-infrastructure-cost correctness check that the compose file parses without error. It does not require Docker runtime, image builds, or registry access.

Defer Docker image builds (`build.yml` migration) to a separate infrastructure sprint — Docker builds require registry credentials and runner setup.

**Requires owner to confirm:**
- Whether GitHub Actions runners in the current setup have Docker CLI available (needed for `docker compose config`)
- If yes: add the compose validation step immediately
- If no: defer entirely; compose validation runs only locally

**Why OWNER_CONFIRMATION_ONLY:**
Adding a step to root `ci.yml` modifies the active CI pipeline (REQUIRES_APPROVAL per governance). The recommendation is clear but requires owner authorization before modification.

**Actions blocked if owner does not confirm:** Only the CI YAML modification is blocked. Phase 3 frontend work is not blocked.

**Owner response options:**
- Confirm default (silence or "confirmed") → Add compose-config validation step to root CI
- Redirect: "Do the full Docker build migration" → More ambitious; requires registry config, runner setup
- Redirect: "Skip entirely" → No CI changes; acceptable

---

## SUMMARY TABLE

| ID | Item | Recommended Default | Blocks Phase 3? | Response Needed By |
|----|------|--------------------|-----------------|--------------------|
| OCR-001 | Frontend stays in `backend/ui/` through Phase 3 | CONFIRMED (proceed from `backend/ui/`) | No | Before Phase 3 kickoff |
| OCR-002 | Deploy validation CI migration as `workflow_dispatch` | CONFIRM runner + secrets strategy | No | When CI work begins |
| OCR-003 | Compose-config validation step in root CI | CONFIRM runner has Docker CLI | No | When CI work begins |

**Phase 3 blocking items: ZERO**
All three OCR items have recommended defaults that allow Phase 3 to proceed without any owner response. The confirmations are needed only when the specific CI work or relocation work is being executed.

---

## HOW TO RESPOND

The owner may respond by:
1. Stating "OCR-001 confirmed" (or equivalent) to formally acknowledge the default
2. Providing a redirect ("relocate before Phase 3", "use self-hosted runner", etc.)
3. Ignoring the register — Phase 3 will proceed on all recommended defaults

The only action required before Phase 3 can begin: none. These items are informational, not blocking.
