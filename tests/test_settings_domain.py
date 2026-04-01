from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNTIME_SCRIPT = r"""
const assert = require('node:assert/strict');
const { SettingsRepository } = require('./services/settings-service/settings.repository.js');
const { SettingsService } = require('./services/settings-service/settings.service.js');
const { ConflictError, NotFoundError } = require('./services/employee-service/service.errors.js');
const { ValidationError } = require('./services/employee-service/employee.validation.js');

const repository = new SettingsRepository('tenant-default');
const service = new SettingsService(repository, 'tenant-default');
const otherTenantRepository = new SettingsRepository('tenant-beta');
const otherTenantService = new SettingsService(otherTenantRepository, 'tenant-beta');

const attendanceRule = service.createAttendanceRule({
  code: 'HQ-GENERAL',
  name: 'Headquarters General Shift',
  timezone: 'America/Los_Angeles',
  workdays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
  standard_work_hours: 8,
  grace_period_minutes: 10,
  late_after_minutes: 15,
  auto_clock_out_hours: 12,
  require_geo_fencing: true,
  status: 'Active',
});
assert.equal(attendanceRule.status, 'Active');

const updatedAttendanceRule = service.updateAttendanceRule(attendanceRule.attendance_rule_id, {
  grace_period_minutes: 5,
  late_after_minutes: 10,
  status: 'Archived',
});
assert.equal(updatedAttendanceRule.status, 'Archived');
assert.equal(service.listAttendanceRules({ status: 'Archived' }).length, 1);

assert.throws(
  () => service.createAttendanceRule({
    code: 'HQ-GENERAL',
    name: 'Duplicate Code',
    timezone: 'America/Los_Angeles',
    workdays: ['Monday'],
    standard_work_hours: 8,
    grace_period_minutes: 0,
    late_after_minutes: 0,
  }),
  ConflictError,
);

const annualPolicy = service.createLeavePolicy({
  code: 'ANNUAL-STD',
  name: 'Annual Leave Standard',
  leave_type: 'Annual',
  accrual_frequency: 'Monthly',
  accrual_rate_days: 1.5,
  annual_entitlement_days: 18,
  carry_forward_limit_days: 5,
  requires_approval: true,
  allow_negative_balance: false,
  status: 'Active',
});
assert.equal(annualPolicy.leave_type, 'Annual');

assert.throws(
  () => service.createLeavePolicy({
    code: 'ANNUAL-ALT',
    name: 'Duplicate Active Annual Policy',
    leave_type: 'Annual',
    accrual_frequency: 'Monthly',
    accrual_rate_days: 2,
    annual_entitlement_days: 20,
    carry_forward_limit_days: 5,
    status: 'Active',
  }),
  ConflictError,
);

const sickPolicy = service.createLeavePolicy({
  code: 'SICK-CORE',
  name: 'Sick Leave Core',
  leave_type: 'Sick',
  accrual_frequency: 'None',
  accrual_rate_days: 0,
  annual_entitlement_days: 10,
  carry_forward_limit_days: 0,
  status: 'Draft',
});

const activatedSickPolicy = service.updateLeavePolicy(sickPolicy.leave_policy_id, {
  status: 'Active',
  name: 'Sick Leave Core Active',
});
assert.equal(activatedSickPolicy.status, 'Active');

assert.throws(
  () => service.createLeavePolicy({
    code: 'UNPAID-BAD',
    name: 'Unpaid Invalid',
    leave_type: 'Unpaid',
    accrual_frequency: 'None',
    accrual_rate_days: 0,
    annual_entitlement_days: 1,
    carry_forward_limit_days: 0,
  }),
  ValidationError,
);

const payroll = service.upsertPayrollSettings({
  pay_schedule: 'Monthly',
  pay_day: 25,
  currency: 'USD',
  overtime_multiplier: 1.5,
  attendance_cutoff_days: 2,
  leave_deduction_mode: 'Prorated',
  approval_chain: ['HR Ops', 'Finance Controller'],
  status: 'Active',
});
assert.equal(payroll.currency, 'USD');
assert.equal(service.getPayrollSettings().pay_schedule, 'Monthly');

assert.throws(
  () => service.upsertPayrollSettings({
    pay_schedule: 'Weekly',
    pay_day: 9,
    currency: 'USD',
    overtime_multiplier: 1.5,
    attendance_cutoff_days: 2,
    leave_deduction_mode: 'Prorated',
    approval_chain: ['HR Ops'],
  }),
  ValidationError,
);

assert.throws(
  () => service.upsertPayrollSettings({
    pay_schedule: 'Monthly',
    pay_day: 15,
    currency: 'USD',
    overtime_multiplier: 1.5,
    attendance_cutoff_days: 1,
    leave_deduction_mode: 'FullDay',
    approval_chain: ['Payroll Lead'],
    status: 'Draft',
  }),
  ConflictError,
);



const tenantConfig = service.upsertTenantConfig({
  feature_flags: { self_service_leave: true, payroll_preview: false },
  leave_policy_refs: ['ANNUAL-STD'],
  payroll_rule_refs: ['monthly-core'],
  locale: 'en-US',
  legal_entity: 'Acme HR LLC',
  enabled_locations: ['US-NY', 'US-CA'],
});
assert.equal(tenantConfig.tenant_id, 'tenant-default');
assert.equal(service.isFeatureEnabled('self_service_leave'), true);
assert.equal(service.getTenantConfig().legal_entity, 'Acme HR LLC');

otherTenantService.upsertTenantConfig({
  feature_flags: { self_service_leave: false },
  legal_entity: 'Beta HR Ltd',
});
assert.equal(otherTenantService.isFeatureEnabled('self_service_leave'), false);
assert.equal(otherTenantService.getTenantConfig().legal_entity, 'Beta HR Ltd');
assert.equal(service.getTenantConfig().legal_entity, 'Acme HR LLC');

const readModels = service.getSettingsReadModels();
assert.equal(readModels.settings_configuration_view.attendance_rules.length, 1);
assert.equal(readModels.settings_configuration_view.leave_policies.length, 2);
assert.equal(readModels.settings_configuration_view.payroll_settings.pay_schedule, 'Monthly');
assert.equal(readModels.settings_configuration_view.tenant_id, 'tenant-default');
assert.equal(readModels.settings_configuration_view.tenant_configuration.feature_flags.self_service_leave, true);
assert.match(readModels.settings_configuration_view.leave_policies[0].entitlement_summary, /days\/year/);

const settingsConfiguration = service.getSettingsConfiguration();
assert.equal(settingsConfiguration.attendance_rules[0].attendance_rule_id, attendanceRule.attendance_rule_id);
assert.equal(service.getAttendanceRuleById(attendanceRule.attendance_rule_id).code, 'HQ-GENERAL');
assert.equal(service.getLeavePolicyById(annualPolicy.leave_policy_id).code, 'ANNUAL-STD');
assert.equal(service.getPayrollSettings().payroll_setting_id, payroll.payroll_setting_id);

assert.throws(() => service.getAttendanceRuleById('missing-rule'), NotFoundError);
assert.throws(() => service.getLeavePolicyById('missing-policy'), NotFoundError);
"""


def test_settings_service_domain_rules_and_read_models() -> None:
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
                    "{ROOT / 'services/settings-service/settings.model.ts'}",
                    "{ROOT / 'services/settings-service/settings.validation.ts'}",
                    "{ROOT / 'services/settings-service/settings.repository.ts'}",
                    "{ROOT / 'services/settings-service/settings.service.ts'}",
                    "{ROOT / 'services/employee-service/service.errors.ts'}",
                    "{ROOT / 'services/employee-service/employee.validation.ts'}",
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
        assert (tmpdir / 'out' / 'services' / 'settings-service' / 'settings.service.js').exists(), compile_result.stderr + compile_result.stdout

        runtime_file = tmpdir / 'out' / 'settings-domain.runtime.cjs'
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
