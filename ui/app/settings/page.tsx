import { Settings } from '@/components/surfaces/Settings'
import AppShell from '@/components/hrms/shell/app-shell'

export default function SettingsPage() {
  return (
    <AppShell pageTitle="Settings" pageDescription="Configure company-wide HR defaults, integrations, and operational controls.">
      <Settings />
    </AppShell>
  )
}
