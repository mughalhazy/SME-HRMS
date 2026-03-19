from __future__ import annotations

from time import perf_counter
from uuid import UUID, uuid4

from service import AuthService, AuthServiceError

_ERROR_STATUS_BY_CODE = {
    'VALIDATION_ERROR': 422,
    'INVALID_CREDENTIALS': 401,
    'ACCOUNT_DISABLED': 403,
    'TOKEN_INVALID': 401,
    'TOKEN_EXPIRED': 401,
    'TOKEN_REVOKED': 401,
    'FORBIDDEN': 403,
    'USER_EXISTS': 409,
    'ROLE_INVALID': 422,
}


def post_auth_login(service: AuthService, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    if not isinstance(payload, dict):
        service.observability.track('post_auth_login', trace_id=trace_id, started_at=started, success=False, context={'status': 422})
        return _error_response('VALIDATION_ERROR', 'Request body must be an object', trace_id=trace_id)

    username = payload.get('username')
    password = payload.get('password')
    if not isinstance(username, str) or not isinstance(password, str):
        service.observability.track('post_auth_login', trace_id=trace_id, started_at=started, success=False, context={'status': 422})
        return _error_response(
            'VALIDATION_ERROR',
            'username and password are required',
            details=[{'field': 'username/password', 'reason': 'must be non-empty strings'}],
            trace_id=trace_id,
        )

    try:
        token_payload = service.login(username=username, password=password)
        service.observability.track('post_auth_login', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return 200, {'data': token_payload}
    except AuthServiceError as exc:
        service.observability.logger.error('auth.login_failed', trace_id=trace_id, context={'code': exc.code, 'details': exc.details, 'username': username})
        service.observability.track('post_auth_login', trace_id=trace_id, started_at=started, success=False, context={'status': _ERROR_STATUS_BY_CODE.get(exc.code, 400), 'code': exc.code})
        return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)


def post_auth_refresh(service: AuthService, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    if not isinstance(payload, dict):
        service.observability.track('post_auth_refresh', trace_id=trace_id, started_at=started, success=False, context={'status': 422})
        return _error_response('VALIDATION_ERROR', 'Request body must be an object', trace_id=trace_id)

    refresh_token = payload.get('refresh_token')
    if not isinstance(refresh_token, str) or not refresh_token:
        service.observability.track('post_auth_refresh', trace_id=trace_id, started_at=started, success=False, context={'status': 422})
        return _error_response(
            'VALIDATION_ERROR',
            'refresh_token is required',
            details=[{'field': 'refresh_token', 'reason': 'must be a non-empty string'}],
            trace_id=trace_id,
        )

    try:
        token_payload = service.refresh_session(refresh_token=refresh_token)
        service.observability.track('post_auth_refresh', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return 200, {'data': token_payload}
    except AuthServiceError as exc:
        service.observability.logger.error('auth.refresh_failed', trace_id=trace_id, context={'code': exc.code, 'details': exc.details})
        service.observability.track('post_auth_refresh', trace_id=trace_id, started_at=started, success=False, context={'status': _ERROR_STATUS_BY_CODE.get(exc.code, 400), 'code': exc.code})
        return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)


def post_auth_logout(service: AuthService, payload: dict, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    if not isinstance(payload, dict):
        service.observability.track('post_auth_logout', trace_id=trace_id, started_at=started, success=False, context={'status': 422})
        return _error_response('VALIDATION_ERROR', 'Request body must be an object', trace_id=trace_id)

    refresh_token = payload.get('refresh_token')
    if not isinstance(refresh_token, str) or not refresh_token:
        service.observability.track('post_auth_logout', trace_id=trace_id, started_at=started, success=False, context={'status': 422})
        return _error_response(
            'VALIDATION_ERROR',
            'refresh_token is required',
            details=[{'field': 'refresh_token', 'reason': 'must be a non-empty string'}],
            trace_id=trace_id,
        )

    try:
        service.logout_refresh_token(refresh_token=refresh_token)
        service.observability.track('post_auth_logout', trace_id=trace_id, started_at=started, success=True, context={'status': 200})
        return 200, {'data': {'logged_out': True}}
    except AuthServiceError as exc:
        service.observability.logger.error('auth.logout_failed', trace_id=trace_id, context={'code': exc.code, 'details': exc.details})
        service.observability.track('post_auth_logout', trace_id=trace_id, started_at=started, success=False, context={'status': _ERROR_STATUS_BY_CODE.get(exc.code, 400), 'code': exc.code})
        return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)


def get_auth_me(service: AuthService, authorization_header: str | None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    if not authorization_header or not authorization_header.startswith('Bearer '):
        service.observability.track('get_auth_me', trace_id=trace_id, started_at=started, success=False, context={'status': 401, 'code': 'TOKEN_INVALID'})
        return _error_response('TOKEN_INVALID', 'Missing bearer token', trace_id=trace_id)

    token = authorization_header.split(' ', 1)[1]
    try:
        principal = service.authenticate_token(token)
        service.observability.track('get_auth_me', trace_id=trace_id, started_at=started, success=True, context={'status': 200, 'role': principal.role})
        session = service.get_current_session(token)
        return (
            200,
            {
                'data': {
                    'user_id': str(principal.user_id),
                    'employee_id': str(principal.employee_id) if principal.employee_id else None,
                    'role': principal.role,
                    'department_id': str(principal.department_id) if principal.department_id else None,
                    'session_id': session['session_id'],
                    'session_status': session['status'],
                }
            },
        )
    except AuthServiceError as exc:
        service.observability.logger.error('auth.me_failed', trace_id=trace_id, context={'code': exc.code, 'details': exc.details})
        service.observability.track('get_auth_me', trace_id=trace_id, started_at=started, success=False, context={'status': _ERROR_STATUS_BY_CODE.get(exc.code, 400), 'code': exc.code})
        return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)


def _error_response(code: str, message: str, *, details: list | None = None, trace_id: str) -> tuple[int, dict]:
    return (
        _ERROR_STATUS_BY_CODE.get(code, 400),
        {
            'error': {
                'code': code,
                'message': message,
                'details': details or [],
                'traceId': trace_id,
            }
        },
    )


def get_auth_session(service: AuthService, authorization_header: str | None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    if not authorization_header or not authorization_header.startswith('Bearer '):
        service.observability.track('get_auth_session', trace_id=trace_id, started_at=started, success=False, context={'status': 401, 'code': 'TOKEN_INVALID'})
        return _error_response('TOKEN_INVALID', 'Missing bearer token', trace_id=trace_id)

    token = authorization_header.split(' ', 1)[1]
    try:
        data = service.get_current_session(token)
        service.observability.track('get_auth_session', trace_id=trace_id, started_at=started, success=True, context={'status': 200, 'session_id': data['session_id']})
        return 200, {'data': data}
    except AuthServiceError as exc:
        service.observability.logger.error('auth.session_failed', trace_id=trace_id, context={'code': exc.code, 'details': exc.details})
        service.observability.track('get_auth_session', trace_id=trace_id, started_at=started, success=False, context={'status': _ERROR_STATUS_BY_CODE.get(exc.code, 400), 'code': exc.code})
        return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)


def get_auth_sessions(service: AuthService, query: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    params = query or {}
    user_id = params.get('user_id')
    status = params.get('status')

    parsed_user_id = None
    if user_id is not None:
        if not isinstance(user_id, str) or not user_id:
            service.observability.track('get_auth_sessions', trace_id=trace_id, started_at=started, success=False, context={'status': 422, 'code': 'VALIDATION_ERROR'})
            return _error_response('VALIDATION_ERROR', 'user_id must be a non-empty UUID string', details=[{'field': 'user_id', 'reason': 'must be a non-empty UUID string'}], trace_id=trace_id)
        try:
            parsed_user_id = UUID(user_id)
        except ValueError:
            service.observability.track('get_auth_sessions', trace_id=trace_id, started_at=started, success=False, context={'status': 422, 'code': 'VALIDATION_ERROR'})
            return _error_response('VALIDATION_ERROR', 'user_id must be a valid UUID', details=[{'field': 'user_id', 'reason': 'must be a valid UUID'}], trace_id=trace_id)

    if status is not None and (not isinstance(status, str) or not status):
        service.observability.track('get_auth_sessions', trace_id=trace_id, started_at=started, success=False, context={'status': 422, 'code': 'VALIDATION_ERROR'})
        return _error_response('VALIDATION_ERROR', 'status must be a non-empty string', details=[{'field': 'status', 'reason': 'must be a non-empty string'}], trace_id=trace_id)

    try:
        data = service.list_sessions(user_id=parsed_user_id, status=status)
        service.observability.track('get_auth_sessions', trace_id=trace_id, started_at=started, success=True, context={'status': 200, 'count': len(data)})
        return 200, {'data': data}
    except AuthServiceError as exc:
        service.observability.logger.error('auth.sessions_failed', trace_id=trace_id, context={'code': exc.code, 'details': exc.details})
        service.observability.track('get_auth_sessions', trace_id=trace_id, started_at=started, success=False, context={'status': _ERROR_STATUS_BY_CODE.get(exc.code, 400), 'code': exc.code})
        return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)


def post_auth_session_revoke(service: AuthService, session_id: str, payload: dict | None = None, trace_id: str | None = None) -> tuple[int, dict]:
    trace_id = trace_id or uuid4().hex
    started = perf_counter()
    actor = payload.get('actor') if isinstance(payload, dict) else None

    if not isinstance(session_id, str) or not session_id:
        service.observability.track('post_auth_session_revoke', trace_id=trace_id, started_at=started, success=False, context={'status': 422, 'code': 'VALIDATION_ERROR'})
        return _error_response('VALIDATION_ERROR', 'session_id is required', details=[{'field': 'session_id', 'reason': 'must be a non-empty string'}], trace_id=trace_id)

    try:
        data = service.revoke_session(session_id, actor=actor if isinstance(actor, str) and actor else None)
        service.observability.track('post_auth_session_revoke', trace_id=trace_id, started_at=started, success=True, context={'status': 200, 'session_id': session_id})
        return 200, {'data': data}
    except AuthServiceError as exc:
        service.observability.logger.error('auth.revoke_session_failed', trace_id=trace_id, context={'code': exc.code, 'details': exc.details, 'session_id': session_id})
        service.observability.track('post_auth_session_revoke', trace_id=trace_id, started_at=started, success=False, context={'status': _ERROR_STATUS_BY_CODE.get(exc.code, 400), 'code': exc.code})
        return _error_response(exc.code, exc.message, details=exc.details, trace_id=trace_id)
