# Helpdesk Service

HR service delivery and employee query management: ticket creation, routing, SLA tracking, and resolution for HR operations queries.

## Scope
- Manages employee-initiated HR queries and tickets (payslip issues, policy questions, document requests, HR ops).
- Routes tickets to the correct HR team or department based on category.
- Tracks SLA compliance per ticket category.
- Supports knowledge base articles for self-service resolution before ticket creation.
- Integrates with notification-service for ticket status updates.
- Does NOT own payroll, compliance, or attendance data — it surfaces issues and routes resolution requests to the owning service.

## HTTP surface (`/api/v1`)
- `POST /api/v1/helpdesk/tickets` — create HR support ticket
- `GET /api/v1/helpdesk/tickets/{ticket_id}`
- `PATCH /api/v1/helpdesk/tickets/{ticket_id}`
- `POST /api/v1/helpdesk/tickets/{ticket_id}/assign`
- `POST /api/v1/helpdesk/tickets/{ticket_id}/resolve`
- `POST /api/v1/helpdesk/tickets/{ticket_id}/close`
- `POST /api/v1/helpdesk/tickets/{ticket_id}/reopen`
- `POST /api/v1/helpdesk/tickets/{ticket_id}/comments`
- `GET /api/v1/helpdesk/tickets?employee_id=&status=&category=&assigned_to=&limit=&cursor=`
- `GET /api/v1/helpdesk/categories` — ticket category taxonomy
- `GET /api/v1/helpdesk/articles?q=&category=` — knowledge base search
- `POST /api/v1/helpdesk/articles` — create knowledge base article
- `GET /api/v1/helpdesk/sla-report?period=&category=&department_id=`

## Ticket lifecycle states
```
OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED
                              → PENDING_EMPLOYEE → IN_PROGRESS
     → REOPENED → ASSIGNED
```

## Ticket categories
- Payslip / salary queries
- Leave and attendance corrections
- Policy and compliance questions
- Document requests (letters, certificates)
- IT / system access (HR-initiated only)
- Onboarding / offboarding support
- General HR operations

## Domain rules
- SLA timers start when ticket is created and pause when status is `PENDING_EMPLOYEE`.
- Ticket resolution requires a resolution note.
- Tickets can only be reopened within a configurable window after closure.
- Knowledge base articles reduce ticket volume; agents should link articles to resolved tickets.

## Authorization capabilities
- `CAP-HLP-001`: ticket creation and self-service (Employee, all principals)
- `CAP-HLP-002`: ticket assignment, resolution, and management (Admin, HR Ops agent role)
- `CAP-HLP-003`: knowledge base management (Admin)
- `CAP-HLP-004`: SLA reports and helpdesk analytics (Admin)

## Owned entities
- `HelpDeskTicket`
- `TicketComment`
- `TicketCategory`
- `KnowledgeBaseArticle`

## Supported workflows
- `hr_ticket_resolution`

## Events published
- `TicketCreated`
- `TicketAssigned`
- `TicketResolved`
- `TicketClosed`
- `TicketReopened`
- `TicketCommentAdded`
- `SLABreached`

## Events subscribed
- `EmployeeStatusChanged` — close open tickets for terminated employees
- `PayrollProcessed` — auto-close pending payslip tickets for the processed period

## Read models produced
- `helpdesk_tickets_view` — per-employee ticket history and status
- `helpdesk_sla_view` — SLA compliance by category and team

## Dependencies
- `employee-service` — employee identity and department context for routing
- `auth-service` — authorization for ticket management
- `notification-service` — ticket status updates, SLA breach alerts
- `audit-service` — ticket mutation audit trail

## Notes
- Helpdesk is an HR operations support layer. It does not own or modify core HR data.
- Ticket resolution may link to the owning service (e.g., payroll-service for payslip issues) but executes no mutations on those services directly.
- WhatsApp can surface ticket creation and status via `whatsapp-service` integration.
