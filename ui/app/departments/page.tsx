import { PeopleStructurePage } from '@/components/employees/people-structure-page'
import { AppShell } from '@/components/shared/app-shell'

export default function DepartmentsPage() {
  return (
    <AppShell currentPath="/departments">
      <PeopleStructurePage mode="departments" />
    </AppShell>
  )
}
