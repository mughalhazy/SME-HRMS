import { Request, Response } from 'express';
import { logAuditMutation } from '../../middleware/audit';
import { ApiError, sendApiError } from '../../middleware/error-handler';
import { getStructuredLogger } from '../../middleware/logger';
import { ValidationError } from './employee.validation';
import { EmployeeService } from './employee.service';
import { ConflictError, NotFoundError } from './service.errors';
import { AuthContext } from './rbac.middleware';
import { LearningService } from './learning.service';

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

export class LearningController {
  private readonly logger = getStructuredLogger('employee-service');

  constructor(
    private readonly learningService: LearningService,
    private readonly employeeService: EmployeeService,
  ) {}

  private canAccessEmployee(auth: AuthContext, employeeId: string | undefined): boolean {
    if (!employeeId) {
      return auth.role === 'Admin' || auth.role === 'Service' || auth.role === 'Manager';
    }
    if (auth.role === 'Admin' || auth.role === 'Service') {
      return true;
    }
    if (auth.role === 'Employee' || auth.role === 'PayrollAdmin') {
      return auth.employee_id === employeeId;
    }
    if (auth.role === 'Manager') {
      return this.employeeService.canManagerAccessEmployee(auth.employee_id, auth.department_id, employeeId);
    }
    return false;
  }

  private ensureEmployeeScope(req: Request, res: Response, auth: AuthContext, employeeId: string | undefined): boolean {
    if (this.canAccessEmployee(auth, employeeId)) {
      return true;
    }
    sendError(req, res, 403, 'FORBIDDEN', 'Insufficient team scope');
    return false;
  }

