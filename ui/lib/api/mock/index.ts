import { clockInMock, clockOutMock, listAttendanceMock } from './attendance.mock'
import { loginMock, logoutMock, meMock, refreshMock } from './auth.mock'
import { createEmployeeMock, getEmployeeMock, listEmployeesMock, updateEmployeeMock } from './employees.mock'
import {
  createJobPostingMock,
  listCandidatesMock,
  listInterviewsMock,
  listJobPostingsMock,
  scheduleInterviewMock,
  updateInterviewStatusMock,
  updateCandidateStageMock,
} from './hiring.mock'
import { approveLeaveRequestMock, listLeaveRequestsMock } from './leave.mock'
import { ingestNotificationEventMock, getInboxMock, listNotificationDeliveryMock, markInboxMessageReadMock } from './notifications.mock'
import { listPayrollMock, runPayrollMock } from './payroll.mock'

function parseBody(body?: BodyInit | null) {
  if (typeof body !== 'string' || body.length === 0) {
    return {}
  }

  try {
    return JSON.parse(body) as Record<string, unknown>
  } catch {
    return {}
  }
}

function response<T>(payload: T) {
  return payload
}

export async function mockApiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const url = new URL(path, 'http://mock.local')
  const pathname = url.pathname
  const method = (init?.method ?? 'GET').toUpperCase()
  const body = parseBody(init?.body)

  if (pathname === '/api/v1/auth/login' && method === 'POST') {
    return response(await loginMock(body as never)) as T
  }

  if (pathname === '/api/v1/auth/me' && method === 'GET') {
    return response(await meMock(init?.headers)) as T
  }

  if (pathname === '/api/v1/auth/refresh' && method === 'POST') {
    return response(await refreshMock(body as never)) as T
  }

  if (pathname === '/api/v1/auth/logout' && method === 'POST') {
    return response(await logoutMock(body as never)) as T
  }

  if (pathname === '/api/v1/employees' && method === 'GET') {
    return response(await listEmployeesMock({
      status: (url.searchParams.get('status') as 'all' | undefined) ?? undefined,
      departmentId: url.searchParams.get('department_id') ?? undefined,
      limit: url.searchParams.get('limit') ? Number(url.searchParams.get('limit')) : undefined,
      cursor: url.searchParams.get('cursor'),
    })) as T
  }

  if (pathname === '/api/v1/employees' && method === 'POST') {
    return response(await createEmployeeMock(body as never)) as T
  }

  if (pathname.startsWith('/api/v1/employees/') && method === 'GET') {
    return response(await getEmployeeMock(pathname.split('/').pop() ?? '')) as T
  }

  if (pathname.startsWith('/api/v1/employees/') && method === 'PATCH') {
    return response(await updateEmployeeMock(pathname.split('/').pop() ?? '', body as never)) as T
  }

  if (pathname === '/api/v1/attendance/records' && method === 'GET') {
    return response(await listAttendanceMock({
      employeeId: url.searchParams.get('employee_id') ?? undefined,
      from: url.searchParams.get('from') ?? undefined,
      to: url.searchParams.get('to') ?? undefined,
    })) as T
  }

  if (pathname === '/api/v1/attendance/records' && method === 'POST') {
    return response(await clockInMock(body as never)) as T
  }

  if (pathname.startsWith('/api/v1/attendance/records/') && method === 'PATCH') {
    return response(await clockOutMock(pathname.split('/').pop() ?? '', body as never)) as T
  }

  if (pathname === '/api/v1/leave/requests' && method === 'GET') {
    return response(await listLeaveRequestsMock({
      status: url.searchParams.get('status') ?? undefined,
      from: url.searchParams.get('from') ?? undefined,
      to: url.searchParams.get('to') ?? undefined,
    })) as T
  }

  if (pathname.match(/^\/api\/v1\/leave\/requests\/[^/]+\/approve$/) && method === 'POST') {
    const parts = pathname.split('/')
    return response(await approveLeaveRequestMock(parts[5] ?? '')) as T
  }

  if (pathname === '/api/v1/payroll/records' && method === 'GET') {
    return response(await listPayrollMock({
      periodStart: url.searchParams.get('period_start') ?? undefined,
      periodEnd: url.searchParams.get('period_end') ?? undefined,
      status: url.searchParams.get('status') ?? undefined,
    })) as T
  }

  if (pathname === '/api/v1/payroll/run' && method === 'POST') {
    return response(await runPayrollMock({
      periodStart: url.searchParams.get('period_start') ?? '',
      periodEnd: url.searchParams.get('period_end') ?? '',
    })) as T
  }

  if (pathname === '/api/v1/hiring/job-postings' && method === 'GET') {
    return response(await listJobPostingsMock({
      status: url.searchParams.get('status') ?? undefined,
      limit: url.searchParams.get('limit') ? Number(url.searchParams.get('limit')) : undefined,
    })) as T
  }

  if (pathname === '/api/v1/hiring/job-postings' && method === 'POST') {
    return response(await createJobPostingMock(body as never)) as T
  }

  if (pathname === '/api/v1/hiring/candidates' && method === 'GET') {
    return response(await listCandidatesMock()) as T
  }

  if (pathname === '/api/v1/hiring/interviews' && method === 'GET') {
    return response(await listInterviewsMock()) as T
  }

  if (pathname.match(/^\/api\/v1\/hiring\/candidates\/[^/]+\/stage$/) && method === 'PATCH') {
    const parts = pathname.split('/')
    return response(await updateCandidateStageMock(parts[5] ?? '', String(body.pipeline_stage) as never)) as T
  }

  if (pathname.match(/^\/api\/v1\/hiring\/candidates\/[^/]+\/interviews$/) && method === 'POST') {
    const parts = pathname.split('/')
    return response(await scheduleInterviewMock(parts[5] ?? '', {
      interviewType: String(body.interview_type) as never,
      scheduledAt: String(body.scheduled_at),
      scheduledEndAt: String(body.scheduled_end_at),
      location: String(body.location ?? ''),
    })) as T
  }

  if (pathname.match(/^\/api\/v1\/hiring\/interviews\/[^/]+$/) && method === 'PATCH') {
    const parts = pathname.split('/')
    return response(await updateInterviewStatusMock(parts[5] ?? '', String(body.status) as never)) as T
  }

  if (pathname.match(/^\/api\/v1\/notifications\/inbox\/[^/]+$/) && method === 'GET') {
    const parts = pathname.split('/')
    return response(await getInboxMock({
      subjectId: parts[5] ?? '',
      unreadOnly: url.searchParams.get('unread_only') === 'true',
    })) as T
  }

  if (pathname.match(/^\/api\/v1\/notifications\/inbox\/[^/]+\/read\/[^/]+$/) && method === 'POST') {
    const parts = pathname.split('/')
    return response(await markInboxMessageReadMock(parts[5] ?? '', parts[7] ?? '')) as T
  }

  if (pathname === '/api/v1/notifications/delivery' && method === 'GET') {
    return response(await listNotificationDeliveryMock({
      subjectId: url.searchParams.get('subject_id') ?? undefined,
      channel: url.searchParams.get('channel') ?? undefined,
      status: url.searchParams.get('status') ?? undefined,
    })) as T
  }

  if (pathname === '/api/v1/notifications/events' && method === 'POST') {
    return response(await ingestNotificationEventMock(body)) as T
  }

  throw new Error(`No mock handler registered for ${method} ${pathname}`)
}
