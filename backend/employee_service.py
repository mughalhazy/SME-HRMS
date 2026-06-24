from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from event_contract import EventRegistry
from outbox_system import OutboxManager
from persistent_store import PersistentKVStore
from resilience import CentralErrorLogger, DeadLetterQueue, IdempotencyStore, Observability
from tenant_support import DEFAULT_TENANT_ID, assert_tenant_access, normalize_tenant_id


@dataclass
class Department:
    tenant_id: str
    department_id: str
    name: str
    code: str
    description: str | None
    parent_department_id: str | None
    head_employee_id: str | None
    status: str  # Proposed | Active | Inactive | Archived
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Role:
    tenant_id: str
    role_id: str
    title: str
    level: str | None
    description: str | None
    employment_category: str  # Staff | Manager | Executive | Contractor
    permissions: list[str]
    status: str  # Draft | Active | Inactive | Archived
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Employee:
    tenant_id: str
    employee_id: str
    employee_number: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    hire_date: str | None
    employment_type: str  # FullTime | PartTime | Contract | Intern
    status: str  # Draft | Active | OnLeave | Suspended | Terminated
    department_id: str | None
    role_id: str | None
    manager_employee_id: str | None
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EmployeeServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str, trace_id: str, details: list[dict] | None = None):
        self.status_code = status_code
        self.payload = {
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "trace_id": trace_id,
            }
        }
        super().__init__(message)


