# Read Model Catalog

This catalog defines query-optimized projections and validates each read model against canonical source services, workflows, and entities.

## Cross-cutting conventions
- Source of truth for services: `docs/canon/service-map.md`.
- Source of truth for entities: `docs/canon/domain-model.md`.
- Use immutable event timestamps where available for deterministic replay.
- Preserve source identifiers (`*_id`) for traceability.
- Keep personally identifiable information limited to operationally required fields.
- Version read-model contracts when fields are added or renamed.
- Read models may denormalize display-only attributes, but authoritative writes always go to owning services.

## 1) `employee_directory_view`
- **Source services:** `employee-service`
- **Source workflows:** `employee_onboarding`
- **Source entities:** `Employee`, `Department`, `Role`
- **Key/grain:** one row per employee (`employee_id`)
- **Fields:** `employee_id`, `employee_number`, `full_name`, `email`, `phone`, `hire_date`, `employment_type`, `employee_status`, `department_id`, `department_name`, `role_id`, `role_title`, `manager_employee_id`, `manager_name`, `updated_at`
- **Primary consumers:** dashboard, employee list, employee profile

## 2) `organization_structure_view`
- **Source services:** `employee-service`
- **Source workflows:** `employee_onboarding`
- **Source entities:** `Department`, `Employee`, `Role`
- **Key/grain:** one row per employee assignment within the org structure (`department_id`, `employee_id`)
- **Fields:** `department_id`, `department_name`, `department_code`, `department_status`, `head_employee_id`, `head_employee_name`, `employee_id`, `employee_name`, `employee_status`, `manager_employee_id`, `manager_name`, `role_id`, `role_title`, `updated_at`
- **Primary consumers:** departments page, roles page, manager hierarchy views

## 3) `attendance_dashboard_view`
- **Source services:** `attendance-service`, `employee-service`
- **Source workflows:** `attendance_tracking`
- **Source entities:** `AttendanceRecord`, `Employee`, `Department`
- **Key/grain:** one row per employee per attendance date (`employee_id`, `attendance_date`)
- **Fields:** `employee_id`, `employee_number`, `employee_name`, `department_id`, `department_name`, `attendance_date`, `attendance_status`, `check_in_time`, `check_out_time`, `total_hours`, `source`, `record_state`, `updated_at`
- **Primary consumers:** dashboard, attendance dashboard, employee profile

## 4) `leave_requests_view`
- **Source services:** `leave-service`, `employee-service`
- **Source workflows:** `leave_request`
- **Source entities:** `LeaveRequest`, `Employee`, `Department`
- **Key/grain:** one row per leave request (`leave_request_id`)
- **Fields:** `leave_request_id`, `employee_id`, `employee_number`, `employee_name`, `department_id`, `department_name`, `leave_type`, `start_date`, `end_date`, `total_days`, `reason`, `approver_employee_id`, `approver_name`, `status`, `submitted_at`, `decision_at`, `updated_at`
- **Primary consumers:** dashboard, leave requests, employee profile

## 5) `payroll_summary_view`
- **Source services:** `payroll-service`, `employee-service`, `attendance-service`, `leave-service`
- **Source workflows:** `payroll_processing`
- **Source entities:** `PayrollRecord`, `Employee`, `AttendanceRecord`, `LeaveRequest`, `Department`
- **Key/grain:** one row per employee per pay period (`employee_id`, `pay_period_start`, `pay_period_end`)
- **Fields:** `payroll_record_id`, `employee_id`, `employee_number`, `employee_name`, `department_id`, `department_name`, `pay_period_start`, `pay_period_end`, `base_salary`, `allowances`, `deductions`, `overtime_pay`, `gross_pay`, `net_pay`, `currency`, `payment_date`, `status`, `attendance_days_count`, `approved_leave_days`, `updated_at`
- **Primary consumers:** dashboard, payroll dashboard, employee profile

## 6) `job_posting_directory_view`
- **Source services:** `hiring-service`, `employee-service`
- **Source workflows:** `candidate_hiring`
- **Source entities:** `JobPosting`, `Department`, `Role`
- **Key/grain:** one row per job posting (`job_posting_id`)
- **Fields:** `job_posting_id`, `title`, `department_id`, `department_name`, `role_id`, `role_title`, `employment_type`, `location`, `openings_count`, `posting_date`, `closing_date`, `status`, `candidate_count`, `updated_at`
- **Primary consumers:** job postings page, dashboard

## 7) `candidate_pipeline_view`
- **Source services:** `hiring-service`, `employee-service`
- **Source workflows:** `candidate_hiring`
- **Source entities:** `Candidate`, `JobPosting`, `Department`, `Role`, `Interview`, `Employee`
- **Key/grain:** one row per candidate application (`candidate_id`)
- **Fields:** `candidate_id`, `candidate_name`, `candidate_email`, `job_posting_id`, `job_title`, `department_id`, `department_name`, `role_id`, `role_title`, `application_date`, `pipeline_stage`, `stage_updated_at`, `source`, `source_candidate_id`, `next_interview_at`, `interview_count`, `last_interview_recommendation`, `updated_at`
- **Primary consumers:** candidate pipeline, dashboard

