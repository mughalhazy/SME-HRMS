from __future__ import annotations

import pickle
import sqlite3
import tempfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Generic, TypeVar

K = TypeVar('K')
V = TypeVar('V')


class PersistentKVStore(Generic[K, V]):
    """Sqlite-backed mapping with an in-process cache for live object mutation safety."""

    _shared_connections: dict[str, sqlite3.Connection] = {}
    _shared_locks: dict[str, threading.RLock] = {}
    _registry_lock = threading.RLock()

    def __init__(self, *, service: str, namespace: str, db_path: str | None = None):
        self.service = service
        self.namespace = namespace
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
                conn = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                self._shared_connections[self.db_path] = conn
                self._shared_locks[self.db_path] = threading.RLock()
        self._conn = self._shared_connections[self.db_path]
        self._shared_lock = self._shared_locks[self.db_path]
        self._transaction_depth = 0
        self._conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS persistent_kv (
              service TEXT NOT NULL,
              namespace TEXT NOT NULL,
              key BLOB NOT NULL,
              value BLOB NOT NULL,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (service, namespace, key)
            )
            '''
        )
        self._conn.commit()
        self._cache: dict[K, V] = {}
        self._load_cache()

    @staticmethod
    def _dump(value: object) -> bytes:
        return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def _load(payload: bytes) -> object:
        return pickle.loads(payload)

    def _load_cache(self) -> None:
        with self._shared_lock:
            cursor = self._conn.execute(
                'SELECT key, value FROM persistent_kv WHERE service = ? AND namespace = ?',
                (self.service, self.namespace),
            )
            self._cache = {
                self._load(row[0]): self._load(row[1])
                for row in cursor.fetchall()
            }

    def _flush(self, *, in_transaction: bool = False) -> None:
        with self._lock, self._shared_lock:
            self._conn.execute(
                'DELETE FROM persistent_kv WHERE service = ? AND namespace = ?',
                (self.service, self.namespace),
            )
            self._conn.executemany(
                'INSERT INTO persistent_kv(service, namespace, key, value) VALUES (?, ?, ?, ?)',
                [
                    (self.service, self.namespace, sqlite3.Binary(self._dump(key)), sqlite3.Binary(self._dump(value)))
                    for key, value in self._cache.items()
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
    def transaction(cls, *stores: 'PersistentKVStore[object, object]'):
        unique_stores = []
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
        snapshots = {
            id(store): pickle.loads(pickle.dumps(store._cache, protocol=pickle.HIGHEST_PROTOCOL))
            for store in unique_stores
        }
        with shared_lock:
            for store in unique_stores:
                store._transaction_depth += 1
            connection.execute('BEGIN IMMEDIATE')
            try:
                yield
                for store in unique_stores:
                    store._flush(in_transaction=True)
                connection.commit()
            except Exception:
                connection.rollback()
                for store in unique_stores:
                    store._cache = snapshots[id(store)]
                raise
            finally:
                for store in unique_stores:
                    store._transaction_depth = max(0, store._transaction_depth - 1)
