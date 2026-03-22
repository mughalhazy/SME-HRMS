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
const { AssetManagementRepository } = require('./services/employee-service/asset-management.repository.js');
const { AssetManagementService } = require('./services/employee-service/asset-management.service.js');
const { AssetManagementController } = require('./services/employee-service/asset-management.controller.js');
const { ValidationError } = require('./services/employee-service/employee.validation.js');
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
  employee_number: 'E-401',
  first_name: 'Jordan',
  last_name: 'Reed',
  email: 'jordan.reed@example.com',
  hire_date: '2026-01-05',
  employment_type: 'FullTime',
  status: 'Active',
  department_id: 'dep-eng',
  role_id: 'role-ops-lead',
});
const employee = employeeService.createEmployee({
  tenant_id: 'tenant-default',
  employee_number: 'E-402',
  first_name: 'Taylor',
  last_name: 'Nguyen',
  email: 'taylor.nguyen@example.com',
  hire_date: '2026-01-06',
  employment_type: 'FullTime',
  status: 'Active',
  department_id: 'dep-eng',
  role_id: 'role-frontend-engineer',
  manager_employee_id: manager.employee_id,
});

const repository = new AssetManagementRepository();
const service = new AssetManagementService(repository, employeeRepository, 'tenant-default');
const controller = new AssetManagementController(service, employeeService);

assert.throws(() => service.createAsset({
  tenant_id: 'tenant-default',
  asset_tag: 'LAP-001',
  asset_type: 'Laptop',
  status: 'Allocated',
}), ValidationError);

const created = service.createAsset({
  tenant_id: 'tenant-default',
  asset_tag: 'LAP-001',
  asset_type: 'Laptop',
  category: 'IT',
  model: 'ThinkPad X1',
  serial_number: 'SER-001',
  vendor: 'Lenovo',
  procurement_date: '2026-01-01',
});
assert.equal(created.asset.status, 'InStock');
assert.equal(created.lifecycle.length, 1);
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'asset.registered'), true);

const allocated = service.allocateAsset(created.asset.asset_id, {
  tenant_id: 'tenant-default',
  employee_id: employee.employee_id,
  allocated_by: manager.employee_id,
  expected_return_date: '2026-12-31',
  notes: 'Primary developer laptop',
});
assert.equal(allocated.asset.assigned_employee_id, employee.employee_id);
assert.equal(allocated.asset.status, 'Allocated');
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'asset.allocated'), true);
assert.throws(() => service.allocateAsset(created.asset.asset_id, {
  tenant_id: 'tenant-default',
  employee_id: manager.employee_id,
}), ConflictError);

const damaged = service.updateAssetStatus(created.asset.asset_id, {
  tenant_id: 'tenant-default',
  status: 'Lost',
  actor_id: manager.employee_id,
  notes: 'Investigating loss while assigned',
});
assert.equal(damaged.asset.status, 'Lost');
assert.equal(damaged.asset.assigned_employee_id, employee.employee_id);
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'asset.status.changed'), true);

const returned = service.returnAsset(created.asset.asset_id, {
  tenant_id: 'tenant-default',
  returned_by: manager.employee_id,
  return_status: 'InRepair',
  notes: 'Returned with keyboard issue',
});
assert.equal(returned.asset.assigned_employee_id, undefined);
assert.equal(returned.asset.status, 'InRepair');
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'asset.returned'), true);

const lifecycle = service.listAssetLifecycle(created.asset.asset_id);
assert.equal(lifecycle.length, 4);
assert.deepEqual(lifecycle.map((entry) => entry.action), ['Registered', 'Allocated', 'StatusChanged', 'Returned']);
assert.equal(service.listAssets({ tenant_id: 'tenant-default', status: 'InRepair' }).length, 1);
assert.equal(service.listAssets({ tenant_id: 'tenant-default', employee_id: employee.employee_id }).length, 0);

const req = {
  traceId: 'trace-asset-audit',
  tenantId: 'tenant-default',
  headers: {},
  auth: { role: 'Admin', employee_id: 'admin-1', capabilities: ['CAP-EMP-001', 'CAP-EMP-002'], scopes: [], subject_type: 'user' },
  params: { assetId: created.asset.asset_id },
  query: {},
  body: {
    employee_id: employee.employee_id,
    allocated_by: manager.employee_id,
    expected_return_date: '2027-01-15',
    notes: 'Reissued after repair',
  },
};
const res = createResponse();
controller.allocateAsset(req, res);
assert.equal(res.statusCode, 200);

const records = fs.readFileSync(process.env.HRMS_AUDIT_LOG_PATH, 'utf8').trim().split('\\n').map((line) => JSON.parse(line));
const auditRecord = records.find((record) => record.action === 'asset_allocated');
assert.ok(auditRecord, 'expected asset_allocated audit record');
assert.equal(auditRecord.entity, 'Asset');
assert.equal(auditRecord.after.asset.assigned_employee_id, employee.employee_id);
"""


def test_asset_management_domain_lifecycle_and_audit() -> None:
    audit_log = ROOT / '.tmp-asset-audit.jsonl'
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
                    "{ROOT / 'services' / 'employee-service' / 'asset-management.model.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'asset-management.repository.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'asset-management.service.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'asset-management.controller.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'rbac.middleware.ts'}",
                    "{ROOT / 'cache' / 'cache.service.ts'}",
                    "{ROOT / 'db' / 'optimization.ts'}"
                  ]
                }}
                """
            ).strip()
        )
        compile_result = subprocess.run(['tsc', '-p', str(tsconfig)], cwd=ROOT, capture_output=True, text=True, check=False)
        assert (tmpdir / 'out' / 'services' / 'employee-service' / 'asset-management.service.js').exists(), compile_result.stderr + compile_result.stdout

        runtime_file = tmpdir / 'out' / 'asset-management.runtime.cjs'
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
        assert any(record['action'] == 'asset_allocated' for record in records)
    finally:
        subprocess.run(['rm', '-rf', str(tmpdir)], check=False)
        if audit_log.exists():
            audit_log.unlink()
