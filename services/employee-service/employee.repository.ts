import { randomUUID } from 'node:crypto';
import { CreateEmployeeInput, Employee, EmployeeFilters, EmployeeStatus, UpdateEmployeeInput } from './employee.model';

export class EmployeeRepository {
  private readonly employees = new Map<string, Employee>();

  create(input: CreateEmployeeInput): Employee {
    const timestamp = new Date().toISOString();
    const record: Employee = {
      employee_id: randomUUID(),
      employee_number: input.employee_number,
      first_name: input.first_name,
      last_name: input.last_name,
      email: input.email,
      phone: input.phone,
      hire_date: input.hire_date,
      employment_type: input.employment_type,
      status: input.status ?? 'Draft',
      department_id: input.department_id,
      role_id: input.role_id,
      manager_employee_id: input.manager_employee_id,
      created_at: timestamp,
      updated_at: timestamp,
    };

    this.employees.set(record.employee_id, record);
    return record;
  }

  findById(employeeId: string): Employee | null {
    return this.employees.get(employeeId) ?? null;
  }

  findByEmployeeNumber(employeeNumber: string): Employee | null {
    for (const employee of this.employees.values()) {
      if (employee.employee_number === employeeNumber) {
        return employee;
      }
    }

    return null;
  }

  findByEmail(email: string): Employee | null {
    for (const employee of this.employees.values()) {
      if (employee.email === email) {
        return employee;
      }
    }

    return null;
  }

  list(filters: EmployeeFilters): Employee[] {
    return [...this.employees.values()].filter((employee) => {
      if (filters.department_id && employee.department_id !== filters.department_id) {
        return false;
      }

      if (filters.status && employee.status !== filters.status) {
        return false;
      }

      return true;
    });
  }

  update(employeeId: string, input: UpdateEmployeeInput): Employee | null {
    const employee = this.employees.get(employeeId);

    if (!employee) {
      return null;
    }

    const updated: Employee = {
      ...employee,
      ...input,
      updated_at: new Date().toISOString(),
    };

    this.employees.set(employeeId, updated);
    return updated;
  }

  updateDepartment(employeeId: string, departmentId: string): Employee | null {
    const employee = this.employees.get(employeeId);

    if (!employee) {
      return null;
    }

    const updated: Employee = {
      ...employee,
      department_id: departmentId,
      updated_at: new Date().toISOString(),
    };

    this.employees.set(employeeId, updated);
    return updated;
  }

  updateStatus(employeeId: string, status: EmployeeStatus): Employee | null {
    const employee = this.employees.get(employeeId);

    if (!employee) {
      return null;
    }

    const updated: Employee = {
      ...employee,
      status,
      updated_at: new Date().toISOString(),
    };

    this.employees.set(employeeId, updated);
    return updated;
  }

  delete(employeeId: string): boolean {
    return this.employees.delete(employeeId);
  }
}
