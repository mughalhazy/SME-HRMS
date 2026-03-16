# Capability Matrix

Source anchors:
- `docs/canon/domain-model.md`
- `docs/canon/service-map.md`
- `docs/canon/ui-surface-map.md`
- `docs/canon/api-standards.md`

## Capability registry

| Capability ID | Capability Name | Service Owner | Primary Entities | UI Surface(s) | API Endpoint Category |
|---|---|---|---|---|---|
| `CAP-EMP-001` | Employee directory and lifecycle management | `employee-service` | Employee, Department, Role | `dashboard`, `employee_list` | `/employees`, `/departments`, `/roles` |
| `CAP-EMP-002` | Employee profile maintenance and org assignment | `employee-service` | Employee, Department, Role | `employee_profile` | `/employees/{employee_id}` |
| `CAP-ATT-001` | Attendance capture and monitoring | `attendance-service` | AttendanceRecord, Employee | `dashboard`, `attendance_dashboard`, `employee_profile` | `/attendance/records`, `/attendance/summaries` |
| `CAP-ATT-002` | Attendance validation and period lock | `attendance-service` | AttendanceRecord | `attendance_dashboard` | `/attendance/periods/{period_id}/lock` |
| `CAP-LEV-001` | Leave request lifecycle management | `leave-service` | LeaveRequest, Employee | `dashboard`, `leave_requests`, `employee_profile` | `/leave/requests` |
| `CAP-LEV-002` | Leave decision workflow | `leave-service` | LeaveRequest | `leave_requests` | `/leave/requests/{leave_request_id}/approve`, `/reject`, `/submit` |
| `CAP-PAY-001` | Payroll record processing and payroll dashboard | `payroll-service` | PayrollRecord, Employee | `dashboard`, `payroll_dashboard`, `employee_profile` | `/payroll/records`, `/payroll/run` |
| `CAP-PAY-002` | Payroll disbursement completion | `payroll-service` | PayrollRecord | `payroll_dashboard` | `/payroll/records/{payroll_record_id}/mark-paid` |
| `CAP-HIR-001` | Job posting and requisition management | `hiring-service` | JobPosting, Department, Role | `dashboard`, `job_postings` | `/job-postings` |
| `CAP-HIR-002` | Candidate pipeline and interview management | `hiring-service` | Candidate, Interview, JobPosting | `candidate_pipeline`, `dashboard` | `/candidates`, `/interviews` |
| `CAP-PRF-001` | Performance review lifecycle | `employee-service` | PerformanceReview, Employee | `dashboard`, `performance_reviews`, `employee_profile` | `/performance-reviews` |

## Entity coverage check

| Domain Entity | Owning Service | Capabilities |
|---|---|---|
| Employee | `employee-service` | `CAP-EMP-001`, `CAP-EMP-002` |
| Department | `employee-service` | `CAP-EMP-001` |
| Role | `employee-service` | `CAP-EMP-001` |
| AttendanceRecord | `attendance-service` | `CAP-ATT-001`, `CAP-ATT-002` |
| LeaveRequest | `leave-service` | `CAP-LEV-001`, `CAP-LEV-002` |
| PayrollRecord | `payroll-service` | `CAP-PAY-001`, `CAP-PAY-002` |
| JobPosting | `hiring-service` | `CAP-HIR-001`, `CAP-HIR-002` |
| Candidate | `hiring-service` | `CAP-HIR-002` |
| Interview | `hiring-service` | `CAP-HIR-002` |
| PerformanceReview | `employee-service` | `CAP-PRF-001` |
