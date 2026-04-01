from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


class MobileSessionError(ValueError):
    """Raised when a mobile session token is invalid."""


class MobileSessionManager:
    """Token-based auth with lightweight stateless validation for mobile."""

    def __init__(self, secret: str, *, ttl_seconds: int = 1800) -> None:
        if not secret or len(secret) < 16:
            raise ValueError('secret must be at least 16 characters')
        self._secret = secret.encode('utf-8')
        self._ttl_seconds = max(ttl_seconds, 60)

    @staticmethod
    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')

    @staticmethod
    def _unb64url(data: str) -> bytes:
        padding = '=' * (-len(data) % 4)
        return base64.urlsafe_b64decode((data + padding).encode('ascii'))

    def _sign(self, unsigned_token: str) -> str:
        digest = hmac.new(self._secret, unsigned_token.encode('utf-8'), hashlib.sha256).digest()
        return self._b64url(digest)

    def issue_token(self, *, user_id: str, role: str) -> str:
        now = int(time.time())
        payload = {'sub': user_id, 'role': role, 'iat': now, 'exp': now + self._ttl_seconds}
        encoded_payload = self._b64url(json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8'))
        signature = self._sign(encoded_payload)
        return f'{encoded_payload}.{signature}'

    def validate_token(self, authorization: str | None) -> dict[str, Any]:
        if not authorization or not authorization.startswith('Bearer '):
            raise MobileSessionError('Missing bearer token')

        raw_token = authorization.split(' ', 1)[1].strip()
        if '.' not in raw_token:
            raise MobileSessionError('Malformed token')

        encoded_payload, signature = raw_token.split('.', 1)
        expected = self._sign(encoded_payload)
        if not hmac.compare_digest(signature, expected):
            raise MobileSessionError('Invalid token signature')

        payload = json.loads(self._unb64url(encoded_payload).decode('utf-8'))
        if int(payload.get('exp', 0)) < int(time.time()):
            raise MobileSessionError('Token expired')

        user_id = payload.get('sub')
        role = payload.get('role')
        if not isinstance(user_id, str) or not user_id:
            raise MobileSessionError('Invalid subject')
        if not isinstance(role, str) or not role:
            raise MobileSessionError('Invalid role')

        return {'user_id': user_id, 'role': role}
