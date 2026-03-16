import unittest

from employee_ui import build_employee_ui


class EmployeeUiBuilderTests(unittest.TestCase):
    def test_build_employee_ui_includes_expected_surfaces(self) -> None:
        ui = build_employee_ui()

        self.assertEqual(set(ui.keys()), {"employee_list", "employee_profile"})

    def test_employee_list_maps_to_canonical_read_model(self) -> None:
        ui = build_employee_ui()
        employee_list = ui["employee_list"]

        self.assertEqual(employee_list["primary_read_models"], ["employee_directory_view"])
        self.assertEqual(employee_list["capability_ids"], ["CAP-EMP-001"])
        self.assertEqual(employee_list["primary_service_owner"], "employee-service")

        self.assertEqual(employee_list["view"]["read_model"], "employee_directory_view")
        self.assertIn("full_name", employee_list["view"]["columns"])
        self.assertIn("department_name", employee_list["view"]["columns"])

    def test_employee_profile_composes_related_panels(self) -> None:
        ui = build_employee_ui()
        profile = ui["employee_profile"]

        self.assertEqual(
            profile["primary_read_models"],
            [
                "employee_directory_view",
                "attendance_dashboard_view",
                "leave_requests_view",
                "payroll_summary_view",
                "performance_review_view",
            ],
        )

        panels = profile["view"]["panels"]
        self.assertEqual(panels["identity"]["read_model"], "employee_directory_view")
        self.assertEqual(panels["attendance"]["read_model"], "attendance_dashboard_view")
        self.assertEqual(panels["leave"]["read_model"], "leave_requests_view")
        self.assertEqual(panels["payroll"]["read_model"], "payroll_summary_view")
        self.assertEqual(panels["performance"]["read_model"], "performance_review_view")

    def test_builder_returns_mutable_copy(self) -> None:
        one = build_employee_ui()
        two = build_employee_ui()

        one["employee_list"]["view"]["columns"].append("temporary")
        self.assertNotIn("temporary", two["employee_list"]["view"]["columns"])


if __name__ == "__main__":
    unittest.main()
