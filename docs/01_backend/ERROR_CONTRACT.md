# ERROR CONTRACT

Status: Draft
Authority Level: High
Last Reviewed: 2026-06-15
Owner: AI

---

## 1. Error Envelope Shape

Source: `D:\SaaS\HRMS\backend\api_contract.py` — `error_payload()` / `error_response()`

All services that use `api_contract.py` produce errors in this shape:

```json
{
  "status": "error",
  "data": {},
  "meta": {
    "request_id": "<uuid string>",
    "timestamp": "<ISO8601 UTC>",
    "pagination": {},
    "tenant_id": "<str>",
    "actor": { "id": "...", "type": "user|service", "role": "..." },
    "service": "<str>"
  },
  "error": {
    "code": "STRING_ERROR_CODE",
    "message": "Human-readable message",
    "details": {} | [{"field": "...", "reason": "..."}]
  }
}
```

### Field constraints

| Field | Rule |
|---|---|
| `status` | Always `"error"` on error responses. |
| `data` | Always `{}` (empty object). Never null, never absent. Enforced in `error_payload()`. |
| `meta.request_id` | Always present. Must be the `trace_id` / `X-Request-Id` for the request. |
| `meta.timestamp` | Always present. UTC ISO8601 with `Z` suffix. |
| `meta.pagination` | Always `{}` (empty object) on error responses. |
| `error.code` | Machine-readable string. Should be from the registered error codes in Section 3. Unregistered codes are allowed but discouraged. |
| `error.message` | Human-readable string. Must not expose internal stack traces. |
| `error.details` | Optional field-level detail. Type is `dict[str, Any] \| list[dict[str, Any]]`; defaults to `{}` if not provided. Field-level validation errors use list form: `[{"field": "...", "reason": "..."}]`. |

### Non-standard envelopes (violation)

The following services do **not** use `api_contract.py` and produce a non-compliant error shape that is missing `meta`:

| Service | File | Non-standard shape |
|---|---|---|
| compliance-service | `compliance_api.py` | `{"status": "error", "code": ..., "message": ..., "service": ...}` |
| bank-service | `banking_api.py` | Same as above |
| whatsapp-service | `whatsapp_api.py` | Same as above |
| decision-service | `decision_api.py` | Same as above |

These responses lack `meta.request_id`, `meta.timestamp`, and `meta.pagination`, violating the Service Contract Standard (SCS) defined in `D:\SaaS\HRMS\backend\docs\canon\api-standards.md`.

---

## 2. HTTP Status Code Conventions

Source: `D:\SaaS\HRMS\backend\docs\canon\api-standards.md` (§4); confirmed by `*_api.py` handler files.

### Success Codes

| Code | Meaning | When Used |
|---|---|---|
| `200 OK` | Successful read / update / action | Most GET, PATCH, PUT, POST action endpoints |
| `201 Created` | Resource created | POST endpoints that create a new resource (e.g. leave request, hiring candidate, automation rule) |
| `202 Accepted` | Async processing started | Payroll run, report export, notification event ingestion, background job enqueue |
| `204 No Content` | Success with no body | Not observed in current handlers; reserved per standard |

### Client Error Codes

| Code | Meaning | Typical Error Code | Observed In |
|---|---|---|---|
| `400 Bad Request` | Malformed request shape; fallback for unrecognized codes | varies | `payroll_api.py`, `automation_api.py` fallback |
| `401 Unauthorized` | Missing or invalid authentication | `TOKEN_INVALID`, `TOKEN_EXPIRED`, `TOKEN_REVOKED`, `INVALID_CREDENTIALS` | `auth-service/api.py` |
| `403 Forbidden` | Authenticated but not authorized | `FORBIDDEN`, `ACCOUNT_DISABLED`, `TENANT_SCOPE_VIOLATION` | `auth-service/api.py`, `automation_api.py`, `integration_api.py` |
| `404 Not Found` | Resource does not exist | `NOT_FOUND`, `EMPLOYEE_NOT_FOUND`, `RULE_NOT_FOUND`, `WEBHOOK_NOT_FOUND` | multiple services |
| `409 Conflict` | State or uniqueness conflict | `ATTENDANCE_DUPLICATE`, `PAYROLL_DUPLICATE_RUN`, `USER_EXISTS`, `INVALID_JOB_STATE` | `attendance_service/api.py`, `payroll_api.py`, `auth-service/api.py`, `background_jobs_api.py` |
| `412 Precondition Failed` | Pre-condition for operation not met | `PRECONDITION_FAILED` | `compliance_api.py`, `banking_api.py` |
| `422 Unprocessable Entity` | Validation or business rule failure | `VALIDATION_ERROR`, `ROLE_INVALID`, `UNKNOWN_JOB_TYPE`, `DATE_RANGE_INVALID`, `ATTENDANCE_MISSING_PUNCH` | all services |
| `429 Too Many Requests` | Rate limit / queue overflow | `QUEUE_OVERFLOW` | `background_jobs_api.py` |

