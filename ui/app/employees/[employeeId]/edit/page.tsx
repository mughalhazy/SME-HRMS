import { EmployeeEditPage } from '@/components/employees/employee-edit-page'
import { AppShell } from '@/components/shared/app-shell'

export default async function EditEmployeeRoute({ params }: { params: Promise<{ employeeId: string }> }) {
  const { employeeId } = await params

  return (
    <AppShell>
      <EmployeeEditPage employeeId={employeeId} />
    </AppShell>
  )
}
