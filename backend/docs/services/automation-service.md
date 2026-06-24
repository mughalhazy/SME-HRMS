# Automation Service

Infrastructure-layer orchestration engine: rule-based workflow triggers, scheduled jobs, event-driven automations, and cross-service action dispatch.

## Scope
- Infrastructure service — not a business domain module.
- Executes automation rules: event-triggered, schedule-triggered, and threshold-triggered.
- Manages automation definitions (trigger + condition + action chains).
- Dispatches actions to domain services via their canonical APIs.
- Does NOT own business data or business logic — it orchestrates; domain services execute.
- Powers background automations like: auto-escalation, SLA breach alerts, scheduled payroll runs, compliance reminders, period-close triggers.

## HTTP surface (`/api/v1`)
- `POST /api/v1/automations` — create automation rule
- `GET /api/v1/automations/{automation_id}`
- `PATCH /api/v1/automations/{automation_id}`
- `POST /api/v1/automations/{automation_id}/enable`
- `POST /api/v1/automations/{automation_id}/disable`
- `DELETE /api/v1/automations/{automation_id}`
- `GET /api/v1/automations?status=&trigger_type=&limit=&cursor=`
- `GET /api/v1/automations/{automation_id}/executions?status=&limit=&cursor=` — execution history
- `POST /api/v1/automations/{automation_id}/trigger` — manual trigger (admin/testing)
- `GET /api/v1/automations/executions/{execution_id}` — retrieve single execution log

## Automation rule schema
```yaml
automation_id: uuid
name: string
trigger:
  type: event | schedule | threshold
  event_type: string          # e.g., AttendancePeriodClosed (for event triggers)
  cron_expression: string     # e.g., "0 9 * * 1" (for schedule triggers)
  threshold:                  # for threshold triggers
    metric: string
    operator: gt | lt | eq
    value: number
conditions:
  - field: string
    operator: eq | ne | gt | lt | contains
    value: any
actions:
  - type: api_call | event_emit | notification
    target_service: string
    endpoint: string
    payload_template: object
enabled: boolean
tenant_id: string
created_at: timestamp
```

## Trigger types

### Event-triggered
- Fires when a canonical domain event is received (e.g., `AttendancePeriodClosed` → trigger payroll run).
- Conditions filter whether the automation executes for this specific event instance.

### Schedule-triggered
- Fires on a cron schedule (e.g., monthly compliance reminder on the 25th).
- Used for: payroll run reminders, compliance deadline alerts, leave balance expiry notifications.

### Threshold-triggered
- Fires when a metric crosses a threshold (e.g., overtime hours > 40 for a department).
- Reads from analytics projections or read models; does not query transactional stores.

## Example automations in use
- `AttendancePeriodClosed` → trigger `POST /api/v1/payroll/run` for the closed period
- Schedule: 25th of month → send compliance submission reminder to PayrollAdmin
- Schedule: daily 9am → notify managers of pending approvals older than 48h
- `SLABreached` (helpdesk) → escalate ticket to HR Ops lead
- `DecisionCardCreated` (High risk) → notify PayrollAdmin immediately

## Authorization capabilities
- `CAP-AUT-002`: automation rule management (Admin only)
- `CAP-AUT-003`: automation execution history and manual trigger (Admin)

> Note: `CAP-AUT-001` is reserved for `auth-service` identity/access administration to avoid naming collision. Automation capabilities use `CAP-AUT-002` onwards.

## Owned entities
- `AutomationRule`
- `AutomationExecution`
- `AutomationExecutionLog`

## Supported workflows
- `automation_execution`

## Events published
- `AutomationTriggered`
- `AutomationExecuted`
- `AutomationFailed`
- `AutomationDisabled` (e.g., on repeated failure)

## Events subscribed
- All canonical domain events (filtered by registered automation rules)

## Read models produced
- `automation_execution_view` — execution history, success/failure rates, last run timestamps

## Dependencies
- All domain services (as action targets via canonical APIs)
- `auth-service` — admin-only authorization for rule management
- `notification-service` — notification-type action dispatch
- `audit-service` — automation execution audit trail
- Background jobs infrastructure (`background_jobs.py`) for schedule execution

## Sub-module: SupervisorEngine

**File:** `supervisor_engine.py` (749 lines)

The SupervisorEngine is a background infrastructure supervisor that runs alongside the automation service. It is NOT a user-facing module — it has no HTTP surface.

Responsibilities:
- Service health monitoring — polls internal health signals for all registered services
- Incident detection — identifies degradation patterns (latency spikes, error rate thresholds, failed background jobs)
- Recovery hooks — triggers remediation callbacks when an incident is confirmed
- Background-job supervision — monitors scheduled and long-running jobs; restarts on failure

Relationship to AutomationService:
- AutomationService handles operator-defined automation rules (business workflows).
- SupervisorEngine handles platform-level incident response (infrastructure self-healing).
- They share the background-job infrastructure (`background_jobs.py`) but operate independently.

This is registered in `service-map.md` under the `automation-service` entry as a sub-component.

> NOTE (2026-06-13): as of this pass, `docs/canon/service-map.md`'s `## automation-service` section does not yet contain a SupervisorEngine sub-component reference — this line is a forward-pointer to a cross-reference that has not been added to service-map.md. Not corrected here per [[feedback_divergence_resolution]] (service-map.md edits are out of scope for this pass except for the manifest-completeness extension); flagged for a future service-map.md update pass.

## Notes
- Automation service is infrastructure, not an HR feature. It has no HR business logic of its own.
- All actions it dispatches are subject to the same authorization and audit rules as if an operator called those endpoints directly.
- Automation rules are tenant-scoped; cross-tenant execution is prohibited.
- Failed automations are logged with full execution trace; repeated failures auto-disable the rule and alert Admin.
