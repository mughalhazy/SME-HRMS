import { ConflictError, NotFoundError } from './service.errors';
import { ValidationError } from './employee.validation';
import { CreateRoleInput, Role, RoleFilters, UpdateRoleInput } from './role.model';
import { RoleRepository } from './role.repository';
import { validateCreateRole, validateUpdateRole } from './role.validation';

export class RoleService {
  constructor(private readonly repository: RoleRepository) {}

  createRole(input: CreateRoleInput): Role {
    validateCreateRole(input);

    if (this.repository.findByTitle(input.title)) {
      throw new ConflictError('role title already exists');
    }

    return this.repository.create(input);
  }

  getRoleById(roleId: string): Role {
    const role = this.repository.findById(roleId);
    if (!role) {
      throw new NotFoundError('role not found');
    }
    return role;
  }

  getActiveRoleById(roleId: string): Role {
    const role = this.getRoleById(roleId);
    if (role.status !== 'Active') {
      throw new ValidationError([{ field: 'role_id', reason: 'role must be active for employee assignment' }]);
    }
    return role;
  }

  listRoles(filters: RoleFilters = {}): Array<Role & { employee_count: number }> {
    return this.repository.list(filters).map((role) => ({
      ...role,
      employee_count: this.repository.countEmployees(role.role_id),
    }));
  }

  updateRole(roleId: string, input: UpdateRoleInput): Role {
    validateUpdateRole(input);

    const existing = this.repository.findById(roleId);
    if (!existing) {
      throw new NotFoundError('role not found');
    }

    if (input.title && input.title.trim().toLowerCase() !== existing.title.trim().toLowerCase()) {
      const duplicate = this.repository.findByTitle(input.title);
      if (duplicate && duplicate.role_id !== roleId) {
        throw new ConflictError('role title already exists');
      }
    }

    if (input.status && input.status !== 'Active' && this.repository.countEmployees(roleId) > 0) {
      throw new ConflictError('cannot deactivate or archive a role with assigned employees');
    }

    const updated = this.repository.update(roleId, input);
    if (!updated) {
      throw new NotFoundError('role not found');
    }
    return updated;
  }

  deleteRole(roleId: string): void {
    if (this.repository.countEmployees(roleId) > 0) {
      throw new ConflictError('cannot delete role with assigned employees');
    }

    if (!this.repository.delete(roleId)) {
      throw new NotFoundError('role not found');
    }
  }

  linkEmployee(roleId: string, employeeId: string): void {
    this.repository.assignEmployee(roleId, employeeId);
  }

  relinkEmployee(previousRoleId: string, nextRoleId: string, employeeId: string): void {
    if (previousRoleId !== nextRoleId) {
      this.repository.unassignEmployee(previousRoleId, employeeId);
      this.repository.assignEmployee(nextRoleId, employeeId);
    }
  }

  unlinkEmployee(roleId: string, employeeId: string): void {
    this.repository.unassignEmployee(roleId, employeeId);
  }

  getRoleIntegrity(roleId: string): {
    role: Role;
    employee_ids: string[];
    employee_count: number;
  } {
    const role = this.getRoleById(roleId);
    const employee_ids = this.repository.listEmployeeIds(roleId);
    return {
      role,
      employee_ids,
      employee_count: employee_ids.length,
    };
  }
}
