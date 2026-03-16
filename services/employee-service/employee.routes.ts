import { Router } from 'express';
import { EmployeeController } from './employee.controller';
import { EmployeeRepository } from './employee.repository';
import { EmployeeService } from './employee.service';

export function createEmployeeRouter(): Router {
  const repository = new EmployeeRepository();
  const service = new EmployeeService(repository);
  const controller = new EmployeeController(service);

  const router = Router();

  router.post('/api/v1/employees', controller.createEmployee);
  router.get('/api/v1/employees/:employeeId', controller.getEmployee);
  router.get('/api/v1/employees', controller.listEmployees);
  router.patch('/api/v1/employees/:employeeId', controller.updateEmployee);
  router.patch('/api/v1/employees/:employeeId/department', controller.assignDepartment);
  router.patch('/api/v1/employees/:employeeId/status', controller.updateStatus);
  router.delete('/api/v1/employees/:employeeId', controller.deleteEmployee);

  return router;
}
