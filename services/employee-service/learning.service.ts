import { EmployeeRepository } from './employee.repository';
import { EmployeeEventOutbox } from './event-outbox';
import { ValidationError } from './employee.validation';
import {
  COMPLETION_STATUSES,
  CompletionFilters,
  COURSE_DELIVERY_MODES,
  COURSE_STATUSES,
  CourseCompletionRecord,
  CourseEnrollment,
  CourseFilters,
  CreateLearningPathInput,
  CreateCourseInput,
  CreateEnrollmentInput,
  EmployeeLearningSummary,
  ENROLLMENT_STATUSES,
  EnrollmentFilters,
  LearningCourse,
  LearningCertification,
  LearningPath,
  LearningPathFilters,
  RecordCompletionInput,
  UpdateCourseInput,
  UpdateEnrollmentProgressInput,
} from './learning.model';
import { LearningRepository } from './learning.repository';
import { ConflictError, NotFoundError } from './service.errors';

function isIsoDate(value: string | undefined): boolean {
  if (!value) {
    return false;
  }
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));
}

export class LearningService {
  readonly eventOutbox = new EmployeeEventOutbox();

  constructor(
    private readonly repository: LearningRepository,
    private readonly employeeRepository: EmployeeRepository,
    private readonly tenantId: string = 'tenant-default',
  ) {}

  createCourse(input: CreateCourseInput): LearningCourse {
    this.assertActorTenant(input.tenant_id);
    this.validateCourseInput(input);
    this.ensureUniqueCourseCode(input.course_code);

    const course = this.repository.createCourse({ ...input, tenant_id: this.tenantId });
    this.eventOutbox.enqueue('LearningCourseCreated', this.tenantId, {
      course_id: course.course_id,
      course_code: course.course_code,
      title: course.title,
      status: course.status,
      delivery_mode: course.delivery_mode,
    }, course.course_id);
    this.eventOutbox.dispatchPending();
    return course;
  }

  updateCourse(courseId: string, patch: UpdateCourseInput): LearningCourse {
    this.validateCoursePatch(patch);
    const existing = this.getCourseById(courseId);
    const updated = this.repository.updateCourse(courseId, patch);
    if (!updated) {
      throw new NotFoundError('course not found');
    }
    this.eventOutbox.enqueue('LearningCourseUpdated', this.tenantId, {
      course_id: updated.course_id,
      course_code: updated.course_code,
      title: updated.title,
      previous_status: existing.status,
      status: updated.status,
    }, `${updated.course_id}:${updated.updated_at}`);
    this.eventOutbox.dispatchPending();
    return updated;
  }

  getCourseById(courseId: string): LearningCourse {
    const course = this.repository.findCourseById(courseId);
    if (!course || course.tenant_id !== this.tenantId) {
      throw new NotFoundError('course not found');
    }
    return course;
  }

  listCourses(filters: CourseFilters): LearningCourse[] {
    this.assertActorTenant(filters.tenant_id);
    return this.repository.listCourses({ ...filters, tenant_id: this.tenantId });
  }

  createEnrollment(input: CreateEnrollmentInput): CourseEnrollment {
    this.assertActorTenant(input.tenant_id);
    this.validateEnrollmentInput(input);
    const course = this.getCourseById(input.course_id);
    this.ensureEmployeeExists(input.employee_id);
    if (course.status !== 'Published') {
      throw new ConflictError('course must be Published before enrollment');
    }
    if (this.repository.findActiveEnrollmentForEmployeeCourse(input.employee_id, input.course_id, this.tenantId)) {
      throw new ConflictError('employee already has an active enrollment for this course');
    }

    const status = input.status ?? ((input.progress_percent ?? 0) > 0 ? 'InProgress' : 'Enrolled');
    const progressPercent = input.progress_percent ?? (status === 'InProgress' ? 1 : 0);
    const enrollment = this.repository.createEnrollment({ ...input, tenant_id: this.tenantId, status, progress_percent: progressPercent });
    this.eventOutbox.enqueue('LearningEnrollmentCreated', this.tenantId, {
      enrollment_id: enrollment.enrollment_id,
      course_id: enrollment.course_id,
      employee_id: enrollment.employee_id,
      due_date: enrollment.due_date,
      status: enrollment.status,
      progress_percent: enrollment.progress_percent,
    }, enrollment.enrollment_id);
    this.eventOutbox.dispatchPending();
    return enrollment;
  }

  getEnrollmentById(enrollmentId: string): CourseEnrollment {
    const enrollment = this.repository.findEnrollmentById(enrollmentId);
    if (!enrollment || enrollment.tenant_id !== this.tenantId) {
      throw new NotFoundError('enrollment not found');
    }
    return enrollment;
  }

