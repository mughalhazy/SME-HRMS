from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_SCRIPT = """
const assert = require('node:assert/strict');
const { EmployeeRepository } = require('./services/employee-service/employee.repository.js');
const { EmployeeService } = require('./services/employee-service/employee.service.js');
const { CompensationRepository } = require('./services/employee-service/compensation.repository.js');
const { CompensationService } = require('./services/employee-service/compensation.service.js');
const { ConflictError } = require('./services/employee-service/service.errors.js');
const { ValidationError } = require('./services/employee-service/employee.validation.js');

const employeeRepository = new EmployeeRepository();
const employeeService = new EmployeeService(employeeRepository);
const compensationRepository = new CompensationRepository({
  findEmployeeById: (employeeId) => employeeRepository.findById(employeeId),
  findDepartmentById: (departmentId) => employeeRepository.findDepartmentById(departmentId),
  findGradeBandById: (gradeBandId) => employeeRepository.findGradeBandById(gradeBandId),
});
const service = new CompensationService(compensationRepository, employeeRepository);

const employee = employeeService.createEmployee({
  employee_number: 'E-300',
  first_name: 'Ava',
  last_name: 'Cole',
  email: 'ava.comp@example.com',
  hire_date: '2025-01-10',
  employment_type: 'FullTime',
  status: 'Active',
  department_id: 'dep-eng',
  role_id: 'role-frontend-engineer',
  grade_band_id: 'gb-ic3',
  cost_center_id: 'cc-eng-001',
});

const band = service.createCompensationBand({
  grade_band_id: 'gb-ic3',
  name: 'IC3 Engineering USD',
  code: 'IC3-USD',
  currency: 'USD',
  min_salary: '5000.00',
  max_salary: '9000.00',
  target_salary: '7000.00',
  status: 'Active',
});
assert.equal(band.status, 'Active');

const revision = service.createSalaryRevision({
  employee_id: employee.employee_id,
  compensation_band_id: band.compensation_band_id,
  effective_from: '2026-01-01',
  base_salary: '7200.00',
  currency: 'USD',
  reason: 'Annual review',
  status: 'Approved',
});
assert.equal(revision.base_salary, '7200.00');

const plan = service.createBenefitsPlan({
  name: 'Health Plus',
  code: 'HLTH-PLUS',
  plan_type: 'Health',
  provider: 'CareCo',
  currency: 'USD',
  employee_contribution_default: '125.00',
  employer_contribution_default: '325.00',
  payroll_deduction_code: 'BEN-HEALTH',
  status: 'Active',
});
assert.equal(plan.status, 'Active');

const enrollment = service.createBenefitsEnrollment({
  employee_id: employee.employee_id,
  benefits_plan_id: plan.benefits_plan_id,
  effective_from: '2026-01-01',
  coverage_level: 'Employee+Family',
  employee_contribution: '150.00',
  employer_contribution: '350.00',
  status: 'Active',
});
assert.equal(enrollment.employee_contribution, '150.00');

const allowance = service.createAllowance({
  employee_id: employee.employee_id,
  name: 'Transport',
  code: 'ALLOW-TRANS',
  amount: '250.00',
  currency: 'USD',
  taxable: true,
  recurring: true,
  effective_from: '2026-01-01',
  status: 'Active',
});
assert.equal(allowance.amount, '250.00');

const context = service.getEmployeePayrollCompensationContext(employee.employee_id, '2026-02-01');
assert.equal(context.base_salary, '7200.00');
assert.equal(context.allowances, '250.00');
assert.equal(context.deductions, '150.00');
assert.equal(context.allowance_items.length, 1);
assert.equal(context.benefits_deductions.length, 1);

const readModel = service.getEmployeeCompensationReadModel(employee.employee_id, '2026-02-01');
assert.equal(readModel.employee_name, 'Ava Cole');
assert.equal(readModel.allowances_total, '250.00');
assert.equal(readModel.benefit_deductions_total, '150.00');

const forecast = service.forecastWorkforcePlan({
  effective_date: '2026-02-01',
  forecast_months: 6,
  departments: [
    {
      department_id: 'dep-eng',
      planned_headcount: 3,
      compensation_band_id: band.compensation_band_id,
      average_allowances: '100.00',
      average_deductions: '50.00',
      average_employer_contributions: '200.00',
    },
  ],
});
assert.equal(forecast.headcount_plan.current_headcount, 1);
assert.equal(forecast.headcount_plan.planned_headcount, 3);
assert.equal(forecast.headcount_plan.required_hires, 2);
assert.equal(forecast.salary_forecast.monthly_base_salary, '21200.00');
assert.equal(forecast.salary_forecast.monthly_allowances, '450.00');
assert.equal(forecast.salary_forecast.monthly_employee_deductions, '250.00');
assert.equal(forecast.salary_forecast.monthly_employer_contributions, '750.00');
assert.equal(forecast.salary_forecast.monthly_payroll_cost, '22400.00');
assert.equal(forecast.salary_forecast.forecast_payroll_cost, '134400.00');
assert.equal(forecast.department_budgets[0].department_name, 'Engineering');

assert.throws(() => service.createSalaryRevision({
  employee_id: employee.employee_id,
  compensation_band_id: band.compensation_band_id,
  effective_from: '2026-01-15',
  base_salary: '7300.00',
  currency: 'USD',
  status: 'Approved',
}), ConflictError);

assert.throws(() => service.createBenefitsEnrollment({
  employee_id: employee.employee_id,
  benefits_plan_id: plan.benefits_plan_id,
  effective_from: '2026-01-15',
  employee_contribution: '100.00',
  employer_contribution: '250.00',
  status: 'Active',
}), ConflictError);

assert.throws(() => service.createAllowance({
  employee_id: employee.employee_id,
  name: 'Transport Bonus',
  code: 'ALLOW-TRANS',
  amount: '50.00',
  effective_from: '2026-03-01',
  status: 'Active',
}), ConflictError);

assert.throws(() => service.createSalaryRevision({
  employee_id: employee.employee_id,
  compensation_band_id: band.compensation_band_id,
  effective_from: '2027-01-01',
  base_salary: '12000.00',
  currency: 'USD',
  status: 'Approved',
}), ValidationError);
"""


