import { EmployeeRepository } from './employee.repository';
import {
  CreatePerformanceReviewInput,
  PerformanceReview,
  PerformanceReviewFilters,
  PerformanceReviewReadModelBundle,
  PerformanceReviewStatus,
  UpdatePerformanceReviewInput,
} from './performance.model';
import { PerformanceReviewRepository } from './performance.repository';
import {
  validateCreatePerformanceReview,
  validatePerformanceReviewStatus,
  validateUpdatePerformanceReview,
} from './performance.validation';
import { ConflictError, NotFoundError } from './service.errors';
import { ValidationError } from './employee.validation';

const STATUS_TRANSITIONS: Record<PerformanceReviewStatus, PerformanceReviewStatus[]> = {
  Draft: ['Submitted'],
  Submitted: ['Finalized'],
  Finalized: [],
};

export class PerformanceReviewService {
  constructor(
    private readonly repository: PerformanceReviewRepository,
    private readonly employeeRepository: EmployeeRepository,
  ) {}

  createReview(input: CreatePerformanceReviewInput): PerformanceReview {
    validateCreatePerformanceReview(input);
    this.ensureEmployeeReferences(input.employee_id, input.reviewer_employee_id);
    this.ensureUniqueCycle(input.employee_id, input.review_period_start, input.review_period_end);

    if (input.status && input.status !== 'Draft') {
      throw new ConflictError('performance reviews must be created in Draft status');
    }

    return this.repository.create(input);
  }

  getReviewById(performanceReviewId: string): PerformanceReview {
    const review = this.repository.findById(performanceReviewId);
    if (!review) {
      throw new NotFoundError('performance review not found');
    }
    return review;
  }

  getReviewReadModels(performanceReviewId: string): PerformanceReviewReadModelBundle {
    return this.repository.toReadModelBundle(this.getReviewById(performanceReviewId));
  }

  listReviews(filters: PerformanceReviewFilters) {
    return this.repository.list(filters);
  }

  listReviewReadModels(filters: PerformanceReviewFilters) {
    const page = this.repository.list(filters);
    return this.repository.toReadModelListBundle(page.data);
  }

  updateReview(performanceReviewId: string, input: UpdatePerformanceReviewInput): PerformanceReview {
    validateUpdatePerformanceReview(input);

    const review = this.getReviewById(performanceReviewId);
    if (review.status !== 'Draft') {
      throw new ConflictError('only Draft performance reviews can be updated');
    }

    const nextReviewPeriodStart = input.review_period_start ?? review.review_period_start;
    const nextReviewPeriodEnd = input.review_period_end ?? review.review_period_end;

    const duplicate = this.repository.findByCycle(review.employee_id, nextReviewPeriodStart, nextReviewPeriodEnd);
    if (duplicate && duplicate.performance_review_id !== performanceReviewId) {
      throw new ConflictError('performance review cycle already exists');
    }

    const updated = this.repository.update(performanceReviewId, input);
    if (!updated) {
      throw new NotFoundError('performance review not found');
    }
    return updated;
  }

  submitReview(performanceReviewId: string): PerformanceReview {
    return this.transitionReview(performanceReviewId, 'Submitted');
  }

  finalizeReview(performanceReviewId: string): PerformanceReview {
    const review = this.getReviewById(performanceReviewId);
    if (review.overall_rating === undefined) {
      throw new ValidationError([{ field: 'overall_rating', reason: 'is required before finalization' }]);
    }
    if (!review.strengths || !review.improvement_areas || !review.goals_next_period) {
      throw new ValidationError([{ field: 'body', reason: 'strengths, improvement_areas, and goals_next_period are required before finalization' }]);
    }
    return this.transitionReview(performanceReviewId, 'Finalized');
  }

  private transitionReview(performanceReviewId: string, nextStatus: PerformanceReviewStatus): PerformanceReview {
    validatePerformanceReviewStatus(nextStatus);

    const review = this.getReviewById(performanceReviewId);
    if (review.status === nextStatus) {
      return review;
    }

    if (!STATUS_TRANSITIONS[review.status].includes(nextStatus)) {
      throw new ConflictError(`cannot transition performance review from ${review.status} to ${nextStatus}`);
    }

    const updated = this.repository.updateStatus(performanceReviewId, nextStatus);
    if (!updated) {
      throw new NotFoundError('performance review not found');
    }

    return updated;
  }

  private ensureEmployeeReferences(employeeId: string, reviewerEmployeeId: string): void {
    const employee = this.employeeRepository.findById(employeeId);
    if (!employee) {
      throw new ValidationError([{ field: 'employee_id', reason: 'employee was not found' }]);
    }

    const reviewer = this.employeeRepository.findById(reviewerEmployeeId);
    if (!reviewer) {
      throw new ValidationError([{ field: 'reviewer_employee_id', reason: 'reviewer employee was not found' }]);
    }

    if (employeeId === reviewerEmployeeId) {
      throw new ValidationError([{ field: 'reviewer_employee_id', reason: 'reviewer must differ from employee' }]);
    }

    if (employee.status === 'Terminated') {
      throw new ValidationError([{ field: 'employee_id', reason: 'employee cannot be Terminated' }]);
    }

    if (reviewer.status === 'Terminated') {
      throw new ValidationError([{ field: 'reviewer_employee_id', reason: 'reviewer employee cannot be Terminated' }]);
    }
  }

  private ensureUniqueCycle(employeeId: string, reviewPeriodStart: string, reviewPeriodEnd: string): void {
    if (this.repository.findByCycle(employeeId, reviewPeriodStart, reviewPeriodEnd)) {
      throw new ConflictError('performance review cycle already exists');
    }
  }
}
