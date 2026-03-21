CREATE TABLE IF NOT EXISTS attendance_records (
  tenant_id VARCHAR(80) NOT NULL,
  attendance_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id UUID NOT NULL,
  attendance_date DATE NOT NULL,
  check_in_time TIMESTAMPTZ,
  check_out_time TIMESTAMPTZ,
  total_hours NUMERIC(5,2),
  attendance_status VARCHAR(20) NOT NULL CHECK (attendance_status IN ('Present', 'Absent', 'Late', 'HalfDay', 'Holiday')),
  source VARCHAR(20) CHECK (source IN ('Manual', 'Biometric', 'APIImport')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_attendance_records_tenant_attendance UNIQUE (tenant_id, attendance_id),
  CONSTRAINT uq_attendance_records_employee_date UNIQUE (tenant_id, employee_id, attendance_date),
  CONSTRAINT fk_attendance_records_employee
    FOREIGN KEY (tenant_id, employee_id)
    REFERENCES employees (tenant_id, employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_attendance_records_tenant_id ON attendance_records (tenant_id);
CREATE INDEX IF NOT EXISTS idx_attendance_records_tenant_employee_id ON attendance_records (tenant_id, employee_id);
CREATE INDEX IF NOT EXISTS idx_attendance_records_tenant_date ON attendance_records (tenant_id, attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_records_tenant_status ON attendance_records (tenant_id, attendance_status);

CREATE TABLE IF NOT EXISTS leave_requests (
  tenant_id VARCHAR(80) NOT NULL,
  leave_request_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id UUID NOT NULL,
  leave_type VARCHAR(20) NOT NULL CHECK (leave_type IN ('Annual', 'Sick', 'Casual', 'Unpaid', 'Other')),
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  total_days NUMERIC(4,1) NOT NULL,
  reason TEXT,
  approver_employee_id UUID,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Submitted', 'Approved', 'Rejected', 'Cancelled')),
  submitted_at TIMESTAMPTZ,
  decision_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_leave_requests_tenant_request UNIQUE (tenant_id, leave_request_id),
  CONSTRAINT chk_leave_requests_date_range CHECK (end_date >= start_date),
  CONSTRAINT fk_leave_requests_employee
    FOREIGN KEY (tenant_id, employee_id)
    REFERENCES employees (tenant_id, employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_leave_requests_approver
    FOREIGN KEY (tenant_id, approver_employee_id)
    REFERENCES employees (tenant_id, employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_leave_requests_tenant_id ON leave_requests (tenant_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_tenant_employee_id ON leave_requests (tenant_id, employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_tenant_approver_employee_id ON leave_requests (tenant_id, approver_employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_tenant_status ON leave_requests (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_leave_requests_tenant_date_range ON leave_requests (tenant_id, start_date, end_date);

CREATE TABLE IF NOT EXISTS payroll_records (
  tenant_id VARCHAR(80) NOT NULL,
  payroll_record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id UUID NOT NULL,
  pay_period_start DATE NOT NULL,
  pay_period_end DATE NOT NULL,
  base_salary NUMERIC(12,2) NOT NULL,
  allowances NUMERIC(12,2) DEFAULT 0.00,
  deductions NUMERIC(12,2) DEFAULT 0.00,
  overtime_pay NUMERIC(12,2) DEFAULT 0.00,
  gross_pay NUMERIC(12,2) NOT NULL,
  net_pay NUMERIC(12,2) NOT NULL,
  currency CHAR(3) NOT NULL,
  payment_date DATE,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Processed', 'Paid', 'Cancelled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_payroll_records_tenant_record UNIQUE (tenant_id, payroll_record_id),
  CONSTRAINT chk_payroll_records_period CHECK (pay_period_end >= pay_period_start),
  CONSTRAINT uq_payroll_records_employee_period UNIQUE (tenant_id, employee_id, pay_period_start, pay_period_end),
  CONSTRAINT fk_payroll_records_employee
    FOREIGN KEY (tenant_id, employee_id)
    REFERENCES employees (tenant_id, employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_payroll_records_tenant_id ON payroll_records (tenant_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_tenant_employee_id ON payroll_records (tenant_id, employee_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_tenant_status ON payroll_records (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_payroll_records_tenant_payment_date ON payroll_records (tenant_id, payment_date);

CREATE TABLE IF NOT EXISTS job_postings (
  tenant_id VARCHAR(80) NOT NULL,
  job_posting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(200) NOT NULL,
  department_id UUID NOT NULL,
  role_id UUID,
  employment_type VARCHAR(20) NOT NULL CHECK (employment_type IN ('FullTime', 'PartTime', 'Contract', 'Intern')),
  location VARCHAR(200),
  description TEXT NOT NULL,
  openings_count INTEGER NOT NULL CHECK (openings_count >= 1),
  posting_date DATE NOT NULL,
  closing_date DATE,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Open', 'OnHold', 'Closed', 'Filled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_job_postings_tenant_posting UNIQUE (tenant_id, job_posting_id),
  CONSTRAINT chk_job_postings_dates CHECK (closing_date IS NULL OR closing_date >= posting_date),
  CONSTRAINT fk_job_postings_department
    FOREIGN KEY (tenant_id, department_id)
    REFERENCES departments (tenant_id, department_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_job_postings_role
    FOREIGN KEY (tenant_id, role_id)
    REFERENCES roles (tenant_id, role_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_job_postings_tenant_id ON job_postings (tenant_id);
CREATE INDEX IF NOT EXISTS idx_job_postings_tenant_department_id ON job_postings (tenant_id, department_id);
CREATE INDEX IF NOT EXISTS idx_job_postings_tenant_role_id ON job_postings (tenant_id, role_id);
CREATE INDEX IF NOT EXISTS idx_job_postings_tenant_status ON job_postings (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_job_postings_tenant_posting_date ON job_postings (tenant_id, posting_date);

CREATE TABLE IF NOT EXISTS candidates (
  tenant_id VARCHAR(80) NOT NULL,
  candidate_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  job_posting_id UUID NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(30),
  resume_url TEXT,
  source VARCHAR(20) CHECK (source IN ('Referral', 'JobBoard', 'CareerSite', 'Agency', 'LinkedIn', 'Other')),
  source_candidate_id VARCHAR(120),
  source_profile_url TEXT,
  application_date DATE NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Applied', 'Screening', 'Interviewing', 'Offered', 'Hired', 'Rejected', 'Withdrawn')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_candidates_tenant_candidate UNIQUE (tenant_id, candidate_id),
  CONSTRAINT uq_candidates_posting_email UNIQUE (tenant_id, job_posting_id, email),
  CONSTRAINT fk_candidates_job_posting
    FOREIGN KEY (tenant_id, job_posting_id)
    REFERENCES job_postings (tenant_id, job_posting_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidates_tenant_id ON candidates (tenant_id);
CREATE INDEX IF NOT EXISTS idx_candidates_tenant_job_posting_id ON candidates (tenant_id, job_posting_id);
CREATE INDEX IF NOT EXISTS idx_candidates_tenant_status ON candidates (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_candidates_tenant_application_date ON candidates (tenant_id, application_date);
CREATE INDEX IF NOT EXISTS idx_candidates_tenant_source_candidate_id ON candidates (tenant_id, source_candidate_id);

CREATE TABLE IF NOT EXISTS candidate_stage_transitions (
  tenant_id VARCHAR(80) NOT NULL,
  candidate_stage_transition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  candidate_id UUID NOT NULL,
  from_status VARCHAR(20) CHECK (from_status IN ('Applied', 'Screening', 'Interviewing', 'Offered', 'Hired', 'Rejected', 'Withdrawn')),
  to_status VARCHAR(20) NOT NULL CHECK (to_status IN ('Applied', 'Screening', 'Interviewing', 'Offered', 'Hired', 'Rejected', 'Withdrawn')),
  changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  changed_by VARCHAR(120),
  reason TEXT,
  notes TEXT,
  CONSTRAINT uq_candidate_stage_transitions_tenant_transition UNIQUE (tenant_id, candidate_stage_transition_id),
  CONSTRAINT fk_candidate_stage_transitions_candidate
    FOREIGN KEY (tenant_id, candidate_id)
    REFERENCES candidates (tenant_id, candidate_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidate_stage_transitions_tenant_id ON candidate_stage_transitions (tenant_id);
CREATE INDEX IF NOT EXISTS idx_candidate_stage_transitions_tenant_candidate_id ON candidate_stage_transitions (tenant_id, candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_stage_transitions_tenant_changed_at ON candidate_stage_transitions (tenant_id, changed_at);
CREATE INDEX IF NOT EXISTS idx_candidate_stage_transitions_tenant_to_status ON candidate_stage_transitions (tenant_id, to_status);

CREATE TABLE IF NOT EXISTS interviews (
  tenant_id VARCHAR(80) NOT NULL,
  interview_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  candidate_id UUID NOT NULL,
  interview_type VARCHAR(20) NOT NULL CHECK (interview_type IN ('PhoneScreen', 'Technical', 'Behavioral', 'Panel', 'Final')),
  scheduled_start TIMESTAMPTZ NOT NULL,
  scheduled_end TIMESTAMPTZ NOT NULL,
  location_or_link TEXT,
  interviewer_employee_ids UUID[],
  feedback_summary TEXT,
  recommendation VARCHAR(20) CHECK (recommendation IN ('StrongHire', 'Hire', 'NoHire', 'Undecided')),
  status VARCHAR(20) NOT NULL CHECK (status IN ('Scheduled', 'Completed', 'Cancelled', 'NoShow')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_interviews_tenant_interview UNIQUE (tenant_id, interview_id),
  CONSTRAINT chk_interviews_schedule CHECK (scheduled_end > scheduled_start),
  CONSTRAINT fk_interviews_candidate
    FOREIGN KEY (tenant_id, candidate_id)
    REFERENCES candidates (tenant_id, candidate_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_interviews_tenant_id ON interviews (tenant_id);
CREATE INDEX IF NOT EXISTS idx_interviews_tenant_candidate_id ON interviews (tenant_id, candidate_id);
CREATE INDEX IF NOT EXISTS idx_interviews_tenant_schedule ON interviews (tenant_id, scheduled_start, scheduled_end);
CREATE INDEX IF NOT EXISTS idx_interviews_tenant_status ON interviews (tenant_id, status);

CREATE TABLE IF NOT EXISTS attendance_rules (
  tenant_id VARCHAR(80) NOT NULL,
  attendance_rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code VARCHAR(80) NOT NULL,
  name VARCHAR(160) NOT NULL,
  timezone VARCHAR(80) NOT NULL,
  workdays VARCHAR(20)[] NOT NULL,
  standard_work_hours NUMERIC(4,2) NOT NULL CHECK (standard_work_hours >= 0 AND standard_work_hours <= 24),
  grace_period_minutes INTEGER NOT NULL DEFAULT 0 CHECK (grace_period_minutes >= 0),
  late_after_minutes INTEGER NOT NULL DEFAULT 0 CHECK (late_after_minutes >= grace_period_minutes),
  auto_clock_out_hours NUMERIC(4,2) CHECK (auto_clock_out_hours IS NULL OR (auto_clock_out_hours >= 0 AND auto_clock_out_hours <= 24)),
  require_geo_fencing BOOLEAN NOT NULL DEFAULT FALSE,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Active', 'Archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_attendance_rules_tenant_rule UNIQUE (tenant_id, attendance_rule_id),
  CONSTRAINT uq_attendance_rules_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_attendance_rules_tenant_id ON attendance_rules (tenant_id);
CREATE INDEX IF NOT EXISTS idx_attendance_rules_tenant_status ON attendance_rules (tenant_id, status);

CREATE TABLE IF NOT EXISTS leave_policies (
  tenant_id VARCHAR(80) NOT NULL,
  leave_policy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code VARCHAR(80) NOT NULL,
  name VARCHAR(160) NOT NULL,
  leave_type VARCHAR(20) NOT NULL CHECK (leave_type IN ('Annual', 'Sick', 'Casual', 'Unpaid', 'Parental', 'Other')),
  accrual_frequency VARCHAR(20) NOT NULL CHECK (accrual_frequency IN ('None', 'Monthly', 'Quarterly', 'Yearly')),
  accrual_rate_days NUMERIC(5,2) NOT NULL CHECK (accrual_rate_days >= 0),
  annual_entitlement_days NUMERIC(5,2) NOT NULL CHECK (annual_entitlement_days >= 0),
  carry_forward_limit_days NUMERIC(5,2) NOT NULL CHECK (carry_forward_limit_days >= 0 AND carry_forward_limit_days <= annual_entitlement_days),
  requires_approval BOOLEAN NOT NULL DEFAULT TRUE,
  allow_negative_balance BOOLEAN NOT NULL DEFAULT FALSE,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Active', 'Archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_leave_policies_tenant_policy UNIQUE (tenant_id, leave_policy_id),
  CONSTRAINT uq_leave_policies_code UNIQUE (tenant_id, code),
  CONSTRAINT chk_leave_policies_unpaid_entitlement CHECK (leave_type <> 'Unpaid' OR annual_entitlement_days = 0)
);

CREATE INDEX IF NOT EXISTS idx_leave_policies_tenant_id ON leave_policies (tenant_id);
CREATE INDEX IF NOT EXISTS idx_leave_policies_tenant_status ON leave_policies (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_leave_policies_tenant_type_status ON leave_policies (tenant_id, leave_type, status);
CREATE UNIQUE INDEX IF NOT EXISTS uq_leave_policies_active_type ON leave_policies (tenant_id, leave_type) WHERE status = 'Active';

CREATE TABLE IF NOT EXISTS payroll_settings (
  tenant_id VARCHAR(80) NOT NULL,
  payroll_setting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pay_schedule VARCHAR(20) NOT NULL CHECK (pay_schedule IN ('Weekly', 'BiWeekly', 'SemiMonthly', 'Monthly')),
  pay_day INTEGER NOT NULL CHECK (pay_day >= 1 AND pay_day <= 31),
  currency CHAR(3) NOT NULL,
  overtime_multiplier NUMERIC(4,2) NOT NULL CHECK (overtime_multiplier >= 1),
  attendance_cutoff_days INTEGER NOT NULL CHECK (attendance_cutoff_days >= 0 AND attendance_cutoff_days <= 31),
  leave_deduction_mode VARCHAR(20) NOT NULL CHECK (leave_deduction_mode IN ('None', 'Prorated', 'FullDay')),
  approval_chain TEXT[] NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Active', 'Archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_payroll_settings_tenant_setting UNIQUE (tenant_id, payroll_setting_id)
);

CREATE INDEX IF NOT EXISTS idx_payroll_settings_tenant_id ON payroll_settings (tenant_id);
CREATE INDEX IF NOT EXISTS idx_payroll_settings_tenant_status ON payroll_settings (tenant_id, status);

CREATE TABLE IF NOT EXISTS performance_review_cycles (
  tenant_id VARCHAR(80) NOT NULL,
  review_cycle_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code VARCHAR(40) NOT NULL,
  name VARCHAR(160) NOT NULL,
  review_period_start DATE NOT NULL,
  review_period_end DATE NOT NULL,
  owner_employee_id UUID NOT NULL,
  workflow_id UUID,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Open', 'Closed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_performance_review_cycles_tenant_review UNIQUE (tenant_id, review_cycle_id),
  CONSTRAINT uq_performance_review_cycles_tenant_code UNIQUE (tenant_id, code),
  CONSTRAINT chk_performance_review_cycles_period CHECK (review_period_end >= review_period_start),
  CONSTRAINT fk_performance_review_cycles_owner FOREIGN KEY (tenant_id, owner_employee_id)
    REFERENCES employees (tenant_id, employee_id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_performance_review_cycles_tenant_id ON performance_review_cycles (tenant_id);
CREATE INDEX IF NOT EXISTS idx_performance_review_cycles_tenant_status ON performance_review_cycles (tenant_id, status);

CREATE TABLE IF NOT EXISTS performance_goals (
  tenant_id VARCHAR(80) NOT NULL,
  goal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  review_cycle_id UUID NOT NULL,
  employee_id UUID NOT NULL,
  owner_employee_id UUID NOT NULL,
  title VARCHAR(160) NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  metric_name VARCHAR(120) NOT NULL,
  target_value NUMERIC(10,2) NOT NULL,
  current_value NUMERIC(10,2) NOT NULL DEFAULT 0,
  weight NUMERIC(5,2) NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Submitted', 'Approved', 'Rejected')),
  workflow_id UUID,
  approved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_performance_goals_tenant_goal UNIQUE (tenant_id, goal_id),
  CONSTRAINT fk_performance_goals_cycle FOREIGN KEY (tenant_id, review_cycle_id)
    REFERENCES performance_review_cycles (tenant_id, review_cycle_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_performance_goals_employee FOREIGN KEY (tenant_id, employee_id)
    REFERENCES employees (tenant_id, employee_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_performance_goals_owner FOREIGN KEY (tenant_id, owner_employee_id)
    REFERENCES employees (tenant_id, employee_id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_performance_goals_tenant_employee ON performance_goals (tenant_id, employee_id);
CREATE INDEX IF NOT EXISTS idx_performance_goals_tenant_status ON performance_goals (tenant_id, status);

CREATE TABLE IF NOT EXISTS performance_feedback (
  tenant_id VARCHAR(80) NOT NULL,
  feedback_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id UUID NOT NULL,
  provider_employee_id UUID NOT NULL,
  review_cycle_id UUID,
  feedback_type VARCHAR(20) NOT NULL CHECK (feedback_type IN ('Manager', 'Peer', 'Self', 'Upward')),
  strengths TEXT NOT NULL DEFAULT '',
  opportunities TEXT NOT NULL DEFAULT '',
  visibility VARCHAR(20) NOT NULL CHECK (visibility IN ('Private', 'Employee', 'ManagerAndHR')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_performance_feedback_tenant_feedback UNIQUE (tenant_id, feedback_id),
  CONSTRAINT fk_performance_feedback_employee FOREIGN KEY (tenant_id, employee_id)
    REFERENCES employees (tenant_id, employee_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_performance_feedback_provider FOREIGN KEY (tenant_id, provider_employee_id)
    REFERENCES employees (tenant_id, employee_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_performance_feedback_cycle FOREIGN KEY (tenant_id, review_cycle_id)
    REFERENCES performance_review_cycles (tenant_id, review_cycle_id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_performance_feedback_tenant_employee ON performance_feedback (tenant_id, employee_id, created_at DESC);

CREATE TABLE IF NOT EXISTS performance_calibrations (
  tenant_id VARCHAR(80) NOT NULL,
  calibration_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  review_cycle_id UUID NOT NULL,
  facilitator_employee_id UUID NOT NULL,
  department_id UUID NOT NULL,
  proposed_rating NUMERIC(2,1) NOT NULL,
  final_rating NUMERIC(2,1),
  notes TEXT NOT NULL DEFAULT '',
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Submitted', 'Finalized', 'Rejected')),
  workflow_id UUID,
  finalized_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_performance_calibrations_tenant_calibration UNIQUE (tenant_id, calibration_id),
  CONSTRAINT fk_performance_calibrations_cycle FOREIGN KEY (tenant_id, review_cycle_id)
    REFERENCES performance_review_cycles (tenant_id, review_cycle_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_performance_calibrations_facilitator FOREIGN KEY (tenant_id, facilitator_employee_id)
    REFERENCES employees (tenant_id, employee_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_performance_calibrations_department FOREIGN KEY (tenant_id, department_id)
    REFERENCES departments (tenant_id, department_id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_performance_calibrations_tenant_cycle ON performance_calibrations (tenant_id, review_cycle_id, status);

CREATE TABLE IF NOT EXISTS performance_pip_plans (
  tenant_id VARCHAR(80) NOT NULL,
  pip_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id UUID NOT NULL,
  manager_employee_id UUID NOT NULL,
  review_cycle_id UUID,
  reason TEXT NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Submitted', 'Active', 'Completed', 'Cancelled', 'Rejected')),
  workflow_id UUID,
  started_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_performance_pip_plans_tenant_pip UNIQUE (tenant_id, pip_id),
  CONSTRAINT fk_performance_pip_plans_employee FOREIGN KEY (tenant_id, employee_id)
    REFERENCES employees (tenant_id, employee_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_performance_pip_plans_manager FOREIGN KEY (tenant_id, manager_employee_id)
    REFERENCES employees (tenant_id, employee_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_performance_pip_plans_cycle FOREIGN KEY (tenant_id, review_cycle_id)
    REFERENCES performance_review_cycles (tenant_id, review_cycle_id) ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_performance_pip_plans_tenant_employee ON performance_pip_plans (tenant_id, employee_id, status);

CREATE TABLE IF NOT EXISTS performance_pip_milestones (
  tenant_id VARCHAR(80) NOT NULL,
  pip_milestone_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pip_id UUID NOT NULL,
  title VARCHAR(160) NOT NULL,
  due_date DATE NOT NULL,
  success_metric TEXT NOT NULL,
  completed BOOLEAN NOT NULL DEFAULT FALSE,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_performance_pip_milestones_tenant_milestone UNIQUE (tenant_id, pip_milestone_id),
  CONSTRAINT fk_performance_pip_milestones_pip FOREIGN KEY (tenant_id, pip_id)
    REFERENCES performance_pip_plans (tenant_id, pip_id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_performance_pip_milestones_tenant_pip ON performance_pip_milestones (tenant_id, pip_id);


