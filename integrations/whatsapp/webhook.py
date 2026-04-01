from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

_SUPPORTED_COMMANDS = {
    'payslip': 'payslip.get',
    'leave': 'leave.apply',
    'approval': 'approval.pending',
}


def parse_intent(message_text: str | None) -> dict[str, object]:
    """Parse a WhatsApp message into a supported HR intent.

    Supports commands aligned with docs/specs/integrations/whatsapp.md:
    - payslip
    - leave
    - approval
    """

    normalized = (message_text or '').strip().lower()
    if not normalized:
        return {'intent': 'unknown', 'status': 'error', 'command': None, 'args': []}

    parts = normalized.split()
    command = parts[0]
    args = parts[1:]

    if command not in _SUPPORTED_COMMANDS:
        return {'intent': 'unknown', 'status': 'error', 'command': command, 'args': args}

    return {
        'intent': _SUPPORTED_COMMANDS[command],
        'status': 'success',
        'command': command,
        'args': args,
    }


def receive_message(payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    """Process inbound WhatsApp webhook and produce outbound API response schema."""

    message = payload.get('message') if isinstance(payload, dict) else None
    if not isinstance(message, dict):
        return 400, {
            'correlation_id': f'corr_{uuid4().hex[:10]}',
            'status': 'error',
            'code': 'VALIDATION_ERROR',
            'message': 'Missing required message envelope.',
            'recoverable': True,
            'next_step': 'Send a valid WhatsApp payload with a message object.',
        }

    sender = str(message.get('from') or '').strip()
    message_type = str(message.get('type') or '').strip().lower()
    text = message.get('text')

    if not sender or not message_type:
        return 400, {
            'correlation_id': f'corr_{uuid4().hex[:10]}',
            'status': 'error',
            'code': 'VALIDATION_ERROR',
            'message': 'Missing required message.from or message.type.',
            'recoverable': True,
            'next_step': 'Provide required webhook fields: message.from and message.type.',
        }

    if message_type != 'text':
        return 422, {
            'correlation_id': f'corr_{uuid4().hex[:10]}',
            'status': 'error',
            'code': 'VALIDATION_ERROR',
            'message': 'Only text messages are supported by this webhook handler.',
            'recoverable': True,
            'next_step': 'Send a text command: payslip, leave, or approval.',
        }

    parsed = parse_intent(text if isinstance(text, str) else None)
    correlation_id = f'corr_{uuid4().hex[:10]}'

    if parsed['status'] != 'success':
        return 200, {
            'correlation_id': correlation_id,
            'to': sender,
            'type': 'text',
            'text': 'I couldn\'t understand that command. Try: payslip, leave, or approval.',
            'meta': {
                'intent': 'unknown',
                'status': 'error',
                'request_id': f'req_{uuid4().hex[:8]}',
            },
        }

    command = str(parsed['command'])
    now = datetime.now(timezone.utc)
    request_id = f'req_{uuid4().hex[:8]}'

    if command == 'payslip':
        period = str(parsed['args'][0]) if parsed['args'] else now.strftime('%Y-%m')
        return 200, {
            'correlation_id': correlation_id,
            'to': sender,
            'type': 'interactive',
            'text': f'Your payslip for {period} is ready.',
            'interactive': {
                'buttons': [
                    {'id': f'download_payslip_{period.replace("-", "_")}', 'title': 'Download'},
                    {'id': f'view_summary_{period.replace("-", "_")}', 'title': 'Summary'},
                ]
            },
            'attachments': [
                {
                    'kind': 'link',
                    'label': 'Payslip PDF',
                    'url': f'https://hrms.example.com/payslip/{request_id}',
                    'expires_at': (now + timedelta(minutes=30)).isoformat(),
                }
            ],
            'meta': {'intent': 'payslip.get', 'status': 'success', 'request_id': request_id},
        }

    if command == 'leave':
        return 200, {
            'correlation_id': correlation_id,
            'to': sender,
            'type': 'text',
            'text': 'Leave flow started. Please provide leave type, start date, and end date (YYYY-MM-DD).',
            'meta': {'intent': 'leave.apply', 'status': 'success', 'request_id': request_id},
        }

    return 200, {
        'correlation_id': correlation_id,
        'to': sender,
        'type': 'text',
        'text': 'Pending approvals: send approve <request_id> or reject <request_id> <reason>.',
        'meta': {'intent': 'approval.pending', 'status': 'success', 'request_id': request_id},
    }
