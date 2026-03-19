import { Router } from 'express';
import { HealthController } from '../../health/health.controller';
import { createRateLimitMiddleware } from '../../middleware/rate-limit';
import { createLoggerMiddleware } from '../../middleware/logger';
import { requestIdMiddleware } from '../../middleware/request-id';
import { createThrottleMiddleware } from '../../middleware/throttle';
import { createPayloadLimitMiddleware } from '../../middleware/validation';
import { createMetricsMiddleware } from '../../metrics/metrics';
import { DepartmentController } from './department.controller';
import { DepartmentRepository } from './department.repository';
import { DepartmentService } from './department.service';
import { EmployeeController } from './employee.controller';
import { EmployeeRepository } from './employee.repository';
import { EmployeeService } from './employee.service';
import { authenticate, authorizeEmployeeAction } from './rbac.middleware';

const serviceThrottle = createThrottleMiddleware({
  maxConcurrent: 32,
  maxQueue: 64,
  queueTimeoutMs: 200,
  keyGenerator: () => 'employee-service',
});

const createEmployeeRateLimit = createRateLimitMiddleware({
  keyPrefix: 'employees:create',
  windowMs: 60_000,
  maxRequests: 30,
});

const readEmployeeRateLimit = createRateLimitMiddleware({
  keyPrefix: 'employees:read',
  windowMs: 60_000,
  maxRequests: 180,
});

const listEmployeeRateLimit = createRateLimitMiddleware({
  keyPrefix: 'employees:list',
  windowMs: 60_000,
  maxRequests: 120,
});

const updateEmployeeRateLimit = createRateLimitMiddleware({
  keyPrefix: 'employees:update',
  windowMs: 60_000,
  maxRequests: 60,
});

const deleteEmployeeRateLimit = createRateLimitMiddleware({
  keyPrefix: 'employees:delete',
  windowMs: 60_000,
  maxRequests: 20,
});

const createDepartmentRateLimit = createRateLimitMiddleware({
  keyPrefix: 'departments:create',
  windowMs: 60_000,
  maxRequests: 20,
});

const readDepartmentRateLimit = createRateLimitMiddleware({
  keyPrefix: 'departments:read',
  windowMs: 60_000,
  maxRequests: 180,
});

const listDepartmentRateLimit = createRateLimitMiddleware({
  keyPrefix: 'departments:list',
  windowMs: 60_000,
  maxRequests: 120,
});

const updateDepartmentRateLimit = createRateLimitMiddleware({
  keyPrefix: 'departments:update',
  windowMs: 60_000,
  maxRequests: 40,
});

const deleteDepartmentRateLimit = createRateLimitMiddleware({
  keyPrefix: 'departments:delete',
  windowMs: 60_000,
  maxRequests: 10,
});

export function createEmployeeRouter(): Router {
  const employeeRepository = new EmployeeRepository();
  const departmentRepository = new DepartmentRepository();
  const employeeService = new EmployeeService(employeeRepository, departmentRepository);
  const departmentService = new DepartmentService(departmentRepository, employeeRepository);
  const employeeController = new EmployeeController(employeeService);
  const departmentController = new DepartmentController(departmentService);
  const healthController = new HealthController('employee-service');

  const router = Router();

  router.use(requestIdMiddleware);
  router.use(serviceThrottle);
  router.use(createLoggerMiddleware('employee-service'));
  router.use(createMetricsMiddleware('employee-service'));
  router.use(createPayloadLimitMiddleware(16 * 1024));

  router.get('/health', healthController.getHealth);
  router.get('/ready', healthController.getReady);
  router.get('/metrics', healthController.getMetrics);

  router.use(['/api/v1/employees', '/api/v1/departments'], authenticate);

  router.post('/api/v1/employees', createEmployeeRateLimit, authorizeEmployeeAction('create'), employeeController.createEmployee);
  router.get('/api/v1/employees/:employeeId', readEmployeeRateLimit, authorizeEmployeeAction('read'), employeeController.getEmployee);
  router.get('/api/v1/employees', listEmployeeRateLimit, authorizeEmployeeAction('list'), employeeController.listEmployees);
  router.patch('/api/v1/employees/:employeeId', updateEmployeeRateLimit, authorizeEmployeeAction('updateProfile'), employeeController.updateEmployee);
  router.patch('/api/v1/employees/:employeeId/department', updateEmployeeRateLimit, authorizeEmployeeAction('manageDepartment'), employeeController.assignDepartment);
  router.patch('/api/v1/employees/:employeeId/status', updateEmployeeRateLimit, authorizeEmployeeAction('manageStatus'), employeeController.updateStatus);
  router.delete('/api/v1/employees/:employeeId', deleteEmployeeRateLimit, authorizeEmployeeAction('delete'), employeeController.deleteEmployee);

  router.post('/api/v1/departments', createDepartmentRateLimit, authorizeEmployeeAction('createDepartment'), departmentController.createDepartment);
  router.get('/api/v1/departments/:departmentId', readDepartmentRateLimit, authorizeEmployeeAction('readDepartment'), departmentController.getDepartment);
  router.get('/api/v1/departments', listDepartmentRateLimit, authorizeEmployeeAction('listDepartments'), departmentController.listDepartments);
  router.patch('/api/v1/departments/:departmentId', updateDepartmentRateLimit, authorizeEmployeeAction('updateDepartmentRecord'), departmentController.updateDepartment);
  router.delete('/api/v1/departments/:departmentId', deleteDepartmentRateLimit, authorizeEmployeeAction('deleteDepartmentRecord'), departmentController.deleteDepartment);

  return router;
}
