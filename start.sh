#!/bin/sh
set -eu

if [ -n "${DATABASE_URL:-}" ]; then
  echo "Running database migrations..."
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f /app/deployment/config/postgres-init.sql

  migration_files=$(find /app/deployment/migrations -maxdepth 1 -type f -name '[0-9][0-9][0-9]_*.sql' | sort -V)
  migration_prefixes=$(printf '%s\n' "$migration_files" | sed -E 's|^.*/([0-9]{3})_.*$|\1|' | sort)
  duplicate_prefixes=$(printf '%s\n' "$migration_prefixes" | uniq -d)
  if [ -n "$duplicate_prefixes" ]; then
    echo "Duplicate migration prefixes detected: $duplicate_prefixes"
    exit 1
  fi

  printf '%s\n' "$migration_files" | while IFS= read -r file; do
    [ -n "$file" ] || continue
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$file"
  done

  echo "Migrations complete."
else
  echo "DATABASE_URL not set, skipping migrations."
fi

SERVICE_SPECS="
employee-service:8001
attendance-service:8002
leave-service:8003
payroll-service:8004
hiring-service:8005
auth-service:8006
notification-service:8007
audit-service:8008
workflow-service:8009
performance-service:8010
engagement-service:8011
helpdesk-service:8012
reporting-analytics-service:8013
search-service:8014
expense-service:8015
integration-service:8016
automation-service:8017
travel-service:8018
project-service:8019
settings-service:8020
"

PIDS=""

for spec in $SERVICE_SPECS; do
  service_name=${spec%:*}
  service_port=${spec#*:}
  echo "Starting ${service_name} on port ${service_port}"
  PORT="$service_port" SERVICE_NAME="$service_name" python /app/docker/service_runtime.py &
  PIDS="$PIDS $!"
done

cleanup() {
  echo "Shutting down background services..."
  for pid in $PIDS; do
    kill "$pid" 2>/dev/null || true
  done
}

trap cleanup INT TERM EXIT

sleep 2

echo "Starting api-gateway on port 8000"
PORT=8000 python /app/docker/api_gateway_service.py
