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
