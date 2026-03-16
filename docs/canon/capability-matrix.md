# Capability Matrix

> Source anchors: `docs/canon/domain-model.md` and `docs/canon/service-map.md`.
> Note: `docs/canon/service-map.md` was not present in the repository at generation time, so this matrix is derived from the domain model entities and relationships.

## Purpose

This matrix maps each HRMS module to:
- Core business capabilities
- Primary domain entities
- Key upstream/downstream dependencies

---

## Module Capability Matrix

| Module | Core Capabilities | Primary Entities | Upstream Inputs | Downstream Outputs / Integrations |
|---|---|---|---|---|
| `employee_management` | Employee profile lifecycle (create/update/status transitions), organizational assignment (department/role/manager), directory and reporting hierarchy management | Employee, Department, Role | Hiring outcomes (new hire conversion), org structure definitions | Attendance, Leave, Payroll, and Performance processes consume active employee master data |
| `attendance_management` | Daily attendance capture (check-in/out), attendance validation and approval, period locking for payroll readiness | AttendanceRecord, Employee | Employee master data, attendance source events (manual/biometric/API import) | Approved/locked time data contributes to payroll calculations and operational attendance reporting |
| `leave_management` | Leave request submission workflow, manager approval/rejection workflow, leave status tracking and scheduling | LeaveRequest, Employee | Employee master data, approver hierarchy (manager/approver employee) | Approved leave affects employee availability and can influence payroll deductions/entitlements |
| `payroll_management` | Pay-period payroll calculation (gross/net), earning and deduction consolidation, payroll processing and disbursement state tracking | PayrollRecord, Employee | Employee master data, approved attendance summaries, approved leave impacts | Processed/paid payroll records for finance disbursement, employee payslip/reporting outputs |
| `hiring_management` | Job posting and vacancy planning, candidate application pipeline management, interview progression, candidate-to-employee conversion | JobPosting, Candidate, Interview (relationship-level), Department, Role, Employee (conversion target) | Department/role demand signals, hiring approvals | New employee creation in employee management; staffing pipeline and hiring analytics |
| `performance_management` | Review cycle administration, review subject assignment, performance outcome recording and progression tracking | PerformanceReview, Employee | Employee master data, reviewer/manager relationships | Performance outcomes for talent decisions (promotion, compensation input, development plans) |

---

## Capability Coverage by Domain Entity

| Domain Entity | employee_management | attendance_management | leave_management | payroll_management | hiring_management | performance_management |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Employee | ✅ Primary | ✅ Reference | ✅ Reference | ✅ Reference | ✅ Conversion Target | ✅ Reference/Subject |
| Department | ✅ Primary | — | — | — | ✅ Reference | — |
| Role | ✅ Primary | — | — | — | ✅ Reference | — |
| AttendanceRecord | — | ✅ Primary | — | ✅ Input | — | — |
| LeaveRequest | — | — | ✅ Primary | ✅ Input | — | — |
| PayrollRecord | — | — | — | ✅ Primary | — | — |
| JobPosting | — | — | — | — | ✅ Primary | — |
| Candidate | — | — | — | — | ✅ Primary | — |
| Interview | — | — | — | — | ✅ Primary Process Artifact | — |
| PerformanceReview | — | — | — | — | — | ✅ Primary |

---

## Notes and Assumptions

1. `Interview` and `PerformanceReview` are referenced by relationships in the domain model narrative but are not fully specified as standalone entity sections; they are treated here as module-owned artifacts.
2. `hiring_management` is modeled as the producer of `Employee` onboarding handoff (candidate hired -> employee record creation).
3. `payroll_management` depends on approved attendance and leave outcomes, consistent with record lifecycle states and HR process norms.
4. `performance_management` is anchored on `PerformanceReview` references from `Employee` relationships and assumed review workflows.
