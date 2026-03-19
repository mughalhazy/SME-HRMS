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
| `CAP-HIR-001` | Job posting and requisition management | `hiring-service` | `JobPosting`, `Department`, `Role` | `job_posting_directory_view` | `/api/v1/hiring/job-postings` |
| `CAP-HIR-002` | Candidate pipeline and interview management | `hiring-service` | `Candidate`, `Interview`, `JobPosting` | `candidate_pipeline_view` | `/api/v1/hiring/candidates`, `/api/v1/hiring/interviews` |
| `CAP-PRF-001` | Performance review lifecycle | `employee-service` | `PerformanceReview`, `Employee` | `performance_review_view` | `/api/v1/performance-reviews` |
| `CAP-AUT-001` | Identity and access administration | `auth-service` | `UserAccount`, `RoleBinding`, `PermissionPolicy`, `Session`, `RefreshToken` | `access_control_view` | `/api/v1/auth` |
| `CAP-NOT-001` | Notification template and delivery operations | `notification-service` | `NotificationTemplate`, `NotificationMessage`, `DeliveryAttempt` | `notification_delivery_view` | `/api/v1/notifications/send`, `/api/v1/notifications/templates`, `/api/v1/notifications/messages/{message_id}` |
| `CAP-NOT-002` | Notification preference management | `notification-service` | `NotificationPreference` | `notification_delivery_view` | `/api/v1/notifications/preferences/{subject_id}` |

## Entity coverage check

| Domain Entity | Owning Service | Capabilities |
|---|---|---|
| `Employee` | `employee-service` | `CAP-EMP-001`, `CAP-EMP-002` |
| `Department` | `employee-service` | `CAP-EMP-001`, `CAP-HIR-001` |
| `Role` | `employee-service` | `CAP-EMP-001`, `CAP-HIR-001` |
| `PerformanceReview` | `employee-service` | `CAP-PRF-001` |
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
| `employee-service` | `CAP-EMP-001`, `CAP-EMP-002`, `CAP-PRF-001` |
| `attendance-service` | `CAP-ATT-001`, `CAP-ATT-002` |
| `leave-service` | `CAP-LEV-001`, `CAP-LEV-002` |
| `payroll-service` | `CAP-PAY-001`, `CAP-PAY-002` |
| `hiring-service` | `CAP-HIR-001`, `CAP-HIR-002` |
| `auth-service` | `CAP-AUT-001` |
| `notification-service` | `CAP-NOT-001`, `CAP-NOT-002` |
