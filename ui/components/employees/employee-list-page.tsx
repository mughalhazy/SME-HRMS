'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'
import { ArrowUpRight, PencilLine, RefreshCw, Search, UserPlus, Users } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { EmptyState, ErrorState, InlineLoading, TableSkeleton } from '@/components/ui/feedback'
import { Input, Select } from '@/components/ui/input'
import { PageStack } from '@/components/ui/page'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { getEmployeeFullName, listEmployees } from '@/lib/employees/api'
import { EMPLOYEE_STATUSES, type Employee } from '@/lib/employees/types'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 25

type QuickStatus = 'all' | 'active' | 'inactive'

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value))
}

function getInitials(employee: Pick<Employee, 'first_name' | 'last_name'>) {
  return `${employee.first_name.charAt(0)}${employee.last_name.charAt(0)}`.toUpperCase()
}

function formatStatus(status: Employee['status']) {
  switch (status) {
    case 'OnLeave':
      return 'On leave'
    default:
      return status
  }
}

function statusTone(status: Employee['status']) {
  const variants: Record<Employee['status'], string> = {
    Draft: 'border-transparent bg-slate-100 text-slate-700',
    Active: 'border-transparent bg-emerald-50 text-emerald-700',
    OnLeave: 'border-transparent bg-amber-50 text-amber-700',
    Suspended: 'border-transparent bg-rose-50 text-rose-700',
    Terminated: 'border-transparent bg-slate-200 text-slate-600',
  }

  return variants[status]
}

function matchesQuickStatus(employee: Employee, quickStatus: QuickStatus) {
  if (quickStatus === 'active') {
    return employee.status === 'Active'
  }

  if (quickStatus === 'inactive') {
    return employee.status !== 'Active'
  }

  return true
}

