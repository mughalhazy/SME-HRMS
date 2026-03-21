from __future__ import annotations

from chaos_engine import ChaosEngineeringEngine


def test_chaos_engine_runs_all_required_failure_modes_with_full_recovery() -> None:
    report = ChaosEngineeringEngine().run_all()

    assert report.quality_standard == "10/10"
    assert report.scenario_count == 5
    assert report.success_count == 5
    assert report.recovery_success_rate == 1.0
    scenario_ids = {scenario.scenario_id for scenario in report.scenarios}
    assert scenario_ids == {
        "service-downtime",
        "db-latency-and-job-failure",
        "event-processing-failure",
        "api-timeout-and-fallback",
        "partial-outage-no-cascade",
    }
    failure_modes = {mode for scenario in report.scenarios for mode in scenario.failure_modes}
    assert {
        "service_downtime",
        "db_latency_failure",
        "job_queue_failure",
        "event_processing_failure",
        "api_timeout",
        "partial_system_outage",
    }.issubset(failure_modes)
    assert all(scenario.detected for scenario in report.scenarios)
    assert all(scenario.recovered for scenario in report.scenarios)
    assert all(scenario.observability_verified for scenario in report.scenarios)
    assert all(scenario.auto_healing_verified for scenario in report.scenarios)
    assert all(scenario.no_cascade_failures for scenario in report.scenarios)
    assert report.summary["failure_coverage"] == 10
    assert report.summary["recovery_success"] == 10
    assert report.summary["no_cascade_failures"] == 10
    assert report.summary["observability_accuracy"] == 10
    assert report.summary["auto_healing"] == 10


def test_chaos_engine_uses_supervisor_paths_for_retry_reprocess_and_escalation() -> None:
    report = ChaosEngineeringEngine().run_all()
    scenarios = {scenario.scenario_id: scenario for scenario in report.scenarios}

    assert "retry" in scenarios["db-latency-and-job-failure"].recovery_actions
    assert "reprocess" in scenarios["event-processing-failure"].recovery_actions
    assert "escalate" in scenarios["partial-outage-no-cascade"].recovery_actions
    assert "fallback" in scenarios["partial-outage-no-cascade"].recovery_actions
    assert scenarios["api-timeout-and-fallback"].workflow_continued is True
    assert scenarios["api-timeout-and-fallback"].details["manual_fallback"] == "manual-scheduling-required"


def test_chaos_engine_report_covers_critical_services_and_identifies_guardrails() -> None:
    report = ChaosEngineeringEngine().run_all()

    assert set(report.summary["critical_services_tested"]) == {
        "employee-service",
        "auth-service",
        "settings-service",
        "attendance-service",
        "leave-service",
        "payroll-service",
        "performance-service",
        "hiring-service",
        "notification-service",
        "background-jobs",
        "workflow-service",
        "integration-service",
        "search-service",
    }
    assert report.weak_points
    assert any("Circuit breakers intentionally skip repeated fallback attempts" in weak_point for weak_point in report.weak_points)
    assert any("Background-job executor treats sub-500 job errors" in weak_point for weak_point in report.weak_points)
