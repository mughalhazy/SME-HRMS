# Meridian HCM — API Contracts
## Version: 1.4 | Date: 2026-06-06 (AttendanceSource enum extended 3→6 values — MN-G04)
## Source of truth for all enum display logic and service map
## Rule: Enums defined here are NEVER redefined in page contracts — referenced only

---

## SERVICE MAP

> **Scope note:** This map covers the 17 UI-facing services accessed by Meridian HCM pages. Six backend services are intentionally excluded because they have no direct UI-facing API surface in this project: `compliance-service`, `decision-service`, `bank-service`, `whatsapp-service`, `ewa-financial-service`, `automation-service`. For the full service inventory see `docs/canon/service-map.md`.

> **⚠️ Path divergence:** `reporting_analytics` base path below is `/api/v1/reporting`. However `docs/services/reporting-analytics-service.md` declares `/api/v1/analytics/*` as the actual capability endpoint prefix. H07 page contracts were authored against `/api/v1/reporting`. This inconsistency is unresolved — confirm the live base path before wiring H07 pages to the real API.

| Service | Type | Base Path | Domain |
|---|---|---|---|
| employee-service | TypeScript | `/api/v1/employees` | Employees · Departments · Roles · Org · Contractors |
| settings-service | TypeScript | `/api/v1/settings` | Leave policies · Pay schedules · Attendance rules · Org config |
| auth-service | Python | `/api/v1/auth` | Login · Sessions · Refresh · Me |
| hiring_service | Python | `/api/v1/hiring` | Job postings · Candidates · Pipeline |
| leave_service | Python | `/api/v1/leave` | Leave requests · Policies · Holiday calendars |
| payroll_service | Python | `/api/v1/payroll` | Payroll records · Batches · Cycles · Salary structures |
| performance_service | Python | `/api/v1/performance` | Review cycles · Goals · Feedback · Calibration · PIP |
| attendance_service | Python | `/api/v1/attendance` | Records · Schedules · Rosters · Corrections |
| expense_service | Python | `/api/v1/expenses` | Claims · Categories · Attachments · Reimbursements |
| travel_service | Python | `/api/v1/travel` | Requests · Itineraries |
| helpdesk_service | Python | `/api/v1/helpdesk` | Tickets · Comments · SLA |
| engagement_service | Python | `/api/v1/engagement` | Surveys · Responses · Aggregations |
| workflow_service | Python | `/api/v1/workflow` | Inbox · Approvals · Delegation · Escalation |
| reporting_analytics | Python | `/api/v1/reporting` | Reports · Exports · Schedules |
| search_service | Python | `/api/v1/search` | Employee · Candidate · Document search |
| notification_service | Python | `/api/v1/notifications` | Notifications · Feed |
| integration_service | Python | `/api/v1/integrations` | External connectors |

---

## ENUM DISPLAY LOGIC

### Employee.status
```
Draft      → chip: "Draft"      · colour: amber
Active     → chip: "Active"     · colour: green
OnLeave    → chip: "On Leave"   · colour: blue
Suspended  → chip: "Suspended"  · colour: red
Terminated → chip: "Terminated" · colour: grey
```
Source: `employee-service/employee.model.ts · EMPLOYEE_STATUSES`

### Employee.employment_type
```
FullTime   → "Full Time"
PartTime   → "Part Time"
Contract   → "Contract"
Intern     → "Intern"
```
Source: `employee-service/employee.model.ts · EMPLOYMENT_TYPES`

### Employee.contract_type
```
IndependentContractor → "Independent Contractor"
Agency                → "Agency"
StatementOfWork       → "Statement of Work"
```
Source: `employee-service/employee.model.ts · CONTRACT_TYPES`

### Department.status
```
Proposed → chip: "Proposed" · colour: amber
Active   → chip: "Active"   · colour: green
Inactive → chip: "Inactive" · colour: grey
Archived → chip: "Archived" · colour: grey
```
Source: `employee-service/employee.model.ts · DEPARTMENT_STATUSES`

### Role.status
```
Draft    → chip: "Draft"    · colour: amber
Active   → chip: "Active"   · colour: green
Inactive → chip: "Inactive" · colour: grey
Archived → chip: "Archived" · colour: grey
```
Source: `employee-service/role.model.ts · ROLE_STATUSES`

### Role.employment_category
```
Staff      → "Staff"
Manager    → "Manager"
Executive  → "Executive"
Contractor → "Contractor"
```
Source: `employee-service/role.model.ts · EMPLOYMENT_CATEGORIES`

### OrgEntity.status
```
Draft    → chip: "Draft"    · colour: amber
Active   → chip: "Active"   · colour: green
Inactive → chip: "Inactive" · colour: grey
Archived → chip: "Archived" · colour: grey
```
Source: `employee-service/org.model.ts · ORG_ENTITY_STATUSES`

