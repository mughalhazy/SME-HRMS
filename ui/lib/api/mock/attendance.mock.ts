import { clone, getMockDb, jitterNumber, nowIso, randomId, simulateLatency } from './shared'

export async function listAttendanceMock(params: { employeeId?: string; from?: string; to?: string }) {
  await simulateLatency()

  const rows = getMockDb().attendance
    .filter((record) => (!params.employeeId || record.employee_id === params.employeeId))
    .filter((record) => (!params.from || record.attendance_date >= params.from))
    .filter((record) => (!params.to || record.attendance_date <= params.to))
    .map((record) => ({
      ...clone(record),
      total_hours: record.check_out_time ? jitterNumber(Number(record.total_hours || '0'), 0.03).toFixed(2) : record.total_hours,
    }))
    .sort((left, right) => `${right.attendance_date}${right.updated_at}`.localeCompare(`${left.attendance_date}${left.updated_at}`))

  return { data: rows }
}

export async function clockInMock(payload: { employee_id: string; attendance_date: string; attendance_status: string; source: string; check_in_time: string }) {
  await simulateLatency({ failRate: 0.05 })

  const db = getMockDb()
  const employee = db.employees.find((entry) => entry.employee_id === payload.employee_id)
  if (!employee) {
    throw new Error('Employee not found')
  }

  const record = {
    attendance_id: randomId('att'),
    employee_id: employee.employee_id,
    employee_number: employee.employee_number,
    employee_name: employee.full_name,
    department_id: employee.department_id,
    department_name: employee.department_name,
    attendance_date: payload.attendance_date,
    attendance_status: 'Present' as const,
    check_in_time: payload.check_in_time,
    check_out_time: null,
    total_hours: '0.00',
    source: 'Manual' as const,
    record_state: 'Captured' as const,
    updated_at: nowIso(),
  }

  db.attendance.unshift(record)
  return { data: clone(record) }
}

export async function clockOutMock(attendanceId: string, payload: { check_out_time: string }) {
  await simulateLatency({ failRate: 0.05 })

  const db = getMockDb()
  const record = db.attendance.find((entry) => entry.attendance_id === attendanceId)
  if (!record) {
    throw new Error('Attendance record not found')
  }

  record.check_out_time = payload.check_out_time
  record.total_hours = jitterNumber(8, 0.08).toFixed(2)
  record.record_state = 'Validated'
  record.updated_at = nowIso()

  return { data: clone(record) }
}