### Server / Dependency Error Codes

| Code | Meaning | Typical Error Code | Notes |
|---|---|---|---|
| `500 Internal Server Error` | Unexpected service failure | `SYSTEM_ERROR`, `SECRET_INTEGRITY_ERROR` | `error_registry.py`, `integration_api.py` |
| `502 Bad Gateway` | Upstream returned invalid response | TBD | Defined in `api-standards.md`; not observed in handlers |
| `503 Service Unavailable` | Temporary outage / circuit open | TBD | Defined in `api-standards.md`; not observed in handlers |
| `504 Gateway Timeout` | Upstream dependency timeout | TBD | Defined in `api-standards.md`; not observed in handlers |

---

## 3. Error Code Registry

Source: `D:\SaaS\HRMS\backend\error_registry.py`

The central registry maps error codes to descriptors with `type`, `severity`, `resolution_steps`, and `retryable`. The `get_error_descriptor(code)` function returns the descriptor or `None` for unregistered codes.

### 3.1 Payroll Errors

| Code | Type | Severity | Retryable | Resolution |
|---|---|---|---|---|
| `PAYROLL_EMPLOYEE_DATA_INCOMPLETE` | validation | critical | Yes | Complete CNIC, bank account, tax category, department in employee record |
| `PAYROLL_CNIC_INVALID` | validation | critical | Yes | Verify 13-digit CNIC format; update employee record |
| `PAYROLL_TAX_CONFIG_MISSING` | validation | high | Yes | Assign tax category (Filer/Non-Filer/Exempt) in Settings → Tax Configuration |
| `PAYROLL_ATTENDANCE_INCONSISTENCY` | validation | high | Yes | Resolve missing punches in Attendance → Corrections; lock period before re-running |
| `PAYROLL_COMPLIANCE_GATE_FAILED` | validation | critical | Yes | Run Compliance → Validate; resolve all compliance errors |
| `PAYROLL_DUPLICATE_RUN` | validation | high | No | Void existing run before creating a new one |

### 3.2 Compliance Errors

| Code | Type | Severity | Retryable | Resolution |
|---|---|---|---|---|
| `COMPLIANCE_SUBMISSION_FAILED` | external_dependency | high | Yes | Check FBR/EOBI/PESSI portal; correct data errors; retry |
| `COMPLIANCE_DATA_INVALID` | validation | high | Yes | Review compliance validation report; correct employee/salary data |
| `COMPLIANCE_PERIOD_ALREADY_SUBMITTED` | validation | medium | No | File amendment via the statutory portal |

### 3.3 Attendance Errors

| Code | Type | Severity | Retryable | Resolution |
|---|---|---|---|---|
| `ATTENDANCE_DUPLICATE` | validation | medium | No | Use Attendance → Corrections to amend existing record |
| `ATTENDANCE_MISSING_PUNCH` | validation | medium | Yes | Submit correction for missing check-in/check-out; requires manager/admin approval |
| `EMPLOYEE_STATUS_INVALID` | validation | medium | No | Attendance valid only for Active or On-Leave employees |
| `DATE_RANGE_INVALID` | validation | low | Yes | `from_date` must be on or before `to_date` |

### 3.4 Bank / Disbursement Errors

| Code | Type | Severity | Retryable | Resolution |
|---|---|---|---|---|
| `BANK_ACCOUNT_INVALID` | validation | high | Yes | Verify bank account number / Raast IBAN or mobile; update employee bank record |
| `BANK_DISBURSEMENT_FAILED` | external_dependency | high | Yes | Check bank gateway / Raast status; review failure code; retry |

### 3.5 WhatsApp Errors

| Code | Type | Severity | Retryable | Resolution |
|---|---|---|---|---|
| `WHATSAPP_COMMAND_UNKNOWN` | validation | low | Yes | Send a recognised command: payslip, leave, approval, attendance |
| `WHATSAPP_AUTH_FAILED` | validation | high | Yes | Session expired or OTP incorrect; request new OTP by sending START |

