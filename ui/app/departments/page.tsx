import { Departments } from '@/components/surfaces/Departments'
import { AppShell } from '@/components/shared/app-shell'

export default function DepartmentsPage() {
  return (
    <AppShell currentPath="/departments">
      <Departments />
    </AppShell>
  )
}
