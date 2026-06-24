-- Migration 012: Compensation domain tables
-- Covers: CompensationBand, SalaryRevision, BenefitsPlan, BenefitsEnrollment, Allowance
-- Spec: docs/canon/domain-model.md, docs/canon/data-architecture.md (G47)

BEGIN;

-- ---------------------------------------------------------------------------
-- compensation_bands
-- Approved salary ranges per grade/band used to validate salary revisions.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS compensation_bands (
    tenant_id           VARCHAR(80)     NOT NULL,
    compensation_band_id UUID           NOT NULL DEFAULT uuid_generate_v4(),
    grade_band_id       UUID            NOT NULL,
    name                VARCHAR(150)    NOT NULL,
    code                VARCHAR(30)     NOT NULL,
    currency            CHAR(3)         NOT NULL,
    min_salary          NUMERIC(12,2)   NOT NULL CHECK (min_salary >= 0),
    max_salary          NUMERIC(12,2)   NOT NULL CHECK (max_salary >= min_salary),
    target_salary       NUMERIC(12,2)   NULL,
    status              VARCHAR(20)     NOT NULL DEFAULT 'Draft'
                            CHECK (status IN ('Draft','Active','Inactive','Archived')),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_compensation_bands PRIMARY KEY (compensation_band_id),
    CONSTRAINT uq_compensation_bands_tenant_code UNIQUE (tenant_id, code),
    CONSTRAINT fk_compensation_bands_grade_band
        FOREIGN KEY (grade_band_id) REFERENCES grade_bands (grade_band_id)
);

CREATE INDEX IF NOT EXISTS idx_compensation_bands_tenant_id
    ON compensation_bands (tenant_id);
CREATE INDEX IF NOT EXISTS idx_compensation_bands_grade_band_id
    ON compensation_bands (grade_band_id);
CREATE INDEX IF NOT EXISTS idx_compensation_bands_tenant_status
    ON compensation_bands (tenant_id, status);

-- ---------------------------------------------------------------------------
-- salary_revisions
-- Effective-dated base-pay decisions per employee; master payroll input.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS salary_revisions (
    tenant_id               VARCHAR(80)     NOT NULL,
    salary_revision_id      UUID            NOT NULL DEFAULT uuid_generate_v4(),
    employee_id             UUID            NOT NULL,
    compensation_band_id    UUID            NULL,
    effective_from          DATE            NOT NULL,
    effective_to            DATE            NULL,
    base_salary             NUMERIC(12,2)   NOT NULL CHECK (base_salary >= 0),
    currency                CHAR(3)         NOT NULL,
    reason                  TEXT            NULL,
    status                  VARCHAR(20)     NOT NULL DEFAULT 'Draft'
                                CHECK (status IN ('Draft','Approved','Superseded')),
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_salary_revisions PRIMARY KEY (salary_revision_id),
    CONSTRAINT fk_salary_revisions_employee
        FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
    CONSTRAINT fk_salary_revisions_band
        FOREIGN KEY (compensation_band_id) REFERENCES compensation_bands (compensation_band_id)
);

CREATE INDEX IF NOT EXISTS idx_salary_revisions_tenant_id
    ON salary_revisions (tenant_id);
CREATE INDEX IF NOT EXISTS idx_salary_revisions_employee_id
    ON salary_revisions (employee_id);
