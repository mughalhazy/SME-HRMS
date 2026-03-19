CREATE TABLE IF NOT EXISTS departments (
  department_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(150) NOT NULL UNIQUE,
  code VARCHAR(30) NOT NULL UNIQUE,
  description TEXT,
  parent_department_id UUID,
  head_employee_id UUID,
  status VARCHAR(20) NOT NULL CHECK (status IN ('Proposed', 'Active', 'Inactive', 'Archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_departments_parent_department_id ON departments (parent_department_id);
CREATE INDEX IF NOT EXISTS idx_departments_head_employee_id ON departments (head_employee_id);
CREATE INDEX IF NOT EXISTS idx_departments_status ON departments (status);

CREATE TABLE IF NOT EXISTS roles (
  role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(150) NOT NULL,
  level VARCHAR(50),
  description TEXT,
  employment_category VARCHAR(20) NOT NULL CHECK (employment_category IN ('Staff', 'Manager', 'Executive', 'Contractor')),
  status VARCHAR(20) NOT NULL CHECK (status IN ('Active', 'Inactive', 'Archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_roles_title ON roles (title);
CREATE INDEX IF NOT EXISTS idx_roles_status ON roles (status);

CREATE TABLE IF NOT EXISTS employees (
  employee_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  employee_number VARCHAR(40) NOT NULL UNIQUE,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone VARCHAR(30),
  hire_date DATE NOT NULL,
  employment_type VARCHAR(20) NOT NULL CHECK (employment_type IN ('FullTime', 'PartTime', 'Contract', 'Intern')),
  status VARCHAR(20) NOT NULL CHECK (status IN ('Draft', 'Active', 'OnLeave', 'Suspended', 'Terminated')),
  department_id UUID NOT NULL,
  role_id UUID NOT NULL,
  manager_employee_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT fk_employees_department
    FOREIGN KEY (department_id)
    REFERENCES departments (department_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_employees_role
    FOREIGN KEY (role_id)
    REFERENCES roles (role_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT fk_employees_manager
    FOREIGN KEY (manager_employee_id)
    REFERENCES employees (employee_id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees (department_id);
CREATE INDEX IF NOT EXISTS idx_employees_role_id ON employees (role_id);
CREATE INDEX IF NOT EXISTS idx_employees_manager_employee_id ON employees (manager_employee_id);
CREATE INDEX IF NOT EXISTS idx_employees_status ON employees (status);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_departments_parent_department'
  ) THEN
    ALTER TABLE departments
      ADD CONSTRAINT fk_departments_parent_department
      FOREIGN KEY (parent_department_id)
      REFERENCES departments (department_id)
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
      FOREIGN KEY (head_employee_id)
      REFERENCES employees (employee_id)
      ON UPDATE CASCADE
      ON DELETE RESTRICT;
  END IF;
END $$;
