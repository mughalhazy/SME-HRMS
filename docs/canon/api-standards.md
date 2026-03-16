# API Standards

This document defines canonical standards for all HTTP APIs in this repository.

## 1) REST Naming

### Resource-oriented URLs
- Use **nouns** for resource names, not verbs.
- Use **plural** resource names.
- Use lowercase and hyphens for path segments.
- Keep nesting shallow (prefer 1-2 levels).

Examples:
- `GET /employees`
- `GET /employees/{employeeId}`
- `POST /employees`
- `PATCH /employees/{employeeId}`
- `GET /departments/{departmentId}/employees`

### HTTP methods
- `GET`: Read (safe, idempotent)
- `POST`: Create
- `PUT`: Replace full resource (idempotent)
- `PATCH`: Partial update
- `DELETE`: Remove resource (idempotent)

### Query parameters
Use query parameters for filtering, sorting, field selection, and pagination.

Examples:
- `GET /employees?status=active&departmentId=dep_123`
- `GET /employees?sort=-createdAt,name`
- `GET /employees?fields=id,name,email`

## 2) Status Codes

Use standard HTTP status codes consistently.

### Success
- `200 OK`: Successful read/update/delete request returning a body.
- `201 Created`: Resource created successfully.
- `202 Accepted`: Accepted for asynchronous processing.
- `204 No Content`: Successful request with no response body.

### Client errors
- `400 Bad Request`: Invalid request syntax/shape.
- `401 Unauthorized`: Missing/invalid authentication credentials.
- `403 Forbidden`: Authenticated but not allowed.
- `404 Not Found`: Resource does not exist.
- `409 Conflict`: State conflict (e.g., duplicate/constraint issue).
- `422 Unprocessable Entity`: Validation errors.
- `429 Too Many Requests`: Rate-limit exceeded.

### Server errors
- `500 Internal Server Error`: Unexpected server failure.
- `502 Bad Gateway`: Upstream dependency error.
- `503 Service Unavailable`: Temporary downtime/overload.
- `504 Gateway Timeout`: Upstream timeout.

## 3) Error Format

All non-2xx responses MUST use this JSON envelope:

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
    "traceId": "9f43a8f6ad2b4db9"
  }
}
```

### Error fields
- `error.code` (string, required): Stable machine-readable code.
- `error.message` (string, required): Human-readable summary.
- `error.details` (array, optional): Structured validation/domain details.
- `error.traceId` (string, required): Correlation ID for support/log tracing.

### Rules
- Do not leak internal stack traces or secrets.
- Keep `code` values stable across releases.
- Use `traceId` from incoming request context when available; otherwise generate one.

## 4) Pagination

Use cursor-based pagination for list endpoints.

### Request
- `limit` (optional, default `25`, max `100`)
- `cursor` (optional, opaque string)

Example:
- `GET /employees?limit=25&cursor=eyJsYXN0SWQiOiJlbXBfMDAxIn0`

### Response

```json
{
  "data": [
    { "id": "emp_001", "name": "Ada Lovelace" }
  ],
  "page": {
    "nextCursor": "eyJsYXN0SWQiOiJlbXBfMDAyIn0",
    "hasNext": true,
    "limit": 25
  }
}
```

### Rules
- Cursors are opaque and must not be parsed by clients.
- Sort order must be deterministic and documented per endpoint.
- If `hasNext` is `false`, `nextCursor` should be `null`.

## 5) Authentication

### Scheme
- Use OAuth 2.0 Bearer tokens (JWT or opaque token).
- Send token via `Authorization: Bearer <token>`.
- All endpoints are authenticated by default unless explicitly documented as public.

### Authorization
- Enforce role/scope checks at endpoint and resource levels.
- Return:
  - `401` for missing/invalid token.
  - `403` for insufficient permissions.

### Security baseline
- Require HTTPS in all environments except approved local development.
- Validate token signature, issuer, audience, expiry, and not-before claims.
- Minimize token lifetimes and support key rotation.

## 6) Versioning

### Strategy
- Version in URL path using major version only.
- Format: `/api/v{major}` (e.g., `/api/v1/employees`).

### Compatibility
- Additive, backward-compatible changes are allowed within the same major version.
- Breaking changes require a new major version.

### Deprecation
- Announce deprecations with migration guidance.
- Include deprecation metadata via headers when applicable:
  - `Deprecation: true`
  - `Sunset: <HTTP-date>`
- Maintain an overlap period where old and new versions both function.
