import { Attendance } from '@/components/surfaces/Attendance'
import { AppShell } from '@/components/shared/app-shell'

export default function AttendancePage() {
  return (
    <AppShell currentPath="/attendance">
      <Attendance />
    </AppShell>
  )
}
