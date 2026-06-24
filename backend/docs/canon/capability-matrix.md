# Capability Matrix

Source anchors:
- `docs/canon/domain-model.md`
- `docs/canon/service-map.md`
- `docs/canon/read-model-catalog.md`
- `docs/canon/api-standards.md`

## Capability registry

| Capability ID | Capability Name | Service Owner | Primary Entities | Primary Read Model(s) | API Endpoint Category |
|---|---|---|---|---|---|
| `CAP-EMP-001` | Employee directory and lifecycle management | `employee-service` | `Employee`, `Department`, `Role` | `employee_directory_view`, `organization_structure_view` | `/api/v1/employees`, `/api/v1/departments`, `/api/v1/roles` |
| `CAP-EMP-002` | Employee profile maintenance and org assignment | `employee-service` | `Employee`, `Department`, `Role` | `employee_directory_view`, `organization_structure_view` | `/api/v1/employees/{employee_id}` |
| `CAP-ATT-001` | Attendance capture and monitoring | `attendance-service` | `AttendanceRecord`, `Employee` | `attendance_dashboard_view` | `/api/v1/attendance/records`, `/api/v1/attendance/summaries` |
| `CAP-ATT-002` | Attendance validation and period lock | `attendance-service` | `AttendanceRecord` | `attendance_dashboard_view` | `/api/v1/attendance/records/{attendance_id}/validate`, `/approve`, `/api/v1/attendance/periods/{period_id}/lock` |
| `CAP-LEV-001` | Leave request lifecycle management | `leave-service` | `LeaveRequest`, `Employee` | `leave_requests_view` | `/api/v1/leave/requests` |
| `CAP-LEV-002` | Leave decision workflow | `leave-service` | `LeaveRequest` | `leave_requests_view` | `/api/v1/leave/requests/{leave_request_id}/submit`, `/approve`, `/reject`, `/cancel` |
| `CAP-PAY-001` | Payroll processing and payroll data access | `payroll-service` | `PayrollRecord`, `Employee` | `payroll_summary_view` | `/api/v1/payroll/records`, `/api/v1/payroll/run` |
| `CAP-PAY-002` | Payroll disbursement completion | `payroll-service` | `PayrollRecord` | `payroll_summary_view` | `/api/v1/payroll/records/{payroll_record_id}/mark-paid` |
| `CAP-HIR-001` | Job posting and requisition management | `hiring-service` | `JobPosting`, `Department`, `Role` | `job_posting_directory_view` | `/api/v1/hiring/job-postings`, `/api/v1/hiring/job-postings/{job_posting_id}/hold`, `/api/v1/hiring/job-postings/{job_posting_id}/reopen` |
| `CAP-HIR-002` | Candidate pipeline and interview management | `hiring-service` | `Candidate`, `Interview`, `JobPosting` | `candidate_pipeline_view` | `/api/v1/hiring/candidates`, `/api/v1/hiring/interviews`, `/api/v1/hiring/interviews/{interview_id}/cancel`, `/api/v1/hiring/interviews/{interview_id}/mark-no-show` |
| `CAP-PRF-001` | Enterprise performance management | `performance-service` | `ReviewCycle`, `Goal`, `Feedback`, `CalibrationSession`, `PipPlan`, `Employee` | `performance_review_view` | `/api/v1/performance/review-cycles`, `/api/v1/performance/goals`, `/api/v1/performance/feedback`, `/api/v1/performance/calibrations`, `/api/v1/performance/pips` |
| `CAP-ENG-001` | Employee engagement surveys and analytics | `engagement-service` | `Survey`, `SurveyQuestion`, `SurveyResponse`, `AggregatedSurveyResult`, `Employee` | `engagement_survey_view` | `/api/v1/engagement/surveys`, `/api/v1/engagement/responses`, `/api/v1/engagement/surveys/{survey_id}/aggregates` |
| `CAP-AUT-001` | Identity and access administration | `auth-service` | `UserAccount`, `RoleBinding`, `PermissionPolicy`, `Session`, `RefreshToken` | `access_control_view` | `/api/v1/auth/users`, `/api/v1/auth/sessions`, `/api/v1/auth/policies`, `/api/v1/auth/access` |
| `CAP-NOT-001` | Notification template and delivery operations | `notification-service` | `NotificationTemplate`, `NotificationMessage`, `DeliveryAttempt` | `notification_delivery_view` | `/api/v1/notifications/send`, `/api/v1/notifications/templates`, `/api/v1/notifications/messages/{message_id}`, `/api/v1/notifications/delivery` |
| `CAP-NOT-002` | Notification preference management | `notification-service` | `NotificationPreference` | `notification_delivery_view` | `GET/PATCH /api/v1/notifications/preferences/{subject_id}` |
| `CAP-COM-001` | Compliance submission management | `compliance-service` | `ComplianceSubmission`, `ComplianceReport` | `compliance_status_view` | `/api/v1/compliance/submissions`, `/api/v1/compliance/submissions/{id}/validate`, `/submit`, `/retry` |
| `CAP-COM-002` | Compliance report access | `compliance-service` | `ComplianceReport`, `ComplianceAuditRecord` | `compliance_status_view` | `/api/v1/compliance/submissions/{id}/report`, `/api/v1/compliance/audit` |
| `CAP-COM-003` | Compliance audit trail | `compliance-service` | `ComplianceAuditRecord` | `compliance_status_view` | `GET /api/v1/compliance/audit` |
| `CAP-DEC-001` | Decision Cards and anomaly visibility | `decision-service` | `DecisionCard`, `AnomalyRecord` | `decision_cards_view` | `/api/v1/decisions/cards`, `/api/v1/decisions/anomalies` |
| `CAP-DEC-002` | Decision Card actions (acknowledge/override/dismiss) | `decision-service` | `DecisionCard`, `DecisionAuditEntry` | `decision_cards_view` | `/api/v1/decisions/cards/{id}/acknowledge`, `/override`, `/dismiss` |
| `CAP-DEC-003` | On-demand anomaly scan trigger | `decision-service` | `DecisionCard`, `AnomalyRecord` | `decision_cards_view` | `POST /api/v1/decisions/scan` |
| `CAP-EWA-001` | Earned wage access request and status | `ewa-financial-service` | `EWARequest` | `financial_wellness_view` | `/api/v1/financial-wellness/ewa` |
| `CAP-EWA-002` | Salary advance request and approval | `ewa-financial-service` | `SalaryAdvance`, `RepaymentSchedule` | `financial_wellness_view` | `/api/v1/financial-wellness/loan` |
| `CAP-BNK-001` | Salary disbursement and payment execution | `bank-service` | `DisbursementBatch`, `PaymentRecord` | `disbursement_status_view` | `/api/v1/banking/disbursements`, `/api/v1/banking/raast/payout` |
| `CAP-BNK-002` | Payment tracking and reconciliation | `bank-service` | `ReconciliationReport` | `disbursement_status_view`, `reconciliation_view` | `/api/v1/banking/reconcile`, `/api/v1/banking/payments` |
| `CAP-BNK-003` | Bank account management | `bank-service` | `EmployeeBankAccount` | `disbursement_status_view` | `GET /api/v1/banking/accounts`, `POST /api/v1/banking/accounts`, `PATCH /api/v1/banking/accounts/{account_id}` |
| `CAP-RPT-001` | Operational and compliance reports | `reporting-analytics-service` | `ReportDefinition`, `ReportExecution` | `analytics_dashboard_view` | `/api/v1/analytics/reports`, `/api/v1/analytics/payroll-summary`, `/api/v1/analytics/compliance-status` |
| `CAP-RPT-002` | Predictive insights and anomaly feed | `reporting-analytics-service` | `AnalyticsProjection` | `analytics_dashboard_view` | `/api/v1/analytics/anomalies`, `/api/v1/analytics/turnover` |
| `CAP-RPT-003` | Report scheduling | `reporting-analytics-service` | `ReportDefinition`, `ReportExecution` | `analytics_dashboard_view` | `POST /api/v1/analytics/reports/schedule` |
| `CAP-WA-001` | WhatsApp inbound processing and session management | `whatsapp-service` | `WhatsAppSession`, `WhatsAppConversationEvent` | `whatsapp_session_view` | `/api/v1/whatsapp/webhook`, `/api/v1/whatsapp/sessions` |
| `CAP-EXP-001` | Expense claim submission and management | `expense-service` | `ExpenseClaim`, `ExpenseReceipt` | `expense_claims_view` | `/api/v1/expenses/claims` |
| `CAP-EXP-002` | Expense claim approval | `expense-service` | `ExpenseClaim` | `expense_claims_view` | `POST /api/v1/expenses/claims/{claim_id}/approve`, `/reject` |
| `CAP-EXP-003` | Expense reports and accounting export | `expense-service` | `ExpenseClaim`, `ExpenseCategory` | `expense_claims_view` | `GET /api/v1/expenses/reports` |
| `CAP-HLP-001` | HR ticket creation and self-service | `helpdesk-service` | `HelpDeskTicket`, `KnowledgeBaseArticle` | `helpdesk_tickets_view` | `/api/v1/helpdesk/tickets`, `/api/v1/helpdesk/articles` |
| `CAP-HLP-002` | Ticket assignment, resolution, and management | `helpdesk-service` | `HelpDeskTicket`, `TicketComment` | `helpdesk_tickets_view`, `helpdesk_sla_view` | `/api/v1/helpdesk/tickets/{id}/assign`, `/resolve`, `/close` |
| `CAP-HLP-003` | Knowledge base management | `helpdesk-service` | `KnowledgeBaseArticle` | `helpdesk_tickets_view` | `POST /api/v1/helpdesk/articles` |
| `CAP-HLP-004` | SLA reports and helpdesk analytics | `helpdesk-service` | `HelpDeskTicket`, `TicketCategory` | `helpdesk_sla_view` | `GET /api/v1/helpdesk/sla-report` |
| `CAP-AUT-002` | Automation rule management | `automation-service` | `AutomationRule` | `automation_execution_view` | `/api/v1/automations` |
| `CAP-AUT-003` | Automation execution history and manual trigger | `automation-service` | `AutomationExecution`, `AutomationExecutionLog` | `automation_execution_view` | `/api/v1/automations/{id}/executions`, `/trigger` |

