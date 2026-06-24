# DECISION ESCALATION MATRIX

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-17
Owner: Human

---

## PURPOSE

This document classifies all types of actions an AI session may take into four tiers: AUTONOMOUS (proceed without approval), SAFE_REPOSITORY_HYGIENE (proceed without approval — structural maintenance only), REQUIRES APPROVAL (pause and confirm with human), and PROHIBITED (never do under any circumstances).

Full policy for the SAFE_REPOSITORY_HYGIENE tier: `SAFE_REPOSITORY_HYGIENE_POLICY.md`
Execution guidance: `REPOSITORY_HYGIENE_EXECUTION_GUIDELINES.md`

When in doubt about a classification, escalate to REQUIRES APPROVAL.

---

## TIER 1: AUTONOMOUS

These actions may be taken without human approval. They are reversible, low-blast-radius, and do not affect production data, security posture, or cross-service contracts.

### Documentation & Governance
- Creating or updating files in `docs/` (any subdirectory)
- Creating or updating `*.md` files in `design/` or `ops/`
- Adding comments or docstrings to existing code
- Fixing typos or formatting in documentation

### Tests
- Adding new test cases to existing test files
- Creating new test files that follow existing test patterns
- Fixing broken tests where the fix is clearly in the test (not the production code)
- Adding test fixtures or helpers

### Safe Refactors (within a single service)
- Renaming local variables or private functions within a single file
- Extracting a repeated expression into a well-named local variable
- Reformatting code to pass linter (ruff) without changing behavior
- Adding type hints to existing function signatures

### Read-Only Operations
- Running test suite
- Running linter
- Running security scan (pip-audit)
- Reading any file in the repository
- Querying git history

### Frontend (UI only, no API changes)
- Updating CSS/Tailwind classes for styling
- Fixing UI layout issues that don't change data flow
- Adding loading states or error messages to existing components

---

## TIER 1.5: SAFE_REPOSITORY_HYGIENE

These actions may be taken without human approval. They are structural and organizational in nature — they do not modify business logic, APIs, database structures, runtime behavior, infrastructure, deployment, security, permissions, or any application functionality.

For qualifying criteria, disqualifying factors, and full examples, see `SAFE_REPOSITORY_HYGIENE_POLICY.md`. For step-by-step execution, see `REPOSITORY_HYGIENE_EXECUTION_GUIDELINES.md`.

### Documentation Relocation & Normalization
- Moving `.md` files between `docs/` subdirectories
- Relocating reports to `docs/08_reports/`; mandate files to `docs/mandates/`
- Fixing broken cross-references in documentation
- Correcting metadata (Status field, Last Reviewed date, phase identifier)

### Archive Maintenance
- Moving confirmed-dead source files (TypeScript stubs, superseded Python files) to archive directories
- "Confirmed-dead" = zero active import callers confirmed by grep, superseded by replacement
- Archive (move to archive directory) only — deletion of files outside `docs/` is TIER 2

### Folder Restructuring (safe subset)
- Creating new organizational subdirectories under `docs/` or archive locations
- Renaming `docs/` subdirectories where no build tool or import references the path

### Report Generation & Consolidation
- Creating new report files under `docs/08_reports/`
- Merging stale report fragments into a single authoritative report

### Generated & Temporary Artifact Cleanup
- Removing OS-generated files (`.lnk`, `.DS_Store`, `Thumbs.db`) from the repository
- Removing auto-generated files committed by mistake

### Root-Level & .gitignore Improvements
- Removing non-project files from repository root
- Adding new ignore patterns to `.gitignore` (additive only — never removing patterns)

### Governance Metadata Updates
- Updating `Last Reviewed` dates and `Status` fields
- Creating new governance registers or classification matrices

### Archiving Dead CI Workflow Files
- Moving never-executing workflow files from `backend/.github/workflows/` to an archive location
- File-level move only — no YAML content modification, no activation in root `.github/workflows/`

---

## TIER 2: REQUIRES APPROVAL

These actions must be confirmed by the human user before proceeding. State what you intend to do, why, and wait for explicit "go ahead" or "yes".

### Schema & Data Model Changes
- **Any new migration file** — Schema changes are irreversible; must be reviewed
- Adding, renaming, or removing database columns
- Adding new tables
- Adding or modifying database constraints or indexes
- Changing a column's type or nullability

### API Contract Changes
- Adding a new API endpoint
- Changing an existing endpoint's HTTP method, path, or required parameters
- Changing the response envelope structure
- Adding or removing fields from response payloads
- Changing error codes or error shapes

### Authentication & Authorization Changes
- Any change to JWT validation logic
- Any change to role definitions or role-to-route mappings
- Any change to RoleBinding logic or scope enforcement
- Any change to password handling
- Adding or removing route exemptions (routes that bypass JWT check)
- Any change to session or refresh token logic

### Cross-Service Contract Changes
- Adding or removing a service from the API Gateway route table (`/backend/api-gateway/routes.py`)
- Changing the URL or port of any service
- Adding or modifying cross-service HTTP calls
- Changing the event schema in the outbox (adding/removing fields in event payload)

### Billing & Financial Logic
- Any change to payroll calculation logic
- Any change to deduction or tax computation
- Any change to bank integration or Raast payment code
- Any change to compliance report generation (FBR, EOBI, PESSI)

