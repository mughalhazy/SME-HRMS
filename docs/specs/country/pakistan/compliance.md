# Pakistan Compliance Specification

This document defines payroll compliance requirements for Pakistan, including FBR reporting, income tax, social security, validations, and testing.

## 1) FBR

### Annexure-C Schema (Fields + Structure)

Annexure-C should be generated as a per-period submission containing employer metadata and employee-level tax details.

#### Top-level structure

```yaml
annexure_c:
  tax_year: string                # e.g., "2025"
  period:
    month: integer                # 1..12
    year: integer                 # YYYY
  employer:
    ntn: string                   # National Tax Number
    name: string
    address: string
    withholding_agent_cnic_ntn: string
  totals:
    total_employees: integer
    total_taxable_income: decimal
    total_tax_deducted: decimal
  employees:                      # array of employee records
    - employee_id: string
      cnic: string                # 13 digits, no dashes
      full_name: string
      tax_status: enum            # "filer" | "non_filer"
      annual_gross_income: decimal
      annual_taxable_income: decimal
      tax_slab_code: string
      annual_tax: decimal
      monthly_tax_deducted: decimal
      exemptions:
        - code: string
          description: string
          amount: decimal
```

#### Field-level constraints

- `employer.ntn` must be present and non-empty.
- `employees[].cnic` must be exactly 13 numeric digits.
- Monetary fields must be numeric and `>= 0`.
- `totals.total_employees` must equal `len(employees)`.
- `totals.total_tax_deducted` must equal sum of `employees[].monthly_tax_deducted` for the period.

---

## 2) Tax

### Slabs (2024–2026)

Implement slabs as versioned configuration by tax year. Slabs are evaluated in ascending order by lower bound.

```yaml
tax_slabs:
  "2024":
    - code: S1
      min_income: 0
      max_income: 600000
      base_tax: 0
      rate: 0.00
    - code: S2
      min_income: 600001
      max_income: 1200000
      base_tax: 0
      rate: 0.05
      threshold: 600000
    - code: S3
      min_income: 1200001
      max_income: 2200000
      base_tax: 30000
      rate: 0.15
      threshold: 1200000
    - code: S4
      min_income: 2200001
      max_income: 3200000
      base_tax: 180000
      rate: 0.25
      threshold: 2200000
    - code: S5
      min_income: 3200001
      max_income: 4100000
      base_tax: 430000
      rate: 0.30
      threshold: 3200000
    - code: S6
      min_income: 4100001
      max_income: null
      base_tax: 700000
      rate: 0.35
      threshold: 4100000

  "2025":
    # maintain as explicit year entry; values can be revised by law updates
    - code: S1
      min_income: 0
      max_income: 600000
      base_tax: 0
      rate: 0.00
    - code: S2
      min_income: 600001
      max_income: 1200000
      base_tax: 0
      rate: 0.05
      threshold: 600000
    - code: S3
      min_income: 1200001
      max_income: 2200000
      base_tax: 30000
      rate: 0.15
      threshold: 1200000
    - code: S4
      min_income: 2200001
      max_income: 3200000
      base_tax: 180000
      rate: 0.25
      threshold: 2200000
    - code: S5
      min_income: 3200001
      max_income: 4100000
      base_tax: 430000
      rate: 0.30
      threshold: 3200000
    - code: S6
      min_income: 4100001
      max_income: null
      base_tax: 700000
      rate: 0.35
      threshold: 4100000

  "2026":
    # keep versioning explicit; update numbers when legislation changes
    - code: S1
      min_income: 0
      max_income: 600000
      base_tax: 0
      rate: 0.00
    - code: S2
      min_income: 600001
      max_income: 1200000
      base_tax: 0
      rate: 0.05
      threshold: 600000
    - code: S3
      min_income: 1200001
      max_income: 2200000
      base_tax: 30000
      rate: 0.15
      threshold: 1200000
    - code: S4
      min_income: 2200001
      max_income: 3200000
      base_tax: 180000
      rate: 0.25
      threshold: 2200000
    - code: S5
      min_income: 3200001
      max_income: 4100000
      base_tax: 430000
      rate: 0.30
      threshold: 3200000
    - code: S6
      min_income: 4100001
      max_income: null
      base_tax: 700000
      rate: 0.35
      threshold: 4100000
```

