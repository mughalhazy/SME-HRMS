CREATE TABLE IF NOT EXISTS engagement_surveys (
  tenant_id VARCHAR(80) NOT NULL,
  survey_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code VARCHAR(80) NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Open', 'Closed')),
  owner_employee_id UUID NOT NULL,
  target_department_id UUID,
  published_at TIMESTAMPTZ,
  closed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_engagement_surveys_tenant_code UNIQUE (tenant_id, code),
  CONSTRAINT fk_engagement_surveys_owner FOREIGN KEY (tenant_id, owner_employee_id)
    REFERENCES employees (tenant_id, employee_id)
    ON UPDATE CASCADE,
  CONSTRAINT fk_engagement_surveys_department FOREIGN KEY (tenant_id, target_department_id)
    REFERENCES departments (tenant_id, department_id)
    ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_engagement_surveys_tenant_status ON engagement_surveys (tenant_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS engagement_survey_questions (
  tenant_id VARCHAR(80) NOT NULL,
  question_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  survey_id UUID NOT NULL,
  prompt TEXT NOT NULL,
  dimension VARCHAR(2) NOT NULL CHECK (dimension IN ('D1', 'D2', 'D3', 'D4', 'D5')),
  kind VARCHAR(20) NOT NULL CHECK (kind IN ('Likert5')),
  required BOOLEAN NOT NULL DEFAULT TRUE,
  scale_min INTEGER NOT NULL DEFAULT 1,
  scale_max INTEGER NOT NULL DEFAULT 5,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fk_engagement_questions_survey FOREIGN KEY (tenant_id, survey_id)
    REFERENCES engagement_surveys (tenant_id, survey_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_engagement_questions_survey ON engagement_survey_questions (tenant_id, survey_id);

CREATE TABLE IF NOT EXISTS engagement_survey_responses (
  tenant_id VARCHAR(80) NOT NULL,
  response_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  survey_id UUID NOT NULL,
  employee_id UUID NOT NULL,
  overall_comment TEXT,
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_engagement_responses_tenant_survey_employee UNIQUE (tenant_id, survey_id, employee_id),
  CONSTRAINT fk_engagement_responses_survey FOREIGN KEY (tenant_id, survey_id)
    REFERENCES engagement_surveys (tenant_id, survey_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_engagement_responses_employee FOREIGN KEY (tenant_id, employee_id)
    REFERENCES employees (tenant_id, employee_id)
    ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_engagement_responses_survey ON engagement_survey_responses (tenant_id, survey_id, submitted_at DESC);

CREATE TABLE IF NOT EXISTS engagement_survey_answers (
  tenant_id VARCHAR(80) NOT NULL,
  answer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  response_id UUID NOT NULL,
  question_id UUID NOT NULL,
  score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
  comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_engagement_answers_response_question UNIQUE (tenant_id, response_id, question_id),
  CONSTRAINT fk_engagement_answers_response FOREIGN KEY (tenant_id, response_id)
    REFERENCES engagement_survey_responses (tenant_id, response_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT fk_engagement_answers_question FOREIGN KEY (tenant_id, question_id)
    REFERENCES engagement_survey_questions (tenant_id, question_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_engagement_answers_response ON engagement_survey_answers (tenant_id, response_id);

CREATE TABLE IF NOT EXISTS engagement_survey_aggregates (
  tenant_id VARCHAR(80) NOT NULL,
  survey_id UUID PRIMARY KEY,
  response_count INTEGER NOT NULL DEFAULT 0,
  participant_count INTEGER NOT NULL DEFAULT 0,
  target_population INTEGER NOT NULL DEFAULT 0,
  participation_rate NUMERIC(6,4) NOT NULL DEFAULT 0,
  overall_average_score NUMERIC(6,2) NOT NULL DEFAULT 0,
  favorable_ratio NUMERIC(6,4) NOT NULL DEFAULT 0,
  question_scores JSONB NOT NULL,
  dimension_scores JSONB NOT NULL,
  score_distribution JSONB NOT NULL,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fk_engagement_aggregates_survey FOREIGN KEY (tenant_id, survey_id)
    REFERENCES engagement_surveys (tenant_id, survey_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);
