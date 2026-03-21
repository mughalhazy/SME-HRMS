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
  PayrollCompensationContext,
  SalaryRevision,
  SalaryRevisionFilters,
  UpdateAllowanceInput,
  UpdateBenefitsEnrollmentInput,
  UpdateBenefitsPlanInput,
  UpdateCompensationBandInput,
  UpdateSalaryRevisionInput,
} from './compensation.model';
import { CompensationRepository } from './compensation.repository';
import {
  validateAllowanceFilters,
  validateBenefitsEnrollmentFilters,
  validateBenefitsPlanFilters,
  validateCompensationBandFilters,
  validateCreateAllowance,
  validateCreateBenefitsEnrollment,
  validateCreateBenefitsPlan,
  validateCreateCompensationBand,
  validateCreateSalaryRevision,
  validateSalaryRevisionFilters,
  validateUpdateAllowance,
  validateUpdateBenefitsEnrollment,
  validateUpdateBenefitsPlan,
  validateUpdateCompensationBand,
  validateUpdateSalaryRevision,
} from './compensation.validation';
import { EmployeeRepository } from './employee.repository';
import { EmployeeEventOutbox } from './event-outbox';
import { ValidationError } from './employee.validation';
import { ConflictError, NotFoundError } from './service.errors';

export class CompensationService {
  readonly eventOutbox = new EmployeeEventOutbox();

  constructor(
    private readonly repository: CompensationRepository,
    private readonly employeeRepository: EmployeeRepository,
  ) {}

  createCompensationBand(input: CreateCompensationBandInput): CompensationBand {
    validateCreateCompensationBand(input);
    this.requireActiveGradeBand(input.grade_band_id, 'grade_band_id');
    this.ensureUniqueCompensationBand(input.name, input.code);
    const band = this.repository.createCompensationBand(input);
    this.eventOutbox.enqueue('CompensationBandCreated', band.tenant_id, { ...band }, band.compensation_band_id);
    this.eventOutbox.dispatchPending();
    return band;
  }

  getCompensationBandById(compensationBandId: string): CompensationBand {
    const band = this.repository.findCompensationBandById(compensationBandId);
    if (!band) {
      throw new NotFoundError('compensation band not found');
    }
    return band;
  }

  listCompensationBands(filters: CompensationBandFilters) {
    validateCompensationBandFilters(filters);
    return this.repository.listCompensationBands(filters);
  }

  updateCompensationBand(compensationBandId: string, input: UpdateCompensationBandInput): CompensationBand {
    validateUpdateCompensationBand(input);
    const existing = this.getCompensationBandById(compensationBandId);
    const gradeBandId = input.grade_band_id ?? existing.grade_band_id;
    this.requireActiveGradeBand(gradeBandId, 'grade_band_id');
    this.ensureUniqueCompensationBand(input.name, input.code, compensationBandId);
    const minSalary = Number(input.min_salary ?? existing.min_salary);
    const maxSalary = Number(input.max_salary ?? existing.max_salary);
    if (maxSalary < minSalary) {
      throw new ValidationError([{ field: 'max_salary', reason: 'must be greater than or equal to min_salary' }]);
    }
    const updated = this.repository.updateCompensationBand(compensationBandId, input);
    if (!updated) {
      throw new NotFoundError('compensation band not found');
    }
    this.eventOutbox.enqueue('CompensationBandUpdated', updated.tenant_id, { ...updated }, updated.compensation_band_id);
    this.eventOutbox.dispatchPending();
    return updated;
  }

  createSalaryRevision(input: CreateSalaryRevisionInput): SalaryRevision {
    validateCreateSalaryRevision(input);
    this.requireEmployee(input.employee_id, 'employee_id');
    if (input.compensation_band_id) {
      const band = this.getCompensationBandById(input.compensation_band_id);
      if (band.status !== 'Active') {
        throw new ValidationError([{ field: 'compensation_band_id', reason: 'compensation band must be Active' }]);
      }
      if (band.currency !== (input.currency ?? 'USD')) {
        throw new ValidationError([{ field: 'currency', reason: 'must match compensation band currency' }]);
      }
      const baseSalary = Number(input.base_salary);
      if (baseSalary < Number(band.min_salary) || baseSalary > Number(band.max_salary)) {
        throw new ValidationError([{ field: 'base_salary', reason: 'must be within the assigned compensation band range' }]);
      }
    }
    this.ensureSalaryRevisionNoOverlap(input.employee_id, input.effective_from, input.effective_to);
    const revision = this.repository.createSalaryRevision(input);
    this.eventOutbox.enqueue('SalaryRevisionCreated', revision.tenant_id, { ...revision }, revision.salary_revision_id);
    this.eventOutbox.dispatchPending();
    return revision;
  }

