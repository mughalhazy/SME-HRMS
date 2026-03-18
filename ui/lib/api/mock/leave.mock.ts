import { clone, getMockDb, nowIso, simulateLatency } from './shared'

export async function listLeaveRequestsMock(params: { status?: string; from?: string; to?: string } = {}) {
  await simulateLatency()

  const rows = getMockDb().leave
    .filter((record) => (!params.status || record.status === params.status))
    .filter((record) => (!params.from || record.start_date >= params.from || record.updated_at.slice(0, 10) >= params.from))
    .filter((record) => (!params.to || record.start_date <= params.to || record.updated_at.slice(0, 10) <= params.to))
    .sort((left, right) => right.updated_at.localeCompare(left.updated_at))
    .map((record) => clone(record))

  return { data: rows }
}

export async function approveLeaveRequestMock(leaveRequestId: string, options?: { failRate?: number }) {
  await simulateLatency({ failRate: options?.failRate ?? 0.07 })

  const record = getMockDb().leave.find((entry) => entry.leave_request_id === leaveRequestId)
  if (!record) {
    throw new Error('Leave request not found')
  }

  record.status = 'Approved'
  record.decision_at = nowIso()
  record.updated_at = record.decision_at

  const employee = getMockDb().employees.find((entry) => entry.employee_id === record.employee_id)
  if (employee && record.start_date <= nowIso().slice(0, 10) && record.end_date >= nowIso().slice(0, 10)) {
    employee.status = 'OnLeave'
    employee.updated_at = nowIso()
  }

  return { data: clone(record) }
}
