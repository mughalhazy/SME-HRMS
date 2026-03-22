export const COURSE_STATUSES = ['Draft', 'Published', 'Archived'] as const;
export type CourseStatus = (typeof COURSE_STATUSES)[number];

export const COURSE_DELIVERY_MODES = ['SelfPaced', 'InstructorLed', 'Virtual', 'Blended'] as const;
export type CourseDeliveryMode = (typeof COURSE_DELIVERY_MODES)[number];

export const ENROLLMENT_STATUSES = ['Enrolled', 'InProgress', 'Completed', 'Cancelled', 'Expired'] as const;
export type EnrollmentStatus = (typeof ENROLLMENT_STATUSES)[number];

export const COMPLETION_STATUSES = ['Completed', 'Passed', 'Failed'] as const;
export type CompletionStatus = (typeof COMPLETION_STATUSES)[number];

export interface LearningCourse {
  tenant_id: string;
  course_id: string;
  course_code: string;
  title: string;
  description?: string;
  category?: string;
  delivery_mode: CourseDeliveryMode;
  duration_hours?: number;
  validity_days?: number;
  status: CourseStatus;
  created_at: string;
  updated_at: string;
}

export interface CourseEnrollment {
  tenant_id: string;
  enrollment_id: string;
  course_id: string;
  employee_id: string;
  status: EnrollmentStatus;
  due_date?: string;
  assigned_by?: string;
  enrolled_at: string;
  started_at?: string;
  progress_percent: number;
  completed_at?: string;
  latest_completion_id?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CourseCompletionRecord {
  tenant_id: string;
  completion_id: string;
  enrollment_id: string;
  course_id: string;
  employee_id: string;
  status: CompletionStatus;
  completed_at: string;
  score_percent?: number;
  certificate_id?: string;
  recorded_by?: string;
  notes?: string;
  created_at: string;
}

export interface CreateCourseInput {
  tenant_id?: string;
  course_code: string;
  title: string;
  description?: string;
  category?: string;
  delivery_mode: CourseDeliveryMode;
  duration_hours?: number;
  validity_days?: number;
  status?: CourseStatus;
}

export interface UpdateCourseInput {
  title?: string;
  description?: string;
  category?: string;
  delivery_mode?: CourseDeliveryMode;
  duration_hours?: number;
  validity_days?: number;
  status?: CourseStatus;
}

export interface CreateEnrollmentInput {
  tenant_id?: string;
  course_id: string;
  employee_id: string;
  due_date?: string;
  assigned_by?: string;
  status?: Extract<EnrollmentStatus, 'Enrolled' | 'InProgress'>;
  progress_percent?: number;
  notes?: string;
}

export interface UpdateEnrollmentProgressInput {
  tenant_id?: string;
  progress_percent: number;
  started_at?: string;
  notes?: string;
}

export interface RecordCompletionInput {
  tenant_id?: string;
  status?: CompletionStatus;
  completed_at?: string;
  score_percent?: number;
  certificate_id?: string;
  recorded_by?: string;
  notes?: string;
}

export interface CourseFilters {
  tenant_id?: string;
  status?: CourseStatus;
  category?: string;
  delivery_mode?: CourseDeliveryMode;
}

export interface EnrollmentFilters {
  tenant_id?: string;
  employee_id?: string;
  course_id?: string;
  status?: EnrollmentStatus;
  due_to?: string;
}

export interface CompletionFilters {
  tenant_id?: string;
  employee_id?: string;
  course_id?: string;
  status?: CompletionStatus;
}

export interface EmployeeLearningSummary {
  employee_id: string;
  total_enrollments: number;
  completed_enrollments: number;
  active_enrollments: number;
  overdue_enrollments: number;
  average_progress_percent: number;
  latest_completion_at?: string;
  required_refresh_count: number;
}
