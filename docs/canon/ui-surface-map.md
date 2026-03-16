# UI Surface Map

This document maps core HRMS UI screens to their primary domain entities, key data surfaces, user actions, and workflow transitions.

## dashboard

### Purpose
Provide an at-a-glance operational summary across workforce, attendance, leave, payroll, hiring, and performance.

### Primary domain entities
- Employee
- AttendanceRecord
- LeaveRequest
- PayrollRecord
- JobPosting
- Candidate
- PerformanceReview

### Key data surfaces
- Headcount by employee status (Active, OnLeave, Suspended).
- Attendance snapshot (present/absent/late today).
- Leave queue summary (Submitted, Approved, Rejected).
- Payroll cycle status (Draft, Processed, Paid).
- Open roles and pipeline volume.
- Pending or in-progress performance reviews.

### Common user actions
- Filter by period and department.
- Navigate to detailed module dashboards.
- Open “needs attention” queues (e.g., pending approvals).

---

## employee_list

### Purpose
List, search, and manage employee directory records.

### Primary domain entities
- Employee
- Department
- Role

### Key data surfaces
- Employee identity (name, employee number, email).
- Organizational assignment (department, role, manager).
- Employment metadata (employment type, hire date, status).

### Common user actions
- Search/filter by status, department, role, manager.
- Open employee profile.
- Create employee record.
- Update status (e.g., Active, OnLeave, Terminated).

---

## employee_profile

### Purpose
Display and maintain a single employee’s detailed information and related records.

### Primary domain entities
- Employee
- Department
- Role
- AttendanceRecord
- LeaveRequest
- PayrollRecord
- PerformanceReview

### Key data surfaces
- Core profile and contact details.
- Reporting line and organizational placement.
- Attendance history and trends.
- Leave history and current balances/requests.
- Payroll history by pay period.
- Performance review timeline and outcomes.

### Common user actions
- Edit employee details.
- Reassign department, role, or manager.
- View linked attendance, leave, payroll, and performance records.
- Trigger profile lifecycle transitions (e.g., Active → OnLeave/Terminated).

---

## attendance_dashboard

### Purpose
Monitor attendance compliance and exceptions for a selected period.

### Primary domain entities
- AttendanceRecord
- Employee

### Key data surfaces
- Daily/period attendance totals.
- Exceptions (Absent, Late, HalfDay) by team/department.
- Check-in/check-out completeness.
- Record source distribution (Manual, Biometric, APIImport).

### Common user actions
- Filter by date range, department, status.
- Drill into individual employee attendance logs.
- Validate/approve attendance records.
- Lock records for period closure.

---

## leave_requests

### Purpose
Manage leave submission and approval workflow.

### Primary domain entities
- LeaveRequest
- Employee

### Key data surfaces
- Requester and approver context.
- Leave type, date range, total days, reason.
- Queue segmented by status (Draft, Submitted, Approved, Rejected, Cancelled).
- Submission and decision timestamps.

### Common user actions
- Submit new leave request.
- Approve/reject/cancel request.
- Filter and sort queue by status, date, department.
- Open employee profile for context.

---

## payroll_dashboard

### Purpose
Track payroll processing status and pay outcomes by period.

### Primary domain entities
- PayrollRecord
- Employee
- AttendanceRecord
- LeaveRequest

### Key data surfaces
- Payroll period summary (record count, gross/net totals).
- Status pipeline (Draft, Processed, Paid, Cancelled).
- Compensation breakdown (base, allowances, deductions, overtime).
- Payment date and currency context.

### Common user actions
- Filter by pay period and status.
- Open employee payroll details.
- Move records through processing lifecycle.
- Export payroll outputs for downstream systems.

---

## job_postings

### Purpose
Create and manage hiring requisitions and their publication lifecycle.

### Primary domain entities
- JobPosting
- Department
- Role

### Key data surfaces
- Posting identity (title, department, employment type, location).
- Vacancy details (openings count, posting/closing dates).
- Posting status (Draft, Open, OnHold, Closed, Filled).
- Candidate volume per posting.

### Common user actions
- Create/edit posting.
- Open/hold/close/fill posting.
- Navigate to associated candidate pipeline.

---

## candidate_pipeline

### Purpose
Track candidates through recruitment stages for one or more postings.

### Primary domain entities
- Candidate
- JobPosting
- Interview

### Key data surfaces
- Candidate stage distribution (Applied → Screening → Interviewing → Offered → Hired).
- Candidate profile and source.
- Interview schedule, feedback, recommendation, and status.
- Conversion/rejection/withdrawal outcomes.

### Common user actions
- Advance or regress candidate stage.
- Schedule/reschedule/cancel interviews.
- Capture interviewer feedback and recommendation.
- Convert hired candidate into employee onboarding flow.

---

## performance_reviews

### Purpose
Manage performance evaluation cycles and completion progress.

### Primary domain entities
- PerformanceReview
- Employee

### Key data surfaces
- Review cycle scope (period, reviewer, employee).
- Status queue (Draft, Submitted, Acknowledged, Finalized).
- Ratings and narrative sections (strengths, improvement areas, goals).
- Submission and acknowledgment timestamps.

### Common user actions
- Create and edit review drafts.
- Submit review for acknowledgment.
- Acknowledge and finalize reviews.
- Filter by cycle, department, reviewer, and status.
