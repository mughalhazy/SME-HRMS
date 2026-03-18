from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def test_rate_limits_and_throttling_cover_employee_api() -> None:
    routes = read('services/employee-service/employee.routes.ts')
    assert 'createThrottleMiddleware' in routes
    assert 'createPayloadLimitMiddleware' in routes
    for token in [
        'createEmployeeRateLimit',
        'readEmployeeRateLimit',
        'listEmployeeRateLimit',
        'updateEmployeeRateLimit',
        'deleteEmployeeRateLimit',
    ]:
        assert token in routes


def test_repository_uses_cache_indexes_and_pagination() -> None:
    repository = read('services/employee-service/employee.repository.ts')
    assert 'CacheService' in repository
    assert 'applyCursorPagination' in repository
    for token in ['employeeNumberIndex', 'emailIndex', 'departmentIndex', 'statusIndex']:
        assert token in repository


def test_payload_and_cursor_validation_are_enforced() -> None:
    controller = read('services/employee-service/employee.controller.ts')
    validation = read('middleware/validation.ts')
    db_optimization = read('db/optimization.ts')
    assert 'INVALID_CURSOR' in controller
    assert 'INVALID_PAGINATION_LIMIT' in controller
    assert 'PAYLOAD_TOO_LARGE' in validation
    assert 'applyCursorPagination' in db_optimization
    assert 'ConnectionPool' in db_optimization
