# error-registry

Central static error-code catalogue: maps every system error code to a structured descriptor (type, severity, resolution steps, retryability) consumed by API response builders and operator-facing error surfaces.

## Scope
- Support module — not a service with an HTTP surface.
- Imported directly by domain services and the API contract layer (`api_contract.py`).
- Provides three functions: lookup, runtime registration, and runtime update.
- Covers 22 pre-registered codes across 6 domains: Payroll, Compliance, Attendance, Bank/Disbursement, WhatsApp/Webhook, and General.
- Extensible: country adapters and plugins can register additional codes at process startup via `register_error()`.

## Functions

### `get_error_descriptor(code: str) → dict | None`
Returns the descriptor dict for a registered code, or `None` if the code is unknown/unclassified.

```python
from error_registry import get_error_descriptor

desc = get_error_descriptor('PAYROLL_COMPLIANCE_GATE_FAILED')
# {
#   'type': 'validation',
#   'severity': 'critical',
#   'resolution_steps': ['Run Compliance → Validate...', ...],
#   'retryable': True,
# }
```

### `register_error(code, *, error_type, severity, resolution_steps, retryable)`
Registers a new code at runtime. Raises `ValueError` if the code already exists (use `update_error()` for amendments).

### `update_error(code, *, resolution_steps, severity, retryable)`
Updates one or more fields of an existing registered code. Raises `ValueError` if code is not registered.

## Descriptor schema
```yaml
type: validation | system | external_dependency
  # validation       — bad input, missing data, business-rule violation (caller must fix data)
  # system           — unexpected internal error (retry; file support if persists)
  # external_dependency — downstream gateway/portal failure (retry when available)
severity: critical | high | medium | low
resolution_steps: list[string]   # ordered, human-readable instructions shown to operators
retryable: bool                  # whether caller can safely retry without changing the request
```

## Registered codes

### Payroll
| Code | Type | Severity | Retryable |
|---|---|---|---|
| `PAYROLL_EMPLOYEE_DATA_INCOMPLETE` | validation | critical | yes |
| `PAYROLL_CNIC_INVALID` | validation | critical | yes |
| `PAYROLL_TAX_CONFIG_MISSING` | validation | high | yes |
| `PAYROLL_ATTENDANCE_INCONSISTENCY` | validation | high | yes |
| `PAYROLL_COMPLIANCE_GATE_FAILED` | validation | critical | yes |
| `PAYROLL_DUPLICATE_RUN` | validation | high | no |

### Compliance
| Code | Type | Severity | Retryable |
|---|---|---|---|
| `COMPLIANCE_SUBMISSION_FAILED` | external_dependency | high | yes |
| `COMPLIANCE_DATA_INVALID` | validation | high | yes |
| `COMPLIANCE_PERIOD_ALREADY_SUBMITTED` | validation | medium | no |

### Attendance
| Code | Type | Severity | Retryable |
|---|---|---|---|
| `ATTENDANCE_DUPLICATE` | validation | medium | no |
| `ATTENDANCE_MISSING_PUNCH` | validation | medium | yes |
| `EMPLOYEE_STATUS_INVALID` | validation | medium | no |
| `DATE_RANGE_INVALID` | validation | low | yes |

### Bank / Disbursement
| Code | Type | Severity | Retryable |
|---|---|---|---|
| `BANK_ACCOUNT_INVALID` | validation | high | yes |
| `BANK_DISBURSEMENT_FAILED` | external_dependency | high | yes |

### WhatsApp / Webhook
| Code | Type | Severity | Retryable |
|---|---|---|---|
| `WHATSAPP_COMMAND_UNKNOWN` | validation | low | yes |
| `WHATSAPP_AUTH_FAILED` | validation | high | yes |

### General
| Code | Type | Severity | Retryable |
|---|---|---|---|
| `VALIDATION_ERROR` | validation | medium | yes |
| `FORBIDDEN` | validation | high | no |
| `NOT_FOUND` | validation | low | no |
| `EMPLOYEE_NOT_FOUND` | validation | medium | no |
| `SYSTEM_ERROR` | system | critical | yes |

## Dependencies
- None — the module is a pure Python dict with no external imports.

## Notes
- Resolution steps are written for operators and HR admins, not developers — they reference UI navigation paths (e.g. "Navigate to Settings → Tax Configuration") not code locations.
- `SYSTEM_ERROR` resolution steps instruct the operator to include the `correlation_id` from the response, which is present in every API error envelope (`api_contract.error_response()`).
- Country adapters should call `register_error()` during service initialization to add jurisdiction-specific codes (e.g. `EOBI_SUBMISSION_REJECTED`, `FBR_CNIC_MISMATCH`) so operator-facing error messages are localized.
