CREATE TABLE IF NOT EXISTS audit_records (
  audit_log_row_id BIGSERIAL PRIMARY KEY,
  audit_id UUID NOT NULL DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(80) NOT NULL,
  actor JSONB NOT NULL,
  action VARCHAR(120) NOT NULL,
  entity VARCHAR(120) NOT NULL,
  entity_id VARCHAR(120) NOT NULL,
  before JSONB NOT NULL DEFAULT '{}'::jsonb,
  after JSONB NOT NULL DEFAULT '{}'::jsonb,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  trace_id VARCHAR(120) NOT NULL,
  source JSONB NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT uq_audit_records_audit_id UNIQUE (audit_id),
  CONSTRAINT fk_audit_records_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_audit_records_tenant_timestamp ON audit_records (tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_records_tenant_actor ON audit_records (tenant_id, ((actor->>'id')), ((actor->>'type')));
CREATE INDEX IF NOT EXISTS idx_audit_records_tenant_entity ON audit_records (tenant_id, entity, entity_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_records_tenant_action ON audit_records (tenant_id, action, timestamp DESC);

CREATE OR REPLACE FUNCTION prevent_audit_record_mutation() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_records is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_records_prevent_update ON audit_records;
CREATE TRIGGER trg_audit_records_prevent_update
BEFORE UPDATE ON audit_records
FOR EACH ROW EXECUTE FUNCTION prevent_audit_record_mutation();

DROP TRIGGER IF EXISTS trg_audit_records_prevent_delete ON audit_records;
CREATE TRIGGER trg_audit_records_prevent_delete
BEFORE DELETE ON audit_records
FOR EACH ROW EXECUTE FUNCTION prevent_audit_record_mutation();
