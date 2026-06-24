import { Dashboard } from '@/components/dashboard/Dashboard'
import AppShell from '@/components/hrms/shell/app-shell'

export default function DashboardPage() {
  return (
    <AppShell pageTitle="Dashboard" pageDescription="Track workforce health, approvals, and operational priorities from one calm command center.">
      <Dashboard />
    </AppShell>
  )
}
