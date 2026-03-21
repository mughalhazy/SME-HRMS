from __future__ import annotations

from datetime import datetime, timezone

import pytest

from workflow_contract import WorkflowContractError, ensure_workflow_contract


FIXED_NOW = datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc)


def test_workflow_contract_auto_fixes_identifiers_engine_and_sla_formats() -> None:
    workflow = ensure_workflow_contract(
        {
            'workflow_id': 'not-a-uuid',
            'steps': [
                {
                    'step_id': 'bad-step-id',
                    'type': 'approval',
                    'assignee': 'hr-ops',
                    'status': 'approved',
                    'sla': '24h',
                },
                {
                    'type': 'auto',
                    'assignee': 'payroll-service',
                    'status': 'pending',
                    'sla': '15m',
                },
            ],
            'status': 'completed',
        },
        now=FIXED_NOW,
    )

    assert workflow['status'] == 'pending'
    assert workflow['created_at'] == FIXED_NOW.isoformat()
    assert workflow['metadata']['engine'] == 'workflow-contract-engine'
    assert workflow['steps'][0]['sla'] == 'PT24H'
    assert workflow['steps'][1]['sla'] == 'PT15M'
    assert workflow['steps'][0]['metadata']['deadline_at'] == '2026-03-22T12:00:00+00:00'
    assert workflow['steps'][1]['metadata']['deadline_at'] == '2026-03-21T12:15:00+00:00'

    auto_fixed = workflow['metadata']['qc']['auto_fixed']
    assert 'generate_workflow_ids' in auto_fixed
    assert 'generate_step_ids' in auto_fixed
    assert 'normalize_sla_durations' in auto_fixed
    assert 'normalize_state_transitions' in auto_fixed

    scores = workflow['metadata']['qc']['score']
    assert scores['workflow_consistency'] == 10
    assert scores['approval_standardization'] == 10
    assert scores['state_management'] == 10
    assert scores['sla_enforcement'] == 10
    assert scores['integration_usage'] == 10
    assert scores['overall'] == 10


def test_workflow_contract_reroutes_inline_approval_logic_to_approval_steps() -> None:
    workflow = ensure_workflow_contract(
        {
            'workflow_id': '5d892b38-2381-4f17-84eb-4d17f5b4d444',
            'created_at': '2026-03-21T10:00:00+00:00',
            'steps': [
                {
                    'step_id': '0eae0fe5-5f05-4b87-8fa5-28b78a6ce129',
                    'type': 'auto',
                    'assignee': 'manager',
                    'status': 'approved',
                    'sla': 'PT1H',
                    'approved_by': 'manager',
                }
            ],
            'status': 'completed',
        },
        now=FIXED_NOW,
    )

    assert workflow['steps'][0]['type'] == 'approval'
    assert 'remove_inline_approvals' in workflow['metadata']['qc']['auto_fixed']
    assert 'reroute_to_workflow_engine' in workflow['metadata']['qc']['auto_fixed']
    assert all(item['passed'] for item in workflow['metadata']['qc']['rechecked'])


def test_workflow_contract_rejects_invalid_state_transitions() -> None:
    with pytest.raises(WorkflowContractError, match='invalid_state_transition'):
        ensure_workflow_contract(
            {
                'workflow_id': 'cb0d88ef-1bfd-42ce-bac9-b92d700e4a4f',
                'created_at': '2026-03-21T10:00:00+00:00',
                'steps': [
                    {
                        'step_id': '2f6902df-8016-449f-b92a-d6ed1a8020dc',
                        'type': 'approval',
                        'assignee': 'hr',
                        'status': 'pending',
                        'sla': 'PT1H',
                    },
                    {
                        'step_id': '4659b518-cf28-4ef4-aacd-4b0f340e0de5',
                        'type': 'auto',
                        'assignee': 'system',
                        'status': 'approved',
                        'sla': 'PT30M',
                    },
                ],
                'status': 'pending',
            },
            now=FIXED_NOW,
        )


def test_workflow_contract_rejects_bypass_without_steps() -> None:
    with pytest.raises(WorkflowContractError, match='workflow_bypass_detected'):
        ensure_workflow_contract(
            {
                'workflow_id': 'ff4d22b6-7fd7-4f89-afbe-e7d2989d2db8',
                'created_at': '2026-03-21T10:00:00+00:00',
                'steps': [],
                'status': 'completed',
            },
            now=FIXED_NOW,
        )