  listEnrollments(filters: EnrollmentFilters): CourseEnrollment[] {
    this.assertActorTenant(filters.tenant_id);
    return this.repository.listEnrollments({ ...filters, tenant_id: this.tenantId }).map((enrollment) => this.withDerivedEnrollmentStatus(enrollment));
  }

  updateEnrollmentProgress(enrollmentId: string, input: UpdateEnrollmentProgressInput): CourseEnrollment {
    this.assertActorTenant(input.tenant_id);
    this.validateProgressInput(input);
    const existing = this.getEnrollmentById(enrollmentId);
    if (existing.status === 'Completed' || existing.status === 'Cancelled' || existing.status === 'Expired') {
      throw new ConflictError(`cannot update progress for enrollment in ${existing.status} status`);
    }

    const nextProgress = Math.max(existing.progress_percent, input.progress_percent);
    const updated = this.repository.updateEnrollment(enrollmentId, {
      progress_percent: nextProgress,
      started_at: existing.started_at ?? input.started_at ?? new Date().toISOString(),
      status: nextProgress > 0 ? 'InProgress' : 'Enrolled',
      notes: input.notes ?? existing.notes,
    });
    if (!updated) {
      throw new NotFoundError('enrollment not found');
    }

    this.eventOutbox.enqueue('LearningEnrollmentProgressUpdated', this.tenantId, {
      enrollment_id: updated.enrollment_id,
      course_id: updated.course_id,
      employee_id: updated.employee_id,
      progress_percent: updated.progress_percent,
      status: updated.status,
    }, `${updated.enrollment_id}:${updated.progress_percent}`);
    this.eventOutbox.dispatchPending();
    return updated;
  }

  recordCompletion(enrollmentId: string, input: RecordCompletionInput): { enrollment: CourseEnrollment; completion: CourseCompletionRecord } {
    this.assertActorTenant(input.tenant_id);
    this.validateCompletionInput(input);
    const enrollment = this.withDerivedEnrollmentStatus(this.getEnrollmentById(enrollmentId));
    if (enrollment.status === 'Cancelled') {
      throw new ConflictError('cannot complete a cancelled enrollment');
    }
    if (enrollment.status === 'Expired') {
      throw new ConflictError('cannot complete an expired enrollment');
    }
    if (this.repository.findLatestCompletionForEnrollment(enrollmentId, this.tenantId)) {
      throw new ConflictError('completion already recorded for enrollment');
    }

    const completedAt = input.completed_at ?? new Date().toISOString();
    const completion = this.repository.createCompletion({
      ...input,
      tenant_id: this.tenantId,
      enrollment_id: enrollment.enrollment_id,
      course_id: enrollment.course_id,
      employee_id: enrollment.employee_id,
      status: input.status ?? 'Completed',
      completed_at: completedAt,
    });
    const updatedEnrollment = this.repository.updateEnrollment(enrollmentId, {
      status: 'Completed',
      progress_percent: 100,
      started_at: enrollment.started_at ?? completedAt,
      completed_at: completedAt,
      latest_completion_id: completion.completion_id,
      notes: input.notes ?? enrollment.notes,
    });
    if (!updatedEnrollment) {
      throw new NotFoundError('enrollment not found');
    }

    this.eventOutbox.enqueue('LearningCompletionRecorded', this.tenantId, {
      completion_id: completion.completion_id,
      enrollment_id: completion.enrollment_id,
      course_id: completion.course_id,
      employee_id: completion.employee_id,
      status: completion.status,
      completed_at: completion.completed_at,
      score_percent: completion.score_percent,
    }, completion.completion_id);
    this.eventOutbox.dispatchPending();
    return { enrollment: updatedEnrollment, completion };
  }

  listCompletions(filters: CompletionFilters): CourseCompletionRecord[] {
    this.assertActorTenant(filters.tenant_id);
    return this.repository.listCompletions({ ...filters, tenant_id: this.tenantId });
  }

  createLearningPath(input: CreateLearningPathInput): LearningPath {
    this.assertActorTenant(input.tenant_id);
    this.validateLearningPathInput(input);
    if (this.repository.findLearningPathByCode(input.code, this.tenantId)) {
      throw new ConflictError('learning path code already exists');
    }
    input.course_ids.forEach((courseId) => this.getCourseById(courseId));
    return this.repository.createLearningPath({ ...input, tenant_id: this.tenantId });
  }

  listLearningPaths(filters: LearningPathFilters): LearningPath[] {
    this.assertActorTenant(filters.tenant_id);
    return this.repository.listLearningPaths({ ...filters, tenant_id: this.tenantId });
  }

  listEmployeeCertifications(employeeId: string): LearningCertification[] {
    this.ensureEmployeeExists(employeeId);
    return this.listCompletions({ tenant_id: this.tenantId, employee_id: employeeId })
      .filter((completion) => completion.status !== 'Failed' && Boolean(completion.certificate_id))
      .map((completion) => ({
        employee_id: completion.employee_id,
        course_id: completion.course_id,
        completion_id: completion.completion_id,
        certificate_id: String(completion.certificate_id),
        completed_at: completion.completed_at,
        status: completion.status,
      }));
  }

