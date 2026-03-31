# Pakistan Payroll System Specification

## 1. Salary Structure

A payroll record must break salary into standardized buckets for transparent processing, taxation, and reporting.

### 1.1 Basic
- **Basic salary** is the fixed core amount of compensation for the pay period.
- It is used as a base for several dependent calculations (e.g., gratuity and provident fund where applicable).
- Basic may be defined as a fixed amount or as a percentage of total package, but must be stored as an explicit value per payroll run.

### 1.2 Allowances
- **Allowances** are additions to basic salary.
- Typical examples: house rent, transport, medical, utility, and special allowances.
- Each allowance must be tagged as either:
  - **Taxable**
  - **Partially taxable**
  - **Non-taxable/exempt** (based on policy/compliance rules)

### 1.3 Deductions
- **Deductions** are subtractions from earnings.
- Typical examples: tax withholding, provident fund contribution, loan installment, penalties, unpaid leave adjustments.
- Each deduction must be tagged as:
  - **Statutory/compliance**
  - **Policy-based**
  - **Recovery/adjustment**

---

## 2. Calculations

### 2.1 Gross Salary
Gross salary is the total earning before statutory and non-statutory deductions.

**Formula:**

`Gross Salary = Basic + Sum(Allowances) + Other Earnings (e.g., bonuses/arrears)`

### 2.2 Taxable Income
Taxable income is the amount subject to tax withholding after exemptions and approved reliefs.

**Formula:**

`Taxable Income = Gross Salary - Exempt Allowances - Approved Pre-Tax Deductions`

> Note: Tax slabs/rates are sourced from compliance configuration and applied during payroll run.

### 2.3 Net Salary
Net salary is the amount payable to employee after all deductions.

**Formula:**

`Net Salary = Gross Salary - Total Deductions`

Where:

`Total Deductions = Tax + Provident Fund + Loan Recovery + Other Deductions`

---

## 3. Components

### 3.1 Gratuity
- Gratuity accrues based on service tenure and policy/compliance criteria.
- System must support:
  - accrual tracking per period
  - eligibility checks (minimum service threshold)
  - payout calculation on separation

### 3.2 Provident Fund
- Employer/employee contributions should be configurable by percentage or fixed amount.
- Contributions must be reflected in both payroll deductions and liability reports.
- If compliance requires caps/thresholds, those must be enforced at calculation time.

### 3.3 Loans/Advances
- Loans/advances are recoverable amounts deducted from payroll.
- System must support:
  - installment schedules
  - early payoff
  - carry-forward balances
  - stop/restructure rules

### 3.4 Arrears/Bonuses
- Arrears account for past underpayments/adjustments.
- Bonuses are one-time or periodic extra earnings.
- Both must be tagged for tax treatment and period attribution.

---

## 4. Final Settlement (F&F)

Final settlement applies when an employee exits and all payable/recoverable balances are closed.

### 4.1 Leave Encashment
- Unused eligible leave is converted to monetary value as per policy.
- Encashment amount must be included in final gross earnings and tax logic where applicable.

### 4.2 Pending Deductions
- Any unsettled recoveries (loans, advances, overpayments, assets, notice adjustments) must be applied.
- If recoveries exceed payable amount, the system must produce a negative payable/outstanding recovery record.

---

## 5. Payroll Flow

Step-by-step payroll lifecycle:

1. **Input**
   - Employee master data
   - Attendance/leave
   - Earnings components (basic, allowances, arrears, bonuses)
   - Deductions (tax setup, PF, loans, penalties)
2. **Calculation**
   - Compute gross salary
   - Compute taxable income
   - Apply compliance/statutory rules
   - Compute net salary
3. **Compliance**
   - Validate tax withholding
   - Validate statutory deductions/contributions
   - Generate compliance ledgers/reports
4. **Output**
   - Payslip generation
   - Bank transfer file/payment advice
   - GL postings and audit trail

**Flow:** `Input → Calculation → Compliance → Output`

---

## 6. Frequencies

System must support configurable payroll cycles:

- **Monthly**: standard salaried cycle.
- **Weekly**: suitable for wage-based staff.
- **Daily**: suitable for daily wage/contract processing.

Each frequency must map to proportional earnings/deductions logic and period-based compliance treatment.

---

## 7. Edge Cases

### 7.1 Partial Month
- Proration required for join/exit mid-period or unpaid leave.

**Example formula:**

`Prorated Basic = (Payable Days / Total Period Days) × Basic`

### 7.2 Zero Salary
- If payable earnings are zero, system should still process mandatory compliance checks and produce a zero-net payslip if required.

### 7.3 Negative Adjustments
- Negative arrears or correction entries may reduce gross/net pay.
- System must allow controlled negative lines and enforce policy on minimum payable amount.

---

## 8. Test Scenarios

1. **Standard monthly payroll**
   - Inputs: basic + taxable allowances + standard deductions.
   - Validate gross, taxable, net calculations.
2. **Employee with exempt allowance**
   - Validate taxable income excludes exempt component.
3. **Loan recovery active**
   - Validate installment deduction and remaining balance.
4. **Bonus + arrears in same period**
   - Validate gross uplift and tax impact.
5. **Final settlement with leave encashment**
   - Validate F&F payable and pending deductions handling.
6. **Mid-month joining**
   - Validate prorated earnings and deductions.
7. **Zero salary period**
   - Validate zero-net output without calculation crash.
8. **Negative adjustment period**
   - Validate policy handling for negative/near-zero payable.

---

## QC (10/10 PASS)

- [x] Formulas defined
- [x] Flow complete
- [x] Integration with compliance clear
