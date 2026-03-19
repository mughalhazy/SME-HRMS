import {
  CreatePerformanceReviewInput,
  PERFORMANCE_REVIEW_STATUSES,
  PerformanceReviewFilters,
  PerformanceReviewStatus,
  UpdatePerformanceReviewInput,
} from './performance.model';
import { ValidationError } from './employee.validation';

function isIsoDate(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));
}

function requireString(
  details: Array<{ field: string; reason: string }>,
  field: string,
  value: unknown,
): void {
  if (typeof value !== 'string' || value.trim() === '') {
    details.push({ field, reason: 'must be a non-empty string' });
  }
}

function validateOptionalText(
  details: Array<{ field: string; reason: string }>,
  field: string,
  value: unknown,
): void {
  if (value !== undefined && (typeof value !== 'string' || value.trim() === '')) {
    details.push({ field, reason: 'must be a non-empty string when provided' });
  }
}

function validateOptionalRating(
  details: Array<{ field: string; reason: string }>,
  value: unknown,
): void {
  if (value === undefined) {
    return;
  }

  if (typeof value !== 'number' || Number.isNaN(value) || value < 1 || value > 5) {
    details.push({ field: 'overall_rating', reason: 'must be a number between 1 and 5' });
    return;
  }

  if (Math.round(value * 10) !== value * 10) {
    details.push({ field: 'overall_rating', reason: 'must use increments of 0.1' });
  }
}

function validatePeriod(
  details: Array<{ field: string; reason: string }>,
  reviewPeriodStart?: string,
  reviewPeriodEnd?: string,
): void {
  if (reviewPeriodStart && !isIsoDate(reviewPeriodStart)) {
    details.push({ field: 'review_period_start', reason: 'must be an ISO date (YYYY-MM-DD)' });
  }

  if (reviewPeriodEnd && !isIsoDate(reviewPeriodEnd)) {
    details.push({ field: 'review_period_end', reason: 'must be an ISO date (YYYY-MM-DD)' });
  }

  if (reviewPeriodStart && reviewPeriodEnd && reviewPeriodEnd < reviewPeriodStart) {
    details.push({ field: 'review_period_end', reason: 'must be on or after review_period_start' });
  }
}

export function validateCreatePerformanceReview(input: CreatePerformanceReviewInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  requireString(details, 'employee_id', input.employee_id);
  requireString(details, 'reviewer_employee_id', input.reviewer_employee_id);
  requireString(details, 'review_period_start', input.review_period_start);
  requireString(details, 'review_period_end', input.review_period_end);

  validatePeriod(details, input.review_period_start, input.review_period_end);
  validateOptionalText(details, 'strengths', input.strengths);
  validateOptionalText(details, 'improvement_areas', input.improvement_areas);
  validateOptionalText(details, 'goals_next_period', input.goals_next_period);
  validateOptionalRating(details, input.overall_rating);

  if (input.status && !PERFORMANCE_REVIEW_STATUSES.includes(input.status)) {
    details.push({
      field: 'status',
      reason: `must be one of: ${PERFORMANCE_REVIEW_STATUSES.join(', ')}`,
    });
  }

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validateUpdatePerformanceReview(input: UpdatePerformanceReviewInput): void {
  const details: Array<{ field: string; reason: string }> = [];

  if (Object.keys(input).length === 0) {
    details.push({ field: 'body', reason: 'must include at least one updatable field' });
  }

  validatePeriod(details, input.review_period_start, input.review_period_end);
  validateOptionalText(details, 'strengths', input.strengths);
  validateOptionalText(details, 'improvement_areas', input.improvement_areas);
  validateOptionalText(details, 'goals_next_period', input.goals_next_period);
  validateOptionalRating(details, input.overall_rating);

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}

export function validatePerformanceReviewStatus(status: PerformanceReviewStatus): void {
  if (!PERFORMANCE_REVIEW_STATUSES.includes(status)) {
    throw new ValidationError([
      { field: 'status', reason: `must be one of: ${PERFORMANCE_REVIEW_STATUSES.join(', ')}` },
    ]);
  }
}

export function validatePerformanceReviewFilters(filters: PerformanceReviewFilters): void {
  const details: Array<{ field: string; reason: string }> = [];

  if (filters.employee_id !== undefined && (typeof filters.employee_id !== 'string' || filters.employee_id.trim() === '')) {
    details.push({ field: 'employee_id', reason: 'must be a non-empty string when provided' });
  }

  if (filters.reviewer_employee_id !== undefined && (typeof filters.reviewer_employee_id !== 'string' || filters.reviewer_employee_id.trim() === '')) {
    details.push({ field: 'reviewer_employee_id', reason: 'must be a non-empty string when provided' });
  }

  if (filters.status !== undefined && !PERFORMANCE_REVIEW_STATUSES.includes(filters.status)) {
    details.push({
      field: 'status',
      reason: `must be one of: ${PERFORMANCE_REVIEW_STATUSES.join(', ')}`,
    });
  }

  if (filters.limit !== undefined && (!Number.isInteger(filters.limit) || filters.limit < 1 || filters.limit > 100)) {
    details.push({ field: 'limit', reason: 'must be an integer between 1 and 100' });
  }

  if (filters.cursor !== undefined && (typeof filters.cursor !== 'string' || filters.cursor.trim() === '')) {
    details.push({ field: 'cursor', reason: 'must be a non-empty string when provided' });
  }

  if (details.length > 0) {
    throw new ValidationError(details);
  }
}
