#!/usr/bin/env python3
"""
HRMS schema migration runner.

Usage:
  python deployment/migrate.py           # apply all pending migrations
  python deployment/migrate.py --status  # list applied vs pending
  python deployment/migrate.py --dry-run # show what would run without executing

Reads HRMS_DATABASE_URL; defaults to hrms_dev.db (SQLite) if unset.
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
TRACKING_TABLE = "schema_migrations"
_FILENAME_RE = re.compile(r"^(\d{3})_[\w]+\.sql$")


def _sorted_migration_files() -> list[Path]:
    files = [f for f in MIGRATIONS_DIR.glob("*.sql") if _FILENAME_RE.match(f.name)]
    files.sort(key=lambda f: f.name)
    seen: set[str] = set()
    for f in files:
        prefix = _FILENAME_RE.match(f.name).group(1)  # type: ignore[union-attr]
        if prefix in seen:
            print(f"ERROR: Duplicate migration prefix {prefix!r}", file=sys.stderr)
            sys.exit(1)
        seen.add(prefix)
    return files


def _is_pg_url(s: str) -> bool:
    return s.startswith("postgresql://") or s.startswith("postgres://")


# ---------------------------------------------------------------------------
# SQLite backend
# ---------------------------------------------------------------------------

def _connect_sqlite(db_path: str):
    con = sqlite3.connect(db_path, isolation_level=None)
    con.execute("PRAGMA journal_mode=WAL")
    return con


def _ensure_tracking_sqlite(con) -> None:
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS {TRACKING_TABLE} (
            filename TEXT PRIMARY KEY NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)


def _applied_sqlite(con) -> set[str]:
    return {row[0] for row in con.execute(f"SELECT filename FROM {TRACKING_TABLE}")}


def _apply_sqlite(con, filepath: Path) -> None:
    sql = filepath.read_text(encoding="utf-8")
    con.executescript(sql)
    con.execute(f"INSERT INTO {TRACKING_TABLE} (filename) VALUES (?)", (filepath.name,))


# ---------------------------------------------------------------------------
# PostgreSQL backend
# ---------------------------------------------------------------------------

def _connect_pg(url: str):
    import psycopg2  # type: ignore[import]
    con = psycopg2.connect(url)
    con.autocommit = True
    return con


def _ensure_tracking_pg(con) -> None:
    with con.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {TRACKING_TABLE} (
                filename TEXT PRIMARY KEY NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)


def _applied_pg(con) -> set[str]:
    with con.cursor() as cur:
        cur.execute(f"SELECT filename FROM {TRACKING_TABLE}")
        return {row[0] for row in cur.fetchall()}


def _apply_pg(con, filepath: Path) -> None:
    sql = filepath.read_text(encoding="utf-8")
    with con.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            f"INSERT INTO {TRACKING_TABLE} (filename) VALUES (%s)", (filepath.name,)
        )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run(dry_run: bool = False, status_only: bool = False) -> int:
    db_url = os.getenv("HRMS_DATABASE_URL", "hrms_dev.db")
    use_pg = _is_pg_url(db_url)

    if use_pg:
        con = _connect_pg(db_url)
        _ensure_tracking_pg(con)
        applied = _applied_pg(con)
    else:
        con = _connect_sqlite(db_url)
        _ensure_tracking_sqlite(con)
        applied = _applied_sqlite(con)

    all_files = _sorted_migration_files()

    if status_only:
        print(f"{'FILE':<50} STATUS")
        print("-" * 60)
        for f in all_files:
            status = "applied" if f.name in applied else "pending"
            print(f"{f.name:<50} {status}")
        pending_count = sum(1 for f in all_files if f.name not in applied)
        print(f"\n{len(applied)} applied, {pending_count} pending")
        return 0

    pending = [f for f in all_files if f.name not in applied]
    if not pending:
        print("All migrations are up to date.")
        return 0

    for filepath in pending:
        if dry_run:
            print(f"[dry-run] would apply: {filepath.name}")
        else:
            print(f"Applying {filepath.name} ...", end=" ", flush=True)
            if use_pg:
                _apply_pg(con, filepath)
            else:
                _apply_sqlite(con, filepath)
            print("done")

    if not dry_run:
        print(f"\n{len(pending)} migration(s) applied.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HRMS migration runner")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run, status_only=args.status))
