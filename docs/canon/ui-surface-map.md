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

## Notes
- Each current UI surface has at least one mapped read model, capability, and primary owning service.
- Cross-module widgets on `dashboard` compose multiple read models but remain governed by stable capability IDs.
