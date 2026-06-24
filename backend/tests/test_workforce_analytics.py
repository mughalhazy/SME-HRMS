from __future__ import annotations

import importlib.util
from pathlib import Path

from services.analytics.workforce import WorkforceAnalyticsService

API_MODULE_PATH = Path(__file__).resolve().parents[1] / 'api' / 'workforce.py'
API_SPEC = importlib.util.spec_from_file_location('workforce_api_module', API_MODULE_PATH)
assert API_SPEC and API_SPEC.loader
workforce_api = importlib.util.module_from_spec(API_SPEC)
API_SPEC.loader.exec_module(workforce_api)


def test_workforce_metric_calculations_align_to_decision_bands() -> None:
    service = WorkforceAnalyticsService()

    absenteeism = service.calculate_absenteeism(absent_days=4, working_days=20, expected_absence_rate=3)
    assert absenteeism['value'] == 20.0
    assert absenteeism['risk_score'] == 100.0
    assert absenteeism['threshold_level'] == 'high'

    overtime = service.calculate_overtime_pattern(overtime_hours=[12, 10, 9, 11], expected_hours=8)
    assert overtime['value'] == 10.5
    assert overtime['threshold_level'] == 'low'
    assert overtime['why_flagged']['anomaly_type'] == 'overtime_anomaly'

    attrition = service.calculate_attrition_risk(
        engagement_score=45,
        tenure_months=5,
        absenteeism_rate=8,
        overtime_ratio=1.7,
    )
    assert attrition['value'] >= 60
    assert attrition['threshold_level'] in {'medium', 'high'}

    burnout = service.calculate_burnout_index(
        engagement_score=50,
        overtime_hours=18,
        absent_days=3,
        working_days=20,
    )
    assert burnout['value'] > 50
    assert burnout['decision_card']['recommended_action']


def test_workforce_api_returns_success_payloads() -> None:
    service = WorkforceAnalyticsService(tenant_id='tenant-qa')

    status_abs, payload_abs = workforce_api.post_absenteeism_metric(service, {'absent_days': 2, 'working_days': 20})
    assert status_abs == 200
    assert payload_abs['status'] == 'success'
    assert payload_abs['data']['metric'] == 'absenteeism_rate'

    status_ot, payload_ot = workforce_api.post_overtime_pattern_metric(service, {'overtime_hours': [8, 8, 9, 10], 'expected_hours': 8})
    assert status_ot == 200
    assert payload_ot['data']['metric'] == 'overtime_pattern'

    status_attr, payload_attr = workforce_api.post_attrition_risk_metric(
        service,
        {'engagement_score': 70, 'tenure_months': 18, 'absenteeism_rate': 2, 'overtime_ratio': 0.8},
    )
    assert status_attr == 200
    assert payload_attr['data']['metric'] == 'attrition_risk'

    status_burn, payload_burn = workforce_api.post_burnout_index_metric(
        service,
        {'engagement_score': 68, 'overtime_hours': 7, 'absent_days': 1, 'working_days': 20},
    )
    assert status_burn == 200
    assert payload_burn['data']['metric'] == 'burnout_index'


def test_workforce_api_returns_validation_errors() -> None:
    service = WorkforceAnalyticsService()
    status, payload = workforce_api.post_absenteeism_metric(service, {'absent_days': 1, 'working_days': 0})

    assert status == 422
    assert payload['status'] == 'error'
    assert payload['error']['code'] == 'VALIDATION_ERROR'
