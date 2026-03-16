# Domain Model

## Employee

### Description
Represents a person employed by the organization, including identity, organizational placement, and employment metadata.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| employee_id | UUID | Yes | Primary identifier. |
| employee_number | String | Yes | Human-readable unique employee code. |
| first_name | String | Yes | Legal or preferred first name. |
| last_name | String | Yes | Legal or preferred last name. |
| email | String | Yes | Work email; unique. |
| phone | String | No | Contact number. |
| hire_date | Date | Yes | Employment start date. |
| employment_type | Enum | Yes | FullTime, PartTime, Contract, Intern. |
| status | Enum | Yes | Draft, Active, OnLeave, Suspended, Terminated. |
| department_id | UUID | Yes | Foreign key to Department. |
| role_id | UUID | Yes | Foreign key to Role. |
| manager_employee_id | UUID | No | Self-reference to manager Employee. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one **Department** (`department_id`).
- Assigned one **Role** (`role_id`).
- May report to one manager **Employee** (`manager_employee_id`).
- Has many **AttendanceRecord** entries.
- Has many **LeaveRequest** entries.
- Has many **PayrollRecord** entries.
- Has many **PerformanceReview** entries (as review subject).

### Lifecycle States
- **Draft**: Profile initiated but not yet fully onboarded.
- **Active**: Currently employed and operational.
- **OnLeave**: Temporarily inactive due to approved leave.
- **Suspended**: Temporarily restricted pending action.
- **Terminated**: Employment ended.

## Department

### Description
Represents an organizational unit used for grouping employees, budgeting, and reporting.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| department_id | UUID | Yes | Primary identifier. |
| name | String | Yes | Department name; unique within organization. |
| code | String | Yes | Short unique code. |
| description | Text | No | Department purpose/details. |
| head_employee_id | UUID | No | Employee leading the department. |
| status | Enum | Yes | Proposed, Active, Inactive, Archived. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Has many **Employee** members.
- May be led by one **Employee** (`head_employee_id`).
- Has many **JobPosting** entries.

### Lifecycle States
- **Proposed**: Department definition initiated.
- **Active**: Department in operation.
- **Inactive**: Temporarily not operating.
- **Archived**: Closed and retained for history.

## Role

### Description
Represents a job role definition with title, level, and organizational permissions context.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| role_id | UUID | Yes | Primary identifier. |
| title | String | Yes | Role title. |
| level | String | No | Grade/band designation. |
| description | Text | No | Role responsibilities summary. |
| employment_category | Enum | Yes | Staff, Manager, Executive, Contractor. |
| status | Enum | Yes | Active, Inactive, Archived. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Assigned to many **Employee** records.
- Referenced by **JobPosting** as target role profile.

### Lifecycle States
- **Draft**: Role being designed.
- **Active**: Role available for assignment.
- **Inactive**: Role paused for new assignments.
- **Archived**: Role retired from use.

## AttendanceRecord

### Description
Represents employee attendance and time tracking entries for workdays/shifts.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| attendance_id | UUID | Yes | Primary identifier. |
| employee_id | UUID | Yes | Foreign key to Employee. |
| attendance_date | Date | Yes | Date of attendance. |
| check_in_time | DateTime | No | Actual check-in timestamp. |
| check_out_time | DateTime | No | Actual check-out timestamp. |
| total_hours | Decimal(5,2) | No | Calculated worked hours. |
| attendance_status | Enum | Yes | Present, Absent, Late, HalfDay, Holiday. |
| source | Enum | No | Manual, Biometric, APIImport. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one **Employee** (`employee_id`).

### Lifecycle States
- **Captured**: Initial attendance event recorded.
- **Validated**: Data verified against policy/rules.
- **Approved**: Accepted for payroll/time reports.
- **Locked**: Finalized and non-editable for period closure.

## LeaveRequest

### Description
Represents an employee’s request for leave with approval workflow and leave balance implications.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| leave_request_id | UUID | Yes | Primary identifier. |
| employee_id | UUID | Yes | Foreign key to Employee. |
| leave_type | Enum | Yes | Annual, Sick, Casual, Unpaid, Other. |
| start_date | Date | Yes | Requested leave start date. |
| end_date | Date | Yes | Requested leave end date. |
| total_days | Decimal(4,1) | Yes | Derived leave duration. |
| reason | Text | No | Employee justification. |
| approver_employee_id | UUID | No | Employee who approves/rejects. |
| status | Enum | Yes | Draft, Submitted, Approved, Rejected, Cancelled. |
| submitted_at | DateTime | No | Submission timestamp. |
| decision_at | DateTime | No | Approval/rejection timestamp. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one **Employee** (`employee_id`).
- May reference one approver **Employee** (`approver_employee_id`).

### Lifecycle States
- **Draft**: Request being prepared.
- **Submitted**: Awaiting review.
- **Approved**: Accepted and scheduled.
- **Rejected**: Denied by approver.
- **Cancelled**: Withdrawn by employee or admin.

## PayrollRecord

