# UI Surface Map

This document maps current UI surfaces in the repository to canonical read models, capabilities, and service owners.

## Mapping table

| UI Surface | Primary Read Model(s) | Capability ID(s) | Primary Service Owner | Domain Entities |
|---|---|---|---|---|
| `dashboard` | `employee_directory_view`, `attendance_dashboard_view`, `leave_requests_view`, `payroll_summary_view`, `job_posting_directory_view`, `candidate_pipeline_view`, `performance_review_view` | `CAP-EMP-001`, `CAP-ATT-001`, `CAP-LEV-001`, `CAP-PAY-001`, `CAP-HIR-001`, `CAP-HIR-002`, `CAP-PRF-001` | `employee-service` | `Employee`, `AttendanceRecord`, `LeaveRequest`, `PayrollRecord`, `JobPosting`, `Candidate`, `PerformanceReview` |
| `employee_list` | `employee_directory_view` | `CAP-EMP-001` | `employee-service` | `Employee`, `Department`, `Role` |
| `employee_profile` | `employee_directory_view`, `attendance_dashboard_view`, `leave_requests_view`, `payroll_summary_view`, `performance_review_view` | `CAP-EMP-002`, `CAP-ATT-001`, `CAP-LEV-001`, `CAP-PAY-001`, `CAP-PRF-001` | `employee-service` | `Employee`, `Department`, `Role`, `AttendanceRecord`, `LeaveRequest`, `PayrollRecord`, `PerformanceReview` |
| `attendance_dashboard` | `attendance_dashboard_view` | `CAP-ATT-001`, `CAP-ATT-002` | `attendance-service` | `AttendanceRecord`, `Employee` |
| `leave_requests` | `leave_requests_view` | `CAP-LEV-001`, `CAP-LEV-002` | `leave-service` | `LeaveRequest`, `Employee` |
| `payroll_dashboard` | `payroll_summary_view` | `CAP-PAY-001`, `CAP-PAY-002` | `payroll-service` | `PayrollRecord`, `Employee`, `AttendanceRecord`, `LeaveRequest` |
| `job_postings` | `job_posting_directory_view` | `CAP-HIR-001` | `hiring-service` | `JobPosting`, `Department`, `Role` |
| `candidate_pipeline` | `candidate_pipeline_view` | `CAP-HIR-002` | `hiring-service` | `Candidate`, `JobPosting`, `Interview` |
| `performance_reviews` | `performance_review_view` | `CAP-PRF-001` | `employee-service` | `PerformanceReview`, `Employee` |
| `departments` | `organization_structure_view` | `CAP-EMP-001` | `employee-service` | `Department`, `Employee`, `Role` |
| `roles` | `organization_structure_view` | `CAP-EMP-001` | `employee-service` | `Role`, `Employee`, `Department` |
| `settings` | `access_control_view`, `notification_delivery_view` | `CAP-AUT-001`, `CAP-NOT-001`, `CAP-NOT-002` | `auth-service` | `UserAccount`, `RoleBinding`, `PermissionPolicy`, `NotificationTemplate`, `NotificationMessage`, `NotificationPreference` |
| `compliance_dashboard` | `compliance_status_view` | `CAP-COM-001`, `CAP-COM-002` | `compliance-service` | `ComplianceSubmission`, `ComplianceReport`, `ComplianceAuditRecord` |
| `decision_center` | `decision_cards_view` | `CAP-DEC-001`, `CAP-DEC-002` | `decision-service` | `DecisionCard`, `AnomalyRecord` |
| `financial_wellness` | `financial_wellness_view` | `CAP-EWA-001`, `CAP-EWA-002` | `ewa-financial-service` | `EWARequest`, `SalaryAdvance`, `RepaymentSchedule` |
| `banking_disbursement` | `disbursement_status_view`, `reconciliation_view` | `CAP-BNK-001`, `CAP-BNK-002` | `bank-service` | `DisbursementBatch`, `PaymentRecord`, `ReconciliationReport` |
| `analytics_reports` | `analytics_dashboard_view` | `CAP-RPT-001`, `CAP-RPT-002` | `reporting-analytics-service` | `ReportDefinition`, `ReportExecution`, `AnalyticsProjection` |
| `whatsapp_admin` | `whatsapp_session_view`, `whatsapp_conversation_view` | `CAP-WA-001` | `whatsapp-service` | `WhatsAppIdentityMap`, `WhatsAppSession`, `WhatsAppConversationEvent` |
| `expense_claims` | `expense_claims_view` | `CAP-EXP-001` | `expense-service` | `ExpenseClaim`, `ExpenseReceipt` |
| `engagement_surveys` | `engagement_survey_view` | `CAP-ENG-001` | `engagement-service` | `Survey`, `SurveyQuestion`, `SurveyResponse`, `AggregatedSurveyResult` |
| `helpdesk` | `helpdesk_tickets_view`, `helpdesk_sla_view` | `CAP-HLP-001`, `CAP-HLP-002` | `helpdesk-service` | `HelpDeskTicket`, `TicketComment`, `KnowledgeBaseArticle` |
| `automations_admin` | `automation_execution_view` | `CAP-AUT-002`, `CAP-AUT-003` | `automation-service` | `AutomationRule`, `AutomationExecution` |

## Notes
- Each UI surface has at least one mapped read model, capability, and primary owning service.
- Cross-module widgets on `dashboard` compose multiple read models but remain governed by stable capability IDs.
- `decision_center` is the primary surface for the AI Payroll Guardian and human-in-loop review flow.
- WhatsApp is a parallel access channel; `whatsapp_admin` is the administrative surface for identity mapping and audit only.
