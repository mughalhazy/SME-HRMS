import { EnterpriseDashboard } from '@/components/dashboard/enterprise-dashboard'
import { AppShell } from '@/components/shared/app-shell'

export default function HomePage() {
  return (
    <AppShell currentPath="/">
      <EnterpriseDashboard />
    </AppShell>
  )
}
