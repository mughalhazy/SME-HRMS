# integration-service

Centralized outbound webhook dispatch: register tenant-scoped endpoints, fan canonical domain events out to subscribers, sign payloads, track every delivery attempt, and replay failures — all without coupling domain services to partner-specific logic.

## Scope
- Add-on service (`integration-service`, `integration_service.py` + `integration_api.py`).
- Manages webhook endpoint lifecycle (create, update, delete, list).
- Consumes all canonical D2-aligned events from the outbox pipeline and fans them out to matching subscriber endpoints.
- Signs every outbound payload with HMAC-SHA256 for receiver authenticity verification.
- Tracks per-delivery attempt detail (request headers, response status, duration, errors) for operator visibility and replay.
- Keeps domain services free of partner-specific dispatch logic — they emit events; integration-service handles external delivery.
- Current implementation is **webhook-only** — OAuth connect flows and API-key partner auth are UI chrome (BG-026, not yet backed).

## HTTP surface (`/api/v1`)
- `POST /api/v1/integrations/webhooks` — register a new webhook endpoint
- `PATCH /api/v1/integrations/webhooks/{webhook_id}` — update URL, events, description, or status
- `DELETE /api/v1/integrations/webhooks/{webhook_id}` — soft-delete (sets `deleted_at`)
- `GET /api/v1/integrations/webhooks?status=&limit=&cursor=` — list tenant webhooks
- `GET /api/v1/integrations/deliveries?webhook_id=&delivery_status=&event_type=&limit=&cursor=` — list delivery attempts
- `POST /api/v1/integrations/deliveries/{delivery_id}/replay` — re-attempt a failed delivery

## Owned entities

### `WebhookEndpoint`
```yaml
webhook_id: uuid
tenant_id: string
target_url: string          # must use https (or http for localhost in dev)
subscribed_events: list[string]   # canonical event type names from event-catalog.md
description: string | null
status: active | disabled
secret_ciphertext: string   # sealed by _SecretSealer (HMAC-SHA256 + XOR; key from HRMS_WEBHOOK_MASTER_KEY)
secret_fingerprint: string
signature_algorithm: "hmac-sha256"
signature_header: string    # header name sent on outbound requests (default: X-HRMS-Signature)
max_attempts: int
retry_backoff_seconds: list[int]
last_delivery_status: string | null
consecutive_failures: int
total_deliveries: int
created_at / updated_at / deleted_at: ISO8601
```

### `WebhookDelivery`
```yaml
delivery_id: uuid
tenant_id / webhook_id / event_id / event_type / source: string
target_url: string
payload: object             # full canonical event envelope
status: pending | delivered | failed | dead_lettered
attempt_count: int
last_http_status: int | null
last_error: string | null
dead_lettered_at / next_retry_at: ISO8601 | null
background_job_id: string | null
replay_of_delivery_id: string | null   # set on replayed deliveries
created_at / updated_at: ISO8601
```

### `WebhookDeliveryAttempt`
Full per-attempt log including request headers, request body, response status, response body, error message, duration_ms, and retryability flag.

## Payload signing
Every outbound request includes an HMAC-SHA256 signature over the serialized payload:
- Header sent: value of `signature_header` (default `X-HRMS-Signature`).
- MAC input: UTF-8 encoded JSON body.
- Key: derived from `HRMS_WEBHOOK_MASTER_KEY` env var (falls back to a dev-only constant — override in all deployed environments).
- `_SecretSealer` stores webhook secrets as sealed ciphertexts (XOR stream cipher + HMAC MAC) — plaintext secret is never written to the KV store.

## Event fan-out flow
1. Canonical event arrives from the outbox pipeline via `consume_event(payload)`.
2. `_subscriptions_for(tenant_id, event_type)` finds all active `WebhookEndpoint` records subscribed to that event type.
3. For each matching endpoint: a `WebhookDelivery` record is created and a background job queued (`integration.webhook.deliver`).
4. `dispatch_delivery()` executes the HTTP call, records the attempt, updates delivery status, and handles retry scheduling.
5. After max attempts: delivery is marked `dead_lettered` and pushed to `DeadLetterQueue` for operator replay.

## Authorization capabilities
- Webhook management (register, update, delete): Admin role only.
- Delivery history and replay: Admin role only.

## Events published
- None — integration-service is infrastructure; it does not emit canonical domain events.

## Events subscribed
- All canonical business events listed in `docs/canon/event-catalog.md` (filtered at dispatch time by each webhook's `subscribed_events` list).

## Read models produced
- `integration_delivery_view` — delivery history and status per webhook endpoint.

## Dependencies
- `audit-service` — logs all webhook management operations (create/update/delete) with before/after state.
- `background_jobs` (`BackgroundJobService`) — queues and executes delivery jobs asynchronously.
- `outbox_system` (`OutboxManager`) — stages events for the service's own internal operations.
- `event_contract` (`EventRegistry`) — validates canonical event envelopes on `consume_event()`.
- `resilience` — `DeadLetterQueue`, `Observability`, `run_with_retry`.
- `auth-service` — authorization for privileged management and replay operations.

## Notes
- `target_url` must use `https` for non-localhost targets; `http` is permitted only for `localhost`/`127.0.0.1` (enforced by `_validate_target_url()`).
- Secrets are validated with `hmac.compare_digest()` to prevent timing attacks.
- `replay_failed_delivery()` creates a new `WebhookDelivery` record with `replay_of_delivery_id` set rather than mutating the original — preserves delivery history.
