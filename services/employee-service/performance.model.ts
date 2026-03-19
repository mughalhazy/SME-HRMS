export const PERFORMANCE_REVIEW_STATUSES = ['Draft', 'Submitted', 'Finalized'] as const;
export type PerformanceReviewStatus = (typeof PERFORMANCE_REVIEW_STATUSES)[number];

export interface PerformanceReview {
  performance_review_id: string;
  employee_id: string;
  reviewer_employee_id: string;
  review_period_start: string;
  review_period_end: string;
  overall_rating?: number;
  strengths?: string;
  improvement_areas?: string;
  goals_next_period?: string;
  status: PerformanceReviewStatus;
  submitted_at?: string;
  finalized_at?: string;
  created_at: string;
  updated_at: string;
}

export interface PerformanceReviewReadModel {
  performance_review_id: string;
  employee_id: string;
  employee_name: string;
  reviewer_employee_id: string;
  reviewer_name: string;
  department_id: string;
  department_name: string;
  review_period_start: string;
  review_period_end: string;
  overall_rating?: number;
  status: PerformanceReviewStatus;
  submitted_at?: string;
  finalized_at?: string;
  updated_at: string;
}

export interface PerformanceReviewReadModelBundle {
  performance_review_view: PerformanceReviewReadModel;
}

export interface PerformanceReviewListReadModelBundle {
  performance_review_view: PerformanceReviewReadModel[];
}

export interface CreatePerformanceReviewInput {
  employee_id: string;
  reviewer_employee_id: string;
  review_period_start: string;
  review_period_end: string;
  overall_rating?: number;
  strengths?: string;
  improvement_areas?: string;
  goals_next_period?: string;
  status?: PerformanceReviewStatus;
}

export interface UpdatePerformanceReviewInput {
  review_period_start?: string;
  review_period_end?: string;
  overall_rating?: number;
  strengths?: string;
  improvement_areas?: string;
  goals_next_period?: string;
}

export interface PerformanceReviewFilters {
  employee_id?: string;
  reviewer_employee_id?: string;
  status?: PerformanceReviewStatus;
  limit?: number;
  cursor?: string;
}
