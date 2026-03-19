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
import { PerformanceReviewController } from './performance.controller';
import { PerformanceReviewRepository } from './performance.repository';
import { PerformanceReviewService } from './performance.service';
import { RoleController } from './role.controller';
import { RoleRepository } from './role.repository';
import { RoleService } from './role.service';
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

const createPerformanceReviewRateLimit = createRateLimitMiddleware({
  keyPrefix: 'performance-reviews:create',
  windowMs: 60_000,
  maxRequests: 30,
});

const readPerformanceReviewRateLimit = createRateLimitMiddleware({
  keyPrefix: 'performance-reviews:read',
  windowMs: 60_000,
  maxRequests: 180,
});

const listPerformanceReviewRateLimit = createRateLimitMiddleware({
  keyPrefix: 'performance-reviews:list',
  windowMs: 60_000,
  maxRequests: 120,
});

const updatePerformanceReviewRateLimit = createRateLimitMiddleware({
  keyPrefix: 'performance-reviews:update',
  windowMs: 60_000,
  maxRequests: 60,
});

const createRoleRateLimit = createRateLimitMiddleware({
  keyPrefix: 'roles:create',
  windowMs: 60_000,
  maxRequests: 20,
});

const readRoleRateLimit = createRateLimitMiddleware({
  keyPrefix: 'roles:read',
  windowMs: 60_000,
  maxRequests: 180,
});

const updateRoleRateLimit = createRateLimitMiddleware({
  keyPrefix: 'roles:update',
  windowMs: 60_000,
  maxRequests: 40,
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
  maxRequests: 20,
});

export function createEmployeeRouter(): Router {
  const departmentRepository = new DepartmentRepository();
  const roleRepository = new RoleRepository();
  const repository = new EmployeeRepository({
    findDepartmentById: (departmentId) => departmentRepository.findById(departmentId),
    findRoleById: (roleId) => roleRepository.findById(roleId),
  });
  const roleService = new RoleService(roleRepository);
  const departmentService = new DepartmentService(departmentRepository, repository);
  const service = new EmployeeService(repository, roleService, departmentRepository);
  const performanceReviewRepository = new PerformanceReviewRepository({
    findEmployeeById: (employeeId) => repository.findById(employeeId),
    findDepartmentById: (departmentId) => repository.findDepartmentById(departmentId),
  });
  const performanceReviewService = new PerformanceReviewService(performanceReviewRepository, repository);
  const controller = new EmployeeController(service);
  const performanceReviewController = new PerformanceReviewController(performanceReviewService);
  const departmentController = new DepartmentController(departmentService);
  const roleController = new RoleController(roleService);
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

  router.use('/api/v1', authenticate);

  router.post('/api/v1/employees', createEmployeeRateLimit, authorizeEmployeeAction('create'), controller.createEmployee);
  router.post('/api/v1/departments', createDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.createDepartment);
  router.post('/api/v1/roles', createRoleRateLimit, authorizeEmployeeAction('createRole'), roleController.createRole);
  router.post('/api/v1/performance-reviews', createPerformanceReviewRateLimit, authorizeEmployeeAction('createReview'), performanceReviewController.createReview);
  router.get('/api/v1/employees/:employeeId', readEmployeeRateLimit, authorizeEmployeeAction('read'), controller.getEmployee);
  router.get('/api/v1/employees', listEmployeeRateLimit, authorizeEmployeeAction('list'), controller.listEmployees);
  router.get('/api/v1/departments/:departmentId', readDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.getDepartment);
  router.get('/api/v1/departments', listDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.listDepartments);
  router.get('/api/v1/roles/:roleId', readRoleRateLimit, authorizeEmployeeAction('readRole'), roleController.getRole);
  router.get('/api/v1/roles', readRoleRateLimit, authorizeEmployeeAction('listRoles'), roleController.listRoles);
  router.get('/api/v1/performance-reviews/:performanceReviewId', readPerformanceReviewRateLimit, authorizeEmployeeAction('readReview'), performanceReviewController.getReview);
  router.get('/api/v1/performance-reviews', listPerformanceReviewRateLimit, authorizeEmployeeAction('listReviews'), performanceReviewController.listReviews);
  router.patch('/api/v1/employees/:employeeId', updateEmployeeRateLimit, authorizeEmployeeAction('updateProfile'), controller.updateEmployee);
  router.patch('/api/v1/departments/:departmentId', updateDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.updateDepartment);
  router.patch('/api/v1/roles/:roleId', updateRoleRateLimit, authorizeEmployeeAction('updateRole'), roleController.updateRole);
  router.patch('/api/v1/employees/:employeeId/department', updateEmployeeRateLimit, authorizeEmployeeAction('manageDepartment'), controller.assignDepartment);
  router.patch('/api/v1/performance-reviews/:performanceReviewId', updatePerformanceReviewRateLimit, authorizeEmployeeAction('updateReview'), performanceReviewController.updateReview);
  router.patch('/api/v1/employees/:employeeId/status', updateEmployeeRateLimit, authorizeEmployeeAction('manageStatus'), controller.updateStatus);
  router.post('/api/v1/performance-reviews/:performanceReviewId/submit', updatePerformanceReviewRateLimit, authorizeEmployeeAction('submitReview'), performanceReviewController.submitReview);
  router.post('/api/v1/performance-reviews/:performanceReviewId/finalize', updatePerformanceReviewRateLimit, authorizeEmployeeAction('finalizeReview'), performanceReviewController.finalizeReview);
  router.delete('/api/v1/employees/:employeeId', deleteEmployeeRateLimit, authorizeEmployeeAction('delete'), controller.deleteEmployee);
  router.delete('/api/v1/departments/:departmentId', deleteDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.deleteDepartment);
  router.delete('/api/v1/roles/:roleId', updateRoleRateLimit, authorizeEmployeeAction('deleteRole'), roleController.deleteRole);

  return router;
}
