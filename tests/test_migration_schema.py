from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_SCHEMA = (ROOT / 'deployment' / 'migrations' / '001_core_schema.sql').read_text()
WORKFLOW_SCHEMA = (ROOT / 'deployment' / 'migrations' / '002_workflow_schema.sql').read_text()


def test_core_schema_matches_canonical_employee_tables() -> None:
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
        'CREATE TABLE IF NOT EXISTS interviews',
        'interviewer_employee_ids UUID[]',
        'CREATE TABLE IF NOT EXISTS performance_reviews',
        'reviewer_employee_id UUID NOT NULL',
    ]

    for fragment in expected_fragments:
        assert fragment in WORKFLOW_SCHEMA


def test_workflow_schema_enforces_referential_integrity() -> None:
    foreign_keys = [
        'REFERENCES employees (employee_id)',
        'REFERENCES departments (department_id)',
        'REFERENCES roles (role_id)',
        'REFERENCES job_postings (job_posting_id)',
        'REFERENCES candidates (candidate_id)',
        'ON UPDATE CASCADE',
    ]

    for fragment in foreign_keys:
        assert fragment in CORE_SCHEMA or fragment in WORKFLOW_SCHEMA
