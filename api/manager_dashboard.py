from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api_contract import pagination_payload, success_response
from resilience import new_trace_id

SERVICE_NAME = 'manager-dashboard'
ENDPOINTS = ('/alerts', '/overtime', '/approvals', '/burnout', '/performance')


def _parse_iso(value: str | None) -> datetime:
    if not value:
        return datetime.max.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _priority(issue: dict[str, Any]) -> tuple[int, datetime]:
    severity_rank = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    return severity_rank.get(str(issue.get('severity', 'low')).lower(), 4), _parse_iso(issue.get('due_at'))


def _sorted_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(issues, key=_priority)


def _success(data: dict[str, Any], trace_id: str) -> tuple[int, dict[str, Any]]:
    count = len(data.get('items', []))
    return success_response(
        200,
        data,
        request_id=trace_id,
        service=SERVICE_NAME,
        pagination=pagination_payload(limit=count, count=count, cursor=None, next_cursor=None),
    )


def get_alerts(aggregate: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
    trace = trace_id or new_trace_id()
    attendance = aggregate.get('attendance', {})
    items: list[dict[str, Any]] = []
    for record in attendance.get('records', []):
        late_minutes = int(record.get('late_minutes', 0) or 0)
        missing = bool(record.get('missing_check_in')) or bool(record.get('missing_check_out'))
        unplanned = bool(record.get('unplanned_absence'))
        if late_minutes <= 15 and not missing and not unplanned:
            continue
        severity = 'medium'
        reason = 'Attendance exception requires manager review.'
        if unplanned or missing:
            severity = 'high'
            reason = 'Unplanned absence or missing attendance event detected.'
        if late_minutes > 45:
            severity = 'critical'
            reason = 'Repeated severe lateness beyond policy threshold.'
        items.append(
            {
                'employee_id': record.get('employee_id'),
                'employee_name': record.get('employee_name'),
                'severity': severity,
                'late_minutes': late_minutes,
                'unplanned_absence': unplanned,
                'missing_check_in': bool(record.get('missing_check_in')),
                'missing_check_out': bool(record.get('missing_check_out')),
                'reason': reason,
                'actions': ['acknowledge', 'notify_employee', 'escalate_hr'],
                'due_at': record.get('due_at'),
            }
        )

    return _success({'endpoint': '/alerts', 'source': ['attendance'], 'items': _sorted_issues(items)}, trace)


def get_overtime(aggregate: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
    trace = trace_id or new_trace_id()
    payroll = aggregate.get('payroll', {})
    threshold = float(payroll.get('policy', {}).get('overtime_threshold_hours', 12))
    items: list[dict[str, Any]] = []
    for row in payroll.get('entries', []):
        overtime_hours = float(row.get('overtime_hours', 0) or 0)
        if overtime_hours <= threshold:
            continue
        approved = bool(row.get('approved'))
        severity = 'medium' if approved else 'high'
        if overtime_hours >= threshold * 1.75:
            severity = 'critical'
        items.append(
            {
                'employee_id': row.get('employee_id'),
                'employee_name': row.get('employee_name'),
                'department': row.get('department'),
                'overtime_hours': overtime_hours,
                'policy_threshold_hours': threshold,
                'approved': approved,
                'severity': severity,
                'reason': 'Overtime exceeds approved policy threshold.',
                'actions': ['approve_exception', 'rebalance_shifts', 'start_compliance_review'],
                'due_at': row.get('due_at'),
            }
        )

    return _success({'endpoint': '/overtime', 'source': ['payroll'], 'items': _sorted_issues(items)}, trace)


def get_approvals(aggregate: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
    trace = trace_id or new_trace_id()
    attendance = aggregate.get('attendance', {})
    payroll = aggregate.get('payroll', {})
    analytics = aggregate.get('analytics', {})
    approvals = [*attendance.get('approvals', []), *payroll.get('approvals', []), *analytics.get('approvals', [])]
    items: list[dict[str, Any]] = []
    for approval in approvals:
        if approval.get('status') != 'pending':
            continue
        age_hours = float(approval.get('age_hours', 0) or 0)
        severity = 'critical' if age_hours >= 24 else 'high' if age_hours >= 8 else 'medium'
        items.append(
            {
                'approval_id': approval.get('id'),
                'approval_type': approval.get('type'),
                'employee_id': approval.get('employee_id'),
                'employee_name': approval.get('employee_name'),
                'age_hours': age_hours,
                'severity': severity,
                'reason': 'Pending manager approval nearing or breaching SLA.',
                'actions': ['approve', 'reject_with_reason', 'request_clarification'],
                'due_at': approval.get('due_at'),
            }
        )

    return _success({'endpoint': '/approvals', 'source': ['attendance', 'payroll', 'analytics'], 'items': _sorted_issues(items)}, trace)


def get_burnout(aggregate: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
    trace = trace_id or new_trace_id()
    analytics = aggregate.get('analytics', {})
    items: list[dict[str, Any]] = []
    for signal in analytics.get('workload_signals', []):
        high_load_days = int(signal.get('high_load_days', 0) or 0)
        overtime_hours = float(signal.get('overtime_hours', 0) or 0)
        leave_days_used = int(signal.get('leave_days_used', 0) or 0)
        after_hours_sessions = int(signal.get('after_hours_sessions', 0) or 0)
        if high_load_days < 5 and overtime_hours < 10 and after_hours_sessions < 4:
            continue

        severity = 'medium'
        if high_load_days >= 10 or (overtime_hours >= 20 and leave_days_used == 0):
            severity = 'critical'
        elif high_load_days >= 7 or overtime_hours >= 15 or after_hours_sessions >= 8:
            severity = 'high'

        items.append(
            {
                'employee_id': signal.get('employee_id'),
                'employee_name': signal.get('employee_name'),
                'high_load_days': high_load_days,
                'overtime_hours': overtime_hours,
                'leave_days_used': leave_days_used,
                'after_hours_sessions': after_hours_sessions,
                'severity': severity,
                'reason': 'Burnout risk pattern detected from workload and after-hours behavior.',
                'actions': ['schedule_check_in', 'enforce_rest_period', 'adjust_workload'],
                'due_at': signal.get('due_at'),
            }
        )

    return _success({'endpoint': '/burnout', 'source': ['analytics'], 'items': _sorted_issues(items)}, trace)


def get_performance(aggregate: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
    trace = trace_id or new_trace_id()
    analytics = aggregate.get('analytics', {})
    items: list[dict[str, Any]] = []
    for row in analytics.get('performance_signals', []):
        current = float(row.get('current_score', 0) or 0)
        baseline = float(row.get('baseline_score', 0) or 0)
        target = float(row.get('target_score', 0) or 0)
        if current >= target and current >= baseline * 0.9:
            continue

        drop_ratio = 0.0 if baseline == 0 else (baseline - current) / baseline
        severity = 'medium'
        if drop_ratio >= 0.25 or current < target * 0.75:
            severity = 'critical'
        elif drop_ratio >= 0.15 or current < target * 0.9:
            severity = 'high'

        items.append(
            {
                'employee_id': row.get('employee_id'),
                'employee_name': row.get('employee_name'),
                'current_score': current,
                'baseline_score': baseline,
                'target_score': target,
                'drop_ratio': round(drop_ratio, 4),
                'severity': severity,
                'reason': 'Performance trend indicates active intervention is required.',
                'actions': ['assign_coaching_plan', 'reprioritize_goals', 'schedule_review'],
                'due_at': row.get('due_at'),
            }
        )

    return _success({'endpoint': '/performance', 'source': ['analytics'], 'items': _sorted_issues(items)}, trace)
