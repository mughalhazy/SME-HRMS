from __future__ import annotations

import json
import os
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_SCRIPT = """
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { EmployeeRepository } = require('./services/employee-service/employee.repository.js');
const { EmployeeService } = require('./services/employee-service/employee.service.js');
const { LearningRepository } = require('./services/employee-service/learning.repository.js');
const { LearningService } = require('./services/employee-service/learning.service.js');
const { LearningController } = require('./services/employee-service/learning.controller.js');
const { ConflictError } = require('./services/employee-service/service.errors.js');

function createResponse() {
  return {
    statusCode: 200,
    payload: undefined,
    status(code) { this.statusCode = code; return this; },
    json(payload) { this.payload = payload; return this; },
    send(body) { this.payload = body; return this; },
    setHeader() { return this; },
  };
}

const employeeRepository = new EmployeeRepository({ tenantId: 'tenant-default' });
const employeeService = new EmployeeService(employeeRepository, undefined, undefined, 'tenant-default');
const manager = employeeService.createEmployee({
  tenant_id: 'tenant-default',
  employee_number: 'E-501',
  first_name: 'Morgan',
  last_name: 'Lee',
  email: 'morgan.lee@example.com',
  hire_date: '2026-01-10',
  employment_type: 'FullTime',
  status: 'Active',
  department_id: 'dep-eng',
  role_id: 'role-ops-lead',
});
const employee = employeeService.createEmployee({
  tenant_id: 'tenant-default',
  employee_number: 'E-502',
  first_name: 'Jamie',
  last_name: 'Park',
  email: 'jamie.park@example.com',
  hire_date: '2026-01-12',
  employment_type: 'FullTime',
  status: 'Active',
  department_id: 'dep-eng',
  role_id: 'role-frontend-engineer',
  manager_employee_id: manager.employee_id,
});

const repository = new LearningRepository();
const service = new LearningService(repository, employeeRepository, 'tenant-default');
const controller = new LearningController(service, employeeService);

const course = service.createCourse({
  tenant_id: 'tenant-default',
  course_code: 'SAFE-100',
  title: 'Workplace Safety Basics',
  category: 'Compliance',
  delivery_mode: 'SelfPaced',
  duration_hours: 2,
  validity_days: 30,
  status: 'Published',
});
assert.equal(course.status, 'Published');
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'learning.course.created'), true);

const enrollment = service.createEnrollment({
  tenant_id: 'tenant-default',
  course_id: course.course_id,
  employee_id: employee.employee_id,
  due_date: '2026-12-15',
  assigned_by: manager.employee_id,
});
assert.equal(enrollment.employee_id, employee.employee_id);
assert.equal(enrollment.status, 'Enrolled');
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'learning.enrollment.created'), true);
assert.throws(() => service.createEnrollment({
  tenant_id: 'tenant-default',
  course_id: course.course_id,
  employee_id: employee.employee_id,
}), ConflictError);

const progressed = service.updateEnrollmentProgress(enrollment.enrollment_id, {
  tenant_id: 'tenant-default',
  progress_percent: 60,
  notes: 'Completed core modules',
});
assert.equal(progressed.status, 'InProgress');
assert.equal(progressed.progress_percent, 60);
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'learning.enrollment.progress.updated'), true);

const completionResult = service.recordCompletion(enrollment.enrollment_id, {
  tenant_id: 'tenant-default',
  status: 'Passed',
  score_percent: 96,
  certificate_id: 'CERT-123',
  recorded_by: manager.employee_id,
});
assert.equal(completionResult.enrollment.status, 'Completed');
assert.equal(completionResult.enrollment.progress_percent, 100);
assert.equal(completionResult.completion.status, 'Passed');
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'learning.completion.recorded'), true);

const completions = service.listCompletions({ tenant_id: 'tenant-default', employee_id: employee.employee_id });
assert.equal(completions.length, 1);
const learningPath = service.createLearningPath({
  tenant_id: 'tenant-default',
  code: 'ONB-ENG',
  title: 'Engineering Onboarding',
  course_ids: [course.course_id],
});
assert.equal(learningPath.course_ids.length, 1);
const certifications = service.listEmployeeCertifications(employee.employee_id);
assert.equal(certifications.length, 1);
assert.equal(certifications[0].certificate_id, 'CERT-123');
const analytics = service.getLearningAnalytics();
assert.equal(analytics.totals.learning_paths, 1);
assert.equal(analytics.totals.certifications, 1);
const summary = service.getEmployeeLearningSummary(employee.employee_id);
assert.equal(summary.completed_enrollments, 1);
assert.equal(summary.active_enrollments, 0);
assert.equal(summary.required_refresh_count, 0);

const req = {
  traceId: 'trace-learning-audit',
  tenantId: 'tenant-default',
  headers: {},
  auth: { role: 'Admin', employee_id: 'admin-1', capabilities: ['CAP-EMP-001', 'CAP-EMP-002'], scopes: [], subject_type: 'user' },
  params: {},
  query: {},
  body: {
    course_code: 'PRIV-200',
    title: 'Privacy Refresher',
    category: 'Compliance',
    delivery_mode: 'Virtual',
    duration_hours: 1.5,
    status: 'Published',
  },
};
const res = createResponse();
controller.createCourse(req, res);
assert.equal(res.statusCode, 201);

const pathReq = {
  ...req,
  body: {
    code: 'PRIV-PATH',
    title: 'Privacy Path',
    course_ids: [course.course_id],
  },
};
const pathRes = createResponse();
controller.createLearningPath(pathReq, pathRes);
assert.equal(pathRes.statusCode, 201);

const certReq = { ...req, params: { employeeId: employee.employee_id }, query: {}, body: {} };
const certRes = createResponse();
controller.getEmployeeCertifications(certReq, certRes);
assert.equal(certRes.statusCode, 200);
assert.equal(certRes.payload.data.length, 1);

const records = fs.readFileSync(process.env.HRMS_AUDIT_LOG_PATH, 'utf8').trim().split('\\n').map((line) => JSON.parse(line));
const auditRecord = records.find((record) => record.action === 'learning_course_created');
assert.ok(auditRecord, 'expected learning_course_created audit record');
assert.equal(auditRecord.entity, 'LearningCourse');
const pathAuditRecord = records.find((record) => record.action === 'learning_path_created');
assert.ok(pathAuditRecord, 'expected learning_path_created audit record');
"""


