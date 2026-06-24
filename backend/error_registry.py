"""Central error registry for AURA HRMS.

Maps every system error code to a structured descriptor:
  type            — validation | system | external_dependency
  severity        — critical | high | medium | low
  resolution_steps — ordered list of human-readable fix instructions
  retryable       — whether the caller can safely retry without changes

Usage:
    from error_registry import get_error_descriptor

    descriptor = get_error_descriptor('PAYROLL_EMPLOYEE_DATA_INCOMPLETE')
    # Returns: {type, severity, resolution_steps, retryable}
    # Returns None if the code is not registered (unknown/unclassified error).
"""
from __future__ import annotations

from typing import Optional

_REGISTRY: dict[str, dict] = {
    # ── Payroll ──────────────────────────────────────────────────────────────
    'PAYROLL_EMPLOYEE_DATA_INCOMPLETE': {
        'type': 'validation',
        'severity': 'critical',
        'resolution_steps': [
            'Open the employee record and complete all required fields.',
            'Required fields: CNIC, bank account, tax category, and department.',
            'Re-run payroll validation after saving.',
        ],
        'retryable': True,
    },
    'PAYROLL_CNIC_INVALID': {
        'type': 'validation',
        'severity': 'critical',
        'resolution_steps': [
            'Verify the CNIC number format: 13 digits, no dashes (e.g. 4210112345671).',
            'Update the employee CNIC field with the correct value.',
            'Cross-check against the original NADRA document if available.',
        ],
        'retryable': True,
    },
    'PAYROLL_TAX_CONFIG_MISSING': {
        'type': 'validation',
        'severity': 'high',
        'resolution_steps': [
            'Navigate to Settings → Tax Configuration.',
            'Assign a tax category (Filer / Non-Filer / Exempt) to the employee.',
            'Save and re-run payroll.',
        ],
        'retryable': True,
    },
    'PAYROLL_ATTENDANCE_INCONSISTENCY': {
        'type': 'validation',
        'severity': 'high',
        'resolution_steps': [
            'Open Attendance → Corrections for the affected employee.',
            'Resolve all flagged missing punches or conflicting records.',
            'Lock the attendance period before re-running payroll.',
        ],
        'retryable': True,
    },
    'PAYROLL_COMPLIANCE_GATE_FAILED': {
        'type': 'validation',
        'severity': 'critical',
        'resolution_steps': [
            'Run Compliance → Validate for the current period.',
            'Resolve all compliance errors shown in the validation report.',
            'Payroll cannot finalize until compliance validation passes.',
        ],
        'retryable': True,
    },
    'PAYROLL_DUPLICATE_RUN': {
        'type': 'validation',
        'severity': 'high',
        'resolution_steps': [
            'A payroll run already exists for this period and entity.',
            'If a correction is needed, void the existing run first.',
            'Contact an administrator to void a finalized payroll run.',
        ],
        'retryable': False,
    },

    # ── Compliance ───────────────────────────────────────────────────────────
    'COMPLIANCE_SUBMISSION_FAILED': {
        'type': 'external_dependency',
        'severity': 'high',
        'resolution_steps': [
            'Check the FBR/EOBI/PESSI portal status for service availability.',
            'Review the submission error detail for data issues.',
            'Correct any reported data errors and use the Retry option.',
        ],
        'retryable': True,
    },
    'COMPLIANCE_DATA_INVALID': {
        'type': 'validation',
        'severity': 'high',
        'resolution_steps': [
            'Review the compliance validation report for field-level errors.',
            'Correct the identified employee or salary data.',
            'Re-run compliance validation before resubmitting.',
        ],
        'retryable': True,
    },
    'COMPLIANCE_PERIOD_ALREADY_SUBMITTED': {
        'type': 'validation',
        'severity': 'medium',
        'resolution_steps': [
            'This period has already been submitted to the statutory authority.',
            'If an amendment is required, file a revised submission directly via the portal.',
            'Contact your compliance officer for guidance.',
        ],
        'retryable': False,
    },

    # ── Attendance ───────────────────────────────────────────────────────────
    'ATTENDANCE_DUPLICATE': {
        'type': 'validation',
        'severity': 'medium',
        'resolution_steps': [
            'An attendance record already exists for this employee and date.',
            'Use Attendance → Corrections to amend the existing record.',
        ],
        'retryable': False,
    },
    'ATTENDANCE_MISSING_PUNCH': {
        'type': 'validation',
        'severity': 'medium',
        'resolution_steps': [
            'The attendance record has an incomplete check-in or check-out.',
            'Submit an Attendance Correction to add the missing punch time.',
            'Manager or Admin approval is required for corrections.',
        ],
        'retryable': True,
    },
    'EMPLOYEE_STATUS_INVALID': {
        'type': 'validation',
        'severity': 'medium',
        'resolution_steps': [
            'Attendance can only be recorded for Active or On-Leave employees.',
            'Verify the employee status in the Employee record.',
            'Contact HR if the status is incorrect.',
        ],
        'retryable': False,
    },
    'DATE_RANGE_INVALID': {
        'type': 'validation',
        'severity': 'low',
        'resolution_steps': [
            'The from_date must be on or before the to_date.',
            'Correct the date range and retry.',
        ],
        'retryable': True,
    },

    # ── Bank / Disbursement ───────────────────────────────────────────────────
    'BANK_ACCOUNT_INVALID': {
        'type': 'validation',
        'severity': 'high',
        'resolution_steps': [
            'Verify the employee bank account number format.',
            'For Raast payments, confirm the IBAN or registered mobile number is correct.',
            'Update the employee bank record and re-initiate disbursement.',
        ],
        'retryable': True,
    },
    'BANK_DISBURSEMENT_FAILED': {
        'type': 'external_dependency',
        'severity': 'high',
        'resolution_steps': [
            'Check the bank gateway or Raast service status.',
            'Review the failure code in the disbursement log.',
            'Retry disbursement after confirming gateway availability.',
        ],
        'retryable': True,
    },

    # ── WhatsApp / Webhook ────────────────────────────────────────────────────
    'WHATSAPP_COMMAND_UNKNOWN': {
        'type': 'validation',
        'severity': 'low',
        'resolution_steps': [
            "Send a recognised command: 'payslip', 'leave', 'approval', or 'attendance'.",
            'Reply HELP for a full list of supported commands.',
        ],
        'retryable': True,
    },
    'WHATSAPP_AUTH_FAILED': {
        'type': 'validation',
        'severity': 'high',
        'resolution_steps': [
            'Your session has expired or the OTP was incorrect.',
            'Request a new OTP by sending START to this number.',
        ],
        'retryable': True,
    },

    # ── General ───────────────────────────────────────────────────────────────
    'VALIDATION_ERROR': {
        'type': 'validation',
        'severity': 'medium',
        'resolution_steps': [
            'Review the field-level errors in the response details.',
            'Correct the indicated fields and resubmit.',
        ],
        'retryable': True,
    },
    'FORBIDDEN': {
        'type': 'validation',
        'severity': 'high',
        'resolution_steps': [
            'You do not have permission to perform this action.',
            'Contact your administrator to request the necessary role.',
        ],
        'retryable': False,
    },
    'NOT_FOUND': {
        'type': 'validation',
        'severity': 'low',
        'resolution_steps': [
            'The requested resource does not exist.',
            'Verify the ID or reference and retry.',
        ],
        'retryable': False,
    },
    'EMPLOYEE_NOT_FOUND': {
        'type': 'validation',
        'severity': 'medium',
        'resolution_steps': [
            'No employee record found for the given ID.',
            'Verify the employee ID and ensure the record has not been archived.',
        ],
        'retryable': False,
    },
    'SYSTEM_ERROR': {
        'type': 'system',
        'severity': 'critical',
        'resolution_steps': [
            'An unexpected internal error occurred.',
            'Retry the operation. If the error persists, contact system support.',
            'Include the correlation_id from the error response when reporting.',
        ],
        'retryable': True,
    },
}


