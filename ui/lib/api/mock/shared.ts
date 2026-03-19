export type MockFailureOptions = {
  failRate?: number
  forceFailure?: boolean
}

export type EmployeeMockRecord = {
  employee_id: string
  employee_number: string
  first_name: string
  last_name: string
  full_name: string
  email: string
  phone?: string
  hire_date: string
  employment_type: 'FullTime' | 'PartTime' | 'Contract' | 'Intern'
  status: 'Draft' | 'Active' | 'OnLeave' | 'Suspended' | 'Terminated'
  department_id: string
  department_name: string
  role_id: string
  role_title: string
  manager_employee_id?: string
  manager_name?: string
  created_at: string
  updated_at: string
}

export type AttendanceMockRecord = {
  attendance_id: string
  employee_id: string
  employee_number: string
  employee_name: string
  department_id: string
  department_name: string
  attendance_date: string
  attendance_status: 'Present' | 'Absent' | 'Late' | 'HalfDay' | 'Holiday'
  check_in_time: string | null
  check_out_time: string | null
  total_hours: string
  source: 'Manual' | 'Biometric' | 'APIImport'
  record_state: 'Captured' | 'Validated' | 'Approved' | 'Locked' | 'Queued locally'
  updated_at: string
}

export type LeaveMockRecord = {
  leave_request_id: string
  employee_id: string
  employee_number: string
  employee_name: string
  department_id: string
  department_name: string
  leave_type: string
  start_date: string
  end_date: string
  total_days: number
  reason: string
  approver_employee_id?: string
  approver_name?: string
  status: 'Draft' | 'Submitted' | 'Approved' | 'Rejected' | 'Cancelled'
  submitted_at: string | null
  decision_at: string | null
  updated_at: string
}

export type PayrollMockRecord = {
  payroll_record_id: string
  employee_id: string
  employee_number: string
  employee_name: string
  department_id: string
  department_name: string
  pay_period_start: string
  pay_period_end: string
  base_salary: string
  allowances: string
  deductions: string
  overtime_pay: string
  gross_pay: string
  net_pay: string
  currency: string
  payment_date: string | null
  status: 'Draft' | 'Processed' | 'Paid' | 'Cancelled'
  updated_at: string
}

export type JobPostingMockRecord = {
  job_posting_id: string
  title: string
  department_id: string
  department_name: string
  role_id?: string
  role_title?: string
  employment_type: 'FullTime' | 'PartTime' | 'Contract' | 'Intern'
  description: string
  openings_count: number
  posting_date: string
  closing_date: string | null
  status: 'Draft' | 'Open' | 'OnHold' | 'Closed' | 'Filled'
  location?: string
  updated_at: string
}

export type CandidateMockRecord = {
  candidate_id: string
  candidate_name: string
  candidate_email: string
  job_posting_id: string
  job_title: string
  department_id: string
  department_name: string
  role_id?: string
  role_title?: string
  application_date: string
  pipeline_stage: 'Applied' | 'Screening' | 'Interviewing' | 'Offered' | 'Hired'
  stage_updated_at: string
  next_interview_at: string | null
  interview_count: number
  hiring_owner_employee_id?: string
  hiring_owner_name?: string
  updated_at: string
  score: number
  source: string
  summary: string
}

export type InterviewMockRecord = {
  interview_id: string
  candidate_id: string
  interview_type: 'PhoneScreen' | 'Technical' | 'Behavioral' | 'Panel' | 'Final'
  scheduled_at: string
  scheduled_end_at: string
  location: string
  status: 'Scheduled' | 'Completed' | 'Cancelled' | 'NoShow'
  updated_at: string
}

export type MockDatabase = {
  employees: EmployeeMockRecord[]
  attendance: AttendanceMockRecord[]
  leave: LeaveMockRecord[]
  payroll: PayrollMockRecord[]
  jobs: JobPostingMockRecord[]
  candidates: CandidateMockRecord[]
  interviews: InterviewMockRecord[]
}

function withTime(date: string, hour: number, minute: number) {
  return `${date}T${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00.000Z`
}

function daysFromToday(offset: number) {
  const date = new Date()
  date.setUTCDate(date.getUTCDate() + offset)
  return date.toISOString().slice(0, 10)
}

