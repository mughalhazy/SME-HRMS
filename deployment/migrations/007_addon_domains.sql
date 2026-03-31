BEGIN;

CREATE TABLE IF NOT EXISTS helpdesk_tickets (
    tenant_id VARCHAR(80) NOT NULL,
    ticket_id UUID PRIMARY KEY,
    requester_employee_id UUID NOT NULL,
    subject VARCHAR(240) NOT NULL,
    category_code VARCHAR(60) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS helpdesk_ticket_sla_events (
    tenant_id VARCHAR(80) NOT NULL,
    event_id UUID PRIMARY KEY,
    ticket_id UUID NOT NULL,
    escalation_stage VARCHAR(30) NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT fk_helpdesk_sla_ticket FOREIGN KEY (ticket_id) REFERENCES helpdesk_tickets (ticket_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workforce_intelligence_snapshots (
    tenant_id VARCHAR(80) NOT NULL,
    snapshot_id UUID PRIMARY KEY,
    snapshot_type VARCHAR(80) NOT NULL,
    dimension_key VARCHAR(80) NOT NULL,
    dimension_value VARCHAR(160) NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS learning_paths (
    tenant_id VARCHAR(80) NOT NULL,
    learning_path_id UUID PRIMARY KEY,
    code VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_learning_paths_tenant_code UNIQUE (tenant_id, code)
);

CREATE TABLE IF NOT EXISTS workforce_cost_plans (
    tenant_id VARCHAR(80) NOT NULL,
    plan_id UUID PRIMARY KEY,
    fiscal_year SMALLINT NOT NULL,
    period_code VARCHAR(20) NOT NULL,
    headcount_target INTEGER NOT NULL CHECK (headcount_target >= 0),
    salary_forecast NUMERIC(14,2) NOT NULL DEFAULT 0,
    budget_limit NUMERIC(14,2) NOT NULL DEFAULT 0,
    forecast_currency CHAR(3) NOT NULL DEFAULT 'USD',
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_workforce_cost_plan UNIQUE (tenant_id, fiscal_year, period_code)
);

COMMIT;
