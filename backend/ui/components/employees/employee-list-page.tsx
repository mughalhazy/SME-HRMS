'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'
import { ArrowUpRight, PencilLine, RefreshCw, Search, Users } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/base/avatar'
import { Badge } from '@/components/base/badge'
import { Button } from '@/components/base/button'
import { ErrorState, InlineLoading, Skeleton } from '@/components/base/feedback'
import { Input, Select } from '@/components/base/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/base/table'
import { getEmployeeFullName, listEmployees } from '@/lib/employees/api'
import { EMPLOYEE_STATUSES, type Employee } from '@/lib/employees/types'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 25

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

function DirectoryLoadingState() {
  return (
    <Table className="table-fixed">
      <colgroup>
        <col className="w-[34%]" />
        <col className="w-[18%]" />
        <col className="w-[16%]" />
        <col className="w-[12%]" />
        <col className="w-[12%]" />
        <col className="w-[8%]" />
      </colgroup>
      <TableHeader className="bg-slate-50/90">
        <TableRow className="h-11 border-b border-slate-200 hover:bg-transparent hover:shadow-none">
          <TableHead className="px-4 py-3 md:px-5">Name</TableHead>
          <TableHead className="px-4 py-3 md:px-5">Role</TableHead>
          <TableHead className="px-4 py-3 md:px-5">Department</TableHead>
          <TableHead className="px-4 py-3 md:px-5">Status</TableHead>
          <TableHead className="px-4 py-3 md:px-5">Join Date</TableHead>
          <TableHead className="px-4 py-3 text-right md:px-5">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Array.from({ length: 8 }).map((_, index) => (
          <TableRow key={index} className="h-[68px] border-b border-slate-200 hover:bg-transparent hover:shadow-none">
            <TableCell className="px-4 py-3 md:px-5">
              <div className="flex items-center gap-3">
                <Skeleton className="h-9 w-9 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-36" />
                  <Skeleton className="h-3 w-52 max-w-full" />
                </div>
              </div>
            </TableCell>
            <TableCell className="px-4 py-3 md:px-5"><Skeleton className="h-4 w-24" /></TableCell>
            <TableCell className="px-4 py-3 md:px-5"><Skeleton className="h-4 w-24" /></TableCell>
            <TableCell className="px-4 py-3 md:px-5"><Skeleton className="h-6 w-20 rounded-full" /></TableCell>
            <TableCell className="px-4 py-3 md:px-5"><Skeleton className="h-4 w-24" /></TableCell>
            <TableCell className="px-4 py-3 md:px-5">
              <div className="flex justify-end gap-2">
                <Skeleton className="h-8 w-8 rounded-lg" />
                <Skeleton className="h-8 w-8 rounded-lg" />
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export function EmployeeListPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<(typeof EMPLOYEE_STATUSES)[number] | 'all'>('all')
  const [departmentId, setDepartmentId] = useState('all')
  const [roleId, setRoleId] = useState('all')

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

      return matchesSearch && matchesStatusFilter && matchesDepartment && matchesRole
    })
  }, [departmentId, employees, roleId, search, status])

  const hasActiveFilters = search.length > 0 || status !== 'all' || departmentId !== 'all' || roleId !== 'all'

  const resetFilters = () => {
    setSearch('')
    setStatus('all')
    setDepartmentId('all')
    setRoleId('all')
  }

  return (
    <section className="min-w-0 rounded-[var(--radius-panel)] border border-slate-200 bg-white shadow-[var(--shadow-panel)]">
      <div className="flex flex-col gap-4 border-b border-slate-200 px-4 py-4 lg:flex-row lg:items-center lg:justify-between lg:px-5">
        <div className="flex min-w-0 flex-1 flex-col gap-4 lg:flex-row lg:items-center">
          <label className="relative min-w-0 flex-1 lg:max-w-md">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              className="h-10 border-slate-200 bg-white pl-10"
              placeholder="Search employees"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>

          <div className="grid gap-3 sm:grid-cols-3 lg:min-w-[540px] lg:flex-1">
            <Select className="h-10" value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}>
              <option value="all">All departments</option>
              {departmentOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </Select>

            <Select className="h-10" value={roleId} onChange={(event) => setRoleId(event.target.value)}>
              <option value="all">All roles</option>
              {roleOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </Select>

            <Select className="h-10" value={status} onChange={(event) => setStatus(event.target.value as (typeof EMPLOYEE_STATUSES)[number] | 'all')}>
              <option value="all">All statuses</option>
              {EMPLOYEE_STATUSES.map((option) => (
                <option key={option} value={option}>
                  {formatStatus(option)}
                </option>
              ))}
            </Select>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 lg:justify-end">
          <div className="text-sm text-slate-500">
            <span className="font-semibold text-slate-950">{filteredEmployees.length}</span> records
          </div>
          {hasActiveFilters ? (
            <Button variant="ghost" size="sm" className="h-10 px-3 text-slate-600" onClick={resetFilters}>
              Clear
            </Button>
          ) : null}
          <Button variant="ghost" size="sm" className="h-10 px-3 text-slate-600" onClick={() => query.refetch()} disabled={query.isFetching}>
            <RefreshCw className={cn('h-4 w-4', query.isFetching ? 'animate-spin' : '')} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 text-sm text-slate-500 lg:px-5">
        <div className="flex flex-wrap items-center gap-3">
          <span>
            Showing <span className="font-medium text-slate-950">{filteredEmployees.length}</span> of{' '}
            <span className="font-medium text-slate-950">{employees.length}</span> loaded employees
          </span>
          {query.isFetching ? <InlineLoading label="Updating list" /> : null}
        </div>
        <span>{hasActiveFilters ? 'Filtered directory' : 'Employee directory'}</span>
      </div>

      {query.isLoading ? (
        <DirectoryLoadingState />
      ) : query.isError ? (
        <ErrorState
          className="rounded-none border-0 px-4 py-6 shadow-none lg:px-5"
          message={query.error.message}
          onRetry={() => query.refetch()}
        />
      ) : filteredEmployees.length === 0 ? (
        <div className="flex min-h-[320px] flex-col items-center justify-center gap-4 px-4 py-12 text-center lg:px-5">
          <div className="rounded-full border border-slate-200 bg-slate-50 p-3 text-slate-500">
            <Users className="h-5 w-5" />
          </div>
          <div className="space-y-2">
            <h2 className="text-lg font-semibold tracking-tight text-slate-950">
              {employees.length === 0 ? 'No employees yet' : 'No employees match the current filters'}
            </h2>
            <p className="text-sm leading-6 text-slate-500">
              {employees.length === 0
                ? 'Add the first employee to start populating the workspace.'
                : 'Change the search or filters to widen the directory results.'}
            </p>
          </div>
          {hasActiveFilters ? (
            <Button variant="outline" onClick={resetFilters}>
              Clear filters
            </Button>
          ) : (
            <Button asChild>
              <Link href="/employees/new">Add employee</Link>
            </Button>
          )}
        </div>
      ) : (
        <div className="min-w-0">
          <Table className="table-fixed">
            <colgroup>
              <col className="w-[34%]" />
              <col className="w-[18%]" />
              <col className="w-[16%]" />
              <col className="w-[12%]" />
              <col className="w-[12%]" />
              <col className="w-[8%]" />
            </colgroup>
            <TableHeader className="bg-slate-50/90">
              <TableRow className="h-11 border-b border-slate-200 bg-transparent hover:bg-transparent hover:shadow-none">
                <TableHead className="px-4 py-3 md:px-5">Name</TableHead>
                <TableHead className="px-4 py-3 md:px-5">Role</TableHead>
                <TableHead className="px-4 py-3 md:px-5">Department</TableHead>
                <TableHead className="px-4 py-3 md:px-5">Status</TableHead>
                <TableHead className="px-4 py-3 md:px-5">Join Date</TableHead>
                <TableHead className="px-4 py-3 text-right md:px-5">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEmployees.map((employee) => (
                <TableRow
                  key={employee.employee_id}
                  className="group h-[68px] cursor-pointer border-b border-slate-200 hover:bg-slate-50/80"
                  onClick={() => router.push(`/employees/${employee.employee_id}`)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault()
                      router.push(`/employees/${employee.employee_id}`)
                    }
                  }}
                  tabIndex={0}
                >
                  <TableCell className="px-4 py-3 md:px-5">
                    <div className="flex min-w-0 items-center gap-3">
                      <Avatar className="h-9 w-9 border border-slate-200 shadow-none">
                        <AvatarFallback className="bg-slate-100 text-xs font-semibold text-slate-700">{getInitials(employee)}</AvatarFallback>
                      </Avatar>
                      <div className="min-w-0">
                        <div className="truncate text-sm font-semibold text-slate-950">{getEmployeeFullName(employee)}</div>
                        <div className="truncate text-xs text-slate-500">
                          {employee.employee_number} · {employee.email}
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="px-4 py-3 text-sm text-slate-600 md:px-5">{employee.role_id}</TableCell>
                  <TableCell className="px-4 py-3 text-sm text-slate-600 md:px-5">{employee.department_id}</TableCell>
                  <TableCell className="px-4 py-3 md:px-5">
                    <Badge variant="outline" className={cn('min-w-[84px] justify-center font-medium', statusTone(employee.status))}>
                      {formatStatus(employee.status)}
                    </Badge>
                  </TableCell>
                  <TableCell className="px-4 py-3 text-sm text-slate-600 md:px-5">{formatDate(employee.hire_date)}</TableCell>
                  <TableCell className="px-4 py-3 md:px-5">
                    <div className="flex items-center justify-end gap-1 opacity-100 transition-opacity md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100">
                      <Button
                        asChild
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-slate-500 hover:text-slate-900"
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
                        className="h-8 w-8 text-slate-500 hover:text-slate-900"
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

          {query.hasNextPage ? (
            <div className="flex justify-end border-t border-slate-200 px-4 py-3 lg:px-5">
              <Button variant="outline" onClick={() => query.fetchNextPage()} disabled={query.isFetchingNextPage}>
                {query.isFetchingNextPage ? 'Loading…' : 'Load more'}
              </Button>
            </div>
          ) : null}
        </div>
      )}
    </section>
  )
}
