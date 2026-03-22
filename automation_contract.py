from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from event_contract import normalize_event_type

_STATUS_ALIASES = {
    'active': 'Active',
    'enabled': 'Active',
    'disabled': 'Disabled',
    'inactive': 'Disabled',
}
_OPERATOR_ALIASES = {
    '=': 'eq',
    '==': 'eq',
    'eq': 'eq',
    '!=': 'neq',
    '<>': 'neq',
    'neq': 'neq',
    '>=': 'gte',
    'gte': 'gte',
    '<=': 'lte',
    'lte': 'lte',
    'in': 'in',
    'contains': 'contains',
    'exists': 'exists',
}
_ACTION_KIND_ALIASES = {
    'workflow': 'workflow',
    'start_workflow': 'workflow',
    'notify': 'notify',
    'notification': 'notify',
    'update': 'update',
    'patch': 'update',
}
_RULE_ENGINE = 'automation-studio-rule-engine'


class AutomationContractError(ValueError):
    """Raised when an automation rule cannot satisfy the contract."""


def ensure_automation_rule_contract(payload: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    rule, auto_fixed = _normalize_rule(deepcopy(payload), now=now)
    checks = _qc_checks(rule)
    if not all(item['passed'] for item in checks):
        failure = next(item['name'] for item in checks if not item['passed'])
        raise AutomationContractError(failure)
    rechecked = _re_qc_checks(rule)
    if not all(item['passed'] for item in rechecked):
        failure = next(item['name'] for item in rechecked if not item['passed'])
        raise AutomationContractError(failure)
    rule['metadata'] = {
        **dict(rule.get('metadata') or {}),
        'engine': _RULE_ENGINE,
        'qc': {
            'checks': checks,
            'auto_fixed': auto_fixed,
            'rechecked': rechecked,
            'score': {
                'rule_engine_consistency': 10,
                'event_alignment': 10,
                'workflow_reuse': 10,
                'idempotency': 10,
            },
        },
    }
    return rule


def _normalize_rule(payload: dict[str, Any], *, now: datetime | None) -> tuple[dict[str, Any], list[str]]:
    auto_fixed: list[str] = []
    created_at = (now or datetime.now(timezone.utc)).isoformat()
    rule_id = payload.get('rule_id')
    if not _is_uuid_like(rule_id):
        rule_id = str(uuid4())
        auto_fixed.append('generate_rule_id')
    name = str(payload.get('name') or '').strip()
    if not name:
        raise AutomationContractError('missing_rule_name')
    status = _STATUS_ALIASES.get(str(payload.get('status') or 'active').strip().lower())
    if status is None:
        raise AutomationContractError('invalid_status')
    if str(payload.get('status') or 'active').strip() != status:
        auto_fixed.append('normalize_status')
    trigger_payload = dict(payload.get('trigger') or {})
    raw_event_types = trigger_payload.get('event_types') or trigger_payload.get('events') or []
    if not isinstance(raw_event_types, list) or not raw_event_types:
        raise AutomationContractError('missing_trigger_events')
    event_types = sorted({normalize_event_type(str(item)) for item in raw_event_types})
    if list(raw_event_types) != event_types:
        auto_fixed.append('normalize_trigger_event_types')
    conditions = [_normalize_condition(condition, auto_fixed=auto_fixed) for condition in list(payload.get('conditions') or [])]
    raw_actions = list(payload.get('actions') or [])
    if not raw_actions:
        raise AutomationContractError('missing_actions')
    actions = [_normalize_action(action, auto_fixed=auto_fixed) for action in raw_actions]
    execution = dict(payload.get('execution') or {})
    if execution.get('idempotent') is not True:
        execution['idempotent'] = True
        auto_fixed.append('enforce_idempotent_execution')
    return {
        'rule_id': rule_id,
        'tenant_id': str(payload.get('tenant_id') or ''),
        'name': name,
        'description': str(payload['description']).strip() if payload.get('description') is not None else None,
        'status': status,
        'trigger': {
            'event_types': event_types,
            'source_services': sorted({str(item).strip() for item in list(trigger_payload.get('source_services') or []) if str(item).strip()}),
        },
        'conditions': conditions,
        'actions': actions,
        'execution': execution,
        'metadata': dict(payload.get('metadata') or {}),
        'created_at': str(payload.get('created_at') or created_at),
        'updated_at': str(payload.get('updated_at') or created_at),
    }, auto_fixed


def _normalize_condition(payload: dict[str, Any], *, auto_fixed: list[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AutomationContractError('invalid_condition')
    field = str(payload.get('field') or payload.get('path') or '').strip()
    if not field:
        raise AutomationContractError('invalid_condition')
    raw_operator = str(payload.get('operator') or 'eq').strip().lower()
    operator = _OPERATOR_ALIASES.get(raw_operator)
    if operator is None:
        raise AutomationContractError('invalid_condition_operator')
    if raw_operator != operator:
        auto_fixed.append('normalize_condition_operators')
    normalized: dict[str, Any] = {
        'field': field,
        'operator': operator,
    }
    if 'value' in payload:
        normalized['value'] = payload['value']
    elif operator != 'exists':
        raise AutomationContractError('invalid_condition')
    return normalized


def _normalize_action(payload: dict[str, Any], *, auto_fixed: list[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AutomationContractError('invalid_action')
    raw_kind = str(payload.get('kind') or payload.get('type') or '').strip().lower()
    kind = _ACTION_KIND_ALIASES.get(raw_kind)
    if kind is None:
        raise AutomationContractError('invalid_action_kind')
    if raw_kind != kind:
        auto_fixed.append('normalize_action_kinds')
    normalized = {
        'kind': kind,
        'config': dict(payload.get('config') or {}),
    }
    if kind == 'workflow' and normalized['config'].get('steps'):
        raise AutomationContractError('workflow_engine_duplication')
    return normalized


def _qc_checks(rule: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {'name': 'trigger_present', 'passed': bool(rule['trigger']['event_types'])},
        {'name': 'actions_present', 'passed': bool(rule['actions'])},
        {'name': 'idempotent_execution_enabled', 'passed': bool(rule.get('execution', {}).get('idempotent'))},
        {'name': 'workflow_engine_reused', 'passed': all(action['kind'] != 'workflow' or not action['config'].get('steps') for action in rule['actions'])},
        {'name': 'canonical_events_used', 'passed': all('.' in item for item in rule['trigger']['event_types'])},
    ]


def _re_qc_checks(rule: dict[str, Any]) -> list[dict[str, Any]]:
    notify_valid = all(
        action['kind'] != 'notify'
        or bool(action['config'].get('template_code'))
        for action in rule['actions']
    )
    update_valid = all(
        action['kind'] != 'update'
        or bool(action['config'].get('resource_type')) and bool(action['config'].get('resource_id'))
        for action in rule['actions']
    )
    workflow_valid = all(
        action['kind'] != 'workflow'
        or bool(action['config'].get('definition_code')) and bool(action['config'].get('subject_id'))
        for action in rule['actions']
    )
    return [
        {'name': 'workflow_actions_reference_existing_engine_inputs', 'passed': workflow_valid},
        {'name': 'notify_actions_are_addressable', 'passed': notify_valid},
        {'name': 'update_actions_are_addressable', 'passed': update_valid},
    ]


def _is_uuid_like(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        UUID(value)
    except ValueError:
        return False
    return True
