"""
ATL Adapter — FBR Active Taxpayer List verification.

G42: Filer status must be verified against FBR's public ATL before payroll runs.
An employee stored as 'filer' who is not on the ATL would have incorrect (lower) tax deducted.

Verification is cached per CNIC with a 30-day TTL. Call verify_filer_status() during
payroll record construction when:
  - employee.tax_status == "filer"
  - last ATL verification > 30 days ago or never verified

FBR ATL endpoint: https://atl.fbr.gov.pk/atl/online/ATL.aspx (public lookup)
Config key: FBR_ATL_ENDPOINT (override in config/integrations.py for sandbox/live)
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any

try:
    from config.integrations import get_integration_config
    _cfg = get_integration_config("fbr_atl")
except Exception:
    _cfg = {}

_ATL_ENDPOINT = _cfg.get("endpoint", "https://atl.fbr.gov.pk/atl/online/ATL.aspx")
_CACHE_TTL_DAYS = int(_cfg.get("cache_ttl_days", 30))
_TIMEOUT = int(_cfg.get("timeout_seconds", 10))

# In-process verification cache: {cnic: {"is_filer": bool, "verified_at": datetime}}
_atl_cache: dict[str, dict[str, Any]] = {}


def _cache_key(cnic: str) -> str:
    return hashlib.sha256(cnic.encode()).hexdigest()


def _is_cache_valid(entry: dict[str, Any]) -> bool:
    verified_at: datetime = entry.get("verified_at", datetime.min)
    return (datetime.utcnow() - verified_at) < timedelta(days=_CACHE_TTL_DAYS)


def verify_filer_status(cnic: str, force_refresh: bool = False) -> dict[str, Any]:
    """
    Verify whether a CNIC is on the FBR Active Taxpayer List.

    Returns:
        {
            "cnic": str,
            "is_filer": bool,
            "source": "cache" | "atl_api" | "unavailable",
            "verified_at": str (ISO datetime),
            "cache_expires_days": int,
        }

    If the ATL API is unreachable, returns source="unavailable" and is_filer=None.
    Caller must decide whether to block payroll or proceed with stored tax_status.
    """
    cnic = str(cnic).strip()
    key = _cache_key(cnic)

    if not force_refresh and key in _atl_cache and _is_cache_valid(_atl_cache[key]):
        entry = _atl_cache[key]
        return {
            "cnic": cnic,
            "is_filer": entry["is_filer"],
            "source": "cache",
            "verified_at": entry["verified_at"].isoformat(),
            "cache_expires_days": _CACHE_TTL_DAYS,
        }

    # Attempt live ATL lookup.
    try:
        import urllib.request
        import urllib.parse
        params = urllib.parse.urlencode({"cnic": cnic})
        url = f"{_ATL_ENDPOINT}?{params}"
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="ignore").lower()
        # FBR ATL returns plain text: "active" if on list, otherwise not found.
        is_filer = "active" in body
        source = "atl_api"
    except Exception:
        # ATL API unreachable — return unavailable, do not update cache.
        return {
            "cnic": cnic,
            "is_filer": None,
            "source": "unavailable",
            "verified_at": None,
            "cache_expires_days": _CACHE_TTL_DAYS,
        }

    now = datetime.utcnow()
    _atl_cache[key] = {"is_filer": is_filer, "verified_at": now, "cnic": cnic}
    return {
        "cnic": cnic,
        "is_filer": is_filer,
        "source": source,
        "verified_at": now.isoformat(),
        "cache_expires_days": _CACHE_TTL_DAYS,
    }


def bulk_verify(cnics: list[str], force_refresh: bool = False) -> list[dict[str, Any]]:
    """Verify a list of CNICs. Returns one result dict per CNIC."""
    return [verify_filer_status(cnic, force_refresh=force_refresh) for cnic in cnics]


def clear_cache(cnic: str | None = None) -> None:
    """Clear ATL cache for a specific CNIC or all entries."""
    if cnic:
        _atl_cache.pop(_cache_key(str(cnic).strip()), None)
    else:
        _atl_cache.clear()