export function EmployeeListPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<(typeof EMPLOYEE_STATUSES)[number] | 'all'>('all')
  const [departmentId, setDepartmentId] = useState('all')
  const [roleId, setRoleId] = useState('all')
  const [quickStatus, setQuickStatus] = useState<QuickStatus>('all')

  const query = useInfiniteQuery({
    queryKey: ['employees-directory'],
    initialPageParam: null as string | null,
    queryFn: ({ pageParam }) =>
      listEmployees({
        status: 'all',
        limit: PAGE_SIZE,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) => (lastPage.page.hasNext ? lastPage.page.nextCursor : null),
  })

  const employees = useMemo(() => query.data?.pages.flatMap((page) => page.data) ?? [], [query.data])

  const departmentOptions = useMemo(
    () => Array.from(new Set(employees.map((employee) => employee.department_id))).sort((left, right) => left.localeCompare(right)),
    [employees],
  )

  const roleOptions = useMemo(
    () => Array.from(new Set(employees.map((employee) => employee.role_id))).sort((left, right) => left.localeCompare(right)),
    [employees],
  )

  const filteredEmployees = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()

    return employees.filter((employee) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        [
          employee.employee_number,
          employee.first_name,
          employee.last_name,
          employee.email,
          employee.department_id,
          employee.role_id,
          employee.manager_employee_id,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
          .includes(normalizedSearch)

      const matchesStatusFilter = status === 'all' || employee.status === status
      const matchesDepartment = departmentId === 'all' || employee.department_id === departmentId
      const matchesRole = roleId === 'all' || employee.role_id === roleId

      return matchesSearch && matchesStatusFilter && matchesDepartment && matchesRole && matchesQuickStatus(employee, quickStatus)
    })
  }, [departmentId, employees, quickStatus, roleId, search, status])

  const hasActiveFilters = search.length > 0 || status !== 'all' || departmentId !== 'all' || roleId !== 'all' || quickStatus !== 'all'

  const resetFilters = () => {
    setSearch('')
    setStatus('all')
    setDepartmentId('all')
    setRoleId('all')
    setQuickStatus('all')
  }

  return (
    <PageStack className="gap-5">
      <section className="space-y-4">
        <div className="grid gap-4 xl:grid-cols-[minmax(0,0.75fr)_minmax(0,1.4fr)_auto] xl:items-center">
          <div className="min-w-0">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-950">Employees</h1>
            <p className="mt-1 text-sm text-slate-500">
              <span className="font-medium text-slate-700">{filteredEmployees.length}</span>
              <span className="ml-1">employees</span>
            </p>
          </div>

          <label className="relative block">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              className="h-11 w-full rounded-full border-[var(--border)] bg-[var(--surface)] pl-11 pr-4 text-sm shadow-none"
              placeholder="Search employees..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>

          <Button asChild className="justify-self-start xl:justify-self-end">
            <Link href="/employees/new">
              <UserPlus className="h-4 w-4" />
              Add employee
            </Link>
          </Button>
        </div>

        <div className="flex flex-col gap-3 border-b border-slate-200 pb-4">
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto]">
            <Select value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}>
              <option value="all">All departments</option>
              {departmentOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </Select>

            <Select value={roleId} onChange={(event) => setRoleId(event.target.value)}>
              <option value="all">All roles</option>
              {roleOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </Select>

            <Select value={status} onChange={(event) => setStatus(event.target.value as (typeof EMPLOYEE_STATUSES)[number] | 'all')}>
              <option value="all">All statuses</option>
              {EMPLOYEE_STATUSES.map((option) => (
                <option key={option} value={option}>
                  {formatStatus(option)}
                </option>
              ))}
            </Select>

            <div className="flex items-center gap-2 lg:justify-end">
              {(['all', 'active', 'inactive'] as const).map((option) => {
                const isActive = quickStatus === option
                const label = option === 'all' ? 'All' : option === 'active' ? 'Active' : 'Inactive'

                return (
                  <button
                    key={option}
                    type="button"
                    className={cn(
                      'rounded-full px-3 py-2 text-sm font-medium transition-colors',
                      isActive ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-950',
                    )}
                    onClick={() => setQuickStatus(option)}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-500">
            <div className="flex flex-wrap items-center gap-3">
              <span>
                Showing <span className="font-medium text-slate-950">{filteredEmployees.length}</span> of{' '}
                <span className="font-medium text-slate-950">{employees.length}</span> loaded employees
              </span>
              {query.isFetching ? <InlineLoading label="Updating directory" /> : null}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {hasActiveFilters ? (
                <Button variant="ghost" size="sm" className="h-8 px-2.5 text-slate-600" onClick={resetFilters}>
                  Clear filters
                </Button>
              ) : null}
              <Button variant="ghost" size="sm" className="h-8 px-2.5 text-slate-600" onClick={() => query.refetch()} disabled={query.isFetching}>
                <RefreshCw className={cn('h-4 w-4', query.isFetching ? 'animate-spin' : '')} />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="min-w-0">
        {query.isLoading ? (
          <TableSkeleton rows={8} columns={6} />
        ) : query.isError ? (
          <ErrorState message={query.error.message} onRetry={() => query.refetch()} />
        ) : filteredEmployees.length === 0 ? (
          <EmptyState
            icon={Users}
            title={employees.length === 0 ? 'No employees yet' : 'No employees match the current filters'}
            message={
              employees.length === 0
                ? 'Add the first employee to start building the directory.'
                : 'Try a broader search or clear filters to see more employees.'
            }
            action={
              employees.length === 0 ? (
                <Button asChild>
                  <Link href="/employees/new">
                    <UserPlus className="h-4 w-4" />
                    Add employee
                  </Link>
                </Button>
              ) : hasActiveFilters ? (
                <Button variant="outline" onClick={resetFilters}>
                  Clear filters
                </Button>
              ) : null
            }
            className="border-0 bg-transparent p-10 shadow-none"
          />
        ) : (
          <div className="overflow-hidden border border-slate-200/80 bg-[var(--surface)]">
            <Table>
              <TableHeader className="bg-[var(--surface)]">
                <TableRow className="h-auto border-b border-slate-200 bg-transparent hover:bg-transparent hover:shadow-none">
                  <TableHead className="px-5 py-3">Employee</TableHead>
                  <TableHead className="px-4 py-3">Department</TableHead>
                  <TableHead className="px-4 py-3">Role</TableHead>
                  <TableHead className="px-4 py-3">Status</TableHead>
                  <TableHead className="px-4 py-3">Join date</TableHead>
                  <TableHead className="px-5 py-3 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="[&_tr:nth-child(even)]:bg-transparent">
                {filteredEmployees.map((employee) => (
                  <TableRow
                    key={employee.employee_id}
                    className="group h-auto cursor-pointer border-b border-slate-100 hover:bg-slate-50"
                    onClick={() => router.push(`/employees/${employee.employee_id}`)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        router.push(`/employees/${employee.employee_id}`)
                      }
                    }}
                    tabIndex={0}
                  >
                    <TableCell className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9 border-slate-200 shadow-none">
                          <AvatarFallback className="bg-slate-100 text-xs font-semibold text-slate-700">{getInitials(employee)}</AvatarFallback>
                        </Avatar>
                        <div className="min-w-0">
                          <div className="truncate font-medium text-slate-950">{getEmployeeFullName(employee)}</div>
                          <div className="truncate text-xs text-slate-500">
                            {employee.employee_number} · {employee.email}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="px-4 py-3.5 text-sm text-slate-600">{employee.department_id}</TableCell>
                    <TableCell className="px-4 py-3.5 text-sm text-slate-600">{employee.role_id}</TableCell>
                    <TableCell className="px-4 py-3.5">
                      <Badge variant="outline" className={cn('font-medium', statusTone(employee.status))}>
                        {formatStatus(employee.status)}
                      </Badge>
                    </TableCell>
                    <TableCell className="px-4 py-3.5 text-sm text-slate-600">{formatDate(employee.hire_date)}</TableCell>
                    <TableCell className="px-5 py-3.5">
                      <div className="flex items-center justify-end gap-1 opacity-100 transition-opacity md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100">
                        <Button
                          asChild
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-slate-500"
                          onClick={(event) => event.stopPropagation()}
                        >
                          <Link href={`/employees/${employee.employee_id}`} aria-label={`View ${getEmployeeFullName(employee)}`}>
                            <ArrowUpRight className="h-4 w-4" />
                          </Link>
                        </Button>
                        <Button
                          asChild
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-slate-500"
                          onClick={(event) => event.stopPropagation()}
                        >
                          <Link href={`/employees/${employee.employee_id}/edit`} aria-label={`Edit ${getEmployeeFullName(employee)}`}>
                            <PencilLine className="h-4 w-4" />
                          </Link>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-3 text-sm text-slate-500">
              <span>{query.hasNextPage ? 'Load more employees to expand the directory.' : 'End of loaded employee results.'}</span>
              {query.hasNextPage ? (
                <Button variant="outline" onClick={() => query.fetchNextPage()} disabled={query.isFetchingNextPage}>
                  {query.isFetchingNextPage ? 'Loading…' : 'Load more'}
                </Button>
              ) : null}
            </div>
          </div>
        )}
      </section>
    </PageStack>
  )
}
