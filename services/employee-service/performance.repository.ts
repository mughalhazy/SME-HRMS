import { randomUUID } from 'node:crypto';
import { CacheService } from '../../cache/cache.service';
import { ConnectionPool, PaginatedResult, QueryOptimizer, applyCursorPagination } from '../../db/optimization';
import { Department, Employee } from './employee.model';
import { DEFAULT_TENANT_ID } from './domain-seed';
import {
  CreatePerformanceReviewInput,
  PerformanceReview,
  PerformanceReviewFilters,
  PerformanceReviewListReadModelBundle,
  PerformanceReviewReadModel,
  PerformanceReviewReadModelBundle,
  PerformanceReviewStatus,
  UpdatePerformanceReviewInput,
} from './performance.model';

const PERFORMANCE_REVIEW_CACHE_PREFIX = 'performance_reviews';

export interface PerformanceReviewReferenceRepository {
  findEmployeeById(employeeId: string): Employee | null;
  findDepartmentById(departmentId: string): Department | null;
}

export class PerformanceReviewRepository {
  private readonly reviews = new Map<string, PerformanceReview>();
  private readonly cycleIndex = new Map<string, string>();
  private readonly employeeIndex = new Map<string, Set<string>>();
  private readonly reviewerIndex = new Map<string, Set<string>>();
  private readonly statusIndex = new Map<PerformanceReviewStatus, Set<string>>();
  private readonly cache = new CacheService({ ttlMs: 15_000, maxEntries: 1_000 });
  private readonly pool = new ConnectionPool(12);
  private readonly optimizer = new QueryOptimizer(10);

  constructor(
    private readonly referenceRepository: PerformanceReviewReferenceRepository,
    private readonly tenantId: string = DEFAULT_TENANT_ID,
  ) {}

