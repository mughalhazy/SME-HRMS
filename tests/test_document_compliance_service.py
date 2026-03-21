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
const { DocumentComplianceRepository } = require('./services/employee-service/document-compliance.repository.js');
const { DocumentComplianceService } = require('./services/employee-service/document-compliance.service.js');
const { DocumentComplianceController } = require('./services/employee-service/document-compliance.controller.js');

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
const employeeService = new EmployeeService(employeeRepository, undefined, undefined, undefined, 'tenant-default');
const worker = employeeService.createEmployee({
  tenant_id: 'tenant-default',
  employee_number: 'E-321',
  first_name: 'Casey',
  last_name: 'Morgan',
  email: 'casey.morgan@example.com',
  hire_date: '2026-01-02',
  employment_type: 'FullTime',
  status: 'Active',
  department_id: 'dep-ops',
  role_id: 'role-ops-lead',
});

const repository = new DocumentComplianceRepository();
const service = new DocumentComplianceService(repository, employeeRepository, 'tenant-default');
const controller = new DocumentComplianceController(service, employeeService);

const contractResult = service.createDocument({
  tenant_id: 'tenant-default',
  employee_id: worker.employee_id,
  document_type: 'Contract',
  title: 'Employment Agreement',
  expiry_date: '2026-12-31',
  storage: {
    provider: 's3',
    bucket: 'tenant-default-docs',
    object_key: 'employees/' + worker.employee_id + '/contract.pdf',
    content_type: 'application/pdf',
    size_bytes: 4096,
    checksum_sha256: 'abc123',
    encrypted_at_rest: true,
  },
  contract_details: {
    contract_kind: 'Employment',
    effective_from: '2026-01-02',
    signed_at: '2026-01-01',
  },
});
assert.equal(contractResult.document.document_type, 'Contract');
assert.ok(contractResult.compliance_task);
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'employee.document.stored'), true);
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'employee.document.expiry.tracked'), true);
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'employee.compliance.task.assigned'), true);

const policy = service.createDocument({
  tenant_id: 'tenant-default',
  employee_id: worker.employee_id,
  document_type: 'Policy',
  title: 'Safety Handbook',
  expiry_date: '2026-09-30',
  requires_acknowledgement: true,
  policy_code: 'SAFE-001',
  storage: {
    provider: 's3',
    bucket: 'tenant-default-docs',
    object_key: 'employees/' + worker.employee_id + '/policy.pdf',
    content_type: 'application/pdf',
    size_bytes: 1024,
    checksum_sha256: 'def456',
    encrypted_at_rest: true,
  },
});
const acknowledgement = service.acknowledgePolicy(policy.document.document_id, {
  tenant_id: 'tenant-default',
  acknowledged_by: worker.employee_id,
  comment: 'Reviewed during onboarding',
});
assert.equal(acknowledgement.employee_id, worker.employee_id);
assert.equal(service.listAcknowledgements(policy.document.document_id).length, 1);
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'employee.policy.acknowledged'), true);

const expiring = service.listExpiringDocuments({ tenant_id: 'tenant-default', employee_id: worker.employee_id, expiry_to: '2026-12-31' });
assert.equal(expiring.length, 2);

const manualTask = service.createComplianceTask({
  tenant_id: 'tenant-default',
  employee_id: worker.employee_id,
  assigned_employee_id: worker.employee_id,
  task_type: 'ManualReview',
  title: 'Upload updated visa copy',
  due_date: '2026-08-15',
});
const completedTask = service.updateComplianceTask(manualTask.task_id, {
  status: 'Completed',
  completed_by: worker.employee_id,
});
assert.equal(completedTask.status, 'Completed');
assert.equal(service.listComplianceTasks({ tenant_id: 'tenant-default', assigned_employee_id: worker.employee_id }).length >= 2, true);
assert.equal(service.eventOutbox.events.some((event) => event.event_type === 'employee.compliance.task.completed'), true);

const req = {
  traceId: 'trace-document-audit',
  tenantId: 'tenant-default',
  headers: {},
  auth: { role: 'Admin', employee_id: 'admin-1', capabilities: ['CAP-EMP-001', 'CAP-EMP-002'], scopes: [], subject_type: 'user' },
  body: {
    employee_id: worker.employee_id,
    document_type: 'Other',
    title: 'I-9 Metadata Record',
    storage: {
      provider: 's3',
      bucket: 'tenant-default-docs',
      object_key: 'employees/' + worker.employee_id + '/i9.json',
      content_type: 'application/json',
      size_bytes: 512,
      checksum_sha256: 'ghi789',
      encrypted_at_rest: true,
    },
  },
  params: {},
  query: {},
};
const res = createResponse();
controller.createDocument(req, res);
assert.equal(res.statusCode, 201);
const records = fs.readFileSync(process.env.HRMS_AUDIT_LOG_PATH, 'utf8').trim().split('\\n').map((line) => JSON.parse(line));
const auditRecord = records.find((record) => record.action === 'document_created');
assert.ok(auditRecord, 'expected document_created audit record');
assert.equal(auditRecord.entity, 'EmployeeDocument');
"""


def test_document_compliance_domain_and_audit_integration() -> None:
    audit_log = ROOT / '.tmp-document-audit.jsonl'
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
                    "{ROOT / 'services' / 'employee-service' / 'document-compliance.model.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'document-compliance.repository.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'document-compliance.service.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'document-compliance.controller.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'rbac.middleware.ts'}",
                    "{ROOT / 'cache' / 'cache.service.ts'}",
                    "{ROOT / 'db' / 'optimization.ts'}"
                  ]
                }}
                """
            ).strip()
        )
        compile_result = subprocess.run(['tsc', '-p', str(tsconfig)], cwd=ROOT, capture_output=True, text=True, check=False)
        assert (tmpdir / 'out' / 'services' / 'employee-service' / 'document-compliance.service.js').exists(), compile_result.stderr + compile_result.stdout

        runtime_file = tmpdir / 'out' / 'document-compliance.runtime.cjs'
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
        assert any(record['action'] == 'document_created' for record in records)
    finally:
        subprocess.run(['rm', '-rf', str(tmpdir)], check=False)
        if audit_log.exists():
            audit_log.unlink()
