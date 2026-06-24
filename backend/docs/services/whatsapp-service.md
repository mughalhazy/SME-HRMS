# WhatsApp Service

Access channel service that exposes HRMS capabilities through WhatsApp — treating it as a first-class employee and manager interface, not a notification bolt-on.

## Scope
- Standalone service in the integration/access layer.
- Handles inbound WhatsApp messages: intent parsing, session management, identity verification, and domain action dispatch.
- Manages phone ↔ employee identity mapping with OTP verification.
- Enforces RBAC through session-bound role context (employee vs. manager scope).
- Routes domain actions to backend services (payroll, leave, attendance, approval workflows).
- Logs all conversation events for analytics and audit.

## HTTP surface (`/api/v1`)
- `POST /api/v1/whatsapp/webhook` — inbound message handler (WhatsApp provider callback)
- `POST /api/v1/whatsapp/identity/register` — register phone ↔ employee mapping
- `POST /api/v1/whatsapp/identity/verify` — OTP verification to activate mapping
- `DELETE /api/v1/whatsapp/identity/{employee_id}` — revoke phone mapping
- `GET /api/v1/whatsapp/identity/{employee_id}` — retrieve mapping status
- `POST /api/v1/whatsapp/send` — outbound message dispatch (system → employee)
- `GET /api/v1/whatsapp/conversations?employee_id=&from=&to=&limit=&cursor=` — conversation log
- `GET /api/v1/whatsapp/sessions/{session_id}` — retrieve active session state

## Capabilities exposed via WhatsApp
- **Payslip**: request current or past payslip; receive secure link or masked summary.
- **Leave**: check balances, apply for leave by date/type/reason, receive tracking ID.
- **Approvals**: managers receive pending approvals; approve/reject directly in chat with optional comment.
- **Alerts**: payroll availability, leave status, approval reminders, policy announcements.

## Identity and security model
- `wa_identity_map(employee_id, phone_e164, status, verified_at, verified_by, last_seen_at)`
- One active employee per phone number enforced; remapping requires revocation of old binding.
- OTP required for initial registration and high-sensitivity actions.
- Session timeout configurable (default: 15 min inactivity).
- Role context (employee / manager) derived from employee record at session start.
- All outbound payslip links are secure and expiring (no persistent public URLs).

## Message interaction model
- Free-text natural language: `"I need my March payslip"`
- Slash-like shortcuts: `payslip 2026-03`, `leave apply 2026-04-10 2026-04-12 annual`
- Button-driven quick replies for common actions.
- Multi-step context retention within session (e.g., leave application flow).
- Explicit cancel keyword: `cancel`.

## Authorization capabilities
- `CAP-WA-001`: inbound message processing and session management (Service principal)
- `CAP-WA-002`: identity mapping administration (Admin)
- `CAP-WA-003`: outbound message dispatch (Service, notification-service)

## Owned entities
- `WhatsAppIdentityMap`
- `WhatsAppSession`
- `WhatsAppConversationEvent`

## Supported workflows
- `whatsapp_payslip_request`
- `whatsapp_leave_application`
- `whatsapp_approval_action`
- `whatsapp_alert_dispatch`

## Events published
- `WhatsAppIdentityRegistered`
- `WhatsAppIdentityVerified`
- `WhatsAppIdentityRevoked`
- `WhatsAppSessionStarted`
- `WhatsAppSessionExpired`
- `WhatsAppMessageReceived`
- `WhatsAppMessageSent`
- `WhatsAppApprovalActioned`

## Events subscribed
- `PayrollProcessed` — trigger payslip availability alert
- `LeaveRequestSubmitted` — confirm submission to employee
- `LeaveRequestApproved` / `LeaveRequestRejected` — notify employee of decision
- `NotificationQueued` (WhatsApp channel) — outbound message dispatch

## Read models produced
- `whatsapp_session_view` — active sessions, identity mapping status
- `whatsapp_conversation_view` — per-employee conversation history for audit

## Dependencies
- `employee-service` — phone ↔ employee identity resolution, role context
- `auth-service` — OTP issuance and session-level authorization
- `payroll-service` — payslip data and secure link generation
- `leave-service` — balance check, leave application dispatch
- `notification-service` — shared outbound channel for alert delivery
- WhatsApp Business API provider — external message transport

## Notes
- WhatsApp = access channel, not a notification bolt-on. It executes real HRMS workflows.
- All actions initiated via WhatsApp are subject to the same RBAC and audit trail as web UI actions.
- See `docs/specs/integrations/whatsapp.md` for full interaction model, OTP flow, and session behavior spec.
