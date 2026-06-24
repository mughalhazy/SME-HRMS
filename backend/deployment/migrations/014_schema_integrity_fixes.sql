-- Migration 014: Schema integrity fixes
-- Fixes two CRITICAL gaps discovered in PHASE 2 BACKEND AUTHORITY CAPTURE:
--   DG-001: grade_bands table is missing (referenced by 012_compensation_domain.sql FK)
--   DG-002: Migrations 012 and 013 use bare single-column FKs, breaking the
--            multi-tenancy invariant (docs/00_authority/DOMAIN_MODEL.md MULTI-TENANCY
--            INVARIANT, docs/07_governance/AI_OPERATING_CONTEXT.md FD-002) that
--            requires compound (tenant_id, entity_id) FKs

BEGIN;

-- ============================================================================
-- SECTION 1: Create grade_bands table (DG-001)
-- Owned by employee-service. Should have been in 001_core_schema.sql alongside
-- departments and roles. Pattern: UUID PK + UNIQUE(tenant_id, grade_band_id).
--
-- Anchor sources:
--   backend/docs/canon/domain-model.md line 142      entity definition + owner
--   backend/docs/canon/data-architecture.md line 94  column list (pre-multi-tenancy)
--   backend/services/employee-service/org.model.ts   GradeBand interface (status type)
--   backend/services/employee-service/domain-seed.ts seedGradeBands() seeding pattern
--   docs/00_authority/DOMAIN_MODEL.md MULTI-TENANCY INVARIANT  mandates tenant_id
--
-- Status resolution: canon data-architecture.md includes 'Draft'; org.model.ts omits it.
-- Peer pattern in migration 012 (compensation_bands, benefits_plans, allowances) all
-- use CHECK (status IN ('Draft','Active','Inactive','Archived')). DB migration pattern
-- is authoritative over TypeScript type definitions. 'Draft' is included here.
-- VARCHAR lengths follow migration 012 peer pattern (name=150, family=100).
-- ============================================================================

CREATE TABLE IF NOT EXISTS grade_bands (
    tenant_id       VARCHAR(80)     NOT NULL,
    grade_band_id   UUID            NOT NULL DEFAULT uuid_generate_v4(),
    name            VARCHAR(150)    NOT NULL,
    code            VARCHAR(30)     NOT NULL,
    family          VARCHAR(100)    NULL,
    level_order     INTEGER         NOT NULL DEFAULT 0,
    status          VARCHAR(20)     NOT NULL DEFAULT 'Active'
                        CHECK (status IN ('Draft','Active','Inactive','Archived')),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_grade_bands               PRIMARY KEY (grade_band_id),
    CONSTRAINT uq_grade_bands_tenant_id     UNIQUE (tenant_id, grade_band_id),
    CONSTRAINT uq_grade_bands_tenant_code   UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_grade_bands_tenant_id     ON grade_bands (tenant_id);
CREATE INDEX IF NOT EXISTS idx_grade_bands_tenant_status ON grade_bands (tenant_id, status);

-- ============================================================================
-- SECTION 2: Add missing UNIQUE (tenant_id, entity_id) constraints
-- Required so that compound FKs can reference these tables correctly.
-- ============================================================================

-- compensation_bands: PK is compensation_band_id only; add compound unique
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_compensation_bands_tenant_id'
    ) THEN
        ALTER TABLE compensation_bands
            ADD CONSTRAINT uq_compensation_bands_tenant_id
            UNIQUE (tenant_id, compensation_band_id);
    END IF;
END $$;

-- benefits_plans: PK is benefits_plan_id only; add compound unique
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_benefits_plans_tenant_id'
    ) THEN
        ALTER TABLE benefits_plans
            ADD CONSTRAINT uq_benefits_plans_tenant_id
            UNIQUE (tenant_id, benefits_plan_id);
    END IF;
END $$;

-- travel_requests: PK is travel_request_id only; add compound unique
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_travel_requests_tenant_id'
    ) THEN
        ALTER TABLE travel_requests
            ADD CONSTRAINT uq_travel_requests_tenant_id
            UNIQUE (tenant_id, travel_request_id);
    END IF;
END $$;

-- ============================================================================
-- SECTION 3: Fix compensation_bands FK → grade_bands (DG-002)
-- Replace bare REFERENCES grade_bands(grade_band_id)
-- with compound REFERENCES grade_bands(tenant_id, grade_band_id)
-- ============================================================================

DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_compensation_bands_grade_band'
    ) THEN
        ALTER TABLE compensation_bands
            DROP CONSTRAINT fk_compensation_bands_grade_band;
    END IF;