def test_learning_service_tracks_courses_enrollments_and_completion_with_employee_links() -> None:
    audit_log = ROOT / '.tmp-learning-audit.jsonl'
    if audit_log.exists():
        audit_log.unlink()

    tmpdir = Path(subprocess.check_output(['mktemp', '-d'], cwd=ROOT, text=True).strip())
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
                    "{ROOT / 'middleware' / 'audit.ts'}",
                    "{ROOT / 'middleware' / 'audit-store.ts'}",
                    "{ROOT / 'middleware' / 'logger.ts'}",
                    "{ROOT / 'middleware' / 'error-handler.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'domain-seed.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'department.model.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'role.model.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'employee.model.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'employee.validation.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'service.errors.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'employee.repository.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'employee.service.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'event-outbox.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'learning.model.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'learning.repository.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'learning.service.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'learning.controller.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'rbac.middleware.ts'}",
                    "{ROOT / 'cache' / 'cache.service.ts'}",
                    "{ROOT / 'db' / 'optimization.ts'}"
                  ]
                }}
                """
            ).strip()
        )
        compile_result = subprocess.run(['tsc', '-p', str(tsconfig)], cwd=ROOT, capture_output=True, text=True, check=False)
        assert (tmpdir / 'out' / 'services' / 'employee-service' / 'learning.service.js').exists(), compile_result.stderr + compile_result.stdout

        runtime_file = tmpdir / 'out' / 'learning.runtime.cjs'
        runtime_file.write_text(textwrap.dedent(RUNTIME_SCRIPT).strip())

        run_result = subprocess.run(
            ['node', str(runtime_file)],
            cwd=tmpdir / 'out',
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, 'HRMS_AUDIT_LOG_PATH': str(audit_log), 'AUTH_TOKEN_SECRET': 'x' * 32},
        )
        assert run_result.returncode == 0, run_result.stderr + run_result.stdout

        records = [json.loads(line) for line in audit_log.read_text().splitlines() if line.strip()]
        assert any(record['action'] == 'learning_course_created' for record in records)
    finally:
        subprocess.run(['rm', '-rf', str(tmpdir)], check=False)
        if audit_log.exists():
            audit_log.unlink()
