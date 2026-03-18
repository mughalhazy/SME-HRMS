'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'
import { ArrowRight, RefreshCw, Search, UserPlus, Users } from 'lucide-react'

import { PageHero, PageStack } from '@/components/ui/page'
import { Button } from '@/components/ui/button'
import { EmptyState, ErrorState, InlineLoading, TableSkeleton } from '@/components/ui/feedback'
import { Input, Select } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { getEmployeeFullName, listEmployees } from '@/lib/employees/api'
import { EMPLOYEE_STATUSES, type Employee } from '@/lib/employees/types'

const PAGE_SIZE = 25

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' }).format(new Date(value))
}

function statusBadge(status: Employee['status']) {
  const variants: Record<Employee['status'], string> = {
    Draft: 'bg-slate-100 text-slate-700',
    Active: 'bg-emerald-100 text-emerald-700',
    OnLeave: 'bg-amber-100 text-amber-700',
    Suspended: 'bg-rose-100 text-rose-700',
    Terminated: 'bg-slate-200 text-slate-600',
  }

  return variants[status]
}

export function EmployeeListPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<(typeof EMPLOYEE_STATUSES)[number] | 'all'>('all')
  const [departmentId, setDepartmentId] = useState('')

  const query = useInfiniteQuery({
    queryKey: ['employees', status, departmentId],
    initialPageParam: null as string | null,
    queryFn: ({ pageParam }) =>
      listEmployees({
        status,
        departmentId: departmentId || undefined,
        limit: PAGE_SIZE,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) => (lastPage.page.hasNext ? lastPage.page.nextCursor : null),
  })

  const employees = useMemo(() => query.data?.pages.flatMap((page) => page.data) ?? [], [query.data])

  const filteredEmployees = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()
    if (!normalizedSearch) {
      return employees
    }

    return employees.filter((employee) => {
      const haystack = [
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

      return haystack.includes(normalizedSearch)
    })
  }, [employees, search])

  return (
    <PageStack>
      <PageHero
        eyebrow="Employee list"
        title="Directory with search, filters, and fast paging"
        description={
          <>
            Built on the canonical <code className="rounded bg-slate-100 px-1 py-0.5">employee_directory_view</code>
            read model with cursor-based loading for larger tables.
          </>
        }
        actions={
          <>
            <Button variant="outline" onClick={() => query.refetch()} disabled={query.isFetching}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            <Button asChild>
              <Link href="/employees/new">
                <UserPlus className="h-4 w-4" />
                Add employee
              </Link>
            </Button>
          </>
        }
      />

      <section className="overflow-hidden rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-surface)]">
        <div className="flex flex-col gap-3 border-b border-slate-200 px-5 py-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600">
            <span>
            Showing <strong className="text-slate-950">{filteredEmployees.length}</strong> of{' '}
            <strong className="text-slate-950">{employees.length}</strong> loaded employees.
            </span>
            {query.isFetching ? <InlineLoading label="Syncing directory…" /> : null}
          </div>

          <div className="grid gap-3 lg:grid-cols-[minmax(0,1.6fr)_220px_220px]">
            <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
              <span>Search</span>
              <span className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  className="pl-10"
                  placeholder="Name, email, employee number, role..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </span>
            </label>

            <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
              <span>Status</span>
              <Select
                value={status}
                onChange={(event) => setStatus(event.target.value as (typeof EMPLOYEE_STATUSES)[number] | 'all')}
              >
                <option value="all">All statuses</option>
                {EMPLOYEE_STATUSES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </Select>
            </label>

            <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
              <span>Department</span>
              <Input placeholder="dep-hr" value={departmentId} onChange={(event) => setDepartmentId(event.target.value)} />
            </label>
          </div>
        </div>

        {query.isLoading ? (
          <TableSkeleton rows={6} columns={6} />
        ) : query.isError ? (
          <div className="p-6">
            <ErrorState message={query.error.message} onRetry={() => query.refetch()} />
          </div>
        ) : filteredEmployees.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Users}
              title="No employees found"
              message="There are no employees matching the current filters yet. Clear filters or add a new employee record to populate the directory."
              action={
                <Button asChild>
                  <Link href="/employees/new">
                    <UserPlus className="h-4 w-4" />
                    Add employee
                  </Link>
                </Button>
              }
            />
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Hire date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEmployees.map((employee) => (
                  <TableRow key={employee.employee_id}>
                    <TableCell className="align-top">
                      <div className="font-medium text-slate-950">{getEmployeeFullName(employee)}</div>
                      <div className="text-sm text-slate-500">{employee.employee_number}</div>
                      <div className="text-sm text-slate-500">{employee.email}</div>
                    </TableCell>
                    <TableCell className="align-top">
                      <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusBadge(employee.status)}`}>
                        {employee.status}
                      </span>
                    </TableCell>
                    <TableCell className="align-top text-slate-600">{employee.department_id}</TableCell>
                    <TableCell className="align-top text-slate-600">{employee.role_id}</TableCell>
                    <TableCell className="align-top text-slate-600">{formatDate(employee.hire_date)}</TableCell>
                    <TableCell className="align-top">
                      <div className="flex flex-wrap gap-1.5">
                        <Button asChild variant="ghost" size="sm">
                          <Link href={`/employees/${employee.employee_id}`}>View</Link>
                        </Button>
                        <Button asChild size="sm">
                          <Link href={`/employees/${employee.employee_id}/edit`}>
                            Edit
                            <ArrowRight className="h-4 w-4" />
                          </Link>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-3.5">
              <p className="text-sm text-slate-500">Cursor pagination keeps the table responsive as the dataset grows.</p>
              <Button onClick={() => query.fetchNextPage()} disabled={!query.hasNextPage || query.isFetchingNextPage}>
                {query.isFetchingNextPage ? 'Loading…' : query.hasNextPage ? 'Load more' : 'No more results'}
              </Button>
            </div>
          </>
        )}
      </section>
    </PageStack>
  )
}
