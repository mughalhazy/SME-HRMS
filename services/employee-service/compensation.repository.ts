import { randomUUID } from 'node:crypto';
import { CacheService } from '../../cache/cache.service';
import { ConnectionPool, PaginatedResult, QueryOptimizer, applyCursorPagination } from '../../db/optimization';
import { PersistentMap } from '../../db/persistent-map';
import { Department, Employee } from './employee.model';
import { DEFAULT_TENANT_ID } from './domain-seed';
import {
  Allowance,
  AllowanceFilters,
  BenefitsEnrollment,
  BenefitsEnrollmentFilters,
  BenefitsPlan,
  BenefitsPlanFilters,
  CompensationBand,
  CompensationBandFilters,
  CreateAllowanceInput,
  CreateBenefitsEnrollmentInput,
  CreateBenefitsPlanInput,
  CreateCompensationBandInput,
  CreateSalaryRevisionInput,
  EmployeeCompensationReadModel,
  PayrollCompensationContext,
  SalaryRevision,
  SalaryRevisionFilters,
  UpdateAllowanceInput,
  UpdateBenefitsEnrollmentInput,
  UpdateBenefitsPlanInput,
  UpdateCompensationBandInput,
  UpdateSalaryRevisionInput,
} from './compensation.model';
import { GradeBand } from './org.model';

const CACHE_PREFIX = 'employee-service:compensation';

type CompensationEntity = CompensationBand | SalaryRevision | BenefitsPlan | BenefitsEnrollment | Allowance;

export interface CompensationReferenceRepository {
  findEmployeeById(employeeId: string): Employee | null;
  findDepartmentById(departmentId: string): Department | null;
  findGradeBandById(gradeBandId: string): GradeBand | null;
}

export class CompensationRepository {
  private readonly compensationBands: PersistentMap<CompensationBand>;
  private readonly salaryRevisions: PersistentMap<SalaryRevision>;
  private readonly benefitsPlans: PersistentMap<BenefitsPlan>;
  private readonly benefitsEnrollments: PersistentMap<BenefitsEnrollment>;
  private readonly allowances: PersistentMap<Allowance>;
  private readonly cache = new CacheService({ ttlMs: 15_000, maxEntries: 2_000 });
  private readonly pool = new ConnectionPool(16);
  private readonly optimizer = new QueryOptimizer(10);

  constructor(
    private readonly referenceRepository: CompensationReferenceRepository,
    private readonly tenantId: string = DEFAULT_TENANT_ID,
  ) {
    this.compensationBands = new PersistentMap<CompensationBand>(`${CACHE_PREFIX}:bands:${tenantId}`);
    this.salaryRevisions = new PersistentMap<SalaryRevision>(`${CACHE_PREFIX}:salary-revisions:${tenantId}`);
    this.benefitsPlans = new PersistentMap<BenefitsPlan>(`${CACHE_PREFIX}:benefits-plans:${tenantId}`);
    this.benefitsEnrollments = new PersistentMap<BenefitsEnrollment>(`${CACHE_PREFIX}:benefits-enrollments:${tenantId}`);
    this.allowances = new PersistentMap<Allowance>(`${CACHE_PREFIX}:allowances:${tenantId}`);
  }

