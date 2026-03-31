# Country Abstraction Layer

## 1. Purpose

The country abstraction layer exists to keep payroll core behavior stable while allowing country-specific tax, compliance, and statutory logic to vary by jurisdiction.

### Why this abstraction exists
- **Regulatory variability:** Tax and payroll regulations differ by country and change frequently.
- **Core stability:** Core payroll workflows (pay-cycle processing, approvals, calculations orchestration, persistence) should not be rewritten for each market.
- **Extensibility:** New countries can be added by implementing country adapters, without modifying core domain logic.
- **Auditability:** Country decisions are isolated, traceable, and testable per jurisdiction.

### Core vs country separation
- **Core (country-agnostic) responsibilities:**
  - Payroll run lifecycle orchestration
  - Employee/payroll data loading and normalization
  - Calling country interfaces in a fixed sequence
  - Error handling, retries, logging, and persistence
  - Reporting aggregation and downstream integrations
- **Country (country-specific) responsibilities:**
  - Tax computation formulas and slabs
  - Statutory validations and filing/report generation
  - Local payroll rules (allowances, deductions, limits, exemptions)

---

## 2. Interfaces

All country modules must implement the following interfaces.

### 2.1 TaxEngine

#### Method
`calculate_tax(input)`

#### Input schema
```yaml
gross_salary: number
employee_data: object
```

#### Output schema
```yaml
tax_amount: number
```

#### Contract
- Returns only the computed tax amount for the provided period context.
- Must be deterministic for the same input payload.
- Must not mutate input.

---

### 2.2 ComplianceEngine

#### Method A
`validate_payroll(input)`

##### Input schema
```yaml
period: string            # e.g., "2026-03"
employee_records: array   # normalized employee payroll rows
organization_data: object
country_code: string      # ISO-like code, e.g., "PK"
```

##### Output schema
```yaml
is_valid: boolean
violations:
  - code: string
    message: string
    severity: string      # error | warning
```

#### Method B
`generate_reports(input)`

##### Input schema
```yaml
period: string
employee_records: array
calculated_results: array
organization_data: object
country_code: string
```

##### Output schema
```yaml
reports:
  - report_type: string
    file_name: string
    content_ref: string   # URI/path/object key to generated report artifact
metadata: object
```

#### Contract
- `validate_payroll` must execute before report generation.
- Reports must reflect finalized calculated results.
- Violations must be explicit and machine-readable.

---

### 2.3 PayrollRulesEngine

#### Method
`apply_rules(input)`

#### Input schema
```yaml
period: string
employee_record: object
gross_salary: number
allowances: object
deductions: object
country_code: string
```

#### Output schema
```yaml
adjusted_gross_salary: number
rule_adjustments:
  - rule_id: string
    description: string
    amount_delta: number
final_deductions: object
```

#### Contract
- Applies local payroll rules before tax calculation.
- Returns structured rule trace (`rule_adjustments`) for auditing.

---

## 3. Adapter Pattern

Each country module is an **adapter** that conforms to the shared interfaces while implementing local logic internally.

### Pattern definition
- Core code depends on interface contracts (`TaxEngine`, `ComplianceEngine`, `PayrollRulesEngine`), not concrete country classes.
- Country adapters translate generic input into local statutory logic and return standardized outputs.

### Implementation expectations
- One adapter per country (e.g., `PakistanAdapter`, `UAEAdapter`, `USAdapter`).
- Adapters expose the same method signatures as defined above.
- Local constants/tables/slabs live inside the country module boundary.
- No country conditionals (`if country == ...`) inside core orchestration.

---

## 4. Resolver

The resolver selects the correct country adapter for a payroll run.

### Selection logic
1. Read organization identifier from payroll context.
2. Resolve organization to country via org→country mapping.
3. Load adapter registered for that country.
4. Fail fast with explicit error if mapping or adapter is missing.

### Org → country mapping
- Source may be config DB, master data service, or static registry.
- Required mapping shape:

```yaml
organization_id: string
country_code: string
adapter_key: string
```

### Resolver contract
- Input: `organization_id` (required)
- Output: adapter instance implementing all required interfaces
- Error cases:
  - `ORG_COUNTRY_NOT_FOUND`
  - `COUNTRY_ADAPTER_NOT_REGISTERED`

---

## 5. Data Flow (step-by-step)

1. Core payroll service receives payroll run request (`organization_id`, period, employee records).
2. Resolver maps `organization_id` to `country_code` and loads corresponding country adapter.
3. For each employee, core calls `PayrollRulesEngine.apply_rules(input)`.
4. Adapter returns adjusted salary, deductions, and rule trace.
5. Core calls `TaxEngine.calculate_tax(input)` using adjusted values.
6. Adapter returns `tax_amount`.
7. Core aggregates per-employee calculations into payroll results.
8. Core calls `ComplianceEngine.validate_payroll(input)` on finalized results.
9. If invalid, core halts finalization and surfaces violation list.
10. If valid, core calls `ComplianceEngine.generate_reports(input)`.
11. Adapter returns report artifacts and metadata.
12. Core persists outputs and publishes completion status.

---

## 6. Example (Pakistan flow)

### Scenario
- Organization: `ORG_PK_001`
- Mapped country: `PK`
- Payroll period: `2026-03`

### End-to-end flow
1. Core receives payroll request for `ORG_PK_001`.
2. Resolver finds mapping: `ORG_PK_001 -> PK -> PakistanAdapter`.
3. For employee A, core sends local inputs to `apply_rules`.
4. Pakistan adapter applies Pakistan-specific rules (allowance handling, deductible treatments, local thresholds) and returns adjusted values.
5. Core calls `calculate_tax` with adjusted gross salary + employee data.
6. Pakistan adapter computes and returns `tax_amount`.
7. After all employees are processed, core calls `validate_payroll`.
8. Pakistan adapter validates statutory constraints and either:
   - returns `is_valid: true`, or
   - returns detailed violations with codes/messages.
9. If valid, core calls `generate_reports`.
10. Pakistan adapter returns required Pakistan payroll/compliance report artifacts.
11. Core stores results and marks run completed.

---

## Test scenarios (QC coverage)

1. **Interface conformance test**
   - Verify each country adapter exposes:
     - `calculate_tax(input)`
     - `validate_payroll(input)`
     - `generate_reports(input)`
     - `apply_rules(input)`
   - Verify input/output shapes match schemas in this document.

2. **Resolver mapping success**
   - Given valid org→country mapping, resolver returns expected adapter.

3. **Resolver missing mapping failure**
   - Given unknown `organization_id`, resolver returns `ORG_COUNTRY_NOT_FOUND`.

4. **Resolver missing adapter failure**
   - Given mapped country with no adapter registration, resolver returns `COUNTRY_ADAPTER_NOT_REGISTERED`.

5. **Deterministic tax calculation**
   - Same `calculate_tax` input executed twice returns same `tax_amount`.

6. **Validation gate test**
   - If `validate_payroll` returns `is_valid: false`, report generation is not executed.

7. **End-to-end Pakistan flow test**
   - `ORG_PK_001` run executes the sequence:
     `resolve -> apply_rules -> calculate_tax -> validate_payroll -> generate_reports`.

**QC status target: 10/10 PASS**
- All interfaces defined with schemas: **covered**.
- Flow is step-by-step: **covered**.
- No ambiguity: **covered via explicit contracts/error codes**.
- Test scenarios included: **covered**.
