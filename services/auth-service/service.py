from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from resilience import Observability


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


@dataclass
class UserAccount:
    user_id: UUID
    username: str
    password_hash: str
    role: str
    employee_id: UUID | None = None
    department_id: UUID | None = None
    active: bool = True


class AuthService:
    """In-memory auth service with login, bearer token auth, and role validation."""

    _ROLE_CAPABILITY_MAP: dict[str, set[str]] = {
        "Admin": {
            "CAP-EMP-001",
            "CAP-EMP-002",
            "CAP-ATT-001",
            "CAP-ATT-002",
            "CAP-LEV-001",
            "CAP-LEV-002",
            "CAP-PAY-001",
            "CAP-PAY-002",
            "CAP-HIR-001",
            "CAP-HIR-002",
            "CAP-PRF-001",
        },
        "Manager": {
            "CAP-EMP-001",
            "CAP-EMP-002",
            "CAP-ATT-001",
            "CAP-ATT-002",
            "CAP-LEV-001",
            "CAP-LEV-002",
            "CAP-PAY-001",
            "CAP-HIR-001",
            "CAP-HIR-002",
            "CAP-PRF-001",
        },
        "Employee": {
            "CAP-EMP-001",
            "CAP-EMP-002",
            "CAP-ATT-001",
            "CAP-LEV-001",
            "CAP-PAY-001",
            "CAP-HIR-001",
            "CAP-PRF-001",
        },
    }

    def __init__(self, token_secret: str, issuer: str = "sme-hrms.auth-service", audience: str = "sme-hrms.api"):
        if not token_secret:
            raise ValueError("token_secret is required")
        if len(token_secret) < 32:
            raise ValueError("token_secret must be at least 32 characters for production-grade entropy")
        self._token_secret = token_secret.encode("utf-8")
        self._issuer = issuer
        self._audience = audience
        self._users_by_name: dict[str, UserAccount] = {}
        self._users_by_id: dict[UUID, UserAccount] = {}
        self._revoked_session_ids: set[str] = set()
        self.observability = Observability("auth-service")

    def register_user(
        self,
        *,
        username: str,
        password: str,
        role: str,
        employee_id: UUID | None = None,
        department_id: UUID | None = None,
    ) -> UserAccount:
        normalized_username = username.strip().lower()
        if role not in self._ROLE_CAPABILITY_MAP:
            raise AuthServiceError("ROLE_INVALID", "Role is not supported")
        if not normalized_username or not password:
            raise AuthServiceError("VALIDATION_ERROR", "username and password are required")
        if len(normalized_username) > 128:
            raise AuthServiceError("VALIDATION_ERROR", "username exceeds maximum length")
        if len(password) > 1024:
            raise AuthServiceError("VALIDATION_ERROR", "password exceeds maximum length")
        if normalized_username in self._users_by_name:
            raise AuthServiceError("USER_EXISTS", "User already exists")

        user = UserAccount(
            user_id=uuid4(),
            username=normalized_username,
            password_hash=self._hash_password(password),
            role=role,
            employee_id=employee_id,
            department_id=department_id,
        )
        self._users_by_name[normalized_username] = user
        self._users_by_id[user.user_id] = user
        self.observability.logger.audit(
            "auth_user_registered",
            actor=str(user.user_id),
            entity="UserAccount",
            entity_id=str(user.user_id),
            context={"username": normalized_username, "role": role},
        )
        return user

    def login(self, username: str, password: str, *, ttl_seconds: int = 900) -> dict[str, Any]:
        if ttl_seconds < 60 or ttl_seconds > 3600:
            raise AuthServiceError("VALIDATION_ERROR", "ttl_seconds must be between 60 and 3600")
        normalized_username = username.strip().lower()
        user = self._users_by_name.get(normalized_username)
        if not user or not self._verify_password(password, user.password_hash):
            raise AuthServiceError("INVALID_CREDENTIALS", "Invalid username or password")
        if not user.active:
            raise AuthServiceError("ACCOUNT_DISABLED", "User account is disabled")

        session_id = str(uuid4())
        now = datetime.now(timezone.utc)
        claims = {
            "sub": str(user.user_id),
            "sid": session_id,
            "role": user.role,
            "employee_id": str(user.employee_id) if user.employee_id else None,
            "department_id": str(user.department_id) if user.department_id else None,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
            "iss": self._issuer,
            "aud": self._audience,
        }
        token = self._encode_token(claims)
        self.observability.logger.info(
            "auth.login_succeeded",
            context={"username": normalized_username, "role": user.role},
        )
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": ttl_seconds,
        }

    def authenticate_token(self, token: str) -> AuthenticatedPrincipal:
        claims = self._decode_token(token)
        sid = claims.get("sid")
        if not sid or sid in self._revoked_session_ids:
            raise AuthServiceError("TOKEN_REVOKED", "Session has been revoked")

        try:
            user_id = UUID(claims["sub"])
        except (KeyError, ValueError) as exc:
            raise AuthServiceError("TOKEN_INVALID", "Token subject is invalid") from exc

        user = self._users_by_id.get(user_id)
        if not user or not user.active:
            raise AuthServiceError("ACCOUNT_DISABLED", "User account is disabled")

        employee_id = UUID(claims["employee_id"]) if claims.get("employee_id") else None
        department_id = UUID(claims["department_id"]) if claims.get("department_id") else None
        return AuthenticatedPrincipal(
            user_id=user_id,
            employee_id=employee_id,
            role=claims["role"],
            department_id=department_id,
        )

    def logout(self, token: str) -> None:
        claims = self._decode_token(token)
        sid = claims.get("sid")
        if sid:
            self._revoked_session_ids.add(sid)
            self.observability.logger.audit(
                "auth_logout",
                actor=claims.get("sub"),
                entity="Session",
                entity_id=sid,
                context={"role": claims.get("role")},
            )

    def validate_role(self, principal: AuthenticatedPrincipal, capability_id: str) -> bool:
        allowed = self._ROLE_CAPABILITY_MAP.get(principal.role, set())
        return capability_id in allowed

    def require_capability(self, principal: AuthenticatedPrincipal, capability_id: str) -> None:
        if not self.validate_role(principal, capability_id):
            raise AuthServiceError("FORBIDDEN", "Insufficient permissions for requested capability")

    def health_snapshot(self) -> dict[str, Any]:
        return self.observability.health_status(
            checks={
                "users": len(self._users_by_id),
                "revoked_sessions": len(self._revoked_session_ids),
            }
        )

    def _encode_token(self, claims: dict[str, Any]) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        header_segment = self._b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_segment = self._b64url_encode(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
        signature = hmac.new(self._token_secret, signing_input, hashlib.sha256).digest()
        signature_segment = self._b64url_encode(signature)
        return f"{header_segment}.{payload_segment}.{signature_segment}"

    def _decode_token(self, token: str) -> dict[str, Any]:
        try:
            header_segment, payload_segment, signature_segment = token.split(".")
        except ValueError as exc:
            raise AuthServiceError("TOKEN_INVALID", "Malformed token") from exc

        signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
        expected_signature = hmac.new(self._token_secret, signing_input, hashlib.sha256).digest()
        actual_signature = self._b64url_decode(signature_segment)
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise AuthServiceError("TOKEN_INVALID", "Token signature is invalid")

        try:
            payload = json.loads(self._b64url_decode(payload_segment).decode("utf-8"))
        except (ValueError, json.JSONDecodeError) as exc:
            raise AuthServiceError("TOKEN_INVALID", "Token payload is invalid") from exc
        self._validate_registered_claims(payload)
        return payload

    def _validate_registered_claims(self, payload: dict[str, Any]) -> None:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if payload.get("iss") != self._issuer or payload.get("aud") != self._audience:
            raise AuthServiceError("TOKEN_INVALID", "Token issuer or audience is invalid")

        nbf = int(payload.get("nbf", 0))
        exp = int(payload.get("exp", 0))
        if now_ts < nbf:
            raise AuthServiceError("TOKEN_INVALID", "Token is not active yet")
        if now_ts >= exp:
            raise AuthServiceError("TOKEN_EXPIRED", "Token has expired")

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 390000)
        return f"{salt.hex()}:{key.hex()}"

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        try:
            salt_hex, key_hex = password_hash.split(":", 1)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(key_hex)
        except (TypeError, ValueError):
            return False

        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 390000)
        return hmac.compare_digest(actual, expected)

    @staticmethod
    def _b64url_encode(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    @staticmethod
    def _b64url_decode(encoded: str) -> bytes:
        padding = "=" * (-len(encoded) % 4)
        return base64.urlsafe_b64decode(encoded + padding)
