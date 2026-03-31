from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = (ROOT / 'master_certification.py').read_text()
TESTS = (ROOT / 'tests' / 'test_master_certification.py').read_text()
REPORT = (ROOT / 'docs' / 'design' / 'addon-certification-pass-p51.md').read_text()

checks = [
    (
        'qc categories enforce full-system integrity',
        all(
            token in MODULE
            for token in [
                'system_integrity',
                'feature_integration',
                'performance_stability',
                'security_compliance',
                'resilience',
            ]
        ),
    ),
    (
        'auto-fix actions cover p51 repair requirements',
        all(
            token in MODULE
            for token in [
                'merge_duplicate_implementations',
                'align_automation_with_workflow_engine',
                'normalize_analytics_and_reporting',
                'restore_audit_event_integrations',
                'optimize_performance_hotspots',
                'repair_retry_and_recovery',
                'enforce_strict_tenant_isolation',
            ]
        ),
    ),
    ('enforced loop fails if below 10/10', 'MasterCertificationError' in MODULE and 'exited below 10/10' in MODULE),
    (
        'tests lock 10/10 loop behavior',
        all(
            token in TESTS
            for token in [
                'test_master_qc_loop_converges_to_enterprise_10_of_10',
                'test_master_qc_raises_when_no_fix_path_exists',
            ]
        ),
    ),
    (
        'report captures p51 objective and constraints',
        all(
            token in REPORT
            for token in [
                'P51 — Add-on Certification Pass',
                'D1–D8',
                'P1–P50',
                '10/10',
                'MUST NOT stop below 10/10',
                'zero duplication',
            ]
        ),
    ),
]

score = sum(1 for _, passed in checks if passed)
for name, passed in checks:
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")
print(f'RE-QC master-certification score: {score}/{len(checks)}')
if score != len(checks):
    raise SystemExit(1)
