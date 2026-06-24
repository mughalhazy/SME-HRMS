import { PaginatedResult } from '../../db/optimization';
import { ConflictError, NotFoundError } from './service.errors';
import { ValidationError } from './employee.validation';
import { CreateDepartmentInput, Department, DepartmentFilters, UpdateDepartmentInput } from './department.model';
import { DepartmentRepository } from './department.repository';
import { validateCreateDepartment, validateUpdateDepartment } from './department.validation';
import { EmployeeRepository } from './employee.repository';

export class DepartmentService {
  constructor(
    private readonly repository: DepartmentRepository,
    private readonly employeeRepository: EmployeeRepository,
  ) {}

  createDepartment(input: CreateDepartmentInput): Department {
    validateCreateDepartment(input);

    if (this.repository.findByName(input.name)) {
      throw new ConflictError('department name already exists');
    }

    if (this.repository.findByCode(input.code)) {
      throw new ConflictError('department code already exists');
    }

    if (input.parent_department_id && !this.repository.findById(input.parent_department_id)) {
      throw new ValidationError([{ field: 'parent_department_id', reason: 'parent department was not found' }]);
    }

    if (input.head_employee_id && !this.employeeRepository.findById(input.head_employee_id)) {
      throw new ValidationError([{ field: 'head_employee_id', reason: 'head employee was not found' }]);
    }

    if (input.head_employee_id) {
      const headEmployee = this.employeeRepository.findById(input.head_employee_id);
      if (headEmployee?.status === 'Terminated') {
        throw new ValidationError([{ field: 'head_employee_id', reason: 'head employee cannot be Terminated' }]);
      }

      const currentHeadDepartment = this.repository.findByHeadEmployeeId(input.head_employee_id);
      if (currentHeadDepartment) {
        throw new ConflictError('head employee is already assigned to another department');
      }
    }

    const department = this.repository.create(input);

    if (department.head_employee_id) {
      this.employeeRepository.updateDepartment(department.head_employee_id, department.department_id);
    }

    return this.repository.findById(department.department_id) ?? department;
  }

  getDepartmentById(departmentId: string): Department {
    const department = this.repository.findById(departmentId);
    if (!department) {
      throw new NotFoundError('department not found');
    }
    return department;
  }

  listDepartments(filters: DepartmentFilters): PaginatedResult<Department> {
    return this.repository.list(filters);
  }

  updateDepartment(departmentId: string, input: UpdateDepartmentInput): Department {
    validateUpdateDepartment(input);

    const existing = this.repository.findById(departmentId);
    if (!existing) {
      throw new NotFoundError('department not found');
    }

    if (input.name && input.name !== existing.name) {
      const sameName = this.repository.findByName(input.name);
      if (sameName && sameName.department_id !== departmentId) {
        throw new ConflictError('department name already exists');
      }
    }

    if (input.code && input.code !== existing.code) {
      const sameCode = this.repository.findByCode(input.code);
      if (sameCode && sameCode.department_id !== departmentId) {
        throw new ConflictError('department code already exists');
      }
    }

    const nextParentDepartmentId = input.parent_department_id ?? existing.parent_department_id;
    if (nextParentDepartmentId) {
      this.assertValidParentDepartment(departmentId, nextParentDepartmentId);
    }

    const nextHeadEmployeeId = input.head_employee_id ?? existing.head_employee_id;
    if (nextHeadEmployeeId) {
      const headEmployee = this.employeeRepository.findById(nextHeadEmployeeId);
      if (!headEmployee) {
        throw new ValidationError([{ field: 'head_employee_id', reason: 'head employee was not found' }]);
      }
      if (headEmployee.status === 'Terminated') {
        throw new ValidationError([{ field: 'head_employee_id', reason: 'head employee cannot be Terminated' }]);
      }

      const currentHeadDepartment = this.repository.findByHeadEmployeeId(nextHeadEmployeeId);
      if (currentHeadDepartment && currentHeadDepartment.department_id !== departmentId) {
        throw new ConflictError('head employee is already assigned to another department');
      }

      if (headEmployee.department_id !== departmentId) {
        this.employeeRepository.updateDepartment(nextHeadEmployeeId, departmentId);
      }
    }

    const nextStatus = input.status ?? existing.status;
    if (nextStatus !== 'Active' && this.employeeRepository.countByDepartmentId(departmentId) > 0) {
      throw new ConflictError('cannot deactivate or archive a department with assigned employees');
    }

    const updated = this.repository.update(departmentId, input);
    if (!updated) {
      throw new NotFoundError('department not found');
    }

    return updated;
  }

  deleteDepartment(departmentId: string): void {
    const existing = this.repository.findById(departmentId);
    if (!existing) {
      throw new NotFoundError('department not found');
    }

    if (this.employeeRepository.countByDepartmentId(departmentId) > 0) {
      throw new ConflictError('department still has assigned employees');
    }

    if (this.repository.hasChildren(departmentId)) {
      throw new ConflictError('department still has child departments');
    }

    if (!this.repository.delete(departmentId)) {
      throw new NotFoundError('department not found');
    }
  }

  private assertValidParentDepartment(departmentId: string, parentDepartmentId: string): void {
    if (departmentId === parentDepartmentId) {
      throw new ValidationError([{ field: 'parent_department_id', reason: 'department cannot be its own parent' }]);
    }

    let cursor = this.repository.findById(parentDepartmentId);
    if (!cursor) {
      throw new ValidationError([{ field: 'parent_department_id', reason: 'parent department was not found' }]);
    }

    while (cursor?.parent_department_id) {
      if (cursor.parent_department_id === departmentId) {
        throw new ValidationError([{ field: 'parent_department_id', reason: 'department hierarchy cannot contain cycles' }]);
      }
      cursor = this.repository.findById(cursor.parent_department_id);
    }
  }
}
