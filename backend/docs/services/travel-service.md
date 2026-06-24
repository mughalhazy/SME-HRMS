# travel-service

Employee travel request management: draft, submit, approve/reject, book itinerary segments, cancel, and complete — with full workflow integration, audit trail, and event emission at every state transition.

## Scope
- Add-on service (`travel-service`, `travel_service.py` + `travel_api.py`).
- Manages the full travel request lifecycle from employee draft through travel-desk completion.
- Reuses `employee-service` snapshots (`EmployeeSnapshot`) for traveler and manager references — does not own employee data.
- Routes approvals through the centralized `workflow-service`; does not implement approval logic directly.
- Every state mutation is audited via `audit-service` and emits a canonical event via the outbox pipeline.
- Noted as PLANNED in some older registry docs, but `travel_service.py` + `travel_api.py` are both fully implemented and importable (per gap S8-G04; BUILD SPEC §10 corrected).

## HTTP surface (`/api/v1`)
- `POST /api/v1/travel/requests` — create a draft travel request
- `POST /api/v1/travel/requests/{travel_request_id}/submit` — submit for approval
- `POST /api/v1/travel/requests/{travel_request_id}/approve` — manager/travel-desk approve
- `POST /api/v1/travel/requests/{travel_request_id}/reject` — manager/travel-desk reject
- `PUT /api/v1/travel/requests/{travel_request_id}/itinerary` — add/update booking segments (Approved or Booked only)
- `POST /api/v1/travel/requests/{travel_request_id}/cancel` — cancel (any non-terminal state)
- `POST /api/v1/travel/requests/{travel_request_id}/complete` — mark Booked request completed
- `GET /api/v1/travel/requests/{travel_request_id}` — retrieve single request
- `GET /api/v1/travel/requests?employee_id=&status=&limit=&cursor=` — list requests

## Request lifecycle

```
Draft ──submit──▶ Submitted ──approve──▶ Approved ──itinerary──▶ Booked ──complete──▶ Completed
                      │
                      └──reject──▶ Rejected
Any non-terminal state ──cancel──▶ Cancelled
```

State transitions are enforced by guard checks before mutation; conflict errors (409) are returned for invalid transitions.

## Owned entities

### `TravelRequest`
```yaml
travel_request_id: uuid
tenant_id: string
employee_id: string
manager_employee_id: string
purpose: string
trip_type: string           # e.g. "domestic", "international"
origin_city / destination_city: string
start_date / end_date: date
estimated_cost: float
currency: string
status: Draft | Submitted | Approved | Rejected | Booked | Completed | Cancelled
workflow_id: string | null  # set on submit, references workflow-service instance
itinerary_segments: list[ItinerarySegment]
notes: string | null
submitted_at / decision_at / approved_at / booked_at / completed_at / cancelled_at: datetime | null
created_at / updated_at: datetime
```

### `ItinerarySegment`
Booking detail added after approval via `PUT .../itinerary`. Fields include segment type (flight/hotel/ground), dates, booking references, and cost.

### `EmployeeSnapshot`
Cached employee projection used for traveler and manager lookups — avoids live employee-service calls on every request read.

## Events published
- `TravelRequestCreated`
- `TravelRequestSubmitted`
- `TravelRequestApproved`
- `TravelRequestRejected`
- `TravelItineraryUpdated`
- `TravelRequestCancelled`
- `TravelRequestCompleted`

## Events subscribed
- `EmployeeCreated`, `EmployeeUpdated`, `EmployeeStatusChanged` — updates `EmployeeSnapshot` cache

## Read models produced
- `travel_requests_view`
- Enriches travel-operations inboxes and employee travel-history projections

## Supported workflows
- `travel_request` — registered with `workflow-service` via `_register_workflows()` on service init

## Dependencies
- `employee-service` — employee existence, department context, reporting-line lookup (via `_require_employee()`)
- `workflow-service` — approval routing; decision resolved via `_resolve_workflow()` / `_resolve_workflow_decision_result()`
- `audit-service` — every state transition logged via `_audit()` with actor, before/after state, trace_id
- `notification-service` — traveler, manager, and travel-desk notifications at key lifecycle events
- `outbox_system` (`OutboxManager`) — canonical event staging and dispatch via `_emit()`
- `auth-service` — access control on management endpoints

## Notes
- `decide_request()` maps workflow engine outcomes (`approved` / `rejected` / multi-step intermediate) to request status — intermediate approvals leave status as `Submitted` pending next approver.
- `update_itinerary()` (which transitions to `Booked`) requires status `Approved` or `Booked`; segments are validated against `start_date`/`end_date` bounds.
- `cancel_request()` is blocked on terminal states (`Completed`, `Cancelled`, `Rejected`) — returns 409 for those.
- `register_employee_profile()` allows employee-service events to pre-populate the `EmployeeSnapshot` cache before a travel request is created.
