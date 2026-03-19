import AppShell from '@/components/hrms/shell/app-shell'
import { OrganizationPage } from '@/components/organization/organization-page'

export default function OrganizationRoute() {
  return (
    <AppShell pageTitle="Organization" pageDescription="Review departments, role coverage, and staffing structure with clean organizational visibility.">
      <OrganizationPage />
    </AppShell>
  )
}
