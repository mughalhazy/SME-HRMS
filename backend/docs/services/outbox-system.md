# outbox-system

Dual-component at-least-once event-delivery infrastructure: stages domain events before they are published, tracks dispatch status, and guarantees idempotent consumer-side processing.

## Scope
- Support infrastructure — not a business domain module.
- Two distinct but complementary components share responsibility:
  - **`OutboxManager`** (`outbox_system.py`) — full-featured per-service outbox with `EventRegistry` contract validation, `IdempotencyStore` deduplication, `DeadLetterQueue` overflow, and `Observability` tracing. Used by services that own canonical events (automation, integration, leave, payroll, attendance, auth, hiring).
  - **`EventOutbox`** (`event_outbox.py`) — lighter-weight low-level outbox backed by `PersistentKVStore`. Used by services with simpler dispatch needs (background-jobs, expense, project).
- Neither component has an HTTP surface — both are imported directly by domain services.
- Underpins the architectural guarantee stated in MASTER BUILD SPEC: no cross-service DB joins; all integration via events.

## OutboxManager — full-featured component

**File:** `outbox_system.py`

### Lifecycle
1. Domain service calls `outbox.enqueue(legacy_event_name, data, ...)` after a successful mutation.
2. `enqueue()` validates the event against `EventRegistry`, wraps it in an `OutboxRecord` with status `pending`, and persists it to the `PersistentKVStore`.
3. A background sweep calls `outbox.dispatch_pending(publisher)`, which iterates all non-dispatched records in insertion order and calls the provided `publisher` callable for each.
4. On success: record status → `dispatched`, dispatch log written, Observability metrics recorded.
5. On failure: record status → `failed`, `attempt_count` incremented, error stored, entry pushed to `DeadLetterQueue`.

### `consume_once()` — idempotent consumer guard
```python
result, was_replay = outbox.consume_once(
    consumer_name='payroll-service:AttendancePeriodClosed',
    event=incoming_event,
    handler=lambda e: process(e),
)
```
- Deduplication key: `{consumer_name}:{event_id}`.
- If the event was already processed, returns the cached result and `was_replay=True` — handler is not called again.
- Uses `IdempotencyStore` (from `resilience.py`) for fingerprint-based replay detection.

### OutboxRecord schema
```yaml
outbox_id: uuid
event_id: uuid
event_type: string       # canonical event type from EventRegistry
tenant_id: string
status: pending | dispatched | failed
source: string           # originating service name
payload: object          # full canonical event envelope
created_at: ISO8601
updated_at: ISO8601
dispatched_at: ISO8601 | null
attempt_count: int
last_error: string | null
last_error_at: ISO8601 | null
metadata: object
```

### Retry behaviour
- `dispatch_pending()` accepts `attempts` (default 3) and a `retryable` predicate.
- Uses `run_with_retry()` from `resilience.py` with `base_delay=0.01s`, `timeout_seconds=0.5`.
- Failed records are retained in the store (status `failed`) and pushed to `DeadLetterQueue` for manual inspection or replay.

---

## EventOutbox — lightweight component

**File:** `event_outbox.py`

### Lifecycle
1. Domain service calls `outbox.stage_event(...)` or `outbox.stage_canonical_event(event)` immediately after a mutation.
2. Event stored with `published_at=None` — marks it as pending.
3. Dispatcher (typically a background sweep) calls `outbox.dispatch_pending(dispatcher)`.
4. On success: `mark_published(event_id)` sets `published_at` timestamp.
5. On failure: `mark_failed(event_id)` increments `failed_attempts`; record remains pending for retry.

### OutboxEvent schema
```yaml
event_id: uuid
tenant_id: string
aggregate_type: string   # e.g. "LeaveRequest", "Expense"
aggregate_id: string
event_name: string
payload: object          # full event envelope
trace_id: string
occurred_at: ISO8601
published_at: ISO8601 | null   # null = still pending
failed_attempts: int
created_at: ISO8601
```

---

## Shared storage
Both components use `PersistentKVStore` (from `persistent_store.py`) with service-scoped namespaces:
- `OutboxManager`: `outbox_records`, `processed_events`, `dispatch_log`
- `EventOutbox`: `event_outbox` (service name: `background-jobs`)

## Dependencies
- `event_contract` — `EventRegistry`, `ensure_event_contract()` (OutboxManager only)
- `persistent_store` — `PersistentKVStore` (both)
- `resilience` — `DeadLetterQueue`, `IdempotencyStore`, `Observability`, `run_with_retry`
- `tenant_support` — `normalize_tenant_id()`, `assert_tenant_access()`

## Services using OutboxManager
`automation_service`, `integration_service`, `leave_service`, `payroll_service`, `services/attendance_service`, `services/auth-service`, `services/hiring_service`

## Services using EventOutbox
`background_jobs`, `expense_service`, `project_service`

## Notes
- The two components are not interchangeable — `OutboxManager` enforces `EventRegistry` contract validation; `EventOutbox` does not. Choose based on whether the service publishes canonical events that must be contract-validated.
- Neither component publishes events itself — that is the responsibility of the injected `publisher` / `dispatcher` callable.
- `OutboxManager.transaction()` helper exposes a joint transaction context over the outbox's three KV stores plus any additional caller-supplied stores, enabling atomic domain-mutation + outbox-enqueue patterns.
