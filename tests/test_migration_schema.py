from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_SCHEMA = (ROOT / 'deployment' / 'migrations' / '001_core_schema.sql').read_text()
WORKFLOW_SCHEMA = (ROOT / 'deployment' / 'migrations' / '002_workflow_schema.sql').read_text()
PERSISTENCE_SCHEMA = (ROOT / 'deployment' / 'migrations' / '003_persistence_normalization.sql').read_text()
TENANT_FOUNDATION_SCHEMA = (ROOT / 'deployment' / 'migrations' / '004_tenant_foundation.sql').read_text()
FULL_SCHEMA = f"{CORE_SCHEMA}\n{WORKFLOW_SCHEMA}\n{PERSISTENCE_SCHEMA}\n{TENANT_FOUNDATION_SCHEMA}"


def test_core_schema_matches_canonical_employee_tables() -> None:
    assert 'tenant_id VARCHAR(80) NOT NULL' in CORE_SCHEMA
    assert 'description TEXT' in CORE_SCHEMA
    assert 'parent_department_id UUID' in CORE_SCHEMA
    assert 'head_employee_id UUID' in CORE_SCHEMA
    assert 'first_name VARCHAR(100) NOT NULL' in CORE_SCHEMA
    assert 'last_name VARCHAR(100) NOT NULL' in CORE_SCHEMA
    assert 'hire_date DATE NOT NULL' in CORE_SCHEMA
    assert 'employment_type VARCHAR(20) NOT NULL' in CORE_SCHEMA
    assert 'manager_employee_id UUID' in CORE_SCHEMA
    assert 'fk_departments_parent_department' in CORE_SCHEMA
    assert 'fk_departments_head_employee' in CORE_SCHEMA


def test_workflow_schema_matches_canonical_operational_tables() -> None:
    expected_fragments = [
        'tenant_id VARCHAR(80) NOT NULL',
        'check_in_time TIMESTAMPTZ',
        'check_out_time TIMESTAMPTZ',
        'leave_type VARCHAR(20) NOT NULL',
        'approver_employee_id UUID',
        'base_salary NUMERIC(12,2) NOT NULL',
        'gross_pay NUMERIC(12,2) NOT NULL',
        'currency CHAR(3) NOT NULL',
        'employment_type VARCHAR(20) NOT NULL',
        'openings_count INTEGER NOT NULL CHECK (openings_count >= 1)',
        'first_name VARCHAR(100) NOT NULL',
        'last_name VARCHAR(100) NOT NULL',
        'source_candidate_id VARCHAR(120)',
        'CREATE TABLE IF NOT EXISTS candidate_stage_transitions',
        'changed_by VARCHAR(120)',
        'CREATE TABLE IF NOT EXISTS interviews',
        'interviewer_employee_ids UUID[]',
        'CREATE TABLE IF NOT EXISTS attendance_rules',
        'workdays VARCHAR(20)[] NOT NULL',
        'CREATE TABLE IF NOT EXISTS leave_policies',
        'carry_forward_limit_days NUMERIC(5,2) NOT NULL',
        'CREATE TABLE IF NOT EXISTS payroll_settings',
        'approval_chain TEXT[] NOT NULL',
        'CREATE TABLE IF NOT EXISTS performance_reviews',
        'reviewer_employee_id UUID NOT NULL',
        "record_state VARCHAR(20) NOT NULL DEFAULT 'Captured'",
        'CREATE TABLE IF NOT EXISTS user_accounts',
        'CREATE TABLE IF NOT EXISTS sessions',
        'CREATE TABLE IF NOT EXISTS refresh_tokens',
    ]

    for fragment in expected_fragments:
        assert fragment in FULL_SCHEMA


def test_workflow_schema_enforces_referential_integrity() -> None:
    foreign_keys = [
        'REFERENCES employees (tenant_id, employee_id)',
        'REFERENCES departments (tenant_id, department_id)',
        'REFERENCES roles (tenant_id, role_id)',
        'REFERENCES job_postings (tenant_id, job_posting_id)',
        'REFERENCES candidates (tenant_id, candidate_id)',
        'ON UPDATE CASCADE',
    ]

    for fragment in foreign_keys:
        assert fragment in CORE_SCHEMA or fragment in WORKFLOW_SCHEMA


def test_all_tables_include_tenant_id() -> None:
    create_table_blocks = re.findall(r'CREATE TABLE IF NOT EXISTS\s+\w+\s*\((.*?)\);', FULL_SCHEMA, re.S)
    assert create_table_blocks
    for block in create_table_blocks:
        assert 'tenant_id VARCHAR(80) NOT NULL' in block


def test_persistence_normalization_schema_adds_auth_and_attendance_persistence() -> None:
    expected_fragments = [
        'ALTER TABLE attendance_records',
        "ADD COLUMN IF NOT EXISTS record_state VARCHAR(20) NOT NULL DEFAULT 'Captured'",
        'ADD COLUMN IF NOT EXISTS correction_note TEXT',
        'CREATE TABLE IF NOT EXISTS user_accounts',
        'CREATE TABLE IF NOT EXISTS role_bindings',
        'CREATE TABLE IF NOT EXISTS permission_policies',
        'CREATE TABLE IF NOT EXISTS sessions',
        'CREATE TABLE IF NOT EXISTS refresh_tokens',
        'REFERENCES user_accounts (tenant_id, user_id)',
        'REFERENCES sessions (tenant_id, session_id)',
    ]

    for fragment in expected_fragments:
        assert fragment in PERSISTENCE_SCHEMA


def test_tenant_foundation_schema_adds_tenant_registry_and_config_store() -> None:
    expected_fragments = [
        'CREATE TABLE IF NOT EXISTS tenants',
        'tenant_id VARCHAR(80) NOT NULL PRIMARY KEY',
        'slug VARCHAR(120) NOT NULL UNIQUE',
        'CREATE TABLE IF NOT EXISTS tenant_configs',
        'feature_flags JSONB NOT NULL DEFAULT',
        'leave_policy_refs JSONB NOT NULL DEFAULT',
        'payroll_rule_refs JSONB NOT NULL DEFAULT',
        'enabled_locations JSONB NOT NULL DEFAULT',
        'REFERENCES tenants (tenant_id)',
    ]

    for fragment in expected_fragments:
        assert fragment in TENANT_FOUNDATION_SCHEMA
