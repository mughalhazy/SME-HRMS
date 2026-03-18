import { clone, getMockDb, jitterNumber, nowIso, randomId, simulateLatency } from './shared'

export async function listPayrollMock(params: { periodStart?: string; periodEnd?: string; status?: string } = {}) {
  await simulateLatency()

  const rows = getMockDb().payroll
    .filter((record) => (!params.periodStart || record.pay_period_end >= params.periodStart))
    .filter((record) => (!params.periodEnd || record.pay_period_start <= params.periodEnd))
    .filter((record) => (!params.status || params.status === 'All' || record.status === params.status))
    .map((record) => ({
      ...clone(record),
      net_pay: jitterNumber(Number(record.net_pay), 0.01).toFixed(2),
      gross_pay: jitterNumber(Number(record.gross_pay), 0.01).toFixed(2),
    }))
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))

  return { data: rows }
}

export async function runPayrollMock(params: { periodStart: string; periodEnd: string }, options?: { failRate?: number }) {
  await simulateLatency({ failRate: options?.failRate ?? 0.06 })

  const db = getMockDb()
  const existing = db.payroll.filter(
    (record) => record.pay_period_start === params.periodStart && record.pay_period_end === params.periodEnd,
  )

  if (existing.length > 0) {
    existing.forEach((record) => {
      if (record.status === 'Draft') {
        record.status = 'Processed'
        record.updated_at = nowIso()
      }
    })

    return { data: clone(existing) }
  }

  const created = db.employees.slice(0, 4).map((employee, index) => {
    const baseSalary = 4200 + index * 550
    const allowances = 150 + index * 40
    const deductions = 180 + index * 30
    const overtime = 80 + index * 20
    const gross = baseSalary + allowances + overtime
    const net = gross - deductions

    return {
      payroll_record_id: randomId('pay'),
      employee_id: employee.employee_id,
      employee_number: employee.employee_number,
      employee_name: employee.full_name,
      department_id: employee.department_id,
      department_name: employee.department_name,
      pay_period_start: params.periodStart,
      pay_period_end: params.periodEnd,
      base_salary: baseSalary.toFixed(2),
      allowances: allowances.toFixed(2),
      deductions: deductions.toFixed(2),
      overtime_pay: overtime.toFixed(2),
      gross_pay: gross.toFixed(2),
      net_pay: net.toFixed(2),
      currency: 'USD',
      payment_date: null,
      status: 'Processed' as const,
      updated_at: nowIso(),
    }
  })

  db.payroll.unshift(...created)
  return { data: clone(created) }
}
