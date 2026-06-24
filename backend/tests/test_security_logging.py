from __future__ import annotations

from resilience import StructuredLogger, sanitize_log_context


def test_sanitize_log_context_redacts_sensitive_fields() -> None:
    payload = sanitize_log_context(
        {
            'username': 'ava.manager',
            'password': 'Password123!',
            'refresh_token': 'refresh-token-value',
            'nested': {
                'bank_account': '123456789',
                'tax_id': '999-99-9999',
            },
        }
    )

    assert payload['username'] == 'ava.manager'
    assert payload['password'] == '[REDACTED]'
    assert payload['refresh_token'] == '[REDACTED]'
    assert payload['nested']['bank_account'] == '[REDACTED]'
    assert payload['nested']['tax_id'] == '[REDACTED]'


def test_structured_logger_redacts_sensitive_context_before_persisting() -> None:
    logger = StructuredLogger('security-test')
    record = logger.info(
        'auth.attempt',
        trace_id='trace-redaction',
        context={'authorization': 'Bearer super-secret', 'password_hash': 'hash', 'username': 'ava.manager'},
    )

    assert record['context']['authorization'] == '[REDACTED]'
    assert record['context']['password_hash'] == '[REDACTED]'
    assert record['context']['username'] == 'ava.manager'



def test_structured_logger_emits_standard_observability_fields() -> None:
    logger = StructuredLogger('security-test')
    record = logger.info(
        'request.completed',
        trace_id='trace-standard-fields',
        message='get_profile',
        context={'tenant_id': 'tenant-acme', 'status': 200, 'correlation_id': 'corr-123', 'action': 'employee.get_profile'},
    )

    assert record['service'] == 'security-test'
    assert record['request_id'] == 'trace-standard-fields'
    assert record['trace_id'] == 'trace-standard-fields'
    assert record['correlation_id'] == 'corr-123'
    assert record['tenant_id'] == 'tenant-acme'
    assert record['action'] == 'employee.get_profile'
    assert record['status'] == '200'
