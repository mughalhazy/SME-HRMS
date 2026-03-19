import { LeaveManagement } from '@/components/surfaces/LeaveManagement'
import AppShell from '@/components/hrms/shell/app-shell'

export default function LeavePage() {
  return (
    <AppShell pageTitle="Leave" pageDescription="Review leave requests, balances, and team coverage with consistent filters and approvals.">
      <LeaveManagement />
    </AppShell>
  )
}
