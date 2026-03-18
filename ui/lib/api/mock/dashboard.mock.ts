import { listAttendanceMock } from './attendance.mock'
import { listEmployeesMock } from './employees.mock'
import { listCandidatesMock, listJobPostingsMock } from './hiring.mock'
import { listLeaveRequestsMock } from './leave.mock'
import { listPayrollMock } from './payroll.mock'
import { simulateLatency } from './shared'

export async function getDashboardMockData() {
  await simulateLatency()

  const [employees, attendance, leave, payroll, jobs, candidates] = await Promise.all([
    listEmployeesMock({ limit: 200 }),
    listAttendanceMock({ from: new Date().toISOString().slice(0, 10), to: new Date().toISOString().slice(0, 10) }),
    listLeaveRequestsMock(),
    listPayrollMock(),
    listJobPostingsMock({ limit: 20 }),
    listCandidatesMock(),
  ])

  return {
    employeeCount: employees.data.length,
    attendanceSummary: {
      total: attendance.data.length,
      present: attendance.data.filter((row) => row.attendance_status === 'Present').length,
      late: attendance.data.filter((row) => row.attendance_status === 'Late').length,
      absent: attendance.data.filter((row) => row.attendance_status === 'Absent').length,
    },
    leaveRequestsCount: leave.data.length,
    payrollStatus: {
      processed: payroll.data.filter((row) => row.status === 'Processed').length,
      paid: payroll.data.filter((row) => row.status === 'Paid').length,
      draft: payroll.data.filter((row) => row.status === 'Draft').length,
    },
    hiring: {
      openJobs: jobs.data.filter((row) => row.status === 'Open').length,
      activeCandidates: candidates.data.filter((row) => row.pipeline_stage !== 'Hired').length,
    },
  }
}
