import {
  CreateEmployeeInput,
  Employee,
  EmployeeFilters,
  EmployeeStatus,
  UpdateEmployeeInput,
} from './employee.model';
import { DepartmentRepository } from './department.repository';
import { EmployeeRepository } from './employee.repository';
import { validateCreateEmployee, validateStatus, validateUpdateEmployee, ValidationError } from './employee.validation';

export class NotFoundError extends Error {}
export class ConflictError extends Error {}

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
    private readonly departmentRepository: DepartmentRepository,
  ) {}

  createEmployee(input: CreateEmployeeInput): Employee {
    validateCreateEmployee(input);

    if (this.repository.findByEmployeeNumber(input.employee_number)) {
      throw new ConflictError('employee_number already exists');
    }

    if (this.repository.findByEmail(input.email)) {
      throw new ConflictError('email already exists');
    }

    if (input.manager_employee_id && !this.repository.findById(input.manager_employee_id)) {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'manager employee was not found' }]);
    }

    if (!this.departmentRepository.findById(input.department_id)) {
      throw new ValidationError([{ field: 'department_id', reason: 'department was not found' }]);
    }

    return this.repository.create(input);
  }

  getEmployeeById(employeeId: string): Employee {
    const employee = this.repository.findById(employeeId);

    if (!employee) {
      throw new NotFoundError('employee not found');
    }

    return employee;
  }

  listEmployees(filters: EmployeeFilters) {
    return this.repository.list(filters);
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

    if (input.manager_employee_id && input.manager_employee_id === employeeId) {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'employee cannot manage themselves' }]);
    }

    if (input.manager_employee_id && !this.repository.findById(input.manager_employee_id)) {
      throw new ValidationError([{ field: 'manager_employee_id', reason: 'manager employee was not found' }]);
    }

    if (input.department_id && !this.departmentRepository.findById(input.department_id)) {
      throw new ValidationError([{ field: 'department_id', reason: 'department was not found' }]);
    }

    const updated = this.repository.update(employeeId, input);

    if (!updated) {
      throw new NotFoundError('employee not found');
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

    if (!STATUS_TRANSITIONS[employee.status].includes(status)) {
      throw new ConflictError(`cannot transition status from ${employee.status} to ${status}`);
    }

    const updated = this.repository.updateStatus(employeeId, status);

    if (!updated) {
      throw new NotFoundError('employee not found');
    }

    return updated;
  }

  deleteEmployee(employeeId: string): void {
    if (this.repository.hasDirectReports(employeeId)) {
      throw new ConflictError('employee still has direct reports');
    }

    const headedDepartment = this.departmentRepository.findByHeadEmployeeId(employeeId);
    if (headedDepartment) {
      throw new ConflictError('employee is still assigned as a department head');
    }

    if (!this.repository.delete(employeeId)) {
      throw new NotFoundError('employee not found');
    }
  }
}