END $$;

ALTER TABLE compensation_bands
    ADD CONSTRAINT fk_compensation_bands_grade_band
        FOREIGN KEY (tenant_id, grade_band_id)
        REFERENCES grade_bands (tenant_id, grade_band_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;

-- ============================================================================
-- SECTION 4: Fix salary_revisions FKs (DG-002)
-- ============================================================================

-- FK to employees: bare employee_id → compound (tenant_id, employee_id)
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_salary_revisions_employee'
    ) THEN
        ALTER TABLE salary_revisions
            DROP CONSTRAINT fk_salary_revisions_employee;
    END IF;
END $$;

ALTER TABLE salary_revisions
    ADD CONSTRAINT fk_salary_revisions_employee
        FOREIGN KEY (tenant_id, employee_id)
        REFERENCES employees (tenant_id, employee_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;

-- FK to compensation_bands: bare compensation_band_id → compound (tenant_id, compensation_band_id)
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_salary_revisions_band'
    ) THEN
        ALTER TABLE salary_revisions
            DROP CONSTRAINT fk_salary_revisions_band;
    END IF;
END $$;

ALTER TABLE salary_revisions
    ADD CONSTRAINT fk_salary_revisions_band
        FOREIGN KEY (tenant_id, compensation_band_id)
        REFERENCES compensation_bands (tenant_id, compensation_band_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;

-- ============================================================================
-- SECTION 5: Fix benefits_enrollments FKs (DG-002)
-- ============================================================================

-- FK to employees
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_benefits_enrollments_employee'
    ) THEN
        ALTER TABLE benefits_enrollments
            DROP CONSTRAINT fk_benefits_enrollments_employee;
    END IF;
END $$;

ALTER TABLE benefits_enrollments
    ADD CONSTRAINT fk_benefits_enrollments_employee
        FOREIGN KEY (tenant_id, employee_id)
        REFERENCES employees (tenant_id, employee_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;

-- FK to benefits_plans
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_benefits_enrollments_plan'
    ) THEN
        ALTER TABLE benefits_enrollments
            DROP CONSTRAINT fk_benefits_enrollments_plan;
    END IF;
END $$;

ALTER TABLE benefits_enrollments
    ADD CONSTRAINT fk_benefits_enrollments_plan
        FOREIGN KEY (tenant_id, benefits_plan_id)
        REFERENCES benefits_plans (tenant_id, benefits_plan_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;

-- ============================================================================
-- SECTION 6: Fix allowances FK → employees (DG-002)
-- ============================================================================

DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_allowances_employee'
    ) THEN
        ALTER TABLE allowances
            DROP CONSTRAINT fk_allowances_employee;
    END IF;
END $$;

ALTER TABLE allowances
    ADD CONSTRAINT fk_allowances_employee
        FOREIGN KEY (tenant_id, employee_id)
        REFERENCES employees (tenant_id, employee_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;

-- ============================================================================
-- SECTION 7: Fix travel_requests FKs → employees (DG-002)
-- ============================================================================

-- FK for employee_id
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_travel_requests_employee'
    ) THEN
        ALTER TABLE travel_requests
            DROP CONSTRAINT fk_travel_requests_employee;
    END IF;
END $$;

ALTER TABLE travel_requests
    ADD CONSTRAINT fk_travel_requests_employee
        FOREIGN KEY (tenant_id, employee_id)
        REFERENCES employees (tenant_id, employee_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;

-- FK for manager_employee_id (nullable)
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_travel_requests_manager'
    ) THEN
        ALTER TABLE travel_requests
            DROP CONSTRAINT fk_travel_requests_manager;
    END IF;
END $$;

ALTER TABLE travel_requests
    ADD CONSTRAINT fk_travel_requests_manager
        FOREIGN KEY (tenant_id, manager_employee_id)
        REFERENCES employees (tenant_id, employee_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL;

-- ============================================================================
-- SECTION 8: Fix travel_itinerary_segments FK → travel_requests (DG-002)
-- ============================================================================

DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_travel_segments_request'
    ) THEN
        ALTER TABLE travel_itinerary_segments
            DROP CONSTRAINT fk_travel_segments_request;
    END IF;
END $$;

ALTER TABLE travel_itinerary_segments
    ADD CONSTRAINT fk_travel_segments_request
        FOREIGN KEY (tenant_id, travel_request_id)
        REFERENCES travel_requests (tenant_id, travel_request_id)
        ON DELETE CASCADE;

COMMIT;