### 3.6 General Errors

| Code | Type | Severity | Retryable | Resolution |
|---|---|---|---|---|
| `VALIDATION_ERROR` | validation | medium | Yes | Review field-level errors in `error.details`; correct and resubmit |
| `FORBIDDEN` | validation | high | No | Contact administrator for required role |
| `NOT_FOUND` | validation | low | No | Verify the ID or reference |
| `EMPLOYEE_NOT_FOUND` | validation | medium | No | Verify employee ID; ensure record is not archived |
| `SYSTEM_ERROR` | system | critical | Yes | Retry; if persists, include `meta.request_id` when reporting to support |

### 3.7 Additional Error Codes (Not in Central Registry)

These codes are used in handler files but **not registered** in `error_registry.py`. They are at risk of documentation drift.

| Code | Used In | HTTP Status |
|---|---|---|
| `INVALID_CREDENTIALS` | `auth-service/api.py` | 401 |
| `ACCOUNT_DISABLED` | `auth-service/api.py` | 403 |
| `TOKEN_INVALID` | `auth-service/api.py` | 401 |
| `TOKEN_EXPIRED` | `auth-service/api.py` | 401 |
| `TOKEN_REVOKED` | `auth-service/api.py` | 401 |
| `USER_EXISTS` | `auth-service/api.py` | 409 |
| `ROLE_INVALID` | `auth-service/api.py` | 422 |
| `CONFLICT` | `hiring_service/api.py` | 409 |
| `RULE_NOT_FOUND` | `automation_api.py` | 404 |
| `TENANT_SCOPE_VIOLATION` | `automation_api.py`, `integration_api.py` | 403 |
| `JOB_NOT_FOUND` | `background_jobs_api.py` | 404 |
| `UNKNOWN_JOB_TYPE` | `background_jobs_api.py` | 422 |
| `INVALID_JOB_STATE` | `background_jobs_api.py` | 409 |
| `QUEUE_OVERFLOW` | `background_jobs_api.py` | 429 |
| `WEBHOOK_NOT_FOUND` | `integration_api.py` | 404 |
| `DELIVERY_NOT_FOUND` | `integration_api.py` | 404 |
| `INVALID_DELIVERY_STATE` | `integration_api.py` | 409 |
| `SECRET_INTEGRITY_ERROR` | `integration_api.py` | 500 |
| `UNSUPPORTED_EVENT` | `notification_api.py` | 422 |
| `TEMPLATE_NOT_FOUND` | `notification_api.py` | 404 |
| `MESSAGE_NOT_FOUND` | `notification_api.py` | 404 |
| `REPORT_NOT_FOUND` | `reporting_analytics_api.py` | 404 |
| `UNSUPPORTED_AGGREGATE` | `reporting_analytics_api.py` | 422 |
| `UNSUPPORTED_REPORT_TYPE` | `reporting_analytics_api.py` | 422 |
| `PRECONDITION_FAILED` | `compliance_api.py`, `banking_api.py`, `decision_api.py` | 412 |
| `HUMAN_IN_LOOP_GATE` | `decision_api.py` (referenced in comments) | 409 |
| `ATTENDANCE_NOT_FOUND` | `attendance_service/api.py` | 404 |
| `SHIFT_NOT_FOUND` | `attendance_service/api.py` | 404 |
| `SCHEDULE_NOT_FOUND` | `attendance_service/api.py` | 404 |
| `CORRECTION_NOT_FOUND` | `attendance_service/api.py` | 404 |
| `ATTENDANCE_LOCKED` | `attendance_service/api.py` | 409 |
| `LOCK_REQUIRES_APPROVAL` | `attendance_service/api.py` | 409 |
| `APPROVAL_REQUIRES_VALIDATED` | `attendance_service/api.py` | 409 |
| `TIME_LOGIC_INVALID` | `attendance_service/api.py` | 422 |
| `SHIFT_INVALID` | `attendance_service/api.py` | 422 |
| `SHIFT_SCOPE_INVALID` | `attendance_service/api.py` | 422 |
| `SCHEDULE_SCOPE_INVALID` | `attendance_service/api.py` | 422 |
| `OVERTIME_RULE_INVALID` | `attendance_service/api.py` | 422 |
| `WORKFLOW_ERROR` | `attendance_service/api.py` | 422 |

