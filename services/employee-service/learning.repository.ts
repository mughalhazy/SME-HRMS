import { randomUUID } from 'node:crypto';
import {
  CompletionFilters,
  CourseCompletionRecord,
  CourseEnrollment,
  CourseFilters,
  CreateCourseInput,
  CreateEnrollmentInput,
  EnrollmentFilters,
  LearningCourse,
  RecordCompletionInput,
  UpdateCourseInput,
} from './learning.model';

export class LearningRepository {
  private readonly courses = new Map<string, LearningCourse>();
  private readonly enrollments = new Map<string, CourseEnrollment>();
  private readonly completions = new Map<string, CourseCompletionRecord>();
  private readonly courseCodeIndex = new Map<string, string>();

  createCourse(input: CreateCourseInput & { tenant_id: string }): LearningCourse {
    const timestamp = new Date().toISOString();
    const course: LearningCourse = {
      tenant_id: input.tenant_id,
      course_id: randomUUID(),
      course_code: input.course_code,
      title: input.title,
      description: input.description,
      category: input.category,
      delivery_mode: input.delivery_mode,
      duration_hours: input.duration_hours,
      validity_days: input.validity_days,
      status: input.status ?? 'Draft',
      created_at: timestamp,
      updated_at: timestamp,
    };
    this.courses.set(course.course_id, course);
    this.courseCodeIndex.set(this.courseCodeKey(course.tenant_id, course.course_code), course.course_id);
    return course;
  }

  updateCourse(courseId: string, patch: UpdateCourseInput): LearningCourse | null {
    const existing = this.findCourseById(courseId);
    if (!existing) {
      return null;
    }
    const updated: LearningCourse = {
      ...existing,
      ...patch,
      updated_at: new Date().toISOString(),
    };
    this.courses.set(courseId, updated);
    return updated;
  }

  findCourseById(courseId: string): LearningCourse | null {
    return this.courses.get(courseId) ?? null;
  }

  findCourseByCode(courseCode: string, tenantId: string): LearningCourse | null {
    const courseId = this.courseCodeIndex.get(this.courseCodeKey(tenantId, courseCode));
    return courseId ? this.findCourseById(courseId) : null;
  }

  listCourses(filters: CourseFilters & { tenant_id: string }): LearningCourse[] {
    return [...this.courses.values()]
      .filter((course) => course.tenant_id === filters.tenant_id)
      .filter((course) => !filters.status || course.status === filters.status)
      .filter((course) => !filters.category || course.category === filters.category)
      .filter((course) => !filters.delivery_mode || course.delivery_mode === filters.delivery_mode)
      .sort((left, right) => {
        if (left.updated_at === right.updated_at) {
          return left.course_code.localeCompare(right.course_code);
        }
        return right.updated_at.localeCompare(left.updated_at);
      });
  }

  createEnrollment(input: CreateEnrollmentInput & { tenant_id: string; progress_percent: number; status: CourseEnrollment['status'] }): CourseEnrollment {
    const timestamp = new Date().toISOString();
    const enrollment: CourseEnrollment = {
      tenant_id: input.tenant_id,
      enrollment_id: randomUUID(),
      course_id: input.course_id,
      employee_id: input.employee_id,
      status: input.status,
      due_date: input.due_date,
      assigned_by: input.assigned_by,
      enrolled_at: timestamp,
      started_at: input.status === 'InProgress' || input.progress_percent > 0 ? timestamp : undefined,
      progress_percent: input.progress_percent,
      notes: input.notes,
      created_at: timestamp,
      updated_at: timestamp,
    };
    this.enrollments.set(enrollment.enrollment_id, enrollment);
    return enrollment;
  }

  findEnrollmentById(enrollmentId: string): CourseEnrollment | null {
    return this.enrollments.get(enrollmentId) ?? null;
  }

  updateEnrollment(enrollmentId: string, patch: Partial<CourseEnrollment>): CourseEnrollment | null {
    const existing = this.findEnrollmentById(enrollmentId);
    if (!existing) {
      return null;
    }
    const updated: CourseEnrollment = {
      ...existing,
      ...patch,
      updated_at: new Date().toISOString(),
    };
    this.enrollments.set(enrollmentId, updated);
    return updated;
  }

  listEnrollments(filters: EnrollmentFilters & { tenant_id: string }): CourseEnrollment[] {
    return [...this.enrollments.values()]
      .filter((enrollment) => enrollment.tenant_id === filters.tenant_id)
      .filter((enrollment) => !filters.employee_id || enrollment.employee_id === filters.employee_id)
      .filter((enrollment) => !filters.course_id || enrollment.course_id === filters.course_id)
      .filter((enrollment) => !filters.status || enrollment.status === filters.status)
      .filter((enrollment) => !filters.due_to || (enrollment.due_date !== undefined && enrollment.due_date <= filters.due_to))
      .sort((left, right) => {
        if (left.updated_at === right.updated_at) {
          return left.enrollment_id.localeCompare(right.enrollment_id);
        }
        return right.updated_at.localeCompare(left.updated_at);
      });
  }

  findActiveEnrollmentForEmployeeCourse(employeeId: string, courseId: string, tenantId: string): CourseEnrollment | null {
    return [...this.enrollments.values()].find((enrollment) => (
      enrollment.tenant_id === tenantId
      && enrollment.employee_id === employeeId
      && enrollment.course_id === courseId
      && enrollment.status !== 'Cancelled'
      && enrollment.status !== 'Expired'
    )) ?? null;
  }

  createCompletion(input: RecordCompletionInput & { tenant_id: string; enrollment_id: string; course_id: string; employee_id: string; status: CourseCompletionRecord['status']; completed_at: string }): CourseCompletionRecord {
    const record: CourseCompletionRecord = {
      tenant_id: input.tenant_id,
      completion_id: randomUUID(),
      enrollment_id: input.enrollment_id,
      course_id: input.course_id,
      employee_id: input.employee_id,
      status: input.status,
      completed_at: input.completed_at,
      score_percent: input.score_percent,
      certificate_id: input.certificate_id,
      recorded_by: input.recorded_by,
      notes: input.notes,
      created_at: new Date().toISOString(),
    };
    this.completions.set(record.completion_id, record);
    return record;
  }

  listCompletions(filters: CompletionFilters & { tenant_id: string }): CourseCompletionRecord[] {
    return [...this.completions.values()]
      .filter((completion) => completion.tenant_id === filters.tenant_id)
      .filter((completion) => !filters.employee_id || completion.employee_id === filters.employee_id)
      .filter((completion) => !filters.course_id || completion.course_id === filters.course_id)
      .filter((completion) => !filters.status || completion.status === filters.status)
      .sort((left, right) => right.completed_at.localeCompare(left.completed_at));
  }

  findLatestCompletionForEnrollment(enrollmentId: string, tenantId: string): CourseCompletionRecord | null {
    return this.listCompletions({ tenant_id: tenantId }).find((completion) => completion.enrollment_id === enrollmentId) ?? null;
  }

  private courseCodeKey(tenantId: string, courseCode: string): string {
    return `${tenantId}:${courseCode}`;
  }
}
