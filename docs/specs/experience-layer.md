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

## 5. Experience Modes

### SME Lite mode

- `sme_lite_mode` provides a simplified feature surface for smaller teams.
- In Lite mode, only payroll, compliance, and attendance remain enabled.
- Lite mode explicitly hides all other modules regardless of tier.

### Payroll-as-a-Service (PaaS) mode

- `payroll_managed_mode` enables managed payroll operation for service-led payroll execution.
- `payroll_admin_override_controls` is only effective when managed payroll mode is enabled.
- Admin override must remain gated to MID/ENTERPRISE tiers.

### Financial wellness hooks

- Loan and EWA integrations are represented as placeholder API contracts.
- Placeholder contracts reserve stable endpoints for downstream providers:
  - `POST /api/v1/financial-wellness/loan`
  - `POST /api/v1/financial-wellness/ewa`

## 6. Tier Logic

### Tier definitions

- **SMB**: payroll + compliance + attendance.
- **MID**: SMB + performance + recruitment + analytics.
- **ENTERPRISE**: MID + governance + advanced compliance + workflows.

### Consistency rules

- Tier gating must be deterministic and monotonic (`SMB ⊆ MID ⊆ ENTERPRISE`).
- `sme_lite_mode` may reduce visible features but must preserve core surfaces.
- Payroll admin override is denied for SMB regardless of mode toggles.

## 7. Test Scenarios

### QC (10/10 PASS)

- [x] SME Lite toggle simplifies features.
- [x] Payroll-as-a-Service controls gate correctly.
- [x] Loan/EWA placeholder APIs are exposed.
- [x] Tier logic is consistent for SMB/MID/ENTERPRISE.
- [x] Feature gating remains deterministic across mode combinations.
