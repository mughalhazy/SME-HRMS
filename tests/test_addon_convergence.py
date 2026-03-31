from __future__ import annotations

import pytest

from addon_convergence import AddonConvergenceError, AddonConvergenceService, AddonModule


def test_enforced_loop_converges_addons_to_10_of_10() -> None:
    modules = [
        AddonModule(
            module_id='travel-addon',
            tenant_id='tenant-acme',
            owner_service='employee-service',
            capabilities=['request', 'request', 'itinerary'],
            approvals_engine='inline-manager',
            workflow_triggers=['travel.request.submitted', 'travel.request.escalated'],
            automation_triggers=['travel.request.submitted'],
            analytics_source='service-db',
            reporting_source='warehouse-export',
            tenant_filter_strategy='loose',
            audit_hooks_enabled=False,
            event_hooks_enabled=False,
        ),
        AddonModule(
            module_id='expense-addon',
            tenant_id='',
            owner_service='leave-service',
            capabilities=['expense-claim', 'expense-claim'],
            approvals_engine='local-state-machine',
            workflow_triggers=['expense.claim.submitted'],
            automation_triggers=['expense.claim.created'],
            analytics_source='derived-cache',
            reporting_source='service-db',
            tenant_filter_strategy='none',
            audit_hooks_enabled=True,
            event_hooks_enabled=False,
        ),
    ]

    service = AddonConvergenceService(modules)
    report = service.converge(max_iterations=10)

    assert report.converged is True
    assert report.score == 10
    assert all(score == 10 for score in report.checks.values())
    assert report.issues == []
    assert report.applied_fixes

    for module in modules:
        assert module.approvals_engine == 'workflow'
        assert module.automation_triggers == sorted(set(module.workflow_triggers))
        assert module.analytics_source == 'read-model'
        assert module.reporting_source == 'read-model'
        assert module.tenant_filter_strategy == 'strict'
        assert module.audit_hooks_enabled is True
        assert module.event_hooks_enabled is True
        assert len(module.capabilities) == len(set(module.capabilities))


def test_convergence_raises_when_no_auto_fix_path_exists() -> None:
    module = AddonModule(
        module_id='project-addon',
        tenant_id='tenant-acme',
        owner_service='wrong-service',
        capabilities=['allocation'],
        approvals_engine='workflow',
        workflow_triggers=['project.assignment.submitted'],
        automation_triggers=['project.assignment.submitted'],
        analytics_source='read-model',
        reporting_source='read-model',
        tenant_filter_strategy='strict',
        audit_hooks_enabled=True,
        event_hooks_enabled=True,
    )
    service = AddonConvergenceService([module])

    # Force a non-repairable failure by disabling auto-fix output.
    service._auto_fix = lambda _issues: []  # type: ignore[method-assign]

    with pytest.raises(AddonConvergenceError):
        service.converge(max_iterations=2)


def test_convergence_restores_boundaries_for_integrated_event_workflow_domains() -> None:
    modules = [
        AddonModule(module_id='helpdesk-addon', tenant_id='tenant-default', owner_service='legacy-core', capabilities=['ticket'], workflow_triggers=['helpdesk.ticket.submitted'], automation_triggers=['helpdesk.ticket.submitted']),
        AddonModule(module_id='engagement-addon', tenant_id='tenant-default', owner_service='legacy-core', capabilities=['survey'], workflow_triggers=['engagement.survey.published'], automation_triggers=['engagement.survey.published']),
        AddonModule(module_id='learning-addon', tenant_id='tenant-default', owner_service='legacy-core', capabilities=['enrollment'], workflow_triggers=['learning.enrollment.created'], automation_triggers=['learning.enrollment.created']),
        AddonModule(module_id='workforce-intelligence-addon', tenant_id='tenant-default', owner_service='legacy-core', capabilities=['reporting'], workflow_triggers=['workforce_intelligence.report_run.generated'], automation_triggers=['workforce_intelligence.report_run.generated']),
        AddonModule(module_id='cost-planning-addon', tenant_id='tenant-default', owner_service='legacy-core', capabilities=['budget'], workflow_triggers=['cost_planning.plan.submitted'], automation_triggers=['cost_planning.plan.submitted']),
    ]

    report = AddonConvergenceService(modules).converge(max_iterations=5)

    assert report.score == 10
    assert {module.module_id: module.owner_service for module in modules} == {
        'helpdesk-addon': 'helpdesk-service',
        'engagement-addon': 'engagement-service',
        'learning-addon': 'employee-service',
        'workforce-intelligence-addon': 'reporting-analytics',
        'cost-planning-addon': 'cost-planning-service',
    }
