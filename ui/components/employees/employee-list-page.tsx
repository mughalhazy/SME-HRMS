'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'
import { ArrowRight, LoaderCircle, RefreshCw, Search, UserPlus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { listEmployees, getEmployeeFullName } from '@/lib/employees/api'
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
    <div className="flex flex-col gap-6">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Employee list</p>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Directory with search, filters, and fast paging</h1>
            <p className="max-w-3xl text-sm leading-6 text-slate-600">
              Built on the canonical <code className="rounded bg-slate-100 px-1 py-0.5">employee_directory_view</code>
              read model with cursor-based loading for larger tables.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={() => query.refetch()}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            <Button asChild>
              <Link href="/employees/new">
                <UserPlus className="h-4 w-4" />
                Add employee
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm lg:grid-cols-[1.5fr,1fr,1fr]">
        <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
          Search
          <span className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              className="h-11 w-full rounded-xl border border-slate-200 bg-white pl-10 pr-3 text-sm shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
              placeholder="Name, email, employee number, role..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </span>
        </label>

        <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
          Status filter
          <select
            className="h-11 rounded-xl border border-slate-200 bg-white px-3 text-sm shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
            value={status}
            onChange={(event) => setStatus(event.target.value as (typeof EMPLOYEE_STATUSES)[number] | 'all')}
          >
            <option value="all">All statuses</option>
            {EMPLOYEE_STATUSES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
          Department filter
          <input
            className="h-11 rounded-xl border border-slate-200 bg-white px-3 text-sm shadow-sm outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
            placeholder="dep-hr"
            value={departmentId}
            onChange={(event) => setDepartmentId(event.target.value)}
          />
        </label>
      </section>

      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 text-sm text-slate-600">
          <span>
            Showing <strong className="text-slate-950">{filteredEmployees.length}</strong> of{' '}
            <strong className="text-slate-950">{employees.length}</strong> loaded employees.
          </span>
          {query.isFetching ? (
            <span className="inline-flex items-center gap-2 text-slate-500">
              <LoaderCircle className="h-4 w-4 animate-spin" />
              Syncing directory...
            </span>
          ) : null}
        </div>

        {query.isError ? (
          <div className="px-6 py-10 text-sm text-rose-600">{query.error.message}</div>
        ) : filteredEmployees.length === 0 && !query.isLoading ? (
          <div className="px-6 py-10 text-sm text-slate-500">No employees match the current filters.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-6 py-3 font-medium">Employee</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">Department</th>
                  <th className="px-6 py-3 font-medium">Role</th>
                  <th className="px-6 py-3 font-medium">Hire date</th>
                  <th className="px-6 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {filteredEmployees.map((employee) => (
                  <tr key={employee.employee_id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 align-top">
                      <div className="font-medium text-slate-950">{getEmployeeFullName(employee)}</div>
                      <div className="text-slate-500">{employee.employee_number}</div>
                      <div className="text-slate-500">{employee.email}</div>
                    </td>
                    <td className="px-6 py-4 align-top">
                      <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusBadge(employee.status)}`}>
                        {employee.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 align-top text-slate-600">{employee.department_id}</td>
                    <td className="px-6 py-4 align-top text-slate-600">{employee.role_id}</td>
                    <td className="px-6 py-4 align-top text-slate-600">{formatDate(employee.hire_date)}</td>
                    <td className="px-6 py-4 align-top">
                      <div className="flex flex-wrap gap-2">
                        <Button asChild variant="outline" size="sm">
                          <Link href={`/employees/${employee.employee_id}`}>View</Link>
                        </Button>
                        <Button asChild size="sm">
                          <Link href={`/employees/${employee.employee_id}/edit`}>
                            Edit
                            <ArrowRight className="h-4 w-4" />
                          </Link>
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-6 py-4">
          <p className="text-sm text-slate-500">
            Cursor pagination keeps the table responsive as the dataset grows.
          </p>
          <Button onClick={() => query.fetchNextPage()} disabled={!query.hasNextPage || query.isFetchingNextPage}>
            {query.isFetchingNextPage ? <LoaderCircle className="h-4 w-4 animate-spin" /> : null}
            {query.hasNextPage ? 'Load more' : 'No more results'}
          </Button>
        </div>
      </section>
    </div>
  )
}