function hoursBetween(start: string | null, end: string | null) {
  if (!start || !end) return '0.00'
  const value = (new Date(end).getTime() - new Date(start).getTime()) / (1000 * 60 * 60)
  return Math.max(value, 0).toFixed(2)
}

function employeeSeed(): EmployeeMockRecord[] {
  const now = new Date().toISOString()

  return [
    {
      employee_id: 'emp-001',
      employee_number: 'E-001',
      first_name: 'Amina',
      last_name: 'Yusuf',
      full_name: 'Amina Yusuf',
      email: 'amina.yusuf@example.com',
      phone: '+1 555-0101',
      hire_date: '2023-02-14',
      employment_type: 'FullTime',
      status: 'Active',
      department_id: 'dep-fin',
      department_name: 'Finance',
      role_id: 'role-finance-manager',
      role_title: 'Finance Manager',
      manager_employee_id: 'emp-006',
      manager_name: 'Helen Brooks',
      created_at: '2023-02-14T09:00:00.000Z',
      updated_at: now,
    },
    {
      employee_id: 'emp-002',
      employee_number: 'E-002',
      first_name: 'Jordan',
      last_name: 'Kim',
      full_name: 'Jordan Kim',
      email: 'jordan.kim@example.com',
      phone: '+1 555-0102',
      hire_date: '2024-06-10',
      employment_type: 'FullTime',
      status: 'OnLeave',
      department_id: 'dep-ops',
      department_name: 'Operations',
      role_id: 'role-ops-lead',
      role_title: 'Operations Lead',
      manager_employee_id: 'emp-006',
      manager_name: 'Helen Brooks',
      created_at: '2024-06-10T09:00:00.000Z',
      updated_at: now,
    },
    {
      employee_id: 'emp-003',
      employee_number: 'E-003',
      first_name: 'Noah',
      last_name: 'Bennett',
      full_name: 'Noah Bennett',
      email: 'noah.bennett@example.com',
      phone: '+1 555-0103',
      hire_date: '2022-09-01',
      employment_type: 'Contract',
      status: 'Active',
      department_id: 'dep-eng',
      department_name: 'Engineering',
      role_id: 'role-frontend-engineer',
      role_title: 'Frontend Engineer',
      manager_employee_id: 'emp-006',
      manager_name: 'Helen Brooks',
      created_at: '2022-09-01T09:00:00.000Z',
      updated_at: now,
    },
    {
      employee_id: 'emp-004',
      employee_number: 'E-004',
      first_name: 'Sara',
      last_name: 'Wong',
      full_name: 'Sara Wong',
      email: 'sara.wong@example.com',
      phone: '+1 555-0104',
      hire_date: '2021-04-12',
      employment_type: 'FullTime',
      status: 'Active',
      department_id: 'dep-hr',
      department_name: 'People Operations',
      role_id: 'role-hr-director',
      role_title: 'HR Director',
      manager_employee_id: 'emp-006',
      manager_name: 'Helen Brooks',
      created_at: '2021-04-12T09:00:00.000Z',
      updated_at: now,
    },
    {
      employee_id: 'emp-005',
      employee_number: 'E-005',
      first_name: 'Marco',
      last_name: 'Diaz',
      full_name: 'Marco Diaz',
      email: 'marco.diaz@example.com',
      phone: '+1 555-0105',
      hire_date: '2020-11-02',
      employment_type: 'FullTime',
      status: 'Active',
      department_id: 'dep-pay',
      department_name: 'Payroll',
      role_id: 'role-payroll-analyst',
      role_title: 'Payroll Analyst',
      manager_employee_id: 'emp-006',
      manager_name: 'Helen Brooks',
      created_at: '2020-11-02T09:00:00.000Z',
      updated_at: now,
    },
    {
      employee_id: 'emp-006',
      employee_number: 'E-006',
      first_name: 'Helen',
      last_name: 'Brooks',
      full_name: 'Helen Brooks',
      email: 'helen.brooks@example.com',
      phone: '+1 555-0106',
      hire_date: '2019-01-15',
      employment_type: 'FullTime',
      status: 'Active',
      department_id: 'dep-exec',
      department_name: 'Executive',
      role_id: 'role-chief-people-officer',
      role_title: 'Chief People Officer',
      created_at: '2019-01-15T09:00:00.000Z',
      updated_at: now,
    },
  ]
}