### Leave.status
```
Draft     → chip: "Draft"     · colour: grey
Submitted → chip: "Pending"   · colour: amber
Approved  → chip: "Approved"  · colour: green
Rejected  → chip: "Rejected"  · colour: red
Cancelled → chip: "Cancelled" · colour: grey
```
Source: `leave_service.py · LeaveStatus`

### Leave.type
```
Annual  → "Annual"
Sick    → "Sick"
Casual  → "Casual"
Unpaid  → "Unpaid"
Other   → "Other"
```
Source: `leave_service.py · LeaveType`

### Payroll.status
```
Draft     → chip: "Draft"     · colour: grey
Processed → chip: "Processed" · colour: blue
Paid      → chip: "Paid"      · colour: green
Cancelled → chip: "Cancelled" · colour: red
```
Source: `payroll_service.py · PayrollStatus`

### PayrollBatch.status
```
Pending        → chip: "Pending"         · colour: amber
Processed      → chip: "Processed"       · colour: blue
PartialFailure → chip: "Partial Failure" · colour: amber
Paid           → chip: "Paid"            · colour: green
Failed         → chip: "Failed"          · colour: red
```
Source: `payroll_service.py · PayrollBatchStatus`

### Attendance.status
```
Present → chip: "Present"  · colour: green
Absent  → chip: "Absent"   · colour: red
Late    → chip: "Late"     · colour: amber
HalfDay → chip: "Half Day" · colour: blue
Holiday → chip: "Holiday"  · colour: grey
```
Source: `attendance_service/models.py · AttendanceStatus`

### Attendance.record_state
```
Captured  → chip: "Captured"  · colour: grey
Validated → chip: "Validated" · colour: blue
Approved  → chip: "Approved"  · colour: green
Locked    → chip: "Locked"    · colour: grey
```
Source: `attendance_service/models.py · RecordState`

### Attendance.source
```
Manual          → "Manual"
Biometric       → "Biometric"
APIImport       → "API Import"
GEO_FENCE       → "Geo-Fence"
FACE_RECOGNITION → "Face Recognition"
MOBILE          → "Mobile"
```
Source: `attendance_service/models.py · AttendanceSource` (GEO_FENCE, FACE_RECOGNITION, MOBILE added MN-G04 Session 5)
Source: `attendance_service/models.py · AttendanceSource`

### Schedule.status
```
Draft     → chip: "Draft"     · colour: grey
Published → chip: "Published" · colour: green
Archived  → chip: "Archived"  · colour: grey
```
Source: `attendance_service/models.py · ScheduleStatus`

### Correction.status
```
Submitted → chip: "Pending"  · colour: amber
Approved  → chip: "Approved" · colour: green
Rejected  → chip: "Rejected" · colour: red
```
Source: `attendance_service/models.py · CorrectionStatus`

### Performance.review_cycle.status
```
Draft          → chip: "Draft"            · colour: grey
Open           → chip: "Open"             · colour: blue
PendingApproval→ chip: "Pending Approval" · colour: amber
Approved       → chip: "Approved"         · colour: green
Closed         → chip: "Closed"           · colour: grey
```
Source: `performance_service.py · status comparisons`

### Goal.status
```
Draft     → chip: "Draft"     · colour: grey
Submitted → chip: "Submitted" · colour: amber
Approved  → chip: "Approved"  · colour: green
```
Source: `performance_service.py · status comparisons`

### Expense.status
```
Draft      → chip: "Draft"      · colour: grey
Submitted  → chip: "Submitted"  · colour: amber
Approved   → chip: "Approved"   · colour: green
Rejected   → chip: "Rejected"   · colour: red
Reimbursed → chip: "Reimbursed" · colour: teal
```
Source: `expense_service.py · status comparisons`

### Travel.status
```
Draft     → chip: "Draft"     · colour: grey
Submitted → chip: "Submitted" · colour: amber
Booked    → chip: "Booked"    · colour: blue
Completed → chip: "Completed" · colour: green
```
Source: `travel_service.py · status comparisons`

### Helpdesk.ticket.status
```
Draft      → chip: "Draft"       · colour: grey
Open       → chip: "Open"        · colour: amber
InProgress → chip: "In Progress" · colour: blue
Resolved   → chip: "Resolved"    · colour: green
Closed     → chip: "Closed"      · colour: grey
```
Source: `helpdesk_service.py · TICKET_STATUSES`
Note: InProgress added v1.2 — confirmed in helpdesk_service.py workflow step; was missing from v1.1.

