from __future__ import annotations

import base64
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from datetime import date, datetime, time
from pathlib import Path
from uuid import uuid4

from attendance_service.models import AttendanceStatus
from attendance_service.service import Actor as AttendanceActor, AttendanceService, EmployeeSnapshot, InMemoryEmployeeDirectory
from audit_service.api import get_audit_records
from audit_service.service import AuditService
from leave_service import LeaveService
from payroll_service import PayrollService
from services.hiring_service import HiringService

ROOT = Path(__file__).resolve().parents[1]
AUTH_SERVICE_DIR = ROOT / 'services' / 'auth-service'
if str(AUTH_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AUTH_SERVICE_DIR))
service_spec = importlib.util.spec_from_file_location('audit_auth_service', AUTH_SERVICE_DIR / 'service.py')
auth_service_module = importlib.util.module_from_spec(service_spec)
assert service_spec and service_spec.loader
sys.modules[service_spec.name] = auth_service_module
service_spec.loader.exec_module(auth_service_module)
AuthService = auth_service_module.AuthService


class AuditServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.audit_path = Path(self.tempdir.name) / 'audit-records.jsonl'
        os.environ['HRMS_AUDIT_LOG_PATH'] = str(self.audit_path)

    def tearDown(self) -> None:
        os.environ.pop('HRMS_AUDIT_LOG_PATH', None)
        self.tempdir.cleanup()

    def test_audit_query_api_enforces_tenant_scope_and_pagination(self) -> None:
        service = AuditService(self.audit_path)
        service.append_record(
            tenant_id='tenant-default',
            actor={'id': 'user-1', 'type': 'user'},
            action='employee_created',
            entity='Employee',
            entity_id='emp-1',
            before={},
            after={'employee_id': 'emp-1'},
            trace_id='trace-1',
            source={'service': 'employee-service'},
        )
        service.append_record(
            tenant_id='tenant-beta',
            actor={'id': 'user-2', 'type': 'user'},
            action='employee_created',
            entity='Employee',
            entity_id='emp-2',
            before={},
            after={'employee_id': 'emp-2'},
            trace_id='trace-2',
            source={'service': 'employee-service'},
        )

        status, payload = get_audit_records({'tenant_id': 'tenant-default', 'limit': '1'}, trace_id='trace-audit-api')
        self.assertEqual(status, 200)
        self.assertEqual(len(payload['data']), 1)
        self.assertEqual(payload['data'][0]['tenant_id'], 'tenant-default')
        self.assertEqual(payload['meta']['pagination']['count'], 1)

        error_status, error_payload = get_audit_records({}, trace_id='trace-audit-error')
        self.assertEqual(error_status, 422)
        self.assertEqual(error_payload['error']['code'], 'VALIDATION_ERROR')

    def test_python_services_emit_centralized_audit_records_with_before_after(self) -> None:
        employee_id = uuid4()
        department_id = uuid4()
        directory = InMemoryEmployeeDirectory([
            EmployeeSnapshot(employee_id=employee_id, status='Active', department_id=department_id),
        ])
        attendance = AttendanceService(directory)
        admin_actor = AttendanceActor(employee_id=uuid4(), role='Admin', department_id=department_id)
        record = attendance.create_record(
            admin_actor,
            employee_id=employee_id,
            attendance_date=date(2026, 1, 5),
            attendance_status=AttendanceStatus.PRESENT,
            check_in_time=datetime(2026, 1, 5, 9, 0),
            check_out_time=datetime(2026, 1, 5, 17, 0),
        )
        attendance.update_record(admin_actor, record.attendance_id, correction_note='manager correction')
        attendance.approve_record(admin_actor, record.attendance_id)
        attendance.lock_period(admin_actor, period_id='period-2026-01', from_date=date(2026, 1, 5), to_date=date(2026, 1, 5))

        leave = LeaveService(db_path=str(Path(self.tempdir.name) / 'leave.sqlite3'))
        _, leave_payload = leave.create_request('Employee', 'emp-001', 'emp-001', 'Annual', date(2026, 4, 10), date(2026, 4, 12), 'vacation')
        leave_id = leave_payload['leave_request_id']
        leave.submit_request('Employee', 'emp-001', leave_id)
        leave.decide_request('approve', 'Manager', 'emp-manager', leave_id)
        leave.patch_request('Employee', 'emp-001', leave_id, {'status': 'Cancelled'})

        payroll = PayrollService(db_path=str(Path(self.tempdir.name) / 'payroll.sqlite3'))
        admin_token = 'Bearer ' + base64.urlsafe_b64encode(json.dumps({'role': 'Admin', 'employee_id': 'pay-admin'}).encode()).decode().rstrip('=')
        payroll.register_employee_profile('emp-001', department_id='dept-eng', role_id='role-eng')
        payroll.create_salary_structure({'employee_id': 'emp-001', 'effective_from': '2026-01-01', 'base_salary': '5000', 'allowances': '200', 'deductions': '50', 'overtime_rate': '25', 'currency': 'USD'}, admin_token)
        _, payroll_record = payroll.create_payroll_record({'employee_id': 'emp-001', 'pay_period_start': '2026-01-01', 'pay_period_end': '2026-01-31', 'base_salary': '5000', 'allowances': '200', 'deductions': '50', 'overtime_pay': '0', 'currency': 'USD'}, admin_token)
        payroll.run_payroll('2026-01-01', '2026-01-31', admin_token)
        payroll.patch_payroll_record(payroll_record['payroll_record_id'], {'allowances': '250'}, admin_token)
        payroll.mark_paid(payroll_record['payroll_record_id'], admin_token, payment_date='2026-02-01')

        hiring = HiringService(db_path=str(Path(self.tempdir.name) / 'hiring.sqlite3'))
        posting = hiring.create_job_posting({'title': 'Backend Engineer', 'department_id': 'dep-1', 'employment_type': 'FullTime', 'description': 'Build APIs', 'openings_count': 1, 'posting_date': '2026-01-01', 'status': 'Open'})
        candidate = hiring.create_candidate({'job_posting_id': posting['job_posting_id'], 'first_name': 'Ava', 'last_name': 'Stone', 'email': 'ava@example.com', 'application_date': '2026-01-03', 'changed_by': 'recruiter-1'})
        candidate = hiring.update_candidate(candidate['candidate_id'], {'status': 'Screening', 'changed_by': 'recruiter-1'})
        candidate = hiring.update_candidate(candidate['candidate_id'], {'status': 'Interviewing', 'changed_by': 'recruiter-1'})
        interview = hiring.create_interview({'candidate_id': candidate['candidate_id'], 'interview_type': 'Technical', 'scheduled_start': '2026-01-08T10:00:00+00:00', 'scheduled_end': '2026-01-08T11:00:00+00:00'})
        hiring.update_interview(interview['interview_id'], {'status': 'Completed', 'recommendation': 'Hire', 'changed_by': 'recruiter-1'})
        candidate = hiring.update_candidate(candidate['candidate_id'], {'status': 'Offered', 'changed_by': 'recruiter-1'})
        hiring.mark_candidate_hired(candidate['candidate_id'], {'changed_by': 'recruiter-1'})

        auth = AuthService(token_secret='test-secret-for-hardening-1234567890', db_path=str(Path(self.tempdir.name) / 'auth.sqlite3'))
        auth.register_user(username='auditor.admin', password='Password123!', role='Admin')
        auth_login = auth.login('auditor.admin', 'Password123!')
        auth.refresh_session(auth_login['refresh_token'])
        auth.logout_refresh_token(auth_login['refresh_token']) if False else None
        auth.revoke_session(auth_login['session_id'], actor='security-admin')

        records = [json.loads(line) for line in self.audit_path.read_text().splitlines() if line.strip()]
        actions = {record['action'] for record in records}
        expected = {
            'attendance_record_created', 'attendance_record_corrected', 'attendance_record_approved', 'attendance_period_locked',
            'leave_request_created', 'leave_request_submitted', 'leave_request_approve', 'leave_request_cancelled',
            'salary_structure_created', 'payroll_record_drafted', 'payroll_run_processed', 'payroll_record_adjusted', 'payroll_record_paid',
            'job_posting_created', 'candidate_created', 'candidate_updated', 'interview_created', 'interview_updated', 'candidate_hired',
            'auth_user_registered', 'auth_refresh_rotated', 'auth_logout',
        }
        self.assertTrue(expected.issubset(actions))

        paid_record = next(record for record in records if record['action'] == 'payroll_record_paid')
        self.assertEqual(paid_record['tenant_id'], 'tenant-default')
        self.assertEqual(paid_record['before']['status'], 'Processed')
        self.assertEqual(paid_record['after']['status'], 'Paid')

        leave_record = next(record for record in records if record['action'] == 'leave_request_submitted')
        self.assertEqual(leave_record['before']['status'], 'Draft')
        self.assertEqual(leave_record['after']['status'], 'Submitted')

    def test_typescript_employee_audit_records_write_to_central_store(self) -> None:
        tsconfig = Path(self.tempdir.name) / 'tsconfig.json'
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
                    "{ROOT / 'services' / 'employee-service' / 'rbac.middleware.ts'}",
                    "{ROOT / 'services' / 'employee-service' / 'employee.controller.ts'}",
                    "{ROOT / 'cache' / 'cache.service.ts'}",
                    "{ROOT / 'db' / 'optimization.ts'}"
                  ]
                }}
                """
            ).strip()
        )
        compile_result = subprocess.run(['tsc', '-p', str(tsconfig)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertTrue((Path(self.tempdir.name) / 'out' / 'middleware' / 'logger.js').exists(), compile_result.stderr + compile_result.stdout)

        runtime_file = Path(self.tempdir.name) / 'out' / 'audit-ts.runtime.cjs'
        runtime_file.write_text(
            textwrap.dedent(
                """
                const { EmployeeRepository } = require('./services/employee-service/employee.repository.js');
                const { EmployeeService } = require('./services/employee-service/employee.service.js');
                const { EmployeeController } = require('./services/employee-service/employee.controller.js');
                function createResponse() {
                  return {
                    statusCode: 200,
                    payload: undefined,
                    status(code) { this.statusCode = code; return this; },
                    json(payload) { this.payload = payload; return this; },
                    send(body) { this.body = body; return this; },
                    setHeader() { return this; },
                  };
                }
                const repository = new EmployeeRepository({ tenantId: 'tenant-default' });
                const service = new EmployeeService(repository, undefined, undefined, undefined, 'tenant-default');
                const controller = new EmployeeController(service);
                const req = {
                  traceId: 'trace-ts-audit',
                  headers: {},
                  auth: { role: 'Admin', employee_id: 'admin-1' },
                  params: {},
                  query: {},
                  body: {
                    tenant_id: 'tenant-default',
                    employee_number: 'E-900',
                    first_name: 'Casey',
                    last_name: 'Morgan',
                    email: 'casey@example.com',
                    phone: '+1 555-0900',
                    hire_date: '2026-01-01',
                    employment_type: 'FullTime',
                    department_id: 'dep-eng',
                    role_id: 'role-frontend-engineer'
                  }
                };
                const res = createResponse();
                controller.createEmployee(req, res);
                if (res.statusCode !== 201) { process.exit(1); }
                """
            ).strip()
        )
        run_result = subprocess.run(['node', str(runtime_file)], cwd=Path(self.tempdir.name) / 'out', capture_output=True, text=True, check=False, env={**os.environ, 'HRMS_AUDIT_LOG_PATH': str(self.audit_path)})
        self.assertEqual(run_result.returncode, 0, run_result.stderr + run_result.stdout)
        records = [json.loads(line) for line in self.audit_path.read_text().splitlines() if line.strip()]
        employee_created = next(record for record in records if record['action'] == 'employee_created')
        self.assertEqual(employee_created['source']['service'], 'employee-service')
        self.assertEqual(employee_created['tenant_id'], 'tenant-default')
        self.assertEqual(employee_created['before'], {})
        self.assertEqual(employee_created['after']['employee_number'], 'E-900')


if __name__ == '__main__':
    unittest.main()
