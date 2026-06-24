# governance-service

Human-in-the-loop gate enforcement: policy-constrained approval and override controls for payroll finalization, compliance submission, anomaly acknowledgement, and decision card lifecycle — aligned to `docs/canon/decision-system.md`.

## Scope
- Support service (`governance-service`, `services/governance/service.py`, 97 lines).
- No HTTP surface — imported directly by payroll / compliance orchestration and test suites.
- Provides policy-enforced state transitions with mandatory human-actor attribution and audit-trail logging.
- Raises `GovernanceError` (subclass of `ValueError`) when an action violates policy constraints — callers must handle these before proceeding.


## Core operations

### Payroll approval gate
```python
svc = GovernanceService()

# 1 — create a pending approval record
approval = svc.create_payroll_approval(user="admin@co", reason="end-of-month run")
# approval: {status: "pending", created_at: ..., updated_at: ...}

# 2 — review: approved or rejected
approval = svc.review_payroll_approval(
    approval, user="finance-lead@co", decision="approved", reason="all checks passed"
)
# raises GovernanceError if status != "pending" or decision not in {approved, rejected}
```

### Compliance submission gate
```python
result = svc.submit_compliance(approval, user="compliance-officer@co")
# raises GovernanceError if approval.status != "approved"
# returns: {status: "submitted"}
```

### Anomaly override
```python
anomaly = svc.override_anomaly(
    anomaly_record, user="hr-admin@co", reason="confirmed manual correction applied"
)
# raises GovernanceError if reason is blank
# mutates anomaly: adds override=True, override_reason, override_user, override_at
```

### Decision card lifecycle
```python
# update — any non-expired card
card = svc.update_decision(card, user="manager@co", reason="context updated", severity="HIGH")
# raises GovernanceError if lifecycle_state == "expire"

# expire — terminal state; expired cards are immutable
card = svc.expire_decision(card, user="manager@co", reason="superseded by new data")
```

## `GovernanceAction` — audit record
```yaml
user: string       # actor identity (email or user_id)
action: string     # e.g. "payroll_approval_approved", "anomaly_override", "decision_expired"
timestamp: ISO8601 UTC
reason: string     # mandatory human-supplied justification
```

All operations append a `GovernanceAction` to `self.audit_trail` — an in-memory `list[GovernanceAction]` on the `GovernanceService` instance.

## Policy constraints enforced

| Operation | Guard |
|---|---|
| `review_payroll_approval()` | status must be `pending`; decision must be `approved` or `rejected` |
| `submit_compliance()` | approval status must be `approved` |
| `override_anomaly()` | reason must be non-empty |
| `update_decision()` | decision card `lifecycle_state` must not be `expire` |
| `expire_decision()` | none — any non-expired card may be expired |

## Decision card lifecycle states
- `update` — card has been amended (set by `update_decision()`)
- `expire` — card is terminal and immutable (set by `expire_decision()`)

> NOTE (G50): This section covers `lifecycle_state` values only (`update | expire`). The canonical `lifecycle_state` enum also includes `create` and `resolve`. The canonical Decision Card `status` enum (`active | resolved | expired`) is defined in `docs/canon/decision-system.md`.

## Events published / subscribed
- None — callers must emit their own audit records via `emit_audit_record()` after each operation.

## Dependencies
- None — pure Python; no I/O, no external service calls.
- `docs/canon/decision-system.md` is the canonical authority this service enforces.

## Notes
- `audit_trail` is in-memory per instance — it is **not** persisted to `audit-service` automatically. Callers that need durable governance records must call `emit_audit_record()` from `audit_service.service` separately after each `GovernanceService` operation.
- `governance` feature is ENTERPRISE-tier-only per `ExperienceLayerService` — this service should not be reachable for SMB/MID tenants without the feature flag being active.
- `GovernanceError` messages are snake_case identifiers (e.g. `"payroll_approval_must_be_pending"`) — callers should map these to user-facing messages using `error-registry.md` conventions or a UI translation layer.
