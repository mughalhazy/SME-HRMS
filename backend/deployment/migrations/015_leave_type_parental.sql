-- Migration 015: Add 'Parental' to leave_requests.leave_type CHECK constraint
-- Fixes DG-003: leave_policies.leave_type permits 'Parental' but leave_requests.leave_type
-- does not, making Parental leave policies unserviceable.
--
-- Fix direction anchored by: leave_policies.leave_type CHECK (in migration 002) is the
-- authoritative list of recognised leave types. leave_requests must accept what
-- leave_policies can configure.
--
-- Anchor sources:
--   backend/deployment/migrations/002_workflow_schema.sql  — both CHECK constraints (source of truth)
--   docs/00_authority/DOMAIN_MODEL.md LEAVE POLICY section — canonical leave type list
--   docs/08_reports/BACKEND_GAP_REGISTER.md DG-003         — gap record and fix direction

BEGIN;

DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'leave_requests'::regclass
          AND conname = 'leave_requests_leave_type_check'
    ) THEN
        ALTER TABLE leave_requests DROP CONSTRAINT leave_requests_leave_type_check;
    END IF;
END $$;

ALTER TABLE leave_requests
    ADD CONSTRAINT chk_leave_requests_leave_type
        CHECK (leave_type IN ('Annual', 'Sick', 'Casual', 'Unpaid', 'Parental', 'Other'));

COMMIT;
