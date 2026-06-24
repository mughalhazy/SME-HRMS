from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from core.country_resolver import CountryResolver
from event_contract import EventRegistry, emit_canonical_event


# ---------------------------------------------------------------------------
# Enums & Value Objects
# ---------------------------------------------------------------------------

class SubmissionState(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SUBMITTED = "SUBMITTED"
    ACK = "ACK"
    FAILED = "FAILED"
    RETRY = "RETRY"
    MANUAL = "MANUAL"   # SPEC-G07: manual fallback submission recorded


class ComplianceErrorType(str, Enum):
    """SPEC §13 error type classification — enables operator triage.

    data_error               — bad/missing employee data, fixable by HR
    rules_error              — statutory rule violated, fixable by updating config/data
    external_dependency_error — government portal/API unavailable, fixable by IT or retry
    operator_error           — process error (wrong period, duplicate), fixable by operator action
    """
    DATA_ERROR = "data_error"
    RULES_ERROR = "rules_error"
    EXTERNAL_DEPENDENCY_ERROR = "external_dependency_error"
    OPERATOR_ERROR = "operator_error"


# Rule-id prefix → error type mapping for classify_compliance_error()
_RULE_ERROR_TYPE_MAP: dict[str, ComplianceErrorType] = {
    # Data errors — missing or invalid employee fields
    "CNIC": ComplianceErrorType.DATA_ERROR,
    "BANK": ComplianceErrorType.DATA_ERROR,
    "EOBI_NUMBER": ComplianceErrorType.DATA_ERROR,
    "PESSI_NUMBER": ComplianceErrorType.DATA_ERROR,
    "SESSI_NUMBER": ComplianceErrorType.DATA_ERROR,
    "EMPLOYEE_DATA": ComplianceErrorType.DATA_ERROR,
    # Rules errors — statutory constraint failures
    "TAX": ComplianceErrorType.RULES_ERROR,
    "STATUTORY": ComplianceErrorType.RULES_ERROR,
    "MIN_WAGE": ComplianceErrorType.RULES_ERROR,
    "OVERTIME": ComplianceErrorType.RULES_ERROR,
    "WPPF": ComplianceErrorType.RULES_ERROR,
    "WWF": ComplianceErrorType.RULES_ERROR,
    # Operator errors — process / workflow mistakes
    "PERIOD": ComplianceErrorType.OPERATOR_ERROR,
    "DUPLICATE": ComplianceErrorType.OPERATOR_ERROR,
    "SUBMISSION_STATE": ComplianceErrorType.OPERATOR_ERROR,
}


def classify_compliance_error(rule_id: str, message: str = "") -> ComplianceErrorType:
    """Classify a compliance violation into one of the 4 SPEC §13 error types.

    Checks rule_id prefix first, then falls back to message keyword scan.
    Returns RULES_ERROR as the default when no match is found.
    """
    upper = rule_id.upper()
    for prefix, error_type in _RULE_ERROR_TYPE_MAP.items():
        if upper.startswith(prefix):
            return error_type
    # Keyword scan on message as secondary signal
    msg_lower = message.lower()
    if any(k in msg_lower for k in ("portal", "api", "timeout", "unavailable", "connection")):
        return ComplianceErrorType.EXTERNAL_DEPENDENCY_ERROR
    if any(k in msg_lower for k in ("missing", "invalid", "required", "cnic", "bank account")):
        return ComplianceErrorType.DATA_ERROR
    if any(k in msg_lower for k in ("duplicate", "already submitted", "wrong period")):
        return ComplianceErrorType.OPERATOR_ERROR
    return ComplianceErrorType.RULES_ERROR


class SubmissionType(str, Enum):
    FBR_ANNEXURE_C = "FBR_ANNEXURE_C"
    EOBI_PR01 = "EOBI_PR01"
    PESSI = "PESSI"
    SESSI = "SESSI"


@dataclass
class ComplianceSubmission:
    submission_id: str
    organization_id: str
    legal_entity_id: str
    period: str                    # "YYYY-MM"
    submission_type: SubmissionType
    state: SubmissionState = SubmissionState.DRAFT
    is_valid: bool = False
    violations: list[dict] = field(default_factory=list)
    report_artifact: dict | None = None
    # SPEC-G07: manual fallback tracking
    manual_mode: bool = False
    manual_reference: str | None = None
    created_at: str = field(default_factory=lambda: _now())
    updated_at: str = field(default_factory=lambda: _now())


@dataclass
class ComplianceAuditRecord:
    audit_id: str
    submission_id: str
    from_state: str
    to_state: str
    actor: str
    detail: dict
    recorded_at: str = field(default_factory=lambda: _now())


# ---------------------------------------------------------------------------
# In-process store (replace with DB repository in production)
# ---------------------------------------------------------------------------

_submissions: dict[str, ComplianceSubmission] = {}
_audit_log: list[ComplianceAuditRecord] = []
_outbox: list[dict] = []
_registry = EventRegistry()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_audit(submission_id: str, from_state: str, to_state: str,
                  actor: str = "system", detail: dict | None = None) -> None:
    _audit_log.append(ComplianceAuditRecord(
        audit_id=str(uuid.uuid4()),
        submission_id=submission_id,
        from_state=from_state,
        to_state=to_state,
        actor=actor,
        detail=detail or {},
    ))


def _transition(sub: ComplianceSubmission, new_state: SubmissionState,
                actor: str = "system", detail: dict | None = None) -> None:
    old = sub.state
    sub.state = new_state
    sub.updated_at = _now()
    _record_audit(sub.submission_id, old, new_state, actor=actor, detail=detail)


# ---------------------------------------------------------------------------
# ComplianceService — country-agnostic orchestrator
# All country-specific logic is delegated to the adapter via CountryResolver.
# ---------------------------------------------------------------------------

class ComplianceService:
    """
    Orchestrates the compliance submission lifecycle.

    Lifecycle: DRAFT → VALIDATED → SUBMITTED → ACK
                                 → FAILED → RETRY → SUBMITTED

    Does NOT contain any country-specific logic. All statutory rules are
    executed by the country adapter returned by CountryResolver.resolve().
    """

    def __init__(self, resolver: CountryResolver | None = None) -> None:
        self._resolver = resolver or CountryResolver()
        self._outbox: list[dict] = _outbox
        self._registry: EventRegistry = _registry

    # ------------------------------------------------------------------
    # Submission management
    # ------------------------------------------------------------------

    def create_submission(
        self,
        organization_id: str,
        legal_entity_id: str,
        period: str,
        submission_type: str,
        actor: str = "system",
    ) -> ComplianceSubmission:
        sub = ComplianceSubmission(
            submission_id=str(uuid.uuid4()),
            organization_id=organization_id,
            legal_entity_id=legal_entity_id,
            period=period,
            submission_type=SubmissionType(submission_type),
        )
        _submissions[sub.submission_id] = sub
        _record_audit(sub.submission_id, "NONE", SubmissionState.DRAFT, actor=actor,
                      detail={"type": submission_type, "period": period})
        emit_canonical_event(
            self._outbox,
            legacy_event_name="ComplianceSubmissionCreated",
            data={"submission_id": sub.submission_id, "organization_id": organization_id,
                  "period": period, "submission_type": submission_type},
            source="compliance-service",
            tenant_id=organization_id,
            registry=self._registry,
        )
        return sub

    def get_submission(self, submission_id: str) -> ComplianceSubmission | None:
        return _submissions.get(submission_id)

    def list_submissions(
        self,
        period: str | None = None,
        submission_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> list[ComplianceSubmission]:
        results = list(_submissions.values())
        if period:
            results = [s for s in results if s.period == period]
        if submission_type:
            results = [s for s in results if s.submission_type == submission_type]
        if status:
            results = [s for s in results if s.state == status]
        # Simple cursor: submission_id alphabetical offset
        if cursor:
            ids = sorted(_submissions.keys())
            start = ids.index(cursor) + 1 if cursor in ids else 0
            results = [s for s in results if s.submission_id in ids[start:]]
        return results[:limit]

    # ------------------------------------------------------------------
    # Lifecycle transitions — delegate computation to country adapter
    # ------------------------------------------------------------------

    def validate_submission(
        self,
        submission_id: str,
        payroll_input: dict[str, Any],
        actor: str = "system",
    ) -> dict[str, Any]:
        """
        Run pre-payroll compliance validation via country adapter.
        Blocks payroll finalization if violations are found.
        """
        sub = self._require(submission_id, SubmissionState.DRAFT)
        adapter = self._resolver.resolve(sub.organization_id)
        result: dict[str, Any] = adapter.validate_payroll({
            "period": sub.period,
            "legal_entity_id": sub.legal_entity_id,
            **payroll_input,
        })
        sub.is_valid = result.get("is_valid", False)
        raw_violations = result.get("violations", [])
        # SPEC-G03: enrich each violation with classified error_type
        enriched_violations = []
        for v in raw_violations:
            rule_id = str(v.get("rule_id", ""))
            message = str(v.get("message", ""))
            enriched = dict(v)
            enriched["error_type"] = classify_compliance_error(rule_id, message).value
            enriched_violations.append(enriched)
        sub.violations = enriched_violations
        result = dict(result)
        result["violations"] = enriched_violations
        new_state = SubmissionState.VALIDATED if sub.is_valid else SubmissionState.DRAFT
        _transition(sub, new_state, actor=actor, detail={"violations": len(sub.violations)})
        event_name = "ComplianceValidationPassed" if sub.is_valid else "ComplianceValidationFailed"
        emit_canonical_event(
            self._outbox,
            legacy_event_name=event_name,
            data={"submission_id": submission_id, "organization_id": sub.organization_id,
                  "is_valid": sub.is_valid, "violation_count": len(sub.violations)},
            source="compliance-service",
            tenant_id=sub.organization_id,
            registry=self._registry,
        )
        return result

    def generate_report(
        self,
        submission_id: str,
        payroll_results: dict[str, Any],
        actor: str = "system",
    ) -> dict[str, Any]:
        """
        Generate statutory report artifacts (FBR Annexure-C, EOBI PR-01, etc.)
        via country adapter. Only permitted after VALIDATED state.
        """
        sub = self._require(submission_id, SubmissionState.VALIDATED)
        adapter = self._resolver.resolve(sub.organization_id)
        artifact: dict[str, Any] = adapter.generate_reports({
            "period": sub.period,
            "submission_type": sub.submission_type,
            "legal_entity_id": sub.legal_entity_id,
            **payroll_results,
        })
        sub.report_artifact = artifact
        _transition(sub, SubmissionState.VALIDATED, actor=actor,
                    detail={"artifact_keys": list(artifact.keys())})
        emit_canonical_event(
            self._outbox,
            legacy_event_name="ComplianceReportGenerated",
            data={"submission_id": submission_id, "organization_id": sub.organization_id,
                  "submission_type": sub.submission_type, "period": sub.period},
            source="compliance-service",
            tenant_id=sub.organization_id,
            registry=self._registry,
        )
        return artifact

    def submit(
        self,
        submission_id: str,
        actor: str = "system",
    ) -> dict[str, Any]:
        """
        Dispatch submission to government authority via country adapter.
        Transitions to SUBMITTED; downstream ACK/FAILED are set by webhook/callback.
        """
        sub = self._require(submission_id, SubmissionState.VALIDATED)
        if not sub.report_artifact:
            raise ValueError(f"submission {submission_id} has no report artifact — call generate_report() first")
        _transition(sub, SubmissionState.SUBMITTED, actor=actor)
        emit_canonical_event(
            self._outbox,
            legacy_event_name="ComplianceSubmitted",
            data={"submission_id": submission_id, "organization_id": sub.organization_id,
                  "submission_type": sub.submission_type, "period": sub.period},
            source="compliance-service",
            tenant_id=sub.organization_id,
            registry=self._registry,
        )
        # Actual dispatch handled by integrations layer (FBR/EOBI/PESSI adapters)
        return {"submission_id": sub.submission_id, "state": sub.state}

    def acknowledge(self, submission_id: str, authority_ref: str, actor: str = "system") -> None:
        """Called by government adapter webhook on successful acknowledgement."""
        sub = self._require(submission_id, SubmissionState.SUBMITTED)
        _transition(sub, SubmissionState.ACK, actor=actor, detail={"authority_ref": authority_ref})
        emit_canonical_event(
            self._outbox,
            legacy_event_name="ComplianceAcknowledged",
            data={"submission_id": submission_id, "organization_id": sub.organization_id,
                  "authority_ref": authority_ref},
            source="compliance-service",
            tenant_id=sub.organization_id,
            registry=self._registry,
        )

    def mark_failed(
        self,
        submission_id: str,
        reason: str,
        error_type: ComplianceErrorType | str | None = None,
        actor: str = "system",
    ) -> None:
        """Called by government adapter webhook or retry logic on failure.

        error_type (SPEC §13): data_error | rules_error | external_dependency_error | operator_error
        When not provided, error type is inferred from the reason string.
        """
        sub = self._require(submission_id, SubmissionState.SUBMITTED)
        if error_type is None:
            inferred = classify_compliance_error("", reason)
        elif isinstance(error_type, ComplianceErrorType):
            inferred = error_type
        else:
            inferred = ComplianceErrorType(error_type)
        _transition(sub, SubmissionState.FAILED, actor=actor,
                    detail={"reason": reason, "error_type": inferred.value})
        emit_canonical_event(
            self._outbox,
            legacy_event_name="ComplianceSubmissionFailed",
            data={"submission_id": submission_id, "organization_id": sub.organization_id,
                  "reason": reason, "error_type": inferred.value},
            source="compliance-service",
            tenant_id=sub.organization_id,
            registry=self._registry,
        )

    def retry(self, submission_id: str, actor: str = "system") -> dict[str, Any]:
        """Re-queue a failed submission for re-dispatch."""
        sub = self._require(submission_id, SubmissionState.FAILED)
        _transition(sub, SubmissionState.RETRY, actor=actor)
        emit_canonical_event(
            self._outbox,
            legacy_event_name="ComplianceRetryQueued",
            data={"submission_id": submission_id, "organization_id": sub.organization_id},
            source="compliance-service",
            tenant_id=sub.organization_id,
            registry=self._registry,
        )
        return {"submission_id": sub.submission_id, "state": sub.state}

    def record_manual_submission(
        self,
        submission_id: str,
        reference_number: str,
        submitted_by: str,
        notes: str = "",
        actor: str = "system",
    ) -> dict[str, Any]:
        """SPEC-G07: Manual compliance fallback — record an offline/paper submission.

        When automated dispatch to a government portal fails and retry is not possible
        (e.g., FBR portal down for extended period), HR can record the manual submission.
        Transitions the submission to MANUAL state, recording the external reference number.

        Args:
            submission_id:    the submission being manually closed
            reference_number: the government-issued reference or receipt number
            submitted_by:     name / ID of the HR officer who submitted manually
            notes:            optional context (courier tracking, portal ticket ID, etc.)
            actor:            system actor for audit trail

        Valid from: FAILED, RETRY, VALIDATED, SUBMITTED states.
        """
        sub = _submissions.get(submission_id)
        if sub is None:
            raise ValueError(f"Submission {submission_id} not found")
        if sub.state not in (
            SubmissionState.FAILED,
            SubmissionState.RETRY,
            SubmissionState.VALIDATED,
            SubmissionState.SUBMITTED,
        ):
            raise ValueError(
                f"Manual submission can only be recorded from FAILED/RETRY/VALIDATED/SUBMITTED states "
                f"(current: {sub.state})"
            )
        if not reference_number or not reference_number.strip():
            raise ValueError("reference_number is required for manual submission recording")

        sub.manual_mode = True
        sub.manual_reference = reference_number.strip()
        _transition(sub, SubmissionState.MANUAL, actor=actor, detail={
            "reference_number": reference_number,
            "submitted_by": submitted_by,
            "notes": notes,
            "manual_fallback": True,
        })
        return {
            "submission_id": sub.submission_id,
            "state": sub.state,
            "manual_mode": sub.manual_mode,
            "manual_reference": sub.manual_reference,
            "submitted_by": submitted_by,
            "notes": notes,
        }

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------

    def get_audit_trail(
        self,
        submission_id: str | None = None,
        period: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> list[ComplianceAuditRecord]:
        records = list(_audit_log)
        if submission_id:
            records = [r for r in records if r.submission_id == submission_id]
        if period:
            sids = {s.submission_id for s in _submissions.values() if s.period == period}
            records = [r for r in records if r.submission_id in sids]
        if cursor:
            audit_ids = [r.audit_id for r in records]
            start = audit_ids.index(cursor) + 1 if cursor in audit_ids else 0
            records = records[start:]
        return records[:limit]

    # ------------------------------------------------------------------
    # MN-G06: Compliance readiness Decision Card
    # ------------------------------------------------------------------

    def get_compliance_readiness_card(
        self,
        organization_id: str,
        legal_entity_id: str,
        period: str,
        payroll_input: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Pre-payroll compliance readiness check — returns a Decision Card if issues exist.

        Runs validation via the country adapter without creating or mutating any submission.
        Returns None when all employees are clean (no card needed).
        Aligned to docs/canon/decision-system.md DecisionCard schema:
          {trigger, impact, confidence, explanation, recommended_action, reversibility, expires_at}
        """
        adapter = self._resolver.resolve(organization_id)
        result: dict[str, Any] = adapter.validate_payroll({
            "period": period,
            "legal_entity_id": legal_entity_id,
            **payroll_input,
        })
        violations: list[dict] = result.get("violations", [])
        if not violations:
            return None

        # Group violations by rule_id for actionable summary
        by_rule: dict[str, list[str]] = {}
        for v in violations:
            rule_id = v.get("rule_id", "UNKNOWN")
            emp_id = str(v.get("employee_id", "unknown"))
            by_rule.setdefault(rule_id, []).append(emp_id)

        affected_count = len({v.get("employee_id") for v in violations})
        rule_summary = "; ".join(
            f"{len(emps)} employee(s) — {rule}" for rule, emps in sorted(by_rule.items())
        )
        now = datetime.now(timezone.utc)
        return {
            "trigger": "pre_payroll_compliance_check",
            "period": period,
            "impact": f"{affected_count} employee(s) will block payroll finalization",
            "confidence": 95,
            "explanation": (
                f"Compliance validation found {len(violations)} violation(s) across "
                f"{affected_count} employee(s): {rule_summary}."
            ),
            "recommended_action": (
                "Resolve all compliance violations before initiating payroll. "
                "Navigate to Compliance → Validate to see per-employee details."
            ),
            "reversibility": "reversible",
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "violations": violations,
            "affected_count": affected_count,
            "organization_id": organization_id,
            "legal_entity_id": legal_entity_id,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require(self, submission_id: str, expected_state: SubmissionState) -> ComplianceSubmission:
        sub = _submissions.get(submission_id)
        if sub is None:
            raise ValueError(f"Submission {submission_id} not found")
        if sub.state != expected_state:
            raise ValueError(
                f"Submission {submission_id} is in state {sub.state}, expected {expected_state}"
            )
        return sub