CREATE INDEX IF NOT EXISTS idx_salary_revisions_tenant_status
    ON salary_revisions (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_salary_revisions_effective_from
    ON salary_revisions (employee_id, effective_from DESC);

-- ---------------------------------------------------------------------------
-- benefits_plans
-- Reusable benefit offerings enrollable by employees.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benefits_plans (
    tenant_id               VARCHAR(80)     NOT NULL,
    benefits_plan_id        UUID            NOT NULL DEFAULT uuid_generate_v4(),
    code                    VARCHAR(30)     NOT NULL,
    name                    VARCHAR(150)    NOT NULL,
    plan_type               VARCHAR(50)     NOT NULL,
    employer_contribution   NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    employee_contribution   NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    currency                CHAR(3)         NOT NULL DEFAULT 'PKR',
    status                  VARCHAR(20)     NOT NULL DEFAULT 'Draft'
                                CHECK (status IN ('Draft','Active','Inactive','Archived')),
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_benefits_plans PRIMARY KEY (benefits_plan_id),
    CONSTRAINT uq_benefits_plans_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_benefits_plans_tenant_id
    ON benefits_plans (tenant_id);
CREATE INDEX IF NOT EXISTS idx_benefits_plans_tenant_status
    ON benefits_plans (tenant_id, status);

-- ---------------------------------------------------------------------------
-- benefits_enrollments
-- Employee elections into a benefits plan with effective dates.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS benefits_enrollments (
    tenant_id               VARCHAR(80)     NOT NULL,
    benefits_enrollment_id  UUID            NOT NULL DEFAULT uuid_generate_v4(),
    employee_id             UUID            NOT NULL,
    benefits_plan_id        UUID            NOT NULL,
    employee_contribution   NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    employer_contribution   NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    effective_from          DATE            NOT NULL,
    effective_to            DATE            NULL,
    status                  VARCHAR(20)     NOT NULL DEFAULT 'Draft'
                                CHECK (status IN ('Draft','Active','Cancelled','Expired')),
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_benefits_enrollments PRIMARY KEY (benefits_enrollment_id),
    CONSTRAINT uq_benefits_enrollments_active
        UNIQUE (tenant_id, employee_id, benefits_plan_id, effective_from),
    CONSTRAINT fk_benefits_enrollments_employee
        FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
    CONSTRAINT fk_benefits_enrollments_plan
        FOREIGN KEY (benefits_plan_id) REFERENCES benefits_plans (benefits_plan_id)
);

CREATE INDEX IF NOT EXISTS idx_benefits_enrollments_tenant_id
    ON benefits_enrollments (tenant_id);
CREATE INDEX IF NOT EXISTS idx_benefits_enrollments_employee_id
    ON benefits_enrollments (employee_id);
CREATE INDEX IF NOT EXISTS idx_benefits_enrollments_plan_id
    ON benefits_enrollments (benefits_plan_id);
CREATE INDEX IF NOT EXISTS idx_benefits_enrollments_tenant_status
    ON benefits_enrollments (tenant_id, status);

-- ---------------------------------------------------------------------------
-- allowances
-- Recurring or one-time compensation additions aggregated into payroll.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS allowances (
    tenant_id       VARCHAR(80)     NOT NULL,
    allowance_id    UUID            NOT NULL DEFAULT uuid_generate_v4(),
    employee_id     UUID            NOT NULL,
    code            VARCHAR(60)     NOT NULL,
    amount          NUMERIC(12,2)   NOT NULL CHECK (amount >= 0),
    currency        CHAR(3)         NOT NULL DEFAULT 'PKR',
    frequency       VARCHAR(20)     NOT NULL DEFAULT 'Monthly'
                        CHECK (frequency IN ('Monthly','OneTime','Quarterly','Annual')),
    effective_from  DATE            NOT NULL,
    effective_to    DATE            NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'Draft'
                        CHECK (status IN ('Draft','Active','Inactive','Archived')),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_allowances PRIMARY KEY (allowance_id),
    CONSTRAINT fk_allowances_employee
        FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
);

CREATE INDEX IF NOT EXISTS idx_allowances_tenant_id
    ON allowances (tenant_id);
CREATE INDEX IF NOT EXISTS idx_allowances_employee_id
    ON allowances (employee_id);
CREATE INDEX IF NOT EXISTS idx_allowances_tenant_status
    ON allowances (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_allowances_employee_effective
    ON allowances (employee_id, effective_from DESC);

COMMIT;
