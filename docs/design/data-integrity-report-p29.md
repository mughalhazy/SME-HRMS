# P29 Data Integrity Validation Report

## Scope
This pass extends existing persistence-backed services, projections, jobs, events, and audit trails to validate trustworthiness across transactional and projected layers without redesigning schemas or moving business ownership.

## What was added
- A cross-service `DataIntegrityValidator` that checks:
  - employee core data consistency and org relationship integrity,
  - leave balance correctness,
  - payroll component / payroll cycle correctness,
  - candidate-to-employee handoff integrity,
  - workflow state vs business state integrity,
  - projection drift in search and analytics layers,
  - tenant ownership consistency,
  - audit and event alignment for major mutations.
- Safe repairs for minor issues only:
  - `repair_minor_projection_drift`,
  - `patch_orphan_reference_issues_where_safe`,
  - `rebuild_inconsistent_indexes_or_projections`,
  - `normalize_tenant_ownership_fields`.
- Background-job support for running safe integrity repairs through the existing job system.
- A CLI repair script in `deployment/repair_data_integrity.py`.

## Quality contract alignment
- **entity_integrity**: employee, leave, payroll, and hiring handoff validations are scored together.
- **cross_service_consistency**: workflow/business-state alignment and cross-service reference checks remain in service-owned boundaries.
- **projection_integrity**: search and analytics projections are rebuilt from canonical read models/events and compared against stored state.
- **tenant_integrity**: tenant drift is detected and normalized only where safe in projection stores.
- **audit_event_alignment**: critical leave, hiring, and payroll mutations require matching audit + event traces.

## Repair policy
Only minor, deterministic drift is auto-fixed. Source-of-truth conflicts remain hard failures under the rejection rule.

## Re-QC
`deployment/re_qc_validate_data_integrity.py` verifies the validator, tests, repair script, and documentation are all present.
