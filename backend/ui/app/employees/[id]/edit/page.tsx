import { EmployeeEditPage } from '@/components/employees/employee-edit-page'
import AppShell from '@/components/hrms/shell/app-shell'

export default async function EditEmployeeRoute({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  return (
    <AppShell pageTitle="Edit Employee" pageDescription="Update employee records with consistent controls and enterprise form spacing.">
      <EmployeeEditPage employeeId={id} />
    </AppShell>
  )
}
