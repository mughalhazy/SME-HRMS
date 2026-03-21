# Domain Model

This document defines the canonical backend domain for SME-HRMS and aligns entity ownership, lifecycle states, relationships, and cross-service references with the current repository service topology.

## Service ownership summary

| Service | Canonical entities |
|---|---|
| `employee-service` | `Employee`, `Department`, `BusinessUnit`, `LegalEntity`, `Location`, `CostCenter`, `GradeBand`, `JobPosition`, `Role`, `PerformanceReview` |
| `attendance-service` | `AttendanceRecord` |
| `leave-service` | `LeaveRequest` |
| `payroll-service` | `PayrollRecord` |
| `hiring-service` | `JobPosting`, `Candidate`, `Interview` |
| `auth-service` | `UserAccount`, `RoleBinding`, `PermissionPolicy`, `Session`, `RefreshToken` |
| `notification-service` | `NotificationTemplate`, `NotificationMessage`, `DeliveryAttempt`, `NotificationPreference` |
| `integration-service` | `WebhookEndpoint`, `WebhookDelivery`, `WebhookDeliveryAttempt` |
| `settings-service` | `AttendanceRule`, `LeavePolicy`, `PayrollSettings` |

## Cross-entity rules

- All primary identifiers use `UUID` values.
- Operational timestamps use UTC `DateTime` values.
- Business-effective dates use `Date` values.
- Entity state transitions are evented; every workflow state change must publish a matching domain event listed in `docs/canon/event-catalog.md`.
- Cross-service references are by identifier and resolved through APIs or projections, never direct database joins across service boundaries.
- Deletion is logical or policy-governed archival for master data; historical records are retained for auditability.

## Employee

### Owning service
- `employee-service`

### Description
Represents a person employed by the organization, including identity, reporting line, and employment status.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| employee_id | UUID | Yes | Primary identifier. |
| employee_number | String | Yes | Human-readable unique employee code. |
| first_name | String | Yes | Legal or preferred given name. |
| last_name | String | Yes | Legal or preferred family name. |
| email | String | Yes | Work email; unique. |
| phone | String | No | Contact number. |
| hire_date | Date | Yes | Effective employment start date. |
| employment_type | Enum | Yes | `FullTime`, `PartTime`, `Contract`, `Intern`. |
| status | Enum | Yes | `Draft`, `Active`, `OnLeave`, `Suspended`, `Terminated`. |
| department_id | UUID | Yes | Foreign key to `Department`. |
| role_id | UUID | Yes | Foreign key to `Role`. |
| manager_employee_id | UUID | No | Self-reference to primary manager `Employee`. |
| business_unit_id | UUID | No | Foreign key to `BusinessUnit`. |
| legal_entity_id | UUID | No | Foreign key to `LegalEntity`. |
| location_id | UUID | No | Foreign key to `Location`. |
| cost_center_id | UUID | No | Primary foreign key to `CostCenter`. |
| job_position_id | UUID | No | Foreign key to `JobPosition`. |
| grade_band_id | UUID | No | Foreign key to `GradeBand`. |
| matrix_manager_employee_ids | UUID[] | No | Matrix-reporting managers for cross-functional accountability. |
| cost_allocations | Object[] | No | Cost-center allocation split that should total 100 percent. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one `Department`.
- Is assigned one `Role`.
- May report to one primary manager `Employee`.
- May have many matrix-reporting managers through reporting-line assignments.
- Belongs to one `BusinessUnit`, `LegalEntity`, and `Location` where assigned.
- May be mapped to one `JobPosition`, one `GradeBand`, and one primary `CostCenter`, with optional split cost allocations.
- Has many `AttendanceRecord` entries.
- Has many `LeaveRequest` entries.
- Has many `PayrollRecord` entries.
- Has many `PerformanceReview` entries as review subject.
- May have one linked `UserAccount`.

### Lifecycle states
- `Draft`: onboarding record created but not yet activated.
- `Active`: actively employed and eligible for operational workflows.
- `OnLeave`: temporarily inactive due to approved leave.
- `Suspended`: temporarily restricted pending HR action.
- `Terminated`: employment ended; historical records retained.

## BusinessUnit

### Owning service
- `employee-service`