### Helpdesk.ticket.priority
```
Low    → chip: "Low"    · colour: grey
Medium → chip: "Medium" · colour: amber
High   → chip: "High"   · colour: amber
Urgent → chip: "Urgent" · colour: red
```
Source: `helpdesk_service.py · PRIORITIES`

### Engagement.survey.status
```
Draft  → chip: "Draft"  · colour: amber
Open   → chip: "Open"   · colour: green
Closed → chip: "Closed" · colour: grey
```
Source: `engagement_service.py · SURVEY_STATUSES`

### Engagement.question.kind
```
Likert5 → "Likert 1–5" (only valid value · scale_min:1 · scale_max:5)
```
Source: `engagement_service.py · QUESTION_KINDS`

### Engagement.question.dimension
```
D1 → "Clarity & Direction"
D2 → "Manager Effectiveness"
D3 → "Wellbeing & Balance"
D4 → "Growth & Development"
D5 → "Recognition & Reward"
```
Source: `engagement_service.py · DIMENSIONS`

### Settings.status
```
Draft    → chip: "Draft"    · colour: amber
Active   → chip: "Active"   · colour: green
Archived → chip: "Archived" · colour: grey
```
Source: `settings-service/settings.model.ts · SettingsStatus` — applies to AttendanceRule and LeavePolicy records

### Settings.leave_deduction_mode
```
None     → "None"
Prorated → "Prorated"
FullDay  → "Full Day"
```
Source: `settings-service/settings.model.ts · LeaveDeductionMode`

### Workflow.instance.status
```
Pending   → chip: "Pending"   · colour: amber
Approved  → chip: "Approved"  · colour: green
Rejected  → chip: "Rejected"  · colour: red
Delegated → chip: "Delegated" · colour: blue
Escalated → chip: "Escalated" · colour: amber
Cancelled → chip: "Cancelled" · colour: grey
```
Source: `workflow_service.py · WorkflowInstance.status`

### Hiring.job.status
```
Draft   → chip: "Draft"    · colour: grey
Open    → chip: "Open"     · colour: green
OnHold  → chip: "On Hold"  · colour: amber
Closed  → chip: "Closed"   · colour: grey
Filled  → chip: "Filled"   · colour: teal
```
Source: `services/hiring_service/service.py · JOB_POSTING_STATUSES`

### Hiring.candidate.status
```
Applied      → chip: "Applied"      · colour: grey
Screening    → chip: "Screening"    · colour: blue
Interviewing → chip: "Interviewing" · colour: violet
Offered      → chip: "Offered"      · colour: amber
Hired        → chip: "Hired"        · colour: green
Rejected     → chip: "Rejected"     · colour: red
Withdrawn    → chip: "Withdrawn"    · colour: grey
```
Source: `services/hiring_service/service.py · CANDIDATE_STATUSES`

### Hiring.pipeline.stage
```
Applied    → kanban col · colour: grey   · maps to status: Applied
Screening  → kanban col · colour: blue   · maps to status: Screening
Interview  → kanban col · colour: violet · maps to status: Interviewing
Offer      → kanban col · colour: green  · maps to status: Offered
Hired      → kanban col · colour: teal   · maps to status: Hired
Rejected   → kanban col · colour: red    · maps to status: Rejected
```
Source: `services/hiring_service/service.py · CANONICAL_PIPELINE_STAGES`
Note: "FinalRound" is UI-only (BG-034) — no backend equivalent; rendered as sub-segment of Interview column

### Hiring.interview.status
```
Scheduled → chip: "Scheduled" · colour: blue
Completed → chip: "Completed" · colour: green
Cancelled → chip: "Cancelled" · colour: red
NoShow    → chip: "No Show"   · colour: amber
```
Source: `services/hiring_service/service.py · INTERVIEW_STATUSES`

### Hiring.interview.type
```
PhoneScreen → "Phone Screen"
Technical   → "Technical"
Behavioral  → "Behavioral"
Panel       → "Panel"
Final       → "Final"
```
Source: `services/hiring_service/service.py · INTERVIEW_TYPES`

### Hiring.offer.status
```
Draft           → chip: "Draft"            · colour: grey
PendingApproval → chip: "Pending Approval" · colour: amber
Approved        → chip: "Approved"         · colour: green
Sent            → chip: "Sent"             · colour: blue
Accepted        → chip: "Accepted"         · colour: green
Declined        → chip: "Declined"         · colour: red
Cancelled       → chip: "Cancelled"        · colour: grey
```
Source: `services/hiring_service/service.py · OFFER_STATUSES`

### Hiring.candidate.source
```
Referral   → "Referral"
JobBoard   → "Job Board"
CareerSite → "Career Site"
Agency     → "Agency"
LinkedIn   → "LinkedIn"
Other      → "Other"
```
Source: `services/hiring_service/service.py · CANDIDATE_SOURCES`

