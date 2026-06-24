from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable
from urllib.parse import urlparse
from uuid import uuid4

from api_contract import pagination_payload
from audit_service.service import emit_audit_record
from background_jobs import BackgroundJobService
from event_contract import EventContractError, EventRegistry, ensure_event_contract, legacy_event_name_for, normalize_event_type
from outbox_system import OutboxManager
from persistent_store import PersistentKVStore
from resilience import DeadLetterQueue, Observability, run_with_retry
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id

HttpClient = Callable[[dict[str, Any]], dict[str, Any]]


class IntegrationServiceError(Exception):
    def __init__(self, code: str, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


class _SecretSealer:
    """Small stdlib-only secret sealer to avoid storing plaintext webhook secrets.

    This is intentionally lightweight for the repo's test environment; callers should override
    HRMS_WEBHOOK_MASTER_KEY in deployed environments.
    """

    def __init__(self, master_key: str | None = None):
        seed = (master_key or os.getenv('HRMS_WEBHOOK_MASTER_KEY') or 'dev-webhook-master-key-please-override').encode('utf-8')
        self._key = hashlib.sha256(seed).digest()

    def seal(self, plaintext: str) -> str:
        nonce = os.urandom(16)
        payload = plaintext.encode('utf-8')
        keystream = self._keystream(nonce, len(payload))
        ciphertext = bytes(left ^ right for left, right in zip(payload, keystream, strict=False))
        mac = hmac.new(self._key, nonce + ciphertext, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(nonce + ciphertext + mac).decode('utf-8')

    def open(self, sealed: str) -> str:
        raw = base64.urlsafe_b64decode(sealed.encode('utf-8'))
        nonce = raw[:16]
        ciphertext = raw[16:-32]
        mac = raw[-32:]
        expected = hmac.new(self._key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected):
            raise IntegrationServiceError('SECRET_INTEGRITY_ERROR', 'Stored webhook secret could not be verified')
        keystream = self._keystream(nonce, len(ciphertext))
        plaintext = bytes(left ^ right for left, right in zip(ciphertext, keystream, strict=False))
        return plaintext.decode('utf-8')

    def fingerprint(self, plaintext: str) -> str:
        return hmac.new(self._key, plaintext.encode('utf-8'), hashlib.sha256).hexdigest()

    def _keystream(self, nonce: bytes, length: int) -> bytes:
        blocks: list[bytes] = []
        counter = 0
        while sum(len(block) for block in blocks) < length:
            blocks.append(hmac.new(self._key, nonce + counter.to_bytes(4, 'big'), hashlib.sha256).digest())
            counter += 1
        return b''.join(blocks)[:length]


@dataclass
class WebhookEndpoint:
    webhook_id: str
    tenant_id: str
    target_url: str
    subscribed_events: tuple[str, ...]
    description: str | None
    status: str
    secret_ciphertext: str
    secret_fingerprint: str
    signature_algorithm: str
    signature_header: str
    max_attempts: int
    retry_backoff_seconds: tuple[int, ...]
    last_delivery_status: str | None
    last_delivery_attempted_at: str | None
    last_success_at: str | None
    last_failure_at: str | None
    consecutive_failures: int
    total_deliveries: int
    created_at: str
    updated_at: str
    deleted_at: str | None = None

    def to_dict(self, *, include_secret: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        payload['subscribed_events'] = list(self.subscribed_events)
        payload['retry_backoff_seconds'] = list(self.retry_backoff_seconds)
        if include_secret:
            payload['secret'] = self.secret_ciphertext
        payload.pop('secret_ciphertext', None)
        return payload


@dataclass
class WebhookDelivery:
    delivery_id: str
    tenant_id: str
    webhook_id: str
    event_id: str
    event_name: str
    event_type: str
    source: str
    target_url: str
    payload: dict[str, Any]
    status: str
    attempt_count: int
    last_http_status: int | None
    last_error: str | None
    dead_lettered_at: str | None
    next_retry_at: str | None
    created_at: str
    updated_at: str
    replay_of_delivery_id: str | None = None
    background_job_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WebhookDeliveryAttempt:
    attempt_id: str
    delivery_id: str
    tenant_id: str
    webhook_id: str
    event_id: str
    event_type: str
    target_url: str
    attempt_number: int
    status: str
    request_headers: dict[str, Any]
    request_body: str
    response_status: int | None
    response_body: str | None
    error_message: str | None
    duration_ms: float
    retryable: bool
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IntegrationService:
    def __init__(
        self,
        *,
        db_path: str | None = None,
        background_jobs: BackgroundJobService | None = None,
        http_client: HttpClient | None = None,
        master_key: str | None = None,
    ) -> None:
        self.webhooks = PersistentKVStore[str, WebhookEndpoint](service='integration-service', namespace='webhooks', db_path=db_path)
        shared_db_path = self.webhooks.db_path
        self.deliveries = PersistentKVStore[str, WebhookDelivery](service='integration-service', namespace='deliveries', db_path=shared_db_path)
        self.delivery_attempts = PersistentKVStore[str, WebhookDeliveryAttempt](service='integration-service', namespace='delivery_attempts', db_path=shared_db_path)
        self.event_registry = EventRegistry()
        self.outbox = OutboxManager(service_name='integration-service', tenant_id=DEFAULT_TENANT_ID, db_path=shared_db_path, event_registry=self.event_registry)
        self.dead_letters = DeadLetterQueue()
        self.observability = Observability('integration-service')
        self.background_jobs = background_jobs or BackgroundJobService(db_path=shared_db_path)
        self.http_client = http_client or self._default_http_client
        self.secret_sealer = _SecretSealer(master_key)
        self._lock = RLock()
        self.background_jobs.register_handler('integration.webhook.deliver', self._run_delivery_job, max_attempts=1)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _default_http_client(request: dict[str, Any]) -> dict[str, Any]:
        return {'status_code': 202, 'body': json.dumps({'accepted': True, 'url': request['url']})}

    def _trace(self, trace_id: str | None) -> str:
        return self.observability.trace_id(trace_id)

    def _validate_target_url(self, target_url: str) -> None:
        parsed = urlparse(target_url)
        if parsed.scheme not in {'https', 'http'}:
            raise IntegrationServiceError('VALIDATION_ERROR', 'target_url must use http or https', details=[{'field': 'target_url', 'reason': 'unsupported scheme'}])
        if parsed.scheme != 'https' and parsed.hostname not in {'localhost', '127.0.0.1'}:
            raise IntegrationServiceError('VALIDATION_ERROR', 'target_url must use https outside local development', details=[{'field': 'target_url', 'reason': 'https required'}])
        if not parsed.netloc:
            raise IntegrationServiceError('VALIDATION_ERROR', 'target_url must be an absolute URL', details=[{'field': 'target_url', 'reason': 'absolute URL required'}])

    def _normalize_subscribed_events(self, subscribed_events: list[str] | tuple[str, ...]) -> tuple[str, ...]:
        if not isinstance(subscribed_events, (list, tuple)) or not subscribed_events:
            raise IntegrationServiceError('VALIDATION_ERROR', 'subscribed_events must contain at least one event', details=[{'field': 'subscribed_events', 'reason': 'must be a non-empty array'}])
        normalized = sorted({normalize_event_type(str(item)) for item in subscribed_events})
        return tuple(normalized)

    def _mask_headers(self, headers: dict[str, Any]) -> dict[str, Any]:
        masked = dict(headers)
        if 'Authorization' in masked:
            masked['Authorization'] = '***'
        return masked

    def _serialize_webhook(self, webhook: WebhookEndpoint) -> dict[str, Any]:
        payload = webhook.to_dict()
        payload['secret'] = {
            'configured': True,
            'fingerprint': webhook.secret_fingerprint,
        }
        return payload

    def _audit(self, *, action: str, tenant_id: str, entity_id: str, before: dict[str, Any], after: dict[str, Any], actor: dict[str, Any] | None, trace_id: str) -> None:
        emit_audit_record(
            service_name='integration-service',
            tenant_id=tenant_id,
            actor=actor or {'id': 'system', 'type': 'service'},
            action=action,
            entity='WebhookEndpoint',
            entity_id=entity_id,
            before=before,
            after=after,
            trace_id=trace_id,
            source={'module': 'webhooks'},
        )

    def create_webhook(self, payload: dict[str, Any], *, actor: dict[str, Any] | None = None, trace_id: str | None = None) -> WebhookEndpoint:
        trace = self._trace(trace_id)
        tenant_id = normalize_tenant_id(str(payload.get('tenant_id') or DEFAULT_TENANT_ID))
        target_url = str(payload.get('target_url') or '').strip()
        secret = str(payload.get('secret') or '').strip()
        description = str(payload['description']).strip() if payload.get('description') is not None else None
        self._validate_target_url(target_url)
        if not secret:
            raise IntegrationServiceError('VALIDATION_ERROR', 'secret is required', details=[{'field': 'secret', 'reason': 'must be a non-empty string'}])
        subscribed_events = self._normalize_subscribed_events(payload.get('subscribed_events') or [])
        max_attempts = int(payload.get('max_attempts', 3) or 3)
        if max_attempts < 1 or max_attempts > 10:
            raise IntegrationServiceError('VALIDATION_ERROR', 'max_attempts must be between 1 and 10', details=[{'field': 'max_attempts', 'reason': 'out of range'}])
        retry_backoff_seconds = tuple(int(value) for value in (payload.get('retry_backoff_seconds') or [0, 1, 5]))
        now = self._now()
        webhook = WebhookEndpoint(
            webhook_id=str(uuid4()),
            tenant_id=tenant_id,
            target_url=target_url,
            subscribed_events=subscribed_events,
            description=description,
            status='Active',
            secret_ciphertext=self.secret_sealer.seal(secret),
            secret_fingerprint=self.secret_sealer.fingerprint(secret),
            signature_algorithm='hmac-sha256',
            signature_header='X-HRMS-Signature-256',
            max_attempts=max_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
            last_delivery_status=None,
            last_delivery_attempted_at=None,
            last_success_at=None,
            last_failure_at=None,
            consecutive_failures=0,
            total_deliveries=0,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self.webhooks[webhook.webhook_id] = webhook
        self._audit(action='webhook_registered', tenant_id=tenant_id, entity_id=webhook.webhook_id, before={}, after=self._serialize_webhook(webhook), actor=actor, trace_id=trace)
        return webhook

    def update_webhook(self, webhook_id: str, payload: dict[str, Any], *, actor: dict[str, Any] | None = None, trace_id: str | None = None) -> WebhookEndpoint:
        trace = self._trace(trace_id)
        webhook = self.webhooks.get(webhook_id)
        if webhook is None or webhook.status == 'Deleted':
            raise IntegrationServiceError('WEBHOOK_NOT_FOUND', 'Webhook not found')
        tenant_id = normalize_tenant_id(str(payload.get('tenant_id') or webhook.tenant_id))
        assert_tenant_access(webhook.tenant_id, tenant_id)
        before = self._serialize_webhook(webhook)
        if 'target_url' in payload:
            webhook.target_url = str(payload['target_url']).strip()
            self._validate_target_url(webhook.target_url)
        if 'subscribed_events' in payload:
            webhook.subscribed_events = self._normalize_subscribed_events(payload['subscribed_events'])
        if 'description' in payload:
            webhook.description = str(payload['description']).strip() if payload['description'] is not None else None
        if 'status' in payload:
            status = str(payload['status'])
            if status not in {'Active', 'Disabled'}:
                raise IntegrationServiceError('VALIDATION_ERROR', 'status must be Active or Disabled', details=[{'field': 'status', 'reason': 'invalid value'}])
            webhook.status = status
        if 'secret' in payload and payload.get('secret'):
            secret = str(payload['secret']).strip()
            webhook.secret_ciphertext = self.secret_sealer.seal(secret)
            webhook.secret_fingerprint = self.secret_sealer.fingerprint(secret)
        if 'max_attempts' in payload:
            max_attempts = int(payload['max_attempts'])
            if max_attempts < 1 or max_attempts > 10:
                raise IntegrationServiceError('VALIDATION_ERROR', 'max_attempts must be between 1 and 10', details=[{'field': 'max_attempts', 'reason': 'out of range'}])
            webhook.max_attempts = max_attempts
        if 'retry_backoff_seconds' in payload:
            webhook.retry_backoff_seconds = tuple(int(value) for value in payload['retry_backoff_seconds'])
        webhook.updated_at = self._now()
        self.webhooks[webhook.webhook_id] = webhook
        self._audit(action='webhook_updated', tenant_id=webhook.tenant_id, entity_id=webhook.webhook_id, before=before, after=self._serialize_webhook(webhook), actor=actor, trace_id=trace)
        return webhook

    def delete_webhook(self, webhook_id: str, *, tenant_id: str, actor: dict[str, Any] | None = None, trace_id: str | None = None) -> WebhookEndpoint:
        trace = self._trace(trace_id)
        webhook = self.webhooks.get(webhook_id)
        if webhook is None or webhook.status == 'Deleted':
            raise IntegrationServiceError('WEBHOOK_NOT_FOUND', 'Webhook not found')
        assert_tenant_access(webhook.tenant_id, tenant_id)
        before = self._serialize_webhook(webhook)
        webhook.status = 'Deleted'
        webhook.deleted_at = self._now()
        webhook.updated_at = webhook.deleted_at
        self.webhooks[webhook.webhook_id] = webhook
        self._audit(action='webhook_deleted', tenant_id=webhook.tenant_id, entity_id=webhook.webhook_id, before=before, after=self._serialize_webhook(webhook), actor=actor, trace_id=trace)
        return webhook

    def get_webhook(self, webhook_id: str, *, tenant_id: str) -> WebhookEndpoint:
        webhook = self.webhooks.get(webhook_id)
        if webhook is None or webhook.status == 'Deleted':
            raise IntegrationServiceError('WEBHOOK_NOT_FOUND', 'Webhook not found')
        assert_tenant_access(webhook.tenant_id, tenant_id)
        return webhook

    def list_webhooks(self, *, tenant_id: str, status: str | None = None, limit: int = 25, cursor: str | None = None) -> tuple[list[WebhookEndpoint], dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [row for row in self.webhooks.values() if row.tenant_id == tenant and row.status != 'Deleted']
        if status is not None:
            rows = [row for row in rows if row.status == status]
        rows.sort(key=lambda row: (row.created_at, row.webhook_id))
        offset = int(cursor or 0)
        page = rows[offset: offset + limit]
        next_cursor = str(offset + limit) if offset + limit < len(rows) else None
        return page, pagination_payload(limit=limit, cursor=cursor, next_cursor=next_cursor, count=len(page), extra={'total_count': len(rows)})

    def _subscriptions_for(self, tenant_id: str, event_type: str) -> list[WebhookEndpoint]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [
            row for row in self.webhooks.values()
            if row.tenant_id == tenant
            and row.status == 'Active'
            and event_type in row.subscribed_events
        ]
        rows.sort(key=lambda row: row.created_at)
        return rows

    def consume_event(self, payload: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        trace = self._trace(trace_id)
        try:
            event, _ = ensure_event_contract(
                payload,
                source=str(payload.get('source') or 'integration-ingress'),
                idempotency_key=(payload.get('metadata') or {}).get('idempotency_key') if isinstance(payload.get('metadata'), dict) else None,
                registry=self.event_registry,
            )
        except EventContractError as exc:
            raise IntegrationServiceError('VALIDATION_ERROR', str(exc)) from exc

        def _schedule(event_payload: dict[str, Any]) -> dict[str, Any]:
            subscriptions = self._subscriptions_for(str(event_payload['tenant_id']), str(event_payload['event_type']))
            scheduled: list[dict[str, Any]] = []
            for webhook in subscriptions:
                scheduled.append(self._create_delivery_for_event(webhook, event_payload, trace_id=trace))
            return {
                'event_id': event_payload['event_id'],
                'event_type': event_payload['event_type'],
                'matched_webhooks': len(subscriptions),
                'scheduled_deliveries': scheduled,
            }

        result, duplicate = self.outbox.consume_once(consumer_name='integration-service', event=event, handler=_schedule)
        return {**result, 'duplicate': duplicate}

    def _create_delivery_for_event(self, webhook: WebhookEndpoint, event: dict[str, Any], *, trace_id: str) -> dict[str, Any]:
        now = self._now()
        event_name = str(event.get('metadata', {}).get('legacy_event_name') or legacy_event_name_for(str(event['event_type'])))
        delivery = WebhookDelivery(
            delivery_id=str(uuid4()),
            tenant_id=webhook.tenant_id,
            webhook_id=webhook.webhook_id,
            event_id=str(event['event_id']),
            event_name=event_name,
            event_type=str(event['event_type']),
            source=str(event['source']),
            target_url=webhook.target_url,
            payload=dict(event),
            status='Scheduled',
            attempt_count=0,
            last_http_status=None,
            last_error=None,
            dead_lettered_at=None,
            next_retry_at=None,
            created_at=now,
            updated_at=now,
        )
        self.deliveries[delivery.delivery_id] = delivery
        job = self.background_jobs.enqueue_job(
            tenant_id=webhook.tenant_id,
            job_type='integration.webhook.deliver',
            payload={'delivery_id': delivery.delivery_id},
            trace_id=trace_id,
            correlation_id=str(event.get('metadata', {}).get('correlation_id') or trace_id),
            idempotency_key=f"integration:{delivery.delivery_id}",
            actor_type='service',
        )
        delivery.background_job_id = job.job_id
        self.deliveries[delivery.delivery_id] = delivery
        return {'delivery_id': delivery.delivery_id, 'webhook_id': webhook.webhook_id, 'background_job_id': job.job_id}

    def _signature_headers(self, webhook: WebhookEndpoint, body: str) -> dict[str, str]:
        secret = self.secret_sealer.open(webhook.secret_ciphertext)
        timestamp = self._now()
        digest = hmac.new(secret.encode('utf-8'), f'{timestamp}.{body}'.encode('utf-8'), hashlib.sha256).hexdigest()
        return {
            'Content-Type': 'application/json',
            'User-Agent': 'sme-hrms-integration-service/1.0',
            'X-HRMS-Webhook-Id': webhook.webhook_id,
            'X-HRMS-Event-Id': body and str(json.loads(body).get('event_id')),
            'X-HRMS-Event-Type': body and str(json.loads(body).get('event_type')),
            'X-HRMS-Tenant-Id': webhook.tenant_id,
            'X-HRMS-Timestamp': timestamp,
            webhook.signature_header: f'sha256={digest}',
        }

    def _record_attempt(
        self,
        *,
        delivery: WebhookDelivery,
        webhook: WebhookEndpoint,
        request_headers: dict[str, Any],
        request_body: str,
        response_status: int | None,
        response_body: str | None,
        error_message: str | None,
        duration_ms: float,
        retryable: bool,
        success: bool,
    ) -> WebhookDeliveryAttempt:
        attempt = WebhookDeliveryAttempt(
            attempt_id=str(uuid4()),
            delivery_id=delivery.delivery_id,
            tenant_id=delivery.tenant_id,
            webhook_id=delivery.webhook_id,
            event_id=delivery.event_id,
            event_type=delivery.event_type,
            target_url=delivery.target_url,
            attempt_number=delivery.attempt_count,
            status='Succeeded' if success else 'Failed',
            request_headers=self._mask_headers(request_headers),
            request_body=request_body,
            response_status=response_status,
            response_body=response_body,
            error_message=error_message,
            duration_ms=round(duration_ms, 3),
            retryable=retryable,
            created_at=self._now(),
        )
        self.delivery_attempts[attempt.attempt_id] = attempt
        webhook.last_delivery_attempted_at = attempt.created_at
        webhook.total_deliveries += 1
        if success:
            webhook.last_delivery_status = 'Succeeded'
            webhook.last_success_at = attempt.created_at
            webhook.consecutive_failures = 0
        else:
            webhook.last_delivery_status = 'Failed'
            webhook.last_failure_at = attempt.created_at
            webhook.consecutive_failures += 1
        webhook.updated_at = self._now()
        self.webhooks[webhook.webhook_id] = webhook
        return attempt

    def _perform_delivery_attempt(self, delivery: WebhookDelivery, webhook: WebhookEndpoint) -> dict[str, Any]:
        started = datetime.now(timezone.utc)
        body = json.dumps(delivery.payload, sort_keys=True)
        headers = self._signature_headers(webhook, body)
        request = {'method': 'POST', 'url': webhook.target_url, 'headers': headers, 'body': body, 'timeout_seconds': 10}
        try:
            response = self.http_client(request)
        except Exception as exc:  # noqa: BLE001
            duration_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
            self._record_attempt(
                delivery=delivery,
                webhook=webhook,
                request_headers=headers,
                request_body=body,
                response_status=None,
                response_body=None,
                error_message=str(exc),
                duration_ms=duration_ms,
                retryable=True,
                success=False,
            )
            raise

        status_code = int(response.get('status_code', 500))
        response_body = str(response.get('body', '')) if response.get('body') is not None else None
        duration_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        if 200 <= status_code < 300:
            self._record_attempt(
                delivery=delivery,
                webhook=webhook,
                request_headers=headers,
                request_body=body,
                response_status=status_code,
                response_body=response_body,
                error_message=None,
                duration_ms=duration_ms,
                retryable=False,
                success=True,
            )
            return {'status_code': status_code, 'body': response_body}

        retryable = status_code >= 500 or status_code in {408, 409, 425, 429}
        self._record_attempt(
            delivery=delivery,
            webhook=webhook,
            request_headers=headers,
            request_body=body,
            response_status=status_code,
            response_body=response_body,
            error_message=f'HTTP {status_code}',
            duration_ms=duration_ms,
            retryable=retryable,
            success=False,
        )
        error = RuntimeError(f'webhook delivery failed with HTTP {status_code}')
        setattr(error, 'retryable', retryable)
        raise error

    def dispatch_delivery(self, delivery_id: str, *, tenant_id: str, trace_id: str | None = None) -> WebhookDelivery:
        trace = self._trace(trace_id)
        delivery = self.deliveries.get(delivery_id)
        if delivery is None:
            raise IntegrationServiceError('DELIVERY_NOT_FOUND', 'Delivery not found')
        assert_tenant_access(delivery.tenant_id, tenant_id)
        webhook = self.get_webhook(delivery.webhook_id, tenant_id=tenant_id)
        delivery.status = 'Delivering'
        delivery.updated_at = self._now()
        self.deliveries[delivery.delivery_id] = delivery

        def _attempt() -> dict[str, Any]:
            delivery.attempt_count += 1
            self.deliveries[delivery.delivery_id] = delivery
            return self._perform_delivery_attempt(delivery, webhook)

        try:
            run_with_retry(
                _attempt,
                attempts=webhook.max_attempts,
                base_delay=max(webhook.retry_backoff_seconds[1] if len(webhook.retry_backoff_seconds) > 1 else 0.01, 0.01),
                timeout_seconds=2.0,
                retryable=lambda exc: bool(getattr(exc, 'retryable', True)),
            )
            last_attempt = max((row for row in self.delivery_attempts.values() if row.delivery_id == delivery.delivery_id), key=lambda row: row.attempt_number)
            delivery.status = 'Succeeded'
            delivery.last_http_status = last_attempt.response_status
            delivery.last_error = None
            delivery.next_retry_at = None
            delivery.updated_at = self._now()
            self.deliveries[delivery.delivery_id] = delivery
        except Exception as exc:  # noqa: BLE001
            last_attempts = [row for row in self.delivery_attempts.values() if row.delivery_id == delivery.delivery_id]
            last_attempt = max(last_attempts, key=lambda row: row.attempt_number)
            delivery.status = 'DeadLettered'
            delivery.last_http_status = last_attempt.response_status
            delivery.last_error = str(exc)
            delivery.dead_lettered_at = self._now()
            delivery.next_retry_at = None
            delivery.updated_at = delivery.dead_lettered_at
            self.deliveries[delivery.delivery_id] = delivery
            self.dead_letters.push(
                'integration.webhook.delivery',
                delivery.event_type,
                {'delivery_id': delivery.delivery_id, 'webhook_id': delivery.webhook_id, 'event_id': delivery.event_id},
                str(exc),
                trace_id=trace,
                retryable=True,
            )
            self.observability.logger.error(
                'integration.delivery_failed',
                trace_id=trace,
                message=delivery.event_type,
                context={'delivery_id': delivery.delivery_id, 'webhook_id': delivery.webhook_id, 'tenant_id': delivery.tenant_id, 'error': str(exc)},
            )
        return delivery

    def _run_delivery_job(self, context: Any) -> dict[str, Any]:
        delivery = self.dispatch_delivery(str(context.job.payload['delivery_id']), tenant_id=context.tenant_id, trace_id=context.trace_id)
        return delivery.to_dict()

    def run_delivery_jobs(self, *, tenant_id: str | None = None) -> list[Any]:
        return self.background_jobs.run_due_jobs(tenant_id=tenant_id)

    def list_delivery_attempts(
        self,
        *,
        tenant_id: str,
        webhook_id: str | None = None,
        delivery_status: str | None = None,
        event_type: str | None = None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        tenant = normalize_tenant_id(tenant_id)
        deliveries = {row.delivery_id: row for row in self.deliveries.values() if row.tenant_id == tenant}
        attempts = [row for row in self.delivery_attempts.values() if row.tenant_id == tenant and row.delivery_id in deliveries]
        if webhook_id is not None:
            attempts = [row for row in attempts if row.webhook_id == webhook_id]
        if event_type is not None:
            normalized = normalize_event_type(event_type)
            attempts = [row for row in attempts if row.event_type == normalized]
        if delivery_status is not None:
            attempts = [row for row in attempts if deliveries[row.delivery_id].status == delivery_status]
        attempts.sort(key=lambda row: (row.created_at, row.attempt_number, row.attempt_id), reverse=True)
        offset = int(cursor or 0)
        page = attempts[offset: offset + limit]
        next_cursor = str(offset + limit) if offset + limit < len(attempts) else None
        items = []
        for row in page:
            payload = row.to_dict()
            payload['delivery'] = deliveries[row.delivery_id].to_dict()
            items.append(payload)
        return items, pagination_payload(limit=limit, cursor=cursor, next_cursor=next_cursor, count=len(items), extra={'total_count': len(attempts)})

    def replay_failed_delivery(self, delivery_id: str, *, tenant_id: str, actor: dict[str, Any] | None = None, trace_id: str | None = None) -> WebhookDelivery:
        trace = self._trace(trace_id)
        delivery = self.deliveries.get(delivery_id)
        if delivery is None:
            raise IntegrationServiceError('DELIVERY_NOT_FOUND', 'Delivery not found')
        assert_tenant_access(delivery.tenant_id, tenant_id)
        if delivery.status not in {'DeadLettered', 'Failed'}:
            raise IntegrationServiceError('INVALID_DELIVERY_STATE', 'Only failed or dead-lettered deliveries can be replayed')
        replay = WebhookDelivery(
            delivery_id=str(uuid4()),
            tenant_id=delivery.tenant_id,
            webhook_id=delivery.webhook_id,
            event_id=delivery.event_id,
            event_name=delivery.event_name,
            event_type=delivery.event_type,
            source=delivery.source,
            target_url=delivery.target_url,
            payload=dict(delivery.payload),
            status='Scheduled',
            attempt_count=0,
            last_http_status=None,
            last_error=None,
            dead_lettered_at=None,
            next_retry_at=None,
            created_at=self._now(),
            updated_at=self._now(),
            replay_of_delivery_id=delivery.delivery_id,
        )
        self.deliveries[replay.delivery_id] = replay
        job = self.background_jobs.enqueue_job(
            tenant_id=replay.tenant_id,
            job_type='integration.webhook.deliver',
            payload={'delivery_id': replay.delivery_id},
            trace_id=trace,
            correlation_id=trace,
            idempotency_key=f'integration:replay:{replay.delivery_id}',
            actor_type='service',
        )
        replay.background_job_id = job.job_id
        self.deliveries[replay.delivery_id] = replay
        emit_audit_record(
            service_name='integration-service',
            tenant_id=replay.tenant_id,
            actor=actor or {'id': 'system', 'type': 'service'},
            action='webhook_delivery_replayed',
            entity='WebhookDelivery',
            entity_id=replay.delivery_id,
            before=delivery.to_dict(),
            after=replay.to_dict(),
            trace_id=trace,
            source={'module': 'webhooks'},
        )
        return replay
