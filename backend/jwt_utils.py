from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


def b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def verify_hs256_jwt(
    token: str,
    secret: bytes,
    *,
    audience: str = "",
    issuer: str = "",
    clock_skew_seconds: int = 5,
) -> dict[str, Any] | None:
    """
    Verify an HS256 JWT token. Returns the claims dict on success, None on any failure.
    clock_skew_seconds provides a grace window on exp/nbf to tolerate minor clock drift.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_seg, payload_seg, sig_seg = parts
        signing_input = f"{header_seg}.{payload_seg}".encode()
        expected_sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
        actual_sig = b64url_decode(sig_seg)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        claims: dict[str, Any] = json.loads(b64url_decode(payload_seg).decode())
        now = int(time.time())
        if now >= int(claims.get("exp", 0)) + clock_skew_seconds:
            return None
        if now < int(claims.get("nbf", 0)) - clock_skew_seconds:
            return None
        if audience and claims.get("aud") != audience:
            return None
        if issuer and claims.get("iss") != issuer:
            return None
        return claims
    except Exception:  # noqa: BLE001
        return None
