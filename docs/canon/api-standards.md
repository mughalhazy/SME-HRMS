# API Standards

This document defines canonical HTTP API standards for SME-HRMS services and the shared API gateway.

## 1) Base path and routing

### Route namespace
- All public routes are versioned under `/api/v1`.
- Service-specific route groups align to the API gateway registry:
  - `/api/v1/employees`, `/api/v1/departments`, `/api/v1/roles`, `/api/v1/performance-reviews`
  - `/api/v1/attendance`
  - `/api/v1/leave`
  - `/api/v1/payroll`
  - `/api/v1/hiring`
  - `/api/v1/auth`
  - `/api/v1/notifications`

### Resource naming
- Use nouns, not verbs, for resource paths.
- Use lowercase kebab-case for path segments.
- Use snake_case for query-parameter names to match the current canonical docs.
- Keep nesting shallow; favor resource IDs over deeply nested paths.

Examples:
- `GET /api/v1/employees`
- `GET /api/v1/employees/{employee_id}`
- `GET /api/v1/leave/requests?employee_id=&status=`
- `POST /api/v1/hiring/candidates/{candidate_id}/mark-hired`

## 2) HTTP methods

- `GET`: read-only retrieval.
- `POST`: create a resource or invoke a state transition/action.
- `PUT`: full replacement when supported.
- `PATCH`: partial update.
- `DELETE`: remove or revoke a resource where hard deletion is allowed.

### Action-style subresources
State transitions that are not plain partial updates may use explicit action subpaths on a resource.

Examples:
- `POST /api/v1/leave/requests/{leave_request_id}/submit`
- `POST /api/v1/attendance/records/{attendance_id}/approve`
- `POST /api/v1/payroll/records/{payroll_record_id}/mark-paid`

## 3) Request and response envelopes

### Success envelope
List endpoints return:

```json
{
  "data": [],
  "page": {
    "next_cursor": null,
    "has_next": false,
    "limit": 25
  },
  "meta": {
    "trace_id": "9f43a8f6ad2b4db9"
  }
}
```

Single-resource endpoints return:

```json
{
  "data": {},
  "meta": {
    "trace_id": "9f43a8f6ad2b4db9"
  }
}
```

### Error envelope
All non-2xx responses use:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more fields are invalid.",
    "details": [
      {
        "field": "email",
        "reason": "must be a valid email address"
      }
    ],
    "trace_id": "9f43a8f6ad2b4db9"
  }
}
```

### Envelope rules
- `trace_id` is required on all responses.
- `details` is optional and reserved for structured validation or domain-conflict information.
- APIs must not leak stack traces, SQL, provider secrets, or raw credential artifacts.

## 4) Status codes

### Success
- `200 OK`: successful read/update/action with body.
- `201 Created`: successful resource creation.
- `202 Accepted`: accepted for asynchronous processing.
- `204 No Content`: successful request with no body.

### Client errors
- `400 Bad Request`: malformed request shape.
- `401 Unauthorized`: missing or invalid authentication.
- `403 Forbidden`: authenticated but not authorized.
- `404 Not Found`: resource does not exist.
- `409 Conflict`: unique or state conflict.
- `422 Unprocessable Entity`: validation or business rule failure.
- `429 Too Many Requests`: rate limit exceeded.

### Server and dependency errors
- `500 Internal Server Error`: unexpected service failure.
- `502 Bad Gateway`: upstream dependency returned an invalid response.
- `503 Service Unavailable`: temporary outage or circuit open.
- `504 Gateway Timeout`: upstream dependency timeout.

## 5) Pagination, filtering, and sorting

### Pagination
- Cursor pagination is the default for list endpoints.
- Supported parameters:
  - `limit` default `25`, max `100`
  - `cursor` opaque continuation token

### Filtering
- Use exact, documented query parameters such as `status`, `department_id`, `employee_id`, `period_start`, `period_end`.
- Use `_from` and `_to` suffixes for range boundaries.

Examples:
- `GET /api/v1/attendance/records?employee_id=...&attendance_date_from=2026-03-01&attendance_date_to=2026-03-31`
- `GET /api/v1/payroll/records?employee_id=...&pay_period_start=2026-03-01&pay_period_end=2026-03-31`

### Sorting
- Use `sort` with comma-separated field names.
- Prefix descending fields with `-`.
- Sort order must be deterministic and documented per endpoint.

## 6) Validation and idempotency

### Validation
- Validate enums and state transitions against canonical domain rules.
- Return `422` for business-rule violations such as invalid workflow transitions.
- Return `409` for duplicates or optimistic-concurrency conflicts.

### Idempotency
- Create or action endpoints that may be retried by clients should accept `Idempotency-Key`.
- Servers must persist idempotency results long enough to protect against duplicate processing for payroll runs, candidate imports, and notification sends.

## 7) Authentication and authorization

### Authentication
- Use bearer tokens in `Authorization: Bearer <token>`.
- All endpoints are authenticated by default unless explicitly public.
- Validate signature, issuer, audience, expiry, and not-before claims.

### Authorization
- Enforce both capability and scope checks.
- Return `401` for invalid credentials and `403` for denied capabilities/scope.
- Service-to-service calls use service principals with scoped capabilities.

## 8) Observability and correlation

- Accept and propagate `X-Trace-Id` when provided; otherwise generate one.
- Include `trace_id` in response envelopes and structured logs.
- Emit audit records for privileged writes, approvals, payroll actions, access changes, and notification preference changes.

## 9) Versioning and compatibility

### Strategy
- Use major versions in the URL: `/api/v{major}`.
- `v1` is the current canonical version in this repository.

### Compatibility rules
- Backward-compatible additive changes are allowed within the same major version.
- Breaking changes require a new major version.
- Read models and event payloads must be versioned independently when contracts change.

### Deprecation
- Signal deprecation with headers when applicable:
  - `Deprecation: true`
  - `Sunset: <HTTP-date>`
- Provide migration guidance before removal.

## 10) Domain-event alignment

- APIs that change canonical workflow state must publish the corresponding domain event from `docs/canon/event-catalog.md` after a successful commit.
- APIs that invoke asynchronous integrations must surface `202 Accepted` when completion occurs out of band.
- Event-producing endpoints should document the resulting state transition and emitted event names.
