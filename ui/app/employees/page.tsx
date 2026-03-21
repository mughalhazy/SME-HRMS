import Link from 'next/link'
import { UserPlus } from 'lucide-react'

import { EmployeeListPage } from '@/components/employees/employee-list-page'
import AppShell from '@/components/hrms/shell/app-shell'
import { Button } from '@/components/ui/button'

export default function EmployeesPage() {
  return (
    <AppShell
      pageTitle="Employees"
      pageDescription="Browse, filter, and act on employee records from a single structured directory table."
      pageActions={
        <Button asChild className="h-11 shadow-none">
          <Link href="/employees/new">
            <UserPlus className="h-4 w-4" />
            Add Employee
          </Link>
        </Button>
      }
    >
      <EmployeeListPage />
    </AppShell>
  )
}
