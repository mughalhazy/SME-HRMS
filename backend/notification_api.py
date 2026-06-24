from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

from api_contract import error_response, success_response
from event_contract import normalize_event_type
from notification_service import NotificationService, NotificationServiceError, serialize_message, serialize_preference
from resilience import new_trace_id
from tenant_support import normalize_tenant_id

_ERROR_STATUS_BY_CODE = {
    "VALIDATION_ERROR": 422,
    "UNSUPPORTED_EVENT": 422,
    "TEMPLATE_NOT_FOUND": 404,
    "MESSAGE_NOT_FOUND": 404,
    "FORBIDDEN": 403,
}


def _error_response(code: str, message: str, *, details: list[dict[str, Any]] | None = None, trace_id: str) -> tuple[int, dict[str, Any]]:
    return error_response(_ERROR_STATUS_BY_CODE.get(code, 400), code, message, request_id=trace_id, details=details)


def _tenant_id_from(source: dict[str, Any] | None = None, fallback: dict[str, Any] | None = None) -> str:
    value = (source or {}).get("tenant_id") or (fallback or {}).get("tenant_id")
    return normalize_tenant_id(str(value)) if value else ""


def _limit_and_cursor(params: dict[str, Any]) -> tuple[int, str | None]:
    limit = int(params.get("limit", 25) or 25)
    cursor = str(params["cursor"]) if "cursor" in params and params["cursor"] is not None else None
    return limit, cursor


def with_error_handling(handler: Callable[..., tuple[int, dict[str, Any]]]) -> Callable[..., tuple[int, dict[str, Any]]]:
    def wrapped(*args: Any, **kwargs: Any) -> tuple[int, dict[str, Any]]:
        trace_id = kwargs.pop("trace_id", None) or new_trace_id()
        service = args[0]
        operation = getattr(handler, "__name__", "notification.operation")
        started = perf_counter()
        try:
            status, payload = handler(*args, trace_id=trace_id, **kwargs)
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=True, context={"status": status})
            pagination = payload.pop("_pagination", None) if isinstance(payload, dict) else None
            return success_response(status, payload, request_id=trace_id, pagination=pagination)
        except NotificationServiceError as exc:
            service.observability.logger.error(operation, trace_id=trace_id, context={"code": exc.code, "details": exc.details})
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={"status": _ERROR_STATUS_BY_CODE.get(exc.code, 400), "code": exc.code})
            return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)
        except (KeyError, TypeError, ValueError) as exc:
            service.observability.logger.error(operation, trace_id=trace_id, context={"error": str(exc)})
            service.observability.track(operation, trace_id=trace_id, started_at=started, success=False, context={"status": 422, "code": "VALIDATION_ERROR"})
            return _error_response("VALIDATION_ERROR", "Invalid request payload", trace_id=trace_id)

    return wrapped


@with_error_handling
def post_notification_event(service: NotificationService, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    messages = service.ingest_event(payload, trace_id=trace_id)
    return 202, {
        "event_name": payload.get("event_name") or payload.get("type"),
        "event_type": normalize_event_type(str(payload.get("event_type") or payload.get("event_name") or payload.get("type") or "")),
        "notifications": [serialize_message(message) for message in messages],
        "count": len(messages),
    }


@with_error_handling
def get_notification_message(service: NotificationService, message_id: str, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    tenant_id = _tenant_id_from(query)
    return 200, serialize_message(service.get_message(message_id=message_id, tenant_id=tenant_id or None))


@with_error_handling
def get_notification_preferences(service: NotificationService, subject_id: str, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    tenant_id = _tenant_id_from(params)
    if not tenant_id:
        raise NotificationServiceError("VALIDATION_ERROR", "tenant_id is required")
    subject_type = str(params.get("subject_type") or "Employee")
    topic_code = params.get("topic_code")
    limit, cursor = _limit_and_cursor(params)
    rows, pagination = service.get_preferences(
        tenant_id=tenant_id,
        subject_type=subject_type,
        subject_id=subject_id,
        topic_code=str(topic_code) if topic_code else None,
        limit=limit,
        cursor=cursor,
    )
    return 200, {"items": [serialize_preference(row) for row in rows], "_pagination": pagination}


@with_error_handling
def patch_notification_preferences(service: NotificationService, subject_id: str, payload: dict[str, Any], *, trace_id: str) -> tuple[int, dict[str, Any]]:
    tenant_id = _tenant_id_from(payload)
    if not tenant_id:
        raise NotificationServiceError("VALIDATION_ERROR", "tenant_id is required")
    subject_type = str(payload.get("subject_type") or "Employee")
    topic_code = str(payload["topic_code"])
    patch = {key: value for key, value in payload.items() if key not in {"tenant_id", "subject_type", "topic_code", "actor"}}
    preference = service.update_preferences(
        tenant_id=tenant_id,
        subject_type=subject_type,
        subject_id=subject_id,
        topic_code=topic_code,
        patch=patch,
        actor=payload.get("actor") if isinstance(payload.get("actor"), dict) else None,
        trace_id=trace_id,
    )
    return 200, serialize_preference(preference)


@with_error_handling
def get_notification_delivery(service: NotificationService, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    tenant_id = _tenant_id_from(params)
    if not tenant_id:
        raise NotificationServiceError("VALIDATION_ERROR", "tenant_id is required")
    limit, cursor = _limit_and_cursor(params)
    rows, pagination = service.list_delivery(
        tenant_id=tenant_id,
        subject_id=str(params["subject_id"]) if "subject_id" in params else None,
        status=str(params["status"]) if "status" in params else None,
        channel=str(params["channel"]) if "channel" in params else None,
        limit=limit,
        cursor=cursor,
    )
    return 200, {"items": rows, "_pagination": pagination}


@with_error_handling
def get_notification_inbox(service: NotificationService, subject_id: str, query: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    params = query or {}
    tenant_id = _tenant_id_from(params)
    if not tenant_id:
        raise NotificationServiceError("VALIDATION_ERROR", "tenant_id is required")
    unread_only = str(params.get("unread_only", "false")).lower() == "true"
    limit, cursor = _limit_and_cursor(params)
    inbox, pagination = service.get_inbox(tenant_id=tenant_id, subject_id=subject_id, unread_only=unread_only, limit=limit, cursor=cursor)
    inbox["_pagination"] = pagination
    return 200, inbox


@with_error_handling
def post_notification_inbox_read(service: NotificationService, subject_id: str, message_id: str, payload: dict[str, Any] | None = None, *, trace_id: str) -> tuple[int, dict[str, Any]]:
    request = payload or {}
    tenant_id = _tenant_id_from(request)
    if not tenant_id:
        raise NotificationServiceError("VALIDATION_ERROR", "tenant_id is required")
    message = service.mark_inbox_item_read(
        tenant_id=tenant_id,
        subject_id=subject_id,
        message_id=message_id,
        actor=request.get("actor") if isinstance(request.get("actor"), dict) else None,
        trace_id=trace_id,
    )
    return 200, serialize_message(message)
