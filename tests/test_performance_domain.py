from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_SCRIPT = """
const assert = require('node:assert/strict');
const { EmployeeRepository } = require('./services/employee-service/employee.repository.js');
const { PerformanceReviewRepository } = require('./services/employee-service/performance.repository.js');
const { EmployeeService } = require('./services/employee-service/employee.service.js');
const { PerformanceReviewService } = require('./services/employee-service/performance.service.js');
const { ConflictError } = require('./services/employee-service/service.errors.js');
const { ValidationError } = require('./services/employee-service/employee.validation.js');

const employeeRepository = new EmployeeRepository();
const employeeService = new EmployeeService(employeeRepository);
const reviewRepository = new PerformanceReviewRepository({
  findEmployeeById: (employeeId) => employeeRepository.findById(employeeId),
  findDepartmentById: (departmentId) => employeeRepository.findDepartmentById(departmentId),
});
const service = new PerformanceReviewService(reviewRepository, employeeRepository);

const reviewer = employeeService.createEmployee({
  employee_number: 'E-200',
  first_name: 'Helen',
  last_name: 'Brooks',
  email: 'helen.review@example.com',
  phone: '+1 555-2000',
  hire_date: '2024-01-10',
  employment_type: 'FullTime',
  status: 'Active',
  department_id: 'dep-eng',
  role_id: 'role-frontend-engineer',
});

const employee = employeeService.createEmployee({
  employee_number: 'E-201',
  first_name: 'Noah',
  last_name: 'Bennett',
  email: 'noah.review@example.com',
  phone: '+1 555-2001',
  hire_date: '2025-02-01',
  employment_type: 'FullTime',
  status: 'Active',
  department_id: 'dep-eng',
  role_id: 'role-frontend-engineer',
  manager_employee_id: reviewer.employee_id,
});

const review = service.createReview({
  employee_id: employee.employee_id,
  reviewer_employee_id: reviewer.employee_id,
  review_period_start: '2026-01-01',
  review_period_end: '2026-03-31',
});
assert.equal(review.status, 'Draft');

const updated = service.updateReview(review.performance_review_id, {
  overall_rating: 4.6,
  strengths: 'Delivers high-quality work',
  improvement_areas: 'Delegate more often',
  goals_next_period: 'Lead the next release stream',
});
assert.equal(updated.overall_rating, 4.6);

const submitted = service.submitReview(review.performance_review_id);
assert.equal(submitted.status, 'Submitted');
assert.ok(submitted.submitted_at);

const finalized = service.finalizeReview(review.performance_review_id);
assert.equal(finalized.status, 'Finalized');
assert.ok(finalized.finalized_at);

const fetched = service.getReviewById(review.performance_review_id);
assert.equal(fetched.status, 'Finalized');
const readModels = service.getReviewReadModels(review.performance_review_id);
assert.equal(readModels.performance_review_view.employee_name, 'Noah Bennett');
assert.equal(readModels.performance_review_view.reviewer_name, 'Helen Brooks');
assert.equal(readModels.performance_review_view.department_name, 'Engineering');

const listed = service.listReviews({ reviewer_employee_id: reviewer.employee_id, limit: 10 });
assert.equal(listed.data.length, 1);
assert.equal(listed.data[0].performance_review_id, review.performance_review_id);

assert.throws(
  () => service.createReview({
    employee_id: employee.employee_id,
    reviewer_employee_id: reviewer.employee_id,
    review_period_start: '2026-01-01',
    review_period_end: '2026-03-31',
  }),
  ConflictError,
);

assert.throws(
  () => service.updateReview(review.performance_review_id, { strengths: 'Late edit attempt' }),
  ConflictError,
);

const secondReview = service.createReview({
  employee_id: employee.employee_id,
  reviewer_employee_id: reviewer.employee_id,
  review_period_start: '2026-04-01',
  review_period_end: '2026-06-30',
});
assert.throws(() => service.finalizeReview(secondReview.performance_review_id), ValidationError);
"""


def test_performance_review_service_crud_and_lifecycle() -> None:
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
                    "{ROOT / 'services/employee-service/performance.model.ts'}",
                    "{ROOT / 'services/employee-service/performance.validation.ts'}",
                    "{ROOT / 'services/employee-service/performance.repository.ts'}",
                    "{ROOT / 'services/employee-service/performance.service.ts'}",
                    "{ROOT / 'services/employee-service/service.errors.ts'}",
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
        assert (tmpdir / 'out' / 'services' / 'employee-service' / 'performance.service.js').exists(), compile_result.stderr + compile_result.stdout

        runtime_file = tmpdir / 'out' / 'performance-domain.runtime.cjs'
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