class EmployeeService:
    def __init__(self, db_path: str | None = None):
        self.departments = PersistentKVStore[str, Department](service='employee-service', namespace='departments', db_path=db_path)
        shared_db_path = self.departments.db_path
        self.roles = PersistentKVStore[str, Role](service='employee-service', namespace='roles', db_path=shared_db_path)
        self.employees = PersistentKVStore[str, Employee](service='employee-service', namespace='employees', db_path=shared_db_path)

        self.error_logger = CentralErrorLogger('employee-service')
        self.dead_letters = DeadLetterQueue()
        self.idempotency = IdempotencyStore()
        self.observability = Observability('employee-service')
        self.tenant_id = DEFAULT_TENANT_ID
        self.event_registry = EventRegistry()
        self.outbox = OutboxManager(
            service_name='employee-service',
            tenant_id=self.tenant_id,
            db_path=shared_db_path,
            observability=self.observability,
            dead_letters=self.dead_letters,
            event_registry=self.event_registry,
        )
        self._lock = RLock()

        self._seed_departments()
        self._seed_employees()

    # ---------------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------------

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _trace(self, trace_id: str | None) -> str:
        return self.observability.trace_id(trace_id)

    def _fail(self, status_code: int, code: str, message: str, trace_id: str | None, details: list[dict] | None = None) -> None:
        trace = self._trace(trace_id)
        error = EmployeeServiceError(status_code, code, message, trace, details)
        self.error_logger.log(code, error, trace_id=trace, details={"details": details or []})
        raise error

    def _resolve_tenant(self, tenant_id: str | None = None) -> str:
        return normalize_tenant_id(tenant_id or self.tenant_id)

    def _assert_tenant(self, tenant_id: str, trace_id: str | None) -> None:
        try:
            assert_tenant_access(tenant_id, self.tenant_id)
        except PermissionError:
            self._fail(403, "TENANT_SCOPE_VIOLATION", "Tenant scope does not permit this operation", trace_id)

    def _emit(self, *, event_name: str, aggregate_id: str, data: dict[str, Any], trace_id: str) -> None:
        self.outbox.enqueue(
            legacy_event_name=event_name,
            data=data,
            correlation_id=trace_id,
        )

    # ---------------------------------------------------------------------------
    # Seed data — matches the existing stub's fallback values so existing
    # integrations and tests that depend on specific IDs continue to work.
    # ---------------------------------------------------------------------------

    def _seed_departments(self) -> None:
        if self.departments:
            return
        now = self._now()
        seed = [
            ("dep-hr", "People Operations", "HR", "People operations, talent, and compliance."),
            ("dep-eng", "Engineering", "ENG", "Product engineering and platform delivery."),
            ("dep-fin", "Finance", "FIN", "Financial planning, accounting, and reporting."),
        ]
        for dept_id, name, code, description in seed:
            self.departments[dept_id] = Department(
                tenant_id=self.tenant_id,
                department_id=dept_id,
                name=name,
                code=code,
                description=description,
                parent_department_id=None,
                head_employee_id=None,
                status="Active",
                created_at=now,
                updated_at=now,
            )

    def _seed_employees(self) -> None:
        if self.employees:
            return
        now = self._now()
        seed = [
            ("emp-hr-admin", "E-100", "Helen", "Brooks", "helen.brooks@example.com", "dep-hr"),
            ("emp-frontend-001", "E-101", "Noah", "Bennett", "noah.bennett@example.com", "dep-eng"),
        ]
        for emp_id, emp_num, first, last, email, dept_id in seed:
            self.employees[emp_id] = Employee(
                tenant_id=self.tenant_id,
                employee_id=emp_id,
                employee_number=emp_num,
                first_name=first,
                last_name=last,
                email=email,
                phone=None,
                hire_date=None,
                employment_type="FullTime",
                status="Active",
                department_id=dept_id,
                role_id=None,
                manager_employee_id=None,
                created_at=now,
                updated_at=now,
            )

    # ---------------------------------------------------------------------------
    # Departments
    # ---------------------------------------------------------------------------

    def create_department(self, payload: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        tenant_id = self._resolve_tenant(payload.get('tenant_id'))
        name = (payload.get('name') or '').strip()
        code = (payload.get('code') or '').strip()
        if not name:
            self._fail(422, "VALIDATION_ERROR", "'name' is required", trace)
        if not code:
            self._fail(422, "VALIDATION_ERROR", "'code' is required", trace)
        with self._lock:
            for dept in self.departments.values():
                if dept.tenant_id == tenant_id and dept.code == code:
                    self._fail(409, "DUPLICATE_CODE", f"Department code '{code}' already exists", trace)
            now = self._now()
            dept = Department(
                tenant_id=tenant_id,
                department_id=payload.get('department_id') or str(uuid.uuid4()),
                name=name,
                code=code,
                description=payload.get('description'),
                parent_department_id=payload.get('parent_department_id'),
                head_employee_id=payload.get('head_employee_id'),
                status=payload.get('status', 'Active'),
                created_at=now,
                updated_at=now,
            )
            self.departments[dept.department_id] = dept
        self._emit(event_name='DepartmentCreated', aggregate_id=dept.department_id, data=dept.to_dict(), trace_id=trace)
        return 201, dept.to_dict()

    def get_department(self, department_id: str, *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        dept = self.departments.get(department_id)
        if not dept:
            self._fail(404, "DEPARTMENT_NOT_FOUND", "Department not found", trace)
        return 200, dept.to_dict()

    def update_department(self, department_id: str, payload: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        with self._lock:
            dept = self.departments.get(department_id)
            if not dept:
                self._fail(404, "DEPARTMENT_NOT_FOUND", "Department not found", trace)
            updated = Department(
                tenant_id=dept.tenant_id,
                department_id=dept.department_id,
                name=payload.get('name', dept.name),
                code=payload.get('code', dept.code),
                description=payload.get('description', dept.description),
                parent_department_id=payload.get('parent_department_id', dept.parent_department_id),
                head_employee_id=payload.get('head_employee_id', dept.head_employee_id),
                status=payload.get('status', dept.status),
                created_at=dept.created_at,
                updated_at=self._now(),
            )
            self.departments[department_id] = updated
        self._emit(event_name='DepartmentUpdated', aggregate_id=department_id, data=updated.to_dict(), trace_id=trace)
        return 200, updated.to_dict()

    def list_departments(self, *, tenant_id: str | None = None, status: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = self._resolve_tenant(tenant_id)
        items = [
            dept.to_dict() for dept in self.departments.values()
            if dept.tenant_id == tenant and (not status or dept.status == status)
        ]
        return 200, {"items": items, "count": len(items)}

    # ---------------------------------------------------------------------------
    # Roles
    # ---------------------------------------------------------------------------

    def create_role(self, payload: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        tenant_id = self._resolve_tenant(payload.get('tenant_id'))
        title = (payload.get('title') or '').strip()
        if not title:
            self._fail(422, "VALIDATION_ERROR", "'title' is required", trace)
        with self._lock:
            for role in self.roles.values():
                if role.tenant_id == tenant_id and role.title == title:
                    self._fail(409, "DUPLICATE_TITLE", f"Role title '{title}' already exists", trace)
            now = self._now()
            role = Role(
                tenant_id=tenant_id,
                role_id=payload.get('role_id') or str(uuid.uuid4()),
                title=title,
                level=payload.get('level'),
                description=payload.get('description'),
                employment_category=payload.get('employment_category', 'Staff'),
                permissions=list(payload.get('permissions') or []),
                status=payload.get('status', 'Draft'),
                created_at=now,
                updated_at=now,
            )
            self.roles[role.role_id] = role
        self._emit(event_name='RoleCreated', aggregate_id=role.role_id, data=role.to_dict(), trace_id=trace)
        return 201, role.to_dict()

    def get_role(self, role_id: str, *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        role = self.roles.get(role_id)
        if not role:
            self._fail(404, "ROLE_NOT_FOUND", "Role not found", trace)
        return 200, role.to_dict()

    def update_role(self, role_id: str, payload: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        with self._lock:
            role = self.roles.get(role_id)
            if not role:
                self._fail(404, "ROLE_NOT_FOUND", "Role not found", trace)
            updated = Role(
                tenant_id=role.tenant_id,
                role_id=role.role_id,
                title=payload.get('title', role.title),
                level=payload.get('level', role.level),
                description=payload.get('description', role.description),
                employment_category=payload.get('employment_category', role.employment_category),
                permissions=list(payload.get('permissions') or role.permissions),
                status=payload.get('status', role.status),
                created_at=role.created_at,
                updated_at=self._now(),
            )
            self.roles[role_id] = updated
        self._emit(event_name='RoleUpdated', aggregate_id=role_id, data=updated.to_dict(), trace_id=trace)
        return 200, updated.to_dict()

    def list_roles(self, *, tenant_id: str | None = None, status: str | None = None, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        tenant = self._resolve_tenant(tenant_id)
        items = [
            role.to_dict() for role in self.roles.values()
            if role.tenant_id == tenant and (not status or role.status == status)
        ]
        return 200, {"items": items, "count": len(items)}

    # ---------------------------------------------------------------------------
    # Employees
    # ---------------------------------------------------------------------------

    def create_employee(self, payload: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        tenant_id = self._resolve_tenant(payload.get('tenant_id'))
        first_name = (payload.get('first_name') or '').strip()
        last_name = (payload.get('last_name') or '').strip()
        email = (payload.get('email') or '').strip()
        if not first_name:
            self._fail(422, "VALIDATION_ERROR", "'first_name' is required", trace)
        if not last_name:
            self._fail(422, "VALIDATION_ERROR", "'last_name' is required", trace)
        if not email:
            self._fail(422, "VALIDATION_ERROR", "'email' is required", trace)
        with self._lock:
            for emp in self.employees.values():
                if emp.tenant_id == tenant_id and emp.email == email:
                    self._fail(409, "DUPLICATE_EMAIL", f"Email '{email}' is already registered", trace)
            now = self._now()
            emp_num = payload.get('employee_number') or f"E-{str(uuid.uuid4())[:8].upper()}"
            emp = Employee(
                tenant_id=tenant_id,
                employee_id=payload.get('employee_id') or str(uuid.uuid4()),
                employee_number=emp_num,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=payload.get('phone'),
                hire_date=payload.get('hire_date'),
                employment_type=payload.get('employment_type', 'FullTime'),
                status=payload.get('status', 'Draft'),
                department_id=payload.get('department_id'),
                role_id=payload.get('role_id'),
                manager_employee_id=payload.get('manager_employee_id'),
                created_at=now,
                updated_at=now,
            )
            self.employees[emp.employee_id] = emp
        self._emit(event_name='EmployeeCreated', aggregate_id=emp.employee_id, data=emp.to_dict(), trace_id=trace)
        return 201, emp.to_dict()

    def get_employee(self, employee_id: str, *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        emp = self.employees.get(employee_id)
        if not emp:
            self._fail(404, "EMPLOYEE_NOT_FOUND", "Employee not found", trace)
        return 200, emp.to_dict()

    def update_employee(self, employee_id: str, payload: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        with self._lock:
            emp = self.employees.get(employee_id)
            if not emp:
                self._fail(404, "EMPLOYEE_NOT_FOUND", "Employee not found", trace)
            prev_status = emp.status
            updated = Employee(
                tenant_id=emp.tenant_id,
                employee_id=emp.employee_id,
                employee_number=payload.get('employee_number', emp.employee_number),
                first_name=payload.get('first_name', emp.first_name),
                last_name=payload.get('last_name', emp.last_name),
                email=payload.get('email', emp.email),
                phone=payload.get('phone', emp.phone),
                hire_date=payload.get('hire_date', emp.hire_date),
                employment_type=payload.get('employment_type', emp.employment_type),
                status=payload.get('status', emp.status),
                department_id=payload.get('department_id', emp.department_id),
                role_id=payload.get('role_id', emp.role_id),
                manager_employee_id=payload.get('manager_employee_id', emp.manager_employee_id),
                created_at=emp.created_at,
                updated_at=self._now(),
            )
            self.employees[employee_id] = updated
        self._emit(event_name='EmployeeUpdated', aggregate_id=employee_id, data=updated.to_dict(), trace_id=trace)
        if updated.status != prev_status:
            self._emit(
                event_name='EmployeeStatusChanged',
                aggregate_id=employee_id,
                data={**updated.to_dict(), 'previous_status': prev_status},
                trace_id=trace,
            )
        return 200, updated.to_dict()

    def list_employees(
        self,
        *,
        tenant_id: str | None = None,
        department_id: str | None = None,
        status: str | None = None,
        trace_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        tenant = self._resolve_tenant(tenant_id)
        items = [
            emp.to_dict() for emp in self.employees.values()
            if emp.tenant_id == tenant
            and (not department_id or emp.department_id == department_id)
            and (not status or emp.status == status)
        ]
        return 200, {"items": items, "count": len(items)}

    def terminate_employee(self, employee_id: str, payload: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        with self._lock:
            emp = self.employees.get(employee_id)
            if not emp:
                self._fail(404, "EMPLOYEE_NOT_FOUND", "Employee not found", trace)
            if emp.status == 'Terminated':
                self._fail(409, "ALREADY_TERMINATED", "Employee is already terminated", trace)
            prev_status = emp.status
            updated = Employee(
                tenant_id=emp.tenant_id,
                employee_id=emp.employee_id,
                employee_number=emp.employee_number,
                first_name=emp.first_name,
                last_name=emp.last_name,
                email=emp.email,
                phone=emp.phone,
                hire_date=emp.hire_date,
                employment_type=emp.employment_type,
                status='Terminated',
                department_id=emp.department_id,
                role_id=emp.role_id,
                manager_employee_id=emp.manager_employee_id,
                created_at=emp.created_at,
                updated_at=self._now(),
            )
            self.employees[employee_id] = updated
        self._emit(
            event_name='EmployeeStatusChanged',
            aggregate_id=employee_id,
            data={**updated.to_dict(), 'previous_status': prev_status, 'reason': payload.get('reason')},
            trace_id=trace,
        )
        return 200, updated.to_dict()

    def transfer_employee(self, employee_id: str, payload: dict[str, Any], *, trace_id: str | None = None) -> tuple[int, dict[str, Any]]:
        trace = self._trace(trace_id)
        new_department_id = payload.get('department_id')
        if not new_department_id:
            self._fail(422, "VALIDATION_ERROR", "'department_id' is required for a transfer", trace)
        with self._lock:
            emp = self.employees.get(employee_id)
            if not emp:
                self._fail(404, "EMPLOYEE_NOT_FOUND", "Employee not found", trace)
            if emp.status not in ('Active', 'OnLeave'):
                self._fail(409, "INVALID_STATUS", "Only Active or OnLeave employees can be transferred", trace)
            prev_dept = emp.department_id
            updated = Employee(
                tenant_id=emp.tenant_id,
                employee_id=emp.employee_id,
                employee_number=emp.employee_number,
                first_name=emp.first_name,
                last_name=emp.last_name,
                email=emp.email,
                phone=emp.phone,
                hire_date=emp.hire_date,
                employment_type=emp.employment_type,
                status=emp.status,
                department_id=new_department_id,
                role_id=payload.get('role_id', emp.role_id),
                manager_employee_id=payload.get('manager_employee_id', emp.manager_employee_id),
                created_at=emp.created_at,
                updated_at=self._now(),
            )
            self.employees[employee_id] = updated
        self._emit(
            event_name='EmployeeUpdated',
            aggregate_id=employee_id,
            data={**updated.to_dict(), 'previous_department_id': prev_dept, 'transfer_reason': payload.get('reason')},
            trace_id=trace,
        )
        return 200, updated.to_dict()
