from __future__ import annotations

import unittest

from notification_api import (
    get_notification_delivery,
    get_notification_inbox,
    get_notification_message,
    get_notification_preferences,
    patch_notification_preferences,
    post_notification_event,
    post_notification_inbox_read,
)
from notification_service import NotificationService


class NotificationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = NotificationService()

    def test_ingesting_leave_approved_event_creates_email_and_in_app_notifications(self) -> None:
        status, response = post_notification_event(
            self.service,
            {
                'event_name': 'LeaveRequestApproved',
                'tenant_id': 'tenant-acme',
                'employee_id': 'emp-001',
                'employee_email': 'amina.yusuf@example.com',
                'approver_name': 'Helen Brooks',
                'leave_type': 'Annual',
                'start_date': '2026-03-21',
                'end_date': '2026-03-25',
            },
            trace_id='trace-notification-approved',
        )

        self.assertEqual(status, 202)
        self.assertEqual(response['data']['count'], 2)
        channels = {row['channel'] for row in response['data']['notifications']}
        self.assertEqual(channels, {'Email', 'InApp'})
        self.assertEqual(response['data']['event_type'], 'leave.request.approved')
        inbox = self.service.get_inbox(subject_id='emp-001')
        self.assertEqual(inbox['summary']['unread'], 1)
        self.assertEqual(inbox['items'][0]['title'], 'Leave request approved')

    def test_preferences_can_suppress_email_but_keep_inbox_notifications(self) -> None:
        status, response = patch_notification_preferences(
            self.service,
            'emp-001',
            {
                'subject_type': 'Employee',
                'topic_code': 'payroll.processed',
                'email_enabled': False,
                'in_app_enabled': True,
            },
            trace_id='trace-pref-update',
        )
        self.assertEqual(status, 200)
        self.assertFalse(response['data']['email_enabled'])

        status, response = post_notification_event(
            self.service,
            {
                'event_name': 'PayrollProcessed',
                'tenant_id': 'tenant-acme',
                'employee_id': 'emp-001',
                'employee_email': 'amina.yusuf@example.com',
                'pay_period_start': '2026-03-01',
                'pay_period_end': '2026-03-31',
                'net_pay': '5190.00',
                'currency': 'USD',
            },
            trace_id='trace-payroll-processed',
        )

        self.assertEqual(status, 202)
        by_channel = {row['channel']: row for row in response['data']['notifications']}
        self.assertEqual(by_channel['Email']['status'], 'Suppressed')
        self.assertEqual(by_channel['InApp']['status'], 'Sent')

    def test_inbox_read_flow_and_delivery_filtering(self) -> None:
        _, response = post_notification_event(
            self.service,
            {
                'event_name': 'SessionRevoked',
                'tenant_id': 'tenant-acme',
                'user_id': 'user-001',
            },
            trace_id='trace-session-revoked',
        )
        message_id = response['data']['notifications'][0]['message_id']

        status, inbox = get_notification_inbox(self.service, 'user-001', {'unread_only': 'true'}, trace_id='trace-inbox')
        self.assertEqual(status, 200)
        self.assertEqual(inbox['data']['summary']['unread'], 1)
        self.assertEqual(len(inbox['data']['items']), 1)

        status, read_response = post_notification_inbox_read(self.service, 'user-001', message_id, trace_id='trace-read')
        self.assertEqual(status, 200)
        self.assertIsNotNone(read_response['data']['read_at'])

        status, filtered = get_notification_delivery(
            self.service,
            {'subject_id': 'user-001', 'channel': 'InApp', 'status': 'Sent'},
            trace_id='trace-delivery-filter',
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(filtered['data']), 1)
        self.assertEqual(filtered['data'][0]['last_attempt_outcome'], 'Sent')

    def test_preferences_and_message_lookup_endpoints_return_serialized_payloads(self) -> None:
        patch_notification_preferences(
            self.service,
            'cand-001',
            {
                'subject_type': 'Candidate',
                'topic_code': 'hiring.interview_scheduled',
                'in_app_enabled': True,
                'email_enabled': True,
            },
            trace_id='trace-candidate-prefs',
        )
        _, event_response = post_notification_event(
            self.service,
            {
                'event_name': 'InterviewScheduled',
                'tenant_id': 'tenant-acme',
                'candidate_id': 'cand-001',
                'candidate_email': 'candidate@example.com',
                'scheduled_start': '2026-03-24T14:00:00Z',
                'location': 'https://meet.google.com/example',
            },
            trace_id='trace-interview',
        )
        message_id = event_response['data']['notifications'][0]['message_id']

        status, preferences = get_notification_preferences(
            self.service,
            'cand-001',
            {'subject_type': 'Candidate'},
            trace_id='trace-pref-get',
        )
        self.assertEqual(status, 200)
        self.assertEqual(preferences['data'][0]['topic_code'], 'hiring.interview_scheduled')

        status, message = get_notification_message(self.service, message_id, trace_id='trace-message-get')
        self.assertEqual(status, 200)
        self.assertEqual(message['data']['subject_id'], 'cand-001')
        self.assertEqual(message['data']['event_name'], 'InterviewScheduled')

    def test_invalid_preference_payloads_and_subject_filters_return_validation_errors(self) -> None:
        status, payload = patch_notification_preferences(
            self.service,
            'emp-001',
            {
                'subject_type': 'Employee',
                'topic_code': 'leave.approval',
                'email_enabled': 'yes',
            },
            trace_id='trace-pref-invalid',
        )
        self.assertEqual(status, 422)
        self.assertEqual(payload['error']['code'], 'VALIDATION_ERROR')

        status, payload = get_notification_delivery(
            self.service,
            {'subject_id': ''},
            trace_id='trace-delivery-invalid',
        )
        self.assertEqual(status, 422)
        self.assertEqual(payload['error']['code'], 'VALIDATION_ERROR')


    def test_canonical_event_envelope_is_accepted_and_missing_tenant_is_rejected(self) -> None:
        status, response = post_notification_event(
            self.service,
            {
                'event_id': '11111111-1111-1111-1111-111111111111',
                'event_type': 'payroll.record.processed',
                'tenant_id': 'tenant-acme',
                'timestamp': '2026-03-21T00:00:00+00:00',
                'source': 'payroll-service',
                'data': {
                    'employee_id': 'emp-001',
                    'employee_email': 'amina.yusuf@example.com',
                    'pay_period_start': '2026-03-01',
                    'pay_period_end': '2026-03-31',
                    'net_pay': '5190.00',
                    'currency': 'USD',
                },
                'metadata': {
                    'version': 'v1',
                    'correlation_id': '22222222-2222-2222-2222-222222222222',
                },
            },
            trace_id='trace-canonical-event',
        )

        self.assertEqual(status, 202)
        self.assertEqual(response['data']['event_type'], 'payroll.record.processed')

        rejected_status, rejected_payload = post_notification_event(
            self.service,
            {
                'event_name': 'PayrollProcessed',
                'employee_id': 'emp-001',
            },
            trace_id='trace-missing-tenant',
        )
        self.assertEqual(rejected_status, 422)
        self.assertEqual(rejected_payload['error']['code'], 'VALIDATION_ERROR')

    def test_unsupported_events_return_validation_error(self) -> None:
        status, payload = post_notification_event(
            self.service,
            {'event_type': 'unknown.entity.received', 'tenant_id': 'tenant-acme', 'employee_id': 'emp-001'},
            trace_id='trace-bad-event',
        )
        self.assertEqual(status, 422)
        self.assertEqual(payload['error']['code'], 'UNSUPPORTED_EVENT')


if __name__ == '__main__':
    unittest.main()
