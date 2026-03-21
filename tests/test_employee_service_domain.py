from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


RUNTIME_SCRIPT = """
const assert = require('node:assert/strict');
const { EmployeeRepository } = require('./services/employee-service/employee.repository.js');
const { EmployeeService, ConflictError } = require('./services/employee-service/employee.service.js');
const { ValidationError } = require('./services/employee-service/employee.validation.js');

const repository = new EmployeeRepository({ tenantId: 'tenant-default' });
const service = new EmployeeService(repository, undefined, undefined, 'tenant-default');

const manager = service.createEmployee({
  tenant_id: 'tenant-default',
  employee_number: 'E-100',
  first_name: 'Helen',
  last_name: 'Brooks',
  email: 'helen.brooks@example.com',
  phone: '+1 555-1000',
  hire_date: '2024-01-10',
  employment_type: 'FullTime',
  status: 'Active',
  department_id: 'dep-hr',
  role_id: 'role-hr-director',
});

assert.equal(service.eventOutbox.events[0].event_type, 'employee.created');
assert.equal(service.eventOutbox.events[0].tenant_id, 'tenant-default');

const employee = service.createEmployee({
  tenant_id: 'tenant-default',
  employee_number: 'E-101',
  first_name: 'Noah',
  last_name: 'Bennett',
  email: 'noah.bennett@example.com',
  phone: '+1 555-1001',
  hire_date: '2025-02-01',
  employment_type: 'FullTime',
  department_id: 'dep-eng',
  role_id: 'role-frontend-engineer',
  manager_employee_id: manager.employee_id,
});

const fetched = service.getEmployeeById(employee.employee_id);
assert.equal(fetched.employee_number, 'E-101');
assert.equal(fetched.tenant_id, 'tenant-default');

const readModels = service.getEmployeeReadModels(employee.employee_id);
assert.equal(readModels.employee_directory_view.department_name, 'Engineering');
assert.equal(readModels.employee_directory_view.role_title, 'Frontend Engineer');
assert.equal(readModels.employee_directory_view.manager_name, 'Helen Brooks');
assert.equal(readModels.employee_directory_view.tenant_id, 'tenant-default');
assert.equal(readModels.organization_structure_view.department_code, 'ENG');

const updated = service.updateEmployee(employee.employee_id, {
  department_id: 'dep-fin',
  role_id: 'role-finance-manager',
  employment_type: 'FullTime',
  email: 'noah.finance@example.com',
});
assert.equal(updated.department_id, 'dep-fin');
assert.equal(updated.role_id, 'role-finance-manager');
assert.equal(service.eventOutbox.events.at(-1).event_type, 'employee.updated');

const listed = service.listEmployees({ tenant_id: 'tenant-default', department_id: 'dep-fin', role_id: 'role-finance-manager', limit: 10 });
assert.equal(listed.data.length, 1);
assert.equal(listed.data[0].employee_id, employee.employee_id);
const listReadModels = service.listEmployeeReadModels({ tenant_id: 'tenant-default', department_id: 'dep-fin', role_id: 'role-finance-manager', limit: 10 });
assert.equal(listReadModels.employee_directory_view[0].department_name, 'Finance');
assert.equal(listReadModels.employee_directory_view[0].role_title, 'Finance Manager');

assert.throws(
  () => service.listEmployees({ tenant_id: 'tenant-other', limit: 10 }),
  ValidationError,
);

const isolatedRepository = new EmployeeRepository({ tenantId: 'tenant-other' });
const isolatedService = new EmployeeService(isolatedRepository, undefined, undefined, 'tenant-other');
assert.throws(() => isolatedService.getEmployeeById(employee.employee_id), /employee not found/);
assert.equal(isolatedService.listEmployees({ tenant_id: 'tenant-other', limit: 10 }).data.length, 0);

const activated = service.updateStatus(employee.employee_id, 'Active');
assert.equal(activated.status, 'Active');
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'employee.status.changed'), true);
const onLeave = service.updateStatus(employee.employee_id, 'OnLeave');
assert.equal(onLeave.status, 'OnLeave');
const backToActive = service.updateStatus(employee.employee_id, 'Active');
assert.equal(backToActive.status, 'Active');
const suspended = service.updateStatus(employee.employee_id, 'Suspended');
assert.equal(suspended.status, 'Suspended');
const terminated = service.updateStatus(employee.employee_id, 'Terminated');
assert.equal(terminated.status, 'Terminated');
assert.throws(() => service.updateStatus(employee.employee_id, 'Active'), ConflictError);

assert.throws(
  () =>
    service.createEmployee({
      tenant_id: 'tenant-default',
      employee_number: 'E-102',
      first_name: 'Invalid',
      last_name: 'Department',
      email: 'invalid.department@example.com',
      hire_date: '2025-02-01',
      employment_type: 'FullTime',
      department_id: 'dep-archive',
      role_id: 'role-frontend-engineer',
    }),
  ValidationError,
);

assert.throws(() => service.deleteEmployee(manager.employee_id), ConflictError);
service.deleteEmployee(employee.employee_id);
assert.throws(() => service.getEmployeeById(employee.employee_id), /employee not found/);
"""


def test_employee_service_crud_lifecycle_and_relationships() -> None:
    with subprocess.Popen(
        ["mktemp", "-d"],
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
                    "{ROOT / 'services/employee-service/department.model.ts'}",
                    "{ROOT / 'services/employee-service/role.model.ts'}",
                    "{ROOT / 'services/employee-service/domain-seed.ts'}",
                    "{ROOT / 'services/employee-service/employee.model.ts'}",
                    "{ROOT / 'services/employee-service/employee.validation.ts'}",
                    "{ROOT / 'services/employee-service/employee.repository.ts'}",
                    "{ROOT / 'services/employee-service/employee.service.ts'}",
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
        assert (tmpdir / 'out' / 'services' / 'employee-service' / 'employee.service.js').exists(), compile_result.stderr + compile_result.stdout

        runtime_file = tmpdir / 'out' / 'employee-domain.runtime.cjs'
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
