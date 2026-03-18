import { PeopleStructurePage } from '@/components/employees/people-structure-page'
import { AppShell } from '@/components/shared/app-shell'

export default function RolesPage() {
  return (
    <AppShell currentPath="/roles">
      <PeopleStructurePage mode="roles" />
    </AppShell>
  )
}
