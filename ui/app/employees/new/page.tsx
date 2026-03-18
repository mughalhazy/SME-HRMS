import { EmployeeCreatePage } from '@/components/employees/employee-create-page'
import { AppShell } from '@/components/shared/app-shell'

export default function NewEmployeePage() {
  return (
    <AppShell currentPath="/employees/new">
      <EmployeeCreatePage />
    </AppShell>
  )
}
