export const COMPENSATION_BAND_STATUSES = ['Draft', 'Active', 'Inactive', 'Archived'] as const;
export type CompensationBandStatus = (typeof COMPENSATION_BAND_STATUSES)[number];

export const SALARY_REVISION_STATUSES = ['Draft', 'Approved', 'Superseded'] as const;
export type SalaryRevisionStatus = (typeof SALARY_REVISION_STATUSES)[number];

export const BENEFITS_PLAN_TYPES = ['Health', 'Retirement', 'Insurance', 'Wellness', 'Other'] as const;
export type BenefitsPlanType = (typeof BENEFITS_PLAN_TYPES)[number];

export const BENEFITS_PLAN_STATUSES = ['Draft', 'Active', 'Inactive', 'Archived'] as const;
export type BenefitsPlanStatus = (typeof BENEFITS_PLAN_STATUSES)[number];

export const BENEFITS_ENROLLMENT_STATUSES = ['Pending', 'Active', 'Cancelled', 'Ended'] as const;
export type BenefitsEnrollmentStatus = (typeof BENEFITS_ENROLLMENT_STATUSES)[number];

export const ALLOWANCE_STATUSES = ['Draft', 'Active', 'Inactive'] as const;
export type AllowanceStatus = (typeof ALLOWANCE_STATUSES)[number];

export interface CompensationBand {
  tenant_id: string;
  compensation_band_id: string;
  grade_band_id: string;
  name: string;
  code: string;
  currency: string;
  min_salary: string;
  max_salary: string;
  target_salary?: string;
  status: CompensationBandStatus;
  created_at: string;
  updated_at: string;
}

export interface SalaryRevision {
  tenant_id: string;
  salary_revision_id: string;
  employee_id: string;
  compensation_band_id?: string;
  effective_from: string;
  effective_to?: string;
  base_salary: string;
  currency: string;
  reason?: string;
  status: SalaryRevisionStatus;
  created_at: string;
  updated_at: string;
}

export interface BenefitsPlan {
  tenant_id: string;
  benefits_plan_id: string;
  name: string;
  code: string;
  plan_type: BenefitsPlanType;
  provider?: string;
  currency: string;
  employee_contribution_default: string;
  employer_contribution_default: string;
  payroll_deduction_code?: string;
  status: BenefitsPlanStatus;
  created_at: string;
  updated_at: string;
}

export interface BenefitsEnrollment {
  tenant_id: string;
  benefits_enrollment_id: string;
  employee_id: string;
  benefits_plan_id: string;
  effective_from: string;
  effective_to?: string;
  coverage_level?: string;
  employee_contribution: string;
  employer_contribution: string;
  status: BenefitsEnrollmentStatus;
  created_at: string;
  updated_at: string;
}

export interface Allowance {
  tenant_id: string;
  allowance_id: string;
  employee_id: string;
  name: string;
  code: string;
  currency: string;
  amount: string;
  taxable: boolean;
  recurring: boolean;
  effective_from: string;
  effective_to?: string;
  status: AllowanceStatus;
  created_at: string;
  updated_at: string;
}

export interface EmployeeCompensationReadModel {
  tenant_id: string;
  employee_id: string;
  employee_name: string;
  department_id: string;
  department_name: string;
  active_salary_revision_id?: string;
  compensation_band_id?: string;
  compensation_band_name?: string;
  base_salary?: string;
  currency?: string;
  allowances_total: string;
  benefit_deductions_total: string;
  active_benefits_count: number;
  active_allowances_count: number;
  updated_at: string;
}

export interface PayrollCompensationContext {
  tenant_id: string;
  employee_id: string;
  effective_from: string;
  base_salary: string;
  allowances: string;
  deductions: string;
  currency: string;
  salary_revision_id?: string;
  compensation_band_id?: string;
  allowance_items: Array<{
    allowance_id: string;
    code: string;
    name: string;
    amount: string;
    taxable: boolean;
    recurring: boolean;
  }>;
  benefits_deductions: Array<{
    benefits_enrollment_id: string;
    benefits_plan_id: string;
    benefits_plan_code: string;
    benefits_plan_name: string;
    employee_contribution: string;
    employer_contribution: string;
  }>;
  updated_at: string;
}


export interface WorkforcePlanDepartmentInput {
  department_id: string;
  planned_headcount: number;
  compensation_band_id?: string;
  average_base_salary?: string;
  average_allowances?: string;
  average_deductions?: string;
  average_employer_contributions?: string;
}

export interface WorkforcePlanScenarioInput {
  effective_date: string;
  forecast_months?: number;
  departments: WorkforcePlanDepartmentInput[];
}

