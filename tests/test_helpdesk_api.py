import unittest

from helpdesk_api import (
    get_helpdesk_ticket,
    get_helpdesk_tickets,
    post_helpdesk_ticket_close,
    post_helpdesk_ticket_comment,
    post_helpdesk_ticket_decision,
    post_helpdesk_ticket_reopen,
    post_helpdesk_ticket_submit,
    post_helpdesk_tickets,
)
from helpdesk_service import HelpdeskService


class HelpdeskApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = HelpdeskService()

    def test_employee_self_service_and_helpdesk_resolution_flow(self) -> None:
        status, created = post_helpdesk_tickets(
            self.service,
            'Employee',
            'emp-001',
            {
                'tenant_id': 'tenant-default',
                'requester_employee_id': 'emp-001',
                'subject': 'Need to update dependent information',
                'category_code': 'BENEFITS',
                'description': 'Dependent date of birth was entered incorrectly during onboarding.',
                'priority': 'High',
            },
            trace_id='trace-helpdesk-api-create',
        )
        self.assertEqual(status, 201)
        ticket_id = created['data']['ticket_id']

        status, submitted = post_helpdesk_ticket_submit(
            self.service,
            'Employee',
            'emp-001',
            ticket_id,
            {'tenant_id': 'tenant-default'},
            trace_id='trace-helpdesk-api-submit',
        )
        self.assertEqual(status, 200)
        self.assertEqual(submitted['data']['status'], 'Open')
        self.assertEqual(submitted['data']['workflow']['definition_code'], 'hr_helpdesk_ticket_lifecycle')

        status, comment = post_helpdesk_ticket_comment(
            self.service,
            'Employee',
            'emp-001',
            ticket_id,
            {'tenant_id': 'tenant-default', 'body': 'Please let me know if you need supporting documents.'},
            trace_id='trace-helpdesk-api-comment',
        )
        self.assertEqual(status, 200)
        self.assertEqual(comment['meta']['service'], 'helpdesk-service')

        status, triaged = post_helpdesk_ticket_decision(
            self.service,
            'approve',
            'Helpdesk',
            'helpdesk-agent',
            ticket_id,
            {'tenant_id': 'tenant-default', 'comment': 'Reviewed and assigned to HR specialist.'},
            trace_id='trace-helpdesk-api-triage',
        )
        self.assertEqual(status, 200)
        self.assertEqual(triaged['data']['status'], 'InProgress')

        status, resolved = post_helpdesk_ticket_decision(
            self.service,
            'approve',
            'Helpdesk',
            'hr-helpdesk-specialist',
            ticket_id,
            {
                'tenant_id': 'tenant-default',
                'comment': 'Dependent information corrected in benefits platform.',
                'resolution_summary': 'Dependent profile corrected and employee notified.',
            },
            trace_id='trace-helpdesk-api-resolve',
        )
        self.assertEqual(status, 200)
        self.assertEqual(resolved['data']['status'], 'Resolved')

        status, closed = post_helpdesk_ticket_close(
            self.service,
            'Employee',
            'emp-001',
            ticket_id,
            {'tenant_id': 'tenant-default', 'closure_comment': 'Confirmed on my side.'},
            trace_id='trace-helpdesk-api-close',
        )
        self.assertEqual(status, 200)
        self.assertEqual(closed['data']['status'], 'Closed')

        status, reopened = post_helpdesk_ticket_reopen(
            self.service,
            'Employee',
            'emp-001',
            ticket_id,
            {'tenant_id': 'tenant-default', 'reopen_comment': 'Actually the spouse coverage still needs review.'},
            trace_id='trace-helpdesk-api-reopen',
        )
        self.assertEqual(status, 200)
        self.assertEqual(reopened['data']['status'], 'Open')

        status, fetched = get_helpdesk_ticket(
            self.service,
            'Employee',
            'emp-001',
            ticket_id,
            {'tenant_id': 'tenant-default'},
            trace_id='trace-helpdesk-api-get',
        )
        self.assertEqual(status, 200)
        self.assertEqual(fetched['data']['ticket_id'], ticket_id)

    def test_list_helpdesk_tickets_filters_for_self_service(self) -> None:
        status, created = post_helpdesk_tickets(
            self.service,
            'Employee',
            'emp-001',
            {
                'tenant_id': 'tenant-default',
                'requester_employee_id': 'emp-001',
                'subject': 'Payroll document request',
                'category_code': 'DOCUMENTS',
                'description': 'Need the last two payslips for loan underwriting.',
            },
            trace_id='trace-helpdesk-api-create-2',
        )
        self.assertEqual(status, 201)

        status, listing = get_helpdesk_tickets(
            self.service,
            'Employee',
            'emp-001',
            {'tenant_id': 'tenant-default', 'requester_employee_id': 'emp-001'},
            trace_id='trace-helpdesk-api-list',
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(listing['data']['items']), 1)
        self.assertEqual(listing['meta']['pagination']['count'], 1)
        self.assertEqual(listing['meta']['service'], 'helpdesk-service')


if __name__ == '__main__':
    unittest.main()