  createCourse = (req: Request, res: Response): void => {
    try {
      const course = this.learningService.createCourse({ ...req.body, tenant_id: req.tenantId });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: course.tenant_id,
        action: 'learning_course_created',
        entity: 'LearningCourse',
        entityId: course.course_id,
        before: {},
        after: course,
      });
      res.status(201).json({ data: course });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listCourses = (req: Request, res: Response): void => {
    try {
      const courses = this.learningService.listCourses({
        tenant_id: req.tenantId,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
        category: typeof req.query.category === 'string' ? req.query.category : undefined,
        delivery_mode: typeof req.query.delivery_mode === 'string' ? req.query.delivery_mode as never : undefined,
      });
      res.status(200).json({ data: courses });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getCourse = (req: Request, res: Response): void => {
    try {
      res.status(200).json({ data: this.learningService.getCourseById(req.params.courseId) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateCourse = (req: Request, res: Response): void => {
    try {
      const before = this.learningService.getCourseById(req.params.courseId);
      const updated = this.learningService.updateCourse(req.params.courseId, req.body);
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: updated.tenant_id,
        action: 'learning_course_updated',
        entity: 'LearningCourse',
        entityId: updated.course_id,
        before,
        after: updated,
      });
      res.status(200).json({ data: updated });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  createEnrollment = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureEmployeeScope(req, res, auth, req.body.employee_id)) {
        return;
      }
      const enrollment = this.learningService.createEnrollment({ ...req.body, tenant_id: req.tenantId, assigned_by: req.body?.assigned_by ?? auth.employee_id });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: enrollment.tenant_id,
        action: 'learning_enrollment_created',
        entity: 'CourseEnrollment',
        entityId: enrollment.enrollment_id,
        before: {},
        after: enrollment,
      });
      res.status(201).json({ data: enrollment });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getEnrollment = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const enrollment = this.learningService.getEnrollmentById(req.params.enrollmentId);
      if (!this.ensureEmployeeScope(req, res, auth, enrollment.employee_id)) {
        return;
      }
      res.status(200).json({ data: enrollment });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listEnrollments = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const employeeId = typeof req.query.employee_id === 'string' ? req.query.employee_id : auth.role === 'Employee' || auth.role === 'PayrollAdmin' ? auth.employee_id : undefined;
      if (employeeId && !this.ensureEmployeeScope(req, res, auth, employeeId)) {
        return;
      }
      const enrollments = this.learningService.listEnrollments({
        tenant_id: req.tenantId,
        employee_id: employeeId,
        course_id: typeof req.query.course_id === 'string' ? req.query.course_id : undefined,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
        due_to: typeof req.query.due_to === 'string' ? req.query.due_to : undefined,
      });
      res.status(200).json({ data: enrollments });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  updateEnrollmentProgress = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const before = this.learningService.getEnrollmentById(req.params.enrollmentId);
      if (!this.ensureEmployeeScope(req, res, auth, before.employee_id)) {
        return;
      }
      const updated = this.learningService.updateEnrollmentProgress(req.params.enrollmentId, { ...req.body, tenant_id: req.tenantId });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: updated.tenant_id,
        action: 'learning_enrollment_progress_updated',
        entity: 'CourseEnrollment',
        entityId: updated.enrollment_id,
        before,
        after: updated,
      });
      res.status(200).json({ data: updated });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  recordCompletion = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const before = this.learningService.getEnrollmentById(req.params.enrollmentId);
      if (!this.ensureEmployeeScope(req, res, auth, before.employee_id)) {
        return;
      }
      const result = this.learningService.recordCompletion(req.params.enrollmentId, {
        ...req.body,
        tenant_id: req.tenantId,
        recorded_by: req.body?.recorded_by ?? auth.employee_id ?? auth.role,
      });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: result.enrollment.tenant_id,
        action: 'learning_completion_recorded',
        entity: 'CourseCompletionRecord',
        entityId: result.completion.completion_id,
        before,
        after: result,
      });
      res.status(201).json({ data: result });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listCompletions = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      const employeeId = typeof req.query.employee_id === 'string' ? req.query.employee_id : auth.role === 'Employee' || auth.role === 'PayrollAdmin' ? auth.employee_id : undefined;
      if (employeeId && !this.ensureEmployeeScope(req, res, auth, employeeId)) {
        return;
      }
      const completions = this.learningService.listCompletions({
        tenant_id: req.tenantId,
        employee_id: employeeId,
        course_id: typeof req.query.course_id === 'string' ? req.query.course_id : undefined,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
      });
      res.status(200).json({ data: completions });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getEmployeeSummary = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureEmployeeScope(req, res, auth, req.params.employeeId)) {
        return;
      }
      res.status(200).json({ data: this.learningService.getEmployeeLearningSummary(req.params.employeeId) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  createLearningPath = (req: Request, res: Response): void => {
    try {
      const path = this.learningService.createLearningPath({ ...req.body, tenant_id: req.tenantId });
      logAuditMutation({
        logger: this.logger,
        req,
        tenantId: path.tenant_id,
        action: 'learning_path_created',
        entity: 'LearningPath',
        entityId: path.learning_path_id,
        before: {},
        after: path,
      });
      res.status(201).json({ data: path });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  listLearningPaths = (req: Request, res: Response): void => {
    try {
      const items = this.learningService.listLearningPaths({
        tenant_id: req.tenantId,
        status: typeof req.query.status === 'string' ? req.query.status as never : undefined,
      });
      res.status(200).json({ data: items });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getEmployeeCertifications = (req: Request, res: Response): void => {
    try {
      const auth = getAuth(req);
      if (!this.ensureEmployeeScope(req, res, auth, req.params.employeeId)) {
        return;
      }
      res.status(200).json({ data: this.learningService.listEmployeeCertifications(req.params.employeeId) });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  getLearningAnalytics = (req: Request, res: Response): void => {
    try {
      getAuth(req);
      res.status(200).json({ data: this.learningService.getLearningAnalytics() });
    } catch (error) {
      this.handleError(req, res, error);
    }
  };

  private handleError(req: Request, res: Response, error: unknown): void {
    if (error instanceof ValidationError) {
      sendError(req, res, 422, 'VALIDATION_ERROR', 'One or more fields are invalid.', error.details);
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
    if (error instanceof Error && error.message === 'UNAUTHORIZED') {
      sendError(req, res, 401, 'TOKEN_INVALID', 'Missing or invalid bearer token');
      return;
    }
    sendError(req, res, 500, 'INTERNAL_ERROR', 'Unexpected error');
  }
}
