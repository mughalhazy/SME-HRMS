# P30 Event Consistency & Replay Safety Report

## Scope

This pass validates and extends the existing event/outbox backbone introduced in earlier prompts without replacing it. The audit focused on:

- canonical event contract normalization and metadata consistency,
- tenant-safe idempotency and replay behavior,
- outbox retry/failure handling,
- replay-safe downstream consumers in notifications, search, reporting, and integrations,
- supervisor/background-job compatibility with duplicate delivery and reprocessing.

## Findings

### 1. Contract consistency

- Canonical normalization already existed through `event_contract.py`, but replay safety had two notable gaps:
  - idempotency keys were not tenant-scoped, creating a potential cross-tenant collision path,
  - normalized events did not consistently expose D2-style aliases such as `event_name`, `occurred_at`, `producer_service`, and `trace_id`.
- This pass extends the existing contract layer to:
  - scope idempotency dedupe by `tenant_id + event_type + idempotency_key`,
  - propagate `tenant_id` into event payloads when absent,
  - reject payloads where `data.tenant_id` conflicts with the envelope tenant,
  - expose compatibility aliases required by downstream D2-oriented readers.

### 2. Outbox integrity

- The repo’s Python domain services already route writes through `OutboxManager`, which preserves retry status, dead-letter evidence, and transactional staging hooks.
- The main outlier found during the audit was `auth-service`, which had an internal `_emit_event` helper bypassing the outbox and appending directly to `self.events`.
- This pass patches `auth-service` to enqueue and dispatch through the existing outbox instead of writing directly, removing a non-transactional event path.

### 3. Consumer idempotency and replay safety

- `integration-service` already consumed events through `OutboxManager.consume_once`, making webhook scheduling replay-safe.
- `search-service` had event-level dedupe but did not normalize/validate all inbound events against the canonical contract first.
- `notification-service` accepted canonical envelopes but did not persist per-event consumption results, so duplicate delivery could create duplicate messages.
- `reporting-analytics` accepted raw events without contract validation or explicit tenant rejection on event ingress.

This pass extends those consumers to:

- normalize inbound events through `ensure_event_contract`,
- persist processed-event markers where needed,
- replay previously processed results instead of re-enqueueing duplicate work,
- reject cross-tenant event ingestion into tenant-scoped reporting projections.

## Changes made

### Event contract hardening

- tenant-scoped idempotency key registration,
- D2-compatible aliases on normalized events,
- payload tenant propagation and tenant mismatch rejection.

### Producer hardening

- `auth-service` now emits through the existing outbox manager instead of direct list writes.

### Consumer hardening

- `notification-service` now records processed event/message mappings and replays them idempotently,
- `search-service` now validates inbound events against the canonical contract before scheduling reindex jobs,
- `reporting-analytics` now validates inbound events, dedupes replays, and rejects cross-tenant event ingestion.

## Replay-safety QC summary

- **all_events_follow_D2:** pass after contract alias normalization and tenant propagation.
- **all_consumers_are_idempotent:** pass for the audited downstream consumers after notification/reporting/search hardening.
- **replay_does_not_corrupt_state:** pass via duplicate-event tests on notification and reporting consumers.
- **outbox_has_no_loss_paths:** pass for the audited Python services after removing the auth direct-write path.
- **tenant_context_is_preserved:** pass after tenant-scoped idempotency and payload tenant enforcement.

## Residual notes

- This pass intentionally extends the current event/outbox design and does not replace transport, storage, or service boundaries.
- The report is anchored to the canonical service/read-model docs and the existing outbox/job/supervisor architecture already present in the repo.
