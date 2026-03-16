from __future__ import annotations

from uuid import uuid4

from service import AuthService, AuthServiceError

_ERROR_STATUS_BY_CODE = {
    "VALIDATION_ERROR": 422,
    "INVALID_CREDENTIALS": 401,
    "ACCOUNT_DISABLED": 403,
    "TOKEN_INVALID": 401,
    "TOKEN_EXPIRED": 401,
    "TOKEN_REVOKED": 401,
    "FORBIDDEN": 403,
    "USER_EXISTS": 409,
    "ROLE_INVALID": 422,
}


def post_auth_login(service: AuthService, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    if not isinstance(payload, dict):
        return _error_response("VALIDATION_ERROR", "Request body must be an object", trace_id=trace_id)

    username = payload.get("username")
    password = payload.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return _error_response(
            "VALIDATION_ERROR",
            "username and password are required",
            details=[{"field": "username/password", "reason": "must be non-empty strings"}],
            trace_id=trace_id,
        )

    try:
        token_payload = service.login(username=username, password=password)
        return 200, {"data": token_payload}
    except AuthServiceError as exc:
        return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)


def get_auth_me(service: AuthService, authorization_header: str | None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    if not authorization_header or not authorization_header.startswith("Bearer "):
        return _error_response("TOKEN_INVALID", "Missing bearer token", trace_id=trace_id)

    token = authorization_header.split(" ", 1)[1]
    try:
        principal = service.authenticate_token(token)
        return (
            200,
            {
                "data": {
                    "user_id": str(principal.user_id),
                    "employee_id": str(principal.employee_id) if principal.employee_id else None,
                    "role": principal.role,
                    "department_id": str(principal.department_id) if principal.department_id else None,
                }
            },
        )
    except AuthServiceError as exc:
        return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)


def _error_response(code: str, message: str, *, details: list | None = None, trace_id: str) -> tuple[int, dict]:
    return (
        _ERROR_STATUS_BY_CODE.get(code, 400),
        {
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "traceId": trace_id,
            }
        },
    )
