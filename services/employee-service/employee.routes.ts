import { Router } from 'express';
import { HealthController } from '../../health/health.controller';
import { createRateLimitMiddleware } from '../../middleware/rate-limit';
import { createLoggerMiddleware } from '../../middleware/logger';
import { requestIdMiddleware } from '../../middleware/request-id';
import { createThrottleMiddleware } from '../../middleware/throttle';
import { createPayloadLimitMiddleware } from '../../middleware/validation';
import { createMetricsMiddleware } from '../../metrics/metrics';
import { tenantContextMiddleware } from '../../middleware/tenant-context';
import { DepartmentController } from './department.controller';
import { DepartmentRepository } from './department.repository';
import { DepartmentService } from './department.service';
import { EmployeeController } from './employee.controller';
import { DocumentComplianceController } from './document-compliance.controller';
import { DocumentComplianceRepository } from './document-compliance.repository';
import { DocumentComplianceService } from './document-compliance.service';
import { EmployeeRepository } from './employee.repository';
import { EmployeeService } from './employee.service';
import { OrgStructureController } from './org.controller';
import { OrgStructureRepository } from './org.repository';
import { OrgStructureService } from './org.service';
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

const createEmployeeRateLimit = createRateLimitMiddleware({ keyPrefix: 'employees:create', windowMs: 60_000, maxRequests: 30 });
const readEmployeeRateLimit = createRateLimitMiddleware({ keyPrefix: 'employees:read', windowMs: 60_000, maxRequests: 180 });
const listEmployeeRateLimit = createRateLimitMiddleware({ keyPrefix: 'employees:list', windowMs: 60_000, maxRequests: 120 });
const updateEmployeeRateLimit = createRateLimitMiddleware({ keyPrefix: 'employees:update', windowMs: 60_000, maxRequests: 60 });
const deleteEmployeeRateLimit = createRateLimitMiddleware({ keyPrefix: 'employees:delete', windowMs: 60_000, maxRequests: 20 });


const createRoleRateLimit = createRateLimitMiddleware({ keyPrefix: 'roles:create', windowMs: 60_000, maxRequests: 20 });
const readRoleRateLimit = createRateLimitMiddleware({ keyPrefix: 'roles:read', windowMs: 60_000, maxRequests: 180 });
const updateRoleRateLimit = createRateLimitMiddleware({ keyPrefix: 'roles:update', windowMs: 60_000, maxRequests: 40 });

const createDepartmentRateLimit = createRateLimitMiddleware({ keyPrefix: 'departments:create', windowMs: 60_000, maxRequests: 20 });
const readDepartmentRateLimit = createRateLimitMiddleware({ keyPrefix: 'departments:read', windowMs: 60_000, maxRequests: 180 });
const listDepartmentRateLimit = createRateLimitMiddleware({ keyPrefix: 'departments:list', windowMs: 60_000, maxRequests: 120 });
const updateDepartmentRateLimit = createRateLimitMiddleware({ keyPrefix: 'departments:update', windowMs: 60_000, maxRequests: 40 });
const deleteDepartmentRateLimit = createRateLimitMiddleware({ keyPrefix: 'departments:delete', windowMs: 60_000, maxRequests: 20 });

const createOrgRateLimit = createRateLimitMiddleware({ keyPrefix: 'org:create', windowMs: 60_000, maxRequests: 30 });
const readOrgRateLimit = createRateLimitMiddleware({ keyPrefix: 'org:read', windowMs: 60_000, maxRequests: 180 });
const updateOrgRateLimit = createRateLimitMiddleware({ keyPrefix: 'org:update', windowMs: 60_000, maxRequests: 60 });

