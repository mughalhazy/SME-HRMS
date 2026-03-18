from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = (ROOT / 'services/employee-service/employee.routes.ts').read_text()
CONTROLLER = (ROOT / 'services/employee-service/employee.controller.ts').read_text()
REPOSITORY = (ROOT / 'services/employee-service/employee.repository.ts').read_text()
VALIDATION = (ROOT / 'middleware/validation.ts').read_text()
RATE_LIMIT = (ROOT / 'middleware/rate-limit.ts').read_text()
THROTTLE = (ROOT / 'middleware/throttle.ts').read_text()
CACHE = (ROOT / 'cache/cache.service.ts').read_text()
DB_OPT = (ROOT / 'db/optimization.ts').read_text()
METRICS = (ROOT / 'metrics/metrics.ts').read_text()
LOGGER = (ROOT / 'middleware/logger.ts').read_text()

checks: list[tuple[str, bool]] = [
    (
        'rate limits applied to public APIs',
        all(token in ROUTES for token in [
            'createEmployeeRateLimit',
            'readEmployeeRateLimit',
            'listEmployeeRateLimit',
            'updateEmployeeRateLimit',
            'deleteEmployeeRateLimit',
        ]),
    ),
    (
        'request throttling enabled',
        'createThrottleMiddleware' in ROUTES and 'serviceThrottle' in ROUTES and 'REQUEST_THROTTLED' in THROTTLE,
    ),
    (
        'read-heavy caching enabled',
        all(token in REPOSITORY for token in ['CacheService', 'cache.get<PaginatedResult<Employee>>', 'cache.set(cacheKey, result']),
    ),
    (
        'heavy queries require pagination',
        all(token in CONTROLLER + DB_OPT for token in ['cursor', 'limit', 'INVALID_PAGINATION_LIMIT', 'applyCursorPagination']),
    ),
    (
        'database queries optimized with indexes',
        all(token in REPOSITORY for token in ['employeeNumberIndex', 'emailIndex', 'departmentIndex', 'statusIndex', 'resolveExpectedIndex']),
    ),
    (
        'connection pooling enabled',
        'ConnectionPool' in REPOSITORY and 'runWithConnection' in DB_OPT,
    ),
    (
        'input payload limits enforced',
        'createPayloadLimitMiddleware' in ROUTES and 'PAYLOAD_TOO_LARGE' in VALIDATION,
    ),
    (
        'slow query protection present',
        'QueryOptimizer' in REPOSITORY and 'slowQueryThresholdMs' in DB_OPT,
    ),
    (
        'memory growth bounded',
        'this.recentRequests.length > 50' in METRICS and 'this.records.length > 500' in LOGGER and 'maxEntries' in CACHE,
    ),
    (
        'non-blocking concurrency safeguards present',
        'queueTimeoutMs' in THROTTLE and 'DB_CONNECTION_POOL_EXHAUSTED' in CONTROLLER,
    ),
]

score = sum(1 for _, ok in checks)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'Performance QC score: {score}/10')
if score < 10:
    raise SystemExit(1)