export interface WorkforcePlanDepartmentForecast {
  department_id: string;
  department_name: string;
  current_headcount: number;
  planned_headcount: number;
  required_hires: number;
  overstaffed_headcount: number;
  monthly_base_salary: string;
  monthly_allowances: string;
  monthly_employee_deductions: string;
  monthly_employer_contributions: string;
  monthly_payroll_cost: string;
  forecast_payroll_cost: string;
}

export interface WorkforcePlanForecast {
  tenant_id: string;
  effective_date: string;
  forecast_months: number;
  headcount_plan: {
    current_headcount: number;
    planned_headcount: number;
    required_hires: number;
    overstaffed_headcount: number;
  };
  salary_forecast: {
    monthly_base_salary: string;
    monthly_allowances: string;
    monthly_employee_deductions: string;
    monthly_employer_contributions: string;
    monthly_payroll_cost: string;
    forecast_payroll_cost: string;
  };
  department_budgets: WorkforcePlanDepartmentForecast[];
  generated_at: string;
}

export interface CreateCompensationBandInput {
  tenant_id?: string;
  grade_band_id: string;
  name: string;
  code: string;
  currency?: string;
  min_salary: string;
  max_salary: string;
  target_salary?: string;
  status?: CompensationBandStatus;
}

export interface UpdateCompensationBandInput {
  grade_band_id?: string;
  name?: string;
  code?: string;
  currency?: string;
  min_salary?: string;
  max_salary?: string;
  target_salary?: string;
  status?: CompensationBandStatus;
}

export interface CompensationBandFilters {
  tenant_id?: string;
  grade_band_id?: string;
  status?: CompensationBandStatus;
  limit?: number;
  cursor?: string;
}

export interface CreateSalaryRevisionInput {
  tenant_id?: string;
  employee_id: string;
  compensation_band_id?: string;
  effective_from: string;
  effective_to?: string;
  base_salary: string;
  currency?: string;
  reason?: string;
  status?: SalaryRevisionStatus;
}

export interface UpdateSalaryRevisionInput {
  compensation_band_id?: string;
  effective_from?: string;
  effective_to?: string;
  base_salary?: string;
  currency?: string;
  reason?: string;
  status?: SalaryRevisionStatus;
}

export interface SalaryRevisionFilters {
  tenant_id?: string;
  employee_id?: string;
  compensation_band_id?: string;
  status?: SalaryRevisionStatus;
  limit?: number;
  cursor?: string;
}

export interface CreateBenefitsPlanInput {
  tenant_id?: string;
  name: string;
  code: string;
  plan_type: BenefitsPlanType;
  provider?: string;
  currency?: string;
  employee_contribution_default?: string;
  employer_contribution_default?: string;
  payroll_deduction_code?: string;
  status?: BenefitsPlanStatus;
}

export interface UpdateBenefitsPlanInput {
  name?: string;
  code?: string;
  plan_type?: BenefitsPlanType;
  provider?: string;
  currency?: string;
  employee_contribution_default?: string;
  employer_contribution_default?: string;
  payroll_deduction_code?: string;
  status?: BenefitsPlanStatus;
}

export interface BenefitsPlanFilters {
  tenant_id?: string;
  plan_type?: BenefitsPlanType;
  status?: BenefitsPlanStatus;
  limit?: number;
  cursor?: string;
}

export interface CreateBenefitsEnrollmentInput {
  tenant_id?: string;
  employee_id: string;
  benefits_plan_id: string;
  effective_from: string;
  effective_to?: string;
  coverage_level?: string;
  employee_contribution?: string;
  employer_contribution?: string;
  status?: BenefitsEnrollmentStatus;
}

export interface UpdateBenefitsEnrollmentInput {
  effective_from?: string;
  effective_to?: string;
  coverage_level?: string;
  employee_contribution?: string;
  employer_contribution?: string;
  status?: BenefitsEnrollmentStatus;
}

export interface BenefitsEnrollmentFilters {
  tenant_id?: string;
  employee_id?: string;
  benefits_plan_id?: string;
  status?: BenefitsEnrollmentStatus;
  limit?: number;
  cursor?: string;
}

export interface CreateAllowanceInput {
  tenant_id?: string;
  employee_id: string;
  name: string;
  code: string;
  currency?: string;
  amount: string;
  taxable?: boolean;
  recurring?: boolean;
  effective_from: string;
  effective_to?: string;
  status?: AllowanceStatus;
}

export interface UpdateAllowanceInput {
  name?: string;
  code?: string;
  currency?: string;
  amount?: string;
  taxable?: boolean;
  recurring?: boolean;
  effective_from?: string;
  effective_to?: string;
  status?: AllowanceStatus;
}

export interface AllowanceFilters {
  tenant_id?: string;
  employee_id?: string;
  status?: AllowanceStatus;
  limit?: number;
  cursor?: string;
}
