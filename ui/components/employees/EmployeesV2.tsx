'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'
import { ArrowUpRight, ListFilter, PencilLine, RefreshCw, Search, SlidersHorizontal, UserPlus, Users } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ErrorState, InlineLoading, Skeleton } from '@/components/ui/feedback'
import { Input, Select } from '@/components/ui/input'
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

function formatEmploymentType(type: Employee['employment_type']) {
  return type.replace(/([a-z])([A-Z])/g, '$1 $2')
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

function EmployeesV2LoadingState() {
  return (
    <Table className="min-w-[1120px] table-fixed">
      <colgroup>
        <col className="w-[26%]" />
        <col className="w-[14%]" />
        <col className="w-[14%]" />
        <col className="w-[12%]" />
        <col className="w-[16%]" />
        <col className="w-[10%]" />
        <col className="w-[8%]" />
      </colgroup>
      <TableHeader className="bg-slate-50/95">
        <TableRow className="h-11 border-b border-slate-200 hover:bg-transparent hover:shadow-none">
          <TableHead className="px-5">Employee</TableHead>
          <TableHead className="px-5">Department</TableHead>
          <TableHead className="px-5">Role</TableHead>
          <TableHead className="px-5">Type</TableHead>
          <TableHead className="px-5">Manager</TableHead>
          <TableHead className="px-5">Status</TableHead>
          <TableHead className="px-5 text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Array.from({ length: 8 }).map((_, index) => (
          <TableRow key={index} className="h-[72px] border-b border-slate-200 hover:bg-transparent hover:shadow-none">
            <TableCell className="px-5 py-3">
              <div className="flex items-center gap-3">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-40" />
                  <Skeleton className="h-3 w-56 max-w-full" />
                </div>
              </div>
            </TableCell>
            <TableCell className="px-5 py-3"><Skeleton className="h-4 w-24" /></TableCell>
            <TableCell className="px-5 py-3"><Skeleton className="h-4 w-28" /></TableCell>
            <TableCell className="px-5 py-3"><Skeleton className="h-4 w-20" /></TableCell>
            <TableCell className="px-5 py-3"><Skeleton className="h-4 w-24" /></TableCell>
            <TableCell className="px-5 py-3"><Skeleton className="h-6 w-20 rounded-full" /></TableCell>
            <TableCell className="px-5 py-3"><div className="ml-auto flex w-fit gap-2"><Skeleton className="h-8 w-8 rounded-lg" /><Skeleton className="h-8 w-8 rounded-lg" /></div></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export function EmployeesV2() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<(typeof EMPLOYEE_STATUSES)[number] | 'all'>('all')
  const [departmentId, setDepartmentId] = useState('all')
  const [employmentType, setEmploymentType] = useState<'all' | Employee['employment_type']>('all')

  const query = useInfiniteQuery({
    queryKey: ['employees-v2-directory'],
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

  const employmentTypeOptions = useMemo(
    () => Array.from(new Set(employees.map((employee) => employee.employment_type))).sort((left, right) => left.localeCompare(right)),
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
          employee.status,
          employee.employment_type,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
          .includes(normalizedSearch)

      const matchesStatus = status === 'all' || employee.status === status
      const matchesDepartment = departmentId === 'all' || employee.department_id === departmentId
      const matchesEmploymentType = employmentType === 'all' || employee.employment_type === employmentType

      return matchesSearch && matchesStatus && matchesDepartment && matchesEmploymentType
    })
  }, [departmentId, employees, employmentType, search, status])

  const activeCount = useMemo(() => filteredEmployees.filter((employee) => employee.status === 'Active').length, [filteredEmployees])
  const hasActiveFilters = search.length > 0 || status !== 'all' || departmentId !== 'all' || employmentType !== 'all'

  const resetFilters = () => {
    setSearch('')
    setStatus('all')
    setDepartmentId('all')
    setEmploymentType('all')
  }

  return (
    <section className="min-w-0 border border-slate-200 bg-white">
      <div className="grid gap-4 border-b border-slate-200 px-5 py-5 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-end">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            <span>Employees V2</span>
            <span className="h-1 w-1 rounded-full bg-slate-300" />
            <span>Grid workspace</span>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-950">Operational employee register</h2>
            <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-700">
              {filteredEmployees.length} visible rows
            </Badge>
          </div>
          <p className="max-w-3xl text-sm leading-6 text-slate-600">
            A table-first employee workspace with dense scanning, quick filters, and direct row actions.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 xl:justify-end">
          <Button variant="outline" className="h-10 gap-2 border-slate-200 text-slate-700 shadow-none" onClick={resetFilters} disabled={!hasActiveFilters}>
            <SlidersHorizontal className="h-4 w-4" />
            Reset filters
          </Button>
          <Button variant="outline" className="h-10 gap-2 border-slate-200 text-slate-700 shadow-none" onClick={() => query.refetch()} disabled={query.isFetching}>
            <RefreshCw className={cn('h-4 w-4', query.isFetching ? 'animate-spin' : '')} />
            Refresh grid
          </Button>
          <Button asChild className="h-10 gap-2 shadow-none">
            <Link href="/employees/new">
              <UserPlus className="h-4 w-4" />
              Add employee
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 border-b border-slate-200 px-5 py-4 xl:grid-cols-[minmax(280px,1.2fr)_repeat(3,minmax(0,0.6fr))_auto] xl:items-center">
        <label className="relative min-w-0">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            className="h-10 border-slate-200 bg-white pl-10 shadow-none"
            placeholder="Search by name, ID, email, team, role"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <Select className="h-10 border-slate-200 bg-white shadow-none" value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}>
          <option value="all">All departments</option>
          {departmentOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </Select>

        <Select className="h-10 border-slate-200 bg-white shadow-none" value={employmentType} onChange={(event) => setEmploymentType(event.target.value as 'all' | Employee['employment_type'])}>
          <option value="all">All employment types</option>
          {employmentTypeOptions.map((option) => (
            <option key={option} value={option}>
              {formatEmploymentType(option)}
            </option>
          ))}
        </Select>

        <Select className="h-10 border-slate-200 bg-white shadow-none" value={status} onChange={(event) => setStatus(event.target.value as (typeof EMPLOYEE_STATUSES)[number] | 'all')}>
          <option value="all">All statuses</option>
          {EMPLOYEE_STATUSES.map((option) => (
            <option key={option} value={option}>
              {formatStatus(option)}
            </option>
          ))}
        </Select>

        <div className="flex flex-wrap items-center justify-between gap-3 border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-600 xl:justify-end">
          <div className="flex items-center gap-2">
            <ListFilter className="h-4 w-4 text-slate-400" />
            <span>
              <span className="font-semibold text-slate-950">{activeCount}</span> active
            </span>
          </div>
          {query.isFetching ? <InlineLoading label="Updating" /> : null}
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-3 text-sm text-slate-500">
        <div className="flex flex-wrap items-center gap-3">
          <span>
            Loaded <span className="font-semibold text-slate-950">{employees.length}</span> employees
          </span>
          <span className="hidden h-1 w-1 rounded-full bg-slate-300 sm:block" />
          <span>
            Showing <span className="font-semibold text-slate-950">{filteredEmployees.length}</span> rows
          </span>
        </div>
        <span>{hasActiveFilters ? 'Filtered grid view' : 'Full directory grid'}</span>
      </div>

      {query.isLoading ? (
        <EmployeesV2LoadingState />
      ) : query.isError ? (
        <ErrorState className="rounded-none border-0 px-5 py-8 shadow-none" message={query.error.message} onRetry={() => query.refetch()} />
      ) : filteredEmployees.length === 0 ? (
        <div className="flex min-h-[360px] flex-col items-center justify-center gap-4 px-5 py-12 text-center">
          <div className="rounded-full border border-slate-200 bg-slate-50 p-3 text-slate-500">
            <Users className="h-5 w-5" />
          </div>
          <div className="space-y-2">
            <h2 className="text-lg font-semibold tracking-tight text-slate-950">
              {employees.length === 0 ? 'No employees loaded yet' : 'No employees match this grid filter'}
            </h2>
            <p className="text-sm leading-6 text-slate-500">
              {employees.length === 0 ? 'Load data or add the first employee to populate the table.' : 'Adjust the search or filter controls to widen the result set.'}
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {hasActiveFilters ? (
              <Button variant="outline" onClick={resetFilters}>
                Reset filters
              </Button>
            ) : (
              <Button asChild>
                <Link href="/employees/new">Add employee</Link>
              </Button>
            )}
          </div>
        </div>
      ) : (
        <div className="min-w-0">
          <Table className="min-w-[1120px] table-fixed">
            <colgroup>
              <col className="w-[26%]" />
              <col className="w-[14%]" />
              <col className="w-[14%]" />
              <col className="w-[12%]" />
              <col className="w-[16%]" />
              <col className="w-[10%]" />
              <col className="w-[8%]" />
            </colgroup>
            <TableHeader className="bg-slate-50/95">
              <TableRow className="h-11 border-b border-slate-200 bg-transparent hover:bg-transparent hover:shadow-none">
                <TableHead className="px-5">Employee</TableHead>
                <TableHead className="px-5">Department</TableHead>
                <TableHead className="px-5">Role</TableHead>
                <TableHead className="px-5">Type</TableHead>
                <TableHead className="px-5">Manager</TableHead>
                <TableHead className="px-5">Status</TableHead>
                <TableHead className="px-5 text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEmployees.map((employee) => (
                <TableRow
                  key={employee.employee_id}
                  className="group h-[72px] cursor-pointer border-b border-slate-200 hover:bg-slate-50"
                  onClick={() => router.push(`/employees/${employee.employee_id}`)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault()
                      router.push(`/employees/${employee.employee_id}`)
                    }
                  }}
                  tabIndex={0}
                >
                  <TableCell className="px-5 py-3">
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
                  <TableCell className="px-5 py-3 text-sm text-slate-600">{employee.department_id}</TableCell>
                  <TableCell className="px-5 py-3 text-sm text-slate-600">{employee.role_id}</TableCell>
                  <TableCell className="px-5 py-3 text-sm text-slate-600">{formatEmploymentType(employee.employment_type)}</TableCell>
                  <TableCell className="px-5 py-3 text-sm text-slate-600">{employee.manager_employee_id ?? 'Unassigned'}</TableCell>
                  <TableCell className="px-5 py-3">
                    <div className="space-y-1">
                      <Badge variant="outline" className={cn('min-w-[92px] justify-center font-medium', statusTone(employee.status))}>
                        {formatStatus(employee.status)}
                      </Badge>
                      <p className="text-xs text-slate-400">Updated {formatDate(employee.updated_at)}</p>
                    </div>
                  </TableCell>
                  <TableCell className="px-5 py-3">
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
            <div className="flex items-center justify-between gap-3 border-t border-slate-200 px-5 py-3 text-sm text-slate-500">
              <span>More employee rows are available for this register.</span>
              <Button variant="outline" onClick={() => query.fetchNextPage()} disabled={query.isFetchingNextPage}>
                {query.isFetchingNextPage ? 'Loading…' : 'Load more rows'}
              </Button>
            </div>
          ) : null}
        </div>
      )}
    </section>
  )
}
