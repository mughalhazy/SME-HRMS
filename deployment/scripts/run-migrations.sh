#!/bin/sh
set -eu

MIGRATIONS_DIR="${MIGRATIONS_DIR:-/migrations}"
DATABASE_URL="postgresql://${POSTGRES_USER}:${PGPASSWORD}@${POSTGRES_HOST}:5432/${POSTGRES_DB}"

migration_files=$(find "$MIGRATIONS_DIR" -maxdepth 1 -type f -name '*.sql' | sort -V)

if [ -z "$migration_files" ]; then
  echo "No migration files found in $MIGRATIONS_DIR"
  exit 1
fi

migration_prefixes=$(printf '%s\n' "$migration_files" | sed -E 's|^.*/([0-9]{3})_.*$|\1|' | sort)
duplicate_prefixes=$(printf '%s\n' "$migration_prefixes" | uniq -d)
if [ -n "$duplicate_prefixes" ]; then
  echo "Duplicate migration prefixes detected: $duplicate_prefixes"
  exit 1
fi

printf '%s\n' "$migration_files" | while IFS= read -r file; do
  [ -n "$file" ] || continue
  echo "Applying migration: $file"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$file"
done

echo "Migrations complete"
