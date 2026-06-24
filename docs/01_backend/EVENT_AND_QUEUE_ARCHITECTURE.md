# EVENT AND QUEUE ARCHITECTURE

Status: Draft
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## PURPOSE

This document describes the backend's event, queue, and background-job architecture **exactly as implemented**, based on direct inspection of source code and migrations. It supersedes assumptions and documents only what is verifiable. Items that could not be verified are marked `TBD – REQUIRES VERIFICATION`.

Primary evidence sources:
- `/backend/event_outbox.py` (KV-store-backed outbox, `EventOutbox` class)
- `/backend/outbox_system.py` (record-based outbox, `OutboxManager` class)
- `/backend/event_contract.py` (canonical event envelope + type registry)
- `/backend/deployment/migrations/007_event_outbox.sql` (`event_outbox`, plus `service_outbox`/`processed_events` from the same file)
- `/backend/deployment/migrations/008_background_jobs_schema.sql` (`background_jobs`, `background_job_failures`)
- `/backend/background_jobs.py`, `/backend/background_jobs_api.py`
- `/backend/automation_service.py`, `/backend/automation_api.py`, `/backend/automation_contract.py`
- `/backend/docs/canon/event-catalog.md` (126-event canonical catalog — verified count 2026-06-15; prior references to 143 or 119 were stale)
- `/backend/resilience.py` (retry, dead-letter, idempotency primitives)

---

## 1. NO MESSAGE QUEUE — DB-OUTBOX-BASED DELIVERY

`/backend/requirements.txt` contains exactly three dependencies:

```
pytest
uvicorn[standard]
psycopg2-binary
```

There is no RabbitMQ, Kafka, Celery, SQS, or Redis client library declared. A repository-wide search for `rabbitmq|kafka|celery|sqs|amqp|redis` (case-insensitive) over `requirements.txt` returns no matches, and no broker client imports were found in the services reviewed. This confirms the `AI_OPERATING_CONTEXT.md` claim (referenced as OAQ-003 context — no message queue) is **still accurate as of this review**.

Event delivery is implemented as:
1. **Transactional outbox write** — domain services append a canonical event record to an in-process/append-only outbox store in the same logical operation as the business-state mutation (no two-phase commit to an external broker).
2. **Polling/relay dispatch** — a dispatcher later iterates pending outbox rows and invokes a `publisher`/`dispatcher` callback per row, marking each row dispatched/published or failed.

There is no push-based subscription, webhook fan-out, or external broker. All "queueing" is rows in Postgres tables (`event_outbox`, `service_outbox`, `background_jobs`) or equivalent KV-store namespaces, polled by application code.

---

## 2. THE OUTBOX PATTERN — TWO IMPLEMENTATIONS

The codebase contains **two outbox implementations** that coexist:

### 2.1 `EventOutbox` (`/backend/event_outbox.py`)

- Backed by `PersistentKVStore[str, OutboxEvent]` (`service='background-jobs'`, `namespace='event_outbox'`).
- `OutboxEvent` dataclass fields: `event_id`, `tenant_id`, `aggregate_type`, `aggregate_id`, `event_name`, `payload`, `trace_id`, `occurred_at`, `published_at`, `failed_attempts`, `created_at`.
- `stage_event(...)` — writes a new `OutboxEvent` with `published_at=None`, `failed_attempts=0`. This is the "stage" half of the outbox pattern — the event row is the record-of-intent.
- `stage_canonical_event(event, aggregate_type, aggregate_id)` — adapts a canonical event dict (from `event_contract.py`) into an `OutboxEvent`.
- `pending_events(tenant_id=None)` — returns all rows where `published_at IS NULL`, sorted by `(occurred_at, created_at, event_id)`.
- `dispatch_pending(dispatcher, tenant_id=None, max_events=None)` — **relay mechanism**: iterates pending rows, calls `dispatcher(row)`. On success: `mark_published(event_id)` sets `published_at`. On exception: `mark_failed(event_id)` increments `failed_attempts`; the event remains pending (no automatic max-retry cutoff in this class — `failed_attempts` is tracked but not used to stop redelivery here).
- **Relay trigger**: `dispatch_pending` is **polling-based**, invoked by the background-jobs system via the registered `outbox.dispatch` job type (`BackgroundJobService.register_outbox_dispatch_handler`, `/backend/background_jobs.py` line ~471-481). It is not a DB trigger/LISTEN-NOTIFY mechanism — `TBD – REQUIRES VERIFICATION` whether any Postgres `LISTEN/NOTIFY` exists elsewhere (none found in files reviewed).
- The `outbox.dispatch` handler dispatches each pending event to `notification_service.ingest_event(...)` if the event name is in `EVENT_NOTIFICATION_PLANS` (`/backend/notification_service.py`).

