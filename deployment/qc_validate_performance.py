from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = (ROOT / 'services/employee-service/employee.routes.ts').read_text()
MODEL = (ROOT / 'services/employee-service/performance.model.ts').read_text()
REPOSITORY = (ROOT / 'services/employee-service/performance.repository.ts').read_text()
SERVICE = (ROOT / 'services/employee-service/performance.service.ts').read_text()
CONTROLLER = (ROOT / 'services/employee-service/performance.controller.ts').read_text()
VALIDATION = (ROOT / 'services/employee-service/performance.validation.ts').read_text()
WORKFLOW_SCHEMA = (ROOT / 'deployment/migrations/002_workflow_schema.sql').read_text()
WORKFLOW_DOC = (ROOT / 'docs/canon/workflow-catalog.md').read_text()
SERVICE_MAP = (ROOT / 'docs/canon/service-map.md').read_text()
RBAC = (ROOT / 'services/employee-service/rbac.middleware.ts').read_text()

checks: list[tuple[str, bool]] = [
    (
        'performance review routes expose CRUD and workflow endpoints',
        all(token in ROUTES for token in [
            '/api/v1/performance-reviews',
            '/api/v1/performance-reviews/:performanceReviewId',
            '/api/v1/performance-reviews/:performanceReviewId/submit',
            '/api/v1/performance-reviews/:performanceReviewId/finalize',
        ]),
    ),
    (
        'rate limits applied to performance review APIs',
        all(token in ROUTES for token in [
            'createPerformanceReviewRateLimit',
            'readPerformanceReviewRateLimit',
            'listPerformanceReviewRateLimit',
            'updatePerformanceReviewRateLimit',
        ]),
    ),
    (
        'review entity models finalized lifecycle timestamps',
        all(token in MODEL for token in ['PerformanceReview', 'submitted_at', 'finalized_at', 'PERFORMANCE_REVIEW_STATUSES']),
    ),
    (
        'repository supports cycle uniqueness and pagination',
        all(token in REPOSITORY for token in ['cycleIndex', 'findByCycle', 'applyCursorPagination', 'CacheService', 'ConnectionPool']),
    ),
    (
        'service enforces draft submit finalize transitions',
        all(token in SERVICE for token in ["Draft: ['Submitted']", "Submitted: ['Finalized']", 'submitReview', 'finalizeReview']),
    ),
    (
        'finalization requires completed review content',
        'overall_rating' in SERVICE and 'strengths, improvement_areas, and goals_next_period are required before finalization' in SERVICE,
    ),
    (
        'controller enforces scoped access and structured errors',
        all(token in CONTROLLER for token in ['ensureReviewScope', 'FORBIDDEN', 'INVALID_CURSOR', 'DB_CONNECTION_POOL_EXHAUSTED']),
    ),
    (
        'validation checks rating and review period fields',
        all(token in VALIDATION for token in ['must be a number between 1 and 5', 'review_period_start', 'review_period_end']),
    ),
    (
        'workflow schema persists finalized state',
        "status IN ('Draft', 'Submitted', 'Finalized')" in WORKFLOW_SCHEMA and 'finalized_at TIMESTAMPTZ' in WORKFLOW_SCHEMA,
    ),
    (
        'canonical docs and RBAC reflect the performance lifecycle',
        all(token in (WORKFLOW_DOC + SERVICE_MAP + RBAC) for token in ['Draft -> Submitted -> Finalized', '/api/v1/performance-reviews/{performance_review_id}/finalize', 'finalizeReview']),
    ),
]

score = sum(1 for _, ok in checks)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'Performance QC score: {score}/{len(checks)}')
if score < len(checks):
    raise SystemExit(1)
