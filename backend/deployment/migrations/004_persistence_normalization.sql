ALTER TABLE attendance_records
  ADD COLUMN IF NOT EXISTS record_state VARCHAR(20) NOT NULL DEFAULT 'Captured' CHECK (record_state IN ('Captured', 'Validated', 'Approved', 'Locked')),
  ADD COLUMN IF NOT EXISTS correction_note TEXT;

CREATE INDEX IF NOT EXISTS idx_attendance_records_tenant_record_state ON attendance_records (tenant_id, record_state);

CREATE TABLE IF NOT EXISTS user_accounts (
  tenant_id VARCHAR(80) NOT NULL,
  user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id UUID,
  username VARCHAR(150) NOT NULL,
  email VARCHAR(255),
  password_hash TEXT NOT NULL,
  identity_provider VARCHAR(40) NOT NULL DEFAULT 'local',
  status VARCHAR(20) NOT NULL CHECK (status IN ('Invited', 'Active', 'Locked', 'Disabled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_login_at TIMESTAMPTZ,
  CONSTRAINT uq_user_accounts_tenant_user UNIQUE (tenant_id, user_id),
  CONSTRAINT uq_user_accounts_tenant_username UNIQUE (tenant_id, username),
  CONSTRAINT fk_user_accounts_employee
    FOREIGN KEY (tenant_id, employee_id)
    REFERENCES employees (tenant_id, employee_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_user_accounts_tenant_employee_id ON user_accounts (tenant_id, employee_id);
CREATE INDEX IF NOT EXISTS idx_user_accounts_tenant_status ON user_accounts (tenant_id, status);

CREATE TABLE IF NOT EXISTS role_bindings (
  tenant_id VARCHAR(80) NOT NULL,
  role_binding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL,
  role_code VARCHAR(80) NOT NULL,
  scope_type VARCHAR(40) NOT NULL,
  scope_id VARCHAR(120),
  status VARCHAR(20) NOT NULL CHECK (status IN ('Active', 'Revoked')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_role_bindings_tenant_binding UNIQUE (tenant_id, role_binding_id),
  CONSTRAINT fk_role_bindings_user
    FOREIGN KEY (tenant_id, user_id)
    REFERENCES user_accounts (tenant_id, user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_role_bindings_tenant_user_id ON role_bindings (tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_role_bindings_tenant_status ON role_bindings (tenant_id, status);

CREATE TABLE IF NOT EXISTS permission_policies (
  tenant_id VARCHAR(80) NOT NULL,
  permission_policy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  policy_code VARCHAR(100) NOT NULL,
  subject_type VARCHAR(40) NOT NULL,
  subject_id VARCHAR(120) NOT NULL,
  capability_code VARCHAR(80) NOT NULL,
  scope_type VARCHAR(40) NOT NULL,
  scope_id VARCHAR(120),
  effect VARCHAR(10) NOT NULL CHECK (effect IN ('Allow', 'Deny')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_permission_policies_tenant_policy UNIQUE (tenant_id, permission_policy_id),
  CONSTRAINT uq_permission_policies_tenant_policy_code UNIQUE (tenant_id, policy_code)
);

CREATE INDEX IF NOT EXISTS idx_permission_policies_tenant_subject ON permission_policies (tenant_id, subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_permission_policies_tenant_capability ON permission_policies (tenant_id, capability_code);

CREATE TABLE IF NOT EXISTS sessions (
  tenant_id VARCHAR(80) NOT NULL,
  session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL,
  access_token_jti VARCHAR(120) NOT NULL,
  client_type VARCHAR(40) NOT NULL DEFAULT 'api',
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  last_rotated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_sessions_tenant_session UNIQUE (tenant_id, session_id),
  CONSTRAINT uq_sessions_access_token_jti UNIQUE (tenant_id, access_token_jti),
  CONSTRAINT fk_sessions_user
    FOREIGN KEY (tenant_id, user_id)
    REFERENCES user_accounts (tenant_id, user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_tenant_user_id ON sessions (tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_tenant_expires_at ON sessions (tenant_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_tenant_revoked_at ON sessions (tenant_id, revoked_at);

CREATE TABLE IF NOT EXISTS refresh_tokens (
  tenant_id VARCHAR(80) NOT NULL,
  refresh_token_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL,
  user_id UUID NOT NULL,
  token_hash TEXT NOT NULL,
  rotated_from_token_id UUID,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_refresh_tokens_tenant_token UNIQUE (tenant_id, refresh_token_id),
  CONSTRAINT fk_refresh_tokens_session
    FOREIGN KEY (tenant_id, session_id)
    REFERENCES sessions (tenant_id, session_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_refresh_tokens_user
    FOREIGN KEY (tenant_id, user_id)
    REFERENCES user_accounts (tenant_id, user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_refresh_tokens_rotated_from
    FOREIGN KEY (tenant_id, rotated_from_token_id)
    REFERENCES refresh_tokens (tenant_id, refresh_token_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_tenant_session_id ON refresh_tokens (tenant_id, session_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_tenant_user_id ON refresh_tokens (tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_tenant_expires_at ON refresh_tokens (tenant_id, expires_at);
