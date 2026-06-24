CREATE TABLE IF NOT EXISTS workflow_definitions (
  tenant_id VARCHAR(80) NOT NULL,
  workflow_definition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code VARCHAR(120) NOT NULL,
  source_service VARCHAR(80) NOT NULL,
  subject_type VARCHAR(80) NOT NULL,
  description TEXT NOT NULL,
  steps JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_workflow_definitions_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_workflow_definitions_tenant_id ON workflow_definitions (tenant_id);

CREATE TABLE IF NOT EXISTS workflow_instances (
  tenant_id VARCHAR(80) NOT NULL,
  workflow_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_definition_id UUID NOT NULL,
  source_service VARCHAR(80) NOT NULL,
  subject_type VARCHAR(80) NOT NULL,
  subject_id UUID NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'completed')),
  created_by VARCHAR(120) NOT NULL,
  created_by_type VARCHAR(20) NOT NULL CHECK (created_by_type IN ('user', 'service', 'system')),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT fk_workflow_instances_definition FOREIGN KEY (workflow_definition_id)
    REFERENCES workflow_definitions (workflow_definition_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_workflow_instances_tenant_status ON workflow_instances (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_workflow_instances_subject ON workflow_instances (tenant_id, subject_type, subject_id);

CREATE TABLE IF NOT EXISTS workflow_steps (
  tenant_id VARCHAR(80) NOT NULL,
  workflow_step_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_id UUID NOT NULL,
  step_code VARCHAR(120) NOT NULL,
  step_type VARCHAR(20) NOT NULL CHECK (step_type IN ('approval', 'auto', 'condition')),
  assignee VARCHAR(120) NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
  sla VARCHAR(32) NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT fk_workflow_steps_instance FOREIGN KEY (workflow_id)
    REFERENCES workflow_instances (workflow_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_workflow_steps_tenant_assignee ON workflow_steps (tenant_id, assignee, status);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_tenant_workflow ON workflow_steps (tenant_id, workflow_id);

CREATE TABLE IF NOT EXISTS workflow_history (
  tenant_id VARCHAR(80) NOT NULL,
  workflow_history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  workflow_id UUID NOT NULL,
  workflow_step_id UUID,
  action VARCHAR(80) NOT NULL,
  actor_id VARCHAR(120) NOT NULL,
  actor_type VARCHAR(20) NOT NULL CHECK (actor_type IN ('user', 'service', 'system')),
  from_status VARCHAR(20),
  to_status VARCHAR(20) NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT fk_workflow_history_instance FOREIGN KEY (workflow_id)
    REFERENCES workflow_instances (workflow_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_workflow_history_step FOREIGN KEY (workflow_step_id)
    REFERENCES workflow_steps (workflow_step_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_workflow_history_tenant_workflow ON workflow_history (tenant_id, workflow_id, created_at);
