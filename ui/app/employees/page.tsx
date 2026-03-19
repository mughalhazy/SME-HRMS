import { EmployeeListPage } from '@/components/employees/employee-list-page'
import AppShell from '@/components/hrms/shell/app-shell'

export default function EmployeesPage() {
  return (
    <AppShell pageTitle="Employees" pageDescription="Manage employee records, search the directory, and move into detailed profiles without leaving the workspace.">
      <EmployeeListPage />
    </AppShell>
  )
}
