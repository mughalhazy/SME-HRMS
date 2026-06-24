from __future__ import annotations

import unittest

from travel_api import (
    get_travel_request,
    get_travel_requests,
    post_travel_request_complete,
    post_travel_request_decision,
    post_travel_request_submit,
    post_travel_requests,
    put_travel_itinerary,
)
from travel_service import TravelService


def seed(service: TravelService) -> None:
    for payload in [
        {
            'employee_id': 'travel-admin',
            'employee_number': 'E-201',
            'full_name': 'Taylor Travel',
            'department_id': 'dep-ops',
            'department_name': 'Travel Ops',
            'manager_employee_id': None,
            'email': 'travel-admin@example.com',
        },
        {
            'employee_id': 'emp-mgr-1',
            'employee_number': 'E-202',
            'full_name': 'Morgan Manager',
            'department_id': 'dep-eng',
            'department_name': 'Engineering',
            'manager_employee_id': 'travel-admin',
            'email': 'manager@example.com',
        },
        {
            'employee_id': 'emp-1',
            'employee_number': 'E-203',
            'full_name': 'Avery Traveler',
            'department_id': 'dep-eng',
            'department_name': 'Engineering',
            'manager_employee_id': 'emp-mgr-1',
            'email': 'employee@example.com',
        },
        {
            'employee_id': 'travel-desk',
            'employee_number': 'E-204',
            'full_name': 'Drew Desk',
            'department_id': 'dep-ops',
            'department_name': 'Travel Ops',
            'manager_employee_id': 'travel-admin',
            'email': 'travel-desk@example.com',
        },
    ]:
        service.register_employee_profile(payload)


class TravelApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = TravelService()
        seed(self.service)

    def test_create_submit_approve_book_and_complete_travel_request(self) -> None:
        status, created = post_travel_requests(
            self.service,
            'Employee',
            'emp-1',
            {
                'employee_id': 'emp-1',
                'purpose': 'Partner meetings',
                'trip_type': 'RoundTrip',
                'origin_city': 'Seattle',
                'destination_city': 'Denver',
                'start_date': '2026-08-10',
                'end_date': '2026-08-12',
                'estimated_cost': 950,
            },
            trace_id='trace-travel-api-create',
        )
        self.assertEqual(status, 201)
        self.assertEqual(created['status'], 'success')
        request_id = created['data']['travel_request_id']

        status, submitted = post_travel_request_submit(self.service, 'Employee', 'emp-1', request_id, trace_id='trace-travel-api-submit')
        self.assertEqual(status, 200)
        self.assertEqual(submitted['data']['status'], 'Submitted')

        status, interim = post_travel_request_decision(self.service, 'approve', 'Manager', 'emp-mgr-1', request_id, trace_id='trace-travel-api-manager-approve')
        self.assertEqual(status, 200)
        self.assertEqual(interim['data']['status'], 'Submitted')

        status, approved = post_travel_request_decision(self.service, 'approve', 'Admin', 'travel-desk', request_id, trace_id='trace-travel-api-desk-approve')
        self.assertEqual(status, 200)
        self.assertEqual(approved['data']['status'], 'Approved')

        status, booked = put_travel_itinerary(
            self.service,
            'Admin',
            'travel-desk',
            request_id,
            {
                'itinerary_segments': [
                    {
                        'segment_type': 'Flight',
                        'departure_city': 'Seattle',
                        'arrival_city': 'Denver',
                        'departure_at': '2026-08-10T14:00:00+00:00',
                        'arrival_at': '2026-08-10T17:00:00+00:00',
                    }
                ]
            },
            trace_id='trace-travel-api-itinerary',
        )
        self.assertEqual(status, 200)
        self.assertEqual(booked['data']['status'], 'Booked')

        status, completed = post_travel_request_complete(self.service, 'Admin', 'travel-desk', request_id, trace_id='trace-travel-api-complete')
        self.assertEqual(status, 200)
        self.assertEqual(completed['data']['status'], 'Completed')

        status, fetched = get_travel_request(self.service, 'Employee', 'emp-1', request_id, trace_id='trace-travel-api-get')
        self.assertEqual(status, 200)
        self.assertEqual(fetched['data']['travel_request_id'], request_id)

    def test_list_and_validate_travel_requests_via_api(self) -> None:
        _, created = post_travel_requests(
            self.service,
            'Employee',
            'emp-1',
            {
                'employee_id': 'emp-1',
                'purpose': 'Roadshow',
                'origin_city': 'San Jose',
                'destination_city': 'Phoenix',
                'start_date': '2026-09-01',
                'end_date': '2026-09-03',
            },
            trace_id='trace-travel-api-create-2',
        )
        request_id = created['data']['travel_request_id']
        post_travel_request_submit(self.service, 'Employee', 'emp-1', request_id, trace_id='trace-travel-api-submit-2')

        status, payload = get_travel_requests(self.service, 'Employee', 'emp-1', {'employee_id': 'emp-1', 'status': 'Submitted'}, trace_id='trace-travel-api-list')
        self.assertEqual(status, 200)
        self.assertEqual(len(payload['data']['items']), 1)
        self.assertEqual(payload['meta']['pagination']['count'], 1)
        self.assertEqual(payload['meta']['service'], 'travel-service')

        status, invalid = post_travel_requests(
            self.service,
            'Employee',
            'emp-1',
            {
                'employee_id': 'emp-1',
                'purpose': 'Invalid trip',
                'origin_city': 'San Jose',
                'destination_city': 'Phoenix',
                'start_date': 'bad-date',
                'end_date': '2026-09-03',
            },
            trace_id='trace-travel-api-invalid',
        )
        self.assertEqual(status, 422)
        self.assertEqual(invalid['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(invalid['meta']['request_id'], 'trace-travel-api-invalid')


if __name__ == '__main__':
    unittest.main()
