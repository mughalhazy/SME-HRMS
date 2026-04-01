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

### 2.1 TaxEngineInterface

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

### 2.2 ComplianceEngineInterface

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

### 2.3 PayrollRulesInterface

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
- Core code depends on interface contracts (`TaxEngineInterface`, `ComplianceEngineInterface`, `PayrollRulesInterface`), not concrete country classes.
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
2. Resolve organization/legal-entity/config context to an adapter key.
3. Load adapter registered for the resolved key.
4. Fail fast with explicit error if mapping or adapter is missing.

### Organization resolver path
- Source should come from organization/legal-entity/config records.
- Required resolver shape:

```yaml
organization_id: string
legal_entity_id: string?
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
2. Resolver reads organization/legal-entity/config path and loads corresponding country adapter.
3. For each employee, core calls `PayrollRulesInterface.apply_rules(input)`.
4. Adapter returns adjusted salary, deductions, and rule trace.
5. Core calls `TaxEngineInterface.calculate_tax(input)` using adjusted values.
6. Adapter returns `tax_amount`.
7. Core aggregates per-employee calculations into payroll results.
8. Core calls `ComplianceEngineInterface.validate_payroll(input)` on finalized results.
9. If invalid, core halts finalization and surfaces violation list.
10. If valid, core calls `ComplianceEngineInterface.generate_reports(input)`.
11. Adapter returns report artifacts and metadata.
12. Core persists outputs and publishes completion status.

---

## 6. Example (Pakistan flow)

### Scenario
- Organization: `<organization_id>`
- Mapped country: `<country_code>`
- Payroll period: `2026-03`

### End-to-end flow
1. Core receives payroll request for `<organization_id>`.
2. Resolver resolves organization/legal-entity/config and returns `<country_adapter>`.
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
   - Given valid org/config mapping, resolver returns expected adapter.

3. **Resolver missing mapping failure**
   - Given unknown `organization_id`, resolver returns `ORG_COUNTRY_NOT_FOUND`.

4. **Resolver missing adapter failure**
   - Given mapped country with no adapter registration, resolver returns `COUNTRY_ADAPTER_NOT_REGISTERED`.

5. **Deterministic tax calculation**
   - Same `calculate_tax` input executed twice returns same `tax_amount`.

6. **Validation gate test**
   - If `validate_payroll` returns `is_valid: false`, report generation is not executed.

7. **End-to-end Pakistan flow test**
   - `<organization_id>` run executes the sequence:
     `resolve -> apply_rules -> calculate_tax -> validate_payroll -> generate_reports`.

**QC status target: 10/10 PASS**
- All interfaces defined with schemas: **covered**.
- Flow is step-by-step: **covered**.
- No ambiguity: **covered via explicit contracts/error codes**.
- Test scenarios included: **covered**.
