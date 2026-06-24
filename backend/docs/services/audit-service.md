# audit-service

Infrastructure-layer immutable audit trail — append-only JSONL log with cursor-paginated query API, consumed by every domain service that mutates sensitive data.

## Scope
- Support service — not a business domain module.
- Records every sensitive mutation (before/after state, actor, entity, action, trace_id, source service) to a tenant-scoped, append-only JSONL log.
- Provides a query API for compliance, HR Ops, and security review use cases.
- Does NOT own business logic — it is a write-once ledger called by domain services.
- Referenced in MASTER BUILD SPEC §19 as a hard requirement; depended on by payroll, compliance, bank, helpdesk, hiring, expense, performance, leave, integration, and travel services.

## HTTP surface (`/api/v1`)
- `GET /api/v1/audit/records?tenant_id=&actor_id=&actor_type=&entity=&entity_id=&action=&timestamp_from=&timestamp_to=&limit=&cursor=` — paginated query of audit records

All write operations are internal — domain services call `emit_audit_record()` directly; there is no public POST endpoint for audit records.

## AuditRecord schema
```yaml
audit_id: uuid          # unique per record
tenant_id: string       # normalized, required
actor:
  id: string            # user_id, service name, or "system"
  type: string          # "user" | "system" | "service"
  role: string | null
  department_id: string | null
action: string          # e.g. "payroll_finalized", "leave_approved", "ticket_assigned"
entity: string          # entity type, e.g. "PayrollRecord", "LeaveRequest"
entity_id: string
before: object          # serialized state before mutation (empty dict if creation)
after: object           # serialized state after mutation (empty dict if deletion)
timestamp: ISO8601 UTC
trace_id: string        # correlates to the originating API request
source: object          # {service: "payroll-service", ...} — injected by emit_audit_record()
```

## Storage
- **Persistence:** append-only JSONL file per process. Path resolved from `HRMS_AUDIT_LOG_PATH` env var; defaults to `{tempdir}/sme-hrms/audit-records.jsonl`.
- **Thread safety:** `RLock` guards both append and read operations — safe for multi-threaded single-process deployments.
- **Immutability:** records are only ever appended, never updated or deleted.
- **Serialization:** `_normalize_mapping()` / `_serialize_value()` handle arbitrary Python objects (dataclasses, Enums, datetime, Decimal, Path, objects with `to_dict()` or `__dict__`) — domain services can pass domain objects directly without pre-serializing.

## Pagination
- Cursor-based: cursor is a base64url-encoded integer offset into the sorted result set.
- Results sorted by `(timestamp DESC, audit_id DESC)` — most recent first.
- `limit` range: 1–100 (default 25). `AuditQueryError` raised for out-of-range values.
- `tenant_id` is required on every query; cross-tenant reads are structurally prevented.

## Integration pattern — `emit_audit_record()`
Domain services call the module-level helper rather than instantiating `AuditService` directly:

```python
from audit_service.service import emit_audit_record

emit_audit_record(
    service_name='payroll-service',
    tenant_id=tenant_id,
    actor={'id': actor_id, 'type': 'user', 'role': 'PayrollAdmin'},
    action='payroll_finalized',
    entity='PayrollRecord',
    entity_id=payroll_run_id,
    before=before_state,
    after=after_state,
    trace_id=trace_id,
)
```
`get_audit_service()` returns a process-singleton `AuditService` instance, creating it on first call.

## Owned entities
- `AuditRecord`
- `AuditActor`

## Events published
- None.

## Events subscribed
- None.

## Read models produced
- None — all reads go directly against the JSONL store via the query API.

## Dependencies
- `tenant_support` — `normalize_tenant_id()` enforced on every record write and query.
- `persistent_store` is **not** used — storage is file-based JSONL, not the KV store.

## Notes
- In a production deployment `HRMS_AUDIT_LOG_PATH` should point to immutable or write-once storage (e.g., an append-only S3 bucket, WORM disk volume) to preserve tamper-evidence guarantees.
- The service is intentionally free of external dependencies so it cannot fail due to DB or network issues during a mutation that already succeeded.
- `AuditQueryError` (subclass of `ValueError`) is used for all query-time validation failures; the API layer converts it to a 422 response.