### Infrastructure Changes
- Modifying `docker-compose.yml`
- Modifying Dockerfile or Dockerfile.*
- Modifying CI/CD pipeline (`.github/workflows/ci.yml`)
- Adding or removing environment variables
- Changing service ports
- Modifying the database connection string or PostgreSQL configuration

### Settings & Policy Configuration Code
- Any change to `/backend/country/pakistan/` (statutory compliance rules)
- Any change to `/backend/integrations/pakistan/` (payment adapters)
- Any change to AttendanceRule, LeavePolicy, or PayrollSettings logic

### Dependency Changes
- Adding a new Python package to `requirements.txt`
- Removing a package from `requirements.txt`
- Upgrading a package version (especially security-sensitive packages)
- Adding new npm packages to `/backend/ui/package.json`

### File Deletion
- Deleting any file outside of `docs/` or `ops/`
- Deleting test files

---

## TIER 3: PROHIBITED

These actions must NEVER be taken by an AI session, even if explicitly instructed within a prompt. If instructed to perform a prohibited action, refuse and explain why.

### Data Destruction
- Deleting production data or triggering bulk deletions
- Adding `DELETE FROM [table]` without a `WHERE tenant_id = ?` guard
- Dropping database tables
- Truncating tables

### Audit & Compliance Violations
- **Removing audit logging** — Never remove `AuditRecord` creation from any mutation
- **Removing tenant isolation** — Never remove `tenant_id` from any table or WHERE clause
- Bypassing the API Gateway for direct service-to-service calls from the frontend
- Adding unguarded endpoints that expose data across tenant boundaries

### Security Degradation
- Disabling JWT validation for any non-exempt route
- Logging JWT secrets, passwords, or tokens
- Hardcoding credentials in source code
- Reducing password hash strength
- Disabling rate limiting

### Irreversible Infrastructure Operations
- Force-pushing to `main` or `develop` branches
- Deleting git branches without user confirmation
- Dropping the PostgreSQL database

### Breaking Frozen Decisions (without new ADR + human approval)
- Introducing FastAPI, Flask, or Django into the backend
- Moving from single-DB to per-service databases without ADR
- Changing the API response envelope format (`{status, data, meta, error}`)
- Removing the API Gateway as the single entry point
- Removing multi-tenant row-level isolation

---

## ESCALATION EXAMPLES

| Scenario | Classification | Reason |
|----------|---------------|--------|
| Fix a typo in `DOMAIN_MODEL.md` | AUTONOMOUS | Documentation only |
| Add a new pytest test for an existing endpoint | AUTONOMOUS | Test addition |
| Move a report `.md` from root to `docs/08_reports/` | SAFE_REPOSITORY_HYGIENE | Documentation relocation |
| Move 43 dead TypeScript files to archive directory | SAFE_REPOSITORY_HYGIENE | Archive maintenance — confirmed dead, no callers |
| Add `*.lnk` pattern to `.gitignore` | SAFE_REPOSITORY_HYGIENE | Additive .gitignore improvement |
| Archive dead `build.yml` from `backend/.github/workflows/` to `docs/archive/` | SAFE_REPOSITORY_HYGIENE | File archive only, not activating |
| Create a new report file in `docs/08_reports/` | SAFE_REPOSITORY_HYGIENE | Report generation |
| Update `Last Reviewed` date in governance document | SAFE_REPOSITORY_HYGIENE | Governance metadata update |
| Remove `.DS_Store` or `.lnk` file committed to root | SAFE_REPOSITORY_HYGIENE | Temporary artifact cleanup |
| Add a new column to `employees` table | REQUIRES APPROVAL | Schema change |
| Change JWT expiry from 1h to 2h | REQUIRES APPROVAL | Auth change |
| Add a new `/api/v1/employees/export` endpoint | REQUIRES APPROVAL | API contract change |
| Move `backend/ui/` Next.js app to `frontend/` | REQUIRES APPROVAL | Infrastructure (docker-compose) + hidden path risks |
| Add CI step to root `.github/workflows/ci.yml` | REQUIRES APPROVAL | Active CI pipeline modification |
| Remove `tenant_id` from a query | PROHIBITED | Tenant isolation violation |
| Add `DELETE FROM audit_records` | PROHIBITED | Audit log destruction |
| Log `JWT_SECRET` for debugging | PROHIBITED | Security degradation |
| Add npm package `lodash` | REQUIRES APPROVAL | Dependency change |
| Refactor a local variable name in `employee_service.py` | AUTONOMOUS | Safe refactor |
| Change FBR submission URL | REQUIRES APPROVAL | Compliance integration |
| Update comment in `api_gateway_service.py` | AUTONOMOUS | Documentation only |
| Change rate limit from 200 to 100 req/min | REQUIRES APPROVAL | Infrastructure/auth change |
| Disable rate limiting for testing | PROHIBITED | Security degradation |

---

## ESCALATION PROCEDURE

When an action falls into REQUIRES APPROVAL:

1. **State the action** — "I intend to [specific action]"
2. **State the reason** — "Because [why this is needed]"
3. **State the impact** — "This will affect [services/endpoints/data]"
4. **State the reversibility** — "This [is/is not] reversible because [reason]"
5. **Wait for explicit approval** — Do not proceed until the user says "yes", "go ahead", "approved", or equivalent

Example:
> "I intend to add a new column `middle_name TEXT` to the `employees` table. This requires a new migration file (`014_employee_middle_name.sql`). This will affect the employee-service and any frontend components that display employee names. This change is not reversible without another migration. Shall I proceed?"