def get_error_descriptor(code: str) -> Optional[dict]:
    """Return the registered descriptor for an error code, or None if unregistered."""
    return _REGISTRY.get(code)


def register_error(
    code: str,
    *,
    error_type: str,
    severity: str,
    resolution_steps: list[str],
    retryable: bool,
) -> None:
    """Register a new error code at runtime (e.g. from a country adapter or plugin).

    Raises ValueError if the code is already registered.
    """
    if code in _REGISTRY:
        raise ValueError(f"Error code '{code}' is already registered. Use update_error() to modify it.")
    _REGISTRY[code] = {
        'type': error_type,
        'severity': severity,
        'resolution_steps': resolution_steps,
        'retryable': retryable,
    }


def update_error(
    code: str,
    *,
    resolution_steps: Optional[list[str]] = None,
    severity: Optional[str] = None,
    retryable: Optional[bool] = None,
) -> None:
    """Update specific fields of an existing registered error code."""
    if code not in _REGISTRY:
        raise ValueError(f"Error code '{code}' is not registered.")
    if resolution_steps is not None:
        _REGISTRY[code]['resolution_steps'] = resolution_steps
    if severity is not None:
        _REGISTRY[code]['severity'] = severity
    if retryable is not None:
        _REGISTRY[code]['retryable'] = retryable