### 2.2 `OutboxManager` (`/backend/outbox_system.py`)

- Backed by three `PersistentKVStore` namespaces per service: `outbox_records`, `processed_events`, `dispatch_log`.
- `OutboxRecord` dataclass fields: `outbox_id`, `event_id`, `event_type`, `tenant_id`, `status` (`pending`/`dispatched`/`failed`), `source`, `payload`, `created_at`, `updated_at`, `dispatched_at`, `attempt_count`, `last_error`, `last_error_at`, `metadata`.
- `enqueue(legacy_event_name, data, correlation_id, idempotency_key, metadata)` — runs the payload through `ensure_event_contract` (canonicalizes to the `event_contract.py` envelope), then writes an `OutboxRecord` with `status='pending'`.
- `dispatch_pending(publisher, attempts=3, retryable=None)` — **relay mechanism**: for each non-`dispatched` record (sorted by `created_at`, `outbox_id`), calls `run_with_retry(publish, attempts=attempts, base_delay=0.01, timeout_seconds=0.5, retryable=...)` where `publish()` invokes `publisher(record.payload)`.
  - On success: `status='dispatched'`, `dispatched_at` set, `attempt_count += 1`, logged to `dispatch_log`.
  - On failure (all retries exhausted): `status='failed'`, `attempt_count += attempts`, `last_error`/`last_error_at` set, and the record is pushed to `DeadLetterQueue` (`/backend/resilience.py`) via `dead_letters.push('outbox_dispatch', event_type, payload, reason, retryable=True)`.
