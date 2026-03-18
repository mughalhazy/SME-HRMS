import { AppShell } from '@/components/shared/app-shell'
import { EmployeeListPage } from '@/components/employees/employee-list-page'

export default function EmployeesPage() {
  return (
    <AppShell currentPath="/employees">
      <EmployeeListPage />
    </AppShell>
  )
}
