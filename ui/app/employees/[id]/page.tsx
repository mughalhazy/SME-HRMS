import { EmployeeProfilePage } from '@/components/employees/employee-profile-page'
import AppShell from '@/components/hrms/shell/app-shell'

export default async function EmployeeDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  return (
    <AppShell pageTitle="Employee Profile" pageDescription="Review employee information, attendance context, payroll status, and profile history in a unified view.">
      <EmployeeProfilePage employeeId={id} />
    </AppShell>
  )
}
