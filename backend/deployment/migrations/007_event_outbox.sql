CREATE TABLE IF NOT EXISTS service_outbox (
  outbox_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(80) NOT NULL,
  source_service VARCHAR(80) NOT NULL,
  event_id UUID NOT NULL,
  event_type VARCHAR(160) NOT NULL,
  event_payload JSONB NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Dispatched', 'Failed')),
  attempt_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  dispatched_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_service_outbox_event UNIQUE (tenant_id, source_service, event_id)
);

CREATE INDEX IF NOT EXISTS idx_service_outbox_dispatch ON service_outbox (tenant_id, source_service, status, created_at);
CREATE INDEX IF NOT EXISTS idx_service_outbox_event_type ON service_outbox (tenant_id, event_type, created_at);

CREATE TABLE IF NOT EXISTS processed_events (
  processed_event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(80) NOT NULL,
  consumer_name VARCHAR(120) NOT NULL,
  event_id UUID NOT NULL,
  event_type VARCHAR(160) NOT NULL,
  processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT uq_processed_events_consumer UNIQUE (tenant_id, consumer_name, event_id)
);

CREATE INDEX IF NOT EXISTS idx_processed_events_lookup ON processed_events (tenant_id, consumer_name, processed_at DESC);
