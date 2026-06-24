# Notification Service

Notification queuing, rendering, delivery, and preference management across all channels: email, SMS, push, and WhatsApp.

## Scope
- Queues, renders, sends, and tracks notifications on behalf of all domain services.
- Applies subject preferences and channel routing rules.
- Translates domain events into outbound communications.
- Manages notification templates per channel and event type.
- Tracks delivery attempts and surfaces failures.

## HTTP surface (`/api/v1`)
- `POST /api/v1/notifications/send`
- `POST /api/v1/notifications/bulk-send`
- `POST /api/v1/notifications/templates`
- `PATCH /api/v1/notifications/templates/{template_id}`
- `GET /api/v1/notifications/templates?code=&channel=&status=&limit=&cursor=`
- `GET /api/v1/notifications/messages/{message_id}`
- `GET /api/v1/notifications/preferences/{subject_id}`
- `PATCH /api/v1/notifications/preferences/{subject_id}`
- `GET /api/v1/notifications/delivery?subject_id=&status=&channel=&limit=&cursor=`

## Channels
- Email (SMTP)
- SMS
- Push (mobile)
- WhatsApp (via `whatsapp-service` outbound dispatch)

## Authorization capabilities
- `CAP-NOT-001`: notification template and delivery operations (Admin full; Manager reads scoped outcomes; Employee reads own)
- `CAP-NOT-002`: notification preference management (all principals manage own)

## Owned entities
- `NotificationTemplate`
- `NotificationMessage`
- `DeliveryAttempt`
- `NotificationPreference`

## Supported workflows
- `notification_dispatch`

## Events published
- `NotificationQueued`
- `NotificationSent`
- `NotificationFailed`
- `NotificationSuppressed`

## Events subscribed
- `LeaveRequestSubmitted` / `LeaveRequestApproved`
- `AttendanceCaptured`
- `PayrollProcessed` / `PayrollPaid`
- `InterviewScheduled` / `InterviewCalendarSynced`
- `UserProvisioned` / `SessionRevoked`
- `AnomalyDetected` (from decision-service) — high-risk alert dispatch
- `ComplianceSubmissionFailed` — compliance failure alerts

## Read models produced
- `notification_delivery_view` — per-subject delivery history, channel status, failure log

## Dependencies
- `auth-service` — operator and service-principal authorization
- External providers: SMTP, SMS gateway, push notification service
- `whatsapp-service` — WhatsApp channel outbound
