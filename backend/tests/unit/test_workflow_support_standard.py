from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text()


def test_workflow_resolution_is_reused_across_services() -> None:
    expected = {
        "leave_service.py": ("resolve_workflow_action", "require_terminal_workflow_result"),
        "performance_service.py": ("resolve_workflow_action", "require_terminal_workflow_result"),
        "travel_service.py": ("resolve_workflow_action", "require_terminal_workflow_result"),
        "project_service.py": ("resolve_workflow_action", "require_terminal_workflow_result"),
        "expense_service.py": ("resolve_workflow_action", "require_terminal_workflow_result"),
        "helpdesk_service.py": ("resolve_workflow_action", "require_terminal_workflow_result"),
        "payroll_service.py": ("resolve_workflow_action", "require_terminal_workflow_result"),
        "attendance_service/service.py": ("resolve_workflow_action",),
        "services/hiring_service/service.py": ("resolve_workflow_action", "require_terminal_workflow_result"),
    }

    for path, tokens in expected.items():
        contents = _read(path)
        assert "from workflow_support import" in contents
        for token in tokens:
            assert token in contents


def test_workflow_convergence_keeps_audit_and_tenant_guards_in_place() -> None:
    for path in [
        "leave_service.py",
        "performance_service.py",
        "travel_service.py",
        "project_service.py",
        "expense_service.py",
        "helpdesk_service.py",
        "payroll_service.py",
        "attendance_service/service.py",
        "services/hiring_service/service.py",
    ]:
        contents = _read(path)
        assert "assert_tenant_access" in contents or path in {"attendance_service/service.py", "payroll_service.py"}
        assert "emit_audit_record" in contents or "_audit(" in contents or "_audit_payroll_mutation(" in contents
