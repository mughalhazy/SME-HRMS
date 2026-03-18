import { AppShell } from '@/components/shared/app-shell'
import { EmployeeProfileWorkspace } from '@/components/surfaces/employee-profile-workspace'

export default function EmployeeProfileWorkspacePage() {
  return (
    <AppShell currentPath="/employee-profile">
      <EmployeeProfileWorkspace />
    </AppShell>
  )
}