  create(input: CreatePerformanceReviewInput): PerformanceReview {
    this.assertTenantFilter(input.tenant_id);
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'performance_reviews.create' }, () => {
      const timestamp = new Date().toISOString();
      const record: PerformanceReview = {
        tenant_id: this.tenantId,
        performance_review_id: randomUUID(),
        employee_id: input.employee_id,
        reviewer_employee_id: input.reviewer_employee_id,
        review_period_start: input.review_period_start,
        review_period_end: input.review_period_end,
        overall_rating: input.overall_rating,
        strengths: input.strengths,
        improvement_areas: input.improvement_areas,
        goals_next_period: input.goals_next_period,
        status: input.status ?? 'Draft',
        submitted_at: input.status === 'Submitted' ? timestamp : undefined,
        finalized_at: input.status === 'Finalized' ? timestamp : undefined,
        created_at: timestamp,
        updated_at: timestamp,
      };

      this.reviews.set(record.performance_review_id, record);
      this.cycleIndex.set(this.toCycleKey(record.employee_id, record.review_period_start, record.review_period_end), record.performance_review_id);
      this.addToIndex(this.employeeIndex, record.employee_id, record.performance_review_id);
      this.addToIndex(this.reviewerIndex, record.reviewer_employee_id, record.performance_review_id);
      this.addToIndex(this.statusIndex, record.status, record.performance_review_id);
      this.invalidatePerformanceReviewCache(record.performance_review_id);
      return record;
    }));
  }

  findById(performanceReviewId: string): PerformanceReview | null {
    const cacheKey = `${PERFORMANCE_REVIEW_CACHE_PREFIX}:by-id:${this.tenantId}:${performanceReviewId}`;
    const cached = this.cache.get<PerformanceReview>(cacheKey);
    if (cached) {
      return cached;
    }

    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'performance_reviews.findById', expectedIndex: 'idx_performance_reviews_tenant_id + pk_performance_reviews' }, () => {
      const review = this.reviews.get(performanceReviewId) ?? null;
      if (review && review.tenant_id === this.tenantId) {
        this.cache.set(cacheKey, review);
        return review;
      }
      return null;
    }));
  }

  findByCycle(employeeId: string, reviewPeriodStart: string, reviewPeriodEnd: string): PerformanceReview | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'performance_reviews.findByCycle', expectedIndex: 'uq_performance_reviews_tenant_cycle' }, () => {
      const reviewId = this.cycleIndex.get(this.toCycleKey(employeeId, reviewPeriodStart, reviewPeriodEnd));
      return reviewId ? this.findById(reviewId) : null;
    }));
  }

  hasEmployeeReference(employeeId: string): boolean {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'performance_reviews.hasEmployeeReference' }, () => {
      return (this.employeeIndex.get(employeeId)?.size ?? 0) > 0
        || (this.reviewerIndex.get(employeeId)?.size ?? 0) > 0;
    }));
  }

  list(filters: PerformanceReviewFilters): PaginatedResult<PerformanceReview> {
    this.assertTenantFilter(filters.tenant_id);
    const cacheKey = `${PERFORMANCE_REVIEW_CACHE_PREFIX}:list:${this.tenantId}:${JSON.stringify(filters)}`;
    const cached = this.cache.get<PaginatedResult<PerformanceReview>>(cacheKey);
    if (cached) {
      return cached;
    }

    const result = this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'performance_reviews.list', expectedIndex: this.resolveExpectedIndex(filters) }, () => {
      const candidateIds = this.collectCandidateIds(filters);
      const rows = candidateIds
        .map((reviewId) => this.reviews.get(reviewId))
        .filter((review): review is PerformanceReview => Boolean(review) && review.tenant_id === this.tenantId)
        .filter((review) => {
          if (filters.employee_id && review.employee_id !== filters.employee_id) {
            return false;
          }
          if (filters.reviewer_employee_id && review.reviewer_employee_id !== filters.reviewer_employee_id) {
            return false;
          }
          if (filters.status && review.status !== filters.status) {
            return false;
          }
          return true;
        })
        .sort((left, right) => {
          if (left.updated_at === right.updated_at) {
            return left.performance_review_id.localeCompare(right.performance_review_id);
          }
          return right.updated_at.localeCompare(left.updated_at);
        });

      return applyCursorPagination(rows, { limit: filters.limit, cursor: filters.cursor });
    }));

    this.cache.set(cacheKey, result, { ttlMs: 10_000 });
    return result;
  }

  update(performanceReviewId: string, input: UpdatePerformanceReviewInput): PerformanceReview | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'performance_reviews.update', expectedIndex: 'idx_performance_reviews_tenant_id + pk_performance_reviews' }, () => {
      const review = this.findById(performanceReviewId);
      if (!review) {
        return null;
      }

      const nextReviewPeriodStart = input.review_period_start ?? review.review_period_start;
      const nextReviewPeriodEnd = input.review_period_end ?? review.review_period_end;
      const nextCycleKey = this.toCycleKey(review.employee_id, nextReviewPeriodStart, nextReviewPeriodEnd);
      const currentCycleKey = this.toCycleKey(review.employee_id, review.review_period_start, review.review_period_end);
      if (nextCycleKey !== currentCycleKey) {
        this.cycleIndex.delete(currentCycleKey);
        this.cycleIndex.set(nextCycleKey, performanceReviewId);
      }

      const updated: PerformanceReview = {
        ...review,
        ...input,
        tenant_id: this.tenantId,
        updated_at: new Date().toISOString(),
      };

      this.reviews.set(performanceReviewId, updated);
      this.invalidatePerformanceReviewCache(performanceReviewId);
      return updated;
    }));
  }

  updateStatus(performanceReviewId: string, status: PerformanceReviewStatus): PerformanceReview | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'performance_reviews.updateStatus', expectedIndex: 'idx_performance_reviews_tenant_id + pk_performance_reviews' }, () => {
      const review = this.findById(performanceReviewId);
      if (!review) {
        return null;
      }

      const timestamp = new Date().toISOString();
      const updated: PerformanceReview = {
        ...review,
        status,
        submitted_at: status === 'Submitted' ? (review.submitted_at ?? timestamp) : review.submitted_at,
        finalized_at: status === 'Finalized' ? (review.finalized_at ?? timestamp) : review.finalized_at,
        updated_at: timestamp,
      };

      this.removeFromIndex(this.statusIndex, review.status, performanceReviewId);
      this.addToIndex(this.statusIndex, updated.status, performanceReviewId);
      this.reviews.set(performanceReviewId, updated);
      this.invalidatePerformanceReviewCache(performanceReviewId);
      return updated;
    }));
  }

  toReadModelBundle(review: PerformanceReview): PerformanceReviewReadModelBundle {
    return { performance_review_view: this.toPerformanceReviewReadModel(review) };
  }

  toReadModelListBundle(reviews: PerformanceReview[]): PerformanceReviewListReadModelBundle {
    return { performance_review_view: reviews.map((review) => this.toPerformanceReviewReadModel(review)) };
  }

  private toPerformanceReviewReadModel(review: PerformanceReview): PerformanceReviewReadModel {
    const employee = this.referenceRepository.findEmployeeById(review.employee_id);
    const reviewer = this.referenceRepository.findEmployeeById(review.reviewer_employee_id);
    const employeeName = employee && employee.tenant_id === this.tenantId ? `${employee.first_name} ${employee.last_name}` : review.employee_id;
    const reviewerName = reviewer && reviewer.tenant_id === this.tenantId ? `${reviewer.first_name} ${reviewer.last_name}` : review.reviewer_employee_id;
    const department = employee && employee.tenant_id === this.tenantId ? this.referenceRepository.findDepartmentById(employee.department_id) : null;

    return {
      tenant_id: review.tenant_id,
      performance_review_id: review.performance_review_id,
      employee_id: review.employee_id,
      employee_name: employeeName,
      reviewer_employee_id: review.reviewer_employee_id,
      reviewer_name: reviewerName,
      department_id: employee?.department_id ?? 'unknown',
      department_name: department?.name ?? employee?.department_id ?? 'unknown',
      review_period_start: review.review_period_start,
      review_period_end: review.review_period_end,
      overall_rating: review.overall_rating,
      status: review.status,
      submitted_at: review.submitted_at,
      finalized_at: review.finalized_at,
      updated_at: review.updated_at,
    };
  }

  private collectCandidateIds(filters: PerformanceReviewFilters): string[] {
    if (filters.employee_id) {
      return [...(this.employeeIndex.get(filters.employee_id) ?? new Set<string>())];
    }

    if (filters.reviewer_employee_id) {
      return [...(this.reviewerIndex.get(filters.reviewer_employee_id) ?? new Set<string>())];
    }

    if (filters.status) {
      return [...(this.statusIndex.get(filters.status) ?? new Set<string>())];
    }

    return [...this.reviews.keys()];
  }

  private resolveExpectedIndex(filters: PerformanceReviewFilters): string {
    if (filters.employee_id) {
      return 'idx_performance_reviews_tenant_employee_id';
    }
    if (filters.reviewer_employee_id) {
      return 'idx_performance_reviews_tenant_reviewer_employee_id';
    }
    if (filters.status) {
      return 'idx_performance_reviews_tenant_status';
    }
    return 'idx_performance_reviews_tenant_id';
  }

  private assertTenantFilter(tenantId?: string): void {
    if (tenantId && tenantId !== this.tenantId) {
      throw new Error('cross_tenant_filter_blocked');
    }
  }

  private invalidatePerformanceReviewCache(performanceReviewId: string): void {
    this.cache.invalidate(`${PERFORMANCE_REVIEW_CACHE_PREFIX}:by-id:${this.tenantId}:${performanceReviewId}`);
    this.cache.invalidateByPrefix(`${PERFORMANCE_REVIEW_CACHE_PREFIX}:list:${this.tenantId}:`);
  }

  private addToIndex(index: Map<string, Set<string>>, key: string, reviewId: string): void {
    const existing = index.get(key) ?? new Set<string>();
    existing.add(reviewId);
    index.set(key, existing);
  }

  private removeFromIndex(index: Map<string, Set<string>>, key: string, reviewId: string): void {
    const existing = index.get(key);
    if (!existing) {
      return;
    }
    existing.delete(reviewId);
    if (existing.size === 0) {
      index.delete(key);
    }
  }

  private toCycleKey(employeeId: string, reviewPeriodStart: string, reviewPeriodEnd: string): string {
    return `${this.tenantId}:${employeeId}:${reviewPeriodStart}:${reviewPeriodEnd}`;
  }
}
