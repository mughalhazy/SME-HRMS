# P31 Workflow Integrity Report

## Scope
- Anchor validation used `docs/canon/workflow-catalog.md`, `docs/canon/security-model.md`, and the centralized workflow contract/engine implementation.
- Reviewed approval-bearing domains: leave, payroll, hiring, performance, and workflow/audit/notification integrations.
- Reviewed document-compliance for bypass risk; it emits compliance tasks/events but does not own approval orchestration.

## Validation Summary
- **Workflow centralization:** leave, payroll, hiring, and performance approval decisions route through `WorkflowService` and canonical workflow definitions.
- **State integrity:** terminal business transitions are now gated on terminal workflow outcomes, preventing premature domain state mutation before workflow completion.
- **Security of assignment:** workflow delegation now enforces assignment-scope safety so tasks cannot be delegated to an unrelated actor namespace.
- **Business alignment:** performance review cycles now remain `PendingApproval` until workflow approval; `PerformanceReviewCycleOpened` is emitted only after approval.
- **Audit/notification alignment:** workflow actions continue to emit workflow audit entries and task notifications, while domains emit business events only after valid workflow outcomes.

## Fixes Applied
1. **Performance review-cycle approval alignment**
   - Fixed a bypass/mismatch where `submit_review_cycle` immediately opened the cycle before approval.
   - Added explicit review-cycle decision handling through the workflow engine.
2. **Terminal workflow outcome enforcement**
   - Added terminal-result validation before performance goals, calibration sessions, and PIPs mutate business state.
3. **Delegation safety hardening**
   - Added assignment-scope validation for delegated workflow tasks.

## Regression Coverage Added
- Review cycle approval path stays pending until approved, then opens.
- Review cycle rejection returns business state to draft while preserving rejected workflow trace.
- Workflow delegation rejects cross-scope target reassignment.

## Domain-by-Domain Findings
- **Leave:** centralized submit/approve/reject path already enforced through workflow.
- **Payroll:** disbursement approval remains centralized through workflow before `Paid`.
- **Hiring:** requisition, offer, and candidate hire approvals remain workflow-backed.
- **Performance:** fixed review-cycle business-state mismatch; other approval paths now require terminal workflow results.
- **Document compliance:** no approval orchestration found; domain remains task/event driven and does not bypass workflow approvals because it does not own approval decisions.
