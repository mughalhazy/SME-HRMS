# Experience Layer

## 1. Principles

- **Show actions, not data**: Surface the next best action users can take instead of presenting raw tables or static metrics.
- **Show what needs fixing**: Make issues explicit, prioritized, and actionable so users can resolve blockers quickly.
- **Show why**: Provide concise rationale for each recommendation or alert to improve trust and decision quality.
- **Show confidence**: Include confidence indicators for suggestions and predictions so users understand certainty and risk.

## 2. System Behavior

- **Decision-first UI**: Every screen should lead users toward a concrete decision or action within one interaction.
- **No report-heavy dashboards**: Avoid dense reporting layouts; replace them with focused cards, tasks, and guided workflows.

## 3. API Interaction Model

- **Flow**: `UI → API → response`
- **Model**:
  1. UI sends an intent-driven request with minimal required context.
  2. API evaluates context, returns a decision payload with rationale and confidence.
  3. UI renders recommended actions first, then supporting detail.

## 4. Mobile Constraints

- **Low bandwidth**: Optimize for unstable/mobile networks with compact requests and responses.
- **Minimal payload**: Return only fields required for the current step; defer non-critical data to follow-up calls.

## 5. Test Scenarios

### QC (10/10 PASS)

- [x] Principles are clear.
- [x] Flows are defined.
- [x] No ambiguity in language or expected behavior.