- `consume_once(consumer_name, event, handler)` — consumer-side idempotency: dedupe key `f'{consumer_name}:{event_id}'` checked against `IdempotencyStore.replay_or_conflict`; records outcome to `processed_events` namespace and `consumer_dedupe`.
- Used by `automation_service.py` (`AutomationService.outbox = OutboxManager(...)`) for `AutomationRuleCreated` / `AutomationRuleExecuted` events and consumer dedupe of incoming events.
- `PayrollService._emit_event` (`/backend/payroll_service.py` line 552) calls `self.outbox.enqueue(...)` immediately followed by `self.outbox.dispatch_pending(self.events.append)` — i.e., **dispatch is invoked synchronously in the same call**, appending the canonical event to an in-memory `self.events` list (used by tests/handlers, e.g. `background_jobs.py`'s `_stage_new_events`).

### 2.3 Relay summary

- **`EventOutbox`**: write happens via `stage_event`/`stage_canonical_event`; relay happens via a separately-invoked `dispatch_pending`, driven by the `outbox.dispatch` background job (polling).
- **`OutboxManager`**: write happens via `enqueue`; relay happens via `dispatch_pending`, which in `PayrollService` is called synchronously right after `enqueue` (effectively immediate, in-process "publish"), with retry + dead-letter on failure.
- Neither implementation uses an external broker, cron daemon process, or DB trigger for the relay step in the code reviewed — the only confirmed automatic scheduling path is the `background_jobs` table/service (Section 4).

---

## 3. `event_outbox` TABLE SCHEMA (Postgres)

Source: `/backend/deployment/migrations/007_event_outbox.sql`

```sql
CREATE TABLE IF NOT EXISTS event_outbox (
  tenant_id VARCHAR(80) NOT NULL,
  event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  aggregate_type VARCHAR(80) NOT NULL,
  aggregate_id VARCHAR(100) NOT NULL,
  event_name VARCHAR(120) NOT NULL,
  payload JSONB NOT NULL,
  trace_id VARCHAR(64) NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  published_at TIMESTAMPTZ,
  failed_attempts INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_event_outbox_tenant_event UNIQUE (tenant_id, event_id)
);

CREATE INDEX idx_event_outbox_unpublished ON event_outbox (tenant_id, published_at);
CREATE INDEX idx_event_outbox_aggregate ON event_outbox (tenant_id, aggregate_type, aggregate_id);
CREATE INDEX idx_event_outbox_event_name ON event_outbox (tenant_id, event_name);
```

This schema maps 1:1 to the `OutboxEvent` dataclass fields in `/backend/event_outbox.py`. The `idx_event_outbox_unpublished` index supports the `pending_events()` query pattern (`WHERE published_at IS NULL`).

The same migration file also defines a second outbox-style table pair (used by `OutboxManager`'s record model, conceptually):

```sql
CREATE TABLE IF NOT EXISTS service_outbox (
  outbox_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(80) NOT NULL,
  source_service VARCHAR(80) NOT NULL,
  event_id UUID NOT NULL,
  event_type VARCHAR(160) NOT NULL,
  event_payload JSONB NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Dispatched', 'Failed')),
  attempt_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  dispatched_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_service_outbox_event UNIQUE (tenant_id, source_service, event_id)
);

CREATE TABLE IF NOT EXISTS processed_events (
  processed_event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(80) NOT NULL,
  consumer_name VARCHAR(120) NOT NULL,
  event_id UUID NOT NULL,
  event_type VARCHAR(160) NOT NULL,
  processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT uq_processed_events_consumer UNIQUE (tenant_id, consumer_name, event_id)
);
```

**SQL-to-Python mapping (DG-006 — resolved by documentation):**

| SQL Table (`007_event_outbox.sql`) | Python Class | Python file | Storage backend | Notes |
|------------------------------------|--------------|-------------|-----------------|-------|
| `event_outbox` | `EventOutbox` | `event_outbox.py` | `PersistentKVStore(service='background-jobs', namespace='event_outbox')` | KV-store namespace, not direct psycopg2 writes to the SQL table |
| `service_outbox` | `OutboxManager` | `outbox_system.py` | `PersistentKVStore(namespace='outbox_records')` | KV-store namespace maps conceptually to service_outbox schema |
| `processed_events` | `OutboxManager` | `outbox_system.py` | `PersistentKVStore(namespace='processed_events')` | Dedupe tracking; same KV-store mechanism |

**Finding:** Both Python classes write to `PersistentKVStore` namespaces, not directly to the SQL tables via psycopg2. The SQL tables in `007_event_outbox.sql` define the conceptual schema; the live storage path is through `PersistentKVStore`. Whether `PersistentKVStore` ultimately writes to the `event_outbox` / `service_outbox` PostgreSQL tables or to a separate KV backing store depends on the `PersistentKVStore` implementation — this is the live path TBD. The SQL table schemas serve as the canonical record shape definition regardless of storage backend.

Evidence: `backend/event_outbox.py` (EventOutbox class), `backend/outbox_system.py` (OutboxManager class), `backend/deployment/migrations/007_event_outbox.sql`.

---

## 4. EVENT ENVELOPE FORMAT

Two envelope shapes appear in the codebase:

### 4.1 Canonical envelope (`/backend/event_contract.py`, `ensure_event_contract` / `_normalize_structure`)

```json
{
  "event_id": "uuid",
  "event_type": "namespaced.dot.case",
  "event_name": "PascalCaseLegacyName",
  "tenant_id": "string",
  "timestamp": "ISO8601",
  "occurred_at": "ISO8601",
  "source": "string (producer service)",
  "producer_service": "string",
  "trace_id": "uuid (= metadata.correlation_id)",
  "data": { "...business payload, always includes tenant_id..." },
  "metadata": {
    "version": "v1",
    "correlation_id": "uuid",
    "occurred_at": "ISO8601",
    "producer_service": "string",
    "legacy_event_name": "PascalCaseLegacyName",
    "idempotency_key": "string (optional)",
    "qc": { "checks": [...], "auto_fixed": [...], "rechecked": [...], "duplicate": "bool" }
  }
}
```

- `event_type` is the canonical dot-namespaced form (e.g. `employee.created`); `event_name`/`legacy_event_name` is the PascalCase form used in `event-catalog.md` (e.g. `EmployeeCreated`). `CANONICAL_EVENT_TYPES` in `event_contract.py` is the bidirectional mapping table (190+ entries spanning all domains).
- `normalize_event_type()` will auto-derive a dot-case type from an unmapped PascalCase/snake_case/kebab-case name if it is not in the lookup table.
- `EventRegistry.register()` enforces idempotency: same `event_id` + matching fingerprint replays the existing event; same `event_id` with a different fingerprint, or same `(tenant_id, event_type, idempotency_key)` with a different fingerprint, raises `EventContractError("non_idempotent_events")`.

### 4.2 Documented summary envelope (`docs/00_authority/DOMAIN_MODEL.md` "DOMAIN EVENT CATALOG SUMMARY")

```json
{
  "event_id": "uuid",
  "event_name": "string",
  "occurred_at": "ISO8601",
  "producer_service": "string",
  "trace_id": "uuid",
  "payload": {}
}
```

This is a simplified description of the same envelope; the implemented envelope (4.1) has additional fields (`event_type`, `tenant_id`, `timestamp`, `source`, `data` vs `payload`, `metadata`). The `event-catalog.md` "Event conventions" section states every payload includes `event_id`, `event_name`, `occurred_at`, `producer_service`, `trace_id` — consistent with the implemented envelope's superset.

### 4.3 `OutboxEvent` (storage envelope, `/backend/event_outbox.py`)

The `event_outbox` table/KV-store row wraps the canonical event differently — it lifts `aggregate_type`/`aggregate_id` to top-level columns and stores the full canonical event (or a simpler payload dict) in `payload JSONB`. `stage_canonical_event()` derives `event_name` from `legacy_event_name`/`event_name`/`type`/`event_type` (in that precedence order) and `trace_id` from `metadata.correlation_id`/`trace_id`.

---

## 5. THE EVENT CATALOG — DOMAIN SUMMARY

Full per-event detail (aggregate, transition, minimum payload, consumers) lives in `/backend/docs/canon/event-catalog.md`. The table below summarizes event **counts per producer service/domain** as recorded at the time of the Phase 2 capture (counts may be stale — verified total as of 2026-06-15 is 126 rows; see EG-002):

| Domain / Producer Service | Event Count | Representative Events |
|---|---|---|
| `employee-service` | 18 | `EmployeeCreated`, `EmployeeUpdated`, `EmployeeStatusChanged`, `DepartmentCreated/Updated`, `RoleCreated/Updated`, `BusinessUnitCreated/Updated`, `LegalEntityCreated/Updated`, `LocationCreated/Updated`, `CostCenterCreated/Updated`, `GradeBandCreated/Updated`, `JobPositionCreated/Updated` |
| `performance-service` | 16 | `PerformanceReviewCycleCreated/Opened/Closed`, `PerformanceGoalCreated/Submitted/Approved/Rejected`, `PerformanceFeedbackRecorded`, `PerformanceCalibrationCreated/Submitted/Finalized/Rejected`, `PerformancePipCreated/Submitted/Active/Rejected/ProgressUpdated` |
| `engagement-service` | 5 | `EngagementSurveyCreated/Published/Closed`, `EngagementSurveyResponseSubmitted`, `EngagementSurveyResultsAggregated` |
| `attendance-service` | 5 | `AttendanceCaptured`, `AttendanceValidated`, `AttendanceApproved`, `AttendanceLocked`, `AttendancePeriodClosed` |
| `leave-service` | 4 | `LeaveRequestSubmitted/Approved/Rejected/Cancelled` |
| `payroll-service` | 4 | `PayrollDrafted`, `PayrollProcessed`, `PayrollPaid`, `PayrollCancelled` |
| `hiring-service` | 13 | `JobPostingOpened/OnHold/Closed`, `CandidateApplied`, `CandidateStageChanged`, `InterviewScheduled/Completed/Cancelled/NoShow/CalendarSynced`, `CandidateImported`, `LinkedInCandidatesImported`, `CandidateHired` |
| `auth-service` | 7 | `UserAuthenticated`, `SessionRevoked`, `UserProvisioned`, `UserAccountStatusChanged`, `RoleBindingChanged`, `RefreshTokenRotated`, `AuthorizationPolicyUpdated` |
| `notification-service` | 4 | `NotificationQueued/Sent/Failed/Suppressed` |
| `travel-service` | 7 | `TravelRequestCreated/Submitted/Approved/Rejected/Cancelled/Completed`, `TravelItineraryUpdated` |
| `compliance-service` | 8 | `ComplianceSubmissionCreated`, `ComplianceValidationPassed/Failed`, `ComplianceReportGenerated`, `ComplianceSubmitted`, `ComplianceAcknowledged`, `ComplianceSubmissionFailed`, `ComplianceRetryQueued` |
| `decision-service` | 6 | `AnomalyDetected`, `DecisionCardCreated/Acknowledged/Overridden/Dismissed/Expired` |
| `ewa-financial-service` | 9 | `EWARequested/Approved/Disbursed/Rejected`, `AdvanceRequested/Approved/Disbursed/Rejected`, `RepaymentDeductionInjected` |
| `bank-service` | 8 | `DisbursementBatchCreated/Submitted/Confirmed/Failed`, `PaymentConfirmed/Failed`, `ReconciliationCompleted`, `ReconciliationExceptionRaised` |
| `whatsapp-service` | 8 | `WhatsAppIdentityRegistered/Verified/Revoked`, `WhatsAppSessionStarted/Expired`, `WhatsAppMessageReceived/Sent`, `WhatsAppApprovalActioned` |
| `reporting-analytics-service` | 2 | `ReportGenerated`, `AnomalySignalEmitted` |

**RESOLVED (2026-06-15, EG-002):** The registry summary table in `event-catalog.md` was recounted directly. Actual row count is **126**. Prior documentation referenced counts of 143 (from `CANONICAL_EVENT_TYPES` entries in `event_contract.py`, which includes events not yet added to the catalog table) and 119 (Phase 2 count, taken before additional events were added to the table). The catalog's `## Registry summary` header has been updated to reflect 126. For the full per-event detail, see `/backend/docs/canon/event-catalog.md`.

---

## 6. CONSUMERS / READ MODELS

`/backend/docs/canon/read-model-catalog.md` and `read-models.md` define query-optimized projections (e.g. `employee_directory_view`, `attendance_dashboard_view`, `leave_requests_view`, `payroll_summary_view`, `job_posting_directory_view`) with documented **source services** and **source entities**, but the catalog does not specify the mechanism by which these projections are kept in sync with source events (i.e., whether they are recomputed via event consumption, on-demand query-time joins, or a separate ETL/projection job).

`TBD – REQUIRES VERIFICATION`: Whether read models are updated via outbox event consumption (event-driven projection) or via direct/synchronous querying of source-of-truth tables at read time. No dedicated "projection consumer" service or `consume_event`-style handler wired to these read models was found in the files reviewed, aside from `AutomationService.consume_event` (which drives automation rules, not read-model projections) and `OutboxManager.consume_once` (generic consumer dedupe utility used by `automation_service.py`).

---

## 7. BACKGROUND JOBS ARCHITECTURE

### 7.1 Schema (`/backend/deployment/migrations/008_background_jobs_schema.sql`)

```sql
CREATE TABLE IF NOT EXISTS background_jobs (
  tenant_id VARCHAR(80) NOT NULL,
  job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_type VARCHAR(120) NOT NULL,
  payload JSONB NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Scheduled', 'Running', 'Succeeded', 'Failed', 'DeadLettered', 'Cancelled')),
  attempts INTEGER NOT NULL DEFAULT 0,
  scheduled_at TIMESTAMPTZ NOT NULL,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  failure_reason TEXT,
  idempotency_key VARCHAR(160),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_background_jobs_tenant_job UNIQUE (tenant_id, job_id)
);

CREATE TABLE IF NOT EXISTS background_job_failures (
  tenant_id VARCHAR(80) NOT NULL,
  background_job_failure_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID NOT NULL,
  attempt_number INTEGER NOT NULL CHECK (attempt_number >= 1),
  failure_reason TEXT NOT NULL,
  retryable BOOLEAN NOT NULL DEFAULT TRUE,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  recovered_at TIMESTAMPTZ,
  CONSTRAINT fk_background_job_failures_job FOREIGN KEY (tenant_id, job_id)
    REFERENCES background_jobs (tenant_id, job_id) ON UPDATE CASCADE ON DELETE CASCADE
);
```

Status enum: `Scheduled → Running → (Succeeded | Failed | DeadLettered | Cancelled)`. `JobStatus` enum in `/backend/background_jobs.py` matches this exactly.

### 7.2 Runtime model (`/backend/background_jobs.py`, class `BackgroundJobService`)

- Jobs stored in `PersistentKVStore` namespace `jobs` (service `background-jobs`); related namespaces: `job_types`, `job_results`, `job_failures`, `tenant_queue_configs`.
- `register_handler(job_type, handler, max_attempts=None, timeout_seconds=None)` — registers a `job_type → JobHandler` mapping plus default `max_attempts` (default `3`) and `timeout_seconds` (default `1.0`).
- `enqueue_job(...)` — idempotency-checked (`IdempotencyStore.replay_or_conflict` keyed by `idempotency_key` or a fingerprint of `job_type+tenant_id+payload+scheduled_at`). Raises `QUEUE_OVERFLOW` (HTTP 429) if `queued_job_count(tenant) >= TenantJobQueueConfig.max_queued_jobs` (default 500). New jobs are created with `status=Scheduled`.
- `run_due_jobs(now=None, tenant_id=None)` — **polling-based scheduler**: selects all `Scheduled` jobs with `scheduled_at <= now`, sorted by `(scheduled_at, job_id)`, capped per-tenant by `TenantJobQueueConfig.max_due_jobs_per_run` (default 50), then calls `execute_job` for each. `TBD – REQUIRES VERIFICATION`: what external process/cron invokes `run_due_jobs` periodically — no scheduler/cron daemon invocation of this method was found in the files reviewed (e.g., no `apscheduler`, `cron`, or `while True` loop calling it).
- `execute_job(job_id, tenant_id, trace_id=None)`:
  - Sets `status=Running`, `started_at`.
  - Invokes the handler via `run_with_retry(invoke, attempts=max(1, max_attempts - attempts), base_delay=0.001, timeout_seconds=<job_type timeout>, retryable=lambda exc: not isinstance(exc, BackgroundJobError) or exc.status_code >= 500)`.
  - On success: `status=Succeeded`, `last_result` and `job_results` namespace populated.
  - On failure: `attempts += max(1, attempt_counter)`; if `attempts >= max_attempts` → `status=DeadLettered` (`dead_lettered_at` set) and pushed to `DeadLetterQueue.push('background_jobs', job_type, {...}, reason, retryable=not terminal)`; otherwise `status=Failed` (retryable). A `JobFailureRecord` is written to `job_failures` / `background_job_failures` for every failed attempt.

### 7.3 Job types registered (evidence: `/backend/background_jobs.py`)

| Job type | Handler | Max attempts | Purpose |
|---|---|---|---|
| `payroll.run` | `register_payroll_run_handler` | 3 | Runs payroll for a period; optionally generates payslips; stages new canonical events to `EventOutbox` via `_stage_new_events`. |
| `payroll.payslip.generate` | (same registration) | 3 | Generates a single payslip for a payroll record. |
| `leave.balance.recompute` | `register_leave_balance_recompute_handler` | 3 | Recomputes an employee's leave balances. |
| `notification.dispatch` | `register_notification_dispatch_handler` | 3 | Calls `notification_service.ingest_event(event)`. |
| `outbox.dispatch` | `register_outbox_dispatch_handler` | 3 | Calls `EventOutbox.dispatch_pending(...)`, routing matching events to `notification_service.ingest_event` per `EVENT_NOTIFICATION_PLANS`. |
| `reporting.export` | `register_reporting_handlers` (export_handler) | 3 | Generates a report export; stages `ReportingExportGenerated` event to `EventOutbox`. |
| `reporting.schedule.dispatch` | `register_reporting_handlers` (schedule_dispatch_handler) | 3 | Claims due reporting schedules and enqueues `reporting.export` jobs per schedule. |
| `workflow.escalation` | `register_workflow_escalation_handler` | 2 | Scans a workflow's steps for overdue ones (`status='pending' and deadline_at <= now`); stages `WorkflowEscalationReady` event to `EventOutbox` if any found. |
| `expire_overdue_decisions` | `register_decision_expiry_handler` (`/backend/background_jobs_api.py`, S8-G06) | (default) | Sweeps overdue Decision Cards and marks them expired via `decision_api.expire_overdue_decisions()`. Comment notes intended schedule: every 15 minutes. `TBD – REQUIRES VERIFICATION`: actual cron/trigger wiring for this 15-minute schedule. |

### 7.4 Background Jobs API (`/backend/background_jobs_api.py`)

REST surface over `BackgroundJobService`:
- `POST /background-jobs` (or equivalent route) → `enqueue_job`, returns 202.
- `GET /background-jobs/{job_id}` → `get_job`.
- `GET /background-jobs` → `list_jobs` (filterable by `status`).
- `POST /background-jobs/{job_id}/retry` → `retry_job` (only `Failed`/`DeadLettered` → `Scheduled`, returns 202).
- `POST /background-jobs/{job_id}/cancel` → `cancel_job` (terminal jobs cannot be cancelled).

Error codes: `JOB_NOT_FOUND` (404), `UNKNOWN_JOB_TYPE` (422), `FORBIDDEN` (403), `INVALID_JOB_STATE` (409), `TENANT_SCOPE_VIOLATION` (403), `QUEUE_OVERFLOW` (429).

### 7.5 Retry behavior summary

| Mechanism | Retry strategy | Evidence |
|---|---|---|
| `BackgroundJobService.execute_job` | Per-attempt `run_with_retry` with exponential backoff (`base_delay=0.001`, doubling), bounded by `job.max_attempts - job.attempts`; only retries if `not isinstance(exc, BackgroundJobError) or exc.status_code >= 500` | `/backend/background_jobs.py` lines 344-357 |
| Cross-attempt persistence | `attempts` counter persisted on `JobRecord`; terminal when `attempts >= max_attempts` → `DeadLettered` | `/backend/background_jobs.py` lines 378-411 |
| `OutboxManager.dispatch_pending` | `run_with_retry(attempts=3, base_delay=0.01, timeout_seconds=0.5)`; on exhaustion, record `status='failed'` and pushed to `DeadLetterQueue` | `/backend/outbox_system.py` lines 128-187 |
| `EventOutbox.dispatch_pending` | No retry/backoff — single attempt per call; failure increments `failed_attempts` but event remains `pending` (re-attempted on next `dispatch_pending` call, i.e. relies on the polling cadence of `outbox.dispatch` jobs) | `/backend/event_outbox.py` lines 138-167 |
| `run_with_retry` primitive | Exponential backoff: `delay = base_delay * 2^(attempt-1)`; raises last error after exhausting `attempts` | `/backend/resilience.py` lines 649-672 |

---

## 8. AUTOMATION ENGINE (F-013)

Evidence: `/backend/automation_service.py`, `/backend/automation_api.py`, `/backend/automation_contract.py`.

### 8.1 Rule model

An `AutomationRule` (`automation_service.py`) has:
- `trigger`: `{ "event_types": [...canonical dot-case event types...], "source_services": [...optional allowlist...] }`
- `conditions`: list of `{ "field", "operator" (eq/neq/gte/lte/in/contains/exists), "value" }`
- `actions`: list of `{ "kind" (workflow/notify/update), "config": {...} }`
- `execution`: must have `idempotent: true` (enforced/auto-fixed by `automation_contract.ensure_automation_rule_contract`)
- `status`: `Active` / `Disabled`

### 8.2 Trigger model — as implemented: EVENT-TRIGGERED ONLY

`automation_contract.py`'s `_normalize_rule` requires `trigger.event_types` to be a non-empty list of canonical event types (validated via `normalize_event_type`). The QC check `canonical_events_used` requires every trigger event type to contain a `.` (i.e., be in dot-namespace form, e.g. `leave.request.submitted`).

`AutomationService.consume_event(event, trace_id=None)`:
1. Normalizes the incoming event via `ensure_event_contract`.
2. Selects `Active` rules for the event's tenant where `event['event_type'] in rule.trigger['event_types']` AND (no `source_services` allowlist, or the event's `source`/`producer_service` is in it).
3. For each matching rule, calls `_execute_rule` via `OutboxManager.consume_once` (consumer-side idempotency keyed by `automation-rule:{rule_id}` + `event_id`).
4. `_execute_rule` evaluates `_conditions_match(rule.conditions, event)`; if matched, runs each action (`_execute_workflow_action` → `WorkflowService.start_workflow`, `_execute_notify_action`, `_execute_update_action`); records an `AutomationExecution` (status `executed`/`skipped`), audits `automation_rule_executed`, and emits `AutomationRuleExecuted` via `_emit_event`.

**RESOLVED (2026-06-15, EG-003):** Both `automation_contract.py` and `automation_service.py` were read in full. The trigger model is exclusively **event-triggered**. Specifically:

- `_normalize_rule()` in `automation_contract.py` requires `trigger.event_types` — a non-empty list of canonical dot-namespaced event types. No `schedule`, `cron`, `threshold`, or `interval` field is accepted or processed.
- The QC check `canonical_events_used` validates that every trigger event type contains a `.` (i.e., is in dot-namespace form). No alternative trigger kind is validated or normalized.
- `AutomationService.consume_event()` matches active rules by `canonical_event['event_type'] in rule.trigger.get('event_types', [])` — purely event-type matching.
- The `workflow.escalation` and `expire_overdue_decisions` background jobs are time-based sweeps but operate outside the `AutomationRule` contract; they are not scheduled/threshold automation rules.

The prior description of "event-triggered, scheduled, and threshold-triggered" rules in `service-map.md` (automation-service row) is **not supported by the implementation**. Documentation referencing scheduled or threshold-triggered automation rules should be corrected to reflect event-triggered-only support. See EG-003 in `docs/08_reports/BACKEND_GAP_REGISTER.md`.

### 8.3 Relationship to the outbox

`AutomationService` instantiates its own `OutboxManager` (`outbox_system.py`) for: (a) emitting its own lifecycle events (`AutomationRuleCreated`, `AutomationRuleExecuted`) via `_emit_event` → `outbox.enqueue(...)`, and (b) consumer-side dedupe of inbound events via `consume_once`. `TBD – REQUIRES VERIFICATION`: the path by which domain events (e.g., `LeaveRequestSubmitted`) staged in `EventOutbox`/`service_outbox` are delivered to `AutomationService.consume_event` — no direct call from `EventOutbox.dispatch_pending` or `BackgroundJobService` to `AutomationService.consume_event` was found in the files reviewed.

---

## 9. SUMMARY OF UNVERIFIED ITEMS

| # | Item | Status |
|---|---|---|
| 1 | 143 vs 119 events in `event-catalog.md` registry table | RESOLVED (2026-06-15): actual table count is 126; stale counts of 143 and 119 corrected in `event-catalog.md` — see EG-002 in BACKEND_GAP_REGISTER.md |
| 2 | `service_outbox`/`processed_events` SQL tables vs `PersistentKVStore` as the live runtime path | `TBD – REQUIRES VERIFICATION` |
| 3 | Read-model projection update mechanism (event-driven vs query-time) | `TBD – REQUIRES VERIFICATION` |
| 4 | External process/cron invoking `BackgroundJobService.run_due_jobs` | `TBD – REQUIRES VERIFICATION` |
| 5 | 15-minute schedule wiring for `expire_overdue_decisions` | `TBD – REQUIRES VERIFICATION` |
| 6 | Scheduled / threshold-triggered automation rule types | RESOLVED (2026-06-15): both `automation_contract.py` and `automation_service.py` read in full — only event-triggered automations exist; no schedule/threshold/cron trigger type found. See EG-003 in BACKEND_GAP_REGISTER.md |
| 7 | Delivery path from `EventOutbox`/`service_outbox` to `AutomationService.consume_event` | `TBD – REQUIRES VERIFICATION` |