export function createEmployeeRouter(): Router {
  const departmentRepository = new DepartmentRepository();
  const roleRepository = new RoleRepository();
  const orgRepository = new OrgStructureRepository();
  const repository = new EmployeeRepository({
    findDepartmentById: (departmentId) => departmentRepository.findById(departmentId),
    findRoleById: (roleId) => roleRepository.findById(roleId),
    findBusinessUnitById: (businessUnitId) => orgRepository.findById('business_unit', businessUnitId) as any,
    findLegalEntityById: (legalEntityId) => orgRepository.findById('legal_entity', legalEntityId) as any,
    findLocationById: (locationId) => orgRepository.findById('location', locationId) as any,
    findCostCenterById: (costCenterId) => orgRepository.findById('cost_center', costCenterId) as any,
    findGradeBandById: (gradeBandId) => orgRepository.findById('grade_band', gradeBandId) as any,
    findJobPositionById: (jobPositionId) => orgRepository.findById('job_position', jobPositionId) as any,
  });
  const roleService = new RoleService(roleRepository);
  const departmentService = new DepartmentService(departmentRepository, repository);
  const orgStructureService = new OrgStructureService(orgRepository, repository, departmentRepository, roleRepository);
  const performanceReviewRepository = new PerformanceReviewRepository({
    findEmployeeById: (employeeId) => repository.findById(employeeId),
    findDepartmentById: (departmentId) => repository.findDepartmentById(departmentId),
  });
  const service = new EmployeeService(repository, roleService, departmentRepository, performanceReviewRepository);
  const documentComplianceRepository = new DocumentComplianceRepository();
  const documentComplianceService = new DocumentComplianceService(documentComplianceRepository, repository);
  const performanceReviewService = new PerformanceReviewService(performanceReviewRepository, repository);
  const controller = new EmployeeController(service);
  const documentComplianceController = new DocumentComplianceController(documentComplianceService, service);
  const performanceReviewController = new PerformanceReviewController(performanceReviewService);
  const departmentController = new DepartmentController(departmentService);
  const orgController = new OrgStructureController(orgStructureService);
  const roleController = new RoleController(roleService);
  const healthController = new HealthController('employee-service');

  const router = Router();

  router.use(requestIdMiddleware);
  router.use(serviceThrottle);
  router.use(createLoggerMiddleware('employee-service'));
  router.use(createMetricsMiddleware('employee-service'));
  router.use(createPayloadLimitMiddleware(16 * 1024));
  router.use(tenantContextMiddleware);

  router.get('/health', healthController.getHealth);
  router.get('/ready', healthController.getReady);
  router.get('/metrics', healthController.getMetrics);

  router.use('/api/v1', authenticate);

  router.post('/api/v1/employees', createEmployeeRateLimit, authorizeEmployeeAction('create'), controller.createEmployee);
  router.post('/api/v1/departments', createDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.createDepartment);
  router.post('/api/v1/roles', createRoleRateLimit, authorizeEmployeeAction('createRole'), roleController.createRole);
  router.post('/api/v1/performance-reviews', createPerformanceReviewRateLimit, authorizeEmployeeAction('createReview'), performanceReviewController.createReview);
  router.post('/api/v1/documents', createEmployeeRateLimit, authorizeEmployeeAction('createDocument'), documentComplianceController.createDocument);
  router.post('/api/v1/documents/:documentId/acknowledgements', updateEmployeeRateLimit, authorizeEmployeeAction('acknowledgePolicy'), documentComplianceController.acknowledgePolicy);
  router.post('/api/v1/compliance-tasks', createEmployeeRateLimit, authorizeEmployeeAction('createComplianceTask'), documentComplianceController.createComplianceTask);
  router.post('/api/v1/org/:kind', createOrgRateLimit, authorizeEmployeeAction('manageOrgStructure'), orgController.createEntity);

  router.get('/api/v1/employees/:employeeId', readEmployeeRateLimit, authorizeEmployeeAction('read'), controller.getEmployee);
  router.get('/api/v1/employees', listEmployeeRateLimit, authorizeEmployeeAction('list'), controller.listEmployees);
  router.get('/api/v1/documents/expiring', readEmployeeRateLimit, authorizeEmployeeAction('listDocuments'), documentComplianceController.listExpiringDocuments);
  router.get('/api/v1/documents/:documentId', readEmployeeRateLimit, authorizeEmployeeAction('readDocument'), documentComplianceController.getDocument);
  router.get('/api/v1/documents', listEmployeeRateLimit, authorizeEmployeeAction('listDocuments'), documentComplianceController.listDocuments);
  router.get('/api/v1/compliance-tasks/:taskId', readEmployeeRateLimit, authorizeEmployeeAction('readComplianceTask'), documentComplianceController.getComplianceTask);
  router.get('/api/v1/compliance-tasks', listEmployeeRateLimit, authorizeEmployeeAction('listComplianceTasks'), documentComplianceController.listComplianceTasks);
  router.get('/api/v1/departments/:departmentId', readDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.getDepartment);
  router.get('/api/v1/departments', listDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.listDepartments);
  router.get('/api/v1/roles/:roleId', readRoleRateLimit, authorizeEmployeeAction('readRole'), roleController.getRole);
  router.get('/api/v1/roles', readRoleRateLimit, authorizeEmployeeAction('listRoles'), roleController.listRoles);
  router.get('/api/v1/org/:kind/:entityId', readOrgRateLimit, authorizeEmployeeAction('readOrgStructure'), orgController.getEntity);
  router.get('/api/v1/org/:kind', readOrgRateLimit, authorizeEmployeeAction('listOrgStructure'), orgController.listEntities);

  router.patch('/api/v1/employees/:employeeId', updateEmployeeRateLimit, authorizeEmployeeAction('updateProfile'), controller.updateEmployee);
  router.patch('/api/v1/documents/:documentId', updateEmployeeRateLimit, authorizeEmployeeAction('updateDocument'), documentComplianceController.updateDocument);
  router.patch('/api/v1/compliance-tasks/:taskId', updateEmployeeRateLimit, authorizeEmployeeAction('updateComplianceTask'), documentComplianceController.updateComplianceTask);
  router.patch('/api/v1/departments/:departmentId', updateDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.updateDepartment);
  router.patch('/api/v1/roles/:roleId', updateRoleRateLimit, authorizeEmployeeAction('updateRole'), roleController.updateRole);
  router.patch('/api/v1/employees/:employeeId/department', updateEmployeeRateLimit, authorizeEmployeeAction('manageDepartment'), controller.assignDepartment);
  router.patch('/api/v1/employees/:employeeId/status', updateEmployeeRateLimit, authorizeEmployeeAction('manageStatus'), controller.updateStatus);
  router.patch('/api/v1/org/:kind/:entityId', updateOrgRateLimit, authorizeEmployeeAction('manageOrgStructure'), orgController.updateEntity);


  router.delete('/api/v1/employees/:employeeId', deleteEmployeeRateLimit, authorizeEmployeeAction('delete'), controller.deleteEmployee);
  router.delete('/api/v1/departments/:departmentId', deleteDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.deleteDepartment);
  router.delete('/api/v1/roles/:roleId', updateRoleRateLimit, authorizeEmployeeAction('deleteRole'), roleController.deleteRole);

  return router;
}