### Description
Represents an enterprise business unit used to group departments, legal entities, cost centers, and leadership accountability.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| business_unit_id | UUID | Yes | Primary identifier. |
| name | String | Yes | Unique business-unit name. |
| code | String | Yes | Unique business-unit code. |
| description | Text | No | Optional description. |
| parent_business_unit_id | UUID | No | Self-reference for hierarchical grouping. |
| leader_employee_id | UUID | No | Employee leader for the business unit. |
| status | Enum | Yes | `Draft`, `Active`, `Inactive`, `Archived`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

## LegalEntity

### Owning service
- `employee-service`

### Description
Represents a legal employer/payroll entity aligned to a business unit.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| legal_entity_id | UUID | Yes | Primary identifier. |
| name | String | Yes | Legal-entity name. |
| code | String | Yes | Unique code. |
| registration_number | String | No | Registration / incorporation reference. |
| tax_identifier | String | No | Tax identifier or employer reference. |
| business_unit_id | UUID | No | Foreign key to `BusinessUnit`. |
| status | Enum | Yes | `Draft`, `Active`, `Inactive`, `Archived`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

## Location

### Owning service
- `employee-service`

### Description
Represents a physical or administrative work location tied to a legal entity.

## CostCenter

### Owning service
- `employee-service`

### Description
Represents finance-facing allocation structures used for workforce costing and downstream payroll/reporting.

## GradeBand

### Owning service
- `employee-service`

### Description
Represents the grade/band framework used to normalize job levels and compensation bands.

## JobPosition

### Owning service
- `employee-service`

### Description
Represents an approved organizational position that anchors department assignment, reporting chains, and grade mapping.

## Department

### Owning service
- `employee-service`

### Description
Represents an organizational unit used for employee assignment, reporting, and requisition ownership.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| department_id | UUID | Yes | Primary identifier. |
| name | String | Yes | Unique department name. |
| code | String | Yes | Unique department code. |
| description | Text | No | Department purpose/details. |
| head_employee_id | UUID | No | Employee leading the department. |
| status | Enum | Yes | `Proposed`, `Active`, `Inactive`, `Archived`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Has many `Employee` members.
- May be led by one `Employee`.
- Has many `JobPosting` requisitions.

### Lifecycle states
- `Proposed`
- `Active`
- `Inactive`
- `Archived`

## Role

### Owning service
- `employee-service`

### Description
Represents a standardized job role definition used for employee assignment and hiring alignment.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| role_id | UUID | Yes | Primary identifier. |
| title | String | Yes | Role title. |
| level | String | No | Grade/band designation. |
| description | Text | No | Role responsibilities summary. |
| employment_category | Enum | Yes | `Staff`, `Manager`, `Executive`, `Contractor`. |
| status | Enum | Yes | `Draft`, `Active`, `Inactive`, `Archived`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Assigned to many `Employee` records.
- Referenced by many `JobPosting` records.

### Lifecycle states
- `Draft`
- `Active`
- `Inactive`
- `Archived`

## PerformanceReview

### Owning service
- `employee-service`

### Description
Represents a structured performance assessment for a review cycle.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| performance_review_id | UUID | Yes | Primary identifier. |
| employee_id | UUID | Yes | Reviewed employee. |
| reviewer_employee_id | UUID | Yes | Reviewer/manager. |
| review_period_start | Date | Yes | Cycle start date. |
| review_period_end | Date | Yes | Cycle end date. |
| overall_rating | Decimal(2,1) | No | Optional rating, typically `1.0-5.0`. |
| strengths | Text | No | Strength narrative. |
| improvement_areas | Text | No | Development areas. |
| goals_next_period | Text | No | Future goals. |
| status | Enum | Yes | `Draft`, `Submitted`, `Finalized`. |
| submitted_at | DateTime | No | Reviewer submission timestamp. |
| finalized_at | DateTime | No | Review finalization timestamp. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one subject `Employee`.
- Belongs to one reviewer `Employee`.
- Is surfaced in employee and manager review read models.

### Lifecycle states
- `Draft`
- `Submitted`
- `Finalized`

## AttendanceRecord

### Owning service
- `attendance-service`

