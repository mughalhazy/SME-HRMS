# Mobile Layer

Low-bandwidth, decision-first mobile gateway. An optimization layer between the mobile client and backend services — not a separate service.

## Scope

- Provides compact, action-oriented responses for mobile clients on unstable/low-bandwidth connections.
- Returns only fields required for the current interaction step; defers non-critical data to follow-up calls.
- In-memory caching layer to reduce redundant payloads on reconnect.
- Decision-card ordering: surfaces critical/high severity items first.
- Does NOT own data — reads from domain services via their canonical APIs.
- Does NOT replace domain service endpoints — mobile clients may call domain APIs directly for complex operations.

## Implementation files

| Component | File |
|---|---|
| MobileGatewayService | `services/mobile_gateway.py` (211 lines) |
| Mobile API contracts | `mobile/contracts.py` |
| Mobile response builders | `mobile/contracts.py → build_mobile_response()` |

## API endpoints (`/api/v1/mobile`)

| Path | Purpose |
|---|---|
| `GET /api/v1/mobile/dashboard` | Compact manager dashboard: Decision Cards, payroll status, pending approvals |
| `GET /api/v1/mobile/employee/{id}` | Employee summary (compact) |
| `GET /api/v1/mobile/payslip/{id}` | Payslip compact view |
| `POST /api/v1/mobile/action` | Execute a quick action (approve, reject, acknowledge) |

## Response model

```json
{
  "cards": [
    {
      "id": "...",
      "type": "decision | alert | task",
      "severity": "critical | high | medium | low",
      "title": "...",
      "why": "...",
      "action": "...",
      "due_at": "..."
    }
  ],
  "pagination": { "cursor": "...", "next_cursor": "..." }
}
```

Cards are sorted: `critical → high → medium → low`, then by `due_at`.

## Design constraints (from P5 — Mobile-first / Poor Employee Access)

- **Compact requests**: minimal required context in each request.
- **Minimal payload**: only fields needed for the current step.
- **Offline tolerance**: clients should degrade gracefully if mobile gateway is unreachable.
- **No dense dashboards**: action-first layout — show what needs to be done, not raw data tables.
- **Page size capped at 25**: prevents large payloads on mobile connections.
- **Session resume**: in-memory cache allows efficient reconnect without re-fetching all state.

## Interaction with decision-service

The mobile gateway composes Decision Cards from the decision-service `decision_cards_view` read model. Cards are re-sorted and compressed for mobile rendering. No new anomaly detection runs here — it reads pre-computed signals.

## Notes

- Mobile gateway uses `resilience.new_trace_id()` for distributed tracing across requests.
- `mobile/contracts.py` defines the stable API contract for mobile clients — endpoints and response schemas here are versioned separately from domain service APIs.
- GPS-based attendance capture is handled by mobile client sending coordinates to `attendance-service` directly (not via mobile gateway).