  getSalaryRevisionById(salaryRevisionId: string): SalaryRevision {
    const revision = this.repository.findSalaryRevisionById(salaryRevisionId);
    if (!revision) {
      throw new NotFoundError('salary revision not found');
    }
    return revision;
  }

  listSalaryRevisions(filters: SalaryRevisionFilters) {
    validateSalaryRevisionFilters(filters);
    return this.repository.listSalaryRevisions(filters);
  }

  updateSalaryRevision(salaryRevisionId: string, input: UpdateSalaryRevisionInput): SalaryRevision {
    validateUpdateSalaryRevision(input);
    const existing = this.getSalaryRevisionById(salaryRevisionId);
    const employeeId = existing.employee_id;
    const effectiveFrom = input.effective_from ?? existing.effective_from;
    const effectiveTo = input.effective_to ?? existing.effective_to;
    const compensationBandId = input.compensation_band_id ?? existing.compensation_band_id;
    if (compensationBandId) {
      const band = this.getCompensationBandById(compensationBandId);
      if (band.status !== 'Active') {
        throw new ValidationError([{ field: 'compensation_band_id', reason: 'compensation band must be Active' }]);
      }
      const baseSalary = Number(input.base_salary ?? existing.base_salary);
      if (baseSalary < Number(band.min_salary) || baseSalary > Number(band.max_salary)) {
        throw new ValidationError([{ field: 'base_salary', reason: 'must be within the assigned compensation band range' }]);
      }
      if ((input.currency ?? existing.currency) !== band.currency) {
        throw new ValidationError([{ field: 'currency', reason: 'must match compensation band currency' }]);
      }
    }
    this.ensureSalaryRevisionNoOverlap(employeeId, effectiveFrom, effectiveTo, salaryRevisionId);
    const updated = this.repository.updateSalaryRevision(salaryRevisionId, input);
    if (!updated) {
      throw new NotFoundError('salary revision not found');
    }
    this.eventOutbox.enqueue('SalaryRevisionCreated', updated.tenant_id, { ...updated }, updated.salary_revision_id);
    this.eventOutbox.dispatchPending();
    return updated;
  }

  createBenefitsPlan(input: CreateBenefitsPlanInput): BenefitsPlan {
    validateCreateBenefitsPlan(input);
    this.ensureUniqueBenefitsPlan(input.name, input.code);
    const plan = this.repository.createBenefitsPlan(input);
    this.eventOutbox.enqueue('BenefitsPlanCreated', plan.tenant_id, { ...plan }, plan.benefits_plan_id);
    this.eventOutbox.dispatchPending();
    return plan;
  }

  getBenefitsPlanById(benefitsPlanId: string): BenefitsPlan {
    const plan = this.repository.findBenefitsPlanById(benefitsPlanId);
    if (!plan) {
      throw new NotFoundError('benefits plan not found');
    }
    return plan;
  }

  listBenefitsPlans(filters: BenefitsPlanFilters) {
    validateBenefitsPlanFilters(filters);
    return this.repository.listBenefitsPlans(filters);
  }

  updateBenefitsPlan(benefitsPlanId: string, input: UpdateBenefitsPlanInput): BenefitsPlan {
    validateUpdateBenefitsPlan(input);
    this.getBenefitsPlanById(benefitsPlanId);
    this.ensureUniqueBenefitsPlan(input.name, input.code, benefitsPlanId);
    const updated = this.repository.updateBenefitsPlan(benefitsPlanId, input);
    if (!updated) {
      throw new NotFoundError('benefits plan not found');
    }
    this.eventOutbox.enqueue('BenefitsPlanUpdated', updated.tenant_id, { ...updated }, updated.benefits_plan_id);
    this.eventOutbox.dispatchPending();
    return updated;
  }

