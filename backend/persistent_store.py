from __future__ import annotations

import base64
import copy
import dataclasses
import datetime
import decimal
import enum
import importlib
import json
import uuid
import os
import sqlite3
import tempfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generic, TypeVar

K = TypeVar('K')
V = TypeVar('V')

# ---------------------------------------------------------------------------
# JSON codec — replaces pickle for safe, cross-version serialization.
# Type-tagged dicts preserve full round-trip fidelity for all domain types.
# ---------------------------------------------------------------------------

def _encode(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, bytes):
        return {"__t": "b64", "v": base64.b64encode(obj).decode()}
    if isinstance(obj, uuid.UUID):
        return {"__t": "uuid", "v": str(obj)}
    if isinstance(obj, decimal.Decimal):
        return {"__t": "dec", "v": str(obj)}
    if isinstance(obj, datetime.datetime):
        return {"__t": "dt", "v": obj.isoformat()}
    if isinstance(obj, datetime.date):
        return {"__t": "d", "v": obj.isoformat()}
    if isinstance(obj, datetime.time):
        return {"__t": "tm", "v": obj.isoformat()}
    if isinstance(obj, enum.Enum):
        cls = type(obj)
        return {"__t": "enum", "c": f"{cls.__module__}.{cls.__qualname__}", "v": obj.value}
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        cls = type(obj)
        return {
            "__t": "dc",
            "c": f"{cls.__module__}.{cls.__qualname__}",
            "v": {f.name: _encode(getattr(obj, f.name)) for f in dataclasses.fields(obj)},
        }
    if isinstance(obj, dict):
        if all(isinstance(k, str) for k in obj) and "__t" not in obj:
            return {k: _encode(v) for k, v in obj.items()}
        return {"__t": "dict", "v": [[_encode(k), _encode(v)] for k, v in obj.items()]}
    if isinstance(obj, tuple):
        return {"__t": "tuple", "v": [_encode(item) for item in obj]}
    if isinstance(obj, list):
        return [_encode(item) for item in obj]
    if isinstance(obj, set):
        return {"__t": "set", "v": [_encode(item) for item in sorted(obj, key=str)]}
    raise TypeError(f"PersistentKVStore: cannot encode {type(obj).__qualname__!r}")


def _decode(obj: Any) -> Any:
    if isinstance(obj, list):
        return [_decode(item) for item in obj]
    if not isinstance(obj, dict):
        return obj
    t = obj.get("__t")
    if t is None:
        return {k: _decode(v) for k, v in obj.items()}
    v = obj.get("v")
    if t == "b64":
        return base64.b64decode(v)
    if t == "uuid":
        return uuid.UUID(v)
    if t == "tm":
        return datetime.time.fromisoformat(v)
    if t == "dec":
        return decimal.Decimal(v)
    if t == "dt":
        return datetime.datetime.fromisoformat(v)
    if t == "d":
        return datetime.date.fromisoformat(v)
    if t == "tuple":
        return tuple(_decode(item) for item in v)
    if t == "set":
        return {_decode(item) for item in v}
    if t == "dict":
        return {_decode(k): _decode(dv) for k, dv in v}
    if t == "enum":
        mod, cls_name = obj["c"].rsplit(".", 1)
        return getattr(importlib.import_module(mod), cls_name)(v)
    if t == "dc":
        mod, cls_name = obj["c"].rsplit(".", 1)
        cls = getattr(importlib.import_module(mod), cls_name)
        return cls(**{k: _decode(dv) for k, dv in v.items()})
    return obj


def _dump(value: Any) -> str:
    return json.dumps(_encode(value), ensure_ascii=False, separators=(",", ":"))


def _load(payload: str) -> Any:
    return _decode(json.loads(payload))


# ---------------------------------------------------------------------------
# PostgreSQL support (optional — requires psycopg2-binary)
# ---------------------------------------------------------------------------

_POSTGRES_URL: str | None = os.getenv("HRMS_DATABASE_URL")

try:
    import psycopg2
    import psycopg2.extras
    _HAS_PG = True
except ImportError:
    _HAS_PG = False