def test_compensation_service_domain_and_payroll_context() -> None:
    with subprocess.Popen(
        ['mktemp', '-d'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=ROOT,
    ) as proc:
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, stderr
        tmpdir = Path(stdout.strip())

    try:
        tsconfig = tmpdir / 'tsconfig.json'
        tsconfig.write_text(
            textwrap.dedent(
                f"""
                {{
                  "compilerOptions": {{
                    "target": "ES2022",
                    "module": "CommonJS",
                    "moduleResolution": "Node",
                    "outDir": "./out",
                    "rootDir": "{ROOT}",
                    "esModuleInterop": true,
                    "skipLibCheck": true,
                    "strict": false,
                    "noEmitOnError": false
                  }},
                  "include": [
                    "{ROOT / 'services/employee-service/employee.model.ts'}",
                    "{ROOT / 'services/employee-service/employee.validation.ts'}",
                    "{ROOT / 'services/employee-service/employee.repository.ts'}",
                    "{ROOT / 'services/employee-service/employee.service.ts'}",
                    "{ROOT / 'services/employee-service/domain-seed.ts'}",
                    "{ROOT / 'services/employee-service/service.errors.ts'}",
                    "{ROOT / 'services/employee-service/event-outbox.ts'}",
                    "{ROOT / 'services/employee-service/compensation.model.ts'}",
                    "{ROOT / 'services/employee-service/compensation.validation.ts'}",
                    "{ROOT / 'services/employee-service/compensation.repository.ts'}",
                    "{ROOT / 'services/employee-service/compensation.service.ts'}",
                    "{ROOT / 'cache/cache.service.ts'}",
                    "{ROOT / 'db/optimization.ts'}"
                  ]
                }}
                """
            ).strip()
        )

        compile_result = subprocess.run(
            ['tsc', '-p', str(tsconfig)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert (tmpdir / 'out' / 'services' / 'employee-service' / 'compensation.service.js').exists(), compile_result.stderr + compile_result.stdout

        runtime_file = tmpdir / 'out' / 'compensation-domain.runtime.cjs'
        runtime_file.write_text(textwrap.dedent(RUNTIME_SCRIPT).strip())

        run_result = subprocess.run(
            ['node', str(runtime_file)],
            cwd=tmpdir / 'out',
            capture_output=True,
            text=True,
            check=False,
        )
        assert run_result.returncode == 0, run_result.stderr + run_result.stdout
    finally:
        subprocess.run(['rm', '-rf', str(tmpdir)], check=False)
