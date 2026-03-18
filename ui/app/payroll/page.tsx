import { AttendancePayrollWorkspace } from '@/components/dashboard/attendance-payroll-workspace'
import { AppShell } from '@/components/shared/app-shell'

export default function PayrollPage() {
  return (
    <AppShell currentPath="/payroll">
      <AttendancePayrollWorkspace />
    </AppShell>
  )
}