### Description
Represents a day-level attendance record built from check-in/check-out activity or imported time data.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| attendance_id | UUID | Yes | Primary identifier. |
| employee_id | UUID | Yes | Foreign key to `Employee`. |
| attendance_date | Date | Yes | Attendance date. |
| check_in_time | DateTime | No | Actual first check-in time. |
| check_out_time | DateTime | No | Actual final check-out time. |
| total_hours | Decimal(5,2) | No | Calculated work duration. |
| attendance_status | Enum | Yes | `Present`, `Absent`, `Late`, `HalfDay`, `Holiday`. |
| source | Enum | No | `Manual`, `Biometric`, `APIImport`. |
| record_state | Enum | Yes | `Captured`, `Validated`, `Approved`, `Locked`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one `Employee`.
- Contributes to `PayrollRecord` calculations via summary projections.

### Lifecycle states
- `Captured`
- `Validated`
- `Approved`
- `Locked`

## LeaveRequest

### Owning service
- `leave-service`

### Description
Represents an employee leave request with approval and downstream payroll/availability impact.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| leave_request_id | UUID | Yes | Primary identifier. |
| employee_id | UUID | Yes | Requesting employee. |
| leave_type | Enum | Yes | `Annual`, `Sick`, `Casual`, `Unpaid`, `Other`. |
| start_date | Date | Yes | Requested leave start. |
| end_date | Date | Yes | Requested leave end. |
| total_days | Decimal(4,1) | Yes | Derived leave duration. |
| reason | Text | No | Employee justification. |
| approver_employee_id | UUID | No | Approver/manager. |
| status | Enum | Yes | `Draft`, `Submitted`, `Approved`, `Rejected`, `Cancelled`. |
| submitted_at | DateTime | No | Submission timestamp. |
| decision_at | DateTime | No | Decision timestamp. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one requestor `Employee`.
- May reference one approver `Employee`.
- Affects payroll when approved, especially for unpaid leave.

### Lifecycle states
- `Draft`
- `Submitted`
- `Approved`
- `Rejected`
- `Cancelled`

## PayrollRecord

### Owning service
- `payroll-service`

### Description
Represents a payroll result for an employee over a defined pay period.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| payroll_record_id | UUID | Yes | Primary identifier. |
| employee_id | UUID | Yes | Employee paid in the period. |
| pay_period_start | Date | Yes | Payroll period start. |
| pay_period_end | Date | Yes | Payroll period end. |
| base_salary | Decimal(12,2) | Yes | Fixed salary component. |
| allowances | Decimal(12,2) | No | Additional earnings. |
| deductions | Decimal(12,2) | No | Taxes, benefits, or manual deductions. |
| overtime_pay | Decimal(12,2) | No | Overtime earning amount. |
| gross_pay | Decimal(12,2) | Yes | Calculated gross amount. |
| net_pay | Decimal(12,2) | Yes | Final payout amount. |
| currency | String | Yes | ISO-4217 currency code. |
| payment_date | Date | No | Actual disbursement date. |
| status | Enum | Yes | `Draft`, `Processed`, `Paid`, `Cancelled`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one `Employee`.
- Consumes attendance and leave summaries through projections/events.

### Lifecycle states
- `Draft`
- `Processed`
- `Paid`
- `Cancelled`


## AttendanceRule

### Owning service
- `settings-service`

### Description
Represents a reusable workforce attendance policy template used to validate schedules, lateness thresholds, and attendance automation.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| attendance_rule_id | UUID | Yes | Primary identifier. |
| code | String | Yes | Unique human-readable rule code. |
| name | String | Yes | Rule name shown to administrators. |
| timezone | String | Yes | IANA timezone used for cutoffs and schedule evaluation. |
| workdays | String[] | Yes | Ordered weekdays expected for the rule. |
| standard_work_hours | Decimal(4,2) | Yes | Expected daily scheduled hours. |
| grace_period_minutes | Integer | Yes | Allowed lateness before flagging. |
| late_after_minutes | Integer | Yes | Threshold for late classification. |
| auto_clock_out_hours | Decimal(4,2) | No | Optional auto clock-out threshold. |
| require_geo_fencing | Boolean | Yes | Indicates whether compliant check-in locations are required. |
| status | Enum | Yes | `Draft`, `Active`, `Archived`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Referenced by attendance schedule templates and validation policies.
- Contributes attendance defaults to downstream `AttendanceRecord` classification logic.

