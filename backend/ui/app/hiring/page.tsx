import AppShell from '@/components/hrms/shell/app-shell'
import { HiringPage } from '@/components/hiring/hiring-page'

export default function HiringRoute() {
  return (
    <AppShell pageTitle="Hiring" pageDescription="Keep requisitions and candidate flow in one polished hiring workspace.">
      <HiringPage />
    </AppShell>
  )
}
