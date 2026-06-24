"""Canonical employee UI builder.

This module defines a single builder function, :func:`build_employee_ui`,
that translates canonical documentation into a concrete UI configuration for
employee-focused surfaces.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_EMPLOYEE_UI_CONFIG: dict[str, Any] = {
    "employee_list": {
        "surface": "employee_list",
        "primary_read_models": ["employee_directory_view"],
        "capability_ids": ["CAP-EMP-001"],
        "primary_service_owner": "employee-service",
        "domain_entities": ["Employee", "Department", "Role"],
        "view": {
            "type": "table",
            "read_model": "employee_directory_view",
            "columns": [
                "employee_number",
                "full_name",
                "email",
                "phone",
                "hire_date",
                "employment_type",
                "employee_status",
                "department_name",
                "role_title",
                "manager_name",
                "updated_at",
            ],
            "key": "employee_id",
        },
    },
    "employee_form": {
        "surface": "employee_form",
        "primary_read_models": ["employee_directory_view"],
        "capability_ids": ["CAP-EMP-001", "CAP-EMP-002"],
        "primary_service_owner": "employee-service",
        "domain_entities": ["Employee", "Department", "Role"],
        "view": {
            "type": "form",
            "mode": ["create", "edit"],
            "read_model": "employee_directory_view",
            "fields": [
                "employee_number",
                "first_name",
                "last_name",
                "email",
                "phone",
                "hire_date",
                "employment_type",
                "employee_status",
                "department_id",
                "role_id",
                "manager_employee_id",
            ],
            "validation": "client_and_api",
        },
    },
    "employee_profile": {
        "surface": "employee_profile",
        "primary_read_models": [
            "employee_directory_view",
            "attendance_dashboard_view",
            "leave_requests_view",
            "payroll_summary_view",
            "performance_review_view",
        ],
        "capability_ids": [
            "CAP-EMP-002",
            "CAP-ATT-001",
            "CAP-LEV-001",
            "CAP-PAY-001",
            "CAP-PRF-001",
        ],
        "primary_service_owner": "employee-service",
        "domain_entities": [
            "Employee",
            "Department",
            "Role",
            "AttendanceRecord",
            "LeaveRequest",
            "PayrollRecord",
            "PerformanceReview",
        ],
        "view": {
            "type": "composite",
            "panels": {
                "identity": {
                    "read_model": "employee_directory_view",
                    "fields": [
                        "employee_id",
                        "employee_number",
                        "full_name",
                        "email",
                        "phone",
                        "hire_date",
                        "employment_type",
                        "employee_status",
                        "department_name",
                        "role_title",
                        "manager_name",
                        "updated_at",
                    ],
                },
                "attendance": {
                    "read_model": "attendance_dashboard_view",
                    "fields": [
                        "attendance_date",
                        "attendance_status",
                        "check_in_time",
                        "check_out_time",
                        "total_hours",
                        "record_state",
                        "updated_at",
                    ],
                },
                "leave": {
                    "read_model": "leave_requests_view",
                    "fields": [
                        "leave_request_id",
                        "leave_type",
                        "start_date",
                        "end_date",
                        "total_days",
                        "status",
                        "submitted_at",
                        "decision_at",
                        "updated_at",
                    ],
                },
                "payroll": {
                    "read_model": "payroll_summary_view",
                    "fields": [
                        "payroll_record_id",
                        "pay_period_start",
                        "pay_period_end",
                        "base_salary",
                        "allowances",
                        "deductions",
                        "overtime_pay",
                        "gross_pay",
                        "net_pay",
                        "currency",
                        "payment_date",
                        "status",
                        "updated_at",
                    ],
                },
                "performance": {
                    "read_model": "performance_review_view",
                    "fields": [
                        "performance_review_id",
                        "reviewer_name",
                        "review_period_start",
                        "review_period_end",
                        "overall_rating",
                        "status",
                        "submitted_at",
                        "acknowledged_at",
                        "updated_at",
                    ],
                },
            },
        },
    },
}


def build_employee_ui() -> dict[str, Any]:
    """Build the canonical employee UI surface configuration.

    Returns a deep copy so callers can mutate the returned payload safely.
    """

    return deepcopy(_EMPLOYEE_UI_CONFIG)
