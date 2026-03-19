import { PeopleStructurePage } from '@/components/employees/people-structure-page'
import AppShell from '@/components/hrms/shell/app-shell'

export default function RolesPage() {
  return (
    <AppShell pageTitle="Roles" pageDescription="Understand role distribution, occupancy, and structure across the organization.">
      <PeopleStructurePage mode="roles" />
    </AppShell>
  )
}
