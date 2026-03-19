# Security Model

## Overview
This document defines canonical authentication, authorization, scope enforcement, and data protection rules for SME-HRMS.

## Security principals
- **Admin**: unrestricted tenant-wide HR operations and access administration.
- **Manager**: scoped to assigned department and reporting hierarchy.
- **Employee**: self-service scope plus limited organizational visibility.
- **Recruiter**: scoped hiring operations for assigned requisitions.
- **PayrollAdmin**: payroll administration and disbursement authority.
- **Service**: non-human service principal used for service-to-service calls.

## Capability-to-role authorization

| Capability ID | Capability | Admin | Manager | Employee | Recruiter | PayrollAdmin | Service |
|---|---|---|---|---|---|---|---|
| `CAP-EMP-001` | Employee directory and lifecycle management | Allow | Allow (scoped) | Read (limited) | Deny | Read (limited) | Scoped |
| `CAP-EMP-002` | Employee profile maintenance and org assignment | Allow | Allow (direct/indirect reports) | Update own profile | Deny | Deny | Scoped |
| `CAP-ATT-001` | Attendance capture and monitoring | Allow | Allow (team) | Create/read/update own | Deny | Read | Scoped |
| `CAP-ATT-002` | Attendance validation and period lock | Allow | Allow (team periods) | Deny | Deny | Read | Scoped |
| `CAP-LEV-001` | Leave request lifecycle | Allow | Allow (team) | Create/read/update own | Deny | Read | Scoped |
| `CAP-LEV-002` | Leave decision workflow | Allow | Allow (team approvals) | Deny | Deny | Deny | Scoped |
| `CAP-PAY-001` | Payroll processing and payroll data access | Allow | Read (policy-scoped) | Read own | Deny | Allow | Scoped |
| `CAP-PAY-002` | Payroll disbursement completion | Allow | Deny | Deny | Deny | Allow | Scoped |
| `CAP-HIR-001` | Job posting management | Allow | Allow (department postings) | Read | Allow | Deny | Scoped |
| `CAP-HIR-002` | Candidate pipeline and interview management | Allow | Allow (assigned requisitions) | Deny | Allow | Deny | Scoped |
| `CAP-PRF-001` | Performance review lifecycle | Allow | Allow (team reviews) | Read own | Deny | Deny | Scoped |
| `CAP-AUT-001` | Identity and access administration | Allow | Deny | Deny | Deny | Deny | Scoped |
| `CAP-NOT-001` | Notification template and delivery operations | Allow | Read (team-visible outcomes only) | Read own inbox/preferences | Deny | Read | Scoped |
| `CAP-NOT-002` | Notification preference management | Allow | Manage own + delegated team defaults where allowed | Manage own | Manage own | Manage own | Scoped |

## Module permission coverage

| Module / Resource | Admin | Manager | Employee | Recruiter | PayrollAdmin | Service |
|---|---|---|---|---|---|---|
| Employee / Department / Role | CRUD | CRU (scoped) | R directory, U own profile | R | R limited | scoped API access |
| PerformanceReview | CRU+submit/finalize | CRU+submit/finalize (scoped) | R own | Deny | Deny | scoped API access |
| AttendanceRecord | CRUD | CRUA (scoped) | CRU own | Deny | R | scoped API access |
| LeaveRequest | CRUDA | CRUA (scoped) | CRU own, submit | Deny | R | scoped API access |
| PayrollRecord | CRUD | R policy-scoped | R own | Deny | CRUD | scoped API access |
| JobPosting / Candidate / Interview | CRUD | CRU (scoped) | R job postings only | CRUD scoped | Deny | scoped API access |
| UserAccount / RoleBinding / PermissionPolicy / Session | CRUD | Deny | Manage own session only | Deny | Deny | scoped API access |
| NotificationTemplate / NotificationMessage / DeliveryAttempt | CRUD | R scoped outcomes | R own messages | R assigned requisitions only if surfaced | R payroll-related outcomes | scoped API access |
| NotificationPreference | CRUD | U own | U own | U own | U own | scoped API access |
| Audit logs | Read | Read (scoped) | Deny | Deny | Read (payroll scope) | emit only |

## Scope model

### Scope dimensions
- **Global**: tenant-wide administration.
- **Department**: limited to department-owned employees, postings, and approvals.
- **Employee**: self-service or direct subject access.
- **Requisition**: limited to assigned hiring workload.
- **Service**: machine principal limited to declared upstream/downstream integrations.

### Enforcement rules
1. Authorization is deny-by-default.
2. Access requires both a granted capability and a matching scope.
3. Scope filters must be enforced in API handlers, service methods, and read-model queries.
4. Sensitive attributes such as compensation, password hashes, refresh tokens, and review narratives require least-privilege access.
5. Approval and payout actions require explicit actor identity and audit logging.

## Authentication controls
- Use short-lived access tokens and rotatable refresh tokens.
- Store only hashed refresh tokens and password hashes.
- Require MFA for privileged actors where supported.
- Revoke sessions on credential compromise, employee termination, or admin lock.
- Service principals must use separately managed credentials and non-human scopes.

## Data protection controls
- Encrypt secrets and token material at rest.
- Enforce HTTPS/TLS for all non-local traffic.
- Redact sensitive fields from logs and error responses.
- Retain audit logs for all privileged operations.
- Apply field-level filtering for salary, review notes, and security data in read models and APIs.

## Audit requirements
- Log actor, capability, scope, target entity, timestamp, and before/after values for write operations.
- Log authentication success/failure, session revocation, payroll actions, leave approvals, candidate hire decisions, and notification preference changes.
- Preserve immutable event traceability through `trace_id` correlation.
