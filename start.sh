#!/bin/sh
set -e

# Run database migrations if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
  echo "Running database migrations..."
  psql "$DATABASE_URL" -f /app/migrations/postgres-init.sql
  psql "$DATABASE_URL" -f /app/migrations/001_core_schema.sql
  psql "$DATABASE_URL" -f /app/migrations/002_workflow_schema.sql
  echo "Migrations complete."
else
  echo "DATABASE_URL not set, skipping migrations."
fi

# Start all backend services in background
PORT=8001 SERVICE_NAME=employee-service     python /app/common_service.py &
PORT=8002 SERVICE_NAME=attendance-service   python /app/common_service.py &
PORT=8003 SERVICE_NAME=leave-service        python /app/common_service.py &
PORT=8004 SERVICE_NAME=payroll-service      python /app/common_service.py &
PORT=8005 SERVICE_NAME=hiring-service       python /app/common_service.py &
PORT=8006 SERVICE_NAME=auth-service         python /app/common_service.py &
PORT=8007 SERVICE_NAME=notification-service python /app/common_service.py &

# Wait briefly for services to bind their ports
sleep 2

# Start API gateway in foreground (keeps container alive)
PORT=8000 python /app/api_gateway_service.py
