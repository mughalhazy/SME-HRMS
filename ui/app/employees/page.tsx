import { AppShell } from '@/components/shared/app-shell'
import { EmployeeList } from '@/components/employees/EmployeeList'

export default function EmployeesPage() {
  return (
    <AppShell currentPath="/employees">
      <EmployeeList />
    </AppShell>
  )
}