---

## 4. Error Registration API

Source: `D:\SaaS\HRMS\backend\error_registry.py`

### `get_error_descriptor(code: str) -> dict | None`

Returns the registered descriptor for a code, or `None` if unregistered.

### `register_error(code, *, error_type, severity, resolution_steps, retryable)`

Registers a new error code at runtime (e.g. from a country adapter or plugin). Raises `ValueError` if the code already exists.

### `update_error(code, *, resolution_steps=None, severity=None, retryable=None)`

Updates specific fields of an existing code. Raises `ValueError` if the code is not registered.

### Error type values

| Type | Meaning |
|---|---|
| `validation` | Request or business rule violation; actionable by the caller |
| `system` | Unexpected internal failure; requires operator investigation |
| `external_dependency` | Downstream service (bank gateway, government portal) failure |

### Severity values

| Severity | Meaning |
|---|---|
| `critical` | Blocks core workflow (payroll finalization, compliance gate) |
| `high` | Significant impact; requires prompt resolution |
| `medium` | Moderate impact; should be addressed |
| `low` | Informational; minor correction required |

---

## 5. How Specific Error Scenarios Are Represented

### 5.1 Validation Error (422)

Triggered by invalid field values, missing required fields, or enum mismatches.

```json
{
  "status": "error",
  "data": {},
  "meta": { "request_id": "...", "timestamp": "...", "pagination": {} },
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request payload.",
    "details": [
      {"field": "attendance_date", "reason": "must be an ISO date"},
      {"field": "username/password", "reason": "must be non-empty strings"}
    ]
  }
}
```

### 5.2 Unauthenticated Request (401)

```json
{
  "status": "error",
  "data": {},
  "meta": { "request_id": "...", "timestamp": "...", "pagination": {} },
  "error": {
    "code": "TOKEN_INVALID",
    "message": "Missing bearer token",
    "details": {}
  }
}
```

### 5.3 Forbidden (403)

```json
{
  "status": "error",
  "data": {},
  "meta": { "request_id": "...", "timestamp": "...", "pagination": {} },
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to perform this action.",
    "details": {}
  }
}
```

### 5.4 Not Found (404)

```json
{
  "status": "error",
  "data": {},
  "meta": { "request_id": "...", "timestamp": "...", "pagination": {} },
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource does not exist.",
    "details": {}
  }
}
```

### 5.5 Conflict / Duplicate (409)

```json
{
  "status": "error",
  "data": {},
  "meta": { "request_id": "...", "timestamp": "...", "pagination": {} },
  "error": {
    "code": "PAYROLL_DUPLICATE_RUN",
    "message": "A payroll run already exists for this period and entity.",
    "details": {}
  }
}
```

### 5.6 Business Rule Failure (422)

```json
{
  "status": "error",
  "data": {},
  "meta": { "request_id": "...", "timestamp": "...", "pagination": {} },
  "error": {
    "code": "PAYROLL_COMPLIANCE_GATE_FAILED",
    "message": "Run Compliance → Validate for the current period.",
    "details": {}
  }
}
```

### 5.7 System Error (500)

```json
{
  "status": "error",
  "data": {},
  "meta": { "request_id": "abc123", "timestamp": "...", "pagination": {} },
  "error": {
    "code": "SYSTEM_ERROR",
    "message": "An unexpected internal error occurred.",
    "details": {}
  }
}
```

Include `meta.request_id` when reporting to support.

---

## 6. Fallback HTTP Status Mapping

Several services define a local `_ERROR_STATUS_BY_CODE` mapping that supplements the global registry. When a code is not in the local map, services fall back to a default.

| Service | Default fallback | Source |
|---|---|---|
| payroll-service | `400` | `payroll_api.py` line 16 |
| notification-service | `400` | `notification_api.py` line 12 |
| automation-service | `400` | `automation_api.py` line 10 |
| background-jobs-service | `400` | `background_jobs_api.py` line 12 |
| integration-service | `400` | `integration_api.py` line 11 |
| compliance-service | `400` | `compliance_api.py` line 9 |
| bank-service | `400` | `banking_api.py` line 9 |
| whatsapp-service | `400` | `whatsapp_api.py` line 9 |
| decision-service | `400` | `decision_api.py` line 18 |

**Implication**: Unregistered codes will surface as HTTP 400, not 422. Callers should inspect `error.code` rather than relying solely on the HTTP status for error classification.
