# Security Model

## Overview
This document defines role-based access control (RBAC) for SME-HRMS. Permissions are granted to system roles and scoped by resource ownership where applicable.

## Roles

### Admin
- Full system administration access.
- Can manage organization settings, users, roles, and all business records.
- Can view and operate across all departments and employees.

### Manager
- Operational access for team and department management.
- Can manage records for direct reports and assigned department(s).
- Can approve/reject workflow items within managerial authority.

### Employee
- Self-service access for personal profile and personal workflow records.
- Can view only information required for daily HR operations.
- Cannot access cross-employee confidential records except where explicitly exposed (for example, directory basics).

## Permission Matrix

### Legend
- **C**: Create
- **R**: Read
- **U**: Update
- **D**: Delete
- **A**: Approve/Decide
- **\***: Scoped (own record, direct-report record, or assigned department)

| Resource | Admin | Manager | Employee |
|---|---|---|---|
| Employee profile | CRUD | CRU* | R/U* (own) |
| Department | CRUD | R | R |
| Role definitions | CRUD | R | - |
| Attendance records | CRUD | CRUA* | CRU* (own) |
| Leave requests | CRUDA | CRUA* | CRU* (own), submit |
| Payroll records | CRUD | R* (team summary/detail per policy) | R* (own) |
| Performance reviews | CRUDA | CRUA* | R* (own), acknowledge |
| Job postings | CRUD | CRU* | R |
| Candidates | CRUD | CRU* | - |
| Interviews | CRUD | CRU* | - |
| Reports & analytics | Full | R* (team/department) | R* (self metrics only) |
| User & access management | CRUD | - | - |
| Organization settings | CRUD | - | - |
| Audit logs | R | R* (team actions where allowed) | - |

## Scope Rules

1. **Admin scope**: Unrestricted across all entities and departments.
2. **Manager scope**: Limited to direct reports, indirect reports (if enabled), and assigned departments.
3. **Employee scope**: Limited to own records except explicitly shared organizational data (for example department list, job postings).
4. **Sensitive data controls**:
   - Compensation data is restricted to Admin and policy-authorized Managers.
   - Performance feedback visibility is restricted to reviewer chain and reviewed employee.
5. **Approval authority**:
   - Managers may approve leave and performance workflows for in-scope employees.
   - Admin may override approvals with audit justification.

## Enforcement Notes
- Every permission check must evaluate both **role** and **scope**.
- All write operations should be audit-logged with actor, timestamp, previous value, and new value.
- Deny-by-default policy applies where permission is not explicitly granted.
- API and UI authorization must remain consistent to avoid privilege escalation.
