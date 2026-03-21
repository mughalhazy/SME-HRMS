import { Router } from 'express';
import { HealthController } from '../../health/health.controller';
import { createRateLimitMiddleware } from '../../middleware/rate-limit';
import { createLoggerMiddleware } from '../../middleware/logger';
import { requestIdMiddleware } from '../../middleware/request-id';
import { createThrottleMiddleware } from '../../middleware/throttle';
import { createPayloadLimitMiddleware } from '../../middleware/validation';
import { createMetricsMiddleware } from '../../metrics/metrics';
import { tenantContextMiddleware } from '../../middleware/tenant-context';
import { CompensationController } from './compensation.controller';
import { CompensationRepository } from './compensation.repository';
import { CompensationService } from './compensation.service';
import { DepartmentController } from './department.controller';
import { DepartmentRepository } from './department.repository';
import { DepartmentService } from './department.service';
import { EmployeeController } from './employee.controller';
import { EmployeeRepository } from './employee.repository';
import { EmployeeService } from './employee.service';
import { OrgStructureController } from './org.controller';
import { OrgStructureRepository } from './org.repository';
import { OrgStructureService } from './org.service';
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

const createEmployeeRateLimit = createRateLimitMiddleware({ keyPrefix: 'employees:create', windowMs: 60_000, maxRequests: 30 });
const readEmployeeRateLimit = createRateLimitMiddleware({ keyPrefix: 'employees:read', windowMs: 60_000, maxRequests: 180 });
const listEmployeeRateLimit = createRateLimitMiddleware({ keyPrefix: 'employees:list', windowMs: 60_000, maxRequests: 120 });
const updateEmployeeRateLimit = createRateLimitMiddleware({ keyPrefix: 'employees:update', windowMs: 60_000, maxRequests: 60 });
const deleteEmployeeRateLimit = createRateLimitMiddleware({ keyPrefix: 'employees:delete', windowMs: 60_000, maxRequests: 20 });

const createPerformanceReviewRateLimit = createRateLimitMiddleware({ keyPrefix: 'performance-reviews:create', windowMs: 60_000, maxRequests: 30 });
const readPerformanceReviewRateLimit = createRateLimitMiddleware({ keyPrefix: 'performance-reviews:read', windowMs: 60_000, maxRequests: 180 });
const listPerformanceReviewRateLimit = createRateLimitMiddleware({ keyPrefix: 'performance-reviews:list', windowMs: 60_000, maxRequests: 120 });
const updatePerformanceReviewRateLimit = createRateLimitMiddleware({ keyPrefix: 'performance-reviews:update', windowMs: 60_000, maxRequests: 60 });

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

