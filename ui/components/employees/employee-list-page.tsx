'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'
import { ArrowUpRight, PencilLine, RefreshCw, Search, Users } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ErrorState, InlineLoading, Skeleton } from '@/components/ui/feedback'
import { Input, Select } from '@/components/ui/input'
import { PageGrid, PageSection, PageStack, pagePanelClassName, pageSectionPaddingClassName } from '@/components/ui/page'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
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
    <section className="min-w-0 overflow-hidden">
      <div className="grid gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 md:grid-cols-[minmax(0,2.8fr)_minmax(0,1.5fr)_minmax(0,1.5fr)_minmax(116px,1fr)_minmax(116px,1fr)_88px] md:px-6">
        <span>Name</span>
        <span>Role</span>
        <span>Department</span>
        <span>Status</span>
        <span>Join date</span>
        <span className="text-right">Actions</span>
      </div>
      <div className="divide-y divide-slate-200">
        {Array.from({ length: 8 }).map((_, index) => (
          <div key={index} className="grid min-h-[72px] gap-3 px-4 py-4 md:grid-cols-[minmax(0,2.8fr)_minmax(0,1.5fr)_minmax(0,1.5fr)_minmax(116px,1fr)_minmax(116px,1fr)_88px] md:items-center md:px-6">
            <div className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-3 w-56 max-w-full" />
              </div>
            </div>
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-4 w-24" />
            <div className="ml-auto flex gap-2">
              <Skeleton className="h-8 w-8 rounded-lg" />
              <Skeleton className="h-8 w-8 rounded-lg" />
            </div>
          </div>
        ))}
      </div>
    </section>
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
  const activeEmployees = filteredEmployees.filter((employee) => employee.status === 'Active').length
  const inactiveEmployees = filteredEmployees.length - activeEmployees

  const resetFilters = () => {
    setSearch('')
    setStatus('all')
    setDepartmentId('all')
    setRoleId('all')
  }

  return (
    <PageStack>
      <PageSection className="min-w-0 overflow-hidden shadow-none">
        <div className={cn('grid gap-4 xl:grid-cols-12 xl:items-center', pageSectionPaddingClassName)}>
          <label className="relative block xl:col-span-5">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              className="h-11 border-slate-200 bg-white pl-11"
              placeholder="Search by name, employee number, email, department, or role"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>

          <Select className="h-11 xl:col-span-2" value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}>
            <option value="all">All departments</option>
            {departmentOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </Select>

          <Select className="h-11 xl:col-span-2" value={roleId} onChange={(event) => setRoleId(event.target.value)}>
            <option value="all">All roles</option>
            {roleOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </Select>

          <Select className="h-11 xl:col-span-2" value={status} onChange={(event) => setStatus(event.target.value as (typeof EMPLOYEE_STATUSES)[number] | 'all')}>
            <option value="all">All statuses</option>
            {EMPLOYEE_STATUSES.map((option) => (
              <option key={option} value={option}>
                {formatStatus(option)}
              </option>
            ))}
          </Select>

          <div className="flex items-center justify-end gap-3 xl:col-span-1 xl:justify-self-end">
            {hasActiveFilters ? (
              <Button variant="ghost" size="sm" className="h-11 px-4 text-slate-600" onClick={resetFilters}>
                Clear
              </Button>
            ) : null}
            <Button variant="ghost" size="sm" className="h-11 px-4 text-slate-600" onClick={() => query.refetch()} disabled={query.isFetching}>
              <RefreshCw className={cn('h-4 w-4', query.isFetching ? 'animate-spin' : '')} />
              Refresh
            </Button>
          </div>
        </div>

      </PageSection>

      <PageGrid className="grid-cols-12 gap-4 xl:gap-6">
        <PageSection className="col-span-12 min-w-0 overflow-hidden shadow-none xl:col-span-9">
              <div className="flex flex-col gap-2 border-b border-[var(--border)] px-4 py-4 text-sm text-slate-500 md:flex-row md:items-center md:justify-between md:px-6">
                <div className="flex flex-wrap items-center gap-3">
                  <span>
                    Showing <span className="font-medium text-slate-950">{filteredEmployees.length}</span> of{' '}
                    <span className="font-medium text-slate-950">{employees.length}</span> loaded employees
                  </span>
                  {query.isFetching ? <InlineLoading label="Updating list" /> : null}
                </div>
                <span>{hasActiveFilters ? 'Filtered list' : 'Full directory'}</span>
              </div>

              {query.isLoading ? (
                <DirectoryLoadingState />
              ) : query.isError ? (
                <ErrorState className="rounded-none border-x-0 border-b-0 border-t border-rose-200 bg-rose-50/60 px-0 py-6 shadow-none" message={query.error.message} onRetry={() => query.refetch()} />
              ) : filteredEmployees.length === 0 ? (
                <div className="border-t border-slate-200 px-4 py-12 md:px-6">
                  <div className="mx-auto flex max-w-md flex-col items-center gap-4 text-center">
                    <div className="rounded-full bg-slate-100 p-3 text-slate-600">
                      <Users className="h-5 w-5" />
                    </div>
                    <div className="space-y-2">
                      <h2 className="text-lg font-semibold tracking-tight text-slate-950">
                        {employees.length === 0 ? 'No employees yet' : 'No employees match this search'}
                      </h2>
                      <p className="text-sm leading-6 text-slate-500">
                        {employees.length === 0
                          ? 'Add the first employee to start building the directory.'
                          : 'Try a broader search or adjust the filters to see more employees.'}
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
                      {hasActiveFilters ? (
                        <Button variant="outline" onClick={resetFilters}>
                          Clear filters
                        </Button>
                      ) : null}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="min-w-0">
                  <Table className="table-fixed">
                    <colgroup>
                      <col className="w-[35%]" />
                      <col className="w-[17%]" />
                      <col className="w-[18%]" />
                      <col className="w-[12%]" />
                      <col className="w-[12%]" />
                      <col className="w-[6%]" />
                    </colgroup>
                    <TableHeader className="bg-slate-50/80">
                      <TableRow className="h-auto border-b border-slate-200 bg-transparent hover:bg-transparent hover:shadow-none">
                        <TableHead className="px-4 py-3 md:px-6">Name</TableHead>
                        <TableHead className="px-4 py-3 md:px-6">Role</TableHead>
                        <TableHead className="px-4 py-3 md:px-6">Department</TableHead>
                        <TableHead className="px-4 py-3 md:px-6">Status</TableHead>
                        <TableHead className="px-4 py-3 md:px-6">Join date</TableHead>
                        <TableHead className="px-4 py-3 text-right md:px-6">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody className="[&_tr:nth-child(even)]:bg-transparent">
                      {filteredEmployees.map((employee) => (
                        <TableRow
                          key={employee.employee_id}
                          className="group h-[72px] cursor-pointer border-b border-slate-200 hover:bg-slate-50/70"
                          onClick={() => router.push(`/employees/${employee.employee_id}`)}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter' || event.key === ' ') {
                              event.preventDefault()
                              router.push(`/employees/${employee.employee_id}`)
                            }
                          }}
                          tabIndex={0}
                        >
                          <TableCell className="px-4 py-4 align-middle md:px-6">
                            <div className="flex min-w-0 items-center gap-3">
                              <Avatar className="h-10 w-10 border border-slate-200 shadow-none">
                                <AvatarFallback className="bg-slate-100 text-xs font-semibold text-slate-700">{getInitials(employee)}</AvatarFallback>
                              </Avatar>
                              <div className="min-w-0 space-y-1">
                                <div className="truncate text-sm font-semibold text-slate-950">{getEmployeeFullName(employee)}</div>
                                <div className="truncate text-xs text-slate-500">
                                  {employee.employee_number} · {employee.email}
                                </div>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell className="px-4 py-4 align-middle text-sm text-slate-600 md:px-6">{employee.role_id}</TableCell>
                          <TableCell className="px-4 py-4 align-middle text-sm text-slate-600 md:px-6">{employee.department_id}</TableCell>
                          <TableCell className="px-4 py-4 align-middle md:px-6">
                            <Badge variant="outline" className={cn('min-w-[84px] justify-center font-medium', statusTone(employee.status))}>
                              {formatStatus(employee.status)}
                            </Badge>
                          </TableCell>
                          <TableCell className="px-4 py-4 align-middle text-sm text-slate-600 md:px-6">{formatDate(employee.hire_date)}</TableCell>
                          <TableCell className="px-4 py-4 align-middle md:px-6">
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

                  <div className="flex flex-col gap-3 border-t border-slate-200 px-4 py-4 text-sm text-slate-500 md:px-6 sm:flex-row sm:items-center sm:justify-between">
                    <span>{query.hasNextPage ? 'Load more employees to expand the directory.' : 'End of loaded employee results.'}</span>
                    {query.hasNextPage ? (
                      <Button variant="outline" onClick={() => query.fetchNextPage()} disabled={query.isFetchingNextPage}>
                        {query.isFetchingNextPage ? 'Loading…' : 'Load more'}
                      </Button>
                    ) : null}
                  </div>
                </div>
              )}
        </PageSection>

        <PageSection className="col-span-12 overflow-hidden shadow-none xl:col-span-3">
              <div className="border-b border-[var(--border)] px-4 py-4 sm:px-5">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--muted-foreground)]">Directory summary</p>
                <p className="mt-1 text-sm leading-6 text-[var(--muted-foreground)]">Keep workforce totals visible without competing with the list.</p>
              </div>
              <div className="grid gap-3 p-4 sm:p-5">
                <div className={cn(pagePanelClassName, 'px-4 py-4')}>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Total employees</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{filteredEmployees.length}</p>
                  <p className="mt-1 text-sm text-slate-500">Visible in the current workspace.</p>
                </div>
                <div className={cn(pagePanelClassName, 'px-4 py-4')}>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Active</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{activeEmployees}</p>
                  <p className="mt-1 text-sm text-slate-500">Employees currently marked active.</p>
                </div>
                <div className={cn(pagePanelClassName, 'px-4 py-4')}>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Inactive</p>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">{inactiveEmployees}</p>
                  <p className="mt-1 text-sm text-slate-500">On leave, suspended, draft, or terminated.</p>
                </div>
              </div>
        </PageSection>
      </PageGrid>
    </PageStack>
  )
}
