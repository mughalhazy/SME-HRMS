import { Payroll } from '@/components/surfaces/Payroll'
import AppShell from '@/components/hrms/shell/app-shell'

export default function PayrollPage() {
  return (
    <AppShell pageTitle="Payroll" pageDescription="Track payroll cycles, exceptions, and settlement readiness across the organization.">
      <Payroll />
    </AppShell>
  )
}