  createBenefitsEnrollment(input: CreateBenefitsEnrollmentInput): BenefitsEnrollment {
    validateCreateBenefitsEnrollment(input);
    this.requireEmployee(input.employee_id, 'employee_id');
    const plan = this.getBenefitsPlanById(input.benefits_plan_id);
    if (plan.status !== 'Active') {
      throw new ValidationError([{ field: 'benefits_plan_id', reason: 'benefits plan must be Active' }]);
    }
    this.ensureBenefitsEnrollmentNoOverlap(input.employee_id, input.benefits_plan_id, input.effective_from, input.effective_to);
    const enrollment = this.repository.createBenefitsEnrollment(input);
    this.eventOutbox.enqueue('BenefitsEnrollmentCreated', enrollment.tenant_id, { ...enrollment }, enrollment.benefits_enrollment_id);
    this.eventOutbox.dispatchPending();
    return enrollment;
  }

  getBenefitsEnrollmentById(benefitsEnrollmentId: string): BenefitsEnrollment {
    const enrollment = this.repository.findBenefitsEnrollmentById(benefitsEnrollmentId);
    if (!enrollment) {
      throw new NotFoundError('benefits enrollment not found');
    }
    return enrollment;
  }

  listBenefitsEnrollments(filters: BenefitsEnrollmentFilters) {
    validateBenefitsEnrollmentFilters(filters);
    return this.repository.listBenefitsEnrollments(filters);
  }

  updateBenefitsEnrollment(benefitsEnrollmentId: string, input: UpdateBenefitsEnrollmentInput): BenefitsEnrollment {
    validateUpdateBenefitsEnrollment(input);
    const existing = this.getBenefitsEnrollmentById(benefitsEnrollmentId);
    const effectiveFrom = input.effective_from ?? existing.effective_from;
    const effectiveTo = input.effective_to ?? existing.effective_to;
    this.ensureBenefitsEnrollmentNoOverlap(existing.employee_id, existing.benefits_plan_id, effectiveFrom, effectiveTo, benefitsEnrollmentId);
    const updated = this.repository.updateBenefitsEnrollment(benefitsEnrollmentId, input);
    if (!updated) {
      throw new NotFoundError('benefits enrollment not found');
    }
    this.eventOutbox.enqueue('BenefitsEnrollmentCreated', updated.tenant_id, { ...updated }, updated.benefits_enrollment_id);
    this.eventOutbox.dispatchPending();
    return updated;
  }

  createAllowance(input: CreateAllowanceInput): Allowance {
    validateCreateAllowance(input);
    this.requireEmployee(input.employee_id, 'employee_id');
    this.ensureAllowanceCodeUniquePerEmployee(input.employee_id, input.code);
    const allowance = this.repository.createAllowance(input);
    this.eventOutbox.enqueue('AllowanceCreated', allowance.tenant_id, { ...allowance }, allowance.allowance_id);
    this.eventOutbox.dispatchPending();
    return allowance;
  }

  getAllowanceById(allowanceId: string): Allowance {
    const allowance = this.repository.findAllowanceById(allowanceId);
    if (!allowance) {
      throw new NotFoundError('allowance not found');
    }
    return allowance;
  }

  listAllowances(filters: AllowanceFilters) {
    validateAllowanceFilters(filters);
    return this.repository.listAllowances(filters);
  }

  updateAllowance(allowanceId: string, input: UpdateAllowanceInput): Allowance {
    validateUpdateAllowance(input);
    const existing = this.getAllowanceById(allowanceId);
    this.ensureAllowanceCodeUniquePerEmployee(existing.employee_id, input.code ?? existing.code, allowanceId);
    const updated = this.repository.updateAllowance(allowanceId, input);
    if (!updated) {
      throw new NotFoundError('allowance not found');
    }
    this.eventOutbox.enqueue('AllowanceUpdated', updated.tenant_id, { ...updated }, updated.allowance_id);
    this.eventOutbox.dispatchPending();
    return updated;
  }

  getEmployeePayrollCompensationContext(employeeId: string, effectiveDate?: string): PayrollCompensationContext {
    this.requireEmployee(employeeId, 'employee_id');
    return this.repository.getPayrollCompensationContext(employeeId, effectiveDate);
  }

  getEmployeeCompensationReadModel(employeeId: string, effectiveDate?: string) {
    this.requireEmployee(employeeId, 'employee_id');
    return this.repository.getEmployeeCompensationReadModel(employeeId, effectiveDate);
  }

