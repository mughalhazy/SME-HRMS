from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_service.service import AuditService
from background_jobs import BackgroundJobService
from data_integrity import DataIntegrityValidator
from leave_service import LeaveService
from payroll_service import PayrollService
from reporting_analytics import ReportingAnalyticsService
from search_service import SearchIndexingService
from services.hiring_service.service import HiringService


def _load_rows(path: str | None) -> list[dict]:
    if not path:
        return []
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, list):
        return [dict(item) for item in payload]
    raise ValueError(f'{path} must contain a JSON array of rows')


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate and optionally repair cross-service data integrity drift.')
    parser.add_argument('--tenant-id', default='tenant-default')
    parser.add_argument('--db-path', help='Shared sqlite path used by persistence-backed services.')
    parser.add_argument('--audit-log-path', help='Audit log path for audit/event alignment checks.')
    parser.add_argument('--employee-directory-json', help='Path to employee_directory_view rows as JSON.')
    parser.add_argument('--organization-structure-json', help='Path to organization_structure_view rows as JSON.')
    parser.add_argument('--employee-reporting-json', help='Path to employee_reporting_view rows as JSON.')
    parser.add_argument('--auto-fix', action='store_true', help='Apply only safe projection/index/tenant normalization repairs.')
    args = parser.parse_args()

    leave = LeaveService(db_path=args.db_path) if args.db_path else LeaveService()
    payroll = PayrollService(db_path=args.db_path) if args.db_path else PayrollService()
    hiring = HiringService(db_path=args.db_path) if args.db_path else HiringService()
    search = SearchIndexingService(db_path=args.db_path) if args.db_path else SearchIndexingService()
    reporting = ReportingAnalyticsService(db_path=args.db_path, tenant_id=args.tenant_id) if args.db_path else ReportingAnalyticsService(tenant_id=args.tenant_id)
    jobs = BackgroundJobService(leave_service=leave, db_path=args.db_path) if args.db_path else BackgroundJobService(leave_service=leave)
    audit = AuditService(log_path=args.audit_log_path) if args.audit_log_path else AuditService()

    validator = DataIntegrityValidator(
        tenant_id=args.tenant_id,
        employee_directory_rows=_load_rows(args.employee_directory_json),
        organization_structure_rows=_load_rows(args.organization_structure_json),
        employee_reporting_rows=_load_rows(args.employee_reporting_json),
        leave_service=leave,
        payroll_service=payroll,
        hiring_service=hiring,
        search_service=search,
        reporting_service=reporting,
        audit_service=audit,
        background_jobs=jobs,
    )
    print(json.dumps(validator.validate(auto_fix=args.auto_fix).to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
