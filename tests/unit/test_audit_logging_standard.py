from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RUNTIME_SCRIPT = r'''
const assert = require('node:assert/strict');
const { getStructuredLogger } = require('./middleware/logger.js');
const { EmployeeRepository } = require('./services/employee-service/employee.repository.js');
const { EmployeeService } = require('./services/employee-service/employee.service.js');
const { EmployeeController } = require('./services/employee-service/employee.controller.js');
const { SettingsRepository } = require('./services/settings-service/settings.repository.js');
const { SettingsService } = require('./services/settings-service/settings.service.js');
const { SettingsController } = require('./services/settings-service/settings.controller.js');

function createResponse() {
  return {
    statusCode: 200,
    payload: undefined,
    body: undefined,
    status(code) {
      this.statusCode = code;
      return this;
    },
    json(payload) {
      this.payload = payload;
      return this;
    },
    send(body) {
      this.body = body;
      return this;
    },
    setHeader() {
      return this;
    },
  };
}

const employeeRepository = new EmployeeRepository({ tenantId: 'tenant-default' });
const employeeService = new EmployeeService(employeeRepository, undefined, undefined, undefined, 'tenant-default');
const employeeController = new EmployeeController(employeeService);
const employeeLogger = getStructuredLogger('employee-service');

const employeeBaseReq = {
  traceId: 'trace-employee-1',
  headers: {},
  auth: { role: 'Admin', employee_id: 'admin-1' },
};

let req = {
  ...employeeBaseReq,
  body: {
    tenant_id: 'tenant-default',
    employee_number: 'E-500',
    first_name: 'Avery',
    last_name: 'Coleman',
    email: 'avery.coleman@example.com',
    phone: '+1 555-0500',
    hire_date: '2025-03-01',
    employment_type: 'FullTime',
    department_id: 'dep-eng',
    role_id: 'role-frontend-engineer',
  },
  params: {},
  query: {},
};
let res = createResponse();
employeeController.createEmployee(req, res);
assert.equal(res.statusCode, 201);
const employeeId = res.payload.data.employee_id;
assert.equal(employeeLogger.auditRecords.length, 1);
assert.equal(employeeLogger.auditRecords[0].action, 'employee_created');
assert.deepEqual(employeeLogger.auditRecords[0].before, {});
assert.equal(employeeLogger.auditRecords[0].after.employee_id, employeeId);
assert.equal(employeeLogger.auditRecords[0].actor.id, 'admin-1');
assert.equal(employeeLogger.auditRecords[0].actor.type, 'user');
assert.equal(employeeLogger.auditRecords[0].trace_id, 'trace-employee-1');
assert.ok(employeeLogger.auditRecords[0].audit_id);
assert.ok(Object.isFrozen(employeeLogger.auditRecords[0]));
assert.ok(Object.isFrozen(employeeLogger.auditRecords[0].before));
assert.ok(Object.isFrozen(employeeLogger.auditRecords[0].after));

req = {
  ...employeeBaseReq,
  params: { employeeId },
  query: {},
  body: { phone: '+1 555-0501' },
};
res = createResponse();
employeeController.updateEmployee(req, res);
assert.equal(res.statusCode, 200);
assert.equal(employeeLogger.auditRecords.length, 2);
assert.equal(employeeLogger.auditRecords[1].action, 'employee_updated');
assert.equal(employeeLogger.auditRecords[1].before.phone, '+1 555-0500');
assert.equal(employeeLogger.auditRecords[1].after.phone, '+1 555-0501');

req = {
  ...employeeBaseReq,
  params: { employeeId },
  query: {},
  body: { department_id: 'dep-fin' },
};
res = createResponse();
employeeController.assignDepartment(req, res);
assert.equal(res.statusCode, 200);
assert.equal(employeeLogger.auditRecords.length, 3);
assert.equal(employeeLogger.auditRecords[2].action, 'employee_department_assigned');
assert.equal(employeeLogger.auditRecords[2].before.department_id, 'dep-eng');
assert.equal(employeeLogger.auditRecords[2].after.department_id, 'dep-fin');

req = {
  ...employeeBaseReq,
  params: { employeeId },
  query: {},
  body: { status: 'Active' },
};
res = createResponse();
employeeController.updateStatus(req, res);
assert.equal(res.statusCode, 200);
assert.equal(employeeLogger.auditRecords.length, 4);
assert.equal(employeeLogger.auditRecords[3].action, 'employee_status_updated');
assert.equal(employeeLogger.auditRecords[3].before.status, 'Draft');
assert.equal(employeeLogger.auditRecords[3].after.status, 'Active');

req = {
  ...employeeBaseReq,
  params: { employeeId },
  query: {},
  body: {},
};
res = createResponse();
employeeController.deleteEmployee(req, res);
assert.equal(res.statusCode, 204);
assert.equal(employeeLogger.auditRecords.length, 5);
assert.equal(employeeLogger.auditRecords[4].action, 'employee_deleted');
assert.equal(employeeLogger.auditRecords[4].before.employee_id, employeeId);
assert.deepEqual(employeeLogger.auditRecords[4].after, {});
assert.deepEqual(
  employeeLogger.auditRecords.map((record) => record.entity),
  ['Employee', 'Employee', 'Employee', 'Employee', 'Employee'],
);

const settingsRepository = new SettingsRepository();
const settingsService = new SettingsService(settingsRepository);
const settingsController = new SettingsController(settingsService);
const settingsLogger = getStructuredLogger('settings-service');

const settingsReqBase = {
  traceId: 'trace-settings-1',
  headers: {
    'x-actor-id': 'settings-sync',
    'x-actor-type': 'service',
    'x-actor-role': 'settings-admin',
  },
  params: {},
  query: {},
};

req = {
  ...settingsReqBase,
  body: {
    code: 'HQ-DAY',
    name: 'HQ Day Shift',
    timezone: 'America/New_York',
    workdays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
    standard_work_hours: 8,
    grace_period_minutes: 10,
    late_after_minutes: 15,
    auto_clock_out_hours: 12,
    require_geo_fencing: true,
    status: 'Active',
  },
};
res = createResponse();
settingsController.createAttendanceRule(req, res);
assert.equal(res.statusCode, 201);
const attendanceRuleId = res.payload.data.attendance_rule_id;
assert.equal(settingsLogger.auditRecords.length, 1);
assert.equal(settingsLogger.auditRecords[0].actor.id, 'settings-sync');
assert.equal(settingsLogger.auditRecords[0].actor.type, 'service');
assert.equal(settingsLogger.auditRecords[0].action, 'attendance_rule_created');
assert.deepEqual(settingsLogger.auditRecords[0].before, {});
assert.equal(settingsLogger.auditRecords[0].after.attendance_rule_id, attendanceRuleId);

req = {
  ...settingsReqBase,
  params: { attendanceRuleId },
  body: { grace_period_minutes: 5, late_after_minutes: 10, status: 'Archived' },
};
res = createResponse();
settingsController.updateAttendanceRule(req, res);
assert.equal(res.statusCode, 200);
assert.equal(settingsLogger.auditRecords.length, 2);
assert.equal(settingsLogger.auditRecords[1].action, 'attendance_rule_updated');
assert.equal(settingsLogger.auditRecords[1].before.status, 'Active');
assert.equal(settingsLogger.auditRecords[1].after.status, 'Archived');

req = {
  ...settingsReqBase,
  params: {},
  body: {
    code: 'ANNUAL-CORE',
    name: 'Annual Core',
    leave_type: 'Annual',
    accrual_frequency: 'Monthly',
    accrual_rate_days: 1.5,
    annual_entitlement_days: 18,
    carry_forward_limit_days: 5,
    requires_approval: true,
    allow_negative_balance: false,
    status: 'Active',
  },
};
res = createResponse();
settingsController.createLeavePolicy(req, res);
assert.equal(res.statusCode, 201);
const leavePolicyId = res.payload.data.leave_policy_id;
assert.equal(settingsLogger.auditRecords.length, 3);
assert.equal(settingsLogger.auditRecords[2].action, 'leave_policy_created');

req = {
  ...settingsReqBase,
  params: { leavePolicyId },
  body: { name: 'Annual Core Updated', carry_forward_limit_days: 4 },
};
res = createResponse();
settingsController.updateLeavePolicy(req, res);
assert.equal(res.statusCode, 200);
assert.equal(settingsLogger.auditRecords.length, 4);
assert.equal(settingsLogger.auditRecords[3].action, 'leave_policy_updated');
assert.equal(settingsLogger.auditRecords[3].before.name, 'Annual Core');
assert.equal(settingsLogger.auditRecords[3].after.name, 'Annual Core Updated');

req = {
  ...settingsReqBase,
  params: {},
  body: {
    pay_schedule: 'Monthly',
    pay_day: 25,
    currency: 'USD',
    overtime_multiplier: 1.5,
    attendance_cutoff_days: 2,
    leave_deduction_mode: 'Prorated',
    approval_chain: ['HR Ops', 'Finance'],
    status: 'Active',
  },
};
res = createResponse();
settingsController.upsertPayrollSettings(req, res);
assert.equal(res.statusCode, 200);
assert.equal(settingsLogger.auditRecords.length, 5);
assert.equal(settingsLogger.auditRecords[4].action, 'payroll_settings_upserted');
assert.deepEqual(settingsLogger.auditRecords[4].before, {});
assert.equal(settingsLogger.auditRecords[4].after.currency, 'USD');

req = {
  ...settingsReqBase,
  params: {},
  body: {
    pay_schedule: 'Monthly',
    pay_day: 26,
    currency: 'USD',
    overtime_multiplier: 2,
    attendance_cutoff_days: 3,
    leave_deduction_mode: 'FullDay',
    approval_chain: ['HR Ops', 'Finance', 'CFO'],
    status: 'Active',
  },
};
res = createResponse();
settingsController.upsertPayrollSettings(req, res);
assert.equal(res.statusCode, 200);
assert.equal(settingsLogger.auditRecords.length, 6);
assert.equal(settingsLogger.auditRecords[5].before.pay_day, 25);
assert.equal(settingsLogger.auditRecords[5].after.pay_day, 26);
assert.ok(Object.isFrozen(settingsLogger.auditRecords[5].before));
assert.ok(Object.isFrozen(settingsLogger.auditRecords[5].after));
'''


