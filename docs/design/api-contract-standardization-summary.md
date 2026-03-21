# API Contract Standardization Summary

This change standardizes API envelopes around the canonical D1 Service Contract Standard using extend-only wrappers, shared helpers, and compatibility-safe payload normalization.

## Shared utilities
- `api_contract.py`
  - Added request-context aware envelope helpers.
  - Standardized optional metadata injection for `tenant_id`, `actor`, and `service`.
  - Added reusable pagination and compatibility list payload helpers.

## Wrapped / normalized endpoints

### Newly wrapped to D1
- `payroll_api.py`
  - `post_payroll_records`
  - `get_payroll_record`
  - `get_payroll_records`
  - `post_payroll_run`
  - `post_payroll_mark_paid`
- Purpose: preserve existing `PayrollService` business methods while adapting legacy payloads such as `{"data": ...}` and `page.nextCursor/hasNext` into D1 envelopes with canonical `meta.pagination`.

### Compatibility-normalized existing APIs
- `leave_api.py`
  - `get_leave_requests` now exposes canonical pagination metadata while preserving the legacy nested `data` list alias for compatibility.
  - All leave API envelopes now include consistent service/tenant/actor request metadata.
- `attendance_service/api.py`
  - Standardized list pagination metadata and request actor metadata without changing business handlers.
- `services/auth-service/api.py`
  - Added consistent service and tenant metadata and standardized list-session pagination metadata.
- `services/hiring_service/api.py`
  - Added consistent service and tenant metadata across existing D1 responses.

## Already compliant or largely compliant before change
- `services/auth-service/api.py`
- `attendance_service/api.py`
- `leave_api.py`
- `services/hiring_service/api.py`
- `notification_api.py`
- `audit_service/api.py`
- `background_jobs_api.py`
- `workflow_api.py`

These modules already used D1-style envelopes; this pass aligned metadata and pagination details and left business endpoints intact.

## Backward-compatibility notes
- No core domain service boundaries were rewritten.
- Payroll domain methods remain unchanged; new wrappers provide contract normalization.
- Leave list responses preserve the legacy `data` alias while adding canonical `items` plus `meta.pagination`.
- Existing request/response business fields remain available to downstream callers.
