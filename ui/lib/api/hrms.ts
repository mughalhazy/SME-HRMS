import { apiRequest, ApiError } from '@/lib/api/client'

const env = (globalThis as typeof globalThis & { process?: { env?: Record<string, string | undefined> } }).process?.env

export type SyncMode = 'live' | 'demo'

export interface EmployeeOption {
  id: string
  number: string
  name: string
  department: string
}

export interface AttendanceRecord {
  attendanceId: string
  employeeId: string
  employeeNumber: string
  employeeName: string
  departmentName: string
  attendanceDate: string
  attendanceStatus: string
  checkInTime: string | null
  checkOutTime: string | null
  totalHours: string
  source: string
  recordState: string
  updatedAt: string
}

export interface PayrollRecord {
  payrollRecordId: string
  employeeId: string
  employeeNumber: string
  employeeName: string
  departmentName: string
  payPeriodStart: string
  payPeriodEnd: string
  baseSalary: string
  allowances: string
  deductions: string
  overtimePay: string
  grossPay: string
  netPay: string
  currency: string
  paymentDate: string | null
  status: string
  updatedAt: string
}

export interface AttendanceResponse {
  records: AttendanceRecord[]
  syncMode: SyncMode
  syncSource: string
}

export interface PayrollResponse {
  records: PayrollRecord[]
  syncMode: SyncMode
  syncSource: string
}

const EMPLOYEES: EmployeeOption[] = [
  { id: 'emp-1', number: 'E-001', name: 'Jane Doe', department: 'Engineering' },
  { id: 'emp-2', number: 'E-002', name: 'John Smith', department: 'Operations' },
  { id: 'emp-3', number: 'E-003', name: 'Amina Yusuf', department: 'Finance' },
]

const DEMO_ATTENDANCE: AttendanceRecord[] = [
  {
    attendanceId: 'att-1003',
    employeeId: 'emp-1',
    employeeNumber: 'E-001',
    employeeName: 'Jane Doe',
    departmentName: 'Engineering',
    attendanceDate: '2026-03-18',
    attendanceStatus: 'Present',
    checkInTime: '2026-03-18T08:57:00Z',
    checkOutTime: null,
    totalHours: '0.00',
    source: 'Manual',
    recordState: 'Validated',
    updatedAt: '2026-03-18T08:57:00Z',
  },
  {
    attendanceId: 'att-1002',
    employeeId: 'emp-1',
    employeeNumber: 'E-001',
    employeeName: 'Jane Doe',
    departmentName: 'Engineering',
    attendanceDate: '2026-03-17',
    attendanceStatus: 'Present',
    checkInTime: '2026-03-17T09:03:00Z',
    checkOutTime: '2026-03-17T17:34:00Z',
    totalHours: '8.52',
    source: 'Biometric',
    recordState: 'Approved',
    updatedAt: '2026-03-17T17:34:00Z',
  },
  {
    attendanceId: 'att-1001',
    employeeId: 'emp-2',
    employeeNumber: 'E-002',
    employeeName: 'John Smith',
    departmentName: 'Operations',
    attendanceDate: '2026-03-17',
    attendanceStatus: 'Late',
    checkInTime: '2026-03-17T09:29:00Z',
    checkOutTime: '2026-03-17T18:01:00Z',
    totalHours: '8.53',
    source: 'Manual',
    recordState: 'Validated',
    updatedAt: '2026-03-17T18:01:00Z',
  },
]

