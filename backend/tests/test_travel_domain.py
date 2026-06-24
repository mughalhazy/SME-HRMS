from __future__ import annotations

from pathlib import Path

from audit_service.service import get_audit_service
from notification_service import NotificationService
from travel_service import TravelService
from workflow_service import WorkflowService


def _seed_employees(service: TravelService) -> None:
    service.register_employee_profile(
        {
            'employee_id': 'travel-admin',
            'employee_number': 'E-100',
            'full_name': 'Taylor Travel',
            'department_id': 'dep-ops',
            'department_name': 'Travel Ops',
            'manager_employee_id': None,
            'email': 'travel-admin@example.com',
        }
    )
    service.register_employee_profile(
        {
            'employee_id': 'emp-mgr-1',
            'employee_number': 'E-101',
            'full_name': 'Morgan Manager',
            'department_id': 'dep-eng',
            'department_name': 'Engineering',
            'manager_employee_id': 'travel-admin',
            'email': 'manager@example.com',
        }
    )
    service.register_employee_profile(
        {
            'employee_id': 'emp-1',
            'employee_number': 'E-102',
            'full_name': 'Avery Traveler',
            'department_id': 'dep-eng',
            'department_name': 'Engineering',
            'manager_employee_id': 'emp-mgr-1',
            'email': 'employee@example.com',
        }
    )
    service.register_employee_profile(
        {
            'employee_id': 'travel-desk',
            'employee_number': 'E-103',
            'full_name': 'Drew Desk',
            'department_id': 'dep-ops',
            'department_name': 'Travel Ops',
            'manager_employee_id': 'travel-admin',
            'email': 'travel-desk@example.com',
        }
    )


def test_travel_service_supports_workflow_itinerary_audit_and_notifications(tmp_path: Path) -> None:
    notifications = NotificationService()
    workflows = WorkflowService(notification_service=notifications)
    service = TravelService(db_path=str(tmp_path / 'travel.sqlite3'), workflow_service=workflows, notification_service=notifications)
    _seed_employees(service)

    _, created = service.create_request(
        {
            'employee_id': 'emp-1',
            'purpose': 'Customer kickoff and workshops',
            'trip_type': 'RoundTrip',
            'origin_city': 'New York',
            'destination_city': 'Austin',
            'start_date': '2026-05-10',
            'end_date': '2026-05-13',
            'estimated_cost': 1850.55,
            'currency': 'USD',
            'notes': 'Need hotel near convention center',
        },
        actor_id='emp-1',
        trace_id='trace-travel-create',
    )
    assert created['status'] == 'Draft'
    assert created['employee']['full_name'] == 'Avery Traveler'

    _, submitted = service.submit_request(created['travel_request_id'], actor_id='emp-1', trace_id='trace-travel-submit')
    assert submitted['status'] == 'Submitted'
    assert submitted['workflow']['definition_code'] == 'travel_request_approval'

    _, manager_step = service.decide_request(created['travel_request_id'], action='approve', actor_id='emp-mgr-1', actor_role='Manager', trace_id='trace-travel-manager-approve')
    assert manager_step['status'] == 'Submitted'
    assert manager_step['workflow']['status'] in {'pending', 'in_progress', 'Pending', 'InProgress'}

    _, approved = service.decide_request(created['travel_request_id'], action='approve', actor_id='travel-desk', actor_role='Admin', trace_id='trace-travel-desk-approve')
    assert approved['status'] == 'Approved'
    assert approved['workflow']['metadata']['terminal_result'] == 'approved'

    _, booked = service.update_itinerary(
        created['travel_request_id'],
        {
            'itinerary_segments': [
                {
                    'segment_type': 'Flight',
                    'departure_city': 'New York',
                    'arrival_city': 'Austin',
                    'departure_at': '2026-05-10T09:00:00+00:00',
                    'arrival_at': '2026-05-10T13:00:00+00:00',
                    'provider_name': 'OpenSkies',
                    'booking_reference': 'OS-12345',
                },
                {
                    'segment_type': 'Hotel',
                    'departure_city': 'Austin',
                    'arrival_city': 'Austin',
                    'departure_at': '2026-05-10T15:00:00+00:00',
                    'arrival_at': '2026-05-13T11:00:00+00:00',
                    'lodging_name': 'Downtown Suites',
                    'lodging_address': '100 Congress Ave',
                },
            ]
        },
        actor_id='travel-desk',
        trace_id='trace-travel-itinerary',
    )
    assert booked['status'] == 'Booked'
    assert booked['segment_count'] == 2

    _, completed = service.complete_request(created['travel_request_id'], actor_id='travel-desk', trace_id='trace-travel-complete')
    assert completed['status'] == 'Completed'

    _, listed = service.list_requests(employee_id='emp-1', status='Completed', limit=10)
    assert listed['_pagination']['count'] == 1
    assert listed['items'][0]['travel_request_id'] == created['travel_request_id']

    records, _ = get_audit_service().list_records(tenant_id='tenant-default', entity='TravelRequest', limit=20)
    actions = {record['action'] for record in records}
    assert 'travel_request_submitted' in actions
    assert 'travel_itinerary_updated' in actions
    assert 'travel_request_completed' in actions
    assert any(event['legacy_event_name'] == 'TravelRequestApproved' for event in service.events)
    assert any(event['legacy_event_name'] == 'TravelItineraryUpdated' for event in service.events)
    assert any(message.event_name == 'WorkflowTaskAssigned' for message in notifications.messages.values())


def test_travel_service_rejects_invalid_employee_reference(tmp_path: Path) -> None:
    service = TravelService(db_path=str(tmp_path / 'travel-invalid.sqlite3'))
    _seed_employees(service)

    try:
        service.create_request(
            {
                'employee_id': 'missing-employee',
                'purpose': 'Broken request',
                'trip_type': 'OneWay',
                'origin_city': 'Boston',
                'destination_city': 'Chicago',
                'start_date': '2026-06-01',
                'end_date': '2026-06-02',
            },
            actor_id='emp-1',
            trace_id='trace-travel-invalid',
        )
    except Exception as exc:  # pragma: no cover
        assert 'employee-service read model' in str(exc)
    else:  # pragma: no cover
        raise AssertionError('expected missing employee reference to fail')