  getLearningAnalytics(): {
    totals: { courses: number; learning_paths: number; enrollments: number; completions: number; certifications: number };
    completion_rate: number;
    avg_progress_percent: number;
    path_coverage_rate: number;
  } {
    const courses = this.listCourses({ tenant_id: this.tenantId });
    const paths = this.listLearningPaths({ tenant_id: this.tenantId, status: 'Active' });
    const enrollments = this.listEnrollments({ tenant_id: this.tenantId });
    const completions = this.listCompletions({ tenant_id: this.tenantId });
    const certifications = completions.filter((completion) => completion.status !== 'Failed' && Boolean(completion.certificate_id));
    const completionRate = enrollments.length === 0 ? 0 : completions.length / enrollments.length;
    const avgProgress = enrollments.length === 0 ? 0 : enrollments.reduce((sum, enrollment) => sum + enrollment.progress_percent, 0) / enrollments.length;
    const coveredEmployees = new Set<string>();
    const scopedEnrollments = this.listEnrollments({ tenant_id: this.tenantId, status: 'Completed' });
    for (const path of paths) {
      if (path.course_ids.length === 0) {
        continue;
      }
      const byEmployee = new Map<string, Set<string>>();
      scopedEnrollments.filter((enrollment) => path.course_ids.includes(enrollment.course_id)).forEach((enrollment) => {
        const employeeCourses = byEmployee.get(enrollment.employee_id) ?? new Set<string>();
        employeeCourses.add(enrollment.course_id);
        byEmployee.set(enrollment.employee_id, employeeCourses);
      });
      byEmployee.forEach((courseIds, employeeId) => {
        if (path.course_ids.every((courseId) => courseIds.has(courseId))) {
          coveredEmployees.add(employeeId);
        }
      });
    }
    return {
      totals: {
        courses: courses.length,
        learning_paths: paths.length,
        enrollments: enrollments.length,
        completions: completions.length,
        certifications: certifications.length,
      },
      completion_rate: Number(completionRate.toFixed(4)),
      avg_progress_percent: Number(avgProgress.toFixed(2)),
      path_coverage_rate: Number((coveredEmployees.size / (paths.length || 1)).toFixed(4)),
    };
  }

  getEmployeeLearningSummary(employeeId: string): EmployeeLearningSummary {
    this.ensureEmployeeExists(employeeId);
    const enrollments = this.listEnrollments({ tenant_id: this.tenantId, employee_id: employeeId });
    const completions = this.listCompletions({ tenant_id: this.tenantId, employee_id: employeeId });
    const overdueEnrollments = enrollments.filter((enrollment) => enrollment.status === 'Expired').length;
    const activeEnrollments = enrollments.filter((enrollment) => enrollment.status === 'Enrolled' || enrollment.status === 'InProgress').length;
    const averageProgressPercent = enrollments.length === 0
      ? 0
      : Math.round((enrollments.reduce((sum, enrollment) => sum + enrollment.progress_percent, 0) / enrollments.length) * 100) / 100;
    const refreshCount = completions.filter((completion) => {
      const course = this.repository.findCourseById(completion.course_id);
      if (!course?.validity_days) {
        return false;
      }
      const expiry = new Date(completion.completed_at);
      expiry.setUTCDate(expiry.getUTCDate() + course.validity_days);
      return expiry.toISOString() < new Date().toISOString();
    }).length;
    return {
      employee_id: employeeId,
      total_enrollments: enrollments.length,
      completed_enrollments: enrollments.filter((enrollment) => enrollment.status === 'Completed').length,
      active_enrollments: activeEnrollments,
      overdue_enrollments: overdueEnrollments,
      average_progress_percent: averageProgressPercent,
      latest_completion_at: completions[0]?.completed_at,
      required_refresh_count: refreshCount,
    };
  }

  private withDerivedEnrollmentStatus(enrollment: CourseEnrollment): CourseEnrollment {
    if (enrollment.status === 'Completed' || enrollment.status === 'Cancelled') {
      return enrollment;
    }
    if (enrollment.due_date && enrollment.due_date < new Date().toISOString().slice(0, 10)) {
      return { ...enrollment, status: 'Expired' };
    }
    return enrollment;
  }

