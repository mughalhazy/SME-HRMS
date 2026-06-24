# Chaos Testing + Auto-Healing Report

> NOTE (2026-06-13): `hrms-doc-catalogue-v1.md` Category 13 entry for this file lists scenario names ("service downtime, cascading failures, event delivery failures, job queue saturation, workflow timeout") that do not match the 5 scenarios actually defined below (service downtime, DB latency/job failure, event processing failure, API timeout+fallback, partial outage/no cascading failures). This file's content is canonical; the catalogue description needs reconciling in a future catalogue-fix pass.

## Scope

This report documents the anchor-doc-driven chaos validation harness implemented in `chaos_engine.py` and verified by `tests/test_chaos_engine.py`.

The harness is extend-only and non-invasive:
- it does not change domain/business logic,
- it injects reversible failures into supervisor-observed paths,
- it uses the existing observability, retry, jobs, event-outbox, workflow, and supervisor subsystems,
- it validates graceful degradation rather than creating real system instability.

## Scenarios Covered

1. **Service downtime**
   - Simulates `employee-service` dependency outage.
   - Verifies supervisor detection, dependency-aware degradation, and dead-letter replay recovery.

2. **DB latency / job failure**
   - Simulates a read-model refresh job failing due to a database timeout condition.
   - Verifies failed-job detection, supervisor retry, and successful completion.

3. **Event processing failure**
   - Simulates outbox dispatch transport failure.
   - Verifies observability capture, supervisor reprocessing, and cleared backlog.

4. **API timeout + fallback**
   - Simulates hiring calendar sync timeout.
   - Verifies fallback to manual scheduling, workflow continuation, and supervisor dead-letter replay.

5. **Partial outage / no cascading failures**
   - Simulates upstream dependency outage with downstream fallback pressure.
   - Verifies circuit-breaker protection, escalation, and prevention of cascading recovery failures.

## Validation Targets

- Retry mechanisms through background jobs and supervisor retries.
- Event reprocessing through the outbox dispatcher.
- Fallback paths for API timeout scenarios.
- Supervisor recovery and escalation handling.
- Observability coverage across logs, traces, and metrics.
- No-cascade guardrails through circuit-breaker-protected fallback behavior.

## Report Output

The executable report is returned by `ChaosEngineeringEngine().run_all()` and includes:
- tested scenarios,
- recovery success rate,
- recovery action types,
- observability validation results,
- weak points / operational guardrails,
- critical services covered.

## Weak Points / Guardrails Identified

- Background-job recovery depends on supervisor retries for isolated transient failures that are deliberately prevented from auto-retrying inside the same execution attempt.
- Partial-outage recovery intentionally suppresses repeated fallback attempts via circuit breakers to avoid turning recovery logic into the cascade trigger.
- Timeout fallbacks preserve workflow continuity first, then rely on supervisor replay for post-failure healing evidence.