## Entity coverage check

> New entities added from compliance, decision, EWA, banking, reporting, WhatsApp, and expense services.

| Domain Entity | Owning Service | Capabilities |
|---|---|---|
| `Employee` | `employee-service` | `CAP-EMP-001`, `CAP-EMP-002` |
| `Department` | `employee-service` | `CAP-EMP-001`, `CAP-HIR-001` |
| `Role` | `employee-service` | `CAP-EMP-001`, `CAP-HIR-001` |
| `ReviewCycle` | `performance-service` | `CAP-PRF-001` |
| `Goal` | `performance-service` | `CAP-PRF-001` |
| `Feedback` | `performance-service` | `CAP-PRF-001` |
| `CalibrationSession` | `performance-service` | `CAP-PRF-001` |
| `PipPlan` | `performance-service` | `CAP-PRF-001` |
| `Survey` | `engagement-service` | `CAP-ENG-001` |
| `SurveyQuestion` | `engagement-service` | `CAP-ENG-001` |
| `SurveyResponse` | `engagement-service` | `CAP-ENG-001` |
| `AggregatedSurveyResult` | `engagement-service` | `CAP-ENG-001` |
| `AttendanceRecord` | `attendance-service` | `CAP-ATT-001`, `CAP-ATT-002` |
| `LeaveRequest` | `leave-service` | `CAP-LEV-001`, `CAP-LEV-002` |
| `PayrollRecord` | `payroll-service` | `CAP-PAY-001`, `CAP-PAY-002` |
| `JobPosting` | `hiring-service` | `CAP-HIR-001`, `CAP-HIR-002` |
| `Candidate` | `hiring-service` | `CAP-HIR-002` |
| `Interview` | `hiring-service` | `CAP-HIR-002` |
| `UserAccount` | `auth-service` | `CAP-AUT-001` |
| `RoleBinding` | `auth-service` | `CAP-AUT-001` |
| `PermissionPolicy` | `auth-service` | `CAP-AUT-001` |
| `Session` | `auth-service` | `CAP-AUT-001` |
| `RefreshToken` | `auth-service` | `CAP-AUT-001` |
| `NotificationTemplate` | `notification-service` | `CAP-NOT-001` |
| `NotificationMessage` | `notification-service` | `CAP-NOT-001` |
| `DeliveryAttempt` | `notification-service` | `CAP-NOT-001` |
| `NotificationPreference` | `notification-service` | `CAP-NOT-002` |

