import { Router } from 'express';
import { HealthController } from '../../health/health.controller';
import { createRateLimitMiddleware } from '../../middleware/rate-limit';
import { createLoggerMiddleware } from '../../middleware/logger';
import { requestIdMiddleware } from '../../middleware/request-id';
import { createThrottleMiddleware } from '../../middleware/throttle';
import { createPayloadLimitMiddleware } from '../../middleware/validation';
import { createMetricsMiddleware } from '../../metrics/metrics';
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

export function createEmployeeRouter(): Router {
  const repository = new EmployeeRepository();
  const service = new EmployeeService(repository);
  const controller = new EmployeeController(service);
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

  router.use('/api/v1/employees', authenticate);

  router.post('/api/v1/employees', createEmployeeRateLimit, authorizeEmployeeAction('create'), controller.createEmployee);
  router.get('/api/v1/employees/:employeeId', readEmployeeRateLimit, authorizeEmployeeAction('read'), controller.getEmployee);
  router.get('/api/v1/employees', listEmployeeRateLimit, authorizeEmployeeAction('list'), controller.listEmployees);
  router.patch('/api/v1/employees/:employeeId', updateEmployeeRateLimit, authorizeEmployeeAction('updateProfile'), controller.updateEmployee);
  router.patch('/api/v1/employees/:employeeId/department', updateEmployeeRateLimit, authorizeEmployeeAction('manageDepartment'), controller.assignDepartment);
  router.patch('/api/v1/employees/:employeeId/status', updateEmployeeRateLimit, authorizeEmployeeAction('manageStatus'), controller.updateStatus);
  router.delete('/api/v1/employees/:employeeId', deleteEmployeeRateLimit, authorizeEmployeeAction('delete'), controller.deleteEmployee);

  return router;
}