  private validateCourseInput(input: CreateCourseInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (!input.course_code?.trim()) {
      details.push({ field: 'course_code', reason: 'must be a non-empty string' });
    }
    if (!input.title?.trim()) {
      details.push({ field: 'title', reason: 'must be a non-empty string' });
    }
    if (!COURSE_DELIVERY_MODES.includes(input.delivery_mode)) {
      details.push({ field: 'delivery_mode', reason: `must be one of: ${COURSE_DELIVERY_MODES.join(', ')}` });
    }
    if (input.status && !COURSE_STATUSES.includes(input.status)) {
      details.push({ field: 'status', reason: `must be one of: ${COURSE_STATUSES.join(', ')}` });
    }
    if (input.duration_hours !== undefined && (!Number.isFinite(input.duration_hours) || input.duration_hours <= 0)) {
      details.push({ field: 'duration_hours', reason: 'must be a positive number when provided' });
    }
    if (input.validity_days !== undefined && (!Number.isInteger(input.validity_days) || input.validity_days <= 0)) {
      details.push({ field: 'validity_days', reason: 'must be a positive integer when provided' });
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateCoursePatch(patch: UpdateCourseInput): void {
    if (Object.keys(patch).length === 0) {
      throw new ValidationError([{ field: 'body', reason: 'must include at least one updatable field' }]);
    }
    this.validateCourseInput({
      course_code: 'patch-placeholder',
      title: patch.title ?? 'patch-placeholder',
      delivery_mode: patch.delivery_mode ?? 'SelfPaced',
      duration_hours: patch.duration_hours,
      validity_days: patch.validity_days,
      status: patch.status,
      description: patch.description,
      category: patch.category,
    });
  }

  private validateEnrollmentInput(input: CreateEnrollmentInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (!input.course_id?.trim()) {
      details.push({ field: 'course_id', reason: 'must be a non-empty string' });
    }
    if (!input.employee_id?.trim()) {
      details.push({ field: 'employee_id', reason: 'must be a non-empty string' });
    }
    if (input.due_date && !isIsoDate(input.due_date)) {
      details.push({ field: 'due_date', reason: 'must be an ISO date in YYYY-MM-DD format' });
    }
    if (input.status && !['Enrolled', 'InProgress'].includes(input.status)) {
      details.push({ field: 'status', reason: 'must be Enrolled or InProgress when provided' });
    }
    if (input.progress_percent !== undefined && (!Number.isFinite(input.progress_percent) || input.progress_percent < 0 || input.progress_percent > 100)) {
      details.push({ field: 'progress_percent', reason: 'must be a number between 0 and 100 when provided' });
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateProgressInput(input: UpdateEnrollmentProgressInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (!Number.isFinite(input.progress_percent) || input.progress_percent < 0 || input.progress_percent > 100) {
      details.push({ field: 'progress_percent', reason: 'must be a number between 0 and 100' });
    }
    if (input.started_at && Number.isNaN(Date.parse(input.started_at))) {
      details.push({ field: 'started_at', reason: 'must be an ISO datetime when provided' });
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateCompletionInput(input: RecordCompletionInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (input.status && !COMPLETION_STATUSES.includes(input.status)) {
      details.push({ field: 'status', reason: `must be one of: ${COMPLETION_STATUSES.join(', ')}` });
    }
    if (input.completed_at && Number.isNaN(Date.parse(input.completed_at))) {
      details.push({ field: 'completed_at', reason: 'must be an ISO datetime when provided' });
    }
    if (input.score_percent !== undefined && (!Number.isFinite(input.score_percent) || input.score_percent < 0 || input.score_percent > 100)) {
      details.push({ field: 'score_percent', reason: 'must be a number between 0 and 100 when provided' });
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private validateLearningPathInput(input: CreateLearningPathInput): void {
    const details: Array<{ field: string; reason: string }> = [];
    if (!input.code?.trim()) {
      details.push({ field: 'code', reason: 'must be a non-empty string' });
    }
    if (!input.title?.trim()) {
      details.push({ field: 'title', reason: 'must be a non-empty string' });
    }
    if (!Array.isArray(input.course_ids) || input.course_ids.length === 0) {
      details.push({ field: 'course_ids', reason: 'must include at least one course id' });
    }
    if (input.status && !['Active', 'Inactive'].includes(input.status)) {
      details.push({ field: 'status', reason: 'must be Active or Inactive when provided' });
    }
    if (details.length > 0) {
      throw new ValidationError(details);
    }
  }

  private ensureEmployeeExists(employeeId: string): void {
    if (!this.employeeRepository.findById(employeeId)) {
      throw new ValidationError([{ field: 'employee_id', reason: 'employee was not found' }]);
    }
  }

  private ensureUniqueCourseCode(courseCode: string): void {
    if (this.repository.findCourseByCode(courseCode, this.tenantId)) {
      throw new ConflictError('course code already exists');
    }
  }

  private assertActorTenant(tenantId?: string): void {
    if (tenantId && tenantId !== this.tenantId) {
      throw new ValidationError([{ field: 'tenant_id', reason: `must match tenant ${this.tenantId}` }]);
    }
  }
}
