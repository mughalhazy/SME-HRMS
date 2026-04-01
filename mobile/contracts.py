from __future__ import annotations

import base64
import gzip
import json
from typing import Any, Mapping

from api_contract import pagination_payload, success_response

MOBILE_ENDPOINTS = {
    'dashboard': '/api/mobile/dashboard',
    'payslip_view': '/api/mobile/payslip',
    'leave_apply': '/api/mobile/leave/apply',
    'alerts': '/api/mobile/alerts',
}


def _compact_json(data: Mapping[str, Any]) -> bytes:
    return json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')


def encode_wire_payload(data: Mapping[str, Any]) -> dict[str, Any]:
    raw = _compact_json(data)
    compressed = gzip.compress(raw, compresslevel=9)
    return {
        'encoding': 'gzip+base64',
        'body': base64.b64encode(compressed).decode('ascii'),
        'raw_size_bytes': len(raw),
        'compressed_size_bytes': len(compressed),
    }


def build_mobile_response(
    endpoint: str,
    *,
    items: list[dict[str, Any]],
    request_id: str,
    cursor: str | None,
    next_cursor: str | None,
    page_size: int,
    source: list[str],
    fallback_used: bool = False,
) -> tuple[int, dict[str, Any]]:
    payload = {
        'endpoint': endpoint,
        'decision_first': True,
        'decision_cards_only': True,
        'minimal_payload': True,
        'fallback_used': fallback_used,
        'source': source,
        'items': items,
    }
    status, response = success_response(
        200,
        payload,
        request_id=request_id,
        pagination=pagination_payload(
            limit=page_size,
            cursor=cursor,
            next_cursor=next_cursor,
            count=len(items),
        ),
        service='mobile-gateway',
    )
    response['wire'] = encode_wire_payload(response)
    return status, response
