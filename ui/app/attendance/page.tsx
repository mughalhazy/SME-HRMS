import { AttendancePayrollWorkspace } from '@/components/dashboard/attendance-payroll-workspace'
import { AppShell } from '@/components/shared/app-shell'

export default function AttendancePage() {
  return (
    <AppShell currentPath="/attendance">
      <AttendancePayrollWorkspace />
    </AppShell>
  )
}
