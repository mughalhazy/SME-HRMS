'use client'

import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Building2, RefreshCw, ShieldCheck, Users } from 'lucide-react'

import { Button } from '@/components/base/button'
import { EmptyState, ErrorState, InlineLoading, TableSkeleton } from '@/components/base/feedback'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/base/table'
import { getEmployeeFullName, listEmployees } from '@/lib/employees/api'

const PAGE_SIZE = 100

type PeopleStructurePageProps = {
  mode: 'departments' | 'roles'
}

type GroupedRecord = {
  id: string
  name: string
  totalEmployees: number
  activeEmployees: number
  managers: string[]
  recentHire: string | null
}

function formatDate(value: string | null) {
  if (!value) {
    return '—'
  }

  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' }).format(new Date(value))
}

export function PeopleStructurePage({ mode }: PeopleStructurePageProps) {
  const query = useQuery({
    queryKey: ['people-structure', mode],
    queryFn: () => listEmployees({ limit: PAGE_SIZE }),
  })

  const groupedRecords = useMemo(() => {
    const employees = query.data?.data ?? []
    const buckets = new Map<string, GroupedRecord>()

    employees.forEach((employee) => {
      const id = mode === 'departments' ? employee.department_id : employee.role_id
      const fallbackName = mode === 'departments' ? employee.department_id : employee.role_id
      const group = buckets.get(id) ?? {
        id,
        name: fallbackName,
        totalEmployees: 0,
        activeEmployees: 0,
        managers: [],
        recentHire: null,
      }

      group.totalEmployees += 1

      if (employee.status === 'Active') {
        group.activeEmployees += 1
      }

      if (employee.manager_employee_id && !group.managers.includes(employee.manager_employee_id)) {
        group.managers.push(employee.manager_employee_id)
      }

      if (!group.recentHire || employee.hire_date > group.recentHire) {
        group.recentHire = employee.hire_date
      }

      buckets.set(id, group)
    })

    return Array.from(buckets.values()).sort((left, right) => right.totalEmployees - left.totalEmployees || left.name.localeCompare(right.name))
  }, [mode, query.data])

  const summary = useMemo(() => {
    const employees = query.data?.data ?? []

    return {
      totalGroups: groupedRecords.length,
      totalEmployees: employees.length,
      activeEmployees: employees.filter((employee) => employee.status === 'Active').length,
      latestHire:
        employees.length > 0
          ? employees.reduce((latest, employee) => (employee.hire_date > latest ? employee.hire_date : latest), employees[0].hire_date)
          : null,
    }
  }, [groupedRecords.length, query.data])

  const isDepartments = mode === 'departments'
  const title = isDepartments ? 'Departments' : 'Roles'
  const description = isDepartments
    ? 'Review headcount distribution across departments without introducing another navigation layer.'
    : 'Review role concentration and occupancy with the same calm information density as the rest of the workspace.'
  const Icon = isDepartments ? Building2 : ShieldCheck

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-gray-500">
              <Icon className="h-4 w-4" />
              <span className="text-sm font-medium">People structure</span>
            </div>
            <div>
              <h2 className="text-2xl font-semibold text-black">{title}</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-gray-600">{description}</p>
            </div>
          </div>
          <Button variant="outline" onClick={() => query.refetch()} disabled={query.isFetching}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <div className="rounded-lg border border-gray-200 p-4">
            <p className="text-sm text-gray-500">Total {title.toLowerCase()}</p>
            <p className="mt-2 text-2xl font-semibold text-black">{summary.totalGroups}</p>
          </div>
          <div className="rounded-lg border border-gray-200 p-4">
            <p className="text-sm text-gray-500">Employees covered</p>
            <p className="mt-2 text-2xl font-semibold text-black">{summary.totalEmployees}</p>
          </div>
          <div className="rounded-lg border border-gray-200 p-4">
            <p className="text-sm text-gray-500">Active employees</p>
            <p className="mt-2 text-2xl font-semibold text-black">{summary.activeEmployees}</p>
          </div>
          <div className="rounded-lg border border-gray-200 p-4">
            <p className="text-sm text-gray-500">Latest hire</p>
            <p className="mt-2 text-2xl font-semibold text-black">{formatDate(summary.latestHire)}</p>
          </div>
        </div>
      </section>

      <section className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 px-6 py-4">
          <div>
            <h3 className="text-base font-semibold text-black">{title} directory</h3>
            <p className="text-sm text-gray-600">Grouped from the employee directory so hierarchy stays clear: sidebar first, content second.</p>
          </div>
          {query.isFetching ? <InlineLoading label={`Syncing ${title.toLowerCase()}…`} /> : null}
        </div>

        {query.isLoading ? (
          <TableSkeleton rows={6} columns={5} />
        ) : query.isError ? (
          <div className="p-6">
            <ErrorState message={query.error.message} onRetry={() => query.refetch()} />
          </div>
        ) : groupedRecords.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Users}
              title={`No ${title.toLowerCase()} found`}
              message={`Employee records are required before ${title.toLowerCase()} can be summarized here.`}
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{isDepartments ? 'Department' : 'Role'}</TableHead>
                <TableHead>Total employees</TableHead>
                <TableHead>Active employees</TableHead>
                <TableHead>Managers</TableHead>
                <TableHead>Latest hire</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {groupedRecords.map((record) => (
                <TableRow key={record.id}>
                  <TableCell>
                    <div className="font-medium text-black">{record.name}</div>
                    <div className="text-sm text-gray-500">{record.id}</div>
                  </TableCell>
                  <TableCell className="text-gray-700">{record.totalEmployees}</TableCell>
                  <TableCell className="text-gray-700">{record.activeEmployees}</TableCell>
                  <TableCell className="text-gray-700">
                    {record.managers.length > 0
                      ? record.managers
                          .map((managerId) => query.data?.data.find((employee) => employee.employee_id === managerId))
                          .filter((employee): employee is NonNullable<typeof employee> => Boolean(employee))
                          .map((employee) => getEmployeeFullName(employee))
                          .join(', ')
                      : '—'}
                  </TableCell>
                  <TableCell className="text-gray-700">{formatDate(record.recentHire)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>
    </div>
  )
}
