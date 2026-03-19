import { Payroll } from '@/components/surfaces/Payroll'
import { AppShell } from '@/components/shared/app-shell'

export default function PayrollPage() {
  return (
    <AppShell currentPath="/payroll">
      <Payroll />
    </AppShell>
  )
}