## Service linkage check

| Service | Linked capabilities |
|---|---|
| `employee-service` | `CAP-EMP-001`, `CAP-EMP-002` |
| `performance-service` | `CAP-PRF-001` |
| `engagement-service` | `CAP-ENG-001` |
| `attendance-service` | `CAP-ATT-001`, `CAP-ATT-002` |
| `leave-service` | `CAP-LEV-001`, `CAP-LEV-002` |
| `payroll-service` | `CAP-PAY-001`, `CAP-PAY-002` |
| `hiring-service` | `CAP-HIR-001`, `CAP-HIR-002` |
| `auth-service` | `CAP-AUT-001` |
| `notification-service` | `CAP-NOT-001`, `CAP-NOT-002` |
| `compliance-service` | `CAP-COM-001`, `CAP-COM-002`, `CAP-COM-003` |
| `decision-service` | `CAP-DEC-001`, `CAP-DEC-002`, `CAP-DEC-003` |
| `ewa-financial-service` | `CAP-EWA-001`, `CAP-EWA-002` |
| `bank-service` | `CAP-BNK-001`, `CAP-BNK-002`, `CAP-BNK-003` |
| `reporting-analytics-service` | `CAP-RPT-001`, `CAP-RPT-002`, `CAP-RPT-003` |
| `whatsapp-service` | `CAP-WA-001` |
| `expense-service` | `CAP-EXP-001`, `CAP-EXP-002`, `CAP-EXP-003` |
| `helpdesk-service` | `CAP-HLP-001`, `CAP-HLP-002`, `CAP-HLP-003`, `CAP-HLP-004` |
| `automation-service` | `CAP-AUT-002`, `CAP-AUT-003` |
