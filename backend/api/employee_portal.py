from __future__ import annotations

from datetime import date
from typing import Any

from api_contract import success_response
from resilience import new_trace_id

SERVICE_NAME = 'employee-portal'
ENDPOINTS = ('/payslip', '/leave/apply', '/attendance', '/profile')


def _decision(action: str, rationale: str, confidence: int) -> dict[str, Any]:
    return {
        'next_action': action,
        'why': rationale,
        'confidence': max(0, min(100, int(confidence))),
    }


def _compact(response: dict[str, Any]) -> dict[str, Any]:
    """Return a compact payload for mobile clients.

    Removes empty/null fields recursively to keep response size low on unstable networks.
    """

    def _clean(value: Any) -> Any:
        if isinstance(value, dict):
            cleaned = {k: _clean(v) for k, v in value.items()}
            return {k: v for k, v in cleaned.items() if v not in (None, '', [], {})}
        if isinstance(value, list):
            cleaned = [_clean(item) for item in value]
            return [item for item in cleaned if item not in (None, '', [], {})]
        return value

    result = _clean(response)
    return result if isinstance(result, dict) else {}


def get_payslip(record: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
    trace = trace_id or new_trace_id()
    payload = _compact(
        {
            'endpoint': '/payslip',
            'payslip': {
                'payroll_record_id': record.get('payroll_record_id'),
                'period': record.get('period'),
                'net_pay': record.get('net_pay'),
                'currency': record.get('currency', 'PKR'),
                'payment_date': record.get('payment_date'),
            },
            'decision': _decision(
                'acknowledge_payslip',
                'Payslip is ready for review and employee acknowledgement.',
                96,
            ),
        }
    )
    return success_response(200, payload, request_id=trace, service=SERVICE_NAME)


def post_leave_apply(request: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
    trace = trace_id or new_trace_id()
    payload = _compact(
        {
            'endpoint': '/leave/apply',
            'leave_request': {
                'employee_id': request.get('employee_id'),
                'leave_type': request.get('leave_type'),
                'start_date': request.get('start_date'),
                'end_date': request.get('end_date'),
                'status': request.get('status', 'submitted'),
            },
            'decision': _decision(
                'track_approval_status',
                'Leave request has been submitted and routed for approval.',
                94,
            ),
        }
    )
    return success_response(201, payload, request_id=trace, service=SERVICE_NAME)


def get_attendance(snapshot: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
    trace = trace_id or new_trace_id()
    today = snapshot.get('date') or date.today().isoformat()
    payload = _compact(
        {
            'endpoint': '/attendance',
            'attendance': {
                'date': today,
                'status': snapshot.get('status', 'present'),
                'check_in': snapshot.get('check_in'),
                'check_out': snapshot.get('check_out'),
                'worked_hours': snapshot.get('worked_hours'),
            },
            'decision': _decision(
                'complete_checkout' if not snapshot.get('check_out') else 'no_action_required',
                'Attendance reflects today\'s progress and highlights pending action if checkout is missing.',
                93,
            ),
        }
    )
    return success_response(200, payload, request_id=trace, service=SERVICE_NAME)


def get_profile(profile: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
    trace = trace_id or new_trace_id()
    payload = _compact(
        {
            'endpoint': '/profile',
            'profile': {
                'employee_id': profile.get('employee_id'),
                'name': profile.get('name'),
                'department': profile.get('department'),
                'role': profile.get('role'),
                'email': profile.get('email'),
            },
            'decision': _decision(
                'verify_profile_details',
                'Profile view prioritizes data needed to confirm identity and contact details.',
                92,
            ),
        }
    )
    return success_response(200, payload, request_id=trace, service=SERVICE_NAME)
