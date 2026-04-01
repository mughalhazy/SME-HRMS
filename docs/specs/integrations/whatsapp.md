# WhatsApp HR Layer Specification

## 1. Capabilities

The WhatsApp HR layer provides conversational self-service for employees and actionable work queues for approvers.

### 1.1 Payslip
- Request current-month payslip.
- Request payslip for a specific month/year.
- Receive secure link or masked summary (net pay, deductions, tax).
- Optional PDF delivery through a secure, expiring URL.

### 1.2 Leave
- Check leave balances by leave type (annual, sick, unpaid, etc.).
- Apply for leave by date range, leave type, and reason.
- Validate overlaps, holidays, and policy constraints.
- Receive immediate submission confirmation and tracking ID.

### 1.3 Approvals
- Managers receive pending approvals (leave, reimbursement, attendance corrections).
- Approve/reject directly in chat with optional comments.
- Request additional information before decision.
- Receive post-decision audit confirmation.

### 1.4 Alerts
- Push alerts for payroll availability, leave status changes, approval reminders, and policy announcements.
- Support priority tags (info, warning, action-required).
- Respect user notification preferences and quiet hours.
- Include deep links to HRMS portal when required.

---

## 2. Interaction Model

### 2.1 Message Pattern
**User message → System response**

1. User sends free-text or quick-reply command via WhatsApp.
2. WhatsApp provider posts inbound payload to HR webhook.
3. HR layer authenticates sender (phone ↔ employee mapping, session/token checks).
4. Intent parser maps message to domain action (payslip/leave/approval/alert handling).
5. Backend service executes business rules and data fetch/update.
6. System sends structured response message (text + optional buttons/doc links).
7. Conversation event is logged for analytics and audit.

### 2.2 Command Modes
- **Natural language:** "I need my March payslip"
- **Slash-like shortcuts:** `payslip 2026-03`, `leave apply 2026-04-10 2026-04-12 annual`
- **Button-driven:** quick replies for common actions.

### 2.3 Session Behavior
- Session timeout configurable (e.g., 15 minutes inactivity).
- Context retention for multi-step forms (leave application flow).
- Explicit cancel keyword supported: `cancel`.

---

## 3. Flows

### 3.1 Flow: Get Payslip (Step-by-Step)
1. User sends: `payslip` or `payslip YYYY-MM`.
2. System validates authentication/session.
3. If period missing, system asks: "Which month do you need? (YYYY-MM)".
4. User provides period.
5. System validates period format and payroll availability.
6. System fetches payslip metadata.
7. System responds with summary and secure download link.
8. System logs transaction ID and outcome.

**Edge Cases**
- Payroll not yet processed for requested month.
- User requests future month.
- Unauthorized number not mapped to employee.

### 3.2 Flow: Apply Leave (Step-by-Step)
1. User sends: `apply leave`.
2. System asks for leave type.
3. User provides leave type.
4. System asks for start and end dates.
5. User provides dates.
6. System asks for reason (optional/mandatory by policy).
7. System validates balance, overlaps, blackout dates, and min/max duration.
8. If validation passes, system creates leave request in HRMS.
9. System returns confirmation: request ID, status `Pending Approval`, and next approver.
10. System sends notification to approver queue.

**Edge Cases**
- Insufficient leave balance.
- Start date after end date.
- Date range includes company holiday for non-deductible policy.
- Duplicate submission caused by message retries.

### 3.3 Flow: Approve Request (Step-by-Step)
1. Approver sends: `pending approvals`.
2. System returns list of pending requests with IDs and key details.
3. Approver sends: `approve <request_id>` or `reject <request_id> <reason>`.
4. System verifies approver authorization and request state.
5. System applies decision transactionally.
6. System notifies requester with decision and comment.
7. System returns audit confirmation to approver.

**Edge Cases**
- Request already processed by another approver.
- Approver lacks authority (delegation expired/out of scope).
- Missing rejection reason where mandatory.

---

## 4. API

### 4.1 Webhook Schema (Inbound from WhatsApp Provider)