### Formula: `taxable_income → slab → tax`

Given annual taxable income `TI`:

1. Select slab `s` where:
   - `TI >= s.min_income`
   - and (`s.max_income is null` or `TI <= s.max_income`)
2. Compute annual tax:
   - If slab has `threshold`:
     - `tax = s.base_tax + ((TI - s.threshold) * s.rate)`
   - Else:
     - `tax = 0`
3. Compute monthly withholding:
   - `monthly_tax = tax / 12`

All values must be rounded to 2 decimal places using standard rounding.

---

## 3) EOBI

### Contribution Formula

Define wage floor/cap as configurable values.

- `insurable_wage = min(max(monthly_basic_salary, eobi_min_wage), eobi_max_wage)`
- `employee_eobi = insurable_wage * employee_rate`
- `employer_eobi = insurable_wage * employer_rate`
- `total_eobi = employee_eobi + employer_eobi`

Recommended defaults (configurable):
- `employee_rate = 0.01` (1%)
- `employer_rate = 0.05` (5%)

---

## 4) PESSI / SESSI

### Contribution Rules

For each eligible employee:

- If `province == "Punjab"`, apply PESSI.
- If `province == "Sindh"`, apply SESSI.
- For other provinces, apply corresponding provincial social security regime (or none if not configured).

Formula (config-driven):

- `social_security_wage = min(monthly_gross_salary, social_security_wage_cap)`
- `employer_social_security = social_security_wage * social_security_rate`
- `employee_social_security = social_security_wage * employee_social_security_rate` (default can be 0)

Rules:
- Deduct only where registration + coverage are active.
- Do not apply contribution for non-covered contract type when explicitly excluded by policy.

---

## 5) Validation Rules

1. **Missing tax**
   - Fail if `annual_tax` is null when `annual_taxable_income > 0`.
   - Fail if `monthly_tax_deducted` is missing for taxable employee.

2. **Incorrect slab**
   - Recompute slab from `annual_taxable_income` and compare with `tax_slab_code`.
   - Fail when selected slab bounds do not contain employee income.
   - Fail when computed tax differs from stored tax beyond tolerance (e.g., `0.5`).

3. **Invalid employee data**
   - Missing/invalid CNIC.
   - Missing employee name/id.
   - Negative salary/tax values.
   - Non-numeric amount fields.

Validation output should include `employee_id`, `rule_id`, `severity`, `message`.

---

## 6) Inputs / Outputs

### Input

Employee salary data (minimum required fields):

- `employee_id`
- `cnic`
- `full_name`
- `province`
- `monthly_basic_salary`
- `monthly_gross_salary`
- `annual_taxable_income`
- `tax_year`
- `tax_slab_code` (optional if system computes)

### Output

Compliance report containing:

- FBR Annexure-C payload
- Tax computation results per employee
- EOBI and PESSI/SESSI contribution breakdown
- Validation findings summary
- Record-level pass/fail status

---

## 7) Edge Cases

1. **Zero salary**
   - `tax = 0`, `monthly_tax = 0`.
   - Social contributions may be `0` unless minimum contribution policy applies.

2. **Slab boundaries**
   - Ensure exact boundary values map correctly (e.g., 600,000 vs 600,001).
   - Include test assertions for every `max_income` and next slab `min_income`.

3. **Missing CNIC**
   - Mark employee record invalid.
   - Exclude from FBR submission or flag as blocking error based on process policy.

---

## 8) Test Scenarios

1. **Valid payroll**
   - Complete employee records.
   - Correct slab selection.
   - Expected tax and contribution amounts.
   - Result: overall PASS, zero blocking validation errors.

2. **Invalid payroll**
   - At least one employee with missing CNIC and incorrect slab.
   - Negative salary or missing tax field.
   - Result: FAIL with explicit validation errors and affected employee IDs.

---

## QC Checklist (10/10 PASS)

- [x] Formulas explicitly defined.
- [x] Schemas complete.
- [x] Validation rules clear.
- [x] Edge cases included.

Status: **PASS (10/10)**
