# EVENT DISCOVERY REPORT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This report is the discovery/audit companion to `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md`. It inventories events, publishers, consumers, queues, jobs, retry behavior, delivery guarantees, processing flows, failure handling, and dependencies as found in source, and flags items requiring further verification. Produced as part of PHASE 2 – BACKEND AUTHORITY CAPTURE.

---

## 1. EVENTS

- **Canonical catalog**: `/backend/docs/canon/event-catalog.md` documents **143 domain events** (per its header and `docs/00_authority/DOMAIN_MODEL.md`'s "DOMAIN EVENT CATALOG SUMMARY"). The catalog's "Registry summary" table itself contains **119 rows** — `TBD – REQUIRES VERIFICATION` for the remaining ~24.
- **Type registry**: `/backend/event_contract.py`'s `CANONICAL_EVENT_TYPES` dict contains **~190 entries** mapping PascalCase legacy names to dot-namespaced canonical types (`event_type`), spanning domains not all represented in the catalog's registry table (e.g. `hiring.requisition.*`, `hiring.offer.*`, `expense.*`, `project.*`, `helpdesk.*`, `learning.*`, `workforce_intelligence.*`, `cost_planning.*`, `compensation.*`, `benefits.*`, `settings.*`, `automation.rule.*`, `attendance.record.logged/corrected`, etc.).
- **Categories** (counted from `event-catalog.md` Registry summary, 119 rows): `employee-service` 18, `performance-service` 16, `engagement-service` 5, `attendance-service` 5, `leave-service` 4, `payroll-service` 4, `hiring-service` 13, `auth-service` 7, `notification-service` 4, `travel-service` 7, `compliance-service` 8, `decision-service` 6, `ewa-financial-service` 9, `bank-service` 8, `whatsapp-service` 8, `reporting-analytics-service` 2. See `EVENT_AND_QUEUE_ARCHITECTURE.md` Section 5 for the full breakdown table.

---

## 2. PUBLISHERS

Files found to call `stage_event`/`stage_canonical_event` (`EventOutbox`) or `emit_canonical_event`/`enqueue`+`dispatch_pending` (`OutboxManager`/`event_contract`) — i.e., services that write to the outbox (32 files matched a broad search for these patterns):

`data_integrity.py`, `background_jobs.py`, `reporting_analytics.py`, `chaos_engine.py`, `bank_service.py`, `decision_api.py`, `services/finance/ewa.py`, `whatsapp_service.py`, `services/compliance_service.py`, `event_contract.py`, `payroll_service.py`, `leave_service.py`, `attendance_service/service.py`, `automation_service.py`, `cost_planning_service.py`, `engagement_service.py`, `event_outbox.py`, `expense_service.py`, `helpdesk_service.py`, `integration_service.py`, `notification_service.py`, `performance_service.py`, `project_service.py`, `services/auth-service/service.py`, `services/hiring_service/service.py`, `travel_service.py`, `workflow_service.py` (plus test files).

### Sample-check: catalog events vs. publish-call evidence

Sampled 12 events for direct source matches (`Grep` for event name strings across `/backend/*.py` and subdirectories):

| Event | Publisher found | Evidence |
|---|---|---|
| `AttendanceCaptured` | Yes | `backend/attendance_service/service.py` |
| `LeaveRequestSubmitted` | Yes | `backend/leave_service.py` |
| `PayrollProcessed` | Yes | `backend/payroll_service.py` |
| `CandidateHired` / `InterviewScheduled` | Yes | `backend/services/hiring_service/service.py` |
| `DecisionCardCreated` | Yes | `backend/decision_api.py` |
| `EWARequested` | Yes | `backend/services/finance/ewa.py` |
| `WhatsAppMessageSent` | Yes | `backend/whatsapp_service.py` |
| `ReportGenerated` | Yes | `backend/reporting_analytics.py` |
| `HelpdeskTicketCreated` | Yes | `backend/helpdesk_service.py` |
| `EmployeeCreated` | **No publisher found** | Only appears in `event_contract.py` (type map) and `tests/test_search_service.py` (test fixture event) |
| `DepartmentCreated` | **No publisher found** | Only appears in `event_contract.py` and test fixtures |
| `RoleCreated`, `BusinessUnitCreated`, `LegalEntityCreated`, `LocationCreated`, `CostCenterCreated`, `GradeBandCreated`, `JobPositionCreated` | **No publisher found** | Same pattern — present in `CANONICAL_EVENT_TYPES`/catalog only |

**Finding**: There is no standalone `employee_service.py` (or equivalently named module) in `/backend/`. The 18 `employee-service` events listed in `event-catalog.md` — including the foundational `EmployeeCreated` — have **no identified runtime publish call** in the files reviewed. This is flagged as `TBD – REQUIRES VERIFICATION`: either (a) employee-service publish logic lives in a module not matched by this search (e.g., under a differently-named file or `services/employee-service/`), (b) employee lifecycle events are not yet implemented as outbox publishes, or (c) employee mutations are handled by a generic/shared mutation path not grep-matched by literal event-name strings.

---

## 3. CONSUMERS

- **`AutomationService.consume_event`** (`/backend/automation_service.py`): consumes canonical events, matches against `AutomationRule.trigger.event_types`, executes matched rules (workflow/notify/update actions). Uses `OutboxManager.consume_once` for consumer-side dedupe (`processed_events` / `consumer_dedupe` via `IdempotencyStore`).
- **`NotificationService.ingest_event`** (`/backend/notification_service.py`): consumed via two background job paths — `notification.dispatch` (direct) and `outbox.dispatch` (relayed from `EventOutbox.dispatch_pending`, filtered by `EVENT_NOTIFICATION_PLANS`).
- **Read models / projections** (`/backend/docs/canon/read-model-catalog.md`, `read-models.md`): document source services/entities per projection (e.g. `employee_directory_view`, `attendance_dashboard_view`, `payroll_summary_view`) but **do not specify an event-consumption mechanism**. `TBD – REQUIRES VERIFICATION` — no projection-rebuild consumer wired to `EventOutbox`/`OutboxManager` was found for these read models in the files reviewed.
- **Delivery path from `EventOutbox`/`service_outbox` to `AutomationService.consume_event`**: `TBD – REQUIRES VERIFICATION` — no direct call chain found connecting `EventOutbox.dispatch_pending` (or the `outbox.dispatch` background job) to `AutomationService.consume_event`. `AutomationService` uses its own separate `OutboxManager` instance for its own emitted events (`AutomationRuleCreated`, `AutomationRuleExecuted`).

---

## 4. QUEUES

- **No message queue / broker** (RabbitMQ, Kafka, Celery, SQS, Redis) found. `/backend/requirements.txt` contains only `pytest`, `uvicorn[standard]`, `psycopg2-binary`. Confirms `AI_OPERATING_CONTEXT.md` claim (OAQ-003 context) of no message queue.
- All "queue" semantics are implemented as **database-row queues**:
  - `event_outbox` table (`/backend/deployment/migrations/007_event_outbox.sql`) + `service_outbox`/`processed_events` (same migration) — event delivery queue.
  - `background_jobs` table (`/backend/deployment/migrations/008_background_jobs_schema.sql`) + `background_job_failures` — job queue.
  - Equivalent runtime state is held in `PersistentKVStore` namespaces (`event_outbox`, `outbox_records`, `processed_events`, `dispatch_log`, `jobs`, `job_types`, `job_results`, `job_failures`, `tenant_queue_configs`).
- `TenantJobQueueConfig` (`/backend/background_jobs.py`) enforces per-tenant queue capacity: `max_queued_jobs` (default 500, raises `QUEUE_OVERFLOW`/429 when exceeded) and `max_due_jobs_per_run` (default 50, throttles `run_due_jobs`).

---

## 5. JOBS

Background job types registered in `/backend/background_jobs.py` (see `EVENT_AND_QUEUE_ARCHITECTURE.md` Section 7.3 for full table):

| Job type | Max attempts | Source |
|---|---|---|
| `payroll.run` | 3 | `register_payroll_run_handler` |
| `payroll.payslip.generate` | 3 | `register_payroll_run_handler` |
| `leave.balance.recompute` | 3 | `register_leave_balance_recompute_handler` |
| `notification.dispatch` | 3 | `register_notification_dispatch_handler` |
| `outbox.dispatch` | 3 | `register_outbox_dispatch_handler` |
| `reporting.export` | 3 | `register_reporting_handlers` |
| `reporting.schedule.dispatch` | 3 | `register_reporting_handlers` |
| `workflow.escalation` | 2 | `register_workflow_escalation_handler` |
| `expire_overdue_decisions` | default (3) | `/backend/background_jobs_api.py`, S8-G06 (decision expiry sweep, comment specifies intended 15-min schedule) |

Jobs are scheduled via `enqueue_job` (status `Scheduled`) and executed via `run_due_jobs`/`execute_job`. `TBD – REQUIRES VERIFICATION`: no cron/daemon/loop invoking `run_due_jobs` periodically was found in the reviewed files — invocation appears to be caller-driven (e.g., test harnesses call `jobs.run_due_jobs(...)` explicitly).

---

## 6. RETRY BEHAVIOR

| Layer | Strategy | Citation |
|---|---|---|
| `BackgroundJobService.execute_job` | `run_with_retry`, exponential backoff (`base_delay=0.001`, doubling per attempt), bounded by `max_attempts - attempts`; only retries on non-`BackgroundJobError` or HTTP ≥500 | `/backend/background_jobs.py` L344-357 |
| Job terminal state | `attempts >= max_attempts` → `DeadLettered`; else `Failed` (re-triggerable via `POST /background-jobs/{id}/retry`) | `/backend/background_jobs.py` L378-411 |
| `OutboxManager.dispatch_pending` | `run_with_retry(attempts=3, base_delay=0.01, timeout_seconds=0.5)`; on exhaustion → `status='failed'` + `DeadLetterQueue.push('outbox_dispatch', ...)` | `/backend/outbox_system.py` L128-187 |
| `EventOutbox.dispatch_pending` | No retry/backoff inside the call; on dispatcher exception, `failed_attempts += 1`, event stays `pending` (`published_at` remains `None`) for the next poll | `/backend/event_outbox.py` L138-167 |
| `run_with_retry` primitive | `delay = base_delay * 2^(attempt-1)`; `on_retry` callback for logging | `/backend/resilience.py` L649-672 |

`background_job_failures` table records every failed attempt with `attempt_number`, `failure_reason`, `retryable`, `occurred_at`, `recovered_at` (citation: `/backend/deployment/migrations/008_background_jobs_schema.sql`).

---

## 7. DELIVERY GUARANTEES

- **At-least-once** is the closest characterization supported by evidence:
  - `EventOutbox`: events remain `pending` (`published_at IS NULL`) until a dispatcher succeeds; failed dispatch attempts increment `failed_attempts` but do not remove the event, so a subsequent `dispatch_pending` call will retry it — i.e., redelivery on failure (`/backend/event_outbox.py`).
  - `OutboxManager`: `enqueue` writes before `dispatch_pending`; on dispatch failure after retries, the record is marked `failed` and pushed to `DeadLetterQueue` rather than silently dropped — but it is **not automatically requeued** for redispatch absent an explicit mechanism (`TBD – REQUIRES VERIFICATION` whether `failed` records are retried by a later `dispatch_pending` call, since `dispatch_pending`'s filter is `status != 'dispatched'`, which *would* include `failed` records, so a subsequent call would re-attempt them — making this effectively at-least-once too).
- **Consumer-side dedupe** (`IdempotencyStore.replay_or_conflict`, `OutboxManager.consume_once`, keyed by `consumer_name:event_id`) provides idempotent processing on the consumer side, which combined with at-least-once delivery yields **effective exactly-once processing semantics for registered consumers** (e.g., `AutomationService.consume_event` via `consume_once`).
- **Exactly-once at the transport/delivery layer**: Not claimed or implemented — no distributed transaction or two-phase commit with an external broker exists (there is no external broker). The "exactly-once" property, where it holds, is achieved via **at-least-once delivery + idempotent consumers**, the standard outbox-pattern guarantee.
- `EventRegistry.register()` (`/backend/event_contract.py`) additionally enforces producer-side idempotency: replays of the same `event_id` (or same `tenant_id`+`event_type`+`idempotency_key`) with matching fingerprints are deduplicated; mismatched fingerprints raise `EventContractError("non_idempotent_events")`.

---

## 8. PROCESSING FLOWS

### 8.1 Synchronous publish (e.g. `PayrollService._emit_event`)
1. Business mutation occurs (e.g., payroll record processed).
2. `outbox.enqueue(legacy_event_name, data, correlation_id, idempotency_key)` — canonicalizes event via `ensure_event_contract`, writes `OutboxRecord(status='pending')`.
3. `outbox.dispatch_pending(self.events.append)` is called immediately in the same method — record is dispatched (with retry) and appended to an in-memory `events` list, `status='dispatched'`.

(`/backend/payroll_service.py` L552-560)

### 8.2 Polling relay (e.g. `EventOutbox` + `outbox.dispatch` job)
1. A service calls `EventOutbox.stage_event(...)` or `stage_canonical_event(...)` — writes an `OutboxEvent` row with `published_at=None`.
2. A `background_jobs` job of type `outbox.dispatch` is enqueued/scheduled and eventually executed (`run_due_jobs` → `execute_job`).
3. The handler calls `EventOutbox.dispatch_pending(dispatch_event, tenant_id=..., max_events=...)`.
4. For each pending row, `dispatch_event` checks `EVENT_NOTIFICATION_PLANS` and calls `notification_service.ingest_event(...)` if applicable; on success `mark_published` sets `published_at`.

(`/backend/event_outbox.py`, `/backend/background_jobs.py` L471-481)

### 8.3 Automation rule evaluation
1. An external caller (or — per open question in Section 3 — an outbox relay) calls `AutomationService.consume_event(event)`.
2. Event normalized via `ensure_event_contract`; matched against `Active` rules by `event_type` + optional `source_services`.
3. `OutboxManager.consume_once` dedupes per `(consumer_name=automation-rule:{rule_id}, event_id)`.
4. `_execute_rule` evaluates conditions; on match, executes actions (start workflow / notify / update); records `AutomationExecution`; emits `AutomationRuleExecuted`.

(`/backend/automation_service.py` L144-225)

### 8.4 Workflow escalation sweep
1. `workflow.escalation` background job runs (max 2 attempts).
2. Loads a workflow contract, finds `pending` steps with `deadline_at <= now`.
3. If any overdue steps found, stages `WorkflowEscalationReady` event via `EventOutbox.stage_event`.

(`/backend/background_jobs.py` L538-564)

---

## 9. FAILURE HANDLING

- **Job-level**: `BackgroundJobService.execute_job` catches all exceptions; records `JobFailureRecord` (`background_job_failures` table); transitions job to `Failed` (retryable) or `DeadLettered` (terminal, `attempts >= max_attempts`); pushes to `DeadLetterQueue.push('background_jobs', job_type, {...}, reason, retryable=...)`. Dead-lettered jobs are retriable via `POST /background-jobs/{id}/retry` (`/backend/background_jobs_api.py`), which resets `status=Scheduled`, clears `failure_reason`/`dead_lettered_at`.
- **Outbox dispatch failure (`OutboxManager`)**: caught per-record; `status='failed'`, `last_error`/`last_error_at` recorded, `dispatch_log` updated, pushed to `DeadLetterQueue.push('outbox_dispatch', event_type, payload, reason, retryable=True)`. Structured logging via `Observability.logger.error('outbox.dispatch_failed', ...)`.
- **Outbox dispatch failure (`EventOutbox`)**: caught per-row in `dispatch_pending`; `mark_failed` increments `failed_attempts`, event remains pending for redelivery; failure recorded in `dispatch_pending`'s returned `failures` list and via `observability.record_trace(..., status='failed', ...)`.
- **Dead Letter Queue** (`/backend/resilience.py` `DeadLetterQueue`): in-memory list of `DeadLetter` entries (`dead_letter_id`, `workflow`, `operation`, `reason`, `payload`, `trace_id`, `created_at`, `retryable`). `TBD – REQUIRES VERIFICATION`: whether `DeadLetterQueue` entries are persisted to a database table (no dead-letter table found in migrations reviewed — `background_job_failures` is the persisted analog for job failures specifically, but `dead_letters.push` itself appears to be in-memory only per `resilience.py`).
- **Central error logging**: `CentralErrorLogger` (`/backend/resilience.py`, used in `background_jobs.py`) logs job-type failures with `trace_id` and context (`job_id`, `tenant_id`).

---

## 10. DEPENDENCIES

- **Database**: Single PostgreSQL 16 instance (per `AI_OPERATING_CONTEXT.md` FD-005), accessed via `psycopg2-binary` — the only DB driver dependency.
- **Runtime**: `PersistentKVStore` (`/backend/persistent_store.py`) is the shared storage abstraction used by `EventOutbox`, `OutboxManager`, `BackgroundJobService`, and `AutomationService` for their respective namespaces — `TBD – REQUIRES VERIFICATION` whether `PersistentKVStore` itself is backed by the Postgres tables in migrations 007/008 or by a separate local persistence mechanism (file-based KV store); the class is imported and instantiated with `db_path` parameters suggesting file-backed storage, while the SQL migrations define parallel-looking Postgres tables (`event_outbox`, `service_outbox`, `processed_events`, `background_jobs`, `background_job_failures`). This dual schema (KV store namespaces vs. SQL tables with matching shapes) is the most significant open question in this review.
- **No external dependencies**: no message broker, no task queue (Celery/RQ), no cache layer (Redis) found in `requirements.txt` or imports.
- **Internal cross-service dependency**: `BackgroundJobService` optionally wires `payroll_service`, `leave_service`, `notification_service`, `reporting_service` into its handler registrations at construction time (constructor injection, not network calls) — consistent with FD-003 (single API Gateway) / FD-005 (single DB) architecture where "services" are modules within one deployable rather than independently networked processes for these flows. `TBD – REQUIRES VERIFICATION` against `docker-compose.yml`/`service-map.md` for how these modules map to the "24 Python microservices" described in `AI_OPERATING_CONTEXT.md`.

---

## 11. SUMMARY OF FLAGGED ITEMS

| # | Item | Severity | Status |
|---|---|---|---|
| 1 | 143 (documented) vs 119 (registry table rows) events in `event-catalog.md` | Medium | `TBD – REQUIRES VERIFICATION` |
| 2 | No publisher found for `employee-service`'s 18 events (`EmployeeCreated`, `DepartmentCreated`, `RoleCreated`, `BusinessUnitCreated`, `LegalEntityCreated`, `LocationCreated`, `CostCenterCreated`, `GradeBandCreated`, `JobPositionCreated`, and their `*Updated`/`*StatusChanged` counterparts) | High | `TBD – REQUIRES VERIFICATION` |
| 3 | Dual schema: `PersistentKVStore` namespaces vs. SQL tables (`event_outbox`, `service_outbox`, `processed_events`, `background_jobs`, `background_job_failures`) — which is the live runtime path | High | `TBD – REQUIRES VERIFICATION` |
| 4 | Read-model projection update mechanism (event-driven vs query-time) | Medium | `TBD – REQUIRES VERIFICATION` |
| 5 | External scheduler/cron invoking `run_due_jobs` and the 15-min `expire_overdue_decisions` sweep | Medium | `TBD – REQUIRES VERIFICATION` |
| 6 | Scheduled/threshold-triggered automation rule types (only event-triggered confirmed) | Medium | `TBD – REQUIRES VERIFICATION` |
| 7 | Delivery path connecting `EventOutbox`/`service_outbox` relay to `AutomationService.consume_event` | Medium | `TBD – REQUIRES VERIFICATION` |
| 8 | Whether `DeadLetterQueue` entries persist beyond in-memory process lifetime | Low | `TBD – REQUIRES VERIFICATION` |
