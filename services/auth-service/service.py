from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from event_contract import EventRegistry
from outbox_system import OutboxManager
from persistent_store import PersistentKVStore
from resilience import Observability
from tenant_support import DEFAULT_TENANT_ID, normalize_tenant_id


class AuthServiceError(Exception):
    def __init__(self, code: str, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    user_id: UUID
    employee_id: UUID | None
    role: str
    department_id: UUID | None
    tenant_id: str


@dataclass
class UserAccount:
    user_id: UUID
    tenant_id: str
    username: str
    password_hash: str
    role: str
    employee_id: UUID | None = None
    department_id: UUID | None = None
    active: bool = True
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SessionRecord:
    session_id: str
    user_id: UUID
    refresh_token_hash: str
    refresh_expires_at: datetime
    started_at: datetime
    last_rotated_at: datetime
    revoked: bool = False
    revoked_at: datetime | None = None


class AuthService:
    """In-memory auth service with login, bearer token auth, refresh-token rotation, and role validation."""

    _ROLE_CAPABILITY_MAP: dict[str, set[str]] = {
        'Admin': {
            'CAP-EMP-001',
            'CAP-EMP-002',
            'CAP-ATT-001',
            'CAP-ATT-002',
            'CAP-LEV-001',
            'CAP-LEV-002',
            'CAP-PAY-001',
            'CAP-PAY-002',
            'CAP-HIR-001',
            'CAP-HIR-002',
            'CAP-PRF-001',
            'CAP-AUT-001',
        },
        'Manager': {
            'CAP-EMP-001',
            'CAP-EMP-002',
            'CAP-ATT-001',
            'CAP-ATT-002',
            'CAP-LEV-001',
            'CAP-LEV-002',
            'CAP-PAY-001',
            'CAP-HIR-001',
            'CAP-HIR-002',
            'CAP-PRF-001',
        },
        'Employee': {
            'CAP-EMP-001',
            'CAP-EMP-002',
            'CAP-ATT-001',
            'CAP-LEV-001',
            'CAP-PAY-001',
            'CAP-HIR-001',
            'CAP-PRF-001',
        },
        'Recruiter': {
            'CAP-HIR-001',
            'CAP-HIR-002',
        },
        'PayrollAdmin': {
            'CAP-PAY-001',
            'CAP-PAY-002',
        },
        'Service': set(),
    }

    def __init__(self, token_secret: str, issuer: str = 'sme-hrms.auth-service', audience: str = 'sme-hrms.api', db_path: str | None = None):
        if not token_secret:
            raise ValueError('token_secret is required')
        if len(token_secret) < 32:
            raise ValueError('token_secret must be at least 32 characters for production-grade entropy')
        self._token_secret = token_secret.encode('utf-8')
        self._issuer = issuer
        self._audience = audience
        self._users_by_name = PersistentKVStore[str, UserAccount](service='auth-service', namespace='users_by_name', db_path=db_path)
        shared_db_path = self._users_by_name.db_path
        self._users_by_id = PersistentKVStore[UUID, UserAccount](service='auth-service', namespace='users_by_id', db_path=shared_db_path)
        self._sessions_by_id = PersistentKVStore[str, SessionRecord](service='auth-service', namespace='sessions_by_id', db_path=shared_db_path)
        self.observability = Observability('auth-service')
        self.events: list[dict[str, Any]] = []
        self.event_registry = EventRegistry()
        self.outbox = OutboxManager(
            service_name='auth-service',
            tenant_id=DEFAULT_TENANT_ID,
            db_path=shared_db_path,
            observability=self.observability,
            event_registry=self.event_registry,
        )

    @staticmethod
    def _user_payload(user: UserAccount) -> dict[str, Any]:
        return {
            'user_id': str(user.user_id),
            'tenant_id': user.tenant_id,
            'username': user.username,
            'role': user.role,
            'employee_id': str(user.employee_id) if user.employee_id else None,
            'department_id': str(user.department_id) if user.department_id else None,
            'active': user.active,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
        }

    def _session_payload(self, session: SessionRecord) -> dict[str, Any]:
        user = self._users_by_id.get(session.user_id)
        return {
            'session_id': session.session_id,
            'user_id': str(session.user_id),
            'tenant_id': user.tenant_id if user else DEFAULT_TENANT_ID,
            'role': user.role if user else None,
            'refresh_expires_at': session.refresh_expires_at.isoformat(),
            'started_at': session.started_at.isoformat(),
            'last_rotated_at': session.last_rotated_at.isoformat(),
            'revoked': session.revoked,
            'revoked_at': session.revoked_at.isoformat() if session.revoked_at else None,
        }

    def _audit_auth_mutation(self, action: str, actor_id: str | None, entity: str, entity_id: str, tenant_id: str, before: dict[str, Any], after: dict[str, Any], *, role: str | None = None, trace_id: str | None = None) -> None:
        self.observability.logger.audit(
            action,
            trace_id=trace_id,
            actor={'id': actor_id or 'system', 'type': 'user' if actor_id else 'system', 'role': role},
            entity=entity,
            entity_id=entity_id,
            context={'tenant_id': tenant_id, 'before': before, 'after': after},
        )

    def register_user(
        self,
        *,
        username: str,
        password: str,
        role: str,
        employee_id: UUID | None = None,
        department_id: UUID | None = None,
        tenant_id: str = DEFAULT_TENANT_ID,
    ) -> UserAccount:
        tenant_id = normalize_tenant_id(tenant_id)
        normalized_username = username.strip().lower()
        if role not in self._ROLE_CAPABILITY_MAP:
            raise AuthServiceError('ROLE_INVALID', 'Role is not supported')
        if not normalized_username or not password:
            raise AuthServiceError('VALIDATION_ERROR', 'username and password are required')
        if len(normalized_username) > 128:
            raise AuthServiceError('VALIDATION_ERROR', 'username exceeds maximum length')
        if len(password) > 1024:
            raise AuthServiceError('VALIDATION_ERROR', 'password exceeds maximum length')
        user_lookup_key = self._user_lookup_key(tenant_id, normalized_username)
        if user_lookup_key in self._users_by_name:
            raise AuthServiceError('USER_EXISTS', 'User already exists')

        now = datetime.now(timezone.utc)
        user = UserAccount(
            user_id=uuid4(),
            tenant_id=tenant_id,
            username=normalized_username,
            password_hash=self._hash_password(password),
            role=role,
            employee_id=employee_id,
            department_id=department_id,
            created_at=now,
            updated_at=now,
        )
        self._users_by_name[user_lookup_key] = user
        self._users_by_id[user.user_id] = user
        self._audit_auth_mutation('auth_user_registered', str(user.user_id), 'UserAccount', str(user.user_id), tenant_id, {}, self._user_payload(user), role=role)
        return user

    def login(self, username: str, password: str, *, tenant_id: str = DEFAULT_TENANT_ID, ttl_seconds: int = 900, refresh_ttl_seconds: int = 604800) -> dict[str, Any]:
        self._validate_ttls(ttl_seconds, refresh_ttl_seconds)
        tenant_id = normalize_tenant_id(tenant_id)
        normalized_username = username.strip().lower()
        user = self._users_by_name.get(self._user_lookup_key(tenant_id, normalized_username))
        if not user or not self._verify_password(password, user.password_hash):
            raise AuthServiceError('INVALID_CREDENTIALS', 'Invalid username or password')
        if not user.active:
            raise AuthServiceError('ACCOUNT_DISABLED', 'User account is disabled')

        user.last_login_at = datetime.now(timezone.utc)
        user.updated_at = user.last_login_at
        token_payload = self._issue_session_tokens(user=user, ttl_seconds=ttl_seconds, refresh_ttl_seconds=refresh_ttl_seconds)
        self.observability.logger.info(
            'auth.login_succeeded',
            context={'username': normalized_username, 'role': user.role, 'session_id': token_payload['session_id'], 'tenant_id': user.tenant_id},
        )
        return token_payload

    def refresh_session(self, refresh_token: str, *, ttl_seconds: int = 900, refresh_ttl_seconds: int = 604800) -> dict[str, Any]:
        self._validate_ttls(ttl_seconds, refresh_ttl_seconds)
        session = self._get_session_by_refresh_token(refresh_token)
        if session.revoked:
            raise AuthServiceError('TOKEN_REVOKED', 'Session has been revoked')
        if session.refresh_expires_at <= datetime.now(timezone.utc):
            self._revoke_session(session.session_id, actor=str(session.user_id), role=self._users_by_id.get(session.user_id).role if self._users_by_id.get(session.user_id) else None)
            raise AuthServiceError('TOKEN_EXPIRED', 'Refresh token has expired')

        user = self._users_by_id.get(session.user_id)
        if not user or not user.active:
            self._revoke_session(session.session_id, actor=str(session.user_id), role=user.role if user else None)
            raise AuthServiceError('ACCOUNT_DISABLED', 'User account is disabled')

        before = self._session_payload(session)
        now = datetime.now(timezone.utc)
        rotated_refresh_token = self._generate_refresh_token()
        session.refresh_token_hash = self._hash_refresh_token(rotated_refresh_token)
        session.refresh_expires_at = now + timedelta(seconds=refresh_ttl_seconds)
        session.last_rotated_at = now
        token_payload = self._build_token_payload(
            user=user,
            session_id=session.session_id,
            ttl_seconds=ttl_seconds,
            refresh_token=rotated_refresh_token,
            refresh_ttl_seconds=refresh_ttl_seconds,
        )
        self._audit_auth_mutation('auth_refresh_rotated', str(user.user_id), 'Session', session.session_id, user.tenant_id, before, self._session_payload(session), role=user.role)
        return token_payload

    def authenticate_token(self, token: str) -> AuthenticatedPrincipal:
        claims = self._decode_token(token)
        sid = claims.get('sid')
        session = self._sessions_by_id.get(sid) if isinstance(sid, str) else None
        if not sid or not session or session.revoked:
            raise AuthServiceError('TOKEN_REVOKED', 'Session has been revoked')
        if session.refresh_expires_at <= datetime.now(timezone.utc):
            self._revoke_session(session.session_id, actor=str(session.user_id), role=self._users_by_id.get(session.user_id).role if self._users_by_id.get(session.user_id) else None)
            raise AuthServiceError('TOKEN_EXPIRED', 'Session has expired')

        try:
            user_id = UUID(claims['sub'])
        except (KeyError, ValueError) as exc:
            raise AuthServiceError('TOKEN_INVALID', 'Token subject is invalid') from exc

        user = self._users_by_id.get(user_id)
        if not user or not user.active:
            raise AuthServiceError('ACCOUNT_DISABLED', 'User account is disabled')

        employee_id = UUID(claims['employee_id']) if claims.get('employee_id') else None
        department_id = UUID(claims['department_id']) if claims.get('department_id') else None
        return AuthenticatedPrincipal(
            user_id=user_id,
            employee_id=employee_id,
            role=claims['role'],
            department_id=department_id,
            tenant_id=normalize_tenant_id(str(claims.get('tenant_id') or user.tenant_id)),
        )

    def logout(self, token: str) -> None:
        claims = self._decode_token(token)
        sid = claims.get('sid')
        if isinstance(sid, str):
            self._revoke_session(sid, actor=claims.get('sub'), role=claims.get('role'))

    def logout_refresh_token(self, refresh_token: str) -> None:
        session = self._get_session_by_refresh_token(refresh_token)
        self._revoke_session(session.session_id, actor=str(session.user_id), role=self._users_by_id.get(session.user_id).role if self._users_by_id.get(session.user_id) else None)

    def get_current_session(self, token: str) -> dict[str, Any]:
        claims = self._decode_token(token)
        sid = claims.get('sid')
        if not isinstance(sid, str):
            raise AuthServiceError('TOKEN_INVALID', 'Token session is invalid')
        session = self._sessions_by_id.get(sid)
        if not session or session.revoked:
            raise AuthServiceError('TOKEN_REVOKED', 'Session has been revoked')

        principal = self.authenticate_token(token)
        return self._serialize_session(session, principal.role, principal.tenant_id)

    def list_sessions(self, *, user_id: UUID | None = None, status: str | None = None, tenant_id: str | None = None) -> list[dict[str, Any]]:
        if status is not None and status not in {'Active', 'Revoked', 'Expired'}:
            raise AuthServiceError('VALIDATION_ERROR', 'status filter is invalid', details=[{'field': 'status', 'reason': 'must be Active, Revoked, or Expired'}])

        rows = []
        now = datetime.now(timezone.utc)
        normalized_tenant_id = normalize_tenant_id(tenant_id) if tenant_id is not None else None
        for session in self._sessions_by_id.values():
            if user_id is not None and session.user_id != user_id:
                continue
            user = self._users_by_id.get(session.user_id)
            if normalized_tenant_id is not None and (not user or user.tenant_id != normalized_tenant_id):
                continue
            session_status = self._session_status(session, now=now)
            if status is not None and session_status != status:
                continue
            rows.append(self._serialize_session(session, user.role if user else None, user.tenant_id if user else None, now=now))
        rows.sort(key=lambda row: row['started_at'], reverse=True)
        return rows

    def revoke_session(self, session_id: str, *, actor: str | None = None) -> dict[str, Any]:
        session = self._sessions_by_id.get(session_id)
        if not session:
            raise AuthServiceError('TOKEN_INVALID', 'Session is invalid')
        user = self._users_by_id.get(session.user_id)
        self._revoke_session(session_id, actor=actor or str(session.user_id), role=user.role if user else None)
        return self._serialize_session(session, user.role if user else None, user.tenant_id if user else None)

    def validate_role(self, principal: AuthenticatedPrincipal, capability_id: str) -> bool:
        allowed = self._ROLE_CAPABILITY_MAP.get(principal.role, set())
        return capability_id in allowed

    def require_capability(self, principal: AuthenticatedPrincipal, capability_id: str) -> None:
        if not self.validate_role(principal, capability_id):
            raise AuthServiceError('FORBIDDEN', 'Insufficient permissions for requested capability')


    @staticmethod
    def _user_lookup_key(tenant_id: str, username: str) -> str:
        return f"{normalize_tenant_id(tenant_id)}::{username.strip().lower()}"

    def health_snapshot(self) -> dict[str, Any]:
        revoked_sessions = sum(1 for session in self._sessions_by_id.values() if session.revoked)
        return self.observability.health_status(
            checks={
                'users': len(self._users_by_id),
                'sessions': len(self._sessions_by_id),
                'revoked_sessions': revoked_sessions,
            }
        )

    def _issue_session_tokens(self, *, user: UserAccount, ttl_seconds: int, refresh_ttl_seconds: int) -> dict[str, Any]:
        session_id = str(uuid4())
        refresh_token = self._generate_refresh_token()
        now = datetime.now(timezone.utc)
        self._sessions_by_id[session_id] = SessionRecord(
            session_id=session_id,
            user_id=user.user_id,
            refresh_token_hash=self._hash_refresh_token(refresh_token),
            refresh_expires_at=now + timedelta(seconds=refresh_ttl_seconds),
            started_at=now,
            last_rotated_at=now,
        )
        return self._build_token_payload(
            user=user,
            session_id=session_id,
            ttl_seconds=ttl_seconds,
            refresh_token=refresh_token,
            refresh_ttl_seconds=refresh_ttl_seconds,
        )

    def _build_token_payload(
        self,
        *,
        user: UserAccount,
        session_id: str,
        ttl_seconds: int,
        refresh_token: str,
        refresh_ttl_seconds: int,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        claims = {
            'sub': str(user.user_id),
            'sid': session_id,
            'tenant_id': user.tenant_id,
            'role': user.role,
            'employee_id': str(user.employee_id) if user.employee_id else None,
            'department_id': str(user.department_id) if user.department_id else None,
            'iat': int(now.timestamp()),
            'nbf': int(now.timestamp()),
            'exp': int((now + timedelta(seconds=ttl_seconds)).timestamp()),
            'iss': self._issuer,
            'aud': self._audience,
        }
        token = self._encode_token(claims)
        return {
            'access_token': token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': ttl_seconds,
            'refresh_expires_in': refresh_ttl_seconds,
            'session_id': session_id,
        }

    def _revoke_session(self, session_id: str, *, actor: str | None, role: str | None) -> None:
        session = self._sessions_by_id.get(session_id)
        if not session:
            return
        if session.revoked:
            return
        before = self._session_payload(session)
        session.revoked = True
        session.revoked_at = datetime.now(timezone.utc)
        user = self._users_by_id.get(session.user_id)
        self._audit_auth_mutation('auth_logout', actor, 'Session', session_id, user.tenant_id if user else DEFAULT_TENANT_ID, before, self._session_payload(session), role=role)

    def _get_session_by_refresh_token(self, refresh_token: str) -> SessionRecord:
        if not refresh_token:
            raise AuthServiceError('TOKEN_INVALID', 'refresh_token is required')
        hashed = self._hash_refresh_token(refresh_token)
        for session in self._sessions_by_id.values():
            if hmac.compare_digest(session.refresh_token_hash, hashed):
                return session
        raise AuthServiceError('TOKEN_INVALID', 'Refresh token is invalid')

    def _emit_event(self, event_name: str, data: dict[str, Any], *, tenant_id: str, idempotency_key: str) -> None:
        self.outbox.tenant_id = normalize_tenant_id(tenant_id)
        self.outbox.enqueue(
            legacy_event_name=event_name,
            data=data,
            idempotency_key=idempotency_key,
        )
        self.outbox.dispatch_pending(self.events.append)


    def _serialize_session(self, session: SessionRecord, role: str | None, tenant_id: str | None = None, *, now: datetime | None = None) -> dict[str, Any]:
        current_time = now or datetime.now(timezone.utc)
        return {
            'session_id': session.session_id,
            'user_id': str(session.user_id),
            'tenant_id': normalize_tenant_id(tenant_id),
            'role': role,
            'status': self._session_status(session, now=current_time),
            'started_at': session.started_at.isoformat(),
            'last_rotated_at': session.last_rotated_at.isoformat(),
            'refresh_expires_at': session.refresh_expires_at.isoformat(),
            'revoked_at': session.revoked_at.isoformat() if session.revoked_at else None,
        }

    def _session_status(self, session: SessionRecord, *, now: datetime | None = None) -> str:
        current_time = now or datetime.now(timezone.utc)
        if session.revoked:
            return 'Revoked'
        if session.refresh_expires_at <= current_time:
            return 'Expired'
        return 'Active'

    @staticmethod
    def _validate_ttls(ttl_seconds: int, refresh_ttl_seconds: int) -> None:
        if ttl_seconds < 60 or ttl_seconds > 3600:
            raise AuthServiceError('VALIDATION_ERROR', 'ttl_seconds must be between 60 and 3600')
        if refresh_ttl_seconds < 300 or refresh_ttl_seconds > 2592000:
            raise AuthServiceError('VALIDATION_ERROR', 'refresh_ttl_seconds must be between 300 and 2592000')
        if refresh_ttl_seconds <= ttl_seconds:
            raise AuthServiceError('VALIDATION_ERROR', 'refresh_ttl_seconds must be greater than ttl_seconds')

    def _encode_token(self, claims: dict[str, Any]) -> str:
        header = {'alg': 'HS256', 'typ': 'JWT'}
        header_segment = self._b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
        payload_segment = self._b64url_encode(json.dumps(claims, separators=(',', ':')).encode('utf-8'))
        signing_input = f'{header_segment}.{payload_segment}'.encode('utf-8')
        signature = hmac.new(self._token_secret, signing_input, hashlib.sha256).digest()
        signature_segment = self._b64url_encode(signature)
        return f'{header_segment}.{payload_segment}.{signature_segment}'

    def _decode_token(self, token: str) -> dict[str, Any]:
        try:
            header_segment, payload_segment, signature_segment = token.split('.')
        except ValueError as exc:
            raise AuthServiceError('TOKEN_INVALID', 'Malformed token') from exc

        signing_input = f'{header_segment}.{payload_segment}'.encode('utf-8')
        expected_signature = hmac.new(self._token_secret, signing_input, hashlib.sha256).digest()
        actual_signature = self._b64url_decode(signature_segment)
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise AuthServiceError('TOKEN_INVALID', 'Token signature is invalid')

        try:
            payload = json.loads(self._b64url_decode(payload_segment).decode('utf-8'))
        except (ValueError, json.JSONDecodeError) as exc:
            raise AuthServiceError('TOKEN_INVALID', 'Token payload is invalid') from exc
        self._validate_registered_claims(payload)
        return payload

    def _validate_registered_claims(self, payload: dict[str, Any]) -> None:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if payload.get('iss') != self._issuer or payload.get('aud') != self._audience:
            raise AuthServiceError('TOKEN_INVALID', 'Token issuer or audience is invalid')

        nbf = int(payload.get('nbf', 0))
        exp = int(payload.get('exp', 0))
        if now_ts < nbf:
            raise AuthServiceError('TOKEN_INVALID', 'Token is not active yet')
        if now_ts >= exp:
            raise AuthServiceError('TOKEN_EXPIRED', 'Token has expired')

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 390000)
        return f'{salt.hex()}:{key.hex()}'

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        try:
            salt_hex, key_hex = password_hash.split(':', 1)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(key_hex)
        except (TypeError, ValueError):
            return False

        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 390000)
        return hmac.compare_digest(actual, expected)

    @staticmethod
    def _generate_refresh_token() -> str:
        return f'{uuid4().hex}{uuid4().hex}'

    @staticmethod
    def _hash_refresh_token(refresh_token: str) -> str:
        return hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()

    @staticmethod
    def _b64url_encode(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).decode('utf-8').rstrip('=')

    @staticmethod
    def _b64url_decode(encoded: str) -> bytes:
        padding = '=' * (-len(encoded) % 4)
        return base64.urlsafe_b64decode(encoded + padding)
