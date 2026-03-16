#!/bin/sh
set -eu

for file in /migrations/*.sql; do
  echo "Applying migration: $file"
  psql "postgresql://${POSTGRES_USER}:${PGPASSWORD}@${POSTGRES_HOST}:5432/${POSTGRES_DB}" -v ON_ERROR_STOP=1 -f "$file"
done

echo "Migrations complete"