### Lifecycle states
- `Draft`
- `Active`
- `Archived`

## LeavePolicy

### Owning service
- `settings-service`

### Description
Represents a configurable leave entitlement policy that defines accrual, carry-forward, and approval requirements.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| leave_policy_id | UUID | Yes | Primary identifier. |
| code | String | Yes | Unique leave policy code. |
| name | String | Yes | Policy display name. |
| leave_type | Enum | Yes | `Annual`, `Sick`, `Casual`, `Unpaid`, `Parental`, `Other`. |
| accrual_frequency | Enum | Yes | `None`, `Monthly`, `Quarterly`, `Yearly`. |
| accrual_rate_days | Decimal(4,2) | Yes | Days accrued per frequency interval. |
| annual_entitlement_days | Decimal(5,2) | Yes | Annual leave entitlement. |
| carry_forward_limit_days | Decimal(5,2) | Yes | Max unused days allowed to carry forward. |
| requires_approval | Boolean | Yes | Whether manager approval is required. |
| allow_negative_balance | Boolean | Yes | Whether balances may go below zero. |
| status | Enum | Yes | `Draft`, `Active`, `Archived`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Applied as a default or assignment source during employee onboarding.
- Governs validation rules for downstream `LeaveRequest` workflows.

### Lifecycle states
- `Draft`
- `Active`
- `Archived`

## PayrollSettings

### Owning service
- `settings-service`

### Description
Represents the authoritative company payroll configuration used for pay schedule timing, approvals, and leave deduction behavior.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| payroll_setting_id | UUID | Yes | Primary identifier. |
| pay_schedule | Enum | Yes | `Weekly`, `BiWeekly`, `SemiMonthly`, `Monthly`. |
| pay_day | Integer | Yes | Pay day number interpreted relative to the chosen schedule. |
| currency | String | Yes | ISO-4217 currency code. |
| overtime_multiplier | Decimal(4,2) | Yes | Multiplier used for overtime calculations. |
| attendance_cutoff_days | Integer | Yes | Number of days before payroll close that attendance must be finalized. |
| leave_deduction_mode | Enum | Yes | `None`, `Prorated`, `FullDay`. |
| approval_chain | String[] | Yes | Ordered payroll approval stages. |
| status | Enum | Yes | `Draft`, `Active`, `Archived`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Configures downstream `PayrollRecord` generation and approval flow.
- Consumes attendance and leave configuration defaults to support payroll processing.

### Lifecycle states
- `Draft`
- `Active`
- `Archived`

## JobPosting

### Owning service
- `hiring-service`

### Description
Represents a requisition or externally published opening for recruitment.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| job_posting_id | UUID | Yes | Primary identifier. |
| title | String | Yes | Posting title. |
| department_id | UUID | Yes | Hiring department. |
| role_id | UUID | No | Optional standardized role mapping. |
| employment_type | Enum | Yes | `FullTime`, `PartTime`, `Contract`, `Intern`. |
| location | String | No | Work location or region. |
| description | Text | Yes | Responsibilities and requirements. |
| openings_count | Integer | Yes | Vacancy count; minimum `1`. |
| posting_date | Date | Yes | Publish date. |
| closing_date | Date | No | Optional close date. |
| status | Enum | Yes | `Draft`, `Open`, `OnHold`, `Closed`, `Filled`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one `Department`.
- May reference one `Role`.
- Has many `Candidate` applications.

### Lifecycle states
- `Draft`
- `Open`
- `OnHold`
- `Closed`
- `Filled`

## Candidate

### Owning service
- `hiring-service`

### Description
Represents an applicant to a `JobPosting` progressing through the hiring pipeline.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| candidate_id | UUID | Yes | Primary identifier. |
| job_posting_id | UUID | Yes | Target job posting. |
| first_name | String | Yes | Candidate first name. |
| last_name | String | Yes | Candidate last name. |
| email | String | Yes | Candidate email; unique per job posting. |
| phone | String | No | Contact number. |
| resume_url | String | No | Resume artifact location. |
| source | Enum | No | `Referral`, `JobBoard`, `CareerSite`, `Agency`, `LinkedIn`, `Other`. |
| source_candidate_id | String | No | External provider candidate/member identifier. |
| source_profile_url | String | No | External profile URL. |
| application_date | Date | Yes | Application submission date. |
| status | Enum | Yes | `Applied`, `Screening`, `Interviewing`, `Offered`, `Hired`, `Rejected`, `Withdrawn`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one `JobPosting`.
- Has many `Interview` records.
- May convert to one `Employee` after hire.

