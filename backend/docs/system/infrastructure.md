# Infrastructure Layer

Platform-level modules that underpin all business services. These are not business services — they have no HTTP surface and own no domain data. They are referenced by (not composed into) domain services.

## Modules

### chaos_engine.py (497 lines)
Fault injection and chaos testing framework.
- Injects controlled failures (latency, errors, service unavailability) into service calls.
- Used in test/staging environments to validate resilience patterns.
- Controlled by `ChaosProfile` config — never active in production unless explicitly enabled.
- Referenced by integration tests and `resilience.py`.

### resilience.py (672 lines)
Resilience patterns library: circuit breakers, retries, bulkheads, timeouts.
- `CircuitBreaker` — opens after N failures, half-opens on probe, closes on success.
- `RetryPolicy` — configurable exponential backoff with jitter.
- `Bulkhead` — concurrency limits per dependency.
- `new_trace_id()` — generates unique trace IDs for distributed tracing.
- Imported by all service API modules and integration adapters.

### outbox_system.py
Outbox pattern implementation for reliable event delivery.
- `OutboxManager` — writes events to an outbox store before acknowledging the originating transaction.
- Background relay picks up undelivered events and dispatches to the event bus.
- Guarantees at-least-once delivery. Consumers must be idempotent.
- All canonical domain events (listed in `docs/canon/event-catalog.md`) are dispatched via outbox.

### background_jobs.py
Background job scheduler and executor.
- Manages scheduled tasks: cron-style and deferred one-off jobs.
- Consumed by `automation-service` for schedule-triggered automations.
- Consumed by `supervisor_engine.py` for health polling jobs.
- Job failures are logged and surfaced to SupervisorEngine for recovery decisions.

### persistent_store.py
Thin persistence abstraction layer (SQLite default; PostgreSQL via `HRMS_DATABASE_URL`).
- `PersistentKVStore[K, V]` — generic typed mapping backed by SQLite WAL or PostgreSQL.
- Serialises values with a safe JSON type-tag codec (`_encode`/`_decode`) supporting: `uuid.UUID`, `datetime`, `date`, `time`, `Decimal`, `bytes`, `Enum`, `dataclass`, `dict`, `tuple`, `set`, `list`. No pickle.
- `transaction(*stores)` — multi-store atomic block using `copy.deepcopy` rollback on failure.
- Memory-URI mode (`file:…?mode=memory`) for ephemeral test/validation instances.

### structured_logging.py
Structured JSON logging for all services and the gateway.
- `StructuredJSONFormatter` — emits one JSON line per log record with `ts`, `level`, `logger`, `message`, `correlation_id`, and any extra fields.
- `configure_logging(service, level)` — replaces root handler with the JSON formatter; reads `LOG_LEVEL` env var.
- `set_correlation_id(cid)` / `get_correlation_id()` — propagate trace IDs via `contextvars.ContextVar` across async and thread boundaries.

### rate_limiting.py
In-process sliding window rate limiter.
- `SlidingWindowRateLimiter(requests_per_window, window_seconds)` — thread-safe per-key bucket.
- `check(key) → RateLimitResult` — returns `allowed`, `limit`, `remaining`, `reset_at`.
- `purge_expired()` — cleans up idle buckets to prevent unbounded memory growth.
- Used by `docker/api_gateway_service.py`; key = client IP (from `X-Forwarded-For` or ASGI scope).

### jwt_utils.py
Stateless HS256 JWT verification shared between gateway and services.
- `verify_hs256_jwt(token, secret, *, audience, issuer) → dict | None` — validates signature, `exp`, `nbf`, `aud`, `iss`; returns claims or `None` on any failure.
- Token format: standard RFC 7519 HS256 (base64url header.payload.signature, no padding).

### secrets_config.py
Startup secrets validation and `.env` loading.
- `require_secrets(*names, fatal=True)` — checks env vars are present and non-empty; exits with clear error if `fatal=True`.
- Auto-loads `.env` via `python-dotenv` (built-in fallback parser if dotenv unavailable).
- Import path: `ENV_FILE` env var overrides the default `.env` filename.

### supervisor_engine.py (749 lines)
Infrastructure incident supervisor. See `docs/services/automation-service.md §Sub-module: SupervisorEngine` for full description.

## Dependency direction

```
Business services
      ↓
  resilience.py / outbox_system.py / background_jobs.py / persistent_store.py
      ↓
  (DB / message bus / external systems)
```

`chaos_engine.py` and `supervisor_engine.py` are test/ops tooling that sit alongside this stack, not inside it.

## Rules

- No domain service may depend on another domain service's DB directly. Use events and read models.
- All external calls (integrations, government adapters) must go through `resilience.py` retry/circuit-breaker wrappers.
- All cross-service events must be dispatched via `outbox_system.py` — no fire-and-forget in-process calls.

- `chaos_engine.py` must be gated by environment flag; it must never inject failures in production.
