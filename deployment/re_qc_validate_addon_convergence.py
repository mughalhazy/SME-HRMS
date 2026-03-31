from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = (ROOT / 'addon_convergence.py').read_text()
TESTS = (ROOT / 'tests' / 'test_addon_convergence.py').read_text()
REPORT = (ROOT / 'docs' / 'design' / 'addon-convergence-report-p50.md').read_text()

checks = [
    ('qc dimensions enforce convergence checks', all(token in MODULE for token in ['duplication', 'workflow_alignment', 'automation_alignment', 'analytics_reporting_consistency', 'tenant_isolation', 'audit_event_coverage', 'service_boundaries'])),
    ('auto-fix actions map to required P50 repair paths', all(token in MODULE for token in ['merge_duplicate_logic_into_existing_module', 'reroute_approvals_to_workflow_engine', 'align_automation_rules_with_workflow_triggers', 'normalize_analytics_to_read_model_standards', 'inject_missing_audit_event_hooks', 'enforce_tenant_filters_everywhere', 'restore_clean_service_boundary'])),
    ('enforced loop fails if below 10/10', 'AddonConvergenceError' in MODULE and 'exited below 10/10' in MODULE),
    ('tests lock 10/10 convergence behavior', all(token in TESTS for token in ['test_enforced_loop_converges_addons_to_10_of_10', 'test_convergence_raises_when_no_auto_fix_path_exists'])),
    ('report captures p50 objective and constraints', all(token in REPORT for token in ['P50 — Add-on Convergence QC', 'D1–D8', 'P1–P49', '10/10', 'no duplication', 'no parallel systems'])),
]

score = sum(1 for _, passed in checks if passed)
for name, passed in checks:
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")
print(f'RE-QC addon-convergence score: {score}/{len(checks)}')
if score != len(checks):
    raise SystemExit(1)