const DEMO_PAYROLL: PayrollRecord[] = [
  {
    payrollRecordId: 'pr-3001',
    employeeId: 'emp-1',
    employeeNumber: 'E-001',
    employeeName: 'Jane Doe',
    departmentName: 'Engineering',
    payPeriodStart: '2026-03-01',
    payPeriodEnd: '2026-03-31',
    baseSalary: '4200.00',
    allowances: '250.00',
    deductions: '180.00',
    overtimePay: '140.00',
    grossPay: '4590.00',
    netPay: '4410.00',
    currency: 'USD',
    paymentDate: null,
    status: 'Processed',
    updatedAt: '2026-03-18T07:00:00Z',
  },
  {
    payrollRecordId: 'pr-3002',
    employeeId: 'emp-2',
    employeeNumber: 'E-002',
    employeeName: 'John Smith',
    departmentName: 'Operations',
    payPeriodStart: '2026-03-01',
    payPeriodEnd: '2026-03-31',
    baseSalary: '3600.00',
    allowances: '210.00',
    deductions: '140.00',
    overtimePay: '95.00',
    grossPay: '3905.00',
    netPay: '3765.00',
    currency: 'USD',
    paymentDate: '2026-03-31',
    status: 'Paid',
    updatedAt: '2026-03-18T07:12:00Z',
  },
  {
    payrollRecordId: 'pr-3003',
    employeeId: 'emp-3',
    employeeNumber: 'E-003',
    employeeName: 'Amina Yusuf',
    departmentName: 'Finance',
    payPeriodStart: '2026-03-01',
    payPeriodEnd: '2026-03-31',
    baseSalary: '4800.00',
    allowances: '420.00',
    deductions: '210.00',
    overtimePay: '180.00',
    grossPay: '5400.00',
    netPay: '5190.00',
    currency: 'USD',
    paymentDate: null,
    status: 'Draft',
    updatedAt: '2026-03-18T07:24:00Z',
  },
]

function getAuthHeaders(): Record<string, string> {
  const authorization = env?.NEXT_PUBLIC_API_AUTHORIZATION

  return authorization ? { Authorization: authorization } : {}
}

function isoDate(value: Date) {
  return value.toISOString().slice(0, 10)
}

function normalizeAttendanceRecord(record: Record<string, unknown>): AttendanceRecord {
  return {
    attendanceId: String(record.attendance_id ?? record.attendanceId ?? crypto.randomUUID()),
    employeeId: String(record.employee_id ?? record.employeeId ?? ''),
    employeeNumber: String(record.employee_number ?? record.employeeNumber ?? '—'),
    employeeName: String(record.employee_name ?? record.employeeName ?? 'Unknown employee'),
    departmentName: String(record.department_name ?? record.departmentName ?? 'Unassigned'),
    attendanceDate: String(record.attendance_date ?? record.attendanceDate ?? isoDate(new Date())),
    attendanceStatus: String(record.attendance_status ?? record.attendanceStatus ?? 'Present'),
    checkInTime: record.check_in_time ? String(record.check_in_time) : record.checkInTime ? String(record.checkInTime) : null,
    checkOutTime: record.check_out_time ? String(record.check_out_time) : record.checkOutTime ? String(record.checkOutTime) : null,
    totalHours: String(record.total_hours ?? record.totalHours ?? '0.00'),
    source: String(record.source ?? 'Manual'),
    recordState: String(record.lifecycle_state ?? record.record_state ?? record.recordState ?? 'Validated'),
    updatedAt: String(record.updated_at ?? record.updatedAt ?? new Date().toISOString()),
  }
}

function normalizePayrollRecord(record: Record<string, unknown>): PayrollRecord {
  return {
    payrollRecordId: String(record.payroll_record_id ?? record.payrollRecordId ?? crypto.randomUUID()),
    employeeId: String(record.employee_id ?? record.employeeId ?? ''),
    employeeNumber: String(record.employee_number ?? record.employeeNumber ?? '—'),
    employeeName: String(record.employee_name ?? record.employeeName ?? 'Unknown employee'),
    departmentName: String(record.department_name ?? record.departmentName ?? 'Unassigned'),
    payPeriodStart: String(record.pay_period_start ?? record.payPeriodStart ?? ''),
    payPeriodEnd: String(record.pay_period_end ?? record.payPeriodEnd ?? ''),
    baseSalary: String(record.base_salary ?? record.baseSalary ?? '0.00'),
    allowances: String(record.allowances ?? '0.00'),
    deductions: String(record.deductions ?? '0.00'),
    overtimePay: String(record.overtime_pay ?? record.overtimePay ?? '0.00'),
    grossPay: String(record.gross_pay ?? record.grossPay ?? '0.00'),
    netPay: String(record.net_pay ?? record.netPay ?? '0.00'),
    currency: String(record.currency ?? 'USD'),
    paymentDate: record.payment_date ? String(record.payment_date) : record.paymentDate ? String(record.paymentDate) : null,
    status: String(record.status ?? 'Draft'),
    updatedAt: String(record.updated_at ?? record.updatedAt ?? new Date().toISOString()),
  }
}