### Description
Represents payroll outcomes for an employee for a given pay period.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| payroll_record_id | UUID | Yes | Primary identifier. |
| employee_id | UUID | Yes | Foreign key to Employee. |
| pay_period_start | Date | Yes | Payroll period start date. |
| pay_period_end | Date | Yes | Payroll period end date. |
| base_salary | Decimal(12,2) | Yes | Fixed salary component. |
| allowances | Decimal(12,2) | No | Additional earnings. |
| deductions | Decimal(12,2) | No | Deductions/taxes/benefits. |
| overtime_pay | Decimal(12,2) | No | Overtime earnings. |
| gross_pay | Decimal(12,2) | Yes | Calculated gross amount. |
| net_pay | Decimal(12,2) | Yes | Final payout amount. |
| currency | String | Yes | ISO currency code. |
| payment_date | Date | No | Actual disbursement date. |
| status | Enum | Yes | Draft, Processed, Paid, Cancelled. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one **Employee** (`employee_id`).

### Lifecycle States
- **Draft**: Record created and editable.
- **Processed**: Payroll calculations completed.
- **Paid**: Disbursement completed.
- **Cancelled**: Invalidated or reversed.

## JobPosting

### Description
Represents an open or planned vacancy published for recruitment.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| job_posting_id | UUID | Yes | Primary identifier. |
| title | String | Yes | Posting title. |
| department_id | UUID | Yes | Target hiring department. |
| role_id | UUID | No | Optional link to standard Role. |
| employment_type | Enum | Yes | FullTime, PartTime, Contract, Intern. |
| location | String | No | Work location. |
| description | Text | Yes | Responsibilities and requirements. |
| openings_count | Integer | Yes | Number of vacancies. |
| posting_date | Date | Yes | Public posting date. |
| closing_date | Date | No | Closing date for applications. |
| status | Enum | Yes | Draft, Open, OnHold, Closed, Filled. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one **Department** (`department_id`).
- May reference one **Role** (`role_id`).
- Has many **Candidate** applications.
- Has many **Interview** schedules via candidates.

### Lifecycle States
- **Draft**: Posting being prepared.
- **Open**: Accepting applications.
- **OnHold**: Temporarily paused.
- **Closed**: No longer accepting applications.
- **Filled**: Hiring completed.

## Candidate

### Description
Represents a person applying for a job posting and progressing through recruitment stages.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| candidate_id | UUID | Yes | Primary identifier. |
| job_posting_id | UUID | Yes | Applied job posting. |
| first_name | String | Yes | Candidate first name. |
| last_name | String | Yes | Candidate last name. |
| email | String | Yes | Candidate email; unique per posting recommended. |
| phone | String | No | Contact number. |
| resume_url | String | No | Link/path to resume artifact. |
| source | Enum | No | Referral, JobBoard, CareerSite, Agency, Other. |
| application_date | Date | Yes | Date of application submission. |
| status | Enum | Yes | Applied, Screening, Interviewing, Offered, Hired, Rejected, Withdrawn. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one **JobPosting** (`job_posting_id`).
- Has many **Interview** entries.
- May convert to one **Employee** upon hire.

### Lifecycle States
- **Applied**: Initial application submitted.
- **Screening**: Under recruiter/hiring manager review.
- **Interviewing**: In active interview process.
- **Offered**: Offer extended.
- **Hired**: Candidate accepted and converted.
- **Rejected**: Application rejected.
- **Withdrawn**: Candidate withdrew.

## Interview

### Description
Represents a scheduled interview interaction between candidate and interview panel.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| interview_id | UUID | Yes | Primary identifier. |
| candidate_id | UUID | Yes | Foreign key to Candidate. |
| interview_type | Enum | Yes | PhoneScreen, Technical, Behavioral, Panel, Final. |
| scheduled_start | DateTime | Yes | Planned start timestamp. |
| scheduled_end | DateTime | Yes | Planned end timestamp. |
| location_or_link | String | No | Onsite location or virtual meeting link. |
| interviewer_employee_ids | UUID[] | No | Employee participants. |
| feedback_summary | Text | No | Consolidated panel feedback. |
| recommendation | Enum | No | StrongHire, Hire, NoHire, Undecided. |
| status | Enum | Yes | Scheduled, Completed, Cancelled, NoShow. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one **Candidate** (`candidate_id`).
- May involve multiple interviewer **Employee** records (`interviewer_employee_ids`).

### Lifecycle States
- **Scheduled**: Planned and communicated.
- **Completed**: Conducted and feedback captured.
- **Cancelled**: Cancelled before completion.
- **NoShow**: Candidate or panel did not attend.

## PerformanceReview

### Description
Represents a formal performance evaluation cycle for an employee.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| performance_review_id | UUID | Yes | Primary identifier. |
| employee_id | UUID | Yes | Employee being reviewed. |
| reviewer_employee_id | UUID | Yes | Employee conducting review. |
| review_period_start | Date | Yes | Period start date. |
| review_period_end | Date | Yes | Period end date. |
| overall_rating | Decimal(2,1) | No | Final numeric score (e.g., 1.0-5.0). |
| strengths | Text | No | Positive performance highlights. |
| improvement_areas | Text | No | Development opportunities. |
| goals_next_period | Text | No | Agreed future goals. |
| status | Enum | Yes | Draft, Submitted, Acknowledged, Finalized. |
| submitted_at | DateTime | No | Reviewer submission timestamp. |
| acknowledged_at | DateTime | No | Employee acknowledgment timestamp. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one reviewed **Employee** (`employee_id`).
- Belongs to one reviewer **Employee** (`reviewer_employee_id`).

### Lifecycle States
- **Draft**: Evaluation in progress.
- **Submitted**: Reviewer submitted assessment.
- **Acknowledged**: Reviewed employee acknowledged.
- **Finalized**: Locked and closed for cycle.