```json
{
  "event_id": "evt_01JX...",
  "timestamp": "2026-04-01T09:15:22Z",
  "channel": "whatsapp",
  "provider": "meta",
  "message": {
    "message_id": "wamid.HBg...",
    "from": "+15551234567",
    "to": "+15557654321",
    "type": "text",
    "text": "payslip 2026-03",
    "interactive": null,
    "attachments": []
  },
  "context": {
    "reply_to_message_id": null,
    "session_id": "sess_a1b2c3",
    "locale": "en-US",
    "timezone": "America/New_York"
  },
  "security": {
    "signature": "sha256=...",
    "signature_header": "X-Hub-Signature-256"
  }
}
```

**Field Requirements**
- Required: `event_id`, `timestamp`, `channel`, `message.message_id`, `message.from`, `message.type`.
- Conditional: `message.text` required when `type=text`.
- Validation: reject if signature invalid, timestamp skew exceeds configured threshold, or duplicate `event_id`.

### 4.2 Response Schema (Outbound to WhatsApp Provider)

```json
{
  "correlation_id": "corr_7f9...",
  "to": "+15551234567",
  "type": "interactive",
  "text": "Your payslip for 2026-03 is ready.",
  "interactive": {
    "buttons": [
      { "id": "download_payslip_2026_03", "title": "Download" },
      { "id": "view_summary_2026_03", "title": "Summary" }
    ]
  },
  "attachments": [
    {
      "kind": "link",
      "label": "Payslip PDF",
      "url": "https://hrms.example.com/payslip/secure-token",
      "expires_at": "2026-04-01T10:15:22Z"
    }
  ],
  "meta": {
    "intent": "payslip.get",
    "status": "success",
    "request_id": "req_12345"
  }
}
```

**Field Requirements**
- Required: `correlation_id`, `to`, `type`, and one of (`text`, `interactive`, `attachments`).
- Security: URLs must be HTTPS and short-lived; never include raw payroll identifiers in clear text.
- Localization: all user-facing text should follow preferred locale.

---

## 5. Error Handling

### 5.1 Invalid Command
- **Condition:** message cannot be mapped to supported intent.
- **System Behavior:**
  - Return help prompt with supported commands.
  - Do not create backend transaction.
  - Increment unknown-intent metric.
- **Example Response:**
  - "I couldn’t understand that command. Try: `payslip`, `apply leave`, or `pending approvals`."

### 5.2 Missing Data
- **Condition:** intent recognized but required fields absent (e.g., leave dates missing).
- **System Behavior:**
  - Prompt only for missing fields.
  - Preserve already collected fields in session context.
  - Timeout gracefully with resume instructions.
- **Example Response:**
  - "Please provide start and end dates in YYYY-MM-DD format."

### 5.3 Standard Error Envelope

```json
{
  "correlation_id": "corr_7f9...",
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "End date cannot be before start date.",
  "recoverable": true,
  "next_step": "Provide valid start and end dates in YYYY-MM-DD format."
}
```

---

## 6. Test Scenarios

### 6.1 Functional Scenarios
1. **Payslip success:** valid employee requests closed payroll month and receives secure link.
2. **Payslip unavailable:** employee requests month not yet processed.
3. **Leave success:** valid leave application with sufficient balance creates pending request.
4. **Leave validation:** start date > end date returns validation error.
5. **Approval success:** authorized manager approves pending request.
6. **Approval conflict:** manager tries to approve already finalized request.

### 6.2 Edge & Resilience Scenarios
7. Duplicate webhook delivery (`event_id` replay) is idempotently ignored.
8. Invalid webhook signature is rejected with unauthorized status.
9. Session timeout during leave flow prompts resume/restart guidance.
10. Missing required payload fields returns structured error envelope.
11. Provider transient failure triggers retry with backoff.
12. Rate-limited user receives polite throttle response.

### 6.3 QC Checklist (10/10 PASS)
- [x] Flows are step-by-step and executable.
- [x] Inbound and outbound schemas are complete with required fields.
- [x] Edge cases for all primary flows are covered.
- [x] Invalid command handling defined.
- [x] Missing data handling defined.
- [x] Error envelope standardized.
- [x] Security checks (signature, expiring URLs) included.
- [x] Idempotency/retry behavior specified.
- [x] Authorization checks included for approvals.
- [x] Test scenarios span success, validation, conflict, and resilience cases.