export function getEmployeeOptions() {
  return EMPLOYEES
}

export async function fetchAttendanceRecords(params: { employeeId: string; from: string; to: string }): Promise<AttendanceResponse> {
  try {
    const response = await apiRequest<{ data?: Record<string, unknown>[] }>(
      `/api/v1/attendance/records?employee_id=${encodeURIComponent(params.employeeId)}&from=${encodeURIComponent(params.from)}&to=${encodeURIComponent(params.to)}`,
      {
        headers: getAuthHeaders(),
        cache: 'no-store',
      },
    )

    return {
      records: (response.data ?? []).map(normalizeAttendanceRecord),
      syncMode: 'live',
      syncSource: 'attendance-service',
    }
  } catch (error) {
    if (!(error instanceof ApiError)) {
      throw error
    }

    const filtered = DEMO_ATTENDANCE.filter(
      (record) =>
        record.employeeId === params.employeeId && record.attendanceDate >= params.from && record.attendanceDate <= params.to,
    )

    return {
      records: filtered,
      syncMode: 'demo',
      syncSource: `fallback (${error.status ?? 'offline'})`,
    }
  }
}

export async function fetchPayrollRecords(params: { periodStart: string; periodEnd: string; status?: string }): Promise<PayrollResponse> {
  const query = new URLSearchParams({
    period_start: params.periodStart,
    period_end: params.periodEnd,
  })

  if (params.status && params.status !== 'All') {
    query.set('status', params.status)
  }

  try {
    const response = await apiRequest<{ data?: Record<string, unknown>[] }>(`/api/v1/payroll/records?${query.toString()}`, {
      headers: getAuthHeaders(),
      cache: 'no-store',
    })

    return {
      records: (response.data ?? []).map(normalizePayrollRecord),
      syncMode: 'live',
      syncSource: 'payroll-service',
    }
  } catch (error) {
    if (!(error instanceof ApiError)) {
      throw error
    }

    const filtered = DEMO_PAYROLL.filter(
      (record) =>
        record.payPeriodStart >= params.periodStart &&
        record.payPeriodEnd <= params.periodEnd &&
        (!params.status || params.status === 'All' || record.status === params.status),
    )

    return {
      records: filtered,
      syncMode: 'demo',
      syncSource: `fallback (${error.status ?? 'offline'})`,
    }
  }
}

export async function clockInEmployee(employeeId: string) {
  const employee = EMPLOYEES.find((entry) => entry.id === employeeId)
  if (!employee) {
    throw new Error('Employee not found')
  }

  const now = new Date().toISOString()
  return apiRequest('/api/v1/attendance/records', {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      employee_id: employeeId,
      attendance_date: isoDate(new Date()),
      attendance_status: 'Present',
      source: 'Manual',
      check_in_time: now,
    }),
  })
}

export async function clockOutEmployee(attendanceId: string) {
  return apiRequest(`/api/v1/attendance/records/${attendanceId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      check_out_time: new Date().toISOString(),
    }),
  })
}

export async function runPayroll(params: { periodStart: string; periodEnd: string }) {
  const query = new URLSearchParams({
    period_start: params.periodStart,
    period_end: params.periodEnd,
  })

  return apiRequest(`/api/v1/payroll/run?${query.toString()}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  })
}