### Hiring.recommendation
```
StrongHire → chip: "Strong Hire" · colour: green
Hire       → chip: "Hire"        · colour: green
NoHire     → chip: "No Hire"     · colour: red
Undecided  → chip: "Undecided"   · colour: amber
```
Source: `services/hiring_service/service.py · RECOMMENDATIONS`

### Hiring.employment.type
```
FullTime → "Full Time"
PartTime → "Part Time"
Contract → "Contract"
Intern   → "Intern"
```
Source: `services/hiring_service/service.py · EMPLOYMENT_TYPES`

### Compensation.band.status
```
Draft    → chip: "Draft"    · colour: grey
Active   → chip: "Active"   · colour: green
Inactive → chip: "Inactive" · colour: grey
Archived → chip: "Archived" · colour: grey
```
Source: `employee-service/compensation.model.ts · COMPENSATION_BAND_STATUSES`

### Compensation.salary_revision.status
```
Draft     → chip: "Draft"     · colour: grey
Approved  → chip: "Approved"  · colour: green
Superseded→ chip: "Superseded"· colour: grey
```
Source: `employee-service/compensation.model.ts · SALARY_REVISION_STATUSES`

### Benefits.plan.type
```
Health     → "Health"
Retirement → "Retirement"
Insurance  → "Insurance"
Wellness   → "Wellness"
Other      → "Other"
```
Source: `employee-service/compensation.model.ts · BENEFITS_PLAN_TYPES`

### Benefits.enrollment.status
```
Pending   → chip: "Pending"   · colour: amber
Active    → chip: "Active"    · colour: green
Cancelled → chip: "Cancelled" · colour: red
Ended     → chip: "Ended"     · colour: grey
```
Source: `employee-service/compensation.model.ts · BENEFITS_ENROLLMENT_STATUSES`

### Settings.pay_schedule
```
Weekly      → "Weekly"
BiWeekly    → "Bi-Weekly"
SemiMonthly → "Semi-Monthly"
Monthly     → "Monthly"
```
Source: `settings-service/settings.model.ts · PAY_SCHEDULES`

### Settings.leave_policy.type
```
Annual   → "Annual"
Sick     → "Sick"
Casual   → "Casual"
Unpaid   → "Unpaid"
Parental → "Parental"
Other    → "Other"
```
Source: `settings-service/settings.model.ts · LEAVE_POLICY_TYPES`

### Reporting.relationship.type
```
Primary → "Primary"
Matrix  → "Matrix"
```
Source: `employee-service/org.model.ts · REPORTING_RELATIONSHIP_TYPES`

---

### Document.status
```
Draft    → chip: "Draft"    · colour: grey
Active   → chip: "Active"   · colour: green
Archived → chip: "Archived" · colour: grey
Expired  → chip: "Expired"  · colour: red
```
Source: `employee-service/document-compliance.model.ts · DOCUMENT_STATUSES`

### Document.document_type
```
Contract       → "Contract"
Policy         → "Policy"
Certification  → "Certification"
License        → "License"
Identification → "Identification"
Training       → "Training"
Other          → "Other"
```
Source: `employee-service/document-compliance.model.ts · DOCUMENT_TYPES`

### Document.contract_kind
```
Employment → "Employment"
Amendment  → "Amendment"
NDA        → "NDA"
Consulting → "Consulting"
Other      → "Other"
```
Source: `employee-service/document-compliance.model.ts · CONTRACT_KINDS`

### ComplianceTask.task_type
```
DocumentExpiry           → "Document Expiry"
PolicyAcknowledgement    → "Policy Acknowledgement"
CertificationRenewal     → "Certification Renewal"
ManualReview             → "Manual Review"
```
Source: `employee-service/document-compliance.model.ts · COMPLIANCE_TASK_TYPES`

### ComplianceTask.status
```
Open       → chip: "Open"        · colour: amber
InProgress → chip: "In Progress" · colour: blue
Completed  → chip: "Completed"   · colour: green
Overdue    → chip: "Overdue"     · colour: red
Cancelled  → chip: "Cancelled"   · colour: grey
```
Source: `employee-service/document-compliance.model.ts · COMPLIANCE_TASK_STATUSES`

---

## CHIP COLOUR SYSTEM (design-language.html)

```
green  → Active · Approved · Paid · Present · Resolved · Published
amber  → Draft · Pending · Submitted · Late · On Hold · Scheduled · Warning
red    → Terminated · Rejected · Failed · Absent · Closed (urgent)
blue   → OnLeave · Processed · Booked · Interviewing · Validated
teal   → Reimbursed · AI-surfaced states
grey   → Inactive · Archived · Cancelled · Closed · Locked · Superseded
```

Rule: Colour encodes meaning, never decoration. Never use red for AI states.
