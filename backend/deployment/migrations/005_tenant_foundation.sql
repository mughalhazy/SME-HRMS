CREATE TABLE IF NOT EXISTS tenants (
  tenant_id VARCHAR(80) NOT NULL PRIMARY KEY,
  tenant_name VARCHAR(200) NOT NULL,
  slug VARCHAR(120) NOT NULL UNIQUE,
  status VARCHAR(20) NOT NULL DEFAULT 'Active' CHECK (status IN ('Provisioning', 'Active', 'Suspended', 'Archived')),
  default_locale VARCHAR(20) NOT NULL DEFAULT 'en-US',
  legal_entity_name VARCHAR(200),
  primary_country_code CHAR(2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants (status);

CREATE TABLE IF NOT EXISTS tenant_configs (
  tenant_config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id VARCHAR(80) NOT NULL,
  feature_flags JSONB NOT NULL DEFAULT '{}'::jsonb,
  leave_policy_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
  payroll_rule_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
  locale VARCHAR(20) NOT NULL DEFAULT 'en-US',
  legal_entity JSONB NOT NULL DEFAULT '{}'::jsonb,
  enabled_locations JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_tenant_configs_tenant UNIQUE (tenant_id),
  CONSTRAINT fk_tenant_configs_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tenant_configs_tenant_id ON tenant_configs (tenant_id);