const createCompensationRateLimit = createRateLimitMiddleware({ keyPrefix: 'compensation:create', windowMs: 60_000, maxRequests: 30 });
const readCompensationRateLimit = createRateLimitMiddleware({ keyPrefix: 'compensation:read', windowMs: 60_000, maxRequests: 180 });
const listCompensationRateLimit = createRateLimitMiddleware({ keyPrefix: 'compensation:list', windowMs: 60_000, maxRequests: 120 });
const updateCompensationRateLimit = createRateLimitMiddleware({ keyPrefix: 'compensation:update', windowMs: 60_000, maxRequests: 60 });

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
  const compensationRepository = new CompensationRepository({
    findEmployeeById: (employeeId) => repository.findById(employeeId),
    findDepartmentById: (departmentId) => repository.findDepartmentById(departmentId),
    findGradeBandById: (gradeBandId) => repository.findGradeBandById(gradeBandId),
  });
  const service = new EmployeeService(repository, roleService, departmentRepository, performanceReviewRepository);
  const performanceReviewService = new PerformanceReviewService(performanceReviewRepository, repository);
  const compensationService = new CompensationService(compensationRepository, repository);
  const controller = new EmployeeController(service);
  const performanceReviewController = new PerformanceReviewController(performanceReviewService);
  const compensationController = new CompensationController(compensationService);
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
  router.post('/api/v1/org/:kind', createOrgRateLimit, authorizeEmployeeAction('manageOrgStructure'), orgController.createEntity);
  router.post('/api/v1/compensation/bands', createCompensationRateLimit, authorizeEmployeeAction('manageCompensation'), compensationController.createCompensationBand);
  router.post('/api/v1/compensation/salary-revisions', createCompensationRateLimit, authorizeEmployeeAction('manageCompensation'), compensationController.createSalaryRevision);
  router.post('/api/v1/benefits/plans', createCompensationRateLimit, authorizeEmployeeAction('manageCompensation'), compensationController.createBenefitsPlan);
  router.post('/api/v1/benefits/enrollments', createCompensationRateLimit, authorizeEmployeeAction('manageCompensation'), compensationController.createBenefitsEnrollment);
  router.post('/api/v1/compensation/allowances', createCompensationRateLimit, authorizeEmployeeAction('manageCompensation'), compensationController.createAllowance);

  router.get('/api/v1/employees/:employeeId', readEmployeeRateLimit, authorizeEmployeeAction('read'), controller.getEmployee);
  router.get('/api/v1/employees', listEmployeeRateLimit, authorizeEmployeeAction('list'), controller.listEmployees);
  router.get('/api/v1/departments/:departmentId', readDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.getDepartment);
  router.get('/api/v1/departments', listDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.listDepartments);
  router.get('/api/v1/roles/:roleId', readRoleRateLimit, authorizeEmployeeAction('readRole'), roleController.getRole);
  router.get('/api/v1/roles', readRoleRateLimit, authorizeEmployeeAction('listRoles'), roleController.listRoles);
  router.get('/api/v1/performance-reviews/:performanceReviewId', readPerformanceReviewRateLimit, authorizeEmployeeAction('readReview'), performanceReviewController.getReview);
  router.get('/api/v1/performance-reviews', listPerformanceReviewRateLimit, authorizeEmployeeAction('listReviews'), performanceReviewController.listReviews);
  router.get('/api/v1/org/:kind/:entityId', readOrgRateLimit, authorizeEmployeeAction('readOrgStructure'), orgController.getEntity);
  router.get('/api/v1/compensation/bands/:compensationBandId', readCompensationRateLimit, authorizeEmployeeAction('readCompensation'), compensationController.getCompensationBand);
  router.get('/api/v1/compensation/bands', listCompensationRateLimit, authorizeEmployeeAction('listCompensation'), compensationController.listCompensationBands);
  router.get('/api/v1/compensation/salary-revisions/:salaryRevisionId', readCompensationRateLimit, authorizeEmployeeAction('readCompensation'), compensationController.getSalaryRevision);
  router.get('/api/v1/compensation/salary-revisions', listCompensationRateLimit, authorizeEmployeeAction('listCompensation'), compensationController.listSalaryRevisions);
  router.get('/api/v1/benefits/plans/:benefitsPlanId', readCompensationRateLimit, authorizeEmployeeAction('readCompensation'), compensationController.getBenefitsPlan);
  router.get('/api/v1/benefits/plans', listCompensationRateLimit, authorizeEmployeeAction('listCompensation'), compensationController.listBenefitsPlans);
  router.get('/api/v1/benefits/enrollments/:benefitsEnrollmentId', readCompensationRateLimit, authorizeEmployeeAction('readCompensation'), compensationController.getBenefitsEnrollment);
  router.get('/api/v1/benefits/enrollments', listCompensationRateLimit, authorizeEmployeeAction('listCompensation'), compensationController.listBenefitsEnrollments);
  router.get('/api/v1/compensation/allowances/:allowanceId', readCompensationRateLimit, authorizeEmployeeAction('readCompensation'), compensationController.getAllowance);
  router.get('/api/v1/compensation/allowances', listCompensationRateLimit, authorizeEmployeeAction('listCompensation'), compensationController.listAllowances);
  router.get('/api/v1/compensation/employees/:employeeId/payroll-context', readCompensationRateLimit, authorizeEmployeeAction('readCompensation'), compensationController.getEmployeePayrollContext);
  router.get('/api/v1/org/:kind', readOrgRateLimit, authorizeEmployeeAction('listOrgStructure'), orgController.listEntities);

  router.patch('/api/v1/employees/:employeeId', updateEmployeeRateLimit, authorizeEmployeeAction('updateProfile'), controller.updateEmployee);
  router.patch('/api/v1/departments/:departmentId', updateDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.updateDepartment);
  router.patch('/api/v1/roles/:roleId', updateRoleRateLimit, authorizeEmployeeAction('updateRole'), roleController.updateRole);
  router.patch('/api/v1/employees/:employeeId/department', updateEmployeeRateLimit, authorizeEmployeeAction('manageDepartment'), controller.assignDepartment);
  router.patch('/api/v1/performance-reviews/:performanceReviewId', updatePerformanceReviewRateLimit, authorizeEmployeeAction('updateReview'), performanceReviewController.updateReview);
  router.patch('/api/v1/employees/:employeeId/status', updateEmployeeRateLimit, authorizeEmployeeAction('manageStatus'), controller.updateStatus);
  router.patch('/api/v1/org/:kind/:entityId', updateOrgRateLimit, authorizeEmployeeAction('manageOrgStructure'), orgController.updateEntity);
  router.patch('/api/v1/compensation/bands/:compensationBandId', updateCompensationRateLimit, authorizeEmployeeAction('manageCompensation'), compensationController.updateCompensationBand);
  router.patch('/api/v1/compensation/salary-revisions/:salaryRevisionId', updateCompensationRateLimit, authorizeEmployeeAction('manageCompensation'), compensationController.updateSalaryRevision);
  router.patch('/api/v1/benefits/plans/:benefitsPlanId', updateCompensationRateLimit, authorizeEmployeeAction('manageCompensation'), compensationController.updateBenefitsPlan);
  router.patch('/api/v1/benefits/enrollments/:benefitsEnrollmentId', updateCompensationRateLimit, authorizeEmployeeAction('manageCompensation'), compensationController.updateBenefitsEnrollment);
  router.patch('/api/v1/compensation/allowances/:allowanceId', updateCompensationRateLimit, authorizeEmployeeAction('manageCompensation'), compensationController.updateAllowance);

  router.post('/api/v1/performance-reviews/:performanceReviewId/submit', updatePerformanceReviewRateLimit, authorizeEmployeeAction('submitReview'), performanceReviewController.submitReview);
  router.post('/api/v1/performance-reviews/:performanceReviewId/finalize', updatePerformanceReviewRateLimit, authorizeEmployeeAction('finalizeReview'), performanceReviewController.finalizeReview);

  router.delete('/api/v1/employees/:employeeId', deleteEmployeeRateLimit, authorizeEmployeeAction('delete'), controller.deleteEmployee);
  router.delete('/api/v1/departments/:departmentId', deleteDepartmentRateLimit, authorizeEmployeeAction('manageDepartment'), departmentController.deleteDepartment);
  router.delete('/api/v1/roles/:roleId', updateRoleRateLimit, authorizeEmployeeAction('deleteRole'), roleController.deleteRole);

  return router;
}
