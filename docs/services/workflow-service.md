# workflow-service

Centralized workflow orchestration for SME-HRMS approval and escalation paths.

## Centralized inline approval paths
- `leave-service.submit_request` now creates a `leave_request_approval` workflow and routes manager approval decisions through the workflow engine before applying leave-domain side effects.
- `payroll-service.mark_paid` now completes a centralized `payroll_disbursement_approval` workflow before finalizing payroll disbursement.
- `hiring-service.mark_candidate_hired` now completes a centralized `candidate_hiring_approval` workflow before changing candidate status to `Hired`.

## API surface
- `GET /api/v1/workflows/{workflow_id}`
- `GET /api/v1/workflows/inbox`
- `POST /api/v1/workflows/{workflow_id}/approve`
- `POST /api/v1/workflows/{workflow_id}/reject`
- `POST /api/v1/workflows/{workflow_id}/delegate`
- `POST /api/v1/workflows/escalate`

## Integration rules
- Domain services initiate workflow instances but do not directly own approval task state.
- Workflow transitions emit workflow events, audit records, and notification ingestion payloads.
- Workflow inbox reads and transitions enforce tenant matching via `tenant_support.assert_tenant_access`.
