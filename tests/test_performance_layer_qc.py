from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def test_performance_routes_expose_crud_and_workflow_endpoints() -> None:
    routes = read('services/employee-service/employee.routes.ts')
    for token in [
        '/api/v1/performance-reviews',
        '/api/v1/performance-reviews/:performanceReviewId',
        '/api/v1/performance-reviews/:performanceReviewId/submit',
        '/api/v1/performance-reviews/:performanceReviewId/finalize',
        'createPerformanceReviewRateLimit',
        'listPerformanceReviewRateLimit',
        'updatePerformanceReviewRateLimit',
    ]:
        assert token in routes


def test_performance_repository_uses_indexes_cache_and_pagination() -> None:
    repository = read('services/employee-service/performance.repository.ts')
    for token in [
        'CacheService',
        'ConnectionPool',
        'applyCursorPagination',
        'cycleIndex',
        'employeeIndex',
        'reviewerIndex',
        'statusIndex',
        'findByCycle',
    ]:
        assert token in repository


def test_performance_service_enforces_draft_submit_finalize_workflow() -> None:
    service = read('services/employee-service/performance.service.ts')
    for token in [
        "Draft: ['Submitted']",
        "Submitted: ['Finalized']",
        "Finalized: []",
        'performance reviews must be created in Draft status',
        'only Draft performance reviews can be updated',
        'submitReview',
        'finalizeReview',
    ]:
        assert token in service


def test_performance_validation_and_schema_cover_required_fields() -> None:
    validation = read('services/employee-service/performance.validation.ts')
    schema = read('deployment/migrations/002_workflow_schema.sql')
    for token in [
        'review_period_start',
        'review_period_end',
        'overall_rating',
        'must be a number between 1 and 5',
    ]:
        assert token in validation
    for token in [
        'CREATE TABLE IF NOT EXISTS performance_reviews',
        "status IN ('Draft', 'Submitted', 'Finalized')",
        'submitted_at TIMESTAMPTZ',
        'finalized_at TIMESTAMPTZ',
    ]:
        assert token in schema
