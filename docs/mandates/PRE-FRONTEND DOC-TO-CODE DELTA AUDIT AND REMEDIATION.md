PRE-FRONTEND DOC-TO-CODE DELTA AUDIT AND REMEDIATION

OBJECTIVE

Before Frontend Authority Capture begins, verify that all governance, backend, repository, and normalization documentation accurately reflects the actual repository and codebase.

Find and fix all documentation/code/repository deltas.

The goal is to ensure frontend planning is based on true backend reality, not assumptions, shortcuts, stale docs, or incomplete audits.

---

CORE RULE

Repository and code evidence are the source of truth.

Documentation must match repository reality.

If docs and code disagree, fix the documentation unless the finding is a true code defect requiring owner approval.

Do not invent functionality.

Do not infer missing behavior.

Do not hide gaps behind vague TBDs.

---

AUDIT SCOPE

Audit the full repository, not only docs/.

Review:

- Root files
- Backend source
- Backend tests
- Backend configs
- Scripts
- Tooling
- CI/CD files
- Deployment files
- Database/migration files
- Generated artifacts
- Legacy folders
- Archive folders
- Documentation
- Reports
- Registers
- Governance files
- Normalization outputs

---

VERIFY AGAINST CODE

Compare actual repository evidence against:

- Governance documents
- Backend authority documents
- Fullstack contract documents
- Repository normalization reports
- Repository restructuring reports
- Gap registers
- Risk registers
- Decision records
- Inventories
- Matrices

---

REQUIRED DELTA CHECKS

Identify:

- Docs claiming files/modules/features that do not exist
- Code files/modules/features missing from docs
- APIs missing from API contracts
- Entities missing from database/domain docs
- Services missing from service catalog
- Repositories missing from repository docs
- DTOs/schemas missing from data-shape docs
- Auth/permission logic missing from contracts
- Validations missing from validation docs
- Events/queues/jobs missing from event docs
- Config/env variables missing from docs
- Tests missing from testing inventory
- Scripts/tooling missing from repo inventory
- Generated artifacts that should be ignored or archived
- Legacy docs still competing with authority docs
- Folder structure differences from normalization reports
- Gaps that are actually resolvable from code
- TBDs that should be replaced with evidence
- Assumptions stated as facts
- Duplicated authority claims
- Misplaced files
- Remaining SAFE_REPOSITORY_HYGIENE items

---

REQUIRED OUTPUTS

Create:

docs/08_reports/PRE_FRONTEND_DELTA_AUDIT.md

docs/08_reports/DOC_TO_CODE_DELTA_MATRIX.md

docs/08_reports/UNVERIFIED_CLAIMS_REGISTER.md

docs/08_reports/UNDOCUMENTED_CODE_REGISTER.md

docs/08_reports/DOC_DRIFT_REGISTER.md

docs/08_reports/TBD_RESOLUTION_REGISTER.md

docs/08_reports/PRE_FRONTEND_READINESS_REPORT.md

---

REMEDIATION RULES

After the audit, immediately fix all findings that fall into:

Documentation correction

Cross-reference correction

Authority mapping correction

Report correction

Inventory correction

Matrix correction

Archive/reference correction

SAFE_REPOSITORY_HYGIENE

Do not wait for another prompt for these.

---

OWNER APPROVAL RULES

Only stop and request approval for findings that require:

- source code behavior changes
- API changes
- database/schema changes
- auth/security changes
- permission model changes
- deployment config decisions
- CI/CD behavior decisions
- deleting or merging conflicting runtime/test configs

For those, create:

docs/08_reports/OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md

Each item must include:

- issue
- evidence
- options
- risk
- recommendation

---

SPECIFIC REQUIRED REVIEW

Also include the remaining repository restructuring items already identified.

Handle all SAFE_REPOSITORY_HYGIENE items now.

For items still requiring approval, perform forensic comparison and document recommended resolution.

Do not merge or delete conflicting runtime/deployment/test configs without owner approval.

---

SUCCESS CRITERIA

Success means:

- Documentation matches backend/repository reality.
- All resolvable doc/code deltas are fixed.
- All SAFE_REPOSITORY_HYGIENE items are executed.
- All remaining unresolved items are true owner-decision items.
- No vague TBD remains where code evidence exists.
- Frontend Authority Capture can begin without building on false assumptions.

Stop after audit, remediation, reports, and owner-approval list.

Do not begin Phase 3.
