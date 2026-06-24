from __future__ import annotations

import pytest

from master_certification import CertificationSnapshot, MasterCertificationError, MasterCertificationService


def test_master_qc_loop_converges_to_enterprise_10_of_10() -> None:
    snapshots = [
        CertificationSnapshot(
            module_id='travel-addon',
            tenant_id='',
            owner_service='employee-service',
            architecture_signature='legacy-v1',
            duplicate_logic_count=3,
            extends_parity_module=False,
            has_parallel_system=True,
            automation_aligned_with_workflow=False,
            analytics_source='service-db',
            reporting_source='warehouse-export',
            avg_latency_ms=740,
            async_flow_intact=False,
            has_blocking_chain=True,
            permissions_enforced=False,
            audit_coverage_complete=False,
            retry_recovery_intact=False,
            no_cascading_failure_risk=False,
            supervisor_compatible=False,
        )
    ]

    service = MasterCertificationService(snapshots)
    report = service.certify(max_iterations=10)

    assert report.converged is True
    assert report.score == 10
    assert all(score == 10 for score in report.categories.values())
    assert report.issues == []
    assert report.applied_fixes

    item = snapshots[0]
    assert item.owner_service == 'travel-service'
    assert item.architecture_signature.startswith('D1-D8:')
    assert item.duplicate_logic_count == 0
    assert item.extends_parity_module is True
    assert item.has_parallel_system is False
    assert item.automation_aligned_with_workflow is True
    assert item.analytics_source == 'read-model'
    assert item.reporting_source == 'read-model'
    assert item.avg_latency_ms <= 400
    assert item.async_flow_intact is True
    assert item.has_blocking_chain is False
    assert item.permissions_enforced is True
    assert item.audit_coverage_complete is True
    assert item.retry_recovery_intact is True
    assert item.no_cascading_failure_risk is True
    assert item.supervisor_compatible is True


def test_master_qc_raises_when_no_fix_path_exists() -> None:
    service = MasterCertificationService(
        [
            CertificationSnapshot(
                module_id='expense-addon',
                tenant_id='',
                owner_service='employee-service',
                architecture_signature='legacy-v1',
            )
        ]
    )
    service._auto_fix = lambda _issues: []  # type: ignore[method-assign]

    with pytest.raises(MasterCertificationError):
        service.certify(max_iterations=2)
