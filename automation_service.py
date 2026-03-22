from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4

from audit_service.service import emit_audit_record
from automation_contract import AutomationContractError, ensure_automation_rule_contract
from event_contract import EventContractError, EventRegistry, emit_canonical_event, ensure_event_contract, legacy_event_name_for
from notification_service import NotificationChannel, NotificationService
from outbox_system import OutboxManager
from persistent_store import PersistentKVStore
from resilience import Observability
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id
from workflow_service import WorkflowService


class AutomationServiceError(Exception):
    def __init__(self, code: str, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


@dataclass(slots=True)
class AutomationRule:
    rule_id: str
    tenant_id: str
    name: str
    description: str | None
    status: str
    trigger: dict[str, Any]
    conditions: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    execution: dict[str, Any]
    metadata: dict[str, Any]
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AutomationExecution:
    execution_id: str
    tenant_id: str
    rule_id: str
    event_id: str
    event_type: str
    status: str
    matched: bool
    duplicate: bool
    action_results: list[dict[str, Any]]
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AutomationService:
    def __init__(
        self,
        *,
        db_path: str | None = None,
        workflow_service: WorkflowService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.rules = PersistentKVStore[str, AutomationRule](service='automation-service', namespace='rules', db_path=db_path)
        shared_db_path = self.rules.db_path
        self.executions = PersistentKVStore[str, AutomationExecution](service='automation-service', namespace='executions', db_path=shared_db_path)
        self.subject_state = PersistentKVStore[str, dict[str, Any]](service='automation-service', namespace='subject_state', db_path=shared_db_path)
        self.events: list[dict[str, Any]] = []
        self.event_registry = EventRegistry()
        self.outbox = OutboxManager(service_name='automation-service', tenant_id=DEFAULT_TENANT_ID, db_path=shared_db_path, event_registry=self.event_registry)
        self.notification_service = notification_service or NotificationService()
        self.workflow_service = workflow_service or WorkflowService(notification_service=self.notification_service)
        self.observability = Observability('automation-service')
        self._lock = RLock()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _trace(self, trace_id: str | None) -> str:
        return self.observability.trace_id(trace_id)

    def create_rule(self, payload: dict[str, Any], *, actor: dict[str, Any] | None = None, trace_id: str | None = None) -> AutomationRule:
        trace = self._trace(trace_id)
        tenant_id = normalize_tenant_id(str(payload.get('tenant_id') or DEFAULT_TENANT_ID))
        try:
            normalized = ensure_automation_rule_contract({**payload, 'tenant_id': tenant_id})
        except AutomationContractError as exc:
            raise AutomationServiceError('VALIDATION_ERROR', f'Invalid automation rule: {exc}') from exc
        now = self._now()
        rule = AutomationRule(
            rule_id=str(normalized['rule_id']),
            tenant_id=tenant_id,
            name=str(normalized['name']),
            description=normalized.get('description'),
            status=str(normalized['status']),
            trigger=dict(normalized['trigger']),
            conditions=[dict(item) for item in normalized['conditions']],
            actions=[dict(item) for item in normalized['actions']],
            execution=dict(normalized['execution']),
            metadata=dict(normalized['metadata']),
            created_at=now,
            updated_at=now,
        )
        self.rules[rule.rule_id] = rule
        self._audit('automation_rule_created', rule.tenant_id, rule.rule_id, {}, rule.to_dict(), actor, trace)
        self._emit_event('AutomationRuleCreated', tenant_id=rule.tenant_id, trace_id=trace, data={'rule_id': rule.rule_id, 'name': rule.name, 'status': rule.status})
        return rule

    def list_rules(self, *, tenant_id: str, status: str | None = None) -> list[AutomationRule]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [row for row in self.rules.values() if row.tenant_id == tenant]
        if status:
            rows = [row for row in rows if row.status == status]
        rows.sort(key=lambda row: (row.created_at, row.rule_id))
        return rows

    def get_rule(self, rule_id: str, *, tenant_id: str) -> AutomationRule:
        rule = self.rules[rule_id]
        assert_tenant_access(rule.tenant_id, normalize_tenant_id(tenant_id))
        return rule

    def list_executions(self, *, tenant_id: str, rule_id: str | None = None) -> list[AutomationExecution]:
        tenant = normalize_tenant_id(tenant_id)
        rows = [row for row in self.executions.values() if row.tenant_id == tenant]
        if rule_id:
            rows = [row for row in rows if row.rule_id == rule_id]
        rows.sort(key=lambda row: (row.created_at, row.execution_id), reverse=True)
        return rows

    def get_subject_state(self, *, tenant_id: str, resource_type: str, resource_id: str) -> dict[str, Any] | None:
        key = self._subject_key(tenant_id=tenant_id, resource_type=resource_type, resource_id=resource_id)
        return self.subject_state.get(key)

    def consume_event(self, event: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        trace = self._trace(trace_id)
        try:
            canonical_event, _ = ensure_event_contract(event, source='automation-service', registry=self.event_registry)
        except EventContractError as exc:
            if str(exc) == 'missing_tenant_context':
                raise AutomationServiceError('VALIDATION_ERROR', 'tenant_id is required') from exc
            raise AutomationServiceError('VALIDATION_ERROR', f'Invalid event payload: {exc}') from exc
        tenant_id = normalize_tenant_id(str(canonical_event['tenant_id']))
        matching_rules = [
            rule for rule in self.list_rules(tenant_id=tenant_id, status='Active')
            if canonical_event['event_type'] in rule.trigger.get('event_types', [])
            and (
                not rule.trigger.get('source_services')
                or str(canonical_event.get('source') or canonical_event.get('producer_service') or '') in rule.trigger.get('source_services', [])
            )
        ]
        results: list[dict[str, Any]] = []
        for rule in matching_rules:
            result, duplicate = self.outbox.consume_once(
                consumer_name=f'automation-rule:{rule.rule_id}',
                event=canonical_event,
                handler=lambda payload, current_rule=rule: self._execute_rule(current_rule, payload, trace_id=trace),
            )
            results.append({**result, 'duplicate': duplicate})
        return {
            'tenant_id': tenant_id,
            'event_id': canonical_event['event_id'],
            'event_type': canonical_event['event_type'],
            'matched_rules': len(matching_rules),
            'results': results,
        }

    def _execute_rule(self, rule: AutomationRule, event: dict[str, Any], *, trace_id: str) -> dict[str, Any]:
        matched = self._conditions_match(rule.conditions, event)
        action_results: list[dict[str, Any]] = []
        status = 'skipped'
        if matched:
            for action in rule.actions:
                action_results.append(self._execute_action(rule, action, event, trace_id=trace_id))
            status = 'executed'
        execution = AutomationExecution(
            execution_id=str(uuid4()),
            tenant_id=rule.tenant_id,
            rule_id=rule.rule_id,
            event_id=str(event['event_id']),
            event_type=str(event['event_type']),
            status=status,
            matched=matched,
            duplicate=False,
            action_results=action_results,
            created_at=self._now(),
            metadata={'trace_id': trace_id},
        )
        self.executions[execution.execution_id] = execution
        self._audit(
            'automation_rule_executed',
            rule.tenant_id,
            rule.rule_id,
            {'matched': matched, 'event_id': event['event_id']},
            execution.to_dict(),
            {'id': 'automation-studio', 'type': 'service'},
            trace_id,
        )
        self._emit_event(
            'AutomationRuleExecuted',
            tenant_id=rule.tenant_id,
            trace_id=trace_id,
            data={'rule_id': rule.rule_id, 'event_id': event['event_id'], 'event_type': event['event_type'], 'matched': matched, 'status': status},
        )
        return execution.to_dict()

    def _execute_action(self, rule: AutomationRule, action: dict[str, Any], event: dict[str, Any], *, trace_id: str) -> dict[str, Any]:
        kind = action['kind']
        config = dict(action.get('config') or {})
        if kind == 'workflow':
            return self._execute_workflow_action(rule, config, event, trace_id=trace_id)
        if kind == 'notify':
            return self._execute_notify_action(config, event, trace_id=trace_id)
        if kind == 'update':
            return self._execute_update_action(config, event)
        raise AutomationServiceError('VALIDATION_ERROR', f'Unsupported action kind: {kind}')

    def _execute_workflow_action(self, rule: AutomationRule, config: dict[str, Any], event: dict[str, Any], *, trace_id: str) -> dict[str, Any]:
        subject_id = self._resolve_template_value(config.get('subject_id'), event)
        if not subject_id:
            raise AutomationServiceError('VALIDATION_ERROR', 'workflow action requires subject_id')
        workflow = self.workflow_service.start_workflow(
            tenant_id=rule.tenant_id,
            definition_code=str(config['definition_code']),
            source_service='automation-service',
            subject_type=str(config.get('subject_type') or 'AutomationSubject'),
            subject_id=str(subject_id),
            actor_id='automation-studio',
            actor_type='service',
            context={
                'automation_rule_id': rule.rule_id,
                'source_event_id': event['event_id'],
                'source_event_type': event['event_type'],
                **dict(config.get('context') or {}),
            },
            trace_id=trace_id,
        )
        return {'kind': 'workflow', 'workflow_id': workflow['workflow_id'], 'definition_code': workflow['definition_code'], 'status': workflow['status']}

    def _execute_notify_action(self, config: dict[str, Any], event: dict[str, Any], *, trace_id: str) -> dict[str, Any]:
        subject_id = self._resolve_template_value(config.get('subject_id'), event)
        if not subject_id:
            raise AutomationServiceError('VALIDATION_ERROR', 'notify action requires subject_id')
        destination = self._resolve_template_value(config.get('destination'), event) or f'inbox:{subject_id}'
        channel = NotificationChannel[str(config.get('channel') or 'IN_APP').upper()]
        message = self.notification_service._queue_notification(
            tenant_id=normalize_tenant_id(str(event['tenant_id'])),
            template_code=str(config['template_code']),
            subject_type=str(config.get('subject_type') or 'Employee'),
            subject_id=str(subject_id),
            topic_code=str(config.get('topic_code') or config['template_code']),
            channel=channel,
            destination=str(destination),
            payload={
                **dict(event.get('data') or {}),
                'event_id': event['event_id'],
                'event_type': event['event_type'],
                'tenant_id': event['tenant_id'],
            },
            event_name=str(config.get('event_name') or legacy_event_name_for(str(event['event_type']))),
            event_type=str(event['event_type']),
            trace_id=trace_id,
        )
        return {'kind': 'notify', 'message_id': message.message_id, 'channel': message.channel.value, 'status': message.status.value}

    def _execute_update_action(self, config: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
        resource_type = str(config.get('resource_type') or '').strip()
        resource_id = self._resolve_template_value(config.get('resource_id'), event)
        if not resource_type or not resource_id:
            raise AutomationServiceError('VALIDATION_ERROR', 'update action requires resource_type and resource_id')
        key = self._subject_key(tenant_id=str(event['tenant_id']), resource_type=resource_type, resource_id=str(resource_id))
        before = dict(self.subject_state.get(key) or {})
        patch = {
            str(field_name): self._resolve_template_value(value, event)
            for field_name, value in dict(config.get('set') or {}).items()
        }
        after = {
            **before,
            'tenant_id': normalize_tenant_id(str(event['tenant_id'])),
            'resource_type': resource_type,
            'resource_id': str(resource_id),
            **patch,
        }
        self.subject_state[key] = after
        return {'kind': 'update', 'resource_type': resource_type, 'resource_id': str(resource_id), 'before': before, 'after': after}

    def _conditions_match(self, conditions: list[dict[str, Any]], event: dict[str, Any]) -> bool:
        for condition in conditions:
            actual = self._lookup_path(event, condition['field'])
            operator = condition['operator']
            expected = condition.get('value')
            if operator == 'exists' and actual is None:
                return False
            if operator == 'eq' and actual != expected:
                return False
            if operator == 'neq' and actual == expected:
                return False
            if operator == 'contains' and expected not in (actual or [] if isinstance(actual, list) else str(actual or '')):
                return False
            if operator == 'in' and actual not in list(expected or []):
                return False
            if operator == 'gte' and actual < expected:
                return False
            if operator == 'lte' and actual > expected:
                return False
        return True

    def _resolve_template_value(self, template: Any, event: dict[str, Any]) -> Any:
        if isinstance(template, dict) and 'from' in template:
            return self._lookup_path(event, str(template['from']))
        return template

    @staticmethod
    def _lookup_path(payload: dict[str, Any], path: str) -> Any:
        current: Any = payload
        normalized_path = path[1:] if path.startswith('$') else path
        for segment in normalized_path.split('.'):
            if not segment:
                continue
            if isinstance(current, dict):
                current = current.get(segment)
            else:
                return None
        return current

    @staticmethod
    def _subject_key(*, tenant_id: str, resource_type: str, resource_id: str) -> str:
        return f'{normalize_tenant_id(tenant_id)}:{resource_type}:{resource_id}'

    def _audit(self, action: str, tenant_id: str, entity_id: str, before: dict[str, Any], after: dict[str, Any], actor: dict[str, Any] | None, trace_id: str) -> None:
        emit_audit_record(
            service_name='automation-service',
            tenant_id=tenant_id,
            actor=actor or {'id': 'automation-studio', 'type': 'service'},
            action=action,
            entity='AutomationRule',
            entity_id=entity_id,
            before=before,
            after=after,
            trace_id=trace_id,
            source={'module': 'automation-studio'},
        )

    def _emit_event(self, legacy_event_name: str, *, tenant_id: str, trace_id: str, data: dict[str, Any]) -> None:
        emit_canonical_event(
            self.events,
            legacy_event_name=legacy_event_name,
            data=data,
            source='automation-service',
            tenant_id=tenant_id,
            registry=self.event_registry,
            correlation_id=trace_id,
            idempotency_key=f'{legacy_event_name}:{data.get("rule_id")}:{data.get("event_id", "na")}',
        )
