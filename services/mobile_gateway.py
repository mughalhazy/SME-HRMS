from __future__ import annotations

from typing import Any

from mobile.contracts import MOBILE_ENDPOINTS, build_mobile_response
from resilience import new_trace_id


class MobileGatewayService:
    """Low-bandwidth, decision-first mobile gateway with basic in-memory caching."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[int, dict[str, Any]]] = {}

    @staticmethod
    def _slice(items: list[dict[str, Any]], page: int, page_size: int) -> tuple[list[dict[str, Any]], str | None, str | None]:
        safe_page = max(page, 1)
        safe_size = max(min(page_size, 25), 1)
        start = (safe_page - 1) * safe_size
        end = start + safe_size
        paged_items = items[start:end]
        cursor = str(safe_page)
        next_cursor = str(safe_page + 1) if end < len(items) else None
        return paged_items, cursor, next_cursor

    @staticmethod
    def _decision_cards(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for row in decisions:
            cards.append(
                {
                    'id': row.get('id'),
                    'type': row.get('type', 'decision'),
                    'severity': row.get('severity', 'medium'),
                    'title': row.get('title', 'Action required'),
                    'why': row.get('why', 'Manager decision required now.'),
                    'action': row.get('primary_action', 'review_now'),
                    'due_at': row.get('due_at'),
                }
            )
        cards.sort(key=lambda item: ({'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(item['severity'], 4), item.get('due_at') or ''))
        return cards

    def _build(
        self,
        *,
        cache_key: str,
        endpoint: str,
        source: list[str],
        items: list[dict[str, Any]],
        request_id: str,
        page: int,
        page_size: int,
        fallback_item: dict[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        if cache_key in self._cache:
            return self._cache[cache_key]

        fallback_used = len(items) == 0
        final_items = items if items else [fallback_item]
        paged, cursor, next_cursor = self._slice(final_items, page, page_size)

        response = build_mobile_response(
            endpoint,
            items=paged,
            request_id=request_id,
            cursor=cursor,
            next_cursor=next_cursor,
            page_size=page_size,
            source=source,
            fallback_used=fallback_used,
        )
        self._cache[cache_key] = response
        return response

    def dashboard(self, aggregate: dict[str, Any], *, page: int = 1, page_size: int = 5, request_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = request_id or new_trace_id()
        cards = self._decision_cards(aggregate.get('decisions', []))
        return self._build(
            cache_key=f'dashboard:{page}:{page_size}:{len(cards)}',
            endpoint=MOBILE_ENDPOINTS['dashboard'],
            source=['decisions'],
            items=cards,
            request_id=trace,
            page=page,
            page_size=page_size,
            fallback_item={
                'id': 'fallback-dashboard',
                'type': 'decision',
                'severity': 'low',
                'title': 'No urgent actions',
                'why': 'No critical decision cards are active.',
                'action': 'refresh',
                'due_at': None,
            },
        )

    def payslip_view(self, aggregate: dict[str, Any], *, page: int = 1, page_size: int = 10, request_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = request_id or new_trace_id()
        items = [
            {
                'id': p.get('id'),
                'period': p.get('period'),
                'net_pay': p.get('net_pay'),
                'currency': p.get('currency', 'PKR'),
                'action': 'view_payslip',
            }
            for p in aggregate.get('payroll', [])
        ]
        return self._build(
            cache_key=f'payslip:{page}:{page_size}:{len(items)}',
            endpoint=MOBILE_ENDPOINTS['payslip_view'],
            source=['payroll'],
            items=items,
            request_id=trace,
            page=page,
            page_size=page_size,
            fallback_item={'id': 'fallback-payslip', 'period': None, 'net_pay': '0.00', 'currency': 'PKR', 'action': 'refresh'},
        )

    def leave_apply(self, aggregate: dict[str, Any], *, page: int = 1, page_size: int = 5, request_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = request_id or new_trace_id()
        items = [
            {
                'id': l.get('id'),
                'leave_type': l.get('leave_type'),
                'balance_days': l.get('balance_days'),
                'action': 'apply_leave',
            }
            for l in aggregate.get('attendance', [])
        ]
        return self._build(
            cache_key=f'leave:{page}:{page_size}:{len(items)}',
            endpoint=MOBILE_ENDPOINTS['leave_apply'],
            source=['attendance'],
            items=items,
            request_id=trace,
            page=page,
            page_size=page_size,
            fallback_item={'id': 'fallback-leave', 'leave_type': 'annual', 'balance_days': 0, 'action': 'apply_leave'},
        )

    def alerts(self, aggregate: dict[str, Any], *, page: int = 1, page_size: int = 10, request_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = request_id or new_trace_id()
        items = [
            {
                'id': n.get('id'),
                'severity': n.get('severity', 'medium'),
                'title': n.get('title', 'Alert'),
                'action': n.get('action', 'open_alert'),
            }
            for n in aggregate.get('notifications', [])
        ]
        return self._build(
            cache_key=f'alerts:{page}:{page_size}:{len(items)}',
            endpoint=MOBILE_ENDPOINTS['alerts'],
            source=['notifications'],
            items=items,
            request_id=trace,
            page=page,
            page_size=page_size,
            fallback_item={'id': 'fallback-alert', 'severity': 'low', 'title': 'No active alerts', 'action': 'refresh'},
        )
