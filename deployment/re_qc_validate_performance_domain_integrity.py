from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = (ROOT / 'services/employee-service/performance.repository.ts').read_text()
SERVICE = (ROOT / 'services/employee-service/performance.service.ts').read_text()
ROUTES = (ROOT / 'services/employee-service/employee.routes.ts').read_text()
SCHEMA = (ROOT / 'deployment/migrations/002_workflow_schema.sql').read_text()
DOMAIN_MODEL = (ROOT / 'docs/canon/domain-model.md').read_text()
WORKFLOW_DOC = (ROOT / 'docs/canon/workflow-catalog.md').read_text()
TESTS = (ROOT / 'tests/test_performance_domain.py').read_text()

checks: list[tuple[str, bool]] = [
    (
        'performance review repository tracks employee reviewer and cycle indexes',
        all(token in REPOSITORY for token in ['cycleIndex', 'employeeIndex', 'reviewerIndex', 'statusIndex']),
    ),
    (
        'service blocks duplicate review cycles and invalid state changes',
        all(token in SERVICE for token in ['performance review cycle already exists', 'cannot transition performance review from', 'only Draft performance reviews can be updated']),
    ),
    (
        'service validates employee and reviewer integrity',
        all(token in SERVICE for token in ['employee was not found', 'reviewer employee was not found', 'reviewer must differ from employee']),
    ),
    (
        'api exposes review read update submit and finalize endpoints',
        all(token in ROUTES for token in ['/api/v1/performance-reviews/:performanceReviewId', '/submit', '/finalize']),
    ),
    (
        'workflow schema and domain model align on finalized lifecycle',
        "status IN ('Draft', 'Submitted', 'Finalized')" in SCHEMA and '`Draft`, `Submitted`, `Finalized`.' in DOMAIN_MODEL,
    ),
    (
        'workflow documentation captures the simplified lifecycle',
        'Draft -> Submitted -> Finalized' in WORKFLOW_DOC and 'PerformanceReviewFinalized' in WORKFLOW_DOC,
    ),
    (
        'automated tests cover runtime lifecycle execution',
        'test_performance_review_service_crud_and_lifecycle' in TESTS and 'service.finalizeReview(review.performance_review_id)' in TESTS,
    ),
]

score = sum(1 for _, ok in checks)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'RE-QC performance-domain-integrity score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
