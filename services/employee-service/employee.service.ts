import {
  CreateEmployeeInput,
  Employee,
  EmployeeFilters,
  EmployeeReadModelBundle,
  EmployeeStatus,
  UpdateEmployeeInput,
} from './employee.model';
import { DepartmentRepository } from './department.repository';
import { EmployeeRepository } from './employee.repository';
import { validateCreateEmployee, validateStatus, validateUpdateEmployee, ValidationError } from './employee.validation';
import { RoleService } from './role.service';
import { ConflictError, NotFoundError } from './service.errors';

const STATUS_TRANSITIONS: Record<EmployeeStatus, EmployeeStatus[]> = {
  Draft: ['Active', 'Terminated'],
  Active: ['OnLeave', 'Suspended', 'Terminated'],
  OnLeave: ['Active', 'Suspended', 'Terminated'],
  Suspended: ['Active', 'Terminated'],
  Terminated: [],
};

export class EmployeeService {
  constructor(
    private readonly repository: EmployeeRepository,
    private readonly roleService: RoleService,
  ) {}

  createEmployee(input: CreateEmployeeInput): Employee {
    validateCreateEmployee(input);
    this.ensureUniqueEmployee(input.employee_number, input.email);
    this.ensureDepartmentAndRoleAreAssignable(input.department_id, input.role_id);
    this.ensureManagerRelationship(input.manager_employee_id);

    if (input.status === 'Active') {
      this.ensureActivationRequirements(input.department_id, input.role_id);
    }

    this.roleService.getActiveRoleById(input.role_id);

    const employee = this.repository.create(input);
    this.roleService.linkEmployee(employee.role_id, employee.employee_id);
    return employee;
  }

  getEmployeeById(employeeId: string): Employee {
    const employee = this.repository.findById(employeeId);

    if (!employee) {
      throw new NotFoundError('employee not found');
    }

    return employee;
  }

  getEmployeeReadModels(employeeId: string): EmployeeReadModelBundle {
    return this.repository.toReadModelBundle(this.getEmployeeById(employeeId));
  }

  listEmployees(filters: EmployeeFilters) {
    return this.repository.list(filters);
  }

  listEmployeeReadModels(filters: EmployeeFilters) {
    const page = this.repository.list(filters);
    return this.repository.toReadModelListBundle(page.data);
  }

  updateEmployee(employeeId: string, input: UpdateEmployeeInput): Employee {
    validateUpdateEmployee(input);

    const existing = this.repository.findById(employeeId);

    if (!existing) {
      throw new NotFoundError('employee not found');
    }

    if (input.email && input.email !== existing.email) {
      const sameEmail = this.repository.findByEmail(input.email);
      if (sameEmail && sameEmail.employee_id !== employeeId) {
        throw new ConflictError('email already exists');
      }
    }

    const nextDepartmentId = input.department_id ?? existing.department_id;
    const nextRoleId = input.role_id ?? existing.role_id;
    this.ensureDepartmentAndRoleAreAssignable(nextDepartmentId, nextRoleId);
    this.ensureManagerRelationship(input.manager_employee_id, employeeId);

    if (input.role_id && input.role_id !== existing.role_id) {
      this.roleService.getActiveRoleById(input.role_id);
    }

    const updated = this.repository.update(employeeId, input);

    if (updated && input.role_id && input.role_id !== existing.role_id) {
      this.roleService.relinkEmployee(existing.role_id, updated.role_id, employeeId);
    }

    if (!updated) {
      throw new NotFoundError('employee not found');
    }

    if (updated.status === 'Active') {
      this.ensureActivationRequirements(updated.department_id, updated.role_id);
    }

    return updated;
  }

  assignDepartment(employeeId: string, departmentId: string): Employee {
    if (!departmentId || departmentId.trim() === '') {
      throw new ValidationError([{ field: 'department_id', reason: 'must be a non-empty string' }]);
    }

    if (!this.departmentRepository.findById(departmentId)) {
      throw new ValidationError([{ field: 'department_id', reason: 'department was not found' }]);
    }

    const updated = this.repository.updateDepartment(employeeId, departmentId);

    if (!updated) {
      throw new NotFoundError('employee not found');
    }

    return updated;
  }

  updateStatus(employeeId: string, status: EmployeeStatus): Employee {
    validateStatus(status);

    const employee = this.repository.findById(employeeId);

    if (!employee) {
      throw new NotFoundError('employee not found');
    }

    if (employee.status === status) {
      return employee;
    }

    if (!STATUS_TRANSITIONS[employee.status].includes(status)) {
      throw new ConflictError(`cannot transition status from ${employee.status} to ${status}`);
    }

    if (status === 'Active') {
      this.ensureActivationRequirements(employee.department_id, employee.role_id);
    }

    const updated = this.repository.updateStatus(employeeId, status);

    if (!updated) {
      throw new NotFoundError('employee not found');
    }

    return updated;
  }

  deleteEmployee(employeeId: string): void {
    const existing = this.repository.findById(employeeId);
    if (!existing) {
      throw new NotFoundError('employee not found');
    }

    if (!this.repository.delete(employeeId)) {
      throw new NotFoundError('employee not found');
    }

    this.roleService.unlinkEmployee(existing.role_id, employeeId);
  }

  private ensureUniqueEmployee(employeeNumber: string, email: string): void {
    if (this.repository.findByEmployeeNumber(employeeNumber)) {
      throw new ConflictError('employee_number already exists');
    }

    if (this.repository.findByEmail(email)) {
      throw new ConflictError('email already exists');
    }
  }

  private ensureDepartmentAndRoleAreAssignable(departmentId: string, roleId: string): void {
    const department = this.repository.findDepartmentById(departmentId);
    if (!department) {
      throw new ValidationError([{ field: 'department_id', reason: 'department was not found' }]);
    }
    if (department.status !== 'Active') {
      throw new ValidationError([{ field: 'department_id', reason: `department must be Active, got ${department.status}` }]);
    }

    const role = this.repository.findRoleById(roleId);
    if (!role) {
      throw new ValidationError([{ field: 'role_id', reason: 'role was not found' }]);
    }
    if (role.status !== 'Active') {
      throw new ValidationError([{ field: 'role_id', reason: `role must be Active, got ${role.status}` }]);
    }
  }

  private ensureManagerRelationship(managerEmployeeId?: string, employeeId?: string): void {
    if (managerEmployeeId === undefined) {
      return;
    }

    if (managerEmployeeId === '') {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'must be omitted or a non-empty string' }]);
    }

    if (employeeId && managerEmployeeId === employeeId) {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'employee cannot manage themselves' }]);
    }

    const manager = this.repository.findById(managerEmployeeId);
    if (!manager) {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'manager employee was not found' }]);
    }
    if (manager.status === 'Terminated') {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'manager employee cannot be Terminated' }]);
    }
  }

  private ensureActivationRequirements(departmentId: string, roleId: string): void {
    this.ensureDepartmentAndRoleAreAssignable(departmentId, roleId);
  }
}
