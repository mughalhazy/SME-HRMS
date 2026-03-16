import { Router } from 'express';
import { EmployeeController } from './employee.controller';
import { EmployeeRepository } from './employee.repository';
import { EmployeeService } from './employee.service';
import { authenticate, authorizeEmployeeAction } from './rbac.middleware';

export function createEmployeeRouter(): Router {
  const repository = new EmployeeRepository();
  const service = new EmployeeService(repository);
  const controller = new EmployeeController(service);

  const router = Router();

  router.use('/api/v1/employees', authenticate);

  router.post('/api/v1/employees', authorizeEmployeeAction('create'), controller.createEmployee);
  router.get('/api/v1/employees/:employeeId', authorizeEmployeeAction('read'), controller.getEmployee);
  router.get('/api/v1/employees', authorizeEmployeeAction('list'), controller.listEmployees);
  router.patch('/api/v1/employees/:employeeId', authorizeEmployeeAction('updateProfile'), controller.updateEmployee);
  router.patch('/api/v1/employees/:employeeId/department', authorizeEmployeeAction('manageDepartment'), controller.assignDepartment);
  router.patch('/api/v1/employees/:employeeId/status', authorizeEmployeeAction('manageStatus'), controller.updateStatus);
  router.delete('/api/v1/employees/:employeeId', authorizeEmployeeAction('delete'), controller.deleteEmployee);

  return router;
}
