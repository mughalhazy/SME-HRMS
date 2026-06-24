# Background Jobs / Scheduler Summary

The background jobs layer extends the current monorepo architecture without taking ownership away from domain services.

## Workloads moved off request path

- `payroll_processing`: payroll batch execution is now job-ready through the `payroll.run` handler, which calls the existing `PayrollService.run_payroll` method.
- `leave_request`: leave balance recomputation is now job-ready through the `leave.balance.recompute` handler, which calls the new `LeaveService.recompute_employee_balance` helper owned by the leave domain.
- `notification_dispatch`: notification fan-out can be queued through the `notification.dispatch` handler, which calls the existing `NotificationService.ingest_event` method.
- `event_outbox`: outbox draining is now job-ready through the `outbox.dispatch` handler, which dispatches staged domain events and marks them published.
- workflow escalation readiness: overdue workflow-step inspection is now schedulable through the `workflow.escalation` handler, which validates workflow payloads against the canonical workflow contract before raising an escalation-ready event.

## Boundary preservation

- Business rules remain in `PayrollService`, `LeaveService`, and `NotificationService`.
- The job layer only schedules, retries, tracks, and replays long-running or time-based work.
- Tenant context and trace/correlation data are carried into every job execution.
