import { Request, Response } from 'express';
import { CompensationService } from './compensation.service';
import { AuthContext } from './rbac.middleware';
import { ConflictError, NotFoundError } from './service.errors';
import { ValidationError } from './employee.validation';
import { ApiError, sendApiError } from '../../middleware/error-handler';
import { logAuditMutation } from '../../middleware/audit';
import { getStructuredLogger } from '../../middleware/logger';

function sendError(
  req: Request,
  res: Response,
  status: number,
  code: string,
  message: string,
  details?: Array<{ field: string; reason: string }>,
): void {
  sendApiError(req, res, new ApiError(status, code, message, details ?? []));
}

function getAuth(req: Request): AuthContext {
  if (!req.auth) {
    throw new Error('UNAUTHORIZED');
  }
  return req.auth;
}

export class CompensationController {
  private readonly logger = getStructuredLogger('employee-service');

  constructor(private readonly compensationService: CompensationService) {}

  createCompensationBand = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const band = this.compensationService.createCompensationBand(req.body);
      this.audit(req, 'compensation_band_created', 'CompensationBand', band.compensation_band_id, {}, band, band.tenant_id);
      res.status(201).json({ data: band });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getCompensationBand = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      res.status(200).json({ data: this.compensationService.getCompensationBandById(req.params.compensationBandId) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listCompensationBands = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const page = this.compensationService.listCompensationBands({
        grade_band_id: typeof req.query.grade_band_id === 'string' ? req.query.grade_band_id : undefined,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
        limit: typeof req.query.limit === 'string' ? Number(req.query.limit) : undefined,
        cursor: typeof req.query.cursor === 'string' ? req.query.cursor : undefined,
      });
      res.status(200).json({ data: page.data, page: page.page });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateCompensationBand = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const before = this.compensationService.getCompensationBandById(req.params.compensationBandId);
      const band = this.compensationService.updateCompensationBand(req.params.compensationBandId, req.body);
      this.audit(req, 'compensation_band_updated', 'CompensationBand', band.compensation_band_id, before, band, band.tenant_id);
      res.status(200).json({ data: band });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  createSalaryRevision = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const revision = this.compensationService.createSalaryRevision(req.body);
      this.audit(req, 'salary_revision_created', 'SalaryRevision', revision.salary_revision_id, {}, revision, revision.tenant_id);
      res.status(201).json({ data: revision, read_models: { employee_compensation_view: this.compensationService.getEmployeeCompensationReadModel(revision.employee_id, revision.effective_from) } });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getSalaryRevision = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      res.status(200).json({ data: this.compensationService.getSalaryRevisionById(req.params.salaryRevisionId) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listSalaryRevisions = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const page = this.compensationService.listSalaryRevisions({
        employee_id: typeof req.query.employee_id === 'string' ? req.query.employee_id : undefined,
        compensation_band_id: typeof req.query.compensation_band_id === 'string' ? req.query.compensation_band_id : undefined,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
        limit: typeof req.query.limit === 'string' ? Number(req.query.limit) : undefined,
        cursor: typeof req.query.cursor === 'string' ? req.query.cursor : undefined,
      });
      res.status(200).json({ data: page.data, page: page.page });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateSalaryRevision = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const before = this.compensationService.getSalaryRevisionById(req.params.salaryRevisionId);
      const revision = this.compensationService.updateSalaryRevision(req.params.salaryRevisionId, req.body);
      this.audit(req, 'salary_revision_updated', 'SalaryRevision', revision.salary_revision_id, before, revision, revision.tenant_id);
      res.status(200).json({ data: revision, read_models: { employee_compensation_view: this.compensationService.getEmployeeCompensationReadModel(revision.employee_id, revision.effective_from) } });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  createBenefitsPlan = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const plan = this.compensationService.createBenefitsPlan(req.body);
      this.audit(req, 'benefits_plan_created', 'BenefitsPlan', plan.benefits_plan_id, {}, plan, plan.tenant_id);
      res.status(201).json({ data: plan });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getBenefitsPlan = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      res.status(200).json({ data: this.compensationService.getBenefitsPlanById(req.params.benefitsPlanId) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listBenefitsPlans = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const page = this.compensationService.listBenefitsPlans({
        plan_type: typeof req.query.plan_type === 'string' ? req.query.plan_type as never : undefined,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
        limit: typeof req.query.limit === 'string' ? Number(req.query.limit) : undefined,
        cursor: typeof req.query.cursor === 'string' ? req.query.cursor : undefined,
      });
      res.status(200).json({ data: page.data, page: page.page });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateBenefitsPlan = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const before = this.compensationService.getBenefitsPlanById(req.params.benefitsPlanId);
      const plan = this.compensationService.updateBenefitsPlan(req.params.benefitsPlanId, req.body);
      this.audit(req, 'benefits_plan_updated', 'BenefitsPlan', plan.benefits_plan_id, before, plan, plan.tenant_id);
      res.status(200).json({ data: plan });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  createBenefitsEnrollment = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const enrollment = this.compensationService.createBenefitsEnrollment(req.body);
      this.audit(req, 'benefits_enrollment_created', 'BenefitsEnrollment', enrollment.benefits_enrollment_id, {}, enrollment, enrollment.tenant_id);
      res.status(201).json({ data: enrollment, read_models: { employee_compensation_view: this.compensationService.getEmployeeCompensationReadModel(enrollment.employee_id, enrollment.effective_from) } });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getBenefitsEnrollment = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      res.status(200).json({ data: this.compensationService.getBenefitsEnrollmentById(req.params.benefitsEnrollmentId) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listBenefitsEnrollments = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const page = this.compensationService.listBenefitsEnrollments({
        employee_id: typeof req.query.employee_id === 'string' ? req.query.employee_id : undefined,
        benefits_plan_id: typeof req.query.benefits_plan_id === 'string' ? req.query.benefits_plan_id : undefined,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
        limit: typeof req.query.limit === 'string' ? Number(req.query.limit) : undefined,
        cursor: typeof req.query.cursor === 'string' ? req.query.cursor : undefined,
      });
      res.status(200).json({ data: page.data, page: page.page });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateBenefitsEnrollment = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const before = this.compensationService.getBenefitsEnrollmentById(req.params.benefitsEnrollmentId);
      const enrollment = this.compensationService.updateBenefitsEnrollment(req.params.benefitsEnrollmentId, req.body);
      this.audit(req, 'benefits_enrollment_updated', 'BenefitsEnrollment', enrollment.benefits_enrollment_id, before, enrollment, enrollment.tenant_id);
      res.status(200).json({ data: enrollment, read_models: { employee_compensation_view: this.compensationService.getEmployeeCompensationReadModel(enrollment.employee_id, enrollment.effective_from) } });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  createAllowance = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const allowance = this.compensationService.createAllowance(req.body);
      this.audit(req, 'allowance_created', 'Allowance', allowance.allowance_id, {}, allowance, allowance.tenant_id);
      res.status(201).json({ data: allowance, read_models: { employee_compensation_view: this.compensationService.getEmployeeCompensationReadModel(allowance.employee_id, allowance.effective_from) } });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getAllowance = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      res.status(200).json({ data: this.compensationService.getAllowanceById(req.params.allowanceId) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listAllowances = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const page = this.compensationService.listAllowances({
        employee_id: typeof req.query.employee_id === 'string' ? req.query.employee_id : undefined,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
        limit: typeof req.query.limit === 'string' ? Number(req.query.limit) : undefined,
        cursor: typeof req.query.cursor === 'string' ? req.query.cursor : undefined,
      });
      res.status(200).json({ data: page.data, page: page.page });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateAllowance = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const before = this.compensationService.getAllowanceById(req.params.allowanceId);
      const allowance = this.compensationService.updateAllowance(req.params.allowanceId, req.body);
      this.audit(req, 'allowance_updated', 'Allowance', allowance.allowance_id, before, allowance, allowance.tenant_id);
      res.status(200).json({ data: allowance, read_models: { employee_compensation_view: this.compensationService.getEmployeeCompensationReadModel(allowance.employee_id, allowance.effective_from) } });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };


  forecastWorkforcePlan = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const forecast = this.compensationService.forecastWorkforcePlan(req.body);
      res.status(200).json({ data: forecast });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getEmployeePayrollContext = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const context = this.compensationService.getEmployeePayrollCompensationContext(
        req.params.employeeId,
        typeof req.query.effective_date === 'string' ? req.query.effective_date : undefined,
      );
      res.status(200).json({
        data: context,
        read_models: {
          employee_compensation_view: this.compensationService.getEmployeeCompensationReadModel(req.params.employeeId, context.effective_from),
        },
      });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  private audit(req: Request, action: string, entity: string, entityId: string, before: unknown, after: unknown, tenantId: string): void {
    logAuditMutation({ logger: this.logger, req, tenantId, action, entity, entityId, before, after });
  }

  private handleError(req: Request, res: Response, error: unknown): void {
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      sendError(req, res, 401, 'TOKEN_INVALID', 'Missing or invalid bearer token');
      return;
    }
    if (error instanceof Error && error.message === 'INVALID_CURSOR') {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [{ field: 'cursor', reason: 'must be a valid opaque cursor' }]);
      return;
    }
    if (error instanceof Error && error.message === 'INVALID_PAGINATION_LIMIT') {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [{ field: 'limit', reason: 'must be an integer between 1 and 100' }]);
      return;
    }
    if (error instanceof Error && error.message === 'DB_CONNECTION_POOL_EXHAUSTED') {
      sendError(req, res, 503, 'SERVICE_UNAVAILABLE', 'Temporary database overload. Please retry later.');
      return;
    }
    if (error instanceof ValidationError) {
      sendError(req, res, 422, 'VALIDATION_ERROR', error.message, error.details);
      return;
    }
    if (error instanceof NotFoundError) {
      sendError(req, res, 404, 'NOT_FOUND', error.message);
      return;
    }
    if (error instanceof ConflictError) {
      sendError(req, res, 409, 'CONFLICT', error.message);
      return;
    }
    sendError(req, res, 500, 'INTERNAL_SERVER_ERROR', 'Unexpected server failure.');
  }
}
