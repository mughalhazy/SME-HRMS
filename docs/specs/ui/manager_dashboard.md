# Manager Dashboard Specification

## 1. Core Principle

The manager dashboard is **decision-first**: every visible element must help a manager identify a problem, decide quickly, and take action.

- **Decision-first**
  - Prioritize unresolved risks, bottlenecks, and required approvals.
  - Present concise context with direct next actions.
  - Order content by urgency, impact, and time sensitivity.
- **No generic charts**
  - Do not include decorative or exploratory charts (e.g., trend-only visuals without explicit actions).
  - Replace passive visualization with issue summaries, thresholds, and action controls.

## 2. Data Blocks

Each block represents a decision area and only surfaces actionable exceptions.

### 2.1 Attendance Alerts
- Late arrivals beyond policy threshold.
- Unplanned absences and repeated absence patterns.
- Missing check-in/check-out records requiring review.
- Action: acknowledge, notify employee, escalate to HR.

### 2.2 Overtime Anomalies
- Employees exceeding overtime thresholds.
- Department-level spikes versus baseline staffing plans.
- Potential policy violations (unapproved overtime).
- Action: approve exception, rebalance shifts, initiate compliance review.

### 2.3 Approvals
- Pending leave approvals with SLA risk.
- Timesheet corrections awaiting manager action.
- Expense or schedule approvals blocked by missing manager input.
- Action: approve, reject with reason, request clarification.

### 2.4 Burnout Signals
- Consecutive high-load days.
- High overtime + low leave utilization combinations.
- Frequent after-hours work patterns.
- Action: schedule check-in, enforce rest period, adjust workload.

### 2.5 Performance Insights
- Missed target indicators tied to active goals.
- Team members needing intervention or coaching.
- Sudden performance drops relative to recent baseline.
- Action: assign coaching plan, reprioritize goals, schedule review.

## 3. Decision Cards

Decision cards are the primary UI unit for every surfaced issue.

### 3.1 Placement
- Fixed top region: critical items requiring action within 24 hours.
- Secondary region: medium-priority items grouped by data block.
- Cards are sorted by severity, then due time.
- Maximum visible cards per block before "View all issues" expansion.

### 3.2 Interaction
- Each card includes: issue title, affected employee/team, risk reason, due time.
- Each card includes at least one primary action button (e.g., `Approve`, `Escalate`, `Assign follow-up`).
- Optional secondary actions: `Snooze`, `Reassign`, `Request details`.
- Interaction must complete in minimal steps (inline action preferred over navigation).

## 4. APIs

All displayed data must be sourced through explicit endpoints.

| Data Block | Endpoint | Method | Purpose |
|---|---|---|---|
| Attendance Alerts | `/api/manager/dashboard/attendance-alerts` | GET | Return active attendance exceptions and severity metadata. |
| Overtime Anomalies | `/api/manager/dashboard/overtime-anomalies` | GET | Return overtime outliers and policy-risk flags. |
| Approvals | `/api/manager/dashboard/approvals` | GET | Return manager-owned pending approvals and due windows. |
| Burnout Signals | `/api/manager/dashboard/burnout-signals` | GET | Return workload-risk signals per employee/team. |
| Performance Insights | `/api/manager/dashboard/performance-insights` | GET | Return intervention-worthy performance exceptions. |

### 4.1 Decision Actions APIs

| Action Type | Endpoint | Method | Purpose |
|---|---|---|---|
| Attendance Action | `/api/manager/dashboard/attendance-alerts/{id}/action` | POST | Resolve, escalate, or request correction for attendance issue. |
| Overtime Action | `/api/manager/dashboard/overtime-anomalies/{id}/action` | POST | Approve exception, reject overtime, or trigger staffing rebalance flow. |
| Approval Action | `/api/manager/dashboard/approvals/{id}/action` | POST | Approve/reject/request-info for pending item. |
| Burnout Action | `/api/manager/dashboard/burnout-signals/{id}/action` | POST | Assign mitigation steps (check-in, rest block, workload adjustment). |
| Performance Action | `/api/manager/dashboard/performance-insights/{id}/action` | POST | Create coaching intervention or schedule follow-up review. |

## 5. UX Rules

- **Show issues only**
  - Do not show neutral/healthy states in primary dashboard space.
  - Hide blocks with zero actionable items or collapse them under "No action needed".
- **Action-oriented**
  - Every surfaced issue must map to at least one direct action.
  - Avoid passive analytics language; use explicit decision language (e.g., "Approve now", "Escalate today").
  - Keep action context on-card: why now, impact, and required response time.

## 6. Test Scenarios

1. **Critical attendance breach appears at top**
   - Given an employee with repeated no-show events,
   - when dashboard loads,
   - then attendance decision card is placed in critical region with escalation action.

2. **Overtime anomaly triggers compliance path**
   - Given overtime exceeds policy threshold without prior approval,
   - when manager opens anomaly card,
   - then compliance risk label and approval/reject actions are available.

3. **Approval SLA risk is surfaced**
   - Given pending leave request near SLA breach,
   - when dashboard refreshes,
   - then request appears in approvals block with due-time indicator and primary action.

4. **Burnout signal prompts mitigation**
   - Given employee has sustained overtime and after-hours pattern,
   - when burnout block is rendered,
   - then card includes check-in and workload-adjustment actions.

5. **Performance drop requires intervention**
   - Given team member performance drops below baseline threshold,
   - when insights block is loaded,
   - then intervention card provides coaching-plan action.

6. **No actionable issues hides block**
   - Given a block API returns no active issues,
   - when dashboard is displayed,
   - then block is collapsed and does not consume primary space.

7. **Card action updates issue state**
   - Given manager executes a primary action,
   - when action API returns success,
   - then card state updates to resolved/assigned and exits active issue queue.

## QC (10/10 PASS)

- [x] No charts defined.
- [x] All data blocks mapped to APIs.
- [x] Decision-first principle enforced across layout and interactions.
