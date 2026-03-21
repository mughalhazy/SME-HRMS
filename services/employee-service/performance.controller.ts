import { Request, Response } from 'express';
import { PERFORMANCE_REVIEW_STATUSES } from './performance.model';
import { PerformanceReviewService } from './performance.service';
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

export class PerformanceReviewController {
  private readonly logger = getStructuredLogger('employee-service');

  constructor(private readonly performanceReviewService: PerformanceReviewService) {}

  private ensureReviewScope(req: Request, res: Response, auth: AuthContext, performanceReviewId: string): boolean {
    const review = this.performanceReviewService.getReviewById(performanceReviewId);

    if (auth.role === 'Employee' && auth.employee_id !== review.employee_id) {
      sendError(req, res, 403, 'FORBIDDEN', 'Insufficient permissions');
      return false;
    }

    if (auth.role === 'Manager' && auth.department_id) {
      const readModel = this.performanceReviewService.getReviewReadModels(performanceReviewId).performance_review_view;
      if (readModel.department_id !== auth.department_id) {
        sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
        return false;
      }
    }

    return true;
  }

  createReview = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      const review = this.performanceReviewService.createReview(req.body);
      const readModels = this.performanceReviewService.getReviewReadModels(review.performance_review_id);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: review.tenant_id,
        action: 'performance_review_created',
        entity: 'PerformanceReview',
        entityId: review.performance_review_id,
        before: {},
        after: review,
      });
      res.status(201).json({ data: review, read_models: readModels });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getReview = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureReviewScope(req, res, auth, req.params.performanceReviewId)) {
        return;
      }
      const review = this.performanceReviewService.getReviewById(req.params.performanceReviewId);
      const readModels = this.performanceReviewService.getReviewReadModels(req.params.performanceReviewId);
      res.status(200).json({ data: review, read_models: readModels });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listReviews = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const status = req.query.status;

      if (status && typeof status === 'string' && !PERFORMANCE_REVIEW_STATUSES.includes(status as never)) {
        sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
          { field: 'status', reason: `must be one of: ${PERFORMANCE_REVIEW_STATUSES.join(', ')}` },
        ]);
        return;
      }

      const rawLimit = typeof req.query.limit === 'string' ? Number(req.query.limit) : undefined;
      if (rawLimit !== undefined && (!Number.isInteger(rawLimit) || rawLimit < 1 || rawLimit > 100)) {
        sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
          { field: 'limit', reason: 'must be an integer between 1 and 100' },
        ]);
        return;
      }

      let employeeFilter = typeof req.query.employee_id === 'string' ? req.query.employee_id : undefined;
      let reviewerFilter = typeof req.query.reviewer_employee_id === 'string' ? req.query.reviewer_employee_id : undefined;
      if (auth.role === 'Employee') {
        employeeFilter = auth.employee_id;
        reviewerFilter = undefined;
      }
      if (auth.role === 'Manager') {
        reviewerFilter = auth.employee_id ?? reviewerFilter;
      }

      const filters = {
        employee_id: employeeFilter,
        reviewer_employee_id: reviewerFilter,
        status: typeof status === 'string' ? (status as never) : undefined,
        limit: rawLimit,
        cursor: typeof req.query.cursor === 'string' ? req.query.cursor : undefined,
      };

      const page = this.performanceReviewService.listReviews(filters);
      const readModels = this.performanceReviewService.listReviewReadModels(filters);
      res.status(200).json({
        data: page.data,
        page: {
          nextCursor: page.page.nextCursor,
          hasNext: page.page.hasNext,
          limit: page.page.limit,
        },
        read_models: readModels,
      });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateReview = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureReviewScope(req, res, auth, req.params.performanceReviewId)) {
        return;
      }
      const before = this.performanceReviewService.getReviewById(req.params.performanceReviewId);
      const review = this.performanceReviewService.updateReview(req.params.performanceReviewId, req.body);
      const readModels = this.performanceReviewService.getReviewReadModels(review.performance_review_id);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: review.tenant_id,
        action: 'performance_review_updated',
        entity: 'PerformanceReview',
        entityId: review.performance_review_id,
        before,
        after: review,
      });
      res.status(200).json({ data: review, read_models: readModels });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  submitReview = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureReviewScope(req, res, auth, req.params.performanceReviewId)) {
        return;
      }
      const before = this.performanceReviewService.getReviewById(req.params.performanceReviewId);
      const review = this.performanceReviewService.submitReview(req.params.performanceReviewId);
      const readModels = this.performanceReviewService.getReviewReadModels(review.performance_review_id);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: review.tenant_id,
        action: 'performance_review_submitted',
        entity: 'PerformanceReview',
        entityId: review.performance_review_id,
        before,
        after: review,
      });
      res.status(200).json({ data: review, read_models: readModels });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  finalizeReview = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureReviewScope(req, res, auth, req.params.performanceReviewId)) {
        return;
      }
      const before = this.performanceReviewService.getReviewById(req.params.performanceReviewId);
      const review = this.performanceReviewService.finalizeReview(req.params.performanceReviewId);
      const readModels = this.performanceReviewService.getReviewReadModels(review.performance_review_id);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: review.tenant_id,
        action: 'performance_review_finalized',
        entity: 'PerformanceReview',
        entityId: review.performance_review_id,
        before,
        after: review,
      });
      res.status(200).json({ data: review, read_models: readModels });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  private handleError(req: Request, res: Response, error: unknown): void {
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      sendError(req, res, 401, 'TOKEN_INVALID', 'Missing or invalid bearer token');
      return;
    }

    if (error instanceof Error && error.message === 'INVALID_CURSOR') {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
        { field: 'cursor', reason: 'must be a valid opaque cursor' },
      ]);
      return;
    }

    if (error instanceof Error && error.message === 'INVALID_PAGINATION_LIMIT') {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', [
        { field: 'limit', reason: 'must be an integer between 1 and 100' },
      ]);
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
