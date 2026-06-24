# Decision Service

Cross-domain intelligence layer that detects anomalies, scores risk, and produces Decision Cards for operator action across payroll, attendance, compliance, and performance domains.

## Scope
- Standalone cross-domain service — NOT a sub-module of payroll-service.
- Runs the AI Payroll Guardian to detect payroll integrity issues before pay is finalized.
- Produces Decision Cards with risk score, confidence, recommended action, and reversibility.
- Surfaces actionable signals to the manager dashboard and HR admin console.
- Maintains a human-in-the-loop gate: high-risk decisions require explicit operator approval before proceeding.
- All AI outputs are explainable and auditable.

## HTTP surface (`/api/v1`)
- `GET /api/v1/decisions/cards?domain=&status=&risk_level=&employee_id=&period=&limit=&cursor=`
- `GET /api/v1/decisions/cards/{card_id}`
- `POST /api/v1/decisions/cards/{card_id}/acknowledge`
- `POST /api/v1/decisions/cards/{card_id}/override` — human-in-loop override with required reason
- `POST /api/v1/decisions/cards/{card_id}/dismiss`
- `GET /api/v1/decisions/anomalies?type=&period=&risk_level=&limit=&cursor=`
- `POST /api/v1/decisions/scan` — trigger on-demand anomaly scan for a pay period

## Decision Card schema
```yaml
card_id: uuid
trigger:            # event/pattern that activated the rule
anomaly_type:       # salary_spike | overtime_anomaly | missing_deductions | ghost_employee
domain:             # payroll | attendance | compliance | performance
employee_id: uuid
period: string
impact:             # business/financial/compliance effect estimate
risk_score:         # 0–100 (Low: 0–39 | Medium: 40–69 | High: 70–100)
confidence:         # 0–100%
threshold_level:    # high | medium | low
recommended_action: # imperative, operator-ready instruction
reversibility:      # reversible | partially_reversible | irreversible
expires_at:         # ISO-8601; card becomes stale after this
why_flagged:
  summary: string
  evidence:
    - metric: string
      value: string
      expected: string
status:             # open | acknowledged | overridden | dismissed | expired
                    # NOTE (G50): canonical values from decision_engine.py: active | resolved | expired
                    # See docs/canon/decision-system.md for authoritative enum
created_at: timestamp
updated_at: timestamp
```

## Anomaly types
- **salary_spike**: unusual salary increase vs. historical pattern, role band, scheduled adjustments.
- **overtime_anomaly**: overtime deviating significantly from shift patterns, team baselines, prior periods.
- **missing_deductions**: expected deductions (tax, statutory, garnishments) absent or materially lower.
- **ghost_employee**: payroll issued to inactive, duplicate, or improperly retained employee records.

## Risk routing
- **High (70–100)**: immediate review required before payroll lock.
- **Medium (40–69)**: queued for analyst review with SLA.
- **Low (0–39)**: logged and monitored; optional spot check.

## Human-in-loop gates (mandatory)
- Payroll approval for periods with open High-risk cards.
- Compliance submission when anomalies are unresolved.
- Anomaly override requires actor identity, reason, and audit log entry.

## Authorization capabilities
- `CAP-DEC-001`: view Decision Cards and anomalies (Admin, Manager scoped, PayrollAdmin)
- `CAP-DEC-002`: acknowledge / override / dismiss cards (Admin, PayrollAdmin)
- `CAP-DEC-003`: trigger on-demand scan (Admin, PayrollAdmin)

## Owned entities
- `DecisionCard`
- `AnomalyRecord`
- `DecisionAuditEntry`

## Card lifecycle
1. **Created** — Guardian detects anomaly; card created with score, confidence, explanation.
2. **Acknowledged** — Operator reviews and acknowledges (logged).
3. **Overridden** — Operator overrides with mandatory reason (logged, irreversible audit entry).
4. **Dismissed** — Operator dismisses as false positive (logged).
5. **Expired** — Card expires at `expires_at` or period close; immutable except compliance annotations.

## Supported workflows
- `anomaly_review`

## Events published
- `AnomalyDetected`
- `DecisionCardCreated`
- `DecisionCardAcknowledged`
- `DecisionCardOverridden`
- `DecisionCardDismissed`
- `DecisionCardExpired`

## Events subscribed
- `PayrollProcessed` — triggers payroll guardian scan
- `AttendancePeriodClosed` — triggers attendance anomaly scan
- `ComplianceValidationFailed` — escalates to decision surface
- `PerformancePipCreated` — surfaces performance intervention signal

## Read models produced
- `decision_cards_view` — active cards by domain, risk level, period
- enriches `manager_dashboard_view` with actionable anomaly signals

## Dependencies
- `payroll-service` — payroll data for guardian scan input
- `attendance-service` — attendance data for overtime and absence anomalies
- `compliance-service` — compliance violations as input signals
- `employee-service` — employee roster, role band, compensation history
- `audit-service` — immutable decision audit records
- `notification-service` — high-risk alerts to approvers

## Implementation files

| Component | File |
|---|---|
| Decision Card dataclass | `services/decision_engine.py` (243 lines) |
| AI Payroll Guardian | `services/ai/payroll_guardian.py` (154 lines) |
| Anomaly Engine | `services/ai/anomaly_engine.py` (166 lines) |
| HR Copilot (explainable Q&A) | `services/ai/hr_copilot.py` (98 lines) |
| Governance / Human-in-loop gates | `services/governance/service.py` (97 lines) |

### GovernanceService

`services/governance/service.py` is the implementation of the human-in-loop gate layer. It enforces:
- `create_payroll_approval()` / `review_payroll_approval()` — payroll approval lifecycle (pending → approved/rejected)
- `submit_compliance()` — blocks compliance submission until payroll is approved
- `override_anomaly()` — mandatory reason enforcement for anomaly override
- `update_decision()` / `expire_decision()` — decision card lifecycle management (immutable once expired)

All GovernanceService operations emit audit trail entries. This service is called by `decision_api.py` endpoints for all override and approval actions.

## Notes
- See `docs/canon/decision-system.md` for full scoring model, "why flagged" format, and QC test scenarios.
- Confidence system: HIGH ≥ 80%, MEDIUM 50–79%, LOW < 50%.
- AI outputs must always include human-readable explanation — no silent flags.