## 8) `performance_review_view`
- **Source services:** `performance-service`, `employee-service`
- **Source workflows:** `performance_management`
- **Source entities:** `ReviewCycle`, `Goal`, `Feedback`, `CalibrationSession`, `PipPlan`, `Employee`, `Department`
- **Key/grain:** one row per employee per review cycle (`review_cycle_id`, `employee_id`)
- **Fields:** `review_cycle_id`, `goal_id`, `employee_id`, `employee_name`, `manager_employee_id`, `manager_name`, `department_id`, `department_name`, `goal_title`, `goal_status`, `progress_percent`, `feedback_count`, `calibration_status`, `final_rating`, `pip_id`, `pip_status`, `pip_completion_percent`, `updated_at`
- **Primary consumers:** performance workspace, employee profile, executive dashboard

## 9) `settings_configuration_view`
- **Source services:** `settings-service`
- **Source workflows:** `settings_administration`
- **Source entities:** `AttendanceRule`, `LeavePolicy`, `PayrollSettings`
- **Key/grain:** one administrative configuration snapshot for the active tenant/workspace
- **Fields:** `attendance_rules`, `leave_policies`, `payroll_settings`, `updated_at`
- **Primary consumers:** settings workspace, administrative dashboards

## 10) `access_control_view`
- **Source services:** `auth-service`, `employee-service`
- **Source workflows:** `access_provisioning`
- **Source entities:** `UserAccount`, `RoleBinding`, `PermissionPolicy`, `Employee`, `Session`, `RefreshToken`
- **Key/grain:** one row per user account (`user_id`)
- **Fields:** `user_id`, `employee_id`, `employee_name`, `username`, `email`, `identity_provider`, `user_status`, `assigned_roles`, `effective_scopes`, `active_session_count`, `active_refresh_token_count`, `last_login_at`, `updated_at`
- **Primary consumers:** settings, security administration

## 11) `notification_delivery_view`
- **Source services:** `notification-service`
- **Source workflows:** `notification_dispatch`
- **Source entities:** `NotificationMessage`, `DeliveryAttempt`, `NotificationTemplate`, `NotificationPreference`
- **Key/grain:** one row per notification message (`message_id`)
- **Fields:** `message_id`, `template_id`, `template_code`, `subject_type`, `subject_id`, `channel`, `destination`, `status`, `queued_at`, `sent_at`, `failure_reason`, `last_provider_name`, `last_attempt_outcome`, `attempt_count`, `updated_at`
- **Primary consumers:** settings, support operations

## Coverage checklist

- Every workflow in `docs/canon/workflow-catalog.md` produces or consumes at least one read model.
- Every UI-facing operational area has a read model contract.
- Every source entity listed above is defined in `docs/canon/domain-model.md`.


## 12) `integration_delivery_view`
- **Source services:** `integration-service`
- **Source workflows:** outbound integration dispatch
- **Source entities:** `WebhookEndpoint`, `WebhookDelivery`, `WebhookDeliveryAttempt`
- **Key/grain:** one row per webhook delivery (`delivery_id`)
- **Fields:** `delivery_id`, `webhook_id`, `tenant_id`, `target_url`, `event_id`, `event_type`, `status`, `attempt_count`, `last_http_status`, `last_error`, `dead_lettered_at`, `updated_at`
- **Primary consumers:** integration operations, support tooling, audit/replay views

## 13) `document_library_view`
- **Source services:** `documents`, `employee-service`
- **Source workflows:** employee-document management, compliance tracking
- **Source entities:** `EmployeeDocument`, `PolicyAcknowledgement`, `ComplianceTask`, `Employee`
- **Key/grain:** one row per document metadata record (`document_id`)
- **Fields:** `document_id`, `employee_id`, `employee_name`, `department_id`, `department_name`, `title`, `document_type`, `status`, `policy_code`, `expiry_date`, `requires_acknowledgement`, `created_at`, `updated_at`
- **Primary consumers:** document operations, compliance dashboards, search indexing

## 14) `global_search_view`
- **Source services:** `search-service`
- **Source workflows:** `projection_search_indexing`
- **Source entities:** `SearchDocument`
- **Key/grain:** one row per searchable projection document (`document_id`)
- **Fields:** `document_id`, `tenant_id`, `source_view`, `source_key`, `domain`, `entity_type`, `display_name`, `department_id`, `department_name`, `role_id`, `role_title`, `status`, `updated_at`, `metadata`
- **Primary consumers:** universal search, directory lookups, command palette, cross-domain navigation

