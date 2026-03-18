import { AppShell } from '@/components/shared/app-shell'
import { EmployeeProfilePage } from '@/components/employees/employee-profile-page'

export default async function EmployeeProfileRoute({ params }: { params: Promise<{ employeeId: string }> }) {
  const { employeeId } = await params

  return (
    <AppShell>
      <EmployeeProfilePage employeeId={employeeId} />
    </AppShell>
  )
}
