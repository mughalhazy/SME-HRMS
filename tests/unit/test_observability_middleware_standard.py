from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_typescript_observability_helpers_define_standardized_logging_fields() -> None:
    logger_source = (ROOT / 'middleware' / 'logger.ts').read_text()
    metrics_source = (ROOT / 'metrics' / 'metrics.ts').read_text()
    request_id_source = (ROOT / 'middleware' / 'request-id.ts').read_text()

    for token in ['action', 'status', 'requestId', 'correlationId', 'tenantId']:
        assert token in logger_source
    for token in ['routeMetrics', 'tenantMetrics', 'correlationId', 'requestId', 'tenantId']:
        assert token in metrics_source
    assert 'x-correlation-id' in request_id_source
