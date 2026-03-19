import { Departments } from '@/components/surfaces/Departments'
import AppShell from '@/components/hrms/shell/app-shell'

export default function DepartmentsPage() {
  return (
    <AppShell pageTitle="Departments" pageDescription="View organizational coverage, staffing distribution, and leadership ownership in one place.">
      <Departments />
    </AppShell>
  )
}
