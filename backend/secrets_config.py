from __future__ import annotations

import os
import sys
from pathlib import Path


def _load_dotenv() -> None:
    env_file = Path(os.getenv("ENV_FILE", ".env"))
    if not env_file.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore[import]
        load_dotenv(env_file, override=False)
    except ImportError:
        _parse_dotenv_file(env_file)


def _parse_dotenv_file(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def require_secrets(*names: str, fatal: bool = True) -> dict[str, str]:
    """
    Validate required env vars are set and non-empty.
    Loads .env automatically before checking.
    Exits (if fatal=True) or raises EnvironmentError on missing values.
    """
    _load_dotenv()
    missing: list[str] = []
    resolved: dict[str, str] = {}
    for name in names:
        value = os.getenv(name, "")
        if not value:
            missing.append(name)
        else:
            resolved[name] = value
    if missing:
        msg = f"Missing required secrets: {', '.join(missing)}"
        if fatal:
            print(f"[secrets_config] FATAL: {msg}", file=sys.stderr)
            sys.exit(1)
        raise EnvironmentError(msg)
    return resolved
