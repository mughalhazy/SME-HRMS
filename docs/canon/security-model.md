# Security Model

## Overview
This document defines RBAC and capability-level authorization for SME-HRMS.

## Roles
- **Admin**: unrestricted tenant-wide HR operations and access administration.
- **Manager**: scoped to assigned department and reporting hierarchy.
- **Employee**: self-service scope plus limited organizational directory visibility.

## Capability-to-role authorization

| Capability ID | Capability | Admin | Manager | Employee |
|---|---|---|---|---|
| `CAP-EMP-001` | Employee directory and lifecycle management | Allow | Allow (scoped) | Read (limited) |
| `CAP-EMP-002` | Employee profile maintenance | Allow | Allow (direct/indirect reports) | Update own profile |
| `CAP-ATT-001` | Attendance capture and monitoring | Allow | Allow (team) | Create/read/update own |
| `CAP-ATT-002` | Attendance validation and lock | Allow | Allow (team periods) | Deny |
| `CAP-LEV-001` | Leave request lifecycle | Allow | Allow (team) | Create/read/update own |
| `CAP-LEV-002` | Leave decision workflow | Allow | Allow (team approvals) | Deny |
| `CAP-PAY-001` | Payroll processing | Allow | Read (team summary/detail per policy) | Read own |
| `CAP-PAY-002` | Payroll disbursement completion | Allow | Deny (unless delegated) | Deny |
| `CAP-HIR-001` | Job posting management | Allow | Allow (department postings) | Read |
| `CAP-HIR-002` | Candidate pipeline and interviews | Allow | Allow (assigned requisitions) | Deny |
| `CAP-PRF-001` | Performance review lifecycle | Allow | Allow (team reviews) | Read own + acknowledge |

## Module permission coverage

| Module / Resource | Admin | Manager | Employee |
|---|---|---|---|
| Employee / Department / Role | CRUD | CRU (scoped) | R (directory), U (own profile) |
| AttendanceRecord | CRUD | CRUA (scoped) | CRU (own) |
| LeaveRequest | CRUDA | CRUA (scoped) | CRU (own), submit |
| PayrollRecord | CRUD | R (policy scoped) | R (own) |
| JobPosting / Candidate / Interview | CRUD | CRU (scoped) | R (job posting only) |
| PerformanceReview | CRUDA | CRUA (scoped) | R (own), acknowledge |
| User/access administration | CRUD | Deny | Deny |
| Audit logs | Read | Read (scoped) | Deny |

## Enforcement rules
1. Deny-by-default when capability permission is not explicitly granted.
2. Authorization must evaluate both **role** and **scope**.
3. Scope filters must be enforced in API handlers and data queries.
4. All write and approval actions are audit logged with actor, timestamp, and before/after values.
5. Compensation and sensitive review data are never exposed outside permitted scopes.