  createCompensationBand(input: CreateCompensationBandInput): CompensationBand {
    this.assertTenantFilter(input.tenant_id);
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'compensation_bands.create' }, () => {
      const timestamp = new Date().toISOString();
      const record: CompensationBand = {
        tenant_id: this.tenantId,
        compensation_band_id: randomUUID(),
        grade_band_id: input.grade_band_id,
        name: input.name,
        code: input.code,
        currency: input.currency ?? 'USD',
        min_salary: input.min_salary,
        max_salary: input.max_salary,
        target_salary: input.target_salary,
        status: input.status ?? 'Draft',
        created_at: timestamp,
        updated_at: timestamp,
      };
      this.compensationBands.set(record.compensation_band_id, record);
      this.invalidatePrefix('bands');
      return record;
    }));
  }

  findCompensationBandById(compensationBandId: string): CompensationBand | null {
    return this.cachedLookup('bands', compensationBandId, this.compensationBands, 'compensation_bands.findById');
  }

  findCompensationBandByCode(code: string): CompensationBand | null {
    return this.findOne(this.compensationBands.values(), (record) => record.code === code);
  }

  listCompensationBands(filters: CompensationBandFilters): PaginatedResult<CompensationBand> {
    this.assertTenantFilter(filters.tenant_id);
    return this.cachedList('bands', filters, 'compensation_bands.list', () => {
      const rows = this.compensationBands.values()
        .filter((record) => record.tenant_id === this.tenantId)
        .filter((record) => !filters.grade_band_id || record.grade_band_id === filters.grade_band_id)
        .filter((record) => !filters.status || record.status === filters.status)
        .sort((left, right) => this.sortByUpdated(left, right, left.compensation_band_id, right.compensation_band_id));
      return applyCursorPagination(rows as Array<{ employee_id: string; created_at: string }>, { limit: filters.limit, cursor: filters.cursor }) as unknown as PaginatedResult<CompensationBand>;
    });
  }

  updateCompensationBand(compensationBandId: string, input: UpdateCompensationBandInput): CompensationBand | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'compensation_bands.update' }, () => {
      const existing = this.findCompensationBandById(compensationBandId);
      if (!existing) {
        return null;
      }
      const updated: CompensationBand = {
        ...existing,
        ...input,
        tenant_id: this.tenantId,
        updated_at: new Date().toISOString(),
      };
      this.compensationBands.set(compensationBandId, updated);
      this.invalidateEntity('bands', compensationBandId);
      return updated;
    }));
  }

  createSalaryRevision(input: CreateSalaryRevisionInput): SalaryRevision {
    this.assertTenantFilter(input.tenant_id);
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'salary_revisions.create' }, () => {
      const timestamp = new Date().toISOString();
      const record: SalaryRevision = {
        tenant_id: this.tenantId,
        salary_revision_id: randomUUID(),
        employee_id: input.employee_id,
        compensation_band_id: input.compensation_band_id,
        effective_from: input.effective_from,
        effective_to: input.effective_to,
        base_salary: input.base_salary,
        currency: input.currency ?? 'USD',
        reason: input.reason,
        status: input.status ?? 'Approved',
        created_at: timestamp,
        updated_at: timestamp,
      };
      this.salaryRevisions.set(record.salary_revision_id, record);
      this.invalidatePrefix('salary-revisions');
      this.invalidatePrefix(`payroll-context:${record.employee_id}`);
      return record;
    }));
  }

  findSalaryRevisionById(salaryRevisionId: string): SalaryRevision | null {
    return this.cachedLookup('salary-revisions', salaryRevisionId, this.salaryRevisions, 'salary_revisions.findById');
  }

  listSalaryRevisions(filters: SalaryRevisionFilters): PaginatedResult<SalaryRevision> {
    this.assertTenantFilter(filters.tenant_id);
    return this.cachedList('salary-revisions', filters, 'salary_revisions.list', () => {
      const rows = this.salaryRevisions.values()
        .filter((record) => record.tenant_id === this.tenantId)
        .filter((record) => !filters.employee_id || record.employee_id === filters.employee_id)
        .filter((record) => !filters.compensation_band_id || record.compensation_band_id === filters.compensation_band_id)
        .filter((record) => !filters.status || record.status === filters.status)
        .sort((left, right) => this.sortByUpdated(left, right, left.salary_revision_id, right.salary_revision_id));
      return applyCursorPagination(rows as Array<{ employee_id: string; created_at: string }>, { limit: filters.limit, cursor: filters.cursor }) as unknown as PaginatedResult<SalaryRevision>;
    });
  }

  updateSalaryRevision(salaryRevisionId: string, input: UpdateSalaryRevisionInput): SalaryRevision | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'salary_revisions.update' }, () => {
      const existing = this.findSalaryRevisionById(salaryRevisionId);
      if (!existing) {
        return null;
      }
      const updated: SalaryRevision = {
        ...existing,
        ...input,
        tenant_id: this.tenantId,
        updated_at: new Date().toISOString(),
      };
      this.salaryRevisions.set(salaryRevisionId, updated);
      this.invalidateEntity('salary-revisions', salaryRevisionId);
      this.invalidatePrefix(`payroll-context:${updated.employee_id}`);
      return updated;
    }));
  }

  createBenefitsPlan(input: CreateBenefitsPlanInput): BenefitsPlan {
    this.assertTenantFilter(input.tenant_id);
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'benefits_plans.create' }, () => {
      const timestamp = new Date().toISOString();
      const record: BenefitsPlan = {
        tenant_id: this.tenantId,
        benefits_plan_id: randomUUID(),
        name: input.name,
        code: input.code,
        plan_type: input.plan_type,
        provider: input.provider,
        currency: input.currency ?? 'USD',
        employee_contribution_default: input.employee_contribution_default ?? '0.00',
        employer_contribution_default: input.employer_contribution_default ?? '0.00',
        payroll_deduction_code: input.payroll_deduction_code,
        status: input.status ?? 'Draft',
        created_at: timestamp,
        updated_at: timestamp,
      };
      this.benefitsPlans.set(record.benefits_plan_id, record);
      this.invalidatePrefix('benefits-plans');
      return record;
    }));
  }

  findBenefitsPlanById(benefitsPlanId: string): BenefitsPlan | null {
    return this.cachedLookup('benefits-plans', benefitsPlanId, this.benefitsPlans, 'benefits_plans.findById');
  }

  findBenefitsPlanByCode(code: string): BenefitsPlan | null {
    return this.findOne(this.benefitsPlans.values(), (record) => record.code === code);
  }

  listBenefitsPlans(filters: BenefitsPlanFilters): PaginatedResult<BenefitsPlan> {
    this.assertTenantFilter(filters.tenant_id);
    return this.cachedList('benefits-plans', filters, 'benefits_plans.list', () => {
      const rows = this.benefitsPlans.values()
        .filter((record) => record.tenant_id === this.tenantId)
        .filter((record) => !filters.plan_type || record.plan_type === filters.plan_type)
        .filter((record) => !filters.status || record.status === filters.status)
        .sort((left, right) => this.sortByUpdated(left, right, left.benefits_plan_id, right.benefits_plan_id));
      return applyCursorPagination(rows as Array<{ employee_id: string; created_at: string }>, { limit: filters.limit, cursor: filters.cursor }) as unknown as PaginatedResult<BenefitsPlan>;
    });
  }

  updateBenefitsPlan(benefitsPlanId: string, input: UpdateBenefitsPlanInput): BenefitsPlan | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'benefits_plans.update' }, () => {
      const existing = this.findBenefitsPlanById(benefitsPlanId);
      if (!existing) {
        return null;
      }
      const updated: BenefitsPlan = {
        ...existing,
        ...input,
        tenant_id: this.tenantId,
        updated_at: new Date().toISOString(),
      };
      this.benefitsPlans.set(benefitsPlanId, updated);
      this.invalidateEntity('benefits-plans', benefitsPlanId);
      this.invalidatePrefix('benefits-enrollments');
      return updated;
    }));
  }

  createBenefitsEnrollment(input: CreateBenefitsEnrollmentInput): BenefitsEnrollment {
    this.assertTenantFilter(input.tenant_id);
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'benefits_enrollments.create' }, () => {
      const timestamp = new Date().toISOString();
      const plan = this.findBenefitsPlanById(input.benefits_plan_id);
      const record: BenefitsEnrollment = {
        tenant_id: this.tenantId,
        benefits_enrollment_id: randomUUID(),
        employee_id: input.employee_id,
        benefits_plan_id: input.benefits_plan_id,
        effective_from: input.effective_from,
        effective_to: input.effective_to,
        coverage_level: input.coverage_level,
        employee_contribution: input.employee_contribution ?? plan?.employee_contribution_default ?? '0.00',
        employer_contribution: input.employer_contribution ?? plan?.employer_contribution_default ?? '0.00',
        status: input.status ?? 'Pending',
        created_at: timestamp,
        updated_at: timestamp,
      };
      this.benefitsEnrollments.set(record.benefits_enrollment_id, record);
      this.invalidatePrefix('benefits-enrollments');
      this.invalidatePrefix(`payroll-context:${record.employee_id}`);
      return record;
    }));
  }

  findBenefitsEnrollmentById(benefitsEnrollmentId: string): BenefitsEnrollment | null {
    return this.cachedLookup('benefits-enrollments', benefitsEnrollmentId, this.benefitsEnrollments, 'benefits_enrollments.findById');
  }

  listBenefitsEnrollments(filters: BenefitsEnrollmentFilters): PaginatedResult<BenefitsEnrollment> {
    this.assertTenantFilter(filters.tenant_id);
    return this.cachedList('benefits-enrollments', filters, 'benefits_enrollments.list', () => {
      const rows = this.benefitsEnrollments.values()
        .filter((record) => record.tenant_id === this.tenantId)
        .filter((record) => !filters.employee_id || record.employee_id === filters.employee_id)
        .filter((record) => !filters.benefits_plan_id || record.benefits_plan_id === filters.benefits_plan_id)
        .filter((record) => !filters.status || record.status === filters.status)
        .sort((left, right) => this.sortByUpdated(left, right, left.benefits_enrollment_id, right.benefits_enrollment_id));
      return applyCursorPagination(rows as Array<{ employee_id: string; created_at: string }>, { limit: filters.limit, cursor: filters.cursor }) as unknown as PaginatedResult<BenefitsEnrollment>;
    });
  }

  updateBenefitsEnrollment(benefitsEnrollmentId: string, input: UpdateBenefitsEnrollmentInput): BenefitsEnrollment | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'benefits_enrollments.update' }, () => {
      const existing = this.findBenefitsEnrollmentById(benefitsEnrollmentId);
      if (!existing) {
        return null;
      }
      const updated: BenefitsEnrollment = {
        ...existing,
        ...input,
        tenant_id: this.tenantId,
        updated_at: new Date().toISOString(),
      };
      this.benefitsEnrollments.set(benefitsEnrollmentId, updated);
      this.invalidateEntity('benefits-enrollments', benefitsEnrollmentId);
      this.invalidatePrefix(`payroll-context:${updated.employee_id}`);
      return updated;
    }));
  }

  createAllowance(input: CreateAllowanceInput): Allowance {
    this.assertTenantFilter(input.tenant_id);
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'allowances.create' }, () => {
      const timestamp = new Date().toISOString();
      const record: Allowance = {
        tenant_id: this.tenantId,
        allowance_id: randomUUID(),
        employee_id: input.employee_id,
        name: input.name,
        code: input.code,
        currency: input.currency ?? 'USD',
        amount: input.amount,
        taxable: input.taxable ?? true,
        recurring: input.recurring ?? true,
        effective_from: input.effective_from,
        effective_to: input.effective_to,
        status: input.status ?? 'Draft',
        created_at: timestamp,
        updated_at: timestamp,
      };
      this.allowances.set(record.allowance_id, record);
      this.invalidatePrefix('allowances');
      this.invalidatePrefix(`payroll-context:${record.employee_id}`);
      return record;
    }));
  }

  findAllowanceById(allowanceId: string): Allowance | null {
    return this.cachedLookup('allowances', allowanceId, this.allowances, 'allowances.findById');
  }

  listAllowances(filters: AllowanceFilters): PaginatedResult<Allowance> {
    this.assertTenantFilter(filters.tenant_id);
    return this.cachedList('allowances', filters, 'allowances.list', () => {
      const rows = this.allowances.values()
        .filter((record) => record.tenant_id === this.tenantId)
        .filter((record) => !filters.employee_id || record.employee_id === filters.employee_id)
        .filter((record) => !filters.status || record.status === filters.status)
        .sort((left, right) => this.sortByUpdated(left, right, left.allowance_id, right.allowance_id));
      return applyCursorPagination(rows as Array<{ employee_id: string; created_at: string }>, { limit: filters.limit, cursor: filters.cursor }) as unknown as PaginatedResult<Allowance>;
    });
  }

  updateAllowance(allowanceId: string, input: UpdateAllowanceInput): Allowance | null {
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation: 'allowances.update' }, () => {
      const existing = this.findAllowanceById(allowanceId);
      if (!existing) {
        return null;
      }
      const updated: Allowance = {
        ...existing,
        ...input,
        tenant_id: this.tenantId,
        updated_at: new Date().toISOString(),
      };
      this.allowances.set(allowanceId, updated);
      this.invalidateEntity('allowances', allowanceId);
      this.invalidatePrefix(`payroll-context:${updated.employee_id}`);
      return updated;
    }));
  }

  findActiveSalaryRevisionForDate(employeeId: string, effectiveDate: string): SalaryRevision | null {
    const eligible = this.salaryRevisions.values()
      .filter((record) => record.tenant_id === this.tenantId)
      .filter((record) => record.employee_id === employeeId)
      .filter((record) => record.status === 'Approved')
      .filter((record) => record.effective_from <= effectiveDate)
      .filter((record) => !record.effective_to || record.effective_to >= effectiveDate)
      .sort((left, right) => right.effective_from.localeCompare(left.effective_from) || right.created_at.localeCompare(left.created_at));
    return eligible[0] ?? null;
  }

  listEmployeeAllowancesForDate(employeeId: string, effectiveDate: string): Allowance[] {
    return this.allowances.values()
      .filter((record) => record.tenant_id === this.tenantId)
      .filter((record) => record.employee_id === employeeId)
      .filter((record) => record.status === 'Active')
      .filter((record) => record.effective_from <= effectiveDate)
      .filter((record) => !record.effective_to || record.effective_to >= effectiveDate)
      .sort((left, right) => left.code.localeCompare(right.code) || left.allowance_id.localeCompare(right.allowance_id));
  }

  listEmployeeBenefitsEnrollmentsForDate(employeeId: string, effectiveDate: string): BenefitsEnrollment[] {
    return this.benefitsEnrollments.values()
      .filter((record) => record.tenant_id === this.tenantId)
      .filter((record) => record.employee_id === employeeId)
      .filter((record) => record.status === 'Active')
      .filter((record) => record.effective_from <= effectiveDate)
      .filter((record) => !record.effective_to || record.effective_to >= effectiveDate)
      .sort((left, right) => left.benefits_enrollment_id.localeCompare(right.benefits_enrollment_id));
  }

  getEmployeeCompensationReadModel(employeeId: string, effectiveDate: string = new Date().toISOString().slice(0, 10)): EmployeeCompensationReadModel {
    const employee = this.referenceRepository.findEmployeeById(employeeId);
    const salaryRevision = this.findActiveSalaryRevisionForDate(employeeId, effectiveDate);
    const allowanceItems = this.listEmployeeAllowancesForDate(employeeId, effectiveDate);
    const benefitsEnrollments = this.listEmployeeBenefitsEnrollmentsForDate(employeeId, effectiveDate);
    const compensationBand = salaryRevision?.compensation_band_id ? this.findCompensationBandById(salaryRevision.compensation_band_id) : null;
    const department = employee ? this.referenceRepository.findDepartmentById(employee.department_id) : null;
    return {
      tenant_id: this.tenantId,
      employee_id: employeeId,
      employee_name: employee ? `${employee.first_name} ${employee.last_name}` : employeeId,
      department_id: employee?.department_id ?? 'unknown',
      department_name: department?.name ?? employee?.department_id ?? 'unknown',
      active_salary_revision_id: salaryRevision?.salary_revision_id,
      compensation_band_id: compensationBand?.compensation_band_id,
      compensation_band_name: compensationBand?.name,
      base_salary: salaryRevision?.base_salary,
      currency: salaryRevision?.currency,
      allowances_total: this.sumMoney(allowanceItems.map((item) => item.amount)),
      benefit_deductions_total: this.sumMoney(benefitsEnrollments.map((item) => item.employee_contribution)),
      active_benefits_count: benefitsEnrollments.length,
      active_allowances_count: allowanceItems.length,
      updated_at: this.latestTimestamp([salaryRevision, ...allowanceItems, ...benefitsEnrollments]),
    };
  }

  getPayrollCompensationContext(employeeId: string, effectiveDate: string = new Date().toISOString().slice(0, 10)): PayrollCompensationContext {
    const cacheKey = `${CACHE_PREFIX}:payroll-context:${this.tenantId}:${employeeId}:${effectiveDate}`;
    const cached = this.cache.get<PayrollCompensationContext>(cacheKey);
    if (cached) {
      return cached;
    }

    const salaryRevision = this.findActiveSalaryRevisionForDate(employeeId, effectiveDate);
    const allowanceItems = this.listEmployeeAllowancesForDate(employeeId, effectiveDate);
    const benefitsEnrollments = this.listEmployeeBenefitsEnrollmentsForDate(employeeId, effectiveDate);
    const context: PayrollCompensationContext = {
      tenant_id: this.tenantId,
      employee_id: employeeId,
      effective_from: salaryRevision?.effective_from ?? effectiveDate,
      base_salary: salaryRevision?.base_salary ?? '0.00',
      allowances: this.sumMoney(allowanceItems.map((item) => item.amount)),
      deductions: this.sumMoney(benefitsEnrollments.map((item) => item.employee_contribution)),
      currency: salaryRevision?.currency ?? 'USD',
      salary_revision_id: salaryRevision?.salary_revision_id,
      compensation_band_id: salaryRevision?.compensation_band_id,
      allowance_items: allowanceItems.map((allowance) => ({
        allowance_id: allowance.allowance_id,
        code: allowance.code,
        name: allowance.name,
        amount: allowance.amount,
        taxable: allowance.taxable,
        recurring: allowance.recurring,
      })),
      benefits_deductions: benefitsEnrollments.map((enrollment) => {
        const plan = this.findBenefitsPlanById(enrollment.benefits_plan_id);
        return {
          benefits_enrollment_id: enrollment.benefits_enrollment_id,
          benefits_plan_id: enrollment.benefits_plan_id,
          benefits_plan_code: plan?.code ?? enrollment.benefits_plan_id,
          benefits_plan_name: plan?.name ?? enrollment.benefits_plan_id,
          employee_contribution: enrollment.employee_contribution,
          employer_contribution: enrollment.employer_contribution,
        };
      }),
      updated_at: this.latestTimestamp([salaryRevision, ...allowanceItems, ...benefitsEnrollments]),
    };
    this.cache.set(cacheKey, context, { ttlMs: 10_000 });
    return context;
  }

  private cachedLookup<T extends CompensationEntity>(namespace: string, entityId: string, map: PersistentMap<T>, operation: string): T | null {
    const cacheKey = `${CACHE_PREFIX}:${namespace}:by-id:${this.tenantId}:${entityId}`;
    const cached = this.cache.get<T>(cacheKey);
    if (cached) {
      return cached;
    }
    return this.pool.runWithConnection(() => this.optimizer.execute({ operation }, () => {
      const value = map.get(entityId) ?? null;
      if (value && value.tenant_id === this.tenantId) {
        this.cache.set(cacheKey, value);
        return value;
      }
      return null;
    }));
  }

  private cachedList<T>(namespace: string, filters: object, operation: string, factory: () => PaginatedResult<T>): PaginatedResult<T> {
    const cacheKey = `${CACHE_PREFIX}:${namespace}:list:${this.tenantId}:${JSON.stringify(filters)}`;
    const cached = this.cache.get<PaginatedResult<T>>(cacheKey);
    if (cached) {
      return cached;
    }
    const value = this.pool.runWithConnection(() => this.optimizer.execute({ operation }, factory));
    this.cache.set(cacheKey, value, { ttlMs: 10_000 });
    return value;
  }

  private invalidateEntity(namespace: string, entityId: string): void {
    this.cache.invalidate(`${CACHE_PREFIX}:${namespace}:by-id:${this.tenantId}:${entityId}`);
    this.invalidatePrefix(namespace);
  }

  private invalidatePrefix(namespace: string): void {
    this.cache.invalidateByPrefix(`${CACHE_PREFIX}:${namespace}:`);
  }

  private findOne<T>(rows: T[], predicate: (row: T) => boolean): T | null {
    return rows.find(predicate) ?? null;
  }

  private sortByUpdated(left: { updated_at: string }, right: { updated_at: string }, leftId: string, rightId: string): number {
    if (left.updated_at === right.updated_at) {
      return rightId.localeCompare(leftId);
    }
    return right.updated_at.localeCompare(left.updated_at);
  }

  private sumMoney(values: string[]): string {
    const total = values.reduce((sum, value) => sum + Number(value), 0);
    return total.toFixed(2);
  }

  private latestTimestamp(rows: Array<{ updated_at: string } | null | undefined>): string {
    const latest = rows
      .filter((row): row is { updated_at: string } => Boolean(row?.updated_at))
      .sort((left, right) => right.updated_at.localeCompare(left.updated_at))[0];
    return latest?.updated_at ?? new Date(0).toISOString();
  }

  private assertTenantFilter(tenantId?: string): void {
    if (tenantId && tenantId !== this.tenantId) {
      throw new Error('cross_tenant_filter_blocked');
    }
  }
}
