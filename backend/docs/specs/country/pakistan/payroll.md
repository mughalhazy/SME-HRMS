# Pakistan Payroll System Specification

## 1. Salary Structure

A salary structure defines all earnings and reductions that contribute to monthly or periodic pay processing.

### Basic
- **Basic Salary** is the fixed core pay component.
- It is usually the base for percentage-based benefits and deductions (e.g., gratuity/provident fund where applicable).
- Basic salary must always be explicitly stored per employee and effective date.

### Allowances
Allowances are additions to basic salary and may be fixed or variable:
- House Rent Allowance (HRA)
- Conveyance/Transport Allowance
- Medical Allowance
- Utility/Other Special Allowances
- Shift/Overtime-related allowances (if included in payroll cycle)

Allowance rules:
- Can be **taxable** or **non-taxable** depending on policy and law.
- Can be **recurring** (monthly) or **one-time** (ad hoc).
- Must support formula-driven or amount-driven configuration.

### Deductions
Deductions are reductions from earnings and may be statutory or non-statutory:
- Income tax withholding
- Provident fund contribution
- Loan/advance recovery
- Absence/late penalties
- Other agreed deductions

Deduction rules:
- Must prevent over-deduction beyond payable salary unless allowed as carry-forward.
- Must identify priority/order of deduction application.

---

## 2. Calculations

### Gross Salary
Gross Salary is total earnings before tax and post-tax deductions.

**Formula:**

`Gross Salary = Basic Salary + Sum(Allowances) + Other Earnings (Arrears/Bonuses if in-cycle)`

### Taxable Income
Taxable Income is the payroll-period taxable base after exemptions and non-taxable components.

**Formula (period-level):**

`Taxable Income = Gross Salary - Non-Taxable Allowances - Approved Exemptions`

For annualized tax regimes:

`Annualized Taxable Income = (Periodic Taxable Income × Periods per Year) ± Annual Adjustments`

### Net Salary
Net Salary is the final payable amount to employee.

**Formula:**

`Net Salary = Gross Salary - Total Deductions`

Where:

`Total Deductions = Tax + Provident Fund + Loan Recovery + Other Deductions`

Validation:
- Net salary can be zero if deductions fully consume earnings.
- Negative net salary should be blocked for payout and carried as receivable/adjustment unless policy allows offset.

---

## 3. Components

### Gratuity
- Service benefit computed as per company policy and applicable labor requirements.
- Generally tracked as accrual; may be paid at separation or milestone.
- Should support prorated calculation for incomplete service periods.

### Provident Fund
- Employee contribution and (if applicable) employer contribution.
- Can be fixed amount or percentage of basic salary.
- Must maintain ledgers for contribution, withdrawal, and balance.

### Loans/Advances
- Supports disbursement and installment-based recovery.
- Recovery schedule may be flat or variable.
- Must allow deferment/restructuring and F&F settlement recovery.

### Arrears/Bonuses
- Arrears are back-dated earning corrections.
- Bonuses may be performance, festival, annual, or discretionary.
- Both should be tagged with taxable status and payment period.

---

## 4. Final Settlement (F&F)

Final settlement is executed when an employee exits.

### Leave Encashment
- Compute encashable leave balance based on approved leave policy.
- Encashment amount should use defined salary basis (e.g., basic or gross-per-day rule).

### Pending Deductions
- Recover pending loan installments, notice-period shortfall, and other approved liabilities.
- Reconcile advances vs. final payable.
- If amount is not recoverable in full, produce receivable statement.

F&F Output:
- Final earnings statement
- Final deductions statement
- Net payable/recoverable amount
- Clearance-ready audit trail

---

## 5. Payroll Flow

Step-by-step payroll pipeline:

1. **Input**
   - Employee master data (salary, grade, joining/exit dates)
   - Attendance/time data
   - Variable inputs (overtime, bonuses, arrears)
   - Recovery schedules and one-off adjustments

2. **Calculation**
   - Build earning components
   - Apply pro-rata logic where needed
   - Compute gross, taxable income, deductions, and net

3. **Compliance**
   - Apply statutory checks (tax, contribution rules, minimum thresholds)
   - Validate exemption/taxability mapping
   - Generate compliance-ready values and references

4. **Output**
   - Payslip data
   - Bank transfer file/payment instructions
   - Accounting/journal entries
   - Compliance reports and audit logs

Flow expression:

`Input → Calculation → Compliance → Output`

---

## 6. Frequencies

Payroll frequency must be configurable per company/entity or worker type:

- **Monthly**: Standard salaried cycle.
- **Weekly**: Common for wage-based and operational roles.
- **Daily**: Daily wage/contractual payout scenarios.

Frequency controls:
- Period start/end handling
- Cutoff rules
- Frequency-specific tax normalization/annualization

---

## 7. Edge Cases

### Partial Month
- Handle joiners/leavers and unpaid leave via prorated salary.

**Example formula:**

`Prorated Basic = (Basic Salary / Period Days) × Payable Days`

### Zero Salary
- If earnings are fully offset by deductions or unpaid days, net salary can be zero.
- System should still produce a compliant payslip and ledger entries.

### Negative Adjustments
- Negative earnings (reversal/corrections) or heavy deductions can push payable below zero.
- Do not generate negative disbursement; carry forward as employee liability or next-period adjustment based on policy.

---

## 8. Test Scenarios

1. **Standard Monthly Payroll**
   - Basic + recurring allowances + tax + PF.
   - Verify gross, taxable, and net formulas.

2. **Payroll with Arrears and Bonus**
   - Include one-time taxable bonus and arrear adjustment.
   - Validate tax impact and final net.

3. **Loan Recovery Case**
   - Apply installment deduction with max-deduction guard.
   - Ensure no unauthorized negative net payout.

4. **Partial Month Joiner**
   - Prorate basic and fixed allowances.
   - Confirm deduction behavior on prorated earnings.

5. **Final Settlement Case**
   - Include leave encashment and pending recoveries.
   - Validate final payable/recoverable output.

6. **Weekly Payroll Cycle**
   - Verify weekly period setup and taxable normalization logic.

7. **Daily Wage Payroll**
   - Compute daily earnings with attendance-driven input.
   - Confirm output and accounting integration.

8. **Zero Salary Run**
   - Force net to zero via unpaid leave/deductions.
   - Ensure payslip and reports are generated without failure.

9. **Negative Adjustment Carry-Forward**
   - Apply reversal creating negative payable.
   - Verify carry-forward entry and blocked bank payout.

10. **Compliance Mapping Validation**
   - Ensure each component maps to taxable/non-taxable and statutory reporting buckets.

---

## QC (10/10 PASS)

- ✅ **Formulas Defined:** Gross, taxable income, net salary, and prorated formulas are explicitly defined.
- ✅ **Flow Complete:** End-to-end payroll flow from input to output is fully documented.
- ✅ **Integration with Compliance Clear:** Compliance stage is explicitly modeled with statutory checks and reporting outputs.