### Lifecycle states
- `Applied`
- `Screening`
- `Interviewing`
- `Offered`
- `Hired`
- `Rejected`
- `Withdrawn`

## Interview

### Owning service
- `hiring-service`

### Description
Represents a scheduled or completed hiring interview round and its outcome metadata.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| interview_id | UUID | Yes | Primary identifier. |
| candidate_id | UUID | Yes | Candidate being interviewed. |
| interview_type | Enum | Yes | `PhoneScreen`, `Technical`, `Behavioral`, `Panel`, `Final`. |
| scheduled_start | DateTime | Yes | Planned start time. |
| scheduled_end | DateTime | Yes | Planned end time. |
| location_or_link | String | No | Physical location or meeting link. |
| interviewer_employee_ids | List<UUID> | No | Interview panel employee IDs. |
| feedback_summary | Text | No | Consolidated interviewer notes. |
| recommendation | Enum | No | `StrongHire`, `Hire`, `NoHire`, `Undecided`. |
| google_calendar_event_id | String | No | External Google Calendar event ID when synced. |
| google_calendar_event_link | String | No | Link to synced calendar event. |
| status | Enum | Yes | `Scheduled`, `Completed`, `Cancelled`, `NoShow`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one `Candidate`.
- References zero or more interviewer `Employee` records by ID.

### Lifecycle states
- `Scheduled`
- `Completed`
- `Cancelled`
- `NoShow`

## UserAccount

### Owning service
- `auth-service`

### Description
Represents an authenticated principal used to access HRMS APIs and UI surfaces.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| user_id | UUID | Yes | Primary identifier. |
| employee_id | UUID | No | Optional link to `Employee` for workforce users. |
| username | String | Yes | Unique login name. |
| email | String | Yes | Unique authentication/contact email. |
| password_hash | String | Yes | Stored credential hash or external identity marker. |
| identity_provider | Enum | Yes | `Local`, `SSO`, `OAuth`. |
| status | Enum | Yes | `Invited`, `Active`, `Locked`, `Disabled`. |
| last_login_at | DateTime | No | Most recent successful login. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- May link to one `Employee`.
- Has many `RoleBinding` assignments.
- Has many `Session` records.
- Has many `RefreshToken` records.
- Has one optional `NotificationPreference` subject scope.

### Lifecycle states
- `Invited`
- `Active`
- `Locked`
- `Disabled`

## RoleBinding

### Owning service
- `auth-service`

### Description
Represents a role or capability assignment to a subject within an explicit scope.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| binding_id | UUID | Yes | Primary identifier. |
| user_id | UUID | Yes | Bound principal. |
| role_name | String | Yes | Canonical role such as `Admin`, `Manager`, `Employee`, `Service`. |
| scope_type | Enum | Yes | `Global`, `Department`, `Employee`, `Service`. |
| scope_id | UUID/String | No | Scoped object identifier when applicable. |
| effective_from | DateTime | Yes | Binding start timestamp. |
| effective_to | DateTime | No | Optional binding expiry. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one `UserAccount`.
- Evaluated against `PermissionPolicy` entries.

### Lifecycle states
- `Active` while current time is within effective range.
- `Expired` after `effective_to`.
- `Revoked` when explicitly removed.

## PermissionPolicy

### Owning service
- `auth-service`

### Description
Defines the mapping from roles/scopes to capabilities and resource constraints.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| policy_id | UUID | Yes | Primary identifier. |
| capability_id | String | Yes | Stable capability identifier. |
| role_name | String | Yes | Applicable role. |
| resource_type | String | Yes | Protected resource family. |
| scope_rule | String | Yes | Scope expression or evaluation rule. |
| effect | Enum | Yes | `Allow`, `Deny`. |
| version | Integer | Yes | Monotonic policy version. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Referenced by authorization checks and audit trails.

