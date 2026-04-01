from integrations.whatsapp.webhook import parse_intent, receive_message


def _payload(text: str) -> dict[str, object]:
    return {
        'event_id': 'evt_123',
        'timestamp': '2026-04-01T09:15:22Z',
        'channel': 'whatsapp',
        'message': {
            'message_id': 'wamid.abc',
            'from': '+15551234567',
            'type': 'text',
            'text': text,
        },
    }


def test_parse_intent_supported_commands() -> None:
    assert parse_intent('payslip 2026-03')['intent'] == 'payslip.get'
    assert parse_intent('leave')['intent'] == 'leave.apply'
    assert parse_intent('approval')['intent'] == 'approval.pending'


def test_parse_intent_unknown_command() -> None:
    parsed = parse_intent('hello there')
    assert parsed['intent'] == 'unknown'
    assert parsed['status'] == 'error'


def test_receive_message_payslip_flow_returns_interactive_response() -> None:
    status, response = receive_message(_payload('payslip 2026-03'))
    assert status == 200
    assert response['type'] == 'interactive'
    assert response['meta']['intent'] == 'payslip.get'
    assert response['attachments'][0]['url'].startswith('https://')


def test_receive_message_leave_flow_returns_prompt() -> None:
    status, response = receive_message(_payload('leave'))
    assert status == 200
    assert response['meta']['intent'] == 'leave.apply'
    assert 'Leave flow started' in response['text']


def test_receive_message_approval_flow_returns_pending_actions() -> None:
    status, response = receive_message(_payload('approval'))
    assert status == 200
    assert response['meta']['intent'] == 'approval.pending'
    assert 'approve <request_id>' in response['text']


def test_receive_message_unknown_command_returns_help() -> None:
    status, response = receive_message(_payload('unknown command'))
    assert status == 200
    assert response['meta']['intent'] == 'unknown'
    assert 'Try: payslip, leave, or approval.' in response['text']
