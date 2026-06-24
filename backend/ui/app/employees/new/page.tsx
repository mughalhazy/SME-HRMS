import { EmployeeCreatePage } from '@/components/employees/employee-create-page'
import AppShell from '@/components/hrms/shell/app-shell'

export default function NewEmployeePage() {
  return (
    <AppShell pageTitle="New Employee" pageDescription="Create employee records with the same layout, controls, and operational standards used across HRMS.">
      <EmployeeCreatePage />
    </AppShell>
  )
}
