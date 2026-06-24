import { Attendance } from '@/components/surfaces/Attendance'
import AppShell from '@/components/hrms/shell/app-shell'

export default function AttendancePage() {
  return (
    <AppShell pageTitle="Attendance" pageDescription="Monitor daily presence, identify exceptions, and keep time-tracking workflows aligned.">
      <Attendance />
    </AppShell>
  )
}
