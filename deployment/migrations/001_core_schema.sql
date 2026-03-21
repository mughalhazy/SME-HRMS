CREATE TABLE IF NOT EXISTS departments (
  tenant_id VARCHAR(80) NOT NULL,
  department_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(150) NOT NULL,
  code VARCHAR(30) NOT NULL,
  description TEXT,
  parent_department_id UUID,
  head_employee_id UUID,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Proposed', 'Active', 'Inactive', 'Archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_departments_tenant_department UNIQUE (tenant_id, department_id),
  CONSTRAINT uq_departments_tenant_name UNIQUE (tenant_id, name),
  CONSTRAINT uq_departments_tenant_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_departments_tenant_id ON departments (tenant_id);
CREATE INDEX IF NOT EXISTS idx_departments_tenant_parent_department_id ON departments (tenant_id, parent_department_id);
CREATE INDEX IF NOT EXISTS idx_departments_tenant_head_employee_id ON departments (tenant_id, head_employee_id);
CREATE INDEX IF NOT EXISTS idx_departments_tenant_status ON departments (tenant_id, status);

CREATE TABLE IF NOT EXISTS roles (
  tenant_id VARCHAR(80) NOT NULL,
  role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(150) NOT NULL,
  level VARCHAR(50),
  description TEXT,
  employment_category VARCHAR(20) NOT NULL CHECK (employment_category IN ('Staff', 'Manager', 'Executive', 'Contractor')),
  permissions TEXT[] NOT NULL DEFAULT '{}',
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Active', 'Inactive', 'Archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_roles_tenant_role UNIQUE (tenant_id, role_id),
  CONSTRAINT uq_roles_tenant_title UNIQUE (tenant_id, title)
);

CREATE INDEX IF NOT EXISTS idx_roles_tenant_id ON roles (tenant_id);
CREATE INDEX IF NOT EXISTS idx_roles_tenant_status ON roles (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_roles_tenant_employment_category ON roles (tenant_id, employment_category);

CREATE TABLE IF NOT EXISTS employees (
  tenant_id VARCHAR(80) NOT NULL,
  employee_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_number VARCHAR(40) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(30),
  hire_date DATE NOT NULL,
  employment_type VARCHAR(20) NOT NULL CHECK (employment_type IN ('FullTime', 'PartTime', 'Contract', 'Intern')),
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Active', 'OnLeave', 'Suspended', 'Terminated')),
  department_id UUID NOT NULL,
  role_id UUID NOT NULL,
  manager_employee_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_employees_tenant_employee UNIQUE (tenant_id, employee_id),
  CONSTRAINT uq_employees_tenant_employee_number UNIQUE (tenant_id, employee_number),
  CONSTRAINT uq_employees_tenant_email UNIQUE (tenant_id, email),
  CONSTRAINT fk_employees_department
    FOREIGN KEY (tenant_id, department_id)
    REFERENCES departments (tenant_id, department_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_employees_role
    FOREIGN KEY (tenant_id, role_id)
    REFERENCES roles (tenant_id, role_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_employees_manager
    FOREIGN KEY (tenant_id, manager_employee_id)
    REFERENCES employees (tenant_id, employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_employees_tenant_id ON employees (tenant_id);
CREATE INDEX IF NOT EXISTS idx_employees_tenant_department_id ON employees (tenant_id, department_id);
CREATE INDEX IF NOT EXISTS idx_employees_tenant_role_id ON employees (tenant_id, role_id);
CREATE INDEX IF NOT EXISTS idx_employees_tenant_manager_employee_id ON employees (tenant_id, manager_employee_id);
CREATE INDEX IF NOT EXISTS idx_employees_tenant_status ON employees (tenant_id, status);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_departments_parent_department'
  ) THEN
    ALTER TABLE departments
      ADD CONSTRAINT fk_departments_parent_department
      FOREIGN KEY (tenant_id, parent_department_id)
      REFERENCES departments (tenant_id, department_id)
      ON UPDATE CASCADE
      ON DELETE RESTRICT;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_departments_head_employee'
  ) THEN
    ALTER TABLE departments
      ADD CONSTRAINT fk_departments_head_employee
      FOREIGN KEY (tenant_id, head_employee_id)
      REFERENCES employees (tenant_id, employee_id)
      ON UPDATE CASCADE
      ON DELETE RESTRICT;
  END IF;
END $$;
