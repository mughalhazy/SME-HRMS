import importlib.util
import pathlib
import sys
import unittest
from datetime import date

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "api-gateway" / "dashboard_ui.py"
SPEC = importlib.util.spec_from_file_location("api_gateway_dashboard_ui", MODULE_PATH)
dashboard_ui = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = dashboard_ui
SPEC.loader.exec_module(dashboard_ui)


class DashboardUiTests(unittest.TestCase):
    def test_dashboard_widgets_map_to_canonical_surfaces(self) -> None:
        widgets = list(dashboard_ui.iter_dashboard_widgets())
        self.assertEqual(len(widgets), 6)
        self.assertEqual([widget.read_model for widget in widgets], [
            "employee_directory_view",
            "attendance_dashboard_view",
            "leave_requests_view",
            "payroll_summary_view",
            "candidate_pipeline_view",
            "performance_review_view",
        ])

    def test_build_dashboard_ui_summarizes_read_models(self) -> None:
        payload = dashboard_ui.build_dashboard_ui(
            {
                "employee_directory_view": [
                    {"employee_id": "E1", "full_name": "Ali", "department_name": "HR", "employee_status": "Active"},
                    {"employee_id": "E2", "full_name": "Sara", "department_name": "Ops", "employee_status": "OnLeave"},
                ],
                "attendance_dashboard_view": [
                    {"employee_id": "E1", "employee_name": "Ali", "attendance_date": "2025-01-05", "attendance_status": "Present"},
                    {"employee_id": "E2", "employee_name": "Sara", "attendance_date": "2025-01-05", "attendance_status": "Late"},
                ],
                "leave_requests_view": [
                    {"leave_request_id": "L1", "employee_name": "Sara", "status": "Submitted"},
                    {"leave_request_id": "L2", "employee_name": "Ali", "status": "Approved"},
                ],
                "payroll_summary_view": [
                    {"payroll_record_id": "P1", "employee_name": "Ali", "status": "Processed", "net_pay": "1000.50"},
                    {"payroll_record_id": "P2", "employee_name": "Sara", "status": "Paid", "net_pay": "500"},
                ],
                "candidate_pipeline_view": [
                    {"candidate_id": "C1", "candidate_name": "Hina", "job_posting_id": "J1", "job_title": "Analyst", "pipeline_stage": "Screening"},
                    {"candidate_id": "C2", "candidate_name": "Khalid", "job_posting_id": "J1", "job_title": "Analyst", "pipeline_stage": "Interview"},
                ],
                "performance_review_view": [
                    {"performance_review_id": "R1", "employee_name": "Ali", "reviewer_name": "Manager A", "status": "Submitted"},
                ],
            },
            today=date(2025, 1, 5),
        )

        self.assertEqual(payload["surface"], "dashboard")
        self.assertEqual(payload["widgets"]["employees"]["summary"], {"total": 2, "active": 1})
        self.assertEqual(payload["widgets"]["attendance"]["summary"], {"today_records": 2, "present": 1})
        self.assertEqual(payload["widgets"]["leave"]["summary"], {"pending": 1, "approved": 1})
        self.assertEqual(payload["widgets"]["payroll"]["summary"]["net_pay_total"], "1500.50")
        self.assertEqual(payload["widgets"]["hiring"]["summary"], {"applications": 2, "openings": 1})
        self.assertEqual(payload["widgets"]["performance"]["summary"], {"reviews": 1, "submitted": 1})


if __name__ == "__main__":
    unittest.main()
