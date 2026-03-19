import { EmployeeDetail } from '@/components/employees/EmployeeDetail'
import { AppShell } from '@/components/shared/app-shell'

export default async function EmployeeProfileRoute() {
  return (
    <AppShell currentPath="/employees">
      <EmployeeDetail />
    </AppShell>
  )
}
