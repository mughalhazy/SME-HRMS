from __future__ import annotations

import json
import logging
import os
import time
from contextvars import ContextVar
from typing import Any

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

_STDLIB_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
})


class StructuredJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        cid = _correlation_id.get("")
        if cid:
            payload["correlation_id"] = cid
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extra = {k: v for k, v in record.__dict__.items()
                 if k not in _STDLIB_ATTRS and not k.startswith("_")}
        if extra:
            payload["context"] = extra
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(service: str = "", level: str | None = None) -> None:
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))


def set_correlation_id(cid: str) -> None:
    _correlation_id.set(cid)


def get_correlation_id() -> str:
    return _correlation_id.get("")