### Lifecycle states
- `Draft`
- `Active`
- `Retired`

## Session

### Owning service
- `auth-service`

### Description
Represents an authenticated browser or API session.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| session_id | UUID | Yes | Primary identifier. |
| user_id | UUID | Yes | Authenticated principal. |
| access_token_jti | String | Yes | Token identifier for revocation/introspection. |
| client_type | Enum | Yes | `Web`, `Mobile`, `Service`. |
| ip_address | String | No | Source IP. |
| user_agent | String | No | Client user agent. |
| started_at | DateTime | Yes | Session start timestamp. |
| expires_at | DateTime | Yes | Session expiry. |
| revoked_at | DateTime | No | Revocation timestamp. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one `UserAccount`.
- May have one or more `RefreshToken` records.

### Lifecycle states
- `Active`
- `Expired`
- `Revoked`

## RefreshToken

### Owning service
- `auth-service`

### Description
Represents a refresh credential associated with a session.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| refresh_token_id | UUID | Yes | Primary identifier. |
| session_id | UUID | Yes | Parent session. |
| user_id | UUID | Yes | Token subject. |
| token_hash | String | Yes | Stored hash of refresh token. |
| issued_at | DateTime | Yes | Issue timestamp. |
| expires_at | DateTime | Yes | Expiry timestamp. |
| rotated_from_token_id | UUID | No | Prior token in rotation chain. |
| revoked_at | DateTime | No | Revocation timestamp. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Belongs to one `Session`.
- Belongs to one `UserAccount`.

### Lifecycle states
- `Active`
- `Rotated`
- `Expired`
- `Revoked`

## NotificationTemplate

### Owning service
- `notification-service`

### Description
Represents a reusable notification definition for a workflow or event.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| template_id | UUID | Yes | Primary identifier. |
| code | String | Yes | Stable template code. |
| channel | Enum | Yes | `Email`, `SMS`, `Push`, `InApp`. |
| subject_template | String | No | Used for subject-capable channels. |
| body_template | Text | Yes | Message body template. |
| locale | String | Yes | Locale code such as `en-US`. |
| status | Enum | Yes | `Draft`, `Active`, `Retired`. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Used by many `NotificationMessage` records.

### Lifecycle states
- `Draft`
- `Active`
- `Retired`

## NotificationMessage

### Owning service
- `notification-service`

### Description
Represents a concrete outbound or in-app notification instance.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| message_id | UUID | Yes | Primary identifier. |
| template_id | UUID | No | Optional source template. |
| subject_type | String | Yes | Recipient subject type such as `Employee`, `Candidate`, `UserAccount`. |
| subject_id | UUID/String | Yes | Recipient subject identifier. |
| channel | Enum | Yes | `Email`, `SMS`, `Push`, `InApp`. |
| destination | String | Yes | Email address, phone number, device token, or inbox key. |
| payload | JSON | Yes | Resolved variable payload. |
| status | Enum | Yes | `Queued`, `Sent`, `Failed`, `Suppressed`. |
| queued_at | DateTime | Yes | Queue timestamp. |
| sent_at | DateTime | No | Delivery completion timestamp. |
| failure_reason | String | No | Provider or policy failure summary. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- May reference one `NotificationTemplate`.
- Has many `DeliveryAttempt` records.
- Governed by `NotificationPreference` rules.

### Lifecycle states
- `Queued`
- `Sent`
- `Failed`
- `Suppressed`

## DeliveryAttempt

### Owning service
- `notification-service`

### Description
Represents a provider-level attempt to deliver a notification.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| delivery_attempt_id | UUID | Yes | Primary identifier. |
| message_id | UUID | Yes | Parent notification message. |
| provider_name | String | Yes | SMTP/SMS/push provider name. |
| provider_message_id | String | No | External provider message identifier. |
| attempt_number | Integer | Yes | Sequential retry number. |
| attempted_at | DateTime | Yes | Attempt timestamp. |
| outcome | Enum | Yes | `Sent`, `Failed`, `Deferred`. |
| response_code | String | No | Provider response code. |
| response_message | String | No | Provider response detail. |
| created_at | DateTime | Yes | Record creation timestamp. |