def test_audit_logging_source_coverage_for_mutations() -> None:
    employee_controller = (ROOT / 'services/employee-service/employee.controller.ts').read_text()
    department_controller = (ROOT / 'services/employee-service/department.controller.ts').read_text()
    role_controller = (ROOT / 'services/employee-service/role.controller.ts').read_text()
    performance_service = (ROOT / 'performance_service.py').read_text()
    settings_controller = (ROOT / 'services/settings-service/settings.controller.ts').read_text()
    logger = (ROOT / 'middleware/logger.ts').read_text()
    audit_helper = (ROOT / 'middleware/audit.ts').read_text()

    for token in [
        'employee_created',
        'employee_updated',
        'employee_department_assigned',
        'employee_status_updated',
        'employee_deleted',
    ]:
        assert token in employee_controller
        assert 'logAuditMutation({' in employee_controller

    for token in ['department_created', 'department_updated', 'department_deleted']:
        assert token in department_controller
        assert 'logAuditMutation({' in department_controller

    for token in ['role_created', 'role_updated', 'role_deleted']:
        assert token in role_controller
        assert 'logAuditMutation({' in role_controller

    for token in ['performance_goal_created', 'performance_feedback_recorded', 'performance_calibration_created', 'performance_pip_created']:
        assert token in performance_service
        assert 'emit_audit_record(' in performance_service

    for token in ['attendance_rule_created', 'attendance_rule_updated', 'leave_policy_created', 'leave_policy_updated', 'payroll_settings_upserted']:
        assert token in settings_controller
        assert 'logAuditMutation({' in settings_controller

    assert 'auditRecordsInternal' in logger
    assert 'this.auditRecordsInternal.push(record);' in logger
    assert 'before: Record<string, unknown>;' in logger
    assert 'after: Record<string, unknown>;' in logger
    assert 'resolveAuditActor' in audit_helper
    assert 'deepFreeze' in audit_helper
    assert 'tenant_id' in audit_helper