function attendanceSeed(employees: EmployeeMockRecord[]): AttendanceMockRecord[] {
  const today = daysFromToday(0)
  const yesterday = daysFromToday(-1)
  const twoDaysAgo = daysFromToday(-2)
  const threeDaysAgo = daysFromToday(-3)

  const rows: AttendanceMockRecord[] = []
  const templates: Array<{ date: string; statuses: AttendanceMockRecord['attendance_status'][] }> = [
    { date: today, statuses: ['Present', 'Present', 'Late', 'Present', 'Present', 'Present'] },
    { date: yesterday, statuses: ['Present', 'Absent', 'Present', 'Present', 'Present', 'Present'] },
    { date: twoDaysAgo, statuses: ['Present', 'Present', 'Present', 'Late', 'Present', 'Present'] },
    { date: threeDaysAgo, statuses: ['Present', 'Present', 'Present', 'Present', 'HalfDay', 'Present'] },
  ]

  templates.forEach(({ date, statuses }, templateIndex) => {
    employees.forEach((employee, employeeIndex) => {
      const status = statuses[employeeIndex] ?? 'Present'
      const checkIn = status === 'Absent' ? null : withTime(date, 8 + (employeeIndex % 2), 55 - templateIndex)
      const checkOut = status === 'Absent' || (date === today && employeeIndex === 0) ? null : withTime(date, 17 + (employeeIndex % 2), 10 + templateIndex)

      rows.push({
        attendance_id: `att-${templateIndex + 1}-${employee.employee_id}`,
        employee_id: employee.employee_id,
        employee_number: employee.employee_number,
        employee_name: employee.full_name,
        department_id: employee.department_id,
        department_name: employee.department_name,
        attendance_date: date,
        attendance_status: status,
        check_in_time: checkIn,
        check_out_time: checkOut,
        total_hours: hoursBetween(checkIn, checkOut),
        source: employeeIndex % 2 === 0 ? 'Biometric' : 'Manual',
        record_state: date === today ? 'Validated' : 'Approved',
        updated_at: checkOut ?? checkIn ?? withTime(date, 18, 0),
      })
    })
  })

  return rows
}

function leaveSeed(employees: EmployeeMockRecord[]): LeaveMockRecord[] {
  return [
    {
      leave_request_id: 'lev-1024',
      employee_id: 'emp-002',
      employee_number: 'E-002',
      employee_name: 'Jordan Kim',
      department_id: 'dep-ops',
      department_name: 'Operations',
      leave_type: 'Annual',
      start_date: daysFromToday(4),
      end_date: daysFromToday(7),
      total_days: 4,
      reason: 'Family travel',
      approver_employee_id: 'emp-004',
      approver_name: 'Sara Wong',
      status: 'Submitted',
      submitted_at: `${daysFromToday(-1)}T14:10:00.000Z`,
      decision_at: null,
      updated_at: `${daysFromToday(-1)}T14:10:00.000Z`,
    },
    {
      leave_request_id: 'lev-1023',
      employee_id: 'emp-001',
      employee_number: 'E-001',
      employee_name: 'Amina Yusuf',
      department_id: 'dep-fin',
      department_name: 'Finance',
      leave_type: 'Sick',
      start_date: daysFromToday(0),
      end_date: daysFromToday(1),
      total_days: 2,
      reason: 'Recovery after medical procedure',
      approver_employee_id: 'emp-005',
      approver_name: 'Marco Diaz',
      status: 'Approved',
      submitted_at: `${daysFromToday(-2)}T08:00:00.000Z`,
      decision_at: `${daysFromToday(-1)}T09:00:00.000Z`,
      updated_at: `${daysFromToday(-1)}T09:00:00.000Z`,
    },
    {
      leave_request_id: 'lev-1022',
      employee_id: 'emp-006',
      employee_number: 'E-006',
      employee_name: 'Helen Brooks',
      department_id: 'dep-exec',
      department_name: 'Executive',
      leave_type: 'Other',
      start_date: daysFromToday(14),
      end_date: daysFromToday(45),
      total_days: 32,
      reason: 'Executive retreat and extended planning leave',
      approver_employee_id: 'emp-004',
      approver_name: 'People Ops Council',
      status: 'Submitted',
      submitted_at: `${daysFromToday(-3)}T12:00:00.000Z`,
      decision_at: null,
      updated_at: `${daysFromToday(-3)}T12:00:00.000Z`,
    },
    {
      leave_request_id: 'lev-1021',
      employee_id: employees[2].employee_id,
      employee_number: employees[2].employee_number,
      employee_name: employees[2].full_name,
      department_id: employees[2].department_id,
      department_name: employees[2].department_name,
      leave_type: 'Casual',
      start_date: daysFromToday(-7),
      end_date: daysFromToday(-6),
      total_days: 2,
      reason: 'Personal matters',
      approver_employee_id: 'emp-004',
      approver_name: 'Sara Wong',
      status: 'Rejected',
      submitted_at: `${daysFromToday(-10)}T10:10:00.000Z`,
      decision_at: `${daysFromToday(-9)}T17:00:00.000Z`,
      updated_at: `${daysFromToday(-9)}T17:00:00.000Z`,
    },
  ]
}

