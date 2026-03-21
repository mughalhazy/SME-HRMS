import Link from 'next/link'
import { Download, UserPlus } from 'lucide-react'

import { EmployeeListPage } from '@/components/employees/employee-list-page'
import AppShell from '@/components/hrms/shell/app-shell'
import { Button } from '@/components/ui/button'

export default function EmployeesPage() {
  return (
    <AppShell
      pageTitle="Employees"
      pageDescription="Manage employee records through a structured directory workspace built for scanning, filtering, and fast row-level actions."
      pageActions={
        <>
          <Button variant="outline" className="h-11 border-slate-200 bg-white text-slate-700 shadow-none hover:bg-slate-50">
            <Download className="h-4 w-4" />
            Export
          </Button>
          <Button asChild className="h-11 shadow-none">
            <Link href="/employees/new">
              <UserPlus className="h-4 w-4" />
              Add Employee
            </Link>
          </Button>
        </>
      }
    >
      <EmployeeListPage />
    </AppShell>
  )
}
