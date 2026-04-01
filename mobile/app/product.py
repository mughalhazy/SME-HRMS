from __future__ import annotations

from typing import Any

from api_contract import error_response
from mobile.session import MobileSessionError, MobileSessionManager
from resilience import new_trace_id
from services.mobile_gateway import MobileGatewayService

SERVICE_NAME = 'mobile-app'


class MobileAppService:
    """Real mobile product layer exposing mobile-first user flows."""

    def __init__(self, *, session_secret: str = 'mobile-dev-secret-123456', gateway: MobileGatewayService | None = None) -> None:
        self.gateway = gateway or MobileGatewayService()
        self.sessions = MobileSessionManager(session_secret)

    def _authorize(self, authorization: str | None, trace_id: str) -> tuple[bool, dict[str, Any] | None, tuple[int, dict[str, Any]] | None]:
        try:
            actor = self.sessions.validate_token(authorization)
            return True, actor, None
        except MobileSessionError as exc:
            return (
                False,
                None,
                error_response(
                    401,
                    'TOKEN_INVALID',
                    str(exc),
                    request_id=trace_id,
                    service=SERVICE_NAME,
                ),
            )

    def _aggregate(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        data = payload or {}
        return {
            'decisions': data.get('decisions', []),
            'payroll': data.get('payroll', []),
            'attendance': data.get('attendance', []),
            'notifications': data.get('notifications', []),
        }

    def get_dashboard(self, payload: dict[str, Any] | None, *, authorization: str | None, page: int = 1, page_size: int = 5, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        rid = trace_id or new_trace_id()
        ok, _, err = self._authorize(authorization, rid)
        if not ok:
            return err  # type: ignore[return-value]
        return self.gateway.dashboard(self._aggregate(payload), page=page, page_size=page_size, request_id=rid)

    def get_payslip_view(self, payload: dict[str, Any] | None, *, authorization: str | None, page: int = 1, page_size: int = 10, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        rid = trace_id or new_trace_id()
        ok, _, err = self._authorize(authorization, rid)
        if not ok:
            return err  # type: ignore[return-value]
        return self.gateway.payslip_view(self._aggregate(payload), page=page, page_size=page_size, request_id=rid)

    def post_leave_apply(self, payload: dict[str, Any] | None, *, authorization: str | None, page: int = 1, page_size: int = 5, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        rid = trace_id or new_trace_id()
        ok, _, err = self._authorize(authorization, rid)
        if not ok:
            return err  # type: ignore[return-value]
        return self.gateway.leave_apply(self._aggregate(payload), page=page, page_size=page_size, request_id=rid)

    def get_alerts(self, payload: dict[str, Any] | None, *, authorization: str | None, page: int = 1, page_size: int = 10, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        rid = trace_id or new_trace_id()
        ok, _, err = self._authorize(authorization, rid)
        if not ok:
            return err  # type: ignore[return-value]
        return self.gateway.alerts(self._aggregate(payload), page=page, page_size=page_size, request_id=rid)
