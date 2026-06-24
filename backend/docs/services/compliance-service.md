# Compliance Service

Orchestrates Pakistan statutory compliance lifecycle: validation, report generation, submission, and audit trail for FBR, EOBI, and PESSI/SESSI obligations.

## Scope
- Owns the compliance submission lifecycle: `DRAFT → VALIDATED → SUBMITTED → ACK → FAILED → RETRY`.
- Validates payroll data against statutory rules BEFORE payroll is finalized.
- Generates required statutory outputs: FBR Annexure-C, EOBI PR-01, PESSI/SESSI returns.
- Delegates country-specific computation to the country abstraction layer (`country/{country}/compliance_engine`).
- Maintains immutable audit trail for all submission events.
- Does NOT contain country-hardcoded logic — all statutory rules live in country adapters.

## HTTP surface (`/api/v1`)
- `POST /api/v1/compliance/submissions` — initiate a compliance submission for a pay period
- `GET /api/v1/compliance/submissions/{submission_id}` — retrieve submission state
- `GET /api/v1/compliance/submissions?period=&type=&status=&limit=&cursor=`
- `POST /api/v1/compliance/submissions/{submission_id}/validate` — run pre-payroll validation gate
- `POST /api/v1/compliance/submissions/{submission_id}/generate` — generate statutory report artifacts
- `POST /api/v1/compliance/submissions/{submission_id}/submit` — submit to authority (FBR/EOBI/PESSI)
- `POST /api/v1/compliance/submissions/{submission_id}/retry` — retry failed submission
- `GET /api/v1/compliance/submissions/{submission_id}/report` — retrieve generated report artifact
- `GET /api/v1/compliance/audit?submission_id=&period=&limit=&cursor=` — compliance audit trail

## Submission lifecycle states
```
DRAFT → VALIDATED → SUBMITTED → ACK
                              → FAILED → RETRY → SUBMITTED
```
- `DRAFT`: submission record created, not yet validated.
- `VALIDATED`: pre-payroll validation passed (`is_valid: true`).
- `SUBMITTED`: report dispatched to government adapter.
- `ACK`: authority acknowledged receipt.
- `FAILED`: submission rejected or network failure.
- `RETRY`: re-queued after failure investigation.

## Authorization capabilities
- `CAP-COM-001`: compliance submission management (Admin, PayrollAdmin)
- `CAP-COM-002`: compliance report access (Admin, PayrollAdmin, read-only Auditor)
- `CAP-COM-003`: compliance audit trail (Admin, Auditor)

## Owned entities
- `ComplianceSubmission`
- `ComplianceReport`
- `ComplianceAuditRecord`

## Domain rules
- Validation MUST execute before payroll can be marked as processed for the same period.
- If `validate_payroll` returns violations, finalization is blocked until resolved.
- Report generation only permitted after `VALIDATED` state.
- All state transitions are immutable log entries; no soft-deletes.
- Submission dispatches through `government-adapters` layer (FBR adapter, EOBI adapter, PESSI adapter).
- Each submission is scoped to `(organization_id, legal_entity_id, period, submission_type)`.

## Supported workflows
- `compliance_submission`

## Events published
- `ComplianceSubmissionCreated`
- `ComplianceValidationPassed`
- `ComplianceValidationFailed`
- `ComplianceReportGenerated`
- `ComplianceSubmitted`
- `ComplianceAcknowledged`
- `ComplianceSubmissionFailed`
- `ComplianceRetryQueued`

## Events subscribed
- `PayrollProcessed` — triggers validation gate for the same period
- `EmployeeStatusChanged` — updates roster used in statutory reports

## Read models produced
- `compliance_status_view` — per-period submission state, violation summary, report links
- enriches `payroll_summary_view` with compliance gate status

## Dependencies
- `payroll-service` — source of payroll data for validation input
- `employee-service` — employee roster and statutory identifiers (CNIC, NTN)
- `government-adapters` — FBR, EOBI, PESSI dispatch layer
- `audit-service` — immutable compliance audit records
- `notification-service` — compliance alerts, failure notifications

## Implementation files

| Component | File |
|---|---|
| ComplianceService (orchestrator) | `services/compliance_service.py` |
| Compliance HTTP surface | `compliance_api.py` |
| Precheck autopilot (payroll gate) | `services/compliance_autopilot.py` |
| Pakistan submission tracking | `integrations/pakistan/submission_tracking.py` (165 lines) |
| FBR adapter | `integrations/pakistan/fbr_adapter.py` |
| EOBI adapter | `integrations/pakistan/eobi_adapter.py` |
| PESSI adapter | `integrations/pakistan/pessi_adapter.py` |

### ComplianceAutopilot
`services/compliance_autopilot.py` is the pre-payroll gate — it calls `validate_payroll()` then `generate_reports()` on an injected compliance service. If validation fails, it halts payroll with `stop_payroll: true`. It accepts any service implementing the compliance interface (no Pakistan hardcoding).

### Submission Tracking
`integrations/pakistan/submission_tracking.py` tracks the status of submissions dispatched to FBR/EOBI/PESSI. It is the downstream component that receives acknowledgement callbacks and updates submission state. Called by the integrations layer; does not expose HTTP directly.

## Notes
- Country logic is fully delegated: `ComplianceEngineInterface.validate_payroll()` and `generate_reports()` are called on the resolved country adapter.
- See `docs/canon/country-layer.md` for adapter contract and resolver rules.
- See `docs/specs/country/pakistan/compliance.md` for Pakistan-specific FBR Annexure-C schema, EOBI PR-01, and PESSI/SESSI field-level rules.
