from pathlib import Path

import pytest

from audit_service.service import get_audit_service
from expense_service import ExpenseService, ExpenseServiceError
from notification_service import NotificationService
from workflow_service import WorkflowService


def test_expense_claim_lifecycle_runs_through_workflow_audit_and_reimbursement(tmp_path: Path) -> None:
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    service = ExpenseService(db_path=str(tmp_path / 'expense.sqlite3'), workflow_service=workflows, notification_service=notifications)

    _, created = service.create_claim(
        {
            'employee_id': 'emp-001',
            'category_code': 'TRAVEL',
            'amount': 425.50,
            'currency': 'USD',
            'expense_date': '2026-03-01',
            'description': 'Conference hotel',
            'attachments': [{'file_name': 'hotel.pdf', 'content_type': 'application/pdf', 'storage_key': 'receipts/hotel.pdf'}],
            'tenant_id': 'tenant-default',
        },
        actor_id='emp-001',
        trace_id='trace-expense-create',
    )
    assert created['status'] == 'Draft'
    assert created['attachments'][0]['file_name'] == 'hotel.pdf'

    _, submitted = service.submit_claim(created['expense_claim_id'], actor_id='emp-001', tenant_id='tenant-default', trace_id='trace-expense-submit')
    assert submitted['status'] == 'Submitted'
    assert submitted['workflow']['definition_code'] == 'expense_claim_approval'
    assert submitted['workflow']['subject_id'] == created['expense_claim_id']

    inbox = workflows.list_inbox(tenant_id='tenant-default', actor_id='emp-manager')
    assert inbox['data'][0]['subject_id'] == created['expense_claim_id']

    _, approved = service.decide_claim(created['expense_claim_id'], action='approve', actor_id='emp-manager', actor_role='Manager', tenant_id='tenant-default', trace_id='trace-expense-approve')
    assert approved['status'] == 'Approved'
    assert approved['workflow']['metadata']['terminal_result'] == 'approved'

    _, reimbursed = service.reimburse_claim(
        created['expense_claim_id'],
        {'tenant_id': 'tenant-default', 'reimbursement_reference': 'ACH-2026-0001'},
        actor_id='finance-admin',
        actor_role='Finance',
        trace_id='trace-expense-reimburse',
    )
    assert reimbursed['status'] == 'Reimbursed'
    assert reimbursed['reimbursement_reference'] == 'ACH-2026-0001'
    assert reimbursed['reimbursed_by'] == 'finance-admin'

    records, _ = get_audit_service().list_records(tenant_id='tenant-default', entity='ExpenseClaim', limit=20)
    actions = {record['action'] for record in records if record['entity_id'] == created['expense_claim_id']}
    assert {'expense_claim_created', 'expense_claim_submitted', 'expense_claim_approved', 'expense_claim_reimbursed'} <= actions

    legacy_names = [event['legacy_event_name'] for event in service.events]
    assert 'ExpenseClaimCreated' in legacy_names
    assert 'ExpenseClaimSubmitted' in legacy_names
    assert 'ExpenseClaimApproved' in legacy_names
    assert 'ExpenseClaimReimbursed' in legacy_names
    assert any(row.payload['tenant_id'] == 'tenant-default' for row in service.event_outbox.list_events(tenant_id='tenant-default'))


def test_expense_claim_requires_workflow_for_approval(tmp_path: Path) -> None:
    service = ExpenseService(db_path=str(tmp_path / 'expense-workflow.sqlite3'))
    _, created = service.create_claim(
        {
            'employee_id': 'emp-001',
            'category_code': 'TRAVEL',
            'amount': 120.0,
            'expense_date': '2026-03-04',
            'description': 'Taxi from airport',
            'attachments': [{'file_name': 'taxi.png', 'content_type': 'image/png', 'storage_key': 'receipts/taxi.png'}],
            'tenant_id': 'tenant-default',
        },
        actor_id='emp-001',
    )

    with pytest.raises(ExpenseServiceError) as exc:
        service.decide_claim(created['expense_claim_id'], action='approve', actor_id='emp-manager', actor_role='Manager', tenant_id='tenant-default')
    assert exc.value.status_code == 409
    assert exc.value.payload['error']['code'] == 'INVALID_TRANSITION'

    _, submitted = service.submit_claim(created['expense_claim_id'], actor_id='emp-001', tenant_id='tenant-default')
    assert submitted['workflow']['workflow_id']

    claim = service.claims[created['expense_claim_id']]
    claim.workflow_id = None
    service.claims[claim.expense_claim_id] = claim
    with pytest.raises(ExpenseServiceError) as missing_workflow:
        service.decide_claim(created['expense_claim_id'], action='approve', actor_id='emp-manager', actor_role='Manager', tenant_id='tenant-default')
    assert missing_workflow.value.payload['error']['code'] == 'WORKFLOW_MISSING'


def test_expense_categories_attachments_and_cross_tenant_guards(tmp_path: Path) -> None:
    service = ExpenseService(db_path=str(tmp_path / 'expense-tenant.sqlite3'))
    service.register_employee_profile(
        {
            'tenant_id': 'tenant-other',
            'employee_id': 'emp-201',
            'employee_number': 'E-201',
            'full_name': 'Olive Other',
            'department_id': 'dep-sales',
            'department_name': 'Sales',
            'manager_employee_id': 'mgr-201',
        }
    )
    service.register_employee_profile(
        {
            'tenant_id': 'tenant-other',
            'employee_id': 'mgr-201',
            'employee_number': 'E-202',
            'full_name': 'Mila Other Manager',
            'department_id': 'dep-sales',
            'department_name': 'Sales',
            'manager_employee_id': None,
        }
    )
    service.create_category(
        {
            'tenant_id': 'tenant-other',
            'code': 'TRAINING',
            'name': 'Training',
            'requires_attachment': True,
            'max_amount': 1500,
        },
        actor_id='mgr-201',
    )

    with pytest.raises(ExpenseServiceError) as missing_attachment:
        service.create_claim(
            {
                'tenant_id': 'tenant-other',
                'employee_id': 'emp-201',
                'category_code': 'TRAINING',
                'amount': 999,
                'expense_date': '2026-03-09',
                'description': 'Certification course',
            },
            actor_id='emp-201',
        )
    assert missing_attachment.value.payload['error']['code'] == 'VALIDATION_ERROR'

    _, created = service.create_claim(
        {
            'tenant_id': 'tenant-other',
            'employee_id': 'emp-201',
            'category_code': 'TRAINING',
            'amount': 999,
            'expense_date': '2026-03-09',
            'description': 'Certification course',
            'attachments': [{'file_name': 'invoice.pdf', 'content_type': 'application/pdf', 'storage_key': 'receipts/invoice.pdf'}],
        },
        actor_id='emp-201',
    )
    assert created['category']['code'] == 'TRAINING'

    with pytest.raises(ExpenseServiceError) as cross_tenant:
        service.get_claim(created['expense_claim_id'], tenant_id='tenant-default')
    assert cross_tenant.value.payload['error']['code'] == 'TENANT_SCOPE_VIOLATION'

    _, submitted = service.submit_claim(created['expense_claim_id'], actor_id='emp-201', tenant_id='tenant-other')
    assert submitted['workflow']['definition_code'] == 'expense_claim_approval'
    with pytest.raises(ExpenseServiceError) as forbidden_reimburse:
        service.reimburse_claim(created['expense_claim_id'], {'tenant_id': 'tenant-other'}, actor_id='mgr-201', actor_role='Manager')
    assert forbidden_reimburse.value.payload['error']['code'] == 'FORBIDDEN'
