from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class AddonModule:
    module_id: str
    tenant_id: str
    owner_service: str
    capabilities: list[str]
    approvals_engine: str = 'workflow'
    automation_triggers: list[str] = field(default_factory=list)
    workflow_triggers: list[str] = field(default_factory=list)
    analytics_source: str = 'read-model'
    reporting_source: str = 'read-model'
    tenant_filter_strategy: str = 'strict'
    audit_hooks_enabled: bool = True
    event_hooks_enabled: bool = True


@dataclass(slots=True)
class ConvergenceIssue:
    check: str
    code: str
    severity: str
    module_id: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConvergenceReport:
    checked_at: str
    iterations: int
    converged: bool
    score: int
    checks: dict[str, int]
    issues: list[ConvergenceIssue]
    applied_fixes: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            'checked_at': self.checked_at,
            'iterations': self.iterations,
            'converged': self.converged,
            'score': self.score,
            'checks': dict(self.checks),
            'issues': [item.to_dict() for item in self.issues],
            'applied_fixes': [dict(item) for item in self.applied_fixes],
        }


class AddonConvergenceError(RuntimeError):
    """Raised when the enforced convergence loop cannot reach 10/10."""


class AddonConvergenceService:
    """QC + auto-fix loop for add-on convergence into the core platform.

    This validator is intentionally deterministic and uses only safe transforms:
    de-duplication, routing approvals to workflow, trigger alignment, read-model
    normalization, tenant filter enforcement, audit/event hook injection, and
    service-boundary restoration.
    """

    CHECKS = (
        'duplication',
        'workflow_alignment',
        'automation_alignment',
        'analytics_reporting_consistency',
        'tenant_isolation',
        'audit_event_coverage',
        'service_boundaries',
    )

    OWNER_MAP = {
        'travel': 'travel-service',
        'expense': 'expense-service',
        'project': 'project-service',
        'helpdesk': 'helpdesk-service',
        'integration': 'integration-service',
        'performance': 'performance-service',
    }

    def __init__(self, modules: list[AddonModule]) -> None:
        self.modules = modules

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def converge(self, *, max_iterations: int = 10) -> ConvergenceReport:
        iterations = 0
        applied: list[dict[str, Any]] = []
        issues: list[ConvergenceIssue] = []
        checks: dict[str, int] = {name: 0 for name in self.CHECKS}

        while iterations < max_iterations:
            iterations += 1
            issues = self._run_qc()
            checks = self._score(issues)
            if self._is_perfect(checks):
                return ConvergenceReport(
                    checked_at=self._now(),
                    iterations=iterations,
                    converged=True,
                    score=10,
                    checks=checks,
                    issues=issues,
                    applied_fixes=applied,
                )

            batch = self._auto_fix(issues)
            if not batch:
                break
            applied.extend(batch)

        issues = self._run_qc()
        checks = self._score(issues)
        if not self._is_perfect(checks):
            raise AddonConvergenceError('P50 convergence loop exited below 10/10; unresolved add-on drift remains.')
        return ConvergenceReport(
            checked_at=self._now(),
            iterations=iterations,
            converged=True,
            score=10,
            checks=checks,
            issues=issues,
            applied_fixes=applied,
        )

    def _run_qc(self) -> list[ConvergenceIssue]:
        issues: list[ConvergenceIssue] = []
        for module in self.modules:
            issues.extend(self._check_duplication(module))
            issues.extend(self._check_workflow_alignment(module))
            issues.extend(self._check_automation_alignment(module))
            issues.extend(self._check_analytics_reporting_consistency(module))
            issues.extend(self._check_tenant_isolation(module))
            issues.extend(self._check_audit_event_coverage(module))
            issues.extend(self._check_service_boundaries(module))
        return issues

    def _check_duplication(self, module: AddonModule) -> list[ConvergenceIssue]:
        seen: set[str] = set()
        duplicates = sorted({cap for cap in module.capabilities if cap in seen or seen.add(cap)})
        if not duplicates:
            return []
        return [ConvergenceIssue('duplication', 'duplicate_capability', 'error', module.module_id, f'duplicate capabilities detected: {duplicates}')]

    def _check_workflow_alignment(self, module: AddonModule) -> list[ConvergenceIssue]:
        if module.approvals_engine == 'workflow':
            return []
        return [ConvergenceIssue('workflow_alignment', 'parallel_approval_path', 'error', module.module_id, 'approval flow bypasses workflow engine')]

    def _check_automation_alignment(self, module: AddonModule) -> list[ConvergenceIssue]:
        if sorted(set(module.automation_triggers)) == sorted(set(module.workflow_triggers)):
            return []
        return [ConvergenceIssue('automation_alignment', 'automation_trigger_drift', 'error', module.module_id, 'automation triggers are not aligned with workflow triggers')]

    def _check_analytics_reporting_consistency(self, module: AddonModule) -> list[ConvergenceIssue]:
        if module.analytics_source == 'read-model' and module.reporting_source == 'read-model':
            return []
        return [ConvergenceIssue('analytics_reporting_consistency', 'projection_source_drift', 'error', module.module_id, 'analytics/reporting do not share read-model source of truth')]

    def _check_tenant_isolation(self, module: AddonModule) -> list[ConvergenceIssue]:
        if module.tenant_filter_strategy == 'strict' and bool(module.tenant_id):
            return []
        return [ConvergenceIssue('tenant_isolation', 'tenant_filter_gap', 'error', module.module_id, 'tenant isolation guard is incomplete')]

    def _check_audit_event_coverage(self, module: AddonModule) -> list[ConvergenceIssue]:
        if module.audit_hooks_enabled and module.event_hooks_enabled:
            return []
        return [ConvergenceIssue('audit_event_coverage', 'missing_audit_or_event_hook', 'error', module.module_id, 'audit/event hook coverage is incomplete')]

    def _check_service_boundaries(self, module: AddonModule) -> list[ConvergenceIssue]:
        expected = self.OWNER_MAP.get(module.module_id.split('-')[0])
        if expected is None or module.owner_service == expected:
            return []
        return [ConvergenceIssue('service_boundaries', 'boundary_drift', 'error', module.module_id, f'module owned by {module.owner_service}; expected {expected}')]

    def _auto_fix(self, issues: list[ConvergenceIssue]) -> list[dict[str, Any]]:
        issue_codes = {(item.module_id, item.code) for item in issues}
        actions: list[dict[str, Any]] = []

        for module in self.modules:
            key = lambda code: (module.module_id, code) in issue_codes

            if key('duplicate_capability'):
                before = list(module.capabilities)
                module.capabilities = list(dict.fromkeys(module.capabilities))
                actions.append({'module_id': module.module_id, 'action': 'merge_duplicate_logic_into_existing_module', 'before': before, 'after': list(module.capabilities)})

            if key('parallel_approval_path'):
                module.approvals_engine = 'workflow'
                actions.append({'module_id': module.module_id, 'action': 'reroute_approvals_to_workflow_engine'})

            if key('automation_trigger_drift'):
                module.automation_triggers = sorted(set(module.workflow_triggers))
                actions.append({'module_id': module.module_id, 'action': 'align_automation_rules_with_workflow_triggers', 'triggers': list(module.automation_triggers)})

            if key('projection_source_drift'):
                module.analytics_source = 'read-model'
                module.reporting_source = 'read-model'
                actions.append({'module_id': module.module_id, 'action': 'normalize_analytics_to_read_model_standards'})

            if key('tenant_filter_gap'):
                module.tenant_filter_strategy = 'strict'
                if not module.tenant_id:
                    module.tenant_id = 'tenant-default'
                actions.append({'module_id': module.module_id, 'action': 'enforce_tenant_filters_everywhere'})

            if key('missing_audit_or_event_hook'):
                module.audit_hooks_enabled = True
                module.event_hooks_enabled = True
                actions.append({'module_id': module.module_id, 'action': 'inject_missing_audit_event_hooks'})

            if key('boundary_drift'):
                expected = self.OWNER_MAP.get(module.module_id.split('-')[0])
                if expected:
                    module.owner_service = expected
                    actions.append({'module_id': module.module_id, 'action': 'restore_clean_service_boundary', 'owner_service': expected})

        return actions

    def _score(self, issues: list[ConvergenceIssue]) -> dict[str, int]:
        penalties = {name: 0 for name in self.CHECKS}
        for item in issues:
            penalties[item.check] += 10
        return {name: max(0, 10 - penalties[name]) for name in self.CHECKS}

    @staticmethod
    def _is_perfect(checks: dict[str, int]) -> bool:
        return all(score == 10 for score in checks.values())
