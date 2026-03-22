from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


RUNTIME_SCRIPT = """
const assert = require('node:assert/strict');
const { EmployeeRepository } = require('./services/employee-service/employee.repository.js');
const { EmployeeService } = require('./services/employee-service/employee.service.js');
const { ValidationError } = require('./services/employee-service/employee.validation.js');

const repository = new EmployeeRepository({ tenantId: 'tenant-default' });
const service = new EmployeeService(repository, undefined, undefined, 'tenant-default');

const sponsor = service.createEmployee({
  tenant_id: 'tenant-default',
  employee_number: 'E-700',
  first_name: 'Morgan',
  last_name: 'Lee',
  email: 'morgan.lee@example.com',
  hire_date: '2024-01-10',
  employment_type: 'FullTime',
  status: 'Active',
  department_id: 'dep-eng',
  role_id: 'role-frontend-engineer',
});

const contractor = service.createContractor({
  tenant_id: 'tenant-default',
  employee_number: 'C-100',
  first_name: 'Riley',
  last_name: 'Chen',
  email: 'riley.chen@vendor.example',
  hire_date: '2025-02-01',
  status: 'Active',
  department_id: 'dep-eng',
  role_id: 'role-contractor-consultant',
  manager_employee_id: sponsor.employee_id,
  business_unit_id: 'bu-product',
  legal_entity_id: 'le-product-labs',
  location_id: 'loc-sfo',
  cost_center_id: 'cc-eng-001',
  contract_metadata: {
    contract_type: 'Agency',
    contract_start_date: '2025-02-01',
    contract_end_date: '2025-12-31',
    vendor_name: 'BuildFast Partners',
    vendor_contact_email: 'vendor.manager@buildfast.example',
    purchase_order_number: 'PO-7741',
    billing_currency: 'USD',
    billing_rate: 145,
    access_expires_at: '2025-12-31',
    sponsor_employee_id: sponsor.employee_id,
    external_worker_id: 'VENDOR-22',
  },
});

assert.equal(contractor.employment_type, 'Contract');
assert.equal(contractor.contract_metadata.contract_type, 'Agency');
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'employee.contract.activated'), true);

const fetched = service.getContractorById(contractor.employee_id);
assert.equal(fetched.employee_id, contractor.employee_id);
assert.equal(fetched.department_id, 'dep-eng');
assert.equal(fetched.contract_metadata.vendor_name, 'BuildFast Partners');

const listResult = service.listContractors({ tenant_id: 'tenant-default', department_id: 'dep-eng', limit: 10 });
assert.equal(listResult.data.length, 1);
assert.equal(listResult.data[0].employee_id, contractor.employee_id);

const listReadModels = service.listContractorReadModels({ tenant_id: 'tenant-default', department_id: 'dep-eng', limit: 10 });
assert.equal(listReadModels.employee_directory_view[0].employment_type, 'Contract');
assert.equal(listReadModels.employee_directory_view[0].contract_metadata.vendor_name, 'BuildFast Partners');
assert.equal(listReadModels.organization_structure_view[0].contract_metadata.access_expires_at, '2025-12-31');

const updated = service.updateContractor(contractor.employee_id, {
  email: 'riley.chen+renewed@vendor.example',
  contract_metadata: {
    ...contractor.contract_metadata,
    contract_end_date: '2026-03-31',
    access_expires_at: '2026-03-31',
  },
});
assert.equal(updated.email, 'riley.chen+renewed@vendor.example');
assert.equal(updated.contract_metadata.contract_end_date, '2026-03-31');

assert.throws(
  () => service.createContractor({
    tenant_id: 'tenant-default',
    employee_number: 'C-101',
    first_name: 'Bad',
    last_name: 'Role',
    email: 'bad.role@vendor.example',
    hire_date: '2025-02-01',
    department_id: 'dep-eng',
    role_id: 'role-frontend-engineer',
    contract_metadata: {
      contract_type: 'IndependentContractor',
      contract_start_date: '2025-02-01',
      access_expires_at: '2025-06-30',
    },
  }),
  ValidationError,
);

assert.throws(
  () => service.updateContractor(contractor.employee_id, { employment_type: 'FullTime' }),
  ValidationError,
);

const isolatedRepository = new EmployeeRepository({ tenantId: 'tenant-beta' });
const isolatedService = new EmployeeService(isolatedRepository, undefined, undefined, 'tenant-beta');
assert.equal(isolatedService.listContractors({ tenant_id: 'tenant-beta', limit: 10 }).data.length, 0);
assert.throws(() => isolatedService.getContractorById(contractor.employee_id), /contractor not found|employee not found/);
"""


def test_contractor_management_reuses_employee_identity_and_preserves_tenant_isolation() -> None:
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
                    "{ROOT / 'services/employee-service/event-outbox.ts'}",
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
        assert (tmpdir / 'out' / 'services' / 'employee-service' / 'employee.service.js').exists(), compile_result.stderr + compile_result.stdout

        runtime_file = tmpdir / 'out' / 'contractor-domain.runtime.cjs'
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
