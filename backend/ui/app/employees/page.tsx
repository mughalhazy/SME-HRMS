import AppShell from '@/components/hrms/shell/app-shell'
import { EmployeesV2 } from '@/components/employees/EmployeesV2'

export default function EmployeesPage() {
  return (
    <AppShell
      pageTitle="Employees V2"
      pageDescription="Use a clean, table-dominant employee grid for high-speed scanning, filtering, and direct record actions."
    >
      <EmployeesV2 />
    </AppShell>
  )
}
