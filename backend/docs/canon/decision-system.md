# Decision System Canon

## 1. AI Payroll Guardian

The **AI Payroll Guardian** is the payroll decision engine responsible for detecting potential payroll integrity issues before pay is finalized.

### Anomaly Types

- **Salary Spike**: Detects unusual salary increases for an employee compared to historical compensation patterns, role band, and scheduled adjustments.
- **Overtime Anomaly**: Detects overtime totals that deviate significantly from expected trends based on shift patterns, team baselines, and prior periods.
- **Missing Deductions**: Detects expected deductions (tax, benefits, garnishments, statutory items) that are absent or materially lower than expected.
- **Ghost Employee**: Detects payroll records that indicate possible non-existent, inactive, duplicate, or improperly retained employees receiving pay.

---

## 2. Scoring

Each anomaly is scored using two separate measures:

- **Risk Score (0–100)**: Measures potential payroll/financial/compliance impact.
- **Confidence (%)**: Measures model certainty that the anomaly is valid.

### Risk Score Bands

- **Low**: 0–39
- **Medium**: 40–69
- **High**: 70–100

### Decision Thresholds

Recommended thresholding for workflow routing:

- **High** risk: immediate review required before payroll lock.
- **Medium** risk: queued for analyst review with SLA.
- **Low** risk: log + monitor; optional spot check.

### AI Confidence Tiers (Canonical)

> NOTE (Group C fix, 2026-06-13): This is the canonical definition for the AI confidence tier boundaries, resolving a divergence between `docs/system/MASTER BUILD SPEC.md` (which previously stated `HIGH (>=80%)` in some readings) and `docs/system/MASTER BEHAVIOR SPEC.md` (`HIGH >= 0.7`, i.e. 70%). The 70% boundary is adopted as canonical because MASTER BEHAVIOR SPEC is the more detailed and authoritative source on AI output behavior (L389: "Provide a confidence score with tier (HIGH >= 0.7, MEDIUM 0.5-0.69, LOW < 0.5)"). MASTER BUILD SPEC's own confidence-tier line (L556, `HIGH (70%+)`) already matches this value; any other reading using an 80% HIGH boundary should be treated as superseded by this definition.

- **HIGH**: confidence >= 0.70 (70%) — system recommendation is reliable.
- **MEDIUM**: 0.50 <= confidence < 0.70 (50-69%) — moderate confidence, human review recommended.
- **LOW**: confidence < 0.50 (<50%) — low confidence, treat as informational only; never present as requiring action.

---

## 3. Explanation

Every flag must include a machine-readable and human-readable explanation in a consistent **"why flagged"** format.

### "Why Flagged" Format

```text
WHY_FLAGGED:
- anomaly_type: <salary_spike|overtime_anomaly|missing_deductions|ghost_employee>
- summary: <one-sentence reason>
- evidence:
  - <metric_1>: <value> (expected: <expected_value>)
  - <metric_2>: <value> (expected: <expected_value>)
- risk_score: <0-100>
- confidence: <0-100%>
- threshold_level: <high|medium|low>
```

---

## 4. Decision Cards

Decision Cards are canonical records produced per anomaly event.

### Schema

```yaml
trigger:              # Event/pattern that activated the rule/model
impact:               # Business/compliance/financial effect estimate
confidence:           # Confidence percentage (0-100)
recommended_action:   # Next best action for operator/system
reversibility:        # reversible | partially_reversible | irreversible
expires_at:           # ISO-8601 timestamp for decision validity
```

### Field Notes

- **trigger**: include anomaly type + key condition.
- **impact**: include both qualitative severity and quantitative estimate when available.
- **confidence**: numeric value with optional model version metadata.
- **recommended_action**: imperative, operator-ready instruction.
- **reversibility**: indicates operational risk of executing action.
- **expires_at**: decision becomes stale after this timestamp and must be re-evaluated.

### Canonical Status Enum

The `status` field on a Decision Card is the authoritative source. Derived from `decision_engine.py`:

| `status`   | Description                                     |
|------------|-------------------------------------------------|
| `active`   | Card is open and awaiting operator action (default) |
| `resolved` | Card explicitly resolved by an operator        |
| `expired`  | Card passed its `expires_at` TTL without action |

> Note: other docs in this workspace use different value sets (`open`, `acknowledged`, `overridden`, `dismissed`, `auto_resolved`, `overridden`). Those are legacy or service-specific states. The canonical values above are the ground truth from `decision_engine.py`.

### Canonical `lifecycle_state` Enum

The `lifecycle_state` field tracks the last mutation applied to the card. Derived from `decision_engine.py`:

| `lifecycle_state` | Description                            |
|-------------------|----------------------------------------|
| `create`          | Card first created (default)           |
| `update`          | Card data updated after creation       |
| `expire`          | Card expired via TTL sweep             |
| `resolve`         | Card explicitly resolved               |

---

## 5. Lifecycle

Decision Cards follow a strict lifecycle:

1. **Create**
   - Generated when AI Payroll Guardian detects an anomaly.
   - Initial score, confidence, and explanation are attached.
2. **Update**
   - Updated when new payroll data, investigator input, or recalculated model output changes card state.
   - Must preserve audit history of prior values.
3. **Expire**
   - Card expires at `expires_at` or when payroll period closes and decision is no longer actionable.
   - Expired cards are immutable except for compliance annotations.

---

## 6. Test Scenarios

Use the following scenarios to validate behavior:

1. **Salary Spike Detection**
   - Input: employee salary rises 35% without promotion event.
   - Expected: anomaly flagged, medium/high risk depending on policy band.
2. **Overtime Anomaly Detection**
   - Input: overtime jumps from 8h average to 42h in one cycle.
   - Expected: anomaly flagged with overtime-specific evidence.
3. **Missing Deductions Detection**
   - Input: recurring retirement deduction absent for current period.
   - Expected: anomaly flagged with deduction delta evidence.
4. **Ghost Employee Detection**
   - Input: payroll issued to inactive employee record.
   - Expected: high-risk flag and immediate hold recommendation.
5. **Lifecycle Transition Validation**
   - Input: card created, then updated after reviewer note, then expired at period close.
   - Expected: state transitions Create → Update → Expire with audit continuity.

---

## QC (10/10 PASS)

- [x] scoring defined
- [x] schema complete
- [x] lifecycle clear