### Relationships
- Belongs to one `NotificationMessage`.

### Lifecycle states
- `Sent`
- `Failed`
- `Deferred`

## NotificationPreference

### Owning service
- `notification-service`

### Description
Represents channel and topic preferences for a subject receiving notifications.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| preference_id | UUID | Yes | Primary identifier. |
| subject_type | String | Yes | `Employee`, `Candidate`, `UserAccount`, `Service`. |
| subject_id | UUID/String | Yes | Preference owner identifier. |
| topic_code | String | Yes | Topic such as `leave.approval` or `security.alert`. |
| email_enabled | Boolean | Yes | Email channel preference. |
| sms_enabled | Boolean | Yes | SMS channel preference. |
| push_enabled | Boolean | Yes | Push channel preference. |
| in_app_enabled | Boolean | Yes | In-app channel preference. |
| quiet_hours | JSON | No | Optional do-not-disturb window. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Record last update timestamp. |

### Relationships
- Governs send eligibility for `NotificationMessage` records.
- May be associated with `Employee`, `Candidate`, or `UserAccount` subjects.

### Lifecycle states
- `Active`
- `Disabled`

## Coverage checklist

- Every entity owned in `docs/canon/service-map.md` is defined in this document.
- Every workflow in `docs/canon/workflow-catalog.md` references only entities defined in this document.
- Every state transition referenced in workflows maps to events in `docs/canon/event-catalog.md`.

## WebhookEndpoint

### Owning service
- `integration-service`

### Description
Represents a tenant-scoped outbound webhook subscription for delivery of canonical HRMS events to an external endpoint.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| webhook_id | UUID | Yes | Primary identifier. |
| tenant_id | UUID/String | Yes | Tenant/workspace scope for the registration. |
| target_url | String | Yes | HTTPS endpoint for outbound delivery; localhost HTTP only for local development. |
| subscribed_events | String[] | Yes | Canonical D2-aligned event types to deliver. |
| secret | Secret | Yes | Managed secret used for request signing; never returned in plaintext. |
| status | Enum | Yes | `Active`, `Disabled`, `Deleted`. |
| signature_algorithm | Enum | Yes | Currently `hmac-sha256`. |
| last_delivery_status | Enum | No | `Succeeded`, `Failed`, `DeadLettered`. |
| retry_policy | Object | Yes | Attempt count and backoff metadata. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Last update timestamp. |

## WebhookDelivery

### Owning service
- `integration-service`

### Description
Represents one webhook fan-out delivery for a specific tenant event and endpoint pairing.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| delivery_id | UUID | Yes | Primary identifier. |
| webhook_id | UUID | Yes | Parent `WebhookEndpoint`. |
| tenant_id | UUID/String | Yes | Tenant scope copied from the webhook and event. |
| event_id | UUID | Yes | Canonical source event identifier. |
| event_type | String | Yes | Canonical event type. |
| status | Enum | Yes | `Scheduled`, `Delivering`, `Succeeded`, `DeadLettered`. |
| attempt_count | Integer | Yes | Number of delivery attempts executed. |
| last_http_status | Integer | No | Final HTTP response code if any. |
| last_error | String | No | Final failure detail if any. |
| dead_lettered_at | DateTime | No | When the delivery exhausted retries. |
| created_at | DateTime | Yes | Record creation timestamp. |
| updated_at | DateTime | Yes | Last status update timestamp. |

## WebhookDeliveryAttempt

### Owning service
- `integration-service`

### Description
Represents an immutable attempt record for a single outbound webhook dispatch try.

### Attributes
| Attribute | Type | Required | Notes |
|---|---|---|---|
| attempt_id | UUID | Yes | Primary identifier. |
| delivery_id | UUID | Yes | Parent `WebhookDelivery`. |
| webhook_id | UUID | Yes | Parent `WebhookEndpoint`. |
| tenant_id | UUID/String | Yes | Tenant scope for the attempt. |
| attempt_number | Integer | Yes | 1-based retry sequence. |
| status | Enum | Yes | `Succeeded` or `Failed`. |
| response_status | Integer | No | HTTP response code if any. |
| error_message | String | No | Transport or validation failure text. |
| created_at | DateTime | Yes | Attempt timestamp. |
