from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HIRING_SERVICE = (ROOT / "services/hiring_service/service.py").read_text()
WORKFLOW_SCHEMA = (ROOT / "deployment/migrations/002_workflow_schema.sql").read_text()
HIRING_TESTS = (ROOT / "tests/test_hiring_service.py").read_text()
HIRING_DOC = (ROOT / "docs/services/hiring-service.md").read_text()

checks: list[tuple[str, bool]] = [
    (
        "candidate entity includes external source metadata",
        all(token in HIRING_SERVICE for token in ["source_candidate_id", "source_profile_url"]),
    ),
    (
        "candidate stage history model is implemented",
        "class CandidateStageTransition" in HIRING_SERVICE and "list_candidate_stage_history" in HIRING_SERVICE,
    ),
    (
        "candidate stage changes are persisted from create/update/hire flows",
        HIRING_SERVICE.count("_record_candidate_stage_transition(") >= 4,
    ),
    (
        "candidate stage tracking is represented in workflow schema",
        "CREATE TABLE IF NOT EXISTS candidate_stage_transitions" in WORKFLOW_SCHEMA
        and "reason TEXT" in WORKFLOW_SCHEMA
        and "notes TEXT" in WORKFLOW_SCHEMA,
    ),
    (
        "schema supports canonical candidate source coverage",
        "LinkedIn" in WORKFLOW_SCHEMA and "source_candidate_id VARCHAR(120)" in WORKFLOW_SCHEMA,
    ),
    (
        "hiring service tests cover stage history and pipeline fields",
        "test_candidate_stage_history_tracks_initial_and_subsequent_stage_changes" in HIRING_TESTS
        and "last_interview_recommendation" in HIRING_TESTS,
    ),
    (
        "service documentation references candidate lifecycle and stage events",
        "CandidateStageChanged" in HIRING_DOC and "CandidateHired" in HIRING_DOC,
    ),
]

score = sum(1 for _, ok in checks if ok)
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f"RE-QC candidate-domain-integrity score: {score}/{len(checks)}")
if score < len(checks):
    raise SystemExit(1)