def _is_pg_url(s: str) -> bool:
    return s.startswith("postgresql://") or s.startswith("postgres://")


def _resolve_db_key(db_path: str | None, is_memory_uri: bool) -> tuple[str, bool]:
    """Return (connection_key, use_postgres)."""
    if not is_memory_uri and not db_path and _POSTGRES_URL and _is_pg_url(_POSTGRES_URL):
        return _POSTGRES_URL, True
    if db_path and _is_pg_url(db_path):
        return db_path, True
    return "", False


class PersistentKVStore(Generic[K, V]):
    """Sqlite-backed (or PostgreSQL-backed) mapping with an in-process cache."""

    _shared_connections: dict[str, Any] = {}
    _shared_locks: dict[str, threading.RLock] = {}
    _registry_lock = threading.RLock()

    def __init__(self, *, service: str, namespace: str, db_path: str | None = None):
        self.service = service
        self.namespace = namespace

        is_memory_uri = bool(db_path) and db_path.startswith('file:') and 'mode=memory' in db_path
        pg_key, use_pg = _resolve_db_key(db_path, is_memory_uri)
        self._use_pg = use_pg

        if use_pg:
            self.db_path = pg_key
        elif is_memory_uri:
            self.db_path = db_path
        else:
            if db_path:
                resolved = Path(db_path)
            else:
                root = Path(tempfile.mkdtemp(prefix='hrms-persistence-'))
                resolved = root / f'{service}.sqlite3'
            resolved.parent.mkdir(parents=True, exist_ok=True)
            self.db_path = str(resolved)

        self._lock = threading.RLock()
        with self._registry_lock:
            if self.db_path not in self._shared_connections:
                if use_pg:
                    if not _HAS_PG:
                        raise RuntimeError(
                            "psycopg2 is not installed. Install psycopg2-binary to use PostgreSQL."
                        )
                    conn = psycopg2.connect(self.db_path)
                    conn.autocommit = True
                else:
                    conn = sqlite3.connect(
                        self.db_path,
                        check_same_thread=False,
                        isolation_level=None,
                        uri=is_memory_uri,
                    )
                    if not is_memory_uri:
                        conn.execute('PRAGMA journal_mode=WAL')
                        conn.execute('PRAGMA synchronous=NORMAL')
                self._shared_connections[self.db_path] = conn
                self._shared_locks[self.db_path] = threading.RLock()

        self._conn = self._shared_connections[self.db_path]
        self._shared_lock = self._shared_locks[self.db_path]
        self._transaction_depth = 0
        self._setup_table()
        self._cache: dict[K, V] = {}
        self._load_cache()

    def _setup_table(self) -> None:
        if self._use_pg:
            self._conn.cursor().execute(
                '''
                CREATE TABLE IF NOT EXISTS persistent_kv (
                  service TEXT NOT NULL,
                  namespace TEXT NOT NULL,
                  key TEXT NOT NULL,
                  value TEXT NOT NULL,
                  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                  PRIMARY KEY (service, namespace, key)
                )
                '''
            )
        else:
            self._conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS persistent_kv (
                  service TEXT NOT NULL,
                  namespace TEXT NOT NULL,
                  key TEXT NOT NULL,
                  value TEXT NOT NULL,
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (service, namespace, key)
                )
                '''
            )
            self._conn.commit()

    def _load_cache(self) -> None:
        with self._shared_lock:
            if self._use_pg:
                cur = self._conn.cursor()
                cur.execute(
                    'SELECT key, value FROM persistent_kv WHERE service = %s AND namespace = %s',
                    (self.service, self.namespace),
                )
                rows = cur.fetchall()
            else:
                cursor = self._conn.execute(
                    'SELECT key, value FROM persistent_kv WHERE service = ? AND namespace = ?',
                    (self.service, self.namespace),
                )
                rows = cursor.fetchall()
            self._cache = {_load(row[0]): _load(row[1]) for row in rows}

    def _flush(self, *, in_transaction: bool = False) -> None:
        with self._lock, self._shared_lock:
            if self._use_pg:
                cur = self._conn.cursor()
                cur.execute(
                    'DELETE FROM persistent_kv WHERE service = %s AND namespace = %s',
                    (self.service, self.namespace),
                )
                if self._cache:
                    psycopg2.extras.execute_values(
                        cur,
                        'INSERT INTO persistent_kv(service, namespace, key, value) VALUES %s',
                        [
                            (self.service, self.namespace, _dump(k), _dump(v))
                            for k, v in self._cache.items()
                        ],
                    )
            else:
                self._conn.execute(
                    'DELETE FROM persistent_kv WHERE service = ? AND namespace = ?',
                    (self.service, self.namespace),
                )
                self._conn.executemany(
                    'INSERT INTO persistent_kv(service, namespace, key, value) VALUES (?, ?, ?, ?)',
                    [
                        (self.service, self.namespace, _dump(k), _dump(v))
                        for k, v in self._cache.items()
                    ],
                )
                if not in_transaction:
                    self._conn.commit()

    def __setitem__(self, key: K, value: V) -> None:
        self._cache[key] = value
        if self._transaction_depth == 0:
            self._flush()

    def __getitem__(self, key: K) -> V:
        self._flush()
        return self._cache[key]

    def get(self, key: K, default: V | None = None) -> V | None:
        self._flush()
        return self._cache.get(key, default)

    def pop(self, key: K, default: V | None = None) -> V | None:
        if self._transaction_depth == 0:
            self._flush()
        if key not in self._cache:
            return default
        value = self._cache.pop(key)
        if self._transaction_depth == 0:
            self._flush()
        return value

    def setdefault(self, key: K, default: V) -> V:
        if self._transaction_depth == 0:
            self._flush()
        if key not in self._cache:
            self._cache[key] = default
            if self._transaction_depth == 0:
                self._flush()
        return self._cache[key]

    def __delitem__(self, key: K) -> None:
        if key in self._cache:
            del self._cache[key]
            if self._transaction_depth == 0:
                self._flush()

    def __contains__(self, key: object) -> bool:
        self._flush()
        return key in self._cache

    def __len__(self) -> int:
        self._flush()
        return len(self._cache)

    def __iter__(self) -> Iterator[K]:
        self._flush()
        return iter(self._cache)

    def __bool__(self) -> bool:
        return len(self) > 0

    def keys(self) -> list[K]:
        self._flush()
        return list(self._cache.keys())

    def values(self) -> list[V]:
        self._flush()
        return list(self._cache.values())

    def items(self) -> list[tuple[K, V]]:
        self._flush()
        return list(self._cache.items())

    def clear(self) -> None:
        self._cache.clear()
        if self._transaction_depth == 0:
            self._flush()

    @classmethod
    @contextmanager
    def transaction(cls, *stores: 'PersistentKVStore[Any, Any]') -> Iterator[None]:
        unique_stores: list[PersistentKVStore[Any, Any]] = []
        seen: set[int] = set()
        for store in stores:
            if id(store) not in seen:
                unique_stores.append(store)
                seen.add(id(store))
        if not unique_stores:
            yield
            return
        db_paths = {store.db_path for store in unique_stores}
        if len(db_paths) != 1:
            raise ValueError('all stores in a transaction must share the same db_path')
        shared_lock = unique_stores[0]._shared_lock
        connection = unique_stores[0]._conn
        use_pg = unique_stores[0]._use_pg
        snapshots = {id(store): copy.deepcopy(store._cache) for store in unique_stores}
        with shared_lock:
            for store in unique_stores:
                store._transaction_depth += 1
            if use_pg:
                connection.autocommit = False
                connection.cursor().execute('BEGIN')
            else:
                connection.execute('BEGIN IMMEDIATE')
            try:
                yield
                for store in unique_stores:
                    store._flush(in_transaction=True)
                connection.commit()
                if use_pg:
                    connection.autocommit = True
            except Exception:
                connection.rollback()
                if use_pg:
                    connection.autocommit = True
                for store in unique_stores:
                    store._cache = snapshots[id(store)]
                raise
            finally:
                for store in unique_stores:
                    store._transaction_depth = max(0, store._transaction_depth - 1)
