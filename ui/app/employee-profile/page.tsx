import { EmployeeProfileWorkspace } from '@/components/surfaces/employee-profile-workspace'
import AppShell from '@/components/hrms/shell/app-shell'

export default function EmployeeProfileWorkspacePage() {
  return (
    <AppShell pageTitle="Employee Profile" pageDescription="Review employee-specific operational data from a dedicated profile workspace.">
      <EmployeeProfileWorkspace />
    </AppShell>
  )
}
