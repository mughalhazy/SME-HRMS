CREATE TABLE IF NOT EXISTS notification_templates (
  tenant_id VARCHAR(80) NOT NULL,
  template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code VARCHAR(100) NOT NULL,
  channel VARCHAR(20) NOT NULL CHECK (channel IN ('Email', 'SMS', 'Push', 'InApp')),
  topic_code VARCHAR(100) NOT NULL,
  subject_template TEXT,
  body_template TEXT NOT NULL,
  locale VARCHAR(10) NOT NULL DEFAULT 'en-US',
  status VARCHAR(20) NOT NULL DEFAULT 'Active' CHECK (status IN ('Draft', 'Active', 'Retired')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_notification_templates_code UNIQUE (tenant_id, code, channel),
  CONSTRAINT fk_notification_templates_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notification_templates_channel ON notification_templates (tenant_id, channel);
CREATE INDEX IF NOT EXISTS idx_notification_templates_active ON notification_templates (tenant_id, status);

CREATE TABLE IF NOT EXISTS notification_messages (
  tenant_id VARCHAR(80) NOT NULL,
  message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  template_id UUID,
  event_name VARCHAR(120),
  event_type VARCHAR(160),
  recipient VARCHAR(100) NOT NULL,
  subject_type VARCHAR(40) NOT NULL,
  subject_id VARCHAR(100) NOT NULL,
  topic_code VARCHAR(100) NOT NULL,
  channel VARCHAR(20) NOT NULL CHECK (channel IN ('Email', 'SMS', 'Push', 'InApp')),
  destination TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Queued', 'Sent', 'Failed', 'Suppressed')),
  queued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_at TIMESTAMPTZ,
  delivered_at TIMESTAMPTZ,
  failed_at TIMESTAMPTZ,
  failure_reason TEXT,
  read_at TIMESTAMPTZ,
  retry_count INTEGER NOT NULL DEFAULT 0,
  last_attempt_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT fk_notification_messages_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_notification_messages_template FOREIGN KEY (template_id) REFERENCES notification_templates (template_id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_messages_subject ON notification_messages (tenant_id, subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_notification_messages_status ON notification_messages (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_notification_messages_channel ON notification_messages (tenant_id, channel);
CREATE INDEX IF NOT EXISTS idx_notification_messages_template_id ON notification_messages (template_id);

CREATE TABLE IF NOT EXISTS delivery_attempts (
  tenant_id VARCHAR(80) NOT NULL,
  delivery_attempt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  message_id UUID NOT NULL,
  provider_name VARCHAR(100) NOT NULL,
  provider_message_id VARCHAR(255),
  attempt_number INTEGER NOT NULL CHECK (attempt_number >= 1),
  attempted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  outcome VARCHAR(20) NOT NULL CHECK (outcome IN ('Sent', 'Failed', 'Deferred', 'Suppressed')),
  response_code VARCHAR(50),
  response_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_delivery_attempts_message_attempt UNIQUE (message_id, attempt_number),
  CONSTRAINT fk_delivery_attempts_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_delivery_attempts_message FOREIGN KEY (message_id) REFERENCES notification_messages (message_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_delivery_attempts_message_id ON delivery_attempts (tenant_id, message_id);
CREATE INDEX IF NOT EXISTS idx_delivery_attempts_outcome ON delivery_attempts (tenant_id, outcome);

CREATE TABLE IF NOT EXISTS notification_preferences (
  tenant_id VARCHAR(80) NOT NULL,
  preference_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_type VARCHAR(40) NOT NULL,
  subject_id VARCHAR(100) NOT NULL,
  topic_code VARCHAR(100) NOT NULL,
  email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  sms_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  in_app_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  quiet_hours JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_notification_preferences_subject_topic UNIQUE (tenant_id, subject_type, subject_id, topic_code),
  CONSTRAINT fk_notification_preferences_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notification_preferences_subject ON notification_preferences (tenant_id, subject_type, subject_id);