function payrollSeed(employees: EmployeeMockRecord[]): PayrollMockRecord[] {
  const start = new Date()
  start.setUTCDate(1)
  const periodStart = start.toISOString().slice(0, 10)
  const periodEnd = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1, 0)).toISOString().slice(0, 10)

  return [
    {
      payroll_record_id: 'pay-3001',
      employee_id: employees[0].employee_id,
      employee_number: employees[0].employee_number,
      employee_name: employees[0].full_name,
      department_id: employees[0].department_id,
      department_name: employees[0].department_name,
      pay_period_start: periodStart,
      pay_period_end: periodEnd,
      base_salary: '5200.00',
      allowances: '350.00',
      deductions: '280.00',
      overtime_pay: '120.00',
      gross_pay: '5670.00',
      net_pay: '5390.00',
      currency: 'USD',
      payment_date: null,
      status: 'Processed',
      updated_at: `${daysFromToday(0)}T07:00:00.000Z`,
    },
    {
      payroll_record_id: 'pay-3002',
      employee_id: employees[1].employee_id,
      employee_number: employees[1].employee_number,
      employee_name: employees[1].full_name,
      department_id: employees[1].department_id,
      department_name: employees[1].department_name,
      pay_period_start: periodStart,
      pay_period_end: periodEnd,
      base_salary: '4300.00',
      allowances: '180.00',
      deductions: '210.00',
      overtime_pay: '0.00',
      gross_pay: '4480.00',
      net_pay: '4270.00',
      currency: 'USD',
      payment_date: `${periodEnd}`,
      status: 'Paid',
      updated_at: `${daysFromToday(0)}T07:10:00.000Z`,
    },
    {
      payroll_record_id: 'pay-3003',
      employee_id: employees[2].employee_id,
      employee_number: employees[2].employee_number,
      employee_name: employees[2].full_name,
      department_id: employees[2].department_id,
      department_name: employees[2].department_name,
      pay_period_start: periodStart,
      pay_period_end: periodEnd,
      base_salary: '6100.00',
      allowances: '420.00',
      deductions: '330.00',
      overtime_pay: '160.00',
      gross_pay: '6680.00',
      net_pay: '6350.00',
      currency: 'USD',
      payment_date: null,
      status: 'Draft',
      updated_at: `${daysFromToday(0)}T07:20:00.000Z`,
    },
    {
      payroll_record_id: 'pay-3004',
      employee_id: employees[3].employee_id,
      employee_number: employees[3].employee_number,
      employee_name: employees[3].full_name,
      department_id: employees[3].department_id,
      department_name: employees[3].department_name,
      pay_period_start: periodStart,
      pay_period_end: periodEnd,
      base_salary: '7200.00',
      allowances: '500.00',
      deductions: '450.00',
      overtime_pay: '0.00',
      gross_pay: '7700.00',
      net_pay: '7250.00',
      currency: 'USD',
      payment_date: null,
      status: 'Processed',
      updated_at: `${daysFromToday(0)}T07:30:00.000Z`,
    },
  ]
}

