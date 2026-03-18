import { AppShell } from '@/components/shared/app-shell'
import { LeaveRequestsPage } from '@/components/surfaces/leave-requests-page'

export default function LeaveRequestsRoute() {
  return (
    <AppShell currentPath="/leave-requests">
      <LeaveRequestsPage />
    </AppShell>
  )
}
