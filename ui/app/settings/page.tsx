import { Settings } from '@/components/surfaces/Settings'
import { AppShell } from '@/components/shared/app-shell'

export default function SettingsPage() {
  return (
    <AppShell currentPath="/settings" pageActions={<></>}>
      <Settings />
    </AppShell>
  )
}
