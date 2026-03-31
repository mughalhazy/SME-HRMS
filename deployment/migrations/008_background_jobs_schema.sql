CREATE TABLE IF NOT EXISTS event_outbox (
  tenant_id VARCHAR(80) NOT NULL,
  event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  aggregate_type VARCHAR(80) NOT NULL,
  aggregate_id VARCHAR(100) NOT NULL,
  event_name VARCHAR(120) NOT NULL,
  payload JSONB NOT NULL,
  trace_id VARCHAR(64) NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  published_at TIMESTAMPTZ,
  failed_attempts INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_event_outbox_tenant_event UNIQUE (tenant_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_event_outbox_unpublished ON event_outbox (tenant_id, published_at);
CREATE INDEX IF NOT EXISTS idx_event_outbox_aggregate ON event_outbox (tenant_id, aggregate_type, aggregate_id);
CREATE INDEX IF NOT EXISTS idx_event_outbox_event_name ON event_outbox (tenant_id, event_name);

CREATE TABLE IF NOT EXISTS background_jobs (
  tenant_id VARCHAR(80) NOT NULL,
  job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_type VARCHAR(120) NOT NULL,
  payload JSONB NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Scheduled', 'Running', 'Succeeded', 'Failed', 'DeadLettered', 'Cancelled')),
  attempts INTEGER NOT NULL DEFAULT 0,
  scheduled_at TIMESTAMPTZ NOT NULL,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  failure_reason TEXT,
  idempotency_key VARCHAR(160),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_background_jobs_tenant_job UNIQUE (tenant_id, job_id)
);

CREATE INDEX IF NOT EXISTS idx_background_jobs_schedulable ON background_jobs (tenant_id, status, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_background_jobs_type ON background_jobs (tenant_id, job_type);
CREATE INDEX IF NOT EXISTS idx_background_jobs_idempotency ON background_jobs (tenant_id, idempotency_key);

CREATE TABLE IF NOT EXISTS background_job_failures (
  tenant_id VARCHAR(80) NOT NULL,
  background_job_failure_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_id UUID NOT NULL,
  attempt_number INTEGER NOT NULL CHECK (attempt_number >= 1),
  failure_reason TEXT NOT NULL,
  retryable BOOLEAN NOT NULL DEFAULT TRUE,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  recovered_at TIMESTAMPTZ,
  CONSTRAINT uq_background_job_failures_tenant_failure UNIQUE (tenant_id, background_job_failure_id),
  CONSTRAINT fk_background_job_failures_job FOREIGN KEY (tenant_id, job_id)
    REFERENCES background_jobs (tenant_id, job_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_background_job_failures_job ON background_job_failures (tenant_id, job_id, occurred_at);
