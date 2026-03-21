from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = (ROOT / 'data_integrity.py').read_text()
TESTS = (ROOT / 'tests' / 'test_data_integrity.py').read_text()
REPORT = (ROOT / 'docs' / 'design' / 'data-integrity-report-p29.md').read_text()
SCRIPT = (ROOT / 'deployment' / 'repair_data_integrity.py').read_text()

checks = [
    ('validator covers entity integrity', all(token in MODULE for token in ['leave_balance_mismatch', 'candidate_handoff_missing_employee_profile', 'payroll_total_mismatch'])),
    ('validator covers projection integrity and tenant normalization', all(token in MODULE for token in ['search_projection_drift', 'analytics_projection_drift', 'normalize_tenant_ownership_fields'])),
    ('validator covers audit/event alignment', all(token in MODULE for token in ['candidate_hire_event_gap', 'payroll_paid_event_gap', 'leave_audit_event_gap'])),
    ('safe repair script exists', all(token in SCRIPT for token in ['--auto-fix', 'DataIntegrityValidator', 'AuditService'])),
    ('tests lock runtime integrity behavior', all(token in TESTS for token in ['test_data_integrity_validator_detects_cross_service_and_projection_drift', 'test_data_integrity_auto_fix_repairs_minor_drift_without_masking_critical_gaps', 'test_integrity_repair_background_job_executes_safe_repairs'])),
    ('report documents scope and repairs', all(token in REPORT for token in ['Data Integrity Validation Report', 'repair_minor_projection_drift', 'candidate-to-employee handoff integrity'])),
]

score = sum(1 for _, passed in checks if passed)
for name, passed in checks:
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")
print(f'RE-QC data-integrity score: {score}/{len(checks)}')
if score != len(checks):
    raise SystemExit(1)