  private ensureUniqueCompensationBand(name?: string, code?: string, compensationBandId?: string): void {
    if (name) {
      const duplicateName = this.repository.listCompensationBands({ limit: 100 }).data.find((item) => item.name === name && item.compensation_band_id !== compensationBandId);
      if (duplicateName) {
        throw new ConflictError('compensation band name already exists');
      }
    }
    if (code) {
      const duplicateCode = this.repository.findCompensationBandByCode(code);
      if (duplicateCode && duplicateCode.compensation_band_id !== compensationBandId) {
        throw new ConflictError('compensation band code already exists');
      }
    }
  }

  private ensureUniqueBenefitsPlan(name?: string, code?: string, benefitsPlanId?: string): void {
    if (name) {
      const duplicateName = this.repository.listBenefitsPlans({ limit: 100 }).data.find((item) => item.name === name && item.benefits_plan_id !== benefitsPlanId);
      if (duplicateName) {
        throw new ConflictError('benefits plan name already exists');
      }
    }
    if (code) {
      const duplicateCode = this.repository.findBenefitsPlanByCode(code);
      if (duplicateCode && duplicateCode.benefits_plan_id !== benefitsPlanId) {
        throw new ConflictError('benefits plan code already exists');
      }
    }
  }

  private ensureAllowanceCodeUniquePerEmployee(employeeId: string, code: string, allowanceId?: string): void {
    const duplicate = this.repository.listAllowances({ employee_id: employeeId, limit: 100 }).data.find((item) => item.code === code && item.allowance_id !== allowanceId);
    if (duplicate) {
      throw new ConflictError('allowance code already exists for employee');
    }
  }

  private ensureSalaryRevisionNoOverlap(employeeId: string, effectiveFrom: string, effectiveTo?: string, salaryRevisionId?: string): void {
    const overlapping = this.repository.listSalaryRevisions({ employee_id: employeeId, limit: 100 }).data.find((revision) => {
      if (salaryRevisionId && revision.salary_revision_id === salaryRevisionId) {
        return false;
      }
      return this.dateRangesOverlap(effectiveFrom, effectiveTo, revision.effective_from, revision.effective_to)
        && revision.status !== 'Superseded';
    });
    if (overlapping) {
      throw new ConflictError('salary revision overlaps an existing effective window');
    }
  }

  private ensureBenefitsEnrollmentNoOverlap(employeeId: string, benefitsPlanId: string, effectiveFrom: string, effectiveTo?: string, benefitsEnrollmentId?: string): void {
    const overlapping = this.repository.listBenefitsEnrollments({ employee_id: employeeId, benefits_plan_id: benefitsPlanId, limit: 100 }).data.find((enrollment) => {
      if (benefitsEnrollmentId && enrollment.benefits_enrollment_id === benefitsEnrollmentId) {
        return false;
      }
      return this.dateRangesOverlap(effectiveFrom, effectiveTo, enrollment.effective_from, enrollment.effective_to)
        && enrollment.status !== 'Cancelled'
        && enrollment.status !== 'Ended';
    });
    if (overlapping) {
      throw new ConflictError('benefits enrollment overlaps an existing effective window');
    }
  }

  private dateRangesOverlap(startA: string, endA: string | undefined, startB: string, endB: string | undefined): boolean {
    const normalizedEndA = endA ?? '9999-12-31';
    const normalizedEndB = endB ?? '9999-12-31';
    return startA <= normalizedEndB && startB <= normalizedEndA;
  }

  private requireEmployee(employeeId: string, field: string): void {
    const employee = this.employeeRepository.findById(employeeId);
    if (!employee) {
      throw new ValidationError([{ field, reason: 'employee was not found' }]);
    }
    if (employee.status === 'Terminated') {
      throw new ValidationError([{ field, reason: 'employee cannot be Terminated' }]);
    }
  }

  private requireActiveGradeBand(gradeBandId: string, field: string): void {
    const gradeBand = this.employeeRepository.findGradeBandById(gradeBandId);
    if (!gradeBand) {
      throw new ValidationError([{ field, reason: 'grade band was not found' }]);
    }
    if (gradeBand.status !== 'Active') {
      throw new ValidationError([{ field, reason: 'grade band must be Active' }]);
    }
  }
}