function jobsSeed(): JobPostingMockRecord[] {
  return [
    {
      job_posting_id: 'job-204',
      title: 'Frontend Engineer',
      department_id: 'dep-eng',
      department_name: 'Engineering',
      role_id: 'role-frontend-engineer',
      role_title: 'Frontend Engineer',
      employment_type: 'FullTime',
      description: 'Own the customer-facing HR experience across dashboards and workflows.',
      openings_count: 2,
      posting_date: daysFromToday(-6),
      closing_date: daysFromToday(21),
      status: 'Open',
      location: 'Remote · US',
      updated_at: `${daysFromToday(-1)}T16:15:00.000Z`,
    },
    {
      job_posting_id: 'job-205',
      title: 'People Operations Manager',
      department_id: 'dep-hr',
      department_name: 'People Operations',
      role_id: 'role-people-ops-manager',
      role_title: 'People Operations Manager',
      employment_type: 'FullTime',
      description: 'Lead employee experience, leave governance, and policy rollout.',
      openings_count: 1,
      posting_date: daysFromToday(-4),
      closing_date: daysFromToday(18),
      status: 'Open',
      location: 'Austin, TX',
      updated_at: `${daysFromToday(-1)}T11:00:00.000Z`,
    },
    {
      job_posting_id: 'job-198',
      title: 'Payroll Analyst',
      department_id: 'dep-pay',
      department_name: 'Payroll',
      role_id: 'role-payroll-analyst',
      role_title: 'Payroll Analyst',
      employment_type: 'Contract',
      description: 'Support payroll reconciliation and period-close operations.',
      openings_count: 1,
      posting_date: daysFromToday(-17),
      closing_date: null,
      status: 'OnHold',
      location: 'Chicago, IL',
      updated_at: `${daysFromToday(-2)}T15:45:00.000Z`,
    },
  ]
}

function candidateSeed(): CandidateMockRecord[] {
  return [
    {
      candidate_id: 'cand-001',
      candidate_name: 'Ava Patel',
      candidate_email: 'ava.patel@example.com',
      job_posting_id: 'job-205',
      job_title: 'People Operations Manager',
      department_id: 'dep-hr',
      department_name: 'People Operations',
      role_id: 'role-people-ops-manager',
      role_title: 'People Operations Manager',
      application_date: daysFromToday(-7),
      pipeline_stage: 'Applied',
      stage_updated_at: `${daysFromToday(-2)}T09:00:00.000Z`,
      next_interview_at: null,
      interview_count: 0,
      hiring_owner_employee_id: 'emp-004',
      hiring_owner_name: 'Sara Wong',
      updated_at: `${daysFromToday(-2)}T09:00:00.000Z`,
      score: 88,
      source: 'LinkedIn',
      summary: 'Strong systems thinking with a deep accessibility portfolio.',
    },
    {
      candidate_id: 'cand-002',
      candidate_name: 'Liam Carter',
      candidate_email: 'liam.carter@example.com',
      job_posting_id: 'job-204',
      job_title: 'Frontend Engineer',
      department_id: 'dep-eng',
      department_name: 'Engineering',
      role_id: 'role-frontend-engineer',
      role_title: 'Frontend Engineer',
      application_date: daysFromToday(-8),
      pipeline_stage: 'Screening',
      stage_updated_at: `${daysFromToday(-2)}T13:15:00.000Z`,
      next_interview_at: null,
      interview_count: 0,
      hiring_owner_employee_id: 'emp-006',
      hiring_owner_name: 'Helen Brooks',
      updated_at: `${daysFromToday(-2)}T13:15:00.000Z`,
      score: 82,
      source: 'Referral',
      summary: 'Referred by engineering lead with strong React and design systems depth.',
    },
    {
      candidate_id: 'cand-003',
      candidate_name: 'Maya Brooks',
      candidate_email: 'maya.brooks@example.com',
      job_posting_id: 'job-205',
      job_title: 'People Operations Manager',
      department_id: 'dep-hr',
      department_name: 'People Operations',
      role_id: 'role-people-ops-manager',
      role_title: 'People Operations Manager',
      application_date: daysFromToday(-10),
      pipeline_stage: 'Interviewing',
      stage_updated_at: `${daysFromToday(-1)}T10:00:00.000Z`,
      next_interview_at: `${daysFromToday(1)}T14:30:00.000Z`,
      interview_count: 1,
      hiring_owner_employee_id: 'emp-004',
      hiring_owner_name: 'Sara Wong',
      updated_at: `${daysFromToday(-1)}T10:00:00.000Z`,
      score: 91,
      source: 'Career Site',
      summary: 'Experienced HR operator with payroll and employee relations expertise.',
    },
    {
      candidate_id: 'cand-004',
      candidate_name: 'Noah Kim',
      candidate_email: 'noah.kim@example.com',
      job_posting_id: 'job-204',
      job_title: 'Frontend Engineer',
      department_id: 'dep-eng',
      department_name: 'Engineering',
      role_id: 'role-frontend-engineer',
      role_title: 'Frontend Engineer',
      application_date: daysFromToday(-14),
      pipeline_stage: 'Offered',
      stage_updated_at: `${daysFromToday(-1)}T15:45:00.000Z`,
      next_interview_at: null,
      interview_count: 3,
      hiring_owner_employee_id: 'emp-006',
      hiring_owner_name: 'Helen Brooks',
      updated_at: `${daysFromToday(-1)}T15:45:00.000Z`,
      score: 86,
      source: 'Job Board',
      summary: 'Excellent SQL and stakeholder communication; offer package shared yesterday.',
    },
    {
      candidate_id: 'cand-005',
      candidate_name: 'Sofia Nguyen',
      candidate_email: 'sofia.nguyen@example.com',
      job_posting_id: 'job-198',
      job_title: 'Payroll Analyst',
      department_id: 'dep-pay',
      department_name: 'Payroll',
      role_id: 'role-payroll-analyst',
      role_title: 'Payroll Analyst',
      application_date: daysFromToday(-17),
      pipeline_stage: 'Hired',
      stage_updated_at: `${daysFromToday(-1)}T17:20:00.000Z`,
      next_interview_at: null,
      interview_count: 2,
      hiring_owner_employee_id: 'emp-005',
      hiring_owner_name: 'Marco Diaz',
      updated_at: `${daysFromToday(-1)}T17:20:00.000Z`,
      score: 93,
      source: 'Agency',
      summary: 'Accepted offer and is queued for onboarding handoff.',
    },
  ]
}

