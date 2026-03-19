import { AppShell } from '@/components/shared/app-shell'
import { LeaveManagement } from '@/components/surfaces/LeaveManagement'

export default function LeaveRequestsRoute() {
  return (
    <AppShell currentPath="/leave-requests">
      <LeaveManagement />
    </AppShell>
  )
}
