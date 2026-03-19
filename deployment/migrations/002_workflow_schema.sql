CREATE TABLE IF NOT EXISTS attendance_records (
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
  CONSTRAINT uq_attendance_records_employee_date UNIQUE (employee_id, attendance_date),
  CONSTRAINT fk_attendance_records_employee
    FOREIGN KEY (employee_id)
    REFERENCES employees (employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_attendance_records_employee_id ON attendance_records (employee_id);
CREATE INDEX IF NOT EXISTS idx_attendance_records_date ON attendance_records (attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_records_status ON attendance_records (attendance_status);

CREATE TABLE IF NOT EXISTS leave_requests (
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
  CONSTRAINT chk_leave_requests_date_range CHECK (end_date >= start_date),
  CONSTRAINT fk_leave_requests_employee
    FOREIGN KEY (employee_id)
    REFERENCES employees (employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_leave_requests_approver
    FOREIGN KEY (approver_employee_id)
    REFERENCES employees (employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_id ON leave_requests (employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_approver_employee_id ON leave_requests (approver_employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests (status);
CREATE INDEX IF NOT EXISTS idx_leave_requests_date_range ON leave_requests (start_date, end_date);

CREATE TABLE IF NOT EXISTS payroll_records (
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
  CONSTRAINT chk_payroll_records_period CHECK (pay_period_end >= pay_period_start),
  CONSTRAINT uq_payroll_records_employee_period UNIQUE (employee_id, pay_period_start, pay_period_end),
  CONSTRAINT fk_payroll_records_employee
    FOREIGN KEY (employee_id)
    REFERENCES employees (employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_payroll_records_employee_id ON payroll_records (employee_id);
CREATE INDEX IF NOT EXISTS idx_payroll_records_status ON payroll_records (status);
CREATE INDEX IF NOT EXISTS idx_payroll_records_payment_date ON payroll_records (payment_date);

CREATE TABLE IF NOT EXISTS job_postings (
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
  CONSTRAINT chk_job_postings_dates CHECK (closing_date IS NULL OR closing_date >= posting_date),
  CONSTRAINT fk_job_postings_department
    FOREIGN KEY (department_id)
    REFERENCES departments (department_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_job_postings_role
    FOREIGN KEY (role_id)
    REFERENCES roles (role_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_job_postings_department_id ON job_postings (department_id);
CREATE INDEX IF NOT EXISTS idx_job_postings_role_id ON job_postings (role_id);
CREATE INDEX IF NOT EXISTS idx_job_postings_status ON job_postings (status);
CREATE INDEX IF NOT EXISTS idx_job_postings_posting_date ON job_postings (posting_date);

CREATE TABLE IF NOT EXISTS candidates (
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
  CONSTRAINT uq_candidates_posting_email UNIQUE (job_posting_id, email),
  CONSTRAINT fk_candidates_job_posting
    FOREIGN KEY (job_posting_id)
    REFERENCES job_postings (job_posting_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidates_job_posting_id ON candidates (job_posting_id);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates (status);
CREATE INDEX IF NOT EXISTS idx_candidates_application_date ON candidates (application_date);
CREATE INDEX IF NOT EXISTS idx_candidates_source_candidate_id ON candidates (source_candidate_id);

CREATE TABLE IF NOT EXISTS candidate_stage_transitions (
  candidate_stage_transition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  candidate_id UUID NOT NULL,
  from_status VARCHAR(20) CHECK (from_status IN ('Applied', 'Screening', 'Interviewing', 'Offered', 'Hired', 'Rejected', 'Withdrawn')),
  to_status VARCHAR(20) NOT NULL CHECK (to_status IN ('Applied', 'Screening', 'Interviewing', 'Offered', 'Hired', 'Rejected', 'Withdrawn')),
  changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  changed_by VARCHAR(120),
  reason TEXT,
  notes TEXT,
  CONSTRAINT fk_candidate_stage_transitions_candidate
    FOREIGN KEY (candidate_id)
    REFERENCES candidates (candidate_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidate_stage_transitions_candidate_id ON candidate_stage_transitions (candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_stage_transitions_changed_at ON candidate_stage_transitions (changed_at);
CREATE INDEX IF NOT EXISTS idx_candidate_stage_transitions_to_status ON candidate_stage_transitions (to_status);

CREATE TABLE IF NOT EXISTS interviews (
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
  CONSTRAINT chk_interviews_schedule CHECK (scheduled_end > scheduled_start),
  CONSTRAINT fk_interviews_candidate
    FOREIGN KEY (candidate_id)
    REFERENCES candidates (candidate_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON interviews (candidate_id);
CREATE INDEX IF NOT EXISTS idx_interviews_schedule ON interviews (scheduled_start, scheduled_end);
CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews (status);

CREATE TABLE IF NOT EXISTS performance_reviews (
  performance_review_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_id UUID NOT NULL,
  reviewer_employee_id UUID NOT NULL,
  review_period_start DATE NOT NULL,
  review_period_end DATE NOT NULL,
  overall_rating NUMERIC(2,1),
  strengths TEXT,
  improvement_areas TEXT,
  goals_next_period TEXT,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Submitted', 'Acknowledged', 'Finalized')),
  submitted_at TIMESTAMPTZ,
  acknowledged_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_performance_reviews_period CHECK (review_period_end >= review_period_start),
  CONSTRAINT uq_performance_reviews_cycle UNIQUE (employee_id, review_period_start, review_period_end),
  CONSTRAINT fk_performance_reviews_employee
    FOREIGN KEY (employee_id)
    REFERENCES employees (employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_performance_reviews_reviewer
    FOREIGN KEY (reviewer_employee_id)
    REFERENCES employees (employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_performance_reviews_employee_id ON performance_reviews (employee_id);
CREATE INDEX IF NOT EXISTS idx_performance_reviews_reviewer_employee_id ON performance_reviews (reviewer_employee_id);
CREATE INDEX IF NOT EXISTS idx_performance_reviews_status ON performance_reviews (status);