def test_audit_logging_runtime_integrity_and_actor_tracking() -> None:
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
                    "{ROOT / 'middleware/audit.ts'}",
                    "{ROOT / 'middleware/logger.ts'}",
                    "{ROOT / 'middleware/error-handler.ts'}",
                    "{ROOT / 'services/employee-service/domain-seed.ts'}",
                    "{ROOT / 'services/employee-service/department.model.ts'}",
                    "{ROOT / 'services/employee-service/role.model.ts'}",
                    "{ROOT / 'services/employee-service/employee.model.ts'}",
                    "{ROOT / 'services/employee-service/employee.validation.ts'}",
                    "{ROOT / 'services/employee-service/service.errors.ts'}",
                    "{ROOT / 'services/employee-service/employee.repository.ts'}",
                    "{ROOT / 'services/employee-service/employee.service.ts'}",
                    "{ROOT / 'services/employee-service/rbac.middleware.ts'}",
                    "{ROOT / 'services/employee-service/employee.controller.ts'}",
                    "{ROOT / 'services/settings-service/settings.model.ts'}",
                    "{ROOT / 'services/settings-service/settings.validation.ts'}",
                    "{ROOT / 'services/settings-service/settings.repository.ts'}",
                    "{ROOT / 'services/settings-service/settings.service.ts'}",
                    "{ROOT / 'services/settings-service/settings.controller.ts'}",
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
        assert (tmpdir / 'out' / 'middleware' / 'logger.js').exists(), compile_result.stderr + compile_result.stdout

        runtime_file = tmpdir / 'out' / 'audit-logging.runtime.cjs'
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