function interviewSeed(): InterviewMockRecord[] {
  return [
    {
      interview_id: 'int-001',
      candidate_id: 'cand-003',
      interview_type: 'Panel',
      scheduled_at: `${daysFromToday(1)}T14:30:00.000Z`,
      scheduled_end_at: `${daysFromToday(1)}T15:15:00.000Z`,
      location: 'Zoom · Hiring Panel',
      status: 'Scheduled',
      updated_at: new Date().toISOString(),
    },
  ]
}

function createMockDatabase(): MockDatabase {
  const employees = employeeSeed()
  return {
    employees,
    attendance: attendanceSeed(employees),
    leave: leaveSeed(employees),
    payroll: payrollSeed(employees),
    jobs: jobsSeed(),
    candidates: candidateSeed(),
    interviews: interviewSeed(),
  }
}

const globalScope = globalThis as typeof globalThis & {
  __SME_HRMS_MOCK_DB__?: MockDatabase
}

export function getMockDb() {
  if (!globalScope.__SME_HRMS_MOCK_DB__) {
    globalScope.__SME_HRMS_MOCK_DB__ = createMockDatabase()
  }

  return globalScope.__SME_HRMS_MOCK_DB__
}

export function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export function jitterNumber(value: number, spread: number, decimals = 2) {
  const delta = (Math.random() * spread * 2 - spread) * value
  return Number(Math.max(value + delta, 0).toFixed(decimals))
}

export async function simulateLatency({ failRate = 0, forceFailure = false }: MockFailureOptions = {}) {
  const duration = 300 + Math.floor(Math.random() * 501)
  await new Promise((resolve) => setTimeout(resolve, duration))

  if (forceFailure || Math.random() < failRate) {
    throw new Error('Mock API temporary failure. Please retry.')
  }
}

export function nowIso() {
  return new Date().toISOString()
}

export function randomId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`
}

export function toTitleName(firstName: string, lastName: string) {
  return `${firstName} ${lastName}`.trim()
}
